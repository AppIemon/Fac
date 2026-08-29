"""매끄러운 돌 공장 — 생성기 + 드로퍼 분배 화로를 한 덩어리로.

돌 생성기를 쓰는 이유:
  조약돌 경로는 조약돌 → (제련) 돌 → (제련) 매끄러운 돌 로 두 번 구워야 한다.
  '위에서 물로 흘러든 용암'은 조약돌이 아니라 곧바로 '돌'을 만든다.
  그래서 제련이 한 번으로 줄고 연료가 절반이 된다.

층 구조 (아래 → 위):
  Y= 0  산출 호퍼(동→) ─────────────> 매끄러운 돌 상자
  Y=+1  화로 / (z=1) 연료 투입 호퍼(북↑)
  Y=+2  호퍼(아래↓) — 드로퍼에서 끌어와 화로 원료 슬롯으로
  Y=+3  드로퍼 사슬(동→) / 연료 드로퍼 사슬(동→)
  Y=+4  받침 블록
  Y=+5  레드스톤 가루 (드로퍼 급전) + 동쪽 끝 관측기 2개 = 자가 발진 클럭
  Y=+6  차단층 (가루와 생성부를 떼어 놓는다)
  Y=+7  생성기 수거 호퍼(서←) ── 서쪽 끝에서 아래로 떨어져 드로퍼 사슬로
  Y=+8  생성칸 (여기서 돌이 생긴다) / (z=-1) 물 수원
  Y=+9  용암 수원

호퍼는 레드스톤 신호를 받으면 잠긴다. 그래서 연결 통로(x=-2)는 가루 줄에서
두 칸 떨어뜨렸고, 생성부와 가루 사이에는 차단층을 두었다.

원료 투입구가 따로 없다. 생성기가 캔 돌이 그대로 화로로 내려간다.
"""
from __future__ import annotations

from .. import mechanics as M
from ..blocks import (DOWN, EAST, GLASS, LAVA, NORTH, STONE, WATER, WEST,
                      chest, dropper, furnace, hopper, observer, redstone_wire)
from ..schematic import Schematic
from . import Design


