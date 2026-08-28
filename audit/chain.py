import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
from llm.schemas import AuditEvent


class AuditChain:
    GENESIS = "GENESIS"

    @staticmethod
    def compute_record_hash(record_dict: Dict[str, Any]) -> str:
        cleaned = {k: v for k, v in record_dict.items() if k != "record_hash"}
        json_str = json.dumps(cleaned, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    @staticmethod
    def create_audit_event(
        request_id: str,
        session_id: str,
        workflow: str,
        policy_version: str,
        model: str,
        input_hash: str,
        output_hash: str,
        checks: Dict[str, Any],
        risk_state: str,
        decision: str,
        reason_codes: list[str],
        token_usage: Dict[str, int],
        estimated_cost: float,
        latency_ms: int,
        prev_hash: str,
        tool_name: Optional[str] = None,
        tool_args_hash: Optional[str] = None,
        regeneration_count: int = 0,
        budget_before: str = "HEALTHY",
        budget_after: str = "HEALTHY",
    ) -> AuditEvent:
        event_dict = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "session_id": session_id,
            "workflow": workflow,
            "policy_version": policy_version,
            "model": model,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "checks": checks,
            "risk_state": risk_state,
            "decision": decision,
            "reason_codes": reason_codes,
            "tool_name": tool_name,
            "tool_args_hash": tool_args_hash,
            "token_usage": token_usage,
            "estimated_cost": estimated_cost,
            "latency_ms": latency_ms,
            "regeneration_count": regeneration_count,
            "budget_before": budget_before,
            "budget_after": budget_after,
            "prev_hash": prev_hash,
        }

        record_hash = AuditChain.compute_record_hash(event_dict)
        event_dict["record_hash"] = record_hash

        return AuditEvent(**event_dict)
