"""World catalog: dimensions, biomes, mobs, structures, factory modules.

Rates are items per hour for one module, based on well-known Java farm
designs (Creative/OP layout, spawn-proofed, chunk-loaded). The designer
stacks modules until production goals are met; the simulator treats these
as continuous rates.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DimensionSpec:
    id: str
    name: str
    name_ko: str
    vanilla_type: str
    sky: str
    floor_layers: tuple[tuple[str, int], ...]
    biome: str
    color: str
    description: str


@dataclass(frozen=True)
class BiomeSpec:
    id: str
    name: str
    temperature: float
    downfall: float
    precipitation: bool
    water_color: int
    sky_color: int
    fog_color: int
    grass_color: int
    foliage_color: int
    ambient_mobs: tuple[tuple[str, int, int, int], ...] = ()
    monster_mobs: tuple[tuple[str, int, int, int], ...] = ()
    creature_mobs: tuple[tuple[str, int, int, int], ...] = ()


@dataclass(frozen=True)
class MobRole:
    id: str
    name: str
    name_ko: str
    entity: str
    role: str
    dimension: str
    biome: str
    notes: str


@dataclass(frozen=True)
class ModuleSpec:
    id: str
    name: str
    name_ko: str
    dimension: str
    biome: str
    structure: str
    footprint: tuple[int, int, int]
    palette: str
    outputs: dict[str, float]
    inputs: dict[str, float] = field(default_factory=dict)
    mobs: tuple[str, ...] = ()
    workers: tuple[str, ...] = ()
    description: str = ""


DIMENSIONS: dict[str, DimensionSpec] = {
    "fac:campus": DimensionSpec(
        id="fac:campus",
        name="Campus",
        name_ko="캠퍼스",
        vanilla_type="minecraft:overworld",
        sky="overworld",
        floor_layers=(
            ("minecraft:bedrock", 1),
            ("minecraft:stone", 3),
            ("minecraft:smooth_stone", 1),
            ("minecraft:gray_concrete", 1),
        ),
        biome="fac:steel_plains",
        color="#5b8def",
        description="HQ, storage, crops, iron, wood, auto-craft.",
    ),
    "fac:nether_works": DimensionSpec(
        id="fac:nether_works",
        name="Nether Works",
        name_ko="네더 공방",
        vanilla_type="minecraft:the_nether",
        sky="nether",
        floor_layers=(
            ("minecraft:bedrock", 1),
            ("minecraft:blackstone", 3),
            ("minecraft:polished_blackstone", 1),
            ("minecraft:red_nether_bricks", 1),
        ),
        biome="fac:crimson_foundry",
        color="#e23d3d",
        description="Gold barter, quartz, debris, hoglin meat.",
    ),
    "fac:end_works": DimensionSpec(
        id="fac:end_works",
        name="End Works",
        name_ko="엔드 공방",
        vanilla_type="minecraft:the_end",
        sky="end",
        floor_layers=(
            ("minecraft:bedrock", 1),
            ("minecraft:end_stone", 4),
            ("minecraft:purpur_block", 1),
        ),
        biome="fac:end_garden",
        color="#c9b3ff",
        description="Chorus, pearls, shulkers, elytra dock.",
    ),
    "fac:void_stack": DimensionSpec(
        id="fac:void_stack",
        name="Void Stack",
        name_ko="보이드 스택",
        vanilla_type="minecraft:overworld",
        sky="overworld",
        floor_layers=(
            ("minecraft:bedrock", 1),
            ("minecraft:obsidian", 2),
            ("minecraft:black_concrete", 1),
        ),
        biome="fac:dark_chamber",
        color="#2ee6a6",
        description="Stacked hostile farms in a light-zero void.",
    ),
}

BIOMES: dict[str, BiomeSpec] = {
    "fac:steel_plains": BiomeSpec(
        id="fac:steel_plains",
        name="Steel Plains",
        temperature=0.7,
        downfall=0.2,
        precipitation=False,
        water_color=0x3D5A80,
        sky_color=0x1B2838,
        fog_color=0x1B2838,
        grass_color=0x4A5A4A,
        foliage_color=0x3E4E3E,
        creature_mobs=(("minecraft:villager", 8, 2, 4), ("minecraft:iron_golem", 4, 1, 1)),
        ambient_mobs=(("minecraft:bat", 2, 1, 1),),
    ),
    "fac:crop_grid": BiomeSpec(
        id="fac:crop_grid",
        name="Crop Grid",
        temperature=0.9,
        downfall=0.6,
        precipitation=True,
        water_color=0x3AA0C8,
        sky_color=0x78C8FF,
        fog_color=0xC0D8E8,
        grass_color=0x7CB342,
        foliage_color=0x558B2F,
        creature_mobs=(
            ("minecraft:villager", 20, 4, 8),
            ("minecraft:cow", 8, 2, 4),
            ("minecraft:chicken", 8, 2, 4),
            ("minecraft:sheep", 6, 2, 4),
        ),
    ),
    "fac:crimson_foundry": BiomeSpec(
        id="fac:crimson_foundry",
        name="Crimson Foundry",
        temperature=2.0,
        downfall=0.0,
        precipitation=False,
        water_color=0x905957,
        sky_color=0x330808,
        fog_color=0x330808,
        grass_color=0x7A2A2A,
        foliage_color=0x9B3030,
        monster_mobs=(("minecraft:piglin", 40, 4, 8), ("minecraft:hoglin", 12, 2, 4)),
        creature_mobs=(("minecraft:strider", 4, 1, 2),),
    ),
    "fac:end_garden": BiomeSpec(
        id="fac:end_garden",
        name="End Garden",
        temperature=0.5,
        downfall=0.0,
        precipitation=False,
        water_color=0x62529E,
        sky_color=0x000000,
        fog_color=0xA080A0,
        grass_color=0x8E82B8,
        foliage_color=0xC9B3FF,
        monster_mobs=(("minecraft:enderman", 40, 1, 4), ("minecraft:shulker", 4, 1, 1)),
    ),
    "fac:dark_chamber": BiomeSpec(
        id="fac:dark_chamber",
        name="Dark Chamber",
        temperature=0.2,
        downfall=0.0,
        precipitation=False,
        water_color=0x101018,
        sky_color=0x000000,
        fog_color=0x000000,
        grass_color=0x1A1A1A,
        foliage_color=0x1A1A1A,
        monster_mobs=(
            ("minecraft:creeper", 80, 1, 4),
            ("minecraft:skeleton", 80, 1, 4),
            ("minecraft:spider", 40, 1, 3),
            ("minecraft:witch", 8, 1, 1),
        ),
    ),
    "fac:warehouse_void": BiomeSpec(
        id="fac:warehouse_void",
        name="Warehouse Void",
        temperature=0.5,
        downfall=0.0,
        precipitation=False,
        water_color=0x2A2A32,
        sky_color=0x111118,
        fog_color=0x111118,
        grass_color=0x3A3A40,
        foliage_color=0x3A3A40,
    ),
}

MOBS: dict[str, MobRole] = {
    "foreman": MobRole(
        "foreman", "Foreman", "현장감독", "minecraft:villager",
        "ops", "fac:campus", "fac:steel_plains",
        "Named villager at HQ. Creative/OP stand-in for workstation routing.",
    ),
    "guard": MobRole(
        "guard", "Guard Golem", "경비 골렘", "minecraft:iron_golem",
        "security", "fac:campus", "fac:steel_plains",
        "Patrols campus plots; player-made golem so it never attacks operators.",
    ),
    "hauler": MobRole(
        "hauler", "Hauler Allay", "운반 알레이", "minecraft:allay",
        "logistics", "fac:campus", "fac:warehouse_void",
        "Item mover between module barrels and the silo.",
    ),
    "farmer": MobRole(
        "farmer", "Crop Farmer", "농부", "minecraft:villager",
        "production", "fac:campus", "fac:crop_grid",
        "Composter villagers for crop towers.",
    ),
    "barterer": MobRole(
        "barterer", "Barterer", "물물교환 피글린", "minecraft:piglin",
        "production", "fac:nether_works", "fac:crimson_foundry",
        "Gold farm / barter hall operator. Zombified piglins for portal gold.",
    ),
    "hoglin_stock": MobRole(
        "hoglin_stock", "Hoglin Stock", "호글린 축산", "minecraft:hoglin",
        "production", "fac:nether_works", "fac:crimson_foundry",
        "Nether meat line.",
    ),
    "pearl_hunter": MobRole(
        "pearl_hunter", "Pearl Hunter", "진주 엔더맨", "minecraft:enderman",
        "production", "fac:end_works", "fac:end_garden",
        "Enderman farm stock.",
    ),
    "shell_keeper": MobRole(
        "shell_keeper", "Shell Keeper", "셜커", "minecraft:shulker",
        "production", "fac:end_works", "fac:end_garden",
        "Shulker clone farm seed.",
    ),
    "creeper_stock": MobRole(
        "creeper_stock", "Creeper Stock", "크리퍼", "minecraft:creeper",
        "production", "fac:void_stack", "fac:dark_chamber",
        "Gunpowder stack.",
    ),
    "skeleton_stock": MobRole(
        "skeleton_stock", "Skeleton Stock", "스켈레톤", "minecraft:skeleton",
        "production", "fac:void_stack", "fac:dark_chamber",
        "Bone / arrow stack.",
    ),
    "spider_stock": MobRole(
        "spider_stock", "Spider Stock", "거미", "minecraft:spider",
        "production", "fac:void_stack", "fac:dark_chamber",
        "String stack.",
    ),
}

STRUCTURES: dict[str, dict] = {
    "hq_tower": {"name": "HQ Tower", "w": 20, "h": 24, "d": 20, "block": "minecraft:iron_block"},
    "silo": {"name": "Storage Silo", "w": 24, "h": 32, "d": 24, "block": "minecraft:barrel"},
    "iron_cell": {"name": "Iron Cell", "w": 22, "h": 16, "d": 22, "block": "minecraft:iron_block"},
    "crop_tower": {"name": "Crop Tower", "w": 18, "h": 28, "d": 18, "block": "minecraft:farmland"},
    "tree_hall": {"name": "Tree Hall", "w": 20, "h": 20, "d": 28, "block": "minecraft:oak_log"},
    "smelter": {"name": "Super Smelter", "w": 16, "h": 12, "d": 24, "block": "minecraft:blast_furnace"},
    "crafter_bay": {"name": "Crafter Bay", "w": 16, "h": 10, "d": 16, "block": "minecraft:crafter"},
    "gold_hall": {"name": "Gold Hall", "w": 28, "h": 24, "d": 28, "block": "minecraft:gold_block"},
    "quartz_pit": {"name": "Quartz Pit", "w": 16, "h": 16, "d": 16, "block": "minecraft:nether_quartz_ore"},
    "debris_line": {"name": "Debris Line", "w": 16, "h": 10, "d": 20, "block": "minecraft:ancient_debris"},
    "chorus_grid": {"name": "Chorus Grid", "w": 24, "h": 22, "d": 24, "block": "minecraft:chorus_flower"},
    "pearl_drop": {"name": "Pearl Drop", "w": 20, "h": 40, "d": 20, "block": "minecraft:end_stone_bricks"},
    "shulker_bay": {"name": "Shulker Bay", "w": 16, "h": 12, "d": 16, "block": "minecraft:shulker_box"},
    "elytra_dock": {"name": "Elytra Dock", "w": 14, "h": 10, "d": 18, "block": "minecraft:purpur_pillar"},
    "creeper_stack": {"name": "Creeper Stack", "w": 20, "h": 48, "d": 20, "block": "minecraft:moss_block"},
    "skeleton_stack": {"name": "Skeleton Stack", "w": 20, "h": 48, "d": 20, "block": "minecraft:bone_block"},
    "spider_stack": {"name": "Spider Stack", "w": 18, "h": 36, "d": 18, "block": "minecraft:cobweb"},
    "cobble_gen": {"name": "Cobble Gen", "w": 12, "h": 8, "d": 12, "block": "minecraft:cobblestone"},
    "portal_hub": {"name": "Portal Hub", "w": 16, "h": 12, "d": 16, "block": "minecraft:obsidian"},
    "chunk_anchor": {"name": "Chunk Anchor", "w": 8, "h": 8, "d": 8, "block": "minecraft:respawn_anchor"},
}

PALETTES: dict[str, dict[str, str]] = {
    "campus": {
        "floor": "minecraft:gray_concrete",
        "frame": "minecraft:iron_block",
        "glass": "minecraft:light_gray_stained_glass",
        "light": "minecraft:sea_lantern",
        "accent": "minecraft:copper_block",
    },
    "nether": {
        "floor": "minecraft:red_nether_bricks",
        "frame": "minecraft:gold_block",
        "glass": "minecraft:orange_stained_glass",
        "light": "minecraft:shroomlight",
        "accent": "minecraft:gilded_blackstone",
    },
    "end": {
        "floor": "minecraft:purpur_block",
        "frame": "minecraft:end_stone_bricks",
        "glass": "minecraft:purple_stained_glass",
        "light": "minecraft:end_rod",
        "accent": "minecraft:purpur_pillar",
    },
    "void": {
        "floor": "minecraft:black_concrete",
        "frame": "minecraft:crying_obsidian",
        "glass": "minecraft:black_stained_glass",
        "light": "minecraft:sculk_sensor",
        "accent": "minecraft:obsidian",
    },
}

MODULES: dict[str, ModuleSpec] = {
    "hq": ModuleSpec(
        id="hq", name="HQ", name_ko="본부",
        dimension="fac:campus", biome="fac:steel_plains", structure="hq_tower",
        footprint=(20, 24, 20), palette="campus",
        outputs={}, mobs=("foreman", "guard"),
        description="Command tower, scoreboards, operator spawn.",
    ),
    "silo": ModuleSpec(
        id="silo", name="Silo", name_ko="사일로",
        dimension="fac:campus", biome="fac:warehouse_void", structure="silo",
        footprint=(24, 32, 24), palette="campus",
        outputs={}, workers=("hauler",),
        description="Central item buffer. Capacity is modeled, not vanilla chests.",
    ),
    "iron_foundry": ModuleSpec(
        id="iron_foundry", name="Iron Foundry", name_ko="철 주조소",
        dimension="fac:campus", biome="fac:steel_plains", structure="iron_cell",
        footprint=(22, 16, 22), palette="campus",
        outputs={"iron_ingot": 400.0, "poppy": 40.0},
        mobs=("guard",),
        description="Village-based iron golem cell. ~400 ingots/h per cell.",
    ),
    "crop_tower": ModuleSpec(
        id="crop_tower", name="Crop Tower", name_ko="작물 타워",
        dimension="fac:campus", biome="fac:crop_grid", structure="crop_tower",
        footprint=(18, 28, 18), palette="campus",
        outputs={"wheat": 4000.0, "bread": 1300.0},
        mobs=("farmer",),
        description="Villager crop tower with composter loop.",
    ),
    "tree_hall": ModuleSpec(
        id="tree_hall", name="Tree Hall", name_ko="나무 홀",
        dimension="fac:campus", biome="fac:crop_grid", structure="tree_hall",
        footprint=(20, 20, 28), palette="campus",
        outputs={"oak_log": 2500.0, "oak_sapling": 200.0, "stick": 400.0},
        description="Bone-meal tree farm hall.",
    ),
    "cow_cooker": ModuleSpec(
        id="cow_cooker", name="Cow Cooker", name_ko="소 조리장",
        dimension="fac:campus", biome="fac:crop_grid", structure="crop_tower",
        footprint=(16, 12, 16), palette="campus",
        outputs={"cooked_beef": 900.0, "leather": 900.0},
        inputs={"wheat": 200.0},
        description="Cooked beef / leather crammer.",
    ),
    "smelter": ModuleSpec(
        id="smelter", name="Super Smelter", name_ko="슈퍼 제련소",
        dimension="fac:campus", biome="fac:steel_plains", structure="smelter",
        footprint=(16, 12, 24), palette="campus",
        outputs={"glass": 2400.0, "smooth_stone": 2400.0},
        inputs={"cobblestone": 2400.0, "oak_log": 300.0},
        description="Blast-furnace array. Fuel from tree hall.",
    ),
    "crafter_bay": ModuleSpec(
        id="crafter_bay", name="Crafter Bay", name_ko="제작 베이",
        dimension="fac:campus", biome="fac:steel_plains", structure="crafter_bay",
        footprint=(16, 10, 16), palette="campus",
        outputs={"chest": 200.0, "hopper": 150.0, "item_frame": 200.0},
        inputs={"oak_log": 800.0, "iron_ingot": 400.0},
        description="1.21+ crafter array for logistics parts.",
    ),
    "cobble_gen": ModuleSpec(
        id="cobble_gen", name="Cobble Gen", name_ko="조약돌 생성기",
        dimension="fac:campus", biome="fac:steel_plains", structure="cobble_gen",
        footprint=(12, 8, 12), palette="campus",
        outputs={"cobblestone": 36000.0},
        description="Lava/water cobble generator, mined by hoppers+tnt or packed ice drills (OP).",
    ),
    "gold_hall": ModuleSpec(
        id="gold_hall", name="Gold Hall", name_ko="금 홀",
        dimension="fac:nether_works", biome="fac:crimson_foundry", structure="gold_hall",
        footprint=(28, 24, 28), palette="nether",
        outputs={"gold_ingot": 6000.0, "gold_nugget": 2000.0, "ender_pearl": 80.0, "obsidian": 40.0},
        mobs=("barterer",),
        description="Portal-based gold + piglin barter mix.",
    ),
    "quartz_pit": ModuleSpec(
        id="quartz_pit", name="Quartz Pit", name_ko="석영 피트",
        dimension="fac:nether_works", biome="fac:crimson_foundry", structure="quartz_pit",
        footprint=(16, 16, 16), palette="nether",
        outputs={"quartz": 3000.0},
        description="Nether quartz vein strip on a foundry floor.",
    ),
    "hoglin_line": ModuleSpec(
        id="hoglin_line", name="Hoglin Line", name_ko="호글린 라인",
        dimension="fac:nether_works", biome="fac:crimson_foundry", structure="gold_hall",
        footprint=(18, 12, 18), palette="nether",
        outputs={"cooked_porkchop": 1200.0, "leather": 400.0},
        mobs=("hoglin_stock",),
        description="Hoglin cooker.",
    ),
    "debris_line": ModuleSpec(
        id="debris_line", name="Debris Line", name_ko="잔해 라인",
        dimension="fac:nether_works", biome="fac:crimson_foundry", structure="debris_line",
        footprint=(16, 10, 20), palette="nether",
        outputs={"netherite_scrap": 12.0},
        inputs={"gold_ingot": 12.0},
        description="Ancient debris smelt + smithing prep. Low rate, high value.",
    ),
    "chorus_grid": ModuleSpec(
        id="chorus_grid", name="Chorus Grid", name_ko="후렴과 그리드",
        dimension="fac:end_works", biome="fac:end_garden", structure="chorus_grid",
        footprint=(24, 22, 24), palette="end",
        outputs={"chorus_fruit": 2500.0, "popped_chorus_fruit": 2000.0},
        description="Chorus flower grid.",
    ),
    "pearl_drop": ModuleSpec(
        id="pearl_drop", name="Pearl Drop", name_ko="진주 드롭",
        dimension="fac:end_works", biome="fac:end_garden", structure="pearl_drop",
        footprint=(20, 40, 20), palette="end",
        outputs={"ender_pearl": 1800.0},
        mobs=("pearl_hunter",),
        description="Enderman drop tower.",
    ),
    "shulker_bay": ModuleSpec(
        id="shulker_bay", name="Shulker Bay", name_ko="셜커 베이",
        dimension="fac:end_works", biome="fac:end_garden", structure="shulker_bay",
        footprint=(16, 12, 16), palette="end",
        outputs={"shulker_shell": 80.0},
        mobs=("shell_keeper",),
        description="Shulker duplication bay.",
    ),
    "elytra_dock": ModuleSpec(
        id="elytra_dock", name="Elytra Dock", name_ko="겉날개 도크",
        dimension="fac:end_works", biome="fac:end_garden", structure="elytra_dock",
        footprint=(14, 10, 18), palette="end",
        outputs={"elytra": 2.0, "dragon_breath": 8.0},
        description="Ship dock / end city gateway plaza.",
    ),
    "creeper_stack": ModuleSpec(
        id="creeper_stack", name="Creeper Stack", name_ko="크리퍼 스택",
        dimension="fac:void_stack", biome="fac:dark_chamber", structure="creeper_stack",
        footprint=(20, 48, 20), palette="void",
        outputs={"gunpowder": 2800.0},
        mobs=("creeper_stock",),
        description="Cat-filtered creeper only stack.",
    ),
    "skeleton_stack": ModuleSpec(
        id="skeleton_stack", name="Skeleton Stack", name_ko="스켈레톤 스택",
        dimension="fac:void_stack", biome="fac:dark_chamber", structure="skeleton_stack",
        footprint=(20, 48, 20), palette="void",
        outputs={"bone": 3500.0, "arrow": 3500.0, "bone_meal": 3500.0},
        mobs=("skeleton_stock",),
        description="Skeleton-only dark stack.",
    ),
    "spider_stack": ModuleSpec(
        id="spider_stack", name="Spider Stack", name_ko="거미 스택",
        dimension="fac:void_stack", biome="fac:dark_chamber", structure="spider_stack",
        footprint=(18, 36, 18), palette="void",
        outputs={"string": 2200.0, "spider_eye": 400.0},
        mobs=("spider_stock",),
        description="Spider stack for string / wool / bows.",
    ),
    "portal_hub": ModuleSpec(
        id="portal_hub", name="Portal Hub", name_ko="포탈 허브",
        dimension="fac:campus", biome="fac:steel_plains", structure="portal_hub",
        footprint=(16, 12, 16), palette="campus",
        outputs={},
        description="Nether/end/void portal room. One per dimension.",
    ),
    "chunk_anchor": ModuleSpec(
        id="chunk_anchor", name="Chunk Anchor", name_ko="청크 앵커",
        dimension="fac:campus", biome="fac:steel_plains", structure="chunk_anchor",
        footprint=(8, 8, 8), palette="campus",
        outputs={},
        description="forceload / nether portal chunk loader marker.",
    ),
}

# Items/hour the factory must sustain after warmup.
DEFAULT_GOALS: dict[str, float] = {
    "iron_ingot": 1600.0,
    "gold_ingot": 6000.0,
    "gunpowder": 2800.0,
    "bone": 3500.0,
    "string": 2200.0,
    "ender_pearl": 1800.0,
    "oak_log": 2500.0,
    "wheat": 4000.0,
    "cobblestone": 36000.0,
    "cooked_beef": 900.0,
    "glass": 2400.0,
    "chorus_fruit": 2500.0,
    "shulker_shell": 80.0,
    "quartz": 3000.0,
}

# How many items the silo can hold per item type before overflow fails a test.
SILO_CAPACITY = 1_000_000.0

# Hopper-equivalent logistics between a module and the silo, items/hour.
BASE_BELT_RATE = 18_000.0  # 2 hopper lines × 2.5 i/s × 3600
BELT_UPGRADE = 18_000.0

GRID_PITCH = 32  # blocks between plot origins
FLOOR_Y = 64
