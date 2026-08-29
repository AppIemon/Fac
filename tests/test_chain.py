"""공장 연결 계층 검증."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

from engine.chain import ChainError, Process, Registry, plan, render  # noqa: E402


def P(pid, outputs, inputs=None, **kw):
    return Process(id=pid, name=pid, unit="대", outputs=outputs, inputs=inputs or {}, **kw)


class TestSolver(unittest.TestCase):
    def setUp(self):
        self.reg = Registry([
            P("farm", {"cane": 10.0}, throttleable=False),
            P("mill", {"meal": 5.0}, {"cane": 100.0}),
        ])

    def test_units_round_up_to_whole_machines(self):
        p = plan("meal", 11, self.reg)
        mill = p.nodes[0]
        self.assertAlmostEqual(mill.units_exact, 2.2)
        self.assertEqual(mill.units, 3, "기계는 정수 단위로만 지을 수 있다")

    def test_throttleable_input_scales_with_utilization(self):
        """가동률이 낮으면 원료도 그만큼만 먹어야 한다."""
        p = plan("meal", 5, self.reg)
        mill = next(n for n in p.nodes if n.process.id == "mill")
        self.assertEqual(mill.units, 1)
        self.assertAlmostEqual(mill.utilization, 1.0)
        self.assertAlmostEqual(mill.consumed["cane"], 100.0)

        p2 = plan("meal", 1, self.reg)
        mill2 = next(n for n in p2.nodes if n.process.id == "mill")
        self.assertEqual(mill2.units, 1)
        self.assertAlmostEqual(mill2.utilization, 0.2)
        self.assertAlmostEqual(mill2.consumed["cane"], 20.0,
                               msg="가동률 20%인데 원료를 100% 먹고 있다")

    def test_non_throttleable_runs_at_full_capacity(self):
        """팜은 수요와 무관하게 자기 속도로 나온다 → 딱 안 떨어지면 부산물이 남는다."""
        reg = Registry([
            P("farm", {"cane": 30.0}, throttleable=False),
            P("mill", {"meal": 5.0}, {"cane": 100.0}),
        ])
        p = plan("meal", 1, reg)        # 밀 20개 필요, 팜 1채가 30개 생산
        farm = next(n for n in p.nodes if n.process.id == "farm")
        self.assertEqual(farm.units, 1)
        self.assertAlmostEqual(farm.produced["cane"], 30.0)
        self.assertAlmostEqual(farm.produced["cane"], farm.capacity)
        self.assertAlmostEqual(p.surplus["cane"], 10.0)

    def test_exact_fit_leaves_no_surplus(self):
        p = plan("meal", 1, self.reg)   # 밀 20개 필요, 팜 10개짜리 2채 = 정확히 20
        farm = next(n for n in p.nodes if n.process.id == "farm")
        self.assertEqual(farm.units, 2)
        self.assertNotIn("cane", p.surplus)

    def test_byproducts_are_netted_against_demand(self):
        reg = Registry([
            P("dual", {"a": 10.0, "b": 10.0}, throttleable=False),
            P("needs_b", {"c": 1.0}, {"b": 5.0}),
            P("b_maker", {"b": 100.0}),
        ])
        p = plan("c", 1, reg, choices={"b": "dual"})
        ids = [n.process.id for n in p.nodes]
        self.assertIn("dual", ids)
        self.assertNotIn("b_maker", ids, "이미 있는 부산물을 두고 새 공정을 세웠다")

    def test_raw_materials_reported(self):
        reg = Registry([P("m", {"out": 1.0}, {"ore": 3.0})])
        p = plan("out", 2, reg)
        self.assertAlmostEqual(p.raw["ore"], 6.0)

    def test_net_positive_loop_is_solved(self):
        """되먹임 고리는 정상이다. 한 바퀴 순이익이면 풀려야 한다.

        연료 -> 화로 -> 연료, 뼛가루 -> 이끼 -> 퇴비통 -> 뼛가루 처럼
        실제 공장은 고리를 이룬다.
        """
        reg = Registry([
            P("seed", {"bm": 100.0}),                       # 외부 공급
            P("bed", {"harvest": 1.0}, {"bm": 1.0}),
            P("comp", {"bm": 3.0}, {"harvest": 1.0}),       # 1 -> 3 순이익
        ])
        p = plan("harvest", 10, reg, choices={"bm": "comp"})
        ids = [n.process.id for n in p.nodes]
        self.assertIn("bed", ids)
        self.assertIn("comp", ids)
        self.assertTrue([w for w in p.warnings if "되먹임 고리" in w])

    def test_net_negative_loop_diverges_with_a_clear_error(self):
        """한 바퀴 순손실인 고리는 아무리 키워도 목표를 못 채운다."""
        reg = Registry([
            P("bed", {"harvest": 1.0}, {"bm": 1.0}),
            P("comp", {"bm": 0.85}, {"harvest": 1.0}),      # 1 -> 0.85 순손실
        ])
        with self.assertRaises(ChainError) as cm:
            plan("harvest", 10, reg, choices={"bm": "comp"})
        self.assertIn("순손실", str(cm.exception))

    def test_unknown_target_errors(self):
        with self.assertRaises(ChainError):
            plan("diamond", 1, self.reg)

    def test_non_positive_rate_errors(self):
        with self.assertRaises(ChainError):
            plan("meal", 0, self.reg)

    def test_ambiguous_producer_warns_and_lists_options(self):
        reg = Registry([P("x1", {"x": 1.0}), P("x2", {"x": 1.0})])
        p = plan("x", 1, reg)
        self.assertTrue([w for w in p.warnings if "--pick" in w])

    def test_pick_overrides_choice(self):
        reg = Registry([P("x1", {"x": 1.0}), P("x2", {"x": 2.0})])
        p = plan("x", 2, reg, choices={"x": "x2"})
        self.assertEqual(p.nodes[0].process.id, "x2")

    def test_bad_pick_errors(self):
        with self.assertRaises(ChainError):
            plan("meal", 1, self.reg, choices={"meal": "nope"})

    def test_hopper_bottleneck_warning(self):
        reg = Registry([P("huge", {"x": 50000.0}, throttleable=False)])
        p = plan("x", 50000, reg)
        self.assertTrue([w for w in p.warnings if "호퍼" in w])

    def test_builds_split_by_max_units(self):
        reg = Registry([P("f", {"x": 1.0}, max_units_per_build=64, throttleable=False)])
        node = plan("x", 130, reg).nodes[0]
        self.assertEqual(node.units, 130)
        self.assertEqual(node.builds, [64, 64, 2])

    def test_registry_rejects_duplicate_and_bad_rates(self):
        r = Registry([P("a", {"x": 1.0})])
        with self.assertRaises(ValueError):
            r.add(P("a", {"y": 1.0}))
        with self.assertRaises(ValueError):
            r.add(P("b", {"y": 0.0}))


class TestRealRegistry(unittest.TestCase):
    def setUp(self):
        import processes
        self.reg = processes.REGISTRY

    def test_every_process_has_a_source(self):
        for pid, p in self.reg.by_id.items():
            self.assertTrue(p.source, f"{pid}: 수치 근거가 비어 있다")

    def test_composter_matches_wiki_numbers(self):
        """성공 7회/뼛가루 1개, 사탕수수 50% → 평균 14개."""
        c = self.reg.by_id["composter_sugar_cane"]
        ratio = c.inputs["sugar_cane"] / c.outputs["bone_meal"]
        self.assertAlmostEqual(ratio, 14.0, places=6)

    def test_bamboo_is_not_compostable(self):
        self.assertNotIn("composter_bamboo", self.reg.by_id)

    def test_bone_to_bonemeal_ratio_is_three(self):
        c = self.reg.by_id["craft_bonemeal_from_bone"]
        self.assertAlmostEqual(c.outputs["bone_meal"] / c.inputs["bone"], 3.0)

    def test_boneblock_to_bonemeal_ratio_is_nine(self):
        c = self.reg.by_id["craft_bonemeal_from_boneblock"]
        self.assertAlmostEqual(c.outputs["bone_meal"] / c.inputs["bone_block"], 9.0)

    def test_furnace_rate_is_360_per_hour(self):
        f = self.reg.by_id["smelt_cactus_green"]
        self.assertAlmostEqual(f.outputs["green_dye"], 360.0)

    def test_farms_are_not_throttleable(self):
        for pid in ("sugarcane_farm", "cactus_farm", "skeleton_spawner"):
            self.assertFalse(self.reg.by_id[pid].throttleable,
                             f"{pid}: 팜은 수요와 무관하게 계속 돌아간다")

    def test_design_backed_processes_can_emit_a_schematic(self):
        from engine.designs import REGISTRY as DESIGNS
        for pid, p in self.reg.by_id.items():
            if p.design:
                self.assertIn(p.design, DESIGNS, f"{pid}: 설계 {p.design} 가 없다")

    def test_design_param_is_a_real_builder_argument(self):
        """design_param 이 실제 설계 함수의 인자여야 한다.

        이끼팜의 size 는 '베드 크기'지 '베드 개수'가 아니라서,
        유닛 수를 그대로 넘기면 1x1 베드를 지으라는 엉뚱한 안내가 나갔다.
        """
        import inspect
        from engine.designs import REGISTRY as DESIGNS
        for pid, p in self.reg.by_id.items():
            if not p.design_param:
                continue
            sig = inspect.signature(DESIGNS[p.design])
            with self.subTest(process=pid):
                self.assertIn(p.design_param, sig.parameters,
                              f"{p.design} 에 {p.design_param} 인자가 없다")

    def test_unit_scaling_designs_actually_scale(self):
        """design_param 을 쓰는 공정은 유닛 수를 넘겼을 때 규모가 커져야 한다."""
        from engine.designs import build as build_design, REGISTRY as DESIGNS
        for pid, p in self.reg.by_id.items():
            if not p.design_param:
                continue
            small = build_design(p.design, **{p.design_param: 2})
            large = build_design(p.design, **{p.design_param: 6})
            with self.subTest(process=pid):
                self.assertLess(len(small.schematic.blocks),
                                len(large.schematic.blocks),
                                f"{p.design} 이 {p.design_param} 에 따라 커지지 않는다")

    def test_plan_commands_actually_run(self):
        """계획서가 인쇄한 litematic 명령이 실제로 실행되어야 한다.

        설계마다 파라미터 이름이 달라서(length/cells/furnaces/bins) 계획서는
        되는데 명령은 안 되는 상태가 실제로 있었다.
        """
        import re
        import tempfile
        from engine.cli import main as cli_main
        plan_doc = render(plan("smooth_stone", 1000, self.reg))
        cmds = re.findall(r"python3 -m engine\.cli (litematic .+)", plan_doc)
        self.assertTrue(cmds, "계획서에 설계도 명령이 하나도 없다")
        with tempfile.TemporaryDirectory() as tmp:
            for cmd in cmds:
                with self.subTest(cmd=cmd):
                    argv = cmd.split() + ["--out", tmp]
                    self.assertEqual(cli_main(argv), 0, f"실행 실패: {cmd}")

    def test_real_plan_renders(self):
        p = plan("bone_meal", 500, self.reg, {"bone_meal": "composter_sugar_cane"})
        doc = render(p)
        for section in ("필요한 공장", "가동률", "근거"):
            self.assertIn(section, doc)
        cane = next(n for n in p.nodes if n.process.id == "sugarcane_farm")
        self.assertGreater(cane.units, 1000, "사탕수수 팜 규모가 비현실적으로 작다")
        self.assertTrue(cane.builds[0] <= 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
