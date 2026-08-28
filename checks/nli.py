import logging
from typing import Tuple, Optional
from sentence_transformers import CrossEncoder
from llm.schemas import RiskState, Claim, EvidenceChunk

logger = logging.getLogger(__name__)


class NLIVerifier:
    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-base"):
        self.model_name = model_name
        self.model = None
        self._load_model()
        self.label_map = {"ENTAILMENT": 0, "NEUTRAL": 1, "CONTRADICTION": 2}

    def _load_model(self):
        try:
            logger.info(f"Loading NLI model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            logger.info("NLI model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NLI model: {e}")

    def verify_claim(
        self,
        claim: Claim,
        evidence_chunk: EvidenceChunk,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.70,
    ) -> Tuple[RiskState, float, float, float]:
        if not self.model:
            return RiskState.UNVERIFIED, 0.0, 0.0, 0.0

        try:
            sentence_pairs = [[claim.text, evidence_chunk.content]]
            scores = self.model.predict(sentence_pairs)

            scores = scores[0]

            entailment_score = float(scores[self.label_map["ENTAILMENT"]])
            neutral_score = float(scores[self.label_map["NEUTRAL"]])
            contradiction_score = float(scores[self.label_map["CONTRADICTION"]])

            if entailment_score >= entailment_threshold:
                risk_state = RiskState.ENTAILED
            elif contradiction_score >= contradiction_threshold:
                risk_state = RiskState.CONTRADICTED
            else:
                risk_state = RiskState.UNVERIFIED

            return risk_state, entailment_score, neutral_score, contradiction_score

        except Exception as e:
            logger.error(f"NLI verification failed: {e}")
            return RiskState.UNVERIFIED, 0.0, 0.0, 0.0

    def aggregate_verification_results(
        self,
        verifications: list[Tuple[RiskState, float, float, float]],
    ) -> RiskState:
        if not verifications:
            return RiskState.UNVERIFIED

        states = [v[0] for v in verifications]

        if RiskState.CONTRADICTED in states:
            return RiskState.CONTRADICTED

        if RiskState.ENTAILED in states:
            return RiskState.ENTAILED

        if RiskState.UNCERTAIN in states:
            return RiskState.UNCERTAIN

        return RiskState.UNVERIFIED
