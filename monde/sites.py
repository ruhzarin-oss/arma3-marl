"""LES SITES DE CHAQUE ILE ( archipel, phase A ) : des objets de la carte aux lieux ou l on vit, travaille, se defend.

A partir de l inventaire ( donnees/<ile>_inventaire.json, version 2 ) :
- les objets d une meme fonction, voisins de moins de RAYON_M metres de proche en proche, forment un SITE ( une base,
  une zone industrielle, un port, un depot de carburant ) ; un site garde son centre, ses objets, sa surface batie ;
- les batiments HABITABLES ( au moins une place interieure ) sont rattaches au lieu nomme le plus proche : la capacite
  de logement de chaque ville, donc une base MESUREE pour la population de chaque pays ;
- les aeroports viennent de la configuration de la carte.
Ce n est qu une proposition : le classement par fonction est une lecture des noms de modeles 3D, a relire.

   python -m monde.sites"""
import json, os, sys
from collections import Counter, defaultdict
import numpy as np
from .lire_inventaire import classer, ILES

ICI = os.path.dirname(os.path.abspath(__file__))
RAYON_M = 250.0
# une fonction ne fait un site qu a partir de ce nombre d objets ( un bunker isole n est pas une base )
MINIMUM = {"eau": 3, "militaire": 4, "industrie": 3, "carburant": 2, "energie": 2, "port": 2, "aeroport": 1, "sante": 1,
           "agriculture": 3, "hangar": 1, "commerce": 3, "administration": 1, "communication": 1}
FONCTIONS_SITES = tuple(MINIMUM)


def grouper(xy, rayon):
    """Composantes connexes a moins de `rayon` ( union-find sur une grille de cote `rayon` ) : l etiquette de chaque point."""
    n = len(xy)
    parent = np.arange(n)
    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    cle = np.floor(xy / rayon).astype(np.int64)
    grille = defaultdict(list)
    for i, (a, b) in enumerate(cle): grille[(a, b)].append(i)
    r2 = rayon * rayon
    for (a, b), ids in grille.items():
        voisins = [j for da in (-1, 0, 1) for db in (-1, 0, 1) for j in grille.get((a + da, b + db), ())]
        vx = xy[voisins]
        for i in ids:
            proches = np.nonzero(((vx - xy[i]) ** 2).sum(1) <= r2)[0]
            ri = racine(i)
            for k in proches:
                rj = racine(voisins[k])
                if rj != ri: parent[rj] = ri
    return np.array([racine(i) for i in range(n)])


def sites_de(inv):
    objets = inv["objets"]
    par_f = defaultdict(list)
    for o in objets:
        f = classer(o)
        if f in FONCTIONS_SITES and not (f == "energie" and o["type"] == "POWER LINES"):   # un pylone n est pas une centrale
            par_f[f].append(o)
    sites = []
    for f, os_ in par_f.items():
        xy = np.array([[o["x"], o["y"]] for o in os_], float)
        etiq = grouper(xy, RAYON_M)
        for e in np.unique(etiq):
            m = [os_[i] for i in np.nonzero(etiq == e)[0]]
            if len(m) < MINIMUM[f]: continue
            sites.append({"fonction": f, "x": round(float(np.mean([o["x"] for o in m]))), "y": round(float(np.mean([o["y"] for o in m]))),
                          "objets": len(m), "surface_m2": int(sum(o.get("sol_m2", 0) for o in m)),
                          "places": int(sum(o.get("places", 0) for o in m)),
                          "modeles": Counter(os.path.basename(str(o["modele"]).replace("\\", "/")).lower() for o in m).most_common(6)})
    for a in (inv.get("carte") or {}).get("aeroports") or []:
        if a and len(a) >= 2: sites.append({"fonction": "piste", "x": round(a[0]), "y": round(a[1]), "objets": 0, "surface_m2": 0,
                                             "places": 0, "modeles": []})
    return sorted(sites, key=lambda s: (s["fonction"], -s["objets"]))


def logements(inv):
    """Chaque batiment habitable ( places interieures > 0, fonction logement ) rattache au lieu habite le plus proche."""
    lieux = [l for l in inv.get("lieux", []) if l["type"] in ("NameCityCapital", "NameCity", "NameVillage", "NameLocal")]
    if not lieux: return {}
    lxy = np.array([[l["x"], l["y"]] for l in lieux], float)
    cap = defaultdict(lambda: {"batiments": 0, "places": 0, "surface_m2": 0})
    for o in inv["objets"]:
        if o.get("places", 0) <= 0 or classer(o) not in ("logement", "inclasse"): continue
        k = int(np.argmin(((lxy - [o["x"], o["y"]]) ** 2).sum(1)))
        c = cap[lieux[k]["id"]]; c["batiments"] += 1; c["places"] += o["places"]; c["surface_m2"] += o.get("sol_m2", 0)
    return {k: dict(v, type=next(l["type"] for l in lieux if l["id"] == k)) for k, v in sorted(cap.items(), key=lambda x: -x[1]["places"])}


def main():
    tout = {}
    for ile in ILES:
        chemin = os.path.join(ICI, "donnees", f"{ile.lower()}_inventaire.json")
        if not os.path.exists(chemin): continue
        inv = json.load(open(chemin))
        if inv.get("version") != 2: print(f"{ile} : inventaire version 1, a recollecter"); continue
        s, lg = sites_de(inv), logements(inv)
        tout[ile] = {"sites": s, "logements": lg}
        json.dump(tout[ile], open(os.path.join(ICI, "donnees", f"{ile.lower()}_sites.json"), "w"), indent=1)
    fonctions = ("militaire", "industrie", "carburant", "eau", "energie", "port", "piste", "aeroport", "hangar", "sante",
                 "agriculture", "commerce", "administration", "communication")
    print("ile      places_logement  batiments_hab | " + " ".join(f"{f[:6]:>6s}" for f in fonctions))
    for ile, d in tout.items():
        c = Counter(s["fonction"] for s in d["sites"])
        places = sum(v["places"] for v in d["logements"].values()); bat = sum(v["batiments"] for v in d["logements"].values())
        print(f"{ile:8s} {places:15d} {bat:14d} | " + " ".join(f"{c.get(f, 0):6d}" for f in fonctions))
    for ile, d in tout.items():
        print(f"\n{ile} : plus grands sites")
        for f in ("militaire", "industrie", "carburant", "energie", "port"):
            for s in [x for x in d["sites"] if x["fonction"] == f][:3]:
                print(f"   {f:10s} ({s['x']:6d},{s['y']:6d}) {s['objets']:4d} objets {s['surface_m2']:7d} m2 | {s['modeles'][:3]}")
        print("   villes les plus logeables : " + ", ".join(f"{k} {v['places']}" for k, v in list(d["logements"].items())[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
