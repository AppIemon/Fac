"""통합 매끄러운 돌 공장 (선택지 2).

구성
  · TNT 복제 조약돌 생성기 (참고 설계 그대로, 폭발 격리를 위해 따로 떨어뜨림)
  · 2단 제련: 조약돌 → 돌 → 매끄러운 돌 (드로퍼 균등 분배)
  · 연료 자급: 뼛가루 켈프 → 건조 화로 → 제작기 → 말린 켈프 블록
  · 뼛가루 자급: 다층 이끼 베드(제자리 돌 재생성) → 퇴비통 뱅크

중력 순서로 탑처럼 쌓는다. 되먹임 고리 두 곳만 물기둥 엘리베이터로 올린다.

  Y 높음  이끼 베드        (뼛가루 → 이끼 수확물)
          퇴비통 뱅크      (수확물 → 뼛가루)   ── 리프트 ①로 베드 발사기에 되돌림
          뼛가루 켈프 팜   (뼛가루 → 켈프)
          건조 화로        (켈프 → 말린 켈프)
          제작기           (말린 켈프 9 → 블록) ── 리프트 ②로 건조 연료에 되돌림
          1단 화로         (조약돌 → 돌)
          2단 화로         (돌 → 매끄러운 돌)
  Y 낮음  산출 상자

이끼 베드는 제자리 돌 재생성(용암이 위에서 물로)을 내장해 돌을 밖에서 받지
않는다. 그래서 조약돌 라인과 뼛가루 라인이 자원을 다투지 않는다.
"""
from __future__ import annotations

import math

from .. import mechanics as M
from ..blocks import (DOWN, EAST, GLASS, NORTH, SOUTH, STONE, WEST, chest,
                      dropper, furnace, hopper, observer, redstone_wire)
from ..schematic import Schematic
from . import Design, composterbank, kelpfarm_bonemeal, mossbed_auto
from . import cobblegen_tnt
from .bubble_lift import build_lift

DRIED_KELP_BLOCK_SMELTS = 20
KELP_PER_BLOCK = 9


def sizing(furnaces: int) -> dict:
    """화로 수(단당)에서 나머지 설비 규모를 역산한다."""
    out = furnaces * M.FURNACE_ITEMS_PER_HOUR
    smelts = 2 * out                                   # 2단 제련
    net = DRIED_KELP_BLOCK_SMELTS - KELP_PER_BLOCK     # 블록당 순 11개분
    blocks = smelts / net
    kelp = blocks * KELP_PER_BLOCK
    ay = mossbed_auto.yields()
    # 이끼 고리: 뼛가루 1개 넣어 ay['bonemeal_est'] 개가 나온다
    net_bm = ay["bonemeal_est"] - 1.0
    cycles = kelp / net_bm
    return {
        "smooth_stone_per_hour": out,
        "smelts_per_hour": smelts,
        "blocks_per_hour": blocks,
        "kelp_per_hour": kelp,
        "drying_furnaces": max(1, math.ceil(kelp / M.FURNACE_ITEMS_PER_HOUR)),
        "moss_cycles_per_hour": cycles,
        "moss_beds": max(1, math.ceil(cycles / 360.0)),
        "bonemeal_per_hour": cycles * ay["bonemeal_est"],
    }


def _smelt_bank(s, x0, n, yf, z0, structure, feed=EAST, fuel=EAST):
    """드로퍼 분배 화로 뱅크. yf 기준 위로 호퍼/드로퍼/받침/가루."""
    yh, yd, ys, yr = yf + 1, yf + 2, yf + 3, yf + 4
    for i in range(n):
        x = x0 + i
        s.set(x, yd, z0, dropper(feed))
        s.set(x, yh, z0, hopper(DOWN))
        s.set(x, yf, z0, furnace(NORTH))
        s.set(x, ys, z0, structure)
        s.set(x, yr, z0, redstone_wire(south="side", east="side",
                                       west="side" if i else "none"))
        s.set(x, yd, z0 + 1, dropper(fuel))
        s.set(x, yh, z0 + 1, hopper(DOWN))
        s.set(x, yf, z0 + 1, hopper(NORTH))
        s.set(x, ys, z0 + 1, structure)
        s.set(x, yr, z0 + 1, redstone_wire(north="side", east="side",
                                           west="side" if i else "none"))
        s.set(x, yf - 1, z0 + 1, structure)
    s.set(x0 + n, yr, z0, observer(EAST))
    s.set(x0 + n + 1, yr, z0, observer(WEST))
    s.set(x0 + n, yd, z0, chest(EAST))
    s.set(x0 + n, yd, z0 + 1, chest(EAST))


