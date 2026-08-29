"""뼛가루 켈프 팜 — 한 줄로 켈프를 뽑아낸다.

자연 성장 켈프는 포기당 시간당 7.4개뿐이라 연료를 대려면 기둥이 수십~수백 개
필요했다. 위키 확인: "Bone meal can be used to grow kelp by 1 block on each use."
즉 뼛가루 1개 = 켈프 1칸이고 즉시 자란다. 성장 대기가 사라지므로 산출량이
기둥 수가 아니라 '뼛가루 공급량'으로 정해진다 — 한 줄이면 충분하다.

단면도 (Z축, 기둥은 X축으로 반복):

        z=-1        z=0              z=1(물기둥)   z=2          z=3
 Y=+5               돌               돌            돌           돌
 Y=+4               뼛가루 라인(동→) 물먹임 호퍼   돌           돌
 Y=+3   돌          호퍼(아래↓)      물(성장칸)    관측기(북)   레드스톤 가루
 Y=+2   가루        드로퍼(아래↓)    물(성장칸)    피스톤(북)   돌 ← 가루 받침
 Y=+1   돌(받침)    발사기(남향)     켈프(밑동)    돌           돌
 Y= 0   돌          돌               모래          돌           돌
 Y=-1   돌          돌               돌(모래 받침) 돌           돌

두 개의 독립 회로
  · 발사기 회로: 가루(z=-1, Y=2) → 받침(z=-1, Y=1) → 인접 발사기 작동.
    같은 가루가 옆의 드로퍼(z=0, Y=2)도 두드려 뼛가루를 발사기에 밀어 넣는다.
    자가 발진 관측기 클럭으로 계속 돈다.
  · 절단 회로: 관측기(z=2, Y=3)가 3번째 칸 성장을 감지 → 가루(z=3, Y=3) →
    받침(z=3, Y=2) → 피스톤(z=2, Y=2)이 2번째 칸을 부순다. 클럭이 필요 없다.

호퍼가 아니라 드로퍼로 발사기에 급이하는 이유
  호퍼는 레드스톤 신호를 받으면 잠긴다. 발사기 급전용 가루 옆에 호퍼를 두면
  클럭이 돌 때마다 급이가 끊긴다. 드로퍼는 반대로 신호를 받아야 밀어내므로
  같은 가루에 붙여도 된다.
"""
from __future__ import annotations

from ..blocks import (DOWN, EAST, GLASS, KELP, NORTH, SAND, SOUTH, STONE, WATER,
                      WEST,
                      chest, dispenser, dropper, hopper, observer, piston,
                      redstone_wire)
from ..schematic import Schematic
from . import Design

KELP_PER_BONEMEAL = 1.0        # 위키 확인: 뼛가루 1개당 1칸


