"""Le LEXIQUE français des énumérations de la base DB3000 de CMO ( tables Enum* ), pour écrire les fiches en français.
Une valeur absente du lexique garde son libellé anglais d'origine ( jamais d'invention ).

Unités de la base, vérifiées le 03/10 sur des valeurs connues ( AIM-120D 86,4 nm, Iskander 270 nm, ATACMS 162 nm ) :
portées en MILLES NAUTIQUES ( nm ), vitesses en NŒUDS, altitudes en MÈTRES, masses en kg, consommation en kg/min.
"""

NM_KM = 1.852

PAYS_FR = {
    "United States": "États-Unis", "Russia [1992-]": "Russie", "China": "Chine", "Belarus [1992-]": "Biélorussie",
    "Poland": "Pologne", "Germany [FRG/Reunified]": "Allemagne", "France": "France", "United Kingdom": "Royaume-Uni",
    "Sweden": "Suède", "Finland": "Finlande", "Denmark": "Danemark", "Norway": "Norvège", "Netherlands": "Pays-Bas",
    "Estonia [1992-]": "Estonie", "Latvia [1992-]": "Lettonie", "Lithuania [1992-]": "Lituanie", "Turkey": "Turquie",
    "Italy": "Italie", "Ukraine [1992-]": "Ukraine", "NATO": "OTAN (moyens communs)",
    "Albania": "Albanie", "Belgium": "Belgique", "Bulgaria": "Bulgarie", "Canada": "Canada", "Croatia [1992-]": "Croatie",
    "Czech Republic [1993-]": "République tchèque", "Greece": "Grèce", "Hungary": "Hongrie", "Iceland": "Islande",
    "Luxembourg": "Luxembourg", "Montenegro [1992-]": "Monténégro", "North Macedonia [1991-]": "Macédoine du Nord",
    "Portugal": "Portugal", "Romania": "Roumanie", "Slovakia [1993-]": "Slovaquie", "Slovenia [1991-]": "Slovénie",
    "Spain": "Espagne", "Iran": "Iran", "North Korea": "Corée du Nord",
}
# Les pays dont les fiches sont écrites : la liste demandée ( 19 + OTAN ), le reste de l'OTAN, et le bloc Russie-Chine
# au sens de cmo/blocs.py ( Biélorussie, Corée du Nord, Iran ).
PAYS_RETENUS = list(PAYS_FR)
PAYS_PRIORITAIRES = ["United States", "Russia [1992-]", "China", "Belarus [1992-]", "Poland", "Germany [FRG/Reunified]",
                     "France", "United Kingdom", "Sweden", "Finland", "Denmark", "Norway", "Netherlands",
                     "Estonia [1992-]", "Latvia [1992-]", "Lithuania [1992-]", "Turkey", "Italy", "Ukraine [1992-]", "NATO"]

SERVICE_FR = {
    "Air Force": "armée de l'air", "Navy": "marine", "Army": "armée de terre", "Marines": "infanterie de marine",
    "Coast Guard": "garde-côtes", "National Guard": "garde nationale", "Home Guard": "garde territoriale",
    "Coastal Artillery": "artillerie côtière", "Marine Corps": "corps des Marines", "Customs": "douanes",
    "Air National Guard": "garde nationale aérienne", "Border Guard": "garde-frontières", "Police": "police",
    "Space Force": "force spatiale", "Royal Air Force": "Royal Air Force", "Royal Navy": "Royal Navy",
    "Royal Army": "British Army", "Royal Marines": "Royal Marines", "Frontal Aviation [VVS]": "aviation tactique (VVS)",
    "Air Defence Troops [PVO]": "défense aérienne (PVO)", "Naval Fleet [V-MF]": "flotte (VMF)",
    "Naval Aviation [AV-MF]": "aéronavale (AV-MF)", "Red Army": "armée de terre", "Naval Infantry": "infanterie de marine",
    "Strategic Rocket Forces": "forces des fusées stratégiques", "Long Range Aviation [DA]": "aviation à long rayon d'action (DA)",
    "Military Transport Aviation (VTA)": "aviation de transport (VTA)", "PLAAF": "armée de l'air chinoise (PLAAF)",
    "PLANAF": "aéronavale chinoise (PLANAF)", "PLAN": "marine chinoise (PLAN)", "PLAGF": "armée de terre chinoise (PLAGF)",
    "PLANMC": "infanterie de marine chinoise", "PLARF / Second Artillery Corps": "force des fusées chinoise (PLARF)",
    "Military": "forces armées", "Reserves": "réserve", "Civilian": "civil", "Commercial": "commercial",
    "Unknown": "inconnu", "Generic": "générique", "None": "",
}

