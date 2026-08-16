#!/usr/bin/env python3
"""
KIT MODULAIRE -- un batiment praticable a partir d'une emprise reelle.

Entree  : un polygone d'emprise en metres, une hauteur.
Sortie  : une liste de solides orientes, en METRES, chacun portant son
          materiau et son epaisseur.

Ce fichier ne sait rien d'Unreal. C'est voulu : la geometrie doit pouvoir
etre lue par le moteur, par le gymnase et par le solveur, sans qu'aucun des
trois ne soit proprietaire de la source.

Tout est une BOITE ORIENTEE. Les dalles suivent le vrai polygone par
decoupe en bandes -- pas de boite englobante qui deborderait les murs.
"""
import json
import math

# ---------------------------------------------------------------- reglages
H_ETAGE      = 3.00     # hauteur d'etage
EP_MUR_EXT   = 0.30     # mur porteur
EP_CLOISON   = 0.10
EP_DALLE     = 0.20
ALLEGE       = 0.90     # bas de fenetre
LINTEAU      = 2.10     # haut de fenetre / de porte
LARG_FENETRE = 1.20
PAS_FENETRE  = 3.50     # entraxe
LARG_PORTE   = 1.00
PAS_BANDE    = 0.50     # finesse de decoupe des dalles

MATERIAUX = {
    "mur_ext":  {"materiau": "beton",    "epaisseur_m": EP_MUR_EXT},
    "cloison":  {"materiau": "platre",   "epaisseur_m": EP_CLOISON},
    "dalle":    {"materiau": "beton",    "epaisseur_m": EP_DALLE},
    "marche":   {"materiau": "beton",    "epaisseur_m": 0.18},
}


