"""Load the farm catalog from the JSON data files under farms/data/."""

from __future__ import annotations

import json
from pathlib import Path

from fac.farms.schema import Farm

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "farms" / "data"


def load_farms(data_dir: Path = DATA_DIR) -> list[Farm]:
    farms: list[Farm] = []
    seen: set[str] = set()
    for path in sorted(Path(data_dir).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload["farms"] if isinstance(payload, dict) else payload
        for entry in entries:
            farm = Farm.from_dict(entry)
            if farm.id in seen:
                raise ValueError(f"duplicate farm id {farm.id!r} in {path.name}")
            seen.add(farm.id)
            farms.append(farm)
    return farms


def farms_by_id(farms: list[Farm] | None = None) -> dict[str, Farm]:
    farms = farms if farms is not None else load_farms()
    return {f.id: f for f in farms}
