from __future__ import annotations

import base64
import logging
import os
import sys
import pytest
import tempfile
from datetime import datetime, timedelta, timezone
from unittest import mock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from PySide6.QtCore import QSettings  # type: ignore

from src import profile_manager, ssl_trust
from src.infrastructure import logging_setup


def _make_cert() -> tuple[str, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    return (
        cert.public_bytes(serialization.Encoding.PEM).decode("ascii"),
        cert.public_bytes(serialization.Encoding.DER),
    )


def _temp_settings() -> QSettings:
    path = os.path.join(tempfile.mkdtemp(), "settings.ini")
    return QSettings(path, QSettings.Format.IniFormat)

class TestSslTrustFunctions:
    def test_default_port_for_scheme(self) -> None:
        assert ssl_trust.default_port_for_scheme("https") == 443
        assert ssl_trust.default_port_for_scheme("HTTPS") == 443
        assert ssl_trust.default_port_for_scheme("http") == 0

    def test_describe_pem_and_der(self) -> None:
        pem, der = _make_cert()
        info = ssl_trust.describe_pem_certificate(pem, "h", 8443)
        assert "test.example.com" in info.subject
        assert info.sha256 and ":" in info.sha256
        assert info.not_before and info.not_after
        assert info.serial_number

        info_der = ssl_trust.describe_der_certificate(der, "h", 0)
        assert info_der.port == 443
        assert "test.example.com" in info_der.subject
        assert info_der.pem.startswith("-----BEGIN CERTIFICATE-----")

    def test_describe_empty_inputs(self) -> None:
        assert ssl_trust.describe_der_certificate(b"", "h", 1).subject == ""
        assert ssl_trust.describe_pem_certificate("  ", "h", 1).subject == ""

    def test_fetch_certificate_info(self) -> None:
        pem, _ = _make_cert()
        with mock.patch("src.ssl_trust.ssl.get_server_certificate", return_value=pem):
            info = ssl_trust.fetch_certificate_info("host", 0)
            assert "test.example.com" in info.subject

    def test_format_certificate_message(self) -> None:
        pem, _ = _make_cert()
        info = ssl_trust.describe_pem_certificate(pem, "host", 443)
        msg = ssl_trust.format_certificate_message(info, errors=["self signed", ""])
        assert "host:443" in msg
        assert "SHA-256:" in msg
        assert "self signed" in msg
        assert "Trust this certificate" in msg


class TestSslTrustStore:
    def test_remember_and_query(self) -> None:
        settings = _temp_settings()
        with mock.patch("src.ssl_trust.QSettings", return_value=settings):
            store = ssl_trust.SslTrustStore()
            assert store.is_trusted("Host.example", 443) is False
            cert = ssl_trust.CertificateInfo(host="host", port=443, sha256="AA:BB", pem="PEMDATA")
            store.remember("Host.example", 443, cert)
            assert store.is_trusted("host.example", 443) is True
            assert store.get_certificate_pem("host.example", 443) == "PEMDATA"
            assert store.get_sha256("host.example", 443) == "AA:BB"

    def test_remember_without_cert(self) -> None:
        settings = _temp_settings()
        with mock.patch("src.ssl_trust.QSettings", return_value=settings):
            store = ssl_trust.SslTrustStore()
            store.remember("h", 0)
            assert store.is_trusted("h", 443) is True


class TestProfile:
    def test_properties(self) -> None:
        p = profile_manager.Profile(server_url="https://vdi.example.com/path", username="ivan.petrov")
        assert p.is_negotiate is False
        assert p.host == "vdi.example.com"
        assert p.display_label == "ivan.petrov@vdi.example.com"
        assert p.initials == "IP"

    def test_initials_single_and_empty(self) -> None:
        assert profile_manager.Profile(username="alice").initials == "A"
        assert profile_manager.Profile(username="").initials == "?"
        assert profile_manager.Profile(username="").display_label.startswith("?@")

    def test_is_negotiate(self) -> None:
        assert profile_manager.Profile(login_method="negotiate").is_negotiate is True

    def test_avatar_color_deterministic(self) -> None:
        p = profile_manager.Profile(id="fixed-id")
        c1 = profile_manager.avatar_color(p)
        c2 = profile_manager.avatar_color(p)
        assert c1 == c2
        assert c1 in profile_manager._AVATAR_COLORS


class TestProfileManager:
    def test_crud_cycle(self) -> None:
        mgr = profile_manager.ProfileManager(_temp_settings())
        assert mgr.load_all() == []
        assert mgr.get_last_used_id() is None

        p = profile_manager.Profile(
            id="p1", server_url="https://srv/x", auth_id="a1", username="user"
        )
        mgr.add_or_update(p)
        loaded = mgr.load_all()
        assert len(loaded) == 1 and loaded[0].id == "p1"
        assert mgr.get_last_used_id() == "p1"

        p2 = profile_manager.Profile(id="p1", server_url="https://srv/x", auth_id="a1", username="changed")
        mgr.add_or_update(p2)
        assert len(mgr.load_all()) == 1
        assert mgr.load_all()[0].username == "changed"

    def test_find_by_connection(self) -> None:
        mgr = profile_manager.ProfileManager(_temp_settings())
        mgr.add_or_update(
            profile_manager.Profile(id="p1", server_url="https://Srv/", auth_id="a1", username="Bob")
        )
        found = mgr.find_by_connection("https://srv", "a1", "bob")
        assert found is not None and found.id == "p1"
        assert mgr.find_by_connection("https://srv", "a1") is not None
        assert mgr.find_by_connection("https://other", "a1", "bob") is None
        assert mgr.find_by_connection("https://srv", "WRONG", "bob") is None

    def test_delete_clears_last_used(self) -> None:
        mgr = profile_manager.ProfileManager(_temp_settings())
        mgr.add_or_update(profile_manager.Profile(id="p1", server_url="https://s", auth_id="a"))
        mgr.delete("p1")
        assert mgr.load_all() == []
        assert mgr.get_last_used_id() is None

    def test_host_and_username_keys(self) -> None:
        assert profile_manager.ProfileManager._host_key("https://Host.COM/path") == "host.com"
        assert profile_manager.ProfileManager._username_key("  Bob ") == "bob"

class TestSensitiveFilter:
    def test_redacts_secrets(self) -> None:
        f = logging_setup._SensitiveFilter()
        rec = logging.LogRecord("n", logging.INFO, __file__, 1, "password=hunter2 token=abc123", None, None)
        assert f.filter(rec) is True
        assert "hunter2" not in rec.msg
        assert "abc123" not in rec.msg
        assert "<REDACTED>" in rec.msg

    def test_filter_resolves_args(self) -> None:
        f = logging_setup._SensitiveFilter()
        rec = logging.LogRecord("n", logging.INFO, __file__, 1, "token=%s", ("secretvalue",), None)
        f.filter(rec)
        assert "secretvalue" not in rec.msg
        assert rec.args is None


class TestSetupLogging:
    def setup_method(self) -> None:
        self._root = logging.getLogger()
        self._saved = self._root.handlers[:]
        self._level = self._root.level
        self._hook = sys.excepthook

    def teardown_method(self) -> None:
        for h in self._root.handlers:
            if h not in self._saved:
                h.close()
        self._root.handlers[:] = self._saved
        self._root.setLevel(self._level)
        sys.excepthook = self._hook

    def test_setup_logging_adds_handlers_once(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            with mock.patch("src.infrastructure.logging_setup._app_log_dir", return_value=__import__("pathlib").Path(d)):
                logging_setup.setup_logging()
                count = len(self._root.handlers)
                logging_setup.setup_logging()
                assert len(self._root.handlers) == count

    def test_app_log_dir_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            env = {"XDG_DATA_HOME": d} if sys.platform not in ("win32", "darwin") else {}
            with mock.patch.dict(os.environ, env):
                path = logging_setup._app_log_dir()
                assert path.exists()

    def test_exception_hook(self) -> None:
        logging_setup._install_exception_hook()
        hook = sys.excepthook
        try:
            raise ValueError("boom")
        except ValueError:
            hook(*sys.exc_info())
        with mock.patch.object(sys, "__excepthook__"):
            try:
                raise KeyboardInterrupt()
            except KeyboardInterrupt:
                hook(*sys.exc_info())

class TestNegotiateClient:
    def _client(self):
        from src.auth import negotiate

        client = negotiate.NegotiateClient.__new__(negotiate.NegotiateClient)
        client._ctx = mock.MagicMock()
        return client

    def test_complete_property(self) -> None:
        c = self._client()
        c._ctx.complete = True
        assert c.complete is True

    def test_step_encodes_tokens(self) -> None:
        c = self._client()
        c._ctx.complete = False
        c._ctx.step.return_value = b"server-token"
        out_b64, complete = c.step(base64.b64encode(b"client-token").decode())
        assert base64.b64decode(out_b64) == b"server-token"
        assert complete is False
        c._ctx.step.assert_called_once_with(b"client-token")

    def test_step_empty_input(self) -> None:
        c = self._client()
        c._ctx.complete = True
        c._ctx.step.return_value = None
        out_b64, complete = c.step("")
        assert out_b64 == ""
        assert complete is True
        c._ctx.step.assert_called_once_with(None)

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="gssapi initiator_name fallback test is not applicable on Windows",
    )
    def test_initiator_name_from_ctx(self) -> None:
        c = self._client()
        c._ctx.initiator_name = "ivan@REALM.LOCAL"
        with mock.patch(
            "src.auth.negotiate.gssapi.Credentials",
            side_effect=RuntimeError("no creds"),
        ):
            assert c.initiator_name == "ivan@REALM.LOCAL"
