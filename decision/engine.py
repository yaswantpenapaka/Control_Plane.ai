import logging
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from llm.schemas import (
    RiskState,
    Decision,
    ChatResponse,
    ToolCall,
    LaneAResult,
    LaneBResult,
    DecisionResult,
    ToolDecision,
    ClaimVerification,
)
from checks.pii import PiiDetector
from checks.tools import ToolPolicyValidator
from checks.nli import NLIVerifier
from retrieval.retriever import Retriever
from policy.schema import WorkflowPolicySchema
from .budget import BudgetAccountant

logger = logging.getLogger(__name__)


class DecisionEngine:
    def __init__(self, nli_verifier: Optional[NLIVerifier] = None, retriever: Optional[Retriever] = None):
        self.nli_verifier = nli_verifier or NLIVerifier()
        self.retriever = retriever or Retriever()
        self.budget = BudgetAccountant()

    def decide(
        self,
        response: ChatResponse,
        policy: WorkflowPolicySchema,
        messages: List[Dict[str, str]],
    ) -> DecisionResult:
        start_time = datetime.now()

        lane_a_result = self._lane_a_checks(response, policy)
        latency_ms_lane_a = int((datetime.now() - start_time).total_seconds() * 1000)

        lane_b_result = None
        if self._should_route_to_lane_b(response, lane_a_result, policy):
            lane_b_result = self._lane_b_checks(response, policy)

        latency_ms_total = int((datetime.now() - start_time).total_seconds() * 1000)

        risk_state = lane_b_result.risk_state if lane_b_result else RiskState.UNVERIFIED

        decision, intervention_type, reason_codes = self._make_decision(
            response, lane_a_result, lane_b_result, policy
        )

        tool_decision = None
        if response.tool_call:
            evidence_passed = lane_b_result and lane_b_result.risk_state == RiskState.ENTAILED
            tool_decision = ToolPolicyValidator.validate_tool_call(
                response.tool_call,
                policy,
                evidence_passed=evidence_passed,
                budget_exhausted=self.budget.get_state().value == "exhausted",
            )

            if not tool_decision.allowed:
                reason_codes.extend(tool_decision.reason_codes)

        confidence = self._calculate_confidence(lane_a_result, lane_b_result, decision)

        return DecisionResult(
            decision=decision,
            risk_state=risk_state,
            reason_codes=reason_codes,
            confidence=confidence,
            tool_decision=tool_decision,
            intervention_type=intervention_type,
        )

    def _lane_a_checks(self, response: ChatResponse, policy: WorkflowPolicySchema) -> LaneAResult:
        text = response.content or ""

        pii_spans = PiiDetector.detect(text)

        violations = []
        passed = True

        if pii_spans:
            policy_pii_types = policy.privacy.pii
            found_pii_types = set(span.entity_type.value for span in pii_spans)
            policy_pii_types_set = set(ptype.lower() for ptype in policy_pii_types)

            if found_pii_types & policy_pii_types_set:
                violations.append("PII_DETECTED")
                if policy.privacy.action_on_hit == "edit":
                    passed = True
                else:
                    passed = False

        tool_violations = []
        if response.tool_call:
            if response.tool_call.name not in policy.tools:
                tool_violations.append(f"TOOL_NOT_IN_POLICY:{response.tool_call.name}")
                passed = False

        return LaneAResult(
            pii_found=pii_spans,
            tool_policy_violations=tool_violations,
            safety_violations=violations,
            passed=passed,
            reasons=violations + tool_violations,
        )

    def _lane_b_checks(self, response: ChatResponse, policy: WorkflowPolicySchema) -> LaneBResult:
        from checks.claims import ClaimExtractor

        text = response.content or ""
        claims = ClaimExtractor.extract(text)

        evidence_by_claim = {}
        verifications = []

        for claim in claims:
            evidence_chunks = self.retriever.retrieve(claim.text, top_k=3)
            evidence_by_claim[claim.text] = evidence_chunks

            best_verification = None
            for evidence in evidence_chunks:
                risk_state, ent_score, neutral_score, contra_score = self.nli_verifier.verify_claim(
                    claim,
                    evidence,
                    entailment_threshold=policy.evidence.min_entailment,
                )

                verification = ClaimVerification(
                    claim=claim,
                    entailment_score=ent_score,
                    neutral_score=neutral_score,
                    contradiction_score=contra_score,
                    risk_state=risk_state,
                )
                verifications.append(verification)

                if best_verification is None or risk_state != RiskState.UNVERIFIED:
                    best_verification = verification

        risk_states = [v.risk_state for v in verifications] if verifications else [RiskState.UNVERIFIED]

        if RiskState.CONTRADICTED in risk_states:
            overall_risk_state = RiskState.CONTRADICTED
        elif RiskState.ENTAILED in risk_states:
            overall_risk_state = RiskState.ENTAILED
        elif RiskState.UNCERTAIN in risk_states:
            overall_risk_state = RiskState.UNCERTAIN
        else:
            overall_risk_state = RiskState.UNVERIFIED

        return LaneBResult(
            claims_extracted=claims,
            evidence_retrieved=evidence_by_claim,
            verifications=verifications,
            risk_state=overall_risk_state,
            uncertainty_score=0.0,
            uncertainty_level="LOW",
        )

    def _should_route_to_lane_b(self, response: ChatResponse, lane_a: LaneAResult, policy: WorkflowPolicySchema) -> bool:
        if policy.risk_tier == "high":
            return True

        if policy.evidence.required:
            return True

        if response.tool_call:
            return True

        return False

    def _make_decision(
        self,
        response: ChatResponse,
        lane_a: LaneAResult,
        lane_b: Optional[LaneBResult],
        policy: WorkflowPolicySchema,
    ) -> tuple[Decision, str, List[str]]:
        reason_codes = []

        if lane_a.pii_found:
            if policy.privacy.action_on_hit == "edit":
                return Decision.EDIT, "redact_pii", ["PII_DETECTED"]

        if not lane_a.passed and lane_a.tool_policy_violations:
            return Decision.BLOCK, "block", lane_a.tool_policy_violations

        if lane_b is None:
            if policy.interventions.ladder and len(policy.interventions.ladder) > 0:
                return Decision.ALLOW, "allow", ["NO_LANE_B_REQUIRED"]
            return Decision.ALLOW, "allow", []

        if lane_b.risk_state == RiskState.ENTAILED:
            return Decision.ALLOW, "allow", ["EVIDENCE_ENTAILED"]

        if lane_b.risk_state == RiskState.CONTRADICTED:
            if policy.interventions.max_regenerations > 0:
                return Decision.REGENERATE, "regenerate", ["EVIDENCE_CONTRADICTION"]
            else:
                return Decision.ESCALATE, "escalate", ["EVIDENCE_CONTRADICTION"]

        if lane_b.risk_state == RiskState.UNVERIFIED:
            if policy.evidence.abstain_without_evidence:
                return Decision.ESCALATE, "escalate", ["EVIDENCE_UNVERIFIED"]
            else:
                return Decision.ALLOW, "allow", ["EVIDENCE_UNVERIFIED_ALLOWED"]

        return Decision.ALLOW, "allow", []

    def _calculate_confidence(
        self, lane_a: LaneAResult, lane_b: Optional[LaneBResult], decision: Decision
    ) -> float:
        base_confidence = 0.5

        if decision == Decision.ALLOW:
            base_confidence = 0.9
        elif decision == Decision.BLOCK:
            base_confidence = 0.95
        elif decision == Decision.ESCALATE:
            base_confidence = 0.7
        elif decision == Decision.EDIT:
            base_confidence = 0.85

        return min(1.0, base_confidence)
