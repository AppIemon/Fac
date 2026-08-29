#!/usr/bin/env python3
"""참고용 .litematic 을 읽어 engine.schematic.Schematic 으로 변환한다.

남의 설계를 뜯어보고 배우기 위한 도구. 층별 도면, 블록 통계,
특정 블록 주변 구조를 뽑아준다.
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import inspect_litematic as IL  # noqa: E402
from engine.blocks import Block  # noqa: E402
from engine.schematic import Schematic  # noqa: E402

# 참고 설계에 자주 나오는 블록의 표시 문자 (engine 팔레트에 없는 것 보강)
EXTRA_CHARS = {
    "air": ".", "stone": "#", "smooth_stone": "S", "cobblestone": "c",
    "water": "~", "lava": "L", "hopper": "h", "chest": "C", "dropper": "D",
    "dispenser": "n", "observer": "O", "piston": "P", "sticky_piston": "Q",
    "redstone_wire": "r", "redstone_block": "R", "redstone_torch": "t",
    "repeater": "y", "comparator": "k", "note_block": "N", "lever": "l",
    "glass": "g", "white_stained_glass": "g", "oak_leaves": "V",
    "moss_block": "M", "composter": "K", "furnace": "F", "sand": "s",
    "slime_block": "J", "honey_block": "Y", "rail": "=", "powered_rail": "+",
    "observer_": "O", "target": "T", "barrel": "B", "trapdoor": "d",
    "oak_trapdoor": "d", "torch": "*", "soul_sand": "$", "bone_block": "b",
    "iron_trapdoor": "i", "stone_button": "u", "lectern": "e",
}
_FALLBACK = "abcdefgijmnopqvwxz0123456789"


def load(path: str) -> tuple[Schematic, dict]:
    nbt = IL.parse(path)
    region_name, region = next(iter(nbt["Regions"].items()))
    size = region["Size"]
    w, h, l = abs(size["x"]), abs(size["y"]), abs(size["z"])
    palette = region["BlockStatePalette"]
    bits = max(2, (len(palette) - 1).bit_length())
    idx = IL.unpack_states(region["BlockStates"], bits, w * h * l)

    s = Schematic(name=nbt.get("Metadata", {}).get("Name", region_name))
    for i, v in enumerate(idx):
        if v == 0:
            continue
        entry = palette[v]
        name = entry["Name"]
        props = tuple(sorted((k, str(x)) for k, x in (entry.get("Properties") or {}).items()))
        y, rem = divmod(i, w * l)
        z, x = divmod(rem, w)
        s.blocks[(x, y, z)] = Block(name, props)
    meta = {
        "name": nbt.get("Metadata", {}).get("Name"),
        "version": nbt.get("Version"),
        "data_version": nbt.get("MinecraftDataVersion"),
        "size": (w, h, l),
        "total": nbt.get("Metadata", {}).get("TotalBlocks"),
    }
    return s, meta


def assign_chars(s: Schematic) -> dict[str, str]:
    """설계에 실제로 쓰인 블록에만 표시 문자를 배정한다."""
    used = sorted({b.short for b in s.blocks.values()})
    mapping, taken, spare = {}, set("."), iter(_FALLBACK)
    for short in used:
        ch = EXTRA_CHARS.get(short)
        if ch is None or ch in taken:
            ch = next((c for c in spare if c not in taken), "?")
        mapping[short] = ch
        taken.add(ch)
    return mapping


def render(s: Schematic, mapping: dict[str, str], y_from=None, y_to=None) -> str:
    lo, hi = s.bounds
    out = []
    ys = range(hi[1], lo[1] - 1, -1)
    for y in ys:
        if y_from is not None and y < y_from:
            continue
        if y_to is not None and y > y_to:
            continue
        rows = []
        for z in range(lo[2], hi[2] + 1):
            rows.append("".join(
                mapping.get(s.get(x, y, z).short, ".") if (x, y, z) in s.blocks else "."
                for x in range(lo[0], hi[0] + 1)))
        if all(set(r) <= {"."} for r in rows):
            continue
        out.append(f"── Y={y} " + "─" * 40)
        out.append("      " + "".join(str(abs(x) % 10) for x in range(lo[0], hi[0] + 1)))
        for i, row in enumerate(rows):
            out.append(f" z{lo[2] + i:>3} {row}")
        out.append("")
    return "\n".join(out)


def legend(s: Schematic, mapping: dict[str, str]) -> str:
    counts = Counter(b.short for b in s.blocks.values())
    lines = []
    for short, ch in sorted(mapping.items(), key=lambda kv: -counts[kv[0]]):
        states = sorted({str(b) for b in s.blocks.values() if b.short == short})
        lines.append(f" {ch}  {short:<24} x{counts[short]:<4}")
        if len(states) <= 6:
            for st in states:
                lines.append(f"      {st}")
        else:
            lines.append(f"      ({len(states)}가지 상태)")
    return "\n".join(lines)


def main() -> int:
    path = sys.argv[1]
    s, meta = load(path)
    print(f"# {meta['name']}   {meta['size'][0]}x{meta['size'][1]}x{meta['size'][2]}"
          f"   블록 {meta['total']}   DataVersion {meta['data_version']}")
    m = assign_chars(s)
    yf = int(sys.argv[2]) if len(sys.argv) > 2 else None
    yt = int(sys.argv[3]) if len(sys.argv) > 3 else None
    print(render(s, m, yf, yt))
    print(legend(s, m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
