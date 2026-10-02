"""THÉÂTRE BALTIQUE RÉEL ( 02/10 ) : la guerre OTAN contre Russie-Chine sur de VRAIES installations. Plus de drapeaux
( Younes : « que du réel, on ne joue plus » ) : la guerre avance par ce qui est détruit.

Les installations sont les modèles livrés avec CMO ( ImportExport/<pays>/*.inst, versions les plus récentes ), sauf les
bases russes de la Baltique, absentes de CMO, construites au même format par bases_construites.py ( HMT/Russia/ ).

CHOIX À VALIDER PAR YOUNES ( copier le réel ) :
- la liste ci-dessous : bases de chasse et de transport en service, sites radar et sol-air ; Belarus et district militaire
  Ouest russe pris dans leur dernière année disponible ( 2013-2014 ), à moderniser ( S-400 à la place des S-300 ) ;
- les bases russes construites ( bases_construites.BASES ) : position, piste, abris et dépôts saisis de mémoire.
"""
from theatres.baltique import CAMPS, PAYS                 # noqa: F401  ( mêmes pays, mêmes parts de budget )
import bases_construites as BC

NOM = "Baltique réel"

# ( fichier sous ImportExport/, camp, pays, rôle )
INSTALLATIONS = [
    ("Poland/32nd TAB-Lask Air Base 2016.inst", "OTAN", "Poland", "chasse"),
    ("Poland/31st TAB- Poznan Air Base 2016.inst", "OTAN", "Poland", "chasse"),
    ("Poland/22nd TAB-Malbork Air Base 2016.inst", "OTAN", "Poland", "chasse"),
    ("Poland/23rd TAB-Minsk Mazowiecki Air Base 2016.inst", "OTAN", "Poland", "chasse"),
    ("Poland/21st TAB-Swidwin Air Base 2016.inst", "OTAN", "Poland", "chasse"),
    ("Poland/33rd Airlift Air Base-Powidz Air Base 2016.inst", "OTAN", "Poland", "transport"),
    ("Poland/43rd Navy Air Base-Gdynia Babie Doly Air Base 2016.inst", "OTAN", "Poland", "aéronavale"),
    ("Lithuania/Siauliai Air Base 2024.inst", "OTAN", "Lithuania [1992-]", "police du ciel balte"),
    ("Lithuania/Lithuania Radar Sites.inst", "OTAN", "Lithuania [1992-]", "radar"),
    ("Latvia/Latvia Radar Sites.inst", "OTAN", "Latvia [1992-]", "radar"),
    ("Estonia/Amari Air Base 2024.inst", "OTAN", "Estonia [1992-]", "police du ciel balte"),
    ("Estonia/Estonia Radar Sites.inst", "OTAN", "Estonia [1992-]", "radar"),
    ("Finland/Air Wing Bases/Birkala 1979-.inst", "OTAN", "Finland", "chasse"),
    ("Finland/Air Wing Bases/Utti.inst", "OTAN", "Finland", "hélicoptères"),
    ("Finland/Radar/Fika 1980-.inst", "OTAN", "Finland", "radar"),
    ("Sweden/Air Wing Bases/F 7 Satenas 1992-.inst", "OTAN", "Sweden", "chasse"),
    ("Sweden/Air Wing Bases/F 17 Ronneby.inst", "OTAN", "Sweden", "chasse"),
    ("Denmark/Skrydstrup Air Base 2014.inst", "OTAN", "Denmark", "chasse"),
    ("Denmark/Bornholm-Ronne Airport 2014.inst", "OTAN", "Denmark", "aérodrome"),
    ("Germany/Schleswig Air Base.inst", "OTAN", "Germany [FRG/Reunified]", "chasse"),
    ("Germany/Hohn Air Base.inst", "OTAN", "Germany [FRG/Reunified]", "transport"),
    ("Germany/Wunstorf Air Base.inst", "OTAN", "Germany [FRG/Reunified]", "transport"),
    ("Belarus/Baranovichi Air Base 2014.inst", "Russie-Chine", "Belarus [1992-]", "chasse"),
    ("Belarus/Babruysk Air Base 2014.inst", "Russie-Chine", "Belarus [1992-]", "attaque"),
    ("Belarus/Belarus AD/Belarus AD 2013.inst", "Russie-Chine", "Belarus [1992-]", "sol-air"),
    ("Belarus/Belarus EW/Belarus EW 2013.inst", "Russie-Chine", "Belarus [1992-]", "radar"),
    ("USSR-Russia/Western Military District/Western Military District AD/Western Military District AD 2013.inst",
     "Russie-Chine", "Russia [1992-]", "sol-air"),
    ("USSR-Russia/Western Military District/Western Military District EW/Western Military District EW 2013.inst",
     "Russie-Chine", "Russia [1992-]", "radar"),
] + [(BC.fichier(nom, pays), "Russie-Chine", "Russia [1992-]", "chasse") for nom, pays, *_ in BC.BASES]

