# -*- coding: utf-8 -*-
"""엄선 100개 팜/공장 원본 데이터.

각 항목은 '작동 원리 한 줄'과 '엔진 파라미터'를 가진다.
원리만 읽으면 engine 이 바로 설계도를 뽑을 수 있게 설계된 스키마다.

refs = 그 설계 계보로 널리 알려진 제작자/설계명 (검색 키워드로 쓸 것. 특정 영상 URL이 아님)
verify:
  "mechanics"  = 26.2 메커니즘 문서로 원리 검증됨, 실측 미실시
  "at_risk"    = 최근 버전 변경으로 재검증 필요 (risk 필드 참조)
"""

FIELDS = ("id", "ko", "en", "cat", "arch", "principle", "dim", "rate",
          "diff", "afk", "refs", "params", "risk", "verify")

_R = []


def F(id, ko, en, cat, arch, principle, dim="overworld", rate="", diff=2,
      afk=True, refs=(), params=None, risk="", verify="mechanics"):
    _R.append(dict(id=id, ko=ko, en=en, cat=cat, arch=arch, principle=principle,
                   dim=dim, rate=rate, diff=diff, afk=afk, refs=list(refs),
                   params=params or {}, risk=risk, verify=verify))


# =============================== 1. 자연 스폰 몹 (14) ===============================
C = "mob"
F("general_mob_tower", "일반 몹 트랩(타워형)", "General Mob Farm", C, "mob_platform_tower",
  "어두운 플랫폼에서 적대 몹 자연 스폰 → 물길로 중앙 집결 → 23블록 낙하 즉사 → 호퍼 수거",
  rate="약 2,000~4,000 아이템/시간", diff=2, refs=("ilmango", "Rays Works"),
  params={"platform": 9, "layers": 4, "spacing": 4, "mob": "zombie", "drop": 24})
F("general_mob_xp", "일반 몹 경험치 트랩", "General Mob XP Farm", C, "mob_platform_tower",
  "동일 구조에서 낙하를 22블록으로 낮춰 1HP만 남김 → 플레이어 직접 타격으로 경험치 획득",
  rate="경험치 30레벨/수 분", diff=2, refs=("ilmango",),
  params={"platform": 9, "layers": 4, "mob": "zombie", "xp": True})
F("ocean_dark_mob", "바다 위 몹 트랩", "Ocean Mob Farm", C, "mob_platform_tower",
  "바다 한가운데는 경쟁 스폰 지면이 없어 몹캡을 독점 → 동일 원리로 효율이 지상 대비 수 배",
  rate="약 6,000~10,000 아이템/시간", diff=2, refs=("ilmango",),
  params={"platform": 15, "layers": 6, "mob": "zombie"})
F("creeper_gunpowder", "크리퍼(화약) 팜", "Creeper Farm", C, "mob_platform_tower",
  "높이 2칸 스폰층으로 키 큰 몹 스폰을 차단 → 크리퍼만 남김 → 고양이로 크리퍼 유인/기피 제어",
  rate="화약 약 500~1,500개/시간", diff=3, refs=("ilmango", "Rays Works"),
  params={"platform": 15, "layers": 4, "spacing": 3, "mob": "creeper"})
F("charged_creeper", "충전 크리퍼 팜", "Charged Creeper Farm", C, "composite",
  "번개가 칠 때 크리퍼에 명중시켜 충전 크리퍼 생성 → 몹 머리 획득용",
  rate="번개 의존, 매우 낮음", diff=5, refs=("Rays Works",),
  params={"chain": ["source", "trigger", "process", "collect"]},
  risk="번개 유도(피뢰침)와 크리퍼 위치 동기화가 까다로움", verify="at_risk")
F("skeleton_bone", "스켈레톤(뼈/화살) 팜", "Skeleton Farm", C, "mob_platform_tower",
  "스켈레톤 자연 스폰 → 낙하 처치. 뼛가루 원료 대량 확보 루트",
  rate="뼈 약 800~2,000개/시간", diff=2, refs=("ilmango",),
  params={"platform": 11, "layers": 5, "mob": "skeleton"})
F("spider_string", "거미(실) 팜", "Spider Farm", C, "spawner_box",
  "거미는 2x2 공간이 필요 → 스포너 기반이 훨씬 효율적. 1칸 통로로 밀어 넣어 분리",
  rate="실 약 400~900개/시간", diff=3, refs=("ilmango",),
  params={"mob": "spider", "xp": False, "drop": 24})
F("witch_farm_hut", "마녀 오두막 팜", "Witch Hut Farm", C, "mob_platform_tower",
  "늪지 마녀 오두막 구조물 경계 안에서만 마녀가 추가 스폰 → 그 구역만 스폰 가능하게 남기고 전부 차단",
  rate="레드스톤/설탕/유리병 다량", diff=4, refs=("ilmango", "Rays Works"),
  params={"platform": 9, "layers": 3, "mob": "witch", "drop": 30})
