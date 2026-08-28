"""Validate farm component IDs against the real Minecraft 26.2 registry.

The registry snapshot (`farms/registry/ids_26.2.json`) is generated from the
vanilla 26.2 data reports (blocks/items/entity_type) plus the paper-api biome
list. Validating every farm's blocks/mobs/items/biomes against it is a
concrete, honest "does this exist in the current version" check.
"""

from __future__ import annotations

import json
from pathlib import Path

from fac.farms.schema import Farm

ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "farms" / "registry" / "ids_26.2.json"


class Registry:
    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.version = data.get("version", "unknown")
        self.blocks = set(data["block"])
        self.items = set(data["item"])
        self.entities = set(data["entity_type"])
        self.biomes = set(data["biome"])

    def has_block(self, i: str) -> bool:
        return i in self.blocks

    def has_item(self, i: str) -> bool:
        # Many blocks are also placeable via their item form; accept either.
        return i in self.items or i in self.blocks

    def has_entity(self, i: str) -> bool:
        return i in self.entities

    def has_biome(self, i: str) -> bool:
        return i in self.biomes

    def has_placeable(self, i: str) -> bool:
        # Build components are placed as blocks or used as items/tools
        # (shears, glass bottle, redstone dust item, etc.).
        return i in self.blocks or i in self.items


def _check(reg_ok, ids: list[str], label: str, errors: list[str]) -> None:
    for i in ids:
        if not reg_ok(i):
            errors.append(f"{label}: unknown id {i!r}")


def validate_farm(farm: Farm, reg: Registry) -> list[str]:
    errors = list(farm.schema_errors())
    _check(reg.has_placeable, farm.blocks, "blocks", errors)
    _check(reg.has_entity, farm.mobs, "mobs", errors)
    _check(reg.has_item, farm.items_out, "items_out", errors)
    _check(reg.has_item, farm.items_in, "items_in", errors)
    _check(reg.has_biome, farm.biomes, "biomes", errors)
    return errors


def validate_all(farms: list[Farm], reg: Registry | None = None) -> dict[str, list[str]]:
    reg = reg or Registry()
    out: dict[str, list[str]] = {}
    for f in farms:
        errs = validate_farm(f, reg)
        if errs:
            out[f.id] = errs
    return out
