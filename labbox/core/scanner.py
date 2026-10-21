"""Non-destructive device inventory checks."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .adb_client import AdbClient, AdbError


@dataclass(frozen=True)
class Finding:
    check_id: str
    title: str
    status: str
    detail: str
    observed_at: str


def scan_device(client: AdbClient, serial: str) -> list[Finding]:
    """Inspect a device only after ADB confirms it is authorized and online."""
    findings: list[Finding] = []
    now = datetime.now(timezone.utc).isoformat()
    try:
        state = client.run("state", serial=serial).stdout.strip()
    except AdbError as exc:
        return [Finding("ADB-001", "حالة الاتصال", "FAIL", str(exc), now)]

    if state != "device":
        return [Finding("ADB-001", "حالة الاتصال", "WARN",
                         f"الحالة: {state or 'غير معروفة'}؛ لم تُنفّذ فحوصات إضافية.", now)]

    findings.append(Finding("ADB-001", "حالة الاتصال", "PASS", "الجهاز متصل ومصرّح به.", now))
    for key, title in (
        ("model", "طراز الجهاز"),
        ("android_version", "إصدار Android"),
        ("manufacturer", "الشركة المصنّعة"),
        ("sdk", "مستوى SDK"),
        ("uptime", "مدة التشغيل"),
        ("disk", "مساحة قسم البيانات"),
    ):
        try:
            value = client.run(key, serial=serial).stdout.strip() or "قيمة فارغة"
            findings.append(Finding("INV-" + key.upper(), title, "INFO", value, now))
        except AdbError as exc:
            findings.append(Finding("INV-" + key.upper(), title, "WARN", str(exc), now))
    return findings


def findings_as_dicts(findings: list[Finding]) -> list[dict[str, str]]:
    return [asdict(item) for item in findings]
