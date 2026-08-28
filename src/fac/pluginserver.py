"""Boot Paper 26.2 with the Fac plugin and apply the AI design to flat worlds.

This is the AI's end-to-end self-test for the *plugin* path: it deploys the
freshly exported ``factory.json`` next to the plugin, boots a real Paper
server on a flat overworld, runs ``/fac setup`` over RCON to build every
dimension, then probes ``/fac validate`` / ``/fac status`` to confirm the
world matches the design. It can also ask the plugin to render PNG maps.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

from fac.paper import PAPER_JAR, ensure_paper_jar
from fac.rcon import Rcon, RconError, wait_for_port

SERVER_DIR = Path("/tmp/fac-server/plugin-instance")
RCON_PASSWORD = "fac"
RCON_PORT = 25577


def prepare_instance(plugin_jar: Path, factory_json: Path) -> Path:
    ensure_paper_jar()
    if not plugin_jar.exists():
        raise FileNotFoundError(
            f"Plugin jar missing: {plugin_jar}. Build it with "
            f"`cd plugin && mvn -q -B package` first."
        )
    SERVER_DIR.mkdir(parents=True, exist_ok=True)
    (SERVER_DIR / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    (SERVER_DIR / "server.properties").write_text(
        "\n".join(
            [
                "enable-rcon=true",
                f"rcon.password={RCON_PASSWORD}",
                f"rcon.port={RCON_PORT}",
                "broadcast-rcon-to-ops=false",
                "online-mode=false",
                "spawn-protection=0",
                "gamemode=creative",
                "difficulty=easy",
                "level-name=lobby",
                "level-type=minecraft:flat",
                "allow-nether=false",
                "enable-command-block=true",
                "motd=Fac AI Factory (plugin)",
                "enforce-secure-profile=false",
                "max-players=4",
                "view-distance=6",
                "simulation-distance=4",
                "sync-chunk-writes=false",
                "pause-when-empty-seconds=0",
                "server-port=25566",
                "white-list=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    plugins = SERVER_DIR / "plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plugin_jar, plugins / "FacPlugin.jar")
    # Deploy the freshly designed factory so the plugin applies the latest AI run.
    data_dir = plugins / "FacPlugin"
    data_dir.mkdir(parents=True, exist_ok=True)
    if factory_json.exists():
        shutil.copy2(factory_json, data_dir / "factory.json")
    return SERVER_DIR


def start_server(cwd: Path) -> subprocess.Popen:
    log = (cwd / "fac-boot.log").open("w", encoding="utf-8")
    return subprocess.Popen(
        [
            "java",
            "-Xms1G",
            "-Xmx3G",
            "-XX:+UseG1GC",
            "-jar",
            str(PAPER_JAR),
            "nogui",
        ],
        cwd=cwd,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
    )


def wait_done(log_path: Path, proc: subprocess.Popen, timeout: float = 300.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"server exited {proc.returncode}\n{text[-4000:]}")
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if "Done (" in text or "Done!" in text:
                return
        time.sleep(1.0)
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    raise TimeoutError(f"server did not reach Done\n{text[-4000:]}")


def _num(pattern: str, text: str, default: int = -1) -> int:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else default


def probe(render_dir: Path | None) -> dict:
    wait_for_port("127.0.0.1", RCON_PORT, timeout=60)
    # Long timeout: /fac setup builds every dimension synchronously.
    r = Rcon("127.0.0.1", RCON_PORT, RCON_PASSWORD, timeout=240.0)
    r.connect()
    out: dict[str, str] = {}
    try:
        out["status_before"] = r.command("fac status")
        out["setup"] = r.command("fac setup")
        out["validate"] = r.command("fac validate")
        out["status_after"] = r.command("fac status")
        out["worlds"] = r.command("execute run list")
        if render_dir is not None:
            out["render"] = r.command(f"fac render {render_dir}")
        return out
    finally:
        try:
            r.command("stop")
        except RconError:
            pass
        r.close()


def run_plugin_test(plugin_jar: Path, factory_json: Path, render_dir: Path | None) -> dict:
    cwd = prepare_instance(plugin_jar, factory_json)
    log_path = cwd / "fac-boot.log"
    proc = start_server(cwd)
    try:
        wait_done(log_path, proc)
        time.sleep(2.0)
        results = probe(render_dir)
        setup = results.get("setup", "")
        validate = results.get("validate", "")
        summary = {
            "worlds": _num(r"worlds=(\d+)", setup),
            "modules": _num(r"modules=(\d+)", setup),
            "blocks": _num(r"blocks=(\d+)", setup),
            "mobs": _num(r"mobs=(\d+)", setup),
            "mob_failures": _num(r"mobFailures=(\d+)", setup),
            "biome_cells": _num(r"biomeCells=(\d+)", setup),
            "validate_ok": "ok=true" in validate,
            "validate_entities": _num(r"entities=(\d+)", validate),
        }
        ok = (
            summary["validate_ok"]
            and summary["modules"] > 0
            and summary["mob_failures"] == 0
        )
        return {
            "ok": ok,
            "summary": summary,
            "results": results,
            "log_tail": log_path.read_text(encoding="utf-8", errors="replace")[-8000:],
        }
    except Exception as exc:  # noqa: BLE001 - surface any boot/probe failure
        log = ""
        if log_path.exists():
            log = log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
        return {"ok": False, "error": str(exc), "log_tail": log}
    finally:
        if proc.poll() is None:
            try:
                if proc.stdin:
                    proc.stdin.write("stop\n")
                    proc.stdin.flush()
            except OSError:
                pass
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
