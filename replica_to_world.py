#!/usr/bin/env python3
"""replica_to_world.py — ETAPE 1 du pont vers Isaac.
Transforme une carte replica (.npz : relief + batiments) en DESCRIPTION d'un monde physique 3D :
  - un CHAMP DE HAUTEURS (le relief du terrain, navigable)
  - des BOITES (les batiments, regroupes en rectangles pour ne pas en avoir 10 000)
Numpy pur, AUCUNE dependance Isaac -> ne peut pas planter. Sortie = world_<nom>.npz.
L'etape 2 (script Isaac) chargera ce fichier pour construire la scene 3D et y poser le G1."""
import argparse, numpy as np


def rects_from_mask(solid, hb):
    """Decoupe le masque bati en rectangles (greedy), groupes par hauteur arrondie -> peu de boites."""
    G = solid.shape[0]; claimed = np.zeros_like(solid, dtype=bool); rects = []
    for j in range(G):
        for i in range(G):
            if not solid[j, i] or claimed[j, i]:
                continue
            h = hb[j, i]
            i1 = i                                          # etendre en largeur (colonnes)
            while i1 + 1 < G and solid[j, i1 + 1] and not claimed[j, i1 + 1] and hb[j, i1 + 1] == h:
                i1 += 1
            j1 = j                                          # etendre en hauteur (lignes) tant que toute la bande colle
            while j1 + 1 < G and solid[j1 + 1, i:i1 + 1].all() and not claimed[j1 + 1, i:i1 + 1].any() and (hb[j1 + 1, i:i1 + 1] == h).all():
                j1 += 1
            claimed[j:j1 + 1, i:i1 + 1] = True
            rects.append((i, i1, j, j1, int(h)))
    return rects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="athens")
    ap.add_argument("--dir", default="/home/younes/arma3-marl")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    R = np.load("%s/replica_%s.npz" % (a.dir, a.name))
    solid = R["solid"] > 0.5
    elev = R["elev"].astype(np.float32)
    solidh = R["solidh"].astype(np.float32)
    G = int(R["GS"]); W = float(R["W"]); cell = 2.0 * W / (G - 1)

    hb = np.where(solid, np.round(np.maximum(solidh, 3.0)), 0).astype(int)   # hauteur arrondie (min 3 m), 0 hors bati
    rects = rects_from_mask(solid, hb)
    boxes = []
    for (i0, i1, j0, j1, h) in rects:
        cx = (((i0 + i1) / 2.0) / (G - 1) - 0.5) * 2.0 * W    # centre en metres, monde centre sur (0,0)
        cy = (((j0 + j1) / 2.0) / (G - 1) - 0.5) * 2.0 * W
        sx = (i1 - i0 + 1) * cell; sy = (j1 - j0 + 1) * cell  # taille en metres
        base = float(elev[j0:j1 + 1, i0:i1 + 1].mean())       # le batiment pose sur le sol local
        boxes.append([cx, cy, base + h / 2.0, sx, sy, float(h)])
    boxes = np.array(boxes, dtype=np.float32) if boxes else np.zeros((0, 6), np.float32)

    out = a.out or ("%s/world_%s.npz" % (a.dir, a.name))
    np.savez(out, heightfield=elev, cell=np.float32(cell), W=np.float32(W), boxes=boxes)

    print("=== MONDE PHYSIQUE : %s ===" % a.name)
    print("  terrain      : %d x %d cases, %.1f m/case  -> %.0f x %.0f m" % (G, G, cell, 2 * W, 2 * W))
    print("  relief       : %.1f m (min %.1f -> max %.1f)" % (elev.max() - elev.min(), elev.min(), elev.max()))
    print("  batiments    : %d cases baties  ->  %d BOITES (regroupees, x%.0f moins)" %
          (int(solid.sum()), len(boxes), max(1, int(solid.sum()) / max(1, len(boxes)))))
    if len(boxes):
        print("  boite type   : hauteur %.0f-%.0f m, emprise %.0f-%.0f m de cote" %
              (boxes[:, 5].min(), boxes[:, 5].max(), np.minimum(boxes[:, 3], boxes[:, 4]).min(), np.maximum(boxes[:, 3], boxes[:, 4]).max()))
    print("  -> ecrit %s  (heightfield + %d boites, pret pour Isaac)" % (out, len(boxes)))


if __name__ == "__main__":
    main()
