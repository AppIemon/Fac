# Iron Foundry (iron_foundry_3) fac:campus
execute in fac:campus run fill 160 64 32 181 64 53 minecraft:gray_concrete
execute in fac:campus run fill 160 65 32 181 79 53 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 160 64 32 160 79 32 minecraft:iron_block
execute in fac:campus run fill 181 64 32 181 79 32 minecraft:iron_block
execute in fac:campus run fill 160 64 53 160 79 53 minecraft:iron_block
execute in fac:campus run fill 181 64 53 181 79 53 minecraft:iron_block
execute in fac:campus run fill 160 79 32 181 79 53 minecraft:iron_block
execute in fac:campus run setblock 171 79 43 minecraft:sea_lantern
execute in fac:campus run setblock 171 65 43 minecraft:barrel[facing=up]
execute in fac:campus run setblock 172 65 43 minecraft:hopper[facing=west]
execute in fac:campus run fill 170 65 42 172 66 44 minecraft:iron_block replace minecraft:air
execute in fac:campus run setblock 171 65 43 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 171 67 43 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Iron Foundry",color:"aqua"}}
execute in fac:campus run summon minecraft:iron_golem 171 66 45 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Guard Golem",color:"yellow"},Invulnerable:1b,NoAI:1b}
