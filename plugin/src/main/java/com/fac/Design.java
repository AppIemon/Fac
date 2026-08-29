package com.fac;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Wraps the AI-designed factory.json produced by the Python `fac` pipeline.
 * Everything the builder needs (dimensions, biomes, palettes, structures,
 * mobs, and placed modules) is read straight from that export, so a new AI
 * design is applied simply by dropping in a new factory.json and reloading.
 */
public final class Design {

    private final JsonObject root;

    private Design(JsonObject root) {
        this.root = root;
    }

    public static Design load(Path file) throws IOException {
        try (Reader r = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            JsonObject obj = new Gson().fromJson(r, JsonObject.class);
            if (obj == null) {
                throw new IOException("factory.json is empty or invalid: " + file);
            }
            return new Design(obj);
        }
    }

    public JsonObject catalog() {
        return root.getAsJsonObject("catalog");
    }

    public JsonObject dimensions() {
        return catalog().getAsJsonObject("dimensions");
    }

    public JsonObject biomes() {
        return catalog().getAsJsonObject("biomes");
    }

    public JsonObject palettes() {
        return catalog().getAsJsonObject("palettes");
    }

    public JsonObject mobs() {
        return catalog().getAsJsonObject("mobs");
    }

    public JsonArray modules() {
        return root.getAsJsonObject("design").getAsJsonArray("modules");
    }

    public boolean acceptancePassed() {
        JsonObject rep = root.getAsJsonObject("report");
        return rep != null && rep.has("ok") && rep.get("ok").getAsBoolean();
    }

    public int acceptancePassedCount() {
        JsonObject rep = root.getAsJsonObject("report");
        return rep != null && rep.has("passed") ? rep.get("passed").getAsInt() : 0;
    }

    public int acceptanceFailedCount() {
        JsonObject rep = root.getAsJsonObject("report");
        return rep != null && rep.has("failed") ? rep.get("failed").getAsInt() : 0;
    }
}
