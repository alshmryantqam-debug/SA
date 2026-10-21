"""Atomic JSON evidence bundles with SHA-256 integrity checks."""
from __future__ import annotations
import hashlib, json, os, tempfile, hmac
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def canonical_json(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def write_evidence(output_dir: str | Path, payload: dict[str, Any]) -> tuple[Path, str]:
    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamped = dict(payload)
    stamped.setdefault("schema_version", 1)
    stamped.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    raw = canonical_json(stamped)
    fd, temporary = tempfile.mkstemp(prefix=".evidence-", suffix=".tmp", dir=root)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        final_path = root / ("evidence-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + os.urandom(4).hex() + ".json")
        os.replace(temp_path, final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return final_path, sha256_file(final_path)

def verify_evidence(path: str | Path, expected_sha256: str) -> bool:
    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        return False
    try:
        actual = sha256_file(candidate)
    except OSError:
        return False
    return hmac.compare_digest(actual.lower(), expected_sha256.strip().lower())
