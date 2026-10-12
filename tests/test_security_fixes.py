"""Regression tests for the audit findings (SEC-*, BUG-*, CONC-*, ...)."""
from __future__ import annotations

import datetime
import json
import os
import socket
import ssl
import stat
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.x509.oid import NameOID  # noqa: E402

from src import ssl_trust  # noqa: E402
from src.ssl_trust import CertificateChangedError, SslTrustStore  # noqa: E402
from src.transport import consts as tc  # noqa: E402
from src.transport import executor as executor_mod  # noqa: E402
from src.transport import tools as tools_mod  # noqa: E402
from src.transport import tunnel as tunnel_mod  # noqa: E402


def _make_cert(tmp_path: Path, name: str) -> tuple[str, str]:
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=30))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / f"{name}.pem"
    key_path = tmp_path / f"{name}.key"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return str(cert_path), str(key_path)


class _TlsJsonServer:

    def __init__(self, tmp_path: Path, status: int = 200, body: object | None = None) -> None:
        self.tmp_path = tmp_path
        self.status = status
        self.body = body if body is not None else {"result": "ok"}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_a):  # noqa: D401
                return

            def do_GET(self):  # noqa: N802
                payload = json.dumps(outer.body).encode()
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.use_cert("first")
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def use_cert(self, name: str) -> None:
        cert, key = _make_cert(self.tmp_path, name)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)
        self.ctx = ctx
        self.httpd.get_request = self._get_request  # type: ignore[method-assign]

    def _get_request(self):
        sock, addr = self.httpd.socket.accept()
        return self.ctx.wrap_socket(sock, server_side=True), addr

    @property
    def url(self) -> str:
        return f"https://localhost:{self.port}/x"

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture()
def fresh_store(monkeypatch):
    store = SslTrustStore()
    monkeypatch.setattr(executor_mod, "_trust_store", store)
    monkeypatch.setattr(tunnel_mod, "_trust_store", store)
    monkeypatch.setattr(tools_mod, "get_cacerts_file", lambda: None)
    return store


class TestTransportFetchTrust:
    def test_untrusted_and_refused_is_rejected(self, tmp_path, fresh_store, monkeypatch):
        srv = _TlsJsonServer(tmp_path)
        prompts = []
        monkeypatch.setattr(
            executor_mod, "confirm_certificate", lambda *a, **k: prompts.append(k) or False
        )
        try:
            with pytest.raises(ssl.SSLCertVerificationError):
                executor_mod._fetch_json(srv.url, {})
            assert len(prompts) == 1
            assert not fresh_store.is_trusted("localhost", srv.port)
        finally:
            srv.close()

    def test_accept_pins_and_next_call_does_not_prompt(self, tmp_path, fresh_store, monkeypatch):
        srv = _TlsJsonServer(tmp_path)
        prompts = []
        monkeypatch.setattr(
            executor_mod, "confirm_certificate", lambda *a, **k: prompts.append(k) or True
        )
        try:
            assert executor_mod._fetch_json(srv.url, {}) == {"result": "ok"}
            assert executor_mod._fetch_json(srv.url, {}) == {"result": "ok"}
            assert len(prompts) == 1
            assert fresh_store.get_fingerprint("localhost", srv.port)
        finally:
            srv.close()

    def test_changed_certificate_is_not_accepted_silently(self, tmp_path, fresh_store, monkeypatch):
        srv = _TlsJsonServer(tmp_path)
        answers = iter([True, False])
        prompts = []

        def _prompt(*_a, **kwargs):
            prompts.append(kwargs.get("changed"))
            return next(answers)

        monkeypatch.setattr(executor_mod, "confirm_certificate", _prompt)
        try:
            executor_mod._fetch_json(srv.url, {})
            srv.use_cert("second")
            with pytest.raises(ssl.SSLCertVerificationError):
                executor_mod._fetch_json(srv.url, {})
            assert prompts == [False, True]
        finally:
            srv.close()

    def test_check_certificate_false_is_refused(self):
        with pytest.raises(executor_mod.TransportError):
            executor_mod._fetch_json("https://localhost:1/x", {}, check_certificate=False)

    def test_pinned_context_does_not_use_system_cas(self):
        ctx = ssl_trust.create_pinned_context()
        assert ctx.verify_mode == ssl.CERT_NONE
        assert ctx.cert_store_stats()["x509_ca"] == 0

    def test_verify_pinned_peer_mismatch_raises(self):
        sock = mock.MagicMock()
        sock.getpeercert.return_value = b"other"
        with pytest.raises(CertificateChangedError):
            ssl_trust.verify_pinned_peer(sock, ssl_trust.sha256_of_der(b"pinned"))

    def test_legacy_entry_without_fingerprint_is_not_trusted(self):
        store = SslTrustStore()
        store.remember("legacy", 443)
        assert store.is_trusted("legacy", 443) is False


