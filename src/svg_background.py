from PySide6 import QtCore, QtWidgets # type: ignore
from PySide6.QtSvg import QSvgRenderer # type: ignore
from PySide6.QtWidgets import QStyleOption # type: ignore
from PySide6.QtGui import QPainter # type: ignore


class SvgBackgroundWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._renderer = QSvgRenderer()
        self._loaded_path = None

    def _ensure_loaded(self):
        path = self.property("svgPath")
        if path and path != self._loaded_path:
            self._renderer.load(path)
            self._loaded_path = path
            self.update()

    def paintEvent(self, e):
        self._ensure_loaded()

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_Widget, opt, p, self)

        if not self._renderer.isValid():
            return

        target = self.rect()
        vb = self._renderer.viewBoxF()

        sx = target.width() / vb.width()
        sy = target.height() / vb.height()
        s = max(sx, sy)

        w = vb.width() * s
        h = vb.height() * s

        x = target.right() - w + 1
        y = target.y() + (target.height() - h) / 2

        dest = QtCore.QRectF(x, y, w, h)
        self._renderer.render(p, dest)