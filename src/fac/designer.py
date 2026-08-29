"""Greedy AI designer: place modules until goals and world constraints hold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from fac.catalog import (
    BASE_BELT_RATE,
    BELT_UPGRADE,
    DEFAULT_GOALS,
    DIMENSIONS,
    GRID_PITCH,
    MODULES,
    ModuleSpec,
)


@dataclass
class PlacedModule:
    uid: str
    spec_id: str
    dimension: str
    biome: str
    x: int
    y: int
    z: int
    belts: int = 1

    @property
    def spec(self) -> ModuleSpec:
        return MODULES[self.spec_id]

    @property
    def belt_rate(self) -> float:
        return BASE_BELT_RATE + (self.belts - 1) * BELT_UPGRADE

    def bbox(self) -> tuple[int, int, int, int, int, int]:
        w, h, d = self.spec.footprint
        return self.x, self.y, self.z, self.x + w, self.y + h, self.z + d


@dataclass
class FactoryDesign:
    goals: dict[str, float]
    modules: list[PlacedModule] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    iterations: int = 0

    def production(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for placed in self.modules:
            for item, rate in placed.spec.outputs.items():
                out[item] = out.get(item, 0.0) + rate
        return out

    def consumption(self) -> dict[str, float]:
        need: dict[str, float] = {}
        for placed in self.modules:
            for item, rate in placed.spec.inputs.items():
                need[item] = need.get(item, 0.0) + rate
        return need

    def net(self) -> dict[str, float]:
        prod = self.production()
        cons = self.consumption()
        keys = set(prod) | set(cons)
        return {k: prod.get(k, 0.0) - cons.get(k, 0.0) for k in keys}

    def modules_by_dim(self) -> dict[str, list[PlacedModule]]:
        grouped: dict[str, list[PlacedModule]] = {d: [] for d in DIMENSIONS}
        for m in self.modules:
            grouped.setdefault(m.dimension, []).append(m)
        return grouped

    def to_dict(self) -> dict:
        return {
            "goals": self.goals,
            "iterations": self.iterations,
            "notes": self.notes,
            "net": self.net(),
            "modules": [
                {
                    "uid": m.uid,
                    "spec": m.spec_id,
                    "name": m.spec.name,
                    "name_ko": m.spec.name_ko,
                    "dimension": m.dimension,
                    "biome": m.biome,
                    "x": m.x,
                    "y": m.y,
                    "z": m.z,
                    "w": m.spec.footprint[0],
                    "h": m.spec.footprint[1],
                    "d": m.spec.footprint[2],
                    "belts": m.belts,
                    "belt_rate": m.belt_rate,
                    "outputs": m.spec.outputs,
                    "inputs": m.spec.inputs,
                    "mobs": list(m.spec.mobs),
                    "structure": m.spec.structure,
                    "palette": m.spec.palette,
                }
                for m in self.modules
            ],
        }


PRODUCERS: dict[str, list[str]] = {}
for _mid, _spec in MODULES.items():
    for _item in _spec.outputs:
        PRODUCERS.setdefault(_item, []).append(_mid)


class Designer:
    """Place the cheapest set of modules that covers goals + infrastructure."""

    INFRA = ("hq", "silo", "portal_hub", "chunk_anchor")

    def __init__(self, goals: dict[str, float] | None = None) -> None:
        self.goals = dict(goals or DEFAULT_GOALS)
        self._counters: dict[str, int] = {}
        self._next_plot: dict[str, int] = {d: 0 for d in DIMENSIONS}

    def design(self) -> FactoryDesign:
        factory = FactoryDesign(goals=dict(self.goals))
        for infra in self.INFRA:
            self._place(factory, infra)
        # One portal hub in every dimension (campus already has one).
        for dim in DIMENSIONS:
            if dim == "fac:campus":
                continue
            self._place(factory, "portal_hub", dimension=dim)
            self._place(factory, "chunk_anchor", dimension=dim)

        factory.iterations = 0
        while factory.iterations < 80:
            factory.iterations += 1
            missing = self._missing(factory)
            if not missing:
                break
            item, deficit = missing[0]
            producer = self._pick_producer(item)
            if producer is None:
                factory.notes.append(f"no producer for {item}")
                break
            self._place(factory, producer)
            factory.notes.append(
                f"iter {factory.iterations}: +{producer} for {item} (need {deficit:.0f}/h)"
            )
        self._upgrade_belts(factory)
        return factory

    def _missing(self, factory: FactoryDesign) -> list[tuple[str, float]]:
        net = factory.net()
        missing = []
        for item, goal in self.goals.items():
            have = net.get(item, 0.0)
            if have + 1e-6 < goal:
                missing.append((item, goal - have))
        for item, need in factory.consumption().items():
            have = factory.production().get(item, 0.0)
            if have + 1e-6 < need:
                missing.append((item, need - have))
        missing.sort(key=lambda kv: -kv[1])
        return missing

    def _pick_producer(self, item: str) -> str | None:
        cands = PRODUCERS.get(item)
        if not cands:
            return None
        # Prefer the module whose primary output is this item.
        cands = sorted(cands, key=lambda mid: -MODULES[mid].outputs.get(item, 0.0))
        return cands[0]

    def _place(
        self,
        factory: FactoryDesign,
        spec_id: str,
        dimension: str | None = None,
    ) -> PlacedModule:
        spec = MODULES[spec_id]
        dim = dimension or spec.dimension
        n = self._counters.get(spec_id, 0)
        self._counters[spec_id] = n + 1
        plot = self._next_plot.get(dim, 0)
        self._next_plot[dim] = plot + 1
        col = plot % 8
        row = plot // 8
        x = col * GRID_PITCH
        z = row * GRID_PITCH
        y = 64
        biome = spec.biome
        # Portal hubs inherit the destination dimension biome.
        if spec_id in ("portal_hub", "chunk_anchor") and dimension:
            biome = DIMENSIONS[dim].biome
        placed = PlacedModule(
            uid=f"{spec_id}_{n}",
            spec_id=spec_id,
            dimension=dim,
            biome=biome,
            x=x,
            y=y,
            z=z,
        )
        factory.modules.append(placed)
        return placed

    def _upgrade_belts(self, factory: FactoryDesign) -> None:
        for placed in factory.modules:
            total_out = sum(placed.spec.outputs.values())
            if total_out <= 0:
                continue
            while placed.belt_rate + 1e-6 < total_out:
                placed.belts += 1
                if placed.belts > 16:
                    break


def overlapping_pairs(modules: Iterable[PlacedModule]) -> list[tuple[str, str]]:
    by_dim: dict[str, list[PlacedModule]] = {}
    for m in modules:
        by_dim.setdefault(m.dimension, []).append(m)
    hits: list[tuple[str, str]] = []
    for group in by_dim.values():
        for i, a in enumerate(group):
            ax1, _, az1, ax2, _, az2 = a.bbox()
            for b in group[i + 1 :]:
                bx1, _, bz1, bx2, _, bz2 = b.bbox()
                if ax1 < bx2 and ax2 > bx1 and az1 < bz2 and az2 > bz1:
                    hits.append((a.uid, b.uid))
    return hits
