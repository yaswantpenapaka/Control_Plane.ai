from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum
from datetime import datetime


class RiskState(str, Enum):
    ENTAILED = "entailed"
    CONTRADICTED = "contradicted"
    UNVERIFIED = "unverified"
    UNCERTAIN = "uncertain"


class Decision(str, Enum):
    ALLOW = "allow"
    EDIT = "edit"
    REGENERATE = "regenerate"
    ESCALATE = "escalate"
    BLOCK = "block"


class BudgetState(str, Enum):
    HEALTHY = "healthy"
    WATCH = "watch"
    TIGHTEN = "tighten"
    EXHAUSTED = "exhausted"


class PiiEntityType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    PAN = "pan"
    AADHAAR = "aadhaar"
    ACCOUNT_NO = "account_no"
    API_KEY = "api_key"


class PiiSpan(BaseModel):
    entity_type: PiiEntityType
    start: int
    end: int
    value: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[Dict[str, Any]]] = None
    workflow: Optional[str] = "refund-copilot"
    cohort: Optional[str] = None
    session_id: Optional[str] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ChatResponse(BaseModel):
    content: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    role: str = "assistant"


class WorkflowPolicy(BaseModel):
    workflow: str
    risk_tier: str
    error_budget: Dict[str, Any]
    latency_budget_ms: int
    evidence: Dict[str, Any]
    privacy: Dict[str, Any]
    tools: Dict[str, Any]
    interventions: Dict[str, Any]
    policy_hash: Optional[str] = None


class Claim(BaseModel):
    text: str
    claim_type: str
    material: bool


class EvidenceChunk(BaseModel):
    document_id: str
    title: str
    version: str
    effective_date: str
    content: str
    similarity: float


class ClaimVerification(BaseModel):
    claim: Claim
    entailment_score: float
    neutral_score: float
    contradiction_score: float
    risk_state: RiskState


class LaneAResult(BaseModel):
    pii_found: List[PiiSpan]
    tool_policy_violations: List[str]
    safety_violations: List[str]
    passed: bool
    reasons: List[str]


class LaneBResult(BaseModel):
    claims_extracted: List[Claim]
    evidence_retrieved: Dict[str, List[EvidenceChunk]]
    verifications: List[ClaimVerification]
    risk_state: RiskState
    uncertainty_score: Optional[float] = None
    uncertainty_level: Optional[str] = None


class ToolDecision(BaseModel):
    allowed: bool
    decision: Decision
    reason_codes: List[str]


class DecisionResult(BaseModel):
    decision: Decision
    risk_state: RiskState
    reason_codes: List[str]
    confidence: float
    tool_decision: Optional[ToolDecision] = None
    intervention_type: str


class RequestMetadata(BaseModel):
    session_id: str
    workflow: str
    timestamp: datetime
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    estimated_cost: float = 0.0


class AuditEvent(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    request_id: str
    session_id: str
    workflow: str
    policy_version: str
    model: str
    input_hash: str
    output_hash: str
    checks: Dict[str, Any]
    risk_state: RiskState
    decision: Decision
    reason_codes: List[str]
    tool_name: Optional[str] = None
    tool_args_hash: Optional[str] = None
    token_usage: Dict[str, int]
    estimated_cost: float
    latency_ms: int
    regeneration_count: int
    budget_before: str
    budget_after: str
    prev_hash: str
    record_hash: Optional[str] = None
