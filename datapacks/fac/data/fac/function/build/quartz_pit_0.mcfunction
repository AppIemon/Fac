# Quartz Pit (quartz_pit_0) fac:nether_works
execute in fac:nether_works run fill 96 64 0 111 64 15 minecraft:red_nether_bricks
execute in fac:nether_works run fill 96 65 0 111 79 15 minecraft:orange_stained_glass hollow
execute in fac:nether_works run fill 96 64 0 96 79 0 minecraft:gold_block
execute in fac:nether_works run fill 111 64 0 111 79 0 minecraft:gold_block
execute in fac:nether_works run fill 96 64 15 96 79 15 minecraft:gold_block
execute in fac:nether_works run fill 111 64 15 111 79 15 minecraft:gold_block
execute in fac:nether_works run fill 96 79 0 111 79 15 minecraft:gold_block
execute in fac:nether_works run setblock 104 79 8 minecraft:shroomlight
execute in fac:nether_works run setblock 104 65 8 minecraft:barrel[facing=up]
execute in fac:nether_works run setblock 105 65 8 minecraft:hopper[facing=west]
execute in fac:nether_works run fill 103 65 7 105 66 9 minecraft:nether_quartz_ore replace minecraft:air
execute in fac:nether_works run setblock 104 65 8 minecraft:barrel[facing=up]
execute in fac:nether_works run summon minecraft:armor_stand 104 67 8 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Quartz Pit",color:"aqua"}}