AVION_TYPE_FR = {
    "None": "aéronef", "Fighter": "chasseur", "Multirole (Fighter/Attack)": "avion multirôle (chasse et attaque)",
    "Anti-Satellite Interceptor (ASAT)": "intercepteur antisatellite", "Airborne Laser Platform": "plate-forme laser aéroportée",
    "Attack": "avion d'attaque", "Wild Weasel": "avion de suppression des défenses (Wild Weasel)", "Bomber": "bombardier",
    "Battlefield Air Interdiction (BAI/CAS)": "appui aérien rapproché (BAI/CAS)", "Electronic Warfare": "avion de guerre électronique",
    "Airborne Early Warning (AEW)": "avion de guet aérien (AEW)", "Airborne Command Post (ACP)": "poste de commandement volant",
    "Search And Rescue (SAR)": "appareil de recherche et sauvetage", "Mine Sweeper (MCM)": "appareil de guerre des mines",
    "Anti-Submarine Warfare (ASW)": "appareil de lutte anti-sous-marine (ASM)", "Maritime Patrol Aircraft (MPA)": "avion de patrouille maritime",
    "Forward Observer": "observateur avancé", "Area Surveillance": "appareil de surveillance de zone", "Recon": "appareil de reconnaissance",
    "Electronic Intelligence (ELINT)": "appareil de renseignement électronique (ELINT)",
    "Signals Intelligence (SIGINT)": "appareil de renseignement d'origine électromagnétique (SIGINT)", "Transport": "avion de transport",
    "Cargo": "avion cargo", "Commercial": "avion commercial", "Civilian": "avion civil", "Utility": "appareil utilitaire",
    "Naval Utility": "appareil utilitaire naval", "Tanker (Air Refueling)": "avion ravitailleur", "Trainer": "avion d'entraînement",
    "Target Towing": "remorqueur de cibles", "Target Drone": "drone cible", "Unmanned Aerial Vehicle (UAV)": "drone (UAV)",
    "Unmanned Combat Aerial Vehicle (UCAV)": "drone de combat (UCAV)", "Rigid Airship": "dirigeable rigide", "Aerostat": "aérostat",
    "Blimp": "dirigeable souple",
}
AVION_CAT_FR = {"None": "", "Fixed Wing": "voilure fixe", "Fixed Wing, Carrier Capable": "voilure fixe embarquable sur porte-avions",
                "Helicopter": "hélicoptère", "Tiltrotor": "convertible", "Airship": "dirigeable", "Seaplane": "hydravion",
                "Amphibian": "amphibie"}

NAVIRE_CAT_FR = {"None": "", "Carrier (Aviation Ship)": "porte-aéronefs", "Surface Combatant": "bâtiment de combat de surface",
                 "Amphibious": "bâtiment amphibie", "Auxiliary": "bâtiment auxiliaire", "Merchant": "navire marchand",
                 "Civilian": "navire civil", "Surface Combatant (Aviation Capable)": "bâtiment de combat de surface (avec aviation)",
                 "Mobile Offshore Base (Aviation Capable)": "base mobile en mer"}
