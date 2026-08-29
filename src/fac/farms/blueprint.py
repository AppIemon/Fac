"""Turn a farm's working principle + mechanics into a concrete build plan.

The knowledge base stores *how a farm works*; this module converts that into
an actionable blueprint: an ordered build checklist derived from the tagged
mechanics, a bill of materials estimated from the footprint, and a coarse
block/entity placement list a previewer (e.g. the Paper plugin) can build.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fac.farms.schema import Farm

# Each mechanic tag maps to a build instruction. Knowing the principle
# (the set of mechanics) is enough to emit a real, ordered plan.
MECHANIC_STEPS: dict[str, str] = {
    "spawning_dark": "Enclose the spawn area and keep light level 0 (no torches; use trapdoors/carpets for spawn-proofing elsewhere).",
    "spawning_platform": "Build flat spawn platforms sized to the mob (usually 3x3+); leave the block above open.",
    "spawning_night": "Leave open sky above; the farm only produces at night / under the right condition.",
    "biome_specific": "Locate/relocate the farm to the required biome; spawns depend on it.",
    "structure_required_spawner": "Center the build on the natural mob spawner; do not break it.",
    "structure_required_monument": "Build inside the ocean monument's spawn volume; drain with sponges as needed.",
    "structure_required_hut": "Build around the swamp witch hut so its bounding-box spawns dominate.",
    "structure_required_trial": "Build around the trial spawner(s); they can't be moved and have a 30-min cooldown.",
    "structure_required_end_city": "Use a captured End-city shulker as the breeder seed.",
    "mob_cap_control": "Spawn-proof all caves within 128 blocks so the hostile cap isn't wasted.",
    "spawn_proofing": "Light or slab every surface except the intended spawn platform.",
    "trapdoor_spawnproof": "Use trapdoors to make the spawn floor valid but escape-proof.",
    "mob_filter_cat": "Place cats on the platform so non-target mobs despawn/flee.",
    "aggro_lure": "Stand at the AFK spot so target mobs aggro and path into the funnel.",
    "water_stream": "Cut flowing-water channels that push mobs to the central collection point.",
    "flowing_water": "Use flowing water (source + 7 blocks) to sweep drops toward hoppers.",
    "water_elevator": "Use a soul-sand (up) / magma (down) bubble column to move mobs vertically.",
    "fall_damage": "Set the drop height so mobs land at ~1 HP (23+ blocks) for a 1-hit kill / auto-kill.",
    "lava_blade": "Place a lava blade (with signs/carpets) that kills adults but spares drops.",
    "campfire_kill": "Kill mobs over a campfire so drops survive and no extra smelting is needed.",
    "fire_kill": "Kill animals with fire/lava/campfire so meat comes out cooked.",
    "lava_kill": "Drop mobs onto lava for a hands-free kill above the collection hopper.",
    "suffocation": "Use pistons/gravity blocks to suffocate mobs for hands-free kills.",
    "manual_kill": "Provide a safe player kill slot (1-tall gap / sweep spot) for XP + looting.",
    "hopper_collection": "Run hoppers under the kill/collection area into a chest/barrel.",
    "hopper_minecart": "Put a hopper-minecart under the farmland/floor to pick up items off solid blocks.",
    "afk_platform": "Add an AFK platform 20-24 blocks from spawns (inside the 24-block no-despawn / activation sweet spot).",
    "portal_spawn": "Use nether portal blocks to generate zombified piglins.",
    "nether_roof": "Build on the nether roof (y=128) or a very large spawn plane.",
    "bartering": "Feed piglins gold ingots via a dropper/dispenser and catch barter drops below.",
    "breeding": "Auto-feed the breeding pair and separate babies from adults.",
    "auto_breed": "Dispense food on a clock to keep the breeder pair in love mode.",
    "growth_tick": "Give crops light>=9 and space; growth is random-tick driven.",
    "observer_harvest": "Put an observer facing the mature block to trigger the piston exactly when ready.",
    "piston_harvest": "Use a piston to break the mature block into a water/hopper channel.",
    "flying_machine": "Build a slime/honey + observer flying machine to sweep tall/wide crops or trees.",
    "bonemeal": "Dispense bone meal to force growth; feed from a composter bone-meal engine.",
    "composter": "Feed plant matter into composters (hopper in, hopper out) to make bone meal.",
    "lava_water_generation": "Set the exact lava+water geometry so the target block forms in one slot.",
    "basalt_generation": "Set lava + soul soil with blue ice adjacent to form basalt.",
    "water_harden": "Drop concrete powder into water to harden, then auto-mine.",
    "dripstone_growth": "Water source above a pointed dripstone on a dripstone block; wait for growth.",
    "dripstone_drip": "Lava/water above a pointed dripstone drips into a cauldron below.",
    "mud_to_clay": "Place mud above a pointed dripstone with air below the tip to convert to clay.",
    "cluster_growth": "Wait for amethyst clusters to fully grow on budding amethyst, then harvest.",
    "freeze_cycle": "In a cold biome with light<=11 and open sky, let water freeze, then harvest ice.",
    "snow_golem_trail": "Trap a snow golem in a cold biome; harvest the snow-layer trail.",
    "frog_eat_magma": "Feed small magma cubes to frogs of the right variant to produce froglights.",
    "sculk_catalyst": "Kill mobs on/near a sculk catalyst to convert XP into sculk.",
    "shulker_reproduction": "Aim a shulker bullet at a second shulker to spawn offspring; kill only offspring.",
    "raid": "Trigger raids with Bad Omen (ominous bottle) over a bell/village arena.",
    "village_mechanics": "Give villagers claimed beds and workstations; keep them enclosed.",
    "villager_panic": "Expose villagers to a safe zombie so they panic and summon golems.",
    "villager_farming": "Give a farmer villager a composter, farmland, seeds, and light>=9.",
    "wave_clear": "Clear each trial-spawner wave to trigger loot ejection.",
    "loot_eject": "Collect the ejected loot; open vaults with trial keys.",
    "cooldown_cycle": "Cycle multiple trial spawners due to the 30-min cooldown.",
    "ominous": "Drink an ominous bottle before triggering for ominous keys / heavy core.",
    "furnace_array": "Split items+fuel across many furnaces via hoppers; merge outputs.",
    "smoker_array": "Use smokers (2x food speed) fed and drained by hoppers.",
    "fuel_loop": "Loop part of the fuel output back so the smelter self-sustains.",
    "crafter": "Pulse a Crafter (1.21) with redstone; use a comparator so it fires only when full.",
    "comparator_filter": "Bias filter hoppers with the target item + 4 filler items (comparator read).",
    "comparator_full": "Read the container/crafter with a comparator to fire only when full.",
    "item_filter": "Divert each item type into its own storage lane.",
    "overflow_protection": "Loop overflow back to input so one full lane doesn't jam the line.",
    "redstone_clock": "Add a redstone clock to pulse dispensers/pistons at the right interval.",
    "dispenser_feed": "Use a dispenser to place/throw the input item on a clock.",
    "dispenser_shear": "Use a dispenser with shears to auto-harvest wool/honeycomb.",
    "mob_cap_fill": "Keep persistent mobs loaded far away to fill the target spawn cap.",
    "portal_transfer": "Link portals precisely so dropped items cross dimensions to the receiver.",
    "self_break": "No harvester needed: the plant breaks itself when it grows (cactus/bamboo tip).",
    "tnt_dupe": "(Technical) uses TNT/gravity-block duplication; confirm it's allowed on your world.",
}

# Default palette used to render a preview shell for any farm.
PREVIEW_PALETTE = {
    "floor": "minecraft:smooth_stone",
    "wall": "minecraft:glass",
    "frame": "minecraft:stone_bricks",
    "light": "minecraft:sea_lantern",
    "collect": "minecraft:hopper",
    "store": "minecraft:chest",
    "afk": "minecraft:cobblestone",
}


@dataclass
class Blueprint:
    farm_id: str
    name: str
    dimension: str
    size: dict
    steps: list[str]
    materials: dict[str, int]
    requirements: dict
    placements: list[dict] = field(default_factory=list)
    entities: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "farm_id": self.farm_id,
            "name": self.name,
            "dimension": self.dimension,
            "size": self.size,
            "requirements": self.requirements,
            "steps": self.steps,
            "materials": self.materials,
            "placements": self.placements,
            "entities": self.entities,
        }


def build_steps(farm: Farm) -> list[str]:
    steps: list[str] = []
    # Preamble from requirements.
    if farm.dimension != "any":
        steps.append(f"Go to the {farm.dimension}.")
    if farm.biomes:
        steps.append("Build in one of these biomes: " + ", ".join(farm.biomes) + ".")
    if farm.y_level and farm.y_level != "any":
        steps.append(f"Build at Y: {farm.y_level}.")
    # Ordered mechanic steps (stable order = the order tags were listed).
    for m in farm.mechanics:
        steps.append(MECHANIC_STEPS.get(m, f"Apply mechanic: {m}."))
    # Collection tail.
    if "hopper_collection" not in farm.mechanics and "hopper_minecart" not in farm.mechanics:
        steps.append("Add hoppers into a chest under the output point.")
    for c in farm.caveats:
        steps.append(f"Caveat: {c}")
    return steps


def estimate_materials(farm: Farm) -> dict[str, int]:
    w, h, d = farm.footprint.w, farm.footprint.h, farm.footprint.d
    floor = w * d
    roof = w * d
    walls = 2 * (w + d) * h
    mats: dict[str, int] = {
        PREVIEW_PALETTE["floor"]: floor,
        PREVIEW_PALETTE["wall"]: walls,
        PREVIEW_PALETTE["frame"]: 4 * h,
        PREVIEW_PALETTE["light"]: max(1, floor // 64),
    }
    # Add the farm's own key blocks with a rough count.
    for b in farm.blocks:
        mats[b] = mats.get(b, 0) + max(4, (w + d))
    mats[PREVIEW_PALETTE["store"]] = 2
    return mats


def make_blueprint(farm: Farm) -> Blueprint:
    w, h, d = farm.footprint.w, farm.footprint.h, farm.footprint.d
    placements: list[dict] = []
    # Floor slab.
    for x in range(w):
        for z in range(d):
            placements.append({"x": x, "y": 0, "z": z, "block": PREVIEW_PALETTE["floor"]})
    # Glass shell (perimeter walls).
    for y in range(1, h):
        for x in range(w):
            for z in range(d):
                if x in (0, w - 1) or z in (0, d - 1):
                    placements.append({"x": x, "y": y, "z": z, "block": PREVIEW_PALETTE["wall"]})
    # Corner frames.
    for (cx, cz) in [(0, 0), (w - 1, 0), (0, d - 1), (w - 1, d - 1)]:
        for y in range(h):
            placements.append({"x": cx, "y": y, "z": cz, "block": PREVIEW_PALETTE["frame"]})
    # Central light + collection column.
    cx, cz = w // 2, d // 2
    placements.append({"x": cx, "y": h - 1, "z": cz, "block": PREVIEW_PALETTE["light"]})
    placements.append({"x": cx, "y": 1, "z": cz, "block": PREVIEW_PALETTE["collect"]})
    placements.append({"x": cx, "y": 1, "z": cz, "block": PREVIEW_PALETTE["store"]})
    # Mob markers (one per role at the center).
    entities = [{"x": cx, "y": 1, "z": cz + 1, "type": m} for m in farm.mobs]

    return Blueprint(
        farm_id=farm.id,
        name=farm.name,
        dimension=farm.dimension,
        size={"w": w, "h": h, "d": d},
        steps=build_steps(farm),
        materials=estimate_materials(farm),
        requirements={
            "biomes": farm.biomes,
            "y_level": farm.y_level,
            "light": farm.light,
            "mobs": farm.mobs,
            "items_in": farm.items_in,
            "redstone": farm.redstone,
            "afk": farm.afk,
            "version": farm.version,
            "status": farm.status,
        },
        placements=placements,
        entities=entities,
    )
