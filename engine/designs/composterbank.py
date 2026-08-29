"""퇴비통 뱅크 — 초목/이끼를 뼛가루로 바꾼다.

퇴비통 규칙 (위키 확인):
  · 성공 7회마다 뼛가루 1개. 성공률은 아이템마다 다르다
    (이끼 블록 65%, 짧은 풀 30%, 이끼 양탄자 30%, 큰 풀 50%,
     진달래 65%, 꽃 진달래 85%, 사탕수수/선인장 50%)
  · 위 호퍼가 아이템을 넣고, 아래 호퍼가 완성된 뼛가루를 뺀다.

단면도 (X축으로 통이 늘어선다):
  Y=+2  투입 라인 호퍼(동→)
  Y=+1  분배 호퍼(아래↓)
  Y= 0  퇴비통
  Y=-1  산출 호퍼(동→) ──> 뼛가루 상자
"""
from __future__ import annotations

from ..blocks import COMPOSTER, DOWN, EAST, NORTH, STONE, chest, hopper
from ..schematic import Schematic
from . import Design


def build(bins: int = 6, structure=STONE) -> Design:
    if bins < 1:
        raise ValueError("bins 는 1 이상이어야 한다")
    s = Schematic(
        name=f"composterbank_{bins}",
        description=f"퇴비통 뱅크 {bins}통 · 투입/산출 라인 분리",
    )
    for x in range(bins):
        s.set(x, 2, 0, hopper(EAST))     # 투입 라인
        s.set(x, 1, 0, hopper(DOWN))     # 위 라인에서 끌어와 퇴비통으로
        s.set(x, 0, 0, COMPOSTER)
        s.set(x, -1, 0, hopper(EAST))    # 완성된 뼛가루를 빼서 동쪽으로
        s.set(x, -2, 0, structure)
    s.set(0, 3, 0, chest(NORTH))         # 초목/이끼 투입구
    s.set(bins, -1, 0, chest(EAST))      # 뼛가루 산출
    s.set(bins, -2, 0, structure)

    s.note("호퍼는 바로 위 컨테이너에서 끌어온다. 분배 호퍼(Y=+1)가 라인(Y=+2)에서 끌어간다.")
    s.note("퇴비통은 위에서 넣고 아래에서 뺀다. 옆으로는 통하지 않는다.")

    return Design(
        schematic=s,
        principle="호퍼가 초목/이끼를 퇴비통에 넣는다 → 성공 7회마다 뼛가루 1개 → "
                  "아래 호퍼가 빼내 상자로",
        circuit=[
            "투입 상자(Y=+3) → 투입 라인 호퍼(Y=+2, 동쪽)",
            "분배 호퍼(Y=+1, 아래)가 바로 위 라인에서 끌어와 퇴비통에 투입",
            "퇴비통이 가득 차면 뼛가루 1개 생성",
            "아래 호퍼(Y=-1, 동쪽)가 뼛가루를 빼내 동쪽 상자로",
        ],
        steps=[
            f"1) 퇴비통 {bins}개를 동서로 한 줄 놓는다.",
            "2) 각 통 위에 아래를 향한 호퍼, 그 위에 동쪽을 향한 투입 라인을 올린다.",
            "3) 라인 맨 앞 위에 투입 상자를 놓는다.",
            "4) 각 통 아래에 동쪽을 향한 호퍼 줄을 깔고 끝에 뼛가루 상자를 놓는다.",
            "5) 이끼 블록(65%)처럼 성공률 높은 재료를 우선 넣는 게 효율이 좋다.",
        ],
        rate=f"통 {bins}개. 한 통의 상한은 호퍼 급이 속도(초당 2.5개)와 "
             "레벨 7 도달 후 1초 대기로 정해진다.",
        warnings=[
            "퇴비통은 옆면으로 아이템이 들어가지 않는다. 반드시 위 호퍼로 넣을 것.",
            "성공률이 낮은 재료(짧은 풀 30%)만 넣으면 처리량이 급감한다.",
        ],
        manual_items=[],
    )
