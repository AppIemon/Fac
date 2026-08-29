# Portal Hub (portal_hub_3) fac:void_stack
execute in fac:void_stack run fill 0 64 0 15 64 15 minecraft:gray_concrete
execute in fac:void_stack run fill 0 65 0 15 75 15 minecraft:light_gray_stained_glass hollow
execute in fac:void_stack run fill 0 64 0 0 75 0 minecraft:iron_block
execute in fac:void_stack run fill 15 64 0 15 75 0 minecraft:iron_block
execute in fac:void_stack run fill 0 64 15 0 75 15 minecraft:iron_block
execute in fac:void_stack run fill 15 64 15 15 75 15 minecraft:iron_block
execute in fac:void_stack run fill 0 75 0 15 75 15 minecraft:iron_block
execute in fac:void_stack run setblock 8 75 8 minecraft:sea_lantern
execute in fac:void_stack run setblock 8 65 8 minecraft:barrel[facing=up]
execute in fac:void_stack run setblock 9 65 8 minecraft:hopper[facing=west]
execute in fac:void_stack run fill 7 65 7 9 66 9 minecraft:obsidian replace minecraft:air
execute in fac:void_stack run setblock 8 65 8 minecraft:barrel[facing=up]
execute in fac:void_stack run summon minecraft:armor_stand 8 67 8 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Portal Hub",color:"aqua"}}
execute in fac:void_stack run fill 6 65 8 9 69 8 minecraft:crying_obsidian
execute in fac:void_stack run fill 7 66 8 8 68 8 minecraft:air
