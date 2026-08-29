"""사탕수수 팜 (관측기 + 피스톤 + 호퍼 광산 수레 수거).

단면도 (Z축, 줄은 X축 방향으로 반복):

        z=0     z=1        z=2         z=3          z=4
 Y=+3   ---     돌         (성장칸)    관측기(북)    레드스톤 가루
 Y=+2   ---     돌         (성장칸)    피스톤(북)    돌  ← 가루의 받침
 Y=+1   ---     돌         사탕수수    돌            돌
 Y= 0   돌      물 수원    흙          돌            돌
 Y=-1   돌      돌         레일        돌            돌
 Y=-2   돌      돌         기초/호퍼   기초/상자     돌

신호 경로 (전부 확정된 레드스톤 규칙만 사용):
  1. 관측기(z=3,Y=3, 북향)가 사탕수수 3번째 칸(z=2,Y=3) 성장을 감지
  2. 관측기 출력면은 남쪽 → (z=4,Y=3) 레드스톤 가루를 직접 급전
  3. 가루는 받침 블록 (z=4,Y=2) 을 약하게 급전
  4. 급전된 블록에 인접한 피스톤 (z=3,Y=2) 이 작동 → 2번째 칸을 부숨
  5. 위에 있던 3번째 칸도 지지를 잃고 함께 떨어짐 → 1회 2개 수확
"""
from __future__ import annotations

from .. import mechanics as M
from ..blocks import (DIRT, NORTH, SOUTH, STONE, SUGAR_CANE, WATER,
                      chest, hopper, observer, piston, rail, redstone_wire,
                      REDSTONE_BLOCK)
from ..schematic import Schematic
from . import Design

POWERED_RAIL_SPACING = 8   # 평지에서 광산 수레가 한 번 가속으로 가는 거리


