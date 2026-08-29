"""Survival farm knowledge base.

A curated, machine-readable catalog of proven Minecraft survival farms
(mob/XP, resource, crop, wood, animal, redstone/utility). Each entry
records the *working principle* and concrete requirements so an AI can go
straight from "I know how it works" to a placeable blueprint.

All block/item/entity/biome IDs in the catalog are validated against the
real Minecraft 26.2 registry (see `farms/registry/ids_26.2.json`).
"""

from fac.farms.schema import Farm, Footprint, Source
from fac.farms.loader import load_farms, farms_by_id
from fac.farms.registry import Registry, validate_farm, validate_all

__all__ = [
    "Farm",
    "Footprint",
    "Source",
    "load_farms",
    "farms_by_id",
    "Registry",
    "validate_farm",
    "validate_all",
]
