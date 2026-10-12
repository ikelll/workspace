from __future__ import annotations

import logging

from PySide6.QtCore import QEventLoop, QObject, Property, Signal, Slot  # type: ignore

from src.dialogs import app_dialogs

log = logging.getLogger(__name__)


class QmlPrompter(QObject):

    changed = Signal()
    requested = Signal(int, str, str, str, str, str)
    _released = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._next_id = 1
        self._loops: dict[int, QEventLoop] = {}
        self._answers: dict[int, bool] = {}
        self._visible_id: int | None = None
        self._closed = False
        app_dialogs.set_prompt_backend(self.ask)

    @Property(bool, notify=changed)
    def active(self) -> bool:
        return bool(self._loops)

    def ask(self, kind: str, title: str, text: str, confirm_text: str, cancel_text: str) -> bool:
        if self._closed:
            return False
        prompt_id = self._next_id
        self._next_id += 1

        while self._visible_id is not None and not self._closed:
            waiter = QEventLoop()
            self._released.connect(waiter.quit)
            try:
                waiter.exec()
            finally:
                self._released.disconnect(waiter.quit)
        if self._closed:
            return False

        loop = QEventLoop()
        self._loops[prompt_id] = loop
        self._visible_id = prompt_id
        self.changed.emit()
        self.requested.emit(prompt_id, kind, title, text, confirm_text, cancel_text)
        if prompt_id not in self._answers:
            loop.exec()
        self._loops.pop(prompt_id, None)
        self.changed.emit()
        return self._answers.pop(prompt_id, False)

    @Slot(int, bool)
    def answer(self, prompt_id: int, accepted: bool) -> None:
        if prompt_id not in self._loops or prompt_id in self._answers:
            return
        self._answers[prompt_id] = bool(accepted)
        if self._visible_id == prompt_id:
            self._visible_id = None
            self._released.emit()
        loop = self._loops.get(prompt_id)
        if loop is not None and loop.isRunning():
            loop.quit()

    def cancel_all(self) -> None:
        for prompt_id in list(self._loops):
            self.answer(prompt_id, False)
        self._released.emit()

    def shutdown(self) -> None:
        self._closed = True
        app_dialogs.close_prompts()
        self.cancel_all()