F("drowned_trident", "익사자(삼지창) 팜", "Drowned/Trident Farm", C, "mob_platform_tower",
  "강 바이옴 수중 스폰 활용. 자연 스폰 익사자만 삼지창을 들 수 있음(좀비 변환체는 불가)",
  rate="구리 다량, 삼지창 저확률", diff=4, refs=("ilmango", "Rays Works"),
  params={"platform": 13, "layers": 4, "mob": "drowned"},
  risk="구리 수요가 26.x에서 급증 → 우선순위 높은 팜")
F("guardian_farm", "가디언 팜", "Guardian Farm", C, "composite",
  "해저 신전 구조물 경계 안 물 블록에서 가디언이 스폰 → 신전 배수 후 스폰 구역만 남기고 물길로 집결",
  rate="프리즈마린/경험치 최상위", diff=5, refs=("ilmango", "Rays Works"),
  params={"chain": ["source", "transport", "process", "collect", "store"]})
F("slime_chunk", "슬라임 청크 팜", "Slime Farm", C, "mob_platform_tower",
  "슬라임 청크(Y40 이하)에서만 스폰 → 해당 청크 전 층을 파내 스폰 면적 극대화",
  rate="슬라임볼 약 300~800개/시간", diff=4, refs=("ilmango",),
  params={"platform": 16, "layers": 8, "spacing": 3, "mob": "slime_large", "drop": 24})
F("swamp_slime", "늪지 슬라임 팜", "Swamp Slime Farm", C, "mob_platform_tower",
  "늪지 Y50~70 밝기 조건에서 밤에 스폰 → 청크 탐색 없이 지을 수 있는 대안",
  rate="슬라임볼 중간", diff=3, refs=("ilmango",),
  params={"platform": 15, "layers": 3, "mob": "slime_large"})
