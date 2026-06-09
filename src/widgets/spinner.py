from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class Spinner(QWidget):

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        color: QColor | None = None,
        thickness: float = 18.0,
        inner_radius: float = 26.0,
        rev_per_sec: float = 1.0,
        arc_deg: float = 80.0,
        tail_steps: int = 18,
        tail_fade: float = 0.85,
        fps: int = 60,
    ):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._angle = 0.0
        self._color = QColor(color) if color else QColor(4, 115, 148)

        self._thickness = float(thickness)
        self._inner_radius = float(inner_radius)

        self._rev_per_sec = float(rev_per_sec)
        self._arc_deg = float(arc_deg)

        self._tail_steps = max(4, int(tail_steps))
        self._tail_fade = max(0.0, min(1.0, float(tail_fade)))

        self._fps = max(24, int(fps))
        self._dt_ms = int(1000 / self._fps)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._update_min_size()

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start(self._dt_ms)
        self.show()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def set_color(self, r: int, g: int, b: int, a: int = 255) -> None:
        self._color = QColor(r, g, b, a)
        self.update()

    def set_rev_per_sec(self, v: float) -> None:
        self._rev_per_sec = float(v)

    def set_thickness(self, t: float) -> None:
        self._thickness = float(t)
        self._update_min_size()
        self.update()

    def set_inner_radius(self, r: float) -> None:
        self._inner_radius = float(r)
        self._update_min_size()
        self.update()

    def set_arc_deg(self, deg: float) -> None:
        self._arc_deg = float(deg)
        self.update()

    def _update_min_size(self) -> None:
        outer = self._inner_radius + self._thickness
        side = int((outer * 2) + 4)
        self.setMinimumSize(side, side)

    def _tick(self) -> None:
        deg_per_sec = 360.0 * self._rev_per_sec
        self._angle = (self._angle + deg_per_sec * (self._dt_ms / 1000.0)) % 360.0
        self.update()

    def paintEvent(self, _e) -> None:
        w, h = self.width(), self.height()
        side = min(w, h)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        cx, cy = w / 2.0, h / 2.0
        p.translate(cx, cy)

        outer_r = self._inner_radius + self._thickness / 2.0
        rect = QRectF(-outer_r, -outer_r, outer_r * 2.0, outer_r * 2.0)

        pen = QPen()
        pen.setWidthF(self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setStyle(Qt.PenStyle.SolidLine)

        head = self._angle
        span = self._arc_deg

        for i in range(self._tail_steps):
            t = i / (self._tail_steps - 1)
            alpha = int(255 * ((1.0 - t) ** (1.0 / max(1e-6, (1.0 - self._tail_fade)))))
            c = QColor(self._color)
            c.setAlpha(max(0, min(255, alpha)))

            pen.setColor(c)
            p.setPen(pen)

            start = head - t * (span * 2.2)
            seg_span = span / 2.2

            start_qt = (90 - start) * 16
            span_qt = -seg_span * 16

            p.drawArc(rect, int(start_qt), int(span_qt))

        p.end()