class TestApiClientPinning:
    def test_matching_fingerprint_is_accepted_without_prompt(self):
        from src.api.client import ApiClient

        c = ApiClient()
        c._ssl_trust_store = mock.MagicMock()
        c._ssl_trust_store.matches.return_value = True
        reply = mock.MagicMock()
        with mock.patch("src.api.client.confirm_certificate") as prompt, \
                mock.patch.object(ApiClient, "_peer_certificate_der", return_value=b"DER"):
            c._handle_ssl_errors(reply, [mock.MagicMock()])
        prompt.assert_not_called()
        reply.ignoreSslErrors.assert_called_once()

    def test_changed_fingerprint_prompts_with_warning(self):
        from PySide6.QtCore import QUrl  # type: ignore

        from src.api.client import ApiClient

        c = ApiClient()
        c._ssl_trust_store = mock.MagicMock()
        c._ssl_trust_store.matches.return_value = False
        c._ssl_trust_store.get_fingerprint.return_value = "aa" * 32
        reply = mock.MagicMock()
        reply.url.return_value = QUrl("https://h:443/x")
        reply.sslConfiguration.return_value.peerCertificate.return_value.isNull.return_value = False
        reply.sslConfiguration.return_value.peerCertificate.return_value.toDer.return_value = b"DER"
        with mock.patch("src.api.client.describe_der_certificate", return_value=mock.MagicMock()), \
                mock.patch("src.api.client.confirm_certificate", return_value=False) as prompt:
            c._handle_ssl_errors(reply, [mock.MagicMock()])
        assert prompt.call_args.kwargs.get("changed") is True
        reply.ignoreSslErrors.assert_not_called()


class _HandshakeTlsServer:

    def __init__(self, tmp_path: Path) -> None:
        cert, key = _make_cert(tmp_path, "tunnel")
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        self.ctx.load_cert_chain(cert, key)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.port = self.sock.getsockname()[1]
        self.prefixes: list[bytes] = []
        self._stop = False
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        while not self._stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            try:
                conn.settimeout(3)
                prefix = b""
                while len(prefix) < len(tc.HANDSHAKE_V1):
                    chunk = conn.recv(len(tc.HANDSHAKE_V1) - len(prefix))
                    if not chunk:
                        break
                    prefix += chunk
                self.prefixes.append(prefix)
                if prefix != tc.HANDSHAKE_V1:
                    conn.close()
                    continue
                tls = self.ctx.wrap_socket(conn, server_side=True)
                tls.close()
            except Exception:  # noqa: BLE001
                conn.close()

    def close(self) -> None:
        self._stop = True
        self.sock.close()


