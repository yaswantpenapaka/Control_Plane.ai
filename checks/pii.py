import re
from llm.schemas import PiiSpan, PiiEntityType
from typing import List


class PiiDetector:
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    PHONE_PATTERN = r"\b(?:\+?91[-.]?)?\d{10}\b"
    PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
    AADHAAR_PATTERN = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    ACCOUNT_NO_PATTERN = r"\b[0-9]{10,18}\b"
    API_KEY_PATTERN = r"(?:api[_-]?key|secret|token|apikey|api_secret)[\s]*[:=][\s]*['\"]?([a-zA-Z0-9_-]+)['\"]?"

    @staticmethod
    def detect(text: str) -> List[PiiSpan]:
        if not text:
            return []

        spans = []

        spans.extend(PiiDetector._find_emails(text))
        spans.extend(PiiDetector._find_phones(text))
        spans.extend(PiiDetector._find_pans(text))
        spans.extend(PiiDetector._find_aadhaar(text))
        spans.extend(PiiDetector._find_account_numbers(text))
        spans.extend(PiiDetector._find_api_keys(text))

        spans.sort(key=lambda x: x.start)
        return spans

    @staticmethod
    def _find_emails(text: str) -> List[PiiSpan]:
        spans = []
        for match in re.finditer(PiiDetector.EMAIL_PATTERN, text):
            spans.append(
                PiiSpan(
                    entity_type=PiiEntityType.EMAIL,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(),
                )
            )
        return spans

    @staticmethod
    def _find_phones(text: str) -> List[PiiSpan]:
        spans = []
        for match in re.finditer(PiiDetector.PHONE_PATTERN, text):
            spans.append(
                PiiSpan(
                    entity_type=PiiEntityType.PHONE,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(),
                )
            )
        return spans

    @staticmethod
    def _find_pans(text: str) -> List[PiiSpan]:
        spans = []
        for match in re.finditer(PiiDetector.PAN_PATTERN, text):
            spans.append(
                PiiSpan(
                    entity_type=PiiEntityType.PAN,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(),
                )
            )
        return spans

    @staticmethod
    def _find_aadhaar(text: str) -> List[PiiSpan]:
        spans = []
        for match in re.finditer(PiiDetector.AADHAAR_PATTERN, text):
            spans.append(
                PiiSpan(
                    entity_type=PiiEntityType.AADHAAR,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(),
                )
            )
        return spans

    @staticmethod
    def _find_account_numbers(text: str) -> List[PiiSpan]:
        spans = []
        for match in re.finditer(PiiDetector.ACCOUNT_NO_PATTERN, text):
            spans.append(
                PiiSpan(
                    entity_type=PiiEntityType.ACCOUNT_NO,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(),
                )
            )
        return spans

    @staticmethod
    def _find_api_keys(text: str) -> List[PiiSpan]:
        spans = []
        for match in re.finditer(PiiDetector.API_KEY_PATTERN, text, re.IGNORECASE):
            spans.append(
                PiiSpan(
                    entity_type=PiiEntityType.API_KEY,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(1),
                )
            )
        return spans

    @staticmethod
    def redact(text: str, spans: List[PiiSpan]) -> str:
        if not spans:
            return text

        offset = 0
        result = text

        for span in sorted(spans, key=lambda x: x.start):
            entity_label = f"[REDACTED:{span.entity_type.value.upper()}]"
            adjusted_start = span.start + offset
            adjusted_end = span.end + offset

            result = result[:adjusted_start] + entity_label + result[adjusted_end:]
            offset += len(entity_label) - (span.end - span.start)

        return result
