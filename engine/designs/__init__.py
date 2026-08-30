"""실제 시공 가능한 파라메트릭 설계 모음 (.litematic 출력용)."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..schematic import Schematic


@dataclass
class Design:
    schematic: Schematic
    principle: str = ""
    circuit: list[str] = field(default_factory=list)   # 신호 경로를 단계별로
    steps: list[str] = field(default_factory=list)
    rate: str = ""
    warnings: list[str] = field(default_factory=list)
    manual_items: list[str] = field(default_factory=list)  # 스케매틱이 못 놓는 것


from . import (cobblegen, cobblegen_tnt, composterbank,
               kelpfarm, kelpfarm_bonemeal, mossbed,
               mossbed_auto,
               smelter,
               full_factory, smelter_dropper, stonegen,
               sugarcane)  # noqa: E402

REGISTRY = {
    "sugarcane": sugarcane.build,
    "cobblegen": cobblegen.build,
    "smelter": smelter.build,
    "mossbed": mossbed.build,
    "composterbank": composterbank.build,
    "kelpfarm": kelpfarm.build,
    "stonegen": stonegen.build,
    "smelter_dropper": smelter_dropper.build,
    "mossbed_auto": mossbed_auto.build,
    "cobblegen_tnt": cobblegen_tnt.build,
    "kelpfarm_bonemeal": kelpfarm_bonemeal.build,
    "full_factory": full_factory.build,
}


def build(name: str, **params):
    if name not in REGISTRY:
        raise KeyError(f"알 수 없는 설계: {name}. 사용 가능: {', '.join(sorted(REGISTRY))}")
    return REGISTRY[name](**params)
