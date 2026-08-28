from pydantic_settings import BaseSettings
from typing import Literal
import os
from pathlib import Path


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"

    controlplane_mode: Literal["live", "demo", "replay"] = "demo"

    database_path: str = "data/controlplane.db"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    nli_model: str = "cross-encoder/nli-deberta-v3-base"

    uncertainty_samples: int = 3
    top_k_evidence: int = 3

    default_workflow: str = "refund-copilot"

    log_level: str = "INFO"

    groq_timeout_seconds: int = 30
    latency_budget_ms: int = 2500

    min_entailment_threshold: float = 0.70
    contradiction_threshold: float = 0.70

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_live_mode(self) -> bool:
        return self.controlplane_mode == "live"

    @property
    def is_demo_mode(self) -> bool:
        return self.controlplane_mode == "demo"

    @property
    def is_replay_mode(self) -> bool:
        return self.controlplane_mode == "replay"

    def validate_for_live_mode(self) -> tuple[bool, str]:
        if not self.is_live_mode:
            return True, ""

        if not self.groq_api_key:
            return False, "GROQ_API_KEY is required for LIVE mode"

        return True, ""


def get_settings() -> Settings:
    return Settings()
