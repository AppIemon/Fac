#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the Fac AI factory world.
#
# Prepares everything needed to design the factory (Python), build the
# Paper 26.2 plugin (Java 25 + Maven), and run the live/plugin tests
# (cached Paper server jar). Safe to run repeatedly.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Fac install: ensuring system toolchain (JDK 25 + Maven) =="
need_apt=0
if ! command -v mvn >/dev/null 2>&1; then need_apt=1; fi
if [ ! -x /usr/lib/jvm/java-25-openjdk-amd64/bin/javac ]; then need_apt=1; fi
if [ "$need_apt" = "1" ]; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq openjdk-25-jdk-headless maven
fi
# Prefer Java 25 (required by Paper 26.2 / paper-api bytecode).
if [ -x /usr/lib/jvm/java-25-openjdk-amd64/bin/java ]; then
  sudo update-alternatives --set java  /usr/lib/jvm/java-25-openjdk-amd64/bin/java  >/dev/null 2>&1 || true
  sudo update-alternatives --set javac /usr/lib/jvm/java-25-openjdk-amd64/bin/javac >/dev/null 2>&1 || true
fi
export JAVA_HOME=/usr/lib/jvm/java-25-openjdk-amd64
java -version
mvn -version | head -1

echo "== Fac install: AI design pass (design -> simulate -> accept -> export) =="
PYTHONPATH=src python3 -m fac complete --out .

echo "== Fac install: Python acceptance tests =="
PYTHONPATH=src python3 -m unittest tests/test_factory.py

echo "== Fac install: building the Paper plugin =="
( cd plugin && mvn -q -B -DskipTests package )
ls -la plugin/target/FacPlugin.jar

echo "== Fac install: caching the pinned Paper 26.2 server jar =="
python3 src/fac/paper.py

echo "== Fac install: done =="
