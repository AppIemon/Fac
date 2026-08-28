# Cow Cooker (cow_cooker_0) fac:campus
execute in fac:campus run fill 96 64 32 111 64 47 minecraft:gray_concrete
execute in fac:campus run fill 96 65 32 111 75 47 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 96 64 32 96 75 32 minecraft:iron_block
execute in fac:campus run fill 111 64 32 111 75 32 minecraft:iron_block
execute in fac:campus run fill 96 64 47 96 75 47 minecraft:iron_block
execute in fac:campus run fill 111 64 47 111 75 47 minecraft:iron_block
execute in fac:campus run fill 96 75 32 111 75 47 minecraft:iron_block
execute in fac:campus run setblock 104 75 40 minecraft:sea_lantern
execute in fac:campus run setblock 104 65 40 minecraft:barrel[facing=up]
execute in fac:campus run setblock 105 65 40 minecraft:hopper[facing=west]
execute in fac:campus run fill 103 65 39 105 66 41 minecraft:farmland replace minecraft:air
execute in fac:campus run setblock 104 65 40 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 104 67 40 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Cow Cooker",color:"aqua"}}
