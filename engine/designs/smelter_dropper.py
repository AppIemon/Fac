"""드로퍼 분배 화로 배열.

호퍼 줄 분배의 문제:
  호퍼는 재고가 있으면 무조건 다음으로 밀어낸다. 그래서 앞쪽 화로가 먼저
  채워지고 뒤쪽은 굶는다. 화로가 많아질수록 편중이 심해진다.

드로퍼 사슬이 푸는 방식:
  드로퍼는 '펄스를 받을 때만' 한 개를 다음 드로퍼로 민다. 그래서 각 드로퍼가
  버퍼가 되고, 그 아래 호퍼가 자기 몫만 끌어내려 화로에 넣는다. 결과적으로
  아이템이 줄 전체에 고르게 퍼진다. 참고 설계 '32 Furnace Array' 가 이 방식이다.

단면도 (X축으로 화로가 늘어선다):

           z=0 (화로 열)              z=1 (연료 열)
 Y=+5   레드스톤 가루 ────────────────── 레드스톤 가루   (드로퍼 급전, 한 줄로 연결)
 Y=+4   받침 블록                      받침 블록
 Y=+3   드로퍼 사슬(동→)               연료 드로퍼 사슬(동→)
 Y=+2   호퍼(아래↓) 화로 원료 슬롯으로  호퍼(아래↓)
 Y=+1   화로                           호퍼(북↑) 화로 연료 슬롯으로
 Y= 0   산출 호퍼(동→) ──────────────> 산출 상자
"""
from __future__ import annotations

from .. import mechanics as M
from ..blocks import (DOWN, EAST, NORTH, STONE, WEST, chest, dropper, furnace,
                      hopper, observer, redstone_wire)
from ..schematic import Schematic
from . import Design


