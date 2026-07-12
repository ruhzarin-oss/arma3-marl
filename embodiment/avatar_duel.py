"""avatar_duel — TEST CONTRÔLÉ mémoire→survie. Avatar FIGÉ derrière un muret. Un ennemi scripté alterne
'dressé+tire' (visible) / 'planqué' (hors de vue). Coût réel : il tire quand il est dressé.
  mode mem   : se souvient de la menace -> reste couché/orienté même quand l'ennemi se planque -> couvert.
  mode nomem : oublie dès que l'ennemi disparaît -> se relève (exposé) -> cueilli quand l'ennemi ressurgit.
Métrique : DÉGÂTS encaissés par l'avatar. args: mode server_idx seed cycles."""
import time, re, sys, math
import numpy as np, torch
import torch.nn as nn
torch.backends.cudnn.enabled = False
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
from memory_system import MemorySystem
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
MODE = sys.argv[1] if len(sys.argv) > 1 else "mem"
SRV = int(sys.argv[2]) if len(sys.argv) > 2 else 7
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 88
CYCLES = int(sys.argv[4]) if len(sys.argv) > 4 else 200
cx, cy = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
A = (cx, cy - 30)            # avatar (regarde +y vers l'ennemi), 30 m au sud
E = (cx, cy)                 # ennemi
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
env.spawn({"AV": A}, [(E[0], E[1], 1, 1)])
# UN SEUL muret, devant l'ENNEMI : couché derrière -> caché ; dressé -> visible et tire. Avatar SANS mur
# (sa protection = être couché = petite cible).
env.b.send(
    'ENCOV = "Land_BagFence_Long_F" createVehicle [%d, %d, 0]; ENCOV setDir 90;'
    'private _av = AV select 0; _av disableAI "MOVE"; _av disableAI "PATH"; _av disableAI "AUTOCOMBAT"; _av setBehaviour "COMBAT"; _av setUnitPos "DOWN"; doStop _av; _av setSkill 0.4;'
    'private _en = HMT_EN select 0; _en enableAI "ALL"; _en setSkill 0.95; _en setBehaviour "COMBAT"; _en setCombatMode "RED"; _en allowFleeing 0; _en disableAI "MOVE"; _en disableAI "PATH"; _en reveal _av;'
    % (cx, cy - 3), wait=True)
time.sleep(2)
mem = MemorySystem(14, E, plan=[("tenir", E)])
t0 = time.time(); dmg = 0.0; last_phase = None; peak = 0.0
print("=== DUEL CONTRÔLÉ : MODE=%s (avatar figé, ennemi pop-up scripté) ===" % MODE, flush=True)
for c in range(CYCLES):
    now = time.time() - t0
    phase = "EXPOSE" if (now % 12.0 < 6.0) else "PLANQUE"
    # --- pilotage de l'ennemi scripté ---
    if phase != last_phase:
        if phase == "EXPOSE":
            env.b.send('private _en = HMT_EN select 0; _en setUnitPos "UP"; _en reveal (AV select 0); _en doWatch (AV select 0); _en doTarget (AV select 0); _en doFire (AV select 0);', wait=True)
        else:
            env.b.send('private _en = HMT_EN select 0; _en setUnitPos "DOWN"; _en doWatch objNull; doStop _en;', wait=True)
        last_phase = phase
    # --- perception de l'avatar ---
    ls = env._query('private _u = AV select 0; private _e = HMT_EN select 0; private _vis = 0;'
                    ' if (alive _e && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    ' diag_log format ["AV %1 %2 %3", round((getDammage _u)*100), round((getSuppression _u)*100), _vis];'
                    ' diag_log format ["EN %1 %2 %3", round(getPosATL _e # 0), round(getPosATL _e # 1), round((getDammage _e)*100)];', settle=0.08)
    vis = 0; ex, ey, ed = E[0], E[1], 0
    for l in ls:
        m = re.search(r"AV (\d+) (\d+) (\d+)", l)
        if m:
            dmg = int(m.group(1)) / 100.0; vis = int(m.group(3))
        me = re.search(r"EN (-?\d+) (-?\d+) (\d+)", l)
        if me:
            ex = int(me.group(1)); ey = int(me.group(2)); ed = int(me.group(3))
    peak = max(peak, dmg)
    if dmg >= 0.95:
        print("  t=%.0fs : avatar NEUTRALISÉ" % now, flush=True); break
    px, py = A
    mem.episodique.observe([(0, ex, ey, ed, vis == 1)], now)
    remembered = mem.episodique.nearest(now, px, py) if MODE == "mem" else None
    # --- RÉACTION par mode ---
    threat = (vis == 1) or (remembered is not None and remembered["conf"] > 0.25)
    if threat:
        # menace (vue OU mémorisée) -> rester COUCHÉ (petite cible) + surveiller la menace. Posture seule (pas de tir).
        env.b.send('private _u = AV select 0; _u setUnitPos "DOWN"; _u doWatch [%d,%d,0];' % (ex, ey), wait=True)
    else:
        # pas de menace perçue (sans mémoire, l'ennemi planqué = oublié) -> se relever / se détendre = EXPOSÉ
        env.b.send('private _u = AV select 0; _u setUnitPos "UP"; _u doWatch objNull;', wait=True)
    if c % 6 == 0:
        rc = ("souvenir conf=%.2f" % remembered["conf"]) if remembered else "—"
        print("  t=%4.1fs | %-7s | ennemi %s | menace_perçue=%s | posture=%s | vie=%3.0f%% [%s]" % (
            now, phase, "VU" if vis else "caché", "OUI" if threat else "non",
            "couché" if threat else "DEBOUT", (1 - dmg) * 100, rc), flush=True)
    time.sleep(0.05)
print(">>> MODE=%s | dégâts encaissés=%.0f%% | pic=%.0f%% | vie finale=%.0f%%" % (MODE, dmg * 100, peak * 100, (1 - dmg) * 100), flush=True)
print("DUEL FINI", flush=True)
