from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Qt, Signal # type: ignore
from PySide6.QtWidgets import QButtonGroup # type: ignore


class SettingsPage(QObject):
    authentication_changed = Signal(str)

    def __init__(self, ui, settings: QSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.ui = ui
        self._settings = settings

        self._radio_group = QButtonGroup(self)
        self._radio_group.setExclusive(True)
        self._provider_map = {
            "active_directory": self.ui.rbSettingsActiveDirectory,
            "authentik": self.ui.rbSettingsAuthentik,
            "default": self.ui.rbSettingsDefault,
        }

        self._setup_styling()
        self._setup_behavior()
        self._load_saved_provider()
        self.retranslate()

    def _setup_styling(self) -> None:
        self.ui.btnSettingsTabAuthentication.setObjectName("btnSettingsTab")
        self.ui.btnSettingsTabAuthentication.setCursor(Qt.PointingHandCursor)
        self.ui.btnSettingsTabAuthentication.setFlat(True)
        self.ui.btnSettingsTabAuthentication.setEnabled(False)
        self.ui.btnSettingsTabAuthentication.setProperty("active", True)

        for button in self._provider_map.values():
            button.setObjectName("rbSettingsOption")
            button.setCursor(Qt.PointingHandCursor)

        self.ui.lblSettingsStatusBadge.setObjectName("badgeSettingsEnabled")

    def _setup_behavior(self) -> None:
        for provider, button in self._provider_map.items():
            self._radio_group.addButton(button)
            button.toggled.connect(
                lambda checked, provider=provider: self._on_provider_toggled(provider, checked)
            )

    def current_provider(self) -> str:
        for provider, button in self._provider_map.items():
            if button.isChecked():
                return provider
        return "default"

    def set_provider(self, provider: str) -> None:
        normalized = (provider or "").strip().lower()
        if normalized not in self._provider_map:
            normalized = "default"
        self._provider_map[normalized].setChecked(True)

    def retranslate(self, _locale_name: str | None = None) -> None:
        self.ui.lblSettingsTitle.setText(
            self.tr("Workspace Configuration")
        )
        self.ui.btnSettingsTabAuthentication.setText(
            self.tr("Authentication")
        )
        self.ui.lblSettingsSectionTitle.setText(
            self.tr("Workspace Authentication")
        )
        self.ui.lblSettingsSectionDescription.setText(
            self.tr("Choose how users sign in to the workspace.")
        )
        self.ui.rbSettingsActiveDirectory.setText("Active Directory")
        self.ui.rbSettingsAuthentik.setText("Authentik")
        self.ui.rbSettingsDefault.setText(
            self.tr("Default settings")
        )
        self.ui.lblSettingsStatusBadge.setText(
            self.tr("Configuration saved")
        )
        self.ui.lblSettingsStatusHint.setText(
            self.tr("The selected authentication method is saved automatically.")
        )

    def _load_saved_provider(self) -> None:
        saved = str(self._settings.value("settings/authentication_provider", "default") or "default")
        self.set_provider(saved)

    def _on_provider_toggled(self, provider: str, checked: bool) -> None:
        if not checked:
            return
        self._settings.setValue("settings/authentication_provider", provider)
        self._settings.sync()
        self.authentication_changed.emit(provider)
