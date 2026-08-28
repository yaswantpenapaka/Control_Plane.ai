from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ErrorBudgetConfig(BaseModel):
    target: float
    window: str


class EvidenceConfig(BaseModel):
    required: bool = False
    min_entailment: float = 0.70
    abstain_without_evidence: bool = True


class PrivacyConfig(BaseModel):
    pii: List[str]
    action_on_hit: str = "edit"


class ToolPolicyConfig(BaseModel):
    gate: bool = False
    max_amount: Optional[float] = None
    prohibited_if: List[str] = Field(default_factory=list)


class InterventionConfig(BaseModel):
    ladder: List[str]
    max_regenerations: int = 0


class WorkflowPolicySchema(BaseModel):
    workflow: str
    risk_tier: str
    error_budget: ErrorBudgetConfig
    latency_budget_ms: int
    evidence: EvidenceConfig
    privacy: PrivacyConfig
    tools: Dict[str, Any] = Field(default_factory=dict)
    interventions: InterventionConfig
    policy_hash: Optional[str] = None
