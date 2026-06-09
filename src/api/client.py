from __future__ import annotations

import json
import logging
import typing
from typing import Callable, Optional, Union

from PySide6.QtCore import QByteArray, QCoreApplication, QObject, QUrl, QUrlQuery # type: ignore
from PySide6.QtNetwork import ( # type: ignore
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
    QSslConfiguration,
    QSslError,
    QSslSocket,
)

from src.api.endpoints import HEADER_AUTH_TOKEN, HEADER_CONTENT_TYPE, USER_AGENT  # noqa: F401
from src.dialogs.app_dialogs import confirm_certificate
from src.ssl_trust import SslTrustStore, default_port_for_scheme, describe_der_certificate

from PySide6 import __version_info__ as _pyside_version_info

log = logging.getLogger(__name__)

SuccessCb = Callable[[Union[dict, list, str]], None]
BinarySuccessCb = Callable[[bytes, str], None]
ErrorCb = Callable[[str, int], None]

_PYSIDE_NEW_HEADER_API = _pyside_version_info >= (6, 5, 0)

def _raw_header(reply: QNetworkReply, name: str) -> str:
    if _PYSIDE_NEW_HEADER_API:
        return reply.rawHeader(name)
    return bytes(reply.rawHeader(name.encode())).decode("utf-8", errors="replace")

