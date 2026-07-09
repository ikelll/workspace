from __future__ import annotations

import base64
import os
import stat
import tempfile
from unittest import mock

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.transport import consts, tools


def _reset_globals() -> None:
    tools._unlink_files.clear()
    tools._awaitable_tasks.clear()
    tools._execute_before_exit.clear()


class TestTempFiles:
    def test_save_and_read_roundtrip(self) -> None:
        path = tools.save_temp_file("hello world", filename="gvs_unit_tmp.txt")
        try:
            assert os.path.exists(path)
            assert tools.read_temp_file("gvs_unit_tmp.txt") == "hello world"
        finally:
            os.remove(path)

    def test_save_temp_file_random_name(self) -> None:
        path = tools.save_temp_file("data")
        try:
            assert path.endswith(".gorizontvs")
        finally:
            os.remove(path)

    def test_read_missing_returns_none(self) -> None:
        assert tools.read_temp_file("definitely-not-here-12345") is None


class TestNetworkHelpers:
    def test_test_server_success(self) -> None:
        with mock.patch("src.transport.tools.socket.create_connection") as cc:
            cc.return_value = mock.MagicMock()
            assert tools.test_server("host", 443) is True

    def test_test_server_failure(self) -> None:
        with mock.patch(
            "src.transport.tools.socket.create_connection", side_effect=OSError("nope")
        ):
            assert tools.test_server("host", "443") is False

    def test_gethostname(self) -> None:
        with mock.patch("src.transport.tools.socket.gethostname", return_value="myhost"):
            assert tools.gethostname() == "myhost"


class TestFindApplication:
    def test_finds_executable_in_extra_path(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            exe = os.path.join(d, "myapp")
            with open(exe, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(exe, os.stat(exe).st_mode | stat.S_IXUSR)
            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False):
                assert tools.find_application("myapp", extra_path=d) == exe

    def test_returns_none_when_missing(self) -> None:
        with mock.patch.dict(os.environ, {"PATH": ""}, clear=False):
            assert tools.find_application("no-such-binary-xyz") is None


class TestDeferredDeletion:
    def setup_method(self) -> None:
        _reset_globals()

    def test_register_and_unlink(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            path = tf.name
        tools.register_for_delayed_deletion(path, early_stage=False)
        assert len(tools._unlink_files) == 1
        with mock.patch("src.transport.tools.time.sleep"): 
            tools.unlink_files(early_stage=False)
        assert not os.path.exists(path)
        assert tools._unlink_files == []

    def test_unlink_swallows_errors(self) -> None:
        tools.register_for_delayed_deletion("/non/existent/path", early_stage=True)
        with mock.patch("src.transport.tools.time.sleep"):
            tools.unlink_files(early_stage=True)
        assert tools._unlink_files == []


class TestTasks:
    def setup_method(self) -> None:
        _reset_globals()

    def test_wait_for_tasks_join_and_wait(self) -> None:
        joinable = mock.MagicMock(spec=["join"])
        waitable = mock.MagicMock(spec=["wait"])
        tools.add_task_to_wait(joinable)
        tools.add_task_to_wait(waitable)
        tools.wait_for_tasks()
        joinable.join.assert_called_once()
        waitable.wait.assert_called_once()
        assert tools._awaitable_tasks == []

    def test_wait_for_tasks_with_subprocesses(self) -> None:
        proc = mock.MagicMock()
        proc.pid = 4242
        child = mock.MagicMock()
        child.ppid.return_value = 4242
        tools.add_task_to_wait(proc, wait_subprocesses=True)
        with mock.patch("src.transport.tools.process_iter", return_value=[child]):
            tools.wait_for_tasks()
        child.wait.assert_called_once()

    def test_wait_for_tasks_swallows_errors(self) -> None:
        bad = mock.MagicMock(spec=["join"])
        bad.join.side_effect = RuntimeError("boom")
        tools.add_task_to_wait(bad)
        tools.wait_for_tasks() 
        assert tools._awaitable_tasks == []

    def test_terminate_tasks(self) -> None:
        terminable = mock.MagicMock(spec=["terminate", "pid"])
        terminable.pid = 1
        tools.add_task_to_wait(terminable)
        with mock.patch("src.transport.tools.process_iter", return_value=[]):
            tools.terminate_tasks()
        terminable.terminate.assert_called_once()
        assert tools._awaitable_tasks == []

    def test_terminate_tasks_kill_and_close_fallbacks(self) -> None:
        killable = mock.MagicMock(spec=["kill"])
        closable = mock.MagicMock(spec=["close"])
        tools.add_task_to_wait(killable)
        tools.add_task_to_wait(closable)
        tools.terminate_tasks()
        killable.kill.assert_called_once()
        closable.close.assert_called_once()


class TestBeforeExit:
    def setup_method(self) -> None:
        _reset_globals()

    def test_callbacks_run_and_errors_swallowed(self) -> None:
        good = mock.MagicMock()
        bad = mock.MagicMock(side_effect=RuntimeError("x"))
        tools.register_execute_before_exit(good)
        tools.register_execute_before_exit(bad)
        tools.execute_before_exit()
        good.assert_called_once()
        bad.assert_called_once()
        assert tools._execute_before_exit == []


class TestVerifySignature:
    def test_valid_signature(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        script = b"echo hello"
        sig = key.sign(script, padding.PKCS1v15(), hashes.SHA256())
        with mock.patch("src.transport.tools.PUBLIC_KEY", pub_pem):
            assert tools.verify_signature(script, base64.b64encode(sig)) is True

    def test_invalid_signature_returns_false(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        with mock.patch("src.transport.tools.PUBLIC_KEY", pub_pem):
            assert tools.verify_signature(b"script", base64.b64encode(b"garbage")) is False


class TestCaCerts:
    def test_env_override(self) -> None:
        with mock.patch.dict(os.environ, {"CERTIFICATE_BUNDLE_PATH": "/custom/ca.pem"}):
            assert tools.get_cacerts_file() == "/custom/ca.pem"

    def test_certifi_path(self) -> None:
        fake_certifi = mock.MagicMock()
        fake_certifi.where.return_value = "/fake/certifi/cacert.pem"
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.dict(
            "sys.modules", {"certifi": fake_certifi}
        ), mock.patch("src.transport.tools.os.path.exists", return_value=True):
            assert tools.get_cacerts_file() == "/fake/certifi/cacert.pem"


class TestPlatformHelpers:
    def test_platform_predicates_consistent(self) -> None:
        results = [tools.is_macos(), tools.is_linux(), tools.is_windows()]
        assert sum(bool(r) for r in results) == 1

    def test_aliases_point_to_functions(self) -> None:
        assert tools.saveTempFile is tools.save_temp_file
        assert tools.testServer is tools.test_server
        assert tools.addTaskToWait is tools.add_task_to_wait


class TestTransportConsts:
    def test_constants_present(self) -> None:
        assert consts.HANDSHAKE_V1 == b"\x5AMGB\xA5\x01\x00"
        assert consts.CMD_TEST == b"TEST"
        assert consts.CMD_OPEN == b"OPEN"
        assert consts.RESPONSE_OK == b"OK"
        assert consts.TICKET_LENGTH == 40
        assert b"BEGIN PUBLIC KEY" in consts.PUBLIC_KEY
        assert "TLS_AES_256_GCM_SHA384" in consts.SECURE_CIPHERS
