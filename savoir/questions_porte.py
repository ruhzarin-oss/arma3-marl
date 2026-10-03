#!/usr/bin/env python3
"""Les QUESTIONS DE LA PORTE ( écrites le 03/10/2026 AVANT toute mesure de l'index ) : des questions en français dont la
réponse est connue et vérifiable ( base DB3000, manuel, atelier ), chacune liée aux fiches qui DOIVENT être retrouvées.
Elles serviront plus tard de données d'entraînement ( LoRA ) : la réponse attendue est écrite en clair.

Règles d'or ( « attendues ») : une liste d'identifiants explicites et / ou des règles résolues sur fiches.jsonl :
  titre   : expression régulière sur le titre ( avec « type » pour restreindre ) ;
  manuel  : ( sections, regex sur le texte anglais ) des passages traduits du manuel ;
  carte   : regex sur le TITRE des fiches de la carte des mécanismes ( ids meca-<carte>-NNN ).
Une question est réussie si AU MOINS UNE fiche attendue est dans les k premiers résultats.

    .venv312/bin/python savoir/questions_porte.py   ->   /mnt/data/hmt/etat/cmo_savoir/porte_questions.jsonl
"""
import json
import os
import re
import sys

DOSSIER = "/mnt/data/hmt/etat/cmo_savoir"


def Q(qid, cat, question, reponse, ids=(), titre=None, type=None, manuel=None, carte=None):
    return {"id": qid, "categorie": cat, "question": question, "reponse": reponse, "regle": {
        "ids": list(ids), "titre": titre, "type": type, "manuel": manuel, "carte": carte}}


