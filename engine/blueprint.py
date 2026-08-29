"""설계도 문서 생성: 원리/카탈로그 -> 사람이 그대로 따라 지을 수 있는 문서."""
from __future__ import annotations

from . import archetypes, catalog, mechanics as M
from .principle import Principle, resolve

CHECKLIST = [
    "스폰 구역 블록광이 0인가? (횃불/용암/빛나는 블록 전부 제거)",
    "주변 128블록 내 경쟁 스폰 지면을 차단했는가? (동굴 밀봉, 반 블록/광원)",
    "AFK 지점이 스폰 구역에서 24블록 이상, 수거부에서 128블록 이내인가?",
    "아이템이 5분 안에 호퍼에 들어가는가? (안 그러면 소멸)",
    "호퍼 처리량이 산출량보다 큰가? (호퍼 1개 = 초당 2.5개)",
    f"청크 로딩 대책이 있는가? 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됨 → AFK 또는 /forceload",
    "몹이 물길 밖으로 새어나가는 틈이 없는가? (거미는 벽 등반, 엔더맨은 순간이동)",
    "상자가 가득 찼을 때 팜이 멈추지 않게 오버플로 라인이 있는가?",
]


def _section(title: str) -> str:
    return f"\n{'=' * 72}\n{title}\n{'=' * 72}"


def render_document(name: str, result: archetypes.BuildResult,
                    header: list[str] | None = None,
                    reasoning: list[str] | None = None,
                    extra_warnings: list[str] | None = None) -> str:
    g = result.grid
    sx, sy, sz = g.size
    out: list[str] = []
    out.append(f"# 설계도: {name}")
    out.append(f"기준 버전: Minecraft {M.GAME_VERSION} ({M.GAME_VERSION_NAME}, {M.GAME_VERSION_DATE})")
    for line in header or []:
        out.append(line)

    out.append(_section("1. 작동 원리"))
    out.append(result.principle or "(미기재)")
    if reasoning:
        out.append("\n[설계 근거]")
        out.extend(f"  - {r}" for r in reasoning)

    out.append(_section("2. 규격"))
    out.append(f"  가로(X) {sx} x 높이(Y) {sy} x 세로(Z) {sz} 블록")
    out.append(f"  배치 블록 수: {len(g.cells):,}개")
    out.append(f"  예상 산출: {result.rate}")

    out.append(_section("3. 층별 평면도 (위에서 내려다본 뷰)"))
    out.append(g.render_layers())
    out.append(g.legend())

    out.append(_section("4. 재료 목록"))
    for mat, n in g.material_list():
        out.append(f"  {mat:<28} {n:>6}개")

    out.append(_section("5. 시공 순서"))
    out.extend(f"  {s}" for s in result.steps)

    if g.annotations:
        out.append(_section("6. 설계 메모"))
        out.extend(f"  * {a}" for a in g.annotations)

    warns = list(result.warnings) + list(extra_warnings or [])
    if warns:
        out.append(_section("7. 경고 / 자주 실패하는 지점"))
        out.extend(f"  ! {w}" for w in warns)

    out.append(_section("8. 시공 후 점검표"))
    out.extend(f"  [ ] {c}" for c in CHECKLIST)
    return "\n".join(out)


def from_catalog(farm_id: str) -> str:
    f = catalog.get(farm_id)
    result = archetypes.build(f["arch"], f["params"])
    result.principle = f["principle"]
    header = [
        f"분류: {catalog.CAT_KO.get(f['cat'], f['cat'])} / 차원: {f['dim']} / 난이도: {'★' * f['diff']}",
        f"영문명: {f['en']}",
        f"아키타입: {f['arch']}",
        f"검증 상태: {f['verify']}" + (f"  ({f['risk']})" if f.get("risk") else ""),
        f"참고 설계 계보(검색 키워드): {', '.join(f['refs']) or '-'}",
        f"AFK 필요: {'예' if f['afk'] else '아니오'}",
    ]
    extra = []
    if f["verify"] == "at_risk":
        extra.append("이 팜은 최근 버전 변경/버그성 메커니즘 의존으로 재검증 필요 항목이다. "
                     "크리에이티브에서 먼저 시험 시공할 것.")
    if f.get("risk"):
        extra.append(f["risk"])
    return render_document(f"{f['ko']} ({f['id']})", result, header, None, extra)


def from_principle(spec: dict) -> str:
    p = Principle.from_dict(spec)
    r = resolve(p)
    result = archetypes.build(r.archetype, r.params)
    header = [
        f"입력 원리: source={p.source} / transport={p.transport} / "
        f"process={p.process} / collect={p.collect}",
        f"대상: {p.target} / 차원: {p.dimension}",
        f"선택된 아키타입: {r.archetype}",
        f"확정 파라미터: {r.params}",
    ]
    return render_document(f"{p.target} 팜 (원리 기반 자동 설계)", result,
                           header, r.reasoning, r.warnings)
