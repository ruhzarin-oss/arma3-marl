"""LA CARTE DE CHAQUE PAYS ( archipel, phase B ) : des sites mesures dans Arma aux lieux du moteur.

Pour chaque ile autre qu Altis ( Altis garde sa carte, choisie a la main le 21/09 et tenue par toutes les portes ),
on ecrit donnees/pays/<ile>.json : les lieux du moteur ( capitale, ville, village, base, carriere, mine, fonderie,
centrale, port ), le siege du gouvernement, les aeroports. REGLES ECRITES, reversibles, tirees d Altis quand c est
possible - jamais inventees :
- CAPITALES ( un marche et un hopital chacune ; decision de Younes le 24/09 : les hopitaux dans les plus grandes
  villes ) : une par tranche de PLACES_PAR_CAPITALE places de logement mesurees, la proportion d Altis ( 3 capitales
  pour 34 761 places ) ; d abord les capitales officielles de la carte, puis les plus grandes villes. Le siege du
  gouvernement est la plus grande capitale.
- BASES : les sites militaires d au moins MIN_BASE objets.
- INDUSTRIE, selon ce que montrent les modeles du site : convoyeurs, tremies, concasseurs -> carriere ; puits de mine
  -> mine ; ateliers, hangars industriels, usines -> fonderie ( elle fait des outils ). Un site de moins de MIN_USINE_M2
  de surface batie n est pas une usine.
- ENERGIE : une centrale seulement la ou il y a un batiment de centrale ou un champ solaire d au moins MIN_SOLAIRE
  panneaux.
- PORT : le plus grand site portuaire ( Livonia n a pas de mer : seulement l air, decision de Younes le 24/09 ).
- Ce que la carte ne montre pas ( puits de petrole, raffinerie, pharmacie ) n existe pas : le pays l importera.
Les aeroports ( configuration de la carte ) sont gardes pour le pont de l archipel.

   python -m monde.pays_carte"""
import json, math, os, re, sys
from collections import Counter

ICI = os.path.dirname(os.path.abspath(__file__))
ILES = ("Malden", "Stratis", "Tanoa", "Enoch", "Sara")
PLACES_PAR_CAPITALE = 34761 / 3          # Altis : 3 capitales ( Kavala, Athira, Pyrgos ) pour 34 761 places de logement
MIN_BASE = 10
MIN_USINE_M2 = 2000
MIN_SOLAIRE = 20
PAR_AIR_SEULEMENT = ("Enoch",)            # Livonia : decision de Younes, 24/09
TYPES_LIEUX = {"NameCityCapital": "capitale", "NameCity": "ville", "NameVillage": "village"}

CARRIERE = re.compile(r"conveyor|hopper|crusher|quarry|stone_?crush|gravel|sy_01_conveyor|reclaimer")
MINE = re.compile(r"mine|shaft|headframe|ore_|excavat")
FONDERIE = re.compile(r"workshop|shed_ind|metal_shed|factory|fabrik|plant|smelter|foundry|warehouse|sawmill|tovarn|repair|kovarn|dilna")
CENTRALE = re.compile(r"powerstation|mainfactory|dpp_01|power_?plant|elektrarn")


def modeles(site): return " ".join(m for m, _ in site["modeles"])


def nature_industrie(site):
    t = modeles(site)
    if CARRIERE.search(t): return "carriere"
    if MINE.search(t): return "mine"
    if FONDERIE.search(t): return "fonderie"
    return None


