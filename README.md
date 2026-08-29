# Fac — 야생 팜 설계 지식베이스 + 설계 도구

**야생(서바이벌)에서 지을 팜/공장을 AI로 미리 설계**하는 도구입니다. 유튜브/설계도로 검증된 팜을 **작동 원리 · 요구조건 · 산출물**로 정리해 두었고, **작동 원리만 알면 바로 설계도(블루프린트)** 를 뽑을 수 있습니다.

대상 버전: **Minecraft 26.2** (Java, data pack format 107.1, Java 25 런타임).

## 1. 팜 지식베이스 (핵심)

`farms/data/*.json` 에 **엄선된 서바이벌 팜 100개** 가 들어 있습니다. 각 항목은 다음을 담습니다.

- `principle` — 핵심 작동 원리 (스폰/이송/처치/수집)
- `mechanics` — 메커니즘 태그 (예: `spawning_dark`, `water_stream`, `fall_damage`, `observer_harvest`, `crafter` …)
- 요구조건 — 차원 / 바이옴 / Y / 광원 / 크기(footprint)
- 구성 — 주요 블록, 필요 몹, 투입/산출 아이템
- 생산량·AFK·레드스톤 난이도, 버전 상태(`works` / `works_with_caveat` / `situational`), 주의사항, 출처(제작자)

카테고리: 몹/경험치 27 · 자원 15 · 작물 19 · 나무 12 · 동물 12 · 유틸/레드스톤 15 = **100**.

### 최신 버전 검증

지식베이스의 **모든 블록/아이템/몹/바이옴 ID를 실제 26.2 레지스트리로 검증**합니다. 레지스트리 스냅샷(`farms/registry/ids_26.2.json`)은 바닐라 26.2 데이터 리포트(`--reports`)에서 생성했습니다. → "지금 버전에 실제로 존재하는 요소인가"를 프로그램으로 보장.

```bash
PYTHONPATH=src python3 -m fac.farms validate     # 전체 100개 ID 검증
PYTHONPATH=src python3 -m fac.farms stats
PYTHONPATH=src python3 -m fac.farms list --category mob
PYTHONPATH=src python3 -m fac.farms search gold
```

> 참고: 실제 인게임 완전 검증은 100개를 헤드리스로 다 돌릴 수 없어, (1) 구성요소·버전 유효성은 레지스트리로 자동 검증하고, (2) 설계도는 실제로 빌드/미리보기 가능하게 했습니다. 각 팜의 `status`/`caveats`/`sources` 에 최신 버전 상태를 명시합니다.

## 2. 작동 원리 → 설계도

`principle`/`mechanics` 로부터 **빌드 순서 + 자재 목록(BOM) + 배치도**를 생성합니다.

```bash
PYTHONPATH=src python3 -m fac.farms blueprint iron_farm          # 텍스트 설계도
PYTHONPATH=src python3 -m fac.farms blueprint iron_farm --json   # 배치/자재 JSON
```

브라우저 대시보드로도 탐색합니다(검색·카테고리·설계도):

```bash
python3 -m http.server 8765 --directory web
# http://localhost:8765/farms.html
```

## 3. 실제 월드에 적용 (Paper 26.2 플러그인)

`plugin/` 의 `FacPlugin` 은 설계를 **실제 평면(superflat) 월드**에 짓고, 바이옴을 칠하고, 몹을 소환해 미리보기/검증합니다.

```bash
bash scripts/cloud-install.sh                      # JDK25+Maven, 테스트, 플러그인 빌드, Paper 캐시
PYTHONPATH=src python3 -m fac apply --render /tmp/r # 평면 월드에 적용 + 인게임 검증 + 맵 렌더
```

바로 켜지는 예시 서버(간단 철공장 평면월드)는 `scripts/make-dist.sh` 로 만듭니다.

## 레이아웃

| 경로 | 내용 |
| --- | --- |
| `farms/data/*.json` | 검증된 팜 100개 (지식베이스) |
| `farms/registry/ids_26.2.json` | 26.2 블록/아이템/몹/바이옴 ID (검증 기준) |
| `src/fac/farms/` | 스키마 · 로더 · 레지스트리 검증 · 설계도 생성 · CLI |
| `web/farms.html` | 팜 탐색 대시보드 |
| `plugin/` | Paper 26.2 플러그인 (실제 평면 월드 적용/미리보기) |
| `datapacks/fac` | 커스텀 월드젠 차원 데이터팩 (선택) |

## 테스트

```bash
PYTHONPATH=src python3 -m unittest tests/test_farms.py tests/test_factory.py
```
