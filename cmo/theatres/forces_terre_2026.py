# -*- coding: utf-8 -*-
"""Forces terrestres réelles autour du corridor de Suwałki, de Kaliningrad, des pays baltes et de la Biélorussie,
état estimé au 3 octobre 2026, calées sur la base DB3000 de CMO (copie DB3K_519.db3, lecture seule).

Lire avec terre_munitions_2026.md (même dossier) : sources, confiance, substituts, munitions.

CONVENTIONS
- SOL_2026 : (pays_cmo, dbid, nom, lat, lon, role). Une ligne = UNE installation mobile DataFacility (catégorie 5001)
  ≈ UNE compagnie / escadron / batterie réelle. L'entrée CMO ne porte que 3 à 6 véhicules : la puissance de feu est
  donc sous-représentée d'un facteur ≈ 3 (une compagnie réelle = 10 à 14 chars ou VCI, une batterie = 6 à 8 pièces).
  Une brigade OTAN pleine ≈ 8 à 12 lignes ; une brigade russe ou biélorusse creuse en 2026 ≈ 3 à 6 lignes.
- role ∈ {"blinde", "mecanise", "infanterie", "artillerie", "lanceur", "sol-air"}.
- lat/lon : garnison (QG ou bataillon), PAS une position de combat ; degrés décimaux, précision ≈ ville (± 5 km).
- Confiance en commentaire : É élevée, M moyenne, F faible. « SUBST » = la base n'a pas le matériel réel : on pose le
  plus proche (voir CATALOGUE_TERRE). Les portées de la base sont en milles nautiques : × 1,852 pour des km.
- Ce qui est ENGAGÉ EN UKRAINE n'est posé qu'à hauteur de ce qui reste en garnison (reconstitution, dépôts) : voir les
  commentaires « Ukraine ». Rien n'est posé pour le matériel commandé mais pas livré au 03/10/2026.
- Défense aérienne longue portée (Patriot, S-400, S-300) : quelques lignes seulement, à vérifier contre les sites
  sol-air déjà posés depuis ImportExport pour éviter les doublons (DOUBLON_POSSIBLE).
- IMPORTANT : STOCKS_MUNITIONS est calé sur la recherche web du 03/10 (sources consultées). SOL_2026 a été écrit
  AVANT le retour des deux recherches d'ordre de bataille : tiré de la base, de ordre_de_bataille_2026.md et des
  connaissances publiques à mi-2026. À recouper avant une guerre « au réel ».
"""

RU = "Russia [1992-]"
BY = "Belarus [1992-]"
PL = "Poland"
LT = "Lithuania [1992-]"
LV = "Latvia [1992-]"
EE = "Estonia [1992-]"
DE = "Germany [FRG/Reunified]"
US = "United States"
FI = "Finland"
SE = "Sweden"
UK = "United Kingdom"   # chef de groupement en Estonie (chaîne exacte du moteur, budgets.py / blocs.py)
CA = "Canada"           # chef de la brigade multinationale en Lettonie
FR = "France"           # contingent en Estonie

