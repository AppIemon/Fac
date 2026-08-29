# Chunk Anchor (chunk_anchor_3) fac:void_stack
execute in fac:void_stack run fill 32 64 0 39 64 7 minecraft:gray_concrete
execute in fac:void_stack run fill 32 65 0 39 71 7 minecraft:light_gray_stained_glass hollow
execute in fac:void_stack run fill 32 64 0 32 71 0 minecraft:iron_block
execute in fac:void_stack run fill 39 64 0 39 71 0 minecraft:iron_block
execute in fac:void_stack run fill 32 64 7 32 71 7 minecraft:iron_block
execute in fac:void_stack run fill 39 64 7 39 71 7 minecraft:iron_block
execute in fac:void_stack run fill 32 71 0 39 71 7 minecraft:iron_block
execute in fac:void_stack run setblock 36 71 4 minecraft:sea_lantern
execute in fac:void_stack run setblock 36 65 4 minecraft:barrel[facing=up]
execute in fac:void_stack run setblock 37 65 4 minecraft:hopper[facing=west]
execute in fac:void_stack run fill 35 65 3 37 66 5 minecraft:respawn_anchor replace minecraft:air
execute in fac:void_stack run setblock 36 65 4 minecraft:barrel[facing=up]
execute in fac:void_stack run summon minecraft:armor_stand 36 67 4 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Chunk Anchor",color:"aqua"}}
execute in fac:void_stack run forceload add 32 0 39 7
execute in fac:void_stack run setblock 36 65 4 minecraft:lodestone
