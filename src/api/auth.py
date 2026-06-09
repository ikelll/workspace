from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QObject, Signal  # type: ignore
from PySide6.QtCore import QUrl

from src.api.client import ApiClient
from src.api import endpoints as ep

if TYPE_CHECKING:
    from src.auth.negotiate import NegotiateClient

log = logging.getLogger(__name__)


class AuthService(QObject):

    authenticators_ready = Signal(list) 
    auth_error = Signal(str)
    login_success = Signal(str, str)  # token, username
    login_error = Signal(str) 
    logged_out = Signal()

    def __init__(self, client: ApiClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._token: str = ""
        self._scrambler: str = ""
        self._username: str = ""
        self._negotiate_client: NegotiateClient | None = None

    @property
    def token(self) -> str:
        return self._token

    @property
    def scrambler(self) -> str:
        return self._scrambler

    @property
    def username(self) -> str:
        return self._username

    @property
    def is_authenticated(self) -> bool:
        return bool(self._token)

    def fetch_authenticators(self, server_url: str) -> None:
        self._client.set_base_url(server_url)
        self._client.clear_token()

        self._client.get(
            ep.AUTH_AUTHS,
            on_success=self._on_auths_ok,
            on_error=self._on_auths_fail,
        )

    def login(self, auth_id: str, username: str, password: str) -> None:
        self._username = username.strip()

        import sys
        if sys.platform == "darwin":
            platform = "MacOsX"
        elif sys.platform == "win32":
            platform = "Windows"
        else:
            platform = "Linux"

        body = {
            "auth_id": auth_id,
            "username": username,
            "password": password,
            "platform": platform,
        }
        self._client.post(
            ep.AUTH_LOGIN,
            body=body,
            on_success=self._on_login_ok,
            on_error=self._on_login_fail,
        )
    
    def login_negotiate(self, auth_id: str, spn: str = "") -> None:
        try:
            from src.auth.negotiate import NegotiateClient
        except Exception:
            log.exception("Negotiate backend is unavailable")
            self.login_error.emit("Negotiate/Kerberos недоступен в этой сборке")
            return

        log.info(
            "Starting negotiate login: auth_id=%s spn=%s base_url=%s",
            auth_id,
            spn,
            self._client.base_url,
        )

        url = QUrl(self._client.base_url)
        host = url.host().strip()
        service = "HTTP"

        if spn and "/" in spn:
            service_part, host_part = spn.split("/", 1)
            service = service_part or "HTTP"
            if host_part.strip():
                host = host_part.strip()

        if not host:
            self.login_error.emit("Broker host is empty")
            return

        self._negotiate_client = NegotiateClient(hostname=host, service=service)

        import sys
        if sys.platform == "darwin":
            platform = "MacOsX"
        elif sys.platform == "win32":
            platform = "Windows"
        else:
            platform = "Linux"

        self._run_negotiate_step(auth_id, "", "", platform)

    def logout(self) -> None:
        if not self._token:
            self.logged_out.emit()
            return

        def _done(data: Any) -> None:
            self._clear()
            self.logged_out.emit()

        def _fail(msg: str, code: int) -> None:
            log.warning("Logout request failed (ignoring): %s", msg)
            self._clear()
            self.logged_out.emit()

        self._client.get(ep.AUTH_LOGOUT, on_success=_done, on_error=_fail)

    def clear_session(self) -> None:
        self._clear()
        
    def _run_negotiate_step(
        self,
        auth_id: str,
        context_id: str,
        in_token_b64: str,
        platform: str,
    ) -> None:
        if self._negotiate_client is None:
            self.login_error.emit("Negotiate client is not initialized")
            return

        out_token_b64, _complete = self._negotiate_client.step(in_token_b64)
        
        log.debug(
            "Negotiate step: auth_id=%s context_id=%s in_token_len=%d out_token_len=%d",
            auth_id,
            context_id,
            len(in_token_b64 or ""),
            len(out_token_b64 or ""),
        )

        self._client.post(
            ep.AUTH_LOGIN_NEGOTIATE,
            body={
                "auth_id": auth_id,
                "context_id": context_id,
                "out_token_b64": out_token_b64,
                "platform": platform,
            },
            on_success=lambda data: self._on_login_negotiate_ok(data, auth_id, platform),
            on_error=self._on_login_fail,
        )

    def _on_login_negotiate_ok(self, data: Any, auth_id: str, platform: str) -> None:
        log.debug("Negotiate response: %s", data)
        if not isinstance(data, dict):
            self.login_error.emit("Unexpected server response")
            return

        result = str(data.get("result", ""))

        if result == "continue":
            self._run_negotiate_step(
                auth_id=auth_id,
                context_id=str(data.get("context_id", "")),
                in_token_b64=str(data.get("in_token_b64", "")),
                platform=platform,
            )
            return

        if self._negotiate_client is not None:
            principal = self._negotiate_client.initiator_name
            if principal:
                self._username = principal.split("@")[0] if "@" in principal else principal
                log.info("Negotiate principal: %s (display: %s)", principal, self._username)

        server_username = str(data.get("username", "")).strip()
        if server_username:
            self._username = server_username

        self._on_login_ok(data)

    def _on_auths_ok(self, data: Any) -> None:
        auths: list[dict] = []

        items = data if isinstance(data, list) else data.get("result", [])

        for item in items:
            if not isinstance(item, dict):
                continue
            auth_id = str(item.get("auth_id", item.get("authId", "")))
            name = str(item.get("auth", ""))
            if not name:
                name = str(item.get("auth_label", item.get("authLabel", auth_id)))
            if auth_id:
                auths.append({
                    "id": auth_id,
                    "name": name,
                    "type": str(item.get("type", "")),
                    "login_methods": list(item.get("login_methods", ["password"])),
                    "preferred_method": str(item.get("preferred_method", "password")),
                    "realm": str(item.get("realm", "")),
                    "spn": str(item.get("spn", "")),
                    "x509": item.get("x509", {"enabled": False}),
                })

        if not auths:
            log.warning("Server returned no authenticators: %s", data)
            self.auth_error.emit(QCoreApplication.translate("AuthService", "Server returned no authenticators"))
            return

        log.info("Fetched %d authenticator(s): %s", len(auths), auths)
        self.authenticators_ready.emit(auths)

    def _on_auths_fail(self, msg: str, code: int) -> None:
        log.warning("Failed to fetch authenticators: %s (status=%d)", msg, code)
        self.auth_error.emit(msg)

    def _on_login_ok(self, data: Any) -> None:
        if not isinstance(data, dict):
            log.warning("Unexpected login response type: %s", type(data))
            self.login_error.emit(QCoreApplication.translate("AuthService", "Unexpected server response"))
            return
        self._negotiate_client = None

        result = data.get("result", "")

        if result != "ok":
            error_msg = data.get("error", QCoreApplication.translate("AuthService", "Invalid username or password"))
            log.warning("Login rejected by server: %s", error_msg)
            self.login_error.emit(str(error_msg))
            return
        
        token = str(data.get("token", ""))
        if not token:
            log.warning("Login response has result=ok but no token: %s", data)
            self.login_error.emit(QCoreApplication.translate("AuthService", "Server did not return an authorization token"))
            return

        server_user = str(data.get("username", "")).strip()
        if server_user and not self._username:
            self._username = server_user

        self._token = token
        self._scrambler = str(data.get("scrambler", ""))
        self._client.set_token(token)
        self._client.set_scrambler(self._scrambler)
        log.info("Login successful, token=<REDACTED> (len=%d)", len(token))
        self.login_success.emit(token, self._username)

    def _on_login_fail(self, msg: str, code: int) -> None:
        if code == 401 or code == 403:
            msg = QCoreApplication.translate("AuthService", "Invalid username or password")
        log.warning("Login failed: %s (status=%d)", msg, code)
        self._negotiate_client = None
        self.login_error.emit(msg)

    def _clear(self) -> None:
        self._token = ""
        self._scrambler = ""
        self._username = ""
        self._client.clear_token()
        self._negotiate_client = None