#!/usr/bin/env bash
# Download and verify the pinned Paper 26.2 server jar used by live tests.
# Idempotent: skips the download when a valid jar is already cached.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/src/fac/paper.py"