F("phantom_membrane", "팬텀 팜", "Phantom Farm", C, "composite",
  "3일 이상 안 잔 플레이어 위 공중에서 스폰 → 지붕으로 유도해 낙하/직접 처치",
  rate="막 소량", diff=4, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect"]})
F("sulfur_cube_farm", "황 큐브 팜 (26.2 신규)", "Sulfur Cube Farm", C, "mob_platform_tower",
  "26.2 황 동굴 바이옴에서 스폰. 큰 큐브는 처치 시 작은 큐브 2개로 분열 → 분열 단계까지 처리 설계 필요",
  rate="미측정(신규)", diff=4, refs=("(26.2 신규 - 커뮤니티 설계 미성숙)",),
  params={"platform": 13, "layers": 3, "mob": "sulfur_cube_large"},
  risk="26.2 신규 몹. 스폰 조건/분열 처리 실측 필요", verify="at_risk")

# =============================== 2. 스포너 (8) ===============================
C = "spawner"
F("zombie_spawner", "좀비 스포너 팜", "Zombie Spawner Farm", C, "spawner_box",
  "던전 스포너가 4초마다 최대 4마리 강제 스폰 → 물길 → 낙하 22블록(1HP) → 직접 타격",
  rate="시간당 500~900마리", diff=1, refs=("Ianxofour", "wattles"),
  params={"mob": "zombie", "xp": True})
F("skeleton_spawner", "스켈레톤 스포너 팜", "Skeleton Spawner Farm", C, "spawner_box",
  "동일 원리. 뼈/화살 대량 + 초반 경험치원으로 최고 가성비",
  rate="시간당 500~900마리", diff=1, refs=("Ianxofour",), params={"mob": "skeleton", "xp": True})
F("cave_spider_spawner", "동굴 거미 스포너 팜", "Cave Spider Farm", C, "spawner_box",
  "폐광 동굴 거미는 체력 12로 낮아 낙하 처치가 쉬움. 실 + 경험치",
  rate="시간당 500~900마리", diff=2, refs=("Ianxofour",), params={"mob": "cave_spider", "xp": True})
F("silverfish_xp", "좀벌레 스포너 경험치 팜", "Silverfish XP Farm", C, "spawner_box",
  "요새 좀벌레 스포너. 체력 8로 매우 낮아 한 방 처치 → 초당 경험치 효율 최상",
  rate="경험치 최상위", diff=2, refs=("ilmango",), params={"mob": "silverfish", "xp": True, "drop": 8})
F("blaze_spawner", "블레이즈 스포너 팜", "Blaze Farm", C, "spawner_box",
  "네더 요새 스포너. 블레이즈는 낙하 면역 → 물 없이 발판 밀어내기 + 직접 타격/용암",
  dim="nether", rate="블레이즈 막대 시간당 수백", diff=3, refs=("ilmango", "Ianxofour"),
  params={"mob": "blaze", "xp": True, "drop": 0},
  risk="블레이즈는 낙하 데미지 면역 → 낙하 처치 설계 금지")
F("trial_chamber_farm", "시련의 방 팜", "Trial Chamber Farm", C, "spawner_box",
  "시련 스포너는 플레이어 수에 비례해 몹을 뿜고 쿨다운 후 보상 → 불길한 시련 열쇠 파밍",
  rate="시련 열쇠/불길한 열쇠", diff=4, refs=("ilmango",), params={"mob": "zombie", "xp": True},
  risk="1회성 보상 스포너와 시련 스포너 구분 필수")
F("magma_cube_spawner", "마그마 큐브 스포너 팜", "Magma Cube Farm", C, "spawner_box",
  "네더 요새/황무지. 분열하는 몹이라 크기별 처리 단계가 필요",
  dim="nether", rate="마그마 크림 중간", diff=3, refs=("ilmango",),
  params={"mob": "magma_cube_large", "xp": True})
F("dungeon_double", "이중 스포너 통합 팜", "Dual Spawner Farm", C, "spawner_box",
  "가까운 스포너 2개를 하나의 낙하 통로로 합쳐 처리량 2배",
  rate="단일 대비 약 2배", diff=3, refs=("Ianxofour",), params={"mob": "zombie", "xp": True})

# =============================== 3. 경작지/식물 (14) ===============================
C = "crop"
F("wheat_villager", "주민 밀 농장", "Villager Wheat Farm", C, "crop_piston_harvester",
  "농부 주민이 성숙 작물을 수확하고 재파종 → 인벤 초과분을 버리면 호퍼가 수거 (완전 무인)",
  rate="시간당 수백 개", diff=2, refs=("Rays Works", "ilmango"),
  params={"crop": "wheat", "width": 9, "length": 9})
F("carrot_villager", "주민 당근 농장", "Villager Carrot Farm", C, "crop_piston_harvester",
  "동일 원리. 당근은 주민 번식용 사료로도 직결",
  rate="시간당 수백 개", diff=2, refs=("Rays Works",),
  params={"crop": "carrot", "width": 9, "length": 9})
F("potato_villager", "주민 감자 농장", "Villager Potato Farm", C, "crop_piston_harvester",
  "동일 원리. 구운 감자는 식량 효율이 좋아 대량 제련과 궁합",
  rate="시간당 수백 개", diff=2, refs=("Rays Works",),
  params={"crop": "potato", "width": 9, "length": 9})
F("beetroot_farm", "비트 농장", "Beetroot Farm", C, "crop_piston_harvester",
  "주민이 비트는 수확하지 않으므로 피스톤 일괄 수확 방식으로 설계",
  rate="1회 수확 수십~수백", diff=2, refs=("ilmango",),
  params={"crop": "beetroot", "width": 9, "length": 9})
F("melon_farm", "수박 농장", "Melon Farm", C, "crop_piston_harvester",
  "줄기가 인접 칸에 열매 블록 생성 → 관측기가 생성을 감지해 피스톤으로 즉시 파괴",
  rate="시간당 1,000개 이상", diff=3, refs=("ilmango", "Shulkercraft"),
  params={"crop": "melon", "width": 12, "length": 6})
F("pumpkin_farm", "호박 농장", "Pumpkin Farm", C, "crop_piston_harvester",
  "수박과 동일 원리. 호박은 조각+제련(호박씨/등불) 라인과 연결",
  rate="시간당 1,000개 이상", diff=3, refs=("ilmango",),
  params={"crop": "pumpkin", "width": 12, "length": 6})
F("nether_wart", "네더 사마귀 농장", "Nether Wart Farm", C, "crop_piston_harvester",
  "영혼 모래 위에서만 성장. 물 필요 없음 → 피스톤 일괄 수확",
  dim="nether", rate="1회 수확 수백", diff=2, refs=("ilmango",),
  params={"crop": "nether_wart", "width": 9, "length": 9})
F("cocoa_farm", "코코아 농장", "Cocoa Bean Farm", C, "crop_piston_harvester",
  "정글 나무 옆면에 부착 성장 → 관측기+피스톤 수직 배열",
  rate="시간당 수백", diff=3, refs=("ilmango",),
  params={"crop": "cocoa", "width": 8, "length": 8})
F("sweet_berry", "달콤한 열매 농장", "Sweet Berry Farm", C, "composite",
  "열매 덤불은 성장 후 우클릭 수확 → 주민(농부)이 자동 수확하지 않으므로 발사기/플레이어 필요",
  rate="중간", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "collect", "store"]})
