#!/usr/bin/env python3
"""officer_live.py — ETAGE 1 : l'officier Qwen sur le VRAI theatre server_fob.
Pont NATIF (TCP 5816, fiable) ; SITREP via fonction HMT_SITREP (officer_sit.sqf) ; Qwen2.5:14b (Ollama) decide.
Injecte une menace (assaut WEST pres d'un FOB), puis N cycles ; log SITREP + raisonnement + ordres + focus.
Etage isole (pas de driver) : apply = stub qui journalise le focus."""
import sys, time, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from arma_bridge import ArmaBridge
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory
from officer import OfficerLoop, qwen_ollama, make_apply

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"


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
    ap.add_argument("--cycles", type=int, default=6)
    ap.add_argument("--fob", default="M1")
    ap.add_argument("--nothreat", action="store_true")
    a = ap.parse_args()

    try:
        b = NativeBridge(port=5816); BR = "NATIF TCP 5816"
    except Exception as e:
        b = ArmaBridge(mission=MIS, log=LOG); BR = "FICHIER (natif indispo: %s)" % e
    print("[pont] %s" % BR, flush=True)

    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    coords = "[" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "]"
    b.send("HMT_FOB_ANCHORS = %s;" % coords)
    b.send('call compile preprocessFileLineNumbers "officer_sit.sqf";')
    time.sleep(1.0)
    fobpos = next(([f[1], f[2], 0] for f in FOBS if f[0] == a.fob), [4279, 3856, 0])

    st = OfficerState(bridge=b)                                   # pour parse()

    def read_sit(tick):
        r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=12)
        return st.parse(r[-1].group(1).rstrip('"').strip(), tick) if r else None

    def measure(sit0, now_tick):
        now = read_sit(now_tick) or sit0
        thr0 = sum(1 for f in sit0["fobs"] if f["threatened"])
        thrN = sum(1 for f in now["fobs"] if f["threatened"])
        return {"cibles_intactes_frac": (now["targets_intact"] / now["targets_total"]) if now["targets_total"] else 1.0,
                "fobs_tenus_frac": sum(1 for f in now["fobs"] if f["held"]) / max(1, len(now["fobs"])),
                "pertes_amies": max(0, sit0["total_force"] - now["total_force"]),
                "pertes_ennemies": max(0, sit0["total_threat"] - now["total_threat"]),
                "exposition": 1 if thrN > thr0 else 0}

    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")

    class Stub:
        focus = None
    drv = Stub()
    loop = OfficerLoop(mem, qwen=qwen_ollama, apply_fn=make_apply(drv))

    if not a.nothreat:
        print("[menace] injection assaut WEST (12) pres de %s %s..." % (a.fob, fobpos[:2]), flush=True)
        inject_threat(b, fobpos)
        time.sleep(22)
    print("=== ETAGE 1 : OFFICIER QWEN LIVE (server_fob :3902) ===", flush=True)
    for tick in range(a.cycles):
        sit = read_sit(tick)
        if not sit:
            print("  [%d] SITREP illisible — retry" % tick, flush=True)
            time.sleep(6); continue
        thr = [(f["name"], f["contacts"]) for f in sit["fobs"] if f["threatened"]]
        t0 = time.time()
        orders = loop.decide(sit, tick, float(tick))
        loop.settle_outcomes(tick, measure)
        appr = (orders.get("appreciation", "") or "")[:110]
        ords = [(o.get("fob"), o.get("action")) for o in orders.get("ordres", [])]
        print("  [%d] menaces=%s force=%d cibles=%d/%d | Qwen %.1fs: \"%s\" | ORDRES=%s | focus=%s" %
              (tick, thr or "-", sit["total_force"], sit["targets_intact"], sit["targets_total"],
               time.time() - t0, appr, ords, drv.focus), flush=True)
        time.sleep(8)
    print("=== FIN etage 1 : %d decisions dans le RAG ===" % mem.count("theatre"), flush=True)


if __name__ == "__main__":
    main()
