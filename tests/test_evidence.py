import json
from labbox.core.evidence import write_evidence, verify_evidence

def test_evidence_roundtrip_and_tamper_detection(tmp_path):
    path, digest = write_evidence(tmp_path, {"mode": "read-only", "findings": []})
    assert path.exists() and verify_evidence(path, digest)
    path.write_text(json.dumps({"mode": "changed"}), encoding="utf-8")
    assert not verify_evidence(path, digest)

def test_evidence_has_schema_and_timestamp(tmp_path):
    path, _ = write_evidence(tmp_path, {"hello": "عربي"})
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["schema_version"] == 1 and content["created_at"]
    assert content["hello"] == "عربي"
