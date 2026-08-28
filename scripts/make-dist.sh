#!/usr/bin/env bash
# Build a ready-to-run Paper 26.2 server folder + zip with a factory already
# built into a real flat world. "Unzip and run" (run.sh / run.bat).
#
# The zip stays small: it ships the pre-built world + plugin + configs, and
# run.sh downloads the Paper server runtime on first launch (one-time).
#
# Usage:
#   scripts/make-dist.sh [FACTORY_JSON] [OUT_ZIP] [SPAWN_X SPAWN_Y SPAWN_Z]
# Defaults: examples/iron_factory.json  dist/fac-iron-server.zip  48 64 40
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FACTORY_JSON="${1:-$ROOT/examples/iron_factory.json}"
OUT_ZIP="${2:-$ROOT/dist/fac-iron-server.zip}"
SPAWN_X="${3:-48}"; SPAWN_Y="${4:-64}"; SPAWN_Z="${5:-40}"

export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-25-openjdk-amd64}"
PAPER_JAR="/tmp/fac-server/paper-26.2-119.jar"
PAPER_URL="https://fill-data.papermc.io/v1/objects/a8c9140c3075bd7c04973e9cdc491b21bfe6bad472b674ef932a4ae0fec19629/paper-26.2-119.jar"
RCON_PORT=25588
BUILD="$(mktemp -d /tmp/fac-dist.XXXXXX)"
NAME="fac-iron-server"
DIST="$BUILD/$NAME"

echo "== make-dist: build plugin =="
( cd plugin && mvn -q -B -DskipTests package )

echo "== make-dist: ensure Paper jar =="
python3 "$ROOT/src/fac/paper.py"

echo "== make-dist: stage server dir =="
mkdir -p "$DIST/plugins/FacPlugin"
cp "$PAPER_JAR" "$DIST/paper-26.2-119.jar"
cp plugin/target/FacPlugin.jar "$DIST/plugins/FacPlugin.jar"
cp "$FACTORY_JSON" "$DIST/plugins/FacPlugin/factory.json"
printf 'eula=true\n' > "$DIST/eula.txt"
# A tall flat preset so the plain's surface sits at y=63 (factory floor slab).
GEN='{"biome":"minecraft:plains","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:stone","height":126},{"block":"minecraft:grass_block","height":1}],"structure_overrides":[]}'
cat > "$DIST/server.properties" <<EOF
level-name=fac_campus
level-type=minecraft:flat
generator-settings=$GEN
gamemode=creative
difficulty=easy
online-mode=false
spawn-protection=0
allow-nether=false
enable-command-block=true
motd=Fac Iron Factory (flat)
view-distance=8
simulation-distance=6
max-players=8
white-list=false
enforce-secure-profile=false
pause-when-empty-seconds=0
server-port=25565
enable-rcon=true
rcon.password=makedist
rcon.port=$RCON_PORT
broadcast-rcon-to-ops=false
EOF

echo "== make-dist: boot + build factory into the world =="
( cd "$DIST" && nohup java -Xms1G -Xmx2G -jar paper-26.2-119.jar nogui > boot.log 2>&1 & echo $! > "$BUILD/pid" )
for _ in $(seq 1 120); do
  grep -aq "Done (" "$DIST/boot.log" 2>/dev/null && break
  sleep 1
done
grep -aq "Done (" "$DIST/boot.log" || { echo "server did not start"; tail -40 "$DIST/boot.log"; exit 1; }

PYTHONPATH="$ROOT/src" python3 - "$RCON_PORT" "$SPAWN_X" "$SPAWN_Y" "$SPAWN_Z" <<'PY'
import sys
from fac.rcon import Rcon, wait_for_port
port, sx, sy, sz = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
wait_for_port("127.0.0.1", port, timeout=30)
r = Rcon("127.0.0.1", port, "makedist", timeout=180.0); r.connect()
print(r.command("fac setup"))
print(r.command(f"setworldspawn {sx} {sy} {sz}"))
print(r.command("stop"))
r.close()
PY