# Le sigle OTAN de la base est gardé ( « DDG ») et expliqué en français.
NAVIRE_SIGLE_FR = {
    "CV": "porte-avions", "CVA": "porte-avions d'attaque", "CVN": "porte-avions à propulsion nucléaire",
    "CVH": "porte-hélicoptères", "CVGH": "croiseur porte-hélicoptères lance-missiles", "CVM": "croiseur porte-aéronefs",
    "BB": "cuirassé", "BCGN": "croiseur de bataille nucléaire lance-missiles", "CG": "croiseur lance-missiles",
    "CGN": "croiseur lance-missiles à propulsion nucléaire", "CGH": "croiseur porte-hélicoptères lance-missiles", "CL": "croiseur léger",
    "DD": "destroyer", "DDG": "destroyer lance-missiles", "DDH": "destroyer porte-hélicoptères", "DDK": "destroyer anti-sous-marin",
    "DE": "aviso-escorteur", "FF": "frégate", "FFG": "frégate lance-missiles", "FFL": "corvette", "PF": "frégate de patrouille",
    "OPV": "patrouilleur hauturier", "LCS": "navire de combat littoral", "PB": "patrouilleur", "PC": "patrouilleur côtier",
    "PCF": "patrouilleur rapide", "PCFG": "patrouilleur rapide lance-missiles", "PG": "canonnière / corvette",
    "PGM": "canonnière lance-missiles", "PHM": "hydroptère lance-missiles", "PHT": "hydroptère lance-torpilles",
    "PT": "vedette lance-torpilles", "MTB": "vedette lance-torpilles", "USV": "drone de surface",
    "WPB": "patrouilleur des garde-côtes", "WPG": "canonnière des garde-côtes", "WHEC": "garde-côtes hauturier",
    "WMEC": "garde-côtes de moyenne endurance", "WMSM": "garde-côtes de sécurité maritime", "MCDV": "bâtiment de défense côtière",
    "LHA": "porte-hélicoptères d'assaut amphibie", "LHD": "porte-hélicoptères amphibie polyvalent", "LPH": "porte-hélicoptères d'assaut",
    "LPD": "transport de chalands de débarquement", "LSD": "bâtiment de débarquement de chars à radier", "LST": "bâtiment de débarquement de chars",
    "LSM": "bâtiment de débarquement moyen", "LSL": "bâtiment logistique de débarquement", "LCC": "bâtiment de commandement amphibie",
    "LCU": "chaland de débarquement", "LCM": "chaland de débarquement mécanisé", "LCAC": "aéroglisseur de débarquement",
    "LCVP": "engin de débarquement de véhicules et personnels", "LCP": "engin de débarquement de personnels",
    "LCPA": "aéroglisseur de débarquement de personnels", "LCT": "chaland de chars", "LCI": "engin de débarquement d'infanterie",
    "MCM": "bâtiment de lutte contre les mines", "MHC": "chasseur de mines côtier", "MSC": "dragueur de mines côtier",
    "MSO": "dragueur de mines océanique", "ML": "mouilleur de mines", "MST": "bâtiment base de dragueurs",
    "MCS": "bâtiment de soutien à la guerre des mines", "MCD": "drone de lutte contre les mines",
    "AOE": "bâtiment de soutien rapide au combat (pétrolier-ravitailleur-munitionnaire)", "AOR": "pétrolier-ravitailleur",
    "AO": "pétrolier d'escadre", "AOT": "pétrolier de transport", "AOL": "petit pétrolier", "AE": "bâtiment munitionnaire",
    "AFS": "bâtiment de vivres et rechanges", "AGS": "bâtiment hydrographique", "AGI": "bâtiment de renseignement",
    "AGOS": "bâtiment de surveillance océanique", "T-AGOS": "bâtiment de surveillance océanique (MSC)", "AGM": "bâtiment d'essais de missiles",
    "AX": "bâtiment-école", "ASR": "bâtiment de sauvetage de sous-marins", "AH": "navire-hôpital", "T-AO": "pétrolier d'escadre (MSC)",
    "T-AKE": "cargo de munitions et vivres (MSC)", "T-AKR": "roulier (MSC)", "AK": "cargo", "AKR": "roulier",
}
SOUSMARIN_TYPE_FR = {
    "SSN - Nuclear Powered Attack Submarine": "sous-marin nucléaire d'attaque (SNA)",
    "SSK - Hunter-Killer Submarine ": "sous-marin d'attaque à propulsion classique (SSK)",
    "SS - Attack/Fleet Submarine ": "sous-marin d'attaque classique (SS)",
    "SSBN - Nuclear Powered Ballistic Missile Submarine": "sous-marin nucléaire lanceur d'engins (SNLE)",
    "SSGN - Nuclear Powered Guided Missile Attack Submarine": "sous-marin nucléaire lance-missiles de croisière (SSGN)",
    "SSG - Guided Missile Attack Submarine": "sous-marin lance-missiles classique (SSG)",
    "SSB - Ballistic Missile Submarine": "sous-marin lanceur d'engins classique (SSB)",
    "SSM - Midget Submarine ": "sous-marin de poche", "SDV - Swimmer Delivery Vehicle": "propulseur de nageurs de combat",
    "ROV - Remotely Operated Vehicle": "robot sous-marin téléopéré (ROV)", "UUV - Unmanned Underwater Vehicle": "drone sous-marin (UUV)",
    "Unmanned Underwater Glider": "planeur sous-marin", "False Target": "fausse cible (leurre)", "Biologics": "biologique (cétacé)",
    "AGSS - Auxilary/Experimental Submarine ": "sous-marin expérimental",
}
INSTALLATION_CAT_FR = {
    "None": "", "Runway": "piste", "Runway-Grade Taxiway": "taxiway de qualité piste", "Runway Access Point": "point d'accès de piste",
    "Building (Surface)": "bâtiment en surface", "Building (Reveted)": "bâtiment protégé par merlon",
    "Building (Bunker)": "bâtiment bunkérisé", "Building (Underground)": "bâtiment souterrain", "Structure (Open)": "structure ouverte",
    "Structure (Reveted)": "structure protégée par merlon", "Surface (Flat) & Underground": "surface plane et souterrain",
    "Underwater": "sous-marine", "Water (Surface)": "en surface de l'eau", "Mobile Vehicle(s)": "véhicules mobiles",
    "Mobile Personnel": "personnel mobile", "Mobile Vehicle(s) - Tracked": "véhicules chenillés",
    "Mobile Vehicle(s) - Half-Track": "véhicules semi-chenillés", "Mobile Vehicle(s) - Wheeled": "véhicules à roues",
    "Aerostat Mooring": "amarrage d'aérostat", "Air Base": "base aérienne",
}
INSTALLATION_TYPE_FR = {
    "None": "", "Radar": "radar", "Electronic Warfare": "guerre électronique", "SAM": "défense sol-air (SAM)", "AAA": "artillerie antiaérienne",
    "Artillery": "artillerie", "Towed Artillery": "artillerie tractée", "Self Propelled Artillery": "artillerie automotrice",
    "Wheeled Rocket Artillery": "lance-roquettes sur roues", "Tracked Rocket Artillery": "lance-roquettes chenillé", "Mortar": "mortier",
    "SSM": "missiles sol-sol (SSM)", "Armored": "blindés", "Combined Arms": "interarmes", "Infantry": "infanterie",
    "Marines": "infanterie de marine", "Air Assault": "aéromobile", "Mountain": "troupes de montagne", "Airborne": "parachutistes",
    "Special Forces": "forces spéciales", "Mechanized": "mécanisée", "Mechanized Airborne": "parachutistes mécanisés",
    "Mechanized Wheeled": "mécanisée sur roues", "Motorized": "motorisée", "Ammo": "dépôt de munitions", "Fuel": "dépôt de carburant",
    "Supply": "ravitaillement", "Recon": "reconnaissance", "Amphibious Recon": "reconnaissance amphibie", "Anti Tank": "antichar",
    "Engineer": "génie", "Headquarters": "poste de commandement",
}
TERRESTRE_CAT_FR = {
    "None": "", "Infantry": "infanterie", "Marines": "infanterie de marine", "Air Assault": "aéromobile", "Mountain": "montagne",
    "Airborne": "parachutiste", "Special Forces": "forces spéciales", "Combined Arms": "interarmes", "Armor": "char / blindé",
    "Armor Recon": "blindé de reconnaissance", "Artillery": "artillerie", "Towed Artillery": "artillerie tractée",
    "Self-Propelled Artillery": "artillerie automotrice", "Wheeled Rocket Artillery": "lance-roquettes sur roues",
    "Tracked Rocket Artillery": "lance-roquettes chenillé", "Mortar": "mortier", "SSM": "lanceur sol-sol (SSM)",
    "AAA": "artillerie antiaérienne", "SAM": "lanceur sol-air (SAM)", "Engineer": "génie", "Supply": "véhicule logistique",
    "Surveillance": "surveillance (radar, capteur)", "Recon": "reconnaissance", "Amphibious Recon": "reconnaissance amphibie",
    "Mech Infantry": "infanterie mécanisée", "Mech Marines": "infanterie de marine mécanisée", "Mech Airborne": "parachutistes mécanisés",
    "Mech Wheeled": "infanterie mécanisée sur roues", "Motorized Infantry": "infanterie motorisée", "Anti Tank": "antichar",
    "Radar": "radar", "Electronic Warfare": "guerre électronique", "Headquarters": "poste de commandement",
}
BLINDAGE_FR = {
    "None": "aucun", "Light (Handgun Resistant)": "léger (résiste aux armes de poing)",
    "Light (Assault Rifle Resistant)": "léger (résiste aux fusils d'assaut)", "Light (HMG Resistant)": "léger (résiste aux mitrailleuses lourdes)",
    "Light (20-25mm RHA)": "léger (20-25 mm RHA)", "Light (26-30mm RHA)": "léger (26-30 mm RHA)", "Light (31-35mm RHA)": "léger (31-35 mm RHA)",
    "Light (36-40mm RHA)": "léger (36-40 mm RHA)", "Light (41-90mm RHA)": "léger (41-90 mm RHA)", "Medium (91-140mm RHA)": "moyen (91-140 mm RHA)",
    "Heavy (141-200mm RHA)": "lourd (141-200 mm RHA)", "Special (201-500mm RHA)": "spécial (201-500 mm RHA)",
}

