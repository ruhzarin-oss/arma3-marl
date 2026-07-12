"""arma_axis_assault — la COMPOSITION : la survie a l'approche (defile -> escouade arrive entiere) se traduit-elle
en PRISE DE L'OBJECTIF ? Operation complete (approche + assaut), defile vs pire axe. Garnison reduite/killable
pour que l'assaut SE RESOLVE. Mesure : garnison neutralisee + pertes totales + succes. Discipline matrice."""
import time, argparse, threading, json, re, math
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (12000, 21000); R_SPAWN = 170.0; GARR_N = 6; SQ_N = 8; NPATH = 12
SQUADS = (("SQ_ASSAUT", SQ_N),)
# surveillance statique (l'approche exposee est punie) mais skill modere + effectif reduit -> l'assaut peut conclure
HARDEN_SQF = '{ _x setSkill 0.5; _x disableAI "PATH"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x allowFleeing 0; _x setUnitPos "AUTO"; } forEach HMT_EN;\n'


def expo_sqf(ox, oy):
    return ('HMT_OX=%d; HMT_OY=%d; HMT_DEF=[]; { HMT_DEF pushBack [HMT_OX+12*cos _x, HMT_OY+12*sin _x] } forEach [0,90,180,270];\n'
            'for "_k" from 0 to 7 do { private _th=_k*45; private _sx=HMT_OX+%f*cos _th; private _sy=HMT_OY+%f*sin _th; private _seen=0;\n'
            '  for "_i" from 1 to %d do { private _t=_i/%d; private _px=_sx+(HMT_OX-_sx)*_t; private _py=_sy+(HMT_OY-_sy)*_t;\n'
            '    private _pz=(getTerrainHeightASL [_px,_py])+1.5; private _vis=false;\n'
            '    { private _dz=(getTerrainHeightASL [_x#0,_x#1])+1.5; if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis=true }; } forEach HMT_DEF;\n'
            '    if (_vis) then { _seen=_seen+1 }; };\n'
            '  diag_log format ["HARMATTAN_EXPO %%1 %%2", _k, round (100*_seen/%d)]; };\n'
            % (ox, oy, R_SPAWN, R_SPAWN, NPATH, NPATH, NPATH))


def axis_pos(k):
    th = math.radians(k * 45.0); return (OBJ[0] + R_SPAWN * math.cos(th), OBJ[1] + R_SPAWN * math.sin(th))


def make_plan(name):
    return {"name": name,
            "phases": [
                {"name": "APPROCHE", "orders": {"SQ_ASSAUT": (OBJ, "move")},
                 "done_when": ("any", [("squad_at", 0, OBJ, 55), ("steps", 35)])},
                {"name": "ASSAUT", "orders": {"SQ_ASSAUT": (OBJ, "assault")},
                 "done_when": ("any", [("enemy_dead_frac", 0.8), ("losses", 0.85)])}],
            "success": ("all", [("enemy_dead_frac", 0.7), ("losses_max", 0.6)])}


def run_one(brain, srv, seed, k, max_steps, max_wall, stall_wall):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=SQUADS, mission=mis, log=log, move=15, seed=seed)
    sx, sy = axis_pos(k)
    env.spawn({"SQ_ASSAUT": (sx, sy)}, [(OBJ[0], OBJ[1], GARR_N, 10)])
    env.b.send(HARDEN_SQF, wait=True); time.sleep(1.0)
    runner = OperationRunner(env, brain, make_plan("k%d_s%d" % (k, seed)), log_path="/dev/null", verbose=False)
    ok = runner.run(max_steps=max_steps, max_wall=max_wall, stall_wall=stall_wall)
    eal = env.en_alive()
    return {"garr_killed": 1.0 - (float(eal.mean()) if env.en_n else 0.0), "losses": float(runner.losses()),
            "success": bool(ok), "abort": getattr(runner, "abort_reason", None)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=6)
    p.add_argument("--servers", type=int, default=12)
    p.add_argument("--max_steps", type=int, default=120); p.add_argument("--max_wall", type=float, default=240.0); p.add_argument("--stall_wall", type=float, default=180.0)
    p.add_argument("--out", type=str, default="arma_axis_assault.jsonl")
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    probe = OpArma(squads=SQUADS, mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    lines = probe._query(expo_sqf(*OBJ), settle=1.5)
    ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
    vals = [ex[k] for k in range(8)]; dk = int(np.argmin(vals)); wk = int(np.argmax(vals))
    print("obj %s | DEFILE=axe%d(%d%%) PIRE=axe%d(%d%%) | assaut complet, garnison %d" % (OBJ, dk, vals[dk], wk, vals[wk], GARR_N), flush=True)
    jobs = []
    for s in range(a.reps):
        jobs.append(("defile", dk, s)); jobs.append(("pire", wk, s))
    print("=== ASSAUT COMPLET : %d ops (%d/cond) ===" % (len(jobs), a.reps), flush=True)
    results = []; lock = threading.Lock(); cur = [0]

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                ji = cur[0]; cur[0] += 1
            cond, k, seed = jobs[ji]
            try:
                m = run_one(brain, srv, seed, k, a.max_steps, a.max_wall, a.stall_wall)
            except Exception as e:
                m = {"err": type(e).__name__ + ":" + str(e)[:50]}
            m.update({"cond": cond, "srv": srv, "seed": seed})
            with lock:
                results.append(m)
                with open(a.out, "a") as f: f.write(json.dumps(m) + "\n")
                print("[%2d/%2d] srv%-2d %-6s -> garr_killed=%s losses=%s succes=%s abort=%s"
                      % (len(results), len(jobs), srv, cond, ("%.2f" % m["garr_killed"]) if "garr_killed" in m else m.get("err"),
                         ("%.2f" % m["losses"]) if "losses" in m else "-", m.get("success"), m.get("abort")), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()
    print("\n=== COMPOSITION : l'assaut depuis le defile prend-il l'objectif ? ===", flush=True)
    for cond in ("defile", "pire"):
        ok = [r for r in results if r.get("cond") == cond and "garr_killed" in r]
        if ok:
            gk = sum(r["garr_killed"] for r in ok) / len(ok); lo = sum(r["losses"] for r in ok) / len(ok)
            su = sum(r["success"] for r in ok) / len(ok); ab = sum(1 for r in ok if r.get("abort"))
            print(">>> %-6s (n=%d, %d aborts) : garnison neutralisee %3.0f%% | pertes %3.0f%% | succes op %3.0f%%"
                  % (cond, len(ok), ab, 100 * gk, 100 * lo, 100 * su), flush=True)
    print("ASSAUT FINI", flush=True)
