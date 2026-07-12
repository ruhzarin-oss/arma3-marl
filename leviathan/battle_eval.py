#!/usr/bin/env python3
"""battle_eval.py — F.2 : LA FONCTION DE REWARD LIVE.
Joue N batailles d'assaut avec un cerveau WEST donne (EAST = voyant fixe), mesure l'ISSUE REELLE
(penetration vers le FOB + survie WEST + attrition des defenseurs) -> score de succes MOYEN.
--compare : league vs voyant, meme defense, moyennes cote a cote (tue le bruit d'une bataille)."""
import sys, time, argparse, ast, re
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import FOBS
import torch, torch.nn as nn

LEV = "/home/younes/arma3-marl/leviathan/"
CKV = LEV + "orchestration_arma_voyant.pt"
CKL = LEV + "orchestration_arma_league.pt"


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def load_net(p):
    n = OrchNet(); n.load_state_dict(torch.load(p, map_location="cpu")); n.eval(); return n


def spawn_assault(b, fob, n=16):
    sqf = ('[] spawn { if (!isNil "HMT_ATK") then { { deleteVehicle _x } forEach HMT_ATK }; '
           'HMT_ATK_G = createGroup west; HMT_ATK = []; '
           'for "_i" from 0 to %d do { private _p = [%d - 170 + (_i mod 5) * 14, %d - 150 + (floor (_i / 5)) * 14, 0]; '
           'private _u = HMT_ATK_G createUnit ["B_recon_F", _p, [], 0, "FORM"]; '
           '_u setSkill 0.6; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u addMagazine "SmokeShell"; HMT_ATK pushBack _u; }; '
           'HMT_ATK_G move [%d, %d, 0]; sleep 3; '
           '{ private _r = _x; { _x reveal [_r, 3] } forEach (allUnits select {side _x == east && alive _x && _x distance _r < 500}); } forEach HMT_ATK; '
           '};') % (n - 1, fob[0], fob[1], fob[0], fob[1])
    b.send(sqf)


def snap_dispatch(b, net, ctr, side):
    r = b.query("[[%d,%d,0],10,%s] call HMT_ORCH_SNAP;" % (ctr[0], ctr[1], side),
                r'HARMATTAN_ORCH (\[.*\]) \| (\[.*\])', want=1, timeout=8)
    if not r:
        return
    try:
        vs = ast.literal_eval(r[-1].group(1))
    except Exception:
        vs = []
    ids = re.findall(r'(\d+:\d+(?::\d+)*)', r[-1].group(2))
    if not vs:
        return
    with torch.no_grad():
        tacs = net(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
    if len(ids) == len(tacs):
        b.send("[%s,%s] call HMT_TAC_DISPATCH;" % ("[" + ",".join('"%s"' % i for i in ids) + "]", tacs))


def measure(b, fob):
    sqf = ("private _f=[%d,%d,0]; private _wa=allUnits select {side _x==west && alive _x}; "
           "private _pen=999; { _pen=_pen min (_x distance _f) } forEach _wa; "
           "private _en=count (allUnits select {side _x==east && alive _x && _x distance _f<200}); "
           "(format[\"HARMATTAN_M wv=%%1 pen=%%2 en=%%3\", count _wa, round _pen, _en]) call HMT_EMIT;") % (fob[0], fob[1])
    r = b.query(sqf, r'HARMATTAN_M wv=(\d+) pen=(\d+) en=(\d+)', want=1, timeout=10)
    return (int(r[-1].group(1)), int(r[-1].group(2)), int(r[-1].group(3))) if r else None


def battle(b, net_e, net_w, fob, ticks=10):
    b.send("{ private _v=missionNamespace getVariable [_x,[]]; { deleteVehicle _x } forEach _v; } forEach [\"HMT_ATK\"];")
    time.sleep(2)
    spawn_assault(b, fob); time.sleep(18)
    m0 = measure(b, fob) or (16, 160, 20)
    drive = ('if (!isNil "HMT_ATK_G") then { HMT_ATK_G move [%d,%d,0]; '
             '{ _x setUnitPos "UP"; _x forceSpeed -1; } forEach units HMT_ATK_G; };') % (fob[0], fob[1])
    for k in range(ticks):
        snap_dispatch(b, net_e, fob, "east")
        snap_dispatch(b, net_w, fob, "west")
        b.send(drive)                                             # ELAN STRATEGIQUE en DERNIER : l'avance vers le FOB prime sur le mouvement tactique (fumi/grenade/suppr se superposent)
        time.sleep(2)
    m1 = measure(b, fob) or m0
    wv, pen, en = m1
    start_pen = max(m0[1], 1)
    penetr = max(0.0, (start_pen - pen) / start_pen)
    surv = wv / 16.0
    attr = max(0.0, (m0[2] - en) / max(m0[2], 1))
    score = 0.5 * penetr + 0.2 * surv + 0.3 * attr
    return {"wv": wv, "pen": pen, "en": en, "penetr": penetr, "surv": surv, "attr": attr, "score": score}


def eval_policy(b, net_e, net_w, fob, n, ticks, label):
    scores = []
    for i in range(n):
        r = battle(b, net_e, net_w, fob, ticks)
        scores.append(r["score"])
        print("  [%s b%d] wv=%d pen=%dm en=%d | penetr=%.2f surv=%.2f attr=%.2f -> score=%.3f"
              % (label, i, r["wv"], r["pen"], r["en"], r["penetr"], r["surv"], r["attr"], r["score"]), flush=True)
    m = sum(scores) / len(scores)
    print("  == %s : score MOYEN = %.3f  (%d batailles) ==" % (label, m, n), flush=True)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--ticks", type=int, default=10)
    ap.add_argument("--fob", default="M1")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--west", default=CKL)
    a = ap.parse_args()
    b = NativeBridge(port=5816)
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    for f in ("orch_features_v6.sqf", "tactics_exec_v2.sqf"):
        b.send('call compile preprocessFileLineNumbers "%s";' % f)
    time.sleep(1.0)
    fobpos = next(([f[1], f[2], 0] for f in FOBS if f[0] == a.fob), [4279, 3856, 0])
    net_e = load_net(CKV)
    print("=== F.2 REWARD LIVE : score = 0.5*penetration + 0.3*attrition + 0.2*survie ===", flush=True)
    if a.compare:
        ml = eval_policy(b, net_e, load_net(CKL), fobpos, a.n, a.ticks, "LEAGUE")
        mv = eval_policy(b, net_e, load_net(CKV), fobpos, a.n, a.ticks, "VOYANT")
        print("\n=== VERDICT : LEAGUE=%.3f  vs  VOYANT=%.3f  -> %s ===" %
              (ml, mv, "league gagne" if ml > mv else ("voyant gagne" if mv > ml else "egalite")), flush=True)
    else:
        eval_policy(b, net_e, load_net(a.west), fobpos, a.n, a.ticks, a.west.split("/")[-1])
    b.send("{ private _v=missionNamespace getVariable [_x,[]]; { deleteVehicle _x } forEach _v; } forEach [\"HMT_ATK\"];")


if __name__ == "__main__":
    main()
