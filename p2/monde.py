"""
MONDE -- le chargeur commun, et l'empreinte qui fait foi.

Ce fichier est lu par les deux cotes : le gymnase et Unreal. Il ne depend
que de la bibliotheque standard, pour pouvoir vivre dans n'importe lequel
des deux.

L'empreinte est la seule preuve qu'on parle du meme monde. Un accord entre
deux mondes differents n'est pas un accord -- et un accord entre deux mondes
qu'on n'a pas empreintes n'est qu'une esperance.

Precision : 1 mm. Les transformations d'Unreal sont en float32 ; un arrondi
plus fin ferait diverger les deux empreintes sans qu'aucun monde ne change.
"""
import hashlib
import json

PRECISION = 3          # decimales en metres -> le millimetre


def ligne_solide(nom, centre_m, demi_m, yaw_deg, materiau, epaisseur_m):
    """La forme canonique d'un solide. Les deux cotes DOIVENT produire ceci."""
    f = "%%.%df" % PRECISION
    c = ",".join(f % v for v in centre_m)
    d = ",".join(f % v for v in demi_m)
    # -0.000 et 0.000 sont le meme nombre : on normalise, sinon l'empreinte
    # depend du sens dans lequel on a tourne.
    c = c.replace("-0.000", "0.000")
    d = d.replace("-0.000", "0.000")
    y = (f % (yaw_deg % 360.0)).replace("-0.000", "0.000")
    return "%s|%s|%s|%s|%s|%s" % (nom, c, d, y, materiau, f % epaisseur_m)


def empreinte_depuis_lignes(lignes):
    return hashlib.sha256("\n".join(sorted(lignes)).encode()).hexdigest()


def empreinte_fichier(chemin):
    """L'empreinte telle que le GENERATEUR la decrit."""
    with open(chemin) as fh:
        b = json.load(fh)
    return empreinte_depuis_lignes(lignes_fichier(b)), b


def lignes_fichier(b):
    return [ligne_solide(s["nom"], s["centre_m"], s["demi_m"],
                         s["yaw_deg"], s["materiau"], s["epaisseur_m"])
            for s in b["solides"]]


# ---------------------------------------------------------------- gymnase
def charger_pour_gymnase(chemin):
    """Ce que le gymnase a besoin de savoir du monde.

    Renvoie des boites orientees en METRES -- meme unite, meme convention
    que le fichier. C'est au gymnase de convertir vers ses propres axes,
    pas au monde de se plier a lui.
    """
    with open(chemin) as fh:
        b = json.load(fh)
    boites = []
    for s in b["solides"]:
        boites.append({
            "nom": s["nom"],
            "centre": tuple(s["centre_m"]),
            "demi": tuple(s["demi_m"]),
            "yaw_rad": s["yaw_deg"] * 3.141592653589793 / 180.0,
            "materiau": s["materiau"],
            "epaisseur": s["epaisseur_m"],
            "opaque": True,          # tout est opaque tant qu'on n'a pas de vitrage
        })
    return {
        "boites": boites,
        "ouvertures": b["ouvertures"],
        "escalier": b.get("escalier"),
        "n_niveaux": b["n_niveaux"],
        "empreinte": empreinte_depuis_lignes(lignes_fichier(b)),
    }


if __name__ == "__main__":
    import sys
    chemin = sys.argv[1] if len(sys.argv) > 1 else "batiment.json"
    e, b = empreinte_fichier(chemin)
    m = charger_pour_gymnase(chemin)
    print("MONDE fichier    : %d solides" % len(b["solides"]))
    print("MONDE gymnase    : %d boites, %d ouvertures"
          % (len(m["boites"]), len(m["ouvertures"])))
    print("MONDE EMPREINTE  : %s" % e)
    assert m["empreinte"] == e, "le chargeur gymnase diverge du fichier"
    print("MONDE le chargeur gymnase rend la meme empreinte : OK")


# ---------------------------------------------------------------- sondes
def points_de_sonde(b):
    """Les segments de sonde, en METRES, calcules depuis les ouvertures declarees.

    Cette fonction est LE point commun : les deux cotes doivent sonder
    exactement les memes segments, sinon comparer leurs reponses ne veut
    rien dire. Elle vit donc ici, pas dans l'un des deux bancs.
    """
    par_arete = {}
    for o in b["ouvertures"]:
        if o["type"] == "fenetre" and o["bas_m"] < 1.0:
            par_arete.setdefault(o["arete"], []).append(o)
    arete = next((k for k, v in sorted(par_arete.items()) if len(v) >= 2), None)
    if arete is None:
        raise ValueError("aucune arete avec deux fenetres au rez")

    f0 = sorted(par_arete[arete], key=lambda o: o["centre_m"][0])[0]
    nx, ny, _ = f0["normale"]
    cx, cy, _ = f0["centre_m"]
    tx, ty = -ny, nx

    spans = []
    for o in b["ouvertures"]:
        if o["arete"] != arete or o["bas_m"] >= 1.0:
            continue
        d = (o["centre_m"][0] - cx) * tx + (o["centre_m"][1] - cy) * ty
        spans.append((d - o["largeur_m"] / 2, d + o["largeur_m"] / 2))
    spans.sort()
    trumeau = None
    for i in range(len(spans) - 1):
        a, c = spans[i][1], spans[i + 1][0]
        if c - a >= 1.30:
            trumeau = (a + c) / 2
            break
    if trumeau is None:
        raise ValueError("aucun trumeau plein sur l'arete %d" % arete)

    def pt(vers_dehors, lateral, z):
        return (round(cx + nx * vers_dehors + tx * lateral, PRECISION),
                round(cy + ny * vers_dehors + ty * lateral, PRECISION),
                round(z, PRECISION))

    return {
        "arete": arete,
        "trumeau_m": round(trumeau, PRECISION),
        "segments": {
            # nom                    (depuis, vers)                attendu
            # 1,5 m et non 3 : avec les cloisons, 3 m mettrait la sonde dans
            # la piece VOISINE, et on mesurerait une cloison au lieu du mur.
            "debout_par_la_fenetre": (pt(8, 0, 1.50),  pt(-1.5, 0, 1.50)),
            "accroupi_sous_allege":  (pt(8, 0, 1.50),  pt(-1.5, 0, 0.50)),
            "derriere_le_trumeau":   (pt(8, trumeau, 1.50), pt(-1.5, trumeau, 1.50)),
            "ctrl_pos_ouverture":    (pt(8, 0, 1.50),  pt(0, 0, 1.50)),
            "ctrl_pos_terrain":      (pt(8, -12, 1.50), pt(8, 12, 1.50)),
        },
    }