def build(cells: int = 2, furnaces: int = 6, structure=STONE) -> Design:
    if cells < 1 or furnaces < 1:
        raise ValueError("cells 와 furnaces 는 1 이상이어야 한다")
    c, n = cells, furnaces
    width = max(c, n)

    s = Schematic(
        name=f"smoothstone_factory_c{c}_f{n}",
        description=f"매끄러운 돌 공장 · 돌 생성칸 {c}개 + 드로퍼 분배 화로 {n}대 "
                    f"(시간당 {n * M.FURNACE_ITEMS_PER_HOUR:,.0f}개)",
    )

    # ---------------- 제련부 (드로퍼 분배) ----------------
    for x in range(n):
        s.set(x, 3, 0, dropper(EAST))
        s.set(x, 2, 0, hopper(DOWN))
        s.set(x, 1, 0, furnace(NORTH))
        s.set(x, 0, 0, hopper(EAST))
        s.set(x, -1, 0, structure)
        s.set(x, 4, 0, structure)
        s.set(x, 5, 0, redstone_wire(south="side", east="side",
                                     west="side" if x > 0 else "none"))

        s.set(x, 3, 1, dropper(EAST))
        s.set(x, 2, 1, hopper(DOWN))
        s.set(x, 1, 1, hopper(NORTH))
        s.set(x, 0, 1, structure)
        s.set(x, -1, 1, structure)
        s.set(x, 4, 1, structure)
        s.set(x, 5, 1, redstone_wire(north="side", east="side",
                                     west="side" if x > 0 else "none"))

    # 연료 투입구 (서쪽) — 원료는 생성기가 직접 넣으므로 연료만 받는다
    s.set(-1, 4, 1, chest(NORTH))
    s.set(-1, 3, 1, hopper(EAST))
    s.fill(-1, -1, 1, -1, 2, 1, structure)

    # 드로퍼 사슬 끝은 반드시 컨테이너 (공기면 아이템을 월드로 뱉는다)
    s.set(n, 3, 0, chest(EAST))
    s.set(n, 3, 1, chest(EAST))
    s.set(n, 0, 0, chest(EAST))            # 매끄러운 돌 산출
    s.set(n, -1, 0, structure)
    s.set(n, -1, 1, structure)

    # 자가 발진 클럭 (동쪽 끝. 서쪽은 투입 상자 자리라 위를 막으면 안 열린다)
    s.set(n, 5, 0, observer(EAST))
    s.set(n + 1, 5, 0, observer(WEST))

    # ---------------- 차단층 ----------------
    # 호퍼는 레드스톤 신호를 받으면 잠긴다. 가루 줄(Y=+5)과 생성부를 떼어 놓는다.
    for x in range(-1, n + 2):
        s.set(x, 6, 0, structure)
        s.set(x, 6, 1, structure)

    # ---------------- 생성부 (제자리 돌 생성기) ----------------
    for x in range(c):
        s.set(x, 9, 0, LAVA)               # 용암 수원 — 아래로 흘러든다
        # (x, 8, 0) 은 비워 둔다 — 여기에 돌이 생성된다
        s.set(x, 7, 0, hopper(WEST))       # 캔 돌을 서쪽으로 나른다

        s.set(x, 8, -1, WATER)             # 물 수원 (생성칸을 채운다)
        s.set(x, 7, -1, structure)
        s.set(x, 9, -1, structure)
        s.fill(x, 7, 1, x, 9, 1, structure)   # 남쪽 벽

    s.fill(c, 7, -1, c, 9, 1, structure)      # 생성부 동쪽 끝막이
    for x in range(-2, c + 1):                # 북쪽(z=-2) 벽
        s.fill(x, 7, -2, x, 9, -2, structure)

    # ---------------- 생성부 → 제련부 연결 ----------------
    # 가루 줄에서 두 칸 떨어진 x=-2 통로로 내려보낸다.
    # 호퍼를 가루 옆에 두면 신호를 받아 잠겨서 공급이 끊긴다.
    s.set(-2, 7, 0, hopper(DOWN))
    s.set(-2, 6, 0, hopper(DOWN))
    s.set(-2, 5, 0, hopper(DOWN))
    s.set(-2, 4, 0, hopper(DOWN))
    s.set(-2, 3, 0, hopper(EAST))
    s.set(-1, 3, 0, hopper(EAST))          # 첫 드로퍼로 밀어 넣는다
    s.fill(-2, -1, 0, -2, 2, 0, structure)
    s.fill(-1, -1, 0, -1, 2, 0, structure)
    s.fill(-1, 4, 0, -1, 5, 0, structure)
    s.set(-1, 7, 0, hopper(WEST))          # 수거 줄을 하강 통로까지 잇는다
    s.set(-1, 7, -1, structure)
    s.fill(-1, 8, -1, -1, 9, 0, structure)
    s.fill(-2, 7, -1, -2, 9, -1, structure)
    s.fill(-2, 8, 0, -2, 9, 0, structure)

    s.note("호퍼는 레드스톤 신호를 받으면 잠긴다. 연결 통로를 가루에서 두 칸 떼고 "
           "Y=+6 에 차단층을 둔 이유다.")
    s.note("생성칸(Y=+8)은 반드시 비워 둔다. 물이 채우고 용암이 내려와 '돌'이 된다.")
    s.note("물은 항상 용암 수원의 '아래'에 있다 → 흑요석 조건(위/옆)에 걸리지 않는다.")
    s.note("드로퍼 사슬 끝은 상자다. 공기를 향하면 아이템을 월드로 뱉는다.")
    s.note("관측기 2개가 마주보면 클럭이 저절로 돈다. 점화용 레버가 필요 없다.")

    per_hour = n * M.FURNACE_ITEMS_PER_HOUR
    fuel_per_hour = per_hour  # 제련 1단이므로 산출 1개당 연료 1개분
    return Design(
        schematic=s,
        principle="용암이 위에서 물로 흘러들어 '돌'이 생성 → 캐면 아래 호퍼가 수거 → "
                  "서쪽 끝에서 떨어져 드로퍼 사슬로 → 각 화로에 균등 분배 → "
                  "매끄러운 돌 제련 → 동쪽 상자",
        circuit=[
            "[생성] 물 수원(z=-1) → 생성칸(Y=+8) 을 채움",
            "[생성] 용암 수원(Y=+9) → 아래로 흘러 물에 진입 → 물이 '돌'로 변한다",
            "[생성] 플레이어가 캔다 → 바로 아래 호퍼(Y=+7)가 수거, 서쪽으로 이송",
            "[연결] x=-2 통로의 호퍼 4칸이 아래로 떨어뜨려 원료 드로퍼 사슬(Y=+3)로. "
            "가루에서 두 칸 떨어뜨린 건 호퍼가 신호를 받으면 잠기기 때문이다",
            "[분배] 클럭 → 가루(Y=+5) → 받침(Y=+4) → 드로퍼 작동 → 한 개씩 동쪽으로",
            "[분배] 각 드로퍼 아래 호퍼(Y=+2)가 끌어내려 화로 원료 슬롯으로",
            "[연료] 서쪽 연료 상자 → 연료 드로퍼 사슬 → 호퍼 → 옆에서 화로 연료 슬롯으로",
            "[산출] 화로 아래 호퍼(Y=0) → 동쪽 매끄러운 돌 상자",
        ],
        steps=[
            "1) 아래층부터 짓는다. Y=-1 바닥 → Y=0 산출 호퍼 줄 → 동쪽 끝 상자.",
            f"2) Y=+1 에 화로 {n}대, 그 남쪽 옆칸에 북향 연료 호퍼.",
            "3) Y=+2 아래방향 호퍼, Y=+3 동향 드로퍼 사슬 (두 줄: 원료/연료).",
            "4) 드로퍼 사슬 동쪽 끝에 상자를 반드시 놓는다.",
            "5) Y=+4 받침 블록, Y=+5 레드스톤 가루 두 줄. 동쪽 끝에 관측기 2개를 마주보게.",
            "6) 서쪽 끝(x=-1)에 아래방향 호퍼 3칸을 쌓아 생성부와 제련부를 잇는다.",
            "7) Y=+6 에 차단층을 깐다. 여기를 빼면 호퍼가 가루에 잠긴다.",
            f"8) Y=+7 에 서향 호퍼 {c}칸(생성기 수거), Y=+9 에 용암 수원 {c}개.",
            "9) z=-1, Y=+8 에 물 수원을 붓는다. 물 먼저, 용암 나중이다. "
            "생성칸(Y=+8, z=0)은 비워 둔 채로 둔다.",
            "10) 서쪽 연료 상자에 말린 켈프 블록이나 석탄을 넣는다.",
        ],
        rate=f"화로 {n}대 → 매끄러운 돌 시간당 {per_hour:,.0f}개. "
             f"제련 1단이라 연료는 시간당 {fuel_per_hour:,.0f}개분 "
             f"(조약돌 경로의 절반).",
        warnings=[
            "물을 먼저 붓고 용암을 나중에 부어야 한다. 순서를 바꾸면 흐르는 물이 "
            "용암 수원에 닿아 흑요석이 되어 양동이를 날린다.",
            "바닐라에 자동 블록 파괴기가 없어 생성칸 채굴은 수동이다. "
            "그 아래 수거부터 산출 상자까지는 전부 자동이다.",
            f"생성칸 {c}개는 이론상 시간당 {c * 2400:,.0f}개까지 낼 수 있지만 "
            f"실제 상한은 곡괭이질(시간당 3,600~7,200개)이다. "
            f"화로 {n}대가 먹는 양은 시간당 {per_hour:,.0f}개다.",
            "관측기 클럭은 빠르다. 서버가 버거우면 가루 줄에 중계기를 넣어 늦출 것.",
            f"연료는 자급되지 않는다. 켈프 팜(litematic kelpfarm)으로 말린 켈프 블록을 "
            f"대거나 석탄을 넣어야 한다.",
        ],
        manual_items=[
            f"용암 양동이 {c}개",
            f"물 양동이 {c}개",
            "연료 (말린 켈프 블록 권장 — 석탄의 2.5배)",
        ],
    )
