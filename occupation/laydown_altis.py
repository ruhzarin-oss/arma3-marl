#!/usr/bin/env python3
"""occupation/laydown_altis.py — GENERATEUR de l'occupation REDFOR d'Altis (DONNEE, pas code en dur).
Lit staff/{altis_catalog,altis_roads,altis_relief}.json -> ecrit staff/occupation_altis.json :
{secteurs, elements:[{type,pos,size,posture,loadout,route,sector,name}]}. Cale au TARGET par echelle.
Usage : python laydown_altis.py --target 2000 --seed 0 --sectors 4
"""
import json, math, argparse, random, os

ROOT = "/home/younes/arma3-marl"
def load(n): return json.load(open(os.path.join(ROOT, "staff", n)))

CAT_SIZE = {"ville": 50, "bourg": 26, "village": 13, "hameau": 6, "site": 6}

def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

def sector_of(x, y, cx, cy):
    ns = "N" if y >= cy else "S"; eo = "E" if x >= cx else "O"; return ns + eo  # NE NO SE SO

def farthest_sample(pts, k):
    """echantillonne k points bien repartis (farthest-point)."""
    if len(pts) <= k: return list(pts)
    chosen = [pts[0]]
    while len(chosen) < k:
        best, bd = None, -1
        for p in pts:
            d = min(dist(p, c) for c in chosen)
            if d > bd: bd, best = d, p
        chosen.append(best)
    return chosen

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sectors", type=int, default=4)
    a = ap.parse_args(); random.seed(a.seed)
    cat = load("altis_catalog.json"); roads = load("altis_roads.json")["roads"]
    locs = cat["objectifs"]; size = cat.get("size", 30720)
    cx = sum(l["x"] for l in locs) / len(locs); cy = sum(l["y"] for l in locs) / len(locs)
    for l in locs: l["sector"] = sector_of(l["x"], l["y"], cx, cy)
    roadpts = [[r[0], r[1]] for r in roads]

    E = []  # elements
    def add(**k): E.append(k)

    # 1. GARNISONS urbaines (occupation de bati) — taille par categorie
    for l in locs:
        sz = CAT_SIZE.get(l["cat"], 6)
        add(type="garrison", pos=[l["x"], l["y"]], size=sz, posture="AWARE", loadout="csat_rifle",
            hmg=(2 if l["cat"] == "ville" else 1 if l["cat"] == "bourg" else 0),
            name=l["nom"], cat=l["cat"], sector=l["sector"])

    # 2. QG DE THEATRE — plus gros centre (proxy aerodrome principal)
    hq = max(locs, key=lambda l: l.get("val", l.get("bati", 0)))
    add(type="theater_hq", pos=[hq["x"], hq["y"]], size=140, posture="SAFE", sector=hq["sector"], name="QG-THEATRE")

    # 3. SECTEURS : QG de secteur (FOB) + QRF, au plus gros centre de chaque secteur
    secs = {}
    for s in sorted(set(l["sector"] for l in locs)):
        sl = [l for l in locs if l["sector"] == s]
        shq = max(sl, key=lambda l: l.get("val", 0))
        secs[s] = dict(name=s, hq=[shq["x"], shq["y"]], alert="CALME", n_localites=len(sl))
        add(type="fob", pos=[shq["x"], shq["y"]], size=60, posture="AWARE", sector=s, name="FOB-" + s)
        add(type="qrf", pos=[shq["x"], shq["y"]], size=25, posture="SAFE", sector=s, name="QRF-" + s)
        # relais comms (dorsale) : 1 par secteur, sur une hauteur du secteur
        rel = max(sl, key=lambda l: l["h"])
        add(type="comms_relay", pos=[rel["x"], rel["y"]], size=4, posture="AWARE", sector=s, name="RELAIS-" + s)

    # 4. OP de hauteur — top-h (sites/pics dominants)
    for l in sorted(locs, key=lambda l: l["h"], reverse=True)[:16]:
        add(type="op", pos=[l["x"], l["y"]], size=5, posture="AWARE", sector=l["sector"], name="OP-" + l["nom"])

    # 5. CHECKPOINTS — points de route bien repartis (entrees/jonctions)
    for i, p in enumerate(farthest_sample(roadpts, 20)):
        add(type="checkpoint", pos=p, size=8, posture="AWARE", sector=sector_of(p[0], p[1], cx, cy), name="CP-%02d" % i)

    # 6. POSITIONS COTIERES — localites basses pres du bord de carte
    coast = [l for l in locs if l["h"] < 20 and (min(l["x"], size - l["x"]) < 3500 or min(l["y"], size - l["y"]) < 3500)]
    for l in coast[:6]:
        add(type="coastal", pos=[l["x"], l["y"]], size=10, posture="AWARE", sector=l["sector"], name="COTE-" + l["nom"])

    # 7. GBAD — pres du QG theatre + 2 secteurs
    for s, sd in list(secs.items())[:3]:
        add(type="gbad", pos=sd["hq"], size=5, posture="AWARE", sector=s, name="DCA-" + s)

    # 8. PATROUILLES motorisees — boucle autour d'un point de route par secteur
    patrol_centers = farthest_sample(roadpts, 12)
    for i, p in enumerate(patrol_centers):
        add(type="patrol", pos=p, size=8, radius=900, posture="AWARE",
            sector=sector_of(p[0], p[1], cx, cy), name="PATROUILLE-%02d" % i)

    # 9. CONVOIS logistiques — QG theatre -> chaque FOB
    for s, sd in secs.items():
        add(type="convoy", pos=[hq["x"], hq["y"]], size=10, posture="SAFE", sector=s,
            route=[[hq["x"], hq["y"]], sd["hq"]], name="CONVOI-" + s)

    # --- ECHELLE au TARGET (sur les effectifs "personnel a pied", pas les vehicules legers) ---
    scalable = ("garrison", "fob", "theater_hq", "op", "checkpoint", "coastal", "qrf")
    cur = sum(e["size"] for e in E if e["type"] in scalable)
    fixed = sum(e["size"] for e in E if e["type"] not in scalable)
    scale = max(0.1, (a.target - fixed) / max(1, cur))
    for e in E:
        if e["type"] in scalable:
            e["size"] = max(3, round(e["size"] * scale))
    total = sum(e["size"] for e in E)

    out = dict(world="Altis", target=a.target, seed=a.seed, scale=round(scale, 3),
               center=[round(cx), round(cy)], sectors=list(secs.values()),
               n_elements=len(E), total_units=total, elements=E)
    json.dump(out, open(os.path.join(ROOT, "staff", "occupation_altis.json"), "w"), indent=1)

    # --- resume ---
    from collections import Counter
    by_type = Counter(); units_type = Counter(); units_sec = Counter()
    for e in E:
        by_type[e["type"]] += 1; units_type[e["type"]] += e["size"]; units_sec[e.get("sector", "?")] += e["size"]
    print("=== LAYDOWN OCCUPATION ALTIS — target=%d seed=%d echelle=%.2f ===" % (a.target, a.seed, scale))
    print("Elements: %d  |  Unites totales: %d" % (len(E), total))
    print("--- par type (nb elements / unites) ---")
    for t in sorted(by_type, key=lambda t: -units_type[t]):
        print("  %-12s : %3d elem / %4d unites" % (t, by_type[t], units_type[t]))
    print("--- par secteur ---")
    for s in sorted(units_sec): print("  %-3s : %4d unites" % (s, units_sec[s]))
    print("ecrit -> staff/occupation_altis.json")

if __name__ == "__main__":
    main()
