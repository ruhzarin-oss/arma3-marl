"""export_replica — exporte le complexe Arma ET le rasterise en GRILLE D'OCCUPATION SOLIDE
(ce que le sandbox-replique utilisera : murs qui bloquent mouvement + LOS). Sauve replica.npz, rend la verif."""
import re, math
import numpy as np
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
CX, CY = OBJ
W = 140.0; NE = 64; GS = 140                 # fenetre +-140m ; elev 64x64 ; occupation 140x140 (2 m/case)
step = 2 * W / (NE - 1)

env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)
sqf = ('private _cx=%d; private _cy=%d; private _W=%d; private _N=%d; private _st=%f;'
       ' for "_j" from 0 to (_N-1) do { private _r="";'
       '   for "_i" from 0 to (_N-1) do { _r=_r+format ["%%1 ", round((getTerrainHeightASL [_cx-_W+_i*_st, _cy-_W+_j*_st])*10)]; };'
       '   diag_log format ["ELEV %%1 %%2", _j, _r]; };'
       ' { private _p=getPosATL _x; private _a=(boundingBoxReal _x)#0; private _b=(boundingBoxReal _x)#1;'
       '   diag_log format ["BLD %%1 %%2 %%3 %%4 %%5 %%6 %%7", round(_p#0),round(_p#1),round(getDir _x),'
       '     round(10*(_a#0)),round(10*(_a#2)),round(10*(_b#0)),round(10*(_b#2))]; }'
       ' forEach (nearestObjects [[_cx,_cy,0],["House","Building"],%d]);'
       ' diag_log "EXPORT_END";') % (CX, CY, int(W), NE, step, int(W * 1.25))
ls = env._query(sqf, settle=0.9)

elev = np.full((NE, NE), np.nan); blds = []
for l in ls:
    me = re.search(r"ELEV (\d+) (.+)", l)
    if me:
        j = int(me.group(1)); v = me.group(2).split()
        if len(v) >= NE:
            elev[j] = np.array([int(x) for x in v[:NE]]) / 10.0
    mb = re.search(r"BLD (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)", l)
    if mb:
        blds.append([int(mb.group(k)) for k in range(1, 8)])   # px,py,dir, xmin,zmin,xmax,zmax (decimetres)

# --- rasterisation : grille d'occupation solide (cases dans un batiment = 1) ---
xs = CX - W + (np.arange(GS) + 0.5) * (2 * W / GS)
ys = CY - W + (np.arange(GS) + 0.5) * (2 * W / GS)
GX, GY = np.meshgrid(xs, ys)                                    # (GS,GS) centres de cases
solid = np.zeros((GS, GS), dtype=bool)
for (px, py, hd, xmin, zmin, xmax, zmax) in blds:
    th = math.radians(hd); dx = GX - px; dy = GY - py
    mx = dx * math.cos(th) - dy * math.sin(th)                  # monde -> repere batiment
    mz = dx * math.sin(th) + dy * math.cos(th)
    solid |= (mx >= xmin / 10.) & (mx <= xmax / 10.) & (mz >= zmin / 10.) & (mz <= zmax / 10.)

# elevation re-echantillonnee a GS (pour une grille unifiee)
from numpy import interp
ei = np.linspace(0, NE - 1, GS)
elevG = np.array([np.interp(ei, np.arange(NE), elev[min(int(round(j)), NE - 1)]) for j in ei]) if not np.all(np.isnan(elev)) else np.zeros((GS, GS))

np.savez("/home/younes/arma3-marl/replica.npz", solid=solid, elev=elevG,
         cx=CX, cy=CY, W=W, GS=GS, obj=np.array(OBJ))
print("REPLICA sauvee : solid %dx%d (%.1f%% bati), elev %.1f-%.1f m, %d batiments" %
      (GS, GS, 100 * solid.mean(), np.nanmin(elev), np.nanmax(elev), len(blds)))

# --- verif visuelle : empreintes (gauche) vs grille rasterisee (droite) ---
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
fig, (a1, a2) = plt.subplots(1, 2, figsize=(18, 9))
ext = [CX - W, CX + W, CY - W, CY + W]
a1.imshow(elevG, extent=ext, origin="lower", cmap="terrain", alpha=0.7)
for (px, py, hd, xmin, zmin, xmax, zmax) in blds:
    th = math.radians(hd)
    cc = [(xmin / 10., zmin / 10.), (xmax / 10., zmin / 10.), (xmax / 10., zmax / 10.), (xmin / 10., zmax / 10.)]
    wd = [(px + mx * math.cos(th) + mz * math.sin(th), py - mx * math.sin(th) + mz * math.cos(th)) for (mx, mz) in cc]
    a1.add_patch(Polygon(wd, closed=True, facecolor="#2b2b2b", edgecolor="k", lw=.3))
a1.scatter([CX], [CY], c="red", marker="*", s=250); a1.set_title("Empreintes Arma (vecteur)")
a2.imshow(solid, extent=ext, origin="lower", cmap="gray_r", alpha=1.0)
a2.scatter([CX], [CY], c="red", marker="*", s=250); a2.set_title("Grille d'occupation SOLIDE (%dx%d, 2 m/case) = ce que le sandbox utilise" % (GS, GS))
for a in (a1, a2):
    a.set_xlim(CX - W, CX + W); a.set_ylim(CY - W, CY + W); a.set_aspect("equal")
fig.tight_layout(); fig.savefig("/tmp/replica_grid.png", dpi=100)
print("VERIF -> /tmp/replica_grid.png")
