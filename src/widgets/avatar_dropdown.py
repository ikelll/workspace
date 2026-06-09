from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .unified_combobox import UnifiedComboBox


class AvatarDropdownPopup(QWidget):
    language_selected = Signal(str)
    theme_selected = Signal(str)
    settings_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("avatarDropdownPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.card = QFrame(self)
        self.card.setObjectName("avatarDropdownCard")
        root.addWidget(self.card)

        effect = QGraphicsDropShadowEffect(self.card)
        effect.setBlurRadius(30)
        effect.setOffset(0, 10)
        effect.setColor(Qt.black)
        self.card.setGraphicsEffect(effect)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        self.lblTitle = QLabel(self.card)
        self.lblTitle.setObjectName("lblAvatarDropdownTitle")
        card_layout.addWidget(self.lblTitle)

        self.lblSubtitle = QLabel(self.card)
        self.lblSubtitle.setObjectName("lblAvatarDropdownSubtitle")
        self.lblSubtitle.setWordWrap(True)
        card_layout.addWidget(self.lblSubtitle)

        self._add_combo_row(
            card_layout,
            label_name="lblAvatarDropdownLanguage",
            combo_name="cmbAvatarDropdownLanguage",
            attr_label="lblLanguage",
            attr_combo="cmbLanguage",
        )
        self._add_combo_row(
            card_layout,
            label_name="lblAvatarDropdownTheme",
            combo_name="cmbAvatarDropdownTheme",
            attr_label="lblTheme",
            attr_combo="cmbTheme",
        )

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        actions.setSpacing(10)
        card_layout.addLayout(actions)

        self.btnSettings = QPushButton(self.card)
        self.btnSettings.setObjectName("btnAvatarDropdownAction")
        self.btnSettings.setCursor(Qt.CursorShape.PointingHandCursor)
        actions.addWidget(self.btnSettings, 1)

        self.btnLogout = QPushButton(self.card)
        self.btnLogout.setObjectName("btnAvatarDropdownDanger")
        self.btnLogout.setCursor(Qt.CursorShape.PointingHandCursor)
        actions.addWidget(self.btnLogout, 1)

        self._populate_defaults()
        self._wire_events()

        self.resize(292, self.sizeHint().height())

    def _add_combo_row(
        self,
        layout: QVBoxLayout,
        *,
        label_name: str,
        combo_name: str,
        attr_label: str,
        attr_combo: str,
    ) -> None:
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(6)
        layout.addLayout(wrapper)

        label = QLabel(self.card)
        label.setObjectName(label_name)
        wrapper.addWidget(label)

        combo = UnifiedComboBox(self.card)
        combo.setObjectName(combo_name)
        combo.setProperty("comboVariant", "compact")
        combo.setMinimumWidth(0)
        combo.setSizeAdjustPolicy(UnifiedComboBox.SizeAdjustPolicy.AdjustToContents)
        wrapper.addWidget(combo)

        setattr(self, attr_label, label)
        setattr(self, attr_combo, combo)

    def _populate_defaults(self) -> None:
        self._fill_combo(
            self.cmbLanguage,
            [("ru_RU", "Русский"), ("en_US", "English")],
        )
        self._fill_combo(
            self.cmbTheme,
            [("light", "Light"), ("dark", "Dark")],
        )

    def _wire_events(self) -> None:
        self.cmbLanguage.currentIndexChanged.connect(self._emit_language)
        self.cmbTheme.currentIndexChanged.connect(self._emit_theme)
        self.btnSettings.clicked.connect(self._on_settings_clicked)
        self.btnLogout.clicked.connect(self._on_logout_clicked)

    def _fill_combo(self, combo: UnifiedComboBox, items: Iterable[tuple[str, str]]) -> None:
        combo.blockSignals(True)
        combo.clear()
        for value, text in items:
            combo.addItem(text, value)
        combo.blockSignals(False)

    def set_translations(
        self,
        *,
        title: str,
        subtitle: str,
        language_label: str,
        theme_label: str,
        settings_text: str,
        logout_text: str,
        light_text: str,
        dark_text: str,
    ) -> None:
        self.lblTitle.setText(title)
        self.lblSubtitle.setText(subtitle)
        self.lblLanguage.setText(language_label)
        self.lblTheme.setText(theme_label)
        self.btnSettings.setText(settings_text)
        self.btnLogout.setText(logout_text)

        current_language = self.current_language()
        current_theme = self.current_theme()

        self._fill_combo(
            self.cmbLanguage,
            [("ru_RU", "Русский"), ("en_US", "English")],
        )
        self._fill_combo(
            self.cmbTheme,
            [("light", light_text), ("dark", dark_text)],
        )
        self.set_language(current_language)
        self.set_theme(current_theme)

    def current_language(self) -> str:
        return str(self.cmbLanguage.currentData() or "ru_RU")

    def current_theme(self) -> str:
        return str(self.cmbTheme.currentData() or "light")

    def set_language(self, locale_name: str) -> None:
        self._set_combo_value(self.cmbLanguage, locale_name or "ru_RU")

    def set_theme(self, theme_name: str) -> None:
        self._set_combo_value(self.cmbTheme, theme_name or "light")

    def _set_combo_value(self, combo: UnifiedComboBox, value: str) -> None:
        combo.blockSignals(True)
        try:
            index = max(0, combo.findData(value))
            combo.setCurrentIndex(index)
        finally:
            combo.blockSignals(False)

    def popup_for(self, anchor: QWidget) -> None:
        self.adjustSize()
        width = max(292, self.sizeHint().width())
        self.resize(width, self.sizeHint().height())

        anchor_global = anchor.mapToGlobal(QPoint(anchor.width() - self.width(), anchor.height() + 10))
        target = QPoint(anchor_global.x(), anchor_global.y())

        screen = QGuiApplication.screenAt(anchor.mapToGlobal(anchor.rect().center())) or anchor.screen()
        if screen is not None:
            available = screen.availableGeometry()
            if target.x() + self.width() > available.right():
                target.setX(max(available.left(), available.right() - self.width()))
            if target.y() + self.height() > available.bottom():
                target.setY(anchor.mapToGlobal(QPoint(anchor.width() - self.width(), -self.height() - 8)).y())
            if target.y() < available.top():
                target.setY(max(available.top(), anchor.mapToGlobal(QPoint(0, anchor.height() + 8)).y()))

        self.move(target)
        self.show()
        self.raise_()
        self.activateWindow()

    def _emit_language(self, _index: int) -> None:
        self.hide()
        self.language_selected.emit(self.current_language())

    def _emit_theme(self, _index: int) -> None:
        self.hide()
        self.theme_selected.emit(self.current_theme())

    def _on_settings_clicked(self) -> None:
        self.hide()
        self.settings_requested.emit()

    def _on_logout_clicked(self) -> None:
        self.hide()
        self.logout_requested.emit()
