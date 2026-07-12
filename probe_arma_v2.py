"""Probe B v2 — isole l'elevation (couche critique) + teste les syntaxes routes/batiments separement."""
import re
from op_arma import OpArma
import maneuvers as M
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=M.SQUADS, mission=SB+"/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB+"/logs/server0.out", move=36, seed=1)

# 1) ELEVATION SEULE (+ marqueur depart pour savoir si le SQF tourne du tout)
sqf = ('diag_log "HMT_PROBE_START"; '
       'private _t0 = diag_tickTime; private _grid = []; '
       'for "_i" from 0 to 31 do { for "_j" from 0 to 31 do { '
       '_grid pushBack (getTerrainHeightASL [15000 - 64 + _i*4, 16000 - 64 + _j*4]); }; }; '
       'diag_log format ["HMT_ELEV dt=%1 n=%2 hmin=%3 hmax=%4", diag_tickTime - _t0, count _grid, selectMin _grid, selectMax _grid];')
lines = env._query(sqf)
start = any("HMT_PROBE_START" in l for l in lines)
elev = None
for ln in reversed(lines):
    m = re.search(r"HMT_ELEV dt=([0-9.]+) n=(\d+) hmin=([0-9.eE+-]+) hmax=([0-9.eE+-]+)", ln)
    if m: elev = m; break
print("SQF tourne (HMT_PROBE_START vu): %s" % start)
if elev:
    dt=float(elev.group(1))
    print("ELEVATION: %s pts en %.3fs | %.1f a %.1f m (var %.1f m) -> %s" % (elev.group(2), dt, float(elev.group(3)), float(elev.group(4)), float(elev.group(4))-float(elev.group(3)), "FAISABLE" if dt<5 else "lent (offline)"))
else:
    print("ELEVATION: pas de reponse")

# 2) ROUTES + BATIMENTS : 3 syntaxes candidates, on voit laquelle marche
for label, expr in [("nearRoads", 'count ([15000,16000,0] nearRoads 300)'),
                    ("nearestTerrainObjects(road)", 'count (nearestTerrainObjects [[15000,16000,0], ["ROAD"], 300])'),
                    ("nearestObjects(house)", 'count (nearestObjects [[15000,16000,0], ["House"], 400])'),
                    ("nearestTerrainObjects(house)", 'count (nearestTerrainObjects [[15000,16000,0], ["HOUSE","BUILDING"], 400])')]:
    sqf2 = 'private _r = -1; _r = %s; diag_log format ["HMT_Q %%1", _r];' % expr
    res = None
    for ln in reversed(env._query(sqf2)):
        mm = re.search(r"HMT_Q (-?\d+)", ln)
        if mm: res = mm.group(1); break
    print("  %-32s -> %s" % (label, res if res is not None else "ERREUR/aucune reponse"))
