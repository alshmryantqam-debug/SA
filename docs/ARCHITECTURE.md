# Architecture

- `labbox.core.adb_client`: bounded subprocess wrapper; callers use named operations, never raw commands.
- `labbox.core.scanner`: maps read-only observations into timestamped findings.
- `labbox.core.evidence`: atomic UTF-8 JSON report writing and SHA-256 verification.
- `labbox.core.redaction`: best-effort identifier masking before sharing.
- `labbox.main`: optional Arabic Qt UI; core modules can be tested headlessly.

The initial release deliberately avoids remote execution, router management, privilege escalation, automatic remediation, and arbitrary shell entry.
