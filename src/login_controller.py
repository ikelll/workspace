from __future__ import annotations

import base64
import html as html_lib
import re

from PySide6.QtCore import QCoreApplication, QObject, QSettings, Qt, Signal  # type: ignore
from PySide6.QtGui import QAction, QPixmap  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QLabel,
    QLayout,
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

_URL_RE = re.compile(r"^https?://[A-Z0-9\-.]+(:\d{1,5})?(/.*)?$", re.I)
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

def _set_layout_alignment(layout: QLayout | None, widget: QWidget, alignment: Qt.AlignmentFlag) -> bool:
    if layout is None:
        return False
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item.widget() is widget:
            layout.setAlignment(widget, alignment)
            return True
        if _set_layout_alignment(item.layout(), widget, alignment):
            return True
    return False


def _center_widget_in_parent_layout(widget: QWidget | None) -> None:
    if widget is None:
        return
    parent = widget.parentWidget()
    while parent is not None:
        if _set_layout_alignment(parent.layout(), widget, Qt.AlignCenter):
            return
        parent = parent.parentWidget()


def _setup_logo(label: QLabel, pixmap: QPixmap) -> None:
    label.setScaledContents(False)
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignCenter)
    label.setFixedHeight(int(pixmap.height() / pixmap.devicePixelRatio()) + 8)
    _center_widget_in_parent_layout(label)


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
    mfa_verify_requested = Signal(str, str, bool)

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
        self._pg_mfa_legacy = getattr(self.ui, "pageMfa", None)
        self._pg_mfa_setup = getattr(self.ui, "pageMfaSetup", None)
        self._pg_mfa_verify = getattr(self.ui, "pageMfaVerify", None)
        self._pg_mfa = self._pg_mfa_verify or self._pg_mfa_setup or self._pg_mfa_legacy
        self._mfa_origin_page: QWidget | None = None
        self._mfa_token = ""
        self._mfa_setup_was_shown = False

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

        self._mfa_setup_title_lbl = getattr(self.ui, "lblMfaSetupTitle", None)
        self._mfa_setup_description_lbl = getattr(self.ui, "lblMfaSetupDescription", None)
        self._mfa_setup_qr_lbl = getattr(self.ui, "lblMfaSetupQrCode", getattr(self.ui, "lblMfaQrCode", None))
        self._mfa_setup_message_lbl = getattr(self.ui, "lblMfaSetupMessage", None)
        self._btn_mfa_setup_continue = getattr(self.ui, "btnMfaSetupContinue", None)
        self._btn_mfa_setup_back = getattr(self.ui, "btnMfaSetupBack", None)

        self._mfa_banner = getattr(self.ui, "lblMfaErrorBanner", None)
        self._mfa_title_lbl = getattr(
            self.ui,
            "lblMfaVerifyTitle",
            getattr(self.ui, "lblMfaTitle", getattr(self.ui, "lblMfaLogo_2", None)),
        )
        self._mfa_description_lbl = getattr(
            self.ui,
            "lblMfaVerifyDescription",
            getattr(self.ui, "lblMfaDescription", None),
        )
        self._mfa_message_lbl = getattr(self.ui, "lblMfaVerifyMessage", getattr(self.ui, "lblMfaMessage", None))
        self._le_mfa_code = getattr(self.ui, "leMfaCode", None)
        self._cb_mfa_remember = getattr(self.ui, "cbMfaRememberDevice", None)
        self._btn_mfa_verify = getattr(self.ui, "btnMfaVerify", None)
        self._btn_mfa_back = getattr(self.ui, "btnMfaVerifyBack", getattr(self.ui, "btnMfaBack", None))

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

        for name in (
            "lblServerLogo",
            "lblCredsLogo",
            "lblPasswordLogo",
            "lblMfaLogo",
            "lblMfaSetupLogo",
            "lblMfaVerifyLogo",
        ):
            lbl = getattr(self.ui, name, None)
            if lbl:
                _setup_logo(lbl, px)

    def _init_field_icons(self) -> None:
        self._le_server.addAction(icon_globe(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._le_creds_user.addAction(icon_user(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._le_creds_pass.addAction(icon_lock(_ICON_SIZE), QLineEdit.LeadingPosition)
        self._le_pw_pass.addAction(icon_lock(_ICON_SIZE), QLineEdit.LeadingPosition)
        if self._le_mfa_code is not None:
            self._le_mfa_code.addAction(icon_lock(_ICON_SIZE), QLineEdit.LeadingPosition)
            self._le_mfa_code.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._le_mfa_code.setPlaceholderText(self.tr("Authentication code"))
        self._eye_creds = _setup_password_toggle(self._le_creds_pass)
        self._eye_pw = _setup_password_toggle(self._le_pw_pass)

    def _init_banners(self) -> None:
        for banner in (self._srv_banner, self._creds_banner, self._pw_banner, self._mfa_banner):
            if banner is not None:
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
        if self._btn_mfa_setup_continue is not None:
            self._btn_mfa_setup_continue.clicked.connect(self._show_mfa_verify_page)
        if self._btn_mfa_setup_back is not None:
            self._btn_mfa_setup_back.clicked.connect(self._on_mfa_cancel_clicked)
        if self._btn_mfa_verify is not None:
            self._btn_mfa_verify.clicked.connect(self._on_mfa_verify_clicked)
        if self._le_mfa_code is not None:
            self._le_mfa_code.returnPressed.connect(self._on_mfa_verify_clicked)
            self._le_mfa_code.textChanged.connect(lambda _: self._clear_field_error(self._le_mfa_code))
        if self._btn_mfa_back is not None:
            self._btn_mfa_back.clicked.connect(self._on_mfa_verify_back_clicked)

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

    def show_mfa_page(self, payload: dict) -> bool:
        self._mfa_origin_page = self.ui.stackedWidgetLogin.currentWidget()
        self._mfa_setup_was_shown = False
        payload = self._normalize_mfa_payload(payload)

        if not self._stack_contains(self._pg_mfa_verify):
            self._restore_form_after_mfa_abort(
                self.tr("MFA is required, but MFA verification page is missing in UI")
            )
            return False

        self._mfa_token = str(payload.get("mfa_token", "") or "").strip()
        if not self._mfa_token:
            self._restore_form_after_mfa_abort(
                self.tr("Server did not return MFA challenge token")
            )
            return False

        if self._mfa_banner is not None:
            _hide_banner(self._mfa_banner)
        if self._le_mfa_code is not None:
            _set_field_error(self._le_mfa_code, False)
            self._le_mfa_code.clear()

        label = str(payload.get("label", "") or "").strip()
        message = str(payload.get("message", "") or "").strip()
        html = str(payload.get("html", "") or "")
        if not message and html:
            message = self._plain_text_from_html(html)
        message = self._translate_mfa_message(message)

        qr_image = str(payload.get("qr_image", "") or "").strip()
        if not qr_image and html:
            qr_image = self._extract_qr_image(html)

        has_qr = bool(qr_image)
        self._fill_mfa_setup_page(message=message, qr_image=qr_image)
        self._fill_mfa_verify_page(payload=payload, label=label, message=message, has_qr=has_qr)

        self._set_mfa_form_enabled(True)
        if has_qr and self._stack_contains(self._pg_mfa_setup):
            self._mfa_setup_was_shown = True
            self._set_mfa_setup_enabled(True)
            self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_mfa_setup)
            if self._btn_mfa_setup_continue is not None:
                self._btn_mfa_setup_continue.setFocus()
            return True

        self._show_mfa_verify_page()
        return True

    def _stack_contains(self, page: QWidget | None) -> bool:
        return page is not None and self.ui.stackedWidgetLogin.indexOf(page) >= 0

    def _is_mfa_page(self, page: QWidget | None) -> bool:
        return page in (self._pg_mfa_setup, self._pg_mfa_verify, self._pg_mfa_legacy)
    
    def _translate_mfa_message(self, message: str) -> str:
        normalized = re.sub(r"\s+", " ", message or "").strip().lower()
        if (
            "use your authenticator" in normalized
            and "google authenticator" in normalized
        ):
            return self.tr(
                "Use your authenticator app to add your account "
                "(for example, Google Authenticator, Authy, etc.)."
            )
        return message

    def _fill_mfa_setup_page(self, message: str, qr_image: str) -> None:
        if self._mfa_setup_title_lbl is not None:
            self._mfa_setup_title_lbl.setText(self.tr("Set up two-factor authentication"))
            self._mfa_setup_title_lbl.setAlignment(Qt.AlignCenter)

        if self._mfa_setup_description_lbl is not None:
            self._mfa_setup_description_lbl.setText(self.tr("Scan this QR code with your authenticator app"))
            self._mfa_setup_description_lbl.setAlignment(Qt.AlignCenter)

        if self._mfa_setup_message_lbl is not None:
            self._mfa_setup_message_lbl.setText(message)
            self._mfa_setup_message_lbl.setVisible(bool(message))
            self._mfa_setup_message_lbl.setAlignment(Qt.AlignCenter)

        self._set_mfa_qr_image(qr_image)
        _center_widget_in_parent_layout(self._mfa_setup_qr_lbl)

        if self._btn_mfa_setup_continue is not None:
            self._btn_mfa_setup_continue.setText(self.tr("I have scanned the QR code"))
        if self._btn_mfa_setup_back is not None:
            self._btn_mfa_setup_back.setText(self.tr("← Back"))

    def _fill_mfa_verify_page(self, payload: dict, label: str, message: str, has_qr: bool) -> None:
        if self._mfa_title_lbl is not None:
            self._mfa_title_lbl.setText(label or self.tr("Authentication code"))
            self._mfa_title_lbl.setAlignment(Qt.AlignCenter)

        if self._mfa_description_lbl is not None:
            if has_qr:
                text = self.tr("Enter the code from your authenticator app")
            else:
                text = self.tr("Enter the code from your authenticator app or email")
            self._mfa_description_lbl.setText(text)
            self._mfa_description_lbl.setAlignment(Qt.AlignCenter)

        if self._mfa_message_lbl is not None:
            self._mfa_message_lbl.setText("" if has_qr else message)
            self._mfa_message_lbl.setVisible(bool(message and not has_qr))
            self._mfa_message_lbl.setAlignment(Qt.AlignCenter)

        remember_text = str(payload.get("remember_device", "") or "").strip()
        if self._cb_mfa_remember is not None:
            self._cb_mfa_remember.setText(
                self.tr("Remember this device")
                if not remember_text
                else self.tr("Remember this device for {duration}").format(duration=remember_text)
            )
            self._cb_mfa_remember.setChecked(False)
            self._cb_mfa_remember.setVisible(bool(payload.get("can_remember_device", remember_text)))

    def _show_mfa_verify_page(self) -> None:
        if not self._stack_contains(self._pg_mfa_verify):
            return
        self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_mfa_verify)
        self._set_mfa_form_enabled(True)
        if self._mfa_banner is not None:
            _hide_banner(self._mfa_banner)
        if self._le_mfa_code is not None:
            _set_field_error(self._le_mfa_code, False)
            self._le_mfa_code.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._le_mfa_code.setPlaceholderText(self.tr("Authentication code"))
            self._le_mfa_code.setFocus()

    def _normalize_mfa_payload(self, payload: dict) -> dict:
        data = dict(payload or {})
        for key in ("mfa", "challenge", "data"):
            nested = data.get(key)
            if isinstance(nested, dict):
                data.update(nested)
        if not str(data.get("mfa_token", "") or "").strip():
            token = data.get("mfaToken") or data.get("challenge_token") or data.get("challengeToken")
            if token:
                data["mfa_token"] = token
        return data

    def _restore_form_after_mfa_abort(self, message: str) -> None:
        origin = self._mfa_origin_page or self.ui.stackedWidgetLogin.currentWidget()
        self._mfa_token = ""
        self._mfa_setup_was_shown = False
        if origin is self._pg_password:
            self._set_pw_form_enabled(True)
            self._btn_pw_login.setText(self.tr("Login"))
            self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_password)
            _show_banner(self._pw_banner, message)
            alert(self._pg_password, self.tr("MFA failed"), message, kind="danger")
            return
        if origin is self._pg_creds:
            self._set_creds_form_enabled(True)
            self._refresh_creds_mode()
            self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_creds)
            _show_banner(self._creds_banner, message)
            alert(self._pg_creds, self.tr("MFA failed"), message, kind="danger")
            return
        self.show_server_page()
        _show_banner(self._srv_banner, message)

    def _extract_qr_image(self, html: str) -> str:
        match = re.search(r"data:image/(?:png|jpeg);base64,([A-Z0-9+/=]+)", html or "", re.I)
        return match.group(1) if match else ""

    def _plain_text_from_html(self, html: str) -> str:
        text = re.sub(r"<img[^>]*>", " ", html or "", flags=re.I)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html_lib.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    def _set_mfa_qr_image(self, image_b64: str) -> None:
        qr_label = self._mfa_setup_qr_lbl
        if qr_label is None:
            return
        if not image_b64:
            qr_label.clear()
            qr_label.setVisible(False)
            return
        try:
            raw = base64.b64decode(image_b64)
            pixmap = QPixmap()
            if not pixmap.loadFromData(raw):
                raise ValueError("invalid QR image")
            qr_label.setPixmap(pixmap)
            qr_label.setScaledContents(True)
            qr_label.setAlignment(Qt.AlignCenter)
            _center_widget_in_parent_layout(qr_label)
            qr_label.setVisible(True)
        except Exception:
            qr_label.clear()
            qr_label.setVisible(False)

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

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            self._le_server.setText(url)

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

    def _on_mfa_verify_clicked(self) -> None:
        if self._le_mfa_code is None:
            return
        if self._mfa_banner is not None:
            _hide_banner(self._mfa_banner)
        _set_field_error(self._le_mfa_code, False)

        code = self._le_mfa_code.text().strip().replace(" ", "")
        if not code:
            _set_field_error(self._le_mfa_code, True)
            if self._mfa_banner is not None:
                _show_banner(self._mfa_banner, self.tr("Enter the authentication code"))
            return

        remember = bool(self._cb_mfa_remember and self._cb_mfa_remember.isVisible() and self._cb_mfa_remember.isChecked())
        self._set_mfa_form_enabled(False)
        if self._btn_mfa_verify is not None:
            self._btn_mfa_verify.setText(self.tr("Verifying..."))
        self.mfa_verify_requested.emit(self._mfa_token, code, remember)

    def _on_mfa_cancel_clicked(self) -> None:
        self._mfa_token = ""
        self._mfa_setup_was_shown = False
        target = self._mfa_origin_page
        if target is self._pg_password:
            self._set_pw_form_enabled(True)
            self._btn_pw_login.setText(self.tr("Login"))
            self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_password)
            self._le_pw_pass.setFocus()
        elif target is self._pg_creds:
            self._set_creds_form_enabled(True)
            self._refresh_creds_mode()
            self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_creds)
            self._le_creds_pass.setFocus()
        else:
            self.show_server_page()

    def _on_mfa_verify_back_clicked(self) -> None:
        if self._mfa_setup_was_shown and self._stack_contains(self._pg_mfa_setup):
            self.ui.stackedWidgetLogin.setCurrentWidget(self._pg_mfa_setup)
            if self._btn_mfa_setup_continue is not None:
                self._btn_mfa_setup_continue.setFocus()
            return
        self._on_mfa_cancel_clicked()

    def _on_mfa_back_clicked(self) -> None:
        self._on_mfa_cancel_clicked()

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
            self._le_creds_user.setPlaceholderText(self.tr("Username"))
            self._le_creds_pass.setPlaceholderText(self.tr("Password"))

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
        if current is self._pg_creds or (self._is_mfa_page(current) and self._mfa_origin_page is self._pg_creds):
            self._save_profile_from_creds(username)
        elif current is self._pg_password or (self._is_mfa_page(current) and self._mfa_origin_page is self._pg_password):
            self._save_profile_from_password(username)
        self._mfa_token = ""
        self._mfa_origin_page = None
        self._mfa_setup_was_shown = False

    def _save_profile_from_creds(self, username: str = "") -> None:
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

        existing = self._pm.find_by_connection(
            self._setup_server_url,
            auth_id,
            effective_username,
        )
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

    def _save_profile_from_password(self, username: str = "") -> None:
        if not self._current_profile:
            return
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
        elif self._is_mfa_page(current):
            self.on_mfa_failed(msg)

    def on_mfa_failed(self, msg: str) -> None:
        self._set_mfa_form_enabled(True)
        if self._mfa_banner is not None:
            _show_banner(self._mfa_banner, msg)
        page = self.ui.stackedWidgetLogin.currentWidget() or self._pg_mfa
        if page is not None:
            alert(page, self.tr("MFA failed"), msg, kind="danger")

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

    def _set_mfa_setup_enabled(self, on: bool) -> None:
        if self._btn_mfa_setup_continue is not None:
            self._btn_mfa_setup_continue.setEnabled(on)
        if self._btn_mfa_setup_back is not None:
            self._btn_mfa_setup_back.setEnabled(on)

    def _set_mfa_form_enabled(self, on: bool) -> None:
        if self._le_mfa_code is not None:
            self._le_mfa_code.setEnabled(on)
        if self._cb_mfa_remember is not None:
            self._cb_mfa_remember.setEnabled(on)
        if self._btn_mfa_verify is not None:
            self._btn_mfa_verify.setEnabled(on)
            self._btn_mfa_verify.setText(self.tr("Continue"))
        if self._btn_mfa_back is not None:
            self._btn_mfa_back.setEnabled(on)
