# Iron Foundry (iron_foundry_0) fac:campus
execute in fac:campus run fill 32 64 32 53 64 53 minecraft:gray_concrete
execute in fac:campus run fill 32 65 32 53 79 53 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 32 64 32 32 79 32 minecraft:iron_block
execute in fac:campus run fill 53 64 32 53 79 32 minecraft:iron_block
execute in fac:campus run fill 32 64 53 32 79 53 minecraft:iron_block
execute in fac:campus run fill 53 64 53 53 79 53 minecraft:iron_block
execute in fac:campus run fill 32 79 32 53 79 53 minecraft:iron_block
execute in fac:campus run setblock 43 79 43 minecraft:sea_lantern
execute in fac:campus run setblock 43 65 43 minecraft:barrel[facing=up]
execute in fac:campus run setblock 44 65 43 minecraft:hopper[facing=west]
execute in fac:campus run fill 42 65 42 44 66 44 minecraft:iron_block replace minecraft:air
execute in fac:campus run setblock 43 65 43 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 43 67 43 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Iron Foundry",color:"aqua"}}
execute in fac:campus run summon minecraft:iron_golem 43 66 45 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Guard Golem",color:"yellow"},Invulnerable:1b,NoAI:1b}
