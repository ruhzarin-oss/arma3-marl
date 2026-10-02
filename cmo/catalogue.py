#!/usr/bin/env python3
"""Le catalogue d'achat de chaque pays d'un théâtre : ses avions de combat en service en 2026 ( base DB3000 de CMO, lue en
lecture seule ), avec un armement air-air de la base et un prix.

CHOIX À VALIDER ( copier le réel ) :
- prix unitaires 2026 en millions de dollars par FAMILLE ( table PRIX_M ), ordres de grandeur publics. Le matériel russe
  est compté à son prix russe : le budget russe converti au taux de change sous-estime son pouvoir d'achat ( parité ~x2,5 ),
  et payer un Su-35 au prix d'un Typhoon effacerait l'aviation russe ;
- armement : le premier chargement de la base au rôle « supériorité aérienne BVR », sinon « interception BVR », sinon WVR ;
- au plus TROIS familles par pays, les plus chères ( donc les plus modernes ), le biplace écarté quand le monoplace existe ;
- un avion sans chargement air-air n'est pas au catalogue ( v1 : guerre aérienne ).

    .venv312/bin/python cmo/catalogue.py [baltique]
"""
import importlib
import json
import os
import re
import sqlite3
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
BASE = "/mnt/data/hmt/etat/cmo_db/DB3K_519.db3"
SORTIE = "/mnt/data/hmt/etat/cmo_db"
TYPES = ("Multirole (Fighter/Attack)", "Fighter")
ROLES_AIR_AIR = (2003, 2001, 2004, 2002)         # supériorité BVR, interception BVR, supériorité WVR, interception WVR

PRIX_M = [  # ( motif du nom, famille, prix en M$ ) : le premier motif qui correspond l'emporte
    (r"^F-22", "F-22", 150), (r"^F-35", "F-35", 100), (r"^F-15EX", "F-15EX", 90), (r"^F-15E", "F-15E", 55),
    (r"^F-15C", "F-15C", 45), (r"Typhoon|EF2000", "Typhoon", 90), (r"Rafale", "Rafale", 85),
    (r"JAS 39[EF]|Gripen NG", "Gripen E", 85), (r"JAS 39[CD]", "Gripen C", 45), (r"F-16.*(Blk 70|Block 70|V\b)", "F-16 Block 70", 70),
    (r"^F-16", "F-16", 45), (r"F/A-18E|F/A-18F|Super Hornet", "Super Hornet", 67), (r"F/A-18", "F/A-18 Hornet", 35),
    (r"FA-50", "FA-50", 35), (r"Tornado", "Tornado", 30),
    (r"E-3[A-G]? Sentry|Sentry AEW", "E-3", 300), (r"E-7|Wedgetail", "E-7", 500), (r"Saab 340 AEW|S 100", "Saab 340 AEW", 30),
    (r"KC-135", "KC-135", 40), (r"KC-46", "KC-46", 165), (r"A.330.*MRTT", "A330 MRTT", 300), (r"EA-18G", "EA-18G", 70),
    (r"A-50", "A-50", 330), (r"Il-78", "Il-78", 50), (r"Il-22", "Il-22", 60),
    (r"B-52", "B-52H", 85), (r"B-1B", "B-1B", 300), (r"Tu-95", "Tu-95MS", 90), (r"Tu-160", "Tu-160M", 250), (r"Tu-22M", "Tu-22M3", 60),
    (r"^Su-57", "Su-57", 45), (r"^Su-35", "Su-35", 38), (r"^Su-34", "Su-34", 36), (r"^Su-30", "Su-30", 32),
    (r"^Su-27", "Su-27", 20), (r"^MiG-31", "MiG-31", 30), (r"^MiG-35", "MiG-35", 30), (r"^MiG-29", "MiG-29", 20),
]
BIPLACE = re.compile(r"Two-Seater|\bT\.\d|F-16[BD]|F-16DJ|F/A-18D|JAS 39[DF]|Su-57D|MiG-29UB|F-15D", re.I)


def famille(nom):
    for motif, fam, prix in PRIX_M:
        if re.search(motif, nom):
            return fam, prix
    return None, None


ROLES_FRAPPE = (3101, 3001, 3102, 3002)          # frappe terrestre, frappe terre/mer, à distance terrestre, à distance
GUIDEE = re.compile(r"GBU|JDAM|LGB|Paveway|JSOW|JASSM|Storm Shadow|Taurus|PBK|KAB|Kh-|BetAB", re.I)


