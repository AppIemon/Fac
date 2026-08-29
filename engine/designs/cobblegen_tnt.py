"""TNT 복제기 조약돌 생성기 — 참고 설계에서 그대로 가져온 모듈.

출처: 사용자가 제공한 `2.7万刷石机_稳定版` (5x7x5, 101블록).

왜 재유도하지 않고 복사했는가:
  TNT 복제는 틱 단위로 정밀한 장치다. 관측기 8개 · 피스톤 2개 · 중계기 4개 ·
  우는 흑요석 · 노트 블록의 배치와 지연값이 한 칸/한 틱만 어긋나도 작동하지
  않는다. 블록 덤프에서 원리를 되짚어 재구성하면 틀릴 가능성이 크고, 그걸
  검증할 방법이 없다. 검증된 원본을 그대로 쓰는 쪽이 정직하다.

원리 요약 (관측한 바):
  · Y=1  용암 3x3 코어 + 둘레 12칸이 조약돌 생성칸
  · Y=2~3 물먹임 참나무 잎이 링을 감싼다 — 흐르지 않는 물이라 용암 수원이
    흑요석이 되지 않으면서, 흐르는 용암이 닿으면 조약돌이 생긴다
  · Y=5  관측기·피스톤·TNT·우는 흑요석으로 만든 복제기가 TNT를 계속 뿜어
    생성된 조약돌을 부순다
  · Y=0  호퍼 12 + 상자 8 로 수거

TNT 복제는 바닐라의 오래된 버그성 메커니즘이다. 모장이 의도적으로 고치지 않고
남겨 두었지만, 서버에 따라 패치되어 있을 수 있다.
"""
from __future__ import annotations

import json
import pathlib

from ..blocks import Block
from ..schematic import Schematic
from . import Design

MODULE = pathlib.Path(__file__).resolve().parent.parent.parent / "reference" / "cobble_tnt_module.json"
RATE_PER_HOUR = 27000.0     # 원본 이름이 밝힌 수치 (2.7만/시간)


def load_module() -> tuple[list, dict]:
    doc = json.loads(MODULE.read_text(encoding="utf-8"))
    return doc["blocks"], doc


def build(units: int = 1, spacing: int = 7) -> Design:
    """units: 나란히 놓을 복제기 수 (Z축으로 spacing 간격)."""
    if units < 1:
        raise ValueError("units 는 1 이상이어야 한다")
    blocks, doc = load_module()
    sx, sy, sz = doc["size"]

    s = Schematic(
        name=f"cobblegen_tnt_x{units}",
        description=f"TNT 복제기 조약돌 생성기 {units}기 "
                    f"(원본: {doc['source']}) · 시간당 약 {RATE_PER_HOUR * units:,.0f}개",
    )
    for u in range(units):
        dz = u * spacing
        for x, y, z, bid, props in blocks:
            s.blocks[(x, y, z + dz)] = Block(bid, tuple(sorted(props.items())))

    s.note(f"원본 그대로다: {doc['source']} ({sx}x{sy}x{sz}, {len(blocks)}블록, "
           f"DataVersion {doc['data_version']}).")
    s.note("Y=5 의 레버가 복제기 스위치다. 지은 뒤 레버를 켜면 돈다.")
    s.note("TNT 복제는 서버에 따라 패치되어 있을 수 있다. 먼저 시험할 것.")

    return Design(
        schematic=s,
        principle="흐르는 용암이 물먹임 나뭇잎에 닿아 조약돌 생성 → TNT 복제기가 계속 "
                  "TNT를 뿜어 조약돌을 파괴 → 아래 호퍼가 수거. 채굴이 완전 자동이다.",
        circuit=[
            "Y=1 용암 3x3 코어에서 흘러나온 용암이 둘레 12칸에서 조약돌이 된다",
            "Y=2~3 물먹임 참나무 잎이 '흐르지 않는 물' 역할 — 흑요석 사고를 막는다",
            "Y=5 관측기+피스톤+우는 흑요석 조합이 TNT를 복제해 계속 터뜨린다",
            "터진 조약돌이 Y=0 호퍼 12개로 떨어져 상자 8개에 모인다",
            "※ 복제기 배선은 원본 그대로다. 한 칸만 어긋나도 작동하지 않는다.",
        ],
        steps=[
            "1) Litematica 로 통째로 붙여 넣는다. 손으로 옮겨 짓지 말 것 — "
            "관측기/중계기 방향과 지연값이 정확해야 한다.",
            "2) 용암과 물은 스케매틱에 포함되어 있지만, 유체는 Litematica 가 놓지 못하는 "
            "경우가 있으니 확인 후 양동이로 직접 채운다.",
            "3) 물을 먼저 붓고 그 자리에 나뭇잎을 놓아 물먹임으로 만든 뒤 용암을 붓는다.",
            "4) Y=5 레버를 켜면 복제기가 돈다.",
            "5) 조약돌이 안 나오면 레버를 껐다 켜서 복제기를 재시동한다.",
        ],
        rate=f"원본 표기 기준 시간당 약 {RATE_PER_HOUR:,.0f}개 x {units}기. "
             f"실측은 아니고 원본 이름(2.7만)이 밝힌 수치다.",
        warnings=[
            "TNT 복제는 바닐라의 버그성 메커니즘이다. 서버/버전에 따라 막혀 있을 수 있으니 "
            "먼저 시험해 볼 것.",
            "원본의 DataVersion 은 4438 (1.21.x 계열)이다. 26.2 에서 그대로 도는지는 "
            "확인하지 못했다.",
            "TNT 폭발은 주변 블록을 부순다. 다른 설비와 붙여 짓지 말고 최소 몇 칸 띄울 것.",
            "이 모듈은 내가 설계한 것이 아니라 제공된 참고 설계를 그대로 옮긴 것이다.",
        ],
        manual_items=["용암 양동이", "물 양동이", "TNT 1개 (복제 씨앗)"],
    )
