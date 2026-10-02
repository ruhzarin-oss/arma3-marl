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

FICHIERS = tuple(f for f, *_ in INSTALLATIONS)
