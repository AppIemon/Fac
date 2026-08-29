"""사탕수수 팜 설계의 물리/회로 정합성 검증.

'파일이 열린다' 가 아니라 '지으면 실제로 돈다' 를 검사한다.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.blocks import NORTH, OFFSET, OPPOSITE, SOUTH  # noqa: E402
from engine.designs import build  # noqa: E402
from engine.schematic import Schematic, verify_litematic  # noqa: E402

SOLID = {"stone", "dirt", "redstone_block", "hopper", "chest"}
OPAQUE_SUPPORT = {"stone", "dirt"}   # 레드스톤 가루를 받칠 수 있는 불투명 블록


class TestSugarcaneDesign(unittest.TestCase):
    LENGTH = 12

    def setUp(self):
        self.d = build("sugarcane", length=self.LENGTH)
        self.s: Schematic = self.d.schematic

    # --- 성장 조건 ------------------------------------------------------
    def test_soil_has_adjacent_water(self):
        """사탕수수는 심는 블록에 물이 '수평으로' 붙어 있어야 자란다."""
        for x in range(self.LENGTH):
            soil = self.s.get(x, 0, 2)
            self.assertEqual(soil.short, "dirt", f"x={x} 흙 없음")
            neighbours = [self.s.get(x + dx, 0, 2 + dz).short
                          for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            self.assertIn("water", neighbours, f"x={x} 흙 옆에 물이 없다 → 자라지 않음")

    def test_cane_planted_only_at_base(self):
        """스케매틱에는 밑동 1칸만. 나머지는 게임 안에서 자란다."""
        for x in range(self.LENGTH):
            self.assertEqual(self.s.get(x, 1, 2).short, "sugar_cane")
            for y in (2, 3):
                self.assertEqual(self.s.get(x, y, 2).short, "air",
                                 f"x={x}, y={y} 성장 공간이 막혀 있다")

    def test_growth_column_is_clear_above(self):
        """3칸까지 자라야 관측기가 감지한다 → 위가 비어 있어야 한다."""
        for x in range(self.LENGTH):
            self.assertEqual(self.s.get(x, 4, 2).short, "air")

    # --- 회로 ------------------------------------------------------------
    def test_observer_watches_third_cane_block(self):
        for x in range(self.LENGTH):
            obs = self.s.get(x, 3, 3)
            self.assertEqual(obs.short, "observer", f"x={x} 관측기 없음")
            facing = obs.properties["facing"]
            dx, dy, dz = OFFSET[facing]
            tx, ty, tz = x + dx, 3 + dy, 3 + dz
            self.assertEqual((tx, ty, tz), (x, 3, 2),
                             f"x={x} 관측기가 사탕수수 3번째 칸을 보고 있지 않다 (facing={facing})")

    def test_observer_output_face_has_redstone(self):
        """관측기는 '바라보는 방향의 반대편' 으로 신호를 낸다."""
        for x in range(self.LENGTH):
            obs = self.s.get(x, 3, 3)
            out = OPPOSITE[obs.properties["facing"]]
            dx, dy, dz = OFFSET[out]
            wire = self.s.get(x + dx, 3 + dy, 3 + dz)
            self.assertEqual(wire.short, "redstone_wire",
                             f"x={x} 관측기 출력면({out})에 레드스톤 가루가 없다")

    def test_wire_support_is_opaque_and_touches_piston(self):
        """가루 -> 받침 블록 약한 급전 -> 인접 피스톤 작동."""
        for x in range(self.LENGTH):
            support = self.s.get(x, 2, 4)
            self.assertIn(support.short, OPAQUE_SUPPORT,
                          f"x={x} 가루 받침이 불투명 블록이 아니다 → 급전 불가")
            neighbours = [(x + dx, 2 + dy, 4 + dz) for dx, dy, dz in OFFSET.values()]
            pistons = [p for p in neighbours if self.s.get(*p).short == "piston"]
            self.assertTrue(pistons, f"x={x} 급전된 받침 블록 옆에 피스톤이 없다")

    def test_piston_breaks_second_cane_block(self):
        for x in range(self.LENGTH):
            pis = self.s.get(x, 2, 3)
            self.assertEqual(pis.short, "piston", f"x={x} 피스톤 없음")
            self.assertEqual(pis.properties["extended"], "false")
            dx, dy, dz = OFFSET[pis.properties["facing"]]
            self.assertEqual((x + dx, 2 + dy, 3 + dz), (x, 2, 2),
                             f"x={x} 피스톤이 사탕수수 2번째 칸을 향하지 않는다")

    def test_wire_line_is_continuous(self):
        """포기마다 관측기가 있으므로 길이가 늘어도 중계기가 필요 없다."""
        for x in range(self.LENGTH):
            self.assertEqual(self.s.get(x, 3, 4).short, "redstone_wire")

    # --- 수거 ------------------------------------------------------------
    def test_rail_runs_directly_under_soil(self):
        """호퍼 광산 수레는 '레일 바로 위 블록에 놓인' 아이템을 관통 수거한다."""
        for x in range(self.LENGTH):
            self.assertIn(self.s.get(x, -1, 2).short, ("rail", "powered_rail"),
                          f"x={x} 레일 없음")
            self.assertEqual(self.s.get(x, 0, 2).short, "dirt",
                             f"x={x} 레일 바로 위가 흙이 아니다 → 수거 안 됨")

    def test_powered_rails_have_power_source(self):
        for x in range(self.LENGTH):
            if self.s.get(x, -1, 2).short == "powered_rail":
                self.assertEqual(self.s.get(x, -2, 2).short, "redstone_block",
                                 f"x={x} 가속 레일 아래에 전원이 없다")

    def test_rail_has_bumpers_at_both_ends(self):
        """양 끝 벽이 있어야 광산 수레가 튕겨 왕복한다."""
        for x in (-1, self.LENGTH):
            self.assertIn(self.s.get(x, -1, 2).short, SOLID,
                          f"x={x} 레일 끝 벽이 없다 → 수레가 멈춘다")

    def test_hopper_feeds_a_chest(self):
        hoppers = [(p, b) for p, b in self.s.blocks.items() if b.short == "hopper"]
        self.assertEqual(len(hoppers), 1)
        (hx, hy, hz), hop = hoppers[0]
        self.assertEqual(self.s.get(hx, hy + 1, hz).short, "rail",
                         "호퍼가 레일 바로 아래에 있어야 수레를 비운다")
        dx, dy, dz = OFFSET[hop.properties["facing"]]
        self.assertEqual(self.s.get(hx + dx, hy + dy, hz + dz).short, "chest",
                         "호퍼가 상자를 향하고 있지 않다")

    def test_hopper_not_on_powered_rail_position(self):
        (hx, _, _), _ = next(iter(
            (p, b) for p, b in self.s.blocks.items() if b.short == "hopper"))
        self.assertNotEqual(self.s.get(hx, -1, 2).short, "powered_rail",
                            "호퍼 자리와 가속 레일(레드스톤 블록) 자리가 충돌한다")

    # --- 아이템 유실 방지 -------------------------------------------------
    def test_water_canal_is_capped(self):
        """뚜껑이 없으면 수확물이 물에 빠져 회수되지 않는다."""
        for x in range(self.LENGTH):
            for y in (1, 2, 3):
                self.assertIn(self.s.get(x, y, 1).short, SOLID,
                              f"x={x}, y={y} 물 수로 위가 열려 있다")

    def test_row_ends_are_sealed(self):
        for x in (-1, self.LENGTH):
            for y in (0, 1, 2, 3):
                self.assertIn(self.s.get(x, y, 2).short, SOLID,
                              f"x={x}, y={y} 줄 끝이 막혀 있지 않다")
            self.assertIn(self.s.get(x, 0, 1).short, SOLID, f"x={x} 물이 새어나간다")

    # --- 파라미터 / 출력 ---------------------------------------------------
    def test_scales_with_length(self):
        for n in (4, 7, 20, 33):
            s = build("sugarcane", length=n).schematic
            canes = [p for p, b in s.blocks.items() if b.short == "sugar_cane"]
            self.assertEqual(len(canes), n)
            self.assertEqual(s.size[0], n + 2)

    def test_rejects_too_short(self):
        with self.assertRaises(ValueError):
            build("sugarcane", length=2)

    def test_litematic_round_trip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/t.litematic"
            self.s.to_litematic(path)
            ok, msgs = verify_litematic(path, self.s)
            self.assertTrue(ok, msgs)

    def test_litematic_format_is_valid(self):
        """litemapy 를 거치지 않고 NBT 를 직접 파싱해 포맷을 검사한다."""
        import tempfile
        sys.path.insert(0, str(ROOT / "tools"))
        import inspect_litematic as IL
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/t.litematic"
            self.s.to_litematic(path)
            nbt = IL.parse(path)
            self.assertEqual(nbt["Version"], 6)
            self.assertEqual(nbt["MinecraftDataVersion"], 4903)
            region = next(iter(nbt["Regions"].values()))
            palette = region["BlockStatePalette"]
            self.assertEqual(IL.name_of(palette[0]), "minecraft:air")
            w = abs(region["Size"]["x"]); h = abs(region["Size"]["y"]); l = abs(region["Size"]["z"])
            bits = max(2, (len(palette) - 1).bit_length())
            idx = IL.unpack_states(region["BlockStates"], bits, w * h * l)
            self.assertEqual(sum(1 for v in idx if v), nbt["Metadata"]["TotalBlocks"])
            self.assertEqual(len(region["BlockStates"]), (w * h * l * bits + 63) // 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
