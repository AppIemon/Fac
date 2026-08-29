package com.fac;

import org.bukkit.plugin.java.JavaPlugin;

import java.io.File;
import java.io.IOException;

public final class FacPlugin extends JavaPlugin {

    private Design design;

    @Override
    public void onEnable() {
        System.setProperty("java.awt.headless", "true");
        if (!getDataFolder().exists() && !getDataFolder().mkdirs()) {
            getLogger().warning("could not create data folder");
        }
        File designFile = new File(getDataFolder(), "factory.json");
        if (!designFile.exists()) {
            saveResource("factory.json", false);
        }
        if (!reloadDesign()) {
            getLogger().severe("Fac could not load factory.json; commands will report the error.");
        }
        FacCommand command = new FacCommand(this);
        if (getCommand("fac") != null) {
            getCommand("fac").setExecutor(command);
            getCommand("fac").setTabCompleter(command);
        }
        getLogger().info("FacPlugin enabled. /fac setup to apply the AI factory to flat worlds.");
    }

    public boolean reloadDesign() {
        File designFile = new File(getDataFolder(), "factory.json");
        try {
            this.design = Design.load(designFile.toPath());
            getLogger().info("Loaded factory.json: " + design.modules().size()
                    + " modules, acceptance " + (design.acceptancePassed() ? "PASS" : "FAIL")
                    + " (" + design.acceptancePassedCount() + "/" 
                    + (design.acceptancePassedCount() + design.acceptanceFailedCount()) + ")");
            return true;
        } catch (IOException | RuntimeException ex) {
            getLogger().severe("Failed to load factory.json: " + ex.getMessage());
            this.design = null;
            return false;
        }
    }

    public Design design() {
        return design;
    }
}
