# Crop Tower (crop_tower_0) fac:campus
execute in fac:campus run fill 160 64 0 177 64 17 minecraft:gray_concrete
execute in fac:campus run fill 160 65 0 177 91 17 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 160 64 0 160 91 0 minecraft:iron_block
execute in fac:campus run fill 177 64 0 177 91 0 minecraft:iron_block
execute in fac:campus run fill 160 64 17 160 91 17 minecraft:iron_block
execute in fac:campus run fill 177 64 17 177 91 17 minecraft:iron_block
execute in fac:campus run fill 160 91 0 177 91 17 minecraft:iron_block
execute in fac:campus run setblock 169 91 9 minecraft:sea_lantern
execute in fac:campus run setblock 169 65 9 minecraft:barrel[facing=up]
execute in fac:campus run setblock 170 65 9 minecraft:hopper[facing=west]
execute in fac:campus run fill 168 65 8 170 66 10 minecraft:farmland replace minecraft:air
execute in fac:campus run setblock 169 65 9 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 169 67 9 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Crop Tower",color:"aqua"}}
execute in fac:campus run summon minecraft:villager 169 66 11 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Crop Farmer",color:"yellow"},Invulnerable:1b,NoAI:1b}
