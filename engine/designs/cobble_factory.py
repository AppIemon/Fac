"""매끄러운 돌 공장 (조약돌 팜 + 2단 제련 + 켈프 연료 자급).

전체 흐름
  조약돌 생성기 → 1단 화로(조약돌→돌) → 2단 화로(돌→매끄러운 돌) → 상자
  켈프 팜 → 건조 화로(켈프→말린 켈프) → 제작기(9개→블록) → 연료 라인

연료 고리
  말린 켈프 블록은 4,000틱 = 20개 제련. 블록 하나를 만들려면 켈프 9개를 구워야
  하므로 9개분을 되먹어 순 11개분이다. 2단 제련은 매끄러운 돌 1개당 2개분을
  먹으므로, 켈프 소요가 산출의 약 1.6배가 된다 — 켈프 팜이 공장 부피의 대부분을
  차지하는 이유다.

제작기를 클럭으로 계속 두드려도 되는 이유
  제작기는 슬롯 조합이 유효한 레시피일 때만 제작한다. 말린 켈프가 9칸에 다 차기
  전에는 어떤 레시피에도 맞지 않으므로 헛제작이 없다. 비교기 신호 필터가 필요 없다.

층 구성 (본체, z=-1..2)
  Y=14  물먹임 잎(z=-1) │ 조약돌 생성칸(z=0) │ 용암 수원(z=1)
  Y=13  생성기 수거 호퍼(서←)
  Y=12  차단층 — 호퍼가 가루에 잠기지 않게 떼어 놓는다
  Y=11  가루 + 동쪽 끝 관측기 클럭        Y=10  받침
  Y= 9  조약돌 드로퍼 사슬(동→)          연료 드로퍼 사슬(동→)
  Y= 8  호퍼(아래)                       호퍼(아래)
  Y= 7  1단 화로                         연료 호퍼(북)
  Y= 6  1단 산출 호퍼(서←)
  Y= 5  차단층
  Y= 4  가루 + 클럭                      Y= 3  받침
  Y= 2  돌 드로퍼 사슬(동→)              연료 드로퍼 사슬(서←)
  Y= 1  호퍼(아래)                       호퍼(아래)
  Y= 0  2단 화로                         연료 호퍼(북)
  Y=-1  산출 호퍼(동→) → 매끄러운 돌 상자
"""
from __future__ import annotations

import math

from .. import mechanics as M
from ..blocks import (B, DOWN, EAST, GLASS, KELP, LAVA, NORTH, SAND, SOUTH,
                      STONE, WATER, WEST, chest, dropper, furnace, hopper,
                      observer, piston, redstone_wire, waterlogged_leaves)
from ..schematic import Schematic
from . import Design

KELP_GROWTH_TICKS = 9752.0
KELP_PER_PLANT_HOUR = 3600.0 / (KELP_GROWTH_TICKS / M.TPS)
DRIED_KELP_BLOCK_SMELTS = 20      # 4,000틱 / 200틱
KELP_PER_BLOCK = 9


def sizing(furnaces: int) -> dict:
    """화로 수에서 켈프 팜 규모를 역산한다 (전부 위키 확인 수치에서 파생)."""
    out_per_hour = furnaces * M.FURNACE_ITEMS_PER_HOUR
    smelts = 2 * out_per_hour                       # 2단 제련
    net_per_block = DRIED_KELP_BLOCK_SMELTS - KELP_PER_BLOCK   # 순 11개분
    blocks = smelts / net_per_block
    kelp = blocks * KELP_PER_BLOCK
    return {
        "smooth_stone_per_hour": out_per_hour,
        "smelts_per_hour": smelts,
        "blocks_per_hour": blocks,
        "kelp_per_hour": kelp,
        "kelp_columns": math.ceil(kelp / KELP_PER_PLANT_HOUR),
        "drying_furnaces": math.ceil(kelp / M.FURNACE_ITEMS_PER_HOUR),
    }


def crafter(orientation: str = "north_up") -> object:
    return B("crafter", crafting="false", orientation=orientation, triggered="false")


