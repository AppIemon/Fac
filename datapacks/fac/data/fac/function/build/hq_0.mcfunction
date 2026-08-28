# HQ (hq_0) fac:campus
execute in fac:campus run fill 0 64 0 19 64 19 minecraft:gray_concrete
execute in fac:campus run fill 0 65 0 19 87 19 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 0 64 0 0 87 0 minecraft:iron_block
execute in fac:campus run fill 19 64 0 19 87 0 minecraft:iron_block
execute in fac:campus run fill 0 64 19 0 87 19 minecraft:iron_block
execute in fac:campus run fill 19 64 19 19 87 19 minecraft:iron_block
execute in fac:campus run fill 0 87 0 19 87 19 minecraft:iron_block
execute in fac:campus run setblock 10 87 10 minecraft:sea_lantern
execute in fac:campus run setblock 10 65 10 minecraft:barrel[facing=up]
execute in fac:campus run setblock 11 65 10 minecraft:hopper[facing=west]
execute in fac:campus run fill 9 65 9 11 66 11 minecraft:iron_block replace minecraft:air
execute in fac:campus run setblock 10 65 10 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 10 67 10 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"HQ",color:"aqua"}}
execute in fac:campus run summon minecraft:villager 10 66 12 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Foreman",color:"yellow"},Invulnerable:1b,NoAI:1b}
execute in fac:campus run summon minecraft:iron_golem 10 66 12 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Guard Golem",color:"yellow"},Invulnerable:1b,NoAI:1b}
