# -*- coding: utf-8 -*-
"""공정 등록부 — "유닛 1개가 시간당 무엇을 먹고 뱉는가".

수치는 engine.mechanics 의 상수에서 계산해 파생시킨다. 버전이 바뀌어
상수가 달라지면 여기 수치도 같이 따라간다.

verify:
  confirmed = 위키/릴리스 노트로 확인한 수치에서 직접 계산
  estimate  = 확인된 상수에서 유도했지만 실측으로 검증되지 않음
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from engine import mechanics as M                      # noqa: E402
from engine.chain import CONFIRMED, ESTIMATE, Process, Registry  # noqa: E402

# ---------------------------------------------------------------------------
# 컴포스터: 성공 7회 -> 뼛가루 1개. 성공 확률은 아이템마다 다르다.
# 호퍼로 먹이면 초당 2.5개가 들어가고, 레벨 7->8 로 넘어갈 때 20틱(1초)을 쉰다.
# ---------------------------------------------------------------------------
COMPOST_LEVELS = 7          # 위키 확인: 성공 7회면 뼛가루 1개
COMPOST_READY_DELAY_SEC = 1.0   # 위키 확인: 레벨 7 도달 후 20틱
COMPOST_CHANCE = {          # 위키 표
    "sugar_cane": 0.50, "cactus": 0.50, "melon_slice": 0.50,
    "kelp": 0.30, "pumpkin": 0.65, "wheat": 0.85, "hay_block": 0.85,
}
# 대나무는 퇴비화가 불가능하다 (위키 확인). 연료로만 쓴다.


def composter(item: str) -> Process:
    chance = COMPOST_CHANCE[item]
    items_per_bonemeal = COMPOST_LEVELS / chance
    feed_sec = items_per_bonemeal / M.HOPPER_ITEMS_PER_SEC
    cycle_sec = feed_sec + COMPOST_READY_DELAY_SEC
    bonemeal_per_hour = 3600.0 / cycle_sec
    return Process(
        id=f"composter_{item}",
        name=f"컴포스터 ({item})",
        unit="대",
        outputs={"bone_meal": bonemeal_per_hour},
        inputs={item: bonemeal_per_hour * items_per_bonemeal},
        verify=ESTIMATE,
        source=f"성공 7회/뼛가루 · {item} 성공률 {chance:.0%} → 평균 "
               f"{items_per_bonemeal:.1f}개 · 호퍼 급이 {M.HOPPER_ITEMS_PER_SEC}개/초 + 대기 1초",
        limits=(f"호퍼 1줄 급이가 상한이다. 한 대가 {items_per_bonemeal:.0f}개/뼛가루를 먹는다.",),
    )


# ---------------------------------------------------------------------------
# 제작 (제작기 Crafter). 실질 상한은 호퍼 급이 속도다.
# ---------------------------------------------------------------------------
CRAFTER_ITEMS_PER_HOUR = M.HOPPER_ITEMS_PER_SEC * 3600   # 9,000개/시간


def crafting(pid: str, name: str, inputs: dict[str, float], outputs: dict[str, float],
             source: str) -> Process:
    """inputs/outputs 는 '1회 제작' 비율. 호퍼 급이 속도로 스케일한다."""
    total_in = sum(inputs.values())
    batches = CRAFTER_ITEMS_PER_HOUR / total_in
    return Process(
        id=pid, name=name, unit="대",
        inputs={k: v * batches for k, v in inputs.items()},
        outputs={k: v * batches for k, v in outputs.items()},
        verify=ESTIMATE, source=source,
        limits=("제작기 자체 속도가 아니라 호퍼 급이(초당 2.5개)가 상한이다.",),
    )


COMPOST_CHANCE_MOSS = 0.65     # 위키: 이끼 블록 퇴비 성공률

def composter_for_harvest(pid: str, name: str, moss_per_harvest: float,
                          bonemeal_per_harvest: float, design: str | None,
                          note: str) -> Process:
    """수확물 '한 벌'을 퇴비통 처리량으로 환산한다.

    퇴비통 한 대의 상한은 호퍼 급이(초당 2.5개)와 레벨 7 도달 후 1초 대기다.
    이끼 블록 성공률 65% -> 뼛가루 1개당 평균 10.8개 투입.
    수확물 한 벌이 이끼 몇 개인지 알면 시간당 몇 벌을 처리하는지 나온다.
    """
    chance = COMPOST_CHANCE_MOSS
    items_per_bm = COMPOST_LEVELS / chance
    cycle = items_per_bm / M.HOPPER_ITEMS_PER_SEC + COMPOST_READY_DELAY_SEC
    bm_per_hour = 3600.0 / cycle
    items_per_hour = bm_per_hour * items_per_bm
    harvests_per_hour = items_per_hour / moss_per_harvest
    return Process(
        id=pid, name=name, unit="통",
        inputs={"moss_harvest": harvests_per_hour},
        outputs={"bone_meal": harvests_per_hour * bonemeal_per_harvest},
        design=design, design_param="bins" if design else None,
        verify=ESTIMATE,
        source=f"이끼 성공률 {chance:.0%} → 뼛가루당 {items_per_bm:.1f}개 투입 · "
               f"호퍼 급이 {M.HOPPER_ITEMS_PER_SEC}개/초 + 대기 1초 → 통당 "
               f"시간당 이끼 {items_per_hour:,.0f}개 = 수확물 {harvests_per_hour:.0f}벌. {note}",
        limits=("퇴비통은 위 호퍼로만 넣을 수 있다. 옆면은 통하지 않는다.",))


# ---------------------------------------------------------------------------
# 등록
# ---------------------------------------------------------------------------
def registry() -> Registry:
    r = Registry()

    # --- 1차 생산 ---------------------------------------------------------
    r.add(Process(
        id="sugarcane_farm", name="사탕수수 팜", unit="포기",
        outputs={"sugar_cane": M.column_crop_rate(1, "sugar_cane")},
        throttleable=False,
        design="sugarcane", design_param="length", max_units_per_build=64,
        verify=ESTIMATE,
        source=f"1칸 성장에 랜덤틱 {M.COLUMN_CROP_STAGES['sugar_cane']}회 "
               f"(randomTickSpeed {M.RANDOM_TICK_SPEED}) → 포기당 "
               f"{M.column_crop_rate(1, 'sugar_cane'):.2f}개/시간",
        limits=("한 채 64포기까지. 그 이상은 모듈을 나눈다.",
                "AFK 또는 /forceload 범위 안이어야 자란다."),
    ))
    r.add(Process(
        id="cactus_farm", name="선인장 팜", unit="포기",
        outputs={"cactus": M.column_crop_rate(1, "cactus")},
        throttleable=False,
        verify=ESTIMATE,
        source=f"1칸 성장에 랜덤틱 {M.COLUMN_CROP_STAGES['cactus']}회 → 포기당 "
               f"{M.column_crop_rate(1, 'cactus'):.2f}개/시간",
        limits=("옆 블록에 닿으면 자동 파괴되므로 레드스톤이 필요 없다.",),
    ))
    r.add(Process(
        id="skeleton_spawner", name="스켈레톤 스포너 팜", unit="스포너",
        outputs={"bone": 700.0 * 1.5, "arrow": 700.0 * 0.5},
        throttleable=False,
        verify=ESTIMATE,
        source="스포너 1개 시간당 약 700마리(추정) · 뼈 평균 1.5개 드롭",
        limits=("플레이어가 스포너 16블록 안에 있어야 작동한다.",),
    ))

    # --- 가공 -------------------------------------------------------------
    for item in ("sugar_cane", "cactus", "wheat", "kelp", "pumpkin"):
        r.add(composter(item))

    r.add(crafting("craft_bonemeal_from_bone", "뼈 → 뼛가루 (제작기)",
                   {"bone": 1}, {"bone_meal": 3},
                   "위키 확인: 뼈 1개 → 뼛가루 3개"))
    r.add(crafting("craft_bonemeal_from_boneblock", "뼈 블록 → 뼛가루 (제작기)",
                   {"bone_block": 1}, {"bone_meal": 9},
                   "위키 확인: 뼈 블록 1개 → 뼛가루 9개"))
    r.add(crafting("craft_paper", "사탕수수 → 종이 (제작기)",
                   {"sugar_cane": 3}, {"paper": 3},
                   "제작법: 사탕수수 3개 → 종이 3장"))
    r.add(crafting("craft_sugar", "사탕수수 → 설탕 (제작기)",
                   {"sugar_cane": 1}, {"sugar": 1},
                   "제작법: 사탕수수 1개 → 설탕 1개"))

    # --- 돌 라인 -----------------------------------------------------------
    # 용암은 오버월드에서 30틱마다 퍼진다 -> 생성칸 하나가 이론상 시간당 2,400개.
    LAVA_SPREAD_TICKS = 30
    cell_rate = 3600.0 / (LAVA_SPREAD_TICKS / M.TPS)
    r.add(Process(
        id="cobblegen", name="조약돌 생성기", unit="생성칸",
        outputs={"cobblestone": cell_rate},
        design="cobblegen", design_param="cells", max_units_per_build=8,
        throttleable=False, verify=ESTIMATE,
        source=f"오버월드 용암 확산 {LAVA_SPREAD_TICKS}틱 → 칸당 이론상 "
               f"{cell_rate:,.0f}개/시간",
        limits=("바닐라에는 자동 블록 파괴기가 없다. 실제 산출은 플레이어의 곡괭이질"
                "(초당 1~2개 = 시간당 3,600~7,200개)로 막힌다 — 칸을 늘려도 이 상한을 못 넘는다.",
                "물먹임 계단을 써야 용암 수원이 흑요석이 되지 않는다.")))

    # 제자리 돌 생성기: 조약돌이 아니라 '돌'을 직접 낸다 → 제련이 한 단 줄어든다
    r.add(Process(
        id="stonegen", name="제자리 돌 생성기", unit="생성칸",
        outputs={"stone": cell_rate},
        design="stonegen", design_param="cells", max_units_per_build=8,
        throttleable=False, verify=ESTIMATE,
        source=f"용암이 위에서 물로 흘러들면 물이 '돌'이 된다 · 용암 확산 "
               f"{LAVA_SPREAD_TICKS}틱 → 칸당 이론상 {cell_rate:,.0f}개/시간",
        limits=("조약돌 경로는 두 번 구워야 하지만 이쪽은 한 번이면 된다 → 연료 절반.",
                "채굴은 수동. 실제 상한은 곡괭이질(시간당 3,600~7,200개)이다.",
                "이끼 베드에 넣을 돌도 여기서 나온다 (조약돌은 이끼로 변환 안 됨).")))

    for pid, name, src, dst in (
            ("smelt_cobble_to_stone", "조약돌 → 돌 제련", "cobblestone", "stone"),
            ("smelt_stone_to_smooth", "돌 → 매끄러운 돌 제련", "stone", "smooth_stone")):
        r.add(Process(
            id=pid, name=name, unit="화로",
            inputs={src: M.FURNACE_ITEMS_PER_HOUR,
                    "fuel_smelt": M.FURNACE_ITEMS_PER_HOUR},
            outputs={dst: M.FURNACE_ITEMS_PER_HOUR},
            design="smelter", design_param="furnaces", max_units_per_build=16,
            verify=CONFIRMED,
            source=f"화로 1대 = 아이템당 {M.FURNACE_SMELT_TICKS}틱 → "
                   f"{M.FURNACE_ITEMS_PER_HOUR:,.0f}개/시간 · 석탄 1개당 8개",
            limits=(f"호퍼 1줄로는 화로 "
                    f"{int(M.HOPPER_ITEMS_PER_SEC * 3600 / M.FURNACE_ITEMS_PER_HOUR)}대까지. "
                    "그 이상은 원료 라인을 나눈다.",)))

    # --- 이끼 뼛가루 팜 (되먹임 고리) --------------------------------------
    # 뼛가루 -> 이끼 -> 퇴비통 -> 뼛가루. 솔버가 고정점 반복으로 푼다.
    # 'moss_harvest' 1단위 = 뼛가루 1개를 썼을 때 나오는 수확물 한 벌
    # (이끼 27개 + 초목 16개).
    from engine.designs.mossbed import yields as _moss_yields
    my = _moss_yields()
    CYCLES_PER_HOUR = 30.0     # 뼛가루 발사 -> 괭이질 -> 물 세척 -> 돌 보충 1회전
    r.add(Process(
        id="mossbed", name="이끼 베드", unit="베드",
        inputs={"bone_meal": CYCLES_PER_HOUR,
                "stone": my["stone_consumed"] * CYCLES_PER_HOUR},
        outputs={"moss_harvest": CYCLES_PER_HOUR},
        design="mossbed", design_param=None, max_units_per_build=1,
        verify=ESTIMATE,
        source=f"뼛가루 1개 → 이끼 {my['counts']['moss_block']:.0f}개 + 초목 "
               f"{sum(v for k, v in my['counts'].items() if k != 'moss_block'):.0f}개, "
               f"돌 {my['stone_consumed']:.0f}칸 소비 · 회전 {CYCLES_PER_HOUR:.0f}회/시간 가정",
        limits=("이끼 수확이 수동이라 회전수가 산출을 좌우한다. 30회/시간은 가정값이다.",
                "베드는 '돌'이어야 한다. 조약돌은 이끼로 변환되지 않는다.",
                "참고 설계 'Bonemeal Farm 4k/h' 는 다층 베드 + 피스톤 자동 수확으로 "
                "시간당 4,000개를 낸다. 이 설계는 거기까지 가지 못했다.")))

    # 다층 자동 이끼 베드는 제자리 돌 재생성(용암이 위에서 물로)을 내장해서
    # 돌을 밖에서 받지 않는다. 용암 수원과 물 수원은 소모되지 않으므로
    # 사실상 무료로 돌이 다시 채워진다. 그래서 입력이 뼛가루뿐이다.
    from engine.designs.mossbed_auto import yields as _auto_yields
    ay = _auto_yields()
    AUTO_CYCLES_PER_HOUR = 360.0    # 뼛가루 발사 -> 피스톤 -> 물 침수 -> 용암 재생성 1회전
    r.add(Process(
        id="mossbed_auto", name="다층 자동 이끼 베드", unit="베드",
        inputs={"bone_meal": AUTO_CYCLES_PER_HOUR},
        outputs={"moss_harvest": AUTO_CYCLES_PER_HOUR},
        design="mossbed_auto", design_param=None, max_units_per_build=1,
        verify=ESTIMATE,
        source=f"베드 {ay['cells']}칸 · 평평한 7x7 변환율(27/49)을 다층에 적용해 "
               f"뼛가루당 이끼 약 {ay['moss_est']:.0f}개 (추정) · "
               f"회전 {AUTO_CYCLES_PER_HOUR:.0f}회/시간 가정",
        limits=("제자리 돌 재생성을 내장해 돌을 밖에서 받지 않는다.",
                "회전수는 가정값이다. 참고 설계는 시간당 뼛가루 4,000개를 낸다.")))

    r.add(composter_for_harvest(
        "composter_moss_auto", "퇴비통 (다층 베드 수확물)",
        ay["moss_est"], ay["bonemeal_est"], "composterbank",
        "층을 촘촘히 쌓아 초목이 거의 없어 수확물이 사실상 전부 이끼 블록이다."))

    r.add(composter_for_harvest(
        "composter_moss_harvest", "퇴비통 (이끼 + 초목 전량)",
        my["counts"]["moss_block"], my["with_moss_bonemeal"], None,
        "이끼 블록을 반드시 함께 넣어야 한다. 빼면 고리가 순손실이 된다."))

    r.add(Process(
        id="composter_vegetation_only", name="퇴비통 (초목만 · 이끼는 보관)", unit="통",
        inputs={"moss_harvest": 1.0},
        outputs={"bone_meal": my["veg_only_bonemeal"], "moss_block": my["stone_consumed"]},
        verify=ESTIMATE,
        source=f"초목만 퇴비화 = 뼛가루 {my['veg_only_bonemeal']:.2f}개 "
               f"(이끼 블록은 자재로 보관)",
        limits=("뼛가루 고리로는 순손실(1개 미만)이라 발산한다. "
                "이끼 블록 자체가 목적일 때만 쓸 것.",)))

    # --- 켈프 연료 라인 (되먹임 고리) ----------------------------------------
    # fuel_smelt = '아이템 1개를 제련할 수 있는 연료' 단위.
    # 말린 켈프 블록은 4,000틱 = 20개 제련. 만드는 데 켈프 9개를 굽느라 9개분을
    # 되먹으므로 순 11개분 (위키가 명시한 수치와 일치).
    KELP_GROWTH_TICKS = 9752.0      # 위키: 14%/랜덤틱 → 평균 9,752틱
    kelp_per_plant_hour = 3600.0 / (KELP_GROWTH_TICKS / M.TPS)
    r.add(Process(
        id="kelp_farm", name="켈프 팜", unit="포기",
        outputs={"kelp": kelp_per_plant_hour},
        design="kelpfarm", design_param="columns", max_units_per_build=64,
        throttleable=False, verify=ESTIMATE,
        source=f"켈프 성장 14%/랜덤틱 → 평균 {KELP_GROWTH_TICKS:,.0f}틱 "
               f"({KELP_GROWTH_TICKS / M.TPS:.0f}초) → 포기당 "
               f"{kelp_per_plant_hour:.2f}개/시간",
        limits=("물기둥 안에서만 자란다. 관측기+피스톤으로 자란 칸을 끊는다.",)))

    r.add(Process(
        id="cobblegen_tnt", name="TNT 복제 조약돌 생성기", unit="기",
        outputs={"cobblestone": 27000.0},
        design="cobblegen_tnt", design_param="units", max_units_per_build=4,
        throttleable=False, verify=ESTIMATE,
        source="참고 설계 '2.7万刷石机' 표기 수치 (실측 아님)",
        limits=("TNT 복제는 버그성 메커니즘이라 서버에 따라 막혀 있을 수 있다.",
                "채굴이 완전 자동이다 — 손으로 캘 필요가 없다.")))

    r.add(Process(
        id="kelp_bonemeal", name="뼛가루 켈프 팜", unit="기둥",
        inputs={"bone_meal": 3600.0}, outputs={"kelp": 3600.0},
        design="kelpfarm_bonemeal", design_param="columns", max_units_per_build=16,
        verify=ESTIMATE,
        source="위키 확인: 뼛가루 1개가 켈프를 1칸 자라게 한다 → 1:1",
        limits=("성장 대기가 없어 산출량은 뼛가루 공급량이 정한다.",
                "기둥 수는 클럭 속도상 여유가 크다 — 한 줄이면 충분하다.")))

    r.add(Process(
        id="smelt_kelp_to_dried", name="켈프 → 말린 켈프 제련", unit="화로",
        inputs={"kelp": M.FURNACE_ITEMS_PER_HOUR,
                "fuel_smelt": M.FURNACE_ITEMS_PER_HOUR},
        outputs={"dried_kelp": M.FURNACE_ITEMS_PER_HOUR},
        design="smelter", design_param="furnaces", max_units_per_build=16,
        verify=CONFIRMED,
        source=f"화로 1대 {M.FURNACE_ITEMS_PER_HOUR:,.0f}개/시간"))

    r.add(crafting("craft_dried_kelp_block", "말린 켈프 → 블록 (제작기)",
                   {"dried_kelp": 9}, {"dried_kelp_block": 1},
                   "위키 확인: 말린 켈프 9개 → 블록 1개"))

    r.add(Process(
        id="burn_dried_kelp_block", name="말린 켈프 블록 연소", unit="투입구",
        inputs={"dried_kelp_block": 1.0},
        outputs={"fuel_smelt": 20.0},
        verify=CONFIRMED,
        source="위키 확인: 말린 켈프 블록 4,000틱 = 20개 제련 (석탄 8개의 2.5배). "
               "블록을 만드는 데 켈프 9개를 굽느라 9개분을 되먹으므로 순 11개분.",
        limits=("연료는 고리다. 켈프를 말리는 화로도 같은 연료를 먹는다.",)))

    r.add(Process(
        id="burn_coal", name="석탄 연소", unit="투입구",
        inputs={"coal": 1.0}, outputs={"fuel_smelt": 8.0},
        verify=CONFIRMED,
        source="위키 확인: 석탄 1개 = 1,600틱 = 8개 제련",
        limits=("석탄은 캐야 한다. 자동 공급 공정이 없다.",)))

    r.add(Process(
        id="smelt_cactus_green", name="선인장 제련 → 초록 염료", unit="화로",
        inputs={"cactus": M.FURNACE_ITEMS_PER_HOUR,
                "fuel_smelt": M.FURNACE_ITEMS_PER_HOUR},
        outputs={"green_dye": M.FURNACE_ITEMS_PER_HOUR},
        verify=CONFIRMED,
        source=f"화로 1대 = 아이템당 {M.FURNACE_SMELT_TICKS}틱 → "
               f"{M.FURNACE_ITEMS_PER_HOUR:,.0f}개/시간 · 석탄 1개당 8개 제련",
        limits=(f"호퍼 1줄(초당 {M.HOPPER_ITEMS_PER_SEC}개)로는 화로 "
                f"{int(M.HOPPER_ITEMS_PER_SEC * 3600 / M.FURNACE_ITEMS_PER_HOUR)}대까지가 한계.",),
    ))
    return r


REGISTRY = registry()
