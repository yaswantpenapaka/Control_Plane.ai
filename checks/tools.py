from llm.schemas import ToolCall, Decision, ToolDecision
from policy.schema import WorkflowPolicySchema
from typing import Optional, List


class ToolPolicyValidator:
    @staticmethod
    def validate_tool_call(
        tool_call: ToolCall,
        policy: WorkflowPolicySchema,
        evidence_passed: bool = True,
        budget_exhausted: bool = False,
    ) -> ToolDecision:
        reason_codes: List[str] = []

        if tool_call.name not in policy.tools:
            return ToolDecision(
                allowed=False,
                decision=Decision.BLOCK,
                reason_codes=["TOOL_NOT_IN_POLICY"],
            )

        tool_policy = policy.tools.get(tool_call.name, {})

        if not tool_policy.get("gate", False):
            return ToolDecision(
                allowed=True,
                decision=Decision.ALLOW,
                reason_codes=["TOOL_NOT_GATED"],
            )

        if "max_amount" in tool_policy:
            amount = tool_call.arguments.get("amount", 0)
            max_amount = tool_policy["max_amount"]

            if amount > max_amount:
                reason_codes.append("TOOL_AMOUNT_LIMIT_EXCEEDED")
                return ToolDecision(
                    allowed=False,
                    decision=Decision.ESCALATE,
                    reason_codes=reason_codes,
                )

        prohibited_conditions = tool_policy.get("prohibited_if", [])

        if "unsupported_claim" in prohibited_conditions and not evidence_passed:
            reason_codes.append("TOOL_CLAIM_NOT_SUPPORTED")

        if "evidence_failed" in prohibited_conditions and not evidence_passed:
            reason_codes.append("EVIDENCE_NOT_PASSED")

        if "budget_exhausted" in prohibited_conditions and budget_exhausted:
            reason_codes.append("BUDGET_EXHAUSTED")

        if reason_codes:
            return ToolDecision(
                allowed=False,
                decision=Decision.ESCALATE,
                reason_codes=reason_codes,
            )

        return ToolDecision(
            allowed=True,
            decision=Decision.ALLOW,
            reason_codes=["TOOL_POLICY_PASSED"],
        )
