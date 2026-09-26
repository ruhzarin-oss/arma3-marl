"""LES ZONES DU CHAMP DE BATAILLE : les secteurs de Warlords, et les sites du moteur qu ils tiennent.

Source : la mission officielle de Bohemia `MP_Warlords_04_large.Malden` ( missions_f_warlords.pbo, lu dans le jeu
installe, jamais recopie a la main ). Chaque secteur est un carre de cote `Size` ( fn_WLInSectorArea ), sa valeur
`Funds` est le revenu par minute qu il rapporte dans Warlords, ses services disent ce qu il debloque ( A piste,
H helipad, W port ).

Rattachement d un site du moteur ( donnees/pays/<ile>.json ) a une zone - REGLE ECRITE, reversible :
- un site DANS le carre d un secteur lui appartient ;
- sinon, au secteur le plus proche si son centre est a moins de RAYON_INFLUENCE_M ( la centrale et les fonderies
  du Port de Malden sont a 400-500 m du secteur le plus proche : les laisser hors de toute zone les rendait
  imprenables ) ;
- les BASES de Warlords ne tiennent aucun site : ce sont les quartiers generaux des deux camps, pas des lieux du pays.

   python -m guerre.zones [ --mission <mission.sqm> ] [ --ile malden ]"""
import argparse, json, math, os, re

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(ICI)
PAYS = os.path.join(DEPOT, "monde", "donnees", "pays")
RAYON_INFLUENCE_M = 1000.0
SERVICES = (("A", "Service_Runway"), ("H", "Service_Helipad"), ("W", "Service_Harbour"))


def lire_mission(texte):
    """Les secteurs et les bases d un mission.sqm de Warlords ( texte ), dans l ordre du fichier :
    [ { n, genre ( secteur | base ), x, y, taille, valeur, services, camp_base } ]. Valeurs par defaut = celles du
    module ( modules_f_warlords : Size 250, Funds 25 pour un secteur, 10 pour une base )."""
    zones = []
    for m in re.finditer(r'type="ModuleWL(Sector|Base)_F";', texte):
        avant = texte[max(0, m.start() - 800):m.start()]
        pos = re.findall(r"position\[\]=\{([^}]*)\}", avant)
        if not pos: raise ValueError(f"module {m.group(1)} sans position a l octet {m.start()}")
        x, _, y = (float(v) for v in pos[-1].split(","))
        seg = texte[m.start():m.start() + 12000]
        fin = seg.find("class Item", 40)
        seg = seg[:fin if fin > 0 else len(seg)]
        attr = {k: v.strip().strip('"') for k, v in
                re.findall(r'property="ModuleWL(?:Sector|Base)_F_(\w+)";.*?value=([^;]*);', seg, re.S)}
        base = m.group(1) == "Base"
        zones.append({"n": len(zones), "genre": "base" if base else "secteur", "x": x, "y": y,
                      "taille": float(attr.get("Size", 250)), "valeur": int(float(attr.get("Funds", 10 if base else 25))),
                      "services": "".join(c for c, k in SERVICES if attr.get(k) == "1"),
                      "camp_base": int(float(attr["Side"])) if base and "Side" in attr else None})
    return zones


def dans_le_carre(z, x, y):
    h = z["taille"] / 2.0
    return abs(x - z["x"]) <= h and abs(y - z["y"]) <= h


def rattacher(zones, lieux, rayon=RAYON_INFLUENCE_M):
    """{ n de zone : [ ids des lieux ] } et la liste des lieux hors de toute zone."""
    secteurs = [z for z in zones if z["genre"] == "secteur"]
    tenus = {z["n"]: [] for z in secteurs}
    hors = []
    for l in lieux:
        x, y = l["pos"]
        z = next((z for z in secteurs if dans_le_carre(z, x, y)), None)
        if z is None and secteurs:
            d, z = min((math.hypot(x - s["x"], y - s["y"]), s) for s in secteurs)
            if d > rayon: z = None
        if z is None: hors.append(l["id"])
        else: tenus[z["n"]].append(l["id"])
    return tenus, hors


def carte_de_guerre(texte_mission, ile):
    """Tout ce que la guerre sait du champ de bataille : les zones et les sites qu elles tiennent."""
    zones = lire_mission(texte_mission)
    lieux = json.load(open(os.path.join(PAYS, f"{ile.lower()}.json")))["lieux"]
    tenus, hors = rattacher(zones, lieux)
    for z in zones: z["lieux"] = tenus.get(z["n"], [])
    return {"ile": ile, "zones": zones, "hors_zone": hors, "rayon_influence_m": RAYON_INFLUENCE_M}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--mission", default=os.path.join(ICI, "mission", "GuerreIles.Malden", "mission.sqm"))
    a.add_argument("--ile", default="Malden")
    x = a.parse_args()
    c = carte_de_guerre(open(x.mission, encoding="latin-1").read(), x.ile)
    for z in c["zones"]:
        print(f"{z['n']:2d} {z['genre']:7s} ({z['x']:7.0f}, {z['y']:7.0f}) cote {z['taille']:4.0f} valeur {z['valeur']:3d} "
              f"{z['services'] or '-':3s} {' '.join(z['lieux'])}")
    print("hors de toute zone :", " ".join(c["hors_zone"]) or "aucun")


if __name__ == "__main__":
    main()
