"""다층 자동 이끼 베드 — 피스톤 수확 + 제자리 돌 재생성.

평평한 단층 베드(mossbed)와의 차이:
  · 뼛가루 확산 부피는 7x11x7 로 '세로가 11칸'이다. 층을 쌓으면 뼛가루 한 개가
    훨씬 많은 돌을 이끼로 바꾼다.
  · 이끼 블록은 피스톤에 밀리면 부서져 아이템으로 떨어진다 (위키 확인).
    베드 칸마다 피스톤을 1:1 로 붙여 전량을 자동 수확한다.
  · 수확 후 빈 칸은 '위에서 물로 흘러든 용암'이 다시 돌로 채운다.
    돌을 손으로 채워 넣을 필요가 없다.

왜 층을 촘촘히 쌓아도 되는가:
  위키는 "뼛가루를 쓴 이끼 블록의 바로 위가 공기인지" 먼저 확인한다고 한다.
  그건 '대상 블록' 하나의 조건이고, 주변 돌이 이끼로 변환되는 데는 위가 공기일
  필요가 없다. 위가 공기여야 하는 건 '초목'이 자랄 때뿐이다.
  이끼 블록 자체가 퇴비 65% 로 수익의 대부분이므로, 초목을 포기하고 층을
  촘촘히 쌓는 쪽이 유리하다.

한 층의 단면 (Z축):
  z=0 : 물 수원 열 (수확으로 비면 줄 전체를 다시 채운다)
  z=1 : 베드 칸      z=2 : 피스톤(북) — z=1 을 부순다
  z=3 : 베드 칸      z=4 : 피스톤(북) — z=3 을 부순다
  z=5 : 베드 칸      z=6 : 피스톤(북) — z=5 을 부순다

한 층의 높이 구성:
  Y   : 베드 칸 / 피스톤
  Y+1 : 베드 칸 위는 용암 수원(돌 재생성), 피스톤 위는 받침 블록
  Y+2 : 받침 블록 위에 레드스톤 가루(피스톤 급전), 나머지는 층 분리 블록
  Y+3 : 다음 층
"""
from __future__ import annotations

from ..blocks import (DOWN, GLASS, LAVA, MOSS_BLOCK, NORTH, SOUTH, STONE, UP, WATER,
                      chest, dispenser, hopper, piston, redstone_wire)
from ..schematic import Schematic
from . import Design

