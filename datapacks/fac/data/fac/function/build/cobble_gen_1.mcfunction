# Cobble Gen (cobble_gen_1) fac:campus
execute in fac:campus run fill 0 64 32 11 64 43 minecraft:gray_concrete
execute in fac:campus run fill 0 65 32 11 71 43 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 0 64 32 0 71 32 minecraft:iron_block
execute in fac:campus run fill 11 64 32 11 71 32 minecraft:iron_block
execute in fac:campus run fill 0 64 43 0 71 43 minecraft:iron_block
execute in fac:campus run fill 11 64 43 11 71 43 minecraft:iron_block
execute in fac:campus run fill 0 71 32 11 71 43 minecraft:iron_block
execute in fac:campus run setblock 6 71 38 minecraft:sea_lantern
execute in fac:campus run setblock 6 65 38 minecraft:barrel[facing=up]
execute in fac:campus run setblock 7 65 38 minecraft:hopper[facing=west]
execute in fac:campus run fill 5 65 37 7 66 39 minecraft:cobblestone replace minecraft:air
execute in fac:campus run setblock 6 65 38 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 6 67 38 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Cobble Gen",color:"aqua"}}
