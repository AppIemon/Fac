#!/usr/bin/env python3
"""data/farms_src.py -> data/farms.json 생성 + 무결성 검증."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

import farms_src  # noqa: E402
from engine import mechanics as M  # noqa: E402
from engine.archetypes import ARCHETYPES, build  # noqa: E402

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Fac farm catalog entry",
    "type": "object",
    "required": ["id", "ko", "en", "cat", "arch", "principle", "dim", "diff", "verify"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
        "ko": {"type": "string"},
        "en": {"type": "string"},
        "cat": {"enum": ["mob", "spawner", "crop", "column", "animal",
                          "village", "nether", "end", "resource", "infra"]},
        "arch": {"enum": sorted(ARCHETYPES)},
        "principle": {"type": "string", "minLength": 10},
        "dim": {"enum": ["overworld", "nether", "end"]},
        "rate": {"type": "string"},
        "diff": {"type": "integer", "minimum": 1, "maximum": 5},
        "afk": {"type": "boolean"},
        "refs": {"type": "array", "items": {"type": "string"}},
        "params": {"type": "object"},
        "risk": {"type": "string"},
        "verify": {"enum": ["mechanics", "at_risk"]},
    },
}


def main() -> int:
    farms = farms_src.FARMS
    errors: list[str] = []

    seen: set[str] = set()
    for f in farms:
        if f["id"] in seen:
            errors.append(f"중복 id: {f['id']}")
        seen.add(f["id"])
        if f["arch"] not in ARCHETYPES:
            errors.append(f"{f['id']}: 알 수 없는 아키타입 {f['arch']}")
            continue
        if not (1 <= f["diff"] <= 5):
            errors.append(f"{f['id']}: 난이도 범위 이탈")
        if len(f["principle"]) < 10:
            errors.append(f"{f['id']}: 작동 원리 설명이 너무 짧음")
        try:
            r = build(f["arch"], f["params"])
            if not r.grid.cells:
                errors.append(f"{f['id']}: 빈 설계도 생성")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{f['id']}: 빌드 실패 {exc!r}")

    if errors:
        print("검증 실패:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        return 1

    doc = {
        "game_version": M.GAME_VERSION,
        "game_version_name": M.GAME_VERSION_NAME,
        "game_version_date": M.GAME_VERSION_DATE,
        "count": len(farms),
        "verification_policy": (
            "verify=mechanics: 26.2 공식 위키 문서로 '작동 원리'를 검증함(실제 인게임 실측은 미실시). "
            "verify=at_risk: 최근 버전 변경 또는 버그성 메커니즘 의존으로 재검증이 필요함. "
            "refs는 출처 URL이 아니라 해당 설계 계보로 알려진 제작자 검색 키워드다."
        ),
        "farms": farms,
    }
    (ROOT / "data" / "farms.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "data" / "schema" / "farm.schema.json").write_text(
        json.dumps(SCHEMA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(farms)}개 팜 검증 통과 → data/farms.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
