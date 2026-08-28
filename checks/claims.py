import logging
from typing import List
from llm.schemas import Claim

logger = logging.getLogger(__name__)


class ClaimExtractor:
    @staticmethod
    def extract(text: str) -> List[Claim]:
        if not text:
            return []

        claims = []

        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            policy_keywords = ["policy", "refund", "day", "days", "full refund", "within", "eligible", "entitled"]

            is_policy_claim = any(keyword in sentence.lower() for keyword in policy_keywords)

            if is_policy_claim and len(sentence) > 10:
                claim = Claim(
                    text=sentence.strip(),
                    claim_type="policy_fact" if is_policy_claim else "factual",
                    material=is_policy_claim,
                )
                claims.append(claim)

        return claims
