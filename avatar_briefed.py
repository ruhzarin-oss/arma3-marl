"""avatar_briefed — BRIEFING + MÉMOIRE = CONTEXTE. L'agent reçoit un briefing (objectif + ennemi présumé sur un
flanc) qui PRÉ-CHARGE sa mémoire épisodique/spatiale. Il avance vers l'objectif MAIS, grâce au briefing, surveille
déjà la menace présumée — il ANTICIPE. L'agent aveugle ne réagit qu'à vue.
Métrique robuste (sans dépendre du tir) : ORIENTATION vers la menace réelle (erreur de cap), surtout AVANT le
premier contact visuel. args: mode(briefed/blind) server_idx seed cycles."""
import time, re, sys, math
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
from memory_system import MemorySystem
import paros as M
SB = "/mnt/data/harmattan-sandbox"
MODE = sys.argv[1] if len(sys.argv) > 1 else "briefed"
SRV = int(sys.argv[2]) if len(sys.argv) > 2 else 7
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 90
CYCLES = int(sys.argv[4]) if len(sys.argv) > 4 else 150
cx, cy = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
OBJ = (cx, cy)                         # objectif plein nord
E_FLANC = (cx + 45, cy - 25)           # ennemi RÉEL sur le flanc droit (nord-est)
START = (cx, cy - 70)
# ───── LE BRIEFING (ce que l'officier transmet ; ici structuré, pourrait venir du LLM officier) ─────
BRIEFING = {
    "objectif": OBJ,
    "ennemi_presume": (cx + 42, cy - 28),     # position PRÉSUMÉE (proche du réel, pas exacte)
    "consigne": "avance prudente, surveille le flanc droit",
}


def cap_vers(px, py, tx, ty):
    return (math.degrees(math.atan2(tx - px, ty - py)) + 360) % 360     # cap compas (0=nord)


def err_cap(a, b):
    return abs((a - b + 180) % 360 - 180)


env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
env.spawn({"AV": START}, [(E_FLANC[0], E_FLANC[1], 1, 1)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '(AV select 0) setBehaviour "AWARE"; (AV select 0) setCombatMode "YELLOW"; (AV select 0) setSpeedMode "NORMAL";'
           '{ _x enableAI "ALL"; _x setSkill 0.6; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "UP"; } forEach HMT_EN;', wait=True)
time.sleep(2)
mem = MemorySystem(14, OBJ, plan=[("rejoindre", OBJ)])
# ───── PRÉ-CHARGEMENT par le briefing (mode briefed seulement) ─────
if MODE == "briefed":
    bx, by = BRIEFING["ennemi_presume"]
    mem.episodique.slots[99] = {"x": bx, "y": by, "t_last": 0.0, "conf": 0.6, "dmg": 0, "seen_count": 0}  # contact PRÉSUMÉ
    mem.episodique.tau = 1e9   # un briefing ne s'oublie pas tout seul ; il se CONFIRME ou se corrige
print("=== BRIEFING+MÉMOIRE : MODE=%s ===" % MODE, flush=True)
if MODE == "briefed":
    print("   briefing reçu : objectif au nord ; ennemi présumé flanc droit (%d,%d) ; %s" % (BRIEFING["ennemi_presume"][0], BRIEFING["ennemi_presume"][1], BRIEFING["consigne"]), flush=True)
t0 = time.time(); first_seen_t = None; err_avant = []; oriente_avant = 0; n_avant = 0; last_watch = None
for c in range(CYCLES):
    ls = env._query('private _u = AV select 0; private _p = getPosATL _u;'
                    ' diag_log format ["AV %1 %2 %3 %4", round(_p#0), round(_p#1), round(getDir _u), round((getDammage _u)*100)];'
                    ' private _e = HMT_EN select 0; private _q = getPosATL _e; private _vis = 0;'
                    ' if (alive _e && {(AV select 0) distance _e < 130} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    ' diag_log format ["EN %1 %2 %3 %4", round(_q#0), round(_q#1), _vis, round((getDammage _e)*100)];', settle=0.08)
    px, py, hdir, dmg, ex, ey, vis = START[0], START[1], 0, 0.0, E_FLANC[0], E_FLANC[1], 0
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if m:
            px = int(m.group(1)); py = int(m.group(2)); hdir = int(m.group(3)); dmg = int(m.group(4)) / 100.0
        me = re.search(r"EN (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if me:
            ex = int(me.group(1)); ey = int(me.group(2)); vis = int(me.group(3))
    now = time.time() - t0
    mem.episodique.observe([(99, ex, ey, 0, vis == 1)], now)            # la perception CONFIRME/corrige le briefing
    remembered = mem.episodique.nearest(now, px, py) if MODE == "briefed" or vis else (None)
    if vis and first_seen_t is None:
        first_seen_t = now
    # cap réel de l'avatar vs cap vers la menace RÉELLE
    cap_menace = cap_vers(px, py, ex, ey)
    e = err_cap(hdir, cap_menace)
    if first_seen_t is None:                                            # fenêtre AVANT le premier contact visuel
        err_avant.append(e); n_avant += 1
        if e < 45: oriente_avant += 1
    # ───── COMPORTEMENT ─────
    cible = remembered if remembered else (None)
    if MODE == "briefed" and cible is not None:
        # le briefing/souvenir : avancer vers l'objectif MAIS surveiller la menace présumée (anticipation)
        wt = (int(cible["x"]), int(cible["y"]))
        if wt != last_watch:
            env.b.send('private _u = AV select 0; _u setUnitPos "AUTO"; _u doMove [%d,%d,0]; _u doWatch [%d,%d,0];' % (OBJ[0], OBJ[1], wt[0], wt[1]), wait=True); last_watch = wt
    else:
        # aveugle : avancer vers l'objectif, regard droit devant (vers l'objectif)
        if last_watch != "obj":
            env.b.send('private _u = AV select 0; _u setUnitPos "AUTO"; _u doMove [%d,%d,0]; _u doWatch [%d,%d,0];' % (OBJ[0], OBJ[1], OBJ[0], OBJ[1]), wait=True); last_watch = "obj"
    if c % 6 == 0:
        tag = "VU" if vis else ("présumé" if (MODE == "briefed" and first_seen_t is None) else "—")
        print("  t=%4.1fs|pos(%d,%d) cap=%3d°|menace %s à cap %3d° (erreur %3d°)|orienté=%s" % (
            now, px, py, hdir, tag, int(cap_menace), int(e), "OUI" if e < 45 else "non"), flush=True)
    time.sleep(0.05)
moy = sum(err_avant) / max(len(err_avant), 1)
frac = 100.0 * oriente_avant / max(n_avant, 1)
print(">>> MODE=%s | AVANT 1er contact : erreur de cap moyenne vers la menace = %.0f° | temps orienté vers la menace = %.0f%% | 1er contact à %s" % (
    MODE, moy, frac, ("%.0fs" % first_seen_t) if first_seen_t else "jamais"), flush=True)
print("BRIEF FINI", flush=True)
