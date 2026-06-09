from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal, QEvent # type: ignore
from PySide6.QtGui import QCursor # type: ignore
from PySide6.QtWidgets import QFrame, QWidget # type: ignore

from src.service_image_loader import ServiceImageLoader
from ui.ui_app_card import Ui_appCard

log = logging.getLogger(__name__)


class AppCard(QFrame):
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
        self.ui = Ui_appCard()
        self.ui.setupUi(self)

        self.service = service
        self._favorite = False

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setObjectName("appCard")

        title = (getattr(service, "visual_name", "") or getattr(service, "name", "") or "Unknown app").strip()
        description = (getattr(service, "description", "") or "").strip()

        self.ui.lblAppName.setText(title)
        self.ui.lblAppName.setWordWrap(True)
        self.ui.lblAppName.setAlignment(Qt.AlignCenter)
        self.ui.lblAppName.setToolTip(description or title)

        initials = "".join(part[:1] for part in title.split()[:2]).upper() or "A"
        image_id = getattr(service, "image_id", "")
        if image_loader is not None:
            image_loader.load_into_label(
                image_id,
                self.ui.lblAppIcon,
                fallback_text=initials,
            )
        else:
            self.ui.lblAppIcon.setText(initials)
            self.ui.lblAppIcon.setAlignment(Qt.AlignCenter)

        self.ui.btnAppFavorite.setCheckable(True)
        self.ui.btnAppFavorite.toggled.connect(self._on_favorite_toggled)
        self._sync_favorite_text(False)

        self.ui.btnAppMenu.setText("⋯")
        self.ui.btnAppMenu.clicked.connect(lambda: self.menu_clicked.emit(self.service))

        self._blocked_widgets = {
            getattr(self.ui, "btnAppAction", None),
            getattr(self.ui, "btnAppFavorite", None),
            getattr(self.ui, "btnAppMenu", None),
        }
        self._install_click_forwarding()

        tooltip = description or getattr(service, "status_text", "") or title
        self.setToolTip(tooltip)

    def set_favorite(self, checked: bool) -> None:
        self.ui.btnAppFavorite.blockSignals(True)
        self.ui.btnAppFavorite.setChecked(checked)
        self.ui.btnAppFavorite.blockSignals(False)
        self._favorite = checked
        self._sync_favorite_text(checked)

    def _sync_favorite_text(self, checked: bool) -> None:
        self.ui.btnAppFavorite.setText("★" if checked else "☆")

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
