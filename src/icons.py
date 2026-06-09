from __future__ import annotations

from PySide6.QtCore import QByteArray, QFile, QRectF, Qt  # type: ignore
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap  # type: ignore
from PySide6.QtSvg import QSvgRenderer  # type: ignore

DEFAULT_ICON_COLOR = "#9CA3AF"
LOGO_PATH = ":/img/static/gorizontvs-logo.svg"


def _device_pixel_ratio(dpr: float | None = None) -> float:
    if dpr is not None:
        return dpr
    screen = QGuiApplication.primaryScreen()
    return screen.devicePixelRatio() if screen else 1.0


def _read_svg_text(source: str) -> str:
    if "<svg" in source:
        return source

    file = QFile(source)
    if not file.open(QFile.ReadOnly | QFile.Text):
        return ""

    try:
        data = file.readAll()
        return bytes(data).decode("utf-8")
    finally:
        file.close()


def _build_renderer(source: str, color: str | None = None) -> QSvgRenderer:
    svg_text = _read_svg_text(source)
    if not svg_text:
        return QSvgRenderer()

    if color is not None:
        svg_text = svg_text.replace("currentColor", color)

    return QSvgRenderer(QByteArray(svg_text.encode("utf-8")))


def _render_renderer(
    renderer: QSvgRenderer,
    width: int,
    height: int,
    dpr: float | None = None,
) -> QPixmap:
    if not renderer.isValid():
        return QPixmap()

    dpr = _device_pixel_ratio(dpr)
    logical_w = max(1, int(width))
    logical_h = max(1, int(height))
    device_w = max(1, round(logical_w * dpr))
    device_h = max(1, round(logical_h * dpr))

    px = QPixmap(device_w, device_h)
    px.fill(Qt.transparent)
    px.setDevicePixelRatio(dpr)

    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, logical_w, logical_h))
    painter.end()

    return px


def svg_pixmap(
    source: str,
    width: int,
    height: int | None = None,
    color: str | None = None,
    dpr: float | None = None,
) -> QPixmap:
    if height is None:
        height = width
    renderer = _build_renderer(source, color=color)
    return _render_renderer(renderer, width, height, dpr=dpr)


def svg_icon(
    source: str,
    size: int = 16,
    color: str = DEFAULT_ICON_COLOR,
) -> QIcon:
    icon = QIcon()
    for dpr in (1.0, 2.0, 3.0):
        icon.addPixmap(svg_pixmap(source, size, size, color=color, dpr=dpr))
    return icon


def logo_pixmap(height: int, dpr: float | None = None) -> QPixmap:
    renderer = _build_renderer(LOGO_PATH, color=None)
    if not renderer.isValid():
        return QPixmap()

    size = renderer.defaultSize()
    if size.isValid() and size.height() > 0:
        src_w = size.width()
        src_h = size.height()
    else:
        vb = renderer.viewBoxF()
        src_w = vb.width() or 1
        src_h = vb.height() or 1

    width = max(1, round(src_w * height / src_h))
    return _render_renderer(renderer, width, height, dpr=dpr)


def icon_globe(size: int = 16, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(":/img/static/globe.svg", size, color)


def icon_user(size: int = 16, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(":/img/static/user.svg", size, color)


def icon_lock(size: int = 16, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(":/img/static/lock.svg", size, color)


def icon_eye(size: int = 16, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(":/img/static/eye_open.svg", size, color)


def icon_eye_off(size: int = 16, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(":/img/static/eye_off.svg", size, color)


def _static_path(filename: str) -> str:
    return f":/img/static/{filename}"


def icon_search(size: int = 16, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(_static_path("search.svg"), size, color)


def icon_home_nav(size: int = 18, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(_static_path("nav-home.svg"), size, color)


def icon_apps_nav(size: int = 18, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(_static_path("nav-apps.svg"), size, color)


def icon_desktops_nav(size: int = 18, color: str = DEFAULT_ICON_COLOR) -> QIcon:
    return svg_icon(_static_path("nav-desktops.svg"), size, color)
