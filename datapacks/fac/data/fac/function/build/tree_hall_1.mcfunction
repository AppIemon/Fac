# Tree Hall (tree_hall_1) fac:campus
execute in fac:campus run fill 192 64 32 211 64 59 minecraft:gray_concrete
execute in fac:campus run fill 192 65 32 211 83 59 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 192 64 32 192 83 32 minecraft:iron_block
execute in fac:campus run fill 211 64 32 211 83 32 minecraft:iron_block
execute in fac:campus run fill 192 64 59 192 83 59 minecraft:iron_block
execute in fac:campus run fill 211 64 59 211 83 59 minecraft:iron_block
execute in fac:campus run fill 192 83 32 211 83 59 minecraft:iron_block
execute in fac:campus run setblock 202 83 46 minecraft:sea_lantern
execute in fac:campus run setblock 202 65 46 minecraft:barrel[facing=up]
execute in fac:campus run setblock 203 65 46 minecraft:hopper[facing=west]
execute in fac:campus run fill 201 65 45 203 66 47 minecraft:oak_log replace minecraft:air
execute in fac:campus run setblock 202 65 46 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 202 67 46 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Tree Hall",color:"aqua"}}
