"""squad_deploy — deploie le SQUAD appris (squad_curr2_A20.pt) sur le VRAI complexe Arma.
20 soldats pilotes par la politique : obs 26-dim EXACTE de l'entrainement (base9 + coque13 + equipe4),
calculee par soldat via le pont ; actions = 8 caps / tenir / supprimer. Mesure la garnison neutralisee REELLE.
args: server_idx n_att n_def cycles checkpoint"""
import time, re, sys, math
import torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
NATT = int(sys.argv[2]) if len(sys.argv) > 2 else 20
NDEF = int(sys.argv[3]) if len(sys.argv) > 3 else 10
CYC = int(sys.argv[4]) if len(sys.argv) > 4 else 160
CK = sys.argv[5] if len(sys.argv) > 5 else "squad_curr2_A20.pt"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
GX, GY = OBJ; S = 140.0; R = 60.0; FIRE = 110.0

net = Net(26, 10, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/" + CK, map_location=DEV)); net.eval()

env = OpArma(squads=(("AV", NATT),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SRV)
start = (GX + 10, GY - 115)                      # bord bati (~115 m, palier final)
env.spawn({"AV": start}, [(GX, GY, NDEF, 14)])
env.b.send('{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill 0.55; _x reveal [(AV select 0), 4]; _x doWatch (AV select 0); } forEach HMT_EN;', wait=True)
# VOIE 1 : pilotage setVelocity (50 Hz EachFrame). CLE 1 : couper FSM+ANIM+AUTOCOMBAT (sinon l'IA d'Arma
# repositionne le corps et ecrase setVelocity -> 6 m au lieu de 30). On GARDE TARGET/AUTOTARGET/AIMING = tir reflexe.
env.b.send('{ _x disableAI "MOVE"; _x disableAI "PATH"; _x disableAI "FSM"; _x disableAI "ANIM"; _x disableAI "AUTOCOMBAT"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x enableAI "AIMING"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach AV;', wait=True)
# CLE 2 : pilotage par TABLEAUX GLOBAUX directs (HMT_VX/HMT_VY), PAS [] spawn{40 setVariable} (qui sous charge
# ne termine pas -> 17/20 restent immobiles). Le handler indexe les tableaux. setVelocity scale a 20/20 (teste).
env.b.send('HMT_VX = []; HMT_VY = []; { HMT_VX pushBack 0; HMT_VY pushBack 0; } forEach AV;', wait=True)
env.b.send('HMT_EF = addMissionEventHandler ["EachFrame", { { if (_forEachIndex < count HMT_VX) then { _x setVelocity [HMT_VX select _forEachIndex, HMT_VY select _forEachIndex, (velocity _x)#2]; }; } forEach AV; }];', wait=True)
time.sleep(6)                                   # warm-up serveur (sinon SENSE ramene 0 ligne sur serveur frais)
print("=== SQUAD DEPLOY %s | server%d %dv%d (pilotage setVelocity) ===" % (CK, SRV, NATT, NDEF), flush=True)

# requete capteur : 1 ligne par soldat (pos,dir,dmg,slope, ennemi proche los/dist, coque 12) + garnison vivante
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

last_act = [8] * NATT
t0 = time.time(); outcome = "timeout"; n_alive0 = NDEF
mind = 9999.0; ever_los = False
from collections import Counter
act_hist = []


def build_obs(S_rows):
    # S_rows[i] = dict(px,py,dir,dmg,slope,ex,ey,ed,vis,shell[12])
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
        # equipe : binome vivant le plus proche
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
        team4 = [adx, ady, asup, frac]
        obs.append(base + shell13 + team4)
    return torch.tensor(obs, dtype=torch.float32, device=DEV)


for c in range(CYC):
    rows = {}; n_alive = NDEF
    for _try in range(3):                       # SENSE flanche parfois sur serveur charge -> retry, settle plus long
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
        if len(rows) >= NATT // 2:
            break
        time.sleep(0.1)
    if len(rows) < NATT // 2:
        time.sleep(0.05); continue
    S_rows = [rows.get(i, rows[min(rows)]) for i in range(NATT)]
    md = sum(math.hypot(r["px"] - GX, r["py"] - GY) for r in S_rows) / len(S_rows)
    mind = min(mind, md); ever_los = ever_los or any(r["vis"] for r in S_rows)
    if n_alive == 0:
        outcome = "GARNISON NEUTRALISEE"; print("  t=%.0fs : %s" % (time.time() - t0, outcome), flush=True); break
    with torch.no_grad():
        acts = net.a_logits(build_obs(S_rows)).argmax(-1).tolist()
    act_hist += acts
    vx = [0.0] * NATT; vy = [0.0] * NATT; fires = []
    for i, a in enumerate(acts):
        r = S_rows[i]
        if a < 8:
            br = math.radians(a * 45.0); vx[i] = math.sin(br) * 4.0; vy[i] = math.cos(br) * 4.0
        elif a == 9 and r["ed"] < 900:
            fires.append((i, r["ex"], r["ey"]))
        last_act[i] = a
    # mouvement : 2 assignations de tableaux dans [] spawn (1 instruction chacune -> ne drope pas, ET pas de
    # GIAS stack violation que l'assignation directe en contexte non-planifie declenche sous charge)
    env.b.send('[] spawn { HMT_VX = [%s]; HMT_VY = [%s]; };' % (",".join("%.2f" % v for v in vx), ",".join("%.2f" % v for v in vy)), wait=True)
    # tir : commande lourde -> [] spawn (pas de stack violation)
    if fires:
        env.b.send('[] spawn { %s };' % "".join('(AV select %d) doSuppressiveFire [%d,%d,1];' % f for f in fires), wait=False)
    if c % 8 == 0:
        nA = sum(1 for r in S_rows if r["dmg"] < 0.9)
        cc = Counter(acts); mv = sum(cc.get(k, 0) for k in range(8))
        print("  t=%4.0fs | dist_moy %3.0fm | garn %d/%d | squad %d/%d | actes: avance %d tenir %d suppr %d" % (
            time.time() - t0, md, n_alive, NDEF, nA, NATT, mv, cc.get(8, 0), cc.get(9, 0)), flush=True)
killed = n_alive0 - n_alive
cc = Counter(act_hist); tot = max(len(act_hist), 1)
print(">>> %s srv%d | %.0fs | garnison tuee %d/%d (%.0f%%) | approche min %.0fm | contact=%s | issue=%s" % (CK, SRV, time.time() - t0, killed, NDEF, 100 * killed / NDEF, mind, ever_los, outcome), flush=True)
print(">>> ACTES : avance %.0f%% | tenir %.0f%% | supprimer %.0f%%" % (100 * sum(cc.get(k, 0) for k in range(8)) / tot, 100 * cc.get(8, 0) / tot, 100 * cc.get(9, 0) / tot), flush=True)
print("SQUAD DEPLOY FINI", flush=True)
