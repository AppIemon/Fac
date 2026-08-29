"""파라메트릭 설계 -> .litematic + 사람이 읽는 시공 문서."""
from __future__ import annotations

import pathlib

from . import mechanics as M
from .designs import Design
from .schematic import MC_DATA_VERSION_26_2, verify_litematic


def render(name: str, d: Design) -> str:
    s = d.schematic
    sx, sy, sz = s.size
    out = [f"# {name}",
           f"기준 버전: Minecraft {M.GAME_VERSION} ({M.GAME_VERSION_NAME}, {M.GAME_VERSION_DATE}) "
           f"· DataVersion {MC_DATA_VERSION_26_2}",
           "",
           "## 작동 원리", d.principle, ""]
    if d.circuit:
        out += ["## 신호 경로"] + [f"  {c}" for c in d.circuit] + [""]
    out += ["## 규격",
            f"  가로(X) {sx} × 높이(Y) {sy} × 세로(Z) {sz}  ·  블록 {len(s.blocks):,}개",
            f"  예상 산출: {d.rate}", "",
            "## 층별 평면도 (위 → 아래, 화면 위쪽이 북쪽)", s.preview(),
            "## 블록 기호", s.legend(), "",
            "## 재료 목록"]
    for mat, n in s.material_list():
        out.append(f"  {mat:<24} {n:>5}개")
    if d.manual_items:
        out += ["", "## 직접 놓아야 하는 것 (스케매틱에 안 들어감)"] + [f"  - {m}" for m in d.manual_items]
    out += ["", "## 시공 순서"] + [f"  {s_}" for s_ in d.steps]
    if s.notes:
        out += ["", "## 설계 메모"] + [f"  * {n}" for n in s.notes]
    if d.warnings:
        out += ["", "## 주의"] + [f"  ! {w}" for w in d.warnings]
    return "\n".join(out)


def export(design_name: str, d: Design, out_dir: str = "blueprints") -> dict:
    """.litematic + .txt 을 쓰고, 저장한 파일을 다시 읽어 검증한다."""
    base = pathlib.Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)
    lite = base / f"{d.schematic.name}.litematic"
    doc = base / f"{d.schematic.name}.txt"

    d.schematic.to_litematic(str(lite))
    ok, msgs = verify_litematic(str(lite), d.schematic)
    doc.write_text(render(design_name, d) + "\n", encoding="utf-8")
    return {"litematic": str(lite), "doc": str(doc), "verified": ok, "messages": msgs,
            "bytes": lite.stat().st_size}