ARME_TYPE_FR = {
    "None": "arme", "Guided Weapon": "missile / arme guidée", "Rocket": "roquette", "Bomb": "bombe", "Gun": "canon (obus)",
    "Decoy (Expendable)": "leurre consommable", "Decoy (Towed)": "leurre remorqué", "Decoy (Vehicle)": "leurre-véhicule",
    "Training Round": "munition d'exercice", "Dispenser": "lance-sous-munitions", "Contact Bomb - Suicide": "charge suicide",
    "Contact Bomb - Sabotage": "charge de sabotage", "Guided Projectile": "obus guidé", "Small Arms": "arme légère",
    "UAV (Expendable)": "drone consommable (munition rôdeuse)", "Sensor Pod": "nacelle de capteurs", "Drop Tank": "réservoir largable",
    "Buddy Store": "nacelle de ravitaillement en vol", "Ferry Tank": "réservoir de convoyage", "Torpedo": "torpille",
    "Depth Charge": "grenade anti-sous-marine", "Sonobuoy": "bouée acoustique", "Bottom Mine": "mine de fond",
    "Moored Mine": "mine à orin", "Floating Mine": "mine flottante", "Moving Mine": "mine mobile", "Rising Mine": "mine ascensionnelle",
    "Drifting Mine": "mine dérivante", "Attached Mine": "mine ventouse", "Dummy Mine": "mine factice",
    "Guided Depth Charge": "grenade anti-sous-marine guidée", "Helicopter-Towed Package": "équipement remorqué par hélicoptère",
    "Aircraft": "aéronef (charge)", "Ship": "embarcation (charge)", "Submarine": "engin sous-marin (charge)", "Satellite": "satellite (charge)",
    "Ground Unit": "unité terrestre (charge)", "RV / MRV/ MIRV": "corps de rentrée (RV/MRV/MIRV)", "Pallet Munition": "munition palettisée",
    "Laser": "laser", "Microwave": "arme à micro-ondes", "Laser Dazzler": "laser éblouissant",
    "Hypersonic Glide Vehicle": "planeur hypersonique", "Glide Vehicle": "planeur", "Hypersonic Cruise Missile": "missile de croisière hypersonique",
    "Cargo": "fret", "Troops": "troupes", "Paratroops": "parachutistes",
}
CIBLE_FR = {
    "Aircraft": "avions", "Helicopter": "hélicoptères", "Missile": "missiles", "Satellite": "satellites",
    "C-RAM (Counter Rocket, Artillery and Mortar)": "roquettes, obus et mortiers (C-RAM)", "Surface Vessel": "navires de surface",
    "Submarine": "sous-marins", "Mine": "mines", "Torpedo": "torpilles", "Land Structure - Soft": "structures terrestres non durcies",
    "Land Structure - Hardened": "structures terrestres durcies", "Runway": "pistes", "Radar": "radars",
    "Mobile Target - Soft": "cibles mobiles non blindées", "Mobile Target - Hardened": "cibles mobiles blindées",
    "Mobile Target - Personnel": "personnel", "Underwater Structure": "structures sous-marines", "Air Base": "bases aériennes",
}
OGIVE_FR = {
    "None": "aucune", "High Explosive (HE) Blast / Frag": "explosive à souffle et fragmentation", "Armor-Piercing (AP)": "perforante (AP)",
    "High Explosive Anti-Tank (HEAT) Shaped Charge": "charge creuse (HEAT)", "Incendiary (Napalm, WP)": "incendiaire",
    "Fragmentation": "à fragmentation", "Semi Armor-Piercing (SAP)": "semi-perforante (SAP)", "High Explosive Splash Head (HESH)": "HESH",
    "Continuous Rod": "à barreau continu", "Hard Target Penetrator (HTP)": "pénétrante pour cibles durcies",
    "Fuel-Air Explosive (FAE / Thermobaric)": "thermobarique (FAE)", "Enhanced Armor-Piercing Fragmentation": "perforante à fragmentation renforcée",
    "Fragmentation - ABM-Optimized": "fragmentation optimisée antimissile", "Torpedo": "de torpille", "Depth Charge": "de grenade ASM",
    "Torpedo, ASW Optimized": "de torpille ASM", "Nuclear": "NUCLÉAIRE", "Chemical": "chimique", "Bacteriological": "biologique",
    "Microwave": "micro-ondes", "Cluster Bomb, Anti-Personnel (Fragmentation)": "à sous-munitions antipersonnel",
    "Cluster Bomb, Anti-Tank (Shaped Charge)": "à sous-munitions antichar", "Cluster Bomb, Anti-Runway (Penetrator)": "à sous-munitions anti-piste",
    "Cluster Bomb, Guided Submunitions, Anti-Tank (Shaped Charge)": "à sous-munitions antichar guidées",
    "Mine, Anti-Personnel (Fragmentation)": "mine antipersonnel", "Mine, Anti-Tank (Shaped Charge)": "mine antichar",
    "Long Rod Penetrator (APDS / APFSDS)": "flèche (APFSDS)", "Anti-Electrical": "anti-réseaux électriques (graphite)",
    "Solid-State Laser (Fiber)": "laser à fibre", "EMP - Directed": "impulsion électromagnétique dirigée",
}
CODE_ARME_FR = {
    "Illuminate at Launch": "illumination radar dès le tir", "Terminal Illumination": "illumination en phase terminale seulement",
    "Supports Buddy Illumination": "illumination par un autre appareil possible", "Home On Jam (HOJ)": "ralliement sur brouilleur (HOJ)",
    "Anti-Air Stern Chase": "tir air-air en poursuite arrière", "Anti-Air Rear-Aspect": "tir air-air secteur arrière",
    "Anti-Air All-Aspect": "tir air-air tous secteurs", "Anti-Air Dogfight (High Off-Boresight)": "combat rapproché à fort dépointage",
    "Capable vs Seaskimmer": "efficace contre missiles rasants", "ARH AAW - No HQ Track Required": "autodirecteur actif, pas de piste de qualité exigée",
    "Counter- Rocket, Arty, Mortar (C-RAM) Capable": "capacité C-RAM",
    "Lock-On After Launch (LOAL) - CEC-Capable": "accrochage après tir (LOAL), compatible CEC",
    "Flight Profile - Terrain Following": "suivi de terrain", "Lock-On After Launch (LOAL)": "accrochage après tir (LOAL)",
    "Launcher occupied during guidance": "lanceur occupé pendant le guidage", "ARM Target Memory": "antiradar à mémoire de position",
    "Loiter Capability": "capacité de rôder (munition rôdeuse)", "Search Pattern": "trajectoire de recherche",
    "Bearing-Only Launch (BOL)": "tir sur relèvement seul (BOL)",
    "Depressed Ballistic Trajectory (Iskander, ATACMS, etc.)": "trajectoire balistique tendue (quasi balistique)",
    "Ballistic Trajectory (Ballistic Missile, GMLRS, etc.)": "trajectoire balistique", "Multi-Stage Missile": "missile à plusieurs étages",
    "Weapon - INS Navigation": "navigation inertielle", "Weapon - INS w/ GNSS Navigation": "navigation inertielle recalée par satellites",
    "Weapon - TERCOM Navigation": "navigation par corrélation de terrain (TERCOM)", "Weapon - Pre-Briefed Target Only": "cible préprogrammée seulement",
    "Weapon - Can Target Specific Subsystems": "peut viser un sous-système précis", "Terminal Maneuver - Pop-Up": "ressource terminale (pop-up)",
    "Terminal Maneuver - Zig-Zag": "zigzag terminal", "Terminal Maneuver - Random (Advanced)": "manœuvre terminale aléatoire",
    "Re-Attack Capability": "peut réattaquer", "Uses GPS": "GPS", "Uses GLONASS": "GLONASS", "Uses BeiDou/COMPASS": "BeiDou",
    "Fuze - Impact": "fusée d'impact", "Fuze - Proximity": "fusée de proximité", "Is Retarded Munition": "munition freinée",
    "Boosted Penetrator": "pénétrateur propulsé", "Torpedo - Wake Homing (WH)": "torpille à autoguidage sur sillage",
    "Flight Profile - Hi-Hi-Lo": "profil haut-haut-bas", "Flight Profile - Level Cruise Flight": "croisière en palier",
    "Mine - Contact Fuze": "mine à contact", "Mine - Magnetic Fuze, Simple Magnetic": "mine magnétique simple",
    "Mine - Passive Acoustic Fuze, Broad-Band (Simple)": "mine acoustique simple", "Mine - Pressure Fuze": "mine à dépression",
    "Mine - Target Discrimination / Identification": "mine à discrimination de cible", "Mine - Remote Controlled": "mine télécommandée",
    "Warhead - Multiple Independent Re-Entry Vehicles (MIRV)": "têtes multiples indépendantes (MIRV)",
}
CAPTEUR_TYPE_FR = {
    "None": "capteur", "Radar": "radar", "Semi-Active": "autodirecteur semi-actif", "Visual": "capteur optique (visuel)",
    "Infrared": "capteur infrarouge", "Track-Via-Missile (TVM)": "guidage par le missile (TVM)", "Terminal Semi-Active": "semi-actif terminal",
    "ESM": "détecteur d'émissions (ESM)", "ECM": "brouilleur (ECM)", "EMP Projector": "projecteur IEM",
    "Passive Coherent Location System": "radar passif (localisation cohérente)", "Laser Designator": "désignateur laser",
    "Laser Spot Tracker (LST)": "poursuiteur de tache laser", "Laser Rangefinder": "télémètre laser", "LIDAR": "lidar",
    "Hull Sonar, Passive-Only": "sonar de coque passif", "Hull Sonar, Active/Passive": "sonar de coque actif/passif",
    "Hull Sonar, Active-Only": "sonar de coque actif", "Bow Sonar, Active/Passive": "sonar d'étrave actif/passif",
    "TASS, Passive-Only Towed Array Sonar System": "sonar remorqué passif (antenne linéaire)",
    "TASS, Active/Passive Towed Array Sonar System": "sonar remorqué actif/passif", "TASS, Active Towed Array Sonar System": "sonar remorqué actif",
    "VDS, Passive Only Sonar": "sonar à immersion variable passif", "VDS, Active/Passive Sonar": "sonar à immersion variable actif/passif",
    "VDS, Active Only Sonar": "sonar à immersion variable actif", "Dipping Sonar, Passive-Only": "sonar trempé passif",
    "Dipping Sonar, Active/Passive": "sonar trempé actif/passif", "Dipping Sonar, Active-Only": "sonar trempé actif",
    "Bottom Fixed Sonar, Passive-Only": "sonar fixe de fond passif", "MAD": "détecteur d'anomalie magnétique (MAD)",
    "Wake Detector": "détecteur de sillage", "Acoustic Intercept (Active Sonar Warning)": "intercepteur acoustique (alerte sonar actif)",
    "Mine Sweep, Mechanical Cable Cutter": "drague mécanique", "Mine Sweep, Magnetic Influence": "drague magnétique",
    "Mine Sweep, Acoustic Influence": "drague acoustique", "Mine Sweep, Magnetic & Acoustic Multi-Influence": "drague multi-influence",
    "Mine Sweep, Two-Ship Magnetic Influence": "drague magnétique à deux bâtiments",
    "Mine Neutralization, Moored Mine Cable Cutter": "neutralisation de mines à orin (cisaille)",
    "Mine Neutralization, Explosive Charge Mine Disposal": "neutralisation de mines par charge",
    "Mine Neutralization, Diver-deployed Explosive Charge": "neutralisation de mines par plongeurs", "Microwave Emitter": "émetteur micro-ondes",
    "Non-Detecting Emitter": "émetteur non détectant", "Sensor Group": "groupe de capteurs",
}
CAPACITE_CAPTEUR_FR = {
    "Air Search": "veille aérienne", "Surface Search": "veille surface", "Submarine Search": "détection sous-marine",
    "Land Search - Fixed Facility": "détection d'installations terrestres", "Land Search - Mobile Unit": "détection d'unités terrestres mobiles",
    "Periscope Search": "détection de périscope", "C-RAM (Counter-Rocket, Artillery and Mortar)": "C-RAM",
    "Space Search (ABM)": "veille spatiale / antimissile", "Mine & Obstacle Search": "recherche de mines et d'obstacles",
    "Torpedo Warning": "alerte torpille", "Missile Approach Warning": "alerte d'approche de missile", "Range Information": "distance",
    "Altitude Information": "altitude", "Speed Information": "vitesse", "Heading Information": "cap", "Navigation Only": "navigation seulement",
    "Ground Mapping Only": "cartographie du sol seulement", "Terrain Avoidance / Following Only": "évitement / suivi de terrain seulement",
    "Weather Only": "météo seulement", "Weather and Navigation Only": "météo et navigation seulement",
    "OTH-B (Backscatter)": "transhorizon par rétrodiffusion (OTH-B)", "OTH-SW (Surface Wave)": "transhorizon à onde de surface (OTH-SW)",
    "TDOA (Time Difference of Arrivals)": "localisation par différence de temps d'arrivée (TDOA)", "DF (Direction Finding)": "radiogoniométrie",
}
CODE_CAPTEUR_FR = {
    "Identification Friend or Foe (IFF) [Side Info]": "IFF (identifie le camp)",
    "Classification [Class Info] / Brilliant Weapon [Automatic Target Aquisition]": "classification (donne la classe)",
    "Non-Cooperative Target Recognition (NCTR)  - Jet Engine Modulation [Class Info]": "identification non coopérative (NCTR, modulation des réacteurs)",
    "Non-Cooperative Target Recognition (NCTR)  - Narrow Beam Interleaved Search and Track [Class Info]": "identification non coopérative (NCTR)",
    "Continuous Tracking Capability": "poursuite continue", "Track While Scan (TWS)": "poursuite pendant le balayage (TWS)",
    "Moving Target Indicator (MTI)": "indicateur de cibles mobiles (MTI)", "Low Probability of Intercept (LPI)": "faible probabilité d'interception (LPI)",
    "Pulse-Only Radar": "radar à impulsions seulement (pas de vision vers le bas)", "Pulse Doppler Radar (Full LDSD Capability)": "Doppler pulsé, vision vers le bas complète",
    "Pulse Doppler Radar (Limited LDSD Capability)": "Doppler pulsé, vision vers le bas limitée",
    "Passive Electronically Scanned Array (PESA)": "antenne à balayage électronique passive (PESA)",
    "Active Electronically Scanned Array (AESA)": "antenne active à balayage électronique (AESA)",
    "Can Classify Ground Targets (SAR)": "classe les cibles au sol (SAR)", "Continuous Wave Illumination": "illumination à onde continue",
    "Interrupted Continuous Wave Illumination": "illumination à onde continue interrompue", "Weapon FCR (No CW Illumination)": "conduite de tir sans illumination",
    "Frequency Agile": "agilité de fréquence", "Cognitive EW": "guerre électronique cognitive", "Generates AAW Fire-Control Data": "fournit une conduite de tir antiaérienne",
    "Shallow Water Capable (Partial)": "eaux peu profondes (partiel)", "Shallow Water Capable (Full) [Classification Flag Required]": "eaux peu profondes (complet)",
    "Supports Bistatic Mode [Passive Sonar]": "mode bistatique (sonar passif)",
    "LLTV / NVG / CCD (Night-Capable) / Searchlight [Visual Night-Capable]": "vision de nuit",
}
CODE_AVION_FR = {
    "Probe Refueling": "ravitaillement en vol par perche", "Boom Refueling": "ravitaillement en vol par perche rigide (boom)",
    "Centerline Drogue": "ravitailleur à panier central", "Wing Drogue": "ravitailleur à paniers d'aile", "Centerline Boom": "ravitailleur à perche rigide",
    "Supermanouverability (5th Gen Fighters)": "supermanœuvrabilité", "Helmet Mounted Sight / Display (HMS/HMD)": "viseur de casque",
    "Terrain Following (Land: 200ft [60.9m], Sea: 100ft [30.5m])": "suivi de terrain",
    "Terrain Avoidance (Land: 300ft [91.4m], Sea: 100ft [30.5m])": "évitement de terrain",
    "Night Navigation/Attack (Incl. Bomb, Rocket Delivery)": "navigation et attaque de nuit",
    "Night Navigation (Ferry, Air-to-Air, Air-to-Surface Missiles)": "navigation de nuit",
    "Bombsight - Advanced Navigation (INS/GPS)": "système de bombardement INS/GPS", "HIFR Capable": "ravitaillement d'hélicoptère en vol stationnaire",
    "Nap-of-the-Earth (NOE)": "vol tactique très basse altitude (NOE)",
}
CODE_NAVIRE_PREFIXES = (("Refuel to", "peut ravitailler en carburant"), ("Refuel from", "peut recevoir du carburant à la mer"),
                        ("Replenish to", "peut ravitailler en vivres et munitions"), ("Replenish from", "peut être ravitaillé en vivres et munitions"))

