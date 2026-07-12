"""arma_landdemo — garnison sur le VRAI objectif terre COMPLEXE=(15000,16000) (eprouve par les missions §4.7)
+ deplace la camera Zeus du joueur dessus. Pas encore l'escouade : on confirme d'abord que tu vois la terre."""
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
OBJ = (15000, 16000); GARR_N = 5

SQF = (
    '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;\n'
    '{ if (({isPlayer _u} count units _x) == 0) then { deleteGroup _x } } forEach allGroups;\n'
    'HMT_EN=[]; west setFriend [east,0]; east setFriend [west,0];\n'
    'private _e0 = createGroup east;\n'
    'for "_a" from 0 to ' + str(GARR_N - 1) + ' do {\n'
    '  _e0 createUnit ["O_Soldier_F", [' + str(OBJ[0]) + ' + 8*(cos (360*_a/' + str(GARR_N) + ')), ' + str(OBJ[1]) + ' + 8*(sin (360*_a/' + str(GARR_N) + ')), 0], [], 0, "FORM"];\n'
    '  private _u = (units _e0) select ((count (units _e0))-1);\n'
    '  _u setBehaviour "COMBAT"; _u setSkill 0.5; _u disableAI "PATH"; _u setUnitPos "UP"; _u setCombatMode "RED"; HMT_EN pushBack _u;\n};\n'
    '{ _x allowDamage false; private _c = getAssignedCuratorLogic _x;\n'
    '  if (!isNull _c) then { _c setPosATL [' + str(OBJ[0]) + ', ' + str(OBJ[1]) + ', 60]; _c addCuratorEditableObjects [allUnits, true];\n'
    '    _c setVariable ["area", [[' + str(OBJ[0]) + ',' + str(OBJ[1]) + ',0], [40000,40000], 0, false, -1], true]; };\n'
    '} forEach allPlayers;\n'
    'diag_log "HARMATTAN_LANDDEMO garnison sur COMPLEXE + camera deplacee";\n'
)

if __name__ == "__main__":
    env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    env.b.send(SQF, wait=True)
    print("Garnison (5) posee sur COMPLEXE (15000,16000) = vraie terre eprouvee. Camera Zeus deplacee dessus.")
    print("-> Dans Arma : ferme Zeus (Y), rouvre (Y). Tu dois voir 5 defenseurs sur de la TERRE.")
