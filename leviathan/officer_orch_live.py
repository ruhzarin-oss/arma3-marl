#!/usr/bin/env python3
"""officer_orch_live.py — ETAGES 2+4 COMBINES (la couture) sur server_fob, pont NATIF.
Double horloge :
  LENTE (tous les 5 ticks) : officier Qwen lit le SITREP -> ordonne -> pose le FOCUS (quel FOB renforcer).
  RAPIDE (chaque tick)     : orchestration -> agents du FOB focus AU CONTACT : 10 features -> orchestration_arma_voyant.pt -> tactique.
Etage de DECISION (log officier + tactiques par agent) ; les executeurs SQF = etape suivante."""
import sys, time, argparse, ast, re
from collections import Counter
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from arma_bridge import ArmaBridge
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory
from officer import OfficerLoop, qwen_ollama, make_apply
import torch, torch.nn as nn

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
CKPT = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def inject_threat(b, fob, n=12):
    sqf = ('[] spawn { if (!isNil "HMT_OFFT") then { { deleteVehicle _x } forEach HMT_OFFT }; '
           'HMT_OFFT_G = createGroup west; HMT_OFFT = []; '
           'for "_i" from 0 to %d do { private _p = [%d - 150 + (_i mod 4) * 15, %d - 120 + (floor (_i / 4)) * 15, 0]; '
           'private _u = HMT_OFFT_G createUnit ["B_recon_F", _p, [], 0, "FORM"]; '
           '_u setSkill 0.55; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; HMT_OFFT pushBack _u; }; '
           'HMT_OFFT_G move [%d, %d, 0]; sleep 3; '
           '{ private _r = _x; { _x reveal [_r, 3] } forEach (allUnits select {side _x == east && alive _x && _x distance _r < 500}); } forEach HMT_OFFT; '
           '};') % (n - 1, fob[0], fob[1], fob[0], fob[1])
    b.send(sqf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=24)
    ap.add_argument("--fob", default="M1")
    ap.add_argument("--nothreat", action="store_true")
    a = ap.parse_args()

    try:
        b = NativeBridge(port=5816); BR = "NATIF TCP 5816"
    except Exception as e:
        b = ArmaBridge(mission=MIS, log=LOG); BR = "FICHIER (%s)" % e
    print("[pont] %s" % BR, flush=True)
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    coords = "[" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "]"
    b.send("HMT_FOB_ANCHORS = %s;" % coords)
    b.send('call compile preprocessFileLineNumbers "officer_sit.sqf";')
    b.send('call compile preprocessFileLineNumbers "orch_features_v5.sqf";')
    b.send('call compile preprocessFileLineNumbers "tactics_exec.sqf";')      # les executeurs
    time.sleep(1.2)
    fobpos = next(([f[1], f[2], 0] for f in FOBS if f[0] == a.fob), [4279, 3856, 0])

    st = OfficerState(bridge=b)

    def read_sit(tick):
        r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=12)
        return st.parse(r[-1].group(1).rstrip('"').strip(), tick) if r else None

    net = OrchNet(); net.load_state_dict(torch.load(CKPT, map_location="cpu")); net.eval()
    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")

    class Stub:
        focus = None
    drv = Stub()
    loop = OfficerLoop(mem, qwen=qwen_ollama, apply_fn=make_apply(drv))

    if not a.nothreat:
        print("[menace] assaut WEST (12) pres de %s %s..." % (a.fob, fobpos[:2]), flush=True)
        inject_threat(b, fobpos); time.sleep(22)
    print("=== ETAGES 2+4 : OFFICIER Qwen -> FOCUS -> ORCHESTRATION par agent (server_fob :3902) ===", flush=True)

    for tick in range(a.ticks):
        if tick % 5 == 0:                                            # --- LENTE : l'officier ---
            sit = read_sit(tick)
            if sit:
                t0 = time.time()
                orders = loop.decide(sit, tick, float(tick))
                thr = [(f["name"], f["contacts"]) for f in sit["fobs"] if f["threatened"]]
                ords = [(o.get("fob"), o.get("action")) for o in orders.get("ordres", [])]
                print("[%02d] OFFICIER (%.1fs) menaces=%s -> ordres=%s | FOCUS=%s" %
                      (tick, time.time() - t0, thr or "-", ords or "-", drv.focus), flush=True)
        if drv.focus:                                               # --- RAPIDE : l'orchestration sur le FOB focus ---
            fx, fy = drv.focus[0], drv.focus[1]
            r = b.query("[[%d,%d,0],8] call HMT_ORCH_SNAP;" % (fx, fy),
                        r'HARMATTAN_ORCH (\[.*\]) \| (\[.*\])', want=1, timeout=8)
            if r:
                try:
                    vs = ast.literal_eval(r[-1].group(1))
                except Exception:
                    vs = []
                ids = re.findall(r'(\d+:\d+(?::\d+)*)', r[-1].group(2))
                if vs:
                    with torch.no_grad():
                        logits, _ = net(torch.tensor(vs, dtype=torch.float32))
                        tacs = logits.argmax(1).tolist()
                    dist = Counter(TAC[t] for t in tacs)
                    disp = ""
                    if len(ids) == len(tacs):                        # DISPATCH -> executeurs SQF (action reelle)
                        ids_sqf = "[" + ",".join('"%s"' % i for i in ids) + "]"
                        b.send("[%s,%s] call HMT_TAC_DISPATCH;" % (ids_sqf, tacs))
                        disp = " -> DISPATCH %d" % len(ids)
                    print("     [%02d] ORCH  %d agents @ focus -> %s%s" % (tick, len(tacs), dict(dist), disp), flush=True)
                else:
                    print("     [%02d] ORCH  0 agent au contact au focus" % tick, flush=True)
        else:
            if tick % 5 == 0:
                print("     [%02d] (calme : pas de focus, rien a orchestrer)" % tick, flush=True)
        time.sleep(2)
    print("=== FIN couture 2+4 ===", flush=True)


if __name__ == "__main__":
    main()
