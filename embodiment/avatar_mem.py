"""avatar_mem — DEPLOIEMENT LIVE DU CERVEAU A MEMOIRE (GRU). A chaque pas, le reseau recurrent met a jour un
etat mental persistant (h) puis decide -> il SE SOUVIENT en temps reel (l'ennemi connu, le contexte). Terrain
degage, OPFOR active. Compare au MLP sans memoire (meme boucle). args: server_idx seed cycles."""
import time, re, sys, math
import numpy as np, torch
import torch.nn as nn
torch.backends.cudnn.enabled = False
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 6
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 61
CYCLES = int(sys.argv[3]) if len(sys.argv) > 3 else 300
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
SCALE, SIGHT = 140.0, 110.0
STANCE = {"STAND": 0.0, "CROUCH": 0.5, "PRONE": 1.0}
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]


class RecurrentBrain(nn.Module):
    def __init__(self, obs_dim=14, n_act=4, hidden=128):
        super().__init__()
        self.gru = nn.GRU(obs_dim, hidden, batch_first=True)
        self.head = nn.Linear(hidden, n_act)

    def step(self, x1, h=None):
        out, h = self.gru(x1.unsqueeze(1), h)
        return self.head(out.squeeze(1)), h


brain = RecurrentBrain(14, 4, 128).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_gru14.pt", map_location=DEV)); brain.eval()
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
start = (OBJ[0] + 10, OBJ[1] - 70)
env.spawn({"AV": start}, [(OBJ[0], OBJ[1], 3, 14)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '_g setBehaviour "AWARE"; _g setCombatMode "YELLOW"; _g setSpeedMode "NORMAL";'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill 0.55; _x reveal (AV select 0); } forEach HMT_EN;', wait=True)
time.sleep(2)
print("=== AVATAR A MEMOIRE (GRU, etat mental persistant) — server%d ===" % SRV, flush=True)
gx, gy = OBJ
px, py, dmg, sup, fat, ammo = start[0], start[1], 0.0, 0.0, 0.0, 30
pos_stance = "STAND"; last_act = -1; t_start = time.time(); hz = []
took_fire = False; outcome = "timeout"; h = None
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
    if sup > 0.05 or dmg > 0.0:
        took_fire = True
    if dmg >= 0.9:
        outcome = "TOMBE"; print("  t=%.0fs : avatar %s" % (time.time() - t_start, outcome), flush=True); break
    if not enemies:
        hz.append(time.time() - t0); time.sleep(0.05); continue
    alive_en = [(ex, ey, ed, ev) for (ex, ey, ed, ev) in enemies if ed < 70]
    n_en = len(alive_en); n_vis = sum(1 for e in alive_en if e[3] == 1)
    if n_en == 0:
        outcome = "OPFOR NEUTRALISE"; print("  t=%.0fs : %s" % (time.time() - t_start, outcome), flush=True); break
    vis = [e for e in alive_en if e[3] == 1]
    seen = min(vis, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2) if vis else None
    known = min(alive_en, key=lambda e: (e[0] - px) ** 2 + (e[1] - py) ** 2)
    o = [(px - gx) / SCALE, (py - gy) / SCALE, (gx - px) / SCALE, (gy - py) / SCALE, 1.0, 0.0, 0.0,
         (seen[0] - px) / SCALE if seen else 0.0, (seen[1] - py) / SCALE if seen else 0.0, sup, fat,
         STANCE.get(pos_stance, 0.0), (known[0] - px) / SCALE, (known[1] - py) / SCALE]
    with torch.no_grad():
        logits, h = brain.step(torch.tensor([o], dtype=torch.float32, device=DEV), h)
        a = int(logits.argmax(1).item())
    engaged = (seen is not None) or sup > 0.3
    if not engaged:
        a = 1
    u = "(AV select 0)"
    if a == 1:
        if last_act != 1 or c % 10 == 0:
            env.b.send('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (u, gx, gy), wait=True)
    elif a == 2:
        env.b.send('private _u = %s; doStop _u; _u setUnitPos "MIDDLE"; _u doWatch [%d, %d, 0]; _u doSuppressiveFire [%d, %d, 1];' % (u, known[0], known[1], known[0], known[1]), wait=True)
    elif a == 3:
        env.b.send('private _u = %s; doStop _u; _u setUnitPos "DOWN";' % u, wait=True)
    else:
        env.b.send('private _u = %s; doStop _u;' % u, wait=True)
    last_act = a
    hz.append(time.time() - t0)
    if c % 6 == 0:
        do = math.hypot(gx - px, gy - py)
        eye = ("VOIT %d/%d" % (n_vis, n_en)) if seen else ("0/%d (mémoire)" % n_en)
        print("  t=%4.1fs|obj %3.0fm|vie %3.0f%% sup %.2f %-6s|yeux %-13s|->%-10s" % (
            time.time() - t_start, do, dmg * 100, sup, pos_stance, eye, ACT[a]), flush=True)
print(">>> AVATAR-MEM | %.0fs @ %.1fHz | feu_recu=%s | issue=%s | vie=%.0f%% OPFOR=%d" % (
    time.time() - t_start, (1.0 / (sum(hz) / len(hz))) if hz else 0, took_fire, outcome, dmg * 100, n_en if 'n_en' in dir() else 3), flush=True)
print("MEM FINI", flush=True)