ROLE_CHARGEMENT_FR = {
    "n/a": "sans rôle", "Intercept, BVR AAMs": "interception, missiles au-delà de la vue (BVR)",
    "Intercept, WVR AAMs": "interception, missiles à courte portée (WVR)", "Air Superiority, BVR AAMs": "supériorité aérienne, missiles BVR",
    "Air Superiority, WVR AAMs": "supériorité aérienne, missiles WVR", "Point-defence, BVR AAMs": "défense de point, missiles BVR",
    "Point-defence, WVR AAMs": "défense de point, missiles WVR", "Guns Only": "canon seulement",
    "Strike, Land/Naval": "frappe terre et mer", "Standoff Strike, Land/Naval": "frappe à distance de sécurité terre et mer",
    "SEAD, ARM, Land/Naval": "SEAD par missiles antiradar, terre et mer", "SEAD, TALD, Land/Naval": "SEAD par leurres, terre et mer",
    "DEAD, Land/Naval": "DEAD (destruction des défenses), terre et mer", "Strike, Land-only": "frappe terrestre",
    "Standoff Strike, Land": "frappe terrestre à distance de sécurité", "SEAD, ARM, Land": "SEAD terrestre par missiles antiradar",
    "SEAD, TALD, Land": "SEAD terrestre par leurres", "DEAD, Land": "DEAD terrestre", "Strike, Naval": "frappe antinavire",
    "Standoff Strike, Naval": "frappe antinavire à distance de sécurité", "SEAD, ARM, Naval": "SEAD navale par antiradar",
    "SEAD, TALD, Naval": "SEAD navale par leurres", "DEAD, Naval": "DEAD navale", "BAI/CAS": "appui aérien rapproché (CAS/BAI)",
    "Buddy Illumination": "illumination pour un autre appareil", "Offensive ECM": "brouillage offensif", "Airborne Early Warning (AEW)": "guet aérien (AEW)",
    "Airborne Command Post (ACP)": "poste de commandement volant", "Chaff Dispenser": "lance-paillettes", "Drone Deployment": "largage de drones",
    "Search And Rescue (SAR)": "recherche et sauvetage", "Combat Search And Rescue (CSAR)": "sauvetage au combat (CSAR)",
    "Mine Sweep (MCM)": "dragage de mines", "Mine Reconnaissance": "reconnaissance des mines", "Naval Mine Laying": "mouillage de mines",
    "ASW Patrol": "patrouille anti-sous-marine", "ASW Attack": "attaque anti-sous-marine", "Forward Observer": "observation avancée",
    "Area Surveillance": "surveillance de zone", "Armed Recon": "reconnaissance armée", "Unarmed Recon": "reconnaissance non armée",
    "Maritime Surveillance": "surveillance maritime", "Paratroops": "parachutage", "Troop Transport": "transport de troupes",
    "Cargo Transport": "transport de fret", "Air Refueling": "ravitaillement en vol", "Training": "entraînement", "Target Tow": "remorquage de cible",
    "Target Drone": "drone cible", "Ferry": "convoyage", "Unavailable": "indisponible (maintenance)", "Reserve": "réserve (sans armement)",
    "Armed Ferry": "convoyage armé", "Packed for Cargo": "conditionné pour le fret", "Anti-Satellite Intercept (ASAT)": "interception antisatellite",
    "Airborne Laser (ABM)": "laser aéroporté antimissile",
}
JOUR_FR = {"n/a": "", "Day and night": "jour et nuit", "Night-only": "nuit seulement", "Day-only": "jour seulement"}
METEO_FR = {"n/a": "", "All-weather": "tout temps", "Limited all-weather": "tout temps limité", "Clear weather": "beau temps seulement"}
TAILLE_AVION_FR = {
    "None": "", "Small Aircraft (0-12m)": "petit (0-12 m)", "Medium Aircraft (12.1-18m)": "moyen (12-18 m)",
    "Large Aircraft (18.1-26m)": "grand (18-26 m)", "Very Large Aircraft (26.1-75m)": "très grand (26-75 m)",
    "UAS [NATO Class I, Micro] (0-2kg)": "drone micro (0-2 kg)", "UAS [NATO Class I, Mini] (2-20kg)": "drone mini (2-20 kg)",
    "UAS [NATO Class I, Small] (20-150kg)": "petit drone (20-150 kg)", "UAS [NATO Class II] (150-600kg)": "drone classe II (150-600 kg)",
}
INSTALL_AVIATION_FR = {
    "Runway": "piste", "Runway w/ Arrest": "piste avec brins d'arrêt", "Runway-Grade Taxiway": "taxiway de qualité piste",
    "Runway Access Point": "point d'accès de piste", "Carrier Catapult": "catapulte", "Carrier Ski Jump": "tremplin",
    "Carrier Arresting Gear": "brins d'arrêt", "Pad": "plate-forme hélicoptère", "Pad with Haul-Down": "plate-forme avec harpon",
    "Hangar": "hangar", "Open Parking": "parking à découvert", "Elevator": "ascenseur", "UAV Catapult": "catapulte de drones",
    "Flat-Top Deck (Helo/STOL Only)": "pont plat (hélicoptères et ADAC)", "Flat-Top Deck (VTOL Capable)": "pont plat (ADAV)",
}
PROPULSION_FR = {
    "Turbojet": "turboréacteur", "Turbofan": "turbofan", "Turboprop": "turbopropulseur", "Piston": "moteur à pistons",
    "Helo Turboshaft": "turbomoteur", "Diesel": "diesel", "Steam": "vapeur", "Gas Turbine": "turbine à gaz", "Nuclear": "nucléaire",
    "Pump Jet Propulsor": "pompe-hélice", "Gasoline": "essence", "Electric": "électrique", "Air Independent": "anaérobie (AIP)",
}


