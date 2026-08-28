# Chunk Anchor (chunk_anchor_0) fac:campus
execute in fac:campus run fill 96 64 0 103 64 7 minecraft:gray_concrete
execute in fac:campus run fill 96 65 0 103 71 7 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 96 64 0 96 71 0 minecraft:iron_block
execute in fac:campus run fill 103 64 0 103 71 0 minecraft:iron_block
execute in fac:campus run fill 96 64 7 96 71 7 minecraft:iron_block
execute in fac:campus run fill 103 64 7 103 71 7 minecraft:iron_block
execute in fac:campus run fill 96 71 0 103 71 7 minecraft:iron_block
execute in fac:campus run setblock 100 71 4 minecraft:sea_lantern
execute in fac:campus run setblock 100 65 4 minecraft:barrel[facing=up]
execute in fac:campus run setblock 101 65 4 minecraft:hopper[facing=west]
execute in fac:campus run fill 99 65 3 101 66 5 minecraft:respawn_anchor replace minecraft:air
execute in fac:campus run setblock 100 65 4 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 100 67 4 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Chunk Anchor",color:"aqua"}}
execute in fac:campus run forceload add 96 0 103 7
execute in fac:campus run setblock 100 65 4 minecraft:lodestone
