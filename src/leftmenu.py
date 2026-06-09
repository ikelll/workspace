from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Qt, QEvent  # type: ignore
from PySide6.QtWidgets import QApplication, QPushButton, QFrame, QWidget  # type: ignore

from src.icons import icon_apps_nav, icon_desktops_nav, icon_home_nav


class MenuController(QObject):
    state_changed = Signal()

    def __init__(self, ui, parent: QObject | None = None):
        super().__init__(parent)
        self.ui = ui
        self.group = "home"

        self._items = {
            "home": {
                "frame": self.ui.frameHomeNav,
                "indicator": self.ui.frameHomeIndicator,
                "icon": self.ui.btnHomeIcon,
                "text": self.ui.btnHome,
                "icon_factory": icon_home_nav,
            },
            "apps": {
                "frame": self.ui.frameAppsNav,
                "indicator": self.ui.frameAppsIndicator,
                "icon": self.ui.btnAppsIcon,
                "text": self.ui.btnApps,
                "icon_factory": icon_apps_nav,
            },
            "desktops": {
                "frame": self.ui.frameDesktopsNav,
                "indicator": self.ui.frameDesktopsIndicator,
                "icon": self.ui.btnDesktopsIcon,
                "text": self.ui.btnDesktops,
                "icon_factory": icon_desktops_nav,
            },
        }

        self._nav_targets: dict[QWidget, str] = {}

        for key, item in self._items.items():
            self._prepare_item(key, item)

        self.ui.btnHome.clicked.connect(self.go_home)
        self.ui.btnHomeIcon.clicked.connect(self.go_home)
        self.ui.btnApps.clicked.connect(self.go_apps)
        self.ui.btnAppsIcon.clicked.connect(self.go_apps)
        self.ui.btnDesktops.clicked.connect(self.go_desktops)
        self.ui.btnDesktopsIcon.clicked.connect(self.go_desktops)

        self.go_home()

    def _theme_name(self) -> str:
        app = QApplication.instance()
        if app is None:
            return "light"
        return str(app.property("theme") or "light").strip().lower() or "light"

    def _palette(self) -> dict[str, str]:
        if self._theme_name() == "dark":
            return {
                "active": "#E5E7EB",
                "idle": "#9CA3AF",
                "avatar_fg": "#111827",
                "avatar_hover": "#FFFFFF",
            }
        return {
            "active": "#333333",
            "idle": "#4B5563",
            "avatar_fg": "#FFFFFF",
            "avatar_hover": "#1F2937",
        }

    @property
    def active_color(self) -> str:
        return self._palette()["active"]

    @property
    def idle_color(self) -> str:
        return self._palette()["idle"]

    @property
    def avatar_foreground_color(self) -> str:
        return self._palette()["avatar_fg"]

    @property
    def avatar_hover_color(self) -> str:
        return self._palette()["avatar_hover"]

    def _prepare_item(self, key: str, item: dict) -> None:
        frame: QFrame = item["frame"]
        text_button: QPushButton = item["text"]
        icon_button: QPushButton = item["icon"]

        frame.setProperty("active", False)
        frame.setCursor(Qt.PointingHandCursor)
        frame.installEventFilter(self)
        self._nav_targets[frame] = key

        indicator = item.get("indicator")
        if isinstance(indicator, QWidget):
            indicator.setCursor(Qt.PointingHandCursor)
            indicator.installEventFilter(self)
            self._nav_targets[indicator] = key

        for child in frame.findChildren(QWidget):
            if child in (text_button, icon_button, indicator):
                continue
            child.setCursor(Qt.PointingHandCursor)
            child.installEventFilter(self)
            self._nav_targets[child] = key

        text_button.setCursor(Qt.PointingHandCursor)
        text_button.setFlat(True)
        text_button.setFocusPolicy(Qt.NoFocus)

        icon_button.setCursor(Qt.PointingHandCursor)
        icon_button.setFlat(True)
        icon_button.setFocusPolicy(Qt.NoFocus)

    def _all_widgets(self):
        widgets = []
        for item in self._items.values():
            widgets.extend([
                item["frame"],
                item["indicator"],
                item["icon"],
                item["text"],
            ])
        return widgets

    def _repolish_all(self) -> None:
        for widget in self._all_widgets():
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _clear_props(self) -> None:
        for item in self._items.values():
            item["frame"].setProperty("active", False)
            item["indicator"].setProperty("active", False)
            item["icon"].setProperty("active", False)
            item["text"].setProperty("active", False)
            if item["text"].isCheckable():
                item["text"].setChecked(False)
            if item["icon"].isCheckable():
                item["icon"].setChecked(False)

    def _set_item_active(self, key: str, active: bool) -> None:
        item = self._items[key]
        item["frame"].setProperty("active", active)
        item["indicator"].setProperty("active", active)
        item["icon"].setProperty("active", active)
        item["text"].setProperty("active", active)
        if item["text"].isCheckable():
            item["text"].setChecked(active)
        if item["icon"].isCheckable():
            item["icon"].setChecked(active)

    def _apply_state(self, *, active_key: str | None = None) -> None:
        self._clear_props()
        if active_key is not None:
            self._set_item_active(active_key, True)
        self._update_icons()
        self._repolish_all()

    def _icon_color(self, key: str) -> str:
        return self.active_color if bool(self._items[key]["frame"].property("active")) else self.idle_color

    def _update_icons(self) -> None:
        for key, item in self._items.items():
            item["icon"].setIcon(item["icon_factory"](color=self._icon_color(key)))

    def refresh_theme(self) -> None:
        self._update_icons()
        self._repolish_all()

    def eventFilter(self, watched, event):
        if (
            watched in self._nav_targets
            and event.type() == QEvent.Type.MouseButtonRelease
            and getattr(event, "button", lambda: None)() == Qt.MouseButton.LeftButton
        ):
            key = self._nav_targets[watched]
            if key == "home":
                self.go_home()
            elif key == "apps":
                self.go_apps()
            elif key == "desktops":
                self.go_desktops()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def _show_page(self, page_widget):
        self.ui.stackedWidgetMainContent.setCurrentWidget(page_widget)

    def current_apps_mode(self) -> str:
        return "all"

    def current_desktops_mode(self) -> str:
        return "all"

    def go_home(self):
        self.group = "home"
        self._apply_state(active_key="home")
        self._show_page(self.ui.pageHome)
        self.state_changed.emit()

    def go_apps(self):
        self.group = "apps"
        self._apply_state(active_key="apps")
        self._show_page(self.ui.pageApps)
        self.state_changed.emit()

    def go_desktops(self):
        self.group = "desktops"
        self._apply_state(active_key="desktops")
        self._show_page(self.ui.pageDesktops)
        self.state_changed.emit()
