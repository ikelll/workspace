from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QSettings, Signal  # type: ignore
from PySide6.QtWidgets import QApplication  # type: ignore

from src.utils.resource_utils import read_text_resource

log = logging.getLogger(__name__)


class ThemeManager(QObject):

    theme_changed = Signal(str)

    def __init__(self, settings: QSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._current = str(settings.value("ui/theme", "light") or "light")

    @property
    def current(self) -> str:
        return self._current

    def apply(self, theme_name: str) -> None:
        normalized = "dark" if str(theme_name).strip().lower() == "dark" else "light"
        app = QApplication.instance()
        if app is None:
            return

        self._current = normalized
        self._settings.setValue("ui/theme", normalized)
        self._settings.sync()

        stylesheet = self._load_stylesheet(normalized)
        app.setProperty("theme", normalized)
        app.setStyleSheet(stylesheet)

        log.info("Theme changed to %s", normalized)
        self.theme_changed.emit(normalized)

    def toggle(self) -> None:
        self.apply("dark" if self._current == "light" else "light")

    @staticmethod
    def _load_stylesheet(theme: str) -> str:
        stylesheet = read_text_resource(":/styles/styles.qss")
        if theme == "dark":
            dark_stylesheet = read_text_resource(":/styles/styles_dark.qss")
            if dark_stylesheet:
                stylesheet = (stylesheet + "\n\n" + dark_stylesheet) if stylesheet else dark_stylesheet
        return stylesheet
