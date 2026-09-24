"""Lire l inventaire des cartes : le portrait de chaque ile ( terre, forets, routes, aeroports, batiments par fonction ).

Le classement des batiments se fait par le TYPE que le jeu donne a l objet ( hopital, station-service, quai, ligne
electrique... ) puis, pour les batiments ordinaires, par des MOTS du nom de leur modele 3D. Ce qui ne se classe pas est
liste a part, jamais cache : le classement est une premiere lecture, a relire.

   python -m monde.lire_inventaire"""
import json, os, re, sys
from collections import Counter

ICI = os.path.dirname(os.path.abspath(__file__))
ILES = ("Altis", "Malden", "Stratis", "Tanoa", "Enoch", "Sara")

PAR_TYPE = {"HOSPITAL": "sante", "FUELSTATION": "carburant", "QUAY": "port", "LIGHTHOUSE": "port",
            "POWER LINES": "energie", "POWERSOLAR": "energie", "POWERWIND": "energie", "POWERWAVE": "energie",
            "TRANSMITTER": "communication", "CHURCH": "culte", "CHAPEL": "culte", "CROSS": "culte",
            "BUNKER": "militaire", "FORTRESS": "militaire", "WATERTOWER": "eau", "RAILWAY": "rail",
            "STACK": "industrie", "SHIPWRECK": "epave", "RUIN": "ruine", "TOURISM": "tourisme",
            "VIEW-TOWER": "militaire", "BUSSTOP": "transport", "FOUNTAIN": "eau"}
# l ordre compte : le premier mot trouve gagne
PAR_MOT = [
    ("aeroport", r"airport|terminal|controltower|control_tower|runway|airfield|heli_?pad"),
    ("militaire", r"mil_|military|barrack|bunker|cargo_hq|cargo_tower|cargo_patrol|cargo_house|guardhouse|guardbox|"
                  r"army|bagbunker|hbarrier|checkpoint|ammo|armory|dragons|mil\b|garrison"),
    ("hangar", r"hangar|shed_big|dome_big|tenthangar"),
    ("eau", r"water|well|toilet|cistern|reservoir|pumpa|kasna"),        # avant le carburant : 24/09, « oil » prenait les
    ("carburant", r"fuel|(^|_)oil|petrol|pump|refinery|bigtank|smalltank|storagetank|tank_rust|railwaycar_01_tank|"
                  r"gasstation|benzin"),                                  # toilettes seches, « tank » les citernes d eau
    ("energie", r"power|transformer|substation|spp_|solar|windturbine|wind_turbine|wtg|generator"),
    ("industrie", r"factory|ind_|industrial|indust|warehouse|workshop|sawmill|silo|cement|mine|quarry|conveyor|"
                  r"crane|dp_|kombinat|shed_ind|storage|containerline|metal_shed|slaughter|fabrik"),
    ("sante", r"hospital|clinic|medevac|medical|pharma"),
    ("port", r"pier|quay|dock|harbour|harbor|port_|lighthouse|boathouse|mooring"),
    ("agriculture", r"barn|farm|stable|cowshed|greenhouse|haystack|hay_|chickencoop|pigsty|cattle|agri|vineyard|"
                    r"orchard|shed_small|shed_wooden|farmhouse|granary"),
    ("culte", r"church|chapel|mosque|temple|monastery|cathedral|shrine|cemetery|grave"),
    ("commerce", r"shop|store|market|kiosk|supermarket|restaurant|cafe|bar_|hotel|kiosek|mall"),
    ("administration", r"government|police|cityhall|townhall|school|office|court|prison|bank|post|fire_?station|"
                       r"administration|embassy|library|university|castle"),
    ("communication", r"radio|tower_comm|comm_tower|antenna|transmitter|telek"),
    ("logement", r"house|home|villa|panelak|slum|apartment|flat|dwelling|bungalow|hut|cabin|residential|garage|"
                 r"i_|u_|d_|stone_|addon_0|sara_|ca_|dom|budova|hlaseni|kulna|kostel"),
]
MOTS = [(c, re.compile(m)) for c, m in PAR_MOT]


