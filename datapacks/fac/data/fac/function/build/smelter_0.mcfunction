# Super Smelter (smelter_0) fac:campus
execute in fac:campus run fill 224 64 0 239 64 23 minecraft:gray_concrete
execute in fac:campus run fill 224 65 0 239 75 23 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 224 64 0 224 75 0 minecraft:iron_block
execute in fac:campus run fill 239 64 0 239 75 0 minecraft:iron_block
execute in fac:campus run fill 224 64 23 224 75 23 minecraft:iron_block
execute in fac:campus run fill 239 64 23 239 75 23 minecraft:iron_block
execute in fac:campus run fill 224 75 0 239 75 23 minecraft:iron_block
execute in fac:campus run setblock 232 75 12 minecraft:sea_lantern
execute in fac:campus run setblock 232 65 12 minecraft:barrel[facing=up]
execute in fac:campus run setblock 233 65 12 minecraft:hopper[facing=west]
execute in fac:campus run fill 231 65 11 233 66 13 minecraft:blast_furnace replace minecraft:air
execute in fac:campus run setblock 232 65 12 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 232 67 12 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Super Smelter",color:"aqua"}}
