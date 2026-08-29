package com.fac;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.GameRule;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Registry;
import org.bukkit.World;
import org.bukkit.WorldCreator;
import org.bukkit.WorldType;
import org.bukkit.block.Biome;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Entity;
import org.bukkit.entity.EntityType;
import org.bukkit.entity.LivingEntity;
import org.bukkit.event.entity.CreatureSpawnEvent;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.logging.Logger;

/**
 * Turns a {@link Design} into blocks, biomes, and mobs inside real Paper
 * flat worlds — one flat world per factory dimension. Runs on the main
 * server thread (called from the /fac command).
 */
public final class WorldBuilder {

    /** Y level of the built factory floor slab. Modules sit on top at BASE_Y. */
    public static final int FLOOR_Y = 63;
    public static final int BASE_Y = 64;
    private static final int MARGIN = 4;

    private final Design design;
    private final Logger log;

    public WorldBuilder(Design design, Logger log) {
        this.design = design;
        this.log = log;
    }

    public static final class Stats {
        public final Map<String, Integer> modulesPerDim = new LinkedHashMap<>();
        public final Map<String, String> worldPerDim = new LinkedHashMap<>();
        public int worlds = 0;
        public int modules = 0;
        public long blocks = 0;
        public int mobs = 0;
        public int mobFailures = 0;
        public long biomeCells = 0;
    }

    /** Maps a factory dimension id ("fac:campus") to its Paper world name. */
    public static String worldName(String dimId) {
        return "fac_" + dimId.substring(dimId.indexOf(':') + 1);
    }

    public World getOrCreateWorld(String dimId) {
        JsonObject dim = design.dimensions().getAsJsonObject(dimId);
        String name = worldName(dimId);
        World existing = org.bukkit.Bukkit.getWorld(name);
        if (existing != null) {
            return existing;
        }
        String vanillaType = str(dim, "vanilla_type", "minecraft:overworld");
        World.Environment env = environmentFor(vanillaType);
        String topBiome = topBiomeKey(dimId);
        WorldCreator wc = new WorldCreator(name)
                .type(WorldType.FLAT)
                .environment(env)
                .generateStructures(false)
                .generatorSettings(flatSettings(dim, topBiome))
                .seed(0L);
        World world = wc.createWorld();
        if (world == null) {
            throw new IllegalStateException("createWorld returned null for " + name);
        }
        world.setGameRule(GameRule.DO_DAYLIGHT_CYCLE, false);
        world.setGameRule(GameRule.DO_WEATHER_CYCLE, false);
        world.setGameRule(GameRule.DO_MOB_SPAWNING, false);
        world.setGameRule(GameRule.DO_FIRE_TICK, false);
        world.setGameRule(GameRule.MOB_GRIEFING, false);
        world.setGameRule(GameRule.DO_TRADER_SPAWNING, false);
        // The Nether/End have no world clock; setTime throws there.
        try {
            world.setTime(6000L);
        } catch (RuntimeException ignored) {
            // no daylight clock in this environment
        }
        try {
            world.setStorm(false);
            world.setThundering(false);
        } catch (RuntimeException ignored) {
            // Some environments (end) do not support weather.
        }
        return world;
    }

