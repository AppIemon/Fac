"""복셀 그리드와 ASCII 설계도 렌더러.

좌표계: x = 동서(→), y = 높이(↑), z = 남북(↓ 화면 아래쪽)
층별로 위에서 내려다본 평면도를 출력한다 (마인크래프트 리터럴 뷰와 동일).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# 코드 -> (한글 블록명, 기본 재료 태그)
PALETTE: dict[str, tuple[str, str]] = {
    ".": ("공기", ""),
    "#": ("건축 블록(아무 불투명 블록)", "building"),
    "g": ("유리", "glass"),
    "s": ("하프 블록", "slab"),
    "w": ("물 수원", "water"),
    "-": ("흐르는 물", "water"),
    "h": ("호퍼", "hopper"),
    "c": ("상자", "chest"),
    "C": ("큰 상자(더블)", "chest"),
    "t": ("다락문", "trapdoor"),
    "f": ("울타리", "fence"),
    "l": ("용암", "lava"),
    "m": ("마그마 블록", "magma"),
    "p": ("피스톤", "piston"),
    "P": ("끈끈이 피스톤", "sticky_piston"),
    "o": ("관측기", "observer"),
    "r": ("레드스톤 가루", "redstone"),
    "y": ("중계기", "repeater"),
    "b": ("레드스톤 블록", "redstone_block"),
    "n": ("발사기/공급기", "dispenser"),
    "x": ("스포너", "spawner"),
    "k": ("표지판", "sign"),
    "a": ("카펫", "carpet"),
    "e": ("레일", "rail"),
    "N": ("호퍼 광산 수레", "hopper_minecart"),
    "z": ("횃불/광원", "light"),
    "d": ("흙/경작지", "soil"),
    "v": ("작물/식물", "plant"),
    "i": ("얼음(뭉친/푸른)", "ice"),
    "u": ("깔때기 위 화로", "furnace"),
    "S": ("영혼 모래", "soul_sand"),
    "L": ("잎/나뭇잎", "leaves"),
    "T": ("나무/원목", "log"),
    "B": ("발판(장력줄/압력판)", "plate"),
    "W": ("벽/담장", "wall"),
    "@": ("플레이어 AFK 위치", ""),
    "?": ("설계 미지정(직접 결정)", ""),
}


@dataclass
class Grid:
    """희소 복셀 그리드. 좌표는 정수 (x, y, z)."""
    name: str = "blueprint"
    cells: dict[tuple[int, int, int], str] = field(default_factory=dict)
    annotations: list[str] = field(default_factory=list)

    # -- 배치 --------------------------------------------------------------
    def set(self, x: int, y: int, z: int, code: str) -> None:
        if code == ".":
            self.cells.pop((x, y, z), None)
        else:
            if code not in PALETTE:
                raise KeyError(f"팔레트에 없는 블록 코드: {code!r}")
            self.cells[(x, y, z)] = code

    def fill(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, code: str) -> None:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, code)

    def hollow_box(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int,
                   code: str, floor: bool = True, ceiling: bool = True) -> None:
        """벽(+선택적 바닥/천장)만 채운 상자."""
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    on_wall = x in (x0, x1) or z in (z0, z1)
                    on_floor = y == min(y0, y1)
                    on_ceil = y == max(y0, y1)
                    if on_wall or (floor and on_floor) or (ceiling and on_ceil):
                        self.set(x, y, z, code)

    def note(self, text: str) -> None:
        self.annotations.append(text)

    # -- 조회 --------------------------------------------------------------
    @property
    def bounds(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        if not self.cells:
            return (0, 0, 0), (0, 0, 0)
        xs = [c[0] for c in self.cells]
        ys = [c[1] for c in self.cells]
        zs = [c[2] for c in self.cells]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    @property
    def size(self) -> tuple[int, int, int]:
        lo, hi = self.bounds
        return (hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1)

    def material_list(self) -> list[tuple[str, int]]:
        counts = Counter(self.cells.values())
        rows = [(PALETTE[c][0], n) for c, n in counts.items() if PALETTE[c][1]]
        return sorted(rows, key=lambda r: -r[1])

    # -- 렌더 --------------------------------------------------------------
    def render_layers(self, max_layers: int = 40) -> str:
        if not self.cells:
            return "(빈 설계도)"
        lo, hi = self.bounds
        used = sorted({c[1] for c in self.cells})
        out: list[str] = []
        if len(used) > max_layers:
            step = len(used) // max_layers + 1
            shown = used[::step]
            out.append(f"※ 층이 {len(used)}개라 {step}층 간격으로 발췌해 표시함\n")
        else:
            shown = used
        width = hi[0] - lo[0] + 1
        header = "    " + "".join(str(abs(x) % 10) for x in range(lo[0], hi[0] + 1))
        for y in shown:
            out.append(f"── Y={y:+d} 층 " + "─" * max(0, width - 4))
            out.append(header)
            for z in range(lo[2], hi[2] + 1):
                row = "".join(self.cells.get((x, y, z), ".") for x in range(lo[0], hi[0] + 1))
                out.append(f"{abs(z) % 10:>3} {row}")
            out.append("")
        return "\n".join(out)

    def legend(self) -> str:
        used = sorted({c for c in self.cells.values()})
        lines = ["기호  블록"]
        for code in used:
            lines.append(f" {code}    {PALETTE[code][0]}")
        return "\n".join(lines)
