"""Hour-resolution factory simulator.

Modules consume inputs from a shared silo and push outputs through a
belt with finite items/hour. The silo is the only buffer. This is not a
redstone-tick emulator; it is the acceptance model the AI iterates on.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fac.catalog import SILO_CAPACITY
from fac.designer import FactoryDesign


@dataclass
class SimResult:
    hours: float
    produced: dict[str, float]
    consumed: dict[str, float]
    silo: dict[str, float]
    starved: dict[str, float]
    overflow: dict[str, float]
    belt_backlog: dict[str, float]
    snapshots: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "hours": self.hours,
            "produced": self.produced,
            "consumed": self.consumed,
            "silo": self.silo,
            "starved": self.starved,
            "overflow": self.overflow,
            "belt_backlog": self.belt_backlog,
            "snapshots": self.snapshots,
        }


def simulate(design: FactoryDesign, hours: float = 1.0, steps: int = 60) -> SimResult:
    """Simulate `hours` of factory time in `steps` equal slices."""
    dt = hours / steps
    silo: dict[str, float] = {}
    produced: dict[str, float] = {}
    consumed: dict[str, float] = {}
    starved: dict[str, float] = {}
    overflow: dict[str, float] = {}
    belt_backlog: dict[str, float] = {}
    snapshots: list[dict] = []

    for step in range(steps):
        # Consume first so crafters/smelters can starve honestly.
        for placed in design.modules:
            if not placed.spec.inputs:
                continue
            can_run = 1.0
            for item, rate in placed.spec.inputs.items():
                need = rate * dt
                have = silo.get(item, 0.0)
                if need > 0:
                    can_run = min(can_run, have / need)
            can_run = max(0.0, min(1.0, can_run))
            if can_run < 1.0 - 1e-9:
                starved[placed.uid] = starved.get(placed.uid, 0.0) + (1.0 - can_run) * dt
            for item, rate in placed.spec.inputs.items():
                take = rate * dt * can_run
                silo[item] = silo.get(item, 0.0) - take
                consumed[item] = consumed.get(item, 0.0) + take
            # Scale outputs of processing modules by can_run
            for item, rate in placed.spec.outputs.items():
                made = rate * dt * can_run
                _push(placed, item, made, silo, produced, overflow, belt_backlog, dt)

        for placed in design.modules:
            if placed.spec.inputs:
                continue
            for item, rate in placed.spec.outputs.items():
                made = rate * dt
                _push(placed, item, made, silo, produced, overflow, belt_backlog, dt)

        if step in (0, steps // 2, steps - 1):
            snapshots.append(
                {
                    "hour": (step + 1) * dt,
                    "silo_total": sum(silo.values()),
                    "iron": silo.get("iron_ingot", 0.0),
                    "gold": silo.get("gold_ingot", 0.0),
                    "gunpowder": silo.get("gunpowder", 0.0),
                }
            )

    return SimResult(
        hours=hours,
        produced=produced,
        consumed=consumed,
        silo=silo,
        starved=starved,
        overflow=overflow,
        belt_backlog=belt_backlog,
        snapshots=snapshots,
    )


def _push(
    placed,
    item: str,
    made: float,
    silo: dict[str, float],
    produced: dict[str, float],
    overflow: dict[str, float],
    belt_backlog: dict[str, float],
    dt: float,
) -> None:
    if made <= 0:
        return
    cap = placed.belt_rate * dt
    shipped = min(made, cap)
    if made > cap + 1e-9:
        belt_backlog[placed.uid] = belt_backlog.get(placed.uid, 0.0) + (made - cap)
    new_total = silo.get(item, 0.0) + shipped
    if new_total > SILO_CAPACITY:
        overflow[item] = overflow.get(item, 0.0) + (new_total - SILO_CAPACITY)
        silo[item] = SILO_CAPACITY
    else:
        silo[item] = new_total
    produced[item] = produced.get(item, 0.0) + shipped
