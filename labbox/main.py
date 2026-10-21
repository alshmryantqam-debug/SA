"""Arabic desktop UI. Core remains importable when Qt is not installed."""
from __future__ import annotations
import sys
import ssl
from pathlib import Path
from labbox.core.adb_client import AdbClient, AdbError
from labbox.core.evidence import write_evidence
from labbox.core.redaction import redact_text
from labbox.core.scanner import scan_device, findings_as_dicts
from labbox.tls_audit import inspect_tls

def main() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QLabel, QMainWindow, QMessageBox, QInputDialog, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout
    except ImportError:
        print("واجهة Qt غير مثبتة. نفّذ: pip install -r requirements.txt", file=sys.stderr)
        return 2

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Labbox | مختبر تدقيق أجهزة Android")
            self.resize(1020, 700)
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.client = AdbClient()
            self.findings = []
            root = QWidget(); layout = QVBoxLayout(root)
            heading = QLabel("LABBOX  /  مركز التشخيص الآمن")
            heading.setStyleSheet("font-size:25px;font-weight:800;color:#d9b5ff;padding:12px")
            layout.addWidget(heading)
            sub = QLabel("فحص للقراءة فقط • لا تثبيت ولا حذف ولا تعديل على الجهاز")
            sub.setStyleSheet("color:#c1b2d3;padding:4px")
            layout.addWidget(sub)
            row = QHBoxLayout(); self.devices = QComboBox()
            refresh = QPushButton("تحديث الأجهزة"); scan = QPushButton("بدء الفحص الآمن"); tls_scan = QPushButton("فحص شهادة TLS"); save = QPushButton("حفظ تقرير الأدلة")
            row.addWidget(self.devices, 1); row.addWidget(refresh); row.addWidget(scan); row.addWidget(tls_scan); row.addWidget(save); layout.addLayout(row)
            self.status = QLabel("جاهز — استخدم الأداة فقط على جهاز تملكه أو لديك إذن صريح لفحصه.")
            self.status.setWordWrap(True); layout.addWidget(self.status)
            self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["المعرّف", "الفحص", "النتيجة", "التفاصيل"])
            self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 1)
            self.setCentralWidget(root)
            self.setStyleSheet("QMainWindow,QWidget{background:#100b1c;color:#f3eaff;font-size:14px} QPushButton,QComboBox{background:#261738;border:1px solid #7048a0;border-radius:8px;padding:9px} QPushButton:hover{background:#3a2055} QTableWidget{background:#181123;gridline-color:#39264d} QHeaderView::section{background:#291a3a;padding:8px;border:0}")
            refresh.clicked.connect(self.refresh_devices); scan.clicked.connect(self.scan_selected); tls_scan.clicked.connect(self.scan_tls); save.clicked.connect(self.save_report)
            self.refresh_devices()

        def refresh_devices(self):
            self.devices.clear()
            try:
                devices = self.client.list_devices()
                for item in devices:
                    self.devices.addItem(f"{item['serial']} — {item['state']}", item['serial'])
                self.status.setText(f"تم العثور على {len(devices)} جهاز. قد تظهر أجهزة غير مصرح بها أو غير متصلة بالكامل.")
            except AdbError as exc:
                self.status.setText(str(exc))

        def scan_selected(self):
            serial = self.devices.currentData()
            if not serial:
                QMessageBox.information(self, "لا يوجد جهاز", "لم يتم العثور على جهاز ADB متصل."); return
            answer = QMessageBox.question(self, "تأكيد الفحص", f"سيتم تنفيذ استعلامات قراءة فقط على {serial}. هل تملك الجهاز أو لديك إذن صريح لفحصه؟")
            if answer != QMessageBox.StandardButton.Yes: return
            self.findings = scan_device(self.client, serial)
            self.table.setRowCount(len(self.findings))
            for r, finding in enumerate(self.findings):
                for c, value in enumerate((finding.check_id, finding.title, finding.status, finding.detail)):
                    self.table.setItem(r, c, QTableWidgetItem(str(value)))
            self.status.setText(f"اكتمل الفحص: {len(self.findings)} نتيجة. لم تُنفّذ أوامر تعديل.")

        def scan_tls(self):
            host, accepted = QInputDialog.getText(
                self, "فحص شهادة TLS", "أدخل نطاقاً تملكه أو لديك إذن بفحصه:"
            )
            if not accepted or not host.strip():
                return
            try:
                result = inspect_tls(host.strip())
                certificate = result["certificate"]
                subject = certificate["subject"].get("commonName", host.strip())
                issuer = certificate["issuer"].get("commonName") or certificate["issuer"].get("organizationName", "غير معروف")
                expiry = certificate["not_after"] or "غير متاح"
                summary = (
                    f"المضيف: {result['host']}:{result['port']}\\n"
                    f"التحقق من الشهادة: ناجح\\n"
                    f"إصدار TLS: {result['tls_version']}\\n"
                    f"التشفير: {result['cipher']}\\n"
                    f"الاسم: {subject}\\n"
                    f"الجهة المصدرة: {issuer}\\n"
                    f"انتهاء الشهادة: {expiry}\\n\\n"
                    "هذه بيانات المصافحة والشهادة فقط؛ لا يجري التقاط أو فك تشفير محتوى التطبيقات."
                )
                QMessageBox.information(self, "نتيجة فحص TLS", summary)
            except (OSError, ssl.SSLError, ValueError) as exc:
                QMessageBox.warning(self, "تعذر فحص TLS", f"فشل الاتصال أو التحقق من الشهادة: {exc}")

        def save_report(self):
            if not self.findings:
                QMessageBox.information(self, "لا توجد نتائج", "نفّذ فحصًا أولًا."); return
            folder = QFileDialog.getExistingDirectory(self, "اختر مجلد حفظ الأدلة")
            if not folder: return
            payload = {"tool": "Labbox ADB Audit", "device_serial": "[REDACTED]", "mode": "read-only", "privacy": "common identifiers redacted on export", "findings": [{**item, "detail": redact_text(item["detail"])} for item in findings_as_dicts(self.findings)]}
            try:
                path, digest = write_evidence(Path(folder), payload)
                QMessageBox.information(self, "تم حفظ التقرير", f"{path}\nSHA-256: {digest}")
            except OSError as exc:
                QMessageBox.critical(self, "فشل الحفظ", str(exc))

    app = QApplication(sys.argv); window = MainWindow(); window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
