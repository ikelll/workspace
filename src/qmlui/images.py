from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import QByteArray, QObject, QSize, Qt, Signal  # type: ignore
from PySide6.QtGui import QImage, QPainter  # type: ignore
from PySide6.QtQuick import QQuickImageProvider  # type: ignore

from src.api import endpoints as ep
from src.api.client import ApiClient

log = logging.getLogger(__name__)

PROVIDER_ID = "services"
_SVG_SIZE = QSize(128, 128)


class ServiceImageStore(QObject):

    changed = Signal()

    def __init__(self, client: ApiClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._cache: dict[str, QImage] = {}
        self._failed: set[str] = set()
        self._pending: dict[str, list[Callable[[QImage | None], None]]] = {}
        self._version = 0

    @property
    def version(self) -> int:
        return self._version

    def image(self, image_id: str) -> QImage | None:
        return self._cache.get(str(image_id or "").strip())

    def has(self, image_id: str) -> bool:
        return str(image_id or "").strip() in self._cache

    def clear(self) -> None:
        self._cache.clear()
        self._failed.clear()
        self._pending.clear()
        self._version += 1
        self.changed.emit()

    @staticmethod
    def _normalize(image_ids: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for raw in image_ids:
            normalized = str(raw or "").strip()
            if not normalized or normalized.lower() == "x" or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique

    def preload(self, image_ids: list[str], on_complete: Callable[[list[str]], None]) -> None:
        unique = [
            i for i in self._normalize(image_ids)
            if i not in self._cache and i not in self._failed
        ]
        if not unique:
            on_complete([])
            return
        failures: list[str] = []
        remaining = {"count": len(unique)}

        def _done(image_id: str, image: QImage | None) -> None:
            if image is None or image.isNull():
                failures.append(image_id)
            remaining["count"] -= 1
            if remaining["count"] <= 0:
                on_complete(failures)

        for image_id in unique:
            self._request(image_id, lambda image, image_id=image_id: _done(image_id, image))

    def _request(self, image_id: str, callback: Callable[[QImage | None], None]) -> None:
        cached = self._cache.get(image_id)
        if cached is not None:
            callback(cached)
            return
        if image_id in self._pending:
            self._pending[image_id].append(callback)
            return
        self._pending[image_id] = [callback]
        self._client.get_bytes(
            ep.service_image(image_id),
            on_success=lambda raw, content_type: self._on_loaded(image_id, raw, content_type),
            on_error=lambda msg, code: self._on_failed(image_id, msg, code),
        )

    def _on_loaded(self, image_id: str, raw: bytes, content_type: object) -> None:
        raw = bytes(raw)
        content_type = bytes(content_type).decode("latin-1", errors="replace") if isinstance(content_type, (bytes, bytearray, memoryview)) else str(content_type or "")
        if not isinstance(content_type, str):
            content_type = str(content_type)
        image = self._decode(raw, content_type)
        if image is not None and not image.isNull():
            self._cache[image_id] = image
            self._version += 1
            self.changed.emit()
        else:
            self._failed.add(image_id)
            log.warning("Image decode failed: image_id=%s bytes=%d content_type=%r", image_id, len(raw), content_type)
        for callback in self._pending.pop(image_id, []):
            callback(image)

    def _on_failed(self, image_id: str, msg: str, code: int) -> None:
        log.warning("Failed to load image %s: %s (status=%d)", image_id, msg, code)
        self._failed.add(image_id)
        for callback in self._pending.pop(image_id, []):
            callback(None)

    @staticmethod
    def _looks_like_svg(raw: bytes, content_type: str) -> bool:
        if "svg" in str(content_type or "").lower():
            return True
        head = raw[:512].lstrip().lower()
        return head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head)

    @classmethod
    def _decode(cls, raw: bytes, content_type: str) -> QImage | None:
        if not raw:
            return None
        if cls._looks_like_svg(raw, content_type):
            return cls._render_svg(raw)
        image = QImage.fromData(QByteArray(raw))
        return image if not image.isNull() else None

    @staticmethod
    def _render_svg(raw: bytes) -> QImage | None:
        try:
            from PySide6.QtSvg import QSvgRenderer  # type: ignore
        except Exception:  # pragma: no cover
            return None
        renderer = QSvgRenderer(QByteArray(raw))
        if not renderer.isValid():
            return None
        image = QImage(_SVG_SIZE, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return image


class ServiceImageProvider(QQuickImageProvider):

    def __init__(self, store: ServiceImageStore) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._store = store

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:  # noqa: N802
        key = str(image_id or "").split("?", 1)[0]
        image = self._store.image(key)
        if image is None:
            return QImage()
        if requested_size.isValid() and requested_size.width() > 0 and requested_size.height() > 0:
            image = image.scaled(requested_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return image