QUESTIONS = [
    # ------------------------------------------------------------------ ARMES ( DB3000 )
    Q("a01", "arme", "Jusqu'à quelle distance le missile air-air Meteor peut-il engager un avion ?",
      "100 nm ( 185 km ) contre aéronefs, PoK de base 95 %.", ids=["arme-961", "arme-371"]),
    Q("a02", "arme", "Quelle est la portée maximale de l'AIM-120D contre une cible aérienne ?",
      "86,4 nm ( environ 160 km ).", ids=["arme-51"]),
    Q("a03", "arme", "Quelle allonge a le R-37M russe, le missile à très longue portée des MiG-31 ?",
      "162 nm ( 300 km ) contre aéronefs.", ids=["arme-915"]),
    Q("a04", "arme", "Portée du PL-15 chinois dans la base de CMO ?", "108 nm ( 200 km ).", ids=["arme-3413"]),
    Q("a05", "arme", "Le R-77M porte à combien de milles nautiques ?", "108 nm contre aéronefs.", ids=["arme-3126"]),
    Q("a06", "arme", "Quelle est la portée du JASSM-ER contre des cibles terrestres ?", "430 nm ( 796 km ).",
      ids=["arme-11", "arme-3906"]),
    Q("a07", "arme", "Jusqu'où peut frapper un Storm Shadow tiré d'avion ?", "302 nm ( 559 km ) contre cibles terrestres.",
      ids=["arme-957", "arme-333"]),
    Q("a08", "arme", "Portée du missile de croisière allemand Taurus KEPD 350 ?", "270 nm ( 500 km ).", ids=["arme-489"]),
    Q("a09", "arme", "Quelle est la portée du missile de croisière russe Kh-101 ?", "1 600 nm contre cibles terrestres.",
      ids=["arme-16"]),
    Q("a10", "arme", "Quelle vitesse et quelle portée a le missile aérobalistique Kinjal Kh-47M2 ?",
      "700 nm, 6 570 nœuds ( environ Mach 9,9 ).", ids=["arme-3532"]),
    Q("a11", "arme", "Le missile hypersonique Zircon : portée et vitesse dans CMO ?", "700 nm, 5 000 nœuds ( ≈ Mach 7,6 ).",
      ids=["arme-3361"]),
    Q("a12", "arme", "Quelle portée a le missile antinavire P-800 Onyx ?", "325 nm contre navires et cibles terrestres.",
      ids=["arme-1173", "arme-2685"]),
    Q("a13", "arme", "Portée du Naval Strike Missile norvégien ( NSM Block 1 ) ?", "108 nm contre navires et terre.",
      ids=["arme-299"]),
    Q("a14", "arme", "Quelle est la portée d'un Harpoon RGM-84D tiré d'un navire ?", "75 nm contre navires.", ids=["arme-1611"]),
    Q("a15", "arme", "Le Tomahawk Block IV TACTOM tiré d'un navire porte à combien ?", "864 nm contre cibles terrestres.",
      ids=["arme-586"]),
    Q("a16", "arme", "Portée air du SM-6 Block IA ?", "230 nm contre aéronefs ( et 230 nm contre navires ).",
      ids=["arme-3541"]),
    Q("a17", "arme", "Quelle est la portée de l'Aster 30 Block 1 NT ?", "60 nm contre aéronefs.", ids=["arme-3774"]),
    Q("a18", "arme", "Jusqu'à quelle distance intercepte un Patriot PAC-3 MSE ?", "60 nm.", ids=["arme-3207"]),
    Q("a19", "arme", "Portée du missile 48N6DM du S-400 ?", "135 nm ( 250 km ).", ids=["arme-2103"]),
    Q("a20", "arme", "Quelle est la portée du 40N6, le plus long missile du S-400 ?", "215 nm ( 398 km ).", ids=["arme-2104"]),
    Q("a21", "arme", "Quelle distance couvre un missile Iskander-M 9M723 ?", "270 nm ( 500 km ), vitesse 4 500 nœuds.",
      ids=["arme-567", "arme-1235"]),
    Q("a22", "arme", "Portée de l'ATACMS dans la base de CMO ?", "162 nm ( 300 km ) pour le Block IA et le MGM-168A unitaire.",
      ids=["arme-779", "arme-1717"]),
    Q("a23", "arme", "Quelle est la portée d'une roquette guidée GMLRS M31 ?", "45 nm ( 83 km ).", ids=["arme-2699"]),
    Q("a24", "arme", "Quelle portée pour le missile antiradar AARGM-ER ?", "140 nm.", ids=["arme-3588"]),
    Q("a25", "arme", "Le Kh-31PD antiradar porte à quelle distance ?", "110 nm.", ids=["arme-1307"]),
    Q("a26", "arme", "Quelle est la portée du HQ-9B chinois ?", "140 nm contre aéronefs.", ids=["arme-3763"]),
    Q("a27", "arme", "Vitesse et portée de la torpille Mk48 Mod 7 CBASS ?", "65 nœuds, 21 nm.", ids=["arme-1712"]),
    Q("a28", "arme", "Quelle portée et quelle vitesse a le drone d'attaque Shahed-136 ?", "1 350 nm, 108 nœuds.",
      titre=r"^Shahed-136 ", type="arme"),
    Q("a29", "arme", "Jusqu'où une petite bombe planante GBU-39 SDB peut-elle être larguée ?", "60 nm contre cibles terrestres.",
      ids=["arme-484"]),
    Q("a30", "arme", "Portée du missile balistique chinois DF-26 conventionnel ?", "2 160 nm.", ids=["arme-3373", "arme-3372"]),
    Q("a31", "arme", "Quelle est la portée de l'Exocet MM40 Block 3 ?", "100 nm.", ids=["arme-575", "arme-3902"]),
    Q("a32", "arme", "Portée du missile antinavire chinois YJ-18 ?", "320 nm.", ids=["arme-2868"]),
    Q("a33", "arme", "Le missile nord-coréen KN-23 porte à combien ?", "325 nm.", ids=["arme-3817", "arme-3816"]),
    Q("a34", "arme", "Quelle portée a le missile de croisière Kalibr 3M14 contre la terre ?", "750 nm.", ids=["arme-2713"]),

    # ------------------------------------------------------------------ PLATES-FORMES ( DB3000 )
    Q("p01", "plateforme", "Quelle est la vitesse maximale du chasseur furtif russe Su-57 ?", "1 000 nœuds ( 1 852 km/h ).",
      titre=r"^Su-57 Felon \(Russie\)", type="plateforme"),
    Q("p02", "plateforme", "Quel radar équipe le Su-35S russe ?", "Le radar PESA Irbis-E ( « Slot Back », 160 nm ), avec l'IRST OLS-35 et le brouilleur Khibiny-M.",
      ids=["capteur-4480"], titre=r"^Su-35S Flanker M \(Russie\)", type="plateforme"),
    Q("p03", "plateforme", "Quelle vitesse maximale atteint le MiG-31BM ?", "1 350 nœuds.", titre=r"^MiG-31BM Foxhound \(Russie\)", type="plateforme"),
    Q("p04", "plateforme", "Quels capteurs porte le F-35A de l'armée de l'air finlandaise ?",
      "Radar AN/APG-81 AESA, ESM AN/ASQ-239 Barracuda, EOTS et DAS.", titre=r"^F-35A Lightning II \(Finlande\)", type="plateforme"),
    Q("p05", "plateforme", "Quel radar a le Gripen E suédois ?", "Le PS-05/A Mk4 AESA ( ES-05 Raven ), plus l'IRST Skyward-G.",
      titre=r"^JAS 39E Gripen NG \(Suède\)", type="plateforme"),
    Q("p06", "plateforme", "Quel radar emporte l'avion de guet Saab 340 AEW polonais et quelle est sa portée ?",
      "Le PS-890 Erieye, 245 nm.", ids=["capteur-544"], titre=r"^Saab 340 AEW \(Pologne\)", type="plateforme"),
    Q("p07", "plateforme", "Comment est armé un destroyer Arleigh Burke Flight I ?",
      "Tomahawk, Harpoon, SM-2MR, torpilles Mk46, canon de 127 mm, Phalanx ; radar SPY-1D.",
      titre=r"^DDG 51 Arleigh Burke \[Flight I\] \(États-Unis\)", type="plateforme"),
    Q("p08", "plateforme", "Quel est le déplacement du porte-avions Gerald R. Ford ?", "100 000 t à pleine charge.",
      titre=r"^CVN 78 Gerald R\. Ford \(États-Unis\)", type="plateforme"),
    Q("p09", "plateforme", "Quels missiles antinavires embarque la frégate russe Amiral Gorshkov ?",
      "16 Kalibr 3M54T ( ou 16 Zircon selon la version ), plus 32 9M96D sol-air.",
      titre=r"Admiral Sergey Gorshkov.*\(Russie\)", type="plateforme"),
    Q("p10", "plateforme", "Combien de missiles HHQ-9B porte un croiseur chinois Type 055 Renhai ?", "84 HHQ-9B.",
      titre=r"^Type 055 Renhai \[101 Nanchang\] \(Chine\)", type="plateforme"),
    Q("p11", "plateforme", "Quelle vitesse maximale pour le porte-avions Charles de Gaulle ?", "33 nœuds.",
      titre=r"Charles De Gaulle \(France\)", type="plateforme"),
    Q("p12", "plateforme", "Quel radar multifonction équipe les destroyers britanniques Type 45 ?",
      "Le Type 1045 Sampson ( 215 nm ), avec des Aster 30 et Aster 15.", ids=["capteur-500"],
      titre=r"^D 32 Daring \[Type 45 Batch 1\] \(Royaume-Uni\)", type="plateforme"),
    Q("p13", "plateforme", "Quel est le déplacement du porte-avions britannique Queen Elizabeth ?", "65 600 t.",
      titre=r"^R 08 Queen Elizabeth \(Royaume-Uni\)", type="plateforme"),
    Q("p14", "plateforme", "Comment est armée la frégate allemande F125 Baden-Württemberg ?",
      "8 Harpoon, RAM, canon de 127 mm.", titre=r"Baden-Wurttemberg \[Type F125\] \(Allemagne\)", type="plateforme"),
    Q("p15", "plateforme", "Quels missiles porte une frégate danoise de classe Iver Huitfeldt ?",
      "32 SM-2MR Block IIIA, ESSM, Harpoon II ou NSM.", titre=r"^F 361 Iver Huitfeldt \(Danemark\)", type="plateforme"),
    Q("p16", "plateforme", "Quel sonar remorqué équipe la frégate norvégienne Fridtjof Nansen ?",
      "Le sonar à immersion variable CAPTAS Mk2 ( UMS 4229 ).", titre=r"^F 310 Fridtjof Nansen \(Norvège\)", type="plateforme"),
    Q("p17", "plateforme", "Quel est le déplacement d'une corvette suédoise Visby ?", "640 t, 35 nœuds.",
      titre=r"^K 31 Visby \(Suède\)", type="plateforme"),
    Q("p18", "plateforme", "Quel armement porte la corvette russe Karakurt ( projet 22800 ) ?",
      "8 missiles Kalibr 3M54T, canon de 76 mm, Pantsir-M ou défense rapprochée.",
      titre=r"\[Pr\.22800 Karakurt\] \(Russie\)", type="plateforme"),
    Q("p19", "plateforme", "Quelle immersion maximale pour un SNLE russe Boreï ?", "380 m ; 16 missiles Boulava.",
      titre=r"Borei.*\(Russie\)", type="plateforme"),
    Q("p20", "plateforme", "Comment est armé le sous-marin russe Severodvinsk ( Iassen ) ?",
      "32 P-800 Onyx, torpilles UGST, SA-N-8.", titre=r"Severodvinsk \[Yasen\] \(Russie\)", type="plateforme"),
    Q("p21", "plateforme", "Quelles torpilles utilisent les sous-marins allemands Type 212A ?", "DM2A4 Seehecht ( DM2A3 pour le premier lot ).",
      titre=r"\[Type 212A.*\(Allemagne\)", type="plateforme"),
    Q("p22", "plateforme", "Quelle est l'immersion maximale d'un Kilo amélioré russe projet 636.3 ?", "240 m.",
      titre=r"PL-636\.3 Improved Kilo II.*\(Russie\)", type="plateforme"),
    Q("p23", "plateforme", "Quelle vitesse maximale pour un SNA britannique Astute ?", "32 nœuds, torpilles Spearfish.",
      titre=r"^S 119 Astute \(Royaume-Uni\)", type="plateforme"),
    Q("p24", "plateforme", "Jusqu'à quelle profondeur peut plonger un SNLE français Le Triomphant ?", "450 m ; 16 M51.",
      titre=r"^S 616 Le Triomphant \(France\)", type="plateforme"),
    Q("p25", "plateforme", "Combien de missiles et quelle portée pour un bataillon S-400 russe ?",
      "48 missiles 48N6DM à 135 nm ( versions avec 40N6 à 215 nm ).", titre=r"S-400 Triumf\]\) \(Russie\)", type="plateforme"),
    Q("p26", "plateforme", "Que contient un bataillon Iskander-M russe dans CMO ?", "Des lanceurs 9K720 avec missiles 9M723 ( et 9M728 ).",
      titre=r"^SSM Bn \(SS-26 Stone \[9K720 Iskander-M\] TEL\) \(Russie\)", type="plateforme"),
    Q("p27", "plateforme", "Combien de missiles a une section Patriot PAC-3 MSE polonaise ?", "48 PAC-3 MSE, plus des Piorun.",
      titre=r"Patriot \[PAC-3 MSE\]\) \(Pologne\)", type="plateforme"),
    Q("p28", "plateforme", "Quels missiles tire le NASAMS III lituanien ?", "12 AMRAAM MIM-120C-7, portée 20 nm.",
      titre=r"NASAMS III\) \(Lituanie\)", type="plateforme"),
    Q("p29", "plateforme", "Comment est armée une batterie SAMP/T française ?", "32 Aster 30, portée 60 nm.",
      titre=r"SAMP/T \[Mamba\]\) \(France\)", type="plateforme"),
    Q("p30", "plateforme", "Quelle portée pour une section Pantsir-S1 russe ?", "10 nm, 24 missiles 57E6 et canons de 30 mm.",
      titre=r"\[Pantsir-S1\]\) \(Russie\)", type="plateforme"),
    Q("p31", "plateforme", "Quelles munitions tire une batterie HIMARS polonaise ?", "Roquettes GMLRS M31 ( 36 ).",
      titre=r"M142 HIMARS\) \(Pologne\)", type="plateforme"),
    Q("p32", "plateforme", "Quel missile tire le système côtier russe Bastion-P ?", "P-800 Onyx ( ou Zircon selon la version ).",
      titre=r"Bastion-P\]\) \(Russie\)", type="plateforme"),
    Q("p33", "plateforme", "Quel blindage a le char russe T-72B3 dans CMO ?", "Blindage spécial ( 201-500 mm RHA ), canon de 125 mm.",
      ids=["terrestre-102"]),
    Q("p34", "plateforme", "Quel capteur particulier porte le Tornado ECR allemand ?",
      "Le système de localisation d'émetteurs ELS ( Emitter Locator System ) pour ses missiles antiradar.",
      titre=r"^Tornado ECR \(Allemagne\)", type="plateforme"),
    Q("p35", "plateforme", "Quelle est la portée du radar de l'avion de guet russe A-50U ?", "Shmel-2, 350 nm.",
      ids=["capteur-2130"], titre=r"^A-50U Mainstay A \(Russie\)", type="plateforme"),
    Q("p36", "plateforme", "Quelle vitesse maximale a l'avion de patrouille maritime P-8A Poseidon ?", "520 nœuds.",
      titre=r"^P-8A Poseidon.*\(États-Unis\)", type="plateforme"),
    Q("p37", "plateforme", "Quelle est la vitesse du drone Bayraktar TB2 ukrainien ?", "135 nœuds.",
      titre=r"^Bayraktar TB2 UCAV \(Ukraine\)", type="plateforme"),
    Q("p38", "plateforme", "Quel radar équipe le FA-50PL polonais ?", "L'EL/M-2032.", titre=r"^FA-50PL Golden Eagle \(Pologne\)", type="plateforme"),
    Q("p39", "plateforme", "Quel est le déplacement du porte-avions chinois Fujian ?", "100 000 t ( Type 003 ).",
      titre=r"\[18 Fujian\] \(Chine\)", type="plateforme"),
    Q("p40", "plateforme", "Quels capteurs de guerre électronique porte l'EA-18G Growler ?", "Radar APG-79, récepteur AN/ALQ-218, brouilleurs.",
      titre=r"^EA-18G Growler \(États-Unis\)", type="plateforme"),

    # ------------------------------------------------------------------ CHARGEMENTS ( DB3000 )
    Q("c01", "chargement", "Quel rayon d'action a un Rafale C armé de deux SCALP ?", "600 nm ( chargement « SCALP EG, 2x, Heavy Deep Strike » ), préparation 360 min.",
      ids=["chargements-avion-560", "chargements-avion-1749"]),
    Q("c02", "chargement", "Combien de temps faut-il pour préparer un B-52H à une nouvelle frappe ?", "1 200 min ( 20 h ) de préparation au sol.",
      ids=["chargements-avion-14", "chargements-avion-567"]),
    Q("c03", "chargement", "Quel rayon d'action pour un Tornado ECR allemand armé de HARM ?", "820 nm ( 460 nm en version courte portée ), préparation 360 min.",
      ids=["chargements-avion-98", "chargements-avion-1635", "chargements-avion-2171"]),
    Q("c04", "chargement", "Avec quel rayon d'action un Su-34 emporte-t-il des Kh-59 ?", "670 nm, avec la nacelle de liaison APK-9.",
      ids=["chargements-avion-275", "chargements-avion-3723", "chargements-avion-4960"]),
    Q("c05", "chargement", "Le F-16 polonais en AMRAAM peut-il faire de la rotation rapide ?", "Oui : 60 min de préparation, 2 sorties ( préparation normale 180 min ).",
      ids=["chargements-avion-841", "chargements-avion-4372"]),
    Q("c06", "chargement", "Quel est le rayon d'action d'un KC-135R en mission de ravitaillement ?", "4 700 nm ( perche centrale ) ou 3 900 nm ( perche et paniers d'aile ).",
      ids=["chargements-avion-1692", "chargements-avion-1984"]),
    Q("c07", "chargement", "Quel rayon d'action pour un P-8A en patrouille anti-sous-marine ?", "1 200 nm, préparation 240 min.",
      ids=["chargements-avion-2705", "chargements-avion-3685", "chargements-avion-4427"]),
    Q("c08", "chargement", "Quel rayon d'action pour un Gripen E armé de Meteor ?", "350 nm, préparation 180 min.",
      ids=["chargements-avion-6078"]),

    # ------------------------------------------------------------------ CAPTEURS ( DB3000 )
    Q("s01", "capteur", "Quelle est la portée du radar AN/APG-81 du F-35 ?", "200 nm ( 370 km ), AESA, LPI.", ids=["capteur-2081"]),
    Q("s02", "capteur", "Portée du radar AN/SPY-6(V)1 des Arleigh Burke Flight III ?", "350 nm.", ids=["capteur-5360"]),
    Q("s03", "capteur", "Quelle portée pour le radar N036 Byelka du Su-57 ?", "215 nm.", ids=["capteur-1821"]),
    Q("s04", "capteur", "Quelle portée a le radar de conduite de tir 92N2 Grave Stone du S-400 ?", "215 nm.", ids=["capteur-4155"]),
    Q("s05", "capteur", "Quelle est la portée du radar AN/APY-2 de l'AWACS E-3 ?", "350 nm.", ids=["capteur-581", "capteur-913"]),
    Q("s06", "capteur", "Quelle portée pour le radar CAPTOR-E de l'Eurofighter ?", "185 nm.", ids=["capteur-1349"]),
    Q("s07", "capteur", "Quelle portée a le radar de veille russe 55Zh6U Nebo-U ?", "320 nm.", ids=["capteur-2522"]),
    Q("s08", "capteur", "Quelle est la portée du radar AN/MPQ-65 du Patriot ?", "110 nm.", ids=["capteur-2498"]),

    # ------------------------------------------------------------------ MÉCANISMES ET DOCTRINE ( manuel )
    Q("m01", "doctrine", "Quelle différence entre armes libres, armes restreintes et armes bloquées ?",
      "Restreintes : tir seulement sur hostile confirmé ; libres : sur tout ce qui n'est pas confirmé ami ; bloquées : jamais sans ordre manuel.",
      ids=["doctrine-roe-wcs"], manuel=(["3.3.13"], r"Weapons TIGHT|Weapons FREE"), carte=r"(Weapons Free|Weapons Tight|armes libres|armes restreintes|contrôle des armes)"),
    Q("m02", "mecanisme", "À quoi sert la règle du tiers dans une mission de patrouille ?",
      "Seul un tiers des avions affectés est en l'air à la fois, pour une couverture continue.",
      ids=["meca-regle-du-tiers", "meca-mission-patrol", "meca-mission-support"], manuel=(["7.2.2", "7.2.3"], r"1/3 Rule"),
      carte=r"(Règle du tiers \((Patrol|Support)\)|Mission de soutien et règle du tiers)"),
    Q("m03", "mecanisme", "Quel est le délai d'armement par défaut des mines mouillées par une mission ?",
      "2 heures ( Arming Delay ), pour laisser le mouilleur sortir de la zone.",
      ids=["meca-mission-mining"], manuel=(["7.2.5"], r"Arming Delay"), carte=r"(délai d'armement|Arming Delay)"),
    Q("m04", "doctrine", "Que signifie l'état carburant Bingo et que règle Joker ?",
      "Bingo : juste assez pour rentrer ( défaut ) ; Joker : seuils plus prudents ; Fuel State/RTB dit quand le vol rentre.",
      ids=["doctrine-carburant-armes-rtb"], manuel=(["3.3.13"], r"Bingo"), carte=r"Bingo"),
    Q("m05", "doctrine", "Que veut dire Winchester et Shotgun pour un avion ?",
      "Winchester : armes de la mission épuisées ; Shotgun : rentrer après un nombre réduit de tirs ( toutes les BVR, un engagement… ).",
      ids=["doctrine-carburant-armes-rtb"], manuel=(["3.3.13", "3.3.15"], r"Winchester|Shotgun"), carte=r"(Winchester|Shotgun)"),
    Q("m06", "doctrine", "Quelle est la différence entre un tempo Surge et Sustained ?",
      "Surge génère les sorties bien plus vite mais ne tient pas longtemps ; Sustained est l'effort durable.",
      ids=["doctrine-tempo-rotation"], manuel=(["3.3.13"], r"Surge|surge"), carte=r"(Tempo des opérations|Cadence surge|Surge, sustained)"),
    Q("m07", "doctrine", "Qu'est-ce que la rotation rapide ( Quick Turnaround ) des avions ?",
      "Des sorties courtes répétées avec un temps de préparation réduit, puis un repos ; réglable : oui, chasse et ASM seulement, non.",
      ids=["doctrine-tempo-rotation"], manuel=(["3.3.13"], r"Quick Turnaround|quick turnaround"), carte=r"(rotation rapide|Quick Turnaround|quick turnaround)"),
    Q("m08", "doctrine", "Comment la WRA utilise-t-elle la valeur de défense antimissile d'un navire ?",
      "Elle dimensionne la salve ( autant, deux fois, quatre fois la valeur… ) ; valeur en équivalents Harpoon, de 2 à 96 ; cible identifiée seulement.",
      ids=["doctrine-wra"], manuel=(["3.3.15"], r"Missile Defense"), carte=r"(Autorisation de tir)"),
    Q("m09", "doctrine", "Que fait le réglage EMCON et pourquoi garder les radars éteints ?",
      "Il allume ou éteint radar, sonar actif et brouillage ; un émetteur actif se détecte plus loin qu'il ne voit.",
      ids=["doctrine-emcon"], manuel=(["3.3.14"], r"EMCON|PASSIVE"),
      carte=r"(EMCON : radar|Ignorer l'EMCON|Héritage de l'EMCON|Niveau d'alerte|Émissions intermittentes|obéissance à l'EMCON|bataille de l'EMCON)"),
    Q("m10", "mecanisme", "Tous les combien de milles se forment les zones de convergence acoustiques ?",
      "Tous les 20 nm ( équateur ) à 40 nm ( pôles ), avec au moins 200 m d'eau sous la cible.",
      ids=["meca-sous-marins"], manuel=(["9.2.3"], r"CZ intervals|convergence"), carte=r"(convergence)"),
    Q("m11", "mecanisme", "À quelle profondeur un sous-marin chasseur a-t-il intérêt à se placer pour son antenne remorquée ?",
      "Juste au-dessus de la couche : l'antenne pend sous la couche et la couche masque le sous-marin.",
      ids=["meca-sous-marins"], manuel=(["9.2.3"], r"Just above layer"), carte=r"(Juste au-dessus de la couche|Antennes remorquées et couche)"),
    Q("m12", "mecanisme", "Quelle différence entre la DLZ et la NEZ d'un missile ?",
      "NEZ : la cible fuit dès le tir ; DLZ : la cible garde son cap, sa vitesse et son altitude.",
      ids=["meca-dlz"], manuel=(["9.2.9"], r"NEZ"),
      carte=r"(Zone sans échappatoire \(NEZ\) — DLZ|Zone de lancement dynamique \(DLZ\) — DLZ|Défaut tactique caché|Zone de tir dynamique \(DLZ\) et zone sans)"),
    Q("m13", "mecanisme", "À quelle distance de la position du sous-marin faut-il larguer une torpille ASM ?",
      "À moins de 0,5 nm du point visé.", ids=["meca-pourquoi-pas-de-tir", "meca-asm-moyens"],
      manuel=(["9.2.8"], r"0\.5nm"), carte=r"0,5 nm"),
    Q("m14", "mecanisme", "Un incendie ou une inondation peut-il détruire un navire qui a encore des points de dégâts ?",
      "Oui : si le feu ou l'inondation atteint son maximum, l'unité est détruite quels que soient ses points restants.",
      ids=["meca-ogives-degats"], manuel=(["9.2.7"], r"fire|flood"), carte=r"(Incendie et envahissement progressifs|Dégâts partiels|Dégâts totaux, incendie|État des dégâts et incendie)"),
    Q("m15", "mecanisme", "Quelles installations faut-il au minimum pour qu'une base aérienne fonctionne ?",
      "Une piste assez longue, un point d'accès ou taxiway, un abri ou parking à la bonne taille, un dépôt de munitions.",
      ids=["meca-bases-aeriennes"], manuel=(["9.3.1", "9.3"], r"minimum units necessary|Access Point or Taxiway"),
      carte=r"(Composition minimale|Base multi-unités : minimum)"),
    Q("m16", "mecanisme", "Pour neutraliser une base, vaut-il mieux frapper les pistes ou les points d'accès ?",
      "Les deux bloquent la base ; les points d'accès sont peu nombreux mais réparables, les pistes se réparent vite : refrapper.",
      ids=["meca-detruire-base"], manuel=(["9.3", "9.3.1"], r"Access Points|runways"), carte=r"(Neutraliser)"),
    Q("m17", "mecanisme", "Quelle différence entre brouillage DECM et OECM ?",
      "DECM : autoprotection dans le calcul final contre l'arme ; OECM : bruit qui gêne les radars de recherche, détectable par ESM.",
      ids=["meca-guerre-electronique"], manuel=(["9.2.6"], r"DECM|OECM"), carte=r"(DECM|OECM)"),
    Q("m18", "mecanisme", "Quels comportements peut avoir une mission de convoyage ( Ferry ) ?",
      "Aller simple, cycle aller-retour, ou aléatoire.", ids=["meca-mission-ferry"], manuel=(["7.2.1"], r"One-Way|Cycle"),
      carte=r"(Ferry|convoyage)"),
    Q("m19", "mecanisme", "Que deviennent des conteneurs de munitions livrés par une mission de fret ?",
      "Ils vont dans un dépôt existant à moins de 2 nm, sinon un point avancé de ravitaillement ( FARP ) est créé ; les munitions rechargent les unités.",
      ids=["meca-mission-cargo"], manuel=(["7.2.8"], r"container"), carte=r"(Conteneurs de cargo|Livraison de conteneurs|livrée?s? par conteneur)"),
    Q("m20", "doctrine", "Que fait le réglage « engager les contacts ambigus » en mode optimiste ?",
      "L'IA tire si l'incertitude de la cible est inférieure à 3 fois la tolérance de l'arme ( pessimiste : inférieure à la tolérance ).",
      ids=["doctrine-ambiguite"], manuel=(["3.3.13"], r"Optimistic"), carte=r"(ambigu)"),
    Q("m21", "mecanisme", "Une escorte rapprochée dans une frappe est-elle toujours la bonne solution ?",
      "Non : utile surtout aux époques canon ou premiers missiles ; avec des missiles longue portée, une patrouille séparée est recommandée.",
      ids=["meca-mission-strike-escorte"], manuel=(["7.1.1", "7.2.4"], r"close escort|separate patrol mission"),
      carte=r"(Escortes air-air ou SEAD)"),
    Q("m22", "mecanisme", "Un missile semi-actif peut-il être guidé si le tireur se détourne ?",
      "Non : la cible doit rester illuminée par le radar du tireur ; rompre l'accrochage fait perdre le missile.",
      ids=["meca-armes-guidage"], manuel=(["9.1.2"], r"Semi-Active Radar"), carte=r"(semi-actif \(SARH\)|radar semi-actif)"),
    Q("m23", "mecanisme", "Comment un avion peut-il échapper à un missile sol-air ?",
      "Fuir à pleine vitesse ( le missile perd de l'énergie ), masquer par le relief le radar de guidage, ou manœuvre brutale en fin de course.",
      ids=["meca-combat-aerien"], manuel=(["9.2.1"], r"SAM"), carte=r"(Échapper à un missile)"),
    Q("m24", "mecanisme", "Comment une unité terrestre à court de missiles se ravitaille-t-elle ?",
      "Elle rejoint un camion de munitions qui porte ses armes ( « replenish » ), comme un ravitaillement à la mer.",
      ids=["meca-combat-terrestre", "meca-logistique"], manuel=(["9.2.5"], r"replenish"), carte=r"(unités terrestres par camion|camion de munitions)"),
    Q("m25", "mecanisme", "Le carburant des avions est-il suivi sur les bases aériennes dans CMO ?",
      "Non : il est fourni à l'atterrissage ; seules les munitions sont suivies ; un avion sans base tombe à sec.",
      ids=["meca-bases-aeriennes", "meca-logistique"], manuel=(["9.3.1", "9.3"], r"Fuel is not currently tracked"), carte=r"(Carburant non suivi)"),
    Q("m26", "mecanisme", "Que se passe-t-il quand une unité perd ses communications ?",
      "NOCOMM : le camp ne connaît que sa dernière position, elle perd l'image commune, agit seule, risque de tir fratricide.",
      ids=["meca-communications"], manuel=(["10.7", "10.7.1", "10.7.2"], r"positive control|common operational picture|blue-on-blue|NOCOMM"), carte=r"(Effet :|NOCOMM|perte de l'image commune|Instantané des contacts)"),

    # ------------------------------------------------------------------ ATELIER ET LUA ( notre pont )
    Q("w01", "atelier", "Pourquoi un avion seul affecté à une patrouille reste-t-il au parking ?",
      "Une patrouille ne décolle que par vols d'au moins deux avions de la même base ; u:Launch(true) force un décollage.",
      ids=["atelier-patrouille-par-paires", "meca-regle-du-tiers"]),
    Q("w02", "atelier", "Ma mission de frappe créée en Lua ne part pas : pourquoi ?",
      "Une frappe neuve naît OnHold et attend des vols de quatre : l'activer ( Phase = 20 ) et régler des vols de deux.",
      ids=["atelier-frappe-onhold", "lua-missions"]),
    Q("w03", "atelier", "Faut-il passer le guid ou le nom de l'avion à ScenEdit_SetLoadout ?",
      "Le nom ( UnitName ) : par guid la fonction rend false ; l'avion doit être au sol et prêt, le dépôt garni.",
      ids=["atelier-setloadout"]),
    Q("w04", "atelier", "Pourquoi les avions posés ne se réarment-ils jamais dans la guerre du 29/09 ?",
      "Les dépôts de munitions des bases DB3000 et importées sont vides ( magasin 1185 ) : il faut les remplir ( FillMagsForLoadout ).",
      ids=["atelier-magasins-vides"]),
    Q("w05", "atelier", "Qu'est-ce qui ralentit CMO dans un scénario de guerre ?",
      "La suppression en masse d'unités ( x0,25 jusqu'au rechargement ), et les réglages Command.ini ( multithread coupé, autosauvegarde ).",
      ids=["atelier-suppression-differee", "atelier-reglages-perf"]),
    Q("w06", "atelier", "Comment savoir en Lua si l'ennemi voit une de mes unités et à quel niveau de classification ?",
      "u.ascontact liste les camps qui la voient ; ScenEdit_GetContact / GetContacts donne classificationlevel ( 0 à 4 ), âge, position.",
      ids=["atelier-contacts-brouillard", "lua-lecture-etat", "meca-contacts-classification"]),
    Q("w07", "regle", "En quelle unité sont les portées des armes dans la base de données de CMO ?",
      "En milles nautiques ( 1 nm = 1,852 km ) ; vitesses en nœuds, altitudes en mètres.",
      ids=["meca-unites-mesure", "atelier-unites-doctrine-py"]),
    Q("w08", "regle", "Quelles sont les phases d'une campagne aérienne pour l'état-major ?",
      "Supériorité aérienne ( SEAD, DEAD, OCA ), interdiction, appui au sol ; défense des bases en permanence.",
      ids=["regle-phases-campagne-aerienne", "commandement"]),
    Q("w09", "regle", "Peut-on frapper une base couverte par un S-400 intact avec des bombes guidées laser ?",
      "Non : DEAD d'abord, ou armes à distance de sécurité hors de sa portée, ou avion furtif.",
      ids=["regle-parapluie-sol-air", "regle-phases-campagne-aerienne", "commandement"]),
    Q("w10", "regle", "Quelle arme choisir contre un abri durci ou un dépôt enterré ?",
      "Une arme à ogive perforante ( pénétrante ) ; deux GBU-12 n'ont fait que 2,4 % à un dépôt enterré.",
      ids=["regle-arme-cible", "meca-ogives-degats", "atelier-frappe-onhold"]),
]


