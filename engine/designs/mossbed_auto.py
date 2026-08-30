"""다층 자동 이끼 베드 — 피스톤 수확 + 제자리 돌 재생성.

평평한 단층 베드(mossbed)와의 차이:
  · 뼛가루 확산 부피는 7x11x7 로 '세로가 11칸'이다. 층을 쌓으면 뼛가루 한 개가
    훨씬 많은 돌을 이끼로 바꾼다.
  · 이끼 블록은 피스톤에 밀리면 부서져 아이템으로 떨어진다 (위키 확인).
    베드 칸마다 피스톤을 1:1 로 붙여 전량을 자동 수확한다.
  · 수확 후 빈 칸은 '위에서 물로 흘러든 용암'이 다시 돌로 채운다.
    돌을 손으로 채워 넣을 필요가 없다.

한 층의 단면 (Z축) — 벽 / 베드 / 피스톤 이 3칸 주기로 반복한다:

  z=0 벽   z=1 베드  z=2 피스톤(북)   z=3 벽   z=4 베드  z=5 피스톤(북) ...

왜 베드마다 뒤에 벽을 두는가 (이전 판의 버그)
  피스톤이 미는 칸은 대부분 '돌'이다. 이끼는 밀리면 부서지지만(PushReaction
  DESTROY) 돌은 그냥 밀려난다. 뒤가 뚫려 있으면 수확 직후 빈 칸이 생겼을 때
  돌과 앞줄 피스톤이 통째로 한 칸 밀려 베드가 어긋난다.
  베드 바로 뒤에 벽을 두면 돌일 때는 '밀 곳이 없어' 피스톤이 아예 펴지지
  않고, 이끼일 때만 부서진다. 호퍼도 블록 개체라 자바에서는 밀리지 않으므로
  급이 통로가 벽을 대신해도 된다.

한 층의 높이 구성:
  Y   : 베드 칸(비움) / 피스톤 / 벽
  Y+1 : 베드 칸 위는 용암 수원(돌 재생성), 피스톤 위는 받침 블록
  Y+2 : 받침 위에 레드스톤 가루(피스톤 급전), 나머지는 층 분리 블록
  Y+3 : 다음 층

급전
  층마다 서쪽 기둥(x=-1)의 Y+2 를 전부 가루로 깔아 피스톤 세 줄을 하나로 묶고,
  서쪽 끝에 관측기 두 개를 마주 보게 놓아 자가 발진시킨다. 층마다 클럭 하나다.
  (이전 판은 가루만 깔고 급전원이 없어 피스톤이 영영 움직이지 않았다.)
"""
from __future__ import annotations

from ..blocks import (DOWN, EAST, GLASS, LAVA, MOSS_BLOCK, NORTH, SOUTH, STONE,
                      WATER, WEST,
                      chest, dispenser, hopper, observer, piston, redstone_wire)
from ..schematic import Schematic
from . import Design

BED_ROWS = (1, 4, 7)          # 베드가 놓이는 z
PISTON_ROWS = (2, 5, 8)       # 피스톤이 놓이는 z (각각 z-1 을 부순다)
WALL_ROWS = (0, 3, 6)         # 베드 뒤를 받치는 벽 (밀림 방지)
DEPTH = 9                     # z=0..8
LAYER_PITCH = 3
COMPOST_MOSS = 0.65           # 이끼 블록 퇴비 성공률 (위키)
COMPOST_LEVELS = 7            # 성공 7회 = 뼛가루 1개 (위키)
FLAT_CONVERSION = 27 / 49     # 위키: 평평한 7x7 49칸 중 평균 27칸이 이끼가 된다


def bed_cells(width: int, layers: int) -> int:
    return width * len(BED_ROWS) * layers - 1     # 씨앗 칸 1개는 수확하지 않는다


def yields(width: int = 7, layers: int = 3) -> dict:
    cells = bed_cells(width, layers)
    moss = cells * FLAT_CONVERSION
    bonemeal = moss * COMPOST_MOSS / COMPOST_LEVELS
    return {"cells": cells, "moss_est": moss, "bonemeal_est": bonemeal,
            "stone_est": moss}


