import pytest
from policy.engine import PolicyEngine


def test_policy_loading():
    engine = PolicyEngine()
    workflows = engine.list_workflows()
    assert len(workflows) > 0
    assert "refund-copilot" in workflows
    assert "internal-summarizer" in workflows


def test_refund_copilot_policy():
    engine = PolicyEngine()
    policy = engine.get_policy("refund-copilot")
    assert policy is not None
    assert policy.workflow == "refund-copilot"
    assert policy.risk_tier == "high"
    assert policy.evidence.required is True


def test_internal_summarizer_policy():
    engine = PolicyEngine()
    policy = engine.get_policy("internal-summarizer")
    assert policy is not None
    assert policy.workflow == "internal-summarizer"
    assert policy.risk_tier == "low"
    assert policy.evidence.required is False


def test_policy_validation():
    engine = PolicyEngine()
    valid, msg = engine.validate_policy("refund-copilot")
    assert valid is True
    assert msg == ""


def test_policy_hash():
    engine = PolicyEngine()
    hash1 = engine.get_policy_hash("refund-copilot")
    hash2 = engine.get_policy_hash("refund-copilot")
    assert hash1 == hash2


def test_nonexistent_policy():
    engine = PolicyEngine()
    policy = engine.get_policy("nonexistent")
    assert policy is None
