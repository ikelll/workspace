from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal, QEvent # type: ignore
from PySide6.QtGui import QCursor # type: ignore
from PySide6.QtWidgets import QFrame, QWidget # type: ignore

from src.service_image_loader import ServiceImageLoader
from ui.ui_desktop_card import Ui_desktopCard

log = logging.getLogger(__name__)


class DesktopCard(QFrame):
    clicked = Signal(object)
    action_clicked = Signal(object, str)
    favorite_clicked = Signal(object, bool)
    menu_clicked = Signal(object)

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
        group = getattr(service, "group", None)
        group_name = (getattr(group, "name", "") or "").strip()
        status = (getattr(service, "status_text", "") or "").strip()
        subtitle = " · ".join(part for part in (group_name, status) if part) or "Virtual desktop"
        description = (getattr(service, "description", "") or "").strip()
        default_transport = getattr(service, "default_transport", None)
        transport_type = (getattr(default_transport, "transport_type", "") or getattr(default_transport, "name", "") or "—").strip()

        self.ui.lblDesktopName.setText(name)
        self.ui.lblDesktopName.setToolTip(description or name)
        self.ui.lblDesktopTransport.setText(self.tr("Transport: {type}").format(type=transport_type))
        self.ui.lblDesktopSubtitle.setText(subtitle)

        initials = "".join(part[:1] for part in name.split()[:2]).upper() or "D"
        image_id = getattr(service, "image_id", "")
        log.debug(
            "Build DesktopCard: service=%r image_id=%r label=%s size=%sx%s",
            name,
            image_id,
            self.ui.lblDesktopIcon.objectName(),
            self.ui.lblDesktopIcon.width(),
            self.ui.lblDesktopIcon.height(),
        )
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
            lambda: self.menu_clicked.emit(self.service)
        )

        self._blocked_widgets = {
            getattr(self.ui, "btnDesktopFavorite", None),
            getattr(self.ui, "btnDesktopMenu", None),
        }
        self._install_click_forwarding()

        tooltip = description or subtitle or name
        self.setToolTip(tooltip)

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
