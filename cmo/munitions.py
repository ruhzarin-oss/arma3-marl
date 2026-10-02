#!/usr/bin/env python3
"""Les munitions d'un chargement ( base DB3000 de CMO, lecture seule ) et leur prix. Les dépôts de munitions de CMO
( aérodromes génériques, Ammo Bunker, Ammo Revetment : magasin 1185, capacité 10 000 ) sont VIDES dans la base : un pays
qui ne les remplit pas ne réarme pas ses avions ( guerre du 29/09, figée au tour 167 ). Chaque munition est donc achetée
sur le budget du pays et livrée à sa base, comme dans le réel.

CHOIX À VALIDER ( copier le réel ) : prix unitaires 2026 en millions de dollars, ordres de grandeur publics saisis de
mémoire ( table PRIX_ARME_M, air-air et air-sol ; un missile russe à son prix russe estimé ) ; le matériel russe à son prix russe, comme les avions ( catalogue.py ) ; les nacelles
( brouillage, leurres, IRST ) ne se consomment pas : prix 0, mais stockées pour que le chargement soit complet.

    .venv312/bin/python cmo/munitions.py [loadout ...]
"""
import re
import sqlite3
import sys

BASE = "/mnt/data/hmt/etat/cmo_db/DB3K_519.db3"

PRIX_ARME_M = [  # ( motif du nom de l'arme dans la base, prix en M$ ) : le premier motif qui correspond l'emporte
    (r"AIM-120D", 1.2), (r"AIM-120C-7", 1.1), (r"AIM-120C", 1.0), (r"AIM-120[AB]", 0.9),
    (r"AIM-9X", 0.45), (r"AIM-9[LMP]", 0.1), (r"Meteor", 2.2), (r"IRIS-T", 0.45), (r"ASRAAM|AIM-132", 0.4),
    (r"Sky Flash", 0.3),
    (r"R-77M\b", 1.0), (r"R-77-1|RVV-SD", 0.6), (r"R-77\b|RVV-AE", 0.5), (r"R-27", 0.3), (r"R-74", 0.3), (r"R-73", 0.2),
    (r"R-37", 1.5), (r"PL-15", 1.0), (r"PL-10", 0.3),
    (r"Drop Tank", 0.03),
    # air-sol ( 02/10 ) : kits de guidage et corps de bombe, missiles de croisière et antiradar
    (r"JASSM", 1.5), (r"Storm Shadow|SCALP", 1.0), (r"Taurus", 1.0), (r"Tomahawk", 2.0), (r"JSOW", 0.7),
    (r"GBU-31|GBU-32|GBU-38|JDAM", 0.035), (r"GBU-1[026]|Paveway II|LGB", 0.03), (r"Paveway IV", 0.07),
    (r"CPU-123", 0.05), (r"AGM-88|HARM|AARGM", 0.8), (r"ALARM", 0.6),
    (r"Iskander|9M723", 3.0), (r"Kalibr|3M14", 1.0), (r"Kh-59", 1.0), (r"Kh-38", 0.6), (r"Kh-31", 0.6),
    (r"Kh-58", 0.5), (r"Kh-29", 0.15), (r"PBK-500", 0.1), (r"KAB-", 0.05), (r"BetAB", 0.02),
    (r"Mk ?84", 0.015), (r"Mk ?83", 0.01), (r"Mk ?82", 0.005), (r"CBU-", 0.015), (r"OFAB|FAB-", 0.003),
    (r"Rocket|HYDRA|S-8|S-13|M/70", 0.003),
    (r"Pod|IRST|EOTS", 0.0),
]


def prix(nom):
    """Prix unitaire en M$, ou None si aucune ligne de la table ne connaît cette arme."""
    for motif, p in PRIX_ARME_M:
        if re.search(motif, nom):
            return p
    return None


def armes(loadout, base=BASE):
    """[ { arme, n, nom, prix_m } ] d'un chargement : n = la charge par défaut de la base."""
    c = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
    out = []
    for (rid,) in c.execute("select ComponentID from DataLoadoutWeapons where ID = ? order by ComponentNumber", (loadout,)):
        w, n = c.execute("select ComponentID, DefaultLoad from DataWeaponRecord where ID = ?", (rid,)).fetchone()
        nom = c.execute("select Name from DataWeapon where ID = ?", (w,)).fetchone()[0]
        out.append({"arme": w, "n": n, "nom": nom, "prix_m": prix(nom)})
    return out


def cout(liste):
    """Prix d'un chargement complet ; lève si une arme n'a pas de prix ( jamais de munition gratuite par oubli )."""
    sans = [a["nom"] for a in liste if a["prix_m"] is None]
    if sans:
        raise ValueError(f"armes sans prix dans PRIX_ARME_M : {sans}")
    return sum(a["n"] * a["prix_m"] for a in liste)


if __name__ == "__main__":
    for lo in (int(x) for x in sys.argv[1:] or ["7453"]):
        L = armes(lo)
        for a in L:
            print(f"  {a['n']:2d} x {a['nom']:40s} {a['prix_m']} M$")
        print(f"chargement {lo} : {cout(L):.2f} M$")
