"""Boot Paper 26.2, load the datapack, and probe dimensions over RCON."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from fac.paper import PAPER_JAR, ensure_paper_jar
from fac.rcon import Rcon, RconError, wait_for_port

SERVER_DIR = Path("/tmp/fac-server/instance")
RCON_PASSWORD = "fac"
RCON_PORT = 25575


def prepare_instance(datapack: Path) -> Path:
    SERVER_DIR.mkdir(parents=True, exist_ok=True)
    ensure_paper_jar()
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
                "allow-nether=true",
                "enable-command-block=true",
                "motd=Fac AI Factory World",
                "level-name=world",
                "enforce-secure-profile=false",
                "max-players=4",
                "view-distance=4",
                "simulation-distance=4",
                "sync-chunk-writes=false",
                "pause-when-empty-seconds=0",
                "server-port=25565",
                "white-list=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    pack_dest = SERVER_DIR / "world" / "datapacks" / "fac"
    if pack_dest.exists():
        shutil.rmtree(pack_dest)
    pack_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(datapack, pack_dest)
    return SERVER_DIR


def start_server(cwd: Path) -> subprocess.Popen:
    log = (cwd / "fac-boot.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(
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
    return proc


def wait_done(log_path: Path, proc: subprocess.Popen, timeout: float = 240.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"server exited {proc.returncode}\n{text[-4000:]}")
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if "Done (" in text or "Done!" in text:
                return
            if "Failed to load datapacks" in text and "Done (" not in text:
                # Keep waiting — vanilla still boots, datapack errors show later.
                pass
        time.sleep(1.0)
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    raise TimeoutError(f"server did not reach Done\n{text[-4000:]}")


def probe() -> dict[str, str]:
    wait_for_port("127.0.0.1", RCON_PORT, timeout=30)
    r = Rcon("127.0.0.1", RCON_PORT, RCON_PASSWORD)
    r.connect()
    try:
        commands = [
            "datapack list",
            "function fac:validate",
            "execute in fac:campus run spawnpoint @a 8 66 8",
            "execute in fac:nether_works run worldborder get",
            "execute in fac:end_works run worldborder get",
            "execute in fac:void_stack run worldborder get",
            "scoreboard players get $ok fac_ok",
            "scoreboard players get $campus fac_ok",
            "scoreboard players get $nether fac_ok",
            "scoreboard players get $end fac_ok",
            "scoreboard players get $void fac_ok",
        ]
        out: dict[str, str] = {}
        for cmd in commands:
            out[cmd] = r.command(cmd)
        return out
    finally:
        try:
            r.command("stop")
        except RconError:
            pass
        r.close()


def run_live_test(datapack: Path) -> dict:
    cwd = prepare_instance(datapack)
    log_path = cwd / "fac-boot.log"
    proc = start_server(cwd)
    try:
        wait_done(log_path, proc)
        time.sleep(2.0)
        results = probe()
        return {
            "ok": True,
            "results": results,
            "log_tail": log_path.read_text(encoding="utf-8", errors="replace")[-8000:],
        }
    except Exception as exc:
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
                proc.wait(timeout=40)
            except subprocess.TimeoutExpired:
                proc.kill()
