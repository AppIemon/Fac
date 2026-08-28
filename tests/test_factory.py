import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fac.acceptance import evaluate
from fac.catalog import BIOMES, DEFAULT_GOALS, DIMENSIONS, MOBS, MODULES
from fac.datapack import export_datapack
from fac.designer import Designer, overlapping_pairs
from fac.simulator import simulate
from fac.__main__ import complete


class CatalogTests(unittest.TestCase):
    def test_every_module_points_at_known_world(self):
        for spec in MODULES.values():
            self.assertIn(spec.dimension, DIMENSIONS, spec.id)
            self.assertIn(spec.biome, BIOMES, spec.id)
            for mob in spec.mobs + spec.workers:
                self.assertIn(mob, MOBS, f"{spec.id}:{mob}")

    def test_every_goal_has_a_producer(self):
        produced = set()
        for spec in MODULES.values():
            produced.update(spec.outputs)
        self.assertTrue(set(DEFAULT_GOALS).issubset(produced))


class DesignerTests(unittest.TestCase):
    def test_default_design_covers_dimensions(self):
        design = Designer().design()
        used = {m.dimension for m in design.modules}
        self.assertEqual(used, set(DIMENSIONS))
        self.assertFalse(overlapping_pairs(design.modules))
        self.assertGreaterEqual(len(design.modules), 10)

    def test_grid_pitch_fits_footprints(self):
        from fac.catalog import GRID_PITCH

        for spec in MODULES.values():
            self.assertLess(spec.footprint[0], GRID_PITCH, spec.id)
            self.assertLess(spec.footprint[2], GRID_PITCH, spec.id)


class SimulatorTests(unittest.TestCase):
    def test_one_hour_meets_goals(self):
        result = complete()
        report = result["report"]
        failed = [c for c in report.checks if not c.ok]
        self.assertTrue(report.ok, json.dumps([c.__dict__ for c in failed], indent=2))
        net = result["design"].net()
        for item, goal in DEFAULT_GOALS.items():
            self.assertGreaterEqual(net.get(item, 0.0) + 1e-6, goal, item)


class DatapackTests(unittest.TestCase):
    def test_export_writes_dimensions_biomes_functions(self):
        result = complete()
        dest = ROOT / "datapacks"
        pack = export_datapack(result["design"], dest)
        meta = json.loads((pack / "pack.mcmeta").read_text(encoding="utf-8"))
        self.assertEqual(meta["pack"]["min_format"], [107, 1])
        for dim in DIMENSIONS:
            rel = dim.split(":")[1]
            path = pack / "data" / "fac" / "dimension" / f"{rel}.json"
            self.assertTrue(path.exists(), path)
            json.loads(path.read_text(encoding="utf-8"))
        for biome in BIOMES:
            rel = biome.split(":")[1]
            path = pack / "data" / "fac" / "worldgen" / "biome" / f"{rel}.json"
            self.assertTrue(path.exists(), path)
            body = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("spawners", body)
        self.assertTrue((pack / "data" / "fac" / "function" / "validate.mcfunction").exists())
        self.assertTrue((pack / "data" / "fac" / "function" / "setup.mcfunction").exists())
        self.assertIn(
            "fac:load",
            json.loads(
                (pack / "data" / "minecraft" / "tags" / "function" / "load.json").read_text()
            )["values"],
        )
        # One build function per placed module.
        build_dir = pack / "data" / "fac" / "function" / "build"
        uids = {p.uid for p in result["design"].modules}
        for uid in uids:
            self.assertTrue((build_dir / f"{uid}.mcfunction").exists(), uid)


if __name__ == "__main__":
    unittest.main()
