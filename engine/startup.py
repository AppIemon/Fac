"""시운전 절차 생성 — 설계에서 '어디에 무엇을 넣고 어떤 순서로 켜는가'를 뽑는다.

공장은 켜는 순서를 틀리면 망가진다. 특히:
  · 물보다 용암을 먼저 부으면 흑요석이 되어 양동이를 날린다
  · Litematica 는 유체를 놓지 못하는 경우가 많아 손으로 채워야 한다
  · 관측기 2개짜리 클럭은 놓는 즉시 돈다 — 준비 전에 놓으면 헛돈다
"""
from __future__ import annotations

from collections import defaultdict

from .blocks import OFFSET, OPPOSITE
from .schematic import Schematic

# 유체/식재/장전이 필요한 블록과 안내 문구
NEEDS_BUCKET = {"water": "물 양동이", "lava": "용암 양동이"}
NEEDS_PLANTING = {"kelp": "켈프", "moss_block": "이끼 블록 (씨앗)",
                  "sugar_cane": "사탕수수", "sand": "모래"}
NEEDS_LOADING = {"dispenser": "발사기 — 내용물을 채워야 작동한다",
                 "dropper": "드로퍼 — 사슬 시작점만 초기 장전 필요",
                 "crafter": "제작기 — 재료가 9칸에 다 차야 제작한다"}
SWITCHES = {"lever": "레버 — 켜야 돈다", "button": "버튼"}


def _fed_targets(s: Schematic) -> dict:
    fed = defaultdict(list)
    for p, b in s.blocks.items():
        if b.short in ("hopper", "dropper"):
            dx, dy, dz = OFFSET[b.properties["facing"]]
            fed[(p[0] + dx, p[1] + dy, p[2] + dz)].append(p)
    return fed


def analyze(s: Schematic) -> dict:
    """시운전에 필요한 지점을 분류한다."""
    fed = _fed_targets(s)
    out = {
        "buckets": defaultdict(list), "planting": defaultdict(list),
        "loading": defaultdict(list), "switches": defaultdict(list),
        "output_chests": [], "buffer_chests": [], "prime_points": [],
        "clocks": [], "risky_pairs": [],
    }
    for p, b in sorted(s.blocks.items()):
        k = b.short
        if k in NEEDS_BUCKET:
            out["buckets"][k].append(p)
        if k in NEEDS_PLANTING:
            out["planting"][k].append(p)
        if k in NEEDS_LOADING and (k != "dropper" or not fed.get(p)):
            out["loading"][k].append(p)
        if k in SWITCHES:
            out["switches"][k].append(p)
        if k == "chest":
            drained = s.get(p[0], p[1] - 1, p[2]).short == "hopper"
            (out["buffer_chests"] if drained else out["output_chests"]).append(p)
        if k == "observer":
            # 서로 마주보는 관측기 = 자가 발진 클럭
            f = b.properties["facing"]
            dx, dy, dz = OFFSET[f]
            n = s.get(p[0] + dx, p[1] + dy, p[2] + dz)
            # 서로를 마주 보는 관측기 두 개 = 자가 발진 클럭. 짝이므로 한 번만 센다.
            if n.short == "observer" and n.properties["facing"] == OPPOSITE[f]:
                pair = tuple(sorted((p, (p[0] + dx, p[1] + dy, p[2] + dz))))
                if pair not in out["clocks"]:
                    out["clocks"].append(pair)

    # 물과 용암이 가까이 있는 곳 = 주입 순서가 중요한 지점
    lava = set(out["buckets"].get("lava", []))
    for w in out["buckets"].get("water", []):
        for dx, dy, dz in OFFSET.values():
            if (w[0] + dx, w[1] + dy, w[2] + dz) in lava:
                out["risky_pairs"].append((w, (w[0] + dx, w[1] + dy, w[2] + dz)))
    return out


def render(name: str, s: Schematic, notes: list[str] | None = None) -> str:
    a = analyze(s)
    L = [f"# 시운전 절차: {name}", ""]

    L.append("## 0. 준비물")
    for k, v in sorted(a["buckets"].items()):
        L.append(f"  · {NEEDS_BUCKET[k]}  ({len(v)}칸 채워야 함 — 무한 수원을 만들면 양동이 2개면 된다)")
    for k, v in sorted(a["planting"].items()):
        L.append(f"  · {NEEDS_PLANTING[k]}  x{len(v)}")
    for k, v in sorted(a["loading"].items()):
        L.append(f"  · {NEEDS_LOADING[k]}  x{len(v)}")

    L += ["", "## 1. 조립",
          "  Litematica 로 붙여 넣는다. 아래층부터 위로 쌓아야 중력 블록이 안 떨어진다.",
          "  ※ Litematica 는 물·용암을 놓지 못하는 경우가 많다. 유체는 2단계에서 손으로 채운다."]
    if a["clocks"]:
        L.append("  ※ 관측기 클럭은 놓는 즉시 돈다. 준비가 끝날 때까지 한쪽 관측기를 빼 두면 편하다:")
        for p, q in a["clocks"][:6]:
            L.append(f"      {p} ↔ {q}")

    L += ["", "## 2. 유체 주입 (순서가 중요하다)"]
    if a["risky_pairs"]:
        L.append("  물과 용암이 맞닿는 지점이 있다. 반드시 물을 먼저, 용암을 나중에 붓는다.")
        L.append("  순서를 바꾸면 흐르는 물이 용암 수원에 닿아 흑요석이 되고 양동이를 날린다.")
        for w, l in a["risky_pairs"][:8]:
            L.append(f"      물 {w}  →  용암 {l}")
        if len(a["risky_pairs"]) > 8:
            L.append(f"      … 외 {len(a['risky_pairs']) - 8}쌍")
    for k in ("water", "lava"):
        v = a["buckets"].get(k, [])
        if v:
            ys = sorted({p[1] for p in v})
            L.append(f"  {NEEDS_BUCKET[k]}: {len(v)}칸, 높이 Y={ys[0]}~{ys[-1]}")

    L += ["", "## 3. 식재 / 씨앗"]
    for k, v in sorted(a["planting"].items()):
        if k == "sand":
            continue
        L.append(f"  {NEEDS_PLANTING[k]}: " + ", ".join(str(p) for p in v[:8])
                 + (" …" if len(v) > 8 else ""))

    L += ["", "## 4. 초기 장전 (고리 점화)"]
    for k, v in sorted(a["loading"].items()):
        L.append(f"  {k}: " + ", ".join(str(p) for p in v[:8])
                 + (" …" if len(v) > 8 else ""))
    L.append("  되먹임 고리는 스스로 시작하지 못한다. 첫 재료를 사람이 넣어야 돈다.")

    if a["switches"]:
        L += ["", "## 5. 스위치"]
        for k, v in sorted(a["switches"].items()):
            L.append(f"  {SWITCHES[k]}: " + ", ".join(str(p) for p in v))
    else:
        L += ["", "## 5. 스위치",
              "  레버가 없다. 관측기 클럭이 자가 발진하므로 유체·재료만 채우면 바로 돈다."]

    L += ["", "## 6. 산출 확인"]
    for p in a["output_chests"][:12]:
        L.append(f"  상자 {p}")
    for n in notes or []:
        L.append(f"  ※ {n}")

    if s.notes:
        L += ["", "## 7. 설계 메모"]
        for n in s.notes:
            L.append(f"  · {n}")
    return "\n".join(L)
