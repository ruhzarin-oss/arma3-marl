"""avatar_fight (programme de nuit) — PRISE EN COMBAT, terrain DEGAGE, parametrable.
args: server_idx start_dist n_en skill seed cycles label
YEUX = LOS geometrique, OREILLES = getSuppression, PROPRIO = posture/souffle/vie. Cerveau = clone + intention.
Robuste : un cycle sans lecture ne conclut rien (pas de faux 'victoire'); serveur frais par run."""
import time, re, sys, math
import numpy as np, torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 6
DIST = float(sys.argv[2]) if len(sys.argv) > 2 else 70.0
N_EN = int(sys.argv[3]) if len(sys.argv) > 3 else 3
SKILL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 41
CYCLES = int(sys.argv[6]) if len(sys.argv) > 6 else 300
LABEL = sys.argv[7] if len(sys.argv) > 7 else "run"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)        # zone DEGAGEE au sud de Paros
SCALE, SIGHT = 140.0, 110.0
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
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x enableAI "FSM"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill %.2f; _x reveal (AV select 0); } forEach HMT_EN;' % SKILL, wait=True)
time.sleep(2)
print("=== FIGHT %s : server%d dist=%.0f n_en=%d skill=%.2f ===" % (LABEL, SRV, DIST, N_EN, SKILL), flush=True)
gx, gy = OBJ
px, py, dmg, sup, fat, ammo = start[0], start[1], 0.0, 0.0, 0.0, 30
pos_stance = "STAND"; last_act = -1; t_start = time.time(); hz = []
took_fire = False; first_react = None; ever_en = False; outcome = "timeout"
max_sup = 0.0
for c in range(CYCLES):
    t0 = time.time()
    ls = env._query('private _u = AV select 0; private _p = getPosATL _u;'
                    ' diag_log format ["AV %1 %2 %3 %4 %5 %6 %7", round(_p#0), round(_p#1), stance _u, round((getDammage _u)*100), round((getSuppression _u)*100), round((getFatigue _u)*100), (_u ammo currentWeapon _u)];'
                    ' { private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; private _vis = 0;'
                    '   if (alive _e && {(_u distance _e) < 110} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    '   diag_log format ["EN %1 %2 %3 %4 %5", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100), _vis]; } forEach HMT_EN;'
                    ' diag_log "SENSEND";', settle=0.08)
    got_av = False; enemies = []
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\w+) (\d+) (\d+) (\d+) (\d+)", l)
        if m:
            got_av = True
            px = int(m.group(1)); py = int(m.group(2)); pos_stance = m.group(3); dmg = int(m.group(4)) / 100.0
            sup = int(m.group(5)) / 100.0; fat = int(m.group(6)) / 100.0; ammo = int(m.group(7))
        me = re.search(r"EN (\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            enemies.append((int(me.group(2)), int(me.group(3)), int(me.group(4)), int(me.group(5))))
    if sup > 0.05 or dmg > 0.0:
        took_fire = True
    max_sup = max(max_sup, sup)
    if dmg >= 0.9:
        outcome = "AVATAR TOMBE"; print("  t=%.0fs : %s" % (time.time() - t_start, outcome), flush=True); break
    if not enemies:                 # lecture ratee ce cycle -> on ne conclut RIEN
        hz.append(time.time() - t0); time.sleep(0.05); continue
    alive_en = [(ex, ey, ed, ev) for (ex, ey, ed, ev) in enemies if ed < 70]
    n_en = len(alive_en); n_vis = sum(1 for e in alive_en if e[3] == 1)
    if len(enemies) >= N_EN:
        ever_en = ever_en or (n_en > 0)
    if ever_en and n_en == 0:
        outcome = "OPFOR NEUTRALISE"; print("  t=%.0fs : VICTOIRE (%s)" % (time.time() - t_start, outcome), flush=True); break
    vis = [e for e in alive_en if e[3] == 1]
    seen = min(vis, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2) if vis else None
    known = min(alive_en, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2) if alive_en else None
    o = [(px - gx) / SCALE, (py - gy) / SCALE, (gx - px) / SCALE, (gy - py) / SCALE, 1.0, 0.0, 0.0]
    o += [(seen[0] - px) / SCALE if seen else 0.0, (seen[1] - py) / SCALE if seen else 0.0, sup, fat,
          STANCE.get(pos_stance, 0.0), (known[0] - px) / SCALE if known else 0.0, (known[1] - py) / SCALE if known else 0.0]
    with torch.no_grad():
        a = int(brain.a_logits(torch.tensor([o], dtype=torch.float32, device=DEV)).argmax(1).item())
    engaged = (seen is not None) or sup > 0.3
    if not engaged:
        a = 1
    if engaged and first_react is None and a in (2, 3):
        first_react = "%s@%.0fs" % (ACT[a], time.time() - t_start)
    u = "(AV select 0)"
    if a == 1:
        if last_act != 1 or c % 10 == 0:
            env.b.send('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (u, gx, gy), wait=True)
    elif a == 2 and known:
        env.b.send('private _u = %s; doStop _u; _u setUnitPos "MIDDLE"; _u doWatch [%d, %d, 0]; _u doSuppressiveFire [%d, %d, 1];' % (u, known[0], known[1], known[0], known[1]), wait=True)
    elif a == 3:
        env.b.send('private _u = %s; doStop _u; _u setUnitPos "DOWN";' % u, wait=True)
    else:
        env.b.send('private _u = %s; doStop _u;' % u, wait=True)
    last_act = a
    hz.append(time.time() - t0)
    if c % 8 == 0:
        do = math.hypot(gx - px, gy - py)
        eye = ("VOIT %d/%d(%.0fm)" % (n_vis, n_en, math.hypot(seen[0] - px, seen[1] - py))) if seen else ("0/%d" % n_en)
        print("  t=%4.1fs|obj %3.0fm|vie %3.0f%% souffle %2.0f%% SUP %.2f %-6s|%-12s|->%-10s" % (
            time.time() - t_start, do, dmg * 100, fat * 100, sup, pos_stance, eye, ACT[a]), flush=True)
print(">>> %s | %.0fs @ %.1fHz | feu_recu=%s sup_max=%.2f | 1re_reaction=%s | issue=%s | vie=%.0f%% OPFOR_vivants=%d" % (
    LABEL, time.time() - t_start, (1.0 / (sum(hz) / len(hz))) if hz else 0, took_fire, max_sup, first_react, outcome, dmg * 100, n_en if 'n_en' in dir() else N_EN), flush=True)
print("FIGHT FINI", flush=True)
