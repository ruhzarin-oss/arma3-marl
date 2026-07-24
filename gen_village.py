#!/usr/bin/env python3
"""gen_village — carte-VILLAGE DESSINÉE avec ASYMÉTRIE : couloir central OUVERT (frontal exposé) + flanc EST COUVERT.
Approche = NORD (+Y, th=0). Défenseurs à (0,+35) face nord. Objectif à (0,0).
Le flanc traverse l'est derrière les bâtiments (LOS coupée), débouche à l'est de l'objectif (hors des arcs nord)."""
import numpy as np
GS = 200; W = 200.0; SCALE = 200.0   # monde [-200,200], 2 m/cellule
solid = np.zeros((GS, GS), dtype=bool)


def w2c(x): return int(np.clip((x / SCALE * 0.5 + 0.5) * (GS - 1), 0, GS - 1))   # world x -> colonne


def block(x0, x1, y0, y1):   # rempli solid pour un rectangle en coords MONDE (x=est, y=nord)
    c0, c1 = sorted((w2c(x0), w2c(x1))); r0, r1 = sorted((w2c(y0), w2c(y1)))   # w2c identique pour y->row
    solid[r0:r1 + 1, c0:c1 + 1] = True


# plages DISJOINTES : couloir central [-14,14] | mur [16,24] | voie flanc [28,44] | fond est [50,90]
# --- MUR CONTINU EST (x in [16,24], y in [10,130]) : masque TOUT l'est (x>28) des défenseurs (x in [-12,12], y~34) ---
block(16, 24, 10, 130)
block(50, 90, 20, 120)   # arrière-plan est (profondeur de couvert)
# lanes OUVERTES (colonnes = plage x, toutes lignes y) — après les murs, plages disjointes donc pas d'écrasement
solid[:, w2c(-14):w2c(14)] = False   # couloir central OUVERT (frontal exposé)
solid[:, w2c(28):w2c(44)] = False    # VOIE DE FLANC est OUVERTE (le flanc y descend, masqué par le mur)
solid[w2c(-6):w2c(6) + 1, w2c(-6):w2c(6) + 1] = False   # objectif (0,0) libre

np.savez("/home/younes/arma3-marl/replica_village.npz", solid=solid, elev=np.zeros((GS, GS), "float32"),
         solidh=np.where(solid, 12.0, 0.0).astype("float32"), cx=np.float64(0), cy=np.float64(0),
         W=np.float64(W), GS=np.int64(GS), obj=np.array([0.0, 0.0]))

# ASCII viz (N en haut) : # bâti, . libre, O objectif, D défenseurs (~0,35), S spawn (~0,140)
art = []
for r in range(GS - 1, -1, -8):        # haut = nord
    line = ""
    for c in range(0, GS, 4):
        wx = (c / (GS - 1) - 0.5) * SCALE; wy = (r / (GS - 1) - 0.5) * SCALE
        ch = "#" if solid[r, c] else "."
        if abs(wx) < 6 and abs(wy) < 6: ch = "O"
        elif abs(wx) < 6 and abs(wy - 35) < 6: ch = "D"
        elif abs(wx) < 8 and abs(wy - 140) < 8: ch = "S"
        line += ch
    art.append(line)
print("VILLAGE (haut=Nord=approche, O=objectif, D=defense, gauche=Ouest droite=Est) :")
print("\n".join(art))
print("solid%% = %.3f" % solid.mean())