def build(width: int = 7, layers: int = 3, structure=STONE) -> Design:
    if width < 1 or layers < 1:
        raise ValueError("width 와 layers 는 1 이상이어야 한다")
    if width > 7:
        raise ValueError("뼛가루 확산은 중심에서 좌우 3칸까지다 → width 는 7 이하")
    if layers > 3:
        raise ValueError("확산 높이는 중심에서 위아래 5칸 → 간격 3 기준 3층까지")

    s = Schematic(
        name=f"mossbed_auto_w{width}_l{layers}",
        description=f"다층 자동 이끼 베드 {width}x{len(BED_ROWS)}칸 x {layers}층 · "
                    f"피스톤 수확 + 제자리 돌 재생성",
    )
    cx = width // 2
    mid = layers // 2
    seed_y = mid * LAYER_PITCH
    # 씨앗은 가운데 베드 줄에 둔다. 뼛가루 확산이 중심에서 z 로 3칸까지라,
    # 가운데(z=4)에 두어야 세 줄(1,4,7)이 전부 사정거리에 들어온다.
    seed_z = BED_ROWS[len(BED_ROWS) // 2]
    feed_z = seed_z - 1                          # 씨앗 뒤 벽줄 = 급이 통로

    for L in range(layers):
        y = L * LAYER_PITCH
        for x in range(width):
            for z in BED_ROWS:
                if x == cx and y == seed_y and z == seed_z:
                    s.set(x, y, z, MOSS_BLOCK)          # 영구 씨앗
                    # 씨앗 위는 공기여야 뼛가루가 작동한다 → 용암을 놓지 않는다
                else:
                    s.set(x, y + 1, z, LAVA)            # 제자리 돌 재생성
                s.set(x, y + 2, z, structure)           # 층 분리
            for z in PISTON_ROWS:
                if x == cx and y == seed_y and z == seed_z + 1:
                    s.set(x, y, z, structure)           # 씨앗을 부수지 않도록 막는다
                else:
                    s.set(x, y, z, piston(NORTH))
                s.set(x, y + 1, z, structure)           # 가루 받침 = 피스톤 급전원
                s.set(x, y + 2, z, redstone_wire(
                    north="side", south="side",
                    east="side" if x < width - 1 else "none",
                    west="side"))
            for z in WALL_ROWS:                          # 베드 뒤 벽
                s.fill(x, y, z, x, y + 2, z, structure)

        # 서쪽 기둥: 베드 줄엔 물 수원, Y+2 는 전부 가루로 깔아 세 줄을 묶는다
        for z in range(DEPTH):
            s.set(-1, y, z, WATER if z in BED_ROWS else structure)
            s.set(-1, y + 1, z, structure)
            s.set(-1, y + 2, z, redstone_wire(
                north="side" if z else "none",
                south="side" if z < DEPTH - 1 else "none",
                east="side" if z in PISTON_ROWS else "none"))
        for z in BED_ROWS:
            s.set(-2, y, z, structure)                   # 물 수원 바깥벽

        # 층마다 자가 발진 클럭 하나. 가루에 붙는 관측기는 가루 반대편을 봐야
        # 출력면이 가루를 때린다.
        s.set(-2, y + 2, 0, observer(WEST))
        s.set(-3, y + 2, 0, observer(EAST))

        # 동쪽 끝. 베드 줄은 아래에서 호퍼 기둥으로 통째로 잇는다.
        for z in range(DEPTH):
            if z not in BED_ROWS:
                s.fill(width, y, z, width, y + 2, z, structure)

    # 맨 아래층 바닥. 베드 칸은 비워 두는 자리라 바닥이 없으면 물도 용암도
    # 그대로 흘러내린다.
    for x in range(-1, width):
        for z in range(DEPTH):
            if (x, -1, z) not in s.blocks:
                s.set(x, -1, z, structure)

    # 씨앗 옆(벽줄) 뼛가루 발사기 + 급이 통로.
    # 발사기를 '씨앗 아래'가 아니라 '옆'에 두는 이유: 아래는 층 분리면(Y+2)이라
    # 피스톤 가루가 지나간다. 호퍼는 가루 옆에서 잠기므로 급이할 길이 없다.
    # 벽줄(Y=씨앗과 같은 높이)은 가루와 대각선이라 안전하다.
    s.set(cx, seed_y, feed_z, dispenser(SOUTH))
    # 급이는 동쪽에서 들어온다. 서쪽 기둥은 층 가루가 바로 위를 지나가서,
    # 거기 호퍼를 두면 클럭이 돌 때마다 잠긴다.
    for x in range(width, cx, -1):
        s.set(x, seed_y, feed_z, hopper(WEST))
    # 발사기 급전: 바로 위 블록에 가루를 얹어 그 블록을 약하게 급전한다.
    # 가루는 옆(z=피스톤 줄)의 가루와 이어져 층 클럭을 그대로 받는다.
    s.set(cx, seed_y + 2, feed_z, redstone_wire(north="side", south="side"))

    # 수거 호퍼 기둥: 최상층 베드 높이부터 Y=0 까지 끊김 없이 아래로.
    # 재생성용 물이 흐를 때 부서진 이끼가 동쪽으로 밀려와 이 기둥으로 들어간다.
    top_bed = (layers - 1) * LAYER_PITCH
    for z in BED_ROWS:
        for yy in range(0, top_bed + 1):
            s.set(width, yy, z, hopper(DOWN))
        s.fill(width, top_bed + 1, z, width, top_bed + 2, z, structure)
    for z in range(DEPTH):
        s.set(width, -1, z, hopper(SOUTH))
        s.set(width, -2, z, structure)
    s.set(width, -1, DEPTH, chest(SOUTH))
    s.set(width, 0, DEPTH, GLASS)
    s.set(width, -2, DEPTH, structure)

    s.note("베드 칸은 비워 둔다. 물이 채우고 위 용암이 흘러들어 '돌'이 된다.")
    s.note("씨앗 칸만 위가 공기다. 뼛가루는 '대상 이끼 위가 공기'일 때만 작동한다.")
    s.note("씨앗 앞의 피스톤 자리는 막아 두었다. 씨앗을 부수면 팜이 멈춘다.")
    s.note("이끼 블록은 피스톤에 밀리면 부서져 아이템이 된다 (위키 확인).")
    s.note("베드 뒤 벽이 밀림을 막는다. 돌일 때는 피스톤이 아예 펴지지 않는다.")

    y = yields(width, layers)
    return Design(
        schematic=s,
        principle=f"가운데 씨앗에 발사기가 뼛가루 사용 → {layers}층에 걸친 돌 "
                  f"{y['cells']}칸이 이끼로 변환 → 칸마다 붙은 피스톤이 전량 파괴 → "
                  f"빈 칸은 위 용암이 다시 돌로 채움 → 무한 순환",
        circuit=[
            "1. 층마다 관측기 클럭(x=-2,-3)이 서쪽 기둥 가루를 계속 때린다",
            "2. 가루 줄(각 층 Y+2) → 받침 블록(Y+1) → 인접 피스톤(Y) 작동",
            "3. 같은 가루가 씨앗 옆 발사기도 두드려 뼛가루를 사용한다",
            "4. 7x11x7 부피 안의 돌이 이끼로 변환 (층을 쌓아 부피를 채운다)",
            "5. 피스톤이 앞의 이끼를 부순다. 돌이면 뒤 벽에 막혀 펴지지 않는다",
            "6. 빈 칸에 서쪽 물 수원이 흘러들고, 위 용암이 내려와 다시 '돌'이 된다",
            "7. 아이템은 물살에 동쪽으로 밀려 호퍼 기둥 → 상자로",
        ],
        steps=[
            f"1) 층 간격 3으로 {layers}층. 한 층은 (벽·베드·피스톤) 3칸 주기 x 3벌이다.",
            "2) 베드 칸(z=1,4,7)은 비워 두고, 그 바로 위에 용암 수원을 놓는다.",
            "3) 피스톤 줄(z=2,5,8)은 전부 북쪽을 향하게 한다. 앞의 베드 칸을 부순다.",
            "4) 피스톤 위에 받침 블록, 그 위에 레드스톤 가루를 깐다. "
            "서쪽 기둥(x=-1)의 같은 높이를 전부 가루로 이어 세 줄을 한 번에 묶는다.",
            "5) 서쪽 끝(x=-2,-3)에 관측기 두 개를 마주 보게 놓으면 클럭이 저절로 돈다.",
            f"6) 가운데 씨앗 칸(x={cx}, z={seed_z}, 층 {mid})에만 이끼 블록을 놓고, "
            "그 위는 반드시 비워 둔다.",
            f"7) 씨앗 바로 북쪽(z={feed_z})에 남쪽을 향한 발사기를 넣고 뼛가루를 채운다. "
            f"그 줄이 곧 급이 통로다 — 동쪽 끝(x={width})에서 서쪽으로 호퍼를 잇는다.",
            "8) 서쪽 끝 각 베드 줄에 물 수원을 하나씩 붓는다. "
            "수확으로 줄이 비면 물이 흘러 들어가 채운다.",
            f"9) 동쪽 끝(x={width}) 베드 줄마다 아래방향 호퍼를 놓고 기둥으로 이어 "
            "Y=-1 남쪽 호퍼 줄 → 상자로 모은다.",
            "10) 상자를 퇴비통 뱅크(litematic composterbank)에 물린다.",
        ],
        rate=f"베드 {y['cells']}칸 · 뼛가루 1개당 이끼 약 {y['moss_est']:.0f}개 (추정) → "
             f"퇴비 환산 약 {y['bonemeal_est']:.1f}개, 돌 약 {y['stone_est']:.0f}칸 소비",
        warnings=[
            "산출량은 추정이다. 위키가 주는 확실한 수치는 '평평한 7x7(49칸)에서 평균 "
            "27칸'뿐이라, 그 변환율(55%)을 다층에 그대로 적용했다.",
            "관측기 클럭은 매우 빠르다. 피스톤이 계속 여닫히므로 서버 부하가 있다. "
            "가루 줄에 중계기를 끼워 늦출 수 있다.",
            "씨앗 칸 위를 막으면 뼛가루가 아예 작동하지 않는다. 절대 채우지 말 것.",
            "물을 먼저, 용암을 나중에 놓아야 한다. 반대로 하면 흑요석이 된다.",
            "수거는 재생성용 물이 흐를 때 아이템을 동쪽으로 밀어주는 것에 기댄다. "
            "베드 폭을 7보다 넓히지 말 것 (물은 수원에서 7칸까지 흐른다).",
        ],
        manual_items=[
            f"용암 양동이 {width * len(BED_ROWS) * layers - 1}개",
            f"물 양동이 {len(BED_ROWS) * layers}개",
            "이끼 블록 1개 (씨앗)",
        ],
    )
