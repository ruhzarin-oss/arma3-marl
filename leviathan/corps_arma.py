#!/usr/bin/env python3
"""corps_arma.py — DÉPLOIE le corps-sous-le-feu APPRIS (corps_bc.pt) sur le VRAI Arma, mesuré sur le banc.
Redéploiement par la COUTURE existante : réutilise l'assemblage d'obs 17 + l'actuateur de shamal_arma.py.
PAS d'officier : tous les soldats visent le FOB = pur test du micro. Mesure : FOB pris + pertes.
À comparer aux baselines Arma (timide ~20% pris, téméraire ~0%)."""
import sys, time, json, argparse, math
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import shamal_arma as SH
from native_bridge import NativeBridge
import torch
from train_koth_gpu import Net
CKPT = "/home/younes/arma3-marl/corps_bc.pt"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--nag", type=int, default=18)
    ap.add_argument("--steps", type=int, default=45); ap.add_argument("--secure", type=float, default=25.0)
    ap.add_argument("--oracle", action="store_true")   # ORACLE : « toujours avancer vers le FOB » via la MÊME couture (calcule le plafond du banc)
    ap.add_argument("--bound_time", type=float, default=1.0)   # COUTURE À BONDS : temps laissé au soldat pour parcourir son bond avant de re-décider (1 décision = 1 bond de ~14m à ~7s)
    a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]; sx, sy = fx, fy + 140
    SH.NAG = a.nag
    b = NativeBridge(port=5816)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "shamal_obs.sqf";'); time.sleep(0.3)
        b.send('call compile preprocessFileLineNumbers "envelop_arma.sqf";'); time.sleep(0.3)
        ld = SH.loadout003()
        r = b.query(SH.setup_sqf(sx, sy, fx, fy, ld), r"HARMATTAN_SHL west=(\d+)", want=1, timeout=120)
        print("CORPS en place : soldats=%s | ZERO LAMBS" % (r[-1].group(1) if r else "?")); return

    if a.cmd == "disarm":
        b.send('if (!isNil "HMT_WPILOT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];')
        print("nettoyé"); return

    # --- run : le micro appris pilote, tous vers le FOB ---
    net = None
    if not a.oracle:
        net = Net(17, 13, 256, 3); net.load_state_dict(torch.load(CKPT, map_location="cpu")); net.eval()
    b.send("private _es = allUnits select {side _x==east && alive _x}; { private _e=_x; { _e reveal [_x,4] } forEach HMT_WPILOT } forEach _es; { private _w=_x; { _w reveal [_x,4] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)
    prev_dmg = [0.0] * a.nag; sup_mem = [False] * a.nag; min_pen = 999.0; took_tick = None; west0 = None; rows = []
    for step in range(a.steps):
        r = b.query("call HMT_SHAMAL_SENSE;", r"HARMATTAN_SHS (.+)", want=1, timeout=12)
        if not r: time.sleep(1); continue
        rows = SH.parse_sense(r[-1].group(1))
        if not rows: time.sleep(1); continue
        n = len(rows); alive = [row[2] > 0.5 for row in rows]
        if west0 is None: west0 = a.nag
        if a.oracle:                                               # ORACLE : cap vers le FOB (rel FOB = -px,-py), à travers la même couture
            acts = [int(round(math.atan2(-row[0], -row[1]) / (math.pi / 4)) % 8) for row in rows]
        else:
            targets = [(fx, fy)] * n                               # tous -> FOB (pas d'officier)
            obs = SH.build_obs(rows, targets, fx, fy, prev_dmg, sup_mem)
            with torch.no_grad(): acts = net.a_logits(obs).argmax(-1).tolist()
        sup_mem = [False] * a.nag
        for i, ac in enumerate(acts):
            if ac == 9 and i < a.nag: sup_mem[i] = True
        b.send("HMT_ACTS=%s; call HMT_SHAMAL_APPLY;" % json.dumps(acts))   # actuateur SHAMAL prouvé (respecte les postures de la politique)
        ax = [fx + row[0] for row in rows]; ay = [fy + row[1] for row in rows]
        pen = min((math.hypot(ax[i] - fx, ay[i] - fy) for i in range(n) if alive[i]), default=999)
        min_pen = min(min_pen, pen)
        if pen < a.secure and took_tick is None: took_tick = step
        na = sum(alive)
        print("  [%02d] vivants=%d/%d ->FOB=%3.0fm" % (step, na, a.nag, pen), flush=True)
        if na == 0: break
        if pen < a.secure: print("  -> FOB PRIS !"); break
        time.sleep(a.bound_time)   # laisse le BOND se compléter (une décision = un bond)
    fr = b.query("call HMT_SHAMAL_SENSE;", r"HARMATTAN_SHS (.+)", want=1, timeout=10)
    rows2 = SH.parse_sense(fr[-1].group(1)) if fr else rows
    wf = sum(1 for row in rows2 if row[2] > 0.5)
    took = took_tick is not None
    print("=== CORPS_BC | FOB pris=%s (tick %s) | pertes %d/%d | dist min %dm ===" % (
        "OUI" if took else "non", took_tick, a.nag - wf, a.nag, round(min_pen)), flush=True)


if __name__ == "__main__":
    main()
