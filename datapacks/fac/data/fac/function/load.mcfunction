gamerule commandBlockOutput false
gamerule logAdminCommands false
gamerule announceAdvancements false
gamerule keepInventory true
gamerule doImmediateRespawn true
gamerule sendCommandFeedback true
difficulty easy
scoreboard objectives add fac_ok dummy
scoreboard objectives add fac_tick dummy
scoreboard objectives add fac_built dummy
scoreboard players set $modules fac_ok 30
tellraw @a [{"text":"[Fac] ","color":"aqua"},{"text":"공장 월드 로드됨. 크리에이티브에서 /function fac:setup 으로 모듈을 짓고 /function fac:validate 로 차원을 점검하세요.","color":"white"}]