def classer(o):
    c = PAR_TYPE.get(o["type"])
    if c: return c
    nom = os.path.basename(str(o["modele"]).replace("\\", "/")).lower()
    for categorie, motif in MOTS:
        if motif.search(nom): return categorie
    return "inclasse"


def portrait(d):
    carte, cases, objets = d.get("carte") or {}, d["cases"], d["objets"]
    pas = (carte.get("pas_m") or 2000) / 1000.0
    v2 = d.get("version") == 2
    if v2: terre_km2 = sum(c["terre_sondages"] / c["sondages"] for c in cases) * pas * pas
    else: terre_km2 = sum(c["terre_pct"] for c in cases) / 100.0 * pas * pas
    sols = Counter()
    for c in cases:     # la version 1 ( 24/09 ) a mal lu les sols ( paires prises pour deux listes ) : on garde le lisible
        sols.update({k: v for k, v in c["sols"].items() if isinstance(v, (int, float))})
    tot_sols = sum(sols.values()) or 1
    cat = Counter(classer(o) for o in objets)
    inclasses = Counter(os.path.basename(str(o["modele"]).replace("\\", "/")).lower() for o in objets if classer(o) == "inclasse")
    veg, routes, alt = Counter(), Counter(), []
    for c in cases:
        if v2:
            veg.update(c["vegetation"]); routes.update(c["routes_m"]); alt.append(c["altitude"]["max"])
        else:
            veg["arbres"] += c["arbres"]; routes["?"] += c["routes"]
    return {"terre_km2": round(terre_km2, 1), "taille_km": (carte.get("taille_m") or 0) / 1000.0,
            "aeroports": len([a for a in (carte.get("aeroports") or []) if a]),
            "arbres": int(veg.get("arbres", 0) + veg.get("petits_arbres", 0)), "vegetation": dict(veg),
            "routes": int(sum(routes.values())), "routes_m": dict(routes),
            "altitude_max": max(alt) if alt else None,
            "places_interieures": int(sum(o.get("places", 0) for o in objets)),
            "objets": len(objets), "par_fonction": dict(cat.most_common()),
            "sols": {k: round(v / tot_sols, 3) for k, v in sols.most_common(8)},
            "inclasses_principaux": inclasses.most_common(25),
            "lieux_nommes": len(d.get("lieux", [])), "fin": d.get("fin")}


def main():
    portraits = {}
    for ile in ILES:
        chemin = os.path.join(ICI, "donnees", f"{ile.lower()}_inventaire.json")
        if not os.path.exists(chemin): print(f"{ile} : pas d inventaire"); continue
        portraits[ile] = portrait(json.load(open(chemin)))
    json.dump(portraits, open(os.path.join(ICI, "donnees", "portraits_iles.json"), "w"), indent=1, ensure_ascii=False)
    fonctions = ["logement", "commerce", "administration", "sante", "culte", "agriculture", "industrie", "hangar",
                 "carburant", "energie", "port", "aeroport", "militaire", "communication", "eau", "rail", "inclasse"]
    print("ile      terre km2  aeroports   arbres  routes_m  alt_max  places  objets | " + " ".join(f"{f[:6]:>6s}" for f in fonctions))
    for ile, p in portraits.items():
        print(f"{ile:8s} {p['terre_km2']:9.1f} {p['aeroports']:10d} {p['arbres']:8d} {p['routes']:9d} {p['altitude_max'] or 0:8.0f} "
              f"{p['places_interieures']:7d} {p['objets']:7d} | "
              + " ".join(f"{p['par_fonction'].get(f, 0):6d}" for f in fonctions))
    for ile, p in portraits.items():
        print(f"\n{ile} : sols {p['sols']} | routes {p['routes_m']} | vegetation {p['vegetation']}")
        print(f"  inclasses : {p['inclasses_principaux'][:15]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