class TestTunnel:
    def test_certificate_prompt_uses_handshake_prefix(self, tmp_path, fresh_store, monkeypatch):
        srv = _HandshakeTlsServer(tmp_path)
        prompts = []
        monkeypatch.setattr(tunnel_mod, "confirm_certificate", lambda *a, **k: prompts.append(1) or True)
        try:
            sock = tunnel_mod.ForwardServer._connect(("127.0.0.1", srv.port))
            sock.close()
            sock = tunnel_mod.ForwardServer._connect(("127.0.0.1", srv.port))
            sock.close()
            assert prompts == [1]
            assert srv.prefixes and all(p == tc.HANDSHAKE_V1 for p in srv.prefixes)
        finally:
            srv.close()

    def test_refused_certificate_raises(self, tmp_path, fresh_store, monkeypatch):
        srv = _HandshakeTlsServer(tmp_path)
        monkeypatch.setattr(tunnel_mod, "confirm_certificate", lambda *a, **k: False)
        try:
            with pytest.raises(ssl.SSLCertVerificationError):
                tunnel_mod.ForwardServer._connect(("127.0.0.1", srv.port))
        finally:
            srv.close()

    def test_connection_counter_is_thread_safe(self):
        fs = tunnel_mod.ForwardServer(("127.0.0.1", 9), "t" * 48, timeout=60)
        try:
            def _work():
                for _ in range(2000):
                    fs._acquire_connection()
                    fs._release_connection()

            threads = [threading.Thread(target=_work) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert fs.current_connections == 0
        finally:
            fs.stop()
            fs.server_close()

    def test_keep_listening_survives_single_channel_error(self, monkeypatch):
        fs = tunnel_mod.ForwardServer(("127.0.0.1", 9), "t" * 48, timeout=-60)
        assert fs.keep_listening
        try:
            monkeypatch.setattr(
                tunnel_mod.ForwardServer, "_connect", staticmethod(mock.Mock(side_effect=OSError("refused")))
            )
            handler = tunnel_mod.Handler.__new__(tunnel_mod.Handler)
            handler.server = fs
            handler.request = mock.MagicMock()
            handler.handle()
            assert not fs.stop_flag.is_set()
        finally:
            fs.stop()
            fs.server_close()

    def test_take_all_detaches_servers(self):
        fs = tunnel_mod.ForwardServer(("127.0.0.1", 9), "t" * 48, timeout=60)
        with tunnel_mod._ACTIVE_LOCK:
            tunnel_mod._ACTIVE_FORWARD_SERVERS.add(fs)
        servers = tunnel_mod.take_all()
        assert fs in servers and not list(tunnel_mod._ACTIVE_FORWARD_SERVERS)
        tunnel_mod.stop_servers(servers)
        assert fs.stop_flag.is_set()


class TestClientAllowlist:
    from src.transport import client_options as co

    @pytest.mark.parametrize("program", [
        "gorizont-spicy", "/opt/x/gorizont-spicy", "C:\\Program Files\\G\\gorizont-spicy.exe",
        "remote-viewer", "x2goclient",
    ])
    def test_allowed(self, program):
        self.co.validate_transport_params({"as_cmd": [program, "--x"]})

    @pytest.mark.parametrize("program", ["sh", "/bin/bash", "cmd.exe", "powershell", "viewer", ""])
    def test_rejected(self, program):
        with pytest.raises(self.co.UnsafeTransportParams):
            self.co.validate_transport_params({"as_cmd": [program, "-c", "id"]})

    def test_env_extends_allowlist(self, monkeypatch):
        monkeypatch.setenv("GORIZONTVS_ALLOWED_CLIENTS", "my-viewer")
        self.co.validate_transport_params({"as_cmd": ["/usr/bin/my-viewer"]})

    def test_params_without_as_cmd_pass(self):
        self.co.validate_transport_params({"other": 1})

    def test_worker_blocks_unexpected_program(self, monkeypatch):
        import base64
        import bz2

        def pack(obj):
            raw = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
            return base64.b64encode(bz2.compress(raw)).decode()

        executed = []
        data = {"result": {
            "script": pack(b"executed.append(1)"),
            "signature": "c2ln",
            "params": pack({"as_cmd": ["/bin/sh", "-c", "id"]}),
        }}
        monkeypatch.setattr(executor_mod, "_fetch_json", lambda *a, **k: data)
        monkeypatch.setattr(executor_mod.tools_mod, "verify_signature", lambda *a: True)
        worker = executor_mod._FetchAndRunWorker("https://b", "tok", "scr", "s", "t", transport_type="SPICE")
        errors = []
        worker.error.connect(lambda _id, msg, retry: errors.append(msg))
        worker.run()
        assert errors and executed == []


class TestRedaction:
    from src.infrastructure.logging_setup import redact

    @pytest.mark.parametrize("text,secret", [
        (str({"result": "ok", "token": "SECRET1"}), "SECRET1"),
        ('{"token": "SECRET2", "mfa_token": "SECRET3"}', "SECRET2"),
        ('{"token": "SECRET2", "mfa_token": "SECRET3"}', "SECRET3"),
        ("password=SECRET4", "SECRET4"),
        ("Authorization: Negotiate SECRET5", "SECRET5"),
        ("X-Auth-Token: SECRET6", "SECRET6"),
        ("https://b/gorizontvs/rest/connection/svc/tr/SECRET7/host", "SECRET7"),
    ])
    def test_secrets_are_removed(self, text, secret):
        assert secret not in type(self).redact(text)

    def test_harmless_text_is_kept(self):
        assert type(self).redact("status_code=on items=3") == "status_code=on items=3"

    def test_default_level_is_info(self, monkeypatch):
        import logging

        from src.infrastructure import logging_setup

        monkeypatch.delenv("GORIZONTVS_DEBUG", raising=False)
        assert logging_setup._file_level() == logging.INFO
        monkeypatch.setenv("GORIZONTVS_DEBUG", "1")
        assert logging_setup._file_level() == logging.DEBUG


@pytest.mark.parametrize("platform,win,mac,linux", [
    ("win32", True, False, False),
    ("darwin", False, True, False),
    ("linux", False, False, True),
])
def test_platform_detection(monkeypatch, platform, win, mac, linux):
    monkeypatch.setattr(tools_mod.sys, "platform", platform)
    assert (tools_mod.is_windows(), tools_mod.is_macos(), tools_mod.is_linux()) == (win, mac, linux)


def test_client_platform_helper(monkeypatch):
    from src.api import auth

    for platform, expected in (("darwin", "MacOsX"), ("win32", "Windows"), ("linux", "Linux")):
        monkeypatch.setattr(auth.sys, "platform", platform)
        assert auth.client_platform() == expected


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
class TestTempFiles:
    def test_file_is_private(self):
        path = tools_mod.save_temp_file("password=secret")
        try:
            assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
            assert stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode) == 0o700
            assert os.path.basename(path).endswith(".gorizontvs")
            assert tools_mod.read_temp_file(os.path.basename(path)) == "password=secret"
        finally:
            os.unlink(path)

    def test_explicit_name_cannot_escape_directory(self):
        path = tools_mod.save_temp_file("x", "../../escape.txt")
        try:
            assert os.path.dirname(path) == tools_mod.private_temp_dir()
        finally:
            os.unlink(path)

    def test_symlink_is_not_followed(self, tmp_path):
        target = tmp_path / "victim"
        target.write_text("keep")
        link = os.path.join(tools_mod.private_temp_dir(), "planted.vv")
        with pytest.raises(FileNotFoundError):
            os.unlink(link)
        os.symlink(target, link)
        path = tools_mod.save_temp_file("new", "planted.vv")
        try:
            assert target.read_text() == "keep"
            assert not os.path.islink(path)
        finally:
            os.unlink(path)


