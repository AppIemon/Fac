# Crop Tower (crop_tower_1) fac:campus
execute in fac:campus run fill 224 64 32 241 64 49 minecraft:gray_concrete
execute in fac:campus run fill 224 65 32 241 91 49 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 224 64 32 224 91 32 minecraft:iron_block
execute in fac:campus run fill 241 64 32 241 91 32 minecraft:iron_block
execute in fac:campus run fill 224 64 49 224 91 49 minecraft:iron_block
execute in fac:campus run fill 241 64 49 241 91 49 minecraft:iron_block
execute in fac:campus run fill 224 91 32 241 91 49 minecraft:iron_block
execute in fac:campus run setblock 233 91 41 minecraft:sea_lantern
execute in fac:campus run setblock 233 65 41 minecraft:barrel[facing=up]
execute in fac:campus run setblock 234 65 41 minecraft:hopper[facing=west]
execute in fac:campus run fill 232 65 40 234 66 42 minecraft:farmland replace minecraft:air
execute in fac:campus run setblock 233 65 41 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 233 67 41 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Crop Tower",color:"aqua"}}
execute in fac:campus run summon minecraft:villager 233 66 43 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Crop Farmer",color:"yellow"},Invulnerable:1b,NoAI:1b}
