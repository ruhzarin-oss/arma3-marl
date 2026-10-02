"""LES OBJECTIFS REELS d une ile ( Arma a fond, etape 1a, HMT-192 ) : chaque site de la carte du pays ( centrale,
fonderie, base, port, depot de carburant, aeroport ) est un objectif fait de VRAIS objets du terrain d Arma ( l inventaire
de l ile, monde/donnees/<ile>_inventaire.json ), et de ce qui en depend dans le moteur. Lecture seule.

Les composants d un objectif ( base, fonderie, centrale, port, depot ) : EXACTEMENT la grappe de monde/sites.py qui a fait
naitre le site ( meme fonction, meme algorithme : grouper a 250 m, memes minimums ), retrouvee par son centre, qui est la
position du lieu dans la carte du pays. ( Le 02/10, la premiere porte a ete REFUSEE : le rectangle +/- 150 m n etait que
le rayon par defaut de pays_carte, la grappe le deborde. ) Un aeroport ( un point de la configuration de la carte ) a pour
composants les objets de fonction aeroport ou hangar a moins de RAYON_AEROPORT_M ( CHOIX ), qui ne sont a aucun autre
objectif ; sans aucun, c est une piste sans corps destructible ( Arma ne detruit pas une piste ). Le poids d un composant
est sa surface au sol ( sol_m2 ), au moins 1. La destruction ( 1b ) se lira sur ces objets.

   python -m guerre.objectifs --ile malden"""
import argparse
import json
import math
import os
import re
from collections import Counter, defaultdict

import numpy as np

from monde import lire_inventaire as LI, sites as SI

ICI = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(os.path.dirname(ICI), "monde", "donnees")
CARTES = ("malden", "stratis", "tanoa", "enoch", "sara")
FONCTION = {"centrale": "energie", "fonderie": "industrie", "base": "militaire", "port": "port", "depot": "carburant",
            "aeroport": "aeroport"}
TYPES = tuple(FONCTION)
RAYON_AEROPORT_M = 1500.0        # CHOIX : une piste d aeroport de ces iles fait 1 a 2 km ; la carte n en donne qu un point
FONCTIONS_AEROPORT = ("aeroport", "hangar")


def charger(ile):
    ile = ile.lower()
    pays = json.load(open(os.path.join(DONNEES, "pays", f"{ile}.json")))
    inv = json.load(open(os.path.join(DONNEES, f"{ile}_inventaire.json")))
    return pays, inv


def sites(pays):
    """Les sites-objectifs de la carte du pays, dans l ordre de la carte, puis les aeroports."""
    out = [{"id": l["id"], "type": l["type"], "pos": tuple(l["pos"]), "rayon": tuple(l.get("rayon") or (150, 150)),
            "source": l.get("source", "")} for l in pays["lieux"] if l["type"] in TYPES]
    for k, a in enumerate(pays.get("aeroports") or []):
        out.append({"id": f"aeroport{k + 1:02d}", "type": "aeroport", "pos": (a["x"], a["y"]),
                    "rayon": (RAYON_AEROPORT_M, RAYON_AEROPORT_M), "source": "aeroport de la configuration de la carte"})
    return out


def grappes(inv):
    """Les grappes de monde/sites.sites_de ( meme filtre, meme algorithme, memes minimums ) avec leurs objets :
    [ ( fonction, cx, cy, [ indices dans l inventaire ] ) ]."""
    objets = inv["objets"]; par_f = defaultdict(list)
    for i, o in enumerate(objets):
        f = LI.classer(o)
        if f in SI.FONCTIONS_SITES and not (f == "energie" and o["type"] == "POWER LINES"): par_f[f].append(i)
    out = []
    for f, idx in par_f.items():
        xy = np.array([[objets[i]["x"], objets[i]["y"]] for i in idx], float)
        etiq = SI.grouper(xy, SI.RAYON_M)
        for e in np.unique(etiq):
            m = [idx[k] for k in np.nonzero(etiq == e)[0]]
            if len(m) < SI.MINIMUM[f]: continue
            out.append((f, round(float(np.mean([objets[i]["x"] for i in m]))), round(float(np.mean([objets[i]["y"] for i in m]))), m))
    return out


def _composant(i, o):
    sol = float(o.get("sol_m2") or 0.0)
    return {"i": i, "modele": o["modele"], "x": o["x"], "y": o["y"], "z": o.get("z"), "dir": o.get("dir"), "sol_m2": sol,
            "poids": max(1.0, sol)}


