"""작동 원리 -> 아키타입 해석기.

이 파일이 이 프로젝트의 핵심이다.
"뭐가 산출되고 / 어떻게 옮기고 / 어떻게 처리하고 / 어떻게 담는가" 네 가지만 주면
적절한 아키타입과 파라미터를 고르고, '왜 그렇게 골랐는지'까지 남긴다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import mechanics as M

# 허용 값 (자유 서술이 아니라 열거형이어야 기계가 설계할 수 있다)
SOURCES = {
    "natural_spawn": "어둠/바이옴 조건에 따른 몹 자연 스폰",
    "spawner": "스포너 블록의 강제 스폰",
    "structure_spawn": "구조물 경계 안에서만 일어나는 스폰(요새/신전/오두막/전초기지)",
    "growth_column": "위로 자라는 기둥형 식물(사탕수수/대나무/선인장/다시마/코러스)",
    "growth_farmland": "경작지 위 단계 성장 작물(밀/당근/감자/비트/수박/호박)",
    "breeding": "동물 번식으로 개체 증식",
    "villager": "주민 직업/공포/번식 메커니즘",
    "generation": "블록 물리로 새 블록이 생기는 것(조약돌/돌/현무암/얼음/눈)",
    "bartering": "피글린 물물교환",
}
TRANSPORTS = {
    "water": "물길 (오버월드 전용, 네더에서는 증발)",
    "gravity": "낙하/중력만으로 이동",
    "piston": "피스톤/플라잉 머신으로 밀어내기",
    "minecart": "호퍼 미니카트 회수 라인",
    "mob_ai": "몹 AI 유인(유인체/경로 유도)",
    "none": "이송 없음(제자리 수확)",
}
PROCESSES = {
    "fall": "낙하 데미지 처치",
    "fall_then_hit": "낙하로 1HP 남기고 플레이어 직접 타격(드롭/경험치 극대화)",
    "lava": "용암 블레이드 처치",
    "observer_cut": "관측기 감지 + 피스톤 절단",
    "piston_break": "피스톤으로 블록 파괴",
    "smelt": "화로 제련",
    "trade": "주민 거래",
    "manual": "플레이어 직접 처리",
}
COLLECTS = {"hopper": "호퍼 라인", "minecart": "호퍼 미니카트", "water": "물길 집결 후 호퍼", "none": "없음"}


@dataclass
class Principle:
    source: str
    process: str
    transport: str = "water"
    collect: str = "hopper"
    target: str = "zombie"
    dimension: str = "overworld"
    scale: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Principle":
        unknown = set(d) - {"source", "process", "transport", "collect", "target", "dimension", "scale"}
        if unknown:
            raise ValueError(f"알 수 없는 키: {sorted(unknown)}")
        p = cls(**d)
        for name, table in (("source", SOURCES), ("process", PROCESSES),
                            ("transport", TRANSPORTS), ("collect", COLLECTS)):
            v = getattr(p, name)
            if v not in table:
                raise ValueError(f"{name}={v!r} 는 허용되지 않음. 가능: {', '.join(sorted(table))}")
        if p.dimension not in ("overworld", "nether", "end"):
            raise ValueError("dimension 은 overworld/nether/end 중 하나")
        return p


@dataclass
class Resolution:
    archetype: str
    params: dict
    reasoning: list[str]
    warnings: list[str]


def resolve(p: Principle) -> Resolution:
    """원리 -> 아키타입 + 파라미터. 판단 근거를 전부 남긴다."""
    why: list[str] = []
    warn: list[str] = []
    params: dict = dict(p.scale)

    # --- 물리적 모순 먼저 잡는다 ---------------------------------------
    if p.dimension == "nether" and p.transport == "water":
        warn.append("네더에서는 물이 즉시 증발한다 → transport를 piston/gravity/mob_ai 로 바꿔야 한다.")
    hp = M.MOB_HP.get(p.target)
    if p.process in ("fall", "fall_then_hit") and p.target in M.FALL_IMMUNE:
        warn.append(f"{p.target} 은(는) 낙하 데미지가 통하지 않는다 → lava 또는 manual 로 바꿔야 한다.")

    # --- 낙하 높이 자동 계산 -------------------------------------------
    if p.process in ("fall", "fall_then_hit") and hp:
        leave = p.process == "fall_then_hit"
        drop = M.drop_height_for(hp, leave_alive=leave)
        params.setdefault("drop", drop)
        params["xp"] = leave
        why.append(f"{p.target} 체력 {hp} → 낙하 데미지 공식(거리-3)으로 "
                   f"{'1HP 남기려면' if leave else '즉사시키려면'} {drop}블록 필요")

    # --- 아키타입 선택 --------------------------------------------------
    if p.source == "spawner":
        arch = "spawner_box"
        params.setdefault("mob", p.target)
        why.append("스포너는 강제 스폰이라 면적이 아니라 활성 거리(16블록)가 변수 → spawner_box")
    elif p.source in ("natural_spawn", "structure_spawn"):
        if p.dimension == "end":
            arch = "enderman_platform"
            why.append("엔드 자연 스폰은 본섬 128블록 밖 허공 플랫폼이 정석 → enderman_platform")
        elif p.dimension == "nether":
            arch = "nether_platform"
            params.setdefault("kind", "gold" if p.target in ("zombified_piglin", "piglin") else p.target)
            why.append("네더 스폰은 물 이송이 불가하고 스폰 차단 범위가 성패를 가름 → nether_platform")
        else:
            arch = "mob_platform_tower"
            params.setdefault("mob", p.target)
            why.append("오버월드 자연 스폰은 '어두운 면적 확보 + 몹캡 독점'이 핵심 → mob_platform_tower")
        if p.source == "structure_spawn":
            warn.append("구조물 한정 스폰이다. 구조물 경계(bounding box) 밖에 지으면 스폰이 0이 된다. "
                        "좌표를 먼저 확정할 것.")
    elif p.source == "growth_column":
        arch = "column_crop"
        params.setdefault("crop", p.target)
        why.append("기둥 성장은 관측기 1개가 성장 1칸을 감지하는 구조 → column_crop")
    elif p.source == "growth_farmland":
        arch = "crop_piston_harvester"
        params.setdefault("crop", p.target)
        why.append("경작지 작물은 면적 x 랜덤틱이 산출을 결정 → crop_piston_harvester")
    elif p.source == "breeding":
        arch = "animal_farm"
        params.setdefault("animal", p.target)
        params.setdefault("cook", p.process == "lava")
        why.append("번식형은 '성체/새끼 분리'가 설계의 전부 → animal_farm")
    elif p.source == "villager":
        if p.process == "trade":
            arch = "villager_hall"
            why.append("거래 목적이면 스폰이 아니라 부스 수가 변수 → villager_hall")
        else:
            arch = "iron_golem_farm"
            why.append("주민 공포 기반 골렘 스폰 → iron_golem_farm")
    elif p.source == "bartering":
        arch = "composite"
        params.setdefault("chain", ["source", "trigger", "collect", "store", "loop"])
        why.append("물물교환은 투척-회수 순환이라 전용 복셀보다 모듈 구성도가 정확 → composite")
    else:  # generation
        arch = "composite"
        params.setdefault("chain", ["source", "process", "collect", "loop"])
        why.append("블록 생성형은 생성-파괴-재생성 순환 구조 → composite")

    # --- 처리 방식이 아키타입과 안 맞을 때 보정 --------------------------
    if p.process == "smelt":
        arch = "smelter_array"
        params.setdefault("furnaces", int(p.scale.get("furnaces", 8)))
        why.append("제련이 최종 공정이면 병목은 화로 수 → smelter_array 로 대체")
    if p.collect == "none" and arch != "villager_hall":
        warn.append("collect=none 이면 아이템이 5분 뒤 소멸한다. hopper 또는 minecart 를 권장.")

    # --- 청크 로딩 (1.21.9 변경 대응) ------------------------------------
    warn.append(f"스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됨 → AFK 상주 또는 /forceload 로 "
                "청크를 고정해야 팜이 돈다.")

    return Resolution(arch, params, why, warn)