# Wait for shutdown.
PID="$(cat "$BUILD/pid")"
for _ in $(seq 1 60); do kill -0 "$PID" 2>/dev/null || break; sleep 1; done

echo "== make-dist: slim + finalize (runtime is fetched on first launch) =="
( cd "$DIST" && rm -rf paper-26.2-119.jar cache versions libraries .paper logs boot.log && find . -name session.lock -delete )
# server.properties without rcon for distribution.
cat > "$DIST/server.properties" <<EOF
level-name=fac_campus
level-type=minecraft:flat
generator-settings=$GEN
gamemode=creative
difficulty=easy
online-mode=false
spawn-protection=0
allow-nether=false
enable-command-block=true
motd=Fac Iron Factory (flat)
view-distance=8
simulation-distance=6
max-players=8
white-list=false
enforce-secure-profile=false
pause-when-empty-seconds=0
server-port=25565
EOF
cat > "$DIST/run.sh" <<EOF
#!/usr/bin/env bash
# Fac Iron Factory - Paper 26.2 server. Requires Java 25+. First launch downloads Paper (one-time).
set -e
cd "\$(dirname "\$0")"
JAR=paper-26.2-119.jar
URL="$PAPER_URL"
if [ ! -f "\$JAR" ]; then
  echo "[Fac] Downloading Paper 26.2 (one-time)..."
  curl -fL -o "\$JAR" "\$URL" || wget -O "\$JAR" "\$URL"
fi
exec java -Xms1G -Xmx2G -jar "\$JAR" nogui
EOF
chmod +x "$DIST/run.sh"
cat > "$DIST/run.bat" <<EOF
@echo off
rem Fac Iron Factory - Paper 26.2 server. Requires Java 25+. First launch downloads Paper (one-time).
cd /d "%~dp0"
set JAR=paper-26.2-119.jar
if not exist "%JAR%" (
  echo [Fac] Downloading Paper 26.2 ^(one-time^)...
  powershell -Command "Invoke-WebRequest -Uri '$PAPER_URL' -OutFile '%JAR%'"
)
java -Xms1G -Xmx2G -jar "%JAR%" nogui
pause
EOF

cat > "$DIST/README.txt" <<'EOF'
Fac - Iron Factory (Paper 26.2 flat world)
==========================================

압축을 풀고 바로 실행하면, 평면 월드에 이미 지어진 간단한 철공장
(본부 · 사일로 · 철 주조소 2 · 아이언 골렘 경비)이 나옵니다.

■ 필요 사항
  - Java 25 이상 (Paper 26.2 는 Java 25 필요).  확인: java -version

■ 실행
  - Linux/macOS :  ./run.sh
  - Windows     :  run.bat  (더블클릭)
  * 최초 1회 실행 시 Paper 26.2 서버 런타임을 자동 다운로드합니다(인터넷 필요, 약 60MB).
    이후에는 오프라인 실행 가능. 콘솔에 "Done (...)" 가 뜨면 준비 완료.

■ 접속
  - Minecraft Java 26.2 클라이언트 → 멀티플레이 → 서버 추가 → 주소: localhost
  - online-mode=false, 크리에이티브. 스폰이 철공장 앞 평지입니다.
  - OP: 서버 콘솔에  op <닉네임>

■ 플러그인 명령 (OP)
  /fac status | setup | validate | render <경로> | reload | tp campus
  설계 변경: plugins/FacPlugin/factory.json 교체 후  /fac reload → /fac setup
EOF

mkdir -p "$(dirname "$OUT_ZIP")"
rm -f "$OUT_ZIP"
( cd "$BUILD" && zip -r -q "$OUT_ZIP" "$NAME" )
echo "== make-dist: done -> $OUT_ZIP =="
ls -la "$OUT_ZIP"
rm -rf "$BUILD"
