"""B1 — rejoue l'episode LIVE en ENREGISTRANT les positions, puis rend un mp4 vue-de-dessus.
Memes mecaniques que b1_loop (d6 gele pilote via setVelocity). Fond = grid solide du replica (vrais batiments)."""
import sys, time, re, torch, numpy as np
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
import imageio.v2 as imageio
DEV = "cpu"; S = 140.0
b = ArmaBridge()

SPAWN = r'''
[] spawn {
  createCenter west; createCenter east; createCenter civilian;
  HMT_C = [20885,16779,0]; HMT_OBJ = HMT_C; HMT_INS = [(HMT_C select 0),(HMT_C select 1)-90,0]; HMT_EXT = HMT_INS; HMT_PICKED = 0;
  if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach (HMT_FR + HMT_GUARDS); if (!isNull HMT_HOSTAGE) then { deleteVehicle HMT_HOSTAGE }; };
  private _civg = createGroup civilian; HMT_HOSTAGE = _civg createUnit ["B_Soldier_F", HMT_C, [], 0, "CAN_COLLIDE"];
  HMT_HOSTAGE setCaptive true; HMT_HOSTAGE disableAI "ALL"; HMT_HOSTAGE setBehaviour "CARELESS"; HMT_HOSTAGE setPosATL HMT_C;
  private _gg = createGroup east; HMT_GUARDS = [];
  for "_i" from 0 to 8 do { private _a=_i*40; private _gp=[(HMT_C select 0)+25*cos _a,(HMT_C select 1)+25*sin _a,0]; private _u=_gg createUnit ["O_Soldier_F",_gp,[],0,"FORM"]; HMT_GUARDS pushBack _u; };
  private _bg = createGroup west; HMT_FR = [];
  for "_i" from 0 to 8 do { private _sp=[(HMT_INS select 0)+(_i mod 3)*4-4,(HMT_INS select 1)+(floor(_i/3))*4,0]; private _u=_bg createUnit ["B_Soldier_F",_sp,[],0,"NONE"];
     _u disableAI "FSM"; _u disableAI "PATH"; _u disableAI "MOVE"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "AWARE"; _u setUnitPos "UP"; HMT_FR pushBack _u; };
  diag_log format ["HARMATTAN_SPAWN fr=%1 g=%2 h=%3", count HMT_FR, count HMT_GUARDS, !isNull HMT_HOSTAGE];
};
'''

