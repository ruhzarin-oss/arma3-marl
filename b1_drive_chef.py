"""Deploie le CHEF COORDONNE en live Arma. Le chef lit la scene globale -> axe commun + roles.
ASSAUT courent sur l'axe (doMove, ensemble) ; APPUI tiennent accroupis et couvrent (tir reflexe).
Coordination visible : l'escouade bouge en UNITE. Soldats existants (pas de re-spawn)."""
import sys, time, re, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
DEV = "cpu"; S = 140.0
b = ArmaBridge()


class Coord(nn.Module):
    def __init__(self, gdim, A, h=256):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(gdim, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.dirh = nn.Linear(h, 8); self.roleh = nn.Linear(h, A * 2); self.v = nn.Linear(h, 1); self.A = A

    def forward(self, o):
        z = self.tr(o); return self.dirh(z), self.roleh(z).view(-1, self.A, 2), self.v(z).squeeze(-1)


WAKE = r'''
HMT_PICKED = 0;
{ _x enableAI "MOVE"; _x enableAI "PATH"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x disableAI "AUTOCOMBAT"; _x disableAI "FSM"; _x setBehaviour "AWARE"; _x forceSpeed 4 } forEach HMT_FR;
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_GUARDS;
diag_log "HARMATTAN_WAKE chef-coord live";
'''

POS = r'''
HMT_CX=20885; HMT_CY=16779;
private _A=""; { _A=_A+format["%1,%2,%3;", round((getPosATL _x select 0)-HMT_CX), round((getPosATL _x select 1)-HMT_CY), alive _x] } forEach HMT_FR;
private _G=""; { _G=_G+format["%1,%2,%3;", round((getPosATL _x select 0)-HMT_CX), round((getPosATL _x select 1)-HMT_CY), alive _x] } forEach HMT_GUARDS;
private _hp=getPosATL HMT_HOSTAGE;
diag_log format ["HARMATTAN_GOBS A=%1 G=%2 H=%3,%4 HD=%5 PK=%6 EX=%7,%8", _A, _G, round((_hp select 0)-HMT_CX), round((_hp select 1)-HMT_CY), damage HMT_HOSTAGE, HMT_PICKED, round((HMT_EXT select 0)-HMT_CX), round((HMT_EXT select 1)-HMT_CY)];
'''

ACT_TPL = r'''
HMT_CX=20885; HMT_CY=16779; HMT_DIR=__DIR__; HMT_ROLE=[__ROLE__];
{ private _i=_forEachIndex; private _p=getPosATL _x;
  if ((HMT_ROLE select _i)==1) then { private _ang=HMT_DIR*45; _x setUnitPos "AUTO"; _x doMove [(_p select 0)+25*sin _ang,(_p select 1)+25*cos _ang,0]; }
  else { _x doMove (getPosATL _x); _x setUnitPos "MIDDLE"; private _ng=objNull; private _nd=1e9; { if (alive _x) then { private _d=_x distance _p; if (_d<_nd) then {_nd=_d;_ng=_x} } } forEach HMT_GUARDS; if (!isNull _ng) then { _x doSuppressiveFire _ng }; };
} forEach HMT_FR;
private _car=objNull; private _cd=1e9; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_cd) then {_cd=_d;_car=_x} } } forEach HMT_FR;
if (_cd < 25) then { HMT_PICKED=1 };
if (HMT_PICKED==1 && !isNull _car) then { HMT_HOSTAGE setPosATL (getPosATL _car); HMT_HOSTAGE doMove (getPosATL _car) };
private _dex=HMT_HOSTAGE distance2D [(HMT_EXT select 0),(HMT_EXT select 1),0];
private _succ=if (HMT_PICKED==1 && _dex<25) then {1} else {0};
diag_log format ["HARMATTAN_STATUS picked=%1 succ=%2 dh=%3 dex=%4 alive=%5", HMT_PICKED, _succ, round _cd, round _dex, ({alive _x} count HMT_FR)];
'''


def query_gobs(timeout=15):
    n = b.send(POS, wait=True, timeout=timeout); time.sleep(0.5)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_GOBS A=(.*?) G=(.*?) H=(-?\d+),(-?\d+) HD=([\d.]+) PK=(\d) EX=(-?\d+),(-?\d+)", ln)
        if m: break
    else: return None
    def units(s, k):
        out = []
        for tok in s.strip().strip(";").split(";"):
            if tok:
                p = tok.split(","); out += [float(p[0]) / S, float(p[1]) / S, 1.0 if p[2].strip() == "true" else 0.0]
        while len(out) < k * 3: out += [0.0, 0.0, 0.0]
        return out[:k * 3]
    ag = units(m.group(1), 9); dg = units(m.group(2), 6)
    h = [float(m.group(3)) / S, float(m.group(4)) / S, float(m.group(5)), float(m.group(6))]
    e = [float(m.group(7)) / S, float(m.group(8)) / S]
    return torch.tensor([ag + dg + h + e], dtype=torch.float32)


def send_act(d, roles, timeout=15):
    sqf = ACT_TPL.replace("__DIR__", str(int(d))).replace("__ROLE__", ",".join(str(int(x)) for x in roles))
    b.send(sqf, wait=True, timeout=timeout); time.sleep(1.6)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_STATUS picked=(\d+) succ=(\d+) dh=(-?\d+) dex=(-?\d+) alive=(\d+)", ln)
        if m: return {"picked": int(m.group(1)), "succ": int(m.group(2)), "dh": int(m.group(3)), "dex": int(m.group(4)), "alive": int(m.group(5))}
    return None


chef = Coord(51, 9).to(DEV); chef.load_state_dict(torch.load("/home/younes/compose-embodiment/chef_coord.pt", map_location=DEV)); chef.eval()
b.send(WAKE, wait=True, timeout=15); time.sleep(1)
print("=== CHEF COORDONNE EN COMMANDE (live) ===", flush=True)
for t in range(200):
    g = query_gobs()
    if g is None: break
    with torch.no_grad():
        dl, rl, _ = chef(g); d = dl.argmax(-1)[0]; roles = rl.argmax(-1)[0].tolist()
    st = send_act(d, roles)
    if t % 6 == 0: print("t=%d dir=%d %s" % (t, int(d), st), flush=True)
    if st and st["succ"]: print(">>> RESCOUSSE COORDONNEE REUSSIE t=%d <<<" % t, flush=True); break
    if st and st["alive"] == 0: print(">>> aneantie t=%d" % t, flush=True); break
print("FIN", flush=True)