# ---------------------------------------------------------------------------------------------------------------
# CATALOGUE : type réel -> (dbid DataFacility, nom exact DB3000, pays opérateur dans la base, remarque)
# Relu dans la base le 03/10/2026 : non hypothétique, non retiré, YearCommissioned <= 2026 sauf mention.
# ---------------------------------------------------------------------------------------------------------------
CATALOGUE_TERRE = {
    # Pologne
    "PL_K2":       (3516, "Armored Plt (Leopard 2A7 MBT x 3)", DE, "SUBST : aucun K2 dans DB3000 (ni installation, ni véhicule) ; 120 mm L55, même génération"),
    "PL_M1A2C":    (4881, "Armored Plt (M1A2C Abrams MBT x 4)", PL, "exact (M1A2 SEPv3)"),
    "PL_M1A1FEP":  (4592, "Armored Plt (M1A1 Abrams MBT x 4)", US, "SUBST pays"),
    "PL_LEO2PL":   (2340, "Armored Plt (Leopard 2A5 MBT x 3)", DE, "SUBST : 2PL = 2A4 au niveau 2A5"),
    "PL_LEO2A4":   (2333, "Armored Plt (Leopard 2A4 MBT x 3)", DE, "SUBST pays"),
    "PL_PT91":     (4726, "Armored Plt (PT-91 Twardy MBT x 3)", PL, "exact"),
    "PL_ROSOMAK":  (3043, "Mech Inf Plt (M1296 Dragoon ICVD x 3)", US, "SUBST : 8x8 à canon de 30 mm ; aucun Rosomak/AMV"),
    "PL_BWP1":     (2043, "Mech Inf Plt (BMP-1P [AT-5 Spandrel] IFV x 3)", RU, "SUBST pays (BWP-1 = BMP-1)"),
    "PL_BORSUK":   (2330, "Mech Inf Plt (Puma IFV [Spike LR ] x 3)", DE, "SUBST : chenillé, 30 mm + Spike LR comme la tourelle ZSSW-30"),
    "PL_K9":       (4652, "Arty Bty (155mm/52 K-9A1 EGY Thunder Self-Propelled Howitzer x 6)", PL, "pays exact, nom égyptien dans la base"),
    "PL_KRAB":     (2048, "Arty Bty (155mm/52 Krab Self-Propelled Howitzer x 6)", PL, "exact"),
    "PL_LANGUSTA": (2088, "Arty Bty (BM-21 Grad MLRS Mod [WR-40 Langusta] x 6)", PL, "exact, 48 km"),
    "PL_HOMAR_K":  (5244, "Arty Plt (Homar-K [K239 Chunmoo KMLRS])", PL, "exact ; roquette guidée 239 mm 81 km ; PAS de CTM-290 dans la base"),
    "PL_HIMARS":   (3659, "Arty Bty (M142 HIMARS)", PL, "exact ; M31 GMLRS 83 km chargées, ATACMS 300 km à 0"),
    "PL_PATRIOT":  (3653, "SAM Plt (Patriot [PAC-3 MSE])", PL, "exact (Wisła phase 1), 48 PAC-3 MSE 111 km"),
    "PL_CAMM":     (3269, "SAM Bty (Sky Sabre [Land Ceptor]) TEL)", UK, "SUBST : Mała Narew / Pilica+ (CAMM, 28 km dans la base)"),
    "PL_OSA":      (3985, "SAM Bn/2 (SA-8b Gecko Mod-1 [9K33M3 Osa-AKM-P1 Zadlos])", PL, "exact"),
    "PL_POPRAD":   (3527, "SAM Plt/2 (Poprad [Piorun])", PL, "exact"),
    # Lituanie
    "LT_VILKAS":   (3043, "Mech Inf Plt (M1296 Dragoon ICVD x 3)", US, "SUBST : Vilkas = Boxer à tourelle 30 mm ; les Boxer de la base (2316, 2878) n'ont AUCUNE arme"),
    "LT_M113":     (5081, "Mech Inf Plt (M113A2 APC x 4)", LT, "exact"),
    "LT_JLTV":     (5086, "Motorized Inf Sec (JLTV x 3)", LT, "exact"),
    "LT_JAVELIN":  (5087, "Anti-Tank Plt (FGM-148 Javelin x 3)", LT, "exact"),
    "LT_PZH2000":  (5088, "Arty Bty (155mm/52 PzH 2000 Self-Propelled Howitzer x 6)", LT, "exact"),
    "LT_NASAMS":   (5268, "SAM Plt/2 (NASAMS III)", LT, "exact, AMRAAM 37 km"),
    "LT_HIMARS":   (4649, "Arty Bty (M142 HIMARS)", LT, "exact mais NON POSÉ : livraison en Lituanie annoncée fin 2026"),
    "LT_CAESAR":   (4651, "Arty Bty (155mm/52 Caesar Self-Propelled Howitzer)", LT, "NON POSÉ : 48 commandés, livraisons 2027 (base : 2027)"),
    "LT_LEO2A8":   (5264, "Armored Plt (Leopard 2A8 MBT x 4)", LT, "NON POSÉ : 44 commandés, livraisons 2027-2030"),
    # Estonie
    "EE_CV90":     (5098, "Mech Inf Plt (CV 9035EE x 4)", EE, "exact"),
    "EE_K9":       (3550, "Arty Bty (155mm/52 K-9 Thunder [Kou] Self-Propelled Howitzer x 6)", EE, "exact"),
    "EE_HIMARS":   (4650, "Arty Bty (M142 HIMARS)", EE, "exact, 6 lanceurs livrés le 30/04/2025"),
    "EE_CAESAR":   (4646, "Arty Bty (155mm/52 Caesar Self-Propelled Howitzer)", EE, "exact (base 2025) ; livraison réelle à vérifier (F)"),
    "EE_XA188":    (3832, "Motor Inf Plt (LAV-6 x 4)", CA, "SUBST : 6x6/8x8 à roues ; aucun Patria XA dans la base"),
    "EE_MISTRAL":  (3521, "SAM Plt (Mistral III MANPADS x 3)", EE, "exact"),
    "EE_IRIST":    (5055, "SAM Plt (IRIS-T SLM)", EE, "⚠ Hypothetical=1 dans la base (toutes les IRIS-T SLM le sont) ; 1 unité de tir livrée 06/2026"),
    "EE_CHUNMOO":  (5245, "Arty Plt (K239 Chunmoo KMLRS)", EE, "NON POSÉ : livraison 2e semestre 2027"),
    # Lettonie
    "LV_PATRIA":   (3832, "Motor Inf Plt (LAV-6 x 4)", CA, "SUBST : Patria 6x6"),
    "LV_RBS70":    (4274, "SAM Plt (RBS 70 NG MANPADS x 3)", LV, "exact"),
    "LV_M109":     (2929, "Arty Bty (155mm/39 M109A5 Self-Propelled Howitzer x 6)", US, "SUBST pays (M109A5Ö) ; une partie donnée à l'Ukraine (F)"),
    "LV_HIMARS":   (4647, "Arty Bty (M142 HIMARS)", LV, "NON POSÉ : livraisons 2027 (base : 2027)"),
    # Allemagne (brigade blindée 45 « Litauen »)
    "DE_LEO2A6":   (2341, "Armored Plt (Leopard 2A6 MBT x 3)", DE, "exact"),
    "DE_LEO2A7":   (3516, "Armored Plt (Leopard 2A7 MBT x 3)", DE, "exact"),
    "DE_PUMA":     (2330, "Mech Inf Plt (Puma IFV [Spike LR ] x 3)", DE, "exact"),
    "DE_PZH2000":  (2133, "Arty Bty (155mm/52 PzH 2000 Self-Propelled Howitzer x 6)", DE, "exact"),
    "DE_OZELOT":   (557, "SAM Sec (LeFlaSys [Ozelot])", DE, "SUBST du Skyranger 30 (absent de la base)"),
    # États-Unis
    "US_M1A2C":    (3517, "Armored Plt (M1A2C Abrams MBT x 4)", US, "exact (SEPv3)"),
    "US_M2A3":     (2784, "Mech Inf Plt (M2A3 Bradley AFV x 4)", US, "exact (M2A4 de la base = hypothétique)"),
    "US_M109A7":   (3228, "Arty Bty (155mm/39 M109A7 Self-Propelled Howitzer x 6)", US, "exact"),
    "US_STRYKER":  (3043, "Mech Inf Plt (M1296 Dragoon ICVD x 3)", US, "exact (escadron de cavalerie à Orzysz)"),
    "US_AVENGER":  (286, "SAM Sec (Avenger)", US, "exact"),
    # Royaume-Uni, Canada, France, Suède, Finlande (présences avancées et flanc nord)
    "UK_CR2":      (1930, "Armored Plt (Challenger 2 MBT x 4)", UK, "exact"),
    "UK_WARRIOR":  (2263, "Mech Inf Plt (FV510 Warrior IFV x 4)", UK, "exact"),
    "UK_ARCHER":   (4462, "Arty Bty/3 (155mm/52 FH-77BW L52 Archer Self-Propelled Howitzer)", UK, "exact (remplace les AS-90 donnés à l'Ukraine)"),
    "CA_LEO2A4M":  (2380, "Armored Plt (Leopard 2A4M MBT x 4)", CA, "exact"),
    "CA_LAV6":     (3832, "Motor Inf Plt (LAV-6 x 4)", CA, "exact"),
    "CA_M777":     (2383, "Arty Bty (155mm/39 M777 Towed Howitzer x 6)", CA, "exact"),
    "FR_LECLERC":  (1928, "Armored Plt (AMX-56 Leclerc MBT x 4)", FR, "exact"),
    "FR_VBCI":     (2396, "Mech Inf Plt (VBCI IFV x 4)", FR, "exact"),
    "SE_STRV122":  (2054, "Armored Plt (Leopard 2A5 MBT [Stridsvagn 122] x 4)", SE, "exact"),
    "SE_CV9040":   (2056, "Mech Inf Plt (CV 9040 x 4)", SE, "exact"),
    "SE_ARCHER":   (2297, "Arty Bty/3 (155mm/52 FH-77BW L52 Archer Self-Propelled Howitzer)", SE, "exact"),
    "SE_IRIST_SLS": (2159, "SAM Plt (EldE 98 [IRIS-T SLS])", SE, "exact"),
    "FI_LEO2A6":   (3848, "Armored Plt (Leopard 2A6M MBT x 4)", FI, "exact"),
    "FI_LEO2A4":   (5010, "Armored Plt (Leopard 2A4 MBT x 3)", FI, "exact"),
    "FI_CV9030":   (5096, "Mech Inf Plt (CV 9035DK x 4)", "Denmark", "SUBST : aucun CV9030FIN dans la base"),
    "FI_K9":       (3548, "Arty Bty (155mm/52 K-9 Thunder [Moukari] Self-Propelled Howitzer x 6)", FI, "exact"),
    "FI_M270":     (3663, "Arty Plt (M270 MLRS [298 RsRakH 06])", FI, "exact ; 3664 (2025) porte le GMLRS-ER 148 km"),
    "FI_NASAMS":   (2011, "SAM Plt/2 (NASAMS II [ItO 12])", FI, "exact"),
    # Russie
    "RU_T72B3":    (532, "Armored Plt (T-72BM MBT x 4)", RU, "SUBST : pas de T-72B3 en installation ; véhicule seul DataGroundUnit 102 (type 'Vehicle')"),
    "RU_T90M":     (1918, "Armored Plt (T-90A MBT x 4)", RU, "SUBST : T-90M seulement en véhicule seul (DataGroundUnit 136)"),
    "RU_T80BVM":   (2106, "Armored Plt (T-80U MBT x 4)", RU, "SUBST : T-80BVM en véhicule seul (DataGroundUnit 103)"),
    "RU_BMP2":     (1993, "Mech Inf Plt (BMP-2 IFV x 3)", RU, "exact"),
    "RU_BMP2M":    (4936, "Mech Inf Plt (BMP-2M IFV x 3)", RU, "exact"),
    "RU_BMP3":     (2045, "Mech Inf Plt (BMP-3 IFV x 3)", RU, "exact"),
    "RU_BTR82A":   (2218, "Motor Rifle Plt (BTR-82A APC x 3)", RU, "exact"),
    "RU_BMD4M":    (2860, "Mech Inf Plt (BMD-4M IFV x 3)", RU, "exact"),
    "RU_NONA":     (2071, "Arty Bty (120mm 2S9-S Nona-S Self-Propelled Mortar x 6)", RU, "exact"),
    "RU_2S19":     (1953, "Arty Bty (152mm/48 2S19 MSTA-S Self-Propelled Howitzer x 6)", RU, "exact, 22-41 km"),
    "RU_2S3M2":    (4218, "Arty Bty (152mm/34 2S3M2 Akatsiya M1973 Self-Propelled Howitzer x 6)", RU, "exact"),
    "RU_MSTA_B":   (1976, "Arty Bty (152mm/48 2A36 Giatsint-B Towed Howitzer x 6)", RU, "SUBST : 2A65 Msta-B absent, Giatsint-B à la place"),
    "RU_TORNADO_G": (2816, "Arty Bty (9A53 Tornado-G MLRS x 6)", RU, "exact, 40 km"),
    "RU_URAGAN":   (1969, "Arty Bty (BM-27 Uragan MLRS x 6)", RU, "exact, 41 km"),
    "RU_TORNADO_S": (4853, "Arty Bty (9A53 Tornado-S MLRS x 4)", RU, "exact ; 9M544 120 km chargées"),
    "RU_ISKANDER": (2556, "SSM Bn (SS-26 Stone [9K720 Iskander-M] TEL)", RU, "exact ; 4 9M723 + 4 9M728 (500 km dans la base)"),
    "RU_TOR_M2":   (2162, "SAM Plt (SA-15e Gauntlet [9K330 Tor-M2KM])", RU, "exact"),
    "RU_BUK_M3":   (2276, "SAM Plt (SA-27 Grizzly [9K317M Buk-M3])", RU, "exact, 70 km"),
    "RU_PANTSIR":  (3250, "SAM Plt (SA-22 Greyhound [Pantsir-SM])", RU, "exact"),
    "RU_S400":     (1937, "SAM Bn (SA-21a/b Growler [S-400 Triumf])", RU, "exact ; 48N6DM 250 km, 40N6 398 km"),
    # Biélorussie
    "BY_T72B3":    (5320, "Armored Plt (T-72BM MBT x 3)", BY, "pays exact (T-72B3 livrés depuis 2017)"),
    "BY_T72B":     (5319, "Armored Plt (T-72 MBT x 3)", BY, "exact"),
    "BY_BMP2":     (5316, "Mech Inf Plt (BMP-2 IFV x 3)", BY, "exact"),
    "BY_BTR82A":   (5315, "Motor Rifle Plt (BTR-82A APC x 3)", BY, "exact"),
    "BY_BTR80":    (5324, "Motor Rifle Plt (BTR-80 APC x 3)", BY, "exact (sans arme lourde dans la base)"),
    "BY_2S1":      (5321, "Arty Bty (122mm/36 2S1 Gvozdika M1974 Self-Propelled Howitzer x 6)", BY, "exact"),
    "BY_2S3":      (5322, "Arty Bty (152mm/34 2S3 Akatsiya M1973 Self-Propelled Howitzer x 6)", BY, "exact"),
    "BY_BM21":     (5326, "Arty Bty (BM-21 Grad MLRS x 6)", BY, "exact"),
    "BY_URAGAN":   (5327, "Arty Bty (BM-27 Uragan MLRS x 6)", BY, "exact"),
    "BY_SMERCH":   (2118, "Arty Bty (BM-30 Smerch MLRS x 6)", BY, "exact, 70 km"),
    "BY_POLONEZ":  (4127, "Arty Bty (V-200 Polonez MLRS x 6)", BY, "exact ; A-200 193 km (4469 = variante avec missile chinois)"),
    "BY_ISKANDER": (3609, "SSM Bn (SS-26 Stone [9K720 Iskander-M] TEL)", BY, "exact, 8 9M723"),
    "BY_TOR_M2":   (3515, "SAM Plt (SA-15d Gauntlet [9K330 Tor-M2K])", BY, "exact"),
    "BY_BUK":      (492, "SAM Plt (SA-11 Gadfly [9K37 Buk-M1])", BY, "exact"),
    "BY_S400":     (5339, "SAM Bn (SA-21a/b Growler [S-400 Triumf])", BY, "exact"),
    "BY_S300PS":   (396, "SAM Bn (SA-10b Grumble [S-300PS])", BY, "exact"),
}