def _smelt_bank(s, x0, n, y_furnace, z0, feed_dir, fuel_dir, structure):
    """화로 한 뱅크: 드로퍼 사슬 + 분배 호퍼 + 화로 + 연료 열 + 가루/클럭.

    y_furnace 를 기준으로 위로 호퍼(+1) 드로퍼(+2) 받침(+3) 가루(+4) 가 올라간다.
    """
    yf, yh, yd, ys, yr = y_furnace, y_furnace + 1, y_furnace + 2, y_furnace + 3, y_furnace + 4
    za, zb = z0, z0 + 1
    for i in range(n):
        x = x0 + i
        s.set(x, yd, za, dropper(feed_dir))
        s.set(x, yh, za, hopper(DOWN))
        s.set(x, yf, za, furnace(NORTH))
        s.set(x, ys, za, structure)
        s.set(x, yr, za, redstone_wire(
            south="side", east="side", west="side" if i > 0 else "none"))

        s.set(x, yd, zb, dropper(fuel_dir))
        s.set(x, yh, zb, hopper(DOWN))
        s.set(x, yf, zb, hopper(NORTH))
        s.set(x, ys, zb, structure)
        s.set(x, yr, zb, redstone_wire(
            north="side", east="side", west="side" if i > 0 else "none"))

    # 자가 발진 클럭 (동쪽 끝)
    s.set(x0 + n, yr, za, observer(EAST))
    s.set(x0 + n + 1, yr, za, observer(WEST))
    # 드로퍼 사슬 끝은 반드시 컨테이너 (공기면 아이템을 월드로 뱉는다)
    if feed_dir == EAST:
        s.set(x0 + n, yd, za, chest(EAST))
    if fuel_dir == EAST:
        s.set(x0 + n, yd, zb, chest(EAST))


