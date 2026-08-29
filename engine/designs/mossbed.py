"""이끼 베드 (뼛가루 팜의 생산부).

원리 (위키 확인):
  · 이끼 블록에 뼛가루를 쓰면 모서리를 뺀 7x11x7 부피 안의 변환 가능 블록이
    이끼로 바뀐다. 평평한 7x7 격자 기준 뼛가루 1개당 평균 이끼 27개.
  · 변환 가능 블록: 돌, 심층암, 안산암, 섬록암, 화강암, 응회암, 흙 계열, 진흙 등.
    조약돌은 변환되지 않는다 -> 조약돌 팜의 산출을 화로에 한 번 구워 '돌'로 만들어야 한다.
  · 변환된 블록의 60% 에 초목이 자란다.
    짧은 풀 52.08% / 이끼 양탄자 26.04% / 큰 풀 10.42% / 진달래 7.29% / 꽃 진달래 4.17%
  · 뼛가루가 작동하려면 대상 이끼 블록의 '바로 위가 공기'여야 한다.
    그래서 베드 위(Y=+1)에는 아무것도 놓지 않는다. 피스톤도 물도 상시로는 못 둔다.

수확:
  이끼 블록은 돌 괭이 이상이면 0.05초에 즉시 부서진다. 베드를 괭이로 한 번 훑으면
  이끼와 초목이 전부 아이템이 된다. 그 다음은 전부 자동이다 —
  발사기가 물을 뿌려 아이템을 호퍼 줄로 밀어넣고, 물을 다시 회수한다.

단면도 (Y 기준):
  Y=+1  공기 (초목이 자라는 칸 · 물 세척이 지나가는 칸)
  Y= 0  7x7 돌 베드, 중앙 한 칸만 이끼
  Y=-1  중앙에 위를 향한 발사기(뼛가루) · 나머지는 바닥
"""
from __future__ import annotations

from ..blocks import (EAST, GLASS, MOSS_BLOCK, SOUTH, STONE, UP, chest,
                      dispenser, hopper)
from ..schematic import Schematic
from . import Design

# 위키 수치
MOSS_PER_BONEMEAL = 27.0        # 평평한 7x7 기준 평균 이끼 블록 수
VEGETATION_RATE = 0.60          # 변환된 블록 중 초목이 자라는 비율
VEGETATION_MIX = {              # 초목 분포
    "short_grass": 0.5208, "moss_carpet": 0.2604, "tall_grass": 0.1042,
    "azalea": 0.0729, "flowering_azalea": 0.0417,
}
COMPOST_CHANCE = {              # 퇴비 성공률
    "moss_block": 0.65, "short_grass": 0.30, "moss_carpet": 0.30,
    "tall_grass": 0.50, "azalea": 0.65, "flowering_azalea": 0.85,
}
COMPOST_LEVELS_PER_BONEMEAL = 7


def yields() -> dict:
    """뼛가루 1개를 썼을 때의 산출과 퇴비 환산."""
    plants = MOSS_PER_BONEMEAL * VEGETATION_RATE
    counts = {"moss_block": MOSS_PER_BONEMEAL}
    for name, share in VEGETATION_MIX.items():
        counts[name] = plants * share
    veg_levels = sum(n * COMPOST_CHANCE[k] for k, n in counts.items() if k != "moss_block")
    moss_levels = counts["moss_block"] * COMPOST_CHANCE["moss_block"]
    total = veg_levels + moss_levels
    return {
        "counts": counts,
        "stone_consumed": MOSS_PER_BONEMEAL,
        "veg_only_bonemeal": veg_levels / COMPOST_LEVELS_PER_BONEMEAL,
        "with_moss_bonemeal": total / COMPOST_LEVELS_PER_BONEMEAL,
    }


