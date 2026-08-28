import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fac.farms.loader import load_farms
from fac.farms.registry import Registry, validate_all, validate_farm
from fac.farms.blueprint import make_blueprint
from fac.farms.schema import CATEGORIES, DIMENSIONS, STATUS


class FarmCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.farms = load_farms()
        cls.reg = Registry()

    def test_curated_one_hundred(self):
        self.assertEqual(len(self.farms), 100, "the knowledge base should hold 100 farms")

    def test_ids_unique(self):
        ids = [f.id for f in self.farms]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_component_exists_in_2620_registry(self):
        # The core guarantee: no farm references a block/item/entity/biome
        # that does not exist in the real Minecraft 26.2 registry.
        problems = validate_all(self.farms, self.reg)
        self.assertEqual(problems, {}, f"registry validation failures: {problems}")

    def test_schema_fields_valid(self):
        for f in self.farms:
            self.assertIn(f.category, CATEGORIES, f.id)
            self.assertIn(f.dimension, DIMENSIONS, f.id)
            self.assertIn(f.status, STATUS, f.id)
            self.assertTrue(f.principle, f.id)
            self.assertTrue(f.mechanics, f.id)
            self.assertTrue(f.sources, f"{f.id} has no source")
            self.assertEqual(validate_farm(f, self.reg), [], f.id)

    def test_categories_cover_survival_scope(self):
        cats = {f.category for f in self.farms}
        for expected in ("mob", "resource", "crop", "wood", "animal", "utility"):
            self.assertIn(expected, cats)

    def test_blueprint_generates_for_every_farm(self):
        for f in self.farms:
            bp = make_blueprint(f)
            self.assertTrue(bp.steps, f"{f.id}: no build steps")
            self.assertTrue(bp.materials, f"{f.id}: no materials")
            self.assertTrue(bp.placements, f"{f.id}: no placements")
            # Every produced item is a real 26.2 item/block.
            for item in f.items_out:
                self.assertTrue(self.reg.has_item(item), f"{f.id}: bad output {item}")


if __name__ == "__main__":
    unittest.main()