def build(furnaces: int = 8, structure=STONE) -> Design:
    if furnaces < 1:
        raise ValueError("furnaces 는 1 이상이어야 한다")
    n = furnaces
    s = Schematic(
        name=f"smelter_dropper_{n}",
        description=f"드로퍼 분배 화로 {n}대 · 균등 분배 · "
                    f"시간당 {n * M.FURNACE_ITEMS_PER_HOUR:,.0f}개",
    )

    for x in range(n):
        # 화로 열
        s.set(x, 3, 0, dropper(EAST))       # 분배 사슬
        s.set(x, 2, 0, hopper(DOWN))        # 드로퍼에서 끌어와 화로 위로
        s.set(x, 1, 0, furnace(NORTH))
        s.set(x, 0, 0, hopper(EAST))        # 화로 아래에서 산출을 끌어냄
        s.set(x, -1, 0, structure)
        s.set(x, 4, 0, structure)           # 가루 받침 = 드로퍼 급전원
        s.set(x, 5, 0, redstone_wire(
            south="side",
            east="side",                       # 동쪽 끝에는 클럭 관측기가 붙는다
            west="side" if x > 0 else "none"))

        # 연료 열
        s.set(x, 3, 1, dropper(EAST))
        s.set(x, 2, 1, hopper(DOWN))
        s.set(x, 1, 1, hopper(NORTH))       # 옆에서 화로 연료 슬롯으로
        s.set(x, 0, 1, structure)
        s.set(x, -1, 1, structure)
        s.set(x, 4, 1, structure)
        s.set(x, 5, 1, redstone_wire(
            north="side",
            east="side" if x < n - 1 else "none",
            west="side" if x > 0 else "none"))

    # 서쪽: 투입구 + 드로퍼 사슬 시작
    for z, label in ((0, "원료"), (1, "연료")):
        s.set(-1, 4, z, chest(NORTH))       # 투입 상자
        s.set(-1, 3, z, hopper(EAST))       # 첫 드로퍼로 밀어 넣는다
        s.set(-1, 2, z, structure)
        s.set(-1, 1, z, structure)
        s.set(-1, 0, z, structure)
        s.set(-1, -1, z, structure)

    # 동쪽: 사슬 끝은 반드시 컨테이너여야 한다 (공기면 아이템을 밖으로 뱉는다)
    s.set(n, 3, 0, chest(EAST))
    s.set(n, 3, 1, chest(EAST))
    s.set(n, 0, 0, chest(EAST))             # 산출 상자
    s.set(n, -1, 0, structure)
    s.set(n, -1, 1, structure)

    # 관측기 2개로 만든 자가 발진 클럭. 동쪽 끝에 둔다 —
    # 서쪽 끝은 투입 상자 자리라 위를 막으면 상자가 열리지 않는다.
    s.set(n, 5, 0, observer(EAST))          # 동쪽(B)을 본다, 출력은 서쪽(가루)
    s.set(n + 1, 5, 0, observer(WEST))      # 서쪽(A)을 본다

    s.note("드로퍼 사슬 끝은 상자다. 드로퍼가 공기를 향하면 아이템을 월드로 뱉는다.")
    s.note("호퍼는 바로 위 컨테이너에서 끌어온다 — 드로퍼가 그 컨테이너 역할을 한다.")
    s.note("관측기 2개가 서로를 마주보면 자가 발진 클럭이 된다. 별도 점화가 필요 없다.")

    per_hour = n * M.FURNACE_ITEMS_PER_HOUR
    return Design(
        schematic=s,
        principle=f"드로퍼 사슬이 원료를 줄 전체에 고르게 밀어 넣고, 각 드로퍼 아래 "
                  f"호퍼가 자기 화로 몫만 끌어내린다. 화로 {n}대 병렬.",
        circuit=[
            "관측기 2개(서쪽 끝)가 서로를 마주보며 자가 발진 → 가루 줄(Y=+5)을 두드림",
            "가루 → 받침 블록(Y=+4) 약한 급전 → 인접 드로퍼(Y=+3) 작동",
            "드로퍼가 아이템을 동쪽 다음 드로퍼로 한 개씩 민다 (버퍼 = 균등 분배)",
            "각 드로퍼 아래 호퍼(Y=+2)가 위에서 끌어와 화로 원료 슬롯으로",
            "연료 열도 같은 방식. 다만 마지막에 옆(북)에서 넣어 연료 슬롯으로 간다",
            "화로 아래 호퍼(Y=0)가 완성품을 끌어내 동쪽 상자로",
        ],
        steps=[
            f"1) 동서(X) 방향으로 화로 {n}대를 한 줄로 놓는다 (Y=+1).",
            "2) 화로 아래에 동쪽을 향한 산출 호퍼 줄 → 끝에 상자.",
            "3) 화로 위에 아래를 향한 호퍼, 그 위에 동쪽을 향한 드로퍼 사슬.",
            "4) 화로 남쪽 옆칸(z=1)에 북쪽 호퍼 → 그 위 아래방향 호퍼 → 그 위 연료 드로퍼 사슬.",
            "5) 드로퍼 사슬 위에 받침 블록을 깔고 그 위에 레드스톤 가루를 한 줄 잇는다.",
            "6) 서쪽 끝에 투입 상자 2개(원료/연료)와 각각 동쪽 호퍼를 놓아 사슬에 밀어 넣는다.",
            "7) 동쪽 끝 사슬 자리에 상자를 놓는다. 비워 두면 아이템이 밖으로 튀어나온다.",
            "8) 서쪽 끝에 관측기 2개를 마주보게 놓으면 클럭이 저절로 돈다.",
        ],
        rate=f"화로 {n}대 → 시간당 {per_hour:,.0f}개 (연속 가동 기준)",
        warnings=[
            "관측기 클럭은 매우 빠르다. 서버가 버거우면 가루 줄 중간에 중계기를 넣어 늦출 것.",
            "드로퍼 사슬 끝을 상자로 막지 않으면 아이템이 월드로 뱉어져 사라진다.",
            f"호퍼 1줄은 시간당 9,000개까지다. 화로 25대를 넘기면 산출 줄도 나눠야 한다.",
        ],
        manual_items=[],
    )
