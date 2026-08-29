"""제자리 돌 생성기 뱅크.

유체 규칙 (위키 확인):
  "If lava flows into a water block, the water turns into stone.
   Due to rule 1, this can only occur if the lava flows into water from above."

즉 용암이 '위에서 아래로' 물에 흘러들면 그 물이 돌이 된다. 조약돌이 아니라
곧바로 '돌'이 나오므로 매끄러운 돌까지 제련 한 번만 하면 된다
(조약돌 경로는 두 번 구워야 한다).

흑요석 사고가 나지 않는 이유:
  흑요석은 "물이 용암 '수원'의 위 또는 옆에 닿을 때" 생긴다.
  이 설계에서 물은 항상 용암 수원의 '아래'에 있고, 물 수원은 용암과 대각선이라
  절대 인접하지 않는다.

단면도 (X축, 생성칸은 Z축으로 반복):

        x=-1     x=0        x=1            x=2          x=3
 Y=+1   돌       돌         용암 수원       돌           돌
 Y= 0   돌       물 수원    생성칸(돌)      돌           돌
 Y=-1   돌       돌         호퍼(남→)       돌           돌
"""
from __future__ import annotations

from ..blocks import GLASS, LAVA, SOUTH, STONE, WATER, chest, hopper
from ..schematic import Schematic
from . import Design


def build(cells: int = 6, structure=STONE) -> Design:
    if cells < 1:
        raise ValueError("cells 는 1 이상이어야 한다")

    s = Schematic(
        name=f"stonegen_{cells}",
        description=f"제자리 돌 생성기 {cells}칸 · 용암이 위에서 물로 흘러 '돌' 생성 · 호퍼 수거",
    )

    for z in range(cells):
        s.fill(-1, -1, z, -1, 1, z, structure)     # 서쪽 벽
        s.set(0, -1, z, structure)
        s.set(0, 0, z, WATER)                      # 물 수원 (생성칸으로 흘러든다)
        s.set(0, 1, z, structure)

        s.set(1, -1, z, hopper(SOUTH))             # 생성칸 바로 아래 수거 호퍼
        # (1, 0, z) 는 비워 둔다 — 여기에 돌이 생성된다
        s.set(1, 1, z, LAVA)                       # 용암 수원 (아래로 흘러든다)

        s.fill(2, -1, z, 2, 1, z, structure)       # 동쪽 벽
        s.fill(3, -1, z, 3, 1, z, structure)

    for z in (-1, cells):                          # 남북 끝막이
        s.fill(-1, -1, z, 3, 1, z, structure)
    s.set(1, -1, cells, chest(SOUTH))
    s.set(1, 0, cells, GLASS)                      # 상자 위는 불투명 금지

    s.note("용암 수원은 생성칸 '바로 위'에 있고 물 수원은 옆에 있다. "
           "물이 용암 수원의 위나 옆에 닿지 않으므로 흑요석이 되지 않는다.")
    s.note("조약돌이 아니라 '돌'이 나온다 → 매끄러운 돌까지 제련 한 번이면 된다.")
    s.note("이끼는 조약돌을 변환하지 못하므로, 이끼 베드에 넣을 돌도 여기서 나온다.")

    return Design(
        schematic=s,
        principle="용암 수원이 아래 생성칸으로 흘러들고, 옆 물 수원이 채운 물과 만나 "
                  "'돌'이 된다 → 캐면 즉시 재생성 → 바로 아래 호퍼가 수거",
        circuit=[
            "물 수원(x=0) → 생성칸(x=1, Y=0) 을 물로 채움",
            "용암 수원(x=1, Y=+1) → 아래로 흘러 생성칸의 물에 진입",
            "'위에서 물로 흘러든 용암' → 물이 돌로 변한다",
            "돌을 캐면 물이 다시 채우고 용암이 다시 내려와 재생성",
            "※ 물은 항상 용암 수원의 아래에 있다 → 흑요석 조건(위/옆)에 걸리지 않는다",
        ],
        steps=[
            f"1) 남북(Z) 방향 {cells}칸 뱅크다. Y=-1 에 호퍼 줄을 깔고 남쪽 끝 상자로 연결한다.",
            "2) x=0 (Y=0) 에 물 수원을 붓는다.",
            "3) x=1 (Y=+1) 에 용암 수원을 붓는다. 생성칸(x=1, Y=0)은 비워 둔 상태로.",
            "4) 물이 생성칸을 채우고 용암이 내려오면 돌이 생긴다.",
            "5) 플레이어는 서쪽이나 위에서 생성칸을 캔다. 캘 때마다 재생성된다.",
        ],
        rate=f"{cells}칸. 재생성은 용암 확산 주기(30틱)에 걸리고, 실제 상한은 곡괭이질 속도다.",
        warnings=[
            "물을 먼저, 용암을 나중에 부어야 한다. 순서를 바꾸면 흐르는 물이 "
            "용암 수원에 닿아 흑요석이 될 수 있다.",
            "생성칸(x=1, Y=0)에 블록을 놓으면 안 된다. 비어 있어야 돌이 생긴다.",
            "바닐라에 자동 블록 파괴기가 없어 채굴은 수동이다. 수거부터는 자동이다. "
            "(참고 설계는 TNT 복제로 이걸 자동화한다)",
            "캔 직후 용암이 다시 내려오기 전에 호퍼가 아이템을 주워야 한다. "
            "호퍼 8틱 vs 용암 확산 30틱이라 보통 호퍼가 이긴다.",
        ],
        manual_items=[f"용암 양동이 {cells}개", f"물 양동이 {cells}개"],
    )