F("mushroom_farm", "버섯 농장", "Mushroom Farm", C, "composite",
  "버섯은 어두운 곳에서 주변으로 번짐 → 관측기로 번짐 감지 후 피스톤 수확",
  rate="중간", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect"]})
F("huge_mushroom", "거대 버섯 농장", "Huge Mushroom Farm", C, "composite",
  "뼛가루로 거대 버섯 성장 → 피스톤/TNT로 파괴해 버섯 블록 대량 수확",
  rate="블록 대량", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect"]})
F("moss_bonemeal", "이끼 확장 팜", "Moss Farm", C, "composite",
  "이끼 블록에 뼛가루 → 주변 블록을 이끼로 변환 → 피스톤 수확 후 반복 (무한 블록 생성)",
  rate="블록 대량", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect", "loop"]})
F("azalea_flower", "꽃/진달래 팜", "Flower Farm", C, "composite",
  "뼛가루를 잔디에 사용해 꽃 생성 → 바이옴별로 나오는 꽃 종류가 다름(염료 라인)",
  rate="염료 원료 다량", diff=2, refs=("ilmango",),
  params={"chain": ["source", "trigger", "collect"]})
F("wart_block_shroomlight", "빛나는 버섯/네더 이끼 팜", "Shroomlight Farm", C, "composite",
  "뼛가루를 네더 이끼에 사용해 거대 균사 성장 → 빛나는 버섯/버섯 줄기 수확",
  dim="nether", rate="블록 대량", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect"]})

# =============================== 4. 기둥 성장 (11) ===============================
C = "column"
F("sugarcane_farm", "사탕수수 농장", "Sugar Cane Farm", C, "column_crop",
  "물 옆 흙/모래에서 3칸까지 성장 → 2번째 칸 관측기가 성장 감지 → 피스톤 절단",
  rate="시간당 수백~수천", diff=2, refs=("ilmango", "Shulkercraft"),
  params={"crop": "sugar_cane", "rows": 4, "length": 16})
F("bamboo_farm", "대나무 농장", "Bamboo Farm", C, "column_crop",
  "대나무는 성장이 매우 빨라 연료/비계 무한 공급원. 관측기+피스톤 1세트로 충분",
  rate="시간당 수천", diff=1, refs=("ilmango",),
  params={"crop": "bamboo", "rows": 4, "length": 16})
F("bamboo_fuel_plant", "대나무 연료 발전 공장", "Bamboo Fuel Plant", C, "smelter_array",
  "대나무 → 비계 조합 → 화로 연료로 자동 공급. 연료 자급형 제련 공장",
  rate="화로 연속 가동", diff=3, refs=("ilmango",), params={"furnaces": 8})
F("cactus_farm", "선인장 농장", "Cactus Farm", C, "column_crop",
  "선인장은 옆칸에 블록이 있으면 자동 파괴 → 레드스톤 없이도 완전 자동 (초록 염료/제련)",
  rate="시간당 수백", diff=1, refs=("ilmango",),
  params={"crop": "cactus", "rows": 4, "length": 16})
F("cactus_xp", "선인장 경험치 공장", "Cactus XP Farm", C, "smelter_array",
  "선인장을 화로에 제련해 초록 염료 → 제련 경험치를 대량 축적 (AFK 경험치)",
  rate="경험치 지속", diff=3, refs=("ilmango",), params={"furnaces": 8})
F("kelp_farm", "다시마 농장", "Kelp Farm", C, "column_crop",
  "물속에서 위로 성장 → 관측기가 감지해 피스톤 절단 → 말린 켈프 블록(연료 4000틱)",
  rate="시간당 수백", diff=2, refs=("ilmango",),
  params={"crop": "kelp", "rows": 3, "length": 12})
F("chorus_farm", "감귤(코러스) 농장", "Chorus Fruit Farm", C, "column_crop",
  "엔드석 위에서 가지치며 성장 → 밑동을 부수면 전체가 붕괴 → 피스톤 1개로 전량 수확",
  dim="end", rate="시간당 수백", diff=2, refs=("ilmango",),
  params={"crop": "chorus", "rows": 3, "length": 8})
F("vine_farm", "덩굴 팜", "Vine Farm", C, "composite",
  "덩굴이 아래로 번짐 → 일정 길이마다 피스톤/물로 절단",
  rate="중간", diff=2, refs=("ilmango",), params={"chain": ["source", "process", "collect"]})
F("twisting_weeping_vine", "뒤틀린/우는 덩굴 팜", "Nether Vine Farm", C, "column_crop",
  "네더 덩굴은 위/아래로 자람 → 뼛가루 가속 가능, 관측기 절단",
  dim="nether", rate="중간", diff=2, refs=("ilmango",),
  params={"crop": "bamboo", "rows": 2, "length": 12})
F("sea_pickle", "바다 발광체 팜", "Sea Pickle Farm", C, "composite",
  "산호초 바이옴 물속에서 뼛가루로 증식 → 수동/반자동 수확",
  rate="낮음", diff=3, refs=("ilmango",), params={"chain": ["source", "trigger", "collect"]})
F("tree_farm_auto", "자동 나무 농장", "Auto Tree Farm", C, "composite",
  "묘목 자동 심기(발사기) → 뼛가루 성장 → TNT/피스톤 파괴 → 원목·묘목 수거 후 재파종 순환",
  rate="원목 시간당 수천", diff=5, refs=("ilmango", "Shulkercraft"),
  params={"chain": ["source", "trigger", "process", "collect", "loop"]})

# =============================== 5. 동물 (9) ===============================
C = "animal"
F("cow_farm", "소 농장(자동 조리)", "Cow Farm", C, "animal_farm",
  "번식 → 새끼만 1칸 구멍으로 분리 → 성장 시 용암/낙하 처치 → 소고기·가죽 수거",
  rate="시간당 수십~수백", diff=2, refs=("ilmango", "Shulkercraft"),
  params={"animal": "cow", "cook": True},
  risk="26.1 황금 민들레로 새끼 성장 제어 가능 → 성장 압사형 설계 재검토")
F("pig_farm", "돼지 농장", "Pig Farm", C, "animal_farm",
  "동일 원리. 당근으로 번식",
  rate="시간당 수십~수백", diff=2, refs=("ilmango",), params={"animal": "pig", "cook": True})
F("chicken_egg", "닭 알 팜(자동 부화)", "Chicken Farm", C, "composite",
  "닭이 낳은 알을 호퍼로 수거 → 발사기로 벽에 던져 부화 → 병아리 성장 시 용암 조리",
  rate="시간당 수백", diff=3, refs=("ilmango", "Shulkercraft"),
  params={"chain": ["source", "collect", "trigger", "process", "collect", "loop"]})
F("sheep_wool", "양털 팜", "Sheep Farm", C, "composite",
  "양이 잔디를 먹어 양털 회복 → 발사기의 가위로 자동 깎기 → 호퍼 수거",
  rate="시간당 수백", diff=2, refs=("ilmango",),
  params={"chain": ["source", "trigger", "collect", "loop"]})
F("rabbit_farm", "토끼 농장", "Rabbit Farm", C, "animal_farm",
  "동일 원리. 토끼 발/가죽 확보용",
  rate="낮음", diff=3, refs=("ilmango",), params={"animal": "rabbit", "cook": True})
F("honey_farm", "꿀 농장", "Honey Farm", C, "composite",
  "벌집이 꿀 레벨 5가 되면 비교기 신호 → 발사기가 유리병/가위 자동 사용 → 꿀/벌집 수거",
  rate="시간당 수십", diff=3, refs=("ilmango", "Shulkercraft"),
  params={"chain": ["source", "trigger", "collect", "loop"]})
F("fish_farm", "물고기 팜", "Fish Farm", C, "composite",
  "물고기를 좁은 수조에 가둬 번식/포획. 26.x에서는 낚시 자동화가 대부분 제한됨",
  rate="낮음", diff=4, refs=("ilmango",), params={"chain": ["source", "transport", "collect"]},
  risk="AFK 낚시는 다수 버전에서 반복 패치됨 → 재검증 필요", verify="at_risk")
F("squid_ink", "오징어(먹물) 팜", "Squid Farm", C, "composite",
  "수중 스폰 → 물길로 집결 → 낙하/직접 처치. 검은 염료 대량",
  rate="중간", diff=3, refs=("ilmango",), params={"chain": ["source", "transport", "process", "collect"]})
F("axolotl_bucket", "우파루파 번식소", "Axolotl Farm", C, "composite",
  "열대어 양동이 급여로 번식 → 희귀 색 파밍",
  rate="낮음", diff=3, refs=("ilmango",), params={"chain": ["source", "loop", "collect"]})

# =============================== 6. 마을/골렘/습격 (10) ===============================
C = "village"
F("iron_farm", "철 골렘 팜", "Iron Farm", C, "iron_golem_farm",
  "주민 3명이 좀비를 보고 공포 상태 → 철 골렘 스폰 → 용암 블레이드 처치 → 철괴 수거",
  rate="시간당 철괴 약 100~350", diff=3, refs=("Rays Works", "ilmango"),
  params={"pods": 3})
F("iron_farm_mega", "대형 철 공장(다중 유닛)", "Mega Iron Farm", C, "iron_golem_farm",
  "동일 유닛을 여러 개 쌓아 병렬화. 유닛 간 간섭(골렘 스폰 판정 범위) 분리가 핵심",
  rate="시간당 철괴 1,000+", diff=5, refs=("Rays Works",), params={"pods": 9})
F("villager_breeder", "주민 번식기", "Villager Breeder", C, "composite",
  "침대 여유 + 식량 충분 → 주민이 번식 → 새끼를 물길로 분리해 거래소로 운반",
  rate="시간당 수십 명", diff=3, refs=("Rays Works", "ilmango"),
  params={"chain": ["source", "transport", "store", "loop"]})
F("trading_hall", "주민 거래소", "Trading Hall", C, "villager_hall",
  "직업 블록 재설치로 거래 재추첨 → 원하는 거래 고정 → 에메랄드 경제 기반",
  rate="거래 의존", diff=3, refs=("Rays Works",), params={"stalls": 12},
  risk="26.1부터 거래가 데이터팩 기반 → 서버마다 목록 상이", verify="at_risk")
F("librarian_book", "사서 인챈트 책 공장", "Librarian Book Farm", C, "villager_hall",
  "사서 승급 전 서가대 재설치로 원하는 인챈트 책 추첨 → 수선/효율V 등 확보",
  rate="책 상시", diff=3, refs=("Rays Works",), params={"stalls": 8},
  risk="26.1: 마스터 사서의 이름표 거래 삭제 → 이름표는 방랑상인/조합으로")
F("emerald_farm", "에메랄드 자동 환전소", "Emerald Farm", C, "composite",
  "농장 산출물(당근/수박/호박/종이) → 호퍼로 주민에게 자동 공급 → 에메랄드 수거",
  rate="시간당 수백", diff=4, refs=("Rays Works",),
  params={"chain": ["source", "transport", "process", "collect"]})
F("raid_farm", "습격 팜", "Raid Farm", C, "composite",
  "불길한 징조를 가진 플레이어가 마을에 진입 → 습격대 스폰 → 물길 집결 → 처치. 에메랄드/불길한 물병",
  rate="에메랄드/총알 최상위", diff=5, refs=("Rays Works", "ilmango"),
  params={"chain": ["trigger", "source", "transport", "process", "collect"]},
  risk="습격 스폰 판정과 마을 경계 판정이 버전마다 자주 바뀜", verify="at_risk")
F("pillager_outpost", "약탈자 전초기지 팜", "Pillager Farm", C, "mob_platform_tower",
  "전초기지 구조물 경계 안에서 약탈자가 계속 스폰 → 그 구역만 남기고 스폰 차단",
  rate="화살/석궁/에메랄드", diff=4, refs=("ilmango",),
  params={"platform": 11, "layers": 3, "mob": "pillager", "drop": 30})
F("zombie_villager_cure", "주민 치료 할인 공장", "Zombie Villager Curing", C, "composite",
  "주민을 좀비화 → 황금 사과+나약함 물약으로 치료 → 거래 가격 대폭 할인 고정",
  rate="할인 영구", diff=3, refs=("Rays Works",),
  params={"chain": ["source", "process", "loop"]})
F("copper_golem_sorter", "구리 골렘 자동 분류소 (26.x)", "Copper Golem Sorter", C, "item_sorter",
  "구리 골렘이 구리 상자에서 최대 16스택 픽업 → 같은 아이템이 든 나무 상자에만 투입",
  rate="레드스톤 분류기보다 느림", diff=2, refs=("(1.21.9 신규)",),
  params={"channels": 10, "copper_golem": True},
  risk="산화되면 동작 저하 → 밀랍칠 필요. 고속 팜에는 부적합")

# =============================== 7. 네더 (11) ===============================
C = "nether"
F("gold_farm", "금 팜(좀비화 피글린)", "Gold Farm", C, "nether_platform",
  "네더 황무지 전 층을 플랫폼으로 덮어 몹캡 독점 → 좀비화 피글린 낙하 처치 → 금 조각/금괴",
  dim="nether", rate="시간당 금괴 수백~수천", diff=5, refs=("ilmango", "Rays Works"),
  params={"kind": "gold", "platform": 21, "drop": 24})
F("gold_farm_portal", "포탈형 금 팜", "Portal Gold Farm", C, "nether_platform",
  "오버월드에 네더 포탈을 두면 좀비화 피글린이 포탈로 스폰 → 네더 진입 없이 수거",
  rate="중간", diff=4, refs=("ilmango",), params={"kind": "gold", "platform": 9, "drop": 24})
F("wither_skeleton", "위더 스켈레톤 팜", "Wither Skeleton Farm", C, "nether_platform",
  "네더 요새 구조물 경계 안에서만 스폰 → 요새 스폰 구역을 플랫폼으로 덮고 나머지 차단",
  dim="nether", rate="해골 시간당 수십", diff=5, refs=("ilmango", "Rays Works"),
  params={"kind": "wither_skeleton", "platform": 15, "drop": 24})
F("piglin_bartering", "피글린 물물교환 공장", "Bartering Farm", C, "composite",
  "발사기가 금괴를 피글린에게 자동 투척 → 산출 아이템을 호퍼 미니카트로 수거 → 분류",
  dim="nether", rate="시간당 수천 아이템", diff=4, refs=("ilmango", "Rays Works"),
  params={"chain": ["source", "trigger", "collect", "store", "loop"]})
F("hoglin_farm", "호글린 팜", "Hoglin Farm", C, "nether_platform",
  "진홍빛 숲에서만 스폰 → 경작지/광원으로 스폰 차단 후 유도 → 낙하 처치(생 돼지고기·가죽)",
  dim="nether", rate="시간당 수백", diff=4, refs=("ilmango",),
  params={"kind": "hoglin", "platform": 15, "drop": 30})
F("ghast_farm", "가스트 팜", "Ghast Farm", C, "composite",
  "가스트는 4x4x5 공간이 필요 → 영혼 모래 골짜기의 넓은 공간에서만 스폰. 화약/가스트 눈물",
  dim="nether", rate="낮음", diff=5, refs=("ilmango",),
  params={"chain": ["source", "transport", "process", "collect"]},
  risk="가스트는 낙하 면역 → 처치는 직접/피스톤 압사")
F("magma_cream", "마그마 크림 팜", "Magma Cube Farm", C, "nether_platform",
  "네더 황무지/요새에서 스폰 → 분열 단계별로 낙하 통로를 나눠 처리",
  dim="nether", rate="중간", diff=4, refs=("ilmango",),
  params={"kind": "gold", "platform": 15, "drop": 24})
F("blaze_rod_plant", "블레이즈 막대 공장", "Blaze Rod Plant", C, "spawner_box",
  "블레이즈 막대 → 가루 → 물약 라인 원료. 스포너 기반이 유일하게 안정적",
  dim="nether", rate="시간당 수백", diff=3, refs=("Ianxofour",),
  params={"mob": "blaze", "xp": True, "drop": 0})
F("nether_quartz", "네더 석영 자동 채굴", "Quartz Farm", C, "composite",
  "TNT 복제/플라잉 머신으로 네더랙 층을 굴착 → 석영 광석을 수거",
  dim="nether", rate="시간당 수백", diff=5, refs=("ilmango",),
  params={"chain": ["trigger", "process", "collect", "loop"]},
  risk="TNT 복제는 버그성 메커니즘 → 서버/버전에 따라 차단될 수 있음", verify="at_risk")
F("soul_sand_wart", "영혼 모래 + 사마귀 통합 공장", "Soul Farm", C, "crop_piston_harvester",
  "영혼 모래 골짜기에서 영혼 모래 채집 → 네더 사마귀 농장 확장에 직결",
  dim="nether", rate="중간", diff=3, refs=("ilmango",),
  params={"crop": "nether_wart", "width": 12, "length": 12})
F("crimson_warped_wood", "진홍/뒤틀린 나무 공장", "Nether Wood Farm", C, "composite",
  "네더 균사 + 뼛가루 → 거대 균류 성장 → 피스톤/TNT 파괴 → 줄기 수확",
  dim="nether", rate="블록 대량", diff=4, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect", "loop"]})

# =============================== 8. 엔드 (6) ===============================
C = "end"
F("enderman_farm", "엔더맨 팜", "Enderman Farm", C, "enderman_platform",
  "본섬에서 128블록 이상 떨어진 허공 플랫폼 → 엔더맨만 스폰 → 낙하 후 직접 타격",
  dim="end", rate="진주/경험치 최상위", diff=4, refs=("ilmango", "Rays Works"),
  params={"drop": 40})
F("enderman_endermite", "엔더마이트 유인형 엔더맨 팜", "Endermite Enderman Farm", C, "enderman_platform",
  "엔더마이트를 광산 수레에 가둬 유인체로 사용 → 엔더맨이 자발적으로 낙하 지점으로 이동",
  dim="end", rate="진주 대량", diff=5, refs=("ilmango",), params={"drop": 40})
F("shulker_farm", "셜커 팜", "Shulker Farm", C, "composite",
  "셜커가 총알에 맞은 대상에 새 셜커를 생성하는 성질 이용 → 셜커 상자 무한 확보",
  dim="end", rate="셜커 껍질 지속", diff=5, refs=("ilmango", "Rays Works"),
  params={"chain": ["source", "loop", "process", "collect"]},
  risk="셜커 증식 조건이 버전마다 조정된 이력 있음", verify="at_risk")
F("chorus_end", "코러스 대량 농장", "Chorus Farm", C, "column_crop",
  "엔드석 위 코러스 → 밑동 파괴 시 전체 붕괴 → 피스톤 1개로 전량 수확 (보라 블록/순간이동 과일)",
  dim="end", rate="시간당 수백", diff=2, refs=("ilmango",),
  params={"crop": "chorus", "rows": 4, "length": 10})
F("dragon_xp", "엔더 드래곤 자동 처치", "Dragon Farm", C, "composite",
  "드래곤 재소환 → 침대/TNT 폭발로 자동 처치 → 경험치·드래곤 숨결 수거",
  dim="end", rate="경험치 대량/1회", diff=5, refs=("ilmango",),
  params={"chain": ["trigger", "process", "collect", "loop"]})
F("end_city_looter", "엔드 시티 자동 약탈 루트", "End City Route", C, "composite",
  "얼음 보트 하이웨이로 엔드 시티 간 이동 자동화 → 셜커 상자/엘리트라 회수 루트",
  dim="end", rate="탐험 효율", diff=4, refs=("ilmango",),
  params={"chain": ["transport", "collect", "store"]})

# =============================== 9. 자원/블록 생성 (9) ===============================
C = "resource"
F("cobblestone_gen", "조약돌 생성기", "Cobblestone Generator", C, "composite",
  "물+용암 접촉으로 조약돌 생성 → 피스톤이 밀어 파괴 → 무한 블록",
  rate="시간당 수천", diff=2, refs=("ilmango",),
  params={"chain": ["source", "process", "collect", "loop"]})
F("stone_gen", "돌 생성기", "Stone Generator", C, "composite",
  "용암 위로 물이 흐르면 돌 생성 → 실크터치/피스톤 수확",
  rate="시간당 수천", diff=2, refs=("ilmango",),
  params={"chain": ["source", "process", "collect", "loop"]})
F("basalt_gen", "현무암 생성기", "Basalt Generator", C, "composite",
  "용암이 청빙 위 영혼 모래에 닿으면 현무암 생성 → 피스톤 수확",
  rate="시간당 수천", diff=3, refs=("ilmango",),
  params={"chain": ["source", "process", "collect", "loop"]})
F("obsidian_gen", "흑요석 생성기", "Obsidian Generator", C, "composite",
  "용암 수원에 물 → 흑요석 → 자동 채굴(TNT/실크터치 불가로 대개 반자동)",
  rate="중간", diff=4, refs=("ilmango",),
  params={"chain": ["source", "process", "collect", "loop"]})
F("ice_farm", "얼음 팜", "Ice Farm", C, "composite",
  "눈 바이옴 수원이 얼음으로 변함 → 실크터치 발사기/플레이어가 채집 → 재결빙 반복",
  rate="시간당 수백", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "collect", "loop"]})
F("snow_farm", "눈 팜", "Snow Farm", C, "composite",
  "눈 골렘이 이동하며 눈층 생성 → 삽 발사기/피스톤으로 수확 → 눈덩이 대량",
  rate="시간당 수천", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "collect", "loop"]})
F("amethyst_farm", "자수정 팜", "Amethyst Farm", C, "composite",
  "자수정 정동에서 싹이 4단계로 성장 → 완전 성장 시 피스톤이 밀어 파괴 → 자수정 조각",
  rate="시간당 수백", diff=3, refs=("ilmango",),
  params={"chain": ["source", "trigger", "process", "collect", "loop"]})
F("gravel_flint", "자갈/부싯돌 팜", "Gravel Farm", C, "composite",
  "TNT 폭파 또는 중력 블록 낙하 반복으로 자갈 대량 확보 → 부싯돌 변환",
  rate="중간", diff=4, refs=("ilmango",),
  params={"chain": ["source", "process", "collect", "loop"]})
F("copper_oxidation", "구리 산화 공정 라인 (26.x)", "Copper Processing", C, "composite",
  "구리 블록 산화 단계를 도끼/밀랍으로 제어 → 26.x 구리 수요(골렘/구리 상자) 대응 자동 라인",
  rate="공정 라인", diff=3, refs=("(1.21.9+ 신규 수요)",),
  params={"chain": ["source", "process", "store"]})

# =============================== 10. 인프라/공정 (8) ===============================
C = "infra"
F("item_sorter_classic", "호퍼 아이템 분류기", "Item Sorter", C, "item_sorter",
  "비교기가 분류 호퍼의 필터 아이템 신호를 읽음 → 일치할 때만 호퍼 잠금 해제 → 지정 상자로",
  rate="채널당 초당 2.5개", diff=3, refs=("ilmango", "Mumbo Jumbo"),
  params={"channels": 12})
F("bulk_storage", "대용량 저장 시스템", "Bulk Storage", C, "item_sorter",
  "분류기 + 다중 상자 배열 + 오버플로 라인 → 팜 산출물 전량을 무인 저장",
  rate="저장 용량", diff=4, refs=("ilmango",), params={"channels": 24})
F("super_smelter", "대량 제련로", "Super Smelter", C, "smelter_array",
  "호퍼 3방향(위=원료/옆=연료/아래=산출) 병렬 화로 → 화로 1대당 시간당 360개",
  rate="화로 수 x 360개/시간", diff=3, refs=("ilmango", "Shulkercraft"),
  params={"furnaces": 16})
F("auto_crafter", "자동 조합기 라인", "Auto Crafter", C, "composite",
  "1.21 제작기(Crafter) + 비교기 → 산출물을 자동으로 상위 아이템으로 가공(블록화/도구화)",
  rate="라인 속도", diff=3, refs=("ilmango", "Mumbo Jumbo"),
  params={"chain": ["source", "process", "collect", "store"]})
F("brewing_plant", "자동 양조 공장", "Brewing Plant", C, "composite",
  "호퍼로 재료·유리병 자동 투입 → 양조대 3슬롯 산출을 아래 호퍼로 회수 → 다단 물약 라인",
  rate="물약 라인", diff=4, refs=("ilmango",),
  params={"chain": ["source", "process", "collect", "store"]})
F("shulker_loader", "셜커 상자 자동 적재기", "Shulker Loader", C, "composite",
  "산출물을 셜커 상자에 자동 적재 → 가득 차면 배출하고 빈 상자 재장전 (무한 저장 확장)",
  rate="상자 단위", diff=5, refs=("ilmango",),
  params={"chain": ["source", "process", "store", "loop"]})
F("xp_bank", "경험치 은행", "XP Bank", C, "composite",
  "몹/제련 경험치를 병에 담아 저장하거나, 경험치 오브를 보관해 필요 시 일괄 수령",
  rate="경험치 저장", diff=4, refs=("ilmango",),
  params={"chain": ["source", "store", "trigger"]})
F("forceload_hub", "강제 로딩 허브 (1.21.9+ 필수)", "Forceload Hub", C, "composite",
  "1.21.9에서 스폰 청크가 삭제됨 → /forceload 로 청크를 고정하거나 AFK 지점을 설계에 포함시켜야 함",
  rate="인프라", diff=2, refs=("(1.21.9 변경 대응)",),
  params={"chain": ["trigger", "loop"]},
  risk="OP 권한이 없는 서버에서는 /forceload 불가 → AFK 설계 필수")

FARMS = _R