    /** Builds every module for one dimension. Returns per-dimension counts. */
    public Stats buildDimension(String dimId, Stats stats) {
        World world = getOrCreateWorld(dimId);
        stats.worlds++;
        stats.worldPerDim.put(dimId, world.getName());

        JsonArray modules = design.modules();
        // Bounding box of this dimension's modules, for the floor slab + biome.
        int minX = Integer.MAX_VALUE, minZ = Integer.MAX_VALUE;
        int maxX = Integer.MIN_VALUE, maxZ = Integer.MIN_VALUE;
        int count = 0;
        for (int i = 0; i < modules.size(); i++) {
            JsonObject m = modules.get(i).getAsJsonObject();
            if (!dimId.equals(str(m, "dimension", ""))) {
                continue;
            }
            count++;
            int x = m.get("x").getAsInt();
            int z = m.get("z").getAsInt();
            int w = m.get("w").getAsInt();
            int d = m.get("d").getAsInt();
            minX = Math.min(minX, x - MARGIN);
            minZ = Math.min(minZ, z - MARGIN);
            maxX = Math.max(maxX, x + w + MARGIN);
            maxZ = Math.max(maxZ, z + d + MARGIN);
        }
        stats.modulesPerDim.put(dimId, count);
        if (count == 0) {
            return stats;
        }

        String palName = dimPalette(dimId);
        JsonObject pal = design.palettes().getAsJsonObject(palName);
        Material floorMat = mat(str(pal, "floor", "minecraft:gray_concrete"));
        Biome biome = biomeFor(topBiomeKey(dimId));

        // Factory floor slab across the whole used plane. Laying the slab
        // loads every chunk in the build area (via setType).
        for (int x = minX; x <= maxX; x++) {
            for (int z = minZ; z <= maxZ; z++) {
                set(world, x, FLOOR_Y, z, floorMat, stats);
                if (biome != null && ((x & 3) == 0) && ((z & 3) == 0)) {
                    world.setBiome(x, BASE_Y, z, biome);
                    stats.biomeCells++;
                }
            }
        }

        // Idempotent: clear factory entities from a previous /fac setup in this
        // area so re-running rebuilds cleanly instead of stacking mobs/labels.
        for (Entity e : world.getEntities()) {
            if (e instanceof org.bukkit.entity.Player) {
                continue;
            }
            int ex = e.getLocation().getBlockX();
            int ez = e.getLocation().getBlockZ();
            if (ex >= minX && ex <= maxX && ez >= minZ && ez <= maxZ) {
                e.remove();
            }
        }

        // Build each module.
        for (int i = 0; i < modules.size(); i++) {
            JsonObject m = modules.get(i).getAsJsonObject();
            if (!dimId.equals(str(m, "dimension", ""))) {
                continue;
            }
            buildModule(world, m, stats);
            stats.modules++;
        }
        return stats;
    }

    private void buildModule(World world, JsonObject m, Stats stats) {
        String palName = str(m, "palette", dimPalette(str(m, "dimension", "fac:campus")));
        JsonObject pal = design.palettes().getAsJsonObject(palName);
        Material floor = mat(str(pal, "floor", "minecraft:gray_concrete"));
        Material frame = mat(str(pal, "frame", "minecraft:iron_block"));
        Material glass = mat(str(pal, "glass", "minecraft:light_gray_stained_glass"));
        Material light = mat(str(pal, "light", "minecraft:sea_lantern"));

        int x = m.get("x").getAsInt();
        int z = m.get("z").getAsInt();
        int w = m.get("w").getAsInt();
        int h = m.get("h").getAsInt();
        int d = m.get("d").getAsInt();
        int y = BASE_Y;
        int x2 = x + w - 1, y2 = y + h - 1, z2 = z + d - 1;
        int cx = x + w / 2, cz = z + d / 2;

        // Floor.
        fill(world, x, y, z, x2, y, z2, floor, stats);
        // Glass shell (walls + roof), hollow.
        hollow(world, x, y + 1, z, x2, y2, z2, glass, stats);
        // Frame the four vertical corner columns.
        fill(world, x, y, z, x, y2, z, frame, stats);
        fill(world, x2, y, z, x2, y2, z, frame, stats);
        fill(world, x, y, z2, x, y2, z2, frame, stats);
        fill(world, x2, y, z2, x2, y2, z2, frame, stats);
        // Roof rim frame.
        fill(world, x, y2, z, x2, y2, z, frame, stats);
        fill(world, x, y2, z2, x2, y2, z2, frame, stats);
        fill(world, x, y2, z, x, y2, z2, frame, stats);
        fill(world, x2, y2, z, x2, y2, z2, frame, stats);
        // Ceiling light + working barrel/hopper.
        set(world, cx, y2, cz, light, stats);
        set(world, cx, y + 1, cz, mat("minecraft:barrel"), stats);
        set(world, cx + 1, y + 1, cz, mat("minecraft:hopper"), stats);

        // Structure accent cluster identifies the module type at a glance.
        String structId = str(m, "structure", "");
        Material accent = structureBlock(structId, mat(str(pal, "accent", "minecraft:copper_block")));
        fill(world, cx - 1, y + 1, cz - 1, cx + 1, y + 2, cz + 1, accent, stats);
        set(world, cx, y + 1, cz, mat("minecraft:barrel"), stats); // restore barrel

        // Floating name tag.
        String label = str(m, "name_ko", str(m, "name", str(m, "uid", "module")));
        spawnLabel(world, cx + 0.5, y + 3, cz + 0.5, label);

        // Role mobs.
        if (m.has("mobs")) {
            JsonArray roles = m.getAsJsonArray("mobs");
            for (int i = 0; i < roles.size(); i++) {
                String roleId = roles.get(i).getAsString();
                summonRole(world, roleId, cx + 0.5, y + 1, cz + 2.5, stats);
            }
        }

        // Structure extras.
        String specId = str(m, "spec", "");
        if ("portal_hub".equals(specId)) {
            buildPortal(world, str(m, "dimension", "fac:campus"), cx, y, cz, stats);
        } else if ("chunk_anchor".equals(specId)) {
            set(world, cx, y + 1, cz, mat("minecraft:lodestone"), stats);
            set(world, cx, y + 2, cz, mat("minecraft:beacon"), stats);
        }
    }

