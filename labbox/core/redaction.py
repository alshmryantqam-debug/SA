"""Best-effort redaction; never treat this as a guarantee of anonymization."""
import re
_PATTERNS = [
    (re.compile(r"(?i)(serial(?:no)?\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(imei\s*[:=]\s*)\d{10,20}"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(android_id\s*[:=]\s*)[0-9a-f]{8,}"), r"\1[REDACTED]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP-REDACTED]"),
]
def redact_text(value: str) -> str:
    for pattern, replacement in _PATTERNS:
        value = pattern.sub(replacement, value)
    return value
