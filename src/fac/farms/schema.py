"""Schema for a survival-farm knowledge-base entry."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict


CATEGORIES = {
    "mob",        # hostile mob / XP / drops
    "resource",   # non-mob resources (ore-ish, minerals, blocks)
    "crop",       # plants, food crops
    "wood",       # trees / logs
    "animal",     # passive animals / food
    "utility",    # redstone, trading, storage, smelting
}

DIMENSIONS = {"overworld", "nether", "end", "any"}

REDSTONE = {"none", "low", "medium", "high"}

# Confidence that the design still works on the target version.
STATUS = {
    "works",             # standard, widely reproduced, no known breakage
    "works_with_caveat", # works but has a version-specific gotcha (see caveats)
    "situational",       # depends on structure/biome availability
}


@dataclass(frozen=True)
class Footprint:
    w: int
    h: int
    d: int

    def volume(self) -> int:
        return self.w * self.h * self.d


@dataclass(frozen=True)
class Source:
    creator: str          # reputable channel/author, e.g. "ilmango"
    kind: str = "youtube"  # youtube | wiki | forum | blueprint
    ref: str = ""          # search phrase or URL (kept generic, not fabricated)


@dataclass
class Farm:
    id: str
    name: str
    name_ko: str
    category: str
    subcategory: str
    principle: str                       # the core mechanic, one/two sentences
    mechanics: list[str]                 # tags: spawning, water_stream, fall_damage, ...
    dimension: str
    footprint: Footprint
    # Requirements / components (all validated against the 26.2 registry).
    blocks: list[str] = field(default_factory=list)      # key build blocks
    mobs: list[str] = field(default_factory=list)        # entity_type ids
    items_out: list[str] = field(default_factory=list)   # produced items
    items_in: list[str] = field(default_factory=list)    # consumed items
    biomes: list[str] = field(default_factory=list)      # required biome ids (may be empty)
    # Operating envelope.
    y_level: str = "any"
    light: str = "any"
    rate: str = ""                       # human string, approx per hour
    afk: bool = True
    redstone: str = "low"
    difficulty: str = "medium"
    # Provenance / currency.
    version: str = "26.2"
    status: str = "works"
    caveats: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: dict) -> "Farm":
        fp = d["footprint"]
        srcs = [Source(**s) if isinstance(s, dict) else s for s in d.get("sources", [])]
        return Farm(
            id=d["id"],
            name=d["name"],
            name_ko=d.get("name_ko", d["name"]),
            category=d["category"],
            subcategory=d.get("subcategory", ""),
            principle=d["principle"],
            mechanics=list(d.get("mechanics", [])),
            dimension=d["dimension"],
            footprint=Footprint(**fp) if isinstance(fp, dict) else Footprint(*fp),
            blocks=list(d.get("blocks", [])),
            mobs=list(d.get("mobs", [])),
            items_out=list(d.get("items_out", [])),
            items_in=list(d.get("items_in", [])),
            biomes=list(d.get("biomes", [])),
            y_level=d.get("y_level", "any"),
            light=d.get("light", "any"),
            rate=d.get("rate", ""),
            afk=d.get("afk", True),
            redstone=d.get("redstone", "low"),
            difficulty=d.get("difficulty", "medium"),
            version=d.get("version", "26.2"),
            status=d.get("status", "works"),
            caveats=list(d.get("caveats", [])),
            sources=srcs,
            tags=list(d.get("tags", [])),
        )

    def schema_errors(self) -> list[str]:
        """Structural (non-registry) validation."""
        errs: list[str] = []
        if self.category not in CATEGORIES:
            errs.append(f"bad category {self.category!r}")
        if self.dimension not in DIMENSIONS:
            errs.append(f"bad dimension {self.dimension!r}")
        if self.redstone not in REDSTONE:
            errs.append(f"bad redstone {self.redstone!r}")
        if self.status not in STATUS:
            errs.append(f"bad status {self.status!r}")
        if not self.principle:
            errs.append("empty principle")
        if not self.mechanics:
            errs.append("no mechanics tags")
        for fld in ("w", "h", "d"):
            if getattr(self.footprint, fld) <= 0:
                errs.append(f"footprint.{fld} must be > 0")
        return errs
