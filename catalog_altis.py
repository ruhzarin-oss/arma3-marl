"""catalog_altis (v7) — SQF EXACT de scout_towns (qui marche) : nom + position + altitude + densite de bati.
Classification par densite (ville/bourg/village/site). Catalogue Altis complet -> staff/altis_catalog.json."""
import re, json
from collections import Counter
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = (
    'private _locs = nearestLocations [[15360,15360,0], ["NameCityCapital","NameCity","NameVillage","NameLocal"], 36000];\n'
    '{ private _p = locationPosition _x;\n'
    '  private _nb = ({_x isKindOf "House"} count (_p nearObjects ["House", 150]));\n'
    '  diag_log format ["HARMATTAN_TOWN nom=%1 x=%2 y=%3 h=%4 bati=%5", text _x, round (_p#0), round (_p#1), round (getTerrainHeightASL _p), _nb];\n'
    '} forEach _locs;\n'
    'diag_log "HARMATTAN_CATDONE";\n'
)
ls = env._query(sqf, settle=3.0)


def classe(bati, h):
    if bati >= 100: return "ville"
    if bati >= 45: return "bourg"
    if bati >= 18: return "village"
    if bati >= 6: return "hameau"
    return "site"


locs = {}
nraw = 0
for l in ls:
    m = re.search(r"HARMATTAN_TOWN nom=(.+?) x=(-?\d+) y=(-?\d+) h=(-?\d+) bati=(\d+)", l)
    if not m:
        continue
    nraw += 1
    nom, x, y, h, bati = m.group(1).strip(), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
    if not nom or bati == 0 and h < 5:
        continue
    cat = classe(bati, h)
    val = bati + (h // 4 if h > 80 else 0)
    o = {"nom": nom, "cat": cat, "x": x, "y": y, "h": h, "bati": bati, "val": val}
    if nom not in locs or val > locs[nom]["val"]:
        locs[nom] = o
cat = sorted(locs.values(), key=lambda o: -o["val"])
json.dump({"world": "Altis", "size": 30720, "objectifs": cat}, open("/home/younes/arma3-marl/staff/altis_catalog.json", "w"))
print("brutes=%d | CATALOGUE ALTIS : %d objectifs | %s" % (nraw, len(cat), dict(Counter(o["cat"] for o in cat))))
for o in cat[:16]:
    print("  %-16s %-8s (%5d,%5d) h=%3dm bati=%3d" % (o["nom"][:16], o["cat"], o["x"], o["y"], o["h"], o["bati"]))
