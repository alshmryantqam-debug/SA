# Threat model

## Assets
Device metadata, diagnostic evidence, integrity digest, and operator trust in read-only behavior.

## Threats
Accidental destructive commands, command injection, evidence tampering, identifier disclosure, and overconfident conclusions from incomplete output.

## Controls
Fixed command allowlist, shell-disabled subprocess calls, bounded timeout, serial control-character validation, atomic report writes, SHA-256 integrity checks, authorization prompt, and documented redaction limits.

## Out of scope
Remote exploitation, privilege escalation, bypassing Android authorization prompts, and forensic-grade chain of custody.
