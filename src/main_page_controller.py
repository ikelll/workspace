from __future__ import annotations

import logging

from typing import Iterable

from PySide6.QtCore import QCoreApplication, QObject, QSettings, Qt, Signal # type: ignore
from PySide6.QtWidgets import QLabel, QGridLayout, QLayout, QVBoxLayout # type: ignore

from src.app_card import AppCard
from src.desktop_card import DesktopCard
from src.service_image_loader import ServiceImageLoader

log = logging.getLogger(__name__)


class MainPageController(QObject):
    connect_requested = Signal(object)
    action_requested = Signal(object, str)

    def __init__(
        self,
        ui,
        menu=None,
        settings: QSettings | None = None,
        image_loader: ServiceImageLoader | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ui = ui
        self.menu = menu
        self._settings = settings
        self._services: list[object] = []
        self._favorite_ids: set[str] = set(self._load_favorites())
        self._image_loader = image_loader

        self._home_layout: QVBoxLayout = self.ui.vlytHomeContent
        self._apps_grid: QGridLayout = self.ui.gridAppsCards
        self._desktops_grid: QGridLayout = self.ui.gridDesktopsCards

        self._home_empty = getattr(self.ui, "wHomeEmptyState", None)
        self._apps_empty = getattr(self.ui, "wAppsEmptyState", None)
        self._desktops_empty = getattr(self.ui, "wDesktopsEmptyState", None)
        self._home_empty_label = getattr(self.ui, "lblHomeEmpty", None)
        self._apps_empty_label = getattr(self.ui, "lblAppsEmpty", None)
        self._desktops_empty_label = getattr(self.ui, "lblDesktopsEmpty", None)

        self._cmb_apps_sort = getattr(self.ui, "cmbAppsSort", None)
        self._cmb_desktops_sort = getattr(self.ui, "cmbDesktopsSort", None)
        self._search = getattr(self.ui, "leWorkspaceSearch", None)

        self._init_view_combo(self._cmb_apps_sort)
        self._init_view_combo(self._cmb_desktops_sort)

        if self._cmb_apps_sort is not None:
            self._cmb_apps_sort.currentIndexChanged.connect(self._rebuild_pages)

        if self._cmb_desktops_sort is not None:
            self._cmb_desktops_sort.currentIndexChanged.connect(self._rebuild_pages)

        if self._search is not None:
            self._search.textChanged.connect(self._rebuild_pages)

        if self.menu is not None and hasattr(self.menu, "state_changed"):
            self.menu.state_changed.connect(self._rebuild_pages)

        self.clear()

    def _init_view_combo(self, combo) -> None:
        if combo is None:
            return

        combo.blockSignals(True)
        combo.clear()
        options = [
            (self.tr("All · A to Z"), ("all", "az")),
            (self.tr("All · Z to A"), ("all", "za")),
            (self.tr("All · Status"), ("all", "status")),
            (self.tr("Favorites · A to Z"), ("favorites", "az")),
            (self.tr("Favorites · Z to A"), ("favorites", "za")),
            (self.tr("Favorites · Status"), ("favorites", "status")),
        ]
        for label, value in options:
            combo.addItem(label, value)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def _load_favorites(self) -> list[str]:
        if self._settings is None:
            return []
        raw = self._settings.value("workspace/favorite_service_ids", [])
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw] if raw else []
        return [str(v) for v in raw]

    def _save_favorites(self) -> None:
        if self._settings is None:
            return
        self._settings.setValue(
            "workspace/favorite_service_ids",
            sorted(self._favorite_ids),
        )
        self._settings.sync()

    def _msg(self, key: str) -> str:
        catalog = {
            "home_empty": QCoreApplication.translate("Widget", "Home is empty"),
            "no_apps": QCoreApplication.translate("Widget", "No applications"),
            "no_desktops": QCoreApplication.translate("Widget", "No desktops"),
            "no_resources_filtered": self.tr("No resources match the current filters."),
            "no_favorite_apps": self.tr("No favorite applications yet."),
            "no_favorite_desktops": self.tr("No favorite desktops yet."),
            "no_apps_available": self.tr("No applications available."),
            "no_desktops_available": self.tr("No desktops available."),
            "home_search_results": self.tr("Search results for “{query}”"),
            "desktops_section": QCoreApplication.translate("Widget", "Desktops"),
            "apps_section": QCoreApplication.translate("Widget", "Apps"),
            "profile": self.tr("Profile"),
        }
        return catalog.get(key, key)

    def clear(self) -> None:
        self._services.clear()
        self._clear_layout(self._home_layout)
        self._clear_layout(self._apps_grid)
        self._clear_layout(self._desktops_grid)
        self._set_empty_state("home", True, self._msg("home_empty"))
        self._set_empty_state("apps", True, self._msg("no_apps"))
        self._set_empty_state("desktops", True, self._msg("no_desktops"))

    def retranslate_ui(self) -> None:
        current_apps = self._cmb_apps_sort.currentData() if self._cmb_apps_sort is not None else None
        current_desktops = self._cmb_desktops_sort.currentData() if self._cmb_desktops_sort is not None else None

        self._init_view_combo(self._cmb_apps_sort)
        self._init_view_combo(self._cmb_desktops_sort)

        if self._cmb_apps_sort is not None and current_apps is not None:
            for index in range(self._cmb_apps_sort.count()):
                if self._cmb_apps_sort.itemData(index) == current_apps:
                    self._cmb_apps_sort.setCurrentIndex(index)
                    break

        if self._cmb_desktops_sort is not None and current_desktops is not None:
            for index in range(self._cmb_desktops_sort.count()):
                if self._cmb_desktops_sort.itemData(index) == current_desktops:
                    self._cmb_desktops_sort.setCurrentIndex(index)
                    break

        if self._services:
            self._rebuild_pages()
        else:
            self.clear()

    def populate(self, services: list[object]) -> None:
        self._services = list(services or [])
        log.info("Populate main page with %d service(s)", len(self._services))
        for svc in self._services:
            log.debug(
                "Service for UI: id=%r title=%r image_id=%r is_application=%r in_use=%r maintenance=%r not_accessible=%r",
                getattr(svc, "id", ""),
                getattr(svc, "visual_name", "") or getattr(svc, "name", ""),
                getattr(svc, "image_id", ""),
                getattr(svc, "is_application", None),
                getattr(svc, "in_use", None),
                getattr(svc, "maintenance", None),
                getattr(svc, "not_accessible", None),
            )
        self._rebuild_pages()

    def set_user_identity(self, username: str | None) -> None:
        btn = getattr(self.ui, "btnUserAvatar", None)
        if btn is None:
            return

        initial = "?"
        if username:
            stripped = username.strip()
            if stripped:
                initial = stripped[0].upper()

        btn.setText(initial)
        btn.setToolTip(username or self._msg("profile"))

    def _rebuild_pages(self, *_args) -> None:
        self._clear_layout(self._home_layout)
        self._clear_layout(self._apps_grid)
        self._clear_layout(self._desktops_grid)

        self._set_empty_state("home", False)
        self._set_empty_state("apps", False)
        self._set_empty_state("desktops", False)

        apps_all = self._collect_services(kind="app", favorites_only=False, combo=None)
        desktops_all = self._collect_services(kind="desktop", favorites_only=False, combo=None)

        apps_mode = self._combo_filter_mode(self._cmb_apps_sort)
        desktops_mode = self._combo_filter_mode(self._cmb_desktops_sort)

        apps = self._collect_services(
            kind="app",
            favorites_only=(apps_mode == "favorites"),
            combo=self._cmb_apps_sort,
        )
        desktops = self._collect_services(
            kind="desktop",
            favorites_only=(desktops_mode == "favorites"),
            combo=self._cmb_desktops_sort,
        )

        self._populate_home(apps_all, desktops_all)
        self._populate_apps(apps)
        self._populate_desktops(desktops)

    def _collect_services(self, *, kind: str, favorites_only: bool, combo=None) -> list[object]:
        services = [
            svc
            for svc in self._filtered_by_search(self._services)
            if self._matches_kind(svc, kind)
        ]

        if favorites_only:
            services = [svc for svc in services if self._is_favorite(svc)]

        return self._sorted_services(services, kind=kind, combo=combo)

    def _filtered_by_search(self, services: Iterable[object]) -> list[object]:
        query = self._search_text().lower()
        if not query:
            return list(services)

        def _haystack(svc: object) -> str:
            parts = [
                getattr(svc, "name", "") or "",
                getattr(svc, "visual_name", "") or "",
                getattr(svc, "description", "") or "",
                getattr(getattr(svc, "group", None), "name", "") or "",
                getattr(svc, "status_text", "") or "",
            ]
            return " ".join(parts).lower()

        return [svc for svc in services if query in _haystack(svc)]

    def _combo_value(self, combo) -> tuple[str, str]:
        if combo is None:
            return ("all", "az")
        data = combo.currentData()
        if isinstance(data, tuple) and len(data) == 2:
            return data
        return ("all", "az")

    def _combo_filter_mode(self, combo) -> str:
        return self._combo_value(combo)[0]

    def _combo_sort_mode(self, combo) -> str:
        return self._combo_value(combo)[1]

    def _sorted_services(self, services: list[object], *, kind: str, combo=None) -> list[object]:
        del kind
        out = list(services)
        sort_mode = self._combo_sort_mode(combo)

        if sort_mode == "za":
            out.sort(key=lambda s: self._service_title(s).lower(), reverse=True)
            return out

        if sort_mode == "status":
            out.sort(
                key=lambda s: (
                    self._status_rank(s),
                    self._service_title(s).lower(),
                )
            )
            return out

        out.sort(key=lambda s: self._service_title(s).lower())
        return out

    def _status_rank(self, svc: object) -> int:
        if getattr(svc, "in_use", False):
            return 0
        if getattr(svc, "maintenance", False):
            return 2
        if getattr(svc, "not_accessible", False):
            return 3
        return 1

    def _service_title(self, svc: object) -> str:
        return (getattr(svc, "visual_name", "") or getattr(svc, "name", "") or self.tr("Resource")).strip()

    def _matches_kind(self, svc: object, kind: str) -> bool:
        is_application = getattr(svc, "is_application", None)
        if is_application is not None:
            return bool(is_application) if kind == "app" else not bool(is_application)

        is_desktop = self._is_desktop(svc)
        return is_desktop if kind == "desktop" else not is_desktop

    def _is_desktop(self, svc: object) -> bool:
        if hasattr(svc, "is_desktop"):
            try:
                return bool(getattr(svc, "is_desktop"))
            except Exception:
                pass

        group = getattr(svc, "group", None)
        group_name = (getattr(group, "name", "") or "").lower()
        name = (getattr(svc, "name", "") or "").lower()
        visual_name = (getattr(svc, "visual_name", "") or "").lower()
        description = (getattr(svc, "description", "") or "").lower()
        markers = (
            "desktop",
            "desktops",
            "workspace",
            "рабоч",
            "vdi",
            "wvd",
        )
        haystack = " ".join((group_name, name, visual_name, description))
        return any(marker in haystack for marker in markers)

    def _is_favorite(self, svc: object) -> bool:
        return str(getattr(svc, "id", "")) in self._favorite_ids

    def _search_text(self) -> str:
        if self._search is None:
            return ""
        return self._search.text().strip()

    def _apps_mode(self) -> str:
        return self._combo_filter_mode(self._cmb_apps_sort)

    def _desktops_mode(self) -> str:
        return self._combo_filter_mode(self._cmb_desktops_sort)

    def _populate_home(self, apps: list[object], desktops: list[object]) -> None:
        query = self._search_text()

        if query:
            hint = QLabel(self._msg("home_search_results").format(query=query))
            hint.setObjectName("lblHomeSectionTitle")
            self._home_layout.addWidget(hint)

        if not apps and not desktops:
            self._set_empty_state("home", True, self._msg("no_resources_filtered"))
            return

        if desktops:
            block_title = QLabel(self._msg("desktops_section"))
            block_title.setObjectName("lblHomeSectionTitle")
            self._home_layout.addWidget(block_title)

            for svc in desktops[:3]:
                card = DesktopCard(svc, self.ui.wHomeScrollHost, image_loader=self._image_loader)
                card.setProperty("compact", True)
                card.setMaximumWidth(420)
                self._wire_desktop_card(card)
                self._home_layout.addWidget(card, 0, Qt.AlignLeft)

        if apps:
            block_title = QLabel(self._msg("apps_section"))
            block_title.setObjectName("lblHomeSectionTitle")
            self._home_layout.addWidget(block_title)

            apps_grid = QGridLayout()
            apps_grid.setContentsMargins(0, 0, 0, 0)
            apps_grid.setHorizontalSpacing(18)
            apps_grid.setVerticalSpacing(18)
            columns = 3
            for i, svc in enumerate(apps[:6]):
                row = i // columns
                col = i % columns
                card = AppCard(svc, self.ui.wHomeScrollHost, image_loader=self._image_loader)
                self._wire_app_card(card)
                apps_grid.addWidget(card, row, col)

            apps_grid.setColumnStretch(columns, 1)
            self._home_layout.addLayout(apps_grid)

        self._home_layout.addStretch()

    def _populate_apps(self, apps: list[object]) -> None:
        if not apps:
            label = (
                self._msg("no_favorite_apps")
                if self._apps_mode() == "favorites"
                else self._msg("no_apps_available")
            )
            self._set_empty_state("apps", True, label)
            return

        columns = 5
        for i, svc in enumerate(apps):
            row = i // columns
            col = i % columns
            card = AppCard(svc, self.ui.wAppsScrollHost, image_loader=self._image_loader)
            self._wire_app_card(card)
            self._apps_grid.addWidget(card, row, col)

        self._apps_grid.setRowStretch((len(apps) + columns - 1) // columns, 1)
        self._apps_grid.setColumnStretch(columns, 1)

    def _populate_desktops(self, desktops: list[object]) -> None:
        if not desktops:
            label = (
                self._msg("no_favorite_desktops")
                if self._desktops_mode() == "favorites"
                else self._msg("no_desktops_available")
            )
            self._set_empty_state("desktops", True, label)
            return

        columns = 2
        for i, svc in enumerate(desktops):
            row = i // columns
            col = i % columns
            card = DesktopCard(svc, self.ui.wDesktopsScrollHost, image_loader=self._image_loader)
            self._wire_desktop_card(card)
            self._desktops_grid.addWidget(card, row, col)

        self._desktops_grid.setRowStretch((len(desktops) + columns - 1) // columns, 1)
        self._desktops_grid.setColumnStretch(columns, 1)

    def _wire_app_card(self, card: AppCard) -> None:
        card.set_favorite(self._is_favorite(card.service))
        card.clicked.connect(self.connect_requested.emit)
        card.action_clicked.connect(self.action_requested.emit)
        card.favorite_clicked.connect(self._on_favorite_changed)
        card.menu_clicked.connect(self._on_card_menu_requested)

    def _wire_desktop_card(self, card: DesktopCard) -> None:
        card.set_favorite(self._is_favorite(card.service))
        card.clicked.connect(self.connect_requested.emit)
        card.action_clicked.connect(self.action_requested.emit)
        card.favorite_clicked.connect(self._on_favorite_changed)
        card.menu_clicked.connect(self._on_card_menu_requested)

    def _on_favorite_changed(self, svc: object, checked: bool) -> None:
        service_id = str(getattr(svc, "id", ""))
        if not service_id:
            return

        if checked:
            self._favorite_ids.add(service_id)
        else:
            self._favorite_ids.discard(service_id)

        self._save_favorites()
        self._rebuild_pages()

    def _on_card_menu_requested(self, svc: object) -> None:
        del svc

    def _set_empty_state(self, kind: str, visible: bool, text: str | None = None) -> None:
        mapping = {
            "home": (self._home_empty, self._home_empty_label),
            "apps": (self._apps_empty, self._apps_empty_label),
            "desktops": (self._desktops_empty, self._desktops_empty_label),
        }
        widget, label = mapping.get(kind, (None, None))
        if label is not None and text is not None:
            label.setText(text)
        if widget is not None:
            widget.setVisible(visible)
        if label is not None:
            label.setVisible(visible)

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)
                continue

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