# ---------------------------------------------------------------- geometrie
def aire_signee(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def centroide(poly):
    a = aire_signee(poly)
    if abs(a) < 1e-9:
        n = len(poly)
        return (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    cx = cy = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        f = x0 * y1 - x1 * y0
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    return (cx / (6 * a), cy / (6 * a))


def normaliser(poly):
    """Recentre sur le centroide et force le sens trigonometrique."""
    cx, cy = centroide(poly)
    p = [(x - cx, y - cy) for x, y in poly]
    if aire_signee(p) < 0:
        p.reverse()
    return p


# La source DOIT etre alignee sur la grille du millimetre. Sinon une valeur
# comme 1,3235 tombe sur la frontiere d'arrondi et c'est l'aller-retour
# float32 du moteur qui decide de quel cote elle bascule -- deux empreintes
# differentes pour un monde identique.
GRILLE = 3


def solide(nom, kind, centre, demi, yaw=0.0):
    m = MATERIAUX.get(kind, {"materiau": "inconnu", "epaisseur_m": 0.0})
    return {
        "nom": nom,
        "type": kind,
        "centre_m": [round(v, GRILLE) for v in centre],
        "demi_m":   [round(v, GRILLE) for v in demi],
        "yaw_deg":  round(yaw, GRILLE),
        "materiau": m["materiau"],
        "epaisseur_m": m["epaisseur_m"],
    }


# ---------------------------------------------------------------- murs
def bandes_pleines(longueur, ouvertures):
    """Les morceaux de mur qui restent entre les ouvertures, le long d'une arete.

    ouvertures : liste de (debut, fin) en abscisse curviligne.
    Renvoie les segments pleins, sous forme (debut, fin).
    """
    ouvertures = sorted(o for o in ouvertures if o[1] > 0 and o[0] < longueur)
    pleins, curseur = [], 0.0
    for a, b in ouvertures:
        a, b = max(0.0, a), min(longueur, b)
        if a > curseur:
            pleins.append((curseur, a))
        curseur = max(curseur, b)
    if curseur < longueur:
        pleins.append((curseur, longueur))
    return [(a, b) for a, b in pleins if b - a > 0.05]


def positions_fenetres(longueur):
    """Fenetres regulierement reparties, jamais a moins de 0,8 m d'un angle."""
    marge = 0.80
    utile = longueur - 2 * marge
    if utile < LARG_FENETRE:
        return []
    n = max(1, int(utile // PAS_FENETRE))
    pas = utile / n
    out = []
    for i in range(n):
        c = marge + pas * (i + 0.5)
        out.append((c - LARG_FENETRE / 2, c + LARG_FENETRE / 2))
    return out


def mur_arete(idx, p0, p1, z_bas, avec_porte, ouvertures_out=None):
    """Une arete d'emprise -> les boites qui la composent, ouvertures comprises.

    ouvertures_out : si fourni, on y depose chaque ouverture avec sa position
    monde et la NORMALE SORTANTE du mur. Le banc doit pouvoir viser une
    fenetre precise, pas la chercher a tatons.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    if L < 0.20:
        return []
    yaw = math.degrees(math.atan2(dy, dx))
    ux, uy = dx / L, dy / L
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    out = []

    def boite(nom, s0, s1, zb, zh):
        """Boite couvrant [s0,s1] le long de l'arete, entre zb et zh."""
        sc = (s0 + s1) / 2 - L / 2          # ecart au milieu de l'arete
        cx, cy = mx + ux * sc, my + uy * sc
        out.append(solide(nom, "mur_ext",
                          (cx, cy, (zb + zh) / 2),
                          ((s1 - s0) / 2, EP_MUR_EXT / 2, (zh - zb) / 2),
                          yaw))

    fen = positions_fenetres(L)
    portes = []
    if avec_porte and L > LARG_PORTE + 1.6:
        c = L / 2
        portes = [(c - LARG_PORTE / 2, c + LARG_PORTE / 2)]
        # une porte remplace la fenetre qui la chevauche
        fen = [f for f in fen if f[1] < portes[0][0] or f[0] > portes[0][1]]

    # 1. allege : plein partout sauf sous les portes
    for a, b in bandes_pleines(L, portes):
        boite("mur%d_allege_%.1f" % (idx, a), a, b, z_bas, z_bas + ALLEGE)
    # 2. bandeau des ouvertures : plein entre fenetres ET portes
    for a, b in bandes_pleines(L, fen + portes):
        boite("mur%d_trumeau_%.1f" % (idx, a), a, b, z_bas + ALLEGE, z_bas + LINTEAU)
    # 3. linteau : plein sur toute la longueur
    boite("mur%d_linteau" % idx, 0.0, L, z_bas + LINTEAU, z_bas + H_ETAGE)

    if ouvertures_out is not None:
        # normale sortante : polygone en sens trigo -> l'exterieur est a droite
        nx, ny = uy, -ux
        for kind, liste, zb in (("fenetre", fen, z_bas + ALLEGE),
                                ("porte", portes, z_bas)):
            for a, b in liste:
                sc = (a + b) / 2 - L / 2
                ouvertures_out.append({
                    "type": kind,
                    "arete": idx,
                    "centre_m": [round(mx + ux * sc, 4),
                                 round(my + uy * sc, 4),
                                 round((zb + z_bas + LINTEAU) / 2, 4)],
                    "normale": [round(nx, 4), round(ny, 4), 0.0],
                    "largeur_m": round(b - a, 3),
                    "bas_m": round(zb, 3),
                    "haut_m": round(z_bas + LINTEAU, 3),
                })
    return out


# ---------------------------------------------------------------- dalles
def intersections_x(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            t = (y - y0) / (y1 - y0)
            xs.append(x0 + t * (x1 - x0))
    return sorted(xs)


def dalle_bandes(poly, z_haut, nom, trou=None):
    """La dalle suit le VRAI polygone : decoupe en bandes, pas de boite englobante.

    trou : (xmin, xmax, ymin, ymax) a evider -- la tremie de l'escalier.
    """
    ys = [p[1] for p in poly]
    y0, y1 = min(ys), max(ys)
    out, k = [], 0
    y = y0
    while y < y1 - 1e-6:
        yc = y + PAS_BANDE / 2
        xs = intersections_x(poly, yc)
        for i in range(0, len(xs) - 1, 2):
            xa, xb = xs[i], xs[i + 1]
            morceaux = [(xa, xb)]
            if trou:
                tx0, tx1, ty0, ty1 = trou
                if not (yc < ty0 or yc > ty1):
                    morceaux = []
                    if xa < tx0:
                        morceaux.append((xa, min(xb, tx0)))
                    if xb > tx1:
                        morceaux.append((max(xa, tx1), xb))
            for (ma, mb) in morceaux:
                if mb - ma < 0.05:
                    continue
                out.append(solide("%s_%d" % (nom, k), "dalle",
                                  ((ma + mb) / 2, yc, z_haut - EP_DALLE / 2),
                                  ((mb - ma) / 2, PAS_BANDE / 2, EP_DALLE / 2)))
                k += 1
        y += PAS_BANDE
    return out


# ---------------------------------------------------------------- cloisons
def intersections_y(poly, x):
    """Les ordonnees ou la verticale x traverse le polygone."""
    ys = []
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (x0 <= x < x1) or (x1 <= x < x0):
            t = (x - x0) / (x1 - x0)
            ys.append(y0 + t * (y1 - y0))
    return sorted(ys)


LARG_PASSAGE = 0.90
AIRE_PIECE   = 28.0        # on arrete de couper en dessous
PROF_MAX     = 3


def _segments_cloison(poly, coupe, axe, borne):
    """Les morceaux de cloison le long d'une coupe, clipes sur le VRAI polygone."""
    inter = intersections_y(poly, coupe) if axe == "x" else intersections_x(poly, coupe)
    lo, hi = borne
    out = []
    for i in range(0, len(inter) - 1, 2):
        a, b = max(inter[i], lo), min(inter[i + 1], hi)
        if b - a > 1.0:
            out.append((a, b))
    return out


def _poser_cloison(sol, idx, coupe, a, b, axe, z_bas, trou):
    """Une cloison de a a b, avec un passage au milieu, evitant la tremie."""
    # on retire la tremie : une cloison ne doit pas barrer l'escalier
    morceaux = [(a, b)]
    if trou:
        tx0, tx1, ty0, ty1 = trou
        bloque = (ty0, ty1) if axe == "x" else (tx0, tx1)
        dans = (tx0 <= coupe <= tx1) if axe == "x" else (ty0 <= coupe <= ty1)
        if dans:
            m = []
            for (u, v) in morceaux:
                if u < bloque[0]:
                    m.append((u, min(v, bloque[0])))
                if v > bloque[1]:
                    m.append((max(u, bloque[1]), v))
            morceaux = m

    for (u, v) in morceaux:
        if v - u < 0.30:
            continue
        # passage au milieu si le morceau est assez large
        if v - u >= LARG_PASSAGE + 1.2:
            c = (u + v) / 2
            pleins = [(u, c - LARG_PASSAGE / 2), (c + LARG_PASSAGE / 2, v)]
            linteau = [(c - LARG_PASSAGE / 2, c + LARG_PASSAGE / 2)]
        else:
            pleins, linteau = [(u, v)], []
        for (p0, p1) in pleins:
            _boite_cloison(sol, idx, coupe, p0, p1, axe, z_bas, z_bas + H_ETAGE)
        for (p0, p1) in linteau:
            _boite_cloison(sol, idx, coupe, p0, p1, axe, z_bas + LINTEAU, z_bas + H_ETAGE)


_compteur = [0]


def _boite_cloison(sol, idx, coupe, p0, p1, axe, zb, zh):
    _compteur[0] += 1
    nom = "cloison%d_%d" % (idx, _compteur[0])
    if axe == "x":       # cloison dans le plan x = coupe, s'etendant en y
        centre = (coupe, (p0 + p1) / 2, (zb + zh) / 2)
        demi = (EP_CLOISON / 2, (p1 - p0) / 2, (zh - zb) / 2)
    else:                # cloison dans le plan y = coupe, s'etendant en x
        centre = ((p0 + p1) / 2, coupe, (zb + zh) / 2)
        demi = ((p1 - p0) / 2, EP_CLOISON / 2, (zh - zb) / 2)
    sol.append(solide(nom, "cloison", centre, demi, 0.0))


def cloisons(poly, z_bas, trou=None):
    """Decoupe recursive de l'emprise en pieces. Deterministe : l'empreinte
    du monde doit etre reproductible."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    sol, idx = [], [0]

    def couper(x0, x1, y0, y1, prof):
        if prof > PROF_MAX or (x1 - x0) * (y1 - y0) < AIRE_PIECE:
            return
        idx[0] += 1
        if (x1 - x0) >= (y1 - y0):
            c = (x0 + x1) / 2
            for a, b in _segments_cloison(poly, c, "x", (y0, y1)):
                _poser_cloison(sol, idx[0], c, a, b, "x", z_bas, trou)
            couper(x0, c, y0, y1, prof + 1)
            couper(c, x1, y0, y1, prof + 1)
        else:
            c = (y0 + y1) / 2
            for a, b in _segments_cloison(poly, c, "y", (x0, x1)):
                _poser_cloison(sol, idx[0], c, a, b, "y", z_bas, trou)
            couper(x0, x1, y0, c, prof + 1)
            couper(x0, x1, c, y1, prof + 1)

    couper(min(xs), max(xs), min(ys), max(ys), 0)
    return sol


# ---------------------------------------------------------------- escalier
def escalier(x0, y0, z0, largeur=1.10, montee=0.18, giron=0.28):
    """Volee droite. Le seul element qu'on dimensionne pour etre FRANCHISSABLE :
    une marche de 18 cm passe sous le pas maximal du moteur."""
    # On ne CHOISIT pas la hauteur de marche : on divise exactement la hauteur
    # d'etage. Sinon la volee depasse la dalle -- 17 x 0,18 = 3,06 pour 3,00.
    n = max(1, int(round(H_ETAGE / montee)))
    montee = H_ETAGE / n
    out = []
    for i in range(n):
        z = z0 + montee * (i + 1)
        y = y0 + giron * (i + 0.5)
        out.append(solide("marche_%02d" % i, "marche",
                          (x0, y, z - montee / 2),
                          (largeur / 2, giron / 2, montee / 2)))
    fiche = {
        "n_marches": n,
        "montee_m": round(montee, 4),
        "giron_m": round(giron, 4),
        "largeur_m": largeur,
        # les deux extremites de la volee : centre de la premiere et de la
        # derniere marche, avec la hauteur de LEUR SURFACE.
        "bas_m":  [round(x0, 4), round(y0 + giron * 0.5, 4), round(z0 + montee, 4)],
        "haut_m": [round(x0, 4), round(y0 + giron * (n - 0.5), 4), round(z0 + montee * n, 4)],
    }
    return out, n * giron, fiche


# ---------------------------------------------------------------- assemblage
def batiment(emprise, hauteur_m, avec_porte_sur=0):
    poly = normaliser(emprise)
    n_niv = max(1, int(hauteur_m // H_ETAGE))

    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    # tremie d'escalier : contre le mur ouest, au milieu en profondeur
    esc_x = min(xs) + 1.20
    esc_y = -0.60
    marches, longueur_volee, fiche_esc = escalier(esc_x, esc_y, 0.0)
    trou = (esc_x - 0.75, esc_x + 0.75, esc_y - 0.20, esc_y + longueur_volee + 0.40)

    solides, ouvertures = [], []
    solides += dalle_bandes(poly, 0.0, "dalle_rdc")            # plancher bas
    for niv in range(n_niv):
        z = niv * H_ETAGE
        for i in range(len(poly)):
            solides += mur_arete(i + 10 * niv, poly[i], poly[(i + 1) % len(poly)],
                                 z, avec_porte=(niv == 0 and i == avec_porte_sur),
                                 ouvertures_out=ouvertures)
        # La cage d'escalier reste libre a TOUS les niveaux, pas seulement la
        # ou la dalle est percee : sinon une cloison de l'etage se pose en
        # travers du palier et l'homme ne peut plus deboucher.
        solides += cloisons(poly, z, trou=trou)
        # plancher haut du niveau : evide a la tremie sauf au dernier
        haut = z + H_ETAGE
        solides += dalle_bandes(poly, haut, "dalle_n%d" % (niv + 1),
                                trou=trou if niv < n_niv - 1 else None)
    if n_niv > 1:
        solides += marches

    return {
        "emprise_m": [[round(x, 3), round(y, 3)] for x, y in poly],
        "hauteur_m": hauteur_m,
        "n_niveaux": n_niv,
        "h_etage_m": H_ETAGE,
        "escalier_xy": [round(esc_x, 3), round(esc_y, 3)],
        "escalier": fiche_esc,
        "tremie": [round(v, 3) for v in trou],
        "allege_m": ALLEGE,
        "linteau_m": LINTEAU,
        "pas_fenetre_m": PAS_FENETRE,
        "ouvertures": ouvertures,
        "solides": solides,
    }


# ---------------------------------------------------------------- entree
if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if src:
        with open(src) as f:
            d = json.load(f)
        emprise, hauteur = d["emprise_m"], d["hauteur_m"]
    else:
        # emprise de repli : un L, pour eprouver la decoupe en bandes
        emprise = [(0, 0), (14, 0), (14, 9), (6, 9), (6, 16), (0, 16)]
        hauteur = 6.5

    b = batiment(emprise, hauteur)
    sortie = sys.argv[2] if len(sys.argv) > 2 else "batiment.json"
    with open(sortie, "w") as f:
        json.dump(b, f, indent=1)

    par_type = {}
    for s in b["solides"]:
        par_type[s["type"]] = par_type.get(s["type"], 0) + 1
    print("KIT niveaux=%d solides=%d" % (b["n_niveaux"], len(b["solides"])))
    for k in sorted(par_type):
        print("KIT   %-10s %4d" % (k, par_type[k]))
    print("KIT ouvertures=%d (dont %d portes)"
          % (len(b["ouvertures"]),
             sum(1 for o in b["ouvertures"] if o["type"] == "porte")))
    print("KIT ecrit -> %s" % sortie)
