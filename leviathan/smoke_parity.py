#!/usr/bin/env python3
"""smoke_parity.py — smoke-test de PARITE des 10 features de orchestration_arma_voyant.pt.
Pose des cibles west controlees face a un defenseur east, calcule les 10 features EN ARMA (HMT_ORCH_FEATS),
les passe au .pt, verifie : (1) features dans [0,1] et varient, (2) argmax sensé selon la situation."""
import sys, time, re, ast
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
import torch, torch.nn as nn

LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
b = ArmaBridge(mission=MIS, log=LOG)
FN = ["dist", "vis", "behnd", "entr", "expo", "openg", "fire", "gren", "smoke", "alli"]
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]


class Net(nn.Module):
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def tail_hits(tag):
    txt = open(LOG, errors="ignore").read().splitlines()
    return [l for l in txt if tag in l]


def scenario(label, dx, dy, cover_cls):
    """Pose une cible west a (dx,dy) du defenseur ; cover_cls != '' -> un mur entre defenseur et cible."""
    sqf = (
        '[] spawn {'
        'private _u=(allUnits select {side _x==east && alive _x && _x distance [4279,3856,0]<70}) param [0,objNull];'
        'if (isNull _u) exitWith { diag_log "HARMATTAN_SC nodefender"; };'
        'if (!isNil "HMT_SC_T") then { deleteVehicle HMT_SC_T }; if (!isNil "HMT_SC_W") then { deleteVehicle HMT_SC_W };'
        'private _tp=(getPosATL _u) vectorAdd [%d,%d,0];'
        'private _tg=createGroup west; HMT_SC_T=_tg createUnit ["B_Soldier_F", _tp, [], 0, "NONE"];'
        'HMT_SC_T setPosATL _tp; HMT_SC_T disableAI "ALL";'
        'HMT_SC_W=objNull; if ("%s" != "") then { HMT_SC_W=createVehicle ["%s",(getPosATL _u) vectorAdd [%d,%d,0],[],0,"CAN_COLLIDE"]; };'
        'HMT_SC_T setVelocity [0,0,0];'
        '_u reveal [HMT_SC_T, 4]; uiSleep 0.6;'
        'private _f=[_u] call HMT_ORCH_FEATS;'
        'diag_log format["HARMATTAN_SC %s known=%%1 v=%%2", _u knowsAbout HMT_SC_T, _f];'
        '};'
    ) % (dx, dy, cover_cls, cover_cls, dx // 2, dy // 2, label)
    b.send(sqf)
    time.sleep(3.5)
    hits = tail_hits("HARMATTAN_SC " + label)
    if not hits:
        return None
    m = re.search(r"known=(\S+) v=(\[[^\]]*\])", hits[-1])
    if not m:
        return (label, None, None)
    return (label, m.group(1), ast.literal_eval(m.group(2)))


b.send('call compile preprocessFileLineNumbers "orch_features.sqf";')
time.sleep(1.5)

# scenarios : (label, dx, dy, mur-entre-les-deux)
scn = [
    ("PROCHE_OUVERT", 0, 35, ""),          # ennemi proche, a decouvert
    ("LOIN_OUVERT",   0, 220, ""),         # ennemi loin (retranche-like distance)
    ("DERRIERE_MUR",  0, 45, "Land_HBarrier_3_F"),  # ennemi cache derriere un mur
]
net = Net(); net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt", map_location="cpu")); net.eval()

rows = []
for label, dx, dy, cov in scn:
    r = scenario(label, dx, dy, cov)
    rows.append(r)

print("        " + " ".join("%-5s" % f for f in FN) + "   known -> tactique")
cols = [[] for _ in range(10)]
with torch.no_grad():
    for r in rows:
        if r is None:
            print("  (scenario sans retour)"); continue
        label, known, v = r
        if v is None:
            print("  %-14s : features non lues" % label); continue
        lg, _ = net(torch.tensor([v], dtype=torch.float32)); am = int(lg.argmax())
        for i in range(10):
            cols[i].append(v[i])
        print("%-14s " % label + " ".join("%-5.2f" % x for x in v) + "  k=%-4s -> %s" % (known, TAC[am]))

print("\n=== plage par feature (dans [0,1] et varie ?) ===")
for i in range(10):
    if cols[i]:
        print("  %-6s %.2f .. %.2f" % (FN[i], min(cols[i]), max(cols[i])))
