"""사탕수수 팜 (관측기 + 피스톤 자동 수확, 진흙 아래 호퍼 수거).

단면도 (Z축, 줄은 X축 방향으로 반복):

        z=0     z=1        z=2          z=3          z=4
 Y=+3   ---     돌         (성장칸)     관측기(북)   레드스톤 가루
 Y=+2   ---     돌         (성장칸)     피스톤(북)   돌  ← 가루의 받침
 Y=+1   ---     돌         사탕수수     돌           돌
 Y= 0   돌      물 수원    진흙         돌           돌
 Y=-1   돌      돌         호퍼(동→)    돌           돌
 Y=-2   돌      돌         돌           돌           돌

수확 신호 (확정된 레드스톤 규칙만 사용):
  1. 관측기(z=3,Y=3, 북향)가 사탕수수 3번째 칸(z=2,Y=3) 성장을 감지
  2. 관측기 출력면은 남쪽 → (z=4,Y=3) 레드스톤 가루를 직접 급전
  3. 가루는 받침 블록 (z=4,Y=2) 을 약하게 급전
  4. 급전된 블록에 인접한 피스톤 (z=3,Y=2) 이 작동 → 2번째 칸을 부숨
  5. 위에 있던 3번째 칸도 지지를 잃고 함께 떨어짐 → 1회 2개 수확

수거에 흙이 아니라 '진흙'을 쓰는 이유:
  일반 호퍼는 바로 위 블록 공간의 아이템만 줍는데, 그 자리가 '꽉 찬 블록'이면
  줍지 못한다. 흙은 꽉 찬 블록이라 흙 아래 호퍼로는 수확물을 회수할 수 없다.
  진흙은 꽉 찬 블록이 아니라서 위키가 명시한다 —
  "a hopper that is under a mud block can collect items dropped on top of it".
  사탕수수는 진흙 위에도 심을 수 있으므로, 진흙 한 줄 + 그 아래 호퍼 한 줄이면
  광산 수레/레일 없이 수거가 끝난다.
"""
from __future__ import annotations

from .. import mechanics as M
from ..blocks import (EAST, GLASS, MUD, NORTH, STONE, SUGAR_CANE, WATER,
                      chest, hopper, observer, piston, redstone_wire)
from ..schematic import Schematic
from . import Design