class TestTaskRegistry:
    def test_wait_for_tasks_keeps_tasks_added_meanwhile(self):
        late = mock.MagicMock(spec=["wait"])

        class Slow:
            def wait(self):
                tools_mod.add_task_to_wait(late)

        tools_mod.take_session_resources()
        tools_mod.add_task_to_wait(Slow())
        tools_mod.wait_for_tasks()
        remaining = tools_mod.take_session_resources().tasks
        assert [t.task for t in remaining] == [late]

    def test_take_and_release_session_resources(self, tmp_path):
        f = tmp_path / "f"
        f.write_text("x")
        proc = mock.MagicMock(spec=["terminate"])
        called = []
        tools_mod.take_session_resources()
        tools_mod.register_for_delayed_deletion(str(f))
        tools_mod.add_task_to_wait(proc)
        tools_mod.register_execute_before_exit(lambda: called.append(1))
        res = tools_mod.take_session_resources()
        assert tools_mod.take_session_resources() == tools_mod.SessionResources([], [], [])
        tools_mod.release_session_resources(res)
        assert not f.exists() and called == [1]
        proc.terminate.assert_called_once()

    def test_unlink_without_delay_does_not_sleep(self, tmp_path, monkeypatch):
        f = tmp_path / "f"
        f.write_text("x")
        monkeypatch.setattr(tools_mod.time, "sleep", mock.Mock(side_effect=AssertionError("slept")))
        tools_mod.register_for_delayed_deletion(str(f), early_stage=True)
        tools_mod.unlink_files(True, delay=False)
        assert not f.exists()


