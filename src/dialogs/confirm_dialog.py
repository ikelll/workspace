from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtWidgets import QDialog, QSpacerItem, QWidget  # type: ignore

from ui.ui_confirm_dialog import Ui_dlgConfirm


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        text: str,
        confirm_text: str = "OK",
        cancel_text: str = "Cancel",
        kind: str = "primary",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.ui = Ui_dlgConfirm()
        self.ui.setupUi(self)

        self.setWindowModality(Qt.WindowModal)
        self.setMinimumSize(420, 220)
        self.setMaximumSize(760, 540)
        self.resize(520, 300 if len(text) > 180 else 220)

        self.ui.lblDialogTitle.setWordWrap(True)
        self.ui.lblDialogText.setWordWrap(True)

        self.ui.lblDialogTitle.setText(title)
        self.ui.lblDialogText.setText(text)
        self.ui.btnDialogConfirm.setText(confirm_text)
        self.ui.btnDialogCancel.setText(cancel_text)

        show_cancel = bool(cancel_text.strip())
        self.ui.btnDialogCancel.setVisible(show_cancel)
        if hasattr(self.ui, "horizontalSpacer"):
            spacer = getattr(self.ui, "horizontalSpacer")
            if isinstance(spacer, QSpacerItem):
                spacer.changeSize(40 if show_cancel else 0, 20)

        self.ui.btnDialogCancel.clicked.connect(self.reject)
        self.ui.btnDialogConfirm.clicked.connect(self.accept)

        self.setProperty("dialogKind", kind)
        self.ui.btnDialogConfirm.setProperty("dialogKind", kind)

        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
