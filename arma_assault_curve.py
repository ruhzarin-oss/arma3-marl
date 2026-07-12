"""arma_assault_curve — COURBE B + RECOMPOSITION : isole proprement la composition approche->succes d'assaut.
Courbe B : on spawn l'escouade DEJA AU CONTACT (point d'appui ~55m, sur l'axe defile), avec K hommes (K=2..8),
contre la garnison -> P(prendre l'objectif). Echec = echec (budget fixe, pas d'abort). Puis RECOMPOSITION :
les survivants par axe (mesures d'approche, arma_axis_multi.jsonl) injectes dans la courbe B -> succes attendu
par axe. Curve B mesuree depuis le point d'appui DEFILE pour les deux = CONSERVATEUR pour le pire axe."""
import time, argparse, threading, json, re, math, os
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (12000, 21000); NPATH = 12
HARDEN = '{ _x setSkill %.2f; _x disableAI "PATH"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x allowFleeing 0; _x setUnitPos "AUTO"; } forEach HMT_EN;\n'


def expo_sqf(ox, oy):
    return ('HMT_OX=%d; HMT_OY=%d; HMT_DEF=[]; { HMT_DEF pushBack [HMT_OX+12*cos _x, HMT_OY+12*sin _x] } forEach [0,90,180,270];\n'
            'for "_k" from 0 to 7 do { private _th=_k*45; private _sx=HMT_OX+170*cos _th; private _sy=HMT_OY+170*sin _th; private _seen=0;\n'
            '  for "_i" from 1 to %d do { private _t=_i/%d; private _px=_sx+(HMT_OX-_sx)*_t; private _py=_sy+(HMT_OY-_sy)*_t;\n'
            '    private _pz=(getTerrainHeightASL [_px,_py])+1.5; private _vis=false;\n'
            '    { private _dz=(getTerrainHeightASL [_x#0,_x#1])+1.5; if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis=true }; } forEach HMT_DEF;\n'
            '    if (_vis) then { _seen=_seen+1 }; };\n'
            '  diag_log format ["HARMATTAN_EXPO %%1 %%2", _k, round (100*_seen/%d)]; };\n' % (ox, oy, NPATH, NPATH, NPATH))


def make_plan(name):
    # ASSAUT seul, depuis le contact. Budget fixe : non-nettoye a la fin = ECHEC (pas d'abort qui pollue).
    return {"name": name,
            "phases": [{"name": "ASSAUT", "orders": {"SQ_ASSAUT": (OBJ, "assault")},
                        "done_when": ("any", [("enemy_dead_frac", 0.8), ("steps", 80)])}],
            "success": ("enemy_dead_frac", 0.8)}


