# Cobble Gen (cobble_gen_0) fac:campus
execute in fac:campus run fill 128 64 0 139 64 11 minecraft:gray_concrete
execute in fac:campus run fill 128 65 0 139 71 11 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 128 64 0 128 71 0 minecraft:iron_block
execute in fac:campus run fill 139 64 0 139 71 0 minecraft:iron_block
execute in fac:campus run fill 128 64 11 128 71 11 minecraft:iron_block
execute in fac:campus run fill 139 64 11 139 71 11 minecraft:iron_block
execute in fac:campus run fill 128 71 0 139 71 11 minecraft:iron_block
execute in fac:campus run setblock 134 71 6 minecraft:sea_lantern
execute in fac:campus run setblock 134 65 6 minecraft:barrel[facing=up]
execute in fac:campus run setblock 135 65 6 minecraft:hopper[facing=west]
execute in fac:campus run fill 133 65 5 135 66 7 minecraft:cobblestone replace minecraft:air
execute in fac:campus run setblock 134 65 6 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 134 67 6 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Cobble Gen",color:"aqua"}}