def resoudre(q, fiches):
    r = q["regle"]
    att = set(r["ids"])
    if r["titre"]:
        rx = re.compile(r["titre"])
        att |= {f["id"] for f in fiches if rx.search(f["titre"]) and (r["type"] is None or f["type"] == r["type"])}
    if r["manuel"]:
        secs, rx = r["manuel"][0], re.compile(r["manuel"][1])
        att |= {f["id"] for f in fiches if f["id"].startswith("manuel-") and f["chiffres"].get("section") in secs
                and rx.search(f.get("texte_en", ""))}
    if r["carte"]:                                       # sur le TITRE du mécanisme ( son nom ), pas sur tout le texte
        rx = re.compile(r["carte"], re.I)
        att |= {f["id"] for f in fiches if f["id"].startswith("meca-") and f.get("origine") == "manuel_carte.jsonl"
                and rx.search(f["titre"])}
    return sorted(att)


def main():
    fiches = [json.loads(l) for l in open(os.path.join(DOSSIER, "fiches.jsonl"), encoding="utf-8")]
    ids = {f["id"] for f in fiches}
    out, vides, manquants = [], [], []
    for q in QUESTIONS:
        att = resoudre(q, fiches)
        absents = [i for i in q["regle"]["ids"] if i not in ids]
        if absents:
            manquants.append((q["id"], absents))
        if not att:
            vides.append(q["id"])
        out.append({"id": q["id"], "categorie": q["categorie"], "question": q["question"], "reponse": q["reponse"],
                    "attendues": att, "regle": q["regle"]})
    with open(os.path.join(DOSSIER, "porte_questions.jsonl"), "w", encoding="utf-8") as f:
        for x in out:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    tailles = sorted(len(x["attendues"]) for x in out)
    print(f"{len(out)} questions ; fiches attendues par question : min {tailles[0]}, médiane {tailles[len(tailles) // 2]}, max {tailles[-1]}")
    for x in out:
        print(f"  {x['id']} {len(x['attendues']):3d}  {', '.join(x['attendues'][:6])}{' …' if len(x['attendues']) > 6 else ''}")
    if vides or manquants:
        print("QUESTIONS SANS FICHE ATTENDUE :", vides, "IDENTIFIANTS ABSENTS :", manquants)
        sys.exit(1)


if __name__ == "__main__":
    main()
