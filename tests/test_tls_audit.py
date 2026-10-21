import ssl

import pytest

from labbox import tls_audit


class FakeSocket:
    def __init__(self, certificate):
        self.certificate = certificate

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def wrap_socket(self, raw_socket, server_hostname):
        assert server_hostname == "example.test"
        return FakeTlsSocket(self.certificate)


class FakeTlsSocket:
    def __init__(self, certificate):
        self.certificate = certificate

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getpeercert(self):
        return self.certificate

    def version(self):
        return "TLSv1.3"

    def cipher(self):
        return ("TLS_AES_128_GCM_SHA256", "TLSv1.3", 128)


def test_inspect_tls_reports_certificate_metadata_and_keeps_validation(monkeypatch):
    certificate = {
        "subject": ((("commonName", "example.test"),),),
        "issuer": ((("organizationName", "Example CA"),),),
        "notBefore": "Jan  1 00:00:00 2026 GMT",
        "notAfter": "Jan  1 00:00:00 2027 GMT",
        "subjectAltName": (("DNS", "example.test"),),
    }
    context = type("Context", (), {"wrap_socket": lambda self, raw, server_hostname: FakeTlsSocket(certificate)})()
    monkeypatch.setattr(tls_audit.ssl, "create_default_context", lambda: context)
    monkeypatch.setattr(tls_audit.socket, "create_connection", lambda address, timeout: FakeSocket(certificate))
    result = tls_audit.inspect_tls("example.test")
    assert result["verification"] == "passed"
    assert result["tls_version"] == "TLSv1.3"
    assert result["certificate"]["subject"]["commonName"] == "example.test"
    assert result["certificate"]["subject_alt_names"] == [{"type": "DNS", "value": "example.test"}]
    assert "no application payload" in result["scope"]
    assert ssl.create_default_context().check_hostname is True


@pytest.mark.parametrize("host", ["", " example.test", "bad host", "a/b", "x\ny"])
def test_inspect_tls_rejects_invalid_host_before_network(monkeypatch, host):
    monkeypatch.setattr(
        tls_audit.socket,
        "create_connection",
        lambda *_args, **_kwargs: pytest.fail("network must not be used"),
    )
    with pytest.raises(ValueError):
        tls_audit.inspect_tls(host)


@pytest.mark.parametrize("port", [0, 65536, -1])
def test_inspect_tls_rejects_invalid_port(monkeypatch, port):
    monkeypatch.setattr(
        tls_audit.socket,
        "create_connection",
        lambda *_args, **_kwargs: pytest.fail("network must not be used"),
    )
    with pytest.raises(ValueError):
        tls_audit.inspect_tls("example.test", port)
