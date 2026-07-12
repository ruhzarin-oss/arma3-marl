"""arma_assault_land — assaut sur le VRAI objectif terre (15000,16000). Escouade spawn a un spawn terre eprouve
(~200 m sud), assaut nord. Garde garnison + joueur Zeus. Temps reel."""
import time
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (15000, 16000); SPAWN = (15000, 15790); SQ_N = 8; GARR_N = 5


def spawn_squad(env):
    sx, sy = SPAWN
    sqf = ('SQ_ASSAUT=[]; private _g0 = createGroup west;\n'
           'for "_a" from 0 to ' + str(SQ_N - 1) + ' do {\n'
           '  private _ty = if (_a in [1,2]) then {"B_soldier_LAT_F"} else {"B_Soldier_F"};\n'
           '  _g0 createUnit [_ty, [' + str(sx) + ' + 9*(cos (360*_a/' + str(SQ_N) + ')), ' + str(sy) + ' + 9*(sin (360*_a/' + str(SQ_N) + ')), 0], [], 0, "FORM"];\n'
           '  private _u = (units _g0) select ((count (units _g0))-1);\n'
           '  _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u setSkill 0.5; _u allowFleeing 0; SQ_ASSAUT pushBack _u;\n};\n'
           '{ private _c = getAssignedCuratorLogic _x; if (!isNull _c) then { _c addCuratorEditableObjects [allUnits, true]; }; } forEach allPlayers;\n'
           'setAccTime 1; diag_log "HARMATTAN_SQUAD spawn terre";\n')
    env.b.send(sqf, wait=True); time.sleep(4.0)
    env.en_n = GARR_N; env.epx = np.zeros(GARR_N); env.epy = np.zeros(GARR_N); env.edmg = np.zeros(GARR_N)
    env.read()


def plan():
    return {"name": "ASSAUT-TERRE",
            "phases": [{"name": "APPROCHE", "orders": {"SQ_ASSAUT": (OBJ, "move")}, "done_when": ("any", [("squad_at", 0, OBJ, 55), ("steps", 70)])},
                       {"name": "ASSAUT", "orders": {"SQ_ASSAUT": (OBJ, "assault")}, "done_when": ("any", [("enemy_dead_frac", 0.8), ("steps", 130)])}],
            "success": ("enemy_dead_frac", 0.8)}


if __name__ == "__main__":
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env = OpArma(squads=(("SQ_ASSAUT", SQ_N),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", move=15, acc=1.0, seed=int(time.time()) % 1000)
    print(">> Escouade (8) spawn a (15000,15790), ~200m sud. Assaut nord sur l'objectif terre. Regarde !", flush=True)
    spawn_squad(env)
    runner = OperationRunner(env, brain, plan(), log_path="/dev/null", verbose=True)
    ok = runner.run(max_steps=210, max_wall=700, stall_wall=300)
    print("\n>> Objectif %s | escouade %d/%d vivants | defenseurs restants %d/%d"
          % ("PRIS" if ok else "non pris", int(env.alive(0).sum()), SQ_N, int(env.en_alive().sum()), GARR_N), flush=True)
