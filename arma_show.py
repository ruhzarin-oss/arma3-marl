"""arma_show — opration VISUELLE sur server0 : spawn qui EPARGNE le joueur (Zeus), temps reel (acc=1).
L'officier choisit le defile, l'escouade assaut depuis cet axe, tu regardes a la camera Zeus. On declenche
ca quand tu es connecte et en Zeus."""
import time, math, re
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (12000, 21000); R_SPAWN = 170.0; SQ_N = 8; GARR_N = 5; DEFILE_K = 3  # Sud-Est = le defile pour cet objectif
NPATH = 12


def expo_sqf(ox, oy):
    return ('HMT_OX=%d; HMT_OY=%d; HMT_DEF=[]; { HMT_DEF pushBack [HMT_OX+12*cos _x, HMT_OY+12*sin _x] } forEach [0,90,180,270];\n'
            'for "_k" from 0 to 7 do { private _th=_k*45; private _sx=HMT_OX+%f*cos _th; private _sy=HMT_OY+%f*sin _th; private _seen=0;\n'
            '  for "_i" from 1 to %d do { private _t=_i/%d; private _px=_sx+(HMT_OX-_sx)*_t; private _py=_sy+(HMT_OY-_sy)*_t;\n'
            '    private _pz=(getTerrainHeightASL [_px,_py])+1.5; private _vis=false;\n'
            '    { private _dz=(getTerrainHeightASL [_x#0,_x#1])+1.5; if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis=true }; } forEach HMT_DEF;\n'
            '    if (_vis) then { _seen=_seen+1 }; };\n'
            '  diag_log format ["HARMATTAN_EXPO %%1 %%2", _k, round (100*_seen/%d)]; };\n' % (ox, oy, R_SPAWN, R_SPAWN, NPATH, NPATH, NPATH))


def spawn_visual(env, foot, kbear):
    """Cleanup qui EPARGNE le joueur + le curator, spawn escouade (au cap) + garnison (a l'objectif), temps reel."""
    x, y = foot; gx, gy = OBJ
    sqf = ('{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;\n'
           '{ if (({isPlayer _u} count units _x) == 0) then { deleteGroup _x } } forEach allGroups;\n'
           'SQ_ASSAUT=[]; HMT_EN=[]; west setFriend [east,0]; east setFriend [west,0];\n'
           'private _g0 = createGroup west;\n'
           'for "_a" from 0 to %d do {\n'
           '  private _ty = if (_a in [1,2]) then {"B_soldier_LAT_F"} else {"B_Soldier_F"};\n'
           '  _g0 createUnit [_ty, [%d + 9*(cos (360*_a/%d)), %d + 9*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
           '  private _u = (units _g0) select ((count (units _g0))-1);\n'
           '  _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u setSkill 0.5; _u allowFleeing 0; SQ_ASSAUT pushBack _u;\n};\n'
           'private _e0 = createGroup east;\n'
           'for "_a" from 0 to %d do {\n'
           '  _e0 createUnit ["O_Soldier_F", [%d + 7*(cos (360*_a/%d)), %d + 7*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
           '  private _u = (units _e0) select ((count (units _e0))-1);\n'
           '  _u setBehaviour "COMBAT"; _u setSkill 0.5; _u allowFleeing 0; _u disableAI "PATH"; _u setUnitPos "AUTO"; _u setCombatMode "RED"; HMT_EN pushBack _u;\n};\n'
           'if (!isNil "HMT_CUR") then { HMT_CUR addCuratorEditableObjects [allUnits, true]; };\n'
           'setAccTime 1; diag_log "HARMATTAN_OPSPAWN";\n'
           % (SQ_N - 1, x, SQ_N, y, SQ_N, GARR_N - 1, gx, GARR_N, gy, GARR_N))
    env.b.send(sqf, wait=True); time.sleep(5.0)
    env.en_n = GARR_N; env.epx = np.zeros(GARR_N); env.epy = np.zeros(GARR_N); env.edmg = np.zeros(GARR_N)
    env.read()


def plan():
    return {"name": "DEMO-DEFILE",
            "phases": [{"name": "APPROCHE", "orders": {"SQ_ASSAUT": (OBJ, "move")}, "done_when": ("any", [("squad_at", 0, OBJ, 55), ("steps", 60)])},
                       {"name": "ASSAUT", "orders": {"SQ_ASSAUT": (OBJ, "assault")}, "done_when": ("any", [("enemy_dead_frac", 0.8), ("steps", 120)])}],
            "success": ("enemy_dead_frac", 0.8)}


if __name__ == "__main__":
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env = OpArma(squads=(("SQ_ASSAUT", SQ_N),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", move=15, acc=1.0, seed=int(time.time()) % 1000)
    lines = env._query(expo_sqf(*OBJ), settle=1.5)
    ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
    vals = [ex.get(k, 0) for k in range(8)]
    print(">> Officier : axe Sud-Est (defile, %d%% expose). Escouade spawn a 170 m, assaut sur l'objectif." % vals[DEFILE_K], flush=True)
    th = math.radians(DEFILE_K * 45.0); foot = (OBJ[0] + R_SPAWN * math.cos(th), OBJ[1] + R_SPAWN * math.sin(th))
    print(">> Place ta camera Zeus au-dessus de l'objectif (12000, 21000). Spawn dans 5 s...", flush=True)
    spawn_visual(env, foot, DEFILE_K)
    runner = OperationRunner(env, brain, plan(), log_path="/dev/null", verbose=True)
    ok = runner.run(max_steps=200, max_wall=700, stall_wall=300)
    print("\n>> Objectif %s | escouade %d/%d vivants | defenseurs restants %d/%d"
          % ("PRIS" if ok else "non pris", int(env.alive(0).sum()), SQ_N, int(env.en_alive().sum()), GARR_N), flush=True)
