"""켈프 팜 (연료 자급 라인의 앞단).

원리 (위키 확인):
  · 켈프는 랜덤틱마다 14% 확률로 한 칸 자란다 → 평균 9,752틱(약 488초)에 1칸.
  · 물속에서만 자라고, 위쪽이 물이어야 한다.
  · 말린 켈프 블록은 4,000틱 = 20개 제련. 다만 블록 하나를 만들려면 켈프 9개를
    구워야 해서 9개분을 되먹는다 → 순 11개분. (위키가 명시)

수거는 '물속에서 아이템이 떠오른다'는 성질을 쓴다. 잘린 켈프가 물기둥을 타고
올라와 천장 아래 물먹임 호퍼에 들어간다. 사탕수수처럼 바닥에서 받을 필요가 없다.

단면도 (Z축, 기둥은 X축으로 반복):

        z=0       z=1(물기둥)   z=2          z=3
 Y=+5   돌        돌            돌           돌        ← 천장
 Y=+4   돌        물먹임 호퍼   돌           돌        ← 떠오른 켈프 수거
 Y=+3   돌        물 (성장칸)   관측기(북)   레드스톤 가루
 Y=+2   돌        물 (성장칸)   피스톤(북)   돌  ← 가루의 받침
 Y=+1   돌        켈프 (밑동)   돌           돌
 Y= 0   돌        모래          돌           돌
"""
from __future__ import annotations

from .. import mechanics as M
from ..blocks import (EAST, GLASS, KELP, NORTH, SAND, STONE, WATER,
                      chest, observer, piston, redstone_wire, collect_hopper)
from ..schematic import Schematic
from . import Design

KELP_GROWTH_TICKS = 9752.0      # 위키: 14%/랜덤틱 → 평균 9,752틱


def build(columns: int = 12, structure=STONE) -> Design:
    if columns < 2:
        raise ValueError("columns 는 2 이상이어야 한다")

    s = Schematic(
        name=f"kelpfarm_{columns}",
        description=f"켈프 팜 {columns}기둥 · 관측기+피스톤 절단 · 부력 수거",
    )

    for x in range(columns):
        s.fill(x, -1, 0, x, 5, 0, structure)         # 북쪽 벽

        s.set(x, -1, 1, structure)                    # 모래 받침 (모래는 중력 블록이다)
        s.set(x, 0, 1, SAND)                          # 켈프 식재면
        s.set(x, 1, 1, KELP)                          # 밑동 (영구)
        s.set(x, 2, 1, WATER)                         # 성장칸 (여기서 잘린다)
        s.set(x, 3, 1, WATER)                         # 성장칸 (여기서 감지)
        s.set(x, 4, 1, collect_hopper(EAST))      # 떠오른 아이템 수거
        s.set(x, 5, 1, structure)                     # 천장

        s.set(x, -1, 2, structure)
        s.set(x, 0, 2, structure)
        s.set(x, 1, 2, structure)
        s.set(x, 2, 2, piston(NORTH))                 # 성장칸 2번째를 부순다
        s.set(x, 3, 2, observer(NORTH))               # 3번째 성장 감지
        s.fill(x, 4, 2, x, 5, 2, structure)

        s.fill(x, -1, 3, x, 1, 3, structure)
        s.set(x, 2, 3, structure)                     # 가루의 받침 = 피스톤 급전원
        s.set(x, 3, 3, redstone_wire(
            north="side",
            east="side" if x < columns - 1 else "none",
            west="side" if x > 0 else "none"))
        s.fill(x, 4, 3, x, 5, 3, structure)

    # 서쪽 끝막이
    s.fill(-1, -1, 0, -1, 5, 3, structure)
    # 동쪽 끝: 호퍼 줄이 흘러드는 상자
    s.fill(columns, -1, 0, columns, 5, 3, structure)
    s.set(columns, 4, 1, chest(EAST))
    s.set(columns, 5, 1, GLASS)                       # 상자 위는 불투명 금지

    s.note("물속에서 아이템은 떠오른다. 잘린 켈프가 물기둥을 타고 올라와 "
           "천장 아래 물먹임 호퍼로 들어간다.")
    s.note("호퍼는 자기 칸 안의 아이템도 줍는다. 물먹임이라 물기둥을 막지 않는다.")
    s.note("회로는 사탕수수 팜과 같다: 관측기 출력 → 가루 → 받침 블록 → 인접 피스톤.")

    per_plant = 3600.0 / (KELP_GROWTH_TICKS / M.TPS)
    total = per_plant * columns
    return Design(
        schematic=s,
        principle="물기둥에서 켈프 성장 → 관측기가 3번째 칸 감지 → 피스톤이 2번째 칸 절단 "
                  "→ 잘린 켈프가 부력으로 떠올라 천장 호퍼로 수거",
        circuit=[
            "1. 관측기(z=2, Y=3, 북향) ← 켈프가 3번째 칸(z=1, Y=3)까지 자란 것을 감지",
            "2. 관측기 출력면(남쪽) → 레드스톤 가루(z=3, Y=3)",
            "3. 가루 → 받침 블록(z=3, Y=2) 약한 급전",
            "4. 급전된 블록 → 인접 피스톤(z=2, Y=2) 작동 → 2번째 칸 절단",
            "5. 잘린 켈프가 물기둥을 타고 떠올라 Y=4 물먹임 호퍼로",
        ],
        steps=[
            f"1) 동서(X) 방향 {columns}기둥. 바닥(Y=0)에 모래를 깐다.",
            "2) 모래 위에 켈프를 한 칸만 심는다. 위로는 물로 채운다.",
            "3) z=2 에 피스톤(북향, Y=2)과 관측기(북향, Y=3)를 놓는다.",
            "4) z=3 Y=2 에 받침 블록, 그 위 Y=3 에 레드스톤 가루를 한 줄 잇는다.",
            "5) Y=4 에 물먹임 호퍼 줄을 깔고 동쪽 끝 상자로 연결한다. "
            "호퍼를 물속에 놓으면 자동으로 물먹임이 된다.",
            "6) Y=5 천장을 덮어 물이 새지 않게 한다.",
        ],
        rate=f"{columns}기둥 → 시간당 약 {total:,.0f}개 "
             f"(포기당 {per_plant:.2f}개/시간, 성장 평균 488초)",
        warnings=[
            "켈프는 물이 없으면 즉시 부서진다. 물기둥이 끊기지 않게 천장까지 덮을 것.",
            "말린 켈프 블록은 만들 때 켈프 9개를 굽느라 9개분을 되먹는다. "
            "순 연료는 11개분이지 20개분이 아니다.",
            f"청크 로딩 대책 필요: 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다.",
            "성장이 느리다(포기당 시간당 1.3개). 연료를 자급하려면 기둥 수가 세 자리로 간다.",
        ],
        manual_items=["물 양동이 (물기둥 채우기)", "켈프 (초기 식재)"],
    )
