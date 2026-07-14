"""formations — LE CATALOGUE : le vocabulaire géométrique des formations d'escouade (le « rang »).

Chaque formation = un générateur de SLOTS : positions-cibles relatives de n soldats dans un repère
CANONIQUE (avant = +y, droite = +x, ancre = origine). Sortie (n,3) : [x, y, face] où face = cap
que le soldat regarde (0 = vers l'avant de la formation ; pour les formes fermées, il regarde dehors).

`place(nom, n, ancre, cap)` fait tourner + translate les slots dans le monde -> positions + caps réels.
La co-évolution vient PAR-DESSUS : elle choisit la forme, l'oriente, décide les transitions.
Convention de cap identique au sandbox : cap 0 = +y, direction = (sin cap, cos cap). 100% torch, pas de physique.
"""
import math
import torch

SP = 5.0     # espacement entre soldats (m)
RR = 18.0    # rayon des formations courbes / fermées (m)


def _slots(rows):
    return torch.tensor(rows, dtype=torch.float32)          # (n,3) : x, y, face


# ---------- LINÉAIRES (front / file) ----------
def ligne(n, sp=SP, r=RR):
    return _slots([[(i - (n - 1) / 2) * sp, 0.0, 0.0] for i in range(n)])           # côte à côte, tous vers l'avant

def colonne(n, sp=SP, r=RR):
    return _slots([[0.0, -i * sp, 0.0] for i in range(n)])                          # en file derrière l'ancre

