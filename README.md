# Fac — 마인크래프트 팜/공장 설계 엔진

야생에서 지을 팜·공장을 **미리 설계해보는 저장소**.
팜을 하나하나 외우는 대신, **작동 원리를 입력하면 설계도가 나오게** 만들어 뒀다.

> 기준 버전: **Minecraft Java Edition 26.2 "Chaos Cubed"** (2026-06-16)
> 2026년부터 버전 체계가 연도 기반으로 바뀌었다 (`1.21.x` → `26.x`).

---

## 공장 연결 / 효율 맞추기

목표 아이템과 시간당 수량만 주면 필요한 공장 수를 역산한다.

```bash
python3 -m engine.cli chain plan bone_meal --rate 500 --pick bone_meal=composter_sugar_cane
```
```
1. 컴포스터 (sugar_cane)   1대     가동률  91.7%   sugar_cane 7,003/h 소비
2. 사탕수수 팜           2,123포기  가동률 100.0%   총 34채 — 64포기 x 33채, 11포기 x 1채
                                                 → python3 -m engine.cli litematic sugarcane --length 64
```

핵심은 **가동률**이다. 공정을 두 종류로 나눠 계산한다:

| | 예 | 동작 |
|---|---|---|
| 수요 연동 | 제작기 · 화로 · 컴포스터 | 먹인 만큼만 돈다 → 가동률만큼만 원료를 먹는다 |
| 상시 가동 | 작물 팜 · 몹 팜 | 수요와 무관하게 자기 속도로 나온다 → 남으면 부산물 |

부산물은 자동으로 상계한다. 스켈레톤 팜의 뼈로 뼛가루를 만들면 컴포스터 쪽 수요가
그만큼 줄고, 남는 화살은 부산물로 잡힌다. 호퍼 1줄(9,000개/시간)을 넘는 흐름은
라인을 몇 줄로 나눠야 하는지 경고한다.

```bash
python3 -m engine.cli chain list     # 등록된 공정
python3 -m engine.cli chain items    # 만들 수 있는 아이템과 경로
```

## 설계 모듈

| 설계 | 무엇 | 자동화 |
|---|---|---|
| `sugarcane` | 사탕수수 팜 (관측기+피스톤, 진흙 아래 호퍼) | 완전 자동 |
| `cobblegen` | 조약돌 생성기 뱅크 (물먹임 계단) | 채굴만 수동 |
| `smelter` | 자동 화로 (원료/연료/산출 3라인) | 완전 자동 |
| `mossbed` | 이끼 베드 (뼛가루 발사기 + 물 세척 수거) | 이끼 수확만 수동 |
| `composterbank` | 퇴비통 뱅크 (초목/이끼 → 뼛가루) | 완전 자동 |
| `kelpfarm` | 켈프 팜 (부력 수거) — 연료 라인 앞단 | 완전 자동 |
| `stonegen` | **제자리 돌 생성기** — 조약돌이 아니라 '돌'을 직접 낸다 | 채굴만 수동 |
| `smelter_dropper` | **드로퍼 분배 화로** — 호퍼 줄의 편중을 없앤다 | 완전 자동 |
| `mossbed_auto` | **다층 자동 이끼 베드** — 피스톤 수확 + 제자리 돌 재생성 | 완전 자동 |
| `smoothstone_factory` | **매끄러운 돌 공장** (생성기 + 드로퍼 화로 한 덩어리) | 채굴만 수동 |

바닐라에는 자동 블록 파괴기가 없어서, 블록을 캐야 하는 공정은 채굴만 수동이고
수거부터 아래로는 전부 자동이다. 각 설계의 문서에 어디까지가 자동인지 적혀 있다.

## .litematic 출력 (실제로 지을 수 있는 설계도)

```bash
python3 -m engine.cli litematic sugarcane --length 12
#   .litematic : blueprints/sugarcane_12.litematic
#   시공 문서   : blueprints/sugarcane_12.txt
#   왕복 검증   : 통과 — 블록 420칸 전부 일치
```

Litematica 모드에 그대로 넣으면 되는 스케매틱과, 층별 평면도·재료·시공 순서·신호 경로가
담긴 문서를 같이 낸다. 블록 상태(피스톤/관측기 `facing`)까지 정확히 들어간다.

**3중 검증을 거친다:**
1. `verify_litematic()` — 저장한 파일을 다시 읽어 블록 단위 대조
2. `tools/inspect_litematic.py` — litemapy 없이 NBT 를 직접 파싱해 헤더/팔레트/비트패킹 검사
3. `tests/test_sugarcane.py` — **설계가 메커니즘상 실제로 도는지** 검사
   (물이 흙에 붙어 있나, 관측기가 3번째 칸을 보나, 급전된 블록이 피스톤에 닿나,
   레일이 흙 바로 아래인가, 물 수로 뚜껑이 있나 …)

## 30초 사용법