def test_popen_patcher_restores_after_interleaving():
    original = subprocess.Popen
    a = executor_mod._SubprocessWaitPatcher()
    b = executor_mod._SubprocessWaitPatcher()
    a.__enter__()
    b.__enter__()
    a.__exit__(None, None, None)
    assert subprocess.Popen is not original
    b.__exit__(None, None, None)
    assert subprocess.Popen is original


class TestAuthErrors:
    def _service(self):
        from src.api.auth import AuthService

        api = mock.MagicMock()
        return AuthService(api)

    def test_negotiate_context_creation_failure(self, monkeypatch):
        from src.auth import negotiate

        svc = self._service()
        svc._client.base_url = "https://broker.example"
        errors = []
        svc.login_error.connect(errors.append)
        monkeypatch.setattr(negotiate, "NegotiateClient", mock.Mock(side_effect=RuntimeError("no gssapi")))
        svc.login_negotiate("auth-ad", "HTTP/broker")
        assert errors, "login_error must be emitted"

    def test_negotiate_step_failure(self):
        svc = self._service()
        errors = []
        svc.login_error.connect(errors.append)
        svc._negotiate_client = mock.MagicMock()
        svc._negotiate_client.step.side_effect = RuntimeError("no ticket")
        svc._run_negotiate_step("auth-ad", "", "", "Linux")
        assert errors and svc._negotiate_client is None

    def test_negotiate_round_limit(self):
        from src.api import auth

        svc = self._service()
        errors = []
        svc.login_error.connect(errors.append)
        svc._negotiate_client = mock.MagicMock()
        svc._negotiate_client.step.return_value = ("tok", False)
        svc._negotiate_rounds = auth.MAX_NEGOTIATE_ROUNDS
        svc._run_negotiate_step("auth-ad", "x", "", "Linux")
        assert errors

    def test_authenticators_html_response(self):
        svc = self._service()
        errors = []
        svc.auth_error.connect(errors.append)
        svc._on_auths_ok("<html>login portal</html>")
        assert errors


def test_abort_pending_skips_callbacks():
    from src.api.client import ApiClient

    c = ApiClient()
    reply = mock.MagicMock()
    called = []
    with mock.patch.object(c, "_handle_reply", side_effect=lambda *a: called.append(1)):
        c._connect_reply(reply, lambda d: None, lambda m, code: None)
        c.abort_pending()
        reply.abort.assert_called_once()
        reply.finished.connect.call_args.args[0]()
    assert called == []
    reply.deleteLater.assert_called_once()


def test_transport_executor_ignores_stale_launch():
    ex = executor_mod.TransportExecutor()
    errors = []
    ex.launch_error.connect(errors.append)
    ex._current_launch = 5
    ex._on_error(4, "old", False)
    ex._on_error(5, "current", False)
    assert errors == ["current"]



@pytest.mark.parametrize("url,insecure", [
    ("https://broker", False),
    ("http://127.0.0.1:8080", False),
    ("http://localhost", False),
    ("http://[::1]:80/x", False),
    ("http://broker.example", True),
    ("http://10.0.0.5:8080/x", True),
])
def test_insecure_url_detection(url, insecure):
    from src.qmlui.controller import ClientController

    assert ClientController._is_insecure_url(url) is insecure



def test_profile_cache_is_invalidated_on_write(tmp_path):
    from PySide6.QtCore import QSettings  # type: ignore

    from src.profile_manager import ProfileManager

    settings = QSettings(str(tmp_path / "p.ini"), QSettings.Format.IniFormat)
    pm = ProfileManager(settings)
    assert pm.load_all() == []
    with mock.patch.object(pm, "_read_all", wraps=pm._read_all) as reader:
        pm.load_all()
        pm.load_all()
        assert reader.call_count == 0
    profiles = pm.load_all()
    pm._save_all(profiles)
    with mock.patch.object(pm, "_read_all", wraps=pm._read_all) as reader:
        pm.load_all()
        assert reader.call_count == 1



def test_polkit_rule_requires_local_active_session():
    rule = (ROOT / "build/etc/polkit-1/rules.d/49-usbredir.rules").read_text()
    assert "subject.local" in rule and "subject.active" in rule


def test_autostart_desktop_has_valid_mimetype_key():
    text = (ROOT / "build/etc/xdg/autostart/Gorizont-VS-VDI.desktop").read_text()
    assert "MMimeType" not in text