def build(length: int = 12, soil=DIRT, structure=STONE) -> Design:
    if length < 4:
        raise ValueError("length 는 4 이상이어야 한다 (레일 왕복과 호퍼 자리 확보)")

    s = Schematic(
        name=f"sugarcane_{length}",
        description=f"사탕수수 팜 {length}포기 · 관측기+피스톤 자동수확 · 호퍼 광산 수레 수거",
    )

    # 가속 레일 위치: 양 끝 + 8칸마다
    powered = {0, length - 1} | {x for x in range(0, length, POWERED_RAIL_SPACING)}
    # 호퍼는 가속 레일(아래에 레드스톤 블록이 들어감)과 겹치면 안 된다
    hopper_x = next((x for x in range(length // 2, length) if x not in powered),
                    next(x for x in range(length) if x not in powered))

    for x in range(length):
        # z=0 : 물 수로 바깥 벽
        s.fill(x, -2, 0, x, 0, 0, structure)

        # z=1 : 물 수로 (Y=0 만 물, 위는 막아서 아이템이 새지 않게)
        s.fill(x, -2, 1, x, -1, 1, structure)
        s.set(x, 0, 1, WATER)
        s.fill(x, 1, 1, x, 3, 1, structure)

        # z=2 : 사탕수수 줄 + 그 아래 수거 레일
        s.set(x, -2, 2, hopper(SOUTH) if x == hopper_x
              else (REDSTONE_BLOCK if x in powered else structure))
        s.set(x, -1, 2, rail("east_west", powered=True) if x in powered else rail("east_west"))
        s.set(x, 0, 2, soil)
        s.set(x, 1, 2, SUGAR_CANE)          # 심는 건 밑동 1칸뿐, 나머지는 자란다

        # z=3 : 피스톤 기둥
        s.set(x, -2, 3, chest(SOUTH) if x == hopper_x else structure)
        s.fill(x, -1, 3, x, 1, 3, structure)
        s.set(x, 2, 3, piston(NORTH))        # 사탕수수 2번째 칸을 부순다
        s.set(x, 3, 3, observer(NORTH))      # 3번째 칸 성장을 감지

        # z=4 : 레드스톤 기둥
        s.fill(x, -2, 4, x, 2, 4, structure)  # (x,2,4) 가 가루의 받침 = 피스톤 급전원
        # north=side : 바로 북쪽의 관측기(출력면)와 연결된 상태
        s.set(x, 3, 4, redstone_wire(
            north="side",
            east="side" if x < length - 1 else "none",
            west="side" if x > 0 else "none"))

    # 양 끝 마감: 물 막이 · 레일 범퍼 · 아이템 이탈 방지
    for x in (-1, length):
        s.set(x, -1, 2, structure)            # 광산 수레가 튕겨 돌아오는 벽
        s.set(x, 0, 1, structure)             # 물 수로 끝막이
        s.fill(x, 0, 2, x, 3, 2, structure)   # 수확물이 밖으로 튀지 않게

    s.note("관측기 facing=north = '북쪽을 바라본다' (감지면). 출력은 반대편 남쪽으로 나간다.")
    s.note("레드스톤 가루는 받침 블록을 약하게 급전하고, 급전된 블록이 옆의 피스톤을 켠다.")
    s.note(f"가속 레일 위치(x): {sorted(powered)} · 호퍼/상자 위치(x): {hopper_x}")

    plants = length
    rate = M.column_crop_rate(plants, "sugar_cane")

    return Design(
        schematic=s,
        principle="물 옆 흙에서 사탕수수 성장 → 관측기가 3번째 칸 감지 → 피스톤이 2번째 칸 파괴 "
                  "→ 흙 위에 떨어진 아이템을 아래 호퍼 광산 수레가 관통 수거 → 호퍼 → 상자",
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
            "2) Y=-2 기초 → Y=-1 레일 순서로 아래부터 쌓는다. 가속 레일 아래에는 레드스톤 블록.",
            "3) z=1 에 물 수원을 한 줄 채우고 위(Y=1~3)를 막는다. 막지 않으면 수확물이 물에 빠져 사라진다.",
            "4) z=2 에 흙을 깔고 사탕수수를 밑동 1칸만 심는다. 나머지는 알아서 자란다.",
            "5) z=3 에 피스톤(북향), 그 위에 관측기(북향)를 놓는다. 방향을 반대로 놓으면 작동하지 않는다.",
            "6) z=4 에 받침 블록을 채우고 그 위(Y=3)에 레드스톤 가루를 한 줄 잇는다.",
            f"7) 레일 위에 호퍼 광산 수레 1개를 올린다. (x={hopper_x} 아래 호퍼 → 상자로 배출)",
            "8) 양 끝 마감 블록을 놓아 물과 아이템이 새지 않게 한다.",
            f"9) 상자는 (x={hopper_x}, Y=-2, z=3) 에 묻혀 있다. 꺼내 쓰려면 그 위 블록을 파거나 "
            "상자에서 호퍼를 하나 더 빼서 지상으로 올릴 것.",
        ],
        rate=f"{plants}포기 → 시간당 약 {rate:,.0f}개 (사탕수수 1칸 성장에 랜덤틱 16회 = 실시간 약 18분)",
        warnings=[
            "관측기/피스톤 방향(facing=north)이 핵심이다. Litematica 로 지으면 방향까지 맞춰지지만, "
            "손으로 지을 때는 북쪽을 보고 놓아야 한다.",
            "물 수로 위(Y=1~3)를 막지 않으면 부서진 사탕수수가 물에 빠져 회수되지 않는다.",
            "호퍼 광산 수레는 '레일 바로 위 블록에 놓인 아이템'을 관통해서 줍는다. "
            "레일 위에 다른 블록을 얹지 말 것.",
            f"청크 로딩 대책 필요: 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다. "
            "AFK 상주 또는 /forceload 로 청크를 고정해야 자란다.",
            "피스톤이 수확한 직후 관측기가 '사라짐'도 감지해 한 번 더 펄스를 낸다. "
            "정상 동작이며 수확량에는 영향이 없다.",
        ],
        manual_items=[
            "호퍼 광산 수레 1개 (스케매틱은 엔티티를 배치하지 않는다 — 레일 위에 직접 올릴 것)",
        ],
    )
