"""system_id — SONDER LES DYNAMIQUES DU CORPS ARMA (le 1er chiffre du mur). Un soldat seul, sur terrain ouvert.
Test A : course pleine vitesse en ligne droite -> accélération + vitesse de pointe.
Test B : ordre de pivoter ~120 deg -> vitesse de rotation.
Ces lois commande->réponse calibrent le twin ET quantifient l'écart sim<->Arma."""
import time, re
import numpy as np
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
P0 = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)        # sud de Paros, terrain dégagé (zone d'approche validée)
env = OpArma(squads=(("X", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=0)
print("spawn 1 soldat a %s (terrain ouvert), pas d'ennemi" % str(P0), flush=True)
env.spawn({"X": P0}, [])
env.b.send('private _u = X select 0; _u setBehaviour "CARELESS"; _u setCombatMode "BLUE"; _u allowFleeing 0; _u setUnitPos "UP"; doStop _u; diag_log "READY";', wait=True)
time.sleep(2)


def sample():
    ls = env._query('private _u=X select 0; private _p=getPosATL _u; diag_log format ["SID v=%1 x=%2 y=%3 dir=%4", round((vectorMagnitude velocity _u)*100), round((_p#0)*10), round((_p#1)*10), round(getDir _u)];', settle=0.35)
    for l in ls:
        m = re.search(r"SID v=(\d+) x=(-?\d+) y=(-?\d+) dir=(\d+)", l)
        if m:
            return int(m.group(1)) / 100.0, int(m.group(2)) / 10.0, int(m.group(3)) / 10.0, int(m.group(4))
    return None


# ---------- TEST A : course pleine vitesse ----------
TGT = (P0[0], P0[1] - 200)                          # 200 m plein sud
env.b.send('private _u=X select 0; _u forceSpeed -1; _u setSpeedMode "FULL"; _u doMove [%d,%d];' % (TGT[0], TGT[1]), wait=True)
print("\n=== TEST A : course (forceSpeed -1, doMove 200m) ===", flush=True)
print("t(s) | vitesse(m/s)", flush=True)
t0 = time.time(); vmax = 0.0; t_vmax = 0.0
for i in range(16):
    s = sample()
    if s:
        v = s[0]; t = round(time.time() - t0, 1)
        if v > vmax:
            vmax = v; t_vmax = t
        print("%4.1f | %.2f" % (t, v), flush=True)
    time.sleep(0.45)
print(">>> vitesse de pointe ~ %.2f m/s (atteinte vers %.1fs -> accel ~ %.2f m/s2)" % (vmax, t_vmax, vmax / max(t_vmax, 0.5)), flush=True)

# ---------- TEST B : rotation ----------
env.b.send('private _u=X select 0; doStop _u; _u forceSpeed 0;', wait=True); time.sleep(2)
s = sample(); d0 = s[3] if s else 0
import math
tx = P0[0] + int(200 * math.sin(math.radians(d0 + 120))); ty = P0[1] + int(200 * math.cos(math.radians(d0 + 120)))
env.b.send('private _u=X select 0; _u doWatch [%d,%d,0]; _u doMove [%d,%d];' % (tx, ty, tx, ty), wait=True)
print("\n=== TEST B : pivot ~120 deg (depuis %d deg) ===" % d0, flush=True)
print("t(s) | cap(deg)", flush=True)
t0 = time.time(); prevd = d0; maxrate = 0.0
for i in range(10):
    s = sample()
    if s:
        d = s[3]; t = round(time.time() - t0, 1)
        dd = (d - prevd + 540) % 360 - 180
        rate = abs(dd) / 0.45
        maxrate = max(maxrate, rate); prevd = d
        print("%4.1f | %d" % (t, d), flush=True)
    time.sleep(0.45)
print(">>> vitesse de rotation max ~ %.0f deg/s" % maxrate, flush=True)
print("SID FINI")
