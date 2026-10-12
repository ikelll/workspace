from __future__ import annotations

import hashlib
import socket
import ssl
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterator, TypeVar

T = TypeVar("T")
import contextlib

from cryptography import x509  # type: ignore
from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
from PySide6.QtCore import QCoreApplication, QSettings  # type: ignore


@dataclass
class CertificateInfo:
    host: str
    port: int
    subject: str = ""
    issuer: str = ""
    sha256: str = ""
    serial_number: str = ""
    not_before: str = ""
    not_after: str = ""
    pem: str = ""


class SslTrustStore:

    def __init__(self, settings: QSettings | None = None) -> None:
        self._injected = settings
        self._lock = threading.RLock()

    @property
    def _settings(self) -> QSettings:
        if self._injected is not None:
            return self._injected
        return QSettings("Gorizont-VS", "VDIClient")

    @staticmethod
    def _normalize(host: str, port: int) -> tuple[str, int]:
        normalized_host = (host or "").strip().lower()
        normalized_port = int(port or 443)
        return normalized_host, normalized_port

    def _base_key(self, host: str, port: int) -> str:
        normalized_host, normalized_port = self._normalize(host, port)
        return f"ssl/trusted_certificates/{normalized_host}:{normalized_port}"

    def is_trusted(self, host: str, port: int) -> bool:
        flag = bool(
            self._settings.value(
                f"{self._base_key(host, port)}/trusted",
                False,
                type=bool,
            )
        )
        return flag and bool(self.get_fingerprint(host, port))

    def get_fingerprint(self, host: str, port: int) -> str:
        stored = normalize_fingerprint(self.get_sha256(host, port))
        if stored:
            return stored
        pem = self.get_certificate_pem(host, port)
        if pem.strip():
            try:
                return sha256_of_der(ssl.PEM_cert_to_DER_cert(pem))
            except Exception:  # noqa: BLE001
                return ""
        return ""

    def matches(self, host: str, port: int, der_bytes: bytes) -> bool:
        if not der_bytes:
            return False
        flag = bool(
            self._settings.value(f"{self._base_key(host, port)}/trusted", False, type=bool)
        )
        expected = self.get_fingerprint(host, port)
        return flag and bool(expected) and sha256_of_der(der_bytes) == expected

    def get_certificate_pem(self, host: str, port: int) -> str:
        return str(self._settings.value(f"{self._base_key(host, port)}/pem", "") or "")

    def get_sha256(self, host: str, port: int) -> str:
        return str(self._settings.value(f"{self._base_key(host, port)}/sha256", "") or "")

    def remember(self, host: str, port: int, cert: CertificateInfo | None = None) -> None:
        base = self._base_key(host, port)
        with self._lock:
            settings = self._settings
            settings.setValue(f"{base}/trusted", True)

            if cert is not None:
                settings.setValue(f"{base}/sha256", cert.sha256)
                settings.setValue(f"{base}/subject", cert.subject)
                settings.setValue(f"{base}/issuer", cert.issuer)
                settings.setValue(f"{base}/serial_number", cert.serial_number)
                settings.setValue(f"{base}/not_before", cert.not_before)
                settings.setValue(f"{base}/not_after", cert.not_after)
                settings.setValue(f"{base}/pem", cert.pem)

            settings.setValue(f"{base}/accepted_at", datetime.now(timezone.utc).isoformat())
            settings.sync()


def normalize_fingerprint(value: str) -> str:
    return "".join(ch for ch in (value or "") if ch.isalnum()).upper()


def sha256_of_der(der_bytes: bytes) -> str:
    return hashlib.sha256(der_bytes).hexdigest().upper()


class CertificateChangedError(ssl.SSLCertVerificationError):
    """Server presented a certificate different from the pinned one."""


def create_verified_context(
    *,
    cafile: str | None = None,
    minimum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2,
) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = minimum_version
    ctx.options |= ssl.OP_NO_COMPRESSION
    if cafile:
        ctx.load_verify_locations(cafile)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def create_pinned_context(
    *,
    minimum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2,
) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = minimum_version
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def verify_pinned_peer(sock: ssl.SSLSocket, expected_fingerprint: str) -> None:
    der = sock.getpeercert(binary_form=True) or b""
    actual = sha256_of_der(der) if der else ""
    if not expected_fingerprint or actual != normalize_fingerprint(expected_fingerprint):
        raise CertificateChangedError(
            "server certificate does not match the pinned certificate"
        )


