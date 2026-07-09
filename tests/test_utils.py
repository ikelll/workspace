from __future__ import annotations

from unittest import mock

from src.utils import consts, resource_utils, types, version


class TestTypes:
    def test_ostype_str(self) -> None:
        assert str(types.OsType.LINUX) == "Linux"
        assert str(types.OsType.WINDOWS) == "Windows"
        assert str(types.OsType.MACOS) == "MacOS"
        assert str(types.OsType.UNKNOWN) == "Unknown"

    def test_forward_state_values(self) -> None:
        assert types.ForwardState.TUNNEL_LISTENING == 0
        assert types.ForwardState.TUNNEL_ERROR == 3
        assert int(types.ForwardState.TUNNEL_PROCESSING) == 2

    def test_named_tuples_defaults(self) -> None:
        rf = types.RemovableFile("/tmp/x")
        assert rf.path == "/tmp/x"
        assert rf.early_stage is False

        task = types.AwaitableTask(task="t")
        assert task.task == "t"
        assert task.wait_subprocesses is False

        auth = types.AuthenticatorType("id", "small", "auth", "type", 1, False)
        assert auth.authId == "id"
        assert auth.priority == 1


class TestVersion:
    def test_app_version_is_nonempty_str(self) -> None:
        assert isinstance(version.APP_VERSION, str)
        assert version.APP_VERSION

    def test_read_version_falls_back_to_default(self) -> None:
        with mock.patch.object(version, "read_text_resource", return_value="   "):
            assert version._read_version() == "1.0"

    def test_read_version_uses_resource_value(self) -> None:
        with mock.patch.object(version, "read_text_resource", return_value=" 2.5.1 \n"):
            assert version._read_version() == "2.5.1"


class TestConsts:
    def test_user_agent_format(self) -> None:
        assert consts.USER_AGENT.startswith("GorizontVS/")
        assert consts.VERSION in consts.USER_AGENT

    def test_basic_constants(self) -> None:
        assert consts.BUFFER_SIZE == 1024 * 16
        assert consts.LISTEN_ADDRESS == "127.0.0.1"
        assert consts.LISTEN_ADDRESS_V6 == "::1"
        assert consts.RESPONSE_OK == b"OK"


class TestResourceUtils:
    def test_missing_resource_returns_empty(self) -> None:
        assert resource_utils.read_text_resource(":/does/not/exist") == ""

    def test_existing_resource_is_read(self) -> None:
        text = resource_utils.read_text_resource(":/meta/VERSION")
        assert isinstance(text, str)
        assert text.strip() != ""
