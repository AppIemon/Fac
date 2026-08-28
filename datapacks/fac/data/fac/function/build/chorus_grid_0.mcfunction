# Chorus Grid (chorus_grid_0) fac:end_works
execute in fac:end_works run fill 64 64 0 87 64 23 minecraft:purpur_block
execute in fac:end_works run fill 64 65 0 87 85 23 minecraft:purple_stained_glass hollow
execute in fac:end_works run fill 64 64 0 64 85 0 minecraft:end_stone_bricks
execute in fac:end_works run fill 87 64 0 87 85 0 minecraft:end_stone_bricks
execute in fac:end_works run fill 64 64 23 64 85 23 minecraft:end_stone_bricks
execute in fac:end_works run fill 87 64 23 87 85 23 minecraft:end_stone_bricks
execute in fac:end_works run fill 64 85 0 87 85 23 minecraft:end_stone_bricks
execute in fac:end_works run setblock 76 85 12 minecraft:end_rod
execute in fac:end_works run setblock 76 65 12 minecraft:barrel[facing=up]
execute in fac:end_works run setblock 77 65 12 minecraft:hopper[facing=west]
execute in fac:end_works run fill 75 65 11 77 66 13 minecraft:chorus_flower replace minecraft:air
execute in fac:end_works run setblock 76 65 12 minecraft:barrel[facing=up]
execute in fac:end_works run summon minecraft:armor_stand 76 67 12 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Chorus Grid",color:"aqua"}}
