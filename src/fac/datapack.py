"""Write a Minecraft 26.2 datapack from a FactoryDesign."""

from __future__ import annotations

import json
from pathlib import Path

from fac.catalog import BIOMES, DIMENSIONS, FLOOR_Y, MODULES, PALETTES, STRUCTURES
from fac.designer import FactoryDesign, PlacedModule

PACK_FORMAT = [107, 1]


def export_datapack(design: FactoryDesign, dest: Path) -> Path:
    root = dest / "fac"
    data = root / "data"
    _wipe(root)
    (root / "pack.mcmeta").write_text(
        json.dumps(
            {
                "pack": {
                    "description": "Fac AI Factory World — dimensions, biomes, mobs, structures",
                    "min_format": PACK_FORMAT,
                    "max_format": PACK_FORMAT,
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _biomes(data)
    _dimensions(data)
    _world_preset(data)
    _functions(data, design)
    _tags(data)
    return root


def _wipe(root: Path) -> None:
    if root.exists():
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        root.rmdir()
    root.mkdir(parents=True)


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj if obj.endswith("\n") else obj + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def _biomes(data: Path) -> None:
    for biome in BIOMES.values():
        payload = {
            "temperature": biome.temperature,
            "downfall": biome.downfall,
            "has_precipitation": biome.precipitation,
            "effects": {
                "sky_color": biome.sky_color,
                "fog_color": biome.fog_color,
                "water_color": biome.water_color,
                "water_fog_color": biome.water_color,
                "grass_color": biome.grass_color,
                "foliage_color": biome.foliage_color,
            },
            "spawners": {
                "monster": [_spawner(*m) for m in biome.monster_mobs],
                "creature": [_spawner(*m) for m in biome.creature_mobs],
                "ambient": [_spawner(*m) for m in biome.ambient_mobs],
                "axolotls": [],
                "underground_water_creature": [],
                "water_creature": [],
                "water_ambient": [],
                "misc": [],
            },
            "spawn_costs": {},
            "carvers": [],
            "features": [[], [], [], [], [], [], [], [], [], [], []],
        }
        rel = biome.id.split(":")[1]
        _write(data / "fac" / "worldgen" / "biome" / f"{rel}.json", payload)


def _spawner(entity: str, weight: int, mn: int, mx: int) -> dict:
    return {"type": entity, "weight": weight, "minCount": mn, "maxCount": mx}


def _flat_generator(dim_id: str, biome_id: str) -> dict:
    spec = DIMENSIONS[dim_id]
    return {
        "type": "minecraft:flat",
        "settings": {
            "biome": biome_id,
            "layers": [
                {"block": block, "height": height} for block, height in spec.floor_layers
            ],
            "structure_overrides": [],
        },
    }


def _dim_payload(dim_id: str) -> dict:
    spec = DIMENSIONS[dim_id]
    return {
        "type": spec.vanilla_type,
        "generator": _flat_generator(dim_id, spec.biome),
    }


def _dimensions(data: Path) -> None:
    for spec in DIMENSIONS.values():
        rel = spec.id.split(":")[1]
        _write(data / "fac" / "dimension" / f"{rel}.json", _dim_payload(spec.id))


def _world_preset(data: Path) -> None:
    # New worlds can pick "Fac Factory" from the world-type list.
    preset = {
        "dimensions": {
            "minecraft:overworld": _dim_payload("fac:campus"),
            "minecraft:the_nether": _dim_payload("fac:nether_works"),
            "minecraft:the_end": _dim_payload("fac:end_works"),
            "fac:campus": _dim_payload("fac:campus"),
            "fac:nether_works": _dim_payload("fac:nether_works"),
            "fac:end_works": _dim_payload("fac:end_works"),
            "fac:void_stack": _dim_payload("fac:void_stack"),
        }
    }
    _write(data / "fac" / "worldgen" / "world_preset" / "factory.json", preset)
    _write(
        data / "minecraft" / "tags" / "worldgen" / "world_preset" / "normal.json",
        {"replace": False, "values": ["fac:factory"]},
    )
    _write(
        data / "minecraft" / "tags" / "worldgen" / "world_preset" / "extended.json",
        {"replace": False, "values": ["fac:factory"]},
    )


def _tags(data: Path) -> None:
    _write(
        data / "minecraft" / "tags" / "function" / "load.json",
        {"values": ["fac:load"]},
    )
    _write(
        data / "minecraft" / "tags" / "function" / "tick.json",
        {"values": ["fac:tick"]},
    )
    _write(
        data / "fac" / "tags" / "entity_type" / "factory_mobs.json",
        {
            "values": [
                "minecraft:villager",
                "minecraft:iron_golem",
                "minecraft:allay",
                "minecraft:piglin",
                "minecraft:hoglin",
                "minecraft:enderman",
                "minecraft:shulker",
                "minecraft:creeper",
                "minecraft:skeleton",
                "minecraft:spider",
            ]
        },
    )


def _functions(data: Path, design: FactoryDesign) -> None:
    fn = data / "fac" / "function"
    _write(fn / "load.mcfunction", _load_fn(design))
    _write(fn / "tick.mcfunction", _tick_fn())
    _write(fn / "validate.mcfunction", _validate_fn())
    _write(fn / "setup.mcfunction", _setup_fn(design))
    _write(fn / "clear.mcfunction", _clear_fn(design))
    for placed in design.modules:
        _write(fn / "build" / f"{placed.uid}.mcfunction", _build_module(placed))
    # Per-dimension builders keep command count under the 65k cap.
    for dim, mods in design.modules_by_dim().items():
        short = dim.split(":")[1]
        lines = [f"function fac:build/{m.uid}" for m in mods]
        _write(fn / "build" / f"dim_{short}.mcfunction", "\n".join(lines) + "\n")


def _load_fn(design: FactoryDesign) -> str:
    n = len(design.modules)
    return "\n".join(
        [
            "gamerule commandBlockOutput false",
            "gamerule logAdminCommands false",
            "gamerule announceAdvancements false",
            "gamerule keepInventory true",
            "gamerule doImmediateRespawn true",
            "gamerule sendCommandFeedback true",
            "difficulty easy",
            "scoreboard objectives add fac_ok dummy",
            "scoreboard objectives add fac_tick dummy",
            "scoreboard objectives add fac_built dummy",
            "scoreboard players set $modules fac_ok " + str(n),
            'tellraw @a [{"text":"[Fac] ","color":"aqua"},{"text":"공장 월드 로드됨. 크리에이티브에서 /function fac:setup 으로 모듈을 짓고 /function fac:validate 로 차원을 점검하세요.","color":"white"}]',
            "",
        ]
    )


def _tick_fn() -> str:
    return "\n".join(
        [
            "scoreboard players add $clock fac_tick 1",
            "execute if score $clock fac_tick matches 20.. run scoreboard players set $clock fac_tick 0",
            "",
        ]
    )


def _validate_fn() -> str:
    return "\n".join(
        [
            "scoreboard players set $campus fac_ok 0",
            "scoreboard players set $nether fac_ok 0",
            "scoreboard players set $end fac_ok 0",
            "scoreboard players set $void fac_ok 0",
            "execute in fac:campus run scoreboard players set $campus fac_ok 1",
            "execute in fac:nether_works run scoreboard players set $nether fac_ok 1",
            "execute in fac:end_works run scoreboard players set $end fac_ok 1",
            "execute in fac:void_stack run scoreboard players set $void fac_ok 1",
            "scoreboard players set $ok fac_ok 1",
            "execute unless score $campus fac_ok matches 1 run scoreboard players set $ok fac_ok 0",
            "execute unless score $nether fac_ok matches 1 run scoreboard players set $ok fac_ok 0",
            "execute unless score $end fac_ok matches 1 run scoreboard players set $ok fac_ok 0",
            "execute unless score $void fac_ok matches 1 run scoreboard players set $ok fac_ok 0",
            'tellraw @a [{"text":"[Fac] validate  campus="},{"score":{"name":"$campus","objective":"fac_ok"}},{"text":" nether="},{"score":{"name":"$nether","objective":"fac_ok"}},{"text":" end="},{"score":{"name":"$end","objective":"fac_ok"}},{"text":" void="},{"score":{"name":"$void","objective":"fac_ok"}},{"text":" ok="},{"score":{"name":"$ok","objective":"fac_ok"}}]',
            "",
        ]
    )


def _setup_fn(design: FactoryDesign) -> str:
    lines = [
        "scoreboard players set $built fac_built 0",
        "execute in fac:campus run forceload add 0 0 256 256",
        "execute in fac:nether_works run forceload add 0 0 256 256",
        "execute in fac:end_works run forceload add 0 0 256 256",
        "execute in fac:void_stack run forceload add 0 0 256 256",
    ]
    for dim in DIMENSIONS:
        short = dim.split(":")[1]
        lines.append(f"function fac:build/dim_{short}")
    lines.append("scoreboard players set $built fac_built 1")
    lines.append(
        'tellraw @a [{"text":"[Fac] ","color":"aqua"},{"text":"setup complete","color":"white"}]'
    )
    lines.append("")
    return "\n".join(lines)


def _clear_fn(design: FactoryDesign) -> str:
    lines = []
    for placed in design.modules:
        w, h, d = placed.spec.footprint
        lines.append(
            f"execute in {placed.dimension} run fill {placed.x} {placed.y} {placed.z} "
            f"{placed.x + w} {placed.y + h} {placed.z + d} minecraft:air"
        )
    lines.append("scoreboard players set $built fac_built 0")
    lines.append("")
    return "\n".join(lines)


def _build_module(placed: PlacedModule) -> str:
    spec = placed.spec
    pal = PALETTES[spec.palette]
    x, y, z = placed.x, placed.y, placed.z
    w, h, d = spec.footprint
    x2, y2, z2 = x + w - 1, y + h - 1, z + d - 1
    cx, cz = x + w // 2, z + d // 2
    floor_y = max(y, FLOOR_Y)
    lines = [
        f"# {spec.name} ({placed.uid}) {placed.dimension}",
        f"execute in {placed.dimension} run fill {x} {y} {z} {x2} {y} {z2} {pal['floor']}",
        f"execute in {placed.dimension} run fill {x} {y + 1} {z} {x2} {y2} {z2} {pal['glass']} hollow",
        f"execute in {placed.dimension} run fill {x} {y} {z} {x} {y2} {z} {pal['frame']}",
        f"execute in {placed.dimension} run fill {x2} {y} {z} {x2} {y2} {z} {pal['frame']}",
        f"execute in {placed.dimension} run fill {x} {y} {z2} {x} {y2} {z2} {pal['frame']}",
        f"execute in {placed.dimension} run fill {x2} {y} {z2} {x2} {y2} {z2} {pal['frame']}",
        f"execute in {placed.dimension} run fill {x} {y2} {z} {x2} {y2} {z2} {pal['frame']}",
        f"execute in {placed.dimension} run setblock {cx} {y2} {cz} {pal['light']}",
        f"execute in {placed.dimension} run setblock {cx} {floor_y + 1} {cz} minecraft:barrel[facing=up]",
        f"execute in {placed.dimension} run setblock {cx + 1} {floor_y + 1} {cz} minecraft:hopper[facing=west]",
    ]
    struct = STRUCTURES.get(spec.structure, {})
    accent = struct.get("block", pal["accent"])
    lines.append(
        f"execute in {placed.dimension} run fill {cx - 1} {floor_y + 1} {cz - 1} "
        f"{cx + 1} {floor_y + 2} {cz + 1} {accent} replace minecraft:air"
    )
    # Restore working barrel after accent fill.
    lines.append(
        f"execute in {placed.dimension} run setblock {cx} {floor_y + 1} {cz} minecraft:barrel[facing=up]"
    )
    name = spec.name.replace('"', "")
    lines.append(
        f'execute in {placed.dimension} run summon minecraft:armor_stand {cx} {floor_y + 3} {cz} '
        f'{{Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,'
        f'CustomName:{{text:"{name}",color:"aqua"}}}}'
    )
    for mob in spec.mobs + spec.workers:
        from fac.catalog import MOBS

        role = MOBS.get(mob)
        if not role:
            continue
        lines.append(
            f'execute in {placed.dimension} run summon {role.entity} {cx} {floor_y + 2} {cz + 2} '
            f'{{PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{{text:"{role.name}",color:"yellow"}},'
            f'Invulnerable:1b,NoAI:1b}}'
        )
    if spec.id == "portal_hub":
        lines.extend(_portals(placed, cx, floor_y, cz))
    if spec.id == "chunk_anchor":
        lines.append(
            f"execute in {placed.dimension} run forceload add {x} {z} {x2} {z2}"
        )
        lines.append(
            f"execute in {placed.dimension} run setblock {cx} {floor_y + 1} {cz} minecraft:lodestone"
        )
    lines.append("")
    return "\n".join(lines)


def _portals(placed: PlacedModule, cx: int, y: int, cz: int) -> list[str]:
    dim = placed.dimension
    lines = []
    if dim == "fac:campus":
        # Nether portal frame (4x5) facing west-east
        lines.append(
            f"execute in {dim} run fill {cx - 2} {y + 1} {cz - 4} {cx + 1} {y + 5} {cz - 4} minecraft:obsidian"
        )
        lines.append(
            f"execute in {dim} run fill {cx - 1} {y + 2} {cz - 4} {cx} {y + 4} {cz - 4} minecraft:air"
        )
        # End portal-looking gateway marker (end gateway is entity; use end_portal_frame ring)
        lines.append(
            f"execute in {dim} run fill {cx - 2} {y + 1} {cz + 4} {cx + 2} {y + 1} {cz + 4} minecraft:end_portal_frame[facing=south]"
        )
    if dim == "fac:nether_works":
        lines.append(
            f"execute in {dim} run fill {cx - 2} {y + 1} {cz} {cx + 1} {y + 5} {cz} minecraft:obsidian"
        )
        lines.append(
            f"execute in {dim} run fill {cx - 1} {y + 2} {cz} {cx} {y + 4} {cz} minecraft:air"
        )
    if dim == "fac:end_works":
        lines.append(
            f"execute in {dim} run fill {cx - 1} {y + 1} {cz - 1} {cx + 1} {y + 1} {cz + 1} minecraft:end_portal_frame"
        )
    if dim == "fac:void_stack":
        lines.append(
            f"execute in {dim} run fill {cx - 2} {y + 1} {cz} {cx + 1} {y + 5} {cz} minecraft:crying_obsidian"
        )
        lines.append(
            f"execute in {dim} run fill {cx - 1} {y + 2} {cz} {cx} {y + 4} {cz} minecraft:air"
        )
    return lines
