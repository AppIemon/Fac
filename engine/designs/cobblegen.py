"""조약돌 생성기 뱅크.

유체 혼합 규칙 (위키 확인):
  · 흐르는 용암이 물(수원/흐름)에 아래쪽 외 방향으로 닿으면  -> 용암이 조약돌이 된다
  · 용암이 위에서 물로 흘러들면                              -> 물이 돌이 된다
  · 물이 용암 '수원'의 위/옆에 닿으면                        -> 용암이 흑요석이 된다  ← 사고

그래서 흐르는 물을 아예 만들지 않는다. 물먹임 계단을 쓰면 물을 머금되
흐르지 않으므로 용암 수원이 흑요석이 될 일이 없고, 위키가 명시하듯
"흐르는 용암이 물먹임 블록에 닿으면 조약돌은 그대로 생성된다".

단면도 (X축, 생성칸은 Z축으로 반복):

        x=-1      x=0            x=1           x=2        x=3
 Y=+1   돌        돌             돌            돌         돌      ← 용암 뚜껑
 Y= 0   돌        물먹임 계단     생성칸        용암 수원   돌
 Y=-1   돌        돌             호퍼(남→)     돌         돌
"""
from __future__ import annotations

from ..blocks import (EAST, GLASS, LAVA, SOUTH, STONE, chest, hopper,
                      waterlogged_leaves, waterlogged_stairs)
from ..schematic import Schematic
from . import Design


def build(cells: int = 6, structure=STONE, water_block: str = "leaves") -> Design:
    """water_block: 'leaves'(참고 설계 방식, 싸다) 또는 'stairs'(위키 튜토리얼 방식)."""
    if cells < 1:
        raise ValueError("cells 는 1 이상이어야 한다")
    if water_block not in ("leaves", "stairs"):
        raise ValueError("water_block 은 leaves 또는 stairs")
    holder = waterlogged_leaves() if water_block == "leaves" else waterlogged_stairs(EAST)

    s = Schematic(
        name=f"cobblegen_{cells}",
        description=f"조약돌 생성기 {cells}칸 · 물먹임 계단으로 흑요석 사고 차단 · 호퍼 수거",
    )

    for z in range(cells):
        s.fill(-1, -1, z, -1, 1, z, structure)      # 서쪽 벽
        s.fill(0, -1, z, 0, -1, z, structure)
        s.set(0, 0, z, holder)                      # 물먹임: 흐르지 않는 물
        s.set(0, 1, z, structure)

        s.set(1, -1, z, hopper(SOUTH))              # 생성칸 바로 아래 수거 호퍼
        # (1, 0, z) 는 비워 둔다 — 여기에 조약돌이 생성된다
        s.set(1, 1, z, structure)                   # 뚜껑 (용암이 위로 새지 않게)

        s.set(2, -1, z, structure)
        s.set(2, 0, z, LAVA)                        # 용암 수원
        s.set(2, 1, z, structure)
        s.fill(3, -1, z, 3, 1, z, structure)        # 동쪽 벽

    # 남북 끝막이 + 수거 상자
    for z in (-1, cells):
        s.fill(-1, -1, z, 3, 1, z, structure)
    s.set(1, -1, cells, chest(SOUTH))
    s.set(1, 0, cells, GLASS)   # 상자 위가 불투명하면 열리지 않는다

    s.note("물먹임 블록은 물을 흘려보내지 않는다 → 용암 수원이 흑요석이 되지 않는다.")
    s.note("참고 설계 '2.7만 조약돌 생성기'가 계단 대신 물먹임 나뭇잎을 쓴다. "
           "효과는 같고 재료가 훨씬 싸다.")
    s.note("조약돌은 (x=1, Y=0) 에 생성된다. 여기만 비워 두면 된다.")
    s.note("바닐라에는 자동 블록 파괴기가 없다. 조약돌은 플레이어가 캐야 하고, "
           "그 아래 호퍼부터가 자동이다.")

    return Design(
        schematic=s,
        principle="흐르는 용암이 물먹임 블록에 닿아 조약돌로 굳는다 → 캐면 즉시 재생성 "
                  "→ 바로 아래 호퍼가 수거 → 상자",
        circuit=[
            "용암 수원(x=2) → 서쪽으로 흐름 → 생성칸(x=1) 진입",
            "생성칸에서 물먹임 계단(x=0)과 접촉 → 흐르는 용암이 조약돌이 된다",
            "조약돌을 캐면 생성칸이 비고 → 용암이 다시 흘러들어 재생성",
            "※ 흐르는 물이 없으므로 용암 수원은 절대 흑요석이 되지 않는다",
        ],
        steps=[
            f"1) 남북(Z) 방향으로 {cells}칸짜리 생성기 뱅크다. 아래층부터 쌓는다.",
            "2) Y=-1 에 호퍼 줄을 깔고 남쪽 끝 상자로 연결한다.",
            f"3) x=0 에 물을 붓고 그 자리에 "
            + ("나뭇잎" if water_block == "leaves" else "계단")
            + "을 놓아 물먹임 상태로 만든다. 물이 흐르지 않게 되는 게 핵심이다.",
            "4) x=2 에 용암을 붓는다. 이 순서를 지켜야 물이 흐르는 순간이 없다.",
            "5) x=1 (Y=0) 은 반드시 비워 둔다. 여기에 조약돌이 생긴다.",
            "6) 플레이어는 서쪽(x=-1 너머)이나 위에서 생성칸을 캔다.",
        ],
        rate=f"{cells}칸 · 캐는 속도에 비례 (효율 V 곡괭이 기준 1칸당 약 0.25초). "
             f"손이 병목이지 생성이 병목이 아니다.",
        warnings=[
            "물을 먼저 붓고 반드시 계단으로 막은 뒤에 용암을 부어야 한다. "
            "흐르는 물이 용암 수원에 닿는 순간 흑요석이 되어 양동이를 날린다.",
            "바닐라에 자동 블록 파괴기가 없어 채굴은 수동이다. "
            "수거·제련·이후 공정은 전부 자동이다.",
            "캔 직후 용암이 다시 흘러들기 전에 호퍼가 아이템을 주워야 한다. "
            "호퍼는 8틱, 오버월드 용암 확산은 30틱이라 보통 호퍼가 이긴다.",
            "생성칸 위(Y=+1)를 막지 않으면 용암이 새어 올라온다.",
        ],
        manual_items=[
            f"용암 양동이 {cells}개 (생성칸마다 수원 1개)",
            "물 양동이 1개",
        ],
    )