def carte_du_pays(ile):
    inv = json.load(open(os.path.join(ICI, "donnees", f"{ile.lower()}_inventaire.json")))
    sd = json.load(open(os.path.join(ICI, "donnees", f"{ile.lower()}_sites.json")))
    sites, logements = sd["sites"], sd["logements"]
    lieux, notes = [], []
    # 1. les lieux habites de la carte
    for l in inv["lieux"]:
        t = TYPES_LIEUX.get(l["type"])
        if t: lieux.append({"id": l["id"], "type": t, "pos": [l["x"], l["y"]], "rayon": l["rayon"], "places": logements.get(l["id"], {}).get("places", 0),
                            "source": f"lieu nomme {l['type']}"})
    places = sum(v["places"] for v in logements.values())
    n_cap = max(1, round(places / PLACES_PAR_CAPITALE))
    officielles = sorted([l for l in lieux if l["type"] == "capitale"], key=lambda l: -l["places"])
    autres = sorted([l for l in lieux if l["type"] == "ville"], key=lambda l: -l["places"])
    if not autres: autres = sorted([l for l in lieux if l["type"] == "village"], key=lambda l: -l["places"])
    capitales = (officielles + autres)[:max(n_cap, len(officielles))]
    for l in capitales:
        if l["type"] != "capitale":
            notes.append(f"{l['id']} devient capitale ( {l['places']} places de logement )"); l["type"] = "capitale"
            l["source"] += " -> capitale designee ( marche et hopital )"
    gouvernement = max(capitales, key=lambda l: l["places"])["id"]
    # 2. les sites du travail et de la defense
    k = Counter()
    def ajouter(site, t, pourquoi):
        k[t] += 1
        lieux.append({"id": f"{t}{k[t]:02d}", "type": t, "pos": [site["x"], site["y"]], "rayon": [150, 150],
                      "surface_m2": site["surface_m2"], "objets": site["objets"], "source": pourquoi})
    for s in sites:
        f = s["fonction"]
        if f == "militaire" and s["objets"] >= MIN_BASE:
            ajouter(s, "base", f"site militaire de {s['objets']} objets : {modeles(s)[:80]}")
        elif f == "industrie" and s["surface_m2"] >= MIN_USINE_M2:
            t = nature_industrie(s)
            if t: ajouter(s, t, f"site industriel de {s['surface_m2']} m2 : {modeles(s)[:80]}")
            else: notes.append(f"site industriel non attribue ( {s['surface_m2']} m2 ) : {modeles(s)[:80]}")
        elif f == "energie":
            t = modeles(s)
            panneaux = sum(n for m, n in s["modeles"] if "spp_panel" in m)
            if CENTRALE.search(t) or panneaux >= MIN_SOLAIRE:
                ajouter(s, "centrale", f"site d energie : {t[:80]}")
    ports = [s for s in sites if s["fonction"] == "port"]
    port = None
    if ile not in PAR_AIR_SEULEMENT and ports:
        p = max(ports, key=lambda s: s["surface_m2"])
        ajouter(p, "port", f"plus grand site portuaire ( {p['surface_m2']} m2 )"); port = lieux[-1]["id"]
    aeroports = [{"x": s["x"], "y": s["y"]} for s in sites if s["fonction"] == "piste"]
    absents = [t for t in ("puits", "raffinerie", "pharmacie", "mine", "carriere", "fonderie", "centrale", "base")
               if not any(l["type"] == t for l in lieux)]
    return {"ile": ile, "gouvernement": gouvernement, "port": port, "par_air_seulement": ile in PAR_AIR_SEULEMENT,
            "aeroports": aeroports, "places_logement": places, "lieux": lieux, "absents": absents, "notes": notes,
            "regles": {"places_par_capitale": round(PLACES_PAR_CAPITALE), "min_base": MIN_BASE, "min_usine_m2": MIN_USINE_M2,
                       "min_solaire": MIN_SOLAIRE}}


def main():
    os.makedirs(os.path.join(ICI, "donnees", "pays"), exist_ok=True)
    types = ("capitale", "ville", "village", "base", "carriere", "mine", "fonderie", "centrale", "port")
    print("pays     places  gouvernement            aeroports | " + " ".join(f"{t[:7]:>7s}" for t in types) + " | absents")
    for ile in ILES:
        c = carte_du_pays(ile)
        json.dump(c, open(os.path.join(ICI, "donnees", "pays", f"{ile.lower()}.json"), "w"), indent=1, ensure_ascii=False)
        n = Counter(l["type"] for l in c["lieux"])
        print(f"{ile:8s} {c['places_logement']:6d}  {c['gouvernement'][:22]:22s} {len(c['aeroports']):9d} | "
              + " ".join(f"{n.get(t, 0):7d}" for t in types) + f" | {', '.join(c['absents'])}")
        for x in c["notes"]: print(f"            {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
