"""arma_soldier — tu spawnes EN SOLDAT juste derriere l'escouade, face a la colline, invulnerable (defenseurs
t'ignorent). Garnison + escouade + toi place derriere, puis l'assaut part en temps reel. Tu les suis a pied."""
import time, math
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (12000, 21000); R_SPAWN = 170.0; PLAYER_R = 205.0; SQ_N = 8; GARR_N = 5; K = 3


def setup(env, sx, sy, px, py, pdir):
    sqf = ('{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;\n'
           '{ if (({isPlayer _u} count units _x) == 0) then { deleteGroup _x } } forEach allGroups;\n'
           'SQ_ASSAUT=[]; HMT_EN=[]; west setFriend [east,0]; east setFriend [west,0];\n'
           'private _e0 = createGroup east;\n'
           'for "_a" from 0 to %d do {\n'
           '  _e0 createUnit ["O_Soldier_F", [%d + 7*(cos (360*_a/%d)), %d + 7*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
           '  private _u = (units _e0) select ((count (units _e0))-1);\n'
           '  _u setBehaviour "COMBAT"; _u setSkill 0.5; _u disableAI "PATH"; _u setUnitPos "AUTO"; _u setCombatMode "RED"; HMT_EN pushBack _u;\n};\n'
           'private _g0 = createGroup west;\n'
           'for "_a" from 0 to %d do {\n'
           '  private _ty = if (_a in [1,2]) then {"B_soldier_LAT_F"} else {"B_Soldier_F"};\n'
           '  _g0 createUnit [_ty, [%d + 9*(cos (360*_a/%d)), %d + 9*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
           '  private _u = (units _g0) select ((count (units _g0))-1);\n'
           '  _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u setSkill 0.5; _u allowFleeing 0; SQ_ASSAUT pushBack _u;\n};\n'
           '{ _x setPosATL [%d, %d, 0]; _x setDir %d; _x allowDamage false; _x setCaptive true; _x setUnitPos "UP"; } forEach allPlayers;\n'
           'setAccTime 1; diag_log "HARMATTAN_SOLDIER en place";\n'
           % (GARR_N - 1, OBJ[0], GARR_N, OBJ[1], GARR_N, SQ_N - 1, sx, SQ_N, sy, SQ_N, int(px), int(py), int(pdir)))
    env.b.send(sqf, wait=True); time.sleep(4.0)
    env.en_n = GARR_N; env.epx = np.zeros(GARR_N); env.epy = np.zeros(GARR_N); env.edmg = np.zeros(GARR_N)
    env.read()


def plan():
    return {"name": "ASSAUT-SOLDAT",
            "phases": [{"name": "APPROCHE", "orders": {"SQ_ASSAUT": (OBJ, "move")}, "done_when": ("any", [("squad_at", 0, OBJ, 55), ("steps", 70)])},
                       {"name": "ASSAUT", "orders": {"SQ_ASSAUT": (OBJ, "assault")}, "done_when": ("any", [("enemy_dead_frac", 0.8), ("steps", 130)])}],
            "success": ("enemy_dead_frac", 0.8)}


if __name__ == "__main__":
    import re
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env = OpArma(squads=(("SQ_ASSAUT", SQ_N),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", move=15, acc=1.0, seed=int(time.time()) % 1000)
    ls = env._query('diag_log format ["HARMATTAN_NP %1", count allPlayers];', settle=1.0)
    npl = next((int(m.group(1)) for l in ls for m in [re.search(r"HARMATTAN_NP (\d+)", l)] if m), 0)
    if npl == 0:
        print(">> Personne de connecte. Rejoins le slot WEST (127.0.0.1:2402, PAS de Y), puis redemande."); raise SystemExit
    th = math.radians(K * 45.0)
    sx, sy = OBJ[0] + R_SPAWN * math.cos(th), OBJ[1] + R_SPAWN * math.sin(th)
    px, py = OBJ[0] + PLAYER_R * math.cos(th), OBJ[1] + PLAYER_R * math.sin(th)
    pdir = (math.degrees(math.atan2(OBJ[0] - px, OBJ[1] - py))) % 360
    print(">> Tu es derriere l'escouade (8 hommes a 35 m devant toi), face a la colline. Invulnerable.", flush=True)
    print(">> Avance avec eux par le defile. L'assaut part maintenant...", flush=True)
    setup(env, sx, sy, px, py, pdir)
    runner = OperationRunner(env, brain, plan(), log_path="/dev/null", verbose=True)
    ok = runner.run(max_steps=210, max_wall=700, stall_wall=300)
    print("\n>> Objectif %s | escouade %d/%d vivants | defenseurs restants %d/%d"
          % ("PRIS" if ok else "non pris", int(env.alive(0).sum()), SQ_N, int(env.en_alive().sum()), GARR_N), flush=True)
