"""통합 매끄러운 돌 공장 — 한 덩어리로 압축한 판.

구성은 그대로다.
  · TNT 복제 조약돌 생성기 (참고 설계 그대로, 폭발 격리를 위해 따로 떨어뜨림)
  · 2단 제련: 조약돌 → 돌 → 매끄러운 돌
  · 연료 자급: 뼛가루 켈프 → 건조 화로 → 제작기 → 말린 켈프 블록
  · 뼛가루 자급: 다층 이끼 베드(제자리 돌 재생성) → 퇴비통

부피를 어떻게 줄였나 (39x54x30 = 63,180 → 16x39x9 = 5,616, 약 11배)
  1. 흩어져 있던 모듈을 같은 X/Z 발자국 안에 겹쳐 쌓았다. 예전 판은 켈프를
     z=7, 베드를 z=12, 퇴비통을 z=24 에 두어 빈 공기가 96%였다.
  2. 화로 뱅크에서 드로퍼 분배·받침·가루·관측기 클럭 네 층을 걷어냈다.
     화로가 한 대뿐이면 균등 분배가 필요 없고, 두 대여도 앞 화로가 64개를
     물면 나머지가 뒤로 흘러간다. 한 뱅크가 6층 → 4층이 되고 회로가 0이다.
  3. 물기둥 엘리베이터 두 개를 짧게 줄였다(8칸, 12칸). 되먹임 고리가
     두 개라 두 개는 반드시 필요하다.
  4. 갈래는 '줄 아래에 호퍼를 붙여 끌어가게' 만들었다. 한쪽이 막혀도 나머지가
     그대로 흐른다 — 상자를 두 개 두고 우선순위를 다투게 하지 않는다.

층 구성 (Y가 낮은 곳이 산출구다)
  Y=-1..2   2단 화로   돌 → 매끄러운 돌      → 산출 상자
  Y= 4..7   1단 화로   조약돌 → 돌            ← TNT 생성기(별도)
  Y= 6      제작기     말린 켈프 9 → 블록     → 리프트(2)로 연료선에
  Y= 9..13  건조 화로  켈프 → 말린 켈프
  Y=14..20  켈프 팜    뼛가루 → 켈프
  Y=21      뼛가루 분배 (켈프 / 이끼 베드 두 갈래)
  Y=22..27  퇴비통     이끼 → 뼛가루
  Y=27..37  이끼 베드  뼛가루 → 이끼 (돌은 제자리에서 다시 만든다)
"""
from __future__ import annotations

import math

from .. import mechanics as M
from ..blocks import (B, DOWN, EAST, NORTH, SOUTH, STONE, WEST, chest, dropper,
                      furnace, hopper, observer, redstone_wire)
from ..schematic import Schematic
from . import Design, composterbank, kelpfarm_bonemeal, mossbed_auto
from .bubble_lift import lift_column

DRIED_KELP_BLOCK_SMELTS = 20
KELP_PER_BLOCK = 9

# 층 높이 (화로는 yf 기준으로 yf-1 .. yf+2 를 쓴다)
Y2, Y1, YD = 0, 5, 10      # 2단 / 1단 / 건조 화로
YT = 13                    # 건조 위 이송층
KY = 15                    # 켈프 팜 (모듈 원점, 실제 점유 14..20)
YB = 21                    # 뼛가루 분배선
CY = 24                    # 퇴비통 (모듈 원점, 실제 점유 22..27)
MY = 29                    # 이끼 베드 (모듈 원점, 실제 점유 27..37)
CX = -5                    # 퇴비통 뱅크 서쪽 끝
COMPOSTER_HARVESTS_PER_HOUR = 213.0


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
        "composters": max(1, math.ceil(cycles / COMPOSTER_HARVESTS_PER_HOUR)),
        "bonemeal_per_hour": cycles * ay["bonemeal_est"],
    }


def _bank(s, n, yf, structure, feed, fuel, out):
    """화로 뱅크 — 회로가 없다.

      Y+2  투입선 / 연료선 (가로 호퍼)
      Y+1  아래방향 호퍼 (바로 위 줄에서 끌어간다)
      Y    화로 / 옆구리 연료 호퍼
      Y-1  산출선 / 받침
    """
    for x in range(n):
        s.set(x, yf, 0, furnace(NORTH))
        s.set(x, yf + 1, 0, hopper(DOWN))
        s.set(x, yf + 2, 0, hopper(feed))
        s.set(x, yf, 1, hopper(NORTH))          # 옆구리 = 연료 칸
        s.set(x, yf + 1, 1, hopper(DOWN))
        s.set(x, yf + 2, 1, hopper(fuel))
        s.set(x, yf - 1, 0, hopper(out))        # 화로 아래 = 산출
        s.set(x, yf - 1, 1, structure)


