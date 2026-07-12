#!/usr/bin/env python3
"""osm_to_replica.py — SORT LA GEOMETRIE OSM VERS LE FORMAT SANDBOX (replica.npz).
OSM (empreintes batiments + hauteurs) -> grille d'occupation SOLIDE + hauteurs -> exactement ce que
AssaultTerrain charge (comme replica.npz Stratis). Meme pattern que export_replica.py, source = OSM.
  sortie : replica_<name>.npz {solid[GS,GS] bool, elev[GS,GS], solidh[GS,GS] (hauteur bati m), cx,cy,W,GS,obj}
  + verif visuelle /tmp/osm_<name>.png (empreintes vecteur | grille rasterisee)."""
import argparse, math
import numpy as np
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep
from shapely.strtree import STRtree


def height_of(row):
    h = row.get("height", None)
    try:
        return float(str(h).split()[0])
    except Exception:
        pass
    lv = row.get("building:levels", None)
    try:
        return float(str(lv).split()[0]) * 3.0
    except Exception:
        pass
    return 6.0                                              # defaut ~2 etages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--W", type=float, default=200.0)       # demi-fenetre en metres (fenetre = 2W)
    ap.add_argument("--cell", type=float, default=2.0)      # metres / case
    ap.add_argument("--name", default="ville")
    a = ap.parse_args()
    GS = int(round(2 * a.W / a.cell))
    print("[osm] %s : fenetre %dx%d m, grille %dx%d (%.1f m/case)" % (a.name, 2 * a.W, 2 * a.W, GS, GS, a.cell), flush=True)

    # 1. batiments OSM autour du centre
    b = ox.features_from_point((a.lat, a.lon), tags={"building": True}, dist=a.W * 1.6)
    b = b[b.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
    print("[osm] %d batiments (polygones)" % len(b), flush=True)

    # 2. projection metrique locale (UTM auto) + centre en metres
    utm = b.estimate_utm_crs()
    b = b.to_crs(utm)
    center = gpd.GeoSeries([Point(a.lon, a.lat)], crs="EPSG:4326").to_crs(utm).iloc[0]
    cx, cy = float(center.x), float(center.y)
    b["h"] = b.apply(height_of, axis=1)

    # 3. rasterisation : centre de case dans un batiment -> solide (+ hauteur max)
    xs = cx - a.W + (np.arange(GS) + 0.5) * (2 * a.W / GS)
    ys = cy - a.W + (np.arange(GS) + 0.5) * (2 * a.W / GS)
    geoms = list(b.geometry); hts = list(b["h"])
    union = b.unary_union; pu = prep(union)                 # test solide rapide
    tree = STRtree(geoms)                                   # pour retrouver la hauteur
    solid = np.zeros((GS, GS), dtype=bool)
    solidh = np.zeros((GS, GS), dtype=np.float32)
    for j, yy in enumerate(ys):
        for i, xx in enumerate(xs):
            p = Point(xx, yy)
            if pu.contains(p):
                solid[j, i] = True
                for idx in tree.query(p):
                    g = geoms[idx if np.isscalar(idx) else int(idx)]
                    if g.contains(p):
                        solidh[j, i] = max(solidh[j, i], hts[idx if np.isscalar(idx) else int(idx)])
    elev = np.zeros((GS, GS), dtype=np.float32)              # plat pour v1 (DEM plus tard)

    out = "/home/younes/arma3-marl/replica_%s.npz" % a.name
    np.savez(out, solid=solid, elev=elev, solidh=solidh, cx=cx, cy=cy, W=a.W, GS=GS, obj=np.array([cx, cy]))
    print("[osm] SAUVE %s : solid %dx%d (%.1f%% bati), hauteur max %.0f m, %d batiments" %
          (out, GS, GS, 100 * solid.mean(), solidh.max(), len(b)), flush=True)

    # 4. verif visuelle : empreintes (vecteur) | grille solide rasterisee
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(18, 9))
    ext = [cx - a.W, cx + a.W, cy - a.W, cy + a.W]
    b.plot(ax=a1, facecolor="#2b2b2b", edgecolor="k", linewidth=0.2)
    a1.scatter([cx], [cy], c="red", marker="*", s=200); a1.set_title("%s — empreintes OSM (vecteur)" % a.name)
    a2.imshow(solid, extent=ext, origin="lower", cmap="gray_r"); a2.scatter([cx], [cy], c="red", marker="*", s=200)
    a2.set_title("grille SOLIDE %dx%d (%.1f m/case) = ce que le sandbox charge" % (GS, GS, a.cell))
    for ax in (a1, a2):
        ax.set_xlim(cx - a.W, cx + a.W); ax.set_ylim(cy - a.W, cy + a.W); ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig("/tmp/osm_%s.png" % a.name, dpi=90)
    print("[osm] VERIF -> /tmp/osm_%s.png" % a.name, flush=True)


if __name__ == "__main__":
    main()
