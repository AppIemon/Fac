# Fac — AI 공장 월드

크리에이티브 / OP가 있는 전제에서, **구조물 · 바이옴 · 몹 · 차원**을 데이터로 고정해 두고, AI가 공장을 배치하고 **직접 테스트한 뒤** 마인크래프트 데이터팩으로 내보냅니다.

대상: **Java Edition 26.2** (data pack format 107.1). Paper 26.2에서 로드 검증.

## 월드가 하는 일

| 차원 | 역할 |
| --- | --- |
| `fac:campus` | 본부, 사일로, 철, 작물, 나무, 조약돌, 제련 |
| `fac:nether_works` | 금 홀, 석영 |
| `fac:end_works` | 후렴과, 엔더 진주, 셜커 |
| `fac:void_stack` | 크리퍼 / 스켈레톤 / 거미 스택 |

새 월드를 만들 때 월드 타입 **Fac Factory** (`fac:factory`) 를 고르면 오버월드/네더/엔드 자체가 공장 플로어가 됩니다. 이미 있는 월드에서는 `/execute in fac:campus run tp @s 8 66 8` 로 들어갑니다.

## AI가 돌리는 루프

1. **카탈로그**에서 모듈(철 주조소, 금 홀, …)과 생산량(개/시간)을 읽는다.
2. 목표 생산량을 채울 때까지 모듈을 32칸 그리드에 놓는다. 차원·바이옴·몹 요구를 지킨다.
3. **1시간 시뮬** — 사일로 버퍼, 벨트 용량, 입력 결핍을 계산한다.
4. 합격할 때까지 벨트 증설 / 모듈 추가.
5. `datapacks/fac` 데이터팩과 `web/` 대시보드를 내보낸다.

```bash
PYTHONPATH=src python3 -m fac complete --out .
PYTHONPATH=src python3 -m unittest tests/test_factory.py
python3 -m http.server 8765 --directory web   # 대시보드
```

Paper로 차원 로드까지 확인:

```bash
PYTHONPATH=src python3 -m fac live
```

인게임 (OP / 크리에이티브):

```
/function fac:validate
/function fac:setup
```

`setup` 은 각 모듈을 유리+프레임 구조물로 짓고, 역할 몹(알레이, 피글린, 엔더맨 등)을 소환하고, 포탈 허브와 `forceload` 앵커를 겁니다.

## 레이아웃을 바꾸고 싶을 때

`src/fac/catalog.py` 의 `DEFAULT_GOALS` 와 `MODULES` 가 설계 입력입니다. 목표만 바꿔도 AI가 모듈 수를 다시 맞춥니다.