C = {k: v[0] for k, v in CATALOGUE_TERRE.items()}

# ---------------------------------------------------------------------------------------------------------------
# SOL_2026 : une ligne = une compagnie / batterie réelle (voir CONVENTIONS)
# ---------------------------------------------------------------------------------------------------------------
SOL_2026 = [
    # ======================= POLOGNE =======================
    # 16e division mécanisée (QG Elbląg 54,16 ; 19,40) : face à Kaliningrad, priorité des livraisons K2 et K9. M
    (PL, C["PL_K2"], "9e brigade de cavalerie blindée — chars K2 (1)", 54.38, 19.82, "blinde"),          # Braniewo, M
    (PL, C["PL_K2"], "9e brigade de cavalerie blindée — chars K2 (2)", 54.38, 19.84, "blinde"),          # M
    (PL, C["PL_PT91"], "9e brigade de cavalerie blindée — PT-91", 54.39, 19.80, "blinde"),               # F (passage au K2)
    (PL, C["PL_BWP1"], "9e brigade de cavalerie blindée — infanterie BWP-1", 54.37, 19.81, "mecanise"),   # M
    (PL, C["PL_K2"], "20e brigade mécanisée — chars K2", 54.25, 20.81, "blinde"),                       # Bartoszyce, M
    (PL, C["PL_BWP1"], "20e brigade mécanisée — infanterie (1)", 54.25, 20.83, "mecanise"),              # M
    (PL, C["PL_BWP1"], "20e brigade mécanisée — infanterie (2)", 54.26, 20.79, "mecanise"),              # M
    (PL, C["PL_ROSOMAK"], "15e brigade mécanisée — Rosomak (1)", 54.04, 21.77, "mecanise"),             # Giżycko, M
    (PL, C["PL_ROSOMAK"], "15e brigade mécanisée — Rosomak (2)", 54.05, 21.79, "mecanise"),             # M
    (PL, C["PL_PT91"], "15e brigade mécanisée — chars PT-91", 54.03, 21.75, "blinde"),                  # M
    (PL, C["PL_K9"], "11e régiment d'artillerie — K9PL (1)", 54.21, 21.74, "artillerie"),               # Węgorzewo, M
    (PL, C["PL_K9"], "11e régiment d'artillerie — K9PL (2)", 54.22, 21.76, "artillerie"),               # M
    (PL, C["PL_HOMAR_K"], "11e régiment d'artillerie — Homar-K", 54.20, 21.72, "lanceur"),              # F (affectation)
    (PL, C["PL_OSA"], "15e régiment antiaérien — Osa-AKM-P1", 54.31, 22.30, "sol-air"),                 # Gołdap, M
    (PL, C["PL_POPRAD"], "15e régiment antiaérien — Poprad", 54.31, 22.32, "sol-air"),                  # M
    # 1re division d'infanterie des Légions (Podlasie, la plus jeune, en montée en puissance). F
    (PL, C["PL_ROSOMAK"], "1re division des Légions — bataillon motorisé", 53.13, 23.16, "mecanise"),    # Białystok, F
    (PL, C["PL_K2"], "1re division des Légions — chars K2", 53.10, 21.57, "blinde"),                     # Ostrów Maz./Podlasie, F
    (PL, C["PL_KRAB"], "1re division des Légions — Krab", 53.14, 23.10, "artillerie"),                   # F
    # 18e division mécanisée (QG Siedlce 52,17 ; 22,29) : Abrams. M
    (PL, C["PL_M1A2C"], "1re brigade blindée — M1A2 SEPv3 (1)", 52.24, 21.22, "blinde"),                # Wesoła, M
    (PL, C["PL_M1A2C"], "1re brigade blindée — M1A2 SEPv3 (2)", 52.25, 21.24, "blinde"),                # M
    (PL, C["PL_M1A2C"], "1re brigade blindée — M1A2 SEPv3 (3)", 52.23, 21.20, "blinde"),                # M
    (PL, C["PL_BWP1"], "1re brigade blindée — infanterie", 52.24, 21.25, "mecanise"),                     # M
    (PL, C["PL_M1A1FEP"], "19e brigade mécanisée — M1A1 FEP", 51.25, 22.57, "blinde"),                  # Lublin, M
    (PL, C["PL_ROSOMAK"], "19e brigade mécanisée — Rosomak (1)", 51.24, 22.55, "mecanise"),             # M
    (PL, C["PL_ROSOMAK"], "19e brigade mécanisée — Rosomak (2)", 51.26, 22.59, "mecanise"),             # M
    (PL, C["PL_BWP1"], "21e brigade de chasseurs de Podhale", 50.04, 22.00, "mecanise"),                  # Rzeszów, M
    (PL, C["PL_K9"], "18e régiment d'artillerie — K9", 50.42, 21.75, "artillerie"),                     # Nowa Dęba, M
    (PL, C["PL_KRAB"], "18e régiment d'artillerie — Krab", 50.43, 21.77, "artillerie"),                 # M
    (PL, C["PL_HOMAR_K"], "18e régiment d'artillerie — Homar-K (1)", 50.41, 21.73, "lanceur"),          # M
    (PL, C["PL_HOMAR_K"], "18e régiment d'artillerie — Homar-K (2)", 50.40, 21.76, "lanceur"),          # M
    (PL, C["PL_HIMARS"], "HIMARS polonais (20 lanceurs)", 50.44, 21.74, "lanceur"),                     # garnison F
    # 11e division de cavalerie blindée (Żagań) et 12e division mécanisée (Szczecin) : réserve de l'ouest. M
    (PL, C["PL_LEO2PL"], "10e brigade de cavalerie blindée — Leopard 2PL", 51.53, 15.43, "blinde"),     # Świętoszów, M
    (PL, C["PL_LEO2A4"], "34e brigade de cavalerie blindée — Leopard 2A4", 51.62, 15.32, "blinde"),     # Żagań, M
    (PL, C["PL_ROSOMAK"], "17e brigade mécanisée — Rosomak", 52.45, 15.58, "mecanise"),                 # Międzyrzecz, M
    (PL, C["PL_KRAB"], "23e régiment d'artillerie — Krab", 51.27, 15.57, "artillerie"),                 # Bolesławiec, M
    (PL, C["PL_ROSOMAK"], "12e brigade mécanisée — Rosomak", 53.43, 14.55, "mecanise"),                 # Szczecin, M
    # Défense sol-air (DOUBLON_POSSIBLE avec les sites ImportExport)
    (PL, C["PL_PATRIOT"], "Wisła — 37e escadron Patriot (1)", 52.23, 20.24, "sol-air"),                 # Sochaczew, É
    (PL, C["PL_PATRIOT"], "Wisła — 37e escadron Patriot (2)", 52.20, 20.98, "sol-air"),                 # Varsovie, M
    (PL, C["PL_CAMM"], "Mała Narew / Pilica+ (CAMM)", 52.40, 20.90, "sol-air"),                          # M
    # Présence avancée de l'OTAN en Pologne (groupement américain, Bemowo Piskie / Orzysz). M
    (US, C["US_STRYKER"], "Groupement OTAN Pologne — escadron américain", 53.81, 21.98, "mecanise"),     # M
    (UK, 709, "Groupement OTAN Pologne — cavalerie légère britannique", 53.82, 22.00, "infanterie"),     # F (Jackal absent)
    # ======================= ÉTATS-UNIS (rotation blindée, V Corps avancé à Poznań) =======================
    (US, C["US_M1A2C"], "Brigade blindée américaine en rotation — Abrams (1)", 51.53, 15.40, "blinde"),   # Świętoszów, M
    (US, C["US_M1A2C"], "Brigade blindée américaine en rotation — Abrams (2)", 52.60, 15.50, "blinde"),   # Skwierzyna, M
    (US, C["US_M2A3"], "Brigade blindée américaine en rotation — Bradley (1)", 51.55, 15.38, "mecanise"), # M
    (US, C["US_M2A3"], "Brigade blindée américaine en rotation — Bradley (2)", 52.61, 15.52, "mecanise"), # M
    (US, C["US_M109A7"], "Brigade blindée américaine en rotation — M109A7", 51.27, 15.60, "artillerie"), # Bolesławiec, M
    (US, C["US_AVENGER"], "Brigade blindée américaine en rotation — Avenger", 51.54, 15.42, "sol-air"),  # F
    # ======================= LITUANIE =======================
    # Brigade mécanisée « Loup de fer » (QG Rukla 55,06 ; 24,40). M
    (LT, C["LT_VILKAS"], "Loup de fer — bataillon Algirdas, Vilkas (1)", 55.06, 24.40, "mecanise"),     # Rukla, M
    (LT, C["LT_VILKAS"], "Loup de fer — bataillon Algirdas, Vilkas (2)", 55.07, 24.42, "mecanise"),     # M
    (LT, C["LT_VILKAS"], "Loup de fer — bataillon de uhlans Birutė, Vilkas", 54.40, 24.05, "mecanise"), # Alytus, M
    (LT, C["LT_M113"], "Loup de fer — bataillon de hussards Mindaugas", 55.73, 24.36, "mecanise"),      # Panevėžys (F)
    (LT, C["LT_PZH2000"], "Loup de fer — bataillon d'artillerie, PzH 2000", 55.05, 24.38, "artillerie"), # Rukla, M
    (LT, C["LT_JAVELIN"], "Loup de fer — antichars Javelin", 55.06, 24.43, "infanterie"),                # M
    # Brigade d'infanterie motorisée « Žemaitija » (QG Klaipėda). M
    (LT, C["LT_JLTV"], "Žemaitija — bataillon Kęstutis", 55.25, 22.29, "infanterie"),                   # Tauragė, M
    (LT, C["LT_JLTV"], "Žemaitija — bataillon de dragons Butigeidis", 55.71, 21.13, "infanterie"),      # Klaipėda, M
    (LT, C["LT_M113"], "Žemaitija — appui M113", 55.70, 21.15, "mecanise"),                              # F
    # Brigade « Aukštaitija » (réserve, montée en puissance). F
    (LT, C["LT_JLTV"], "Aukštaitija — infanterie motorisée", 54.90, 23.90, "infanterie"),               # Kaunas (F)
    (LT, C["LT_NASAMS"], "NASAMS — défense de Vilnius (1)", 54.69, 25.28, "sol-air"),                   # M
    (LT, C["LT_NASAMS"], "NASAMS — défense de Vilnius (2)", 54.90, 23.90, "sol-air"),                   # F (2e site)
    # ======================= ALLEMAGNE : brigade blindée 45 « Litauen » (montée en puissance, cible 4 800 en 2027) ===
    (DE, C["DE_LEO2A6"], "Groupement OTAN Lituanie (Rukla) — Leopard 2", 55.06, 24.36, "blinde"),         # M
    (DE, C["DE_PUMA"], "Groupement OTAN Lituanie (Rukla) — Puma", 55.05, 24.35, "mecanise"),             # M
    (DE, C["DE_LEO2A6"], "45e brigade blindée — Panzerbataillon 203", 54.39, 25.11, "blinde"),          # Rūdninkai, F (arrivée 2026)
    (DE, C["DE_PUMA"], "45e brigade blindée — Panzergrenadierbataillon 122", 54.40, 25.13, "mecanise"),  # Rūdninkai, F
    (DE, C["DE_PZH2000"], "45e brigade blindée — artillerie PzH 2000", 54.38, 25.10, "artillerie"),      # F (en formation)
    # ======================= LETTONIE =======================
    (LV, C["LV_PATRIA"], "Brigade mécanisée lettone — Patria 6x6 (1)", 57.08, 24.32, "mecanise"),       # Ādaži, M
    (LV, C["LV_PATRIA"], "Brigade mécanisée lettone — Patria 6x6 (2)", 56.95, 24.11, "mecanise"),       # Riga, M
    (LV, C["LV_M109"], "Brigade mécanisée lettone — artillerie M109A5Ö", 57.09, 24.34, "artillerie"),    # F
    (LV, C["LV_PATRIA"], "2e brigade lettone (Latgale) — en formation", 56.51, 27.33, "mecanise"),      # Rēzekne, F
    (LV, C["LV_RBS70"], "Défense antiaérienne lettone — RBS 70 NG", 57.07, 24.30, "sol-air"),           # M
    # Brigade multinationale Lettonie (Canada, Ādaži)
    (CA, C["CA_LEO2A4M"], "Brigade multinationale Lettonie — Leopard 2A4M canadiens", 57.08, 24.33, "blinde"),  # M
    (CA, C["CA_LAV6"], "Brigade multinationale Lettonie — LAV 6 (1)", 57.07, 24.34, "mecanise"),        # M
    (CA, C["CA_LAV6"], "Brigade multinationale Lettonie — LAV 6 (2)", 57.09, 24.31, "mecanise"),        # M
    (CA, C["CA_M777"], "Brigade multinationale Lettonie — M777", 57.08, 24.35, "artillerie"),           # M
    (SE, C["SE_CV9040"], "Brigade multinationale Lettonie — bataillon suédois CV90", 57.06, 24.33, "mecanise"),  # M
    # ======================= ESTONIE =======================
    (EE, C["EE_CV90"], "1re brigade d'infanterie — bataillon d'éclaireurs CV90 (1)", 59.26, 25.96, "mecanise"),  # Tapa, É
    (EE, C["EE_CV90"], "1re brigade d'infanterie — bataillon d'éclaireurs CV90 (2)", 59.27, 25.98, "mecanise"),  # É
    (EE, C["EE_XA188"], "1re brigade d'infanterie — bataillon Kalev", 59.35, 24.05, "mecanise"),        # Paldiski, M
    (EE, C["EE_XA188"], "1re brigade d'infanterie — bataillon Viru", 59.36, 27.41, "mecanise"),         # Jõhvi, M
    (EE, C["EE_K9"], "Bataillon d'artillerie — K9 Kõu (1)", 59.25, 25.94, "artillerie"),                # Tapa, É
    (EE, C["EE_K9"], "Bataillon d'artillerie — K9 Kõu (2)", 59.24, 25.97, "artillerie"),                # É
    (EE, C["EE_HIMARS"], "HIMARS estoniens (6)", 59.25, 25.92, "lanceur"),                               # É (garnison M)
    (EE, C["EE_XA188"], "2e brigade d'infanterie — bataillon Kuperjanov", 57.84, 27.02, "mecanise"),   # Võru, M
    (EE, C["EE_XA188"], "2e brigade d'infanterie — QG Luunja", 58.36, 26.88, "mecanise"),              # M
    (EE, C["EE_IRIST"], "IRIS-T SLM estonien (1 unité de tir)", 59.26, 24.21, "sol-air"),               # Ämari, É (base : Hypothetical)
    (EE, C["EE_MISTRAL"], "Défense antiaérienne — Mistral", 59.26, 25.95, "sol-air"),                   # M
    # Groupement OTAN Estonie (Royaume-Uni + France, Tapa)
    (UK, C["UK_CR2"], "Groupement OTAN Estonie — Challenger 2", 59.26, 25.99, "blinde"),                # M
    (UK, C["UK_WARRIOR"], "Groupement OTAN Estonie — Warrior", 59.27, 26.00, "mecanise"),               # M
    (UK, C["UK_ARCHER"], "Groupement OTAN Estonie — artillerie", 59.25, 26.01, "artillerie"),           # F
    (FR, C["FR_VBCI"], "Groupement OTAN Estonie — contingent français", 59.27, 25.95, "mecanise"),      # M (Leclerc selon rotation)
    # ======================= FINLANDE (sud-est, Carélie) =======================
    (FI, C["FI_LEO2A6"], "Brigade blindée — Leopard 2A6 (1)", 61.03, 24.37, "blinde"),                   # Parolannummi, É
    (FI, C["FI_LEO2A6"], "Brigade blindée — Leopard 2A6 (2)", 61.04, 24.39, "blinde"),                   # É
    (FI, C["FI_CV9030"], "Brigade blindée — CV9030", 61.02, 24.36, "mecanise"),                          # É (SUBST)
    (FI, C["FI_K9"], "Brigade blindée — K9 Moukari", 61.03, 24.40, "artillerie"),                        # M
    (FI, C["FI_LEO2A4"], "Brigade de Carélie — Leopard 2A4", 60.87, 26.88, "blinde"),                    # Vekaranjärvi, M
    (FI, C["FI_CV9030"], "Brigade de Carélie — CV9030", 60.88, 26.90, "mecanise"),                       # M
    (FI, C["FI_K9"], "Brigade de Carélie — K9 Moukari (1)", 60.86, 26.86, "artillerie"),                 # É
    (FI, C["FI_K9"], "Brigade de Carélie — K9 Moukari (2)", 60.87, 26.92, "artillerie"),                 # É
    (FI, C["FI_M270"], "Lance-roquettes M270 finlandais", 61.84, 22.47, "lanceur"),                      # Niinisalo, M
    (FI, C["FI_NASAMS"], "NASAMS — défense d'Helsinki", 60.25, 24.95, "sol-air"),                        # M
    # ======================= SUÈDE (Gotland) =======================
    (SE, C["SE_STRV122"], "Régiment P 18 Gotland — Strv 122", 57.64, 18.30, "blinde"),                  # Visby, É
    (SE, C["SE_CV9040"], "Régiment P 18 Gotland — CV90", 57.63, 18.32, "mecanise"),                      # É
    (SE, C["SE_IRIST_SLS"], "Gotland — défense antiaérienne IRIS-T SLS", 57.66, 18.35, "sol-air"),     # M
    # ======================= RUSSIE : KALININGRAD (11e corps d'armée) =======================
    # Ukraine : 18e division, 79e régiment, 7e régiment, 336e brigade d'infanterie de marine engagés depuis 2022
    # (Kharkiv, Koupiansk, Koursk 2024-2025) avec de lourdes pertes ; ce qui reste en garnison est creux. F-M
    (RU, C["RU_T72B3"], "18e division de la Garde — 11e régiment de chars", 54.59, 22.20, "blinde"),    # Goussev, F
    (RU, C["RU_BMP2"], "18e division — 79e régiment motorisé", 54.60, 22.18, "mecanise"),                # Goussev, F
    (RU, C["RU_BTR82A"], "18e division — 275e régiment motorisé", 55.08, 21.89, "mecanise"),             # Sovetsk, F
    (RU, C["RU_BMP2"], "18e division — 280e régiment motorisé", 54.63, 21.81, "mecanise"),               # Tcherniakhovsk, F
    (RU, C["RU_2S19"], "18e division — artillerie automotrice", 54.58, 22.22, "artillerie"),            # F
    (RU, C["RU_BTR82A"], "7e régiment motorisé de la Garde", 54.72, 20.45, "mecanise"),                  # Kaliningrad, F
    (RU, C["RU_2S19"], "244e brigade d'artillerie — Msta-S", 54.75, 20.56, "artillerie"),              # Kaliningrad, M
    (RU, C["RU_TORNADO_G"], "244e brigade d'artillerie — Tornado-G", 54.76, 20.58, "artillerie"),      # M
    (RU, C["RU_URAGAN"], "244e brigade d'artillerie — Ouragan", 54.74, 20.54, "artillerie"),            # F
    (RU, C["RU_ISKANDER"], "152e brigade de missiles de la Garde — Iskander", 54.65, 21.83, "lanceur"), # Tcherniakhovsk, M (a tiré sur l'Ukraine)
    (RU, C["RU_BTR82A"], "336e brigade d'infanterie de marine", 54.65, 19.91, "mecanise"),              # Baltiïsk, F (saignée en Ukraine)
    (RU, C["RU_TOR_M2"], "11e corps — défense antiaérienne Tor-M2", 54.60, 22.18, "sol-air"),           # F
    (RU, C["RU_BUK_M3"], "11e corps — défense antiaérienne Buk", 54.72, 20.40, "sol-air"),              # F
    (RU, C["RU_S400"], "183e régiment antiaérien — S-400 (DOUBLON_POSSIBLE)", 54.68, 21.01, "sol-air"), # Gvardeïsk, F (matériel parti en 2023 ?)
    # ======================= RUSSIE : DISTRICT DE LÉNINGRAD =======================
    # Ukraine : 138e et 25e brigades (devenues divisions 69e et 68e selon plusieurs sources, F), 76e division
    # d'assaut aérien : engagées en Ukraine / Koursk. Restent en garnison : dépôts, formation, reconstitution.
    (RU, C["RU_T72B3"], "6e armée — 138e brigade / 69e division, reconstitution", 60.35, 29.03, "blinde"),   # Kamenka, F
    (RU, C["RU_BMP2M"], "6e armée — 138e brigade / 69e division, infanterie", 60.36, 29.05, "mecanise"),     # F
    (RU, C["RU_BMP2"], "6e armée — 25e brigade / 68e division, reconstitution", 58.37, 28.95, "mecanise"),   # Vladimirski Laguer, F
    (RU, C["RU_ISKANDER"], "26e brigade de missiles — Iskander", 58.74, 29.85, "lanceur"),                   # Louga, M (frappée par drones 2025-2026)
    (RU, C["RU_MSTA_B"], "9e brigade d'artillerie", 58.73, 29.83, "artillerie"),                           # Louga, F
    (RU, C["RU_TORNADO_S"], "9e brigade d'artillerie — Tornado-S", 58.72, 29.87, "lanceur"),                # F
    (RU, C["RU_BUK_M3"], "5e brigade antiaérienne — Buk-M3", 60.25, 30.40, "sol-air"),                      # Lekhtoussi, F
    (RU, C["RU_BMD4M"], "76e division d'assaut aérien — dépôt de Pskov", 57.82, 28.33, "mecanise"),         # F
    (RU, C["RU_NONA"], "76e division d'assaut aérien — artillerie Nona-S", 57.80, 28.36, "artillerie"),     # F
    # ======================= BIÉLORUSSIE =======================
    # Armée de terre ≈ 45 000 à 50 000 hommes, unités de temps de paix incomplètes ; rien d'engagé en Ukraine. M
    (BY, C["BY_T72B3"], "6e brigade mécanisée de la Garde — chars", 53.68, 23.83, "blinde"),            # Hrodna, M
    (BY, C["BY_BMP2"], "6e brigade mécanisée de la Garde — infanterie (1)", 53.69, 23.85, "mecanise"),  # M
    (BY, C["BY_BTR82A"], "6e brigade mécanisée de la Garde — infanterie (2)", 53.67, 23.81, "mecanise"), # M
    (BY, C["BY_2S3"], "6e brigade mécanisée de la Garde — artillerie", 53.66, 23.86, "artillerie"),     # M
    (BY, C["BY_T72B3"], "11e brigade mécanisée de la Garde — chars", 53.09, 25.32, "blinde"),           # Slonim, M
    (BY, C["BY_BMP2"], "11e brigade mécanisée de la Garde — infanterie (1)", 53.10, 25.34, "mecanise"), # M
    (BY, C["BY_BMP2"], "11e brigade mécanisée de la Garde — infanterie (2)", 53.08, 25.30, "mecanise"), # M
    (BY, C["BY_2S1"], "11e brigade mécanisée de la Garde — artillerie", 53.11, 25.31, "artillerie"),    # M
    (BY, C["BY_2S3"], "111e brigade d'artillerie", 52.10, 23.70, "artillerie"),                          # Brest, M
    (BY, C["BY_URAGAN"], "111e brigade d'artillerie — Ouragan", 52.11, 23.72, "artillerie"),             # F
    (BY, C["BY_BTR80"], "38e brigade d'assaut aérien de la Garde (1)", 52.08, 23.66, "mecanise"),        # Brest, M
    (BY, C["BY_BTR80"], "38e brigade d'assaut aérien de la Garde (2)", 52.09, 23.68, "mecanise"),        # M
    (BY, C["BY_T72B3"], "19e brigade mécanisée de la Garde — chars", 54.01, 27.27, "blinde"),            # Zaslawye, M
    (BY, C["BY_BMP2"], "19e brigade mécanisée de la Garde — infanterie", 54.02, 27.29, "mecanise"),      # M
    (BY, C["BY_T72B"], "120e brigade mécanisée de la Garde — chars", 53.95, 27.68, "blinde"),            # Minsk (Ourouchtchie), M
    (BY, C["BY_BTR82A"], "120e brigade mécanisée de la Garde — infanterie", 53.96, 27.70, "mecanise"),   # M
    (BY, C["BY_2S3"], "231e brigade d'artillerie", 54.23, 28.50, "artillerie"),                          # Barysaw, M
    (BY, C["BY_BM21"], "231e brigade d'artillerie — Grad", 54.24, 28.52, "artillerie"),                  # M
    (BY, C["BY_BTR80"], "103e brigade aéroportée de la Garde", 55.19, 30.20, "mecanise"),                # Vitebsk, M
    (BY, C["BY_POLONEZ"], "336e brigade d'artillerie à roquettes — Polonez", 53.30, 28.64, "lanceur"),  # Asipovitchy, M
    (BY, C["BY_SMERCH"], "336e brigade d'artillerie à roquettes — Smerch", 53.31, 28.66, "lanceur"),    # M
    (BY, C["BY_ISKANDER"], "465e brigade de missiles — Iskander", 53.30, 28.62, "lanceur"),              # Asipovitchy, M
    (BY, C["BY_TOR_M2"], "Défense antiaérienne — Tor-M2", 53.13, 26.01, "sol-air"),                      # Baranavitchy, M
    (BY, C["BY_BUK"], "120e brigade antiaérienne — Buk", 53.12, 26.03, "sol-air"),                       # M
    (BY, C["BY_S400"], "S-400 biélorusse (DOUBLON_POSSIBLE)", 53.68, 23.90, "sol-air"),                  # site F
    (BY, C["BY_S300PS"], "15e brigade antiaérienne — S-300PS", 53.75, 27.33, "sol-air"),                # Fanipal, M
]

