from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt  # type: ignore
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QApplication,
    QComboBox,
    QFrame,
    QListView,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QWidget,
)


class _UnifiedPopupListView(QListView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def viewportEvent(self, event):  # noqa: D401 - Qt override
        if event.type() in (
            QEvent.Type.Enter,
            QEvent.Type.MouseMove,
            QEvent.Type.HoverMove,
        ):
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        return super().viewportEvent(event)


class _UnifiedComboDelegate(QStyledItemDelegate):
    def __init__(self, combo: "UnifiedComboBox") -> None:
        super().__init__(combo)
        self._combo = combo

    def sizeHint(self, option, index):  # noqa: D401 - Qt override
        size = super().sizeHint(option, index)
        return QSize(
            max(size.width(), 120),
            max(size.height() + 12, self._combo.popup_item_height()),
        )

    def paint(self, painter: QPainter, option, index) -> None:  # noqa: D401 - Qt override
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        theme = self._combo.theme()
        item_rect = QRectF(option.rect).adjusted(6, 2, -6, -2)
        is_enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        bg = QColor(0, 0, 0, 0)
        if is_selected:
            bg = QColor(theme["popup_selected_bg"])
        elif is_hovered:
            bg = QColor(theme["popup_hover_bg"])

        if bg.alpha() > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(item_rect, 10, 10)

        icon = index.data(Qt.ItemDataRole.DecorationRole)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")

        text_rect = item_rect.adjusted(14, 0, -14, 0)
        if isinstance(icon, QIcon) and not icon.isNull():
            icon_side = 16
            icon_rect = QRectF(
                text_rect.left(),
                text_rect.center().y() - (icon_side / 2),
                icon_side,
                icon_side,
            )
            icon.paint(painter, icon_rect.toRect())
            text_rect.setLeft(icon_rect.right() + 10)

        display_color = QColor(
            theme["popup_text_disabled"] if not is_enabled else theme["popup_text"]
        )
        painter.setPen(display_color)
        elided = option.fontMetrics.elidedText(
            text,
            Qt.TextElideMode.ElideRight,
            max(10, int(text_rect.width())),
        )
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            elided,
        )
        painter.restore()


class UnifiedComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hovered = False
        self._popup_visible = False
        self._popup_window = None

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setEditable(False)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setIconSize(QSize(18, 18))
        self.setFrame(False)

        view = _UnifiedPopupListView(self)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setMouseTracking(True)
        view.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        view.setSpacing(2)
        view.setUniformItemSizes(False)
        view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setView(view)
        self.setItemDelegate(_UnifiedComboDelegate(self))

        self.currentIndexChanged.connect(lambda *_: self.update())
        self.highlighted.connect(lambda *_: self.update())

        self._apply_metrics()
        self._refresh_popup_style()

    def combo_variant(self) -> str:
        raw = str(self.property("comboVariant") or "").strip().lower()
        if raw in {"primary", "compact"}:
            return raw
        return "compact"

    def metrics(self) -> dict[str, int]:
        variant = self.combo_variant()
        if variant == "primary":
            return {
                "height": 48,
                "radius": 12,
                "padding_x": 8,
                "arrow_width": 34,
                "popup_radius": 12,
                "item_height": 42,
                "popup_offset_y": 6,
            }
        return {
            "height": 40,
            "radius": 10,
            "padding_x": 12,
            "arrow_width": 30,
            "popup_radius": 10,
            "item_height": 38,
            "popup_offset_y": 4,
        }

    def popup_item_height(self) -> int:
        return self.metrics()["item_height"]

    def theme(self) -> dict[str, str]:
        variant = self.combo_variant()
        app = QApplication.instance()
        theme_name = (
            str(app.property("theme") if app is not None else "light").strip().lower()
            or "light"
        )

        if theme_name == "dark":
            base_bg = "#111827" if variant == "primary" else "#0F172A"
            return {
                "bg": base_bg,
                "bg_hover": "#111827",
                "bg_disabled": "#111827",
                "border": "#334155",
                "border_hover": "#475569",
                "border_focus": "#38BDF8",
                "border_error": "#F87171",
                "text": "#E5E7EB",
                "text_disabled": "#64748B",
                "text_placeholder": "#94A3B8",
                "arrow": "#E5E7EB",
                "arrow_disabled": "#64748B",
                "arrow_bg": "#1E293B",
                "arrow_bg_focus": "#0F2233",
                "arrow_bg_disabled": "#1F2937",
                "focus_glow": "#38BDF8",
                "error_glow": "#F87171",
                "popup_bg": "#111827",
                "popup_border": "#334155",
                "popup_text": "#E5E7EB",
                "popup_text_disabled": "#64748B",
                "popup_hover_bg": "#1E293B",
                "popup_selected_bg": "#0F2233",
                "popup_scroll": "#475569",
                "popup_scroll_hover": "#64748B",
            }

        base_bg = "#F6FBFC" if variant == "primary" else "#FFFFFF"
        return {
            "bg": base_bg,
            "bg_hover": "#FFFFFF",
            "bg_disabled": "#F3F4F6",
            "border": "#D3DEE6",
            "border_hover": "#B9C8D3",
            "border_focus": "#0B7285",
            "border_error": "#DC2626",
            "text": "#0F172A",
            "text_disabled": "#9CA3AF",
            "text_placeholder": "#94A3B8",
            "arrow": "#0B7285",
            "arrow_disabled": "#9CA3AF",
            "arrow_bg": "#EAF7FA",
            "arrow_bg_focus": "#DDF2F7",
            "arrow_bg_disabled": "#E5E7EB",
            "focus_glow": "#0B7285",
            "error_glow": "#DC2626",
            "popup_bg": "#FFFFFF",
            "popup_border": "#D3DEE6",
            "popup_text": "#0F172A",
            "popup_text_disabled": "#94A3B8",
            "popup_hover_bg": "#F3FAFC",
            "popup_selected_bg": "#E6F7FB",
            "popup_scroll": "#C7D2DA",
            "popup_scroll_hover": "#AAB7C2",
        }

    def sizeHint(self):  # noqa: D401 - Qt override
        size = super().sizeHint()
        size.setHeight(max(size.height(), self.metrics()["height"]))
        return size

    def minimumSizeHint(self):  # noqa: D401 - Qt override
        size = super().minimumSizeHint()
        size.setHeight(max(size.height(), self.metrics()["height"]))
        return size

    def showPopup(self) -> None:  # noqa: D401 - Qt override
        self._popup_visible = True
        self._refresh_popup_style()
        self._prepare_popup_window()
        if self.view() is not None:
            self.view().setMinimumWidth(self.width())
        super().showPopup()
        self._position_popup_window()
        self.update()

    def hidePopup(self) -> None:  # noqa: D401 - Qt override
        self._popup_visible = False
        super().hidePopup()
        self.update()

    def enterEvent(self, event) -> None:  # noqa: D401 - Qt override
        self._hovered = True
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: D401 - Qt override
        self._hovered = False
        super().leaveEvent(event)
        self.update()

    def focusInEvent(self, event) -> None:  # noqa: D401 - Qt override
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event) -> None:  # noqa: D401 - Qt override
        super().focusOutEvent(event)
        self.update()

    def changeEvent(self, event) -> None:  # noqa: D401 - Qt override
        super().changeEvent(event)
        self.update()

    def event(self, event):  # noqa: D401 - Qt override
        if event.type() == QEvent.Type.DynamicPropertyChange:
            self._apply_metrics()
            self._refresh_popup_style()
            self.update()
        return super().event(event)

    def eventFilter(self, watched, event):  # noqa: D401 - Qt override
        if watched is self._popup_window and event.type() in (
            QEvent.Type.Show,
            QEvent.Type.Resize,
        ):
            self._position_popup_window()
        return super().eventFilter(watched, event)

    def paintEvent(self, event) -> None:  # noqa: D401 - Qt override
        del event
        metrics = self.metrics()
        theme = self.theme()
        has_error = bool(self.property("hasError"))
        enabled = self.isEnabled()
        focused = self.hasFocus() or self._popup_visible

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        box = QRectF(outer)

        if focused:
            glow = QColor(theme["error_glow"] if has_error else theme["focus_glow"])
            glow.setAlpha(26)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawRoundedRect(outer, metrics["radius"] + 2, metrics["radius"] + 2)
            box = outer.adjusted(2, 2, -2, -2)

        bg = QColor(theme["bg"])
        border = QColor(theme["border"])
        if not enabled:
            bg = QColor(theme["bg_disabled"])
            border = QColor(theme["border"])
        elif has_error:
            bg = QColor("#FFF7F7")
            border = QColor(theme["border_error"])
        elif focused:
            bg = QColor(theme["bg_hover"])
            border = QColor(theme["border_focus"])
        elif self._hovered:
            bg = QColor(theme["bg_hover"])
            border = QColor(theme["border_hover"])

        painter.setPen(QPen(border, 1.2))
        painter.setBrush(bg)
        painter.drawRoundedRect(box, metrics["radius"], metrics["radius"])

        arrow_rect = QRectF(
            box.right() - metrics["arrow_width"] - 8,
            box.top() + 6,
            metrics["arrow_width"],
            box.height() - 12,
        )
        arrow_bg = QColor(theme["arrow_bg"])
        arrow_color = QColor(theme["arrow"])
        if not enabled:
            arrow_bg = QColor(theme["arrow_bg_disabled"])
            arrow_color = QColor(theme["arrow_disabled"])
        elif focused:
            arrow_bg = QColor(theme["arrow_bg_focus"])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(arrow_bg)
        painter.drawRoundedRect(arrow_rect, 10, 10)

        text_rect = QRectF(
            box.left() + metrics["padding_x"],
            box.top(),
            max(10.0, arrow_rect.left() - box.left() - metrics["padding_x"] - 10),
            box.height(),
        )

        current_index = self.currentIndex()
        icon = self.itemIcon(current_index) if current_index >= 0 else QIcon()
        if not icon.isNull():
            icon_side = 18
            icon_rect = QRectF(
                text_rect.left(),
                text_rect.center().y() - (icon_side / 2),
                icon_side,
                icon_side,
            )
            icon.paint(painter, icon_rect.toRect())
            text_rect.setLeft(icon_rect.right() + 10)

        current_text = self.currentText().strip()
        placeholder = self.placeholderText().strip()
        is_placeholder = not current_text and bool(placeholder)
        display_text = placeholder if is_placeholder else current_text

        text_color = QColor(
            theme["text_placeholder"] if is_placeholder else theme["text"]
        )
        if not enabled:
            text_color = QColor(theme["text_disabled"])

        painter.setPen(text_color)
        elided = self.fontMetrics().elidedText(
            display_text,
            Qt.TextElideMode.ElideRight,
            max(10, int(text_rect.width())),
        )
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            elided,
        )

        chevron = QPainterPath()
        cx = arrow_rect.center().x()
        cy = arrow_rect.center().y() + 0.5
        chevron.moveTo(QPointF(cx - 4.5, cy - 2.0))
        chevron.lineTo(QPointF(cx, cy + 2.5))
        chevron.lineTo(QPointF(cx + 4.5, cy - 2.0))

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(
                arrow_color,
                2.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawPath(chevron)
        painter.end()

    def _prepare_popup_window(self) -> None:
        popup_window = self.view().window()
        if popup_window is None:
            return

        popup_window.setObjectName("UnifiedComboPopupWindow")
        if popup_window is not self._popup_window:
            if self._popup_window is not None:
                self._popup_window.removeEventFilter(self)
            popup_window.installEventFilter(self)
            self._popup_window = popup_window
        popup_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        popup_window.setContentsMargins(0, 0, 0, 0)
        popup_window.setCursor(Qt.CursorShape.PointingHandCursor)
        popup_window.setStyleSheet(
            "QFrame#UnifiedComboPopupWindow { background: transparent; border: none; }"
        )
        if isinstance(popup_window, QFrame):
            popup_window.setFrameShape(QFrame.Shape.NoFrame)
            popup_window.setLineWidth(0)
            popup_window.setMidLineWidth(0)
        if popup_window.graphicsEffect() is not None:
            popup_window.setGraphicsEffect(None)

    def _position_popup_window(self) -> None:
        popup_window = self.view().window()
        if popup_window is None or not popup_window.isVisible():
            return

        metrics = self.metrics()
        anchor_global = self.mapToGlobal(
            QPoint(0, self.height() + metrics["popup_offset_y"])
        )
        frame = popup_window.frameGeometry()
        popup_width = max(self.width(), frame.width())
        popup_height = frame.height()

        target_x = anchor_global.x()
        target_y = anchor_global.y()

        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            if target_x + popup_width > available.right():
                target_x = max(available.left(), available.right() - popup_width)
            if target_y + popup_height > available.bottom():
                target_y = self.mapToGlobal(
                    QPoint(0, -popup_height - metrics["popup_offset_y"])
                ).y()
            if target_y < available.top():
                target_y = max(available.top(), anchor_global.y())

        popup_window.resize(popup_width, popup_height)
        popup_window.move(target_x, target_y)

    def _apply_metrics(self) -> None:
        metrics = self.metrics()
        self.setMinimumHeight(metrics["height"])
        self.updateGeometry()

    def _refresh_popup_style(self) -> None:
        metrics = self.metrics()
        theme = self.theme()
        view = self.view()
        if view is None:
            return
        view.setCursor(Qt.CursorShape.PointingHandCursor)
        view.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        view.setStyleSheet(
            f"""
            QListView {{
                background: {theme["popup_bg"]};
                border: 1px solid {theme["popup_border"]};
                border-radius: {metrics["popup_radius"]}px;
                padding: 6px;
                outline: none;
            }}
            QListView::item {{
                border-radius: 8px;
                padding: 4px 8px;
            }}
            QListView::item:hover {{
                background: {theme["popup_hover_bg"]};
            }}
            QListView::item:selected {{
                background: {theme["popup_selected_bg"]};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 6px 2px 6px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {theme["popup_scroll"]};
                border-radius: 4px;
                min-height: 32px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme["popup_scroll_hover"]};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                height: 0px;
            }}
            """
        )
