"""CLI: design, test, export, optionally live-check on Paper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python3 -m fac` from repo root without installing.
ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fac.acceptance import evaluate
from fac.datapack import export_datapack
from fac.designer import Designer
from fac.report import export_report
from fac.simulator import simulate


def complete(goals: dict[str, float] | None = None) -> dict:
    designer = Designer(goals)
    design = designer.design()
    sim = simulate(design, hours=1.0, steps=60)
    report = evaluate(design, sim)
    extra = 0
    while (not report.ok) and extra < 8:
        extra += 1
        # Belt upgrades first, then duplicate the worst missing producer.
        from fac.designer import PRODUCERS

        failed = [c for c in report.checks if not c.ok]
        belt_fails = [c for c in failed if c.id.startswith("logistics:belts") or c.id.startswith("starve:")]
        if belt_fails:
            for placed in design.modules:
                placed.belts += 1
            design.notes.append(f"repair {extra}: +1 belt all modules")
        else:
            goal_fails = [c.id.split(":", 1)[1] for c in failed if c.id.startswith("goal:")]
            if goal_fails:
                item = goal_fails[0]
                producer = PRODUCERS.get(item, [None])[0]
                if producer:
                    designer._place(design, producer)
                    design.notes.append(f"repair {extra}: extra {producer} for {item}")
        designer._upgrade_belts(design)
        sim = simulate(design, hours=1.0, steps=60)
        report = evaluate(design, sim)
        design.iterations += 1
    return {"design": design, "sim": sim, "report": report}


def cmd_complete(args: argparse.Namespace) -> int:
    result = complete()
    design, sim, report = result["design"], result["sim"], result["report"]
    out = Path(args.out)
    export_report(design, sim, report, out / "web")
    pack = export_datapack(design, out / "datapacks")
    summary = {
        "ok": report.ok,
        "iterations": design.iterations,
        "modules": len(design.modules),
        "passed": report.to_dict()["passed"],
        "failed": report.to_dict()["failed"],
        "net": {k: round(v, 1) for k, v in design.net().items()},
        "datapack": str(pack),
        "notes": design.notes,
        "failed_checks": [c.__dict__ for c in report.checks if not c.ok],
    }
    (out / "web" / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if report.ok else 2


def cmd_test(args: argparse.Namespace) -> int:
    result = complete()
    report = result["report"]
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.ok else 2


def cmd_live(args: argparse.Namespace) -> int:
    from fac.servertest import run_live_test

    datapack = Path(args.datapack)
    if not datapack.exists():
        cmd_complete(argparse.Namespace(out=str(ROOT)))
        datapack = ROOT / "datapacks" / "fac"
    result = run_live_test(datapack)
    print(json.dumps({k: v for k, v in result.items() if k != "log_tail"}, indent=2, ensure_ascii=False))
    if result.get("log_tail"):
        print("--- log tail ---")
        print(result["log_tail"][-4000:])
    return 0 if result.get("ok") else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fac", description="AI Minecraft factory designer")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_complete = sub.add_parser("complete", help="design, simulate, accept, export")
    p_complete.add_argument("--out", default=str(ROOT))
    p_complete.set_defaults(func=cmd_complete)
    p_test = sub.add_parser("test", help="run acceptance tests only")
    p_test.set_defaults(func=cmd_test)
    p_live = sub.add_parser("live", help="boot Paper and validate datapack")
    p_live.add_argument("--datapack", default=str(ROOT / "datapacks" / "fac"))
    p_live.set_defaults(func=cmd_live)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