def build(length: int = 12, soil=MUD, structure=STONE) -> Design:
    if length < 2:
        raise ValueError("length 는 2 이상이어야 한다")

    s = Schematic(
        name=f"sugarcane_{length}",
        description=f"사탕수수 팜 {length}포기 · 관측기+피스톤 자동수확 · 진흙 아래 호퍼 수거",
    )

    for x in range(length):
        # z=0 : 물 수로 바깥 벽
        s.fill(x, -2, 0, x, 0, 0, structure)

        # z=1 : 물 수로. Y=0 만 물이고 위는 막는다.
        #       (위키: 인접한 물은 다른 블록으로 덮여 있어도 성장 조건을 만족한다)
        s.fill(x, -2, 1, x, -1, 1, structure)
        s.set(x, 0, 1, WATER)
        s.fill(x, 1, 1, x, 3, 1, structure)

        # z=2 : 진흙에 사탕수수, 그 아래 호퍼 한 줄이 동쪽 상자로 흘려보낸다
        s.set(x, -2, 2, structure)
        s.set(x, -1, 2, hopper(EAST))
        s.set(x, 0, 2, soil)
        s.set(x, 1, 2, SUGAR_CANE)          # 심는 건 밑동 1칸뿐, 나머지는 자란다

        # z=3 : 피스톤 기둥
        s.fill(x, -2, 3, x, 1, 3, structure)
        s.set(x, 2, 3, piston(NORTH))        # 사탕수수 2번째 칸을 부순다
        s.set(x, 3, 3, observer(NORTH))      # 3번째 칸 성장을 감지

        # z=4 : 레드스톤 기둥
        s.fill(x, -2, 4, x, 2, 4, structure)  # (x,2,4) 가 가루의 받침 = 피스톤 급전원
        s.set(x, 3, 4, redstone_wire(
            north="side",                     # 바로 북쪽 관측기(출력면)와 연결
            east="side" if x < length - 1 else "none",
            west="side" if x > 0 else "none"))

    # 서쪽 끝: 물 막이 + 아이템 이탈 방지
    s.fill(-1, -2, 0, -1, -1, 4, structure)
    s.set(-1, 0, 1, structure)
    s.fill(-1, 0, 2, -1, 3, 2, structure)

    # 동쪽 끝: 호퍼 줄이 흘러드는 상자
    s.fill(length, -2, 0, length, -2, 4, structure)
    s.set(length, -1, 2, chest(EAST))
    s.set(length, 0, 1, structure)
    # 상자 바로 위는 불투명 블록이면 안 된다 (상자가 열리지 않는다) → 유리로 막는다
    s.set(length, 0, 2, GLASS)
    s.fill(length, 1, 2, length, 3, 2, structure)

    s.note("관측기 facing=north = '북쪽을 바라본다'(감지면). 출력은 반대편 남쪽으로 나간다.")
    s.note("레드스톤 가루는 받침 블록을 약하게 급전하고, 급전된 블록이 옆의 피스톤을 켠다.")
    s.note("상자 바로 위 칸은 유리다. 불투명 블록을 얹으면 상자가 열리지 않는다.")
    s.note("진흙은 꽉 찬 블록이 아니라서 바로 아래 호퍼가 위에 떨어진 아이템을 줍는다. "
           "흙으로 바꾸면 수거가 되지 않는다.")

    plants = length
    rate = M.column_crop_rate(plants, "sugar_cane")

    return Design(
        schematic=s,
        principle="물 옆 진흙에서 사탕수수 성장 → 관측기가 3번째 칸 감지 → 피스톤이 2번째 칸 파괴 "
                  "→ 진흙 위에 떨어진 아이템을 바로 아래 호퍼가 수거 → 동쪽 끝 상자",
        circuit=[
            "1. 관측기(z=3, Y=3, 북향) ← 사탕수수 3번째 칸(z=2, Y=3) 성장 감지",
            "2. 관측기 출력면(남쪽) → 레드스톤 가루(z=4, Y=3) 강한 신호 15",
            "3. 가루 → 받침 블록(z=4, Y=2) 약한 급전",
            "4. 급전된 블록 → 인접한 피스톤(z=3, Y=2) 작동",
            "5. 피스톤이 사탕수수 2번째 칸을 부숨 → 위 3번째 칸도 함께 낙하 (1회 2개)",
            "※ 가루가 X축으로 이어져 있어 한 포기가 자라면 줄 전체가 같이 수확된다.",
            "※ 포기마다 관측기가 따로 있으므로 길이를 늘려도 중계기가 필요 없다.",
        ],
        steps=[
            f"1) 동서(X) 방향 {length}칸 자리를 잡는다. 스케매틱 원점은 서쪽 끝 바깥 벽이다.",
            f"2) 진흙 {length}개를 미리 만든다. (흙에 물병을 사용하면 진흙이 된다)",
            "3) Y=-2 바닥 → Y=-1 호퍼 줄 순서로 아래부터 쌓는다. 호퍼는 전부 동쪽을 향하게.",
            "4) z=1 에 물 수원을 한 줄 채우고 위(Y=1~3)를 막는다. "
            "덮인 물도 성장 조건을 만족하므로 문제없다.",
            "5) z=2 에 진흙을 깔고 사탕수수를 밑동 1칸만 심는다. 나머지는 알아서 자란다.",
            "6) z=3 에 피스톤(북향), 그 위에 관측기(북향)를 놓는다. 방향이 반대면 작동하지 않는다.",
            "7) z=4 에 받침 블록을 채우고 그 위(Y=3)에 레드스톤 가루를 한 줄 잇는다.",
            f"8) 동쪽 끝(x={length}, Y=-1) 상자에 수확물이 모인다. "
            "상자 바로 위는 유리다 — 돌로 바꾸면 상자가 열리지 않는다.",
        ],
        rate=f"{plants}포기 → 시간당 약 {rate:,.0f}개 "
             f"(사탕수수 1칸 성장에 랜덤틱 16회 = 실시간 약 18분)",
        warnings=[
            "바닥을 흙/모래로 바꾸면 안 된다. 꽉 찬 블록이라 아래 호퍼가 수확물을 줍지 못한다. "
            "진흙이어야 한다.",
            "관측기/피스톤 방향(facing=north)이 핵심이다. 손으로 지을 때는 북쪽을 보고 놓을 것.",
            "물 수로 위(Y=1~3)를 막지 않으면 부서진 사탕수수가 물에 빠져 회수되지 않는다.",
            f"청크 로딩 대책 필요: 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다. "
            "AFK 상주 또는 /forceload 로 청크를 고정해야 자란다.",
            "피스톤이 수확한 직후 관측기가 '사라짐'도 감지해 한 번 더 펄스를 낸다. "
            "정상 동작이며 수확량에는 영향이 없다.",
            "진흙 아래에 뾰족한 종유석을 두면 진흙이 점토로 변하는 메커니즘이 있다. "
            "이 설계는 아래가 호퍼라 해당 없지만, 개조할 때 주의할 것.",
        ],
        manual_items=[],
    )
