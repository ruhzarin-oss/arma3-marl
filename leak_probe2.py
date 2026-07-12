"""leak_probe2 — teste le FIX : UN seul env/pont par serveur, re-spawn 12x dessus (pas de reconnexion).
Si 12/12 propres -> la solution est la REUTILISATION de connexion (1 pont/serveur, re-spawn par op)."""
import re
from op_arma import OpArma
from enemy_profiles import apply_profile
from geometries import GEOMETRIES
import maneuvers as M
import officer_geo as OG

def counts(env):
    sqf = ('diag_log format ["HMT_LEAK g=%1 u=%2 eg=%3", count allGroups, count allUnits, '
           'count (allGroups select {count units _x == 0})];')
    for ln in reversed(env._query(sqf)):
        mm = re.search(r"HMT_LEAK g=(\d+) u=(\d+) eg=(\d+)", ln)
        if mm: return tuple(int(mm.group(k)) for k in range(1, 4))
    return None

mis = OG.SB + "/arma3server/mpmissions/HarmattanBridge0.Altis"
log = OG.SB + "/logs/server0.out"
env = OpArma(squads=M.SQUADS, mission=mis, log=log, move=36, seed=7000)   # UN env, cree une fois
print("op | groupes unites groupes_vides", flush=True)
for i in range(12):
    garrison, prof = apply_profile(env, "skilled", GEOMETRIES["standard"])
    env.spawn(M.SPAWNS, garrison)            # RE-SPAWN sur le MEME pont (pas de nouvelle connexion)
    print("%2d | %s" % (i, counts(env)), flush=True)
print("REUSE OK", flush=True)
