#!/usr/bin/env python3
"""Les bases qui manquent aux vraies installations de CMO, construites AU FORMAT de CMO ( un .inst comme ceux
d'ImportExport/<pays>/ ) : une piste orientée, ses points d'accès, des abris durcis, des dépôts de munitions, des cuves,
une tour. Écrites dans ImportExport/HMT/<pays>/, elles s'importent comme les autres ( HMT_importer ) et forment un groupe
qui accueille les avions ( banc_v8 du 02/10 : un avion se pose sur le groupe d'une vraie base, pas sur une piste seule ).

Aucune base russe de la Baltique n'est livrée avec CMO ( 02/10 : USSR-Russia n'a, pour le district militaire Ouest, que
des sites sol-air et radar de 2003 à 2013 ).

CHOIX À VALIDER ( copier le réel, saisi de mémoire ) : position, cap et longueur de piste, nombre d'abris et de dépôts de
chaque base ( table BASES ). Le plan au sol est schématique : piste au centre, abris à 600 m, dépôts à 1 200 m.

    .venv312/bin/python cmo/bases_construites.py [--ecrire]
"""
import json
import math
import os
import sys
import uuid

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

DOSSIER = "HMT"                                          # sous ImportExport/
PISTES = {2000: 43, 2600: 55, 3200: 35, 4000: 757}        # longueur ( m ) -> dbid de la DB3000
# Abris pour avion LOURD ( 27, 1x Large ) : un Su-30 ou un Su-35 n'entre pas dans un abri « Medium » ( 4 ) ; guerre réelle
# du 02/10 : 22 avions russes refusés par CMO ( REFUS 4 ) faute de place.
ACCES, ABRI, DEPOT, CUVE, TOUR, AIRE = 353, 27, 325, 943, 3, 217
AIRE_TRES_GRAND = 103                                     # « A/C Tarmac Space (4x Very Large Aircraft) » : E-3, KC-135, A-50, Il-78

# nom, pays ( dossier ), lat, lon, cap de piste ( ° ), longueur ( m ), abris, dépôts, aires — À VALIDER
BASES = [
    ("Tchkalovsk", "Russia", 54.766, 20.397, 60, 2600, 16, 4, 6),
    ("Donskoie", "Russia", 54.940, 19.970, 100, 2600, 12, 3, 4),
    ("Pskov-Kresty", "Russia", 57.785, 28.395, 40, 2600, 8, 3, 8),
    ("Levachovo", "Russia", 60.090, 30.190, 100, 2600, 8, 2, 6),
    ("Besovets", "Russia", 61.885, 34.155, 100, 2600, 16, 4, 4),
    ("Khotilovo", "Russia", 57.650, 34.100, 80, 2600, 16, 4, 4),
]

# Les bases des avions de SOUTIEN ( composante air complète, 03/10 ) absentes de CMO : guet radar de l'OTAN ( NAEW&CF,
# Geilenkirchen ), A-50U ( 144e régiment, Ivanovo-Severny ), Il-78M ( 203e régiment, Diaguilevo près de Riazan ). Piste
# longue ( 4 000 m, avions « très grands » ), aires pour très grands avions, pas d'abris. À VALIDER.
BASES_SOUTIEN = [
    ("Geilenkirchen", "Germany", 50.961, 6.042, 90, 4000, 0, 1, 6),
    ("Ivanovo-Severny", "Russia", 57.058, 40.981, 0, 4000, 0, 1, 4),
    ("Diaguilevo", "Russia", 54.643, 39.571, 120, 4000, 0, 1, 4),
    ("Engels", "Russia", 51.481, 46.200, 140, 4000, 0, 2, 6),           # 121e et 184e régiments ( Tu-160, Tu-95MS )
    ("Miroslawiec", "Poland", 53.395, 16.083, 90, 2600, 0, 1, 4),       # 12e base de drones ( MQ-9A américains, TB2 )
    ("Ostrov", "Russia", 57.300, 28.430, 0, 2600, 8, 1, 4),             # 15e brigade d'aviation de l'armée de terre ( Ka-52M, Mi-28NM )
    ("Soltsy-2", "Russia", 58.139, 30.330, 20, 4000, 0, 2, 4),          # 840e régiment ( Tu-22M3 )
]


def _point(lat, lon, cap, metres_long, metres_lat):
    """Décalage en mètres le long du cap ( avant ) et à sa droite ( lat ), en ( lat, lon )."""
    c = math.radians(cap)
    dn = metres_long * math.cos(c) - metres_lat * math.sin(c)
    de = metres_long * math.sin(c) + metres_lat * math.cos(c)
    return lat + dn / 111_320.0, lon + de / (111_320.0 * math.cos(math.radians(lat)))


def construire(nom, lat, lon, cap, piste_m, abris, depots, aires, cuves=2, aire=AIRE):
    piste = PISTES[min(PISTES, key=lambda L: abs(L - piste_m))]
    membres = []

    def poser(dbid, quoi, la, lo, orientation=0.0):
        membres.append({"Member_DBID": dbid, "Member_GUID": str(uuid.uuid4()), "MemberType": "Facility",
                        "MemberName": f"{nom} {quoi}", "ParentGroupName": nom, "Longitude": lo, "Latitude": la,
                        "Altitude": 0.0, "LoadoutID": 0, "Orientation": float(orientation), "HostedAircraftRecords": []})

    poser(piste, "Runway", lat, lon, cap)
    for s in (-1, 1):
        poser(ACCES, "Runway Access Point", *_point(lat, lon, cap, s * piste_m / 2, 0))
    for i in range(abris):
        poser(ABRI, f"HAS {i + 1}", *_point(lat, lon, cap, -piste_m / 2 + (i + 0.5) * piste_m / max(1, abris), 600))
    for i in range(aires):
        poser(aire, f"Tarmac {i + 1}", *_point(lat, lon, cap, -piste_m / 4 + i * 120, -350))
    for i in range(depots):
        poser(DEPOT, f"Ammo Bunker {i + 1}", *_point(lat, lon, cap, -400 + i * 250, 1200))
    for i in range(cuves):
        poser(CUVE, f"AvGas {i + 1}", *_point(lat, lon, cap, 500 + i * 150, -900))
    poser(TOUR, "Control Tower", *_point(lat, lon, cap, 0, -400))
    return {"DB_ID": 1, "FormatVersion": 0, "MemberRecords": membres, "ValidFrom": "", "ValidUntil": "", "Name": nom,
            "Comments": "HMT : base construite au format de CMO ( bases_construites.py ), plan schématique, à valider.",
            "Template": False}


def fichier(nom, pays):
    return f"{DOSSIER}/{pays}/{nom}.inst"


def ecrire(racine=CL.CMO):
    out = []
    for nom, pays, *rest in BASES + BASES_SOUTIEN:
        d = construire(nom, *rest, aire=AIRE_TRES_GRAND if (nom, pays, *rest) in BASES_SOUTIEN else AIRE)
        chemin = os.path.join(racine, "ImportExport", fichier(nom, pays))
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w", encoding="utf-8-sig") as g:
            json.dump(d, g, ensure_ascii=False, indent=2)
        out.append((fichier(nom, pays), len(d["MemberRecords"])))
    return out


if __name__ == "__main__":
    if "--ecrire" in sys.argv:
        for f, n in ecrire():
            print(f"{f} : {n} éléments")
    else:
        for nom, pays, *rest in BASES:
            print(f"{fichier(nom, pays)} : {len(construire(nom, *rest)['MemberRecords'])} éléments")
