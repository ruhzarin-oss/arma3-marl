#!/usr/bin/env python3
"""agg_ab3.py — agrège les runs A/B 3 bras -> tableau + VERDICT (géométrie vs suppression).
Lit ab3_*.json (leviathan/), moyenne par (défense N, mode). Métriques : FOB pris %, pertes WEST, EAST neutralisés."""
import glob, json, os, collections
D = "/home/younes/arma3-marl/leviathan"
runs = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(D, "ab3_*.json"))):
    try:
        m = json.load(open(f))["metrics"]
        parts = os.path.basename(f)[:-5].split("_")   # ab3_<N>_<mode>_<rep>
        N = int(parts[1]); mode = parts[2]
        runs[(N, mode)].append(m)
    except Exception as e:
        print("skip", f, e)

MODES = ["frontal", "supfront", "envelop"]; LABEL = {"frontal": "A frontal", "supfront": "B fix+front", "envelop": "C fix+FLANC"}
print("=== A/B 3 BRAS — moyennes (FOB pris %% | pertes WEST | EAST neutralisés) ===")
agg = {}
for N in (6, 8, 10):
    print("--- défense %d ---" % N)
    for mode in MODES:
        L = runs.get((N, mode), [])
        if not L:
            print("  %-14s : (aucun run)" % LABEL[mode]); continue
        took = 100.0 * sum(x["took"] for x in L) / len(L)
        wl = sum(x["west_losses"] for x in L) / len(L)
        en = sum(x["east_neutralized"] for x in L) / len(L)
        agg[(N, mode)] = (took, wl, en)
        print("  %-14s : pris %3.0f%% | pertes %.1f/%d | EAST neut %.1f | (n=%d)" % (LABEL[mode], took, wl, L[0]["nag"], en, len(L)))

# VERDICT global (moyenne sur défenses) : C>B>A géométrie ; C~B>A suppression
def avg_took(mode):
    v = [agg[(N, mode)][0] for N in (6, 8, 10) if (N, mode) in agg]
    return sum(v) / len(v) if v else None
tA, tB, tC = avg_took("frontal"), avg_took("supfront"), avg_took("envelop")
print("\n=== VERDICT (FOB pris %% moyen) : A=%s B=%s C=%s ===" % (
    "%.0f" % tA if tA is not None else "?", "%.0f" % tB if tB is not None else "?", "%.0f" % tC if tC is not None else "?"))
if None not in (tA, tB, tC):
    if tC - tB >= 15 and tB - tA >= 10:
        print(">>> C > B > A : LA GÉOMÉTRIE DE FLANC PAIE (au-delà de la suppression seule).")
    elif tB - tA >= 15 and abs(tC - tB) < 15:
        print(">>> C ~ B > A : c'est la SUPPRESSION seule qui paie ; le flanc est du folklore -> réorienter vers la brique suppression.")
    elif max(tA, tB, tC) < 15:
        print(">>> tous ~0 : défense trop dure (imprenable) -> baisser skill/N, le banc ne discrimine pas.")
    else:
        print(">>> signal ambigu -> plus de reps / ajuster la calibration.")
print("AGG_DONE")
