#!/usr/bin/env python3
"""clash_live.py — CO-EVOLUTION pas 0 : les DEUX camps equipes du repertoire tactique, affrontement live.
  EAST (le pays, defenseur) : officier Qwen -> focus -> orchestration -> executeurs.
  WEST (l'attaquant)        : orchestration -> executeurs (meme .pt, compose avec le reflexe d'assaut).
Les deux cerveaux tactiques tournent en meme temps sur le vrai Arma. La LEAGUE anti-oubli (entrainement) = coevo2.py, a part."""
import sys, time, argparse, ast, re
from collections import Counter
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory
from officer import OfficerLoop, qwen_ollama, make_apply
import torch, torch.nn as nn

TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
CKPT = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


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


def orch_side(b, net, ctr, side_sqf):
    r = b.query("[[%d,%d,0],8,%s] call HMT_ORCH_SNAP;" % (ctr[0], ctr[1], side_sqf),
                r'HARMATTAN_ORCH (\[.*\]) \| (\[.*\])', want=1, timeout=8)
    if not r:
        return None
    try:
        vs = ast.literal_eval(r[-1].group(1))
    except Exception:
        vs = []
    ids = re.findall(r'(\d+:\d+(?::\d+)*)', r[-1].group(2))
    if not vs:
        return {"n": 0, "dist": {}}
    with torch.no_grad():
        tacs = net(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
    if len(ids) == len(tacs):
        ids_sqf = "[" + ",".join('"%s"' % i for i in ids) + "]"
        b.send("[%s,%s] call HMT_TAC_DISPATCH;" % (ids_sqf, tacs))
    return {"n": len(tacs), "dist": dict(Counter(TAC[t] for t in tacs))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=24)
    ap.add_argument("--fob", default="M1")
    ap.add_argument("--east", default="/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt")
    ap.add_argument("--west", default="/home/younes/arma3-marl/leviathan/orchestration_arma_league.pt")
    a = ap.parse_args()
    b = NativeBridge(port=5816)
    print("[pont] NATIF TCP 5816", flush=True)
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    coords = "[" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "]"
    b.send("HMT_FOB_ANCHORS = %s;" % coords)
    for f in ("officer_sit.sqf", "orch_features_v6.sqf", "tactics_exec_v2.sqf"):
        b.send('call compile preprocessFileLineNumbers "%s";' % f)
    time.sleep(1.2)
    fobpos = next(([f[1], f[2], 0] for f in FOBS if f[0] == a.fob), [4279, 3856, 0])
    st = OfficerState(bridge=b)

    def read_sit(tick):
        r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=12)
        return st.parse(r[-1].group(1).rstrip('"').strip(), tick) if r else None

    def load_net(p):
        n = OrchNet(); n.load_state_dict(torch.load(p, map_location="cpu")); n.eval(); return n
    net_e = load_net(a.east); net_w = load_net(a.west)
    print("[cerveaux] EAST=%s | WEST=%s" % (a.east.split("/")[-1], a.west.split("/")[-1]), flush=True)
    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")

    class Stub:
        focus = None
    drv = Stub()
    loop = OfficerLoop(mem, qwen=qwen_ollama, apply_fn=make_apply(drv))

    print("[assaut] WEST (16) sur %s %s..." % (a.fob, fobpos[:2]), flush=True)
    spawn_assault(b, fobpos); time.sleep(22)
    print("=== CO-EVOLUTION pas 0 : EAST (officier+orch) vs WEST (orch), les 2 tactiques (server_fob :3902) ===", flush=True)

    for tick in range(a.ticks):
        if tick % 5 == 0:
            sit = read_sit(tick)
            if sit:
                loop.decide(sit, tick, float(tick))
                thr = [(f["name"], f["contacts"]) for f in sit["fobs"] if f["threatened"]]
                print("[%02d] OFFICIER EAST menaces=%s -> FOCUS=%s" % (tick, thr or "-", drv.focus), flush=True)
        ctr = drv.focus or fobpos
        de = orch_side(b, net_e, ctr, "east")                         # defenseurs EAST (voyant)
        at = orch_side(b, net_w, ctr, "west")                         # attaquants WEST (league durci)
        de_s = ("%d %s" % (de["n"], de["dist"])) if de else "-"
        at_s = ("%d %s" % (at["n"], at["dist"])) if at else "-"
        print("     [%02d] EAST-def: %s  |  WEST-atk: %s" % (tick, de_s, at_s), flush=True)
        time.sleep(2)
    ro = b.query(("private _f=[%d,%d,0]; private _wa=allUnits select {side _x==west && alive _x}; "
                  "private _pen=999; { _pen=_pen min (_x distance _f) } forEach _wa; "
                  "private _en=count (allUnits select {side _x==east && alive _x && _x distance _f < 200}); "
                  "diag_log format[\"HARMATTAN_OUTCOME wvivants=%%1 penetration=%%2m est_pres=%%3\", count _wa, round _pen, _en];") % (fobpos[0], fobpos[1]),
                 r'HARMATTAN_OUTCOME (.+)', want=1, timeout=10)
    print("[OUTCOME %s] %s" % (a.west.split("/")[-1], ro[-1].group(1) if ro else "?"), flush=True)
    print("=== FIN clash ===", flush=True)


if __name__ == "__main__":
    main()