def _col(s, x, z, y_top, y_bottom):
    """y_top 에서 y_bottom 까지 아래로 내리는 호퍼 기둥 (양 끝 포함)."""
    for y in range(y_bottom, y_top + 1):
        s.set(x, y, z, hopper(DOWN))


def _line(s, y, z, x_from, x_to, facing):
    """x_from → x_to 로 가는 가로 호퍼 줄 (양 끝 포함)."""
    step = 1 if x_to >= x_from else -1
    for x in range(x_from, x_to + step, step):
        s.set(x, y, z, hopper(facing))


def _zline(s, x, y, z_from, z_to, facing):
    step = 1 if z_to >= z_from else -1
    for z in range(z_from, z_to + step, step):
        s.set(x, y, z, hopper(facing))


def build(furnaces: int = 1, kelp_columns: int = 2, structure=STONE) -> Design:
    if furnaces < 1:
        raise ValueError("furnaces 는 1 이상이어야 한다")
    n = furnaces
    sz = sizing(n)
    dry = sz["drying_furnaces"]
    bins = sz["composters"]
    if sz["moss_beds"] > 1:
        raise ValueError(
            f"화로 {n}대면 이끼 베드가 {sz['moss_beds']}개 필요하다. "
            f"부피를 줄이려고 이 공장은 베드 한 개짜리 한 벌로 고정했다 — "
            f"같은 공장을 {sz['moss_beds']}벌 지어라.")
    c = kelp_columns

    s = Schematic(
        name=f"full_factory_f{n}",
        description=f"통합 매끄러운 돌 공장(압축판) · TNT 조약돌 + 2단 제련 + "
                    f"켈프 연료 + 이끼 뼛가루 · 시간당 "
                    f"{sz['smooth_stone_per_hour']:,.0f}개",
    )

    # 모듈을 먼저 붙인다. 물기둥 밀폐 루프가 '빈 칸만' 채우므로,
    # 모듈이 이미 놓은 벽·호퍼를 덮어쓰지 않게 하려면 순서가 중요하다.
    kelp = kelpfarm_bonemeal.build(columns=c, structure=structure)
    s.paste(kelp.schematic, dy=KY, label="켈프")

    comp = composterbank.build(bins=bins, structure=structure)
    s.paste(comp.schematic, dx=CX, dy=CY, label="퇴비통")

    bed = mossbed_auto.build(structure=structure)
    s.paste(bed.schematic, dy=MY, label="이끼베드")

    # ── 제련 3단 (z=0 본선, z=1 연료선) ────────────────────────────────
    _bank(s, n, Y2, structure, feed=EAST, fuel=EAST, out=EAST)
    _bank(s, n, Y1, structure, feed=EAST, fuel=WEST, out=WEST)
    _bank(s, dry, YD, structure, feed=WEST, fuel=EAST, out=WEST)

    # 2단: 산출·투입·연료 줄의 끝 상자
    s.set(n, Y2 - 1, 0, chest(EAST))            # ★ 매끄러운 돌 산출
    s.set(n, Y2 + 2, 0, chest(EAST))            # 투입 넘침
    s.set(n, Y2 + 2, 1, chest(EAST))            # 연료 넘침

    # 1단 산출(돌) → 2단 투입선
    s.set(-1, Y1 - 1, 0, hopper(DOWN))
    s.set(-1, Y1 - 2, 0, hopper(DOWN))
    s.set(-1, Y2 + 2, 0, hopper(EAST))          # 2단 투입선 시작

    # 1단 투입(조약돌) — 서쪽 위 상자가 입구다. TNT 생성기를 여기에 문다.
    s.set(-1, Y1 + 3, 0, chest(NORTH))          # ★ 조약돌 투입구
    s.set(-1, Y1 + 2, 0, hopper(EAST))
    s.set(n, Y1 + 2, 0, chest(EAST))            # 투입 넘침

    # 건조 산출(말린 켈프) → 제작기
    s.set(-1, YD - 1, 0, hopper(WEST))
    _col(s, -2, 0, YD - 1, YD - 4)              # y=9..6
    s.set(-2, YD - 4, 0, hopper(WEST))          # y=6 에서 제작기로
    s.set(-3, YD - 4, 0, B("crafter", crafting="false", orientation="west_up",
                           triggered="false"))
    s.set(-4, YD - 4, 0, dropper(WEST))         # 제작기 산출 → 물기둥으로 발사

    # 제작기·드로퍼 급전. 가루를 옆(z=-1) 받침 위에 올려 약하게 급전한다.
    # 이송 호퍼(-2,6,0)와는 대각선이라 잠기지 않는다.
    s.set(-3, YD - 4, -1, structure)
    s.set(-4, YD - 4, -1, structure)
    s.set(-3, YD - 3, -1, redstone_wire(east="side", west="side"))
    s.set(-4, YD - 3, -1, redstone_wire(east="side"))
    s.set(-2, YD - 3, -1, observer(EAST))       # 자가 발진 클럭
    s.set(-1, YD - 3, -1, observer(WEST))

    # 리프트 ② 말린 켈프 블록 → 건조 화로 연료선
    lift_column(s, -5, 0, YD - 5, YT, out_facing=EAST, structure=structure)
    _line(s, YT, 0, -4, -3, EAST)
    s.set(-2, YT, 0, hopper(SOUTH))
    s.set(-2, YT, 1, hopper(EAST))
    s.set(-1, YT, 1, hopper(DOWN))
    s.set(-1, YD + 2, 1, hopper(EAST))          # 건조 연료선 시작

    # 건조 연료선 동쪽 끝 → 아래 두 단의 연료선으로 (넘치면 내려간다)
    _col(s, dry, 1, YD + 2, Y1 + 3)             # y=12..8
    for x in range(dry, n - 1, -1):
        if x >= n:
            s.set(x, Y1 + 2, 1, hopper(WEST))   # 1단 연료선 시작
    _col(s, -1, 1, Y1 + 2, Y2 + 3)              # y=7..3
    s.set(-1, Y2 + 2, 1, hopper(EAST))          # 2단 연료선 시작

    # ── 켈프 팜 ────────────────────────────────────────────────────────
    # 켈프 수거 상자를 이송선으로 바꿔 건조 화로 투입선까지 내린다.
    kx = c + 2
    _line(s, KY + 4, 1, c, kx - 1, EAST)
    _col(s, kx, 1, KY + 4, YT + 1)              # y=19..14
    s.set(kx, YT, 1, hopper(NORTH))
    _line(s, YT, 0, kx, dry + 1, WEST)
    s.set(dry, YT, 0, hopper(DOWN))
    s.set(dry, YD + 2, 0, hopper(WEST))         # 건조 투입선 시작
    s.set(-1, YD + 2, 0, chest(WEST))           # 투입 넘침

    # ── 퇴비통 ─────────────────────────────────────────────────────────
    # 뼛가루 산출 상자 → 분배선(Y=21). 갈래는 아래에서 끌어간다.
    s.set(CX + bins, CY - 2, 0, hopper(DOWN))   # 산출 상자 바로 아래
    s.set(CX + bins, YB, 0, hopper(EAST))
    _line(s, YB, 0, CX + bins + 1, 6, EAST)
    s.set(7, YB, 0, dropper(EAST))              # 리프트 ①로 발사

    # 갈래: 분배선 아래에서 끌어 켈프 뼛가루 상자로
    s.set(-2, YB - 1, 0, hopper(EAST))          # (-1,20,0) = 켈프 투입 상자

    # 리프트 ① 뼛가루 → 이끼 베드 발사기 급이선
    s.set(7, YB, 1, structure)                  # 드로퍼 급전용 받침
    s.set(7, YB + 1, 1, redstone_wire(west="side"))
    # 가루에 붙는 쪽 관측기는 가루 반대편(서)을 봐야 출력면이 가루를 때린다.
    s.set(6, YB + 1, 1, observer(WEST))         # 자가 발진 클럭
    s.set(5, YB + 1, 1, observer(EAST))
    lift_column(s, 8, 0, YB - 1, MY + 3, out_facing=SOUTH, structure=structure)

    # ── 이끼 베드 ──────────────────────────────────────────────────────
    # 리프트 상단 → 베드 급이 통로(씨앗 뒤 벽줄)의 동쪽 끝
    feed_y = MY + mossbed_auto.LAYER_PITCH          # 씨앗 높이 = 급이 통로 높이
    feed_z = mossbed_auto.BED_ROWS[1] - 1
    _zline(s, 8, feed_y, 1, feed_z - 1, SOUTH)
    s.set(8, feed_y, feed_z, hopper(WEST))
    _line(s, feed_y, feed_z, 7, 7 // 2 + 1, WEST)   # 발사기(x=3)까지

    # 베드 산출 상자 → 퇴비통 투입 상자 (모두 Y=27, 베드 바닥 아래)
    zz = mossbed_auto.DEPTH
    s.set(7, MY - 2, zz, hopper(WEST))
    _line(s, MY - 2, zz, 6, CX + 1, WEST)
    _zline(s, CX + 1, MY - 2, zz, 1, NORTH)
    s.set(CX + 1, MY - 2, 0, hopper(WEST))      # 퇴비통 투입 상자로

    s.note("입구: 조약돌 투입 상자 (-1, 8, 0). 출구: 매끄러운 돌 상자 (%d, -1, 0)."
           % n)
    s.note("TNT 조약돌 생성기는 폭발 때문에 이 스케매틱에 넣지 않았다. 따로 지어"
           "(litematic cobblegen_tnt) 최소 15칸 떨어뜨리고, 호퍼 줄로 조약돌 투입 "
           "상자에 물릴 것. TNT가 막힌 서버면 cobblegen 을 대신 물리면 된다.")
    s.note("되먹임 두 곳만 물기둥 엘리베이터로 올린다. 나머지는 전부 중력이다.")
    s.note("이끼 베드는 제자리 돌 재생성을 내장해 돌을 밖에서 받지 않는다.")
    s.note("뼛가루 분배선은 갈래가 두 개다. 한쪽(베드)이 가득 차면 자동으로 "
           "나머지가 켈프로 간다. 상자를 나눠 우선순위를 다투지 않는다.")

    return Design(
        schematic=s,
        principle="TNT 조약돌 → 2단 제련 → 매끄러운 돌. 연료는 뼛가루 켈프 → 건조 → "
                  "제작기로, 뼛가루는 다층 이끼 베드 → 퇴비통으로 자급한다.",
        circuit=[
            "[돌] TNT 생성기(별도) → 조약돌 투입 상자(-1,8,0) → 1단 화로 → 돌 "
            "→ 서쪽 기둥으로 낙하 → 2단 화로 → 매끄러운 돌 → 산출 상자",
            "[연료] 켈프 → 건조 화로 → 말린 켈프 → 제작기 → 드로퍼 → 리프트②",
            "[연료] 리프트② → 건조 연료선 → 넘치면 1단 → 다시 넘치면 2단 연료선",
            "[뼛가루] 이끼 베드 → 퇴비통 → 분배선(Y=21) → 켈프 발사기",
            "[뼛가루] 분배선 동쪽 끝 → 리프트① → 베드 급이 통로 → 씨앗 발사기",
        ],
        steps=[
            "1) 아래(2단 화로)부터 위로 쌓는다. 물·용암은 마지막에 붓는다.",
            "2) TNT 조약돌 생성기는 별도 스케매틱이다. 최소 15칸 이상 떨어뜨려 짓고 "
            "호퍼 줄로 조약돌 투입 상자(-1,8,0)에 물린다.",
            "3) 물기둥 엘리베이터는 영혼 모래를 먼저 놓고 위를 물 수원으로 채운다. "
            "옆이 한 칸이라도 새면 기포가 서지 않는다.",
            "4) 이끼 베드의 물을 먼저, 용암을 나중에 붓는다. 반대로 하면 흑요석이 된다.",
            "5) 켈프를 심고, 씨앗 이끼를 놓고, 연료 상자에 말린 켈프 블록 몇 개를 "
            "넣어 고리를 돌린다.",
        ],
        rate=f"매끄러운 돌 시간당 {sz['smooth_stone_per_hour']:,.0f}개 · "
             f"켈프 {sz['kelp_per_hour']:,.0f}개/시간 · "
             f"이끼 회전 {sz['moss_cycles_per_hour']:,.0f}회/시간",
        warnings=[
            "TNT 폭발은 주변을 부순다. 조약돌 생성기를 본체에 붙이지 말 것.",
            "TNT 복제는 서버에 따라 막혀 있을 수 있다.",
            "물기둥 엘리베이터의 아이템 운반은 위키가 확인해 주지만, "
            "상단 수거(호퍼)는 표준 방식을 따른 것이지 문서로 확인한 건 아니다.",
            "이끼 베드 산출량은 추정이다. 평평한 7x7 변환율(27/49)을 다층에 적용했다.",
            "화로 뱅크는 균등 분배 회로를 뺐다. 앞 화로가 64개를 물고 나서야 "
            "뒤로 흘러가므로, 켜자마자 뒷 화로가 노는 구간이 잠깐 있다.",
            f"이끼 수확물이 시간당 {sz['moss_cycles_per_hour'] * mossbed_auto.yields()['moss_est']:,.0f}개다. "
            f"호퍼 한 줄의 상한(9,000개/시간)에 가깝다 — 넘치면 공장이 스스로 느려진다.",
            f"청크 로딩: 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다. "
            "공장 전체가 AFK 범위 안이거나 /forceload 되어야 한다.",
        ],
        manual_items=["용암/물 양동이", "켈프·이끼 초기 식재", "말린 켈프 블록 (고리 점화)"],
    )
