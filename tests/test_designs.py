"""모든 설계에 공통으로 걸리는 불변조건.

설계마다 따로 검사하면 같은 실수를 반복한다 (상자 위를 막아 못 여는 버그가
두 번 났다). 여기 한 번 넣으면 앞으로 추가되는 설계에도 자동으로 적용된다.
"""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from engine.blocks import OFFSET  # noqa: E402
from engine.designs import REGISTRY, build  # noqa: E402
from engine.schematic import verify_litematic  # noqa: E402

# 상자 위에 오면 뚜껑을 못 여는 블록
OPAQUE = {"stone", "dirt", "mud", "sand", "cobblestone", "smooth_stone",
          "moss_block", "redstone_block", "furnace", "dispenser", "observer",
          "piston", "sticky_piston"}
CONTAINERS = {"chest", "hopper", "furnace", "composter", "dispenser", "dropper",
              "barrel", "crafter"}
# 호퍼가 물건을 밀어넣을 수 있는 대상
HOPPER_TARGETS = CONTAINERS | {"air"}


class TestAllDesigns(unittest.TestCase):
    """REGISTRY 의 모든 설계에 대해 같은 검사를 돌린다."""

    def designs(self):
        for name in sorted(REGISTRY):
            yield name, build(name)

    def test_every_design_is_documented(self):
        for name, d in self.designs():
            with self.subTest(design=name):
                self.assertTrue(d.schematic.blocks, "빈 설계")
                self.assertTrue(d.principle, "작동 원리가 없다")
                self.assertTrue(d.steps, "시공 순서가 없다")
                self.assertTrue(d.rate, "산출량 설명이 없다")

    GRAVITY = {"sand", "red_sand", "gravel", "suspicious_sand", "suspicious_gravel",
               "anvil", "concrete_powder", "dragon_egg"}

    def test_gravity_blocks_have_support(self):
        """모래/자갈은 아래가 비면 떨어진다.

        켈프 팜의 모래 80개가 전부 받침 없이 떠 있었다. 지으면 통째로 무너진다.
        """
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short in self.GRAVITY:
                    below = s.get(x, y - 1, z).short
                    with self.subTest(design=name, pos=(x, y, z)):
                        self.assertNotEqual(below, "air",
                                            f"{b.short} 아래가 비어 있다 → 떨어진다")

    def test_every_chest_can_be_opened(self):
        """상자 바로 위가 불투명 블록이면 열리지 않는다."""
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short == "chest":
                    above = s.get(x, y + 1, z).short
                    with self.subTest(design=name, chest=(x, y, z)):
                        self.assertNotIn(above, OPAQUE,
                                         f"상자 위가 {above} 라 열 수 없다")

    def test_hoppers_never_point_into_a_dead_solid_block(self):
        """호퍼가 컨테이너도 공기도 아닌 블록을 향하면 거기서 흐름이 막힌다."""
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "hopper":
                    continue
                dx, dy, dz = OFFSET[b.properties["facing"]]
                target = s.get(x + dx, y + dy, z + dz).short
                with self.subTest(design=name, hopper=(x, y, z)):
                    self.assertIn(target, HOPPER_TARGETS,
                                  f"호퍼가 {target} 을(를) 향해 막혀 있다")

    def test_furnaces_are_fed_and_drained(self):
        """화로는 위=원료, 아래=산출 호퍼가 있어야 자동으로 돈다."""
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "furnace":
                    continue
                with self.subTest(design=name, furnace=(x, y, z)):
                    above = s.get(x, y + 1, z)
                    self.assertEqual(above.short, "hopper", "화로 위에 투입 호퍼가 없다")
                    self.assertEqual(above.properties["facing"], "down",
                                     "화로 위 호퍼가 아래를 향하지 않는다")
                    self.assertEqual(s.get(x, y - 1, z).short, "hopper",
                                     "화로 아래에 산출 호퍼가 없다")

    def test_composters_are_fed_and_drained(self):
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "composter":
                    continue
                with self.subTest(design=name, composter=(x, y, z)):
                    above = s.get(x, y + 1, z)
                    self.assertEqual(above.short, "hopper", "퇴비통 위에 투입 호퍼가 없다")
                    self.assertEqual(above.properties["facing"], "down")
                    self.assertEqual(s.get(x, y - 1, z).short, "hopper",
                                     "퇴비통 아래에 산출 호퍼가 없다")

    def test_water_never_touches_a_lava_source(self):
        """물이 용암 수원에 닿으면 흑요석이 되어 설계가 망가진다."""
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "lava":
                    continue
                for dx, dy, dz in OFFSET.values():
                    if dy < 0:
                        continue          # 아래쪽 접촉은 흑요석을 만들지 않는다
                    n = s.get(x + dx, y + dy, z + dz)
                    with self.subTest(design=name, lava=(x, y, z)):
                        self.assertNotEqual(
                            n.short, "water",
                            "용암 수원 옆/위에 물 수원이 있다 → 흑요석이 된다")

    def test_lava_is_contained(self):
        """용암 수원이 설계 밖으로 흘러나가면 안 된다."""
        for name, d in self.designs():
            s = d.schematic
            lo, hi = s.bounds
            for (x, y, z), b in s.blocks.items():
                if b.short != "lava":
                    continue
                for dname, (dx, dy, dz) in OFFSET.items():
                    if dname == "up":
                        continue
                    nx, ny, nz = x + dx, y + dy, z + dz
                    inside = (lo[0] <= nx <= hi[0] and lo[1] <= ny <= hi[1]
                              and lo[2] <= nz <= hi[2])
                    n = s.get(nx, ny, nz).short
                    with self.subTest(design=name, lava=(x, y, z), dir=dname):
                        if n == "air":
                            self.assertTrue(
                                inside,
                                f"용암이 설계 경계 밖({dname})으로 흐른다")

    def test_hoppers_are_not_locked_by_adjacent_redstone(self):
        """호퍼는 레드스톤 신호를 받으면 잠긴다.

        가루 줄 옆에 이송 호퍼를 두면 클럭이 돌 때마다 공급이 끊긴다.
        (호퍼 잠금을 일부러 쓰는 아이템 분류기는 이 설계군에 없다.)
        """
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "hopper":
                    continue
                for dx, dy, dz in OFFSET.values():
                    n = s.get(x + dx, y + dy, z + dz)
                    if n.short in ("redstone_wire", "redstone_block", "repeater"):
                        # 가루는 위쪽으로는 급전하지 않는다
                        if n.short == "redstone_wire" and dy < 0:
                            continue
                        self.fail(f"{name}: 호퍼({x},{y},{z}) 옆에 {n.short} 가 있어 "
                                  f"신호를 받으면 잠긴다")

    def test_droppers_never_face_air(self):
        """드로퍼가 공기를 향하면 아이템을 월드로 뱉어 잃는다.

        호퍼는 막히면 그냥 멈추지만, 드로퍼는 밖으로 던진다. 사슬 끝은
        반드시 컨테이너여야 한다.
        """
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "dropper":
                    continue
                dx, dy, dz = OFFSET[b.properties["facing"]]
                target = s.get(x + dx, y + dy, z + dz).short
                with self.subTest(design=name, dropper=(x, y, z)):
                    # 물을 향하는 건 정상이다 — 물기둥 엘리베이터에 아이템을 쏘아 넣는다
                    self.assertIn(target, CONTAINERS | {"water"},
                                  f"드로퍼가 {target} 을(를) 향한다 → 아이템을 밖으로 뱉는다")

    def test_dispensers_have_a_target(self):
        """발사기가 향한 칸은 비어 있어야 내용물이 나간다."""
        for name, d in self.designs():
            s = d.schematic
            for (x, y, z), b in s.blocks.items():
                if b.short != "dispenser":
                    continue
                dx, dy, dz = OFFSET[b.properties["facing"]]
                target = s.get(x + dx, y + dy, z + dz).short
                with self.subTest(design=name, dispenser=(x, y, z)):
                    self.assertNotIn(target, {"stone", "cobblestone"},
                                     f"발사기가 {target} 에 막혀 있다")

    def test_every_item_chain_reaches_a_container(self):
        """호퍼/드로퍼 사슬을 끝까지 따라가 아이템이 갈 곳에 도착하는지 본다.

        불변조건 검사는 '이 호퍼가 막혔나' 같은 국소 검사라, 사슬이 중간에
        허공으로 끊기는 건 못 잡는다. 이 검사가 켈프 수거 6줄이 통째로
        끊겨 있던 걸 잡았다.
        """
        import trace_flow
        for name, d in self.designs():
            s = d.schematic
            movers = {p for p, b in s.blocks.items() if b.short in trace_flow.MOVERS}
            targeted = set()
            for p in movers:
                b = s.get(*p)
                dx, dy, dz = OFFSET[b.properties["facing"]]
                targeted.add((p[0] + dx, p[1] + dy, p[2] + dz))
            for start in sorted(movers - targeted):
                r = trace_flow.trace(s, start)
                with self.subTest(design=name, start=start):
                    self.assertTrue(
                        r["ok"],
                        f"사슬이 {r['end']}[{r['end_block']}] 에서 끝난다 "
                        f"— {r.get('reason', '컨테이너가 아니다')}")

    def test_litematic_round_trip_and_format(self):
        import inspect_litematic as IL
        for name, d in self.designs():
            with self.subTest(design=name), tempfile.TemporaryDirectory() as tmp:
                path = f"{tmp}/{name}.litematic"
                d.schematic.to_litematic(path)
                ok, msgs = verify_litematic(path, d.schematic)
                self.assertTrue(ok, msgs)

                nbt = IL.parse(path)
                self.assertEqual(nbt["Version"], 6)
                self.assertEqual(nbt["MinecraftDataVersion"], 4903)
                region = next(iter(nbt["Regions"].values()))
                palette = region["BlockStatePalette"]
                self.assertEqual(IL.name_of(palette[0]), "minecraft:air")
                w = abs(region["Size"]["x"])
                h = abs(region["Size"]["y"])
                l = abs(region["Size"]["z"])
                bits = max(2, (len(palette) - 1).bit_length())
                idx = IL.unpack_states(region["BlockStates"], bits, w * h * l)
                self.assertEqual(sum(1 for v in idx if v),
                                 nbt["Metadata"]["TotalBlocks"])


class TestMossEconomics(unittest.TestCase):
    def setUp(self):
        from engine.designs.mossbed import yields
        self.y = yields()

    def test_vegetation_alone_is_net_negative(self):
        """이 사실이 설계를 좌우한다: 초목만 퇴비화하면 손해다."""
        self.assertLess(self.y["veg_only_bonemeal"], 1.0)

    def test_with_moss_it_is_net_positive(self):
        self.assertGreater(self.y["with_moss_bonemeal"], 1.0)
        self.assertAlmostEqual(self.y["with_moss_bonemeal"], 3.36, places=1)

    def test_stone_consumption_matches_moss_produced(self):
        self.assertAlmostEqual(self.y["stone_consumed"],
                               self.y["counts"]["moss_block"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
