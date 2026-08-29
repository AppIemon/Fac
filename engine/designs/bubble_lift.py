"""물기둥 아이템 엘리베이터.

위키(Tutorials/Item transportation) 확인:
  "Using soul sand and bubble columns, it is possible to transport items upward
   quickly." — 영혼 모래 위에 물 수원을 채운 밀폐된 기둥을 만든다.

왜 필요한가:
  공장의 되먹임 고리는 공간적으로 반드시 한 번 아이템을 위로 올려야 한다.
    · 연료 고리: 건조 화로 → 말린 켈프 → 제작기 → 블록 → 다시 건조 화로 연료
    · 이끼 고리: 이끼 베드 → 퇴비통 → 뼛가루 → 다시 이끼 베드 발사기
  중력만으로는 둘 다 닫히지 않는다.

구성 (기둥은 (0,*,0), 주변은 벽):
  Y=y1     물먹임 호퍼  ← 떠오른 아이템을 받아 다음 공정으로
  Y=..     물 수원 (밀폐)
  Y=y0+1   물 수원 — 여기로 드로퍼가 아이템을 쏘아 넣는다
  Y=y0     영혼 모래
"""
from __future__ import annotations

from ..blocks import (EAST, NORTH, SOUL_SAND, SOUTH, STONE, WATER, dropper,
                      hopper, observer, redstone_wire)


def build_lift(s, x: int, z: int, y0: int, y1: int, out_facing: str = EAST,
               feed_from: str = "west", structure=STONE) -> None:
    """(x, y0..y1, z) 에 물기둥 엘리베이터를 놓는다.

    feed_from 쪽에 드로퍼와 자가 발진 클럭을 함께 놓아, 아래에서 들어온
    아이템을 기둥 안으로 쏘아 넣는다.
    """
    if y1 <= y0 + 1:
        raise ValueError("엘리베이터는 최소 2칸 이상이어야 한다")

    s.set(x, y0, z, SOUL_SAND)
    for y in range(y0 + 1, y1):
        s.set(x, y, z, WATER)
    s.set(x, y1, z, hopper(out_facing))        # 물먹임 호퍼 — 떠오른 아이템 수거

    # 기둥 밀폐 (물이 새면 기포가 서지 않는다)
    fx = x - 1 if feed_from == "west" else x + 1
    for y in range(y0, y1 + 1):
        for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, nz = x + dx, z + dz
            if (nx, nz) == (fx, z) and y == y0 + 1:
                continue                        # 투입용 드로퍼 자리
            if (nx, y, nz) not in s.blocks:
                s.set(nx, y, nz, structure)

    # 투입: 드로퍼가 물기둥 안으로 아이템을 쏜다.
    # 급전은 z축(뒤쪽)으로 뽑아, 드로퍼 뒤 x축을 아이템 투입용으로 비워 둔다.
    feed_dir = EAST if feed_from == "west" else "west"
    s.set(fx, y0 + 1, z, dropper(feed_dir))
    s.set(fx, y0 + 1, z - 1, structure)          # 가루 받침 = 드로퍼 급전원
    s.set(fx, y0 + 2, z - 1, redstone_wire(north="side"))
    s.set(fx, y0 + 2, z - 2, redstone_wire(south="side", north="side"))
    s.set(fx, y0 + 1, z - 2, structure)
    s.set(fx, y0 + 2, z - 3, observer(SOUTH))    # 자가 발진 클럭
    s.set(fx, y0 + 2, z - 4, observer(NORTH))
    s.set(fx, y0, z, structure)
    s.set(fx, y0, z - 1, structure)
