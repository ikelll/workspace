from __future__ import annotations

import http.server
import json
import ssl
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from src.dialogs import app_dialogs
from src.transport import executor


def _key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _chain(tmp: Path) -> tuple[Path, Path]:
    root_key, leaf_key = _key(), _key()
    now = datetime.now(timezone.utc)
    root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "GorizontVS Product Root CA")])
    root = (x509.CertificateBuilder().subject_name(root_name).issuer_name(root_name).public_key(root_key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).sign(root_key, hashes.SHA256()))
    leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "GorizontVS proxy1")])
    leaf = (x509.CertificateBuilder().subject_name(leaf_name).issuer_name(root_name).public_key(leaf_key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1"))]), critical=False)
            .sign(root_key, hashes.SHA256()))
    cert_path, key_path = tmp / "chain.pem", tmp / "leaf.key"
    cert_path.write_bytes(leaf.public_bytes(serialization.Encoding.PEM) + root.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(leaf_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return cert_path, key_path


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):  # noqa: D401
        return

    def do_GET(self):  # noqa: N802
        body = json.dumps({"result": {"ok": True, "token": self.headers.get("X-Auth-Token", "")}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def https_server():
    tmp = Path(tempfile.mkdtemp())
    cert_path, key_path = _chain(tmp)
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(cert_path), str(key_path))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "https://127.0.0.1:%d" % server.server_address[1]
    server.shutdown()
    server.server_close()


def test_trusting_leaf_certificate_allows_fetch(https_server, monkeypatch):
    prompts: list[str] = []
    monkeypatch.setattr(executor, "_trust_store", executor._trust_store.__class__())
    app_dialogs.set_prompt_backend(lambda kind, title, text, confirm, cancel: prompts.append(text) or True)
    try:
        data = executor._fetch_json(https_server + "/gorizontvs/rest/connection/s/t/scr/host", {"X-Auth-Token": "abc"})
    finally:
        app_dialogs.set_prompt_backend(None)
    assert data == {"result": {"ok": True, "token": "abc"}}
    assert len(prompts) == 1 and "GorizontVS proxy1" in prompts[0]
    data = executor._fetch_json(https_server + "/gorizontvs/rest/connection/s/t/scr/host", {"X-Auth-Token": "def"})
    assert data["result"]["token"] == "def" and len(prompts) == 1


def test_declined_certificate_raises(https_server, monkeypatch):
    monkeypatch.setattr(executor, "_trust_store", executor._trust_store.__class__())
    app_dialogs.set_prompt_backend(lambda *args: False)
    try:
        with pytest.raises(Exception):
            executor._fetch_json(https_server + "/gorizontvs/rest/connection/s/t/scr/host", {})
    finally:
        app_dialogs.set_prompt_backend(None)