def colonne_double(n, sp=SP, r=RR):
    return _slots([[((i % 2) * 2 - 1) * sp / 2, -(i // 2) * sp, 0.0] for i in range(n)])

def echelon_droit(n, sp=SP, r=RR):
    return _slots([[i * sp * 0.7, -i * sp * 0.7, 0.0] for i in range(n)])           # escalier avant-droite
def echelon_gauche(n, sp=SP, r=RR):
    return _slots([[-i * sp * 0.7, -i * sp * 0.7, 0.0] for i in range(n)])


# ---------- POINTE / COIN ----------
def coin(n, sp=SP, r=RR):                                    # fer de lance : pointe EN AVANT
    rows = [[0.0, 0.0, 0.0]]
    for i in range(1, n):
        side = -1 if i % 2 else 1; rank = (i + 1) // 2
        rows.append([side * rank * sp * 0.8, -rank * sp, 0.0])
    return _slots(rows)

def vee(n, sp=SP, r=RR):                                     # pointe EN ARRIÈRE, s'ouvre vers l'avant
    rows = [[0.0, 0.0, 0.0]]
    for i in range(1, n):
        side = -1 if i % 2 else 1; rank = (i + 1) // 2
        rows.append([side * rank * sp * 0.8, rank * sp, 0.0])
    return _slots(rows)

def losange(n, sp=SP, r=RR):                                 # diamant : 360°, avant/arrière/2 flancs
    D = sp * max(1, (n // 4))
    rows = [[0.0, D, 0.0], [0.0, -D, math.pi]]               # pointe avant (regarde avant), arrière (regarde arrière)
    rest = n - 2; k = 0
    for i in range(rest):
        side = -1 if i % 2 else 1; rank = (i // 2) + 1
        face = -math.pi / 2 if side < 0 else math.pi / 2     # flancs regardent dehors
        rows.append([side * (D * 0.8) * (1 if rank == 1 else 0.6), (rank - 1) * sp * 0.5 * (1 if i % 4 < 2 else -1), face])
    return _slots(rows[:n])


# ---------- ENVELOPPANTES / COURBES ----------
def _arc(n, span, r, bow=0.0, face_out=True):
    """arc de n soldats sur un angle 'span' (rad total), rayon r ; face_out -> regardent dehors."""
    rows = []
    for i in range(n):
        th = (-span / 2 + span * (i / max(n - 1, 1)))
        x = r * math.sin(th); y = r * math.cos(th) - bow
        face = th if face_out else 0.0
        rows.append([x, y, face])
    return _slots(rows)

def demi_cercle(n, sp=SP, r=RR):
    return _arc(n, math.pi, r, face_out=True)                # arc avant 180°, enveloppe un secteur
def arc_cercle(n, sp=SP, r=RR):
    return _arc(n, math.pi * 0.6, r, face_out=True)          # arc partiel ~108°
def fer_a_cheval(n, sp=SP, r=RR):
    return _arc(n, math.pi * 1.4, r, face_out=True)          # ~252°, ouverture arrière (embuscade)
def croissant(n, sp=SP, r=RR):
    return _arc(n, math.pi * 0.8, r, bow=r * 0.6, face_out=True)   # cornes en avant (enveloppement)

def cercle(n, sp=SP, r=RR):                                  # périmètre 360°, tout le monde dehors
    rows = []
    for i in range(n):
        th = 2 * math.pi * i / n
        rows.append([r * math.sin(th), r * math.cos(th), th])
    return _slots(rows)


# ---------- FERMÉES / GÉOMÉTRIQUES ----------
def carre(n, sp=SP, r=RR):                                   # 4 faces, chacun regarde dehors
    L = r; per = 8 * L; rows = []
    for i in range(n):
        d = per * i / n
        if d < 2 * L:   x, y, f = -L + d, L, 0.0                              # face avant
        elif d < 4 * L: x, y, f = L, L - (d - 2 * L), math.pi / 2             # face droite
        elif d < 6 * L: x, y, f = L - (d - 4 * L), -L, math.pi                # face arrière
        else:           x, y, f = -L, -L + (d - 6 * L), -math.pi / 2          # face gauche
        rows.append([x, y, f])
    return _slots(rows)

def triangle(n, sp=SP, r=RR):                                # apex avant, distribué sur 3 côtés
    P = [(0.0, r), (-r * 0.87, -r * 0.5), (r * 0.87, -r * 0.5)]              # sommets (apex avant)
    rows = []
    for i in range(n):
        e = i * 3 // n; a = P[e]; b = P[(e + 1) % 3]
        seg = [j for j in range(n) if j * 3 // n == e]; k = seg.index(i); m = len(seg)
        t = (k + 0.5) / m
        x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        rows.append([x, y, math.atan2(x, y)])                                # regarde dehors (radial)
    return _slots(rows)


# ---------- LE CATALOGUE (forme -> géométrie + fonction) ----------
FORMATIONS = {
    "ligne":          {"fn": ligne,          "classe": "linéaire",     "couverture": "avant",   "role": "feu frontal maximal ; faible en profondeur"},
    "colonne":        {"fn": colonne,        "classe": "linéaire",     "couverture": "avant",   "role": "rapide, terrain contraint ; peu de feu latéral"},
    "colonne_double": {"fn": colonne_double, "classe": "linéaire",     "couverture": "avant",   "role": "compromis vitesse / feu"},
    "echelon_droit":  {"fn": echelon_droit,  "classe": "linéaire",     "couverture": "avant+D", "role": "couvre l'avant + le flanc droit (approche oblique)"},
    "echelon_gauche": {"fn": echelon_gauche, "classe": "linéaire",     "couverture": "avant+G", "role": "couvre l'avant + le flanc gauche"},
    "coin":           {"fn": coin,           "classe": "pointe",       "couverture": "avant+flancs", "role": "ASSAUT / pénétration ; fer de lance"},
    "vee":            {"fn": vee,            "classe": "pointe",       "couverture": "avant large",  "role": "avancer vers contact large ; couverture arrière"},
    "losange":        {"fn": losange,        "classe": "pointe",       "couverture": "360°",    "role": "unité isolée, tout-azimut"},
    "demi_cercle":    {"fn": demi_cercle,    "classe": "courbe",       "couverture": "arc avant","role": "envelopper / contenir un secteur"},
    "arc_cercle":     {"fn": arc_cercle,     "classe": "courbe",       "couverture": "arc",     "role": "enveloppement partiel"},
    "fer_a_cheval":   {"fn": fer_a_cheval,   "classe": "courbe",       "couverture": "~270°",   "role": "EMBUSCADE (gueule ouverte à l'arrière)"},
    "croissant":      {"fn": croissant,      "classe": "courbe",       "couverture": "flancs",  "role": "double enveloppement (Cannae)"},
    "cercle":         {"fn": cercle,         "classe": "fermée",       "couverture": "360°",    "role": "DÉFENSE tout-azimut, halte"},
    "carre":          {"fn": carre,          "classe": "fermée",       "couverture": "360°",    "role": "défense 4 faces (anti-cavalerie historique)"},
    "triangle":       {"fn": triangle,       "classe": "fermée",       "couverture": "360°",    "role": "brique modulaire d'articulation"},
}
NAMES = list(FORMATIONS.keys())


def slots(name, n, sp=SP, r=RR):
    return FORMATIONS[name]["fn"](n, sp, r)                  # (n,3) canonique


def place(name, n, anchor, heading, sp=SP, r=RR, device="cpu"):
    """Slots canoniques -> monde. anchor:(...,2), heading:(...) rad. Renvoie positions (...,n,2) + caps (...,n).
    Rotation : l'avant (+y) de la formation pointe vers 'heading' (convention sandbox : dir=(sin,cos))."""
    tpl = slots(name, n, sp, r).to(device)                  # (n,3)
    x = tpl[:, 0]; y = tpl[:, 1]; f = tpl[:, 2]
    anchor = torch.as_tensor(anchor, dtype=torch.float32, device=device)
    heading = torch.as_tensor(heading, dtype=torch.float32, device=device)
    ch = torch.cos(heading).unsqueeze(-1); sh = torch.sin(heading).unsqueeze(-1)   # (...,1)
    wx = x * ch + y * sh                                     # right=(cos,-sin), forward=(sin,cos)
    wy = -x * sh + y * ch
    pos = torch.stack([wx, wy], dim=-1) + anchor.unsqueeze(-2)   # (...,n,2)
    face = f + heading.unsqueeze(-1)                         # (...,n)
    return pos, face


def templates(n, sp=SP, r=RR, device="cpu"):
    """(F, n, 3) : les slots canoniques des F=15 formes pour n soldats. Précalculé une fois, réutilisé chaque pas."""
    return torch.stack([slots(nm, n, sp, r) for nm in NAMES]).to(device)


def place_idx(form_idx, tmpl, anchor, heading):
    """Placement BATCHÉ : chaque env choisit SA forme. form_idx:(N,) dans [0,F) ; tmpl:(F,n,3) ;
    anchor:(N,2) ; heading:(N,). Renvoie pos (N,n,2) + face (N,n). C'est l'action de l'étage HAUT (co-évo)."""
    sel = tmpl[form_idx.long()]                             # (N,n,3) : la forme choisie par chaque env
    x = sel[..., 0]; y = sel[..., 1]; f = sel[..., 2]
    ch = torch.cos(heading).unsqueeze(-1); sh = torch.sin(heading).unsqueeze(-1)
    wx = x * ch + y * sh; wy = -x * sh + y * ch
    pos = torch.stack([wx, wy], dim=-1) + anchor.unsqueeze(-2)
    face = f + heading.unsqueeze(-1)
    return pos, face


if __name__ == "__main__":
    print("=== CATALOGUE FORMATIONS (%d formes) ===" % len(FORMATIONS))
    for nm, m in FORMATIONS.items():
        s = slots(nm, 9)
        print("  %-15s | %-9s | %-12s | %s | slots ok=%s" % (nm, m["classe"], m["couverture"], m["role"], tuple(s.shape) == (9, 3)))
    # vérif place() : coin de 9, ancre (100,50), cap est (90° -> +x)
    pos, face = place("coin", 9, [100.0, 50.0], math.pi / 2)
    print("place(coin) -> pos[0]=%s (doit etre ~ancre), n=%d" % (pos[0].tolist(), pos.shape[0]))
    print("CATALOGUE_OK")
