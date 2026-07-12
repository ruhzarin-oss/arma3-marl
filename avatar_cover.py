"""avatar_cover — ENVELOPPE ENRICHIE : ajoute la COQUE DE COUVERT (12 rayons) au sens de l'avatar,
et l'UTILISE : sous le feu / engage, le soldat REJOINT un vrai couvert (obstacle entre lui et la menace)
au lieu de se coucher sur place. Meme base que avatar_fight (comparaison propre).
But = prouver que le SENS du couvert permet la manoeuvre. (Regle simple ici ; la politique RL viendra.)
args: server_idx start_dist n_en skill seed cycles label"""
import time, re, sys, math
import numpy as np, torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
DIST = float(sys.argv[2]) if len(sys.argv) > 2 else 70.0
N_EN = int(sys.argv[3]) if len(sys.argv) > 3 else 3
SKILL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 41
CYCLES = int(sys.argv[6]) if len(sys.argv) > 6 else 150
LABEL = sys.argv[7] if len(sys.argv) > 7 else "cover"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
SCALE, SIGHT = 140.0, 110.0
K, R = 12, 15                       # coque : 12 rayons, portee 15 m
COVER_MAX = 9.0                     # un rayon < 9 m = couvert exploitable
STANCE = {"STAND": 0.0, "CROUCH": 0.5, "PRONE": 1.0}
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV)); brain.eval()
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
start = (OBJ[0] + 10, OBJ[1] - DIST)
env.spawn({"AV": start}, [(OBJ[0], OBJ[1], N_EN, 14)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '_g setBehaviour "AWARE"; _g setCombatMode "YELLOW"; _g setSpeedMode "NORMAL";'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill %.2f; _x reveal (AV select 0); } forEach HMT_EN;' % SKILL, wait=True)
time.sleep(2)
print("=== COVER %s : server%d dist=%.0f n_en=%d skill=%.2f ===" % (LABEL, SRV, DIST, N_EN, SKILL), flush=True)

# requete capteur = avatar_fight + COQUE DE COUVERT (origine getPosASL+0.9, repere corps) + cap (getDir)
SENSE = ('private _u = AV select 0; private _p = getPosATL _u;'
         ' diag_log format ["AV %1 %2 %3 %4 %5 %6 %7", round(_p#0), round(_p#1), stance _u, round((getDammage _u)*100), round((getSuppression _u)*100), round((getFatigue _u)*100), (_u ammo currentWeapon _u)];'
         ' diag_log format ["DIR %1", round(getDir _u)];'
         ' private _o = getPosASL _u; _o set [2, (_o#2) + 0.9]; private _s = "";'
         ' for "_i" from 0 to ' + str(K - 1) + ' do { private _a = _i * ' + str(360 // K) + ';'
         '   private _dir = _u vectorModelToWorld [sin _a, cos _a, 0];'
         '   private _to = _o vectorAdd (_dir vectorMultiply ' + str(R) + ');'
         '   private _h = lineIntersectsSurfaces [_o, _to, _u];'
         '   private _d = if (count _h == 0) then {' + str(R) + '} else {_o distance ((_h select 0) select 0)};'
         '   _s = _s + format ["%1 ", round _d]; };'
         ' diag_log format ["SHELL %1", _s];'
         ' { private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; private _vis = 0;'
         '   if (alive _e && {(_u distance _e) < 110} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
         '   diag_log format ["EN %1 %2 %3 %4 %5", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100), _vis]; } forEach HMT_EN;'
         ' diag_log "SENSEND";')

gx, gy = OBJ
px, py, dmg, sup, fat, ammo, hdg = start[0], start[1], 0.0, 0.0, 0.0, 30, 0
pos_stance = "STAND"; shell = [R] * K
t_start = time.time(); hz = []
took_fire = False; first_react = None; ever_en = False; outcome = "timeout"; max_sup = 0.0
in_cover_evt = 0; broke_los_evt = 0; prev_vis_known = False


def body_bearing(ex, ey):
    wb = math.degrees(math.atan2(ex - px, ey - py)) % 360.0      # cap monde vers l'ennemi
    return (wb - hdg + 180.0) % 360.0 - 180.0                    # ramene en repere corps [-180,180]


def best_cover(threat_b):
    """meilleur rayon-couvert : le plus aligne sur la menace (obstacle entre moi et l'ennemi)."""
    cands = [(i * (360 // K), shell[i]) for i in range(K) if shell[i] < COVER_MAX]
    if not cands:
        return None
    def ang(a):  # ecart angulaire a la menace
        return abs((a - (threat_b % 360) + 180) % 360 - 180)
    toward = [c for c in cands if ang(c[0]) <= 70]              # couvert vers la menace -> casse la LOS
    pool = toward if toward else cands                          # sinon n'importe quel couvert
    return min(pool, key=lambda c: (ang(c[0]), c[1]))           # le mieux aligne, puis le plus proche


for c in range(CYCLES):
    t0 = time.time()
    ls = env._query(SENSE, settle=0.08)
    got = False; enemies = []
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\w+) (\d+) (\d+) (\d+) (\d+)", l)
        if m:
            got = True; px = int(m.group(1)); py = int(m.group(2)); pos_stance = m.group(3)
            dmg = int(m.group(4)) / 100.0; sup = int(m.group(5)) / 100.0; fat = int(m.group(6)) / 100.0; ammo = int(m.group(7))
        md = re.search(r"DIR (-?\d+)", l)
        if md:
            hdg = int(md.group(1))
        msh = re.search(r"SHELL ([\d ]+)", l)
        if msh:
            vals = [int(x) for x in msh.group(1).split()]
            if len(vals) == K:
                shell = vals
        me = re.search(r"EN (\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            enemies.append((int(me.group(2)), int(me.group(3)), int(me.group(4)), int(me.group(5))))
    if sup > 0.05 or dmg > 0.0:
        took_fire = True
    max_sup = max(max_sup, sup)
    if dmg >= 0.9:
        outcome = "AVATAR TOMBE"; print("  t=%.0fs : %s" % (time.time() - t_start, outcome), flush=True); break
    if not enemies:
        hz.append(time.time() - t0); time.sleep(0.05); continue
    alive_en = [(ex, ey, ed, ev) for (ex, ey, ed, ev) in enemies if ed < 70]
    n_en = len(alive_en); n_vis = sum(1 for e in alive_en if e[3] == 1)
    if len(enemies) >= N_EN:
        ever_en = ever_en or (n_en > 0)
    if ever_en and n_en == 0:
        outcome = "OPFOR NEUTRALISE"; print("  t=%.0fs : VICTOIRE" % (time.time() - t_start), flush=True); break
    vis = [e for e in alive_en if e[3] == 1]
    seen = min(vis, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2) if vis else None
    known = min(alive_en, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2) if alive_en else None
    engaged = (seen is not None) or sup > 0.15

    act_label = "AVANCER"
    if not engaged:                                            # pas de menace -> on avance a l'objectif
        env.b.send('private _u = (AV select 0); _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (gx, gy), wait=True)
    else:
        tb = body_bearing(known[0], known[1]) if known else 0.0
        cov = best_cover(tb)
        # deja sous un couvert proche cote menace ? -> tenir + supprimer
        ai_threat = min(range(K), key=lambda i: abs((i * (360 // K) - (tb % 360) + 180) % 360 - 180))
        under_cover = shell[ai_threat] < 3.5
        if under_cover or cov is None:
            act_label = "SUPPRESSER" if seen or known else "TENIR"
            if known:
                env.b.send('private _u = (AV select 0); _u setUnitPos "MIDDLE"; _u doWatch [%d,%d,0]; _u doSuppressiveFire [%d,%d,1];' % (known[0], known[1], known[0], known[1]), wait=True)
            else:
                env.b.send('private _u = (AV select 0); doStop _u; _u setUnitPos "DOWN";', wait=True)
        else:
            a_cov, d_cov = cov                                 # azimut corps + distance du couvert
            wb = math.radians((hdg + a_cov) % 360.0)
            tx = px + math.sin(wb) * max(d_cov - 1.5, 0.5)
            ty = py + math.cos(wb) * max(d_cov - 1.5, 0.5)
            env.b.send('private _u = (AV select 0); _u setUnitPos "MIDDLE"; _u doMove [%.0f, %.0f, 0];' % (tx, ty), wait=True)
            act_label = "COUVERT@%dm" % int(d_cov)
            in_cover_evt += 1

    # mesure : a-t-il casse la LOS en se couvrant ? (connu vivant qui passe de vu -> non vu)
    if known is not None:
        kv = (seen is not None)
        if prev_vis_known and not kv and act_label.startswith("COUVERT"):
            broke_los_evt += 1
        prev_vis_known = kv
    if engaged and first_react is None and act_label.startswith(("COUVERT", "SUPPRESSER")):
        first_react = "%s@%.0fs" % (act_label, time.time() - t_start)
    hz.append(time.time() - t0)
    if c % 6 == 0:
        do = math.hypot(gx - px, gy - py)
        eye = ("VOIT %d/%d" % (n_vis, n_en)) if seen else ("0/%d" % n_en)
        cmin = min(shell)
        print("  t=%4.1fs|obj %3.0fm|vie %3.0f%% SUP %.2f %-6s|cple_min %2dm|%-10s|->%-12s" % (
            time.time() - t_start, do, dmg * 100, sup, pos_stance, cmin, eye, act_label), flush=True)
print(">>> %s | %.0fs @ %.1fHz | feu=%s sup_max=%.2f | 1re_reaction=%s | couverts_pris=%d los_cassee=%d | issue=%s vie=%.0f%% OPFOR=%d" % (
    LABEL, time.time() - t_start, (1.0 / (sum(hz) / len(hz))) if hz else 0, took_fire, max_sup, first_react,
    in_cover_evt, broke_los_evt, outcome, dmg * 100, n_en if 'n_en' in dir() else N_EN), flush=True)
print("COVER FINI", flush=True)
