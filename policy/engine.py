import yaml
import hashlib
from pathlib import Path
from typing import Dict, Optional
from .schema import WorkflowPolicySchema


class PolicyEngine:
    def __init__(self, policy_dir: str = "policy/workflows"):
        self.policy_dir = Path(policy_dir)
        self.policies: Dict[str, WorkflowPolicySchema] = {}
        self.policy_hashes: Dict[str, str] = {}
        self._load_all_policies()

    def _load_all_policies(self):
        if not self.policy_dir.exists():
            self.policy_dir.mkdir(parents=True, exist_ok=True)
            return

        for yaml_file in self.policy_dir.glob("*.yaml"):
            workflow_name = yaml_file.stem
            try:
                policy = self.load_policy(workflow_name)
                if policy:
                    self.policies[workflow_name] = policy
                    self.policy_hashes[workflow_name] = self._compute_policy_hash(policy)
            except Exception as e:
                print(f"Failed to load policy {workflow_name}: {e}")

    def load_policy(self, workflow_name: str) -> Optional[WorkflowPolicySchema]:
        policy_file = self.policy_dir / f"{workflow_name}.yaml"

        if not policy_file.exists():
            return None

        try:
            with open(policy_file, "r") as f:
                data = yaml.safe_load(f)

            policy = WorkflowPolicySchema(**data)
            policy.policy_hash = self._compute_policy_hash(policy)
            return policy
        except Exception as e:
            print(f"Error loading policy from {policy_file}: {e}")
            return None

    def get_policy(self, workflow_name: str) -> Optional[WorkflowPolicySchema]:
        return self.policies.get(workflow_name)

    def list_workflows(self) -> list[str]:
        return list(self.policies.keys())

    def _compute_policy_hash(self, policy: WorkflowPolicySchema) -> str:
        policy_dict = policy.model_dump(exclude={"policy_hash"})
        policy_json = str(sorted(policy_dict.items()))
        return hashlib.sha256(policy_json.encode()).hexdigest()

    def get_policy_hash(self, workflow_name: str) -> Optional[str]:
        return self.policy_hashes.get(workflow_name)

    def validate_policy(self, workflow_name: str) -> tuple[bool, str]:
        policy = self.get_policy(workflow_name)
        if not policy:
            return False, f"Policy '{workflow_name}' not found"

        if not policy.workflow:
            return False, "Policy must have 'workflow' field"

        if policy.risk_tier not in ["low", "medium", "high"]:
            return False, "risk_tier must be 'low', 'medium', or 'high'"

        if policy.error_budget.target <= 0 or policy.error_budget.target > 1:
            return False, "error_budget.target must be between 0 and 1"

        if not policy.interventions.ladder:
            return False, "interventions.ladder cannot be empty"

        return True, ""
