# Iron Foundry (iron_foundry_2) fac:campus
execute in fac:campus run fill 128 64 32 149 64 53 minecraft:gray_concrete
execute in fac:campus run fill 128 65 32 149 79 53 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 128 64 32 128 79 32 minecraft:iron_block
execute in fac:campus run fill 149 64 32 149 79 32 minecraft:iron_block
execute in fac:campus run fill 128 64 53 128 79 53 minecraft:iron_block
execute in fac:campus run fill 149 64 53 149 79 53 minecraft:iron_block
execute in fac:campus run fill 128 79 32 149 79 53 minecraft:iron_block
execute in fac:campus run setblock 139 79 43 minecraft:sea_lantern
execute in fac:campus run setblock 139 65 43 minecraft:barrel[facing=up]
execute in fac:campus run setblock 140 65 43 minecraft:hopper[facing=west]
execute in fac:campus run fill 138 65 42 140 66 44 minecraft:iron_block replace minecraft:air
execute in fac:campus run setblock 139 65 43 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 139 67 43 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Iron Foundry",color:"aqua"}}
execute in fac:campus run summon minecraft:iron_golem 139 66 45 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Guard Golem",color:"yellow"},Invulnerable:1b,NoAI:1b}
