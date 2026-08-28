# Tree Hall (tree_hall_0) fac:campus
execute in fac:campus run fill 192 64 0 211 64 27 minecraft:gray_concrete
execute in fac:campus run fill 192 65 0 211 83 27 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 192 64 0 192 83 0 minecraft:iron_block
execute in fac:campus run fill 211 64 0 211 83 0 minecraft:iron_block
execute in fac:campus run fill 192 64 27 192 83 27 minecraft:iron_block
execute in fac:campus run fill 211 64 27 211 83 27 minecraft:iron_block
execute in fac:campus run fill 192 83 0 211 83 27 minecraft:iron_block
execute in fac:campus run setblock 202 83 14 minecraft:sea_lantern
execute in fac:campus run setblock 202 65 14 minecraft:barrel[facing=up]
execute in fac:campus run setblock 203 65 14 minecraft:hopper[facing=west]
execute in fac:campus run fill 201 65 13 203 66 15 minecraft:oak_log replace minecraft:air
execute in fac:campus run setblock 202 65 14 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 202 67 14 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Tree Hall",color:"aqua"}}
