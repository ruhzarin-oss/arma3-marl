"""export_zone — exporte la VRAIE zone Arma (le complexe) : elevation + empreintes SOLIDES des batiments.
Base sur la methode de probe_arma_v2 (getTerrainHeightASL en grille + nearestObjects + boundingBoxReal).
Sortie : carte de la REPLIQUE (/tmp/replica_map.png) a valider AVANT d'entrainer dessus."""
import re, math
import numpy as np
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)   # le complexe qu'on vient de tester
CX, CY = OBJ
W = 140.0; N = 64                            # fenetre +-140 m, grille elevation 64x64
step = 2 * W / (N - 1)

env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)

sqf = ('private _cx=%d; private _cy=%d; private _W=%d; private _N=%d; private _st=%f;'
       ' for "_j" from 0 to (_N-1) do { private _r="";'
       '   for "_i" from 0 to (_N-1) do { private _x=_cx-_W+_i*_st; private _y=_cy-_W+_j*_st;'
       '     _r=_r+format ["%%1 ", round((getTerrainHeightASL [_x,_y])*10)]; };'
       '   diag_log format ["ELEV %%1 %%2", _j, _r]; };'
       ' { private _p=getPosATL _x; private _bb=boundingBoxReal _x; private _a=_bb#0; private _b=_bb#1;'
       '   diag_log format ["BLD %%1 %%2 %%3 %%4 %%5 %%6 %%7 %%8 %%9", round(_p#0),round(_p#1),round(getDir _x),'
       '     round(10*(_a#0)),round(10*(_a#1)),round(10*(_a#2)),round(10*(_b#0)),round(10*(_b#1)),round(10*(_b#2))]; }'
       ' forEach (nearestObjects [[_cx,_cy,0],["House","Building"],%d]);'
       ' diag_log "EXPORT_END";') % (CX, CY, int(W), N, step, int(W * 1.25))

ls = env._query(sqf, settle=0.9)
elev = np.full((N, N), np.nan); blds = []
for l in ls:
    me = re.search(r"ELEV (\d+) (.+)", l)
    if me:
        j = int(me.group(1)); vals = me.group(2).split()
        if len(vals) >= N:
            elev[j] = np.array([int(x) for x in vals[:N]]) / 10.0
    mb = re.search(r"BLD (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)", l)
    if mb:
        g = [int(mb.group(k)) for k in range(1, 10)]
        blds.append(g)   # px,py,dir, ax,ay,az, bx,by,bz  (bbox en decimetres)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
fig, ax = plt.subplots(figsize=(11, 11))
ext = [CX - W, CX + W, CY - W, CY + W]
if not np.all(np.isnan(elev)):
    ax.imshow(np.nan_to_num(elev, nan=np.nanmin(elev)), extent=ext, origin="lower", cmap="terrain", alpha=0.8)
nfoot = 0
for (px, py, hd, ax0, ay0, az0, bx1, by1, bz1) in blds:
    # empreinte au sol = X (largeur) x Z (profondeur) ; Y = hauteur (convention modele Arma)
    wx0, wz0, wx1, wz1 = ax0 / 10.0, az0 / 10.0, bx1 / 10.0, bz1 / 10.0
    th = math.radians(hd)
    corners = [(wx0, wz0), (wx1, wz0), (wx1, wz1), (wx0, wz1)]
    world = [(px + mx * math.cos(th) + mz * math.sin(th), py - mx * math.sin(th) + mz * math.cos(th)) for (mx, mz) in corners]
    ax.add_patch(Polygon(world, closed=True, facecolor="#2b2b2b", edgecolor="black", lw=0.4, alpha=0.92))
    nfoot += 1
ax.scatter([CX], [CY], c="red", marker="*", s=320, zorder=6, label="objectif (ennemis)")
ax.set_xlim(CX - W, CX + W); ax.set_ylim(CY - W, CY + W); ax.set_aspect("equal"); ax.legend(loc="upper right")
ax.set_title("REPLIQUE du complexe (donnees Arma reelles)\nelevation = couleur, batiments SOLIDES = gris fonce | %d batiments, %dx%d elev" % (nfoot, N, N))
fig.tight_layout(); fig.savefig("/tmp/replica_map.png", dpi=110)
print("EXPORT OK : elevation %dx%d (%.1f-%.1f m), %d batiments solides" % (
    N, N, (np.nanmin(elev) if not np.all(np.isnan(elev)) else 0), (np.nanmax(elev) if not np.all(np.isnan(elev)) else 0), nfoot))