BED_ROWS = (1, 3, 5)          # 베드가 놓이는 z
PISTON_ROWS = (2, 4, 6)       # 피스톤이 놓이는 z (각각 z-1 을 부순다)
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
    seed_z = BED_ROWS[len(BED_ROWS) // 2]

    for L in range(layers):
        y = L * LAYER_PITCH
        for x in range(width):
            for z in BED_ROWS:
                is_seed = (x == cx and y == seed_y and z == seed_z)
                # 베드 칸: 비워 둔다 (물이 채우고 용암이 돌로 바꾼다)
                if is_seed:
                    s.set(x, y, z, MOSS_BLOCK)          # 영구 씨앗
                    # 씨앗 위는 공기여야 뼛가루가 작동한다 → 용암을 놓지 않는다
                else:
                    s.set(x, y + 1, z, LAVA)            # 제자리 돌 재생성
            for z in PISTON_ROWS:
                # 씨앗을 부수지 않도록 씨앗 앞 피스톤만 막는다
                if x == cx and y == seed_y and z == seed_z + 1:
                    s.set(x, y, z, structure)
                else:
                    s.set(x, y, z, piston(NORTH))
                s.set(x, y + 1, z, structure)           # 가루 받침 = 피스톤 급전원
                s.set(x, y + 2, z, redstone_wire(
                    north="side", south="side",
                    east="side" if x < width - 1 else "none",
                    west="side"))
            # 층 분리 블록 (베드 칸 위)
            for z in BED_ROWS:
                s.set(x, y + 2, z, structure)
            # 물 수원 열
            s.set(x, y, 0, structure)
            s.fill(x, y + 1, 0, x, y + 2, 0, structure)

        # 서쪽 끝: 각 베드 줄에 물 수원 하나. 수확으로 비면 줄 전체를 채운다.
        for z in BED_ROWS:
            s.set(-1, y, z, WATER)
            s.fill(-1, y + 1, z, -1, y + 2, z, structure)
        for z in PISTON_ROWS:
            s.set(-1, y, z, structure)
            s.set(-1, y + 1, z, structure)
            # 가루를 z 축으로 이어 세 줄을 한 클럭에 묶는다
            s.set(-1, y + 2, z, redstone_wire(north="side", south="side", east="side"))
        s.fill(-1, y, 0, -1, y + 2, 0, structure)

        # 동쪽 끝. 베드 줄(z=1,3,5)은 아래에서 호퍼 기둥으로 통째로 잇는다.
        for z in range(0, 7):
            if z in BED_ROWS:
                continue
            s.fill(width, y, z, width, y + 2, z, structure)

    # 씨앗 아래 뼛가루 발사기
    s.set(cx, seed_y - 1, seed_z, dispenser(UP))

    # 수거 호퍼 기둥: 최상층 베드 높이부터 Y=0 까지 끊김 없이 아래로.
    # 재생성용 물이 흐를 때 부서진 이끼가 동쪽으로 밀려와 이 기둥으로 들어간다.
    top_bed = (layers - 1) * LAYER_PITCH
    for z in BED_ROWS:
        for yy in range(0, top_bed + 1):
            s.set(width, yy, z, hopper(DOWN))
        s.fill(width, top_bed + 1, z, width, top_bed + 2, z, structure)
    for z in range(0, 7):
        s.set(width, -1, z, hopper(SOUTH))
        s.set(width, -2, z, structure)
    s.set(width, -1, 7, chest(SOUTH))
    s.set(width, 0, 7, GLASS)
    s.set(width, -2, 7, structure)

    s.note("베드 칸은 비워 둔다. 물이 채우고 위 용암이 흘러들어 '돌'이 된다.")
    s.note("씨앗 칸(중앙)만 위가 공기다. 뼛가루는 '대상 이끼 위가 공기'일 때만 작동한다.")
    s.note("씨앗 앞의 피스톤 자리는 막아 두었다. 씨앗을 부수면 팜이 멈춘다.")
    s.note("이끼 블록은 피스톤에 밀리면 부서져 아이템이 된다 (위키 확인).")

    y = yields(width, layers)
    return Design(
        schematic=s,
        principle=f"중앙 씨앗에 발사기가 뼛가루 사용 → {layers}층에 걸친 돌 "
                  f"{y['cells']}칸이 이끼로 변환 → 칸마다 붙은 피스톤이 전량 파괴 → "
                  f"빈 칸은 위 용암이 다시 돌로 채움 → 무한 순환",
        circuit=[
            "1. 발사기(씨앗 바로 아래, 위 방향)가 뼛가루를 씨앗 이끼에 사용",
            "2. 7x11x7 부피 안의 돌이 이끼로 변환 (층을 쌓아 부피를 채운다)",
            "3. 가루 줄(각 층 Y+2) → 받침 블록(Y+1) → 인접 피스톤(Y) 작동",
            "4. 피스톤이 앞의 이끼 블록을 부순다 → 아이템 낙하",
            "5. 빈 칸에 서쪽 물 수원이 흘러들고, 위 용암이 내려와 다시 '돌'이 된다",
            "6. 아이템은 남쪽 호퍼 줄 → 상자 → 퇴비통 뱅크로",
        ],
        steps=[
            f"1) 층 간격 3으로 {layers}층을 쌓는다. 한 층은 베드 줄 3개 + 피스톤 줄 3개다.",
            "2) 베드 칸(z=1,3,5)은 비워 두고, 그 바로 위에 용암 수원을 놓는다.",
            "3) 피스톤 줄(z=2,4,6)은 전부 북쪽을 향하게 한다. 앞의 베드 칸을 부순다.",
            "4) 피스톤 위에 받침 블록, 그 위에 레드스톤 가루를 깐다. "
            "서쪽 끝에서 z축으로 이어 세 줄을 한 번에 묶는다.",
            f"5) 중앙 씨앗 칸(x={cx}, z={seed_z}, 층 {mid})에만 이끼 블록을 놓고, "
            "그 위는 반드시 비워 둔다.",
            "6) 씨앗 바로 아래에 위를 향한 발사기를 넣고 뼛가루를 채운다.",
            "7) 서쪽 끝 각 베드 줄에 물 수원을 하나씩 붓는다. "
            "수확으로 줄이 비면 물이 흘러 들어가 채운다.",
            "8) 동쪽 끝(x=width) 베드 줄마다 아래방향 호퍼를 놓고 기둥으로 이어 "
            "Y=-1 남쪽 호퍼 줄 → 상자로 모은다. "
            "재생성용 물이 흐를 때 부서진 이끼가 동쪽으로 밀려와 여기로 들어간다.",
            "9) 상자를 퇴비통 뱅크(litematic composterbank)에 물린다. "
            "이끼 블록을 반드시 함께 넣어야 순이익이 난다.",
        ],
        rate=f"베드 {y['cells']}칸 · 뼛가루 1개당 이끼 약 {y['moss_est']:.0f}개 (추정) → "
             f"퇴비 환산 약 {y['bonemeal_est']:.1f}개, 돌 약 {y['stone_est']:.0f}칸 소비",
        warnings=[
            "산출량은 추정이다. 위키가 주는 확실한 수치는 '평평한 7x7(49칸)에서 평균 "
            "27칸'뿐이라, 그 변환율(55%)을 다층에 그대로 적용했다. 실제 3차원 배치에서는 "
            "다를 수 있다. 참고 설계 'Bonemeal Farm 4k/h' 가 이 방식으로 시간당 4,000개를 낸다.",
            "층을 촘촘히 쌓으면 베드 위가 공기가 아니라 초목이 거의 자라지 않는다. "
            "수확물은 사실상 전부 이끼 블록이다 — 퇴비 65%짜리라 오히려 이쪽이 낫다.",
            "씨앗 칸 위를 막으면 뼛가루가 아예 작동하지 않는다. 절대 채우지 말 것.",
            "물을 먼저, 용암을 나중에 놓아야 한다. 반대로 하면 흑요석이 된다.",
            "돌을 계속 먹는다. 상류에 돌 생성기(litematic stonegen)가 필요하다.",
            "수거는 재생성용 물이 흐를 때 아이템을 동쪽으로 밀어주는 것에 기댄다. "
            "물이 닿지 않는 칸이 생기면 그 칸의 수확물은 남는다. "
            "베드 폭을 7보다 넓히지 말 것 (물은 수원에서 7칸까지 흐른다).",
        ],
        manual_items=[
            f"용암 양동이 {width * len(BED_ROWS) * layers - 1}개",
            f"물 양동이 {len(BED_ROWS) * layers}개",
            "이끼 블록 1개 (씨앗)", "뼛가루 (발사기 초기 장전)",
        ],
    )
