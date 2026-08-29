# Gold Hall (gold_hall_0) fac:nether_works
execute in fac:nether_works run fill 64 64 0 91 64 27 minecraft:red_nether_bricks
execute in fac:nether_works run fill 64 65 0 91 87 27 minecraft:orange_stained_glass hollow
execute in fac:nether_works run fill 64 64 0 64 87 0 minecraft:gold_block
execute in fac:nether_works run fill 91 64 0 91 87 0 minecraft:gold_block
execute in fac:nether_works run fill 64 64 27 64 87 27 minecraft:gold_block
execute in fac:nether_works run fill 91 64 27 91 87 27 minecraft:gold_block
execute in fac:nether_works run fill 64 87 0 91 87 27 minecraft:gold_block
execute in fac:nether_works run setblock 78 87 14 minecraft:shroomlight
execute in fac:nether_works run setblock 78 65 14 minecraft:barrel[facing=up]
execute in fac:nether_works run setblock 79 65 14 minecraft:hopper[facing=west]
execute in fac:nether_works run fill 77 65 13 79 66 15 minecraft:gold_block replace minecraft:air
execute in fac:nether_works run setblock 78 65 14 minecraft:barrel[facing=up]
execute in fac:nether_works run summon minecraft:armor_stand 78 67 14 {Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,CustomNameVisible:1b,CustomName:{text:"Gold Hall",color:"aqua"}}
execute in fac:nether_works run summon minecraft:piglin 78 66 16 {PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"Barterer",color:"yellow"},Invulnerable:1b,NoAI:1b}
