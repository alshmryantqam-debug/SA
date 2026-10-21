# Security model

## Defaults
- Fixed read-only ADB command templates; arbitrary commands are rejected.
- subprocess uses shell disabled and a bounded timeout.
- Evidence is written atomically and can be checked against a SHA-256 digest.
- The GUI should require operator confirmation before scanning a selected device.
- Device identifiers can be sensitive; keep evidence local and redact before sharing.

## Limitations
- A digest detects changes only when the expected digest is kept independently; it does not prove authorship.
- Redaction is best-effort and cannot guarantee removal of all personal information.
- Output varies by host and Android build; the tool is not a forensic-grade chain-of-custody system.

Use only on devices you own or are explicitly authorized to inspect.
