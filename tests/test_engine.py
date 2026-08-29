"""엔진 회귀 테스트. python3 -m unittest discover -s tests 로 실행."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import blueprint, catalog, mechanics as M  # noqa: E402
from engine.archetypes import ARCHETYPES, build  # noqa: E402
from engine.grid import PALETTE, Grid  # noqa: E402
from engine.principle import Principle, resolve  # noqa: E402


class TestMechanics(unittest.TestCase):
    def test_fall_damage_formula(self):
        self.assertEqual(M.fall_damage(3), 0)
        self.assertEqual(M.fall_damage(24), 21)
        self.assertEqual(M.fall_damage(1), 0)

    def test_drop_height_kills_20hp_mob(self):
        d = M.drop_height_for(20)
        self.assertGreaterEqual(M.fall_damage(d), 20)

    def test_drop_height_leaves_one_hp(self):
        d = M.drop_height_for(20, leave_alive=True)
        self.assertEqual(M.fall_damage(d), 19)

    def test_hopper_throughput(self):
        self.assertAlmostEqual(M.hopper_throughput(1), 2.5)
        self.assertAlmostEqual(M.hopper_throughput(4), 10.0)

    def test_furnace_math(self):
        self.assertAlmostEqual(M.FURNACE_ITEMS_PER_HOUR, 360.0)
        self.assertEqual(M.furnaces_needed(1000), 3)

    def test_mob_cap_scales_with_loaded_chunks(self):
        full = M.effective_mob_cap("monster", M.SPAWN_CHUNK_AREA)
        half = M.effective_mob_cap("monster", M.SPAWN_CHUNK_AREA // 2)
        self.assertEqual(full, 70)
        self.assertLess(half, full)


class TestGrid(unittest.TestCase):
    def test_rejects_unknown_block_code(self):
        g = Grid()
        with self.assertRaises(KeyError):
            g.set(0, 0, 0, "Q")

    def test_air_clears_cell(self):
        g = Grid()
        g.set(1, 1, 1, "#")
        g.set(1, 1, 1, ".")
        self.assertEqual(g.cells, {})

    def test_render_and_materials(self):
        g = Grid()
        g.fill(0, 0, 0, 2, 0, 2, "#")
        self.assertEqual(g.size, (3, 1, 3))
        self.assertIn("###", g.render_layers())
        self.assertEqual(dict(g.material_list())["건축 블록(아무 불투명 블록)"], 9)

    def test_every_palette_entry_is_documented(self):
        for code, (name, _tag) in PALETTE.items():
            self.assertTrue(name, f"{code} 에 이름이 없음")


class TestArchetypes(unittest.TestCase):
    def test_all_archetypes_build_non_empty(self):
        for name in ARCHETYPES:
            with self.subTest(archetype=name):
                r = build(name, {})
                self.assertTrue(r.grid.cells, f"{name}: 빈 설계도")
                self.assertTrue(r.steps, f"{name}: 시공 순서 없음")
                self.assertTrue(r.principle, f"{name}: 작동 원리 없음")

    def test_unknown_archetype_raises(self):
        with self.assertRaises(KeyError):
            build("nope", {})

    def test_mob_tower_drop_actually_kills(self):
        r = build("mob_platform_tower", {"mob": "zombie"})
        self.assertFalse([w for w in r.warnings if "즉사 안 됨" in w])

    def test_mob_tower_warns_on_insufficient_drop(self):
        r = build("mob_platform_tower", {"mob": "zombie", "drop": 5})
        self.assertTrue([w for w in r.warnings if "즉사 안 됨" in w])


class TestPrinciple(unittest.TestCase):
    def test_rejects_unknown_source(self):
        with self.assertRaises(ValueError):
            Principle.from_dict({"source": "magic", "process": "fall"})

    def test_rejects_unknown_key(self):
        with self.assertRaises(ValueError):
            Principle.from_dict({"source": "spawner", "process": "fall", "bogus": 1})

    def test_nether_water_transport_is_flagged(self):
        r = resolve(Principle.from_dict(
            {"source": "natural_spawn", "process": "fall", "transport": "water",
             "dimension": "nether", "target": "zombified_piglin"}))
        self.assertTrue([w for w in r.warnings if "증발" in w])

    def test_fall_immune_mob_is_flagged(self):
        r = resolve(Principle.from_dict(
            {"source": "spawner", "process": "fall", "target": "blaze",
             "dimension": "nether"}))
        self.assertTrue([w for w in r.warnings if "낙하 데미지가 통하지 않는다" in w])

    def test_drop_height_is_derived_from_target_hp(self):
        r = resolve(Principle.from_dict(
            {"source": "natural_spawn", "process": "fall", "target": "enderman"}))
        self.assertEqual(r.params["drop"], M.drop_height_for(M.MOB_HP["enderman"]))

    def test_spawn_chunk_warning_always_present(self):
        r = resolve(Principle.from_dict({"source": "spawner", "process": "fall"}))
        self.assertTrue([w for w in r.warnings if "스폰 청크" in w])


class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.farms = catalog.farms()

    def test_exactly_100_farms(self):
        self.assertEqual(len(self.farms), 100)

    def test_ids_unique(self):
        ids = [f["id"] for f in self.farms]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_farm_has_principle_and_archetype(self):
        for f in self.farms:
            with self.subTest(farm=f["id"]):
                self.assertIn(f["arch"], ARCHETYPES)
                self.assertGreaterEqual(len(f["principle"]), 10)
                self.assertIn(f["verify"], ("mechanics", "at_risk"))

    def test_every_farm_renders_a_document(self):
        for f in self.farms:
            with self.subTest(farm=f["id"]):
                doc = blueprint.from_catalog(f["id"])
                self.assertIn("작동 원리", doc)
                self.assertIn("시공 순서", doc)
                self.assertIn("점검표", doc)

    def test_at_risk_farms_declare_a_reason(self):
        for f in self.farms:
            if f["verify"] == "at_risk":
                self.assertTrue(f.get("risk"), f"{f['id']}: at_risk 인데 사유가 없음")

    def test_catalog_json_matches_source(self):
        doc = json.loads((ROOT / "data" / "farms.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["count"], len(doc["farms"]))
        self.assertEqual(doc["game_version"], M.GAME_VERSION)

    def test_search_filters(self):
        self.assertTrue(all(f["dim"] == "nether" for f in catalog.search(dim="nether")))
        self.assertTrue(all(f["diff"] <= 2 for f in catalog.search(max_diff=2)))
        self.assertTrue(catalog.search(q="철"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
