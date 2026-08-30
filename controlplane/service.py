import logging
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime
import uuid

from llm.schemas import ChatResponse, Decision, DecisionResult, AuditEvent, RiskState
from policy.schema import WorkflowPolicySchema
from checks.pii import PiiDetector
from checks.claims import ClaimExtractor
from checks.nli import NLIVerifier
from retrieval.retriever import Retriever
from decision.engine import DecisionEngine
from decision.budget import BudgetAccountant
from audit.chain import AuditChain
from storage.database import Database
from config.settings import get_settings

logger = logging.getLogger(__name__)


class GovernanceOrchestrator:
    def __init__(self):
        self.settings = get_settings()
        self.database = Database(self.settings)
        self.pii_detector = PiiDetector()
        self.claim_extractor = ClaimExtractor()
        self.nli_verifier = NLIVerifier()
        self.retriever = Retriever()
        self.decision_engine = DecisionEngine(
            nli_verifier=self.nli_verifier,
            retriever=self.retriever
        )
        self.budget = BudgetAccountant()
        logger.info("GovernanceOrchestrator initialized")

    def process(
        self,
        response: ChatResponse,
        policy: WorkflowPolicySchema,
        messages: List[Dict[str, str]],
        session_id: str = None,
    ) -> Tuple[DecisionResult, AuditEvent]:
        """
        Execute full governance pipeline on LLM response.

        Flow:
        1. Lane A: Deterministic checks (PII, tool policy)
        2. Risk Router: Decide if Lane B needed
        3. Lane B: Evidence-based checks (retrieval, NLI, uncertainty)
        4. Decision Engine: Make governance decision
        5. Audit: Record decision with hash chain

        Returns:
            (decision_result, audit_event)
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())[:12]
        session_id = session_id or request_id

        try:
            logger.info(f"[{request_id}] Processing {policy.workflow} request")

            lane_a_result = self.decision_engine._lane_a_checks(response, policy)
            logger.info(f"[{request_id}] Lane A: PII={len(lane_a_result.pii_found)}, passed={lane_a_result.passed}")

            lane_b_result = None
            if self.decision_engine._should_route_to_lane_b(response, lane_a_result, policy):
                logger.info(f"[{request_id}] Routing to Lane B")
                lane_b_result = self.decision_engine._lane_b_checks(response, policy)
                logger.info(f"[{request_id}] Lane B: risk_state={lane_b_result.risk_state}")

            decision_result = self.decision_engine.decide(response, policy, messages)
            logger.info(f"[{request_id}] Decision: {decision_result.decision.value}")

            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            audit_event = self._create_audit_event(
                request_id=request_id,
                session_id=session_id,
                workflow=policy.workflow,
                policy_version=policy.policy_hash or "unknown",
                response=response,
                decision_result=decision_result,
                lane_a_result=lane_a_result,
                lane_b_result=lane_b_result,
                latency_ms=latency_ms,
            )

            self.database.insert_audit_event(audit_event.model_dump())
            logger.info(f"[{request_id}] Audit recorded: {audit_event.id}")

            return decision_result, audit_event

        except Exception as e:
            logger.error(f"[{request_id}] Governance pipeline error: {e}", exc_info=True)
            raise

    def _create_audit_event(
        self,
        request_id: str,
        session_id: str,
        workflow: str,
        policy_version: str,
        response: ChatResponse,
        decision_result: DecisionResult,
        lane_a_result,
        lane_b_result,
        latency_ms: int,
    ) -> AuditEvent:
        """Create audit record with hash chaining."""

        input_hash = hashlib.sha256(str(response.content).encode()).hexdigest()
        output_hash = hashlib.sha256(str(decision_result.decision.value).encode()).hexdigest()

        checks = {
            "lane_a": {
                "pii_found": len(lane_a_result.pii_found),
                "pii_types": [s.entity_type.value for s in lane_a_result.pii_found],
                "tool_violations": lane_a_result.tool_policy_violations,
                "passed": lane_a_result.passed,
            },
            "lane_b": {
                "claims_extracted": len(lane_b_result.claims_extracted) if lane_b_result else 0,
                "risk_state": lane_b_result.risk_state.value if lane_b_result else None,
                "uncertainty": lane_b_result.uncertainty_level if lane_b_result else None,
            } if lane_b_result else None,
        }

        reason_codes = decision_result.reason_codes

        event = AuditChain.create_audit_event(
            request_id=request_id,
            session_id=session_id,
            workflow=workflow,
            policy_version=policy_version,
            model=self.settings.groq_model,
            input_hash=input_hash,
            output_hash=output_hash,
            checks=checks,
            risk_state=decision_result.risk_state,
            decision=decision_result.decision,
            reason_codes=reason_codes,
            token_usage={"input_tokens": 0, "output_tokens": 0},
            estimated_cost=0.0,
            latency_ms=latency_ms,
            prev_hash=AuditChain.GENESIS,
            tool_name=response.tool_call.name if response.tool_call else None,
            tool_args_hash=hashlib.sha256(str(response.tool_call.arguments).encode()).hexdigest() if response.tool_call else None,
            regeneration_count=0,
        )

        return event

    def apply_intervention(
        self,
        response: ChatResponse,
        decision: Decision,
        pii_spans,
    ) -> ChatResponse:
        """Apply intervention to response based on decision."""

        if decision == Decision.EDIT and pii_spans:
            edited_content = PiiDetector.redact(response.content, pii_spans)
            return ChatResponse(content=edited_content, role="assistant")

        return response
