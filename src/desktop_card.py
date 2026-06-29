from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal, QEvent, QTimer # type: ignore
from PySide6.QtGui import QCursor # type: ignore
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget # type: ignore

from src.service_image_loader import ServiceImageLoader
from ui.ui_desktop_card import Ui_desktopCard

log = logging.getLogger(__name__)


class DesktopCard(QFrame):
    clicked = Signal(object)
    action_clicked = Signal(object, str)
    favorite_clicked = Signal(object, bool)
    menu_clicked = Signal(object, object)

    def __init__(
        self,
        service,
        parent: QWidget | None = None,
        image_loader: ServiceImageLoader | None = None,
    ) -> None:
        super().__init__(parent)
        self.ui = Ui_desktopCard()
        self.ui.setupUi(self)

        self.service = service
        self._favorite = False

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setObjectName("desktopCard")

        name = (getattr(service, "visual_name", "") or getattr(service, "name", "") or "Desktop").strip()
        default_transport = getattr(service, "default_transport", None)
        transport_name = (getattr(default_transport, "name", "") or getattr(default_transport, "transport_type", "") or "—").strip()
        service_status = (getattr(service, "status_text", "") or "").strip()
        status_code = str(getattr(service, "status_code", "") or "").strip().lower()

        self.ui.lblDesktopName.setText(name)
        self._setup_status_indicator(status_code, service_status)
        self.ui.lblDesktopTransport.setText(self.tr("Transport: {name}").format(name=transport_name))

        initials = "".join(part[:1] for part in name.split()[:2]).upper() or "D"
        image_id = getattr(service, "image_id", "")
        # log.debug(
        #     "Build DesktopCard: service=%r image_id=%r label=%s size=%sx%s",
        #     name,
        #     image_id,
        #     self.ui.lblDesktopIcon.objectName(),
        #     self.ui.lblDesktopIcon.width(),
        #     self.ui.lblDesktopIcon.height(),
        # )
        if image_loader is not None:
            image_loader.load_into_label(
                image_id,
                self.ui.lblDesktopIcon,
                fallback_text=initials,
            )
        else:
            log.debug("DesktopCard has no image loader, fallback initials will be shown: service=%r", name)
            self.ui.lblDesktopIcon.setText(initials)
            self.ui.lblDesktopIcon.setAlignment(Qt.AlignCenter)

        self.ui.btnDesktopFavorite.setCheckable(True)
        self.ui.btnDesktopFavorite.toggled.connect(self._on_favorite_toggled)
        self._sync_favorite_text(False)

        self.ui.btnDesktopMenu.setText("⋯")
        self.ui.btnDesktopMenu.clicked.connect(
            lambda: self.menu_clicked.emit(self.service, self.ui.btnDesktopMenu)
        )

        self._blocked_widgets = {
            getattr(self.ui, "btnDesktopFavorite", None),
            getattr(self.ui, "btnDesktopMenu", None),
        }
        self._install_click_forwarding()

    def _setup_status_indicator(self, status_code: str, service_status: str) -> None:
        status_code = (status_code or "available").strip().lower()
        service_status = service_status or self.tr("Available")

        self._status_dot = QLabel("●", self)
        self._status_dot.setObjectName("lblDesktopStatusDot")
        self._status_dot.setProperty("status", self._status_dot_kind(status_code))
        self._status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_dot.setFixedWidth(14)
        self._status_dot.setToolTip(service_status)

        status_row = QWidget(self)
        status_row.setObjectName("wDesktopStatusRow")
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)

        self.ui.verticalLayout_3.removeWidget(self.ui.lblDesktopStatus)
        status_layout.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.ui.lblDesktopStatus, 1)
        self.ui.verticalLayout_3.insertWidget(0, status_row)

        self.ui.lblDesktopStatus.setText(self.tr("Status: {status}").format(status=service_status))

        self._status_blink_visible = True
        self._status_blink_timer: QTimer | None = None
        if self._status_dot_blinks(status_code):
            self._status_blink_timer = QTimer(self)
            self._status_blink_timer.setInterval(650)
            self._status_blink_timer.timeout.connect(self._toggle_status_dot)
            self._status_blink_timer.start()

    @staticmethod
    def _status_dot_kind(status_code: str) -> str:
        if status_code in {"on", "available", "in_use"}:
            return "ok"
        if status_code in {"off", "unavailable"}:
            return "danger"
        if status_code == "maintenance":
            return "maintenance"
        if status_code in {"powering_on", "powering_off", "rebooting", "preparing"}:
            return "progress"
        return "unknown"

    @staticmethod
    def _status_dot_blinks(status_code: str) -> bool:
        return status_code in {
            "off",
            "unavailable",
            "powering_on",
            "powering_off",
            "rebooting",
            "preparing",
        }

    def _toggle_status_dot(self) -> None:
        dot = getattr(self, "_status_dot", None)
        if dot is None:
            return
        self._status_blink_visible = not self._status_blink_visible
        dot.setText("●" if self._status_blink_visible else "○")

    def set_menu_available(self, available: bool) -> None:
        self.ui.btnDesktopMenu.setEnabled(available)
        self.ui.btnDesktopMenu.setToolTip(
            self.tr("Service menu") if available else self.tr("No actions available")
        )

    def set_favorite(self, checked: bool) -> None:
        self.ui.btnDesktopFavorite.blockSignals(True)
        self.ui.btnDesktopFavorite.setChecked(checked)
        self.ui.btnDesktopFavorite.blockSignals(False)
        self._favorite = checked
        self._sync_favorite_text(checked)

    def _sync_favorite_text(self, checked: bool) -> None:
        self.ui.btnDesktopFavorite.setText("★" if checked else "☆")

    def _on_favorite_toggled(self, checked: bool) -> None:
        self._favorite = checked
        self._sync_favorite_text(checked)
        self.favorite_clicked.emit(self.service, checked)

    def _install_click_forwarding(self) -> None:
        self.installEventFilter(self)
        for widget in self.findChildren(QWidget):
            widget.installEventFilter(self)
            if widget not in self._blocked_widgets:
                widget.setCursor(QCursor(Qt.PointingHandCursor))

    def _is_blocked_target(self, widget: QWidget | None) -> bool:
        current = widget
        while current is not None and current is not self:
            if current in self._blocked_widgets:
                return True
            current = current.parentWidget()
        return False

    def eventFilter(self, watched, event) -> bool:
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and getattr(event, "button", lambda: None)() == Qt.MouseButton.LeftButton
            and isinstance(watched, QWidget)
            and not self._is_blocked_target(watched)
        ):
            self.clicked.emit(self.service)
            event.accept()
            return True
        return super().eventFilter(watched, event)
