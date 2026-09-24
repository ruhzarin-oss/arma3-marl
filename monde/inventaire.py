"""L INVENTAIRE DES CARTES ( archipel, phase A, 24/09 ) : ce que chaque ile contient vraiment.

Les lieux nommes ( monde/geographie.py ) ne disent pas ou sont les usines, les centrales, les bases militaires. Ici
chaque serveur Arma parcourt SON terrain case par case et rend tous ses objets classes par le jeu ( batiments,
stations-service, hopitaux, quais, lignes electriques, eoliennes, bunkers... ), avec leur modele 3D et leur position,
la terre et la nature des sols, les arbres et les routes. Le cerveau ecrit donnees/<ile>_inventaire.json.

   python -m monde.inventaire --port 2350 --pas 2000 --attente 3600"""
import argparse, json, os, time
from . import pont as PT

ICI = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=2350)
    p.add_argument("--pas", type=int, default=2000, help="cote d une case, en metres")
    p.add_argument("--attente", type=float, default=3600.0)
    p.add_argument("--serveurs", type=int, default=6, help="combien d iles attendre avant de demander")
    a = p.parse_args()
    pont = PT.Pont(a.port)
    print("en attente des serveurs", flush=True)
    t0 = time.time()
    while time.time() - t0 < 900:
        iles = sorted(i for i in pont.iles() if i != "inconnue")
        if len(iles) >= a.serveurs: break
        time.sleep(5)
    time.sleep(40)                       # chaque serveur se represente toutes les 30 s : laisser les derniers se nommer
    iles = sorted(i for i in pont.iles() if i != "inconnue")
    print(f"iles connectees ( {len(iles)} ) : {iles}", flush=True)
    for ile in iles: pont.envoyer([["inventaire", a.pas]], ile)

    inv = {ile: {"version": 2, "carte": None, "lieux": [], "objets": [], "cases": [], "fin": None} for ile in iles}
    t0, dernier = time.time(), time.time()
    while time.time() - t0 < a.attente:
        for _, m in pont.messages_iles(1.0):
            if not m or not isinstance(m[0], str) or not m[0].startswith("inv_"): continue
            ile = m[1]
            d = inv.setdefault(ile, {"version": 2, "carte": None, "lieux": [], "objets": [], "cases": [], "fin": None})
            if m[0] == "inv_carte":
                d["carte"] = {"monde": ile, "taille_m": m[2], "pas_m": m[3], "aeroports": m[4], "centre": m[5]}
            elif m[0] == "inv_lieux":
                d["lieux"] += [{"id": l[0], "type": l[1], "nom": l[2], "x": l[3], "y": l[4], "rayon": [l[5], l[6]]} for l in m[2]]
            elif m[0] == "inv_objets":
                d["objets"] += [{"type": o[0], "modele": o[1], "x": o[2], "y": o[3], "z": o[4], "places": o[5],
                                 "sol_m2": o[6], "dir": o[7]} for o in m[2]]
            elif m[0] == "inv_case":
                # 400 sondages par case ; Arma rend les compteurs en paires ( sol, sondages ), ( categorie de route, m )
                veg = dict(zip(("arbres", "petits_arbres", "buissons", "rocher", "rochers", "foret"), m[6]))
                d["cases"].append({"x": m[2], "y": m[3], "terre_sondages": m[4], "sondages": 400,
                                   "sols": {str(k): v for k, v in m[5]}, "vegetation": veg,
                                   "routes_m": {str(k): v for k, v in m[7]}, "ponts": m[8],
                                   "altitude": {"min": m[9][0], "moy": m[9][1], "max": m[9][2]}})
            elif m[0] == "inv_fin":
                d["fin"] = {"objets_annonces": m[2], "cases": m[3], "secondes": m[4], "lieux": m[5]}
                print(f"{ile} : fini en {m[4]} s | {len(d['objets'])} objets recus sur {m[2]} annonces | "
                      f"{len(d['cases'])} cases de terre sur {m[3]}", flush=True)
        if time.time() - dernier > 60:
            dernier = time.time()
            print("  en cours : " + " | ".join(f"{i} {len(d['objets'])} objets, {len(d['cases'])} cases"
                                               + (" FINI" if d["fin"] else "") for i, d in sorted(inv.items())), flush=True)
        if inv and all(d["fin"] for d in inv.values()): break

    for ile, d in sorted(inv.items()):
        chemin = os.path.join(ICI, "donnees", f"{ile.lower()}_inventaire.json")
        with open(chemin, "w") as f: json.dump(d, f)
        types = {}
        for o in d["objets"]: types[o["type"]] = types.get(o["type"], 0) + 1
        print(f"{ile} : {len(d['objets'])} objets ecrits dans {os.path.basename(chemin)} | "
              + ", ".join(f"{k} {v}" for k, v in sorted(types.items(), key=lambda x: -x[1])), flush=True)
    manquantes = [i for i, d in inv.items() if not d["fin"]]
    print("INVENTAIRE " + ("COMPLET" if not manquantes else f"INCOMPLET : {manquantes}"), flush=True)
    return 0 if not manquantes else 1


if __name__ == "__main__":
    raise SystemExit(main())
