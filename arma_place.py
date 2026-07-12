"""arma_place — place la GARNISON sur la colline et positionne le JOUEUR (Zeus) juste au-dessus, en securite.
A lancer quand tu es connecte. Ne spawn PAS encore l'escouade (ca, c'est l'assaut, sur ton 'go')."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
OBJ = (12000, 21000); GARR_N = 5

PLACE = (
    '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;\n'
    '{ if (({isPlayer _u} count units _x) == 0) then { deleteGroup _x } } forEach allGroups;\n'
    'HMT_EN=[]; west setFriend [east,0]; east setFriend [west,0];\n'
    'private _e0 = createGroup east;\n'
    'for "_a" from 0 to %d do {\n'
    '  _e0 createUnit ["O_Soldier_F", [%d + 7*(cos (360*_a/%d)), %d + 7*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
    '  private _u = (units _e0) select ((count (units _e0))-1);\n'
    '  _u setBehaviour "COMBAT"; _u setSkill 0.5; _u disableAI "PATH"; _u setUnitPos "AUTO"; _u setCombatMode "RED"; HMT_EN pushBack _u;\n};\n'
    '{ _x allowDamage false; _x setCaptive true; _x setPosATL [%d, %d, 0]; } forEach allPlayers;\n'
    'if (!isNil "HMT_CUR") then { HMT_CUR addCuratorEditableObjects [allUnits, true]; };\n'
    'diag_log "HARMATTAN_PLACE garnison posee + joueur au-dessus";\n'
    % (GARR_N - 1, OBJ[0], GARR_N, OBJ[1], GARR_N, OBJ[0], OBJ[1])
)

if __name__ == "__main__":
    env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    ls = env._query('diag_log format ["HARMATTAN_NP %1", count allPlayers];', settle=1.0)
    npl = 0
    for l in ls:
        m = re.search(r"HARMATTAN_NP (\d+)", l)
        if m: npl = int(m.group(1))
    print("joueurs connectes :", npl)
    if npl == 0:
        print(">> Personne de connecte. Rejoins le slot WEST (127.0.0.1:2402), puis redemande.")
    else:
        env.b.send(PLACE, wait=True)
        print(">> Garnison (5) posee sur la colline (12000,21000). Tu es positionne juste au-dessus, invulnerable.")
        print(">> Appuie sur Y : Zeus s'ouvre au-dessus des defenseurs. Dis 'go' pour lancer l'assaut.")
