"""게임 메커니즘 상수 및 계산식.

여기 있는 수치는 26.2(Chaos Cubed) 기준이며, 출처가 위키/스냅샷 노트로
확인된 것만 CONFIRMED, 커뮤니티 통설/실측 추정치는 ESTIMATE로 표시한다.
설계 엔진은 이 모듈만 참조하므로, 버전이 바뀌면 여기만 고치면 된다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

GAME_VERSION = "26.2"
GAME_VERSION_NAME = "Chaos Cubed"
GAME_VERSION_DATE = "2026-06-16"

TPS = 20  # tick per second (지연 없을 때)

CONFIRMED = "confirmed"    # 위키/공식 릴리스 노트로 확인
ESTIMATE = "estimate"      # 실측/커뮤니티 통설 기반 추정


@dataclass(frozen=True)
class Fact:
    """검증 상태가 붙은 수치 하나."""
    key: str
    value: float
    unit: str
    status: str
    note: str = ""

    def __str__(self) -> str:
        mark = "O" if self.status == CONFIRMED else "~"
        return f"[{mark}] {self.key} = {self.value}{self.unit}  {self.note}"


# ---------------------------------------------------------------------------
# 1. 아이템 수송
# ---------------------------------------------------------------------------
HOPPER_COOLDOWN_TICKS = 8          # 호퍼가 아이템 1개를 옮기는 주기
HOPPER_ITEMS_PER_SEC = TPS / HOPPER_COOLDOWN_TICKS      # = 2.5
HOPPER_MINECART_PICKUP_PER_SEC = 20.0                   # 레일 위 이동 중 픽업(추정)
WATER_FLOW_RANGE = 7               # 수원에서 평지로 흐르는 거리(수원 포함 8칸)
ITEM_DESPAWN_SEC = 300             # 아이템 엔티티 소멸 시간


def hopper_throughput(hopper_count: int = 1) -> float:
    """병렬 호퍼 n개의 초당 처리량(개/초)."""
    return HOPPER_ITEMS_PER_SEC * max(0, hopper_count)


def hopper_line_required(items_per_hour: float) -> int:
    """시간당 산출량을 병목 없이 받으려면 필요한 병렬 호퍼 수."""
    if items_per_hour <= 0:
        return 0
    per_sec = items_per_hour / 3600.0
    return max(1, -(-int(per_sec * 100) // int(HOPPER_ITEMS_PER_SEC * 100)))


# ---------------------------------------------------------------------------
# 2. 낙하 데미지 / 처치
# ---------------------------------------------------------------------------
FALL_DAMAGE_FREE_BLOCKS = 3        # 데미지 = floor(낙하거리) - 3


def fall_damage(distance: float) -> int:
    """낙하 거리(블록)에 대한 데미지(하트 반칸 단위 = HP)."""
    return max(0, int(distance) - FALL_DAMAGE_FREE_BLOCKS)


def drop_height_for(hp: int, leave_alive: bool = False) -> int:
    """체력 hp인 몹을 죽이거나(기본) 1HP만 남기려면 필요한 낙하 높이."""
    target_damage = hp - 1 if leave_alive else hp
    return target_damage + FALL_DAMAGE_FREE_BLOCKS


MOB_HP = {
    "zombie": 20, "skeleton": 20, "creeper": 20, "spider": 16, "cave_spider": 12,
    "enderman": 40, "witch": 26, "drowned": 20, "husk": 20, "stray": 20,
    "blaze": 20, "wither_skeleton": 20, "piglin": 16, "hoglin": 40,
    "magma_cube_large": 16, "zombified_piglin": 20, "guardian": 30,
    "iron_golem": 100, "villager": 20, "pillager": 24, "vindicator": 24,
    "evoker": 24, "ravager": 100, "slime_large": 16, "shulker": 30,
    "sulfur_cube_large": 16,
}

# 낙하로 즉사시킬 수 없는(체력이 너무 높거나 낙하 면역) 몹
FALL_IMMUNE = {"iron_golem_partial", "shulker", "blaze", "ghast", "wither", "ender_dragon"}


# ---------------------------------------------------------------------------
# 3. 몹 스폰
# ---------------------------------------------------------------------------
MOB_CAP = {                  # 플레이어당 기본 상한(스폰 카테고리별)
    "monster": 70, "creature": 10, "ambient": 15,
    "axolotls": 5, "underground_water_creature": 5,
    "water_creature": 5, "water_ambient": 20,
}
SPAWN_CHUNK_AREA = 289       # 17x17 청크 = 스폰 대상 청크 수
MOB_SPAWN_MIN_DISTANCE = 24  # 플레이어로부터 이 거리 안에서는 자연 스폰 없음
MOB_DESPAWN_INSTANT = 128    # 이 거리 밖 몹은 즉시 소멸
MOB_DESPAWN_RANDOM = 32      # 32~128칸은 확률 소멸
HOSTILE_SPAWN_BLOCK_LIGHT = 0  # 1.18+ : 블록광 0에서만 적대 몹 스폰

# 1.21.9에서 스폰 청크가 삭제되어, 상시 로딩은 /forceload 로만 가능.
SPAWN_CHUNKS_REMOVED_IN = "1.21.9"


def effective_mob_cap(category: str, loaded_chunks: int, players: int = 1) -> float:
    """로딩된 청크 수에 비례해 줄어드는 실효 몹캡."""
    base = MOB_CAP.get(category, 70)
    return base * players * min(1.0, loaded_chunks / SPAWN_CHUNK_AREA)


def spawn_rate_estimate(spawnable_blocks: int, share_of_cap: float = 0.9,
                        cycle_sec: float = 5.0, cap: float = 70.0) -> float:
    """어두운 플랫폼 팜의 시간당 몹 스폰 수 추정(ESTIMATE).

    실제 스폰은 매 틱 청크별 시도로 결정되지만, 실전 설계에서는
    "몹캡을 얼마나 독점하는가 x 몹캡이 다시 채워지는 주기"로 근사한다.
    spawnable_blocks 는 유효 스폰 가능 블록 수(어둡고 지붕이 있는 바닥).
    """
    if spawnable_blocks <= 0:
        return 0.0
    saturation = min(1.0, spawnable_blocks / 1500.0)  # 1500칸이면 사실상 포화
    per_cycle = cap * share_of_cap * saturation
    return per_cycle * (3600.0 / cycle_sec)


# ---------------------------------------------------------------------------
# 4. 가공 설비
# ---------------------------------------------------------------------------
FURNACE_SMELT_TICKS = 200          # 아이템 1개 제련 = 10초
FURNACE_ITEMS_PER_HOUR = 3600 / (FURNACE_SMELT_TICKS / TPS)   # = 360
FUEL_BURN_TICKS = {"coal": 1600, "charcoal": 1600, "blaze_rod": 2400,
                   "lava_bucket": 20000, "dried_kelp_block": 4000, "bamboo": 50}


def furnaces_needed(items_per_hour: float) -> int:
    """시간당 유입량을 밀리지 않고 굽는 데 필요한 화로 수."""
    if items_per_hour <= 0:
        return 0
    return max(1, int(-(-items_per_hour // FURNACE_ITEMS_PER_HOUR)))


def fuel_items_needed(items_smelted: int, fuel: str = "coal") -> float:
    """제련량에 필요한 연료 개수."""
    burn = FUEL_BURN_TICKS.get(fuel, 1600)
    return items_smelted * FURNACE_SMELT_TICKS / burn


# ---------------------------------------------------------------------------
# 5. 작물 / 성장
# ---------------------------------------------------------------------------
RANDOM_TICK_SPEED = 3              # 청크 섹션(16^3)당 매 틱 랜덤틱 횟수
RANDOM_TICKS_PER_BLOCK_PER_SEC = TPS * RANDOM_TICK_SPEED / 4096


def growth_time_sec(stages: int, chance: float = 1.0) -> float:
    """랜덤틱 기반 작물이 stages 단계를 자라는 데 걸리는 평균 시간(초)."""
    if chance <= 0:
        return float("inf")
    return stages / (RANDOM_TICKS_PER_BLOCK_PER_SEC * chance)


COLUMN_CROP_STAGES = {   # 사탕수수/대나무류: 한 칸 자라는 데 필요한 랜덤틱 수
    "sugar_cane": 16, "cactus": 16, "bamboo": 1, "kelp": 1, "chorus": 1,
}


def column_crop_rate(plants: int, crop: str = "sugar_cane") -> float:
    """관측기 자동 수확 기둥 작물의 시간당 산출(개/시간) 추정."""
    stages = COLUMN_CROP_STAGES.get(crop, 16)
    per_plant_per_hour = 3600.0 / growth_time_sec(stages)
    return plants * per_plant_per_hour


# ---------------------------------------------------------------------------
# 6. 요약 출력
# ---------------------------------------------------------------------------
def fact_sheet() -> list[Fact]:
    return [
        Fact("hopper_throughput", HOPPER_ITEMS_PER_SEC, "개/초", CONFIRMED, "호퍼 쿨다운 8틱"),
        Fact("water_flow_range", WATER_FLOW_RANGE, "블록", CONFIRMED, "수원 포함 8칸"),
        Fact("fall_damage_free", FALL_DAMAGE_FREE_BLOCKS, "블록", CONFIRMED, "데미지=거리-3"),
        Fact("kill_drop_20hp", drop_height_for(20), "블록", CONFIRMED, "좀비/스켈레톤 즉사"),
        Fact("xp_drop_20hp", drop_height_for(20, leave_alive=True), "블록", CONFIRMED, "1HP 남김(경험치용)"),
        Fact("monster_cap", MOB_CAP["monster"], "마리", CONFIRMED, "플레이어당, 청크수 비례"),
        Fact("spawn_min_distance", MOB_SPAWN_MIN_DISTANCE, "블록", CONFIRMED, "AFK 위치 산정 기준"),
        Fact("despawn_instant", MOB_DESPAWN_INSTANT, "블록", CONFIRMED, "이 밖은 즉시 소멸"),
        Fact("hostile_block_light", HOSTILE_SPAWN_BLOCK_LIGHT, "레벨", CONFIRMED, "1.18+ 블록광 0 필수"),
        Fact("furnace_rate", FURNACE_ITEMS_PER_HOUR, "개/시간", CONFIRMED, "화로 1대"),
        Fact("random_tick_speed", RANDOM_TICK_SPEED, "회/섹션/틱", CONFIRMED, "기본 게임룰"),
    ]


if __name__ == "__main__":
    print(f"Minecraft {GAME_VERSION} ({GAME_VERSION_NAME}, {GAME_VERSION_DATE}) 기준")
    for f in fact_sheet():
        print(" ", f)
