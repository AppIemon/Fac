# Portal Hub (portal_hub_0) fac:campus
execute in fac:campus run fill 64 64 0 79 64 15 minecraft:gray_concrete
execute in fac:campus run fill 64 65 0 79 75 15 minecraft:light_gray_stained_glass hollow
execute in fac:campus run fill 64 64 0 64 75 0 minecraft:iron_block
execute in fac:campus run fill 79 64 0 79 75 0 minecraft:iron_block
execute in fac:campus run fill 64 64 15 64 75 15 minecraft:iron_block
execute in fac:campus run fill 79 64 15 79 75 15 minecraft:iron_block
execute in fac:campus run fill 64 75 0 79 75 15 minecraft:iron_block
execute in fac:campus run setblock 72 75 8 minecraft:sea_lantern
execute in fac:campus run setblock 72 65 8 minecraft:barrel[facing=up]
execute in fac:campus run setblock 73 65 8 minecraft:hopper[facing=west]
execute in fac:campus run fill 71 65 7 73 66 9 minecraft:obsidian replace minecraft:air
execute in fac:campus run setblock 72 65 8 minecraft:barrel[facing=up]
execute in fac:campus run summon minecraft:armor_stand 72 67 8 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Portal Hub",color:"aqua"}}
execute in fac:campus run fill 70 65 4 73 69 4 minecraft:obsidian
execute in fac:campus run fill 71 66 4 72 68 4 minecraft:air
execute in fac:campus run fill 70 65 12 74 65 12 minecraft:end_portal_frame[facing=south]