def run_one(brain, srv, seed, K, foot, garr_n, skill, max_steps, max_wall, stall_wall):
    mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv
    log = SB + "/logs/server%d.out" % srv
    env = OpArma(squads=(("SQ_ASSAUT", K),), mission=mis, log=log, move=15, seed=seed)
    env.spawn({"SQ_ASSAUT": foot}, [(OBJ[0], OBJ[1], garr_n, 10)])
    env.b.send(HARDEN % skill, wait=True); time.sleep(1.0)
    runner = OperationRunner(env, brain, make_plan("K%d_s%d" % (K, seed)), log_path="/dev/null", verbose=False)
    ok = runner.run(max_steps=max_steps, max_wall=max_wall, stall_wall=stall_wall)
    return {"success": bool(ok), "garr_killed": 1.0 - float(env.en_alive().mean()), "losses": float(runner.losses())}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=5); p.add_argument("--garr", type=int, default=5); p.add_argument("--skill", type=float, default=0.4)
    p.add_argument("--foot", type=float, default=40.0); p.add_argument("--servers", type=int, default=16)
    p.add_argument("--max_steps", type=int, default=80); p.add_argument("--max_wall", type=float, default=180.0); p.add_argument("--stall_wall", type=float, default=150.0)
    p.add_argument("--approach", type=str, default="arma_axis_multi.jsonl"); p.add_argument("--out", type=str, default="arma_assault_curve.jsonl")
    a = p.parse_args()
    Ks = [2, 3, 4, 5, 6, 7, 8]
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()

    # point d'appui = 55 m de l'objectif sur l'axe DEFILE (le point de contact realiste)
    probe = OpArma(squads=(("SQ_ASSAUT", 2),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    lines = probe._query(expo_sqf(*OBJ), settle=1.5)
    ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
    dk = int(np.argmin([ex[k] for k in range(8)])); th = math.radians(dk * 45.0)
    foot = (OBJ[0] + a.foot * math.cos(th), OBJ[1] + a.foot * math.sin(th))
    print("courbe B : garnison %d skill %.2f | point d'appui a %dm (axe defile %d) | K=%s" % (a.garr, a.skill, a.foot, dk, Ks), flush=True)

    jobs = [(K, s) for K in Ks for s in range(a.reps)]
    results = []; lock = threading.Lock(); cur = [0]

    def worker(srv):
        while True:
            with lock:
                if cur[0] >= len(jobs): return
                ji = cur[0]; cur[0] += 1
            K, seed = jobs[ji]
            try:
                m = run_one(brain, srv, seed, K, foot, a.garr, a.skill, a.max_steps, a.max_wall, a.stall_wall)
            except Exception as e:
                m = {"err": type(e).__name__ + ":" + str(e)[:50]}
            m.update({"K": K, "srv": srv, "seed": seed})
            with lock:
                results.append(m)
                with open(a.out, "a") as f: f.write(json.dumps(m) + "\n")
                print("[%2d/%2d] srv%-2d K=%d -> succes=%s garr_killed=%s losses=%s"
                      % (len(results), len(jobs), srv, K, m.get("success"), ("%.2f" % m["garr_killed"]) if "garr_killed" in m else m.get("err"), ("%.2f" % m["losses"]) if "losses" in m else "-"), flush=True)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()

    # courbe B : P(succes | K)
    Psucc = {}
    print("\n=== COURBE B : P(prendre l'objectif | K hommes au contact) ===", flush=True)
    for K in Ks:
        ok = [r for r in results if r.get("K") == K and "success" in r]
        if ok:
            ps = sum(r["success"] for r in ok) / len(ok); Psucc[K] = ps
            print("  K=%d (n=%d) : succes %3.0f%% | garnison neutralisee %3.0f%% | pertes %3.0f%%"
                  % (K, len(ok), 100 * ps, 100 * sum(r["garr_killed"] for r in ok) / len(ok), 100 * sum(r["losses"] for r in ok) / len(ok)), flush=True)

    # RECOMPOSITION : survivants par axe (mesures d'approche) injectes dans la courbe B
    def p_of(s):
        s = max(0, min(8, int(round(s))))
        if s < min(Ks): return 0.0
        return Psucc.get(s, Psucc.get(min(s, max(Ks)), 0.0))
    if os.path.exists(a.approach) and Psucc:
        appr = [json.loads(l) for l in open(a.approach) if l.strip()]
        print("\n=== RECOMPOSITION : succes d'assaut attendu par axe (survivants d'approche -> courbe B) ===", flush=True)
        comp = {}
        for cond in ("defile", "pire"):
            surv = [8 * (1 - r["losses"]) for r in appr if r.get("cond") == cond and "losses" in r]
            if surv:
                es = sum(p_of(s) for s in surv) / len(surv); comp[cond] = es
                print("  %-6s : survivants moy %.1f/8 -> succes d'assaut attendu %3.0f%% (n_approche=%d)"
                      % (cond, sum(surv) / len(surv), 100 * es, len(surv)), flush=True)
        if "defile" in comp and "pire" in comp:
            d = 100 * (comp["defile"] - comp["pire"])
            print("\n>>> COMPOSITION : l'axe defile -> %+.0f pts de succes d'assaut vs le pire axe (conservateur)" % d, flush=True)
            print(">>> %s" % ("LA SURVIE A L'APPROCHE SE COMPOSE EN PRISE DE L'OBJECTIF" if d >= 10 else
                              ("composition faible (courbe B pas assez raide dans la plage K -> ajuster garnison)" if abs(d) < 10 else "inverse (anormal)")), flush=True)
    print("CURVE FINI", flush=True)
