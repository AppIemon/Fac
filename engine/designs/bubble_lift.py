"""물기둥 아이템 엘리베이터 (기둥만).

위키(Tutorials/Item transportation) 확인:
  "Using soul sand and bubble columns, it is possible to transport items upward
   quickly." — 영혼 모래 위에 물 수원을 채운 밀폐된 기둥을 만든다.

왜 필요한가:
  공장의 되먹임 고리는 공간적으로 반드시 한 번 아이템을 위로 올려야 한다.
    · 연료 고리: 건조 화로 → 말린 켈프 → 제작기 → 블록 → 다시 건조 화로 연료
    · 이끼 고리: 이끼 베드 → 퇴비통 → 뼛가루 → 다시 이끼 베드 발사기
  중력만으로는 둘 다 닫히지 않는다.

구성 (기둥은 (x,*,z), 주변은 벽):
  Y=y1     호퍼        ← 떠오른 아이템을 받아 다음 공정으로
  Y=..     물 수원 (밀폐)
  Y=y0+1   물 수원 — 여기로 드로퍼가 아이템을 쏘아 넣는다
  Y=y0     영혼 모래

드로퍼와 그 클럭은 부르는 쪽이 놓는다. 공장마다 아이템이 들어오는 방향이
달라서 여기서 같이 놓으면 자리가 겹치기 때문이다. 드로퍼를 먼저 놓고 부르면
밀폐 루프가 그 칸을 건드리지 않는다.

주의: 기둥 옆에 호퍼를 두지 말 것. 밀폐가 비면 기포가 서지 않는다.
"""
from __future__ import annotations

from ..blocks import SOUL_SAND, STONE, WATER, collect_hopper


def lift_column(s, x: int, z: int, y0: int, y1: int, out_facing: str,
                structure=STONE) -> None:
    """(x, y0..y1, z) 에 물기둥을 세우고 사방을 막는다.

    y0    영혼 모래
    y0+1.. 물 수원 (여기 어딘가로 드로퍼가 쏘아 넣는다)
    y1    수거 호퍼 (out_facing 쪽으로 내보낸다)
    """
    if y1 <= y0 + 1:
        raise ValueError("엘리베이터는 최소 2칸 이상이어야 한다")

    s.set(x, y0, z, SOUL_SAND)
    for y in range(y0 + 1, y1):
        s.set(x, y, z, WATER)
    # 꼭대기 호퍼는 반드시 물먹임이어야 한다. 그래야 기포 기둥이 호퍼 칸까지
    # 이어져 아이템이 그 안으로 떠올라 수거된다. 마른 호퍼면 아이템이 한 칸
    # 아래 물 표면에서 맴돌다 만다.
    s.set(x, y1, z, collect_hopper(out_facing))

    # 밀폐 — 이미 뭔가 놓인 칸(드로퍼·이웃 모듈의 벽)은 건드리지 않는다.
    for y in range(y0, y1 + 1):
        for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            if (x + dx, y, z + dz) not in s.blocks:
                s.set(x + dx, y, z + dz, structure)
