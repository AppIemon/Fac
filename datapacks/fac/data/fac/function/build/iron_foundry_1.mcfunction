# Iron Foundry (iron_foundry_1) fac:campus
execute in fac:campus run fill 64 64 32 85 64 53 minecraft:gray_concrete
execute in fac:campus run fill 64 65 32 85 79 53 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 64 64 32 64 79 32 minecraft:iron_block
execute in fac:campus run fill 85 64 32 85 79 32 minecraft:iron_block
execute in fac:campus run fill 64 64 53 64 79 53 minecraft:iron_block
execute in fac:campus run fill 85 64 53 85 79 53 minecraft:iron_block
execute in fac:campus run fill 64 79 32 85 79 53 minecraft:iron_block
execute in fac:campus run setblock 75 79 43 minecraft:sea_lantern
execute in fac:campus run setblock 75 65 43 minecraft:barrel[facing=up]
execute in fac:campus run setblock 76 65 43 minecraft:hopper[facing=west]
execute in fac:campus run fill 74 65 42 76 66 44 minecraft:iron_block replace minecraft:air
execute in fac:campus run setblock 75 65 43 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 75 67 43 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Iron Foundry",color:"aqua"}}
execute in fac:campus run summon minecraft:iron_golem 75 66 45 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Guard Golem",color:"yellow"},Invulnerable:1b,NoAI:1b}
