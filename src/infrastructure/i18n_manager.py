from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QSettings, QTranslator, Signal  # type: ignore
from PySide6.QtWidgets import QApplication  # type: ignore

import resources.rc_resource as _rc_resource  # noqa: F401

log = logging.getLogger(__name__)

_SUPPORTED = {"ru_RU", "en_US"}


class I18nManager(QObject):

    language_changed = Signal(str)

    def __init__(self, settings: QSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._translator = QTranslator(self)
        self._current = str(settings.value("ui/language", "ru_RU") or "ru_RU")

    @property
    def current(self) -> str:
        return self._current

    def load(self, locale_name: str) -> None:
        app = QApplication.instance()
        if app is None:
            return

        normalized = locale_name if locale_name in _SUPPORTED else "ru_RU"
        app.removeTranslator(self._translator)

        qm_path = f":/i18n/{normalized}.qm"
        loaded = self._translator.load(qm_path)
        if loaded:
            app.installTranslator(self._translator)

        self._current = normalized
        self._settings.setValue("ui/language", normalized)
        self._settings.sync()

        log.info("Language changed to %s (qm loaded=%s)", normalized, loaded)
        self.language_changed.emit(normalized)

    def toggle(self) -> None:
        self.load("en_US" if self._current.startswith("ru") else "ru_RU")
