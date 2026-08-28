import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from llm.schemas import BudgetState

logger = logging.getLogger(__name__)


class BudgetEvent:
    def __init__(self, timestamp: datetime, event_type: str, consumed: bool):
        self.timestamp = timestamp
        self.event_type = event_type
        self.consumed = consumed


class BudgetAccountant:
    def __init__(self, target: float = 0.005, window_days: int = 7):
        self.target = target
        self.window_days = window_days
        self.events: List[BudgetEvent] = []
        self.state = BudgetState.HEALTHY

    def record_event(self, consumed: bool, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()

        event = BudgetEvent(
            timestamp=timestamp,
            event_type="error" if consumed else "success",
            consumed=consumed,
        )
        self.events.append(event)
        self._update_state()

    def _update_state(self):
        now = datetime.now()
        window_start = now - timedelta(days=self.window_days)

        recent_events = [e for e in self.events if e.timestamp >= window_start]

        if not recent_events:
            self.state = BudgetState.HEALTHY
            return

        consumed_count = sum(1 for e in recent_events if e.consumed)
        burn_rate = consumed_count / len(recent_events) if recent_events else 0

        if burn_rate <= self.target:
            self.state = BudgetState.HEALTHY
        elif burn_rate <= self.target * 1.5:
            self.state = BudgetState.WATCH
        elif burn_rate <= self.target * 3:
            self.state = BudgetState.TIGHTEN
        else:
            self.state = BudgetState.EXHAUSTED

    def get_burn_rate(self) -> float:
        now = datetime.now()
        window_start = now - timedelta(days=self.window_days)

        recent_events = [e for e in self.events if e.timestamp >= window_start]

        if not recent_events:
            return 0.0

        consumed_count = sum(1 for e in recent_events if e.consumed)
        return consumed_count / len(recent_events)

    def get_state(self) -> BudgetState:
        self._update_state()
        return self.state

    def should_route_to_lane_b(self) -> bool:
        state = self.get_state()
        return state in [BudgetState.WATCH, BudgetState.TIGHTEN, BudgetState.EXHAUSTED]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "window_days": self.window_days,
            "state": self.state.value,
            "burn_rate": self.get_burn_rate(),
            "total_events": len(self.events),
        }
