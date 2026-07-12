"""analyze_geo — lit la matrice GEOMETRIE (mxg_<geo>_<man>.jsonl) et repond a LA question :
le vainqueur tourne-t-il selon la geometrie ? Calcule la VALEUR DE SELECTION (adaptatif - meilleur fixe)."""
import json
import numpy as np

import glob, re
GEOS = ["standard", "concentre", "disperse", "faible_ouest", "faible_est"]
# decouvre les manoeuvres reellement presentes (s'adapte a la matrice etendue M1/M2/M3/M5/M8...)
_mans = set()
for f in glob.glob("mxg_*_M*.jsonl"):
    m = re.search(r"_M(\d+)\.jsonl$", f)
    if m:
        _mans.add(int(m.group(1)))
ATKS = ["M%d" % n for n in sorted(_mans)] or ["M1", "M2", "M3"]


def rate(geo, man):
    try:
        rows = [json.loads(l) for l in open("mxg_%s_%s.jsonl" % (geo, man))]
    except FileNotFoundError:
        return None
    ok = [r for r in rows if "mil" in r]
    if not ok:
        return None
    return 100 * sum(r["mil"] for r in ok) / len(ok), len(ok)


print("=== MATRICE GEOMETRIE : succes militaire (%) | ennemi=skilled, seule la GEOMETRIE change ===")
print("%-13s" % "geometrie" + "".join("%9s" % m for m in ATKS) + "    vainqueur")
percol = {m: [] for m in ATKS}; best_per_geo = []
for geo in GEOS:
    cells = {m: rate(geo, m) for m in ATKS}
    line = "%-13s" % geo; best = None; bestv = -1
    for m in ATKS:
        c = cells[m]
        if c:
            line += "%7.0f%%" % c[0] + ("*" if False else " ")
            percol[m].append(c[0])
            if c[0] > bestv: bestv = c[0]; best = m
        else:
            line += "%9s" % "-"
    if best is not None:
        best_per_geo.append(bestv)
        line += "    %s (%.0f%%)" % (best, bestv)
    print(line)

if best_per_geo and any(percol.values()):
    best_fixed_man = max(percol, key=lambda m: np.mean(percol[m]) if percol[m] else -1)
    best_fixed = np.mean(percol[best_fixed_man])
    adaptive = np.mean(best_per_geo)
    sel = adaptive - best_fixed
    print("\nMeilleure manoeuvre FIXE = %s (%.0f%% moyen sur geometries)" % (best_fixed_man, best_fixed))
    print("Adaptatif (meilleure PAR geometrie) = %.0f%% moyen" % adaptive)
    print("VALEUR DE SELECTION = %+.0f points   (la session 'postures' donnait +4.7 = marginal)" % sel)
    print(">>> %s" % ("LE VAINQUEUR TOURNE -> commander PAIE -> GATE FRANCHIE" if sel >= 10
                      else "rotation faible -> gate NON franchie (M3 domine encore)"))