# Les COPIES : CMO ne recrée pas un élément dont l'identifiant ( Member_GUID du fichier ) a déjà servi dans la partie, même
# effacé ( 02/10 : Łask réimportée après une table rase n'a rendu qu'un élément sur 62 ). Chaque construction importe donc
# une copie du fichier aux identifiants NEUFS, sous ImportExport/HMT/Copies/ ; les bases construites le sont déjà.
COPIES = "HMT/Copies/"


def fichier_cmo(f):
    return f if f.startswith("HMT/") else COPIES + f


def rafraichir_copies(racine=None):
    """Réécrit les copies ( identifiants neufs ) et les bases construites. Rend le nombre de fichiers écrits."""
    import json
    import os
    import uuid
    import cmo_labo as CL
    racine = racine or CL.CMO
    n = len(BC.ecrire(racine))
    for f, *_ in INSTALLATIONS:
        if f.startswith("HMT/"):
            continue
        with open(os.path.join(racine, "ImportExport", f), encoding="utf-8-sig") as g:
            d = json.load(g)
        for m in d.get("MemberRecords") or []:
            m["Member_GUID"] = str(uuid.uuid4())
        chemin = os.path.join(racine, "ImportExport", fichier_cmo(f))
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w", encoding="utf-8-sig") as g:
            json.dump(d, g, ensure_ascii=False, indent=2)
        n += 1
    return n


FICHIERS = tuple(fichier_cmo(f) for f, *_ in INSTALLATIONS)

# LES FLOTTES ( 2026, copier le réel, À VALIDER ) : ( fichier de la base, pays, dbid de l'avion, nombre, part en frappe ).
# Les avions sont posés PAR PAIRES ( une patrouille ne part que par vols, sonde du 02/10 ) ; la part en frappe reçoit le
# chargement guidé d'attaque au sol ( catalogue.chargement_frappe ), le reste le chargement air-air du catalogue.
_P = "Poland/"
FLOTTES = [
    (_P + "32nd TAB-Lask Air Base 2016.inst", "Poland", 7087, 16, 0.5),             # 32e base : F-16C/D Block 52+
    (_P + "32nd TAB-Lask Air Base 2016.inst", "United States", 8094, 12, 0.5),      # rotation américaine ( F-35A )
    (_P + "31st TAB- Poznan Air Base 2016.inst", "Poland", 7087, 16, 0.5),          # 31e base ( Krzesiny ) : F-16
    (_P + "22nd TAB-Malbork Air Base 2016.inst", "Poland", 2840, 8, 0.0),           # MiG-29 en fin de service
    (_P + "23rd TAB-Minsk Mazowiecki Air Base 2016.inst", "Poland", 6040, 12, 0.5), # FA-50PL
    ("Lithuania/Siauliai Air Base 2024.inst", "Germany [FRG/Reunified]", 8261, 4, 0.0),   # police du ciel balte
    ("Estonia/Amari Air Base 2024.inst", "United Kingdom", 8272, 4, 0.0),          # police du ciel balte
    ("Finland/Air Wing Bases/Birkala 1979-.inst", "Finland", 2836, 16, 0.25),       # escadre de Satakunta, F/A-18C
    ("Sweden/Air Wing Bases/F 7 Satenas 1992-.inst", "Sweden", 6788, 16, 0.25),     # F 7, Gripen C
    ("Sweden/Air Wing Bases/F 17 Ronneby.inst", "Sweden", 6788, 16, 0.25),          # F 17, Gripen C
    ("Denmark/Skrydstrup Air Base 2014.inst", "Denmark", 5180, 12, 0.5),            # F-35A
    ("Denmark/Skrydstrup Air Base 2014.inst", "Denmark", 5756, 8, 0.5),             # F-16 restants
    ("Germany/Schleswig Air Base.inst", "Germany [FRG/Reunified]", 8261, 12, 0.5),  # Typhoon ( pour Laage, absente de CMO )
    (BC.fichier("Tchkalovsk", "Russia"), "Russia [1992-]", 6210, 16, 0.5),          # 689e GvIAP, Su-30SM / Su-27SM3
    (BC.fichier("Donskoie", "Russia"), "Russia [1992-]", 6210, 12, 0.5),            # aéronavale de la Baltique
    (BC.fichier("Besovets", "Russia"), "Russia [1992-]", 6645, 16, 0.25),           # 159e IAP, Su-35S
    (BC.fichier("Khotilovo", "Russia"), "Russia [1992-]", 6645, 12, 0.25),          # 790e IAP
    (BC.fichier("Levachovo", "Russia"), "Russia [1992-]", 8333, 4, 0.5),            # Su-57 ( peu nombreux )
    ("Belarus/Baranovichi Air Base 2014.inst", "Belarus [1992-]", 7695, 8, 0.5),    # 61e base : Su-30SM
    ("Belarus/Baranovichi Air Base 2014.inst", "Belarus [1992-]", 5909, 8, 0.25),   # MiG-29
]

