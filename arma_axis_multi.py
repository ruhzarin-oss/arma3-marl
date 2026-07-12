"""arma_axis_multi — ROBUSTESSE MULTI-OBJECTIFS du jalon 2. Rejoue la mesure propre des PERTES D'APPROCHE
(defile vs pire axe) sur PLUSIEURS objectifs a defile fort d'Altis. Si le defile epargne des pertes sur
TOUS, le -38 d'un seul objectif n'etait pas un coup de chance. Discipline matrice : OpArma fraiche par op,
1 op/serveur a la fois (workers en file, pont frais par op = pattern valide des tables §4.7)."""
import time, argparse, threading, json, re, math
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJECTIFS = [(12000, 21000), (9000, 21000), (21000, 6000), (9000, 18000)]   # defiles forts du scan
R_SPAWN = 170.0; GARR_N = 10; SQ_N = 8; NPATH = 12
SQUADS = (("SQ_ASSAUT", SQ_N),)
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


def axis_pos(obj, k):
    th = math.radians(k * 45.0)
    return (obj[0] + R_SPAWN * math.cos(th), obj[1] + R_SPAWN * math.sin(th))


def make_plan(obj, name):
    return {"name": name,
            "phases": [{"name": "APPROCHE", "orders": {"SQ_ASSAUT": (obj, "move")},
                        "done_when": ("any", [("squad_at", 0, obj, 55), ("steps", 40)])}],
            "success": ("losses_max", 0.5)}


def run_one(brain, srv, seed, obj, k, max_steps, max_wall, stall_wall):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=SQUADS, mission=mis, log=log, move=15, seed=seed)
    sx, sy = axis_pos(obj, k)
    env.spawn({"SQ_ASSAUT": (sx, sy)}, [(obj[0], obj[1], GARR_N, 10)])
    env.b.send(HARDEN_SQF, wait=True); time.sleep(1.0)
    runner = OperationRunner(env, brain, make_plan(obj, "O%d_k%d_s%d" % (obj[0], k, seed)), log_path="/dev/null", verbose=False)
    runner.run(max_steps=max_steps, max_wall=max_wall, stall_wall=stall_wall)
    return {"losses": float(runner.losses()), "abort": getattr(runner, "abort_reason", None)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=4)            # reps PAR condition PAR objectif
    p.add_argument("--servers", type=int, default=16)
    p.add_argument("--max_steps", type=int, default=40); p.add_argument("--max_wall", type=float, default=160.0); p.add_argument("--stall_wall", type=float, default=160.0)
    p.add_argument("--out", type=str, default="arma_axis_multi.jsonl")
    a = p.parse_args()
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()

    # 1) sonder l'exposition de chaque objectif -> defile / pire
    probe = OpArma(squads=SQUADS, mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    plan_obj = []
    for obj in OBJECTIFS:
        lines = probe._query(expo_sqf(*obj), settle=1.5)
        ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
        if len(ex) != 8:
            print("obj %s : expo incomplete -> ignore" % (obj,)); continue
        vals = [ex[k] for k in range(8)]; dk = int(np.argmin(vals)); wk = int(np.argmax(vals))
        plan_obj.append((obj, dk, wk, vals[dk], vals[wk]))
        print("obj %s | defile=axe%d(%d%%) pire=axe%d(%d%%)" % (obj, dk, vals[dk], wk, vals[wk]), flush=True)

    # 2) jobs : pour chaque objectif, reps x {defile, pire}
    jobs = []
    for oi, (obj, dk, wk, _, _) in enumerate(plan_obj):
        for s in range(a.reps):
            jobs.append((oi, obj, "defile", dk, s)); jobs.append((oi, obj, "pire", wk, s))
    print("=== ROBUSTESSE : %d ops sur %d objectifs (%d/cond/obj) ===" % (len(jobs), len(plan_obj), a.reps), flush=True)
    results = []; lock = threading.Lock(); cur = [0]

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                ji = cur[0]; cur[0] += 1
            oi, obj, cond, k, seed = jobs[ji]
            try:
                m = run_one(brain, srv, seed, obj, k, a.max_steps, a.max_wall, a.stall_wall)
            except Exception as e:
                m = {"err": type(e).__name__ + ":" + str(e)[:50]}
            m.update({"oi": oi, "obj": obj, "cond": cond, "srv": srv, "seed": seed})
            with lock:
                results.append(m)
                with open(a.out, "a") as f: f.write(json.dumps(m) + "\n")
                print("[%2d/%2d] srv%-2d obj%d %-6s -> losses=%s abort=%s"
                      % (len(results), len(jobs), srv, oi, cond, ("%.2f" % m["losses"]) if "losses" in m else m.get("err"), m.get("abort")), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()

    print("\n=== PERTES D'APPROCHE PAR OBJECTIF (defile vs pire) ===", flush=True)
    gains = []
    for oi, (obj, dk, wk, de, we) in enumerate(plan_obj):
        d = [r["losses"] for r in results if r.get("oi") == oi and r.get("cond") == "defile" and "losses" in r]
        w = [r["losses"] for r in results if r.get("oi") == oi and r.get("cond") == "pire" and "losses" in r]
        if d and w:
            md, mw = sum(d) / len(d), sum(w) / len(w); gains.append(mw - md)
            print("  obj %-14s | defile %3.0f%% (expo %d%%) vs pire %3.0f%% (expo %d%%) -> defile epargne %+.0f pts"
                  % (str(obj), 100 * md, de, 100 * mw, we, 100 * (mw - md)), flush=True)
    if gains:
        moy = 100 * sum(gains) / len(gains); npos = sum(1 for g in gains if g > 0.05)
        print("\n>>> le defile epargne en moyenne %+.0f pts | favorable sur %d/%d objectifs" % (moy, npos, len(gains)), flush=True)
        print(">>> %s" % ("ROBUSTE : le defile aide sur tous/presque tous les objectifs -> le -38 n'etait pas un coup de chance"
                          if npos >= len(gains) - 1 and moy >= 10 else "effet variable selon l'objectif -> a creuser"), flush=True)
    print("MULTI FINI", flush=True)
