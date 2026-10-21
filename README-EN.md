# Labbox ADB Audit

A conservative local Android diagnostic utility with an Arabic RTL desktop interface, a strict read-only ADB command allowlist, and integrity-verifiable JSON evidence.

## Quick start

- Python 3.10+
- Android Platform Tools (`adb`)
- Install dependencies: `python -m pip install -e '.[dev]'`
- Launch: `labbox-audit` or `python -m labbox.main`
- Tests: `pytest`

## Safety boundaries

The tool does not accept arbitrary ADB commands and does not install, push, delete, reboot, root, or remount devices. Only inspect devices you own or are explicitly authorized to assess. Evidence hashes detect later changes only if the expected hash is retained separately; they do not establish authorship or forensic chain of custody.
