#!/usr/bin/env python3
"""L'inventaire du matériel de chaque pays, lu dans la base de CMO ( DB3000, fichier SQLite ) sans passer par le jeu.
Une COPIE de la base est lue en lecture seule ( 29/09 : sonder la base dans le jeu l'avait ralenti à x0,13 ).

⚠️ La base dit QUELS TYPES chaque pays emploie ( « F-16C Block 52, Grèce, 2003- » ), pas COMBIEN il en a : les
effectifs réels ( un ordre de bataille ) n'y sont pas.

« En service en 2026 » : mis en service au plus tard en 2026, pas retiré avant 2026 ( 0 = toujours en service ). Les fiches
hypothétiques ( Hypothetical ) et retirées de la base ( Deprecated ) sont écartées.

    .venv312/bin/python cmo/inventaire.py [--base /mnt/data/hmt/etat/cmo_db/DB3K_519.db3] [--annee 2026]
Sorties dans /mnt/data/hmt/etat/cmo_db/ : inventaire_<annee>.json, pays_<annee>.csv, plateformes_<annee>.csv.
"""
import csv
import glob
import json
import os
import sqlite3
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import blocs as B                                         # noqa: E402

DOSSIER = "/mnt/data/hmt/etat/cmo_db"
GENRES = [  # ( genre affiché, table, table des types, table des catégories )
    ("avion", "DataAircraft", "EnumAircraftType", "EnumAircraftCategory"),
    ("navire", "DataShip", "EnumShipType", "EnumShipCategory"),
    ("sous-marin", "DataSubmarine", "EnumSubmarineType", "EnumSubmarineCategory"),
    ("unité terrestre", "DataGroundUnit", None, "EnumGroundUnitCategory"),
    ("installation", "DataFacility", "EnumFacilityType", "EnumFacilityCategory"),
    ("satellite", "DataSatellite", "EnumSatelliteType", "EnumSatelliteCategory"),
]


def enum(c, table):
    return {i: d for i, d in c.execute(f"select ID, Description from {table}")} if table else {}


def inventaire(base, annee):
    c = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
    pays, services = enum(c, "EnumOperatorCountry"), enum(c, "EnumOperatorService")
    plates = []
    for genre, table, t_type, t_cat in GENRES:
        types, cats = enum(c, t_type), enum(c, t_cat)
        col_type = ", Type" if t_type else ", NULL"
        for i, nom, p, s, cat, typ, debut, fin in c.execute(
                f"select ID, Name, OperatorCountry, OperatorService, Category{col_type}, YearCommissioned, YearDecommissioned "
                f"from {table} where coalesce(Hypothetical, 0) = 0 and coalesce(Deprecated, 0) = 0"):
            debut, fin = int(debut or 0), int(fin or 0)
            if not (debut <= annee and (fin == 0 or fin >= annee)):
                continue
            plates.append({"dbid": i, "genre": genre, "nom": nom, "pays": pays.get(p, f"?{p}"),
                           "service": services.get(s, ""), "categorie": cats.get(cat, ""), "type": types.get(typ, ""),
                           "debut": debut, "fin": fin})
    par_pays = {}
    for p in sorted(set(pays.values())):
        b, cert, raison = B.bloc(p)
        par_pays[p] = {"pays": p, "bloc": b, "camp": B.CAMP.get(b, ""), "certitude": cert, "raison": raison,
                       **{g: 0 for g, *_ in GENRES}, "total": 0}
    for x in plates:
        r = par_pays.setdefault(x["pays"], {"pays": x["pays"], "bloc": B.NEUTRE, "camp": "", "certitude": "?", "raison": "",
                                            **{g: 0 for g, *_ in GENRES}, "total": 0})
        r[x["genre"]] += 1
        r["total"] += 1
    return {"annee": annee, "base": os.path.basename(base), "pays": list(par_pays.values()), "plateformes": plates}


def ecrire(inv, dossier=DOSSIER):
    a = inv["annee"]
    with open(os.path.join(dossier, f"inventaire_{a}.json"), "w") as f:
        json.dump(inv, f, ensure_ascii=False)
    with open(os.path.join(dossier, f"pays_{a}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(inv["pays"][0]))
        w.writeheader()
        w.writerows(inv["pays"])
    with open(os.path.join(dossier, f"plateformes_{a}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(inv["plateformes"][0]) + ["bloc"])
        w.writeheader()
        for x in inv["plateformes"]:
            w.writerow({**x, "bloc": B.bloc(x["pays"])[0]})


if __name__ == "__main__":
    annee = int(sys.argv[sys.argv.index("--annee") + 1]) if "--annee" in sys.argv else 2026
    base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else sorted(glob.glob(f"{DOSSIER}/DB3K_*.db3"))[-1]
    inv = inventaire(base, annee)
    ecrire(inv)
    par_bloc = {}
    for r in inv["pays"]:
        s = par_bloc.setdefault(r["bloc"], {"pays": 0, "pays_avec_materiel": 0, "types": 0})
        s["pays"] += 1
        s["pays_avec_materiel"] += r["total"] > 0
        s["types"] += r["total"]
    print(f"{inv['base']}, en service en {annee} : {len(inv['plateformes'])} types de matériel, {len(inv['pays'])} pays")
    print(json.dumps(par_bloc, ensure_ascii=False, indent=1))
