"""팜 카탈로그 조회."""
from __future__ import annotations

import json
import pathlib

_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "farms.json"

CAT_KO = {
    "mob": "자연 스폰 몹", "spawner": "스포너", "crop": "경작지/식물",
    "column": "기둥 성장", "animal": "동물", "village": "마을/골렘/습격",
    "nether": "네더", "end": "엔드", "resource": "자원 생성", "infra": "인프라/공정",
}


def load() -> dict:
    return json.loads(_PATH.read_text(encoding="utf-8"))


def farms() -> list[dict]:
    return load()["farms"]


def get(farm_id: str) -> dict:
    for f in farms():
        if f["id"] == farm_id:
            return f
    raise KeyError(f"카탈로그에 없는 팜: {farm_id}")


def search(q: str = "", cat: str = "", dim: str = "", max_diff: int = 5,
           arch: str = "", at_risk: bool | None = None) -> list[dict]:
    out = []
    ql = q.lower()
    for f in farms():
        if cat and f["cat"] != cat:
            continue
        if dim and f["dim"] != dim:
            continue
        if arch and f["arch"] != arch:
            continue
        if f["diff"] > max_diff:
            continue
        if at_risk is not None and (f["verify"] == "at_risk") != at_risk:
            continue
        if ql:
            blob = " ".join([f["id"], f["ko"], f["en"], f["principle"], f.get("risk", "")]).lower()
            if ql not in blob:
                continue
        out.append(f)
    return out
