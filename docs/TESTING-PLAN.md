# Test plan

## Automated
1. Install development dependencies with pip install -e '.[dev]'.
2. Run pytest and ruff check .
3. Confirm evidence JSON has a schema version and timestamp.
4. Confirm editing a report causes digest verification to fail.
5. Confirm unknown ADB command keys fail before subprocess execution.

## Manual smoke test
1. Install Android Platform Tools and verify adb version.
2. Connect a test device you own or are authorized to inspect and approve the host prompt.
3. Launch the GUI, refresh devices, scan the authorized test device, and save a report.
4. Verify the digest and confirm no install, push, reboot, root, remount, or arbitrary shell command runs.
