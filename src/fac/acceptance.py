"""Acceptance tests the AI must pass before a design is exported."""

from __future__ import annotations

from dataclasses import dataclass, field

from fac.catalog import BIOMES, DIMENSIONS, MOBS, MODULES
from fac.designer import FactoryDesign, overlapping_pairs
from fac.simulator import SimResult


@dataclass
class Check:
    id: str
    ok: bool
    detail: str


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def add(self, cid: str, ok: bool, detail: str) -> None:
        self.checks.append(Check(cid, ok, detail))

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "passed": sum(1 for c in self.checks if c.ok),
            "failed": sum(1 for c in self.checks if not c.ok),
            "checks": [c.__dict__ for c in self.checks],
        }


def evaluate(design: FactoryDesign, sim: SimResult) -> Report:
    report = Report()
    _goals(report, design, sim)
    _world(report, design)
    _layout(report, design)
    _logistics(report, design, sim)
    _mobs(report, design)
    return report


def _goals(report: Report, design: FactoryDesign, sim: SimResult) -> None:
    # Steady-state catalog rates (the number the designer sizes against).
    # The simulator is used for belts / starvation / overflow, not for the
    # first-minute warmup penalty on processing chains.
    net = design.net()
    scale = sim.hours if sim.hours else 1.0
    for item, goal in design.goals.items():
        got = net.get(item, 0.0)
        shipped = sim.produced.get(item, 0.0) / scale
        report.add(
            f"goal:{item}",
            got + 1e-6 >= goal,
            f"{got:.1f}/h net, {shipped:.1f}/h shipped vs goal {goal:.1f}/h",
        )


def _world(report: Report, design: FactoryDesign) -> None:
    used_dims = {m.dimension for m in design.modules}
    for dim in DIMENSIONS:
        report.add(
            f"dim:{dim}",
            dim in used_dims,
            "has modules" if dim in used_dims else "empty dimension",
        )
    for dim in used_dims:
        report.add(
            f"dim_known:{dim}",
            dim in DIMENSIONS,
            "catalog dimension" if dim in DIMENSIONS else "unknown dimension",
        )
    used_biomes = {m.biome for m in design.modules}
    for biome in used_biomes:
        report.add(
            f"biome:{biome}",
            biome in BIOMES,
            "catalog biome" if biome in BIOMES else "unknown biome",
        )
    # Portal connectivity: every non-campus dim must have a portal hub.
    by_dim = design.modules_by_dim()
    for dim, mods in by_dim.items():
        if not mods:
            continue
        hubs = [m for m in mods if m.spec_id == "portal_hub"]
        report.add(
            f"portal:{dim}",
            len(hubs) >= 1,
            f"{len(hubs)} hub(s)",
        )
        anchors = [m for m in mods if m.spec_id == "chunk_anchor"]
        report.add(
            f"chunks:{dim}",
            len(anchors) >= 1,
            f"{len(anchors)} anchor(s)",
        )
    hqs = [m for m in design.modules if m.spec_id == "hq"]
    silos = [m for m in design.modules if m.spec_id == "silo"]
    report.add("infra:hq", len(hqs) == 1, f"{len(hqs)} HQ")
    report.add("infra:silo", len(silos) >= 1, f"{len(silos)} silo(s)")


def _layout(report: Report, design: FactoryDesign) -> None:
    hits = overlapping_pairs(design.modules)
    report.add("layout:overlap", not hits, "none" if not hits else f"{hits[:8]}")
    for m in design.modules:
        spec = MODULES[m.spec_id]
        report.add(
            f"layout:dim:{m.uid}",
            m.dimension == spec.dimension or m.spec_id in ("portal_hub", "chunk_anchor"),
            f"{m.dimension} (spec {spec.dimension})",
        )


def _logistics(report: Report, design: FactoryDesign, sim: SimResult) -> None:
    report.add(
        "logistics:overflow",
        not sim.overflow,
        "ok" if not sim.overflow else str(sim.overflow),
    )
    report.add(
        "logistics:belts",
        not sim.belt_backlog,
        "ok" if not sim.belt_backlog else str(sim.belt_backlog),
    )
    # Starvation is allowed only on the first slice of a processing chain
    # if inputs are produced in the same hour — require < 5% of runtime.
    for uid, hours in sim.starved.items():
        report.add(
            f"starve:{uid}",
            hours <= sim.hours * 0.05 + 1e-9,
            f"starved {hours:.3f}h of {sim.hours}h",
        )
    if not sim.starved:
        report.add("logistics:starve", True, "no starvation")


def _mobs(report: Report, design: FactoryDesign) -> None:
    spawned: set[str] = set()
    for m in design.modules:
        spawned.update(m.spec.mobs)
        spawned.update(m.spec.workers)
    required = {role.id for role in MOBS.values()}
    for rid in sorted(required):
        role = MOBS[rid]
        present = rid in spawned
        # Ambient biome-only roles still count if a module uses that biome.
        if not present:
            present = any(m.biome == role.biome for m in design.modules)
        report.add(f"mob:{rid}", present, f"{role.name} in {role.dimension}")
