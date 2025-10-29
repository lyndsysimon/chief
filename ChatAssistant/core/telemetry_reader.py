"""Telemetry reader for the War Thunder local HTTP telemetry API."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from requests import RequestException, Response, Session

from .state_manager import AssistantState

LOGGER = logging.getLogger(__name__)


@dataclass
class TelemetryConfig:
    """Configuration for polling the local telemetry endpoint."""

    endpoint: str = "http://127.0.0.1:8111/state"
    poll_interval_sec: float = 0.25


class TelemetryReader:
    """Continuously polls the local telemetry endpoint and updates shared state."""

    def __init__(
        self,
        state: AssistantState,
        config: Optional[TelemetryConfig] = None,
        session: Optional[Session] = None,
    ) -> None:
        self._state = state
        self._config = config or TelemetryConfig()
        self._session: Session | None = session

    def run_forever(self) -> None:
        """Blocking loop that updates telemetry snapshots until process exit."""

        LOGGER.info("Starting telemetry reader on %s", self._config.endpoint)
        while True:
            try:
                snapshot = self._fetch_snapshot()
                if snapshot:
                    normalized = self._normalize_snapshot(snapshot)
                    self._state.update_telemetry_snapshot(normalized)
            except (RequestException, ValueError) as exc:
                LOGGER.debug("Telemetry poll failed: %s", exc)
            time.sleep(self._config.poll_interval_sec)

    def _fetch_snapshot(self) -> Optional[Dict]:
        response: Response | None = None
        try:
            session = self._ensure_session()
            response = session.get(  # type: ignore[union-attr]
                self._config.endpoint,
                timeout=0.1,
            )
            response.raise_for_status()
            return response.json()
        finally:
            _maybe_close(response)

    def _normalize_snapshot(self, raw: Dict) -> Dict:
        """Normalize units and return a simplified telemetry dictionary."""

        vehicle = raw.get("name") or raw.get("plane_name")
        status = {
            "vehicle": vehicle,
            "fuel_percent": raw.get("fuel", 0) * 100 if isinstance(raw.get("fuel"), float) else raw.get("fuel"),
            "ias_kmh": raw.get("speed", {}).get("kmh") or raw.get("ias"),
            "pitch_deg": raw.get("pitch"),
            "roll_deg": raw.get("roll"),
            "aoa_deg": raw.get("aoa"),
            "altitude_m": raw.get("altitude"),
            "g_load": raw.get("g_force"),
            "ammo": raw.get("ammo"),
            "gear_state": raw.get("gear"),
            "flap_state": raw.get("flaps"),
            "damage": raw.get("damage"),
            "temperatures_c": raw.get("temperatures"),
        }
        return status

    def _ensure_session(self) -> Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session


def _maybe_close(response: Response | None) -> None:
    if response is None:
        return
    close = getattr(response, "close", None)
    if callable(close):
        try:
            close()
        except Exception:  # pragma: no cover - defensive
            LOGGER.debug("Error closing telemetry response", exc_info=True)

