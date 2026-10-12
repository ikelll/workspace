from __future__ import annotations

import datetime
import ipaddress
import logging
import platform
import sys
import threading
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, QSettings, QTimer, Property, Signal, Slot  # type: ignore

from src.api.auth import AuthService
from src.api.client import ApiClient
from src.api.error_messages import translate_server_message
from src.api.services import ServiceInfo, ServicesAPI
from src.infrastructure.i18n_manager import I18nManager
from src.profile_manager import Profile, ProfileManager, avatar_color
from src.qmlui.catalog import FavoritesStore, services_to_list
from src.qmlui.images import ServiceImageStore
from src.qmlui.prompts import QmlPrompter
from src.transport import tools as tools_mod
from src.transport import tunnel as tunnel_mod
from src.transport.executor import TransportExecutor
from src.transport_settings import SpiceSettings, TransportSettingsStore
from src.utils.profile_token import ProfileTokenError, decode_profile_token, looks_like_profile_token
from src.utils.version import APP_VERSION

log = logging.getLogger(__name__)

SERVICES_REFRESH_MS = 30_000
RETRY_DELAY_MS = 3_000



class ClientController(QObject):
    changed = Signal()
    notify = Signal(str, str)
    servicesChanged = Signal()
    settingsChanged = Signal()
    languageChanged = Signal()

    def __init__(self, settings: QSettings, api: ApiClient, images: ServiceImageStore, prompter: QmlPrompter,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._api = api
        self._images = images
        self._prompter = prompter
        self._auth = AuthService(api, parent=self)
        self._services_api = ServicesAPI(api, parent=self)
        self._transport = TransportExecutor(parent=self)
        self._profiles = ProfileManager(settings)
        self._transport_settings = TransportSettingsStore(settings)
        self._favorites = FavoritesStore(settings)
        self._i18n = I18nManager(settings, parent=self)

        self._screen = "login"
        self._login_page = "server"
        self._login_error = ""
        self._login_busy = False
        self._server_url = ""
        self._authenticators: list[dict[str, Any]] = []
        self._selected_auth = ""
        self._current_profile: Profile | None = None
        self._mfa: dict[str, Any] = {}
        self._mfa_origin = ""
        self._pending_username = ""
        self._pending_last_login = ""
        self._login_source = ""
        self._typed_user = ""
        self._typed_pass_used = False

        self._loading_text = ""
        self._loading_error = ""
        self._initial_load = False
        self._pending_services: list[ServiceInfo] = []
        self._services: list[dict[str, Any]] = []
        self._raw_services: dict[str, ServiceInfo] = {}
        self._services_busy = False
        self._refresh_silent = False
        self._pending_launch: tuple[ServiceInfo, Any] | None = None
        self._connecting = False
        self._connecting_service_id = ""
        self._retry_timer: QTimer | None = None
        self._theme = str(settings.value("ui/theme", "light") or "light")

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(SERVICES_REFRESH_MS)
        self._refresh_timer.timeout.connect(lambda: self.refreshServices(True))

        self._images.changed.connect(self.changed)
        self._connect_signals()

    def _connect_signals(self) -> None:
        self._auth.authenticators_ready.connect(self._on_authenticators)
        self._auth.auth_error.connect(self._on_auth_fetch_failed)
        self._auth.login_success.connect(self._on_login_success)
        self._auth.login_error.connect(self._on_login_failed)
        self._auth.mfa_required.connect(self._on_mfa_required)
        self._auth.logged_out.connect(self._on_logged_out)
        self._services_api.services_ready.connect(self._on_services_ready)
        self._services_api.services_error.connect(self._on_services_error)
        self._services_api.connect_error.connect(self._on_connect_error)
        self._services_api.session_expired.connect(self._on_session_expired)
        self._services_api.action_done.connect(self._on_action_done)
        self._transport.launch_started.connect(self._on_transport_started)
        self._transport.launch_ok.connect(self._on_transport_ok)
        self._transport.launch_error.connect(self._on_transport_error)
        self._transport.launch_retry.connect(self._on_transport_retry)
        self._transport.launch_finished.connect(self._on_transport_finished)
        self._i18n.language_changed.connect(self._on_language_changed)

    @Property(str, notify=changed)
    def screen(self) -> str:
        return self._screen

    @Property(str, notify=changed)
    def loginPage(self) -> str:
        return self._login_page

    @Property(str, notify=changed)
    def loginError(self) -> str:
        return self._login_error

    @Property(bool, notify=changed)
    def loginBusy(self) -> bool:
        return self._login_busy

    @Property(str, notify=changed)
    def serverUrl(self) -> str:
        return self._server_url

    @Property(str, notify=changed)
    def serverHost(self) -> str:
        return self._host_of(self._server_url)

    @Property("QVariantList", notify=changed)
    def authenticators(self) -> list[dict[str, Any]]:
        return [
            {
                "id": a["id"],
                "name": a["name"],
                "negotiate": "negotiate" in a.get("login_methods", []),
                "preferredNegotiate": a.get("preferred_method") == "negotiate",
            }
            for a in self._authenticators
        ]

    @Property(str, notify=changed)
    def selectedAuthenticator(self) -> str:
        return self._selected_auth

    @Property(bool, notify=changed)
    def negotiateAvailable(self) -> bool:
        return "negotiate" in self._auth_meta().get("login_methods", [])

    @Property(bool, notify=changed)
    def negotiatePreferred(self) -> bool:
        meta = self._auth_meta()
        return "negotiate" in meta.get("login_methods", []) and meta.get("preferred_method") == "negotiate"

    @Property("QVariantList", notify=changed)
    def profiles(self) -> list[dict[str, Any]]:
        profiles = self._profiles.load_all()
        last_id = self._profiles.get_last_used_id()
        profiles.sort(key=lambda p: p.id != last_id)
        return [self._profile_dict(p, last_id) for p in profiles]

    @Property("QVariantMap", notify=changed)
    def currentProfile(self) -> dict[str, Any]:
        if self._current_profile is None:
            return {}
        return self._profile_dict(self._current_profile, self._profiles.get_last_used_id())

    @Property(bool, notify=changed)
    def hasProfiles(self) -> bool:
        return bool(self._profiles.load_all())

    @Property("QVariantMap", notify=changed)
    def mfa(self) -> dict[str, Any]:
        return dict(self._mfa)

    @Property(str, notify=changed)
    def loadingText(self) -> str:
        return self._loading_text

    @Property(str, notify=changed)
    def loadingError(self) -> str:
        return self._loading_error

    @Property(bool, notify=changed)
    def authenticated(self) -> bool:
        return self._auth.is_authenticated

    @Property(str, notify=changed)
    def username(self) -> str:
        return self._pending_username or self._auth.username

    @Property(str, notify=changed)
    def displayName(self) -> str:
        name = (self._pending_username or self._auth.username or "").strip()
        base = name.split("@", 1)[0]
        parts = [p for p in base.replace(".", " ").replace("_", " ").split() if p]
        return " ".join(p[:1].upper() + p[1:] for p in parts) if parts else name

    @Property(str, notify=changed)
    def initials(self) -> str:
        name = self.displayName
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:1].upper() if name else "?"

    @Property(str, notify=changed)
    def avatarColor(self) -> str:
        if self._current_profile is not None:
            return avatar_color(self._current_profile)
        return "#047394"

    @Property(str, notify=changed)
    def lastLogin(self) -> str:
        return self._format_last_login(self._pending_last_login) if self._pending_last_login else ""

    @Property("QVariantList", notify=servicesChanged)
    def services(self) -> list[dict[str, Any]]:
        return list(self._services)

    @Property(bool, notify=changed)
    def servicesBusy(self) -> bool:
        return self._services_busy

    @Property(bool, notify=changed)
    def connecting(self) -> bool:
        return self._connecting or self._transport.is_running

    @Property(str, notify=changed)
    def connectingServiceId(self) -> str:
        return self._connecting_service_id if self.connecting else ""

    @Property(int, notify=changed)
    def imageVersion(self) -> int:
        return self._images.version

    @Slot(str, int, result=bool)
    def imageAvailable(self, image_id: str, _version: int) -> bool:
        return self._images.has(image_id)

    @Property(str, notify=changed)
    def theme(self) -> str:
        return self._theme

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._i18n.current

    @Property("QVariantMap", notify=settingsChanged)
    def spiceSettings(self) -> dict[str, Any]:
        profile_id = self._current_profile.id if self._current_profile else ""
        value = self._transport_settings.load_spice(profile_id) if profile_id else SpiceSettings()
        return {
            "available": bool(profile_id),
            "multiMonitorEnabled": value.multi_monitor_enabled,
            "monitorCount": value.monitor_count,
            "webdavEnabled": value.webdav_enabled,
            "webdavPath": value.webdav_path,
        }

    @Property("QVariantMap", constant=True)
    def about(self) -> dict[str, Any]:
        import PySide6  # type: ignore
        from PySide6.QtCore import qVersion  # type: ignore
        from src.infrastructure.logging_setup import log_file_path
        from src.utils import consts
        return {
            "version": APP_VERSION,
            "platform": f"{platform.system()} {platform.release()}",
            "python": sys.version.split()[0],
            "qt": f"Qt {qVersion()} · PySide6 {PySide6.__version__}",
            "userAgent": consts.USER_AGENT,
            "logFile": log_file_path(),
        }

    @staticmethod
    def _host_of(url: str) -> str:
        return url.split("://", 1)[-1].rstrip("/").split("/", 1)[0]

    def _profile_dict(self, p: Profile, last_id: str | None) -> dict[str, Any]:
        return {
            "id": p.id, "username": p.username, "host": p.host, "serverUrl": p.server_url,
            "authName": p.auth_name, "authId": p.auth_id, "initials": p.initials, "color": avatar_color(p),
            "negotiate": p.is_negotiate, "isLast": p.id == last_id, "label": p.display_label,
        }

    def _auth_meta(self) -> dict[str, Any]:
        for a in self._authenticators:
            if a["id"] == self._selected_auth:
                return a
        return {}

    def _set_screen(self, screen: str) -> None:
        self._screen = screen
        self.changed.emit()

    def _set_login_page(self, page: str, error: str = "") -> None:
        self._login_page = page
        self._login_error = error
        self._login_busy = False
        self._screen = "login"
        self.changed.emit()

    def _show_loading(self, text: str) -> None:
        self._loading_text = text
        self._loading_error = ""
        self._screen = "loading"
        self.changed.emit()

    def _show_loading_error(self, text: str) -> None:
        self._loading_error = text
        self._screen = "loading"
        self.changed.emit()

    @staticmethod
    def _format_last_login(raw: str) -> str:
        try:
            parsed = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone()
            return parsed.strftime("%d.%m.%Y %H:%M")
        except Exception:  # noqa: BLE001
            return raw

    @Slot()
    def start(self) -> None:
        self._login_error = ""
        profiles = self._profiles.load_all()
        if not profiles:
            self._current_profile = None
            self._set_login_page("server")
            return
        last_id = self._profiles.get_last_used_id()
        match = next((p for p in profiles if p.id == last_id), None) if last_id else None
        if len(profiles) == 1:
            self._current_profile = profiles[0]
            self._set_login_page("password")
        elif match is not None:
            self._current_profile = match
            self._set_login_page("password")
        else:
            self._set_login_page("profiles")

    @Slot()
    def showProfiles(self) -> None:
        self._set_login_page("profiles")

    @Slot()
    def addConnection(self) -> None:
        self._server_url = ""
        self._set_login_page("server")

    @Slot(str)
    def selectProfile(self, profile_id: str) -> None:
        profile = next((p for p in self._profiles.load_all() if p.id == profile_id), None)
        if profile is None:
            return
        self._current_profile = profile
        self._profiles.set_last_used(profile.id)
        self._set_login_page("password")

    @Slot(str, result=bool)
    def deleteProfile(self, profile_id: str) -> bool:
        profile = next((p for p in self._profiles.load_all() if p.id == profile_id), None)
        if profile is None:
            return False
        self._profiles.delete(profile.id)
        self._transport_settings.remove_profile(profile.id)
        if self._current_profile is not None and self._current_profile.id == profile.id:
            self._current_profile = None
        self.start()
        return True

    @Slot()
    def backToServer(self) -> None:
        self._set_login_page("server")

    @Slot(str)
    def connectServer(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            self._set_login_page("server", QCoreApplication.translate("ClientController", "Enter the server address or connection code."))
            return
        if looks_like_profile_token(text):
            self._apply_profile_token(text)
            return
        url = text.rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not self._confirm_insecure_url(url):
            self._set_login_page("server")
            return
        self._server_url = url
        self._login_error = ""
        self._login_busy = True
        self.changed.emit()
        log.info("Fetching authenticators from %s", url)
        self._auth.fetch_authenticators(url)

    @staticmethod
    def _is_insecure_url(url: str) -> bool:
        if not url.lower().startswith("http://"):
            return False
        host = url.split("://", 1)[1].split("/", 1)[0]
        if host.startswith("["):
            host = host[1:].split("]", 1)[0]
        else:
            host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
        if host.lower() == "localhost":
            return False
        try:
            return not ipaddress.ip_address(host).is_loopback
        except ValueError:
            return True

    def _confirm_insecure_url(self, url: str) -> bool:
        if not self._is_insecure_url(url):
            return True
        log.warning("Insecure (http) broker address requested: %s", self._host_of(url))
        return bool(self._prompter.ask(
            "danger",
            QCoreApplication.translate("ClientController", "Insecure connection"),
            QCoreApplication.translate(
                "ClientController",
                "The server address uses HTTP without encryption. Your password and session "
                "data can be intercepted on the network.\n\nContinue only if your administrator "
                "has instructed you to use this address.",
            ),
            QCoreApplication.translate("ClientController", "Continue"),
            QCoreApplication.translate("ClientController", "Cancel"),
        ))

    def _apply_profile_token(self, text: str) -> None:
        try:
            data = decode_profile_token(text)
        except ProfileTokenError as exc:
            if getattr(exc, "code", "") == "version":
                message = QCoreApplication.translate("ClientController", "This connection code was created by a newer server version. Please update the application.")
            else:
                message = QCoreApplication.translate("ClientController", "The connection code is invalid or was not copied completely. Request a new one from your administrator.")
            self._set_login_page("server", message)
            return
        if not self._confirm_insecure_url(data.server_url):
            self._set_login_page("server")
            return
        existing = self._profiles.find_by_connection(data.server_url, data.auth_id, data.username)
        if existing:
            existing.server_url = data.server_url
            existing.auth_name = data.auth_name or existing.auth_name
            existing.username = data.username or existing.username
            existing.login_method = data.login_method
            existing.spn = data.spn
            profile = existing
        else:
            profile = Profile(server_url=data.server_url, auth_id=data.auth_id, auth_name=data.auth_name,
                              username=data.username, login_method=data.login_method, spn=data.spn)
        self._profiles.add_or_update(profile)
        self._current_profile = profile
        self._server_url = ""
        self._set_login_page("password")

    def _on_authenticators(self, auths: list[dict]) -> None:
        self._authenticators = list(auths)
        self._selected_auth = auths[0]["id"] if auths else ""
        self._set_login_page("credentials")

    def _on_auth_fetch_failed(self, message: str) -> None:
        self._set_login_page("server", message)

    @Slot(str)
    def selectAuthenticator(self, auth_id: str) -> None:
        self._selected_auth = auth_id
        self.changed.emit()

    @Slot(str, str)
    def loginWithCredentials(self, username: str, password: str) -> None:
        meta = self._auth_meta()
        auth_id = str(meta.get("id", ""))
        methods = meta.get("login_methods", [])
        username = (username or "").strip()
        if not auth_id:
            self._set_login_page("credentials", QCoreApplication.translate("ClientController", "Select an authenticator."))
            return
        self._login_source = "credentials"
        self._typed_user = username
        self._typed_pass_used = bool(password)
        if "negotiate" in methods and not username and not password:
            self._begin_login(QCoreApplication.translate("ClientController", "Signing in…"))
            self._auth.login_negotiate(auth_id, str(meta.get("spn", "")))
            return
        if not username or not password:
            hint = (QCoreApplication.translate("ClientController", "Enter username and password, or leave both fields empty for automatic sign-in.")
                    if "negotiate" in methods else QCoreApplication.translate("ClientController", "Enter the username and password."))
            self._set_login_page("credentials", hint)
            return
        self._pending_username = username
        self._begin_login(QCoreApplication.translate("ClientController", "Signing in…"))
        self._api.set_base_url(self._server_url)
        self._auth.login(auth_id, username, password)

    @Slot(str)
    def loginWithProfile(self, password: str) -> None:
        profile = self._current_profile
        if profile is None:
            self._set_login_page("server")
            return
        self._login_source = "profile"
        self._api.set_base_url(profile.server_url)
        self._server_url = profile.server_url
        if profile.is_negotiate:
            self._pending_username = profile.username
            self._begin_login(QCoreApplication.translate("ClientController", "Signing in…"))
            self._auth.login_negotiate(profile.auth_id, profile.spn)
            return
        if not password:
            self._set_login_page("password", QCoreApplication.translate("ClientController", "Enter the password."))
            return
        self._pending_username = profile.username
        self._begin_login(QCoreApplication.translate("ClientController", "Signing in…"))
        self._auth.login(profile.auth_id, profile.username, password)

    def _begin_login(self, text: str) -> None:
        self._login_busy = True
        self._login_error = ""
        self._initial_load = False
        self._show_loading(text)

    def _on_login_failed(self, message: str) -> None:
        log.warning("Login failed: %s", message)
        self._refresh_timer.stop()
        self._initial_load = False
        if self._mfa:
            page = "mfaVerify"
        elif self._login_source == "credentials":
            page = "credentials"
        elif self._current_profile is not None:
            page = "password"
        else:
            page = "server"
        self._set_login_page(page, message)

    def _on_login_success(self, token: str, username: str, last_login: str = "") -> None:
        del token
        self._pending_last_login = (last_login or "").strip()
        if username:
            self._pending_username = username
        self._save_profile_after_login(username)
        self._mfa = {}
        self._mfa_origin = ""
        self._initial_load = True
        self._pending_services = []
        self.settingsChanged.emit()
        self._show_loading(QCoreApplication.translate("ClientController", "Loading workspace…"))
        self._services_api.fetch_services()

    def _save_profile_after_login(self, username: str) -> None:
        if self._login_source == "credentials":
            meta = self._auth_meta()
            login_method = "negotiate" if (not self._typed_user and not self._typed_pass_used
                                            and "negotiate" in meta.get("login_methods", [])) else "password"
            effective = self._typed_user or username
            existing = self._profiles.find_by_connection(self._server_url, self._selected_auth, effective)
            if existing:
                existing.auth_name = str(meta.get("name", "")) or existing.auth_name
                existing.username = effective or existing.username
                existing.login_method = login_method
                existing.spn = str(meta.get("spn", ""))
                profile = existing
            else:
                profile = Profile(server_url=self._server_url, auth_id=self._selected_auth,
                                  auth_name=str(meta.get("name", "")), username=effective,
                                  login_method=login_method, spn=str(meta.get("spn", "")))
            self._profiles.add_or_update(profile)
            self._current_profile = profile
            self._profiles.set_last_used(profile.id)
        elif self._current_profile is not None:
            if username and not self._current_profile.username:
                self._current_profile.username = username
                self._profiles.add_or_update(self._current_profile)
            self._profiles.set_last_used(self._current_profile.id)

    def _on_mfa_required(self, payload: dict) -> None:
        log.info("MFA required (keys=%s)", sorted(payload.keys()))
        token = str(payload.get("mfa_token", "") or "").strip()
        if not token:
            self._on_login_failed(QCoreApplication.translate("ClientController", "Server did not return an MFA challenge token."))
            return
        html = str(payload.get("html", "") or "")
        message = str(payload.get("message", "") or "").strip() or self._plain_text(html)
        qr_image = self._image_data_url(str(payload.get("qr_image", "") or "").strip() or self._extract_qr(html))
        self._mfa = {
            "token": token,
            "label": str(payload.get("label", "") or "").strip(),
            "message": self._translate_mfa_message(message),
            "qrImage": qr_image,
            "remember": bool(payload.get("remember_device", payload.get("rememberDevice", True))),
        }
        self._mfa_origin = self._login_source
        self._set_login_page("mfaSetup" if qr_image else "mfaVerify")

    @staticmethod
    def _plain_text(html: str) -> str:
        import html as html_lib
        import re
        text = re.sub(r"<img[^>]*>", " ", html, flags=re.I)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        return " ".join(html_lib.unescape(text).split())

    @staticmethod
    def _extract_qr(html: str) -> str:
        import re
        match = re.search(r"data:image/[a-z+.-]+;base64,[A-Za-z0-9+/=\s]+", html, flags=re.I)
        return re.sub(r"\s+", "", match.group(0)) if match else ""

    @staticmethod
    def _image_data_url(value: str) -> str:
        import base64
        import binascii
        value = (value or "").strip()
        if not value or value.lower().startswith("data:"):
            return value
        try:
            raw = base64.b64decode(value, validate=False)
        except (binascii.Error, ValueError):
            return ""
        if raw.startswith(b"\x89PNG"):
            mime = "image/png"
        elif raw.startswith(b"\xff\xd8"):
            mime = "image/jpeg"
        elif raw.startswith(b"GIF8"):
            mime = "image/gif"
        elif b"<svg" in raw[:512].lower():
            mime = "image/svg+xml"
        else:
            mime = "image/png"
        return "data:{};base64,{}".format(mime, base64.b64encode(raw).decode("ascii"))

    @staticmethod
    def _translate_mfa_message(message: str) -> str:
        import re
        normalized = re.sub(r"\s+", " ", message or "").strip().lower()
        if "use your authenticator" in normalized and "google authenticator" in normalized:
            return QCoreApplication.translate("ClientController",
                                              "Use your authenticator app to add your account (for example, Google Authenticator, Authy, etc.).")
        return message

    @Slot()
    def mfaContinue(self) -> None:
        self._set_login_page("mfaVerify")

    @Slot()
    def mfaBack(self) -> None:
        if self._login_page == "mfaVerify" and self._mfa.get("qrImage"):
            self._set_login_page("mfaSetup")
            return
        self.cancelMfa()

    @Slot()
    def cancelMfa(self) -> None:
        self._mfa = {}
        page = "credentials" if self._mfa_origin == "credentials" else ("password" if self._current_profile else "server")
        self._mfa_origin = ""
        self._set_login_page(page)

    @Slot(str, bool)
    def verifyMfa(self, code: str, remember: bool) -> None:
        code = (code or "").strip().replace(" ", "")
        if not code:
            self._set_login_page("mfaVerify", QCoreApplication.translate("ClientController", "Enter the authentication code."))
            return
        token = str(self._mfa.get("token", ""))
        self._login_busy = True
        self._login_error = ""
        self._show_loading(QCoreApplication.translate("ClientController", "Verifying code…"))
        self._auth.verify_mfa(token, code, bool(remember))

    def _on_services_ready(self, services: list) -> None:
        self._services_busy = False
        if not self._initial_load:
            silent = self._refresh_silent
            self._refresh_silent = False
            self._apply_services(list(services or []))
            ids = [s.image_id for s in services or []]
            self._images.preload(ids, lambda _failed: self.changed.emit())
            if not silent:
                self.notify.emit("success", QCoreApplication.translate("ClientController", "Service list refreshed."))
            return
        self._pending_services = list(services or [])
        ids = [s.image_id for s in self._pending_services]
        if not ids:
            self._finish_initial_load([])
            return
        self._show_loading(QCoreApplication.translate("ClientController", "Loading images…"))
        self._images.preload(ids, self._finish_initial_load)

    def _finish_initial_load(self, failed: list[str]) -> None:
        if not self._initial_load:
            return
        if failed:
            log.warning("Image preload failed for %d image(s)", len(failed))
        self._apply_services(self._pending_services)
        self._pending_services = []
        self._initial_load = False
        self._set_screen("main")
        self._refresh_timer.start()
        if self._pending_last_login:
            self.notify.emit("info", QCoreApplication.translate("ClientController", "Previous sign-in: {date}").format(date=self._format_last_login(self._pending_last_login)))
        self.changed.emit()

    def _apply_services(self, services: list[ServiceInfo]) -> None:
        self._raw_services = {str(s.id): s for s in services}
        self._services = services_to_list(services, self._favorites.ids)
        self.servicesChanged.emit()
        self.changed.emit()

    def _on_services_error(self, message: str) -> None:
        silent = self._refresh_silent
        self._refresh_silent = False
        self._services_busy = False
        if self._initial_load:
            self._initial_load = False
            self._show_loading_error(message)
            return
        self.changed.emit()
        if silent:
            log.warning("Silent services refresh failed: %s", message)
            return
        self.notify.emit("error", message)

    def _on_session_expired(self, message: str) -> None:
        log.warning("Session expired: %s", message)
        self._refresh_timer.stop()
        self._cancel_retry()
        self._services_busy = False
        self._refresh_silent = False
        self._initial_load = False
        self._pending_services = []
        self._api.abort_pending()
        self._auth.clear_session()
        self._services = []
        self._raw_services = {}
        self._images.clear()
        self.servicesChanged.emit()
        self._mfa = {}
        page = "password" if self._current_profile is not None else "server"
        self._set_login_page(page, message)

    @Slot(bool)
    def refreshServices(self, silent: bool = False) -> None:
        if self._initial_load or not self._auth.is_authenticated or self._services_busy:
            return
        self._services_busy = True
        self._refresh_silent = silent
        self.changed.emit()
        self._services_api.fetch_services()

    @Slot(str, result=bool)
    def toggleFavorite(self, service_id: str) -> bool:
        added = self._favorites.toggle(service_id)
        for item in self._services:
            if item["id"] == service_id:
                item["favorite"] = added
        self.servicesChanged.emit()
        return added

    @Slot(str, str)
    def connectService(self, service_id: str, transport_id: str = "") -> None:
        self._start_connection(service_id, transport_id, ask_custom_message=True)

    def _start_connection(self, service_id: str, transport_id: str, *, ask_custom_message: bool) -> None:
        svc = self._raw_services.get(service_id)
        if svc is None:
            return
        transport = next((t for t in svc.transports if t.id == transport_id), None) if transport_id else svc.default_transport
        if transport is None:
            self._prompt_alert(QCoreApplication.translate("ClientController", "Connection error"), QCoreApplication.translate("ClientController", "No transports available for this service."))
            return
        if ask_custom_message:
            self._cancel_retry()
        if self.connecting:
            if ask_custom_message:
                self.notify.emit("info", QCoreApplication.translate(
                    "ClientController", "The previous connection is still being launched. Please wait a moment."))
            return
        if not self._auth.is_authenticated:
            self._prompt_alert(QCoreApplication.translate("ClientController", "Connection error"), QCoreApplication.translate("ClientController", "Session expired. Please sign in again."))
            return
        if ask_custom_message and svc.custom_message:
            title = svc.visual_name or svc.name
            if not self._prompter.ask("warning", QCoreApplication.translate("ClientController", "Service message"), f"{title}\n\n{svc.custom_message}",
                                      QCoreApplication.translate("ClientController", "Continue"), QCoreApplication.translate("ClientController", "Cancel")):
                return
        notice = self._launch_notice(svc)
        if notice:
            self.notify.emit("info", notice)
        log.info("Launch transport: service=%s transport=%s", svc.name, transport.name)
        self._pending_launch = (svc, transport)
        self._connecting = True
        self._connecting_service_id = svc.id
        transport_type = str(transport.transport_type or "")
        client_settings: dict[str, Any] = {}
        if self._current_profile is not None and "spice" in transport_type.lower():
            client_settings["spice"] = self._transport_settings.load_spice(self._current_profile.id).to_dict()
        self._transport.launch(
            base_url=self._api.base_url, token=self._auth.token, scrambler=self._auth.scrambler,
            service_id=svc.id, transport_id=transport.id, transport_type=transport_type,
            client_settings=client_settings, parent_widget=None,
        )

    def _prompt_alert(self, title: str, text: str) -> None:
        self._prompter.ask("danger", title, text, QCoreApplication.translate("ClientController", "OK"), "")

    @staticmethod
    def _status_code(svc: ServiceInfo) -> str:
        return str(getattr(svc, "status_code", "") or "").strip().lower()

    def _launch_notice(self, svc: ServiceInfo) -> str:
        messages = {
            "off": QCoreApplication.translate("ClientController", "The machine is powered off. Power on is being started."),
            "powering_on": QCoreApplication.translate("ClientController", "The machine is powering on. Connection will be available soon."),
            "rebooting": QCoreApplication.translate("ClientController", "The machine is rebooting. Connection will be available after reboot."),
            "preparing": QCoreApplication.translate("ClientController", "The machine is being prepared. Connection will be available soon."),
            "powering_off": QCoreApplication.translate("ClientController", "The machine is powering off. Please wait until the operation finishes."),
            "maintenance": QCoreApplication.translate("ClientController", "The service is in maintenance mode. Connection is temporarily unavailable."),
            "unavailable": QCoreApplication.translate("ClientController", "The service is unavailable. Please try again later."),
        }
        return messages.get(self._status_code(svc), "")

    def _not_ready_message(self, svc: ServiceInfo | None, fallback: str) -> str:
        messages = {
            "off": QCoreApplication.translate("ClientController", "The machine is powered off. Power on is being started."),
            "powering_on": QCoreApplication.translate("ClientController", "The machine is powering on. Please try again shortly."),
            "rebooting": QCoreApplication.translate("ClientController", "The machine is rebooting. Please try again after reboot finishes."),
            "preparing": QCoreApplication.translate("ClientController", "The machine is being prepared. Please try again shortly."),
            "powering_off": QCoreApplication.translate("ClientController", "The machine is powering off. Please wait until the operation finishes."),
            "maintenance": QCoreApplication.translate("ClientController", "The service is in maintenance mode. Connection is temporarily unavailable."),
            "unavailable": QCoreApplication.translate("ClientController", "The service is unavailable. Please try again later."),
        }
        code = self._status_code(svc) if svc is not None else ""
        return messages.get(code, translate_server_message(fallback))

    @Slot()
    def _on_transport_started(self) -> None:
        self._connecting = True
        self._show_loading(QCoreApplication.translate("ClientController", "Connecting…"))

    @Slot()
    def _on_transport_ok(self) -> None:
        self._pending_launch = None
        self._set_screen("main")

    @Slot()
    def _on_transport_finished(self) -> None:
        self._connecting = False
        self._connecting_service_id = ""
        self.changed.emit()

    @Slot()
    def cancelConnection(self) -> None:
        if not self.connecting:
            return
        log.info("Connection cancelled by user")
        self._cancel_retry()
        self._pending_launch = None
        self._transport.stop()
        self._connecting = False
        self._connecting_service_id = ""
        self._set_screen("main" if self._auth.is_authenticated else "login")

    def _cancel_retry(self) -> None:
        if self._retry_timer is not None:
            self._retry_timer.stop()
            self._retry_timer.deleteLater()
            self._retry_timer = None

    @Slot(str)
    def _on_transport_error(self, message: str) -> None:
        log.warning("Transport error: %s", message)
        svc = self._pending_launch[0] if self._pending_launch else None
        self._pending_launch = None
        self._set_screen("main")
        self._prompt_alert(QCoreApplication.translate("ClientController", "Connection error"), self._not_ready_message(svc, message))

    @Slot(str)
    def _on_transport_retry(self, message: str) -> None:
        svc, transport = self._pending_launch if self._pending_launch else (None, None)
        text = self._not_ready_message(svc, message)
        self._set_screen("main")
        retry_question = QCoreApplication.translate(
            "ClientController", "Retry connection?"
        )
        retry = self._prompter.ask(
            "primary",
            QCoreApplication.translate("ClientController", "Service is not ready"),
            f"{text}\n\n{retry_question}",
            QCoreApplication.translate("ClientController", "Retry"),
            QCoreApplication.translate("ClientController", "Cancel"),
        )
        if retry and svc is not None:
            self._cancel_retry()
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(RETRY_DELAY_MS)
            timer.timeout.connect(lambda: self._fire_retry(svc.id, transport.id if transport else ""))
            self._retry_timer = timer
            timer.start()
        else:
            self._pending_launch = None

    def _fire_retry(self, service_id: str, transport_id: str) -> None:
        self._cancel_retry()
        self._start_connection(service_id, transport_id, ask_custom_message=False)

    @Slot(str, str)
    def serviceAction(self, service_id: str, action: str) -> None:
        if not self._auth.is_authenticated:
            self._prompt_alert(QCoreApplication.translate("ClientController", "Connection error"), QCoreApplication.translate("ClientController", "Session expired. Please sign in again."))
            return
        started = {
            "poweron": QCoreApplication.translate("ClientController", "Power on command sent."),
            "poweroff": QCoreApplication.translate("ClientController", "Power off command sent."),
            "reset": QCoreApplication.translate("ClientController", "Reset command sent."),
        }
        self.notify.emit("info", started.get(action, QCoreApplication.translate("ClientController", "Command sent.")))
        self._services_api.service_action(service_id, action)

    def _on_action_done(self, service_id: str, action: str) -> None:
        del service_id
        done = {
            "poweron": QCoreApplication.translate("ClientController", "Power on completed."),
            "poweroff": QCoreApplication.translate("ClientController", "Power off completed."),
            "reset": QCoreApplication.translate("ClientController", "Reset completed."),
        }
        self.notify.emit("success", done.get(action, QCoreApplication.translate("ClientController", "Command completed.")))
        self.refreshServices(True)

    def _on_connect_error(self, message: str) -> None:
        log.warning("Connect error: %s", message)
        self.notify.emit("warning", translate_server_message(message))

    @Slot()
    def logout(self) -> None:
        log.info("Logging out")
        self._refresh_timer.stop()
        self._api.abort_pending()
        self._shutdown_connections()
        self._services = []
        self._raw_services = {}
        self._services_busy = False
        self._images.clear()
        self.servicesChanged.emit()
        self._auth.logout()

    @Slot()
    def backToLogin(self) -> None:
        self._refresh_timer.stop()
        self._initial_load = False
        self._pending_services = []
        self._api.abort_pending()
        self._shutdown_connections()
        self._services = []
        self._raw_services = {}
        self._services_busy = False
        self._images.clear()
        self.servicesChanged.emit()
        if self._auth.is_authenticated:
            self._auth.logout()
        else:
            self._auth.clear_session()
            self._on_logged_out()

    def _on_logged_out(self) -> None:
        self._pending_username = ""
        self._pending_last_login = ""
        self._mfa = {}
        self._login_source = ""
        self.start()

    def _shutdown_connections(self, blocking: bool = False) -> None:
        self._cancel_retry()
        try:
            self._transport.stop()
        except Exception:  # noqa: BLE001
            log.debug("Transport stop failed", exc_info=True)
        servers = tunnel_mod.take_all()
        resources = tools_mod.take_session_resources()

        def _release() -> None:
            for fn in (lambda: tunnel_mod.stop_servers(servers),
                       lambda: tools_mod.release_session_resources(resources)):
                try:
                    fn()
                except Exception:  # noqa: BLE001
                    log.debug("Cleanup failed", exc_info=True)

        if blocking:
            _release()
        else:
            threading.Thread(target=_release, name="GorizontVS-SessionCleanup", daemon=True).start()

    def shutdown(self) -> None:
        self._prompter.shutdown()
        self._refresh_timer.stop()
        self._api.abort_pending()
        self._shutdown_connections(blocking=True)
        self._transport.wait_for_orphans(1000)
        self._i18n.unload()
        if self._auth.is_authenticated:
            from PySide6.QtCore import QEventLoop  # type: ignore
            loop = QEventLoop()
            self._auth.logged_out.connect(loop.quit)
            self._auth.logout()
            QTimer.singleShot(2000, loop.quit)
            loop.exec()
    @Slot(str)
    def setTheme(self, name: str) -> None:
        name = "dark" if name == "dark" else "light"
        self._theme = name
        self._settings.setValue("ui/theme", name)
        self._settings.sync()
        self.changed.emit()

    @Slot(str)
    def _on_language_changed(self, _locale: str) -> None:
        # Python-created model strings are not covered by QQmlEngine.retranslate().
        self._apply_services(list(self._raw_services.values()))
        self.languageChanged.emit()

    @Slot(str)
    def setLanguage(self, locale_name: str) -> None:
        self._i18n.load(locale_name)

    def applyLanguage(self) -> None:
        self._i18n.load(self._i18n.current)

    @Slot("QVariantMap")
    def saveSpiceSettings(self, values: dict) -> None:
        if self._current_profile is None:
            return
        try:
            count = int(values.get("monitorCount", 1))
        except (TypeError, ValueError):
            count = 1
        self._transport_settings.save_spice(self._current_profile.id, SpiceSettings(
            multi_monitor_enabled=bool(values.get("multiMonitorEnabled", False)),
            monitor_count=max(1, min(4, count)),
            webdav_enabled=bool(values.get("webdavEnabled", False)),
            webdav_path=str(values.get("webdavPath", "") or "").strip(),
        ))
        self.settingsChanged.emit()

    @Slot(str, result=str)
    def browseFolder(self, current: str) -> str:
        import os
        from PySide6.QtWidgets import QFileDialog  # type: ignore
        start = current if current and os.path.isdir(current) else ""
        return QFileDialog.getExistingDirectory(None, QCoreApplication.translate("ClientController", "Select folder"), start) or ""
