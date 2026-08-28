import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from config.settings import Settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings):
        self.db_path = Path(settings.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection_string = str(self.db_path)
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.connection_string)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                request_id TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL,
                workflow TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                model TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                output_hash TEXT NOT NULL,
                checks TEXT NOT NULL,
                risk_state TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason_codes TEXT NOT NULL,
                tool_name TEXT,
                tool_args_hash TEXT,
                token_usage TEXT NOT NULL,
                estimated_cost REAL NOT NULL,
                latency_ms INTEGER NOT NULL,
                regeneration_count INTEGER NOT NULL,
                budget_before TEXT NOT NULL,
                budget_after TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                record_hash TEXT
            );

            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL,
                workflow TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_message TEXT,
                model_response TEXT
            );

            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                workflow TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                estimated_cost REAL NOT NULL,
                decision TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS budget_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                workflow TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                budget_state TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bias_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                workflow TEXT NOT NULL,
                cohort TEXT,
                decision TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                workflow TEXT NOT NULL,
                created_at TEXT NOT NULL,
                unresolved_risks TEXT,
                previous_decisions TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_workflow ON audit_events(workflow);
            CREATE INDEX IF NOT EXISTS idx_metrics_workflow ON metrics(workflow);
            CREATE INDEX IF NOT EXISTS idx_bias_cohort ON bias_events(cohort);
        """
        )
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_audit_event(self, event: Dict[str, Any]) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_events (
                timestamp, request_id, session_id, workflow, policy_version, model,
                input_hash, output_hash, checks, risk_state, decision, reason_codes,
                tool_name, tool_args_hash, token_usage, estimated_cost, latency_ms,
                regeneration_count, budget_before, budget_after, prev_hash, record_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("timestamp"),
                event.get("request_id"),
                event.get("session_id"),
                event.get("workflow"),
                event.get("policy_version"),
                event.get("model"),
                event.get("input_hash"),
                event.get("output_hash"),
                event.get("checks"),
                event.get("risk_state"),
                event.get("decision"),
                event.get("reason_codes"),
                event.get("tool_name"),
                event.get("tool_args_hash"),
                event.get("token_usage"),
                event.get("estimated_cost"),
                event.get("latency_ms"),
                event.get("regeneration_count"),
                event.get("budget_before"),
                event.get("budget_after"),
                event.get("prev_hash"),
                event.get("record_hash"),
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id

    def get_audit_event(self, request_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_audit_events(self, workflow: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        if workflow:
            cursor.execute(
                "SELECT * FROM audit_events WHERE workflow = ? ORDER BY timestamp DESC LIMIT ?",
                (workflow, limit),
            )
        else:
            cursor.execute("SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?", (limit,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def insert_metric(self, metric: Dict[str, Any]) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO metrics (
                request_id, workflow, latency_ms, input_tokens, output_tokens,
                estimated_cost, decision, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metric.get("request_id"),
                metric.get("workflow"),
                metric.get("latency_ms"),
                metric.get("input_tokens"),
                metric.get("output_tokens"),
                metric.get("estimated_cost"),
                metric.get("decision"),
                metric.get("timestamp"),
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id

    def insert_bias_event(self, event: Dict[str, Any]) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO bias_events (
                request_id, workflow, cohort, decision, timestamp
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                event.get("request_id"),
                event.get("workflow"),
                event.get("cohort"),
                event.get("decision"),
                event.get("timestamp"),
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id

    def get_bias_events(self, workflow: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bias_events WHERE workflow = ?", (workflow,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def close(self):
        pass
