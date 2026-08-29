"""Fac CLI - 팜/공장 설계 엔진.

  python3 -m engine.cli list --cat mob
  python3 -m engine.cli show general_mob_tower
  python3 -m engine.cli design general_mob_tower --out blueprints/
  python3 -m engine.cli principle --json '{"source":"natural_spawn","target":"creeper","process":"fall"}'
  python3 -m engine.cli facts
  python3 -m engine.cli stats
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import blueprint, catalog, chain as C, litedoc, mechanics as M
from .designs import REGISTRY as DESIGNS, build as build_design
from .archetypes import ARCHETYPES
from .principle import COLLECTS, PROCESSES, SOURCES, TRANSPORTS


def cmd_list(a) -> int:
    rows = catalog.search(q=a.q, cat=a.cat, dim=a.dim, max_diff=a.max_diff,
                          arch=a.arch, at_risk=a.at_risk)
    if not rows:
        print("조건에 맞는 팜이 없습니다.")
        return 1
    print(f"{len(rows)}개:")
    for f in rows:
        flag = "!" if f["verify"] == "at_risk" else " "
        print(f" {flag}{f['id']:<26} {'★'*f['diff']:<5} [{f['cat']:<8}] {f['ko']}")
    return 0


def cmd_show(a) -> int:
    f = catalog.get(a.farm_id)
    print(f"{f['ko']}  ({f['en']})")
    print(f"  id        : {f['id']}")
    print(f"  분류/차원  : {catalog.CAT_KO.get(f['cat'])} / {f['dim']}")
    print(f"  난이도     : {'★'*f['diff']}")
    print(f"  작동 원리  : {f['principle']}")
    print(f"  산출량     : {f['rate'] or '-'}")
    print(f"  아키타입   : {f['arch']}  params={f['params']}")
    print(f"  검증       : {f['verify']}")
    if f.get("risk"):
        print(f"  주의       : {f['risk']}")
    print(f"  검색 키워드: {', '.join(f['refs']) or '-'}")
    return 0


def cmd_design(a) -> int:
    doc = blueprint.from_catalog(a.farm_id)
    if a.out:
        p = pathlib.Path(a.out)
        if p.is_dir() or a.out.endswith("/"):
            p.mkdir(parents=True, exist_ok=True)
            p = p / f"{a.farm_id}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(doc + "\n", encoding="utf-8")
        print(f"저장: {p}")
    else:
        print(doc)
    return 0


def cmd_principle(a) -> int:
    try:
        spec = json.loads(a.json)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}", file=sys.stderr)
        return 2
    try:
        doc = blueprint.from_principle(spec)
    except ValueError as e:
        print(f"원리 명세 오류: {e}", file=sys.stderr)
        return 2
    if a.out:
        p = pathlib.Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(doc + "\n", encoding="utf-8")
        print(f"저장: {p}")
    else:
        print(doc)
    return 0


def cmd_litematic(a) -> int:
    params = {}
    if a.length:
        params["length"] = a.length
    try:
        d = build_design(a.design, **params)
    except (KeyError, ValueError) as e:
        print(f"설계 오류: {e}", file=sys.stderr)
        return 2
    title = f"{d.schematic.description or a.design}"
    res = litedoc.export(title, d, a.out)
    print(f"  .litematic : {res['litematic']}  ({res['bytes']:,} bytes)")
    print(f"  시공 문서   : {res['doc']}")
    print(f"  왕복 검증   : {'통과' if res['verified'] else '실패'} — {res['messages'][0]}")
    if not res["verified"]:
        for m in res["messages"][1:]:
            print("    ", m, file=sys.stderr)
        return 1
    return 0


def _load_registry():
    import importlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "data"))
    return importlib.import_module("processes").REGISTRY


def cmd_chain(a) -> int:
    reg = _load_registry()
    if a.action == "list":
        print(f"공정 {len(reg.by_id)}개:")
        for pid, p in sorted(reg.by_id.items()):
            io = " + ".join(sorted(p.inputs)) or "(원료 없음)"
            print(f"  {pid:<32} {io} → {' + '.join(sorted(p.outputs))}")
        return 0
    if a.action == "items":
        print("생산 가능한 아이템:")
        for item in reg.items():
            makers = [p.id for p in reg.producers(item)]
            print(f"  {item:<20} {'← ' + ', '.join(makers) if makers else '(원료 - 직접 공급)'}")
        return 0

    picks = {}
    for spec in a.pick or []:
        if "=" not in spec:
            print(f"--pick 형식은 item=process_id 다: {spec}", file=sys.stderr)
            return 2
        k, v = spec.split("=", 1)
        picks[k] = v
    try:
        p = C.plan(a.item, a.rate, reg, picks)
    except C.ChainError as e:
        print(f"체인 오류: {e}", file=sys.stderr)
        return 2
    doc = C.render(p)
    if a.out:
        path = pathlib.Path(a.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(doc + "\n", encoding="utf-8")
        print(f"저장: {path}")
    else:
        print(doc)
    return 0


def cmd_facts(a) -> int:
    print(f"Minecraft {M.GAME_VERSION} ({M.GAME_VERSION_NAME}, {M.GAME_VERSION_DATE}) 기준")
    print("  O = 공식 문서 확인,  ~ = 실측/통설 추정\n")
    for f in M.fact_sheet():
        print(" ", f)
    return 0


def cmd_vocab(a) -> int:
    for title, table in (("source (산출원)", SOURCES), ("transport (이송)", TRANSPORTS),
                         ("process (처리)", PROCESSES), ("collect (수거)", COLLECTS)):
        print(f"\n[{title}]")
        for k, v in table.items():
            print(f"  {k:<18} {v}")
    print(f"\n[archetype (설계 원형)]\n  " + "\n  ".join(sorted(ARCHETYPES)))
    return 0


def cmd_stats(a) -> int:
    from collections import Counter
    fs = catalog.farms()
    print(f"총 {len(fs)}개")
    for key, label in (("cat", "분류"), ("dim", "차원"), ("arch", "아키타입"), ("verify", "검증")):
        c = Counter(f[key] for f in fs)
        print(f"\n[{label}]")
        for k, n in c.most_common():
            print(f"  {k:<22} {n:>3}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fac", description="마인크래프트 팜/공장 설계 엔진")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="카탈로그 조회")
    p.add_argument("--q", default="")
    p.add_argument("--cat", default="", choices=[""] + list(catalog.CAT_KO))
    p.add_argument("--dim", default="", choices=["", "overworld", "nether", "end"])
    p.add_argument("--arch", default="", choices=[""] + sorted(ARCHETYPES))
    p.add_argument("--max-diff", type=int, default=5, dest="max_diff")
    p.add_argument("--at-risk", action="store_true", default=None, dest="at_risk")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("show", help="팜 요약")
    p.add_argument("farm_id")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("design", help="카탈로그 팜의 설계도 생성")
    p.add_argument("farm_id")
    p.add_argument("--out", default="")
    p.set_defaults(fn=cmd_design)

    p = sub.add_parser("principle", help="작동 원리만으로 설계도 생성")
    p.add_argument("--json", required=True)
    p.add_argument("--out", default="")
    p.set_defaults(fn=cmd_principle)

    p = sub.add_parser("chain", help="공장 연결 / 효율 맞추기")
    p.add_argument("action", choices=["plan", "list", "items"])
    p.add_argument("item", nargs="?", default="")
    p.add_argument("--rate", type=float, default=100.0, help="목표 개수/시간")
    p.add_argument("--pick", action="append", help="item=process_id (생산 공정 지정)")
    p.add_argument("--out", default="")
    p.set_defaults(fn=cmd_chain)

    p = sub.add_parser("litematic", help=".litematic 스케매틱 생성")
    p.add_argument("design", choices=sorted(DESIGNS))
    p.add_argument("--length", type=int, default=0)
    p.add_argument("--out", default="blueprints")
    p.set_defaults(fn=cmd_litematic)

    p = sub.add_parser("facts", help="검증된 수치 시트")
    p.set_defaults(fn=cmd_facts)

    p = sub.add_parser("vocab", help="원리 DSL 어휘")
    p.set_defaults(fn=cmd_vocab)

    p = sub.add_parser("stats", help="카탈로그 통계")
    p.set_defaults(fn=cmd_stats)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
