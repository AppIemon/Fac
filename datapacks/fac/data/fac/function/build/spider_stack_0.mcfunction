# Spider Stack (spider_stack_0) fac:void_stack
execute in fac:void_stack run fill 128 64 0 145 64 17 minecraft:black_concrete
execute in fac:void_stack run fill 128 65 0 145 99 17 minecraft:black_stained_glass hollow
execute in fac:void_stack run fill 128 64 0 128 99 0 minecraft:crying_obsidian
execute in fac:void_stack run fill 145 64 0 145 99 0 minecraft:crying_obsidian
execute in fac:void_stack run fill 128 64 17 128 99 17 minecraft:crying_obsidian
execute in fac:void_stack run fill 145 64 17 145 99 17 minecraft:crying_obsidian
execute in fac:void_stack run fill 128 99 0 145 99 17 minecraft:crying_obsidian
execute in fac:void_stack run setblock 137 99 9 minecraft:sculk_sensor
execute in fac:void_stack run setblock 137 65 9 minecraft:barrel[facing=up]
execute in fac:void_stack run setblock 138 65 9 minecraft:hopper[facing=west]
execute in fac:void_stack run fill 136 65 8 138 66 10 minecraft:cobweb replace minecraft:air
execute in fac:void_stack run setblock 137 65 9 minecraft:barrel[facing=up]
execute in fac:void_stack run summon minecraft:armor_stand 137 67 9 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Spider Stack",color:"aqua"}}
execute in fac:void_stack run summon minecraft:spider 137 66 11 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Spider Stock",color:"yellow"},Invulnerable:1b,NoAI:1b}
