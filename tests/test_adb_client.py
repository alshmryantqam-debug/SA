import pytest
from labbox.core.adb_client import AdbClient, AdbError, _ALLOWED

def test_arbitrary_commands_are_rejected_before_adb_lookup():
    client = AdbClient(executable="definitely-not-an-adb-binary")
    with pytest.raises(AdbError, match="allowlist"):
        client.run("shell rm -rf /")

def test_mutating_operations_are_not_public_command_keys():
    assert not {"push", "install", "uninstall", "reboot", "root", "remount"}.intersection(_ALLOWED)
