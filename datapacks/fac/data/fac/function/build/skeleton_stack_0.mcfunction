# Skeleton Stack (skeleton_stack_0) fac:void_stack
execute in fac:void_stack run fill 64 64 0 83 64 19 minecraft:black_concrete
execute in fac:void_stack run fill 64 65 0 83 111 19 minecraft:black_stained_glass hollow
execute in fac:void_stack run fill 64 64 0 64 111 0 minecraft:crying_obsidian
execute in fac:void_stack run fill 83 64 0 83 111 0 minecraft:crying_obsidian
execute in fac:void_stack run fill 64 64 19 64 111 19 minecraft:crying_obsidian
execute in fac:void_stack run fill 83 64 19 83 111 19 minecraft:crying_obsidian
execute in fac:void_stack run fill 64 111 0 83 111 19 minecraft:crying_obsidian
execute in fac:void_stack run setblock 74 111 10 minecraft:sculk_sensor
execute in fac:void_stack run setblock 74 65 10 minecraft:barrel[facing=up]
execute in fac:void_stack run setblock 75 65 10 minecraft:hopper[facing=west]
execute in fac:void_stack run fill 73 65 9 75 66 11 minecraft:bone_block replace minecraft:air
execute in fac:void_stack run setblock 74 65 10 minecraft:barrel[facing=up]
execute in fac:void_stack run summon minecraft:armor_stand 74 67 10 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Skeleton Stack",color:"aqua"}}
execute in fac:void_stack run summon minecraft:skeleton 74 66 12 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Skeleton Stock",color:"yellow"},Invulnerable:1b,NoAI:1b}
