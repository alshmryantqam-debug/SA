import json

from labbox.core.evidence import write_evidence
from labbox.verify import main, validate_bundle


def _valid_finding():
    return {
        "check_id": "ADB-001",
        "title": "حالة الاتصال",
        "status": "PASS",
        "detail": "الجهاز متصل ومصرّح به.",
        "observed_at": "2026-01-01T00:00:00+00:00",
    }


def test_validate_bundle_accepts_valid_evidence(tmp_path):
    path, digest = write_evidence(tmp_path, {"findings": [_valid_finding()]})
    valid, message = validate_bundle(path)
    assert valid
    assert "1" in message
    assert len(digest) == 64


def test_validate_bundle_rejects_invalid_findings(tmp_path):
    path, _ = write_evidence(tmp_path, {"findings": ["not-an-object"]})
    valid, message = validate_bundle(path)
    assert not valid
    assert "العنصر" in message


def test_validate_bundle_rejects_unknown_schema_version(tmp_path):
    path, _ = write_evidence(tmp_path, {"findings": []})
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = 999
    path.write_text(json.dumps(payload), encoding="utf-8")
    valid, _ = validate_bundle(path)
    assert not valid


def test_cli_verifies_valid_report(tmp_path, capsys):
    path, digest = write_evidence(tmp_path, {"findings": [_valid_finding()]})
    assert main([str(path), digest]) == 0
    assert "نجح التحقق" in capsys.readouterr().out


def test_cli_detects_tampering(tmp_path, capsys):
    path, digest = write_evidence(tmp_path, {"findings": [_valid_finding()]})
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    assert main([str(path), digest]) == 1
    assert "فشل التحقق من السلامة" in capsys.readouterr().err


def test_cli_rejects_malformed_digest(tmp_path, capsys):
    path, _ = write_evidence(tmp_path, {"findings": []})
    assert main([str(path), "abc"]) == 2
    assert "64" in capsys.readouterr().err
