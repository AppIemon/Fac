# Creeper Stack (creeper_stack_0) fac:void_stack
execute in fac:void_stack run fill 96 64 0 115 64 19 minecraft:black_concrete
execute in fac:void_stack run fill 96 65 0 115 111 19 minecraft:black_stained_glass hollow
execute in fac:void_stack run fill 96 64 0 96 111 0 minecraft:crying_obsidian
execute in fac:void_stack run fill 115 64 0 115 111 0 minecraft:crying_obsidian
execute in fac:void_stack run fill 96 64 19 96 111 19 minecraft:crying_obsidian
execute in fac:void_stack run fill 115 64 19 115 111 19 minecraft:crying_obsidian
execute in fac:void_stack run fill 96 111 0 115 111 19 minecraft:crying_obsidian
execute in fac:void_stack run setblock 106 111 10 minecraft:sculk_sensor
execute in fac:void_stack run setblock 106 65 10 minecraft:barrel[facing=up]
execute in fac:void_stack run setblock 107 65 10 minecraft:hopper[facing=west]
execute in fac:void_stack run fill 105 65 9 107 66 11 minecraft:moss_block replace minecraft:air
execute in fac:void_stack run setblock 106 65 10 minecraft:barrel[facing=up]
execute in fac:void_stack run summon minecraft:armor_stand 106 67 10 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Creeper Stack",color:"aqua"}}
execute in fac:void_stack run summon minecraft:creeper 106 66 12 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Creeper Stock",color:"yellow"},Invulnerable:1b,NoAI:1b}
