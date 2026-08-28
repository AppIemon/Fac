# Fac — AI 공장 월드

크리에이티브 / OP가 있는 전제에서, **구조물 · 바이옴 · 몹 · 차원**을 데이터로 고정해 두고, AI가 공장을 배치하고 **직접 테스트한 뒤** 실제 마인크래프트 월드에 적용합니다.

대상: **Paper 26.2** (Java 25, data pack format 107.1).

두 가지 산출물이 있습니다.

- **Paper 플러그인 (기본, 실제 평면 월드)** — `plugin/` 의 `FacPlugin` 이 AI 설계를 읽어 **진짜 평면(superflat) 월드**에 구조물을 짓고, 바이옴을 칠하고, 역할 몹을 소환합니다. 차원은 차원별 평면 월드(`fac_campus`, `fac_nether_works`, `fac_end_works`, `fac_void_stack`)로 만들어집니다.
- **데이터팩** — `datapacks/fac` 는 커스텀 월드젠 차원 프리셋 버전입니다(월드 생성 시 선택).

## 월드가 하는 일

| 차원 (플러그인 월드) | 역할 |
| --- | --- |
| `fac:campus` (`fac_campus`) | 본부, 사일로, 철, 작물, 나무, 조약돌, 제련 |
| `fac:nether_works` (`fac_nether_works`) | 금 홀, 석영, 호글린 |
| `fac:end_works` (`fac_end_works`) | 후렴과, 엔더 진주, 셜커 |
| `fac:void_stack` (`fac_void_stack`) | 크리퍼 / 스켈레톤 / 거미 스택 |

플러그인은 각 차원을 **평면 월드**로 만들고, y=63 에 공장 바닥 슬래브를 깐 뒤 그 위(y=64)에 32칸 그리드로 모듈을 배치합니다.

## AI가 돌리는 루프

1. **카탈로그**에서 모듈(철 주조소, 금 홀, …)과 생산량(개/시간)을 읽는다.
2. 목표 생산량을 채울 때까지 모듈을 32칸 그리드에 놓는다. 차원·바이옴·몹 요구를 지킨다.
3. **1시간 시뮬** — 사일로 버퍼, 벨트 용량, 입력 결핍을 계산한다.
4. 합격할 때까지 벨트 증설 / 모듈 추가.
5. `datapacks/fac` 데이터팩과 `web/` 대시보드를 내보낸다.

```bash
# 설계 → 시뮬 → 합격 → 내보내기 (web/factory.json + datapacks/fac)
PYTHONPATH=src python3 -m fac complete --out .
PYTHONPATH=src python3 -m unittest tests/test_factory.py
python3 -m http.server 8765 --directory web   # 대시보드
```

### Paper 플러그인 — 실제 평면 월드에 적용 (기본 경로)

```bash
# 개발 환경 준비 (JDK 25 + Maven + Paper 26.2 캐시 + 플러그인 빌드)
bash scripts/cloud-install.sh

# AI가 설계 → 플러그인으로 실제 평면 월드에 짓고 → 스스로 검증 → 맵 렌더
PYTHONPATH=src python3 -m fac apply --render /tmp/fac-renders
```

`fac apply` 는 설계를 새로 뽑고, Paper 26.2 를 띄워 `FacPlugin` 을 로드한 뒤 RCON 으로 다음을 실행합니다.

```
/fac setup      # 4개 평면 월드 생성 + 구조물/바이옴/몹 배치
/fac validate   # 월드·모듈·엔티티 점검 (ok=true 확인)
/fac status     # 현재 상태 요약
/fac render <dir>  # 각 월드 top-down PNG 저장
/fac tp <campus|nether_works|end_works|void_stack>
```

성공 시 `worlds=4 modules=30 blocks=~104k mobs=14 mobFailures=0` 와 `FAC VALIDATE ok=true` 가 나옵니다.

### 데이터팩 — 커스텀 월드젠 차원 (선택 경로)

```bash
PYTHONPATH=src python3 -m fac live   # Paper 로 데이터팩 차원 로드 검증
```

새 월드를 만들 때 월드 타입 **Fac Factory** (`fac:factory`) 를 고르면 됩니다. 인게임(OP/크리에이티브)에서 `/function fac:setup`, `/function fac:validate`.

## 레이아웃을 바꾸고 싶을 때

`src/fac/catalog.py` 의 `DEFAULT_GOALS` 와 `MODULES` 가 설계 입력입니다. 목표만 바꿔도 AI가 모듈 수를 다시 맞춥니다.
