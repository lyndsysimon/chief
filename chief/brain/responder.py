"""Response logic for telemetry and reference queries."""
from __future__ import annotations

from typing import Dict, List

from ..core.reference_data import ReferenceDataRegistry
from ..core.state_manager import AssistantState


class TelemetryResponder:
    """Builds responses and context payloads from telemetry and reference data."""

    def __init__(self, state: AssistantState, reference_data: ReferenceDataRegistry) -> None:
        self._state = state
        self._reference_data = reference_data

    def generate_telemetry_only_response(self) -> str:
        snapshot = self._state.get_telemetry_snapshot()
        parts = []
        fuel = snapshot.get("fuel_percent")
        if fuel is not None:
            parts.append(f"Fuel: {fuel}%")
        ias = snapshot.get("ias_kmh")
        if ias is not None:
            parts.append(f"IAS: {ias} km/h")
        aoa = snapshot.get("aoa_deg")
        if aoa is not None:
            parts.append(f"AoA: {aoa}°")
        g_load = snapshot.get("g_load")
        if g_load is not None:
            annotation = snapshot.get("g_status") or ""
            suffix = f" ({annotation})" if annotation else ""
            parts.append(f"G-load: {g_load}{suffix}")
        damage = snapshot.get("damage")
        if isinstance(damage, dict):
            formatted = "; ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in damage.items())
            parts.append(formatted)
        return ", ".join(parts) if parts else "No data"

    def build_context_messages(self) -> List[Dict[str, str]]:
        snapshot = self._state.get_telemetry_snapshot()
        vehicle_name = snapshot.get("vehicle")
        reference = self._reference_data.find_for_vehicle(vehicle_name) or {}

        telemetry_block = self._serialize_dict(snapshot)
        reference_block = self._serialize_dict(reference)

        return [
            {"role": "assistant", "content": f"Telemetry: {telemetry_block}"},
            {"role": "assistant", "content": f"Reference: {reference_block}"},
        ]

    def _serialize_dict(self, data: Dict) -> str:
        if not data:
            return "{}"
        parts = []
        for key, value in data.items():
            parts.append(f"{key}: {value}")
        return ", ".join(parts)

    def get_current_state(self) -> Dict:
        """Expose the telemetry snapshot for external consumers (UI, tests)."""

        return self._state.get_telemetry_snapshot()
