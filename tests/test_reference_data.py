import json
from pathlib import Path

from ChatAssistant.core.reference_data import ReferenceDataRegistry


def test_returns_none_when_vehicle_missing(tmp_path: Path) -> None:
    registry = ReferenceDataRegistry(str(tmp_path))

    assert registry.find_for_vehicle(None) is None
    assert registry.find_for_vehicle("Unknown Vehicle") is None


def test_loads_matching_vehicle_file(tmp_path: Path) -> None:
    data_dir = tmp_path
    file_path = data_dir / "f_16a.json"
    file_path.write_text(json.dumps({"flaps": "450 km/h"}), encoding="utf-8")

    registry = ReferenceDataRegistry(str(data_dir))

    assert registry.find_for_vehicle("F 16A") == {"flaps": "450 km/h"}
