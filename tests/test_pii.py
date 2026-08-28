import pytest
from checks.pii import PiiDetector
from llm.schemas import PiiEntityType


def test_email_detection():
    text = "Contact me at john.doe@example.com"
    spans = PiiDetector.detect(text)
    assert len(spans) > 0
    assert spans[0].entity_type == PiiEntityType.EMAIL


def test_phone_detection():
    text = "My phone is 9876543210"
    spans = PiiDetector.detect(text)
    assert len(spans) > 0
    assert spans[0].entity_type == PiiEntityType.PHONE


def test_pan_detection():
    text = "My PAN is AAAAA1234A"
    spans = PiiDetector.detect(text)
    assert len(spans) > 0
    assert spans[0].entity_type == PiiEntityType.PAN


def test_aadhaar_detection():
    text = "Aadhaar: 1234 5678 9012"
    spans = PiiDetector.detect(text)
    assert len(spans) > 0
    assert spans[0].entity_type == PiiEntityType.AADHAAR


def test_redaction():
    text = "My email is john@example.com"
    spans = PiiDetector.detect(text)
    redacted = PiiDetector.redact(text, spans)
    assert "[REDACTED:EMAIL]" in redacted
    assert "john@example.com" not in redacted


def test_no_pii():
    text = "This is a normal message without any sensitive data."
    spans = PiiDetector.detect(text)
    assert len(spans) == 0
