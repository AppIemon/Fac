"""CLI for the survival farm knowledge base.

Examples:
  python3 -m fac.farms list
  python3 -m fac.farms list --category mob
  python3 -m fac.farms show iron_farm
  python3 -m fac.farms search gold
  python3 -m fac.farms validate
  python3 -m fac.farms blueprint iron_farm
  python3 -m fac.farms stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fac.farms.loader import load_farms, farms_by_id
from fac.farms.registry import Registry, validate_all, validate_farm
from fac.farms.blueprint import make_blueprint


def cmd_list(args) -> int:
    farms = load_farms()
    if args.category:
        farms = [f for f in farms if f.category == args.category]
    for f in farms:
        print(f"{f.id:32} [{f.category:8}] {f.name}  ({f.status})")
    print(f"\n{len(farms)} farms")
    return 0


def cmd_show(args) -> int:
    farm = farms_by_id().get(args.id)
    if not farm:
        print(f"unknown farm {args.id!r}")
        return 1
    print(json.dumps(farm.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_search(args) -> int:
    q = args.query.lower()
    for f in load_farms():
        hay = " ".join([f.id, f.name, f.name_ko, f.principle, " ".join(f.tags), " ".join(f.items_out)]).lower()
        if q in hay:
            print(f"{f.id:32} {f.name}  -> {', '.join(f.items_out[:4])}")
    return 0


def cmd_validate(args) -> int:
    farms = load_farms()
    reg = Registry()
    problems = validate_all(farms, reg)
    print(f"registry version: {reg.version}")
    print(f"farms: {len(farms)}  blocks:{len(reg.blocks)} items:{len(reg.items)} entities:{len(reg.entities)} biomes:{len(reg.biomes)}")
    if not problems:
        print("OK: all farms valid; every block/item/entity/biome exists in the 26.2 registry.")
        return 0
    for fid, errs in problems.items():
        print(f"\n[{fid}]")
        for e in errs:
            print(f"  - {e}")
    print(f"\n{len(problems)} farms with problems")
    return 2


def cmd_blueprint(args) -> int:
    farm = farms_by_id().get(args.id)
    if not farm:
        print(f"unknown farm {args.id!r}")
        return 1
    bp = make_blueprint(farm)
    if args.json:
        print(json.dumps(bp.to_dict(), indent=2, ensure_ascii=False))
        return 0
    print(f"# Blueprint: {bp.name}  ({farm.id})")
    print(f"Dimension: {bp.dimension}   Size: {bp.size['w']}x{bp.size['h']}x{bp.size['d']}")
    print(f"Principle: {farm.principle}")
    print(f"Version: {farm.version} ({farm.status})")
    print("\n## Requirements")
    print(json.dumps(bp.requirements, indent=2, ensure_ascii=False))
    print("\n## Build steps")
    for i, s in enumerate(bp.steps, 1):
        print(f"{i:2}. {s}")
    print("\n## Bill of materials (approx)")
    for b, n in sorted(bp.materials.items(), key=lambda kv: -kv[1]):
        print(f"  {n:6}  {b}")
    return 0


def cmd_stats(args) -> int:
    farms = load_farms()
    by_cat: dict[str, int] = {}
    by_dim: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for f in farms:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
        by_dim[f.dimension] = by_dim.get(f.dimension, 0) + 1
        by_status[f.status] = by_status.get(f.status, 0) + 1
    print(f"total farms: {len(farms)}")
    print("by category:", json.dumps(by_cat, ensure_ascii=False))
    print("by dimension:", json.dumps(by_dim, ensure_ascii=False))
    print("by status:", json.dumps(by_status, ensure_ascii=False))
    return 0


def cmd_export(args) -> int:
    """Export the whole catalog as one merged JSON (for the AI / plugin)."""
    farms = load_farms()
    out = {"version": "26.2", "count": len(farms), "farms": [f.to_dict() for f in farms]}
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(farms)} farms -> {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fac.farms", description="Survival farm knowledge base")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list"); p_list.add_argument("--category"); p_list.set_defaults(func=cmd_list)
    p_show = sub.add_parser("show"); p_show.add_argument("id"); p_show.set_defaults(func=cmd_show)
    p_search = sub.add_parser("search"); p_search.add_argument("query"); p_search.set_defaults(func=cmd_search)
    p_val = sub.add_parser("validate"); p_val.set_defaults(func=cmd_validate)
    p_bp = sub.add_parser("blueprint"); p_bp.add_argument("id"); p_bp.add_argument("--json", action="store_true"); p_bp.set_defaults(func=cmd_blueprint)
    p_stats = sub.add_parser("stats"); p_stats.set_defaults(func=cmd_stats)
    p_exp = sub.add_parser("export"); p_exp.add_argument("--out", default="web/farms.json"); p_exp.set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
