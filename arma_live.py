"""arma_live — DEMO LIVE bout-en-bout : l'officier lit le VRAI terrain Altis -> choisit l'axe -> justifie,
puis l'escouade ASSAUT et on regarde le journal de l'operation se derouler (verbose). Un seul run, honnete."""
import json, re, math, time, urllib.request
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = (12000, 21000); R_SPAWN = 170.0; GARR_N = 5; SQ_N = 8; NPATH = 12
OLLAMA = "http://localhost:11434/api/chat"; MODEL = "qwen2.5:14b"
NAMES = ["Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ouest", "Ouest", "Nord-Ouest"]
HARDEN = '{ _x setSkill 0.45; _x disableAI "PATH"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x allowFleeing 0; } forEach HMT_EN;\n'
SYS = ("Tu es un officier d'infanterie. Choisis l'AXE D'APPROCHE le moins expose (faible % a decouvert = mieux). "
       'Reponds en JSON : {"axe":"<un des 8 noms>","justification":"<1 phrase en francais citant le %>"}.')


def expo_sqf(ox, oy):
    return ('HMT_OX=%d; HMT_OY=%d; HMT_DEF=[]; { HMT_DEF pushBack [HMT_OX+12*cos _x, HMT_OY+12*sin _x] } forEach [0,90,180,270];\n'
            'for "_k" from 0 to 7 do { private _th=_k*45; private _sx=HMT_OX+%f*cos _th; private _sy=HMT_OY+%f*sin _th; private _seen=0;\n'
            '  for "_i" from 1 to %d do { private _t=_i/%d; private _px=_sx+(HMT_OX-_sx)*_t; private _py=_sy+(HMT_OY-_sy)*_t;\n'
            '    private _pz=(getTerrainHeightASL [_px,_py])+1.5; private _vis=false;\n'
            '    { private _dz=(getTerrainHeightASL [_x#0,_x#1])+1.5; if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis=true }; } forEach HMT_DEF;\n'
            '    if (_vis) then { _seen=_seen+1 }; };\n'
            '  diag_log format ["HARMATTAN_EXPO %%1 %%2", _k, round (100*_seen/%d)]; };\n' % (ox, oy, R_SPAWN, R_SPAWN, NPATH, NPATH, NPATH))


def ask_llm(carte):
    body = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.2},
                       "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": "Carte tactique, terrain reel d'Altis :\n" + carte}]}).encode()
    return json.loads(json.load(urllib.request.urlopen(urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"}), timeout=120))["message"]["content"])


def plan(obj):
    return {"name": "ASSAUT-LIVE",
            "phases": [{"name": "APPROCHE", "orders": {"SQ_ASSAUT": (obj, "move")}, "done_when": ("any", [("squad_at", 0, obj, 50), ("steps", 40)])},
                       {"name": "ASSAUT", "orders": {"SQ_ASSAUT": (obj, "assault")}, "done_when": ("any", [("enemy_dead_frac", 0.8), ("steps", 90)])}],
            "success": ("enemy_dead_frac", 0.8)}


if __name__ == "__main__":
    brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    env = OpArma(squads=(("SQ_ASSAUT", SQ_N),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", move=15, seed=int(time.time()) % 1000)
    print("\n========================= OFFICIER — RECONNAISSANCE =========================")
    print("Objectif sur Altis : (%d, %d). L'officier interroge le relief reel..." % OBJ, flush=True)
    lines = env._query(expo_sqf(*OBJ), settle=1.5)
    ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
    vals = [ex[k] for k in range(8)]; dk = int(np.argmin(vals))
    print("\nCarte tactique (exposition par axe, calculee sur le vrai terrain) :")
    for k in range(8):
        bar = "#" * (vals[k] // 5); mark = "  <= DEFILE" if k == dk else ""
        print("   %-11s %3d%%  %s%s" % (NAMES[k], vals[k], bar, mark))
    carte = "\n".join("  - axe %-11s : %3d%% du trajet a decouvert" % (NAMES[k], vals[k]) for k in range(8))
    ans = ask_llm(carte); axe = ans.get("axe"); ki = NAMES.index(axe) if axe in NAMES else dk
    print("\n>> DECISION OFFICIER : j'attaque par %s (%d%% expose)." % (axe, vals[ki]))
    print(">> \"%s\"" % ans.get("justification", ""))
    th = math.radians(ki * 45.0); sx, sy = OBJ[0] + R_SPAWN * math.cos(th), OBJ[1] + R_SPAWN * math.sin(th)
    print("\n========================= L'ASSAUT — EN DIRECT =========================")
    print("Escouade : %d hommes, spawn a 170 m sur l'axe %s. Garnison : %d defenseurs.\n" % (SQ_N, axe, GARR_N), flush=True)
    env.spawn({"SQ_ASSAUT": (sx, sy)}, [(OBJ[0], OBJ[1], GARR_N, 10)]); env.b.send(HARDEN, wait=True); time.sleep(1.0)
    runner = OperationRunner(env, brain, plan(OBJ), log_path="/dev/null", verbose=True)
    ok = runner.run(max_steps=140, max_wall=260, stall_wall=160)
    alive = int(env.alive(0).sum()); en = int(env.en_alive().sum())
    print("\n========================= RESULTAT =========================")
    print("Objectif %s | escouade : %d/%d vivants | defenseurs restants : %d/%d | pertes %.0f%%"
          % ("PRIS" if ok else "NON PRIS", alive, SQ_N, en, GARR_N, 100 * runner.losses()))
