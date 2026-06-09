from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QObject, QCoreApplication, Signal # type: ignore

from src.api.client import ApiClient
from src.api import endpoints as ep

log = logging.getLogger(__name__)

@dataclass
class TransportInfo:
    id: str = ""
    name: str = ""
    link: str = ""
    priority: int = 0
    is_application: bool | None = None
    transport_type: str = ""
    application: str | None = None


@dataclass
class ServiceGroup:
    id: str = ""
    name: str = ""
    priority: int = 0
    image_uuid: str = ""


@dataclass
class ServiceInfo:
    id: str = ""
    name: str = ""
    visual_name: str = ""
    description: str = ""
    group: ServiceGroup = field(default_factory=ServiceGroup)
    transports: list[TransportInfo] = field(default_factory=list)
    image_id: str = ""
    is_application: bool | None = None
    is_meta: bool = False
    in_use: bool = False
    maintenance: bool = False
    not_accessible: bool = False
    allow_remove: bool = False
    allow_reset: bool = False
    allow_poweroff: bool = False
    allow_poweron: bool = False
    show_transports: bool = False
    custom_message: str | None = None

    @property
    def is_available(self) -> bool:
        return not self.maintenance and not self.not_accessible

    @property
    def status_text(self) -> str:
        if self.maintenance:
            return QCoreApplication.translate("ServiceInfo", "In maintenance")
        if self.not_accessible:
            return QCoreApplication.translate("ServiceInfo", "Unavailable")
        if self.in_use:
            return QCoreApplication.translate("ServiceInfo", "In use")
        return QCoreApplication.translate("ServiceInfo", "Available")

    @property
    def is_desktop(self) -> bool:
        if self.is_application is not None:
            return not self.is_application
        markers = ('desktop', 'desktops', 'workspace', 'рабоч', 'vdi', 'wvd')
        haystack = ' '.join((self.group.name, self.name, self.visual_name, self.description)).lower()
        return any(marker in haystack for marker in markers)

    @property
    def default_transport(self) -> TransportInfo | None:
        if not self.transports:
            return None
        return min(self.transports, key=lambda t: t.priority)

class ServicesAPI(QObject):

    services_ready = Signal(list)
    services_error = Signal(str)
    connect_ready = Signal(str, str)
    connect_error = Signal(str)
    action_done = Signal()

    def __init__(self, client: ApiClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._services: list[ServiceInfo] = []

    @property
    def services(self) -> list[ServiceInfo]:
        return self._services

    def fetch_services(self) -> None:
        self._client.get(
            ep.SERVICES_OVERVIEW,
            on_success=self._on_services_ok,
            on_error=self._on_services_fail,
        )

    def _on_services_ok(self, data: Any) -> None:
        try:
            log.debug("Parsing services response")
            result = data.get("result", data) if isinstance(data, dict) else data
            raw_services = result.get("services", []) if isinstance(result, dict) else []
            log.debug("Raw services list: %d items", len(raw_services))

            self._services = []
            for raw in raw_services:
                svc = self._parse_service(raw)
                if svc:
                    log.debug(
                        "Parsed service: id=%r title=%r image_id=%r is_application=%r transports=%d",
                        svc.id,
                        svc.visual_name or svc.name,
                        svc.image_id,
                        svc.is_application,
                        len(svc.transports),
                    )
                    self._services.append(svc)

            log.info("Fetched %d service(s)", len(self._services))
            self.services_ready.emit(self._services)

        except Exception as exc:
            log.exception("Failed to parse services response")
            self.services_error.emit(QCoreApplication.translate("ServicesAPI", "Failed to parse services list: {error}").format(error=exc))

    def _on_services_fail(self, msg: str, code: int) -> None:
        log.warning("Failed to fetch services: %s (status=%d)", msg, code)
        self.services_error.emit(msg)

    @staticmethod
    def _coerce_optional_bool(value: Any) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", ""}:
                return False
        return None

    @staticmethod
    def _parse_service(raw: dict) -> ServiceInfo | None:
        if not isinstance(raw, dict):
            return None

        raw_group = raw.get("group", {})
        group = ServiceGroup(
            id=str(raw_group.get("id", "")),
            name=str(raw_group.get("name", "")),
            priority=int(raw_group.get("priority", 0)),
            image_uuid=str(raw_group.get("imageUuid", "")),
        )

        transports = []
        transport_application_flags: list[bool] = []
        for rt in raw.get("transports", []):
            if isinstance(rt, dict) and rt.get("id"):
                transport_is_application = ServicesAPI._coerce_optional_bool(rt.get("is_application"))
                if transport_is_application is not None:
                    transport_application_flags.append(transport_is_application)
                transports.append(TransportInfo(
                    id=str(rt.get("id", "")),
                    name=str(rt.get("name", "")),
                    link=str(rt.get("link", "")),
                    priority=int(rt.get("priority", 0)),
                    is_application=transport_is_application,
                    transport_type=str(rt.get("type", "")),
                    application=rt.get("application"),
                ))

        service_is_application = ServicesAPI._coerce_optional_bool(raw.get("is_application")) if "is_application" in raw else None
        if service_is_application is None and transport_application_flags:
            service_is_application = True if any(transport_application_flags) else False

        return ServiceInfo(
            id=str(raw.get("id", "")),
            name=str(raw.get("name", "")),
            visual_name=str(raw.get("visual_name", "")),
            description=str(raw.get("description", "")),
            group=group,
            transports=transports,
            image_id=str(raw.get("imageId", "")),
            is_application=service_is_application,
            is_meta=bool(raw.get("is_meta", False)),
            in_use=bool(raw.get("in_use", False)),
            maintenance=bool(raw.get("maintenance", False)),
            not_accessible=bool(raw.get("not_accesible", False)),
            allow_remove=bool(raw.get("allow_users_remove", False)),
            allow_reset=bool(raw.get("allow_users_reset", False)),
            allow_poweroff=bool(raw.get("allow_users_poweroff", False)),
            allow_poweron=bool(raw.get("allow_users_poweron", False)),
            show_transports=bool(raw.get("show_transports", False)),
            custom_message=raw.get("custom_message_text"),
        )

    def connect_service(self, service_id: str, transport_id: str) -> None:
        path = f"{ep.SERVICES_OVERVIEW}/{service_id}/{transport_id}/gorizontvslink"
        self._client.get(
            path,
            on_success=lambda data: self._on_connect_ok(service_id, data),
            on_error=lambda msg, code: self._on_connect_fail(msg),
        )

    def _on_connect_ok(self, service_id: str, data: Any) -> None:
        result = data.get("result", "") if isinstance(data, dict) else str(data)
        error = data.get("error", "") if isinstance(data, dict) else ""
        if error:
            log.warning("Connect error: %s", error)
            self.connect_error.emit(str(error))
            return
        log.info("Connect ready for %s: %s", service_id, str(result)[:60])
        self.connect_ready.emit(service_id, str(result))

    def _on_connect_fail(self, msg: str) -> None:
        log.warning("Connect request failed: %s", msg)
        self.connect_error.emit(msg)

    def service_action(self, service_id: str, action: str) -> None:
        path = f"{ep.SERVICES_OVERVIEW}/{service_id}/action/{action}"
        self._client.get(
            path,
            on_success=lambda _: self._on_action_ok(service_id, action),
            on_error=lambda msg, code: self.connect_error.emit(msg),
        )

    def _on_action_ok(self, service_id: str, action: str) -> None:
        log.info("Action '%s' on %s completed", action, service_id)
        self.action_done.emit()