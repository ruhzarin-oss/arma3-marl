"""Extrait TOUTE la carte Stratis depuis Arma (server14, monde Stratis) via le pont :
- relief : grille NxN de getTerrainHeightASL
- bati   : tous les batiments via nearestTerrainObjects (8 km) -> rasterise
- eau    : elev <= 0
-> /home/younes/arma3-marl/stratis_full.npz (elev, solid, water, N, W)."""
import os, sys, time, re
import numpy as np
os.environ['HMT_MISSION'] = '/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis'
os.environ['HMT_LOG'] = '/mnt/data/harmattan-sandbox/logs/server14.out'
sys.path.insert(0, '/home/younes/arma3-marl')
from arma_bridge import ArmaBridge
b = ArmaBridge()
N = 160


def wait_token(tok, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if any(tok in ln for ln in b._log_lines()[-4000:]): return True
        time.sleep(1.5)
    return False


# --- worldSize ---
b.send('diag_log format ["HMT_WS %1", worldSize];', wait=True, timeout=20); time.sleep(0.6)
ws = 8192
for ln in reversed(b._log_lines()):
    m = re.search(r"HMT_WS (\d+(?:\.\d+)?)", ln)
    if m: ws = int(float(m.group(1))); break
print("worldSize=%d  grille=%dx%d (%.1f m/cellule)" % (ws, N, N, ws / N), flush=True)

# --- relief ---
ELEV = ('HMT_N=%d; HMT_WS=%d; for "_r" from 0 to (HMT_N-1) do { private _row=[]; '
        'for "_c" from 0 to (HMT_N-1) do { private _x=_c/(HMT_N-1)*HMT_WS; private _y=_r/(HMT_N-1)*HMT_WS; '
        '_row pushBack round (getTerrainHeightASL [_x,_y]); }; diag_log format ["HMT_ELEV %%1 %%2", _r, _row]; }; '
        'diag_log "HMT_ELEV_DONE";') % (N, ws)
b.send(ELEV, wait=True, timeout=360)
wait_token("HMT_ELEV_DONE", 360); time.sleep(1.0)
elev = np.zeros((N, N), dtype="float32"); got = 0
for ln in b._log_lines():
    m = re.search(r"HMT_ELEV (\d+) \[([^\]]*)\]", ln)
    if m:
        r = int(m.group(1)); vals = m.group(2).split(",")
        if r < N and len(vals) == N:
            elev[r] = [float(v) for v in vals]; got += 1
print("relief : %d/%d lignes recues, elev[%d..%d]" % (got, N, int(elev.min()), int(elev.max())), flush=True)

# --- batiments ---
BLD = ('private _o = nearestTerrainObjects [[%d,%d,0], '
       '["HOUSE","BUILDING","CHURCH","CHAPEL","HOSPITAL","FUELSTATION","LIGHTHOUSE","FORTRESS","RUIN","TOURISM","VIEW-TOWER","WATERTOWER","QUAY","TRANSMITTER"], '
       '%d, false, true]; diag_log format ["HMT_BN %%1", count _o]; '
       'private _i=0; while {_i < count _o} do { private _s=""; for "_k" from 0 to 49 do { '
       'if (_i < count _o) then { private _p=getPos (_o select _i); _s=_s+format ["%%1;%%2|", round (_p select 0), round (_p select 1)]; _i=_i+1; }; }; '
       'diag_log format ["HMT_BLD %%1", _s]; }; diag_log "HMT_BLD_DONE";') % (ws // 2, ws // 2, int(ws * 0.72))
b.send(BLD, wait=True, timeout=120)
wait_token("HMT_BLD_DONE", 120); time.sleep(1.0)
pts = []
for ln in b._log_lines():
    if "HMT_BLD " in ln:
        for tok in re.findall(r"(-?\d+);(-?\d+)\|", ln):
            pts.append((int(tok[0]), int(tok[1])))
nb = 0
for ln in reversed(b._log_lines()):
    m = re.search(r"HMT_BN (\d+)", ln)
    if m: nb = int(m.group(1)); break
print("batiments : %d annonces, %d positions parsees" % (nb, len(pts)), flush=True)

# --- grilles ---
solid = np.zeros((N, N), dtype="float32")
for (bx, by) in pts:
    c = min(max(int(bx / ws * (N - 1)), 0), N - 1); r = min(max(int(by / ws * (N - 1)), 0), N - 1)
    solid[r, c] = 1.0
water = (elev <= 0).astype("float32")
np.savez("/home/younes/arma3-marl/stratis_full.npz", elev=elev, solid=solid, water=water, N=N, W=ws)
print("SAVED stratis_full.npz | N=%d W=%d | bati=%.1f%% | eau=%.1f%%" % (N, ws, 100 * solid.mean(), 100 * water.mean()), flush=True)
