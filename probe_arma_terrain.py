"""Probe B — Arma peut-il exporter une grille de terrain autour d'un point ? (elevation 32x32 + routes + batiments)"""
import re
from op_arma import OpArma
import maneuvers as M
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=M.SQUADS, mission=SB+"/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB+"/logs/server0.out", move=36, seed=1)
sqf = ('private _t0 = diag_tickTime; private _grid = []; '
       'for "_i" from 0 to 31 do { for "_j" from 0 to 31 do { '
       '_grid pushBack (getTerrainHeightASL [15000 - 64 + _i*4, 16000 - 64 + _j*4]); }; }; '
       'private _dt = diag_tickTime - _t0; '
       'private _roads = count (nearestRoads [[15000,16000,0], 300]); '
       'private _bldg = count (nearestTerrainObjects [[15000,16000,0], ["HOUSE","BUILDING"], 400]); '
       'diag_log format ["HMT_TERRAIN dt=%1 n=%2 hmin=%3 hmax=%4 roads=%5 bldg=%6", _dt, count _grid, selectMin _grid, selectMax _grid, _roads, _bldg];')
got = None
for ln in reversed(env._query(sqf)):
    m = re.search(r"HMT_TERRAIN dt=([0-9.]+) n=(\d+) hmin=([0-9.eE+-]+) hmax=([0-9.eE+-]+) roads=(\d+) bldg=(\d+)", ln)
    if m: got = m; break
if got:
    dt=float(got.group(1)); n=int(got.group(2))
    print("grille %d points (32x32, pas 4m) extraite en %.3fs (-> 64x64 ~ %.2fs)" % (n, dt, dt*4))
    print("elevation: %.1f a %.1f m (variation %.1f m)" % (float(got.group(3)), float(got.group(4)), float(got.group(4))-float(got.group(3))))
    print("routes <300m: %s | batiments <400m: %s" % (got.group(5), got.group(6)))
    print(">>> EXPORT ARMA: FAISABLE" if dt < 5 else ">>> lent (pre-calcul offline obligatoire)")
else:
    print("pas de reponse HMT_TERRAIN (commande SQF a verifier)")
