"""island_stratis.py — ARCHITECTURE de l'ile (le PAYS a defendre) pour la TRAQUE 1000 vs 40 FS.

L'ile est un reseau de NOEUDS TYPES. Chaque type = une INFRASTRUCTURE du pays ET une ACTION COERCITIVE des FS,
avec une FONCTION dans la traque. C'est ce maillage que les 1000 defendent et que les 40 FS frappent en se cachant.

TYPE       role pays                         action coercitive FS            effet quand detruit
----       ---------                         ------------------             -------------------
hq         commandement (cerveau + VIP)      decapiter / capturer           C2 s'effondre + grosse coercition
radar      capteur (les YEUX)                aveugler                       couverture de detection chute
comms      C2 / liaison (les OREILLES)       aveugler                       coordination/QRF degradee
vip        leadership                        assassiner / kidnapper         coercition (volonte)
infra      depot/carburant/centrale/piste    saboter                        coercition (moyens)
cache      armes/vehicules/aero au sol       detruire                       coercition (moyens)
bridge     logistique (axes)                 couper / IED                   mobilite des traqueurs chute
resource   eco (oil/gas/water, lien LEVIATHAN) etrangler                    coercition eco
town       population                        intimider / psy-ops            coercition (volonte du pays)
"""

# (nom, x, y, type)  — positions reelles sur Stratis (X ~1700-6000, Y ~2900-6600 ; nord = Y haut)
NODES = [
    ("QG-AirStation",  4900, 6350, "hq"),
    ("Radar-Nord",     3050, 6150, "radar"),
    ("Radar-Centre",   4350, 4800, "radar"),
    ("Radar-Sud",      5250, 3300, "radar"),
    ("Comms-Ouest",    2300, 5350, "comms"),
    ("Comms-Est",      5750, 5250, "comms"),
    ("Gouverneur",     4050, 5500, "vip"),
    ("Etat-Major-2",   5400, 5900, "vip"),
    ("Depot-Carburant",3400, 5650, "infra"),
    ("Centrale",       5550, 4250, "infra"),
    ("Aerodrome",      4650, 5950, "infra"),
    ("Cache-Armes",    2000, 5800, "cache"),
    ("Cache-Vehicules",5050, 6300, "cache"),
    ("Pont-Nord",      3600, 5050, "bridge"),
    ("Pont-Centre",    4500, 4100, "bridge"),
    ("Pont-Sud",       5100, 3500, "bridge"),
    ("Petrole-SaltLake",5050, 4250, "resource"),
    ("Gaz-DevilsCastle",4350, 6500, "resource"),
    ("Eau-Theseus",    5950, 4800, "resource"),
    ("Ville-AgiaMarina",3350, 5600, "town"),
    ("Ville-Rogain",   5500, 3150, "town"),
    ("Ville-Kamino",   1900, 5700, "town"),
]

# poids de coercition par type (combien ca "fait mal" au pays quand c'est frappe) + fonction de traque
TYPE_META = {
    "hq":       {"coercion": 10.0, "fonction": "c2",       "label": "QG / commandement"},
    "radar":    {"coercion": 3.0,  "fonction": "capteur",  "label": "radar (yeux)"},
    "comms":    {"coercion": 3.0,  "fonction": "c2",       "label": "comms (C2)"},
    "vip":      {"coercion": 6.0,  "fonction": "moral",    "label": "VIP / leadership"},
    "infra":    {"coercion": 4.0,  "fonction": "moyens",   "label": "infra (sabotage)"},
    "cache":    {"coercion": 3.0,  "fonction": "moyens",   "label": "cache (armes/vehicules)"},
    "bridge":   {"coercion": 2.0,  "fonction": "mobilite", "label": "pont (logistique)"},
    "resource": {"coercion": 4.0,  "fonction": "eco",      "label": "ressource (eco)"},
    "town":     {"coercion": 5.0,  "fonction": "volonte",  "label": "ville (population)"},
}

# capteurs = les YEUX du pays (radar + comms) : ce que les FS visent pour aveugler la traque
SENSOR_TYPES = ("radar", "comms")


def summary():
    from collections import Counter
    c = Counter(t for _, _, _, t in NODES)
    tot = sum(TYPE_META[t]["coercion"] for _, _, _, t in NODES)
    print("ARCHITECTURE STRATIS | %d noeuds | coercition totale en jeu = %.0f" % (len(NODES), tot))
    for t, n in c.most_common():
        print("  %-9s x%d  (%s, coercion/u=%.0f, fonction=%s)" % (t, n, TYPE_META[t]["label"], TYPE_META[t]["coercion"], TYPE_META[t]["fonction"]))
    print("  -> capteurs (yeux a aveugler) : %d" % sum(1 for _, _, _, t in NODES if t in SENSOR_TYPES))


if __name__ == "__main__":
    summary()
