from __future__ import annotations

import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography import x509 # type: ignore
from cryptography.hazmat.primitives import hashes # type: ignore
from PySide6.QtCore import QCoreApplication, QSettings # type: ignore


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


class SslTrustStore:
    def __init__(self) -> None:
        self._settings = QSettings("Gorizont-VS", "VDIClient")

    @staticmethod
    def _normalize(host: str, port: int) -> tuple[str, int]:
        normalized_host = (host or "").strip().lower()
        normalized_port = int(port or 443)
        return normalized_host, normalized_port

    def _base_key(self, host: str, port: int) -> str:
        normalized_host, normalized_port = self._normalize(host, port)
        return f"ssl/trusted_certificates/{normalized_host}:{normalized_port}"

    def is_trusted(self, host: str, port: int) -> bool:
        return bool(self._settings.value(f"{self._base_key(host, port)}/trusted", False, type=bool))

    def remember(self, host: str, port: int, cert: CertificateInfo | None = None) -> None:
        base = self._base_key(host, port)
        self._settings.setValue(f"{base}/trusted", True)
        if cert is not None:
            self._settings.setValue(f"{base}/sha256", cert.sha256)
            self._settings.setValue(f"{base}/subject", cert.subject)
            self._settings.setValue(f"{base}/issuer", cert.issuer)
            self._settings.setValue(f"{base}/serial_number", cert.serial_number)
            self._settings.setValue(f"{base}/not_before", cert.not_before)
            self._settings.setValue(f"{base}/not_after", cert.not_after)
        self._settings.setValue(f"{base}/accepted_at", datetime.now(timezone.utc).isoformat())
        self._settings.sync()



def default_port_for_scheme(scheme: str) -> int:
    return 443 if (scheme or "").lower() == "https" else 0



def describe_der_certificate(der_bytes: bytes, host: str, port: int) -> CertificateInfo:
    info = CertificateInfo(host=host, port=int(port or 443))
    if not der_bytes:
        return info

    cert = x509.load_der_x509_certificate(der_bytes)
    sha256 = cert.fingerprint(hashes.SHA256()).hex().upper()
    info.subject = cert.subject.rfc4514_string()
    info.issuer = cert.issuer.rfc4514_string()
    info.sha256 = ":".join(sha256[i : i + 2] for i in range(0, len(sha256), 2))
    info.serial_number = format(cert.serial_number, "X")
    info.not_before = cert.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    info.not_after = cert.not_valid_after_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    return info



def fetch_certificate_info(host: str, port: int, *, server_hostname: str | None = None, timeout: float = 5.0) -> CertificateInfo:
    normalized_port = int(port or 443)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, normalized_port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=server_hostname or host) as ssl_sock:
            der = ssl_sock.getpeercert(binary_form=True)
    return describe_der_certificate(der, host=host, port=normalized_port)



def format_certificate_message(cert: CertificateInfo, errors: list[str] | None = None) -> str:
    lines: list[str] = [
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

    lines.extend([
        "",
        QCoreApplication.translate("SslTrust", "Trust this certificate for this server?"),
    ])
    return "\n".join(lines)
