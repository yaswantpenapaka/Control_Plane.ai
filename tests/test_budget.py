import pytest
from decision.budget import BudgetAccountant
from llm.schemas import BudgetState


def test_budget_initialization():
    accountant = BudgetAccountant(target=0.005, window_days=7)
    assert accountant.target == 0.005
    assert accountant.window_days == 7
    assert accountant.get_state() == BudgetState.HEALTHY


def test_budget_tracking():
    accountant = BudgetAccountant(target=0.005)
    for _ in range(100):
        accountant.record_event(consumed=False)
    assert accountant.get_state() == BudgetState.HEALTHY


def test_budget_burn():
    accountant = BudgetAccountant(target=0.005)
    for _ in range(100):
        accountant.record_event(consumed=False)
    for _ in range(1):
        accountant.record_event(consumed=True)
    state = accountant.get_state()
    assert state != BudgetState.EXHAUSTED


def test_budget_lane_b_routing():
    accountant = BudgetAccountant(target=0.005)
    for _ in range(50):
        accountant.record_event(consumed=True)
    for _ in range(50):
        accountant.record_event(consumed=False)
    assert accountant.should_route_to_lane_b() is True


def test_burn_rate_calculation():
    accountant = BudgetAccountant(target=0.01)
    for _ in range(50):
        accountant.record_event(consumed=False)
    for _ in range(5):
        accountant.record_event(consumed=True)
    burn_rate = accountant.get_burn_rate()
    assert 0.08 < burn_rate < 0.12
