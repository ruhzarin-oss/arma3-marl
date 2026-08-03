#!/usr/bin/env python3
"""agg_ratio — le balayage du rapport de forces, juge par les criteres figes.

Criteres : leviathan/CRITERES_RATIO_FIBUA.md (empreinte e6a252be9eaf62a3)
Juge : PRISE-A-PERTES = prise / pertes par prise. Repli declare d avance : penetration
et taux d echange.
"""
import glob
import json
import os
import collections

LEV = "/home/younes/arma3-marl/leviathan"
MODES = ["frontal", "supfront", "envelop"]
LAB = {"frontal": "A frontal", "supfront": "B fix+front", "envelop": "C fix+FLANC"}

runs = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(LEV, "ratio_*.json"))):
    try:
        m = json.load(open(f))["metrics"]
        p = os.path.basename(f)[:-5].split("_")     # ratio_<nag>_<mode>_<rep>
        runs[(int(p[1]), p[2])].append(m)
    except Exception as e:
        print("ignore %s (%s)" % (f, e))


def med(v):
    v = sorted(v)
    n = len(v)
    return float("nan") if not n else (v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2]))


NAGS = sorted({k[0] for k in runs})
agg = {}
print("=== BALAYAGE DU RAPPORT DE FORCES — 8 defenseurs au FOB Maxwell (garnison RECONSTRUITE) ===")
print("  juge : PRISE-A-PERTES = prise / pertes par prise")
for nag in NAGS:
    print("")
    print("--- %d attaquants contre 8 (rapport %.2f:1) ---" % (nag, nag / 8.0))
    print("  %-13s %4s %8s %10s %13s %11s %9s" %
          ("bras", "n", "prise", "pertes/ep", "PRISE-A-PERT", "penetr(m)", "E neutr"))
    for mode in MODES:
        L = runs.get((nag, mode), [])
        if not L:
            print("  %-13s   (aucun run)" % LAB[mode])
            continue
        n = len(L)
        pris = sum(1 for x in L if x["took"])
        prise = pris / float(n)
        pertes = sum(x["west_losses"] for x in L) / float(n)
        ppp = (sum(x["west_losses"] for x in L) / float(pris)) if pris else float("nan")
        pap = (prise / ppp) if (ppp == ppp and ppp > 0) else float("nan")
        pen = med([x["min_fob_dist"] for x in L])
        neu = sum(x["east_neutralized"] for x in L) / float(n)
        agg[(nag, mode)] = {"n": n, "prise": prise, "pertes": pertes, "ppp": ppp,
                            "pap": pap, "pen": pen, "neu": neu}
        print("  %-13s %4d %7.0f%% %10.2f %13s %11.0f %9.1f"
              % (LAB[mode], n, 100 * prise, pertes,
                 ("%.2f" % pap) if pap == pap else "n/a", pen, neu))

print("")
print("=== VERDICTS (seuils figes e6a252be9eaf62a3) ===")

# CONTRE-EPREUVE a nag=12
ce = None
if all((12, m) in agg for m in MODES):
    A, B, C = (agg[(12, m)] for m in MODES)
    c1 = A["pertes"] > B["pertes"] and A["pertes"] > C["pertes"]
    c2 = C["neu"] >= 2 * B["neu"] if B["neu"] > 0 else C["neu"] > 0
    c3 = C["pen"] < B["pen"]
    ce = c1 and c2 and c3
    print("  CONTRE-EPREUVE a 12 attaquants (classement du 23/07) :")
    print("    pertes(A) > pertes(B) et > pertes(C)   : %s  (%.2f | %.2f | %.2f)"
          % ("OK" if c1 else "NON", A["pertes"], B["pertes"], C["pertes"]))
    print("    neutralises(C) >= 2 x neutralises(B)   : %s  (%.1f vs %.1f)"
          % ("OK" if c2 else "NON", C["neu"], B["neu"]))
    print("    penetration(C) < penetration(B)        : %s  (%.0f m vs %.0f m)"
          % ("OK" if c3 else "NON", C["pen"], B["pen"]))
    print("    -> %s" % ("CONTRE-EPREUVE PASSEE" if ce else
                         "CONTRE-EPREUVE ECHOUEE : le balayage n est PAS concluant"))
else:
    print("  CONTRE-EPREUVE : pas de run a 12 attaquants.")

# POINT DE CERTIFICATION
print("")
print("  POINT DE CERTIFICATION (les 3 conditions ensemble) :")
trouve = None
for nag in NAGS:
    if (nag, "frontal") not in agg or (nag, "envelop") not in agg:
        continue
    A = agg[(nag, "frontal")]; C = agg[(nag, "envelop")]
    d = C["prise"] - A["prise"]
    ok1 = d >= 0.25
    ok2 = A["prise"] <= 0.50
    ok3 = C["prise"] >= 0.40
    print("    %2d att. : ecart C-A = %+5.0f pts (>=25 : %s) | prise A %3.0f%% (<=50 : %s) | prise C %3.0f%% (>=40 : %s)"
          % (nag, 100 * d, "oui" if ok1 else "non", 100 * A["prise"], "oui" if ok2 else "non",
             100 * C["prise"], "oui" if ok3 else "non"))
    if ok1 and ok2 and ok3 and trouve is None:
        trouve = nag
if trouve is not None:
    print("    -> POINT DE CERTIFICATION = %d attaquants contre 8 (rapport %.2f:1)."
          % (trouve, trouve / 8.0))
    print("       C EST CE POINT QUE LE SANDBOX DOIT REPRODUIRE. Jamais l inverse.")
else:
    print("    -> AUCUN rapport ne separe frontal et crochet selon les trois conditions.")
    print("       On passe au critere de repli, declare d avance.")
    print("")
    print("  REPLI — penetration et pertes :")
    for nag in NAGS:
        if (nag, "frontal") not in agg or (nag, "envelop") not in agg:
            continue
        A = agg[(nag, "frontal")]; C = agg[(nag, "envelop")]
        okp = C["pen"] <= A["pen"] - 25
        okc = C["pertes"] < A["pertes"]
        print("    %2d att. : penetr C %3.0f m vs A %3.0f m (-25 m : %s) | pertes C %.2f vs A %.2f (%s) -> %s"
              % (nag, C["pen"], A["pen"], "oui" if okp else "non", C["pertes"], A["pertes"],
                 "oui" if okc else "non", "SEPARE" if (okp and okc) else "ne separe pas"))
print("AGGRATIO_DONE")