ROLES_TERRE = {
    # blindés
    3516: "blinde", 4881: "blinde", 4592: "blinde", 2340: "blinde", 2333: "blinde", 4726: "blinde", 2341: "blinde",
    3517: "blinde", 1930: "blinde", 2380: "blinde", 1928: "blinde", 2054: "blinde", 3848: "blinde", 5010: "blinde",
    532: "blinde", 1918: "blinde", 2106: "blinde", 5320: "blinde", 5319: "blinde", 5264: "blinde", 2111: "blinde",
    # mécanisés
    3043: "mecanise", 2043: "mecanise", 2330: "mecanise", 5081: "mecanise", 5098: "mecanise", 3832: "mecanise",
    2784: "mecanise", 2263: "mecanise", 2396: "mecanise", 2056: "mecanise", 5096: "mecanise", 1993: "mecanise",
    4936: "mecanise", 2045: "mecanise", 2218: "mecanise", 2860: "mecanise", 5316: "mecanise", 5315: "mecanise",
    5324: "mecanise",
    # infanterie
    5086: "infanterie", 5087: "infanterie", 709: "infanterie",
    # artillerie (tubes et roquettes courtes)
    4652: "artillerie", 2048: "artillerie", 2088: "artillerie", 5088: "artillerie", 3550: "artillerie",
    4646: "artillerie", 2929: "artillerie", 2133: "artillerie", 3228: "artillerie", 4462: "artillerie",
    2383: "artillerie", 3548: "artillerie", 2297: "artillerie", 1953: "artillerie", 4218: "artillerie",
    1976: "artillerie", 2816: "artillerie", 1969: "artillerie", 2071: "artillerie", 5321: "artillerie",
    5322: "artillerie", 5326: "artillerie", 5327: "artillerie", 4651: "artillerie",
    # lanceurs (feux longue portée)
    5244: "lanceur", 3659: "lanceur", 4650: "lanceur", 4649: "lanceur", 4647: "lanceur", 5245: "lanceur",
    3663: "lanceur", 3664: "lanceur", 2556: "lanceur", 254: "lanceur", 5167: "lanceur", 4853: "lanceur",
    3609: "lanceur", 4127: "lanceur", 4469: "lanceur", 2118: "lanceur", 2117: "lanceur",
    # sol-air
    3985: "sol-air", 3527: "sol-air", 3653: "sol-air", 3269: "sol-air", 5268: "sol-air", 5055: "sol-air",
    3521: "sol-air", 4274: "sol-air", 286: "sol-air", 557: "sol-air", 2011: "sol-air", 2159: "sol-air",
    2162: "sol-air", 2276: "sol-air", 3250: "sol-air", 1937: "sol-air", 3515: "sol-air", 492: "sol-air",
    5339: "sol-air", 396: "sol-air",
}

