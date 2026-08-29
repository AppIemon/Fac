"""공장 연결 계층 — 산출/소비 속도를 물려 필요한 공장 수를 푼다.

핵심 개념
  Process : "유닛 1개가 시간당 무엇을 얼마나 먹고 뱉는가"
  plan()  : 목표 아이템/시간당 수량 -> 각 공정의 유닛 수를 위상순서로 역산

부산물 상계(netting)까지 한다. 예를 들어 스켈레톤 팜의 뼈로 뼛가루를 만들면
컴포스터 쪽 수요가 그만큼 줄어든다.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import mechanics as M

CONFIRMED = M.CONFIRMED
ESTIMATE = M.ESTIMATE


@dataclass(frozen=True)
class Process:
    """공정 하나. 모든 수치는 '유닛 1개당 시간당' 기준."""
    id: str
    name: str
    unit: str                                   # 유닛의 단위 (포기, 화로, 컴포스터…)
    outputs: dict[str, float]
    inputs: dict[str, float] = field(default_factory=dict)
    design: str | None = None                   # engine.designs 의 설계 이름
    design_param: str | None = None             # 유닛 수를 넘길 파라미터 이름
    max_units_per_build: int = 0                # 0 = 제한 없음
    verify: str = ESTIMATE
    source: str = ""
    limits: tuple[str, ...] = ()
    throttleable: bool = True
    """수요에 맞춰 조절되는가.

    True  : 먹인 만큼만 돈다 (제작기/화로/컴포스터). 가동률이 낮으면 원료도
            그만큼만 먹는다.
    False : 수요와 무관하게 자기 속도로 계속 나온다 (작물/몹 팜). 남는 건 부산물."""

    def primary(self) -> str:
        return max(self.outputs, key=lambda k: self.outputs[k])


class Registry:
    def __init__(self, processes: list[Process] | None = None):
        self.by_id: dict[str, Process] = {}
        for p in processes or []:
            self.add(p)

    def add(self, p: Process) -> Process:
        if p.id in self.by_id:
            raise ValueError(f"중복 공정 id: {p.id}")
        for item, rate in {**p.inputs, **p.outputs}.items():
            if rate <= 0:
                raise ValueError(f"{p.id}: {item} 속도가 0 이하")
        self.by_id[p.id] = p
        return p

    def producers(self, item: str) -> list[Process]:
        return [p for p in self.by_id.values() if item in p.outputs]

    def items(self) -> list[str]:
        out = set()
        for p in self.by_id.values():
            out |= set(p.outputs) | set(p.inputs)
        return sorted(out)


@dataclass
class Node:
    process: Process
    demand: float          # 이 공정이 채워야 할 주력 산출 수요 (부산물 상계 후)
    units_exact: float
    units: int
    produced: dict[str, float]      # 실제 산출 (조절 가능하면 수요만큼)
    consumed: dict[str, float]      # 실제 소비 (가동률에 비례)
    item: str              # 이 공정이 선택된 이유가 된 아이템
    capacity: float = 0.0  # 유닛 수 x 유닛당 능력 (최대치)

    @property
    def utilization(self) -> float:
        return (self.demand / self.capacity) if self.capacity else 0.0

    @property
    def builds(self) -> list[int]:
        """한 채당 유닛 수로 쪼갠 시공 단위."""
        cap = self.process.max_units_per_build
        if not cap or self.units <= cap:
            return [self.units]
        full, rest = divmod(self.units, cap)
        return [cap] * full + ([rest] if rest else [])


@dataclass
class Plan:
    target: str
    rate: float
    nodes: list[Node] = field(default_factory=list)
    raw: dict[str, float] = field(default_factory=dict)      # 공급원 없는 원료
    surplus: dict[str, float] = field(default_factory=dict)  # 남는 부산물
    warnings: list[str] = field(default_factory=list)
    choices: dict[str, str] = field(default_factory=dict)    # item -> process id


class ChainError(Exception):
    pass


def _choose(item: str, reg: Registry, choices: dict[str, str],
            warnings: list[str]) -> Process | None:
    if item in choices:
        pid = choices[item]
        if pid not in reg.by_id:
            raise ChainError(f"선택한 공정이 없다: {pid}")
        return reg.by_id[pid]
    cands = reg.producers(item)
    if not cands:
        return None
    if len(cands) > 1:
        pick = sorted(cands, key=lambda p: p.id)[0]
        warnings.append(
            f"{item} 생산 공정이 {len(cands)}개다 → {pick.id} 를 골랐다. "
            f"다른 걸 쓰려면 --pick {item}={'|'.join(sorted(c.id for c in cands))}")
        return pick
    return cands[0]


def _graph(target: str, reg: Registry, choices: dict[str, str],
           warnings: list[str]) -> tuple[list[Process], dict[str, Process], list[str]]:
    """공정 그래프를 만든다. 되먹임 고리는 예외가 아니라 기록해서 돌려준다.

    연료 -> 화로 -> 연료, 뼛가루 -> 이끼 -> 퇴비통 -> 뼛가루 처럼
    실제 공장은 고리를 이룬다. 고리 자체는 정상이고, '한 바퀴 돌 때
    순손실인 고리'만 문제다 (그건 solve 단계에서 발산으로 잡힌다).
    """
    chosen: dict[str, Process] = {}
    order: list[Process] = []
    cycles: list[str] = []
    state: dict[str, int] = {}   # 0=방문중, 1=완료

    def visit(item: str, trail: tuple[str, ...]) -> None:
        proc = _choose(item, reg, choices, warnings)
        if proc is None:
            return
        chosen[item] = proc
        if state.get(proc.id) == 1:
            return
        if state.get(proc.id) == 0:
            loop = " → ".join(trail[trail.index(proc.id):] + (proc.id,)) \
                if proc.id in trail else " → ".join(trail + (proc.id,))
            cycles.append(loop)
            return
        state[proc.id] = 0
        for need in sorted(proc.inputs):
            visit(need, trail + (proc.id,))
        state[proc.id] = 1
        order.append(proc)

    visit(target, ())
    order.reverse()   # 소비자가 먼저 오도록
    return order, chosen, cycles


def plan(target: str, rate: float, reg: Registry,
         choices: dict[str, str] | None = None) -> Plan:
    if rate <= 0:
        raise ChainError("목표 수량은 0보다 커야 한다")
    choices = dict(choices or {})
    warnings: list[str] = []

    if not reg.producers(target) and target not in choices:
        raise ChainError(
            f"{target} 를 만드는 공정이 없다. 등록된 아이템: {', '.join(reg.items())}")

    order, chosen, cycles = _graph(target, reg, choices, warnings)
    for loop in cycles:
        warnings.append(f"되먹임 고리: {loop} — 한 바퀴 순이익이 나야 수렴한다.")

    # --- 고정점 반복으로 각 공정의 가동량(x, 소수)을 푼다 -------------------
    # 고리가 있으면 위상정렬 한 번으로는 못 푼다. 수요를 채울 때까지 반복해서
    # 가동량을 키우고, 순이익 고리면 기하급수적으로 수렴한다.
    x: dict[str, float] = {p.id: 0.0 for p in order}
    by_id = {p.id: p for p in order}
    MAX_ITERS, EPS, RUNAWAY = 500, 1e-9, 1e12

    for _ in range(MAX_ITERS):
        supply_f: dict[str, float] = {}
        need_f: dict[str, float] = {target: float(rate)}
        for pid, run in x.items():
            if run <= 0:
                continue
            p = by_id[pid]
            for k, v in p.outputs.items():
                supply_f[k] = supply_f.get(k, 0.0) + v * run
            for k, v in p.inputs.items():
                need_f[k] = need_f.get(k, 0.0) + v * run
        settled = True
        for item, p in chosen.items():
            deficit = need_f.get(item, 0.0) - supply_f.get(item, 0.0)
            if deficit > EPS:
                x[p.id] += deficit / p.outputs[item]
                settled = False
        if any(v > RUNAWAY for v in x.values()):
            raise ChainError(
                "고리가 발산한다 — 한 바퀴 돌 때 순손실이라 아무리 키워도 목표를 못 채운다. "
                + (f"고리: {cycles[0]}" if cycles else ""))
        if settled:
            break
    else:
        raise ChainError(f"{MAX_ITERS}회 반복해도 수렴하지 않았다. 고리 수지를 확인할 것.")

    # --- 소수 가동량 -> 정수 유닛 + 실제 물동량 ---------------------------
    demand: dict[str, float] = {target: float(rate)}
    supply: dict[str, float] = {}
    nodes: list[Node] = []

    for proc in order:
        run = x.get(proc.id, 0.0)
        if run <= EPS:
            continue
        item = next((i for i in proc.outputs if chosen.get(i) is proc), proc.primary())
        per_unit = proc.outputs[item]
        exact = run
        units = max(1, math.ceil(exact - 1e-9))
        capacity = per_unit * units
        need = per_unit * run
        ratio = min(1.0, run / units) if proc.throttleable else 1.0
        produced = {k: v * units * ratio for k, v in proc.outputs.items()}
        consumed = {k: v * units * ratio for k, v in proc.inputs.items()}

        for k, v in produced.items():
            supply[k] = supply.get(k, 0.0) + v
        for k, v in consumed.items():
            demand[k] = demand.get(k, 0.0) + v

        nodes.append(Node(proc, need, exact, units, produced, consumed, item, capacity))

    # 공급원이 없는 원료 / 남는 부산물 정리
    raw: dict[str, float] = {}
    for item, want in demand.items():
        have = supply.get(item, 0.0)
        if want - have > 1e-9 and not reg.producers(item):
            raw[item] = round(want - have, 3)
    surplus = {i: round(s - demand.get(i, 0.0), 3)
               for i, s in supply.items() if s - demand.get(i, 0.0) > 1e-6 and i != target}
    over = round(supply.get(target, 0.0) - rate, 3)
    if over > 1e-6:
        surplus[target] = over

    warnings += _bottlenecks(nodes)
    return Plan(target, float(rate), nodes, raw, surplus, warnings,
                {i: p.id for i, p in chosen.items()})


def _bottlenecks(nodes: list[Node]) -> list[str]:
    """호퍼 라인이 흐름을 감당하는지 확인한다."""
    out: list[str] = []
    cap_per_hour = M.HOPPER_ITEMS_PER_SEC * 3600     # 호퍼 1줄 = 9,000개/시간
    for n in nodes:
        for item, rate in sorted(n.produced.items()):
            lines = math.ceil(rate / cap_per_hour)
            if lines > 1:
                out.append(
                    f"{n.process.id} 의 {item} 산출 {rate:,.0f}개/시간은 호퍼 1줄"
                    f"({cap_per_hour:,.0f}개/시간)로 못 받는다 → 라인을 {lines}줄로 나눌 것")
    return out


def render(p: Plan) -> str:
    L = [f"# 생산 계획: {p.target}  {p.rate:,.0f}개/시간",
         f"기준 버전: Minecraft {M.GAME_VERSION} ({M.GAME_VERSION_NAME})", ""]
    L.append("## 필요한 공장 (하류 → 상류)")
    for i, n in enumerate(p.nodes, 1):
        pr = n.process
        L.append(f"\n{i}. {pr.name}  [{pr.id}]")
        L.append(f"   유닛      : {n.units:,} {pr.unit}  (이론값 {n.units_exact:,.2f})")
        if n.builds != [n.units]:
            from collections import Counter
            grouped = ", ".join(f"{size}{pr.unit} x {cnt}채"
                                for size, cnt in Counter(n.builds).most_common())
            L.append(f"   시공 단위 : 총 {len(n.builds)}채 — {grouped}")
        throttle = "수요 연동" if pr.throttleable else "상시 가동"
        L.append(f"   가동률    : {n.utilization*100:5.1f}%  "
                 f"(수요 {n.demand:,.1f} / 능력 {n.capacity:,.1f} 개/시간, {throttle})")
        if pr.inputs:
            L.append("   소비      : " + ", ".join(
                f"{k} {v:,.1f}/h" for k, v in sorted(n.consumed.items())))
        L.append("   생산      : " + ", ".join(
            f"{k} {v:,.1f}/h" for k, v in sorted(n.produced.items())))
        mark = "O" if pr.verify == CONFIRMED else "~"
        L.append(f"   근거      : [{mark}] {pr.source or '-'}")
        for lim in pr.limits:
            L.append(f"   한계      : {lim}")
        if pr.design:
            L.append(f"   설계도    : python3 -m engine.cli litematic {pr.design}"
                     + (f" --{pr.design_param} {n.builds[0]}" if pr.design_param else ""))

    if p.raw:
        L += ["", "## 직접 공급해야 하는 원료 (자동화 공정 미등록)"]
        L += [f"  {k:<28} {v:,.1f}개/시간" for k, v in sorted(p.raw.items())]
    if p.surplus:
        L += ["", "## 남는 부산물"]
        L += [f"  {k:<28} {v:,.1f}개/시간" for k, v in sorted(p.surplus.items())]
    if p.warnings:
        L += ["", "## 경고"]
        L += [f"  ! {w}" for w in p.warnings]
    L += ["", "## 주의",
          "  · 가동률이 낮은 공정은 그만큼 놀고 있다는 뜻이다. 목표 수량을 올리거나 "
          "유닛 수를 줄여 맞출 것.",
          f"  · 스폰 청크는 {M.SPAWN_CHUNKS_REMOVED_IN}에서 삭제됐다. 체인 전체가 "
          "한 플레이어의 AFK 범위 안이거나 /forceload 되어야 동시에 돈다."]
    return "\n".join(L)
