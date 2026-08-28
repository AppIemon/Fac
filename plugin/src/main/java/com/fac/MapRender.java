package com.fac;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.bukkit.HeightMap;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;

import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

/**
 * Renders a top-down PNG of a built factory world by reading the highest
 * block at each column. This produces real visual proof of the applied
 * world without needing a Minecraft client.
 */
public final class MapRender {

    private static final int SCALE = 3; // pixels per block

    private final Design design;

    public MapRender(Design design) {
        this.design = design;
    }

    public int[] render(World world, String dimId, File out) throws IOException {
        int minX = Integer.MAX_VALUE, minZ = Integer.MAX_VALUE;
        int maxX = Integer.MIN_VALUE, maxZ = Integer.MIN_VALUE;
        JsonArray modules = design.modules();
        for (int i = 0; i < modules.size(); i++) {
            JsonObject m = modules.get(i).getAsJsonObject();
            if (!dimId.equals(get(m, "dimension"))) continue;
            int x = m.get("x").getAsInt(), z = m.get("z").getAsInt();
            int w = m.get("w").getAsInt(), d = m.get("d").getAsInt();
            minX = Math.min(minX, x - 6);
            minZ = Math.min(minZ, z - 6);
            maxX = Math.max(maxX, x + w + 6);
            maxZ = Math.max(maxZ, z + d + 6);
        }
        if (minX > maxX) {
            return new int[]{0, 0};
        }

        int wpx = (maxX - minX + 1) * SCALE;
        int hpx = (maxZ - minZ + 1) * SCALE;
        BufferedImage img = new BufferedImage(wpx, hpx, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setColor(new Color(10, 14, 20));
        g.fillRect(0, 0, wpx, hpx);

        for (int x = minX; x <= maxX; x++) {
            for (int z = minZ; z <= maxZ; z++) {
                Block top = world.getHighestBlockAt(x, z, HeightMap.MOTION_BLOCKING);
                Material mat = top.getType();
                int y = top.getY();
                if (mat.isAir() || y <= WorldBuilder.FLOOR_Y - 2) {
                    continue;
                }
                Color c = colorFor(mat);
                // Shade taller blocks brighter for a little relief.
                int lift = Math.max(0, Math.min(60, (y - WorldBuilder.FLOOR_Y) * 2));
                c = new Color(
                        clamp(c.getRed() + lift),
                        clamp(c.getGreen() + lift),
                        clamp(c.getBlue() + lift));
                g.setColor(c);
                g.fillRect((x - minX) * SCALE, (z - minZ) * SCALE, SCALE, SCALE);
            }
        }
        g.dispose();
        out.getParentFile().mkdirs();
        ImageIO.write(img, "png", out);
        return new int[]{wpx, hpx};
    }

    private static int clamp(int v) {
        return Math.max(0, Math.min(255, v));
    }

    private static String get(JsonObject o, String f) {
        return o.has(f) && !o.get(f).isJsonNull() ? o.get(f).getAsString() : "";
    }

    private static Color colorFor(Material m) {
        String n = m.name();
        if (n.contains("IRON")) return new Color(216, 220, 228);
        if (n.contains("GOLD") || n.contains("GILDED")) return new Color(246, 200, 86);
        if (n.contains("COPPER")) return new Color(196, 120, 84);
        if (n.contains("SEA_LANTERN") || n.contains("END_ROD")) return new Color(180, 240, 235);
        if (n.contains("SHROOMLIGHT")) return new Color(240, 150, 70);
        if (n.contains("PURPUR") || n.contains("CHORUS")) return new Color(170, 120, 190);
        if (n.contains("END_STONE")) return new Color(220, 224, 160);
        if (n.contains("OBSIDIAN")) return new Color(40, 30, 60);
        if (n.contains("BONE")) return new Color(228, 224, 200);
        if (n.contains("MOSS")) return new Color(90, 130, 60);
        if (n.contains("COBWEB")) return new Color(210, 214, 220);
        if (n.contains("BLACKSTONE") || n.contains("BLACK_CONCRETE")) return new Color(30, 30, 36);
        if (n.contains("RED_NETHER") || n.contains("CRIMSON")) return new Color(120, 30, 40);
        if (n.contains("NETHER_QUARTZ") || n.contains("QUARTZ")) return new Color(230, 226, 218);
        if (n.contains("SHULKER")) return new Color(150, 110, 160);
        if (n.contains("BARREL") || n.contains("LOG") || n.contains("FARMLAND")) return new Color(150, 110, 60);
        if (n.contains("BLAST_FURNACE") || n.contains("CRAFTER")) return new Color(90, 96, 104);
        if (n.contains("GLASS")) {
            if (n.contains("ORANGE")) return new Color(180, 120, 60);
            if (n.contains("PURPLE")) return new Color(120, 80, 150);
            if (n.contains("BLACK")) return new Color(50, 50, 58);
            return new Color(150, 165, 185);
        }
        if (n.contains("GRAY_CONCRETE")) return new Color(76, 82, 92);
        if (n.contains("LODESTONE") || n.contains("RESPAWN")) return new Color(90, 95, 120);
        if (n.contains("BEACON")) return new Color(120, 230, 220);
        if (n.contains("CRYING")) return new Color(60, 40, 110);
        if (n.contains("SCULK")) return new Color(20, 40, 55);
        return new Color(110, 120, 130);
    }
}