def connect_with_trust(
    host: str,
    port: int,
    store: "SslTrustStore",
    *,
    attempt_verified: "Callable[[], T]",
    attempt_pinned: "Callable[[str], T]",
    fetch_cert: "Callable[[], CertificateInfo]",
    prompt: "Callable[[CertificateInfo, list[str], bool], bool]",
) -> "T":
    """Single trust policy shared by the transport fetcher and the tunnel.

    1. If a certificate is pinned for host:port, connect and require an exact
       SHA-256 match of the peer certificate (no system CAs, no name check).
    2. Otherwise (or if the pinned certificate no longer matches) try standard
       verification with system CAs and hostname check.
    3. If that fails, show the certificate to the user; on acceptance pin it
       and connect again requiring an exact match.
    """
    def _pinned() -> str:
        return store.get_fingerprint(host, port) if store.is_trusted(host, port) else ""

    pinned = _pinned()
    if pinned:
        try:
            return attempt_pinned(pinned)
        except CertificateChangedError:
            pass

    try:
        return attempt_verified()
    except ssl.SSLCertVerificationError as exc:
        first_error: ssl.SSLCertVerificationError = exc

    with trust_prompt_lock(host, port):
        current = _pinned()
        if current and current != pinned:
            try:
                return attempt_pinned(current)
            except CertificateChangedError:
                pass
        cert = fetch_cert()
        if not cert.sha256:
            raise first_error
        if not prompt(cert, [str(first_error)], bool(pinned)):
            raise first_error
        store.remember(host, port, cert)
        return attempt_pinned(normalize_fingerprint(cert.sha256))


_prompt_locks: dict[tuple[str, int], threading.Lock] = {}
_prompt_locks_guard = threading.Lock()


@contextlib.contextmanager
def trust_prompt_lock(host: str, port: int) -> Iterator[None]:
    key = SslTrustStore._normalize(host, port)
    with _prompt_locks_guard:
        lock = _prompt_locks.setdefault(key, threading.Lock())
    with lock:
        yield


def default_port_for_scheme(scheme: str) -> int:
    return 443 if (scheme or "").lower() == "https" else 0


def describe_der_certificate(der_bytes: bytes, host: str, port: int) -> CertificateInfo:
    info = CertificateInfo(host=host, port=int(port or 443))
    if not der_bytes:
        return info

    cert = x509.load_der_x509_certificate(der_bytes)
    return _describe_certificate(cert, info)


def describe_pem_certificate(pem_text: str, host: str, port: int) -> CertificateInfo:
    info = CertificateInfo(host=host, port=int(port or 443), pem=pem_text)
    if not pem_text.strip():
        return info

    cert = x509.load_pem_x509_certificate(pem_text.encode("ascii"))
    return _describe_certificate(cert, info)


def _describe_certificate(cert: x509.Certificate, info: CertificateInfo) -> CertificateInfo:
    sha256 = cert.fingerprint(hashes.SHA256()).hex().upper()

    info.subject = cert.subject.rfc4514_string()
    info.issuer = cert.issuer.rfc4514_string()
    info.sha256 = ":".join(sha256[i : i + 2] for i in range(0, len(sha256), 2))
    info.serial_number = format(cert.serial_number, "X")
    info.not_before = cert.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    info.not_after = cert.not_valid_after_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    if not info.pem:
        info.pem = cert.public_bytes(serialization.Encoding.PEM).decode("ascii")

    return info


def fetch_certificate_info(
    host: str,
    port: int,
    *,
    server_hostname: str | None = None,
    timeout: float = 5.0,
    prefix: bytes = b"",
    family: int = 0,
) -> CertificateInfo:
    normalized_port = int(port or 443)
    ctx = create_pinned_context()
    if family:
        raw = socket.socket(family, socket.SOCK_STREAM)
        raw.settimeout(timeout)
        try:
            raw.connect((host, normalized_port))
        except Exception:
            raw.close()
            raise
    else:
        raw = socket.create_connection((host, normalized_port), timeout=timeout)
    try:
        if prefix:
            raw.sendall(prefix)
        with ctx.wrap_socket(raw, server_hostname=server_hostname or host) as tls:
            der = tls.getpeercert(binary_form=True) or b""
    finally:
        raw.close()
    if not der:
        raise ssl.SSLError("server did not present a certificate")
    return describe_der_certificate(der, host=host, port=normalized_port)


def format_certificate_message(
    cert: CertificateInfo,
    errors: list[str] | None = None,
    *,
    changed: bool = False,
) -> str:
    lines: list[str] = []
    if changed:
        lines.extend([
            QCoreApplication.translate(
                "SslTrust",
                "WARNING: the certificate of this server has changed since you trusted it. "
                "This may indicate an interception attempt. Continue only if your administrator "
                "has confirmed the new certificate.",
            ),
            "",
        ])
    lines += [
        QCoreApplication.translate("SslTrust", "Server certificate failed standard verification."),
        "",
        QCoreApplication.translate("SslTrust", "Host:") + f" {cert.host}:{cert.port}",
    ]

    if cert.subject:
        lines.append(f"Subject: {cert.subject}")
    if cert.issuer:
        lines.append(f"Issuer: {cert.issuer}")
    if cert.not_before:
        lines.append(QCoreApplication.translate("SslTrust", "Valid from:") + f" {cert.not_before}")
    if cert.not_after:
        lines.append(QCoreApplication.translate("SslTrust", "Valid until:") + f" {cert.not_after}")
    if cert.sha256:
        lines.append(f"SHA-256: {cert.sha256}")

    if errors:
        lines.append("")
        lines.append(QCoreApplication.translate("SslTrust", "Verification errors:"))
        for item in errors:
            if item:
                lines.append(f"• {item}")

    lines.extend(
        [
            "",
            QCoreApplication.translate("SslTrust", "Trust this certificate for this server?"),
        ]
    )
    return "\n".join(lines)