# LES FORCES AU SOL ( 2026, copier le réel, À VALIDER ) : ( pays, dbid de l'unité mobile DB3000, nom, lat, lon ).
SOL = [
    ("Russia [1992-]", 1937, "S-400, 183e régiment ( Gvardeïsk )", 54.65, 21.07),
    ("Russia [1992-]", 1937, "S-400, Kaliningrad", 54.72, 20.52),
    ("Russia [1992-]", 1934, "Pantsir-S1, Tchkalovsk", 54.78, 20.42),
    ("Russia [1992-]", 1934, "Pantsir-S1, Baltiïsk", 54.65, 19.93),
    ("Russia [1992-]", 254, "Iskander-M, 152e brigade ( Tcherniakhovsk )", 54.63, 21.81),
    ("Russia [1992-]", 1894, "Bastion-P, défense côtière ( Baltiïsk )", 54.70, 20.15),   # à terre ( 54,67/19,96 : refusé, REFUS 4 )
    ("Russia [1992-]", 1918, "T-90A, 11e corps ( Goussev )", 54.59, 22.20),
    ("Russia [1992-]", 1918, "T-90A, 11e corps ( Goussev )", 54.60, 22.25),
    ("Russia [1992-]", 1953, "2S19 Msta-S, 244e brigade d'artillerie", 54.74, 20.62),
    ("Russia [1992-]", 1937, "S-400, Saint-Pétersbourg sud", 59.80, 30.10),
    ("Russia [1992-]", 1937, "S-400, Saint-Pétersbourg nord", 60.05, 30.45),
    ("Russia [1992-]", 254, "Iskander-M, 26e brigade ( Louga )", 58.73, 29.85),
    ("Belarus [1992-]", 5339, "S-400 biélorusse ( Minsk )", 53.95, 27.45),
    ("Belarus [1992-]", 3609, "Iskander-M biélorusse ( Assipovitchy )", 53.30, 28.64),
    ("Belarus [1992-]", 4469, "Polonez, MLRS", 53.10, 26.10),
    ("Belarus [1992-]", 3515, "Tor-M2K, Baranovitchi", 53.12, 26.08),
    ("Poland", 3653, "Patriot PAC-3 MSE ( Wisła ), Varsovie", 52.25, 20.95),
    ("Poland", 4690, "Patriot PAC-3 MSE ( Wisła ), Łask", 51.57, 19.20),
    ("Poland", 3659, "HIMARS ( Homar-A )", 53.70, 20.80),
    ("Poland", 5244, "Homar-K ( K239 )", 53.80, 21.60),
    ("Poland", 4881, "M1A2C Abrams, 18e division", 53.10, 22.10),
    ("Poland", 4881, "M1A2C Abrams, 16e division", 54.10, 21.40),
    ("Lithuania [1992-]", 5268, "NASAMS III, Vilnius", 54.70, 25.25),
    ("Lithuania [1992-]", 4649, "HIMARS lituanien", 55.20, 23.90),
    ("Germany [FRG/Reunified]", 3516, "Leopard 2A7, 45e brigade blindée ( Rūdninkai )", 54.40, 25.05),
    ("Germany [FRG/Reunified]", 2228, "Patriot allemand ( Rzeszów )", 50.11, 22.02),
    ("Estonia [1992-]", 4650, "HIMARS estonien", 59.10, 25.70),
    ("Finland", 2011, "NASAMS II, Helsinki", 60.25, 24.95),
    ("Finland", 3548, "K9 Moukari", 60.90, 27.10),
]

# Les lanceurs de missiles sol-sol affectés aux frappes ( Iskander russes et biélorusses, HIMARS, Homar-K ).
LANCEURS = {254, 3609, 3659, 5244, 4649, 4650}
