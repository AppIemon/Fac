package com.fac;

import net.kyori.adventure.text.Component;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class FacCommand implements CommandExecutor, TabCompleter {

    private static final List<String> SUBS =
            Arrays.asList("setup", "validate", "status", "render", "clear", "reload", "tp", "help");

    private final FacPlugin plugin;

    public FacCommand(FacPlugin plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command cmd, String label, String[] args) {
        String sub = args.length == 0 ? "help" : args[0].toLowerCase();
        Design design = plugin.design();
        if (design == null && !sub.equals("reload") && !sub.equals("help")) {
            msg(sender, "FAC ERROR factory.json not loaded. Fix the export and /fac reload.");
            return true;
        }
        switch (sub) {
            case "setup": return doSetup(sender, design);
            case "validate": return doValidate(sender, design);
            case "status": return doStatus(sender, design);
            case "render": return doRender(sender, design, args);
            case "clear": return doClear(sender, design);
            case "reload":
                boolean ok = plugin.reloadDesign();
                msg(sender, "FAC RELOAD " + (ok ? "ok" : "failed"));
                return true;
            case "tp": return doTp(sender, args);
            default:
                msg(sender, "Fac AI factory. /fac <setup|validate|status|render|clear|reload|tp>");
                return true;
        }
    }

    private boolean doSetup(CommandSender sender, Design design) {
        msg(sender, "FAC SETUP starting… acceptance="
                + (design.acceptancePassed() ? "PASS" : "FAIL"));
        long t0 = System.currentTimeMillis();
        WorldBuilder builder = new WorldBuilder(design, plugin.getLogger());
        WorldBuilder.Stats stats = new WorldBuilder.Stats();
        try {
            for (String dimId : design.dimensions().keySet()) {
                builder.buildDimension(dimId, stats);
                msg(sender, "  built " + dimId + " -> " + WorldBuilder.worldName(dimId)
                        + " (" + stats.modulesPerDim.getOrDefault(dimId, 0) + " modules)");
            }
        } catch (RuntimeException ex) {
            msg(sender, "FAC SETUP ERROR " + ex.getMessage());
            plugin.getLogger().severe("setup failed: " + ex);
            return true;
        }
        long ms = System.currentTimeMillis() - t0;
        msg(sender, "FAC SETUP done worlds=" + stats.worlds + " modules=" + stats.modules
                + " blocks=" + stats.blocks + " mobs=" + stats.mobs
                + " mobFailures=" + stats.mobFailures + " biomeCells=" + stats.biomeCells
                + " ms=" + ms);
        return true;
    }

    private boolean doValidate(CommandSender sender, Design design) {
        int worldsOk = 0, worldsExpected = 0;
        int totalEntities = 0;
        boolean allOk = true;
        for (String dimId : design.dimensions().keySet()) {
            worldsExpected++;
            String wn = WorldBuilder.worldName(dimId);
            World w = Bukkit.getWorld(wn);
            int expected = countModules(design, dimId);
            if (w == null) {
                allOk = false;
                msg(sender, "  " + dimId + " world=" + wn + " MISSING expected=" + expected);
                continue;
            }
            worldsOk++;
            loadModuleChunks(design, dimId, w);
            int ents = 0;
            for (Entity e : w.getEntities()) {
                if (!(e instanceof Player)) ents++;
            }
            totalEntities += ents;
            msg(sender, "  " + dimId + " world=" + wn + " OK modules=" + expected
                    + " entities=" + ents);
        }
        boolean ok = allOk && worldsOk == worldsExpected;
        msg(sender, "FAC VALIDATE ok=" + ok + " worlds=" + worldsOk + "/" + worldsExpected
                + " entities=" + totalEntities
                + " acceptance=" + (design.acceptancePassed() ? "PASS" : "FAIL"));
        return true;
    }

    private boolean doStatus(CommandSender sender, Design design) {
        msg(sender, "FAC STATUS modules=" + design.modules().size()
                + " dimensions=" + design.dimensions().size()
                + " acceptance=" + (design.acceptancePassed() ? "PASS" : "FAIL")
                + " checks=" + design.acceptancePassedCount() + "/"
                + (design.acceptancePassedCount() + design.acceptanceFailedCount()));
        for (String dimId : design.dimensions().keySet()) {
            World w = Bukkit.getWorld(WorldBuilder.worldName(dimId));
            String state = w == null ? "not-built"
                    : ("loaded entities=" + (w.getEntities().size()));
            msg(sender, "  " + dimId + " modules=" + countModules(design, dimId) + " " + state);
        }
        return true;
    }

    private boolean doRender(CommandSender sender, Design design, String[] args) {
        File dir = args.length >= 2
                ? new File(args[1])
                : new File(plugin.getDataFolder(), "renders");
        MapRender render = new MapRender(design);
        int done = 0;
        for (String dimId : design.dimensions().keySet()) {
            World w = Bukkit.getWorld(WorldBuilder.worldName(dimId));
            if (w == null) {
                continue;
            }
            String shortId = dimId.substring(dimId.indexOf(':') + 1);
            File out = new File(dir, "fac_" + shortId + ".png");
            try {
                int[] size = render.render(w, dimId, out);
                done++;
                msg(sender, "  rendered " + dimId + " -> " + out.getAbsolutePath()
                        + " (" + size[0] + "x" + size[1] + ")");
            } catch (Exception ex) {
                msg(sender, "  render " + dimId + " FAILED " + ex.getMessage());
            }
        }
        msg(sender, "FAC RENDER done images=" + done + " dir=" + dir.getAbsolutePath());
        return true;
    }

    private boolean doClear(CommandSender sender, Design design) {
        int cleared = 0;
        for (String dimId : design.dimensions().keySet()) {
            World w = Bukkit.getWorld(WorldBuilder.worldName(dimId));
            if (w == null) continue;
            for (Entity e : new ArrayList<>(w.getEntities())) {
                if (!(e instanceof Player)) {
                    e.remove();
                    cleared++;
                }
            }
        }
        msg(sender, "FAC CLEAR removed " + cleared + " entities. Delete fac_* world folders to reset blocks.");
        return true;
    }

    private boolean doTp(CommandSender sender, String[] args) {
        if (!(sender instanceof Player player)) {
            msg(sender, "FAC TP requires a player.");
            return true;
        }
        String dim = args.length >= 2 ? args[1] : "campus";
        String wn = dim.startsWith("fac:") ? WorldBuilder.worldName(dim) : "fac_" + dim;
        World w = Bukkit.getWorld(wn);
        if (w == null) {
            msg(sender, "FAC TP world " + wn + " not built.");
            return true;
        }
        player.teleport(new Location(w, 8, WorldBuilder.BASE_Y + 2, 8));
        msg(sender, "FAC TP -> " + wn);
        return true;
    }

    /** Loads every chunk covering this dimension's modules so entities count. */
    private static void loadModuleChunks(Design design, String dimId, World w) {
        var mods = design.modules();
        for (int i = 0; i < mods.size(); i++) {
            var m = mods.get(i).getAsJsonObject();
            if (!m.has("dimension") || !dimId.equals(m.get("dimension").getAsString())) {
                continue;
            }
            int x = m.get("x").getAsInt(), z = m.get("z").getAsInt();
            int mw = m.get("w").getAsInt(), md = m.get("d").getAsInt();
            for (int cx = (x - 2) >> 4; cx <= (x + mw + 2) >> 4; cx++) {
                for (int cz = (z - 2) >> 4; cz <= (z + md + 2) >> 4; cz++) {
                    w.getChunkAt(cx, cz).load();
                }
            }
        }
    }

    private static int countModules(Design design, String dimId) {
        int n = 0;
        var mods = design.modules();
        for (int i = 0; i < mods.size(); i++) {
            var m = mods.get(i).getAsJsonObject();
            if (m.has("dimension") && dimId.equals(m.get("dimension").getAsString())) {
                n++;
            }
        }
        return n;
    }

    private static void msg(CommandSender sender, String text) {
        sender.sendMessage(Component.text(text));
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command cmd, String label, String[] args) {
        if (args.length == 1) {
            List<String> out = new ArrayList<>();
            for (String s : SUBS) {
                if (s.startsWith(args[0].toLowerCase())) out.add(s);
            }
            return out;
        }
        return new ArrayList<>();
    }
}
