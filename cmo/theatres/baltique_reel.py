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
] + [(BC.fichier(nom, pays), "Russie-Chine", "Russia [1992-]", "chasse") for nom, pays, *_ in BC.BASES] + [
    # composante air complète ( 03/10 ) : les bases réelles des avions de soutien
    ("US-Europe/RAF Mildenhall 2021.inst", "OTAN", "United States", "soutien"),            # 100th ARW, KC-135R
    ("US-Europe/Spangdahlem Air Base 2021.inst", "OTAN", "United States", "soutien"),       # EA-18G ( déploiement de 2022 )
    (BC.fichier("Geilenkirchen", "Germany"), "OTAN", "Germany [FRG/Reunified]", "soutien"),  # E-3A de l'OTAN
    (BC.fichier("Ivanovo-Severny", "Russia"), "Russie-Chine", "Russia [1992-]", "soutien"),  # A-50U, Il-22PP
    (BC.fichier("Diaguilevo", "Russia"), "Russie-Chine", "Russia [1992-]", "soutien"),       # Il-78M
    ("US-Europe/RAF Fairford 2021.inst", "OTAN", "United States", "soutien"),               # B-52H ( Bomber Task Force )
    (BC.fichier("Engels", "Russia"), "Russie-Chine", "Russia [1992-]", "soutien"),          # Tu-160M, Tu-95MSM
    (BC.fichier("Soltsy-2", "Russia"), "Russie-Chine", "Russia [1992-]", "soutien"),        # Tu-22M3M
    (BC.fichier("Miroslawiec", "Poland"), "OTAN", "Poland", "soutien"),                     # drones MQ-9A et TB2
]

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
] + [
    # LA COMPOSANTE AIR COMPLÈTE ( 03/10, À VALIDER ) : la part est un RÔLE ( guet, ravitailleur, brouilleur, sead ).
    (BC.fichier("Geilenkirchen", "Germany"), "Germany [FRG/Reunified]", 1626, 4, "guet"),        # E-3A ( NAEW&CF, 14 en tout )
    ("Poland/33rd Airlift Air Base-Powidz Air Base 2016.inst", "Poland", 6812, 2, "guet"),     # Saab 340 AEW polonais ( 2 )
    ("US-Europe/RAF Mildenhall 2021.inst", "United States", 7712, 6, "ravitailleur"),        # KC-135R ( 15 à Mildenhall )
    ("US-Europe/Spangdahlem Air Base 2021.inst", "United States", 4518, 6, "brouilleur"),    # EA-18G ( 6 en 2022 )
    ("Germany/Schleswig Air Base.inst", "Germany [FRG/Reunified]", 7611, 8, "sead"),        # Tornado ECR, AARGM ( TaktLwG 51 )
    (BC.fichier("Ivanovo-Severny", "Russia"), "Russia [1992-]", 3461, 2, "guet"),            # A-50U ( ~6 restants )
    (BC.fichier("Ivanovo-Severny", "Russia"), "Russia [1992-]", 4607, 2, "brouilleur"),      # Il-22PP Porubchtchik ( 3 )
    (BC.fichier("Diaguilevo", "Russia"), "Russia [1992-]", 2687, 4, "ravitailleur"),         # Il-78M ( ~15 )
    # les bombardiers et leurs missiles de croisière ( jamais un chargement nucléaire )
    ("US-Europe/RAF Fairford 2021.inst", "United States", 4893, 4, "bombardier"),            # B-52H, JASSM-ER + MALD
    (BC.fichier("Engels", "Russia"), "Russia [1992-]", 7023, 4, "bombardier"),               # Tu-95MSM, Kh-101 ( ~20 prêts )
    (BC.fichier("Engels", "Russia"), "Russia [1992-]", 7021, 2, "bombardier"),               # Tu-160M, Kh-101 ( ~10 )
    (BC.fichier("Soltsy-2", "Russia"), "Russia [1992-]", 7022, 6, "bombardier"),             # Tu-22M3M, Kh-32 ( ~12 )
    # la reconnaissance et l'évaluation des dégâts
    (BC.fichier("Miroslawiec", "Poland"), "United States", 7473, 4, "reco"),                # MQ-9A ( détachement américain )
    (BC.fichier("Miroslawiec", "Poland"), "Poland", 5395, 6, "reco"),                       # Bayraktar TB2 polonais ( 24 )
    ("US-Europe/RAF Mildenhall 2021.inst", "United States", 5832, 2, "elint"),             # RC-135V Rivet Joint
    (BC.fichier("Pskov-Kresty", "Russia"), "Russia [1992-]", 2178, 2, "elint"),             # Il-20M
    (BC.fichier("Pskov-Kresty", "Russia"), "Russia [1992-]", 8324, 4, "reco"),              # Orion ( Inokhodets )
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


# LA COMPOSANTE NAVALE ( 03/10, recherche « marines_baltique_2026.md », DB3000 relue ) : ( pays, dbid, nom, nombre engagé,
# lat, lon de la RADE ( un point de mer devant le port : aucune base navale de la Baltique n'existe dans CMO ), rôle, genre ).
# Unités de combat seulement ( pas encore les mines, l'amphibie ni les vedettes ) ; disponibilité réelle appliquée ( les
# frégates allemandes, basées en mer du Nord, sont en baie de Kiel ). CHOIX À VALIDER : rades, nombres, frégates allemandes.
_R, _DE, _DK, _PL, _SE, _FI, _EE = ("Russia [1992-]", "Germany [FRG/Reunified]", "Denmark", "Poland", "Sweden", "Finland",
                                    "Estonia [1992-]")
_BALTIYSK, _KRONSTADT = (54.70, 19.60), (59.98, 29.30)
NAVIRES = [
    (_R, 596, "Neustrashimy", 2, *_BALTIYSK, "fregate", "navire"),
    (_R, 2813, "Steregushchiy ( Redut )", 3, *_BALTIYSK, "corvette", "navire"),
    (_R, 2411, "Buyan-M ( Kalibr )", 4, *_BALTIYSK, "lance_missiles", "navire"),
    (_R, 3294, "Karakurt ( Kalibr )", 2, *_BALTIYSK, "lance_missiles", "navire"),
    (_R, 3295, "Karakurt Pantsir-M ( Kalibr )", 1, *_BALTIYSK, "lance_missiles", "navire"),
    (_R, 3295, "Karakurt Pantsir-M ( Kalibr ), Kronstadt", 1, *_KRONSTADT, "lance_missiles", "navire"),
    (_R, 2992, "Tarantul III ( Moskit )", 4, *_BALTIYSK, "lance_missiles", "navire"),
    (_R, 1101, "Nanuchka III ( P-120 )", 2, *_BALTIYSK, "lance_missiles", "navire"),
    (_R, 31, "Parchim II", 3, *_KRONSTADT, "corvette", "navire"),
    (_R, 31, "Parchim II, Baltiïsk", 3, *_BALTIYSK, "corvette", "navire"),
    (_R, 371, "Kilo 877EKM ( Dmitrov )", 1, *_KRONSTADT, "sous_marin", "sous_marin"),
    (_R, 780, "Lada 677 ( Velikiye Luki )", 1, *_KRONSTADT, "sous_marin", "sous_marin"),
    (_R, 771, "Kilo 636.3 ( mer Noire )", 1, *_KRONSTADT, "sous_marin", "sous_marin"),
    (_R, 2217, "Bal ( Kh-35U ), Donskoïé", 2, 54.93, 20.00, "cotier", "site"),
    (_R, 2217, "Bal ( Kh-35U ), Kotlin", 2, 60.03, 29.72, "cotier", "site"),
    (_DE, 4510, "F124 Sachsen", 2, 54.55, 10.40, "fregate", "navire"),
    (_DE, 2512, "F125 Baden-Württemberg", 2, 54.55, 10.40, "fregate", "navire"),
    (_DE, 2489, "F123 Brandenburg", 2, 54.55, 10.40, "fregate", "navire"),
    (_DE, 1283, "K130 Braunschweig", 6, 54.25, 12.05, "corvette", "navire"),
    (_DE, 498, "U212A lot 1", 1, 54.52, 10.05, "sous_marin", "sous_marin"),
    (_DE, 743, "U212A lot 2", 1, 54.52, 10.05, "sous_marin", "sous_marin"),
    (_DK, 5235, "Iver Huitfeldt", 3, 55.33, 11.00, "fregate", "navire"),
    (_DK, 4357, "Absalon", 2, 55.33, 11.00, "fregate", "navire"),
    (_PL, 3660, "Oliver Hazard Perry ( Kościuszko )", 1, 54.55, 18.75, "fregate", "navire"),
    (_PL, 4484, "Kaszub", 1, 54.55, 18.75, "corvette", "navire"),
    (_PL, 3015, "Orkan ( RBS-15 )", 3, 54.55, 18.75, "lance_missiles", "navire"),
    (_PL, 2145, "NSM côtier, Siemirowice", 4, 54.42, 17.76, "cotier", "site"),
    (_SE, 755, "Visby", 4, 56.05, 15.65, "corvette", "navire"),
    (_SE, 3830, "Gävle", 2, 58.95, 18.60, "corvette", "navire"),
    (_SE, 710, "Gotland", 3, 56.05, 15.65, "sous_marin", "sous_marin"),
    (_SE, 168, "Södermanland", 1, 56.05, 15.65, "sous_marin", "sous_marin"),
    (_SE, 4884, "RBS-15KA côtier, Karlskrona", 2, 56.20, 15.50, "cotier", "site"),
    (_FI, 4643, "Hamina ( Gabriel V )", 4, 59.98, 24.35, "lance_missiles", "navire"),
    (_FI, 3212, "Rauma ( RBS-15 )", 2, 59.70, 22.50, "lance_missiles", "navire"),
    (_FI, 1590, "MTO 85M côtier, Upinniemi", 3, 60.03, 24.36, "cotier", "site"),
    (_EE, 3416, "Blue Spear côtier", 1, 59.35, 24.10, "cotier", "site"),
]
# Les zones navales de chaque camp ( lat, lon, demi-côté km ) : l'OTAN tient la Baltique centrale et barre les approches de
# Baltiïsk ( sous-marins ) ; la Russie tient les approches de Kaliningrad et le golfe de Finlande ( ses sous-marins ).
ZONES_NAVALES = {"OTAN": {"mer": (55.6, 18.0, 60.0), "asm": (55.2, 19.0, 35.0)},
                 "Russie-Chine": {"mer": (55.0, 19.3, 35.0), "asm": (59.95, 27.5, 30.0)}}


# LA COMPOSANTE TERRESTRE ( 03/10 ) : rôle des unités au sol ( DB3000 ) et objectifs de chaque camp ( lat, lon, poids ).
# Le réel : la Russie veut le passage de Suwałki ( relier Kaliningrad à la Biélorussie ) ; l'OTAN le tient, défend Vilnius et
# menace Goussev ( 11e corps, brigade d'Iskander de Tcherniakhovsk ). CHOIX À VALIDER : objectifs, poids, rôles.
ROLES_TERRE = {1918: "blinde", 2045: "mecanise", 1953: "artillerie", 4881: "blinde", 3516: "blinde", 3548: "artillerie",
               2048: "artillerie", 4469: "artillerie"}
OBJECTIFS_TERRE = {
    "Russie-Chine": {"attaque": [("Passage de Suwałki", 54.15, 23.20, 1.0)],
                     "tenir": [("Goussev", 54.59, 22.20, 1.0), ("Kaliningrad", 54.71, 20.51, 1.0)]},
    "OTAN": {"attaque": [("Goussev ( 11e corps, Iskander )", 54.59, 22.20, 1.0)],
             "tenir": [("Passage de Suwałki", 54.15, 23.20, 1.0), ("Vilnius", 54.69, 25.28, 0.8)]},
}
