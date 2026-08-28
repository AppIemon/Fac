# Pearl Drop (pearl_drop_0) fac:end_works
execute in fac:end_works run fill 96 64 0 115 64 19 minecraft:purpur_block
execute in fac:end_works run fill 96 65 0 115 103 19 minecraft:purple_stained_glass hollow
execute in fac:end_works run fill 96 64 0 96 103 0 minecraft:end_stone_bricks
execute in fac:end_works run fill 115 64 0 115 103 0 minecraft:end_stone_bricks
execute in fac:end_works run fill 96 64 19 96 103 19 minecraft:end_stone_bricks
execute in fac:end_works run fill 115 64 19 115 103 19 minecraft:end_stone_bricks
execute in fac:end_works run fill 96 103 0 115 103 19 minecraft:end_stone_bricks
execute in fac:end_works run setblock 106 103 10 minecraft:end_rod
execute in fac:end_works run setblock 106 65 10 minecraft:barrel[facing=up]
execute in fac:end_works run setblock 107 65 10 minecraft:hopper[facing=west]
execute in fac:end_works run fill 105 65 9 107 66 11 minecraft:end_stone_bricks replace minecraft:air
execute in fac:end_works run setblock 106 65 10 minecraft:barrel[facing=up]
execute in fac:end_works run summon minecraft:armor_stand 106 67 10 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Pearl Drop",color:"aqua"}}
execute in fac:end_works run summon minecraft:enderman 106 66 12 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Pearl Hunter",color:"yellow"},Invulnerable:1b,NoAI:1b}