PERC = r'''
HMT_S = 140; HMT_CX = 20885; HMT_CY = 16779;
{
  private _u=_x; private _i=_forEachIndex; private _p=getPosATL _u; private _ax=(_p select 0)-HMT_CX; private _ay=(_p select 1)-HMT_CY;
  private _hp=getPosATL HMT_HOSTAGE; private _hx=(_hp select 0)-HMT_CX; private _hy=(_hp select 1)-HMT_CY;
  private _dhx=_hx-_ax; private _dhy=_hy-_ay; private _dh=sqrt(_dhx*_dhx+_dhy*_dhy)+0.001;
  private _ex=(HMT_EXT select 0)-HMT_CX-_ax; private _ey=(HMT_EXT select 1)-HMT_CY-_ay; private _de=sqrt(_ex*_ex+_ey*_ey)+0.001;
  private _ng=objNull; private _nd=1e9; { if (alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_nd) then {_nd=_d;_ng=_x}; }; } forEach HMT_GUARDS;
  private _gdx=0; private _gdy=0; private _gd=1; private _los=0;
  if (!isNull _ng) then { private _q=getPosATL _ng; _gdx=((_q select 0)-HMT_CX)-_ax; _gdy=((_q select 1)-HMT_CY)-_ay; _gd=sqrt(_gdx*_gdx+_gdy*_gdy)+0.001;
     private _gp=getPosASL _ng; private _aps=getPosASL _u; _los=if (terrainIntersectASL [[(_aps select 0),(_aps select 1),(_aps select 2)+0.9],[(_gp select 0),(_gp select 1),(_gp select 2)+0.9]]) then {0} else {1}; };
  private _nt=objNull; private _td=1e9; { if (_x!=_u && alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_td) then {_td=_d;_nt=_x}; }; } forEach HMT_FR;
  private _tdx=0; private _tdy=0; private _tdist=1;
  if (!isNull _nt) then { private _q=getPosATL _nt; _tdx=((_q select 0)-HMT_CX)-_ax; _tdy=((_q select 1)-HMT_CY)-_ay; _tdist=sqrt(_tdx*_tdx+_tdy*_tdy)+0.001; };
  private _th0=if (!isNull _ng) then { _gdy atan2 _gdx } else {0}; private _shell=[];
  for "_k" from 0 to 11 do { private _ang=_th0+_k*30; private _ddx=cos _ang; private _ddy=sin _ang; private _sv=1;
     for "_s" from 1 to 20 do { private _r=_s/20*60; private _qx=(_p select 0)+_r*_ddx; private _qy=(_p select 1)+_r*_ddy;
        if (count (nearestObjects [[_qx,_qy,(_p select 2)],["House","Wall","Rock"],3])>0) exitWith {_sv=_s/20}; };
     _shell pushBack _sv; };
  private _dmg=damage _u; private _pk=if (isNil "HMT_PICKED") then {0} else {HMT_PICKED};
  private _o=_shell+[_dmg,_dhx/_dh,_dhy/_dh,(_dh/HMT_S) min 2,_ex/_de,_ey/_de,(_de/HMT_S) min 2,_gdx/_gd,_gdy/_gd,(_gd/HMT_S) min 2,_los,_tdx/_tdist,_tdy/_tdist,(_tdist/HMT_S) min 2,_pk,damage HMT_HOSTAGE,_dmg];
  diag_log format ["HARMATTAN_AOBS %1 %2", _i, _o];
} forEach HMT_FR;
'''

ACT_TPL = r'''
HMT_CX=20885; HMT_CY=16779; HMT_ACT = [__ACTS__]; HMT_SPD = 6;
{ private _i=_forEachIndex; private _a=HMT_ACT select _i;
  if (_a < 8) then { private _ang=_a*45; _x setVelocity [HMT_SPD*sin _ang, HMT_SPD*cos _ang, 0]; } else { _x setVelocity [0,0,0]; };
} forEach HMT_FR;
private _car=objNull; private _cd=1e9; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_cd) then {_cd=_d;_car=_x}; }; } forEach HMT_FR;
if (_cd < 25) then { HMT_PICKED=1; };
if (HMT_PICKED==1 && !isNull _car) then { HMT_HOSTAGE setPosATL (getPosATL _car); };
private _dex=HMT_HOSTAGE distance2D [(HMT_EXT select 0),(HMT_EXT select 1),0];
private _succ=if (HMT_PICKED==1 && _dex<25) then {1} else {0};
private _A=""; { _A=_A+format["%1,%2,%3;", round((getPosATL _x select 0)-HMT_CX), round((getPosATL _x select 1)-HMT_CY), alive _x] } forEach HMT_FR;
private _G=""; { _G=_G+format["%1,%2,%3;", round((getPosATL _x select 0)-HMT_CX), round((getPosATL _x select 1)-HMT_CY), alive _x] } forEach HMT_GUARDS;
private _hp=getPosATL HMT_HOSTAGE;
diag_log format ["HARMATTAN_STATUS picked=%1 succ=%2 dh=%3 dex=%4 alive=%5", HMT_PICKED, _succ, round _cd, round _dex, ({alive _x} count HMT_FR)];
diag_log format ["HARMATTAN_POS A=%1 G=%2 H=%3,%4 P=%5", _A, _G, round((_hp select 0)-HMT_CX), round((_hp select 1)-HMT_CY), HMT_PICKED];
'''


