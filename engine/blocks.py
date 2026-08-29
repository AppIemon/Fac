"""실제 마인크래프트 블록 상태 모델.

ASCII 도면용 1글자 코드가 아니라, .litematic 에 그대로 들어가는
네임스페이스 ID + 블록 상태 속성을 다룬다.
facing 같은 속성이 틀리면 회로가 안 돌기 때문에 여기서 엄격하게 관리한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 방향 규약 (마인크래프트 표준)
#   north = -Z,  south = +Z,  west = -X,  east = +X,  up = +Y,  down = -Y
NORTH, SOUTH, WEST, EAST, UP, DOWN = "north", "south", "west", "east", "up", "down"
OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, WEST: EAST, EAST: WEST, UP: DOWN, DOWN: UP}
OFFSET = {NORTH: (0, 0, -1), SOUTH: (0, 0, 1), WEST: (-1, 0, 0),
          EAST: (1, 0, 0), UP: (0, 1, 0), DOWN: (0, -1, 0)}


@dataclass(frozen=True)
class Block:
    """블록 하나. id 는 네임스페이스 포함, props 는 블록 상태 속성."""
    id: str
    props: tuple[tuple[str, str], ...] = ()

    @property
    def properties(self) -> dict[str, str]:
        return dict(self.props)

    def __str__(self) -> str:
        if not self.props:
            return self.id
        inner = ",".join(f"{k}={v}" for k, v in self.props)
        return f"{self.id}[{inner}]"

    @property
    def short(self) -> str:
        return self.id.split(":", 1)[-1]


def B(block_id: str, **props: str) -> Block:
    if ":" not in block_id:
        block_id = "minecraft:" + block_id
    return Block(block_id, tuple(sorted((k, str(v)) for k, v in props.items())))


# --- 자주 쓰는 블록 --------------------------------------------------------
AIR = B("air")
STONE = B("stone")
DIRT = B("dirt")
SAND = B("sand")
MUD = B("mud")
GLASS = B("glass")
WATER = B("water", level="0")
SUGAR_CANE = B("sugar_cane", age="0")
REDSTONE_BLOCK = B("redstone_block")
LAVA = B("lava", level="0")
COBBLESTONE = B("cobblestone")
SMOOTH_STONE = B("smooth_stone")
MOSS_BLOCK = B("moss_block")
COMPOSTER = B("composter", level="0")
KELP = B("kelp", age="0")
SOUL_SAND = B("soul_sand")


def waterlogged_hopper(facing: str = EAST) -> Block:
    """물먹임 호퍼. 물기둥을 막지 않으면서 떠오른 아이템을 받는다."""
    return B("hopper", facing=facing, enabled="true")


def waterlogged_leaves(kind: str = "oak_leaves") -> Block:
    """물먹임 잎. 물을 머금되 흘려보내지 않아 용암 수원이 흑요석이 되는 걸 막는다.
    참고 설계 '2.7만 조약돌 생성기' 가 계단 대신 이걸 쓴다 (훨씬 싸다)."""
    return B(kind, distance="7", persistent="true", waterlogged="true")


def waterlogged_stairs(facing: str = EAST, kind: str = "cobblestone_stairs") -> Block:
    """물먹임 계단. 물을 머금지만 흘려보내지 않아, 용암 수원이 흑요석이 되는 걸 막는다.
    위키: 흐르는 용암이 물먹임 블록에 닿으면 조약돌은 그대로 생성된다."""
    return B(kind, facing=facing, half="bottom", shape="straight", waterlogged="true")


def dropper(facing: str = EAST) -> Block:
    return B("dropper", facing=facing, triggered="false")


def dispenser(facing: str = UP) -> Block:
    return B("dispenser", facing=facing, triggered="false")


def furnace(facing: str = NORTH) -> Block:
    return B("furnace", facing=facing, lit="false")


def piston(facing: str, sticky: bool = False) -> Block:
    """facing = 피스톤 머리가 뻗어나가는 방향."""
    assert facing in OFFSET, facing
    return B("sticky_piston" if sticky else "piston", facing=facing, extended="false")


def observer(facing: str) -> Block:
    """facing = 관측기가 '바라보는'(감지하는) 방향. 출력은 그 반대편으로 나간다."""
    assert facing in OFFSET, facing
    return B("observer", facing=facing, powered="false")


def redstone_wire(east="none", west="none", north="none", south="none", power="0") -> Block:
    return B("redstone_wire", east=east, west=west, north=north, south=south, power=power)


def rail(shape: str = "east_west", powered: bool | None = None) -> Block:
    if powered is None:
        return B("rail", shape=shape, waterlogged="false")
    return B("powered_rail", shape=shape, powered=str(powered).lower(), waterlogged="false")


def hopper(facing: str = DOWN) -> Block:
    return B("hopper", facing=facing, enabled="true")


def chest(facing: str = NORTH) -> Block:
    return B("chest", facing=facing, type="single", waterlogged="false")


# --- ASCII 미리보기용 글자 --------------------------------------------------
PREVIEW_CHARS: dict[str, str] = {
    "air": ".", "stone": "#", "dirt": "d", "sand": "d", "mud": "m", "water": "~",
    "sugar_cane": "|", "piston": "P", "sticky_piston": "P", "observer": "O",
    "redstone_wire": "r", "redstone_block": "R", "rail": "=", "powered_rail": "+",
    "hopper": "h", "chest": "C", "glass": "g", "oak_slab": "s",
    "lava": "L", "cobblestone": "c", "smooth_stone": "S", "moss_block": "M",
    "composter": "K", "furnace": "F", "cobblestone_stairs": "<", "dispenser": "n",
    "kelp": "|", "oak_leaves": "V", "dropper": "D", "soul_sand": "$",
    "crafter": "X",
}


def preview_char(block: Block) -> str:
    return PREVIEW_CHARS.get(block.short, "?")
