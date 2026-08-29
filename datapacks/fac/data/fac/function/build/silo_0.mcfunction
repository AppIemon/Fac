# Silo (silo_0) fac:campus
execute in fac:campus run fill 32 64 0 55 64 23 minecraft:gray_concrete
execute in fac:campus run fill 32 65 0 55 95 23 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 32 64 0 32 95 0 minecraft:iron_block
execute in fac:campus run fill 55 64 0 55 95 0 minecraft:iron_block
execute in fac:campus run fill 32 64 23 32 95 23 minecraft:iron_block
execute in fac:campus run fill 55 64 23 55 95 23 minecraft:iron_block
execute in fac:campus run fill 32 95 0 55 95 23 minecraft:iron_block
execute in fac:campus run setblock 44 95 12 minecraft:sea_lantern
execute in fac:campus run setblock 44 65 12 minecraft:barrel[facing=up]
execute in fac:campus run setblock 45 65 12 minecraft:hopper[facing=west]
execute in fac:campus run fill 43 65 11 45 66 13 minecraft:barrel replace minecraft:air
execute in fac:campus run setblock 44 65 12 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 44 67 12 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Silo",color:"aqua"}}
execute in fac:campus run summon minecraft:allay 44 66 14 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Hauler Allay",color:"yellow"},Invulnerable:1b,NoAI:1b}
