# Shulker Bay (shulker_bay_0) fac:end_works
execute in fac:end_works run fill 128 64 0 143 64 15 minecraft:purpur_block
execute in fac:end_works run fill 128 65 0 143 75 15 minecraft:purple_stained_glass hollow
execute in fac:end_works run fill 128 64 0 128 75 0 minecraft:end_stone_bricks
execute in fac:end_works run fill 143 64 0 143 75 0 minecraft:end_stone_bricks
execute in fac:end_works run fill 128 64 15 128 75 15 minecraft:end_stone_bricks
execute in fac:end_works run fill 143 64 15 143 75 15 minecraft:end_stone_bricks
execute in fac:end_works run fill 128 75 0 143 75 15 minecraft:end_stone_bricks
execute in fac:end_works run setblock 136 75 8 minecraft:end_rod
execute in fac:end_works run setblock 136 65 8 minecraft:barrel[facing=up]
execute in fac:end_works run setblock 137 65 8 minecraft:hopper[facing=west]
execute in fac:end_works run fill 135 65 7 137 66 9 minecraft:shulker_box replace minecraft:air
execute in fac:end_works run setblock 136 65 8 minecraft:barrel[facing=up]
execute in fac:end_works run summon minecraft:armor_stand 136 67 8 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Shulker Bay",color:"aqua"}}
execute in fac:end_works run summon minecraft:shulker 136 66 10 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Shell Keeper",color:"yellow"},Invulnerable:1b,NoAI:1b}
