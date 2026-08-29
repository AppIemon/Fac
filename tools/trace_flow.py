#!/usr/bin/env python3
"""아이템 경로 추적 — 호퍼/드로퍼 사슬을 따라가 어디서 끝나는지 본다.

불변조건 테스트는 '이 호퍼가 막혔나' 같은 국소 검사만 한다.
이 도구는 '생성기에서 나온 아이템이 실제로 산출 상자까지 가나'를 확인한다.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.blocks import OFFSET  # noqa: E402
from engine.schematic import Schematic  # noqa: E402

MOVERS = {"hopper", "dropper"}
# 사슬이 여기서 끝나면 정상이다. 발사기는 아이템을 소비해 밖으로 내보낸다.
TERMINALS = {"chest", "furnace", "composter", "crafter", "barrel", "dispenser"}


def trace(s: Schematic, start: tuple[int, int, int], limit: int = 400) -> dict:
    """start 의 호퍼/드로퍼에서 아이템이 흘러가는 경로를 따라간다."""
    path = [start]
    seen = {start}
    pos = start
    while len(path) < limit:
        b = s.get(*pos)
        if b.short not in MOVERS:
            return {"end": pos, "end_block": b.short, "steps": len(path), "path": path,
                    "ok": b.short in TERMINALS}
        dx, dy, dz = OFFSET[b.properties["facing"]]
        nxt = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
        nb = s.get(*nxt)
        if nb.short not in MOVERS and nb.short not in TERMINALS:
            return {"end": nxt, "end_block": nb.short, "steps": len(path), "path": path,
                    "ok": False, "reason": f"{nb.short} 에서 막힘"}
        if nxt in seen:
            return {"end": nxt, "end_block": nb.short, "steps": len(path), "path": path,
                    "ok": False, "reason": "순환"}
        seen.add(nxt)
        path.append(nxt)
        pos = nxt
    return {"end": pos, "steps": len(path), "path": path, "ok": False, "reason": "너무 길다"}


def describe(s: Schematic, label: str, start: tuple[int, int, int]) -> str:
    r = trace(s, start)
    mark = "OK " if r["ok"] else "!! "
    tail = "" if r["ok"] else f"  ({r.get('reason', '')})"
    return (f"{mark}{label:<34} {start} → {r['end']} [{r['end_block']}] "
            f"{r['steps']}칸{tail}")


if __name__ == "__main__":
    from engine.designs import build
    name = sys.argv[1] if len(sys.argv) > 1 else "cobble_factory"
    kw = {}
    for a in sys.argv[2:]:
        k, v = a.split("=")
        kw[k] = int(v)
    d = build(name, **kw)
    s = d.schematic
    # 모든 호퍼/드로퍼 사슬의 '시작점'(아무도 자기를 향하지 않는 것)을 찾아 추적
    movers = {p for p, b in s.blocks.items() if b.short in MOVERS}
    targeted = set()
    for p in movers:
        b = s.get(*p)
        dx, dy, dz = OFFSET[b.properties["facing"]]
        targeted.add((p[0] + dx, p[1] + dy, p[2] + dz))
    starts = sorted(movers - targeted)
    print(f"# {name} — 사슬 시작점 {len(starts)}개")
    bad = 0
    for p in starts:
        line = describe(s, "", p)
        if not line.startswith("OK"):
            bad += 1
        print(" ", line)
    print(f"\n막힌 사슬: {bad}개")
    raise SystemExit(1 if bad else 0)
