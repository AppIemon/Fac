"""희소 복셀 모델 -> .litematic 파일.

Grid(ASCII 미리보기용) 과 달리 실제 블록 상태를 그대로 담으며,
litemapy 로 Litematica 스케매틱을 쓴다.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .blocks import AIR, Block, preview_char

# Minecraft 26.2 (Chaos Cubed) 의 DataVersion.
# 이 값은 Litematica 의 DataFixer 가 블록 상태를 보정할 때 쓴다.
MC_DATA_VERSION_26_2 = 4903


@dataclass
class Schematic:
    """설계 좌표계: x=동(+)/서(-), y=위(+)/아래(-), z=남(+)/북(-)."""
    name: str = "schematic"
    author: str = "Fac"
    description: str = ""
    blocks: dict[tuple[int, int, int], Block] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    # -- 배치 --------------------------------------------------------------
    def set(self, x: int, y: int, z: int, block: Block) -> None:
        if block.id == "minecraft:air":
            self.blocks.pop((x, y, z), None)
        else:
            self.blocks[(x, y, z)] = block

    def fill(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, block: Block) -> None:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, block)

    def get(self, x: int, y: int, z: int) -> Block:
        return self.blocks.get((x, y, z), AIR)

    def note(self, text: str) -> None:
        self.notes.append(text)

    def paste(self, other: "Schematic", dx: int = 0, dy: int = 0, dz: int = 0,
              label: str = "") -> None:
        """다른 설계를 오프셋을 주고 겹쳐 넣는다 (공장 합성용).

        이미 블록이 있는 자리에 다른 블록을 덮어쓰려 하면 예외를 낸다.
        모듈을 잘못 겹쳐 놓고 모르는 채로 넘어가는 걸 막는다.
        """
        for (x, y, z), b in other.blocks.items():
            pos = (x + dx, y + dy, z + dz)
            old = self.blocks.get(pos)
            if old is not None and old != b:
                raise ValueError(
                    f"모듈 충돌 {label or other.name} at {pos}: "
                    f"{old} 자리에 {b} 를 놓으려 한다")
            self.blocks[pos] = b
        for n in other.notes:
            self.notes.append(f"[{label or other.name}] {n}")

    # -- 조회 --------------------------------------------------------------
    @property
    def bounds(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        if not self.blocks:
            return (0, 0, 0), (0, 0, 0)
        xs, ys, zs = zip(*self.blocks)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    @property
    def size(self) -> tuple[int, int, int]:
        lo, hi = self.bounds
        return hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1

    def material_list(self) -> list[tuple[str, int]]:
        c = Counter(b.short for b in self.blocks.values())
        return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))

    # -- 미리보기 ----------------------------------------------------------
    def preview(self) -> str:
        if not self.blocks:
            return "(빈 설계)"
        lo, hi = self.bounds
        out: list[str] = []
        for y in range(hi[1], lo[1] - 1, -1):          # 위층부터
            rows = []
            for z in range(lo[2], hi[2] + 1):          # 북 -> 남
                rows.append("".join(preview_char(self.get(x, y, z))
                                    for x in range(lo[0], hi[0] + 1)))
            if all(set(r) == {"."} for r in rows):
                continue
            out.append(f"── Y={y:+d} " + "─" * 30)
            out.append("     " + "".join(str(abs(x) % 10) for x in range(lo[0], hi[0] + 1)))
            for i, row in enumerate(rows):
                out.append(f" z{lo[2] + i:+d} {row}")
            out.append("")
        return "\n".join(out)

    def legend(self) -> str:
        """같은 기호라도 블록 상태(facing 등)가 다르면 전부 나열한다.

        호퍼/피스톤은 방향이 틀리면 작동하지 않으므로 범례에서 숨기면 안 된다.
        """
        seen: dict[str, set[str]] = {}
        for b in self.blocks.values():
            seen.setdefault(preview_char(b), set()).add(str(b))
        lines = []
        for ch, names in sorted(seen.items()):
            for i, name in enumerate(sorted(names)):
                lines.append(f" {ch if i == 0 else ' '}  {name}")
        return "\n".join(lines)

    # -- 출력 --------------------------------------------------------------
    def to_litematic(self, path: str, data_version: int = MC_DATA_VERSION_26_2) -> str:
        """Litematica .litematic 파일로 저장하고 경로를 돌려준다."""
        from litemapy import BlockState, Region, Schematic as LMSchematic

        lo, _ = self.bounds
        w, h, l = self.size
        region = Region(0, 0, 0, w, h, l)
        cache: dict[Block, BlockState] = {}
        for (x, y, z), block in self.blocks.items():
            state = cache.get(block)
            if state is None:
                state = cache[block] = BlockState(block.id, **block.properties)
            region[x - lo[0], y - lo[1], z - lo[2]] = state

        schem = LMSchematic(
            name=self.name, author=self.author, description=self.description,
            regions={self.name: region}, mc_version=data_version,
        )
        schem.save(path)
        return path


def verify_litematic(path: str, expected: Schematic) -> tuple[bool, list[str]]:
    """저장한 파일을 다시 읽어 블록 단위로 대조한다."""
    from litemapy import Schematic as LMSchematic

    problems: list[str] = []
    loaded = LMSchematic.load(path)
    regions = list(loaded.regions.values())
    if len(regions) != 1:
        return False, [f"리전 수가 1이 아님: {len(regions)}"]
    region = regions[0]
    lo, _ = expected.bounds
    w, h, l = expected.size
    if (region.width, region.height, region.length) != (w, h, l):
        problems.append(f"크기 불일치: 파일 {(region.width, region.height, region.length)} != 설계 {(w, h, l)}")
    checked = 0
    for x in range(w):
        for y in range(h):
            for z in range(l):
                want = expected.get(x + lo[0], y + lo[1], z + lo[2])
                got = region[x, y, z]
                got_id, got_props = got.id, dict(got.properties())
                if want.id != got_id or want.properties != got_props:
                    problems.append(
                        f"({x},{y},{z}) 설계={want} / 파일={got_id}{got_props or ''}")
                    if len(problems) > 12:
                        return False, problems + ["... (이하 생략)"]
                checked += 1
    return not problems, problems or [f"블록 {checked:,}칸 전부 일치"]
