"""squad_deploy_obj — VRAI critere : ATTEINDRE L'OBJECTIF + savoir neutraliser (pas tout tuer).
  - BASE DE FEU (AV) : politique apprise, setVelocity, supprime/couvre.
  - ELEMENT D'ASSAUT (ASS) : pathfinder Arma, pousse SUR LE POINT (doMove objectif), engage en route.
Mesure : objectif atteint = >=REACH_N soldats vivants a <REACH_R m du centre ; distance min atteinte ; opposition neutralisee.
args: server NFIRE NASS NDEF cycles checkpoint"""
import time, re, sys, math
import torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
NFIRE = int(sys.argv[2]) if len(sys.argv) > 2 else 12
NASS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
NDEF = int(sys.argv[4]) if len(sys.argv) > 4 else 10
CYC = int(sys.argv[5]) if len(sys.argv) > 5 else 200
CK = sys.argv[6] if len(sys.argv) > 6 else "squad_curr2_A20.pt"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180); GX, GY = OBJ
S = 140.0; R = 60.0; ASSAULT_START = 4; REACH_R = 15; REACH_N = 3

net = Net(26, 10, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/" + CK, map_location=DEV)); net.eval()

env = OpArma(squads=(("AV", NFIRE), ("ASS", NASS)), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SRV)
env.spawn({"AV": (GX + 10, GY - 115), "ASS": (GX - 12, GY - 122)}, [(GX, GY, NDEF, 14)])
env.b.send('private _objs = (nearestObjects [[%d,%d,0],["House","Building"],110]) select {count (_x buildingPos -1)>0};'
           ' { private _bld=_objs select (_forEachIndex %% (count _objs)); private _poss=_bld buildingPos -1;'
           '   _x setPosATL (_poss select (_forEachIndex %% (count _poss))); _x setUnitPos "UP"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSkill 0.5; } forEach HMT_EN;' % (GX, GY), wait=True)
env.b.send('{ _x disableAI "MOVE"; _x disableAI "PATH"; _x disableAI "FSM"; _x disableAI "ANIM"; _x disableAI "AUTOCOMBAT"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x enableAI "AIMING"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach AV;', wait=True)
env.b.send('HMT_VX = []; HMT_VY = []; { HMT_VX pushBack 0; HMT_VY pushBack 0; } forEach AV;', wait=True)
env.b.send('HMT_EF = addMissionEventHandler ["EachFrame", { { if (_forEachIndex < count HMT_VX) then { _x setVelocity [HMT_VX select _forEachIndex, HMT_VY select _forEachIndex, (velocity _x)#2]; }; } forEach AV; }];', wait=True)
env.b.send('{ _x enableAI "ALL"; _x enableAI "MOVE"; _x enableAI "PATH"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSkill 0.55; } forEach ASS;', wait=True)
time.sleep(6)
print("=== DEPLOY OBJ %s | srv%d | %d feu + %d assaut -> ATTEINDRE l'objectif (vs %d garnis) ===" % (CK, SRV, NFIRE, NASS, NDEF), flush=True)

SENSE = ('{ private _u = _x; private _i = _forEachIndex; private _p = getPosATL _u;'
         ' private _near = objNull; private _bnd = 1e9;'
         ' { if (alive _x) then { private _dd = _u distance _x; if (_dd < _bnd) then {_bnd=_dd; _near=_x}; }; } forEach HMT_EN;'
         ' private _vis=0; private _ex=0; private _ey=0; private _ed=999;'
         ' if (!isNull _near) then { private _q=getPosATL _near; _ex=_q#0; _ey=_q#1; _ed=_u distance _near;'
         '   if (_ed<110 && {count (lineIntersectsSurfaces [eyePos _u, eyePos _near, _u, _near])==0}) then {_vis=1}; };'
         ' private _tb = if (isNull _near) then {getDir _u} else {_u getDir _near};'
         ' private _o = getPosASL _u; _o set [2,(_o#2)+0.9]; private _s="";'
         ' for "_k" from 0 to 11 do { private _a=_tb+_k*30; private _d=[sin _a,cos _a,0];'
         '   private _h=lineIntersectsSurfaces [_o, _o vectorAdd (_d vectorMultiply 60), _u];'
         '   _s=_s+format ["%1 ", round (if (count _h==0) then {60} else {_o distance ((_h select 0)select 0)})]; };'
         ' private _n = surfaceNormal _p;'
         ' diag_log format ["S %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 ; %11", _i, round(_p#0),round(_p#1),round(getDir _u),round((getDammage _u)*1000),round((1-(_n#2))*1000),round _ex,round _ey,round _ed,_vis,_s];'
         ' } forEach AV;'
         ' private _na=0; { if (alive _x) then {_na=_na+1}; } forEach HMT_EN; diag_log format ["ENA %1", _na]; diag_log "SQEND";')

REACHQ = ('private _al=(AV+ASS) select {alive _x}; private _md=9999; { private _d=_x distance [%d,%d,0]; if (_d<_md) then {_md=_d}; } forEach _al;'
          ' private _nr={(_x distance [%d,%d,0])<%d} count _al;'
          ' diag_log format ["REACH near=%%1 mind=%%2 nf=%%3 na=%%4", _nr, round _md, count _al, ({alive _x} count HMT_EN)];' % (GX, GY, GX, GY, REACH_R))

last_act = [8] * NFIRE
t0 = time.time(); outcome = "objectif NON atteint"
from collections import Counter
act_hist = []
max_near = 0; min_dist = 9999; held = 0; reached = False


def build_obs(S_rows):
    px = [r["px"] for r in S_rows]; py = [r["py"] for r in S_rows]
    sup = [1.0 if last_act[i] == 9 else 0.0 for i in range(len(S_rows))]
    frac = (sum(sup) / max(len(sup), 1))
    obs = []
    for i, r in enumerate(S_rows):
        apx = (r["px"] - GX) / S; apy = (r["py"] - GY) / S
        nd = min(r["ed"], 999) / S; los = float(r["vis"])
        dc = min(r["shell"]) / 280.0
        base = [apx, apy, -apx, -apy, 1.0, r["slope"] / 5.0, dc, los, nd]
        shell13 = [v / R for v in r["shell"]] + [r["dmg"]]
        best = None; bd = 1e18
        for j in range(len(S_rows)):
            if j == i:
                continue
            d2 = (px[j] - r["px"]) ** 2 + (py[j] - r["py"]) ** 2
            if d2 < bd:
                bd = d2; best = j
        if best is not None:
            adx = (px[best] - r["px"]) / S; ady = (py[best] - r["py"]) / S; asup = sup[best]
        else:
            adx = ady = asup = 0.0
        obs.append(base + shell13 + [adx, ady, asup, frac])
    return torch.tensor(obs, dtype=torch.float32, device=DEV)


for c in range(CYC):
    rows = {}; n_alive = NDEF
    for _try in range(3):
        ls = env._query(SENSE, settle=0.30)
        rows = {}; n_alive = NDEF
        for l in ls:
            m = re.search(r"S (\d+) (-?\d+) (-?\d+) (-?\d+) (\d+) (\d+) (-?\d+) (-?\d+) (\d+) (\d+) ; ([\d ]+)", l)
            if m:
                i = int(m.group(1)); shell = [int(x) for x in m.group(11).split()][:12]
                if len(shell) == 12:
                    rows[i] = dict(px=int(m.group(2)), py=int(m.group(3)), dir=int(m.group(4)), dmg=int(m.group(5)) / 1000.0,
                                   slope=int(m.group(6)) / 1000.0, ex=int(m.group(7)), ey=int(m.group(8)), ed=int(m.group(9)), vis=int(m.group(10)), shell=shell)
            me = re.search(r"ENA (\d+)", l)
            if me:
                n_alive = int(me.group(1))
        if len(rows) >= NFIRE // 2:
            break
        time.sleep(0.1)
    if len(rows) < NFIRE // 2:
        time.sleep(0.05); continue
    S_rows = [rows.get(i, rows[min(rows)]) for i in range(NFIRE)]
    md = sum(math.hypot(r["px"] - GX, r["py"] - GY) for r in S_rows) / len(S_rows)
    with torch.no_grad():
        acts = net.a_logits(build_obs(S_rows)).argmax(-1).tolist()
    act_hist += acts
    vx = [0.0] * NFIRE; vy = [0.0] * NFIRE; fires = []
    for i, a in enumerate(acts):
        r = S_rows[i]
        if a < 8:
            br = math.radians(a * 45.0); vx[i] = math.sin(br) * 4.0; vy[i] = math.cos(br) * 4.0
        elif a == 9 and r["ed"] < 900:
            fires.append((i, r["ex"], r["ey"]))
        last_act[i] = a
    # CONSOLIDATION : opposition immediate matee (garnison <= moitie OU apres delai) -> base de feu FONCE sur le
    # point (setVelocity precis) et tient. On NE attend PAS les derniers retranches (critere = atteindre, pas tout tuer).
    if n_alive <= (NDEF // 2) or c >= 30:
        for i in range(NFIRE):
            dx = GX - S_rows[i]["px"]; dy = GY - S_rows[i]["py"]; d = math.hypot(dx, dy) or 1.0
            if d > REACH_R - 5:
                vx[i] = dx / d * 4.0; vy[i] = dy / d * 4.0
            else:
                vx[i] = 0.0; vy[i] = 0.0
    env.b.send('[] spawn { HMT_VX = [%s]; HMT_VY = [%s]; };' % (",".join("%.2f" % v for v in vx), ",".join("%.2f" % v for v in vy)), wait=True)
    if fires:
        env.b.send('[] spawn { %s };' % "".join('(AV select %d) doSuppressiveFire [%d,%d,1];' % f for f in fires), wait=False)
    # ASSAUT : pousse SUR LE POINT (doMove objectif), engage l'ennemi vu en route. doMove PERSISTE -> on le
    # re-emet seulement 1 cycle sur 4 (sinon ca sature le pont et SENSE flanche).
    if c >= ASSAULT_START and c % 4 == 0:
        env.b.send('[] spawn { { _x doMove [%d,%d,0]; private _t=_x findNearestEnemy _x; if (!isNull _t && {_x distance _t < 60}) then {_x doTarget _t}; } forEach (ASS select {alive _x}); };' % (GX, GY), wait=False)
    if c % 6 == 0:
        rls = env._query(REACHQ, settle=0.2)
        near = mind = nf = na = -1
        for l in rls:
            mm = re.search(r"REACH near=(\d+) mind=(\d+) nf=(\d+) na=(\d+)", l)
            if mm:
                near = int(mm.group(1)); mind = int(mm.group(2)); nf = int(mm.group(3)); na = int(mm.group(4))
        if near >= 0:
            max_near = max(max_near, near); min_dist = min(min_dist, mind)
            held = held + 1 if near >= REACH_N else 0
            if near >= REACH_N:
                reached = True
            phase = "SUPPRESSION" if c < ASSAULT_START else "ASSAUT"
            print("  t=%4.0fs [%s] | dist_feu %3.0fm | + proche obj %3.0fm | a<%dm: %d | amis %d | garnison %d/%d" % (
                time.time() - t0, phase, md, mind, REACH_R, near, nf, na, NDEF), flush=True)
            if held >= 3:
                outcome = "OBJECTIF ATTEINT ET TENU"; print("  >>> %s (>=%d amis a <%dm pendant 3 mesures)" % (outcome, REACH_N, REACH_R), flush=True); break

if reached and "TENU" not in outcome:
    outcome = "OBJECTIF ATTEINT (non tenu durablement)"
cc = Counter(act_hist); tot = max(len(act_hist), 1)
print(">>> OBJ %s srv%d | %.0fs | %s | + proche atteint %dm | max amis a <%dm = %d | issue garnison restante mesuree" % (
    CK, SRV, time.time() - t0, outcome, min_dist, REACH_R, max_near), flush=True)
print(">>> politique base-de-feu : avance %.0f%% | tenir %.0f%% | supprimer %.0f%%" % (
    100 * sum(cc.get(k, 0) for k in range(8)) / tot, 100 * cc.get(8, 0) / tot, 100 * cc.get(9, 0) / tot), flush=True)
print("DEPLOY OBJ FINI", flush=True)
