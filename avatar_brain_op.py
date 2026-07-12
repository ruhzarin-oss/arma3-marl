"""avatar_brain_op — EPREUVE OPERATIONNELLE : le cerveau APPRIS (soldier_suffer.pt) pilote le vrai soldat Arma.
Pont d'obs = les 24 features EXACTES du sandbox (base9 + coque12+degats + 2 suffer), calculees cote Arma.
Mapping actions = 8 caps (doMove) + HOLD (doStop) + SUPPRESS (doSuppressiveFire). Aucune feature inventee.
args: server_idx dist n_en skill seed cycles checkpoint"""
import time, re, sys, math
import torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
DIST = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
N_EN = int(sys.argv[3]) if len(sys.argv) > 3 else 3
SKILL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 41
CYCLES = int(sys.argv[6]) if len(sys.argv) > 6 else 150
CK = sys.argv[7] if len(sys.argv) > 7 else "soldier_suffer.pt"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
S = 200.0; R_SHELL = 60.0; FIRE = 110.0; CELL = (2 * S) / 64.0   # echelle/portee = sandbox

# cerveau appris : Net(obs_dim=24, n_actions=10) — meme archi/obs que l'entrainement
net = Net(24, 10, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/" + CK, map_location=DEV)); net.eval()
ACT = ["N", "NE", "E", "SE", "S", "SO", "O", "NO", "TENIR", "SUPPR"]

env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
start = (OBJ[0] + 10, OBJ[1] - DIST)
env.spawn({"AV": start}, [(OBJ[0], OBJ[1], N_EN, 14)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x allowFleeing 0; } forEach units _g;'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill %.2f; _x reveal (AV select 0); } forEach HMT_EN;' % SKILL, wait=True)
# engagement FORCE : les ennemis ciblent activement l'avatar (garantir LOS+feu pour eprouver le combat)
env.b.send('{ _x reveal [(AV select 0), 4]; _x doWatch (AV select 0); _x doTarget (AV select 0); } forEach HMT_EN;', wait=True)
time.sleep(2)
print("=== EPREUVE OP : %s | server%d dist=%.0f n_en=%d skill=%.2f ===" % (CK, SRV, DIST, N_EN, SKILL), flush=True)
TRACE = open("/tmp/op_trace.csv", "w")
TRACE.write("OBJ,%d,%d\n" % (OBJ[0], OBJ[1]))

# requete = TOUTES les mesures brutes pour reconstruire les 24 features
SENSE = (
    'private _u = AV select 0; private _p = getPosATL _u;'
    ' diag_log format ["AV %1 %2 %3 %4 %5", round(_p#0), round(_p#1), round(getDir _u), round((getDammage _u)*1000), round((getSuppression _u)*100)];'
    ' private _near = objNull; private _bnd = 1e9;'
    ' { if (alive _x) then { private _dd = _u distance _x; if (_dd < _bnd) then {_bnd = _dd; _near = _x}; }; } forEach HMT_EN;'
    ' { private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; private _vis = 0;'
    '   if (alive _e && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
    '   diag_log format ["EN %1 %2 %3 %4 %5", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100), _vis]; } forEach HMT_EN;'
    ' private _tb = if (isNull _near) then {getDir _u} else {_u getDir _near};'        # cap monde vers la menace
    ' private _o = getPosASL _u; _o set [2, (_o#2) + 0.9]; private _s = "";'           # coque centree menace
    ' for "_i" from 0 to 11 do { private _a = _tb + _i*30;'
    '   private _dir = [sin _a, cos _a, 0]; private _to = _o vectorAdd (_dir vectorMultiply 60);'
    '   private _h = lineIntersectsSurfaces [_o, _to, _u];'
    '   private _d = if (count _h == 0) then {60} else {_o distance ((_h select 0) select 0)};'
    '   _s = _s + format ["%1 ", round _d]; };'
    ' diag_log format ["SHELL %1", _s];'
    ' private _nt = 0; { if (alive _x && {(_u distance _x) < 110} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _x, _u, _x])) == 0}) then { _nt = _nt + 1; }; } forEach HMT_EN;'
    ' private _n = surfaceNormal _p;'
    ' diag_log format ["AUX %1 %2", _nt, round((1 - (_n#2)) * 1000)];'                 # nb menacant, pente(approx)
    ' diag_log "SENSEND";')

gx, gy = OBJ
px = py = hdg = 0; dmg = 0.0; prev_dmg = 0.0
t_start = time.time(); hz = []; outcome = "timeout"; took_fire = False; ever_en = False
acts_hist = []


def build_obs(px, py, shell, en_list, n_threat, slope, dmg, dmg_prev):
    apx = (px - gx) / S; apy = (py - gy) / S
    alive_en = [(ex, ey, ed, ev) for (ex, ey, ed, ev) in en_list if ed < 70]
    if alive_en:
        known = min(alive_en, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2)
        nd = math.hypot(known[0] - px, known[1] - py) / S
        los = float(min((e for e in alive_en), key=lambda e: (e[0]-px)**2+(e[1]-py)**2)[3])
    else:
        nd = 1.0; los = 0.0
    dcover = (min(shell) / 400.0)                              # min coque (m) -> ~champ dcover sandbox
    last_in = max(0.0, dmg - dmg_prev)
    base = [apx, apy, -apx, -apy, 1.0, slope / 5.0, dcover, los, nd]
    shell13 = [s / R_SHELL for s in shell] + [dmg]
    suffer2 = [min(last_in * 5.0, 1.0), n_threat / max(N_EN, 1)]
    return torch.tensor([base + shell13 + suffer2], dtype=torch.float32, device=DEV)


for c in range(CYCLES):
    t0 = time.time()
    ls = env._query(SENSE, settle=0.08)
    got = False; en_list = []; shell = [R_SHELL] * 12; n_threat = 0; slope = 0.0
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if m:
            got = True; px = int(m.group(1)); py = int(m.group(2)); hdg = int(m.group(3))
            dmg = int(m.group(4)) / 1000.0
        me = re.search(r"EN (\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            en_list.append((int(me.group(2)), int(me.group(3)), int(me.group(4)), int(me.group(5))))
        msh = re.search(r"SHELL ([\d ]+)", l)
        if msh:
            vv = [int(x) for x in msh.group(1).split()]
            if len(vv) == 12:
                shell = vv
        ma = re.search(r"AUX (\d+) (\d+)", l)
        if ma:
            n_threat = int(ma.group(1)); slope = int(ma.group(2)) / 1000.0
    if not got:
        time.sleep(0.05); continue
    if dmg > 0.0 or n_threat > 0:
        took_fire = took_fire or (dmg > 0.0)
    if dmg >= 0.9:
        outcome = "SOLDAT TOMBE"; print("  t=%.0fs : %s" % (time.time() - t_start, outcome), flush=True); break
    alive_en = [e for e in en_list if e[2] < 70]
    if len(en_list) >= N_EN:
        ever_en = ever_en or (len(alive_en) > 0)
    if ever_en and len(alive_en) == 0:
        outcome = "OPFOR NEUTRALISE"; print("  t=%.0fs : VICTOIRE" % (time.time() - t_start), flush=True); break

    obs = build_obs(px, py, shell, en_list, n_threat, slope, dmg, prev_dmg)
    with torch.no_grad():
        a = int(net.a_logits(obs).argmax(-1).item())
    acts_hist.append(a); prev_dmg = dmg
    row = "%d,%d,%d,%d,%.3f,%d" % (c, px, py, a, dmg, n_threat)
    for (ex, ey, ed, ev) in en_list:
        row += ",%d,%d,%d,%d" % (ex, ey, ed, ev)
    TRACE.write(row + "\n"); TRACE.flush()
    u = "(AV select 0)"
    if a < 8:                                                  # cap monde a*45 (0=N) -> doMove
        b = math.radians(a * 45.0)
        tx = px + math.sin(b) * 25.0; ty = py + math.cos(b) * 25.0
        env.b.send('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%.0f, %.0f, 0];' % (u, tx, ty), wait=True)
    elif a == 9 and alive_en:                                  # SUPPRESS
        kn = min(alive_en, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2)
        env.b.send('private _u = %s; _u setUnitPos "MIDDLE"; _u doWatch [%d,%d,0]; _u doSuppressiveFire [%d,%d,1];' % (u, kn[0], kn[1], kn[0], kn[1]), wait=True)
    else:                                                      # HOLD
        env.b.send('private _u = %s; doStop _u;' % u, wait=True)
    hz.append(time.time() - t0)
    if c % 6 == 0:
        do = math.hypot(gx - px, gy - py)
        print("  t=%4.1fs|obj %3.0fm|vie %3.0f%%|menace %d|coque_min %2dm|->%-6s" % (
            time.time() - t_start, do, dmg * 100, n_threat, min(shell), ACT[a]), flush=True)

# repartition des actions (lecture du comportement)
from collections import Counter
cnt = Counter(acts_hist); tot = max(len(acts_hist), 1)
rep = " ".join("%s:%d%%" % (ACT[k], 100 * v // tot) for k, v in cnt.most_common(5))
print(">>> %s | %.0fs @ %.1fHz | feu=%s | issue=%s vie=%.0f%% | actions: %s" % (
    CK, time.time() - t_start, (1.0 / (sum(hz) / len(hz))) if hz else 0, took_fire, outcome, dmg * 100, rep), flush=True)
TRACE.close()
print("OP FINI", flush=True)