```bash
# 1) 원리만 넣으면 설계도가 나온다
python3 -m engine.cli principle --json '{
  "source":"natural_spawn","target":"creeper","transport":"water",
  "process":"fall","collect":"hopper","scale":{"platform":15,"layers":5}
}'

# 2) 엄선 100개 카탈로그에서 찾아 쓴다
python3 -m engine.cli list --cat nether
python3 -m engine.cli design gold_farm --out blueprints/

# 3) 설계에 쓰이는 검증된 수치를 본다
python3 -m engine.cli facts
```

출력에는 **층별 평면도 · 재료 목록 · 시공 순서 · 경고 · 점검표**가 전부 들어 있다.
예시는 [`blueprints/`](blueprints/) 에 있다.

---

## 이게 왜 필요한가

구버전 유튜브 설계도를 그대로 따라 지으면 **안 도는 팜이 많다.** 원인은 대체로 정해져 있다.

- **1.21.9에서 스폰 청크가 완전히 삭제됐다.** "스폰 지점에 지어두면 항상 돈다"는
  설계가 전부 무효가 됐고, `/forceload` 나 AFK로 대체해야 한다.
- 1.18부터 적대 몹은 **하늘광이 아니라 블록광 0**에서만 스폰한다.
- 네더에서 물길을 쓰는 설계는 애초에 작동하지 않는다 (물이 증발한다).
- 낙하 높이가 몹 체력과 안 맞으면 몹이 안 죽는다.

이 엔진은 **설계도를 그리기 전에 이런 모순을 먼저 잡아낸다.**

```
$ python3 -m engine.cli principle --json '{"source":"spawner","target":"blaze","process":"fall","dimension":"nether"}'
  ! 네더에서는 물이 즉시 증발한다 → transport를 piston/gravity/mob_ai 로 바꿔야 한다.
  ! blaze 은(는) 낙하 데미지가 통하지 않는다 → lava 또는 manual 로 바꿔야 한다.
  ! 스폰 청크는 1.21.9에서 삭제됨 → AFK 상주 또는 /forceload 로 청크를 고정해야 한다.
```

---

## 핵심 아이디어: 모든 팜은 5단계다

```
산출원(source) → 이송(transport) → 처리(process) → 수거(collect) → 저장(store)
```

이 5칸만 채우면 어떤 팜이든 설계된다. 자세한 건 [`docs/01_설계원리.md`](docs/01_설계원리.md).

---

## 카탈로그 (100개)

| 분류 | 개수 | 분류 | 개수 |
|---|---|---|---|
| 자연 스폰 몹 | 14 | 마을/골렘/습격 | 10 |
| 경작지/식물 | 14 | 동물 | 9 |
| 기둥 성장 | 11 | 자원 생성 | 9 |
| 네더 | 11 | 스포너 | 8 |
| 엔드 | 6 | 인프라/공정 | 8 |

차원별: 오버월드 78 / 네더 15 / 엔드 7

```bash
python3 -m engine.cli stats     # 통계
python3 -m engine.cli list      # 전체 목록
python3 -m engine.cli list --max-diff 2   # 초반에 지을 수 있는 것만
python3 -m engine.cli list --at-risk      # 재검증이 필요한 것만
```

---

## 검증 상태 (과장하지 않기)

- ✅ **93개**: 26.2 공식 문서로 **작동 원리가 성립함을 확인**함
- ⚠️ **7개**: 최근 버전 변경/버그성 메커니즘 의존 → **재검증 필요** (사유 명시됨)
- ❌ **인게임 실측은 하지 않았다.** `rate` 는 메커니즘 계산 기반 추정치다.
- ❌ `refs` 는 **출처 URL이 아니라 검색 키워드**다 (그 설계 계보로 알려진 제작자 이름).

자세한 건 [`docs/04_검증정책.md`](docs/04_검증정책.md).

---

## 구조

```
engine/
  mechanics.py    설계 상수 (낙하 공식/호퍼 속도/몹캡...) — 버전 바뀌면 여기만 고친다
  principle.py    원리 5칸 → 아키타입 선택 + 모순 검출   ← 이 프로젝트의 핵심
  archetypes.py   아키타입 12종 → 실제 복셀 설계도
  grid.py         복셀 그리드 + 층별 ASCII 렌더러
  blueprint.py    설계도 문서 조립
  catalog.py      100개 카탈로그 조회
  cli.py          명령줄
data/
  farms_src.py    100개 원본 (사람이 편집하는 곳)
  farms.json      빌드 산출물 (tools/build_catalog.py 가 생성)
docs/             설계 원리 / 버전 노트 / 워크플로 / 검증 정책
blueprints/       생성된 설계도 예시
tests/            27개 회귀 테스트
```

## 개발

```bash
python3 tools/build_catalog.py                 # 카탈로그 검증 + JSON 재생성
python3 -m unittest discover -s tests -v       # 테스트
```

새 팜 추가는 대부분 `data/farms_src.py` 에 한 줄 추가하면 끝이다.
정말 새로운 원리일 때만 `engine/archetypes.py` 에 함수를 하나 추가한다.