# ---------------------------------------------------------------------------------------------------------------
# STOCKS_MUNITIONS : (pays_cmo, motif regex du nom d'arme DB3000) -> (stock_2026, production_par_mois, confiance, source)
# stock_2026 = estimation centrale du stock NATIONAL utilisable en 2026 (None = inconnu) ; production_par_mois = sortie
# d'usine attribuable à ce pays (commandes en cours / mois) ; pour les États-Unis et la Russie = production nationale.
# Détails, fourchettes et calculs : terre_munitions_2026.md. Confiance É / M / F.
# ---------------------------------------------------------------------------------------------------------------
STOCKS_MUNITIONS = {
    # NB : guerre États-Unis contre Iran (depuis le 28/02/2026, reprise en 07/2026) : stocks américains au cessez-le-feu
    # d'avril 2026 = PLAFONDS ; livraisons aux alliés probablement retardées. Source principale : CSIS 04/2026
    # (https://csis-website-prod.s3.amazonaws.com/s3fs-public/2026-04/260424_Cancian_Park_Last_Rounds.pdf).
    # --- frappe aérienne OTAN
    (PL, r"AGM-158A JASSM\b"): (40, 0, "É", "commande 2014 ; https://www.flightglobal.com/defence/poland-signs-deal-to-acquire-jassm-er-cruise-missiles/158513.article"),
    (PL, r"AGM-158B(-2)? JASSM-ER"): (110, 5, "M", "70 (2016) + premiers lots du contrat 2024 (≈ 300-350 missiles, livrés 2026-2030, retard probable) ; stock 70-150 ; https://www.flightglobal.com/defence/poland-signs-deal-to-acquire-jassm-er-cruise-missiles/158513.article"),
    (FI, r"AGM-158A JASSM\b"): (70, 0, "M", "≈ 70 JASSM-A sur Hornet (2012) ; https://theaviationist.com/2024/06/01/finland-to-acquire-agm-158b-jassm-er-for-its-f-35as/"),
    (FI, r"AGM-158B(-2)? JASSM-ER"): (0, 0, "M", "200 pour F-35, livrés avec les avions (après 2026) ; https://theaviationist.com/2024/06/01/finland-to-acquire-agm-158b-jassm-er-for-its-f-35as/"),
    (DE, r"AGM-158B(-2)? JASSM-ER"): (0, 0, "M", "75 demandés en 2022, reportés ; https://www.grosswald.org/baainbw-luftwaffe-f-35a-enters-service-without-jassm-er-75-missiles-postponed/"),
    (US, r"AGM-158[AB](-2)? JASSM"): (3300, 70, "M", "4 400 avant guerre - >1 100 tirés sur l'Iran + livraisons ; NYT : peut-être 1 100-1 500 ER seulement ; cadence max 2026 860/an ; CSIS 04/2026"),
    (DE, r"Taurus KEPD 350"): (200, 0, "M", "600 achetés, 150 à 300 en état ; Taurus Neo (600) livré à partir de 2029 ; https://en.wikipedia.org/wiki/Taurus_KEPD_350"),
    (UK, r"^Storm Shadow"): (None, None, "F", "700-1 000 achetés, cessions à l'Ukraine non publiques, relance 2025 ; https://en.wikipedia.org/wiki/Storm_Shadow"),
    (FR, r"^SCALP EG"): (None, None, "F", "500 commandés (1998), cessions NP ; https://en.wikipedia.org/wiki/Storm_Shadow"),
    (US, r"[RU]GM-109[EHJ]"): (2100, 20, "M", "3 100 avant guerre - >1 000 tirés + ≈ 200 livrés (ex. 2026) ; contrat 08/2026 pour >1 000/an à terme ; https://theaviationist.com/2026/08/18/rtx-contract-accelerate-tomahawk-production/"),
    # --- antiradar
    (PL, r"AGM-88G AARGM-ER"): (0, 0, "É", "≈ 200 commandés 01/2025, livrés 2029-2035 ; https://breakingdefense.com/2025/01/poland-adds-long-range-strike-to-its-f-35-fleet-with-aargm-er-missiles/"),
    (FI, r"AGM-88G AARGM-ER"): (0, 0, "M", "150 autorisés, achat 10/2024, livraison NP ; https://thedefensepost.com/2024/10/29/finland-acquire-aargm-er/"),
    (DE, r"AGM-88E AARGM"): (None, 0, "M", "contrat 2021, tir d'essai 04/2025, quantité NP ; https://www.twz.com/electronic-warfare-typhoon-ek-fighter-to-join-german-air-force"),
    # --- antinavire / côtier
    (PL, r"NSM Block 1"): (120, 3, "F", "50 (1er escadron) + 2e escadron + premiers lots du contrat 2023 (« plusieurs centaines », 2026-2032) ; https://www.iiss.org/online-analysis/missile-dialogue-initiative/2023/09/poland-to-acquire-several-hundred-naval-strike-missiles/"),
    (LV, r"NSM Block 1"): (None, 0, "M", "1 batterie, contrat 03/2026, achèvement 2030 ; https://thedefensepost.com/2026/03/16/naval-strike-missile-latvia/"),
    (DE, r"NSM Block 1"): (None, 0, "F", "achat conjoint avec la Norvège 2021, quantité NP ; https://euro-sd.com/2021/07/news/sea/23429/nsm/"),
    (PL, r"RB 15|RBS 15"): (None, 0, "F", "Orkan, contrat 2006, quantité NP ; https://en.wikipedia.org/wiki/RBS_15"),
    (SE, r"RB 15|Gungnir"): (None, None, "F", "Gungnir, NP ; https://en.wikipedia.org/wiki/RBS_15"),
    (DE, r"RB 15"): (None, 0, "F", "corvettes K130, NP ; https://en.wikipedia.org/wiki/RBS_15"),
    # --- défense antimissile
    (PL, r"PAC-3 MSE"): (208, 0, "É", "phase I livrée ; 644 commandés en 2023, livraisons 2026-27 à 2029 probablement retardées ; https://defence24.com/defence-policy/has-poland-supplied-ukraine-with-patriot-missiles-the-ministry-of-national-defence-responds"),
    (DE, r"PAC-3 MSE"): (None, 0, "F", "120 commandés 12/2024 livrés 2028-2029 ; stock actuel NP ; https://defence-industry.eu/germany-orders-120-pac-3-mse-interceptors-for-patriot-air-and-missile-defence-system/"),
    (DE, r"PAC-2 GEM"): (None, 0, "F", "part allemande des 1 000 GEM-T groupés (NSPA) NP ; COMLOG démarre fin 2026 ; https://en.defence-ua.com/news/germany_to_fund_hundreds_of_gem_t_missiles_for_ukraines_patriot_production_timeline_raises_questions-18175.html"),
    (SE, r"PAC-3 MSE"): (None, 0, "F", "200 autorisés (2018), livrés NP ; https://thedefensepost.com/2024/11/18/sweden-patriot-gem-missiles/"),
    (SE, r"PAC-2 GEM"): (None, 0, "F", "100 autorisés (2018) + part NSPA ; https://thedefensepost.com/2024/11/18/sweden-patriot-gem-missiles/"),
    (US, r"PAC-3"): (1350, 52, "M", "2 330 avant guerre - 1 060-1 430 tirés + ≈ 270 livrés ; industrie 620 en 2025 vers ≈ 2 000/an (accord 01/2026) ; https://news.lockheedmartin.com/2026-01-06-Lockheed-Martin-and-Department-of-War-Advance-Landmark-Acquisition-Transformation-to-Accelerate-PAC-3-R-MSE-Production"),
    # --- air-air et sol-air
    (US, r"AIM-120"): (4300, 160, "M", "≈ 4 000-4 600 (graphique CSIS) ; cible >= 1 900/an, contrat 28/09/2026 ; https://breakingdefense.com/2026/09/raytheon-nets-potential-20-7-billion-amraam-deal/"),
    (PL, r"AIM-120C|AIM-120D"): (None, 0, "F", "stock C-5/C-7 NP ; 400 D-3 contractés 11/2025, livrés 2030-31 ; https://theaviationist.com/2025/11/28/aim-120d-3-poland-contract/"),
    (FI, r"AIM-120C|AIM-120D|MIM-120C-7"): (None, 0, "F", "stock C-7 NP ; 405 D-3 achetés 12/2025 ; https://theaviationist.com/2025/12/19/finland-aim-120d-3-amraam-f-35/"),
    (DE, r"AIM-120"): (None, 0, "F", "105 C commandés ; 1 074 C-8 et 400 D-3 autorisés ; https://euro-sd.com/2025/09/major-news/46901/amraam-fms-for-germanys-f-35s/"),
    (LT, r"MIM-120C-7 NASAMS"): (None, 0, "F", "36 C-8 autorisés 10/2023 + stock antérieur NP ; https://militarnyi.com/en/news/lithuania-to-purchase-amraam-missiles-for-an-estimated-cost-of-100-million/"),
    (DE, r"Meteor"): (None, None, "F", "NP ; MBDA +40 % en 2026 ; https://www.defensenews.com/global/europe/2026/03/26/mbda-to-double-aster-air-defense-missile-output-in-2026/"),
    (SE, r"Meteor"): (None, None, "F", "NP ; https://www.defensenews.com/global/europe/2026/03/26/mbda-to-double-aster-air-defense-missile-output-in-2026/"),
    (DE, r"IRIS-T"): (None, 75, "M", "Diehl 800-1 000/an fin 2025 (tous clients, priorité Ukraine), objectif 2 000/an ; https://militarnyi.com/en/news/iris-t-manufacturer-launches-new-production-facility-and-plans-to-produce-10-air-defense-systems-in-2026/"),
    # --- feux sol-sol OTAN
    (PL, r"ATACMS"): (30, 0, "É", "30 M57 (2019) ; Homar-A (45 ATACMS, GMLRS) bloqué 03/2026 ; https://defence24.com/industry/polish-himars-at-an-impasse-what-is-the-munitions-production-roadblock"),
    (EE, r"ATACMS"): (18, 0, "M", "18 livrés 2025 avec 6 HIMARS ; 182 autorisés au total ; https://militarnyi.com/en/news/estonia-expands-himars-fleet-adds-atacms-missiles/"),
    (LT, r"ATACMS"): (0, 0, "M", "18 M57 avec les 8 HIMARS livrés fin 2026 ; https://www.army-technology.com/news/baltics-atacms-production-underway-after-earlier-us-himars-deals/"),
    (LV, r"ATACMS"): (0, 0, "M", "10 autorisés, HIMARS livrés 2027 ; https://media.defense.gov/2024/Dec/09/2003604093/-1/-1/0/PRESS%20RELEASE%20-%20LATVIA%2023-70%20CN.PDF"),
    (US, r"ATACMS"): (800, 0, "M", "jusqu'à ≈ 800 restants ; fin de chaîne vers 2027 ; https://www.defensenews.com/land/2025/10/13/army-accelerates-prsm-output-as-atacms-nears-sunset/"),
    (US, r"PrSM"): (100, 35, "M", "≈ 100 livrés fin 2025, 40-70 tirés sur l'Iran ; objectif 400 puis 550/an ; https://www.lockheedmartin.com/en-us/news/features/2026/lockheed-martin-and-the-us-department-of-war-further-expand-prsm-production.html"),
    (US, r"M3[01]A?1? GMLRS|GMLRS ER"): (None, 1170, "É", "14 000/an atteint, 19 000 visé en 2028 ; https://militarnyi.com/en/news/u-s-to-boost-gmlrs-missile-production-for-himars-to-19-000-per-year/"),
    (EE, r"M3[01]A?1? GMLRS"): (None, 0, "F", "856 conteneurs autorisés au total, livré NP ; https://milmag.pl/en/estonia-ordered-additional-m142-himars-launchers/"),
    (LT, r"M3[01]A?1? GMLRS"): (0, 0, "M", "4 x 36 conteneurs avec le 1er lot (fin 2026) ; https://www.army-technology.com/news/baltics-atacms-production-underway-after-earlier-us-himars-deals/"),
    (FI, r"M3[01]A?1? GMLRS|GMLRS ER"): (210, 0, "M", "35 conteneurs GMLRS-ER autorisés 02/2022 (210 roquettes) + autre lot NP ; https://www.shephardmedia.com/news/landwarfareintl/finland-set-obtain-extended-range-gmlrs/"),
    (PL, r"239mm HE Rocket"): (None, None, "F", "CGR-080 « plusieurs milliers » (2024), 10 000 de plus (12/2025, dès 2030) ; CTM-290 NP et absent de DB3000 ; https://militarnyi.com/en/news/poland-ordered-a-batch-of-homar-k-mrls-and-ballistic-missiles/"),
    # --- Russie (HUR, partie au conflit ; la production est tirée presque aussitôt)
    (RU, r"Kh-101"): (100, 80, "M", "≈ 100 en 08/2026 ; 87 produits en 07/2026, plan 72 ; https://www.pravda.com.ua/eng/news/2026/08/20/8049494/"),
    (RU, r"Kh-555"): (0, 0, "F", "presque épuisé, plus produit ; https://www.newsweek.com/russia-missiles-running-out-kh-555-ukraine-1771174"),
    (RU, r"3M14 Kalibr"): (450, 28, "M", ">450 ; 29 en 07/2026 ; https://www.pravda.com.ua/eng/news/2026/08/20/8049494/"),
    (RU, r"9M723"): (130, 62, "M", "≈ 130 au 05/08/2026 ; 65 en 07/2026 ; https://newsukraine.rbc.ua/news/russia-ramps-up-missile-production-ukraine-1786344941.html"),
    (RU, r"9M728|9M729"): (None, 15, "F", "10-20/mois (06/2026) ; https://en.interfax.com.ua/news/general/1176200.html"),
    (RU, r"Kh-47M2 Kinzhal, 700kg"): (50, 0, "M", "≈ 50 ; production suspendue depuis 04/2026 ; https://rubryka.com/en/2026/08/20/raketnyj-arsenal-rf/"),
    (RU, r"3M22 Zircon"): (120, 3, "M", "30-36/an ; https://kyivindependent.com/how-many-more-missiles-does-russia-have-and-can-it-keep-firing-them/"),
    (RU, r"P-800 Onyx"): (600, 5, "M", "60/an ; https://kyivindependent.com/how-many-more-missiles-does-russia-have-and-can-it-keep-firing-them/"),
    (RU, r"Kh-31P|Kh-59"): (None, None, "F", "Kh-29/31/35/58/59 ensemble <= 2 600 (surtout Kh-29) ; Kh-59 freiné ; https://www.pravda.com.ua/eng/news/2024/01/15/7437286/"),
    (RU, r"KAB-|UPAB|UMPK"): (None, 8500, "M", "8 766 larguées en 08/2026 (≈ 283/jour) ; https://www.defenceukraine.com/en/insights/russian-fab-umpk-glide-bomb-2026/"),
    (RU, r"RM-48U"): (400, 45, "F", "48N6 en mode sol-sol ; https://www.kyivpost.com/post/80652"),
    (RU, r"48N6|40N6|9M96"): (None, None, "F", "NP par type ; Almaz-Antey dit avoir doublé sa production en 2025 ; https://voennoedelo.com/en/posts/id1307-russia-doubles-s-400-and-s-350-missile-production-in-2025"),
    (RU, r"Shahed-136"): (None, 2800, "M", "≈ 2 800 Geran-2/mois + ≈ 3 000 Geran-4/5 (08/2026) ; https://militarnyi.com/en/news/production-of-the-geran-4-5-jet-drones-has-surpassed-that-of-the-geran-2/"),
    (RU, r"Geran-5"): (None, 3000, "M", "drones à réaction Geran-4/5 ; https://militarnyi.com/en/news/production-of-the-geran-4-5-jet-drones-has-surpassed-that-of-the-geran-2/"),
    # --- Biélorussie
    (BY, r"9M723"): (25, 0, "F", "≈ 4 lanceurs et ≈ 25 missiles (2022), non vérifié ; https://en.wikipedia.org/wiki/List_of_equipment_of_the_Armed_Forces_of_Belarus"),
    (BY, r"A-[23]00 301mm"): (None, None, "F", "≈ 12 lanceurs Polonez, roquettes NP ; https://en.wikipedia.org/wiki/336th_Rocket_Artillery_Brigade"),
    (BY, r"48N6|40N6"): (None, 0, "F", "S-400 livré en 2022, NP ; https://www.defensenews.com/global/europe/2022/12/20/belarus-says-its-russian-s-400-iskander-missiles-enter-combat-duty/"),
}


if __name__ == "__main__":
    from collections import Counter
    print(len(SOL_2026), "unités ;", Counter(p for p, *_ in SOL_2026))
    assert all(r in {"blinde", "mecanise", "infanterie", "artillerie", "lanceur", "sol-air"} for *_, r in SOL_2026)
    assert all(d in ROLES_TERRE or d == 709 for _, d, *_ in SOL_2026), "dbid sans rôle"
    assert all(ROLES_TERRE.get(d, r) == r for _, d, _, _, _, r in SOL_2026), "rôle incohérent"
