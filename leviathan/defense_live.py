#!/usr/bin/env python3
"""defense_live.py — DEFENSE PERSISTANTE avec le NOUVEAU commandement (remplace l'ancien leviathan001_live).
Boucle infinie : l'officier Qwen lit le vrai SITREP -> RENFORCE le FOB menace (focus) ; l'orchestration donne
la tactique de chaque defenseur du FOB focus (fumi/grenade/suppr/flanc). Menaces REELLES (pas d'injection).
Fonctions chargees au boot par init.sqf (HMT_SITREP / HMT_ORCH_SNAP / HMT_TAC_DISPATCH)."""
import sys, time, ast, re, math
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
CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
CKV = "/home/younes/compose-embodiment/coevo_live.pt"          # defenseur co-evolue (placement appris)
REAL_R = 42.0                                                  # rayon de deploiement reel du placement (m)


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__(); s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()); s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def main():
    try:
        b = NativeBridge(port=5816); BR = "NATIF 5816"
    except Exception as e:
        b = ArmaBridge(mission=MIS, log=LOG); BR = "FICHIER (%s)" % e
    print("[defense] pont %s" % BR, flush=True)
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    coords = "[" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "]"
    b.send("HMT_FOB_ANCHORS = %s;" % coords)
    time.sleep(1)
    st = OfficerState(bridge=b)

    def read_sit(tick):
        r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=12)
        return st.parse(r[-1].group(1).rstrip('"').strip(), tick) if r else None

    net = OrchNet(); net.load_state_dict(torch.load(CKO, map_location="cpu")); net.eval()

    # ---- defenseur CO-EVOLUE : placement appris (2 clusters), branche sur la vraie FOB ----
    dmu = None
    try:
        ck = torch.load(CKV, map_location="cpu")
        dmu = ck["defender"]["mu"].view(2, 2).tanh().tolist()      # 2 centres normalises [-1,1] (comme applique en co-evo)
        print("[defense] placement co-evolue charge : clusters=%s" % dmu, flush=True)
    except Exception as e:
        print("[defense] pas de placement co-evolue (%s)" % str(e)[:50], flush=True)

    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")

    class Stub:
        focus = None
    drv = Stub()
    loop = OfficerLoop(mem, qwen=qwen_ollama, apply_fn=make_apply(drv))
    fpos = {f[0]: [f[1], f[2]] for f in FOBS}

    print("=== DEFENSE PERSISTANTE (NOUVEAU stack : officier Qwen + orchestration + placement co-evolue) ===", flush=True)
    tick = 0
    last_repos = None                                              # derniere menace pour laquelle on a replace la defense
    while True:
        tick += 1
        if tick % 5 == 1:                                           # tier LENT : l'officier veille
            sit = read_sit(tick)
            if sit:
                loop.decide(sit, tick, float(tick))
                thr = [(f["name"], f["contacts"]) for f in sit["fobs"] if f["threatened"]]
                print("  [%04d] menaces=%s | focus=%s" % (tick, thr or "-", drv.focus), flush=True)
        if drv.focus and dmu is not None and drv.focus != last_repos:   # REPLACEMENT co-evolue (une fois par nouvelle menace)
            try:
                fx, fy = drv.focus[0], drv.focus[1]
                rb = b.query(
                    'private _w=allUnits select {side _x==west && alive _x && _x distance [%d,%d,0]<450}; '
                    'if (count _w==0) then {(format ["HARMATTAN_BRG %%1", -999]) call HMT_EMIT} else '
                    '{private _sx=0;private _sy=0;{private _p=getPosATL _x;_sx=_sx+(_p select 0);_sy=_sy+(_p select 1)} forEach _w; '
                    '_sx=_sx/(count _w);_sy=_sy/(count _w); '
                    '(format ["HARMATTAN_BRG %%1", (_sx-%d) atan2 (_sy-%d)]) call HMT_EMIT};'
                    % (fx, fy, fx, fy), r'HARMATTAN_BRG (-?[0-9.]+)', want=1, timeout=8)
                brg = float(rb[-1].group(1)) if rb else -999.0
                if brg > -900:                                     # oriente le template 2-clusters vers la menace
                    th = math.radians(brg)
                    cls = []
                    for c in dmu:
                        ox, oy = c[0] * REAL_R, c[1] * REAL_R
                        ex = ox * math.cos(th) + oy * math.sin(th)          # composante Est
                        ny = -ox * math.sin(th) + oy * math.cos(th)        # composante Nord
                        cls.append((fx + ex, fy + ny))
                    b.send('private _e=(allUnits select {side _x==east && alive _x && _x distance [%d,%d,0]<120}); '
                           '{ private _t=if ((_forEachIndex mod 2)==0) then {[%.1f,%.1f,0]} else {[%.1f,%.1f,0]}; '
                           '_x setUnitPos "AUTO"; _x doMove _t; } forEach _e;'
                           % (fx, fy, cls[0][0], cls[0][1], cls[1][0], cls[1][1]))
                    print("     [%04d] REPLACEMENT co-evolue -> 2 clusters vers menace (bearing %.0f deg)" % (tick, brg), flush=True)
                    last_repos = drv.focus
            except Exception as e:
                print("     [%04d] replacement echoue: %s" % (tick, str(e)[:50]), flush=True)
        if drv.focus:                                              # tier RAPIDE : orchestration sur les defenseurs du FOB menace
            fx, fy = drv.focus[0], drv.focus[1]
            r = b.query("[[%d,%d,0],10,east] call HMT_ORCH_SNAP;" % (fx, fy), r'HARMATTAN_ORCH (\[.*\]) \| (\[.*\])', want=1, timeout=8)
            if r:
                try: vs = ast.literal_eval(r[-1].group(1))
                except Exception: vs = []
                ids = re.findall(r'(\d+:\d+(?::\d+)*)', r[-1].group(2))
                if vs:
                    with torch.no_grad(): tacs = net(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
                    if len(ids) == len(tacs):
                        b.send("[%s,%s] call HMT_TAC_DISPATCH;" % ("[" + ",".join('"%s"' % i for i in ids) + "]", tacs))
                    print("     [%04d] defense %d agents -> %s" % (tick, len(tacs), dict(Counter(TAC[x] for x in tacs))), flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