    private void buildPortal(World world, String dimId, int cx, int y, int cz, Stats stats) {
        Material obsidian = mat(str(dimId).equals("fac:void_stack")
                ? "minecraft:crying_obsidian" : "minecraft:obsidian");
        // 4x5 nether-style frame with an air interior.
        fill(world, cx - 2, y + 1, cz - 4, cx + 1, y + 5, cz - 4, obsidian, stats);
        fill(world, cx - 1, y + 2, cz - 4, cx, y + 4, cz - 4, Material.AIR, stats);
        if (dimId.equals("fac:campus") || dimId.equals("fac:end_works")) {
            fill(world, cx - 1, y + 1, cz + 4, cx + 1, y + 1, cz + 4,
                    mat("minecraft:end_portal_frame"), stats);
        }
    }

    private void summonRole(World world, String roleId, double x, double y, double z, Stats stats) {
        JsonObject mobs = design.mobs();
        if (!mobs.has(roleId)) {
            return;
        }
        JsonObject role = mobs.getAsJsonObject(roleId);
        String entityKey = str(role, "entity", "");
        EntityType type = entityType(entityKey);
        if (type == null) {
            stats.mobFailures++;
            return;
        }
        String name = str(role, "name", roleId);
        Location loc = new Location(world, x, y, z);
        try {
            world.spawnEntity(loc, type, CreatureSpawnEvent.SpawnReason.CUSTOM, e -> {
                e.setPersistent(true);
                e.setInvulnerable(true);
                e.setSilent(true);
                e.customName(Component.text(name, NamedTextColor.YELLOW));
                e.setCustomNameVisible(true);
                if (e instanceof LivingEntity le) {
                    le.setAI(false);
                    le.setRemoveWhenFarAway(false);
                    le.setCollidable(false);
                }
            });
            stats.mobs++;
        } catch (RuntimeException ex) {
            stats.mobFailures++;
            log.warning("summon " + entityKey + " failed: " + ex.getMessage());
        }
    }

    private void spawnLabel(World world, double x, double y, double z, String text) {
        Location loc = new Location(world, x, y, z);
        world.spawn(loc, ArmorStand.class, stand -> {
            stand.setInvisible(true);
            stand.setMarker(true);
            stand.setGravity(false);
            stand.setInvulnerable(true);
            stand.setPersistent(true);
            stand.customName(Component.text(text, NamedTextColor.AQUA));
            stand.setCustomNameVisible(true);
        });
    }

    // ---- geometry helpers -------------------------------------------------

    private void fill(World w, int x1, int y1, int z1, int x2, int y2, int z2,
                      Material mat, Stats stats) {
        if (mat == null) return;
        for (int x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
            for (int y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
                for (int z = Math.min(z1, z2); z <= Math.max(z1, z2); z++) {
                    set(w, x, y, z, mat, stats);
                }
            }
        }
    }