def build(size: int = 7, structure=STONE) -> Design:
    if size < 3 or size % 2 == 0:
        raise ValueError("size 는 3 이상의 홀수여야 한다 (중앙에 이끼 씨앗을 둔다)")
    c = size // 2
    y = yields()

    s = Schematic(
        name=f"mossbed_{size}",
        description=f"이끼 베드 {size}x{size} · 뼛가루 발사기 + 물 세척 수거 "
                    f"(뼛가루 1개당 순 +{y['with_moss_bonemeal'] - 1:.1f}개)",
    )

    for x in range(size):
        for z in range(size):
            s.set(x, -1, z, structure)                      # 바닥
            s.set(x, 0, z, structure)                       # 변환될 돌 베드
    s.set(c, 0, c, MOSS_BLOCK)                              # 이끼 씨앗 (중앙)
    s.set(c, -1, c, dispenser(UP))                          # 뼛가루 발사기

    # 서쪽 끝: 물 양동이 발사기 (세척용). Y=+1 에서 동쪽으로 물을 뿌린다.
    for z in range(size):
        s.set(-1, 0, z, structure)
        s.set(-1, 1, z, dispenser(EAST))
        s.set(-1, -1, z, structure)

    # 동쪽 끝: 수거 호퍼 줄 (Y=0). 물에 밀려온 아이템이 여기로 떨어진다.
    for z in range(size):
        s.set(size, 0, z, hopper(SOUTH))
        s.set(size, -1, z, structure)

    # 남북 벽 (물과 아이템 이탈 방지) — 상자보다 먼저 그려야 덮이지 않는다
    for x in range(-1, size + 1):
        for zz in (-1, size):
            s.set(x, 0, zz, structure)
            s.set(x, 1, zz, structure)
            s.set(x, -1, zz, structure)

    # 호퍼 줄 끝의 수거 상자 (벽 다음에 놓아 덮이지 않게)
    s.set(size, 0, size, chest(SOUTH))
    s.set(size, 1, size, GLASS)                             # 상자 위는 불투명 금지

    s.note("베드 바로 위(Y=+1)는 반드시 비워 둔다. "
           "뼛가루는 '이끼 위가 공기'일 때만 작동한다 — 피스톤도 물도 상시로 두면 안 된다.")
    s.note("베드는 '돌'이어야 한다. 조약돌은 이끼로 변환되지 않는다.")
    s.note(f"뼛가루 1개 → 이끼 약 {MOSS_PER_BONEMEAL:.0f}개 + 초목 약 "
           f"{MOSS_PER_BONEMEAL * VEGETATION_RATE:.0f}개, 돌 {MOSS_PER_BONEMEAL:.0f}칸 소비")

    return Design(
        schematic=s,
        principle=f"돌 베드 중앙의 이끼에 발사기가 뼛가루를 사용 → 주변 돌 약 "
                  f"{MOSS_PER_BONEMEAL:.0f}칸이 이끼로 바뀌고 60%에 초목이 자람 → "
                  f"괭이로 훑어 수확 → 물 세척으로 호퍼에 몰아넣음 → 퇴비통으로",
        circuit=[
            "1. 발사기(중앙 Y=-1, 위 방향)가 뼛가루를 이끼 블록에 사용",
            "2. 모서리를 뺀 7x11x7 안의 돌이 이끼로 변환 (평평한 7x7 기준 평균 27칸)",
            "3. 변환된 이끼의 60% 위에 초목 생성",
            "4. 괭이로 베드를 훑어 이끼 + 초목을 전부 아이템으로",
            "5. 서쪽 물 발사기 작동 → 아이템이 동쪽 호퍼 줄로 밀려감",
            "6. 물 발사기를 한 번 더 작동시켜 물을 회수 (베드 위는 다시 공기여야 한다)",
            "7. 베드에 돌을 다시 채우고 반복",
        ],
        steps=[
            f"1) {size}x{size} 돌 베드를 깐다. 조약돌이 아니라 반드시 '돌'이어야 한다.",
            f"2) 중앙 (x={c}, z={c}) 한 칸만 이끼 블록으로 바꾼다.",
            f"3) 그 바로 아래(Y=-1)에 위를 향한 발사기를 넣고 뼛가루를 채운다.",
            "4) 서쪽 끝 Y=+1 에 동쪽을 향한 발사기 줄을 놓고 물 양동이를 넣는다.",
            "5) 동쪽 끝 Y=0 에 남쪽을 향한 호퍼 줄을 깔고 끝에 상자를 놓는다.",
            "6) 베드 위(Y=+1)에는 아무것도 두지 않는다. 뼛가루 조건이 깨진다.",
            "7) 뼛가루 발사 → 괭이로 훑기 → 물 세척 → 물 회수 → 돌 보충. 이 순서를 반복한다.",
        ],
        rate=f"뼛가루 1개 → 퇴비 환산 약 {y['with_moss_bonemeal']:.2f}개 "
             f"(순 +{y['with_moss_bonemeal'] - 1:.2f}개), 돌 {y['stone_consumed']:.0f}칸 소비. "
             f"속도는 괭이질 주기에 달려 있다.",
        warnings=[
            f"초목만 퇴비화하면 뼛가루가 {y['veg_only_bonemeal']:.2f}개밖에 안 나와 "
            f"오히려 손해다. 이끼 블록(퇴비 65%)을 반드시 같이 넣어야 "
            f"{y['with_moss_bonemeal']:.2f}개가 되어 순이익이 난다.",
            "베드는 '돌'이다. 조약돌은 이끼로 변환되지 않으므로 "
            "조약돌 팜 산출을 화로에 한 번 구워서 써야 한다.",
            "수확한 만큼 돌이 사라진다. 돌 공급이 끊기면 팜도 멈춘다.",
            "이끼 수확은 수동이다. 돌 괭이 이상이면 0.05초에 즉시 부서지므로 "
            "훑는 데 오래 걸리지는 않는다. 완전 자동화는 플라잉 머신이 필요한데 "
            "이 설계에는 넣지 않았다 (검증하지 못했다).",
            "물 세척 후 반드시 물을 회수해야 한다. 베드 위에 물이 남아 있으면 "
            "다음 뼛가루가 작동하지 않는다.",
        ],
        manual_items=[
            f"뼛가루 (발사기 초기 장전)",
            f"물 양동이 {size}개 (세척 발사기용)",
            "돌 괭이 이상 (이끼 즉시 파괴)",
        ],
    )
