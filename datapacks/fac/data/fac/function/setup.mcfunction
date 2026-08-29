scoreboard players set $built fac_built 0
execute in fac:campus run forceload add 0 0 256 256
execute in fac:nether_works run forceload add 0 0 256 256
execute in fac:end_works run forceload add 0 0 256 256
execute in fac:void_stack run forceload add 0 0 256 256
function fac:build/dim_campus
function fac:build/dim_nether_works
function fac:build/dim_end_works
function fac:build/dim_void_stack
scoreboard players set $built fac_built 1
tellraw @a [{"text":"[Fac] ","color":"aqua"},{"text":"setup complete","color":"white"}]
