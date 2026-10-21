from labbox.core.scanner import scan_device

class FakeResult:
    def __init__(self, stdout): self.stdout = stdout

class FakeClient:
    def run(self, key, *, serial=None):
        values = {"state": "device", "model": "Test Phone", "android_version": "14", "manufacturer": "Example", "sdk": "34"}
        return FakeResult(values[key])

def test_scanner_collects_only_named_read_only_queries():
    findings = scan_device(FakeClient(), "fake-serial")
    assert len(findings) == 5
    assert findings[0].status == "PASS"
    assert findings[1].detail == "Test Phone"
    assert all(item.observed_at for item in findings)
