from __future__ import annotations

from PySide6.QtCore import Qt, Signal  # type: ignore
from PySide6.QtGui import QCursor  # type: ignore
from PySide6.QtWidgets import QFrame, QWidget  # type: ignore

from src.profile_manager import Profile, avatar_color
from ui.ui_profile_card import Ui_profileCard


class ProfileCard(QFrame):
    clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, profile: Profile, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_profileCard()
        self.ui.setupUi(self)

        self.profile = profile
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.ui.lblUsername.setText(profile.username)

        detail = profile.host
        if profile.auth_name:
            detail += f"  ·  {profile.auth_name}"
        self.ui.lblDetail.setText(detail)

        self.ui.lblAvatar.setText(profile.initials)
        bg = avatar_color(profile)
        self.ui.lblAvatar.setStyleSheet(f"QLabel#lblAvatar {{ background: {bg}; }}")

        self.ui.btnDelete.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.btnDelete.clicked.connect(self.delete_clicked.emit)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            if child is not self.ui.btnDelete:
                self.clicked.emit()
        super().mousePressEvent(event)
