"""arma_axis_combat — JALON 2, le test sim->reel de l'officier-axe. Une escouade assaut une garnison depuis
l'AXE choisi par l'officier (defile = exposition min) VS le PIRE axe (exposition max), sur un objectif a defile
fort d'Altis, en VRAI combat Arma. Mesure : garnison neutralisee + pertes amies. Question : le +10/-9 du sim
survit-il au mur sim->reel ? DISCIPLINE MATRICE : OpArma fraiche par op, UN serveur par op (job j -> serveur j,
<=1 op/serveur garanti), conditions alternees sur serveurs pairs/impairs."""
import time, argparse, threading, json, re, math
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (12000, 21000); R_SPAWN = 170.0; GARR_N = 10; SQ_N = 8; NPATH = 12   # garnison qui tient l'objectif ; on mesure l'APPROCHE, pas l'assaut
SQUADS = (("SQ_ASSAUT", SQ_N),)
# garnison en SURVEILLANCE STATIQUE (tient -> elle voit et tire sur l'approche exposee) ; skill modere
HARDEN_SQF = '{ _x setSkill 0.6; _x disableAI "PATH"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x allowFleeing 0; _x setUnitPos "AUTO"; } forEach HMT_EN;\n'


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
    th = math.radians(k * 45.0)
    return (OBJ[0] + R_SPAWN * math.cos(th), OBJ[1] + R_SPAWN * math.sin(th))


def make_plan(name):
    # ISOLE L'APPROCHE : l'escouade TRAVERSE (mode 'move', elle avance sans s'arreter pour la melee) jusqu'a un
    # point d'appui a 55 m de l'objectif. On mesure les pertes A CET INSTANT = les morts subis EN TRAVERSANT
    # le terrain a decouvert. C'est LA que le defile agit (avant le combat rapproche qui noyait le signal).
    return {"name": name,
            "phases": [
                {"name": "APPROCHE", "orders": {"SQ_ASSAUT": (OBJ, "move")},
                 "done_when": ("any", [("squad_at", 0, OBJ, 55), ("steps", 40)])}],
            "success": ("losses_max", 0.5)}


def run_one_axis(brain, srv, seed, k, max_steps, max_wall, stall_wall):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=SQUADS, mission=mis, log=log, move=15, seed=seed)   # approche GRADUELLE -> fenetre d'exposition lisible
    sx, sy = axis_pos(k)
    env.spawn({"SQ_ASSAUT": (sx, sy)}, [(OBJ[0], OBJ[1], GARR_N, 10)])
    env.b.send(HARDEN_SQF, wait=True); time.sleep(1.0)   # garnison en surveillance, punit l'approche exposee
    runner = OperationRunner(env, brain, make_plan("AXE%d_s%d" % (k, seed)), log_path="/dev/null", verbose=False)
    runner.run(max_steps=max_steps, max_wall=max_wall, stall_wall=stall_wall)
    eal = env.en_alive()
    return {"garr_killed": 1.0 - (float(eal.mean()) if env.en_n else 0.0),
            "losses": float(runner.losses()), "abort": getattr(runner, "abort_reason", None)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=8)             # reps PAR condition (defile / pire)
    p.add_argument("--max_steps", type=int, default=40); p.add_argument("--max_wall", type=float, default=160.0); p.add_argument("--stall_wall", type=float, default=160.0)
    p.add_argument("--out", type=str, default="arma_axis_combat.jsonl")
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()

    # 1) exposition par axe sur le vrai terrain -> defile (min) et pire (max)
    probe = OpArma(squads=SQUADS, mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    lines = probe._query(expo_sqf(*OBJ), settle=1.5)
    ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
    vals = [ex[k] for k in range(8)]; defile_k = int(np.argmin(vals)); worst_k = int(np.argmax(vals))
    print("objectif (%d,%d) | expo par axe : %s | DEFILE=axe%d(%d%%) PIRE=axe%d(%d%%)"
          % (OBJ[0], OBJ[1], vals, defile_k, vals[defile_k], worst_k, vals[worst_k]), flush=True)

    # 2) jobs : reps x {defile, pire}, conditions alternees, UN serveur par job
    jobs = []
    for s in range(a.reps):
        jobs.append(("defile", defile_k, s)); jobs.append(("pire", worst_k, s))
    print("=== JALON 2 : %d ops (%d defile / %d pire), 1 serveur/op, combat Arma reel ===" % (len(jobs), a.reps, a.reps), flush=True)
    results = []; lock = threading.Lock()

    def worker(job_i):
        cond, k, seed = jobs[job_i]; srv = job_i  # job j -> serveur j : <=1 op/serveur
        t0 = time.time()
        try:
            m = run_one_axis(brain, srv, seed, k, a.max_steps, a.max_wall, a.stall_wall)
        except Exception as e:
            m = {"err": type(e).__name__ + ":" + str(e)[:60]}
        m.update({"cond": cond, "srv": srv, "seed": seed, "dt": round(time.time() - t0, 1)})
        with lock:
            results.append(m)
            with open(a.out, "a") as f: f.write(json.dumps(m) + "\n")
            print("[%2d/%2d] srv%-2d %-6s -> garr_killed=%s losses=%s abort=%s (%.0fs)"
                  % (len(results), len(jobs), srv, cond, _fmt(m.get("garr_killed")), _fmt(m.get("losses")), m.get("abort"), m.get("dt", 0)), flush=True)

    def _fmt(x): return "%.2f" % x if isinstance(x, float) else x
    th = [threading.Thread(target=worker, args=(i,)) for i in range(len(jobs))]
    for t in th: t.start()
    for t in th: t.join()

    agg = {}
    for cond in ("defile", "pire"):
        ok = [r for r in results if r.get("cond") == cond and "losses" in r and r.get("abort") is None]
        okall = [r for r in results if r.get("cond") == cond and "losses" in r]
        if okall:
            lo = sum(r["losses"] for r in okall) / len(okall); agg[cond] = lo
            naborts = sum(1 for r in okall if r.get("abort"))
            print(">>> %-6s (n=%d, %d aborts) : PERTES D'APPROCHE %.0f%%" % (cond, len(okall), naborts, 100 * lo), flush=True)
    if "defile" in agg and "pire" in agg:
        d = 100 * (agg["pire"] - agg["defile"])
        print("\n=== VERDICT JALON 2 (pertes d'approche, terrain reel Altis) ===", flush=True)
        print("le defile epargne %+.0f pts de pertes d'approche vs le pire axe" % d, flush=True)
        print(">>> %s" % ("LE DEFILE AIDE EN ARMA REEL -> le levier de l'officier passe le mur sim->reel" if d >= 8 else
                          ("effet faible/nul -> le defile ne se transfere pas (ou noye dans le bruit Arma)" if d > -8 else
                           "INVERSE -> le defile NUIT en Arma (le mecanisme ne tient pas hors-sim)")), flush=True)
    print("AXISCOMBAT FINI", flush=True)
