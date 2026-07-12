"""deplace le curator (Zeus) du joueur sur l'objectif pour que la camera puisse y aller."""
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = ('{ _x allowDamage false; '
       'private _c = getAssignedCuratorLogic _x; '
       'if (!isNull _c) then { '
       '  _c setPosATL [12000, 21000, 60]; '
       '  _c addCuratorEditableObjects [allUnits, true]; '
       '  _c setVariable ["area", [[12000,21000,0], [40000,40000], 0, false, -1], true]; '
       '}; } forEach allPlayers; '
       'diag_log "HARMATTAN_MOVECUR curator sur objectif";')
env.b.send(sqf, wait=True)
print("Curator deplace sur l'objectif (12000,21000) + zone d'edition agrandie.")
print("-> Dans Arma : ferme Zeus (Y), rouvre Zeus (Y). La camera doit etre sur la colline.")
