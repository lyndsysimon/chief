"""Reference data access for vehicle-specific limits."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class ReferenceDataRegistry:
    """Loads JSON reference files from disk and returns matching entries."""

    def __init__(self, base_path: str) -> None:
        self._base_path = Path(base_path)

    def find_for_vehicle(self, vehicle_name: Optional[str]) -> Optional[Dict]:
        if not vehicle_name:
            return None
        slug = self._normalize_vehicle_name(vehicle_name)
        file_path = self._base_path / f"{slug}.json"
        if not file_path.exists():
            return None
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _normalize_vehicle_name(self, name: str) -> str:
        return name.lower().replace(" ", "_")

