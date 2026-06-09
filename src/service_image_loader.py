from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Optional

from PySide6.QtCore import QByteArray, QObject, QSize, Qt  # type: ignore
from PySide6.QtGui import QPainter, QPixmap  # type: ignore
from PySide6.QtSvg import QSvgRenderer  # type: ignore
from PySide6.QtWidgets import QLabel  # type: ignore

from src.api import endpoints as ep
from src.api.client import ApiClient

log = logging.getLogger(__name__)

ImageCallback = Callable[[Optional[QPixmap]], None]


class ServiceImageLoader(QObject):
    def __init__(self, client: ApiClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._cache: dict[str, QPixmap] = {}
        self._pending: dict[str, list[ImageCallback]] = {}

    def load_into_label(self, image_id: str | None, label: QLabel, *, fallback_text: str = "") -> None:
        normalized = str(image_id or "").strip()
        self._apply_fallback(label, fallback_text)

        if not normalized or normalized.lower() == "x":
            return

        def _consumer(pixmap: QPixmap | None) -> None:
            try:
                if pixmap is None or pixmap.isNull():
                    return
                self._apply_pixmap(label, pixmap)
            except RuntimeError:
                return

        self._request_image(normalized, _consumer)

    def preload(self, image_ids: list[str], on_complete: Callable[[list[str]], None]) -> None:
        unique_ids: list[str] = []
        seen: set[str] = set()
        for raw in image_ids:
            normalized = str(raw or "").strip()
            if not normalized or normalized.lower() == "x" or normalized in seen:
                continue
            seen.add(normalized)
            unique_ids.append(normalized)

        if not unique_ids:
            on_complete([])
            return

        failures: list[str] = []
        remaining = {"count": len(unique_ids)}

        def _done(image_id: str, pixmap: QPixmap | None) -> None:
            if pixmap is None or pixmap.isNull():
                failures.append(image_id)
            remaining["count"] -= 1
            if remaining["count"] <= 0:
                on_complete(failures)

        for image_id in unique_ids:
            self._request_image(image_id, lambda pixmap, image_id=image_id: _done(image_id, pixmap))

    def _request_image(self, normalized: str, callback: ImageCallback) -> None:
        cached = self._cache.get(normalized)
        if cached is not None and not cached.isNull():
            callback(cached)
            return

        if normalized in self._pending:
            self._pending[normalized].append(callback)
            return

        self._pending[normalized] = [callback]
        self._client.get_bytes(
            ep.service_image(normalized),
            on_success=lambda raw, content_type: self._on_loaded(normalized, raw, content_type),
            on_error=lambda msg, code: self._on_failed(normalized, msg, code),
        )

    def _on_loaded(self, image_id: str, raw: bytes, content_type: str) -> None:
        if raw[:256].lstrip().lower().startswith((b"<!doctype html", b"<html")):
            preview = raw[:200].decode("utf-8", errors="replace").replace("\n", " ")
            log.debug("Image response looks like HTML: %s", preview)
        pixmap = self._pixmap_from_payload(raw, content_type)
        if pixmap is not None and not pixmap.isNull():
            self._cache[image_id] = pixmap
        else:
            log.warning(
                "Image decode failed: image_id=%s bytes=%d content_type=%r",
                image_id,
                len(raw),
                content_type,
            )

        callbacks = self._pending.pop(image_id, [])
        for callback in callbacks:
            callback(pixmap)

    def _on_failed(self, image_id: str, msg: str, code: int) -> None:
        log.warning("Failed to load image %s: %s (status=%d)", image_id, msg, code)
        callbacks = self._pending.pop(image_id, [])
        for callback in callbacks:
            callback(None)

    def _pixmap_from_payload(self, raw: bytes, content_type: str) -> QPixmap | None:
        if not raw:
            log.debug("Empty image payload")
            return None

        if self._looks_like_svg(raw, content_type):
            svg = self._render_svg(raw)
            if not svg.isNull():
                return svg
            log.debug("SVG decode failed, will try raster fallback")

        pixmap = QPixmap()
        if pixmap.loadFromData(raw) and not pixmap.isNull():
            return pixmap

        if b"<svg" in raw[:512].lower():
            svg = self._render_svg(raw)
            if not svg.isNull():
                return svg

        return None

    @staticmethod
    def _looks_like_svg(raw: bytes, content_type: str) -> bool:
        content_type = (content_type or "").lower()
        if "svg" in content_type:
            return True
        return b"<svg" in raw[:512].lower()

    @staticmethod
    def _render_svg(raw: bytes, size: QSize = QSize(56, 56)) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(raw))
        if not renderer.isValid():
            log.debug("QSvgRenderer rejected payload as invalid SVG")
            return QPixmap()

        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    @staticmethod
    def _apply_fallback(label: QLabel, text: str) -> None:
        label.clear()
        label.setText(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setScaledContents(False)

    @staticmethod
    def _apply_pixmap(label: QLabel, pixmap: QPixmap) -> None:
        target_width = max(1, label.width() - 8)
        target_height = max(1, label.height() - 8)
        target = QSize(target_width, target_height)

        if target.width() <= 1 or target.height() <= 1:
            target = QSize(56, 56)

        scaled = pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setText("")
        label.setPixmap(scaled)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setScaledContents(False)
