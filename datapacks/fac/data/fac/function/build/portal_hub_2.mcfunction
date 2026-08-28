# Portal Hub (portal_hub_2) fac:end_works
execute in fac:end_works run fill 0 64 0 15 64 15 minecraft:gray_concrete
execute in fac:end_works run fill 0 65 0 15 75 15 minecraft:light_gray_stained_glass hollow
execute in fac:end_works run fill 0 64 0 0 75 0 minecraft:iron_block
execute in fac:end_works run fill 15 64 0 15 75 0 minecraft:iron_block
execute in fac:end_works run fill 0 64 15 0 75 15 minecraft:iron_block
execute in fac:end_works run fill 15 64 15 15 75 15 minecraft:iron_block
execute in fac:end_works run fill 0 75 0 15 75 15 minecraft:iron_block
execute in fac:end_works run setblock 8 75 8 minecraft:sea_lantern
execute in fac:end_works run setblock 8 65 8 minecraft:barrel[facing=up]
execute in fac:end_works run setblock 9 65 8 minecraft:hopper[facing=west]
execute in fac:end_works run fill 7 65 7 9 66 9 minecraft:obsidian replace minecraft:air
execute in fac:end_works run setblock 8 65 8 minecraft:barrel[facing=up]
execute in fac:end_works run summon minecraft:armor_stand 8 67 8 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Portal Hub",color:"aqua"}}
execute in fac:end_works run fill 7 65 7 9 65 9 minecraft:end_portal_frame