def build(columns: int = 8, structure=STONE) -> Design:
    if columns < 1:
        raise ValueError("columns 는 1 이상이어야 한다")

    s = Schematic(
        name=f"kelpfarm_bonemeal_{columns}",
        description=f"뼛가루 켈프 팜 {columns}기둥 · 뼛가루 1개 = 켈프 1개 · "
                    f"성장 대기 없음",
    )

    for x in range(columns):
        # z=-1 : 발사기 급전 회로
        s.fill(x, -1, -1, x, 0, -1, structure)
        s.set(x, 1, -1, structure)                      # 가루 받침 = 발사기 급전원
        s.set(x, 2, -1, redstone_wire(
            east="side", west="side" if x > 0 else "none"))
        s.fill(x, 3, -1, x, 5, -1, structure)

        # z=0 : 뼛가루 계통
        s.fill(x, -1, 0, x, 0, 0, structure)
        s.set(x, 1, 0, dispenser(SOUTH))                # 켈프 밑동에 뼛가루 사용
        s.set(x, 2, 0, dropper(DOWN))                   # 가루에 두드려 발사기로 밀어 넣는다
        s.set(x, 3, 0, hopper(DOWN))                    # 위 라인에서 끌어와 드로퍼로
        s.set(x, 4, 0, hopper(EAST))                    # 뼛가루 분배 라인
        s.set(x, 5, 0, structure)

        # z=1 : 물기둥 + 켈프
        s.set(x, -1, 1, structure)                      # 모래 받침 (모래는 중력 블록)
        s.set(x, 0, 1, SAND)
        s.set(x, 1, 1, KELP)                            # 밑동 (영구)
        s.set(x, 2, 1, WATER)                           # 성장칸 — 여기서 잘린다
        s.set(x, 3, 1, WATER)                           # 성장칸 — 여기서 감지
        s.set(x, 4, 1, hopper(EAST))                    # 떠오른 켈프를 받는다
        s.set(x, 5, 1, structure)

        # z=2 : 절단 회로
        s.fill(x, -1, 2, x, 1, 2, structure)
        s.set(x, 2, 2, piston(NORTH))
        s.set(x, 3, 2, observer(NORTH))
        s.fill(x, 4, 2, x, 5, 2, structure)

        # z=3 : 절단 회로 급전
        s.fill(x, -1, 3, x, 1, 3, structure)
        s.set(x, 2, 3, structure)                       # 가루 받침 = 피스톤 급전원
        s.set(x, 3, 3, redstone_wire(
            north="side", east="side" if x < columns - 1 else "none",
            west="side" if x > 0 else "none"))
        s.fill(x, 4, 3, x, 5, 3, structure)

    # 서쪽 끝막이 + 뼛가루 투입구
    s.fill(-1, -1, -1, -1, 5, 3, structure)
    s.set(-1, 5, 0, chest(NORTH))                       # 뼛가루 투입 상자
    s.set(-1, 4, 0, hopper(EAST))                       # 라인 시작

    # 동쪽 끝: 수거 상자 + 라인 끝 + 발사기 클럭
    s.fill(columns, -1, -1, columns, 5, 3, structure)
    s.set(columns, 4, 1, chest(EAST))                   # 켈프 수거
    s.set(columns, 5, 1, GLASS)                         # 상자 위는 불투명 금지
    s.set(columns, 4, 0, chest(EAST))                   # 뼛가루 라인 끝(넘침)
    s.set(columns, 5, 0, GLASS)
    s.set(columns, 2, -1, observer(EAST))               # 자가 발진 클럭
    s.set(columns + 1, 2, -1, observer(WEST))

    s.note("뼛가루 1개 = 켈프 1칸. 산출량은 기둥 수가 아니라 뼛가루 공급량이 정한다.")
    s.note("발사기 급이에 호퍼가 아니라 드로퍼를 쓴다. 호퍼는 가루 옆에서 잠긴다.")
    s.note("모래 아래에 받침이 있다. 모래는 중력 블록이라 없으면 떨어진다.")

    return Design(
        schematic=s,
        principle="발사기가 켈프 밑동에 뼛가루를 사용 → 즉시 1칸 성장 → 두 번 자라 "
                  "3칸이 되면 관측기가 감지 → 피스톤이 2번째 칸 절단 → "
                  "부력으로 떠올라 천장 호퍼로 수거",
        circuit=[
            "1. 관측기 클럭 → 가루(z=-1, Y=2)",
            "2. 가루 → 받침(z=-1, Y=1) → 인접 발사기(z=0, Y=1) 작동 → 뼛가루 사용",
            "3. 같은 가루 → 인접 드로퍼(z=0, Y=2) 작동 → 뼛가루를 발사기에 보충",
            "4. 켈프가 3칸이 되면 관측기(z=2, Y=3)가 감지",
            "5. 관측기 출력 → 가루(z=3, Y=3) → 받침(z=3, Y=2) → 피스톤(z=2, Y=2)",
            "6. 피스톤이 2번째 칸을 부숨 → 위 칸도 함께 낙하 (1회 2개)",
            "7. 잘린 켈프가 물기둥을 타고 떠올라 Y=4 물먹임 호퍼로",
        ],
        steps=[
            f"1) 동서(X) 방향 {columns}기둥. Y=-1 받침 위에 모래를 놓고 켈프를 한 칸 심는다.",
            "2) z=0 에 발사기(남향)를 놓고 그 위에 드로퍼(북향), 그 위에 아래방향 호퍼, "
            "맨 위에 동향 뼛가루 라인을 올린다.",
            "3) z=-1 Y=1 에 받침 블록, 그 위 Y=2 에 레드스톤 가루를 한 줄 잇는다. "
            "동쪽 끝에 관측기 2개를 마주보게 놓으면 클럭이 저절로 돈다.",
            "4) z=2 에 피스톤(북)과 관측기(북), z=3 에 받침과 가루를 놓는다.",
            "5) 물기둥(Y=2,3)을 채우고 Y=5 로 천장을 덮는다.",
            "6) 서쪽 뼛가루 투입 상자에 뼛가루를 넣으면 돈다. "
            "이끼 뼛가루 팜(mossbed_auto + composterbank)에 물리면 자급된다.",
        ],
        rate=f"뼛가루 공급량과 1:1. 기둥 {columns}개면 클럭 속도상 여유가 충분하므로 "
             f"실제 산출은 뼛가루가 얼마나 들어오느냐로 정해진다.",
        warnings=[
            "뼛가루가 곧 켈프다. 이끼 뼛가루 팜을 붙이지 않으면 뼛가루를 손으로 대야 한다.",
            "발사기 급이는 반드시 드로퍼로 할 것. 호퍼를 쓰면 급전용 가루에 잠겨 "
            "클럭이 돌 때마다 공급이 끊긴다.",
            "모래 아래 받침을 빼면 안 된다. 모래가 떨어지면 켈프가 통째로 무너진다.",
            "관측기 클럭은 빠르다. 뼛가루를 과소비하면 가루 줄에 중계기를 넣어 늦출 것.",
        ],
        manual_items=["물 양동이 (물기둥)", "켈프 (초기 식재)", "뼛가루 (초기 장전)"],
    )
