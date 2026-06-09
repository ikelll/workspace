from __future__ import annotations

import re

from PySide6.QtCore import QObject, QSettings, Qt, Signal  # type: ignore
from PySide6.QtGui import QAction, QPixmap  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QLabel,
    QLineEdit,
    QToolButton,
    QWidget,
)

from src.dialogs.app_dialogs import alert, confirm
from src.icons import (
    icon_eye,
    icon_eye_off,
    icon_globe,
    icon_lock,
    icon_user,
    logo_pixmap,
)
from src.profile_card import ProfileCard
from src.profile_manager import Profile, ProfileManager, avatar_color

_URL_RE = re.compile(r"^https?://[a-zA-Z0-9\-.]+(:\d{1,5})?(/.*)?$", re.I)
_AVATAR_BIG = 64
_LOGO_HEIGHT = 40
_ICON_SIZE = 16
_BANNER_HEIGHT = 38


def _avatar_label(parent: QWidget, profile: Profile, size: int) -> QLabel:
    lbl = QLabel(profile.initials, parent)
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignCenter)
    bg = avatar_color(profile)
    radius = size // 2
    fs = max(size // 3, 12)
    lbl.setObjectName("lblLoginAvatar")
    lbl.setStyleSheet(
        f"QLabel#lblLoginAvatar {{"
        f"  background: {bg}; border-radius: {radius}px;"
        f"  font-size: {fs}px;"
        f"}}"
    )
    return lbl


def _setup_logo(label: QLabel, pixmap: QPixmap) -> None:
    label.setScaledContents(False)
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    label.setFixedHeight(int(pixmap.height() / pixmap.devicePixelRatio()) + 8)
    label.setObjectName("lblLoginLogo")


def _set_field_error(widget: QWidget, has_error: bool) -> None:
    widget.setProperty("hasError", has_error)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _setup_password_toggle(line_edit: QLineEdit) -> QAction:
    action = QAction(line_edit)
    action.setIcon(icon_eye(_ICON_SIZE))
    line_edit.addAction(action, QLineEdit.TrailingPosition)

    def _apply_cursor() -> None:
        for button in line_edit.findChildren(QToolButton):
            if button.defaultAction() is action:
                button.setCursor(Qt.PointingHandCursor)

    def toggle():
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(icon_eye_off(_ICON_SIZE))
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(icon_eye(_ICON_SIZE))
        _apply_cursor()

    action.triggered.connect(toggle)
    _apply_cursor()
    return action


def _setup_banner(lbl: QLabel) -> None:
    lbl.setFixedHeight(_BANNER_HEIGHT)
    lbl.setWordWrap(True)
    lbl.setAlignment(Qt.AlignCenter)
    _hide_banner(lbl)


def _show_banner(lbl: QLabel, text: str) -> None:
    lbl.setText(text)
    lbl.setProperty("hasError", True)
    lbl.style().unpolish(lbl)
    lbl.style().polish(lbl)


def _hide_banner(lbl: QLabel) -> None:
    lbl.setText("")
    lbl.setProperty("hasError", False)
    lbl.style().unpolish(lbl)
    lbl.style().polish(lbl)


class LoginController(QObject):
    authenticators_requested = Signal(str)
    login_requested = Signal(str, str, str, str)
    negotiate_requested = Signal(str, str, str)

    def __init__(self, ui, settings: QSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = ui
        self._pm = ProfileManager(settings)

        self._current_profile: Profile | None = None
        self._setup_server_url: str = ""
        self._pg_server = self.ui.pageServer
        self._pg_creds = self.ui.pageCreds
        self._pg_password = self.ui.pagePassword
        self._pg_profiles = self.ui.pageProfiles

        self._srv_banner = self.ui.lblServerErrorBanner
        self._le_server = self.ui.leServerUrl
        self._btn_connect = self.ui.btnConnect
        self._link_back_to_profiles = self.ui.btnBackToProfiles

        self._creds_banner = self.ui.lblCredsErrorBanner
        self._creds_server_lbl = self.ui.lblCredsServer
        self._cmb_auth = self.ui.cmbAuthenticator
        self._le_creds_user = self.ui.leCredsUser
        self._le_creds_pass = self.ui.leCredsPass
        self._btn_creds_login = self.ui.btnCredsLogin
        self._btn_creds_back = self.ui.btnCredsBack

        self._pw_banner = self.ui.lblPwErrorBanner
        self._pw_identity_host = self.ui.lytPasswordIdentity
        self._le_pw_pass = self.ui.leProfilePass
        self._btn_pw_login = self.ui.btnProfileLogin
        self._link_switch = self.ui.btnSwitchAccount
        self._link_delete = self.ui.btnDeleteProfile

        self._profiles_list_widget = self.ui.wProfilesListHost
        self._profiles_list_layout = self.ui.lytProfilesList
        self._btn_add_profile = self.ui.btnAddProfile

        self._init_logos()
        self._init_field_icons()
        self._init_banners()
        self._init_signals()

        self.ui.stackedWidgetLogin.setCurrentIndex(0)

        self._cmb_auth.setMaxVisibleItems(3)

    def _init_logos(self) -> None:
        px = logo_pixmap(height=_LOGO_HEIGHT)
        if px.isNull():
            return

        for name in ("lblServerLogo", "lblCredsLogo", "lblPasswordLogo"):
            lbl = getattr(self.ui, name, None)
            if lbl:
                _setup_logo(lbl, px)

    def _init_field_icons(self) -> None:
        self._le_server.addAction(icon_globe(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._le_creds_user.addAction(icon_user(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._le_creds_pass.addAction(icon_lock(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._le_pw_pass.addAction(icon_lock(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._eye_creds = _setup_password_toggle(self._le_creds_pass)
        self._eye_pw = _setup_password_toggle(self._le_pw_pass)

    def _init_banners(self) -> None:
        for banner in (self._srv_banner, self._creds_banner, self._pw_banner):
            _setup_banner(banner)

    def _init_signals(self) -> None:
        self._cmb_auth.currentIndexChanged.connect(lambda _: self._refresh_creds_mode())
        self._btn_connect.clicked.connect(self._on_connect_clicked)
        self._le_server.returnPressed.connect(self._on_connect_clicked)
        self._le_server.textChanged.connect(
            lambda _: self._clear_field_error(self._le_server)
        )
        self._link_back_to_profiles.clicked.connect(self.show_profiles_page)

        self._btn_creds_login.clicked.connect(self._on_creds_login_clicked)
        self._btn_creds_back.clicked.connect(self.show_server_page)
        self._le_creds_user.returnPressed.connect(
            lambda: self._le_creds_pass.setFocus()
        )
        self._le_creds_pass.returnPressed.connect(self._on_creds_login_clicked)
        self._le_creds_user.textChanged.connect(
            lambda _: self._clear_field_error(self._le_creds_user)
        )
        self._le_creds_pass.textChanged.connect(
            lambda _: self._clear_field_error(self._le_creds_pass)
        )

        self._btn_pw_login.clicked.connect(self._on_pw_login_clicked)
        self._le_pw_pass.returnPressed.connect(self._on_pw_login_clicked)
        self._le_pw_pass.textChanged.connect(
            lambda _: self._clear_field_error(self._le_pw_pass)
        )
        self._link_switch.clicked.connect(self._on_switch_account)
        self._link_delete.clicked.connect(self._on_delete_current_profile)

        self._btn_add_profile.clicked.connect(self._on_add_connection)

    def _clear_field_error(self, field: QWidget) -> None:
        _set_field_error(field, False)

    def navigate_to_initial(self) -> None:
        profiles = self._pm.load_all()
        if not profiles:
            self.show_server_page()
            return

        last_id = self._pm.get_last_used_id()
        if len(profiles) == 1:
            self._current_profile = profiles[0]
            self.show_password_page()
        elif last_id:
            match = next((p for p in profiles if p.id == last_id), None)
            if match:
                self._current_profile = match
                self.show_password_page()
            else:
                self.show_profiles_page()
        else:
            self.show_profiles_page()

    def show_server_page(self, clear_url: bool = False) -> None:
        _hide_banner(self._srv_banner)
        _set_field_error(self._le_server, False)
        self._set_server_form_enabled(True)
        self._btn_connect.setText(self.tr("Continue"))

        if clear_url:
            self._le_server.clear()
            self._setup_server_url = ""

        has_profiles = bool(self._pm.load_all())
        self._link_back_to_profiles.setVisible(has_profiles)

        self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_server)
        self._le_server.setFocus()

    def show_creds_page(self) -> None:
        _hide_banner(self._creds_banner)
        _set_field_error(self._le_creds_user, False)
        _set_field_error(self._le_creds_pass, False)
        self._set_creds_form_enabled(True)
        self._btn_creds_login.setText(self.tr("Login"))

        host = self._setup_server_url.split("://", 1)[-1].rstrip("/").split("/", 1)[0]
        self._creds_server_lbl.setText(host)

        self._le_creds_user.clear()
        self._le_creds_pass.clear()
        self._le_creds_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_creds)
        self._le_creds_user.setFocus()
        self._refresh_creds_mode()

    def show_password_page(self) -> None:
        p = self._current_profile
        if p is None:
            self.show_server_page()
            return

        _hide_banner(self._pw_banner)
        _set_field_error(self._le_pw_pass, False)
        self._set_pw_form_enabled(True)
        self._btn_pw_login.setText(self.tr("Login"))
        self._le_pw_pass.clear()
        self._le_pw_pass.setEchoMode(QLineEdit.EchoMode.Password)

        is_sso = p.is_negotiate
        self._le_pw_pass.setVisible(not is_sso)

        self._populate_password_page(p)
        self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_password)
        if is_sso:
            self._btn_pw_login.setFocus()
        else:
            self._le_pw_pass.setFocus()

    def show_profiles_page(self) -> None:
        self._populate_profiles_list()
        self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_profiles)

    def _populate_password_page(self, profile: Profile) -> None:
        while self._pw_identity_host.count():
            item = self._pw_identity_host.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        avatar = _avatar_label(self._pg_password, profile, _AVATAR_BIG)
        self._pw_identity_host.addWidget(avatar, 0, Qt.AlignCenter)

        name_lbl = QLabel(profile.username, self._pg_password)
        name_lbl.setObjectName("lblPasswordUsername")
        name_lbl.setAlignment(Qt.AlignCenter)
        self._pw_identity_host.addWidget(name_lbl)

        detail = profile.host
        if profile.auth_name:
            detail += f"  ·  {profile.auth_name}"

        sub = QLabel(detail, self._pg_password)
        sub.setObjectName("lblPasswordDetail")
        sub.setAlignment(Qt.AlignCenter)
        self._pw_identity_host.addWidget(sub)

    def _populate_profiles_list(self) -> None:
        layout = self._profiles_list_layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        profiles = self._pm.load_all()
        last_id = self._pm.get_last_used_id()
        profiles.sort(key=lambda p: p.id != last_id)

        for p in profiles:
            card = ProfileCard(p, self._profiles_list_widget)
            card.clicked.connect(lambda prof=p: self._on_profile_selected(prof))
            card.delete_clicked.connect(lambda prof=p: self._on_delete_profile(prof))
            layout.addWidget(card)

        layout.addStretch()

    def _on_connect_clicked(self) -> None:
        _hide_banner(self._srv_banner)
        _set_field_error(self._le_server, False)

        url = self._le_server.text().strip().rstrip("/")
        if not url:
            _set_field_error(self._le_server, True)
            _show_banner(
                self._srv_banner, self.tr("The server url/token is not specified")
            )
            return
        # if not _URL_RE.match(url):
        #     _set_field_error(self._le_server, True)
        #     _show_banner(self._srv_banner, self.tr("The address must start with http:// or https://"))
        #     return

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            self._le_server.setText(url)

        # if not _URL_RE.match(url):
        #     _set_field_error(self._le_server, True)
        #     _show_banner(self._srv_banner, self.tr("Invalid server address"))
        #     return

        self._setup_server_url = url
        self._set_server_form_enabled(False)
        self._btn_connect.setText(self.tr("Connection..."))
        self.authenticators_requested.emit(url)

    def _on_creds_login_clicked(self) -> None:
        _hide_banner(self._creds_banner)

        meta = self._current_auth_meta()
        methods = meta.get("login_methods", [])
        auth_id = str(meta.get("id", self._cmb_auth.currentData() or ""))
        spn = str(meta.get("spn", ""))

        user = self._le_creds_user.text().strip()
        pwd = self._le_creds_pass.text()

        _set_field_error(self._le_creds_user, False)
        _set_field_error(self._le_creds_pass, False)

        if not auth_id:
            _show_banner(self._creds_banner, self.tr("Select an authenticator"))
            return

        if "negotiate" in methods and not user and not pwd:
            self._set_creds_form_enabled(False)
            self._btn_creds_login.setText(self.tr("Signing in..."))
            self.negotiate_requested.emit(self._setup_server_url, auth_id, spn)
            return

        # Password path
        errors: list[str] = []

        if not user:
            _set_field_error(self._le_creds_user, True)
            errors.append(self.tr("Enter the username"))
        if not pwd:
            _set_field_error(self._le_creds_pass, True)
            errors.append(self.tr("Enter password"))

        if errors:
            if "negotiate" in methods:
                _show_banner(
                    self._creds_banner,
                    self.tr("Enter username and password, or leave both fields empty for automatic login"),
                )
            else:
                _show_banner(self._creds_banner, errors[0])
            return

        self._set_creds_form_enabled(False)
        self._btn_creds_login.setText(self.tr("Log in..."))
        self.login_requested.emit(self._setup_server_url, auth_id, user, pwd)

    def _on_pw_login_clicked(self) -> None:
        _hide_banner(self._pw_banner)
        _set_field_error(self._le_pw_pass, False)

        p = self._current_profile
        if p is None:
            return

        if p.is_negotiate:
            self._set_pw_form_enabled(False)
            self._btn_pw_login.setText(self.tr("Signing in..."))
            self.negotiate_requested.emit(p.server_url, p.auth_id, p.spn)
            return

        pwd = self._le_pw_pass.text()
        if not pwd:
            _set_field_error(self._le_pw_pass, True)
            _show_banner(self._pw_banner, self.tr("Enter password"))
            return

        self._set_pw_form_enabled(False)
        self._btn_pw_login.setText(self.tr("Log in..."))
        self.login_requested.emit(p.server_url, p.auth_id, p.username, pwd)

    def _on_profile_selected(self, profile: Profile) -> None:
        self._current_profile = profile
        self._pm.set_last_used(profile.id)
        self.show_password_page()

    def _on_add_connection(self) -> None:
        self.show_server_page(clear_url=True)

    def _on_switch_account(self) -> None:
        self.show_profiles_page()

    def _on_delete_current_profile(self) -> None:
        if self._current_profile:
            self._confirm_and_delete(self._current_profile)

    def _on_delete_profile(self, profile: Profile) -> None:
        self._confirm_and_delete(profile)
        
    def _current_auth_meta(self) -> dict:
        idx = self._cmb_auth.currentIndex()
        if idx < 0:
            return {}
        data = self._cmb_auth.itemData(idx, Qt.ItemDataRole.UserRole + 1)
        return data if isinstance(data, dict) else {}
    
    def _refresh_creds_mode(self) -> None:
        meta = self._current_auth_meta()
        methods = meta.get("login_methods", [])
        preferred = str(meta.get("preferred_method", "password"))

        negotiate_available = "negotiate" in methods

        if negotiate_available and preferred == "negotiate":
            self._le_creds_user.setPlaceholderText(self.tr("Leave empty for automatic login"))
            self._le_creds_pass.setPlaceholderText(self.tr("Leave empty for automatic login"))
        else:
            self._le_creds_user.setPlaceholderText("")
            self._le_creds_pass.setPlaceholderText("")

        self._btn_creds_login.setText(self.tr("Login"))

    def _confirm_and_delete(self, profile: Profile) -> None:
        parent_widget = (
            self._pg_profiles
            if self.ui.stackedWidgetLogin.currentWidget() is self._pg_profiles
            else self._pg_password
        )
        ok = confirm(
            parent=parent_widget,
            title=self.tr("Delete profile"),
            text=self.tr('Delete profile "{display_label}"?').format(
                display_label=profile.display_label
            ),
            confirm_text=self.tr("Delete"),
            cancel_text=self.tr("Cancel"),
            kind="danger",
        )
        if not ok:
            return

        self._pm.delete(profile.id)

        if self._current_profile and self._current_profile.id == profile.id:
            self._current_profile = None

        remaining_profiles = self._pm.load_all()
        if not remaining_profiles:
            self.show_server_page(clear_url=True)
        else:
            self.navigate_to_initial()

    def set_authenticators(self, auths: list[dict]) -> None:
        self._cmb_auth.clear()
        for a in auths:
            self._cmb_auth.addItem(a.get("name", ""), a.get("id", ""))
            idx = self._cmb_auth.count() - 1
            self._cmb_auth.setItemData(idx, a, Qt.ItemDataRole.UserRole + 1)

        if len(auths) == 1:
            self._cmb_auth.setCurrentIndex(0)

        self._set_server_form_enabled(True)
        self._btn_connect.setText(self.tr("Continue"))
        self.show_creds_page()
        self._refresh_creds_mode()

    def on_auth_fetch_failed(self, msg: str) -> None:
        self._set_server_form_enabled(True)
        self._btn_connect.setText(self.tr("Continue"))
        _show_banner(self._srv_banner, msg)
        alert(self._pg_server, self.tr("Connection error"), msg, kind="danger")

    def on_login_success(self, username: str = "") -> None:
        current = self.ui.stackedWidgetLogin.currentWidget()
        if current is self._pg_creds:
            auth_id = self._cmb_auth.currentData() or ""
            auth_name = self._cmb_auth.currentText()
            meta = self._current_auth_meta()
            methods = meta.get("login_methods", [])
            spn = str(meta.get("spn", ""))

            typed_user = self._le_creds_user.text().strip()
            typed_pass = self._le_creds_pass.text()

            if not typed_user and not typed_pass and "negotiate" in methods:
                login_method = "negotiate"
            else:
                login_method = "password"

            effective_username = typed_user or username

            existing = self._pm.find_by_connection(self._setup_server_url, auth_id)
            if existing:
                existing.auth_name = auth_name
                existing.username = effective_username or existing.username
                existing.login_method = login_method
                existing.spn = spn
                p = existing
            else:
                p = Profile(
                    server_url=self._setup_server_url,
                    auth_id=auth_id,
                    auth_name=auth_name,
                    username=effective_username,
                    login_method=login_method,
                    spn=spn,
                )
            self._pm.add_or_update(p)
            self._current_profile = p
        elif current is self._pg_password and self._current_profile:
            if username and not self._current_profile.username:
                self._current_profile.username = username
                self._pm.add_or_update(self._current_profile)
            self._pm.set_last_used(self._current_profile.id)

    def on_login_failed(self, msg: str) -> None:
        current = self.ui.stackedWidgetLogin.currentWidget()
        if current is self._pg_creds:
            self._set_creds_form_enabled(True)
            self._refresh_creds_mode()
            _show_banner(self._creds_banner, msg)
            alert(self._pg_creds, self.tr("Login failed"), msg, kind="danger")
        elif current is self._pg_password:
            self._set_pw_form_enabled(True)
            self._btn_pw_login.setText(self.tr("Login"))
            _show_banner(self._pw_banner, msg)
            alert(self._pg_password, self.tr("Login failed"), msg, kind="danger")

    def _set_server_form_enabled(self, on: bool) -> None:
        self._le_server.setEnabled(on)
        self._btn_connect.setEnabled(on)

    def _set_creds_form_enabled(self, on: bool) -> None:
        self._cmb_auth.setEnabled(on)
        self._le_creds_user.setEnabled(on)
        self._le_creds_pass.setEnabled(on)
        self._btn_creds_login.setEnabled(on)

    def _set_pw_form_enabled(self, on: bool) -> None:
        self._le_pw_pass.setEnabled(on)
        self._btn_pw_login.setEnabled(on)
        self._link_switch.setEnabled(on)
        self._link_delete.setEnabled(on)
