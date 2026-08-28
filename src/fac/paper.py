"""Fetch and cache the Paper 26.2 server jar used for live/plugin tests.

Pinned to the exact build the project targets so live tests are
reproducible. Safe to call repeatedly: it verifies the cached jar's
sha256 and only downloads when missing or corrupt.
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

PAPER_VERSION = "26.2"
PAPER_BUILD = 119
PAPER_SHA256 = "a8c9140c3075bd7c04973e9cdc491b21bfe6bad472b674ef932a4ae0fec19629"
PAPER_JAR = Path("/tmp/fac-server/paper-26.2-119.jar")
PAPER_URL = (
    "https://fill-data.papermc.io/v1/objects/"
    f"{PAPER_SHA256}/paper-{PAPER_VERSION}-{PAPER_BUILD}.jar"
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_paper_jar(dest: Path = PAPER_JAR) -> Path:
    """Return the path to a verified Paper jar, downloading it if needed."""
    if dest.exists() and _sha256(dest) == PAPER_SHA256:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    urllib.request.urlretrieve(PAPER_URL, tmp)  # noqa: S310 - pinned https URL
    actual = _sha256(tmp)
    if actual != PAPER_SHA256:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Paper jar checksum mismatch: expected {PAPER_SHA256}, got {actual}"
        )
    tmp.replace(dest)
    return dest


if __name__ == "__main__":
    path = ensure_paper_jar()
    print(f"Paper {PAPER_VERSION} build {PAPER_BUILD} ready at {path}")