def _puissance(c, loadout):
    """La puissance d'un chargement contre une installation : somme, sur ses armes air-sol, du nombre x points de dégâts de
    l'ogive ( DataWarhead ), x 1,5 pour une ogive perforante ( type 2009 : abris durcis, dépôts enterrés ). Sonde du
    02/10 : deux GBU-12 ( 130 points chacune ) n'ont fait que 2,4 % de dégâts à un dépôt enterré de 3 200 points."""
    total = 0.0
    for (rid,) in c.execute("select ComponentID from DataLoadoutWeapons where ID = ?", (loadout,)):
        w, n = c.execute("select ComponentID, DefaultLoad from DataWeaponRecord where ID = ?", (rid,)).fetchone()
        t = c.execute("select Type, coalesce(LandRangeMax, 0) from DataWeapon where ID = ?", (w,)).fetchone()
        if not t or t[0] in (3001, 3002, 3003, 3004, 2004) or t[1] <= 0:
            continue                                     # nacelles, réservoirs, canon, armes sans portée contre le sol
        for dp, typ in c.execute("""select h.DamagePoints, h.Type from DataWeaponWarheads ww join DataWarhead h
                on h.ID = ww.ComponentID where ww.ID = ?""", (w,)):
            total += n * (dp or 0) * (1.5 if typ == 2009 else 1.0)
    return total


def chargement_frappe(dbid, base=BASE):
    """Le chargement d'attaque au sol d'un avion ( DB3000 ) : parmi ses chargements de frappe GUIDÉS ( comme les armées en
    2026, bombes anti-pistes BetAB comprises ), le plus PUISSANT contre une installation ( _puissance ) ; à défaut de
    guidé, le plus puissant tout court. ( id, nom, rôle ) ou None."""
    c = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
    guides, autres = [], []
    for role in ROLES_FRAPPE:
        for i, nom in c.execute("""select l.ID, l.Name from DataAircraftLoadouts al join DataLoadout l on l.ID = al.ComponentID
                where al.ID = ? and l.LoadoutRole = ? and coalesce(l.Hypothetical,0)=0 and l.Name not like '%Short-Range%'
                order by l.ID""", (dbid, role)):
            (guides if GUIDEE.search(nom) else autres).append((_puissance(c, i), -i, i, nom, role))
    choix = max(guides) if guides else (max(autres) if autres else None)
    return (choix[2], choix[3], choix[4]) if choix else None


def catalogue(pays, base=BASE, annee=2026):
    c = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
    rows = c.execute(f"""select a.ID, a.Name, a.YearCommissioned from DataAircraft a
        join EnumOperatorCountry pc on pc.ID = a.OperatorCountry join EnumAircraftType t on t.ID = a.Type
        where pc.Description = ? and coalesce(a.Hypothetical,0)=0 and coalesce(a.Deprecated,0)=0
          and a.YearCommissioned <= ? and (a.YearDecommissioned = 0 or a.YearDecommissioned >= ?)
          and t.Description in ({",".join("?" * len(TYPES))}) order by a.YearCommissioned desc, a.ID desc""",
                     (pays, annee, annee, *TYPES)).fetchall()
    par_famille = {}
    for i, nom, an in rows:
        fam, prix = famille(nom)
        if fam is None or fam in par_famille and not BIPLACE.search(par_famille[fam]["nom"]):
            continue                                     # famille sans prix, ou déjà tenue par un monoplace plus récent
        if fam in par_famille and BIPLACE.search(nom):
            continue
        charge = None
        for role in ROLES_AIR_AIR:
            charge = c.execute("""select l.ID from DataAircraftLoadouts al join DataLoadout l on l.ID = al.ComponentID
                where al.ID = ? and l.LoadoutRole = ? and coalesce(l.Hypothetical,0)=0 order by l.ID limit 1""", (i, role)).fetchone()
            if charge:
                charge = (charge[0], role)
                break
        if charge:
            par_famille[fam] = {"dbid": i, "nom": nom, "famille": fam, "prix_m": prix, "annee": an,
                                "loadout": charge[0], "role": charge[1]}
    return sorted(par_famille.values(), key=lambda x: -x["prix_m"])[:3]


if __name__ == "__main__":
    nom = sys.argv[1] if len(sys.argv) > 1 else "baltique"
    T = importlib.import_module(f"theatres.{nom}")
    import budgets as B
    out = {}
    for pays, (camp, part, _) in T.PAYS.items():
        cat = catalogue(pays)
        mpm = B.millions_par_minute(pays, part)
        out[pays] = {"camp": camp, "part": part, "millions_par_minute": round(mpm, 2), "catalogue": cat}
        moins_cher = min((x["prix_m"] for x in cat), default=None)
        print(f"{pays:26s} {camp:13s} {mpm:6.2f} M$/min  "
              + (f"un avion toutes les {moins_cher / mpm:5.1f} min  " if cat and mpm else "aucun achat possible          ")
              + ", ".join(f"{x['famille']} ({x['prix_m']})" for x in cat))
    with open(os.path.join(SORTIE, f"catalogue_{nom}.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
