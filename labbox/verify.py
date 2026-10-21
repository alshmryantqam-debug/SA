"""Verify exported Labbox evidence bundles without modifying them."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from labbox.core.evidence import verify_evidence

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_bundle(path: str | Path) -> tuple[bool, str]:
    """Validate the minimal public evidence schema and return a safe summary."""
    candidate = Path(path)
    try:
        with candidate.open("r", encoding="utf-8") as stream:
            payload: Any = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False, "تعذر قراءة التقرير: الملف غير موجود أو ليس JSON صالحاً."

    if not isinstance(payload, dict):
        return False, "بنية التقرير غير صالحة: الجذر يجب أن يكون كائناً JSON."
    version = payload.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        return False, "إصدار مخطط التقرير مفقود أو غير مدعوم."
    if not isinstance(payload.get("created_at"), str) or not payload["created_at"].strip():
        return False, "حقل created_at مفقود أو غير صالح."
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return False, "حقل findings مفقود أو ليس قائمة."
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            return False, f"العنصر رقم {index + 1} في findings ليس كائناً."
        required = ("check_id", "title", "status", "detail", "observed_at")
        if any(not isinstance(finding.get(key), str) for key in required):
            return False, f"العنصر رقم {index + 1} لا يطابق حقول النتائج المطلوبة."
    return True, f"بنية التقرير سليمة؛ عدد النتائج: {len(findings)}."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="labbox-verify",
        description="التحقق من سلامة تقرير Labbox وبنيته دون تعديل الملف.",
    )
    parser.add_argument("report", help="مسار ملف JSON")
    parser.add_argument("sha256", help="بصمة SHA-256 الأصلية الموثوقة (64 خانة سداسية)")
    args = parser.parse_args(argv)

    if not _SHA256_RE.fullmatch(args.sha256):
        print("بصمة SHA-256 يجب أن تتكون من 64 خانة سداسية.", file=sys.stderr)
        return 2

    valid, message = validate_bundle(args.report)
    if not valid:
        print(f"فشل التحقق من البنية: {message}", file=sys.stderr)
        return 2
    if not verify_evidence(args.report, args.sha256):
        print("فشل التحقق من السلامة: البصمة لا تطابق الملف أو تعذر قراءته.", file=sys.stderr)
        return 1

    print("نجح التحقق من بصمة SHA-256.")
    print(message)
    print("تنبيه: هذا يثبت تطابق الملف مع البصمة المقدمة فقط، ولا يثبت هوية منشئ التقرير.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
