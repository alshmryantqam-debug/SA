from labbox.core.redaction import redact_text

def test_redacts_common_identifiers():
    result = redact_text("serial: ABC123 imei=123456789012345 android_id=abcdef123456 192.168.1.4")
    assert "ABC123" not in result and "123456789012345" not in result
    assert "192.168.1.4" not in result and "[REDACTED]" in result