def tr(dico, cle):
    """La traduction, sinon le libellé d'origine."""
    if cle is None:
        return ""
    return dico.get(cle, dico.get(cle.strip(), cle.strip()))


def sigle_navire(desc):
    """« DDG - Guided Missile Destroyer » -> « destroyer lance-missiles (DDG) »."""
    if not desc:
        return "navire"
    sigle = desc.split(" - ")[0].strip()
    fr = NAVIRE_SIGLE_FR.get(sigle)
    return f"{fr} ({sigle})" if fr else desc.strip()


_MOTS_ROLE = [("Air & Surface Search", "veille air et surface"), ("Air Search", "veille aérienne"), ("Surface Search", "veille surface"),
              ("Height-Finder", "radar de site"), ("Long-Range", "longue portée"), ("Medium-Range", "moyenne portée"),
              ("Short-Range", "courte portée"), ("FCR", "conduite de tir"), ("Air-to-Air & Air-to-Surface", "air-air et air-sol"),
              ("Air-to-Air", "air-air"), ("Air-to-Surface", "air-sol"), ("Surface-to-Air & Surface-to-Surface", "surface-air et surface-surface"),
              ("Surface-to-Air", "surface-air"), ("Surface-to-Surface", "surface-surface"), ("Target Indicator", "désignation d'objectifs"),
              ("Navigation", "navigation"), ("Weather", "météo"), ("Illuminator", "illuminateur"), ("Weapon Seeker", "autodirecteur"),
              ("Active Radar", "radar actif"), ("Ballistic Missile", "missiles balistiques"), ("Early Warning", "alerte avancée"),
              ("Counter-Battery", "contre-batterie"), ("Towed Array Sonar System", "sonar remorqué"), ("Passive-Only", "passif"),
              ("Active/Passive", "actif/passif"), ("Active-Only", "actif"), ("Hull Sonar", "sonar de coque"), ("Dipping Sonar", "sonar trempé"),
              ("Sonobuoy", "bouée acoustique"), ("Variable Depth Sonar", "sonar à immersion variable"), ("Torpedo Warning", "alerte torpille"),
              ("Mine Hunting", "chasse aux mines"), ("Search & Track", "veille et poursuite"), ("Search", "veille"), ("Track", "poursuite"),
              ("Infrared", "infrarouge"), ("Camera", "caméra"), ("Reconnaissance", "reconnaissance"), ("Surveillance", "surveillance"),
              ("Radar", "radar"), ("Visual", "optique"), ("Missile Approach Warning System", "alerte d'approche de missile"),
              ("Radar Warning Receiver", "détecteur d'alerte radar"), ("Laser Warning Receiver", "détecteur d'alerte laser"),
              ("Offensive ECM", "brouillage offensif"), ("Defensive ECM", "autoprotection électronique"), ("Laser Target Designator", "désignateur laser"),
              ("Emitter Locator", "localisateur d'émetteurs"), ("Communications Jammer", "brouilleur de communications"), ("GNSS Jammer", "brouilleur GNSS")]


def role_capteur(desc):
    """Traduction mot à mot ( approximative, le libellé anglais reste entre parenthèses dans la fiche )."""
    if not desc:
        return ""
    s = desc
    for en, fr in _MOTS_ROLE:
        s = s.replace(en, fr)
    return s
