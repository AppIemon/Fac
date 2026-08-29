"""아키타입 빌더: 작동 원리 파라미터 -> 실제 복셀 설계도.

각 빌더는 (Grid, 시공순서, 산출량설명, 경고) 를 돌려준다.
새 팜을 추가할 때 대부분은 기존 아키타입 + 파라미터로 끝난다.
아키타입이 없는 새 원리만 여기에 함수를 하나 추가하면 된다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import mechanics as M
from .grid import Grid


@dataclass
class BuildResult:
    grid: Grid
    steps: list[str] = field(default_factory=list)
    rate: str = "산출량 미산정"
    warnings: list[str] = field(default_factory=list)
    principle: str = ""


# ---------------------------------------------------------------------------
# 공통 부품
# ---------------------------------------------------------------------------
def _collection_hub(g: Grid, cx: int, y: int, cz: int) -> None:
    """호퍼 -> 상자 수거부. (cx, cz)가 아이템이 떨어지는 지점."""
    g.set(cx, y, cz, "h")
    g.set(cx, y, cz + 1, "h")
    g.set(cx, y - 1, cz + 1, "C")
    g.note(f"수거부: Y={y} (x={cx}, z={cz}) 호퍼 → Y={y-1} 큰 상자")


def _water_channel(g: Grid, x0: int, x1: int, y: int, z: int) -> None:
    """x0..x1 구간에 물길. 8칸마다 수원을 놓아 끊기지 않게 한다."""
    length = abs(x1 - x0) + 1
    step = M.WATER_FLOW_RANGE + 1
    for i, x in enumerate(range(min(x0, x1), max(x0, x1) + 1)):
        g.set(x, y, z, "w" if i % step == 0 else "-")
    return length


# ---------------------------------------------------------------------------
# 1. 자연 스폰 몹 타워 (가장 범용)
# ---------------------------------------------------------------------------
def mob_platform_tower(p: dict) -> BuildResult:
    size = int(p.get("platform", 9))          # 한 변 길이(홀수 권장)
    layers = int(p.get("layers", 4))          # 스폰 플랫폼 층수
    spacing = int(p.get("spacing", 4))        # 층 간격
    mob = p.get("mob", "zombie")
    hp = M.MOB_HP.get(mob, 20)
    xp_mode = bool(p.get("xp", False))
    drop = int(p.get("drop", M.drop_height_for(hp, leave_alive=xp_mode)))

    g = Grid(f"{mob}_platform_tower")
    half = size // 2
    cx, cz = 0, 0

    for i in range(layers):
        y = i * spacing
        # 스폰 바닥
        g.fill(cx - half, y, cz - half, cx + half, y, cz + half, "#")
        # 중앙 낙하 구멍
        g.set(cx, y, cz, ".")
        # 사방에서 중앙으로 흐르는 물길 (동/서 축)
        _water_channel(g, cx - half, cx - 1, y + 1, cz)
        _water_channel(g, cx + half, cx + 1, y + 1, cz)
        # 남/북 축
        for z in range(cz - half, cz):
            g.set(cx, y + 1, z, "w" if (cz - z - 1) % (M.WATER_FLOW_RANGE + 1) == 0 else "-")
        for z in range(cz + 1, cz + half + 1):
            g.set(cx, y + 1, z, "w" if (z - cz - 1) % (M.WATER_FLOW_RANGE + 1) == 0 else "-")
        # 벽(몹 이탈 방지) - 물길 높이 + 1
        g.hollow_box(cx - half, y + 1, cz - half, cx + half, y + 2, cz + half,
                     "#", floor=False, ceiling=False)

    top = (layers - 1) * spacing + 2
    # 중앙 낙하 통로
    for y in range(-drop, top + 1):
        g.hollow_box(cx - 1, y, cz - 1, cx + 1, y, cz + 1, "#", floor=False, ceiling=False)
        g.set(cx, y, cz, ".")
    # 착지 지점 + 수거
    _collection_hub(g, cx, -drop - 1, cz)
    g.set(cx, -drop - 2, cz, "#")
    g.note(f"낙하 높이 {drop}블록 → 데미지 {M.fall_damage(drop)} (체력 {hp})")

    afk_y = top + M.MOB_SPAWN_MIN_DISTANCE
    g.note(f"AFK 지점: 스폰 플랫폼 최상단에서 위로 {M.MOB_SPAWN_MIN_DISTANCE}블록 이상 (Y≈{afk_y})")

    spawnable = layers * (size * size - 1)
    rate = M.spawn_rate_estimate(spawnable)
    warn = []
    if not xp_mode and M.fall_damage(drop) < hp:
        warn.append(f"낙하 데미지({M.fall_damage(drop)})가 {mob} 체력({hp})보다 낮음 → 즉사 안 됨. drop을 {M.drop_height_for(hp)} 이상으로.")
    if size % 2 == 0:
        warn.append("플랫폼 한 변이 짝수라 중앙 정렬이 어긋남. 홀수 권장.")
    if half > M.WATER_FLOW_RANGE + 1:
        warn.append(f"플랫폼 반경({half})이 물 도달거리를 넘어 물길 중간에 수원 추가 필요(엔진이 자동 배치함).")
    warn.append("스폰 플랫폼 내부 블록광은 반드시 0. 인근 동굴은 전부 밀봉하거나 조명 처리.")

    return BuildResult(
        g,
        steps=[
            f"1) 부지 확보: {size}x{size} 평면 x {layers}층, 층 간격 {spacing}블록.",
            "2) 최하단부터 바닥 → 벽 순서로 쌓고, 각 층 중앙 1칸은 비워 낙하 통로로 연결.",
            "3) 각 층 물길 설치. 바깥 끝에서 중앙 구멍 방향으로 흐르게, 8칸마다 수원.",
            f"4) 중앙 통로를 아래로 {drop}블록 파고, 바닥에 호퍼 → 상자.",
            "5) 주변 32블록 내 모든 동굴/어두운 공간 밀봉 또는 조명 (몹캡 경쟁 제거).",
            f"6) AFK 지점을 스폰층 위 {M.MOB_SPAWN_MIN_DISTANCE}블록 이상, 수거부 128블록 이내에 설치.",
        ],
        rate=f"스폰 가능 블록 {spawnable}칸 → 시간당 약 {rate:,.0f}마리 (추정)",
        warnings=warn,
        principle="어둠 속 자연 스폰 → 물길로 한 점 집결 → 낙하 데미지 처치 → 호퍼 수거",
    )


# ---------------------------------------------------------------------------
# 2. 스포너 박스 (던전/시련의 방)
# ---------------------------------------------------------------------------
def spawner_box(p: dict) -> BuildResult:
    mob = p.get("mob", "zombie")
    hp = M.MOB_HP.get(mob, 20)
    xp_mode = bool(p.get("xp", True))
    drop = int(p.get("drop", M.drop_height_for(hp, leave_alive=xp_mode)))

    g = Grid(f"{mob}_spawner_farm")
    # 스포너 중심 9x9x5 활성 구역
    g.hollow_box(-4, 0, -4, 4, 4, 4, "#", floor=True, ceiling=True)
    g.fill(-3, 1, -3, 3, 3, 3, ".")
    g.set(0, 2, 0, "x")
    # 바닥 물길 -> 한쪽 끝 구멍
    _water_channel(g, -3, 3, 1, 0)
    for z in (-3, -2, -1, 1, 2, 3):
        _water_channel(g, -3, 3, 1, z)
    g.set(4, 1, 0, ".")
    # 낙하 통로
    for y in range(-drop, 2):
        g.hollow_box(4, y, -1, 6, y, 1, "#", floor=False, ceiling=False)
        g.set(5, y, 0, ".")
    _collection_hub(g, 5, -drop - 1, 0)
    g.note("스포너는 플레이어 16블록 이내 + 밝기 조건 충족 시 4초마다 최대 4마리 시도")

    return BuildResult(
        g,
        steps=[
            "1) 스포너 중심 반경 4블록을 9x9x5로 파내되 스포너는 절대 부수지 않는다.",
            "2) 바닥 한 층 아래에 물길을 깔아 몹을 한쪽 벽 구멍으로 밀어낸다.",
            f"3) 구멍에서 {drop}블록 낙하 통로를 만들고 바닥에 호퍼 → 상자.",
            "4) 스포너 방 내부 광원은 몹 종류에 맞춰 조절(좀비/스켈레톤은 블록광 0).",
            "5) AFK 지점은 스포너에서 16블록 이내(활성) 이면서 처치 지점을 볼 수 있는 곳.",
        ],
        rate="스포너 1개 기준 시간당 약 500~900마리 (플레이어 상주 시, 추정)",
        warnings=["스포너를 밝히거나 부수면 영구 손실. 시련의 방 스포너는 1회성 보상 스포너와 구분할 것.",
                  "26.2 기준 `spawnerBlocksEnabled` 게임룰이 false면 스포너가 동작하지 않음."],
        principle="스포너 강제 스폰 → 물길 집결 → 낙하 → 수거",
    )


# ---------------------------------------------------------------------------
# 3. 기둥 작물 (사탕수수/대나무/선인장/다시마)
# ---------------------------------------------------------------------------
def column_crop(p: dict) -> BuildResult:
    crop = p.get("crop", "sugar_cane")
    rows = int(p.get("rows", 2))
    length = int(p.get("length", 16))

    g = Grid(f"{crop}_column_farm")
    soil = "d" if crop in ("sugar_cane", "bamboo") else "#"
    for r in range(rows):
        z = r * 3
        for x in range(length):
            g.set(x, 0, z, soil)
            g.set(x, 1, z, "v")
            g.set(x, 2, z, "o")           # 관측기: 2칸째 성장 감지
            g.set(x, 3, z, "p")           # 피스톤이 아니라 관측기 신호선용 자리
            g.set(x, 0, z + 1, "h")       # 수거 호퍼 라인
            g.set(x, -1, z + 1, "#")
            if crop == "sugar_cane":
                g.set(x, 0, z - 1, "w" if x % (M.WATER_FLOW_RANGE + 1) == 0 else "-")
        g.set(length, -1, z + 1, "C")
    g.note("관측기는 작물이 2번째 칸까지 자란 것을 감지 → 같은 높이 피스톤이 밀어 끊음")

    plants = rows * length
    rate = M.column_crop_rate(plants, crop)
    return BuildResult(
        g,
        steps=[
            f"1) {rows}줄 x {length}칸 심을 자리를 만든다. (사탕수수/대나무는 흙/모래, 선인장은 모래)",
            "2) 심는 칸 옆에 호퍼 라인을 깔고 끝을 상자로 연결.",
            "3) 심는 칸 기준 2블록 위에 관측기를 작물 쪽으로 향하게 설치.",
            "4) 관측기 뒤에 피스톤을 붙여, 작물이 자라면 즉시 밀어 끊게 한다.",
            "5) 선인장은 옆칸에 블록만 두면 자동 파괴되므로 피스톤 없이도 가능.",
        ],
        rate=f"{plants}포기 → 시간당 약 {rate:,.0f}개 (랜덤틱 기준 추정)",
        warnings=["플레이어가 없으면 청크가 언로드되어 성장 정지. 1.21.9 이후 스폰 청크가 없으므로 /forceload 또는 AFK 필요."],
        principle="랜덤틱 성장 → 관측기 감지 → 피스톤 절단 → 호퍼 수거",
    )


# ---------------------------------------------------------------------------
# 4. 경작지 작물 (밀/당근/감자/비트) - 피스톤 일괄 수확
# ---------------------------------------------------------------------------
def crop_piston_harvester(p: dict) -> BuildResult:
    crop = p.get("crop", "wheat")
    width = int(p.get("width", 9))
    length = int(p.get("length", 9))

    g = Grid(f"{crop}_piston_farm")
    for z in range(length):
        for x in range(width):
            g.set(x, 0, z, "d")
            g.set(x, 1, z, "v")
        g.set(width, 0, z, "h")
        g.set(width, -1, z, "#")
    # 중앙 관개 수로
    for x in range(width):
        g.set(x, 0, length // 2, "w")
        g.set(x, 1, length // 2, ".")
    # 뒤쪽 피스톤 벽
    for x in range(width):
        g.set(x, 1, -1, "p")
        g.set(x, 2, -1, "b")
    g.set(width, -1, length, "C")
    g.note("수원 1개는 반경 4칸 경작지를 적신다 → 9칸마다 수로 1줄")

    tiles = width * length
    return BuildResult(
        g,
        steps=[
            f"1) {width}x{length} 경작지를 만들고 {length//2}번째 줄에 관개 수로를 판다.",
            "2) 밭 한쪽 끝 전체에 호퍼 라인 → 상자.",
            "3) 밭 뒤쪽에 피스톤 벽을 세우고 레드스톤 블록/관측기로 일괄 작동시킨다.",
            "4) 수확은 물을 흘려 아이템을 호퍼 쪽으로 밀어내는 방식이 가장 안정적.",
            "5) 완전 자동화가 필요하면 주민(농부)을 밭에 가둬 수확·재파종을 맡긴다.",
        ],
        rate=f"경작지 {tiles}칸 → 성장 완료까지 실시간 기준 수십 분, 1회 수확 약 {tiles}~{tiles*2}개",
        warnings=["작물은 광원 9 이상 필요. 완전 자동은 주민 농부 방식이 훨씬 안정적."],
        principle="경작지 성장 → 피스톤/주민 수확 → 물 이송 → 호퍼 수거",
    )


# ---------------------------------------------------------------------------
# 5. 철 골렘 팜
# ---------------------------------------------------------------------------
def iron_golem_farm(p: dict) -> BuildResult:
    pods = int(p.get("pods", 3))
    g = Grid("iron_golem_farm")
    # 주민 포드 3개 (한 유닛)
    for i in range(pods):
        z = i * 2
        g.hollow_box(0, 0, z, 2, 2, z + 1, "#", floor=True, ceiling=True)
        g.set(1, 1, z, ".")     # 주민 자리
        g.set(1, 2, z, "?")     # 침대 머리 방향 표시
    # 좀비 칸 (주민이 볼 수 있게 유리 너머)
    g.fill(4, 1, 0, 4, 2, pods * 2, "g")
    g.set(5, 1, pods, "?")
    g.note("좀비 1마리는 벽/보트로 고정. 주민이 좀비를 '볼 수 있어야' 골렘 스폰 조건 성립")
    # 스폰 플랫폼 (주민 아래)
    g.fill(-3, -4, -1, 3, -4, pods * 2 + 1, "#")
    # 용암 블레이드 처치부
    g.fill(-3, -3, pods * 2 + 3, 3, -3, pods * 2 + 3, "l")
    g.fill(-3, -4, pods * 2 + 4, 3, -4, pods * 2 + 4, "h")
    g.set(0, -5, pods * 2 + 4, "C")
    g.note("골렘은 체력 100 → 낙하로 즉사 불가. 용암 블레이드 또는 낙하+용암 조합 사용")

    return BuildResult(
        g,
        steps=[
            f"1) 주민 {pods}명을 각각 침대와 함께 1x1 포드에 가둔다(포드 간 시야 차단).",
            "2) 주민 전원이 볼 수 있는 위치에 좀비 1마리를 보트/벽으로 고정한다.",
            "3) 주민들이 공포 상태가 되면 아래 스폰 플랫폼에 철 골렘이 생성된다.",
            "4) 스폰 플랫폼을 물길로 밀어 용암 블레이드(용암 1칸 + 반 블록)로 이송.",
            "5) 골렘이 죽는 지점 아래 호퍼 → 상자.",
            "6) 주민이 잠들 수 있게 침대를 반드시 연결하고, 일자리 블록은 두지 않는다.",
        ],
        rate=f"주민 {pods}명 유닛 1개 → 시간당 철괴 약 {pods*30}~{pods*40}개 (추정)",
        warnings=["철 골렘 체력 100 → 낙하 즉사 불가. 용암/용암블레이드 필수.",
                  "주민이 좀비를 볼 수 없으면 스폰이 완전히 멈춘다. 유리는 시야를 막지 않으니 유리 사용.",
                  "스폰 플랫폼은 주민 기준 -? 범위 안에 있어야 하며, 다른 골렘이 남아 있으면 스폰이 막힌다."],
        principle="주민 공포 → 철 골렘 스폰 → 물길 이송 → 용암 처치 → 수거",
    )


# ---------------------------------------------------------------------------
# 6. 네더 플랫폼 (금/위더스켈레톤/호글린)
# ---------------------------------------------------------------------------
def nether_platform(p: dict) -> BuildResult:
    kind = p.get("kind", "gold")
    size = int(p.get("platform", 15))
    drop = int(p.get("drop", 24))

    g = Grid(f"nether_{kind}_farm")
    half = size // 2
    # 스폰 플랫폼 (마그마 블록 = 몹이 걸어서 물길로)
    g.fill(-half, 0, -half, half, 0, half, "#")
    g.set(0, 0, 0, ".")
    _water_channel(g, -half, -1, 1, 0) if kind == "gold" else None
    # 네더에서는 물이 증발 -> 마그마/발판/피스톤 이송
    for x in range(-half, half + 1):
        for z in range(-half, half + 1):
            if (x, z) != (0, 0) and (abs(x) + abs(z)) % 4 == 0:
                g.set(x, 1, z, "m")
    g.hollow_box(-half, 1, -half, half, 3, half, "#", floor=False, ceiling=False)
    for y in range(-drop, 1):
        g.hollow_box(-1, y, -1, 1, y, 1, "#", floor=False, ceiling=False)
        g.set(0, y, 0, ".")
    _collection_hub(g, 0, -drop - 1, 0)
    g.note("네더는 물이 증발한다 → 이송은 마그마 블록/발사기 물 대신 '흐르는 용암 없음' 설계 필요")

    kinds = {
        "gold": ("좀비화 피글린", "네더 황무지 플랫폼 전체를 덮어 스폰 독점"),
        "wither_skeleton": ("위더 스켈레톤", "네더 요새 스폰 구역 안에서만 유효"),
        "hoglin": ("호글린", "진홍빛 숲에서만 스폰, 경작지 블록으로 스폰 차단 후 유도"),
        "piglin_barter": ("피글린 물물교환", "금괴 발사기로 던져 주고 산출물 회수"),
    }
    label, hint = kinds.get(kind, ("몹", ""))
    return BuildResult(
        g,
        steps=[
            f"1) 대상: {label}. {hint}",
            f"2) {size}x{size} 플랫폼을 깔고 중앙 1칸을 비운다.",
            "3) 네더는 물이 증발하므로 이송은 마그마 블록/피스톤/발사기(얼음+물 조합)로 한다.",
            f"4) 중앙에서 {drop}블록 낙하 → 호퍼 → 상자.",
            "5) 주변 128블록 내 다른 스폰 가능 지면을 반 블록/광원으로 전부 차단해야 효율이 난다.",
        ],
        rate="플랫폼 면적과 주변 스폰 차단 정도에 완전히 비례. 차단 미흡 시 효율 1/10 이하.",
        warnings=["네더는 물이 즉시 증발 → 오버월드 물길 설계를 그대로 옮기면 작동하지 않음.",
                  "좀비화 피글린은 플레이어를 공격하면 집단 적대 → 처치는 반드시 간접(낙하/용암)으로.",
                  "위더 스켈레톤은 네더 요새의 스폰 구역(structure bounding box) 안에서만 스폰한다."],
        principle=f"{label} 자연 스폰 독점 → 이송 → 낙하 처치 → 수거",
    )


# ---------------------------------------------------------------------------
# 7. 엔더맨 팜 (엔드 본섬 바깥)
# ---------------------------------------------------------------------------
def enderman_platform(p: dict) -> BuildResult:
    drop = int(p.get("drop", M.drop_height_for(M.MOB_HP["enderman"], leave_alive=True)))
    g = Grid("enderman_farm")
    g.fill(-11, 0, -11, 11, 0, 11, "#")
    g.set(0, 0, 0, ".")
    for x in range(-11, 12):
        for z in range(-11, 12):
            if (x, z) != (0, 0):
                g.set(x, 1, z, "s")   # 하프 블록: 엔더맨만 스폰 가능하게
    g.note("엔드 스폰 플랫폼은 본섬에서 최소 128블록 이상 떨어진 허공에 짓는다")
    for y in range(-drop, 1):
        g.hollow_box(-1, y, -1, 1, y, 1, "#", floor=False, ceiling=False)
        g.set(0, y, 0, ".")
    _collection_hub(g, 0, -drop - 1, 0)
    g.set(0, -drop - 3, 0, "@")
    return BuildResult(
        g,
        steps=[
            "1) 엔드 본섬에서 128블록 이상 떨어진 허공에 23x23 플랫폼을 만든다.",
            "2) AFK 지점을 플랫폼 아래 24블록 이상에 두고, 그 주변 스폰을 전부 막는다.",
            f"3) 중앙 구멍에서 {drop}블록 낙하 → 1HP만 남기고 직접 타격(엔더 진주/경험치 극대화).",
            "4) 엔더마이트를 광산 수레에 가둬 유인체로 두면 효율이 크게 오른다.",
            "5) 처치 지점 아래 호퍼 → 상자.",
        ],
        rate="시간당 엔더 진주 수백 개 (유인체 사용 시 크게 상승, 추정)",
        warnings=["엔더맨은 체력 40 → 낙하 즉사에 43블록 필요. 진주 손실 없이 경험치를 얻으려면 22~37블록 후 직접 타격 권장.",
                  "플레이어를 직접 보면 순간이동으로 이탈 → 시야 차단 필수."],
        principle="엔드 허공 플랫폼 스폰 독점 → 낙하 → 직접 타격 처치",
    )


# ---------------------------------------------------------------------------
# 8. 아이템 분류기
# ---------------------------------------------------------------------------
def item_sorter(p: dict) -> BuildResult:
    channels = int(p.get("channels", 8))
    copper_golem = bool(p.get("copper_golem", False))

    g = Grid("item_sorter")
    if copper_golem:
        # 26.x 구리 골렘 분류: 구리 상자(입력) + 목표 나무 상자들
        g.set(0, 0, 0, "C")
        g.note("입력: 구리 상자 (골렘이 여기서 최대 16스택 픽업)")
        for i in range(channels):
            g.set(2 + i, 0, 0, "c")
            g.set(2 + i, -1, 0, "#")
        g.note("각 목표 상자에 분류할 아이템을 미리 1개씩 넣어두면 그 아이템만 들어간다")
        steps = [
            "1) 입력용 '구리 상자' 1개를 두고, 팜 산출물을 여기로 모은다.",
            "2) 골렘이 걸어다닐 통로를 따라 목표 '나무 상자'들을 배치한다.",
            "3) 각 나무 상자에 분류하려는 아이템을 미리 넣어둔다(같은 종류만 투입됨).",
            "4) 구리 골렘을 소환/배치한다. 산화되면 동작이 느려지므로 밀랍칠 권장.",
            "5) 상자가 가득 차면 골렘이 멈추니, 오버플로 라인을 별도로 둔다.",
        ]
        warn = ["구리 골렘은 '아이템 종류/이름/인챈트'가 같은 상자에만 넣는다. 빈 상자는 아무거나 받으므로 반드시 지정 아이템을 미리 넣을 것.",
                "레드스톤 분류기보다 느리다. 고속 팜에는 아래 클래식 호퍼 분류기를 쓸 것."]
    else:
        for i in range(channels):
            x = i * 2
            g.set(x, 2, 0, "h")       # 상단 이송 호퍼 라인
            g.set(x, 1, 0, "h")       # 분류 호퍼 (위를 향함)
            g.set(x, 1, 1, "?")       # 필터 아이템 표시
            g.set(x, 0, 0, "c")       # 목적지 상자
            g.set(x, 0, 1, "#")
            g.set(x, 1, -1, "r")      # 비교기/레드스톤 라인
            g.set(x, 0, -1, "#")
        g.note("분류 호퍼에 필터 아이템 1종 x 18개 + 이름표 붙인 아이템 4칸 = 표준 필터")
        steps = [
            "1) 상단에 좌→우로 흐르는 이송 호퍼 라인을 깐다.",
            "2) 각 채널마다 이송 라인 아래로 '위를 향한 분류 호퍼'를 붙인다.",
            "3) 분류 호퍼 5칸 중 1칸에 필터 아이템 1개, 나머지 4칸에 아무 아이템 1개씩(스택 불가 물품 권장).",
            "4) 비교기로 신호를 뽑아 레드스톤 블록으로 호퍼 잠금(hopper lock)을 건다.",
            "5) 분류 호퍼 아래에 목적지 상자를 둔다.",
            "6) 라인 끝에 오버플로 상자를 두어 미분류 아이템을 받는다.",
        ]
        warn = ["필터 슬롯 구성이 틀리면 엉뚱한 아이템이 새어 나간다. 필터 아이템 18개 + 채움용 4개가 표준.",
                f"라인 처리량은 호퍼 1개 = 초당 {M.HOPPER_ITEMS_PER_SEC}개. 고속 팜은 라인을 병렬로 나눌 것."]

    return BuildResult(
        g,
        steps=steps,
        rate=f"채널 {channels}개, 라인 처리량 초당 {M.HOPPER_ITEMS_PER_SEC}개 (병렬 시 x라인수)",
        warnings=warn,
        principle=("구리 골렘 자동 분류(26.x)" if copper_golem else "비교기 신호 + 호퍼 잠금으로 지정 아이템만 통과"),
    )


# ---------------------------------------------------------------------------
# 9. 대량 제련로
# ---------------------------------------------------------------------------
def smelter_array(p: dict) -> BuildResult:
    n = int(p.get("furnaces", 8))
    g = Grid("super_smelter")
    for i in range(n):
        x = i * 2
        g.set(x, 2, 0, "h")     # 원료 라인
        g.set(x, 1, 0, "u")     # 화로
        g.set(x, 1, 1, "h")     # 연료 라인 (측면 투입)
        g.set(x, 0, 0, "h")     # 산출 호퍼
        g.set(x, -1, 0, "#")
    g.set(n * 2, -1, 0, "C")
    g.note("호퍼는 위=원료, 옆=연료, 아래=산출")
    per_hour = n * M.FURNACE_ITEMS_PER_HOUR
    return BuildResult(
        g,
        steps=[
            f"1) 화로 {n}대를 한 줄로 놓는다.",
            "2) 화로 위에 원료 이송 호퍼 라인, 옆면에 연료 이송 호퍼 라인을 붙인다.",
            "3) 화로 아래에 산출 호퍼를 깔아 상자로 모은다.",
            "4) 원료를 각 화로에 고르게 분배하려면 라인 끝을 처음으로 되돌리는 순환 구조로 만든다.",
            "5) 연료는 용암 양동이(20000틱)나 말린 켈프 블록(4000틱)이 효율적.",
        ],
        rate=f"화로 {n}대 → 시간당 {per_hour:,.0f}개 (연속 가동 기준)",
        warnings=[f"호퍼 1줄(초당 {M.HOPPER_ITEMS_PER_SEC}개)로는 화로 {int(M.HOPPER_ITEMS_PER_SEC*3600/M.FURNACE_ITEMS_PER_HOUR)}대까지가 한계. 그 이상은 라인 분할 필요."],
        principle="호퍼 3방향 투입(위=원료/옆=연료/아래=산출) 병렬 화로",
    )


# ---------------------------------------------------------------------------
# 10. 동물 사육 + 자동 조리
# ---------------------------------------------------------------------------
def animal_farm(p: dict) -> BuildResult:
    animal = p.get("animal", "cow")
    cook = bool(p.get("cook", True))
    g = Grid(f"{animal}_farm")
    g.hollow_box(0, 0, 0, 6, 3, 6, "#", floor=True, ceiling=False)
    g.fill(1, 1, 1, 5, 1, 5, ".")
    # 새끼가 떨어지는 1칸 구멍(성체는 못 지나감)
    g.set(3, 0, 3, ".")
    g.set(3, -1, 3, "l" if cook else ".")
    g.set(3, -2, 3, "h")
    g.set(3, -3, 3, "C")
    g.note("성체는 높이 1칸 구멍을 통과 못하고 새끼만 떨어지는 구조 (또는 성장 시 압사 방식)")
    return BuildResult(
        g,
        steps=[
            f"1) 6x6 울타리/벽 우리를 만들고 {animal} 성체 2마리 이상을 넣는다.",
            "2) 바닥 한 칸을 비워 새끼만 아래로 떨어지게 한다.",
            "3) 떨어진 새끼가 자라 성체가 되는 지점에 " + ("용암 1칸(자동 조리)" if cook else "처치 장치") + "을 둔다.",
            "4) 아래 호퍼 → 상자로 고기/가죽을 수거한다.",
            "5) 번식은 발사기로 밀/당근을 자동 급여하거나 직접 한다.",
        ],
        rate="성체 쌍 수에 비례. 12마리 우리 기준 시간당 수십 개 (추정)",
        warnings=["26.1에서 '황금 민들레'로 새끼 성장을 정지/재개할 수 있으니, 새끼 압사형 설계는 재검토할 것.",
                  "용암 조리는 가죽이 타지 않는지 확인 필요. 안전하게는 낙하 처치 + 화로 제련 조합 권장."],
        principle="번식 → 새끼만 낙하 분리 → 성장 시 처치 → 수거",
    )


# ---------------------------------------------------------------------------
# 11. 주민 거래소
# ---------------------------------------------------------------------------
def villager_hall(p: dict) -> BuildResult:
    stalls = int(p.get("stalls", 6))
    g = Grid("villager_trading_hall")
    for i in range(stalls):
        z = i * 2
        g.hollow_box(0, 0, z, 2, 2, z + 1, "#", floor=True, ceiling=True)
        g.set(1, 1, z, ".")
        g.set(1, 0, z, "?")   # 일자리 블록 자리
        g.set(3, 1, z, "t")   # 다락문/거래 창
    g.note("일자리 블록을 부수고 다시 놓으면 거래 목록 재추첨 (마스터 승급 전까지)")
    return BuildResult(
        g,
        steps=[
            f"1) {stalls}칸짜리 부스를 만들고 각 칸에 주민 1명을 가둔다.",
            "2) 각 부스에 원하는 직업의 일자리 블록을 놓는다(사서=책장/서가대 등).",
            "3) 거래 목록이 마음에 안 들면 일자리 블록을 부수고 다시 놓아 재추첨한다.",
            "4) 마스터 승급 전까지만 재추첨 가능하므로 원하는 거래가 나오면 즉시 1회 거래한다.",
            "5) 26.1부터 거래가 데이터팩으로 정의되므로 서버 설정에 따라 목록이 다를 수 있다.",
        ],
        rate="거래 목록에 따름. 사서 책 거래가 가장 수익성 높음.",
        warnings=["26.1: 마스터 사서가 더 이상 이름표를 팔지 않음 → 이름표는 방랑상인(에메랄드 1개) 또는 조합(종이+너겟).",
                  "26.1: 거래가 데이터팩 기반으로 바뀌어 서버마다 목록이 다를 수 있음."],
        principle="주민 직업 부여 → 거래 목록 재추첨 → 고정 후 거래",
    )


# ---------------------------------------------------------------------------
# 12. 범용 폴백: 모듈 흐름도만 생성 (거짓 설계도 대신 정직한 구성도)
# ---------------------------------------------------------------------------
def composite(p: dict) -> BuildResult:
    chain = p.get("chain", ["source", "transport", "process", "collect", "store"])
    labels = {
        "source": "산출원 (스폰/성장/생성)",
        "transport": "이송 (물길/피스톤/미니카트)",
        "process": "가공 (처치/제련/조합)",
        "collect": "수거 (호퍼/호퍼 미니카트)",
        "store": "저장 (분류기/상자 배열)",
        "trigger": "발동 (관측기/타이머/비교기)",
        "loop": "순환 (재파종/재장전)",
    }
    g = Grid("composite_flow")
    for i, part in enumerate(chain):
        x = i * 4
        g.hollow_box(x, 0, 0, x + 2, 2, 2, "#", floor=True, ceiling=True)
        g.set(x + 1, 1, 1, "?")
        if i < len(chain) - 1:
            g.set(x + 3, 1, 1, "-")
    for part in chain:
        g.note(f"{part}: {labels.get(part, part)} → 이 칸의 구현체를 직접 지정할 것")
    return BuildResult(
        g,
        steps=[f"{i+1}) {labels.get(part, part)} 모듈을 설계·배치한다." for i, part in enumerate(chain)],
        rate="모듈 중 가장 느린 단계가 전체 속도를 결정(병목 분석 필요)",
        warnings=["이 아키타입은 전용 복셀 설계도가 아직 없는 원리에 대한 '구성도'다. "
                  "각 모듈을 개별 아키타입으로 뽑아 조합할 것."],
        principle=" → ".join(labels.get(c, c) for c in chain),
    )


ARCHETYPES = {
    "mob_platform_tower": mob_platform_tower,
    "spawner_box": spawner_box,
    "column_crop": column_crop,
    "crop_piston_harvester": crop_piston_harvester,
    "iron_golem_farm": iron_golem_farm,
    "nether_platform": nether_platform,
    "enderman_platform": enderman_platform,
    "item_sorter": item_sorter,
    "smelter_array": smelter_array,
    "animal_farm": animal_farm,
    "villager_hall": villager_hall,
    "composite": composite,
}


def build(archetype: str, params: dict | None = None) -> BuildResult:
    fn = ARCHETYPES.get(archetype)
    if fn is None:
        raise KeyError(f"알 수 없는 아키타입: {archetype}. 사용 가능: {', '.join(sorted(ARCHETYPES))}")
    return fn(params or {})
