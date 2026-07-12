"""avatar_live v1 — LA PRISE MATRICE. Un soldat-vaisseau dans Arma, boucle CONTINUE temps reel.
YEUX = ligne de vue geometrique reelle vers les ennemis (lineIntersectsSurfaces), PAS la connaissance bridee d'Arma.
OREILLES = getSuppression. PROPRIO = posture/souffle/vie. Cerveau = clone Sharingan + intention de commande.
La garnison riposte (vrai engagement). On prouve que la prise VIT et VOIT, en direct."""
import time, re, sys, math
import numpy as np, torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = M.COMPLEXE; SCALE, SIGHT = 140.0, 110.0
STANCE = {"STAND": 0.0, "CROUCH": 0.5, "PRONE": 1.0}
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV)); brain.eval()
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge5.Altis",
             log=SB + "/logs/server5.out", acc=1.0, seed=31)
start = (OBJ[0] + 90, OBJ[1] - 40)
env.spawn({"AV": start}, [(OBJ[0], OBJ[1], 3, 12)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '_g setBehaviour "AWARE"; _g setCombatMode "YELLOW"; _g setSpeedMode "NORMAL";'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x enableAI "FSM"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill 0.6; _x reveal (AV select 0); } forEach HMT_EN;', wait=True)
time.sleep(2)
print("=== PRISE MATRICE v1 : avatar branche en direct, avec ses PROPRES yeux ===", flush=True)
gx, gy = OBJ
px, py, dmg, sup, fat, ammo = start[0], start[1], 0.0, 0.0, 0.0, 30
pos_stance = "STAND"; last_act = -1; CYCLES = 130; t_start = time.time(); hz = []
for c in range(CYCLES):
    t0 = time.time()
    ls = env._query('private _u = AV select 0; private _p = getPosATL _u;'
                    ' diag_log format ["AV %1 %2 %3 %4 %5 %6 %7", round(_p#0), round(_p#1), stance _u, round((getDammage _u)*100), round((getSuppression _u)*100), round((getFatigue _u)*100), (_u ammo currentWeapon _u)];'
                    ' { private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; private _vis = 0;'
                    '   if (alive _e && {(_u distance _e) < 110} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    '   diag_log format ["EN %1 %2 %3 %4 %5", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100), _vis]; } forEach HMT_EN;'
                    ' diag_log "SENSEND";', settle=0.08)
    enemies = []
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\w+) (\d+) (\d+) (\d+) (\d+)", l)
        if m:
            px = int(m.group(1)); py = int(m.group(2)); pos_stance = m.group(3); dmg = int(m.group(4)) / 100.0
            sup = int(m.group(5)) / 100.0; fat = int(m.group(6)) / 100.0; ammo = int(m.group(7))
        me = re.search(r"EN (\d+) (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            enemies.append((int(me.group(2)), int(me.group(3)), int(me.group(4)), int(me.group(5))))
    if dmg >= 0.9:
        print("  cycle %d (t=%.0fs) : avatar TOMBE. fin." % (c, time.time() - t_start), flush=True); break
    alive_en = [(ex, ey, ed, ev) for (ex, ey, ed, ev) in enemies if ed < 70]
    n_en = len(alive_en); n_vis = sum(1 for e in alive_en if e[3] == 1)
    # YEUX : ennemi VISIBLE le plus proche ; CONNU : ennemi vivant le plus proche
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
    u = "(AV select 0)"
    if a == 1:
        if last_act != 1 or c % 10 == 0:        # relance la marche sur transition + rappel periodique (anti-blocage)
            env.b.send('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (u, gx, gy), wait=True)
    elif a == 2 and known:
        env.b.send('private _u = %s; doStop _u; _u setUnitPos "MIDDLE"; _u doWatch [%d, %d, 0]; _u doSuppressiveFire [%d, %d, 1];' % (u, known[0], known[1], known[0], known[1]), wait=True)
    elif a == 3:
        env.b.send('private _u = %s; doStop _u; _u setUnitPos "DOWN";' % u, wait=True)
    else:
        env.b.send('private _u = %s; doStop _u;' % u, wait=True)
    last_act = a
    hz.append(time.time() - t0)
    if c % 4 == 0:
        do = math.hypot(gx - px, gy - py)
        eye = ("VOIT %d/%d (proche %.0fm)" % (n_vis, n_en, math.hypot(seen[0] - px, seen[1] - py))) if seen else ("0/%d vu" % n_en)
        print("  t=%4.1fs | obj %3.0fm | vie %3.0f%% souffle %2.0f%% sup %.2f %-6s | yeux: %-18s | -> %-10s [%.1f Hz]" % (
            time.time() - t_start, do, dmg * 100, fat * 100, sup, pos_stance, eye, ACT[a], 1.0 / (sum(hz[-4:]) / len(hz[-4:]))), flush=True)
print(">>> prise vecue %.0f s @ %.1f Hz | ennemis restants vivants : %d" % (time.time() - t_start, 1.0 / (sum(hz) / len(hz)), n_en), flush=True)
print("AVATAR FINI", flush=True)