    private void hollow(World w, int x1, int y1, int z1, int x2, int y2, int z2,
                        Material mat, Stats stats) {
        if (mat == null) return;
        for (int x = x1; x <= x2; x++) {
            for (int y = y1; y <= y2; y++) {
                for (int z = z1; z <= z2; z++) {
                    boolean shell = x == x1 || x == x2 || y == y1 || y == y2 || z == z1 || z == z2;
                    if (shell) {
                        set(w, x, y, z, mat, stats);
                    }
                }
            }
        }
    }

    private void set(World w, int x, int y, int z, Material mat, Stats stats) {
        if (mat == null) return;
        w.getBlockAt(x, y, z).setType(mat, false);
        stats.blocks++;
    }

    // ---- catalog lookups --------------------------------------------------

    private String dimPalette(String dimId) {
        switch (dimId) {
            case "fac:nether_works": return "nether";
            case "fac:end_works": return "end";
            case "fac:void_stack": return "void";
            default: return "campus";
        }
    }

    private String topBiomeKey(String dimId) {
        JsonObject dim = design.dimensions().getAsJsonObject(dimId);
        String facBiome = str(dim, "biome", "");
        JsonObject biomes = design.biomes();
        if (biomes.has(facBiome)) {
            return str(biomes.getAsJsonObject(facBiome), "vanilla", "minecraft:plains");
        }
        return "minecraft:plains";
    }

    private String flatSettings(JsonObject dim, String biomeKey) {
        StringBuilder layers = new StringBuilder();
        if (dim.has("floor_layers")) {
            JsonArray fl = dim.getAsJsonArray("floor_layers");
            for (int i = 0; i < fl.size(); i++) {
                JsonArray pair = fl.get(i).getAsJsonArray();
                if (layers.length() > 0) layers.append(',');
                layers.append("{\"block\":\"").append(pair.get(0).getAsString())
                        .append("\",\"height\":").append(pair.get(1).getAsInt()).append('}');
            }
        }
        return "{\"biome\":\"" + biomeKey + "\",\"layers\":[" + layers + "],\"structure_overrides\":[]}";
    }

    private Material structureBlock(String structId, Material fallback) {
        JsonObject structs = design.catalog().getAsJsonObject("structures");
        if (structs != null && structs.has(structId)) {
            JsonObject s = structs.getAsJsonObject(structId);
            Material m = mat(str(s, "block", ""));
            if (m != null) return m;
        }
        return fallback;
    }

    private static World.Environment environmentFor(String vanillaType) {
        switch (vanillaType) {
            case "minecraft:the_nether": return World.Environment.NETHER;
            case "minecraft:the_end": return World.Environment.THE_END;
            default: return World.Environment.NORMAL;
        }
    }

    private static Material mat(String key) {
        if (key == null || key.isEmpty()) return null;
        int br = key.indexOf('[');
        String clean = br >= 0 ? key.substring(0, br) : key;
        Material m = Material.matchMaterial(clean);
        if (m == null) {
            String bare = clean.contains(":") ? clean.substring(clean.indexOf(':') + 1) : clean;
            try {
                m = Material.valueOf(bare.toUpperCase());
            } catch (IllegalArgumentException ignored) {
                return null;
            }
        }
        return m;
    }

    private static EntityType entityType(String key) {
        if (key == null || key.isEmpty()) return null;
        String bare = key.contains(":") ? key.substring(key.indexOf(':') + 1) : key;
        try {
            return EntityType.valueOf(bare.toUpperCase());
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    private static Biome biomeFor(String key) {
        if (key == null || key.isEmpty()) return null;
        NamespacedKey nk = NamespacedKey.fromString(key);
        if (nk == null) return null;
        return Registry.BIOME.get(nk);
    }

    private static String str(JsonObject o, String field, String def) {
        return o != null && o.has(field) && !o.get(field).isJsonNull()
                ? o.get(field).getAsString() : def;
    }

    private static String str(String s) {
        return s == null ? "" : s;
    }
}