def objectifs_carte(ile):
    """[ objectif ] : id, type, fonction, pos, rayon, composants [ { i, modele, x, y, z, dir, sol_m2, poids } ], poids
    total, modeles comptes, et ce que la carte du pays a ecrit ( objets, surface ) pour le controle."""
    pays, inv = charger(ile)
    objets = inv["objets"]
    ss = sites(pays)
    par_lieu = {l["id"]: l for l in pays["lieux"]}
    gs = grappes(inv)
    pris = set(); out = []
    for s in ss:
        o = dict(s, fonction=FONCTION[s["type"]], composants=[])
        if s["type"] != "aeroport":
            g = [x for x in gs if x[0] == o["fonction"] and (x[1], x[2]) == tuple(s["pos"])]
            if g:
                o["composants"] = [_composant(i, objets[i]) for i in g[0][3]]
                pris.update(g[0][3])
            l = par_lieu[s["id"]]
            o["carte"] = {"objets": l.get("objets"), "surface_m2": l.get("surface_m2")}
        out.append(o)
    for o in out:
        if o["type"] != "aeroport": continue
        x0, y0 = o["pos"]
        for i, ob in enumerate(objets):
            if i in pris or LI.classer(ob) not in FONCTIONS_AEROPORT: continue
            if math.dist((ob["x"], ob["y"]), (x0, y0)) <= RAYON_AEROPORT_M:
                o["composants"].append(_composant(i, ob)); pris.add(i)
    for o in out:
        o["poids_total"] = sum(c["poids"] for c in o["composants"])
        o["modeles"] = dict(Counter(os.path.basename(str(c["modele"]).replace("\\", "/")).lower()
                                    for c in o["composants"]).most_common())
        o["modeles_source"] = re.findall(r"[a-z0-9_]+\.p3d", o["source"].lower())
    return out


def dependances(w, o):
    """Ce qui depend de l objectif dans le monde `w` de son ile : { genre : description } ; vide = sans dependance."""
    p = w.pays; lid = o["id"]; dep = {}
    if o["type"] == "centrale":
        if p.a("energie"):
            us = [u.id for u in p.domaine("energie").unites if u.lieu == lid]
            if us: dep["groupes_energie"] = us
        if lid in w.entreprises: dep["entreprise"] = w.entreprises[lid].id
    elif o["type"] == "fonderie":
        e = w.entreprises.get(lid)
        if e is not None: dep["entreprise"] = e.id; dep["domaine"] = p.repris.get(e.id)
    elif o["type"] == "base":
        d = p.domaines.get("armee")
        if d is not None and any(a.lieu == lid for a in d.armureries): dep["armurerie"] = lid
        if lid in getattr(w, "garnisons", {}): dep["garnison_carburant"] = round(float(w.garnisons[lid]["carburant"]), 1)
    elif o["type"] == "depot":
        if getattr(w, "depot_armee", None) is not None and w.depot_armee.id == lid:
            dep["depot_armee_carburant"] = round(float(w.publics["armee"]["carburant"]), 1)
    elif o["type"] == "port":
        try:
            port = w.carte.port(w.ile)
        except (KeyError, AttributeError, TypeError):
            port = None
        if port is not None and port.id == lid: dep["port"] = lid
    return dep


def valeur(w, o, etat=None):
    """La valeur de l objectif dans le moteur ( information ) : emplois du lieu, groupes d energie, materiel d une base
    ( etat des lieux ), carburant d un depot."""
    t = w.table; n = t.n
    v = {}
    if o["id"] in w.carte.lieux:
        ln = w.carte.lieux[o["id"]].n
        v["emplois"] = int(((t.travail[:n] == ln) & (t.vivant[:n] == 1)).sum())
    if o["type"] == "base" and etat is not None:
        b = etat["bases"].get(o["id"])
        if b: v["materiel_dr"] = b["valeur_dr"]; v["militaires"] = b["effectifs"]
    return v


def registre(ile, w=None):
    """Les objectifs de l ile, avec leurs dependances et leur valeur si un monde est donne."""
    objs = objectifs_carte(ile)
    if w is not None:
        etat = None
        try:
            from guerre.arsenal import etat_des_lieux as EL
            etat = EL.etat_des_lieux(w)
        except Exception:
            etat = None
        for o in objs:
            o["dependances"] = dependances(w, o)
            o["valeur"] = valeur(w, o, etat)
    return objs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ile", default="malden")
    ap.add_argument("--monde", action="store_true", help="creer le monde de l ile ( echelle 20 ) pour les dependances")
    a = ap.parse_args()
    w = None
    if a.monde:
        from monde import archipel as AR
        w = AR.creer_ile(a.ile.capitalize(), 7, 20)
    for o in registre(a.ile, w):
        print(f"{o['id']:12s} {o['type']:9s} {len(o['composants']):4d} composants, poids {o['poids_total']:9.0f} m2 ; "
              f"{list(o['modeles'].items())[:4]} {o.get('dependances', '')} {o.get('valeur', '')}")


if __name__ == "__main__":
    main()