def _drop_column(s, x, z, y_from, y_to, structure):
    """y_from 에서 y_to 까지 아래로 내리는 호퍼 기둥."""
    for y in range(y_to + 1, y_from + 1):
        s.set(x, y, z, hopper(DOWN))


def build(furnaces: int = 3, structure=STONE) -> Design:
    if furnaces < 1:
        raise ValueError("furnaces 는 1 이상이어야 한다")
    n = furnaces
    sz = sizing(n)
    dry = sz["drying_furnaces"]
    beds = sz["moss_beds"]
    bins = max(2, math.ceil(sz["moss_cycles_per_hour"] / 213.0))

    s = Schematic(
        name=f"full_factory_f{n}",
        description=f"통합 매끄러운 돌 공장 · TNT 조약돌 + 2단 제련 + 켈프 연료 + "
                    f"이끼 뼛가루 (시간당 {sz['smooth_stone_per_hour']:,.0f}개)",
    )

    # ---- 제련 본체 (z=0,1) ----
    _smelt_bank(s, 0, n, 0, 0, structure)              # 2단: 돌 → 매끄러운 돌
    _smelt_bank(s, 0, n, 8, 0, structure)              # 1단: 조약돌 → 돌
    for x in range(n):
        s.set(x, -1, 0, hopper(EAST))                  # 매끄러운 돌 산출
        s.set(x, -2, 0, structure)
        s.set(x, -1, 1, structure)
        s.set(x, 7, 0, hopper(WEST))                   # 1단 산출 → 서쪽 하강
        s.set(x, 7, 1, structure)
        s.set(x, 5, 0, structure)                      # 차단층
        s.set(x, 5, 1, structure)
    s.set(n, -1, 0, chest(EAST))
    s.set(n, -2, 0, structure)
    # 1단 산출 → 2단 드로퍼 사슬 (가루에서 두 칸 떼고 하강)
    s.set(-1, 7, 0, hopper(WEST))
    _drop_column(s, -2, 0, 7, 2, structure)
    s.set(-2, 7, 0, hopper(DOWN))
    s.set(-2, 2, 0, hopper(EAST))
    s.set(-1, 2, 0, hopper(EAST))
    for y in (3, 4, 5, 6):
        s.set(-1, y, 0, structure)

    # ---- 건조 화로 + 제작기 (z=3,4) ----
    DY = 16
    _smelt_bank(s, 0, dry, DY, 3, structure)
    for i in range(dry):
        s.set(i, DY - 1, 3, hopper(WEST))              # 말린 켈프 회수
        s.set(i, DY - 1, 4, structure)
    CX = -1
    s.set(CX, DY - 1, 3, hopper(DOWN))
    s.set(CX, DY - 2, 3, hopper(DOWN))
    from ..blocks import B
    s.set(CX, DY - 3, 3, B("crafter", crafting="false", orientation="west_up",
                           triggered="false"))
    s.set(CX - 1, DY - 3, 3, hopper(WEST))             # 제작기 산출
    s.set(CX, DY - 4, 3, structure)
    s.set(CX, DY - 3, 4, structure)
    s.set(CX, DY - 4, 4, structure)
    # 제작기 클럭
    s.set(CX, DY - 4, 2, redstone_wire(west="side"))
    s.set(CX - 1, DY - 4, 2, observer(EAST))
    s.set(CX - 2, DY - 4, 2, observer(WEST))
    s.set(CX, DY - 3, 2, structure)

    # 제작기 산출(블록) → ① 건조 연료로 리프트 ② 아래 제련 연료로 중력
    LX = CX - 3
    build_lift(s, LX, 3, DY - 4, DY + 2, out_facing=EAST, feed_from="east",
               structure=structure)
    # 리프트 상단 → 건조 연료 사슬. 리프트가 벽으로 채운 자리를 덮어쓴다.
    for x in range(LX + 1, 0):
        s.set(x, DY + 2, 3, hopper(EAST))
    # 리프트 상단에서 넘친 연료는 아래 제련 연료 사슬로
    s.set(dry, DY + 2, 4, hopper(EAST))
    _drop_column(s, dry + 1, 4, DY + 2, 12, structure)
    s.set(dry + 1, DY + 2, 4, hopper(DOWN))
    s.set(dry + 1, 12, 4, hopper(WEST))
    for x in range(dry, -1, -1):
        s.set(x, 12, 4, hopper(WEST))
    # z=1 은 1단 가루 줄(Y=12)과 맞닿아 호퍼가 잠긴다. z=2 로 우회한다.
    s.set(-1, 12, 4, hopper(NORTH))
    s.set(-1, 12, 3, hopper(NORTH))
    s.set(-1, 12, 2, hopper(WEST))
    s.set(-2, 12, 2, hopper(DOWN))
    _drop_column(s, -2, 2, 12, 10, structure)
    s.set(-2, 10, 2, hopper(NORTH))
    s.set(-2, 10, 1, hopper(EAST))
    s.set(-1, 10, 1, hopper(EAST))                     # 1단 연료 사슬 투입
    for y in (11, 12):
        if (-1, y, 1) not in s.blocks:
            s.set(-1, y, 1, structure)

    # ---- 뼛가루 켈프 팜 (z=6..10) ----
    KY = 24
    kelp = kelpfarm_bonemeal.build(columns=2, structure=structure)
    s.paste(kelp.schematic, dx=0, dy=KY, dz=7, label="켈프")
    # 켈프 산출 → 건조 드로퍼 사슬로 하강
    s.set(3, KY + 4, 8, hopper(WEST))
    for x in range(2, -2, -1):
        s.set(x, KY + 4, 8, hopper(WEST))
    s.set(-2, KY + 4, 8, hopper(NORTH))
    for z in range(7, 3, -1):
        s.set(-2, KY + 4, z, hopper(NORTH))
    _drop_column(s, -2, 3, KY + 4, DY + 2, structure)
    s.set(-2, DY + 2, 3, hopper(EAST))

    # ---- 이끼 베드 + 퇴비통 (z=12..) ----
    MY = 40
    for b in range(beds):
        bed = mossbed_auto.build()
        s.paste(bed.schematic, dx=b * 11, dy=MY, dz=12, label=f"이끼베드{b}")

    # 퇴비통 두 뱅크: 하나는 켈프로(중력), 하나는 베드 발사기로(리프트)
    half = max(1, bins // 2)
    CY_K, CY_M = 34, 34
    comp_k = composterbank.build(bins=half, structure=structure)
    s.paste(comp_k.schematic, dx=0, dy=CY_K, dz=24, label="퇴비통-켈프")
    comp_m = composterbank.build(bins=max(1, bins - half), structure=structure)
    s.paste(comp_m.schematic, dx=0, dy=CY_M, dz=27, label="퇴비통-베드")

    # (1) 이끼 베드 산출 → 퇴비통 투입 (아래로, 중력)
    for b in range(beds):
        bx = 7 + b * 11
        s.set(bx, MY - 2, 19, hopper(DOWN))            # 베드 상자 아래
        s.set(bx, MY - 3, 19, hopper(SOUTH))
        for z in range(20, 24):
            s.set(bx, MY - 3, z, hopper(SOUTH))
        for x in range(bx, 1, -1):
            s.set(x, MY - 3, 24, hopper(WEST))
        s.set(1, MY - 3, 24, hopper(WEST))             # 켈프용 뱅크 투입 상자로
    # 남는 수확물을 베드용 뱅크로 넘긴다
    s.set(1, MY - 3, 27, hopper(WEST))
    for z in range(25, 27):
        s.set(1, MY - 3, z, hopper(SOUTH))

    # (2) 켈프용 퇴비통 산출 → 켈프 뼛가루 투입 (중력)
    s.set(half, CY_K - 2, 24, hopper(NORTH))
    for z in range(23, 7, -1):
        s.set(half, CY_K - 2, z, hopper(NORTH))
    for x in range(half, -1, -1):
        s.set(x, CY_K - 2, 7, hopper(WEST))
    s.set(-1, CY_K - 2, 7, hopper(DOWN))
    _drop_column(s, -1, 7, CY_K - 2, KY + 5, structure)

    # (3) 베드용 퇴비통 산출 → 리프트 ① → 이끼 베드 발사기
    mb = max(1, bins - half)
    s.set(mb, CY_M - 2, 27, hopper(WEST))
    for x in range(mb - 1, -3, -1):
        s.set(x, CY_M - 2, 27, hopper(WEST))
    # 리프트 투입은 y0+1 이다. 퇴비통 산출선(Y=CY_M-2)과 맞추려면 y0 를 한 칸 낮춘다.
    TOP = MY + 11                                       # 베드 꼭대기보다 위
    build_lift(s, -4, 27, CY_M - 3, TOP, out_facing=EAST, feed_from="east",
               structure=structure)
    for x in range(-3, 1):
        s.set(x, TOP, 27, hopper(EAST))
    s.set(1, TOP, 27, hopper(NORTH))
    for z in range(26, 12, -1):
        s.set(1, TOP, z, hopper(NORTH))
    s.set(1, TOP, 12, hopper(EAST))                     # 분배선으로 꺾는다
    # 베드 위를 지나는 분배선. 각 베드는 그 아래 호퍼가 '위 컨테이너에서 끌어'간다.
    for x in range(2, 11 * beds):
        s.set(x, TOP, 12, hopper(EAST))
    s.set(11 * beds, TOP, 12, chest(EAST))              # 분배선 끝 (넘침)
    for b in range(beds):
        wx = -1 + b * 11                                # 베드 서쪽 벽 = 급이 통로 입구
        s.set(wx, TOP - 1, 12, hopper(DOWN))            # 위 분배선에서 끌어온다
        _drop_column(s, wx, 12, TOP - 1, MY + 2, structure)

    s.note("TNT 조약돌 생성기는 폭발 때문에 이 스케매틱에 넣지 않았다. "
           "따로 지어(litematic cobblegen_tnt) 호퍼 줄로 1단 드로퍼 사슬에 물릴 것.")
    s.note("되먹임 두 곳만 물기둥 엘리베이터로 올린다. 나머지는 전부 중력이다.")
    s.note("이끼 베드는 제자리 돌 재생성을 내장해 돌을 밖에서 받지 않는다.")

    return Design(
        schematic=s,
        principle="TNT 조약돌 → 2단 제련 → 매끄러운 돌. 연료는 뼛가루 켈프 → 건조 → "
                  "제작기로, 뼛가루는 다층 이끼 베드 → 퇴비통으로 자급한다.",
        circuit=[
            "[돌] TNT 생성기(별도) → 1단 화로 → 돌 → 2단 화로 → 매끄러운 돌 → 상자",
            "[연료] 켈프 → 건조 화로 → 말린 켈프 → 제작기 → 블록",
            "[연료] 블록 → 리프트 ② → 건조 연료 사슬, 넘친 분량은 중력으로 제련 연료로",
            "[뼛가루] 이끼 베드 → 퇴비통 → 뼛가루 → 켈프 발사기",
            "[뼛가루] 일부는 리프트 ①로 베드 발사기에 되돌아간다",
        ],
        steps=[
            "1) 아래층(2단 화로)부터 위로 쌓는다.",
            f"2) TNT 조약돌 생성기는 별도 스케매틱이다. 최소 15칸 이상 떨어뜨려 짓고 "
            f"호퍼 줄로 1단 드로퍼 사슬(Y=10, z=0)에 물린다.",
            "3) 물기둥 엘리베이터는 영혼 모래를 먼저 놓고 위를 물 수원으로 채운다. "
            "옆이 한 칸이라도 새면 기포가 서지 않는다.",
            "4) 이끼 베드의 용암·물을 채우고 씨앗 이끼와 뼛가루를 넣어 점화한다.",
            "5) 켈프를 심고, 연료 상자에 말린 켈프 블록 몇 개를 넣어 고리를 돌린다.",
        ],
        rate=f"매끄러운 돌 시간당 {sz['smooth_stone_per_hour']:,.0f}개 · "
             f"켈프 {sz['kelp_per_hour']:,.0f}개/시간 · "
             f"이끼 회전 {sz['moss_cycles_per_hour']:,.0f}회/시간",
        warnings=[
            "TNT 폭발은 주변을 부순다. 조약돌 생성기를 본체에 붙이지 말 것.",
            "TNT 복제는 서버에 따라 막혀 있을 수 있다.",
            "물기둥 엘리베이터의 아이템 운반은 위키가 확인해 주지만, "
            "상단 수거(물먹임 호퍼)는 표준 방식을 따른 것이지 문서로 확인한 건 아니다.",
            "이끼 베드 산출량은 추정이다. 평평한 7x7 변환율(27/49)을 다층에 적용했다.",
            f"청크 로딩: 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다. "
            "공장 전체가 AFK 범위 안이거나 /forceload 되어야 한다.",
        ],
        manual_items=["용암/물 양동이", "켈프·이끼 초기 식재", "말린 켈프 블록 (고리 점화)"],
    )