def read_aobs(timeout=15):
    n = b.send(PERC, wait=True, timeout=timeout); time.sleep(0.7)
    lines = b._log_lines(); idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
    obs = {}
    for ln in lines[idx:]:
        m = re.search(r"HARMATTAN_AOBS (\d+) \[([^\]]+)\]", ln)
        if m: obs[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
    return torch.tensor([obs[k] for k in sorted(obs)], dtype=torch.float32) if obs else None


def parse_units(s):
    out = []
    for tok in s.strip().strip(";").split(";"):
        if not tok: continue
        p = tok.split(",")
        if len(p) >= 3: out.append((float(p[0]), float(p[1]), p[2].strip() == "true"))
    return out


def send_act(acts, timeout=15):
    sqf = ACT_TPL.replace("__ACTS__", ",".join(str(int(a)) for a in acts))
    n = b.send(sqf, wait=True, timeout=timeout); time.sleep(0.5)
    lines = b._log_lines(); st = None; pos = None
    for ln in reversed(lines):
        if st is None:
            m = re.search(r"HARMATTAN_STATUS picked=(\d+) succ=(\d+) dh=(-?\d+) dex=(-?\d+) alive=(\d+)", ln)
            if m: st = {"picked": int(m.group(1)), "succ": int(m.group(2)), "dh": int(m.group(3)), "dex": int(m.group(4)), "alive": int(m.group(5))}
        if pos is None:
            m = re.search(r"HARMATTAN_POS A=(.*?) G=(.*?) H=(-?\d+),(-?\d+) P=(\d)", ln)
            if m: pos = {"A": parse_units(m.group(1)), "G": parse_units(m.group(2)), "H": (float(m.group(3)), float(m.group(4))), "P": int(m.group(5))}
        if st and pos: break
    return st, pos


# --- rendu ---
R = np.load("/home/younes/arma3-marl/replica.npz"); solid = R["solid"]; GS = solid.shape[0]
EXT = (0.0, -90.0)


def px(x, y):
    cx = int(((x / S) * 0.5 + 0.5) * (GS - 1)); cy = int(((y / S) * 0.5 + 0.5) * (GS - 1))
    return min(max(cx, 0), GS - 1), min(max(cy, 0), GS - 1)


def dot(img, x, y, col, r=1):
    cx, cy = px(x, y)
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            img[min(max(cy + dy, 0), GS - 1), min(max(cx + dx, 0), GS - 1)] = col


def frame(fr):
    img = np.full((GS, GS, 3), 245, dtype=np.uint8); img[solid > 0.5] = [120, 120, 120]
    dot(img, EXT[0], EXT[1], [255, 160, 0], 2)
    for (gx, gy, al) in fr["G"]: dot(img, gx, gy, [210, 40, 40] if al else [160, 160, 160], 1)
    dot(img, fr["H"][0], fr["H"][1], [30, 200, 30], 2)
    for (ax, ay, al) in fr["A"]: dot(img, ax, ay, [40, 90, 235] if al else [90, 90, 160], 1)
    return np.repeat(np.repeat(img, 6, 0), 6, 1)


net = Net(29, 10, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); net.eval()
print("d6 charge. spawn + enregistrement...", flush=True)
b.send(SPAWN, wait=True, timeout=20); time.sleep(3)
frames = []
for t in range(240):
    obs = read_aobs()
    if obs is None: break
    with torch.no_grad(): act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
    st, pos = send_act(act.tolist())
    if pos: frames.append(pos)
    if t % 20 == 0: print("t=%d %s frames=%d" % (t, st, len(frames)), flush=True)
    if st and st["succ"]:
        print(">>> SUCCES t=%d, j'enregistre encore 6 frames <<<" % t, flush=True)
        for _ in range(6):
            _, p2 = send_act([8] * 9)
            if p2: frames.append(p2)
        break
    if st and st["alive"] == 0: break
print("rendu de %d frames..." % len(frames), flush=True)
imgs = [frame(f) for f in frames]
imageio.mimwrite("/home/younes/arma3-marl/b1_rescue_hard.mp4", imgs, fps=10, macro_block_size=1)
print("VIDEO -> b1_rescue_hard.mp4 (%d frames)" % len(imgs), flush=True)
