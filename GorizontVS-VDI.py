from __future__ import annotations

import atexit
import contextlib
import logging
import signal
import sys

from src.infrastructure.logging_setup import setup_logging
from src.macos_runtime import setup_macos_bundle_environment
setup_macos_bundle_environment()
setup_logging()

from PySide6.QtCore import QEvent, QEventLoop, QSettings, Qt, QTimer  # type: ignore  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon  # type: ignore  # noqa: E402
from PySide6.QtWidgets import (  # type: ignore  # noqa: E402
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

import resources.rc_resource as rc_resource  # noqa: E402, F401
from src.api.auth import AuthService  # noqa: E402
from src.api.client import ApiClient # noqa: E402
from src.api.services import ServicesAPI # noqa: E402
from src.dialogs.app_dialogs import alert # noqa: E402
from src.icons import icon_search, logo_pixmap # noqa: E402
from src.infrastructure.i18n_manager import I18nManager # noqa: E402
from src.infrastructure.theme_manager import ThemeManager # noqa: E402
from src.leftmenu import MenuController # noqa: E402
from src.login_controller import LoginController # noqa: E402
from src.main_page_controller import MainPageController # noqa: E402
from src.service_image_loader import ServiceImageLoader # noqa: E402
from src.settings_page import SettingsPage # noqa: E402
from src.transport import tools as tools_mod # noqa: E402
from src.transport import tunnel as tunnel_mod # noqa: E402
from src.transport.executor import TransportExecutor # noqa: E402
from src.utils.version import APP_VERSION # noqa: E402
from src.widgets.avatar_dropdown import AvatarDropdownPopup  # noqa: E402
from src.widgets.spinner import Spinner # noqa: E402
from ui.ui_form import Ui_Widget # noqa: E402

log = logging.getLogger(__name__)


def _load_app_fonts(app: QApplication) -> None:
    for src in (
        ":/fonts/Montserrat-Regular.ttf",
        ":/fonts/Montserrat-Medium.ttf",
        ":/fonts/Montserrat-SemiBold.ttf",
        ":/fonts/Montserrat-Bold.ttf",
        ":/fonts/Montserrat-Light.ttf",
        ":/fonts/Montserrat-Black.ttf",
    ):
        QFontDatabase.addApplicationFont(src)
    if "Montserrat" in QFontDatabase.families():
        font = QFont("Montserrat")
        font.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(font)


class AppWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self._settings = QSettings("Gorizont-VS", "VDIClient")

        self._theme = ThemeManager(self._settings, parent=self)
        self._i18n = I18nManager(self._settings, parent=self)

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
            app.setProperty("theme", self._theme.current)

        self._api = ApiClient(parent=self)
        self._api.set_ssl_dialog_parent(self)
        self._api.set_timeout(15_000)
        self._image_loader = ServiceImageLoader(self._api, parent=self)

        self.menu = MenuController(self.ui, parent=self)
        self.main_page = MainPageController(
            self.ui,
            menu=self.menu,
            settings=self._settings,
            image_loader=self._image_loader,
            parent=self,
        )
        self._settings_page = SettingsPage(self.ui, self._settings, self)
        self._spinner = Spinner(
            self.ui.spinnerHost,
            color=QColor(4, 115, 148),
            thickness=18,
            inner_radius=26,
            rev_per_sec=1,
            arc_deg=100,
            tail_steps=18,
            tail_fade=0.85,
            fps=60,
        )
        self._search_action = None
        self._loading_status_label: QLabel | None = None
        self._loading_back_button: QPushButton | None = None
        self._avatar_dropdown: AvatarDropdownPopup | None = None
        self._pending_username: str = ""
        self._initial_workspace_load = False
        self._pending_services: list[object] = []
        self._pending_launch_svc: object | None = None

        self._mount_spinner()
        self._init_login_toolbar()
        self._init_loading_page()
        self._init_main_shell()

        self._auth = AuthService(self._api, parent=self)
        self._services_api = ServicesAPI(self._api, parent=self)
        self.login_ctrl = LoginController(self.ui, self._settings, parent=self)
        self._transport = TransportExecutor(parent=self)
        self._connect_signals()

        self._i18n.load(self._i18n.current)
        self._theme.apply(self._theme.current)
        self.show_login()

    def _connect_signals(self) -> None:
        self.login_ctrl.authenticators_requested.connect(self._on_fetch_authenticators)
        self.login_ctrl.login_requested.connect(self._on_login_requested)
        self.login_ctrl.negotiate_requested.connect(self._on_negotiate_requested)
        self._auth.authenticators_ready.connect(self.login_ctrl.set_authenticators)
        self._auth.auth_error.connect(self.login_ctrl.on_auth_fetch_failed)
        self._auth.login_success.connect(self._on_login_success)
        self._auth.login_error.connect(self._on_login_failed)
        self._auth.logged_out.connect(self._on_logged_out)
        self._services_api.services_ready.connect(self._on_services_ready)
        self._services_api.services_error.connect(self._on_services_error)
        self._services_api.connect_error.connect(self._on_connect_error)
        self._services_api.action_done.connect(self._refresh_services)
        self._transport.launch_started.connect(self._on_transport_started)
        self._transport.launch_ok.connect(self._on_transport_ok)
        self._transport.launch_error.connect(self._on_transport_error)
        self._transport.launch_retry.connect(self._on_transport_retry)
        self.main_page.connect_requested.connect(self._on_service_card_clicked)
        self.main_page.action_requested.connect(self._on_service_action_requested)
        self._i18n.language_changed.connect(self._on_language_changed)
        self._theme.theme_changed.connect(self._on_theme_changed)

    def _on_language_changed(self, locale: str) -> None:
        self.ui.retranslateUi(self)
        self.main_page.retranslate_ui()
        self._settings_page.retranslate()
        self._refresh_login_toolbar_texts()
        self._refresh_avatar_dropdown()
        self._refresh_loading_texts()
        self.main_page.set_user_identity(self._pending_username or None)

    def _on_theme_changed(self, theme: str) -> None:
        svg = (
            ":/img/static/login-bg-white.svg"
            if theme == "light"
            else ":/img/static/login-bg-dark.svg"
        )
        self.ui.pageMain.setProperty("svgPath", svg)
        self.ui.pageLoad.setProperty("svgPath", svg)
        self.menu.refresh_theme()
        self._refresh_search_icon()
        self._refresh_login_toolbar_texts()
        self._refresh_avatar_dropdown()
        for w in (self.ui.pageMain, self.ui.pageLoad, self.ui.pageLogin, self):
            w.update()

    def _mount_spinner(self) -> None:
        host = self.ui.spinnerHost
        layout = host.layout() or QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._spinner, 0)
        self._spinner.stop()

    def _init_login_toolbar(self) -> None:
        btn_lang = getattr(self.ui, "btnLoginLanguage", None)
        btn_theme = getattr(self.ui, "btnLoginThemeToggle", None)
        if btn_lang:
            btn_lang.clicked.connect(self._i18n.toggle)
        if btn_theme:
            btn_theme.clicked.connect(self._theme.toggle)
        self._refresh_login_toolbar_texts()

    def _init_loading_page(self) -> None:
        self.ui.svgLogoSmall.load(":/img/static/logo-small.svg")
        self._loading_status_label = QLabel(self.ui.pageLoad)
        self._loading_status_label.setObjectName("lblLoadingStatus")
        self._loading_status_label.setWordWrap(True)
        self._loading_status_label.setAlignment(Qt.AlignCenter)
        self.ui.lytLoadingRoot.insertWidget(
            2, self._loading_status_label, 0, Qt.AlignHCenter
        )
        self._loading_back_button = QPushButton(self.ui.pageLoad)
        self._loading_back_button.setObjectName("btnLoadingBack")
        self._loading_back_button.setCursor(Qt.PointingHandCursor)
        self._loading_back_button.setVisible(False)
        self._loading_back_button.clicked.connect(self._on_loading_back_clicked)
        self.ui.lytLoadingRoot.insertWidget(
            3, self._loading_back_button, 0, Qt.AlignHCenter
        )
        self._refresh_loading_texts()

    def _init_main_shell(self) -> None:
        px = logo_pixmap(height=28)
        if not px.isNull():
            self.ui.lblTopLogo.setPixmap(px)
        for lyt in (self.ui.vlytMainRoot, self.ui.hlytMainBody):
            lyt.setContentsMargins(0, 0, 0, 0)
            lyt.setSpacing(0)
        page_lyt = self.ui.pageMain.layout()
        if page_lyt:
            page_lyt.setContentsMargins(0, 0, 0, 0)
            page_lyt.setSpacing(0)
        self.ui.lblTopLogo.setMinimumHeight(32)
        self._init_main_content_page_style()
        self._avatar_dropdown = AvatarDropdownPopup(self)
        self.ui.btnUserAvatar.clicked.connect(self._toggle_avatar_dropdown)
        self._wire_avatar_dropdown()
        self._refresh_avatar_dropdown()
        self._search_action = self.ui.leWorkspaceSearch.addAction(
            icon_search(color="#9CA3AF"),
            self.ui.leWorkspaceSearch.ActionPosition.LeadingPosition,
        )
        self._search_action.setEnabled(False)
        self._search_action.setVisible(True)
        self.ui.leWorkspaceSearch.setFocusPolicy(Qt.ClickFocus)
        self.ui.leWorkspaceSearch.clearFocus()
        self.main_page.set_user_identity(None)
        self._refresh_search_icon()

    def _refresh_login_toolbar_texts(self) -> None:
        btn = getattr(self.ui, "btnLoginLanguage", None)
        if btn:
            btn.setText("RU" if self._i18n.current == "ru_RU" else "EN")
            btn.setToolTip(self.tr("Switch language"))
        btn = getattr(self.ui, "btnLoginThemeToggle", None)
        if btn:
            btn.setText("\u2600" if self._theme.current == "dark" else "\u263e")
            btn.setToolTip(self.tr("Toggle theme"))

    def _refresh_loading_texts(self) -> None:
        if self._loading_status_label and not self._loading_status_label.text():
            self._loading_status_label.setText(self.tr("Preparing\u2026"))
        if self._loading_back_button:
            self._loading_back_button.setText(self.tr("Back to login"))

    def _refresh_search_icon(self) -> None:
        if self._search_action:
            color = "#9CA3AF" if self._theme.current == "light" else "#94A3B8"
            self._search_action.setIcon(icon_search(color=color))

    def _init_main_content_page_style(self) -> None:
        _m = self._apply_layout_margins
        _m(
            (
                "verticalLayout_12",
                "verticalLayout_11",
                "verticalLayout_13",
                "verticalLayout_8",
            ),
            (24, 20, 24, 24),
            18,
        )
        _m(("vlytDesktopsPage", "vlytAppsPage", "vlytHomePage"), (0, 0, 0, 0), 18)
        _m(
            (
                "horizontalLayout_10",
                "horizontalLayout_6",
                "horizontalLayout_8",
                "horizontalLayout_14",
            ),
            (0, 0, 0, 0),
            0,
        )
        _m(
            (
                "hlytDesktopsHeader",
                "hlytAppsHeader",
                "hlyHomeHeader",
                "hlySettingsPageHeader",
            ),
            (0, 0, 0, 0),
            12,
        )
        _m(("horizontalLayout_4", "horizontalLayoutSettingsTabs"), (0, 0, 0, 0), 12)
        _m(("verticalLayout_9",), (20, 20, 20, 20), 12)
        _m(("verticalLayoutSettingsPanel",), (0, 0, 0, 0), 10)
        _m(("gridLayout_4", "gridLayout_8", "verticalLayout_15"), (0, 0, 0, 0), None)
        for n in ("gridLayout_4", "gridLayout_8"):
            lw = getattr(self.ui, n, None)
            if lw:
                lw.setHorizontalSpacing(0)
                lw.setVerticalSpacing(18)
        hs = getattr(self.ui, "verticalLayout_15", None)
        if hs:
            hs.setSpacing(18)

    def _apply_layout_margins(self, names, margins, spacing):
        for n in names:
            lw = getattr(self.ui, n, None)
            if lw:
                lw.setContentsMargins(*margins)
                if spacing is not None:
                    lw.setSpacing(spacing)

    def _wire_avatar_dropdown(self) -> None:
        if not self._avatar_dropdown:
            return
        self._avatar_dropdown.language_selected.connect(self._i18n.load)
        self._avatar_dropdown.theme_selected.connect(self._theme.apply)
        self._avatar_dropdown.settings_requested.connect(self.show_settings_page)
        self._avatar_dropdown.logout_requested.connect(self._on_logout)

    def _refresh_avatar_dropdown(self) -> None:
        if not self._avatar_dropdown:
            return
        username = (self._pending_username or "").strip()
        self._avatar_dropdown.set_translations(
            title=self.tr("Profile"),
            subtitle=username or self.tr("Quick profile settings"),
            language_label=self.tr("Interface language"),
            theme_label=self.tr("Color theme"),
            settings_text=self.tr("Settings"),
            logout_text=self.tr("Logout"),
            light_text=self.tr("Light"),
            dark_text=self.tr("Dark"),
        )
        self._avatar_dropdown.set_language(self._i18n.current)
        self._avatar_dropdown.set_theme(self._theme.current)

    def _toggle_avatar_dropdown(self) -> None:
        if not self._avatar_dropdown:
            return
        if self._avatar_dropdown.isVisible():
            self._avatar_dropdown.hide()
            return
        self._refresh_avatar_dropdown()
        self._avatar_dropdown.popup_for(self.ui.btnUserAvatar)

    def show_login(self) -> None:
        self._spinner.stop()
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageLogin)
        self.login_ctrl.navigate_to_initial()

    def show_loading(self, status_text: str | None = None) -> None:
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageLoad)
        self._set_loading_message(status_text or self.tr("Loading\u2026"))
        self._spinner.start()
        if self._loading_back_button:
            self._loading_back_button.setVisible(False)

    def show_loading_error(self, message: str) -> None:
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageLoad)
        self._spinner.stop()
        self._set_loading_message(message, is_error=True)
        if self._loading_back_button:
            self._loading_back_button.setVisible(True)

    def show_main(self) -> None:
        self._spinner.stop()
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageMain)
        self.ui.leWorkspaceSearch.clearFocus()

    def show_settings_page(self) -> None:
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageMain)
        self.ui.stackedWidgetMainContent.setCurrentWidget(self.ui.pageSettings)
        self.ui.leWorkspaceSearch.clearFocus()

    def _set_loading_message(self, message: str, *, is_error: bool = False) -> None:
        if not self._loading_status_label:
            return
        self._loading_status_label.setText(message)
        self._loading_status_label.setProperty("error", is_error)
        self._loading_status_label.style().unpolish(self._loading_status_label)
        self._loading_status_label.style().polish(self._loading_status_label)
        self._loading_status_label.update()

    def _on_fetch_authenticators(self, server_url: str) -> None:
        log.info("Fetching authenticators from %s", server_url)
        self._auth.fetch_authenticators(server_url)

    def _on_login_requested(self, server, auth_id, username, password) -> None:
        log.info("Logging in as %s via %s", username, auth_id)
        self._pending_username = username.strip()
        self.main_page.set_user_identity(self._pending_username)
        self._refresh_avatar_dropdown()
        self._api.set_base_url(server)
        self.show_loading(self.tr("Signing in\u2026"))
        self._initial_workspace_load = False
        self._auth.login(auth_id, username, password)
        
    def _on_negotiate_requested(self, server: str, auth_id: str, spn: str) -> None:
        log.info("Starting negotiate login via auth_id=%s spn=%s", auth_id, spn)
        self._pending_username = ""
        self.main_page.set_user_identity(None)
        self._refresh_avatar_dropdown()
        self._api.set_base_url(server)
        self.show_loading(self.tr("Signing in…"))
        self._initial_workspace_load = False
        self._auth.login_negotiate(auth_id, spn)

    def _on_login_success(self, token: str, username: str) -> None:
        log.info("Login successful, fetching services...")
        if username:
            self._pending_username = username
            self.main_page.set_user_identity(username)
            self._refresh_avatar_dropdown()
        self.login_ctrl.on_login_success(username)
        self._initial_workspace_load = True
        self._pending_services = []
        self.show_loading(self.tr("Loading services\u2026"))
        self._services_api.fetch_services()

    def _on_services_ready(self, services) -> None:
        if not self._initial_workspace_load:
            self.main_page.populate(services)
            return
        self._pending_services = list(services or [])
        ids = [str(getattr(s, "image_id", "") or "") for s in self._pending_services]
        if not ids:
            self._finish_initial_workspace_load([])
            return
        self.show_loading(self.tr("Loading images\u2026"))
        self._image_loader.preload(ids, self._finish_initial_workspace_load)

    def _finish_initial_workspace_load(self, failed) -> None:
        if not self._initial_workspace_load:
            return
        if failed:
            log.warning("Image preload failed for %d image(s)", len(failed))
            self._initial_workspace_load = False
            msg = self.tr("Failed to load workspace content. Please sign in again.")
            self.show_loading_error(msg)
            alert(self, self.tr("Loading error"), msg, kind="danger")
            return
        log.info("Workspace loaded successfully")
        self.main_page.populate(self._pending_services)
        self._pending_services = []
        self._initial_workspace_load = False
        self.show_main()

    def _on_services_error(self, msg) -> None:
        if self._initial_workspace_load:
            log.warning("Services load failed during login: %s", msg)
            self._initial_workspace_load = False
            self.show_loading_error(msg)
        alert(self, self.tr("Loading error"), msg, kind="danger")

    def _on_connect_error(self, msg) -> None:
        log.warning("Connect error: %s", msg)
        alert(self, self.tr("Warning"), msg, kind="warning")

    def _on_login_failed(self, msg) -> None:
        log.warning("Login failed: %s", msg)
        self._initial_workspace_load = False
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageLogin)
        self.login_ctrl.on_login_failed(msg)

    def _on_logout(self) -> None:
        log.info("Logging out")
        self._shutdown_runtime_connections()
        self.main_page.clear()
        self.main_page.set_user_identity(None)
        self._pending_username = ""
        if self._avatar_dropdown:
            self._avatar_dropdown.hide()
            self._refresh_avatar_dropdown()
        self._auth.logout()

    def _on_logged_out(self) -> None:
        self.show_login()

    def _on_loading_back_clicked(self) -> None:
        self._initial_workspace_load = False
        self._pending_services = []
        self._pending_username = ""
        self._shutdown_runtime_connections()
        self.main_page.clear()
        self.main_page.set_user_identity(None)
        if self._avatar_dropdown:
            self._avatar_dropdown.hide()
            self._refresh_avatar_dropdown()
        if self._auth.is_authenticated:
            self._auth.logout()
        else:
            self._auth.clear_session()
            self.show_login()

    def _on_service_card_clicked(self, svc) -> None:
        from src.api.services import ServiceInfo

        if not isinstance(svc, ServiceInfo):
            return
        transport = svc.default_transport
        if not transport:
            self._show_transport_error(
                self.tr("No transports available for this service.")
            )
            return
        if self._transport.is_running:
            return
        if not self._auth.is_authenticated:
            self._show_transport_error(
                self.tr("Session expired. Please sign in again.")
            )
            return
        log.info("Launch transport: service=%s transport=%s", svc.name, transport.name)
        self._pending_launch_svc = svc
        self._transport.launch(
            base_url=self._api.base_url,
            token=self._auth.token,
            scrambler=self._auth.scrambler,
            service_id=svc.id,
            transport_id=transport.id,
            parent_widget=self,
        )

    def _on_service_action_requested(self, svc, action) -> None:
        if action == "open":
            self._on_service_card_clicked(svc)
            return
        self._services_api.service_action(svc.id, action)

    def _on_transport_started(self) -> None:
        self.show_loading(self.tr("Connecting\u2026"))

    def _on_transport_ok(self) -> None:
        self._spinner.stop()
        self._pending_launch_svc = None
        self.show_main()

    def _on_transport_error(self, msg) -> None:
        log.warning("Transport error: %s", msg)
        self._spinner.stop()
        self._pending_launch_svc = None
        self.show_main()
        self._show_transport_error(msg)

    def _on_transport_retry(self, msg) -> None:
        from src.dialogs.app_dialogs import confirm

        svc = self._pending_launch_svc
        ok = confirm(
            self,
            title=self.tr("Service is not ready"),
            text=f"{msg}\n\n{self.tr('Retry connection?')}",
            confirm_text=self.tr("Retry"),
            cancel_text=self.tr("Cancel"),
        )
        if ok and svc:
            QTimer.singleShot(3000, lambda: self._on_service_card_clicked(svc))
        else:
            self._spinner.stop()
            self._pending_launch_svc = None
            self.show_main()

    def _show_transport_error(self, msg) -> None:
        alert(self, self.tr("Connection error"), msg, kind="danger")

    def _refresh_services(self) -> None:
        self._services_api.fetch_services()

    def _shutdown_runtime_connections(self) -> None:
        for fn in (
            self._transport.stop,
            tunnel_mod.stop_all,
            tools_mod.execute_before_exit,
            tools_mod.terminate_tasks,
            lambda: tools_mod.unlink_files(True),
            lambda: tools_mod.unlink_files(False),
        ):
            try:
                fn()
            except Exception:
                log.debug("Cleanup failed", exc_info=True)

    def closeEvent(self, event) -> None:
        self._shutdown_runtime_connections()
        if self._auth.is_authenticated:
            loop = QEventLoop(self)

            def _f():
                loop.isRunning() and loop.quit()

            self._auth.logged_out.connect(_f)
            self._auth.logout()
            QTimer.singleShot(2000, _f)
            loop.exec()
            with contextlib.suppress(Exception):
                self._auth.logged_out.disconnect(_f)
        super().closeEvent(event)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.key() in (
            Qt.Key_Tab,
            Qt.Key_Backtab,
        ):
            return self._handle_tab_navigation(event.key())
        if event.type() == QEvent.MouseButtonPress:
            self._clear_search_focus_if_needed(watched)
        return super().eventFilter(watched, event)

    def _handle_tab_navigation(self, key):
        focus = QApplication.focusWidget()
        allowed = {self.ui.leCredsUser, self.ui.leCredsPass}
        if focus not in allowed:
            return True
        nxt = (
            self.ui.leCredsPass
            if (key == Qt.Key_Tab) == (focus is self.ui.leCredsUser)
            else self.ui.leCredsUser
        )
        nxt.setFocus(Qt.TabFocusReason)
        return True

    def _clear_search_focus_if_needed(self, watched) -> None:
        s = self.ui.leWorkspaceSearch
        if not s.hasFocus():
            return
        w = watched if isinstance(watched, QWidget) else None
        if w is None or w is s or s.isAncestorOf(w):
            return
        s.clearFocus()


_cleanup_done = False


def _cleanup_on_exit() -> None:
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    for fn in (
        tunnel_mod.stop_all,
        lambda: tools_mod.unlink_files(True),
        lambda: tools_mod.unlink_files(False),
        tools_mod.execute_before_exit,
    ):
        try:
            fn()
        except Exception:
            pass


atexit.register(_cleanup_on_exit)

if __name__ == "__main__":
    log.info("Starting Gorizont-VS VDI Client v%s", APP_VERSION)
    app = QApplication(sys.argv)
    app.setApplicationName("Gorizont-VS VDI")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(":/img/static/app.icns"))
    app.setStyle("Fusion")
    _load_app_fonts(app)
    app.aboutToQuit.connect(_cleanup_on_exit)
    for _sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if _sig is not None:
            with contextlib.suppress(Exception):
                signal.signal(_sig, lambda *_a: (_cleanup_on_exit(), app.quit()))
    w = AppWidget()
    w.show()
    sys.exit(app.exec())
