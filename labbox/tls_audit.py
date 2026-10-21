"""Safe TLS handshake and certificate inspection; no interception or decryption."""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
from datetime import datetime, timezone
from typing import Any


def _name_parts(name: tuple[tuple[tuple[str, str], ...], ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for rdn in name:
        for key, value in rdn:
            result[str(key)] = str(value)
    return result


def inspect_tls(host: str, port: int = 443, timeout: float = 5.0) -> dict[str, Any]:
    """Perform a normal certificate-validated TLS handshake and return public metadata."""
    if not host or host != host.strip() or any(ch in host for ch in "\r\n\x00 /\\"):
        raise ValueError("اسم المضيف غير صالح.")
    if not 1 <= int(port) <= 65535:
        raise ValueError("المنفذ يجب أن يكون بين 1 و65535.")
    timeout = max(1.0, min(float(timeout), 15.0))
    context = ssl.create_default_context()
    # Keep CA verification and hostname verification enabled; never install a proxy CA.
    with socket.create_connection((host, int(port)), timeout=timeout) as raw_socket:
        with context.wrap_socket(raw_socket, server_hostname=host) as tls_socket:
            certificate = tls_socket.getpeercert()
            not_after = certificate.get("notAfter")
            expiry = (
                datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), timezone.utc).isoformat()
                if not_after else None
            )
            subject_alt_names = [
                {"type": str(kind), "value": str(value)}
                for kind, value in certificate.get("subjectAltName", ())
            ]
            return {
                "host": host,
                "port": int(port),
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "tls_version": tls_socket.version(),
                "cipher": tls_socket.cipher()[0] if tls_socket.cipher() else None,
                "certificate": {
                    "subject": _name_parts(certificate.get("subject", ())),
                    "issuer": _name_parts(certificate.get("issuer", ())),
                    "not_before": certificate.get("notBefore"),
                    "not_after": expiry,
                    "subject_alt_names": subject_alt_names,
                },
                "verification": "passed",
                "scope": "TLS handshake metadata only; no application payload captured or decrypted.",
            }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="labbox-tls-audit",
        description="فحص شهادة TLS واتصالها بطريقة آمنة دون اعتراض أو فك تشفير المحتوى.",
    )
    parser.add_argument("host", help="اسم نطاق أو مضيف تملكه أو لديك إذن بفحصه")
    parser.add_argument("--port", type=int, default=443, help="المنفذ (افتراضي 443)")
    parser.add_argument("--timeout", type=float, default=5.0, help="مهلة الاتصال بالثواني (1–15)")
    args = parser.parse_args(argv)
    try:
        result = inspect_tls(args.host, args.port, args.timeout)
    except (OSError, ssl.SSLError, ValueError) as exc:
        print(json.dumps({"host": args.host, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
