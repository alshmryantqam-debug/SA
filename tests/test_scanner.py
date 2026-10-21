from labbox.core.scanner import scan_device


class FakeResult:
    def __init__(self, stdout):
        self.stdout = stdout


class FakeClient:
    def __init__(self, state="device"):
        self.state = state
        self.calls = []

    def run(self, key, *, serial=None):
        self.calls.append(key)
        if key == "state":
            return FakeResult(self.state)
        values = {
            "model": "Test Phone",
            "android_version": "14",
            "manufacturer": "Example",
            "sdk": "34",
            "uptime": "up 2 days",
            "disk": "Filesystem Size Used Avail Use% Mounted on",
        }
        return FakeResult(values[key])


def test_scanner_collects_inventory_only_after_authorized_connection():
    client = FakeClient()
    findings = scan_device(client, "fake-serial")
    assert len(findings) == 7
    assert findings[0].status == "PASS"
    assert findings[1].detail == "Test Phone"
    assert all(item.observed_at for item in findings)
    assert client.calls[0] == "state"


def test_scanner_does_not_query_inventory_when_device_is_unauthorized():
    client = FakeClient(state="unauthorized")
    findings = scan_device(client, "fake-serial")
    assert len(findings) == 1
    assert findings[0].status == "WARN"
    assert client.calls == ["state"]