def build(furnaces: int = 2, kelp_rows: int = 4, structure=STONE) -> Design:
    if furnaces < 1:
        raise ValueError("furnaces 는 1 이상이어야 한다")
    if kelp_rows < 1:
        raise ValueError("kelp_rows 는 1 이상이어야 한다")
    n = furnaces
    size = sizing(n)
    kelp_cols = math.ceil(size["kelp_columns"] / kelp_rows)
    dry = size["drying_furnaces"]

    s = Schematic(
        name=f"cobble_factory_f{n}",
        description=f"매끄러운 돌 공장 · 조약돌 팜 + 2단 제련 + 켈프 연료 자급 "
                    f"(시간당 {size['smooth_stone_per_hour']:,.0f}개)",
    )

    # ================= 본체: 2단 제련 =================
    _smelt_bank(s, 0, n, 7, 0, EAST, EAST, structure)   # 1단 (조약돌 → 돌)
    _smelt_bank(s, 0, n, 0, 0, EAST, WEST, structure)   # 2단 (돌 → 매끄러운 돌)

    for x in range(n):
        s.set(x, 6, 0, hopper(WEST))                   # 1단 산출을 서쪽으로
        s.set(x, 6, 1, structure)
        s.set(x, -1, 0, hopper(EAST))                  # 2단 산출을 동쪽 상자로
        s.set(x, -1, 1, structure)
        s.set(x, -2, 0, structure)
        s.set(x, -2, 1, structure)
        s.set(x, 5, 0, structure)                      # 차단층
        s.set(x, 5, 1, structure)
        s.set(x, 12, 0, structure)
        s.set(x, 12, 1, structure)
    s.set(n, -1, 0, chest(EAST))                       # 매끄러운 돌 산출
    s.set(n, -2, 0, structure)
    s.set(n, -1, 1, structure)

    s.set(-1, 2, 1, chest(WEST))                       # 하단 연료 사슬은 서쪽으로 흐른다

    # ================= 조약돌 생성기 =================
    for x in range(n):
        s.set(x, 14, -1, waterlogged_leaves())         # 흐르지 않는 물
        # (x, 14, 0) 은 비워 둔다 — 여기에 조약돌이 생긴다
        s.set(x, 14, 1, LAVA)
        s.set(x, 13, 0, hopper(WEST))                  # 캔 조약돌을 서쪽으로
        s.set(x, 13, -1, structure)
        s.set(x, 13, 1, structure)
        s.set(x, 15, -1, structure)
        s.set(x, 15, 0, structure)
        s.set(x, 15, 1, structure)
    s.fill(n, 13, -1, n, 15, 1, structure)
    s.fill(-1, 14, -1, -1, 15, -1, structure)
    s.set(-1, 14, 1, structure)
    s.set(-1, 15, 1, structure)
    s.set(-1, 15, 0, structure)

    # ================= 하강 통로 (가루에서 2칸 이상 떨어뜨린다) =================
    # 조약돌: Y=13 → Y=9 (x=-2)
    s.set(-1, 13, 0, hopper(WEST))
    for y in (12, 11, 10):
        s.set(-2, y, 0, hopper(DOWN))
    s.set(-2, 13, 0, hopper(DOWN))
    s.set(-2, 9, 0, hopper(EAST))
    s.set(-1, 9, 0, hopper(EAST))
    s.set(-1, 10, 0, structure)
    s.set(-1, 11, 0, structure)
    s.set(-1, 12, 0, structure)

    # 돌: Y=6 → Y=2 (x=-3)
    s.set(-1, 6, 0, hopper(WEST))
    s.set(-2, 6, 0, hopper(WEST))
    for y in (5, 4, 3):
        s.set(-3, y, 0, hopper(DOWN))
    s.set(-3, 6, 0, hopper(DOWN))
    s.set(-3, 2, 0, hopper(EAST))
    s.set(-2, 2, 0, hopper(EAST))
    s.set(-1, 2, 0, hopper(EAST))
    for y in (3, 4, 5):
        s.set(-2, y, 0, structure)
        s.set(-1, y, 0, structure)

    # ================= 연료 배관 =================
    # 상단 연료 사슬(동→) 끝 상자에서 흘러넘친 연료가 하단 사슬(서←)로 내려간다
    s.set(n, 8, 1, hopper(EAST))
    s.set(n + 1, 8, 1, hopper(DOWN))
    for y in (7, 6, 5, 4, 3):
        s.set(n + 1, y, 1, hopper(DOWN))
    s.set(n + 1, 2, 1, hopper(WEST))
    s.set(n, 2, 1, hopper(WEST))
    for y in (3, 4, 5, 6, 7, 8):
        s.set(n, y, 1, structure) if (n, y, 1) not in s.blocks else None
    s.set(-1, 9, 1, hopper(EAST))                      # 상단 연료 투입구
    s.fill(-1, 5, 1, -1, 8, 1, structure)
    s.fill(-1, 10, 1, -1, 12, 1, structure)
    s.fill(-1, -1, 1, -1, 1, 1, structure)

    # ================= 켈프 팜 (본체 위쪽에 얹는다) =================
    # 중력만으로 건조 구역까지 내려보내기 위해 켈프 팜을 위에 둔다.
    KY, KZ = 18, 8                                     # 켈프 구역 높이/깊이 오프셋
    for r in range(kelp_rows):
        z0 = KZ + 4 * r
        for x in range(kelp_cols):
            s.fill(x, KY - 3, z0, x, KY + 3, z0, structure)
            s.set(x, KY - 3, z0 + 1, structure)    # 모래 받침 (중력 블록)
            s.set(x, KY - 2, z0 + 1, SAND)
            s.set(x, KY - 1, z0 + 1, KELP)
            s.set(x, KY + 0, z0 + 1, WATER)
            s.set(x, KY + 1, z0 + 1, WATER)
            s.set(x, KY + 2, z0 + 1, hopper(EAST))     # 떠오른 켈프를 받는다
            s.set(x, KY + 3, z0 + 1, structure)
            s.fill(x, KY - 3, z0 + 2, x, KY - 1, z0 + 2, structure)
            s.set(x, KY + 0, z0 + 2, piston(NORTH))
            s.set(x, KY + 1, z0 + 2, observer(NORTH))
            s.fill(x, KY + 2, z0 + 2, x, KY + 3, z0 + 2, structure)
            s.fill(x, KY - 3, z0 + 3, x, KY - 1, z0 + 3, structure)
            s.set(x, KY + 0, z0 + 3, structure)
            s.set(x, KY + 1, z0 + 3, redstone_wire(
                north="side", east="side" if x < kelp_cols - 1 else "none",
                west="side" if x > 0 else "none"))
            s.fill(x, KY + 2, z0 + 3, x, KY + 3, z0 + 3, structure)
        s.fill(-1, KY - 3, z0, -1, KY + 3, z0 + 3, structure)
        s.fill(kelp_cols, KY - 3, z0, kelp_cols, KY + 3, z0 + 3, structure)
        s.set(kelp_cols, KY + 2, z0 + 1, hopper(EAST))

    # 합류선: 각 줄의 수거를 북쪽으로 모은다
    merge_x = kelp_cols + 1
    for z in range(4, KZ + 4 * kelp_rows):
        s.set(merge_x, KY + 2, z, hopper(NORTH))
        s.set(merge_x, KY + 1, z, structure)
        s.set(merge_x, KY + 3, z, structure)
    s.set(merge_x, KY + 2, 3, hopper(WEST))            # 합류선을 서쪽 이송선으로 꺾는다
    s.set(merge_x, KY + 1, 3, structure)
    s.set(merge_x, KY + 3, 3, structure)

    # ================= 건조 화로 + 제작기 =================
    DX, DZ = 6, 3
    _smelt_bank(s, DX, dry, 15, DZ, EAST, EAST, structure)
    for i in range(dry):
        s.set(DX + i, 14, DZ, hopper(WEST))            # 말린 켈프 회수
        s.set(DX + i, 14, DZ + 1, structure)
        s.set(DX + i, 13, DZ, structure)
        s.set(DX + i, 13, DZ + 1, structure)

    # 합류선 → 서쪽으로 이송 → 하강 → 건조 드로퍼 사슬
    for x in range(DX - 1, merge_x):
        s.set(x, KY + 2, DZ, hopper(WEST))
    s.set(DX - 2, KY + 2, DZ, hopper(DOWN))            # 여기서 아래로 꺾는다
    for y in (19, 18):
        s.set(DX - 2, y, DZ, hopper(DOWN))
    s.set(DX - 2, 17, DZ, hopper(EAST))
    s.set(DX - 1, 17, DZ, hopper(EAST))
    s.fill(DX - 1, 18, DZ, DX - 1, 19, DZ, structure)

    # 건조 화로 연료 투입구 (사람이 채운다 — 유일한 수동 연결)
    s.set(DX - 1, 18, DZ + 1, chest(NORTH))
    s.set(DX - 1, 17, DZ + 1, hopper(EAST))

    # 제작기: 말린 켈프 9개 → 블록. 앞면(서)이 호퍼를 향한다.
    s.set(DX - 1, 14, DZ, hopper(WEST))
    s.set(DX - 2, 14, DZ, hopper(DOWN))
    s.set(DX - 2, 13, DZ, crafter("west_up"))
    s.set(DX - 3, 13, DZ, hopper(WEST))                # 제작기 산출
    s.set(DX - 2, 12, DZ, structure)
    s.set(DX - 2, 15, DZ, structure) if (DX - 2, 15, DZ) not in s.blocks else None
    s.set(DX - 2, 14, DZ + 1, structure)
    s.set(DX - 2, 13, DZ + 1, structure)
    # 제작기 클럭 (드로퍼 클럭과 별개로 하나 더)
    s.set(DX - 2, 12, DZ + 1, redstone_wire(west="side"))
    s.set(DX - 3, 12, DZ + 1, observer(EAST))
    s.set(DX - 4, 12, DZ + 1, observer(WEST))

    # 제작기 산출 → 본체 연료 투입구(-1, 9, 1) 로 중력 이송
    for x in range(DX - 4, -2, -1):
        s.set(x, 13, DZ, hopper(WEST))
        s.set(x, 12, DZ, structure)
    s.set(-1, 13, DZ, hopper(NORTH))
    s.set(-1, 13, 2, hopper(DOWN))
    for y in (12, 11, 10):
        s.set(-1, y, 2, hopper(DOWN))
    s.set(-1, 9, 2, hopper(NORTH))
    s.fill(-2, 9, 2, -2, 13, 2, structure)

    s.note("생성칸(Y=14, z=0)은 비워 둔다. 물먹임 잎 덕분에 흐르는 물이 없어 "
           "용암 수원이 흑요석이 되지 않는다.")
    s.note("드로퍼 사슬 끝은 전부 상자다. 공기를 향하면 아이템을 월드로 뱉는다.")
    s.note("호퍼는 레드스톤 신호를 받으면 잠긴다. 하강 통로를 가루에서 두 칸 이상 "
           "떼고 차단층(Y=5, Y=12)을 둔 이유다.")
    s.note("제작기는 유효한 레시피일 때만 제작한다. 말린 켈프가 9칸에 다 차기 전에는 "
           "아무 일도 일어나지 않으므로 클럭으로 계속 두드려도 된다.")

    return Design(
        schematic=s,
        principle="조약돌 생성기 → 1단 제련(돌) → 2단 제련(매끄러운 돌). "
                  "연료는 켈프 팜 → 건조 화로 → 제작기(9개→블록)로 자급한다.",
        circuit=[
            "[돌 라인] 용암이 물먹임 잎에 닿아 조약돌 생성 → 캐면 아래 호퍼가 수거",
            "[돌 라인] 서쪽 하강 통로 → 1단 드로퍼 사슬 → 화로 → 돌",
            "[돌 라인] 1단 산출 → 서쪽 하강 → 2단 드로퍼 사슬 → 화로 → 매끄러운 돌",
            "[연료] 켈프 팜: 관측기가 3번째 칸 감지 → 피스톤 절단 → 부력으로 떠올라 호퍼",
            "[연료] 합류선 → 건조 화로 → 말린 켈프 → 제작기 9개 → 블록",
            "[연료] 블록이 본체 연료 투입구로 → 상단 사슬 → 넘친 분량이 하단 사슬로",
            "[클럭] 관측기 2개를 마주보게 둔 자가 발진 클럭이 드로퍼와 제작기를 두드린다",
        ],
        steps=[
            "1) 바닥(Y=-2)부터 쌓는다. 본체는 z=-1..2, 켈프 구역은 z=8 이후다.",
            f"2) 2단 화로 {n}대(Y=0) → 산출 호퍼(Y=-1, 동) → 동쪽 상자.",
            "3) 그 위로 호퍼(Y=1) · 드로퍼 사슬(Y=2) · 받침(Y=3) · 가루(Y=4) 순으로.",
            f"4) 같은 패턴으로 1단 화로 {n}대를 Y=7 에 올린다. 사이에 차단층(Y=5)을 넣는다.",
            "5) Y=14 에 조약돌 생성칸을 만든다. z=-1 에 물을 붓고 그 자리에 나뭇잎을 "
            "놓아 물먹임으로 만든 뒤, z=1 에 용암을 붓는다. 순서를 지킬 것.",
            "6) 서쪽 하강 통로 두 줄(x=-2 조약돌, x=-3 돌)을 잇는다.",
            f"7) 켈프 팜 {kelp_rows}줄 x {kelp_cols}기둥을 z=8 부터 4칸 간격으로 놓는다.",
            f"8) 건조 화로 {dry}대와 제작기를 z=3~4 에 놓고 합류선으로 잇는다.",
            "9) 제작기 앞(북) 호퍼가 연료를 본체 연료 투입구로 나른다.",
            "10) 켈프를 심고 물을 채운 뒤, 연료 상자에 말린 켈프 블록을 몇 개 넣어 "
            "고리를 점화한다. 이후로는 자급된다.",
        ],
        rate=f"매끄러운 돌 시간당 {size['smooth_stone_per_hour']:,.0f}개 "
             f"(화로 {n}대 x 2단) · 켈프 {size['kelp_per_hour']:,.0f}개/시간 소비 "
             f"→ 말린 켈프 블록 {size['blocks_per_hour']:.0f}개/시간",
        warnings=[
            f"켈프 팜이 공장 부피의 대부분이다. 화로 {n}대/단에 켈프 기둥 "
            f"{size['kelp_columns']}개가 필요하다. 2단 제련이라 산출 1개당 연료 2개분을 "
            f"먹고, 말린 켈프 블록의 순 연료가 11개분뿐이기 때문이다.",
            "제자리 돌 생성기(stonegen)를 쓰면 제련이 1단으로 줄어 켈프가 절반이 된다. "
            "조약돌 팜을 고른 대가다.",
            "물먹임 잎을 먼저 놓고 용암을 나중에 부어야 한다. 흐르는 물이 용암 수원에 "
            "닿으면 흑요석이 되어 양동이를 날린다.",
            "바닐라에 자동 블록 파괴기가 없어 조약돌 채굴은 수동이다. "
            "수거부터 산출 상자까지는 전부 자동이다.",
            "고리를 처음 돌리려면 말린 켈프 블록 몇 개를 연료 상자에 넣어 점화해야 한다.",
            f"청크 로딩 대책 필요: 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다. "
            "공장 전체가 한 플레이어의 AFK 범위 안이거나 /forceload 되어야 한다.",
        ],
        manual_items=[
            f"용암 양동이 {n}개", "물 양동이 (생성기 1개 + 켈프 물기둥)",
            "켈프 (초기 식재)", "말린 켈프 블록 몇 개 (고리 점화용)",
        ],
    )