class ApiClient(QObject):

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._base_url: str = ""
        self._token: str = ""
        self._scrambler: str = ""
        self._ignore_ssl: bool = False
        self._timeout_ms: int = 15_000
        self._ssl_dialog_parent: QObject | None = None
        self._ssl_trust_store = SslTrustStore()

    def set_base_url(self, url: str) -> None:
        self._base_url = url.rstrip("/")

    @property
    def base_url(self) -> str:
        return self._base_url

    def set_token(self, token: str) -> None:
        self._token = token

    def set_scrambler(self, scrambler: str) -> None:
        self._scrambler = scrambler

    def clear_token(self) -> None:
        self._token = ""
        self._scrambler = ""

    @property
    def has_token(self) -> bool:
        return bool(self._token)

    def set_ignore_ssl_errors(self, ignore: bool) -> None:
        self._ignore_ssl = ignore

    def set_timeout(self, ms: int) -> None:
        self._timeout_ms = ms

    def set_ssl_dialog_parent(self, parent: QObject | None) -> None:
        self._ssl_dialog_parent = parent

    def get(
        self,
        path: str,
        on_success: SuccessCb,
        on_error: ErrorCb,
        *,
        params: dict[str, str] | None = None,
    ) -> None:
        url = self._build_url(path, params)
        request = self._build_request(url)
        reply = self._nam.get(request)
        self._connect_reply(reply, on_success, on_error)

    def get_bytes(
        self,
        path: str,
        on_success: BinarySuccessCb,
        on_error: ErrorCb,
        *,
        params: dict[str, str] | None = None,
    ) -> None:
        url = self._build_url(path, params)
        request = self._build_request(url)
        log.debug(
            "HTTP GET(bytes) %s headers={User-Agent=%r, %s=%r, Scrambler=%r}",
            url.toString(),
            USER_AGENT,
            HEADER_AUTH_TOKEN,
            bool(self._token),
            bool(self._scrambler),
        )
        reply = self._nam.get(request)
        self._connect_binary_reply(reply, on_success, on_error)

    def post(
        self,
        path: str,
        body: dict | None,
        on_success: SuccessCb,
        on_error: ErrorCb,
    ) -> None:
        url = self._build_url(path)
        request = self._build_request(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/json",
        )
        data = QByteArray(json.dumps(body or {}).encode("utf-8"))
        reply = self._nam.post(request, data)
        self._connect_reply(reply, on_success, on_error)

    def put(
        self,
        path: str,
        body: dict | None,
        on_success: SuccessCb,
        on_error: ErrorCb,
    ) -> None:
        url = self._build_url(path)
        request = self._build_request(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/json",
        )
        data = QByteArray(json.dumps(body or {}).encode("utf-8"))
        reply = self._nam.put(request, data)
        self._connect_reply(reply, on_success, on_error)

    def delete(
        self,
        path: str,
        on_success: SuccessCb,
        on_error: ErrorCb,
    ) -> None:
        url = self._build_url(path)
        request = self._build_request(url)
        reply = self._nam.deleteResource(request)
        self._connect_reply(reply, on_success, on_error)

    def _build_url(self, path: str, params: dict[str, str] | None = None) -> QUrl:
        url = QUrl(self._base_url + path)
        if params:
            query = QUrlQuery()
            for k, v in params.items():
                query.addQueryItem(k, v)
            url.setQuery(query)
        return url

    def _build_request(self, url: QUrl) -> QNetworkRequest:
        request = QNetworkRequest(url)

        request.setRawHeader(
            QByteArray(b"User-Agent"),
            QByteArray(USER_AGENT.encode("utf-8")),
        )

        if self._token:
            request.setRawHeader(
                QByteArray(HEADER_AUTH_TOKEN.encode()),
                QByteArray(self._token.encode()),
            )

        if self._scrambler:
            request.setRawHeader(
                QByteArray(b"Scrambler"),
                QByteArray(self._scrambler.encode()),
            )

        request.setTransferTimeout(self._timeout_ms)

        port = url.port(default_port_for_scheme(url.scheme()))
        if self._ignore_ssl or self._ssl_trust_store.is_trusted(url.host(), port):
            ssl_cfg = QSslConfiguration.defaultConfiguration()
            ssl_cfg.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyNone)
            request.setSslConfiguration(ssl_cfg)

        return request

    def _connect_reply(
        self,
        reply: QNetworkReply,
        on_success: SuccessCb,
        on_error: ErrorCb,
    ) -> None:

        reply.sslErrors.connect(lambda errors: self._handle_ssl_errors(reply, errors))

        def _on_finished():
            try:
                self._handle_reply(reply, on_success, on_error)
            finally:
                reply.deleteLater()

        reply.finished.connect(_on_finished)

    def _connect_binary_reply(
        self,
        reply: QNetworkReply,
        on_success: BinarySuccessCb,
        on_error: ErrorCb,
    ) -> None:

        reply.sslErrors.connect(lambda errors: self._handle_ssl_errors(reply, errors))

        def _on_finished():
            try:
                self._handle_binary_reply(reply, on_success, on_error)
            finally:
                reply.deleteLater()

        reply.finished.connect(_on_finished)


    def _handle_ssl_errors(self, reply: QNetworkReply, errors: list[QSslError]) -> None:
        url = reply.url()
        host = url.host()
        port = url.port(default_port_for_scheme(url.scheme()))

        if self._ignore_ssl or self._ssl_trust_store.is_trusted(host, port):
            reply.ignoreSslErrors()
            return

        cert = None
        if errors:
            cert = errors[0].certificate()

        cert_info = describe_der_certificate(
            bytes(cert.toDer()) if cert is not None and not cert.isNull() else b"",
            host=host,
            port=port,
        )
        should_trust = confirm_certificate(
            typing.cast(Optional[QObject], self._ssl_dialog_parent),
            cert=cert_info,
            errors=[err.errorString() for err in errors],
        )
        if should_trust:
            self._ssl_trust_store.remember(host, port, cert_info)
            reply.ignoreSslErrors()

    def _handle_reply(
        self,
        reply: QNetworkReply,
        on_success: SuccessCb,
        on_error: ErrorCb,
    ) -> None:
        status, raw = self._consume_reply_bytes(reply, on_error)
        if raw is None:
            return
    
        if not raw:
            on_success({})
            return

        try:
            data = json.loads(raw.decode("utf-8"))
            on_success(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            log.warning("Failed to parse response: %s", exc)
            on_success(raw.decode("utf-8", errors="replace"))

    def _handle_binary_reply(
        self,
        reply: QNetworkReply,
        on_success: BinarySuccessCb,
        on_error: ErrorCb,
    ) -> None:
        _status, raw = self._consume_reply_bytes(reply, on_error)
        if raw is None:
            return

        content_type = _raw_header(reply, "Content-Type")
        log.debug(
            "HTTP binary success: status=%d url=%s content_type=%r bytes=%d",
            _status,
            reply.url().toString(),
            content_type,
            len(raw),
        )
        on_success(raw, content_type)

    def _consume_reply_bytes(
        self,
        reply: QNetworkReply,
        on_error: ErrorCb,
    ) -> tuple[int, bytes | None]:
        error = reply.error()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        status = int(status) if status is not None else 0

        if error != QNetworkReply.NetworkError.NoError:
            msg = reply.errorString()
            log.warning(
                "HTTP error: %s (status=%d, url=%s)",
                msg,
                status,
                reply.url().toString(),
            )

            if error == QNetworkReply.NetworkError.HostNotFoundError:
                msg = QCoreApplication.translate("ApiClient", "Server not found. Check the address.")
            elif error == QNetworkReply.NetworkError.ConnectionRefusedError:
                msg = QCoreApplication.translate("ApiClient", "Connection refused by server.")
            elif error == QNetworkReply.NetworkError.TimeoutError:
                msg = QCoreApplication.translate("ApiClient", "Request timed out.")
            elif error in (QNetworkReply.NetworkError.SslHandshakeFailedError,):
                msg = QCoreApplication.translate("ApiClient", "SSL certificate error. Check security settings.")

            on_error(msg, status)
            return status, None

        raw = bytes(reply.readAll().data())

        if status >= 400:
            try:
                data = json.loads(raw.decode("utf-8"))
                msg = data.get(
                    "error", data.get("detail", data.get("message", str(data)))
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                msg = f"HTTP {status}"

            log.warning("HTTP %d: %s (url=%s)", status, msg, reply.url().toString())
            on_error(msg, status)
            return status, None

        log.debug(
            "HTTP success: status=%d url=%s bytes=%d content_type=%r",
            status,
            reply.url().toString(),
            len(raw),
            _raw_header(reply, "Content-Type")
        )
        return status, raw