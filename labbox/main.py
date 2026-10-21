"""Arabic desktop UI. Core remains importable when Qt is not installed."""
from __future__ import annotations
import sys
from pathlib import Path
from labbox.core.adb_client import AdbClient, AdbError
from labbox.core.evidence import write_evidence
from labbox.core.redaction import redact_text
from labbox.core.scanner import scan_device, findings_as_dicts

def main() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QLabel, QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout
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
            refresh = QPushButton("تحديث الأجهزة"); scan = QPushButton("بدء الفحص الآمن"); save = QPushButton("حفظ تقرير الأدلة")
            row.addWidget(self.devices, 1); row.addWidget(refresh); row.addWidget(scan); row.addWidget(save); layout.addLayout(row)
            self.status = QLabel("جاهز — استخدم الأداة فقط على جهاز تملكه أو لديك إذن صريح لفحصه.")
            self.status.setWordWrap(True); layout.addWidget(self.status)
            self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["المعرّف", "الفحص", "النتيجة", "التفاصيل"])
            self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 1)
            self.setCentralWidget(root)
            self.setStyleSheet("QMainWindow,QWidget{background:#100b1c;color:#f3eaff;font-size:14px} QPushButton,QComboBox{background:#261738;border:1px solid #7048a0;border-radius:8px;padding:9px} QPushButton:hover{background:#3a2055} QTableWidget{background:#181123;gridline-color:#39264d} QHeaderView::section{background:#291a3a;padding:8px;border:0}")
            refresh.clicked.connect(self.refresh_devices); scan.clicked.connect(self.scan_selected); save.clicked.connect(self.save_report)
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
