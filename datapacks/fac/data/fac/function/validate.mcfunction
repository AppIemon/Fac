scoreboard players set $campus fac_ok 0
scoreboard players set $nether fac_ok 0
scoreboard players set $end fac_ok 0
scoreboard players set $void fac_ok 0
execute in fac:campus run scoreboard players set $campus fac_ok 1
execute in fac:nether_works run scoreboard players set $nether fac_ok 1
execute in fac:end_works run scoreboard players set $end fac_ok 1
execute in fac:void_stack run scoreboard players set $void fac_ok 1
scoreboard players set $ok fac_ok 1
execute unless score $campus fac_ok matches 1 run scoreboard players set $ok fac_ok 0
execute unless score $nether fac_ok matches 1 run scoreboard players set $ok fac_ok 0
execute unless score $end fac_ok matches 1 run scoreboard players set $ok fac_ok 0
execute unless score $void fac_ok matches 1 run scoreboard players set $ok fac_ok 0
tellraw @a [{"text":"[Fac] validate  campus="},{"score":{"name":"$campus","objective":"fac_ok"}},{"text":" nether="},{"score":{"name":"$nether","objective":"fac_ok"}},{"text":" end="},{"score":{"name":"$end","objective":"fac_ok"}},{"text":" void="},{"score":{"name":"$void","objective":"fac_ok"}},{"text":" ok="},{"score":{"name":"$ok","objective":"fac_ok"}}]
