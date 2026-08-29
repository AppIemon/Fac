"""자동 화로 (대량 제련로).

화로의 3면 투입 규칙:
  위에서 넣으면   -> 원료 슬롯
  옆에서 넣으면   -> 연료 슬롯
  아래에서 빼면   -> 산출 슬롯
호퍼는 '바로 위 컨테이너'에서 끌어온다. 이 성질로 라인을 분배한다.

단면도 (X축으로 화로가 늘어선다):

           z=0 (화로 열)              z=1 (연료 열)
 Y=+4   [입력 상자] (x=0 에만)
 Y=+3   원료 라인 호퍼(동→)          [연료 상자] (x=0 에만)
 Y=+2   분배 호퍼(아래↓)             연료 라인 호퍼(동→)
 Y=+1   화로                         연료 투입 호퍼(북↑ 화로로)
 Y= 0   산출 호퍼(동→)  ──────────>  [산출 상자] (x=N)
"""
from __future__ import annotations

from .. import mechanics as M
from ..blocks import DOWN, EAST, NORTH, STONE, chest, furnace, hopper
from ..schematic import Schematic
from . import Design


def build(furnaces: int = 8, structure=STONE) -> Design:
    if furnaces < 1:
        raise ValueError("furnaces 는 1 이상이어야 한다")
    n = furnaces
    s = Schematic(
        name=f"smelter_{n}",
        description=f"자동 화로 {n}대 · 원료/연료/산출 3라인 · 시간당 {n * M.FURNACE_ITEMS_PER_HOUR:,.0f}개",
    )

    for x in range(n):
        s.set(x, 3, 0, hopper(EAST))     # 원료 라인 (동쪽으로 흘려보냄)
        s.set(x, 2, 0, hopper(DOWN))     # 위 라인에서 끌어와 화로로
        s.set(x, 1, 0, furnace(NORTH))
        s.set(x, 0, 0, hopper(EAST))     # 화로 아래에서 산출을 끌어와 동쪽으로

        s.set(x, 2, 1, hopper(EAST))     # 연료 라인
        s.set(x, 1, 1, hopper(NORTH))    # 옆에서 화로 연료 슬롯으로

        s.set(x, 0, 1, structure)
        s.set(x, -1, 0, structure)
        s.set(x, -1, 1, structure)

    s.set(n, 3, 0, chest(EAST))          # 원료 라인 끝 (넘침 확인용)
    s.set(n, 2, 1, chest(EAST))          # 연료 라인 끝
    s.set(0, 4, 0, chest(NORTH))         # 원료 투입구
    s.set(0, 3, 1, chest(NORTH))         # 연료 투입구
    s.set(n, 0, 0, chest(EAST))          # 산출 상자
    s.set(n, -1, 0, structure)

    s.note("호퍼는 바로 위 컨테이너에서 아이템을 끌어온다. "
           "분배 호퍼(Y=+2)가 원료 라인(Y=+3)에서 끌어오는 구조다.")
    s.note("옆에서 들어간 아이템은 화로의 연료 슬롯으로 간다. 위는 원료, 아래는 산출.")

    per_hour = n * M.FURNACE_ITEMS_PER_HOUR
    coal = M.fuel_items_needed(int(per_hour), "coal")
    return Design(
        schematic=s,
        principle=f"화로 {n}대 병렬. 원료는 위, 연료는 옆, 산출은 아래로 빠진다. "
                  "호퍼가 위 컨테이너에서 끌어오는 성질로 한 줄에서 전 화로에 분배한다.",
        circuit=[
            "원료 상자(Y=+4) → 원료 라인 호퍼(Y=+3, 동쪽) 가 끌어옴",
            "분배 호퍼(Y=+2, 아래) 가 바로 위 라인 호퍼에서 끌어와 화로 위로 투입 → 원료 슬롯",
            "연료 상자(Y=+3, z=1) → 연료 라인(Y=+2, z=1) → 투입 호퍼(Y=+1, 북) → 연료 슬롯",
            "화로 아래 산출 호퍼(Y=0, 동) 가 완성품을 끌어내 동쪽 상자로",
        ],
        steps=[
            f"1) 동서(X) 방향으로 화로 {n}대를 한 줄로 놓는다.",
            "2) 화로 아래에 동쪽을 향한 산출 호퍼 줄을 깔고 끝에 상자를 놓는다.",
            "3) 화로 위에 아래를 향한 분배 호퍼, 그 위에 동쪽을 향한 원료 라인을 올린다.",
            "4) 원료 라인 맨 앞(x=0) 위에 입력 상자를 놓는다.",
            "5) 화로 남쪽 옆칸에 북쪽을 향한 연료 호퍼, 그 위에 동쪽 연료 라인, "
            "맨 앞에 연료 상자를 놓는다.",
            "6) 연료는 용암 양동이(20,000틱)나 말린 켈프 블록(4,000틱)이 효율이 좋다.",
        ],
        rate=f"화로 {n}대 → 시간당 {per_hour:,.0f}개 (연속 가동 기준). "
             f"석탄으로 돌리면 시간당 약 {coal:,.0f}개 필요.",
        warnings=[
            f"호퍼 1줄은 초당 {M.HOPPER_ITEMS_PER_SEC}개(시간당 9,000개)까지만 나른다. "
            f"화로 {int(M.HOPPER_ITEMS_PER_SEC * 3600 / M.FURNACE_ITEMS_PER_HOUR)}대를 넘기면 "
            "원료 라인을 나눠야 한다.",
            "라인 끝 상자에 아이템이 쌓이는 건 정상이다. 라인이 가득 차야 각 분배 "
            "호퍼가 끌어갈 재고가 생긴다. 상자가 계속 넘치면 화로가 부족하다는 뜻이다.",
            "다만 분배가 완전히 균등하지는 않아 앞쪽 화로가 더 바쁘다. "
            "완전 균등이 필요하면 라인 끝을 처음으로 되돌리는 순환 구조로 만들 것.",
        ],
        manual_items=[],
    )
