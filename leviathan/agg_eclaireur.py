#!/usr/bin/env python3
"""agg_eclaireur — la grille de l'eclaireur FIBUA, et OU Arma separe le mieux.

Ce n'est PAS une certification : c'est un reperage. On cherche la case ou l'ecart entre
« sans appui » et « avec fixeurs » est le plus net, pour que la certification de demain
parte de la bonne configuration.
"""
import glob
import json
import os
import collections

LEV = "/home/younes/arma3-marl/leviathan"
import sys
PREF = sys.argv[1] if len(sys.argv) > 1 else "ecl"
FORME = ("LIGNE etalee devant l objectif (geometrie certifiee)" + (", part d assaillants 0,75" if PREF == "eclf" else ", part d assaillants 0,45")) if PREF in ("ecll", "eclf") else "ANNEAU a 20 m autour du FOB"
LAB = {"frontal": "sans appui", "envelop": "avec fixeurs"}

runs = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(LEV, PREF + "_*.json"))):
    try:
        m = json.load(open(f))["metrics"]
        p = os.path.basename(f)[:-5].split("_")     # ecl_<nag>_<mode>_<rep>
        runs[(int(p[1]), p[2])].append(m)
    except Exception as e:
        print("ignore %s (%s)" % (os.path.basename(f), e))


def med(v):
    v = sorted(v)
    n = len(v)
    return float("nan") if not n else (v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2]))


NAGS = sorted({k[0] for k in runs})
agg = {}
print("")
print("=== ECLAIREUR FIBUA — 8 defenseurs POSES PAR SCRIPT au FOB Maxwell ===")
print("    forme de la garnison : " + FORME)
print("    reperage, PAS certification")
print("")
print("  %-6s %-14s %4s %8s %11s %14s %11s %9s"
      % ("att.", "appui", "n", "prise", "pertes/ep", "PRISE-A-PERTES", "penetr(m)", "E neutr"))
for nag in NAGS:
    for mode in ("frontal", "envelop"):
        L = runs.get((nag, mode), [])
        if not L:
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
        print("  %-6d %-14s %4d %7.0f%% %11.2f %14s %11.0f %9.1f"
              % (nag, LAB[mode], n, 100 * prise, pertes,
                 ("%.2f" % pap) if pap == pap else "n/a", pen, neu))

print("")
print("=== OU ARMA SEPARE-T-IL LE MIEUX ? ===")
best = None
for nag in NAGS:
    A = agg.get((nag, "frontal"))
    C = agg.get((nag, "envelop"))
    if not A or not C:
        continue
    d_prise = C["prise"] - A["prise"]
    d_pertes = A["pertes"] - C["pertes"]
    d_pen = A["pen"] - C["pen"]
    # score de separation : ecart de prise en points, + le gain de penetration ramene a 100 m
    score = 100 * d_prise + d_pen
    print("  %2d contre 8 : ecart de prise %+5.0f pts | pertes evitees %+5.2f | penetration gagnee %+5.0f m  (score %.0f)"
          % (nag, 100 * d_prise, d_pertes, d_pen, score))
    if best is None or score > best[1]:
        best = (nag, score, d_prise, d_pertes, d_pen)
print("")
if best and best[2] > 0:
    print("  -> MEILLEURE SEPARATION EN FAVEUR DU FLANC : %d attaquants contre 8 (rapport %.2f:1)."
          % (best[0], best[0] / 8.0))
    print("     Case a certifier demain, gros n et criteres haches.")
elif best:
    print("  -> AUCUN REGIME NE FAIT PAYER LE FLANC. Dans TOUTES les cases, l'appui prend")
    print("     MOINS et perd PLUS que l'assaut frontal. La separation existe — elle est")
    print("     simplement dans l'autre sens.")
    print("")
    if PREF in ("ecll", "eclf"):
        print("  Cette grille utilise la geometrie CERTIFIEE (ligne devant l'objectif).")
        print("  Le resultat negatif ne peut donc plus etre impute a la forme de la garnison.")
        print("  A NOMMER quand meme : avec fixeurs, seuls 45 pour cent des hommes assautent")
        print("  (flank=0.45). Sur un banc ou prendre exige des hommes A MOINS DE 25 m,")
        print("  l'appui part avec deux fois moins d'assaillants. C'est le prix de la")
        print("  doctrine, pas un biais — mais il faut le dire avant de conclure.")
        _saut = True
    else:
        _saut = False
    if not _saut:
      print("  !! DEFAUT DE DISPOSITIF A DIRE AVANT TOUTE LECTURE :")
      print("     la garnison posee par poser_fob.py est un ANNEAU de 8 hommes a 20 m")
      print("     autour du FOB. Or c'est exactement la geometrie dont le projet sait deja")
      print("     qu'elle ne recompense PAS le contournement : « on ne flanque pas un point »")
      print("     (certification du 22/07). La geometrie qui certifie est une LIGNE etalee")
      print("     DEVANT l'objectif, face au dehors.")
      print("     Ce que cet eclaireur mesure peut donc etre MON ANNEAU, pas le monde d'Arma.")
else:
    print("  -> aucune case complete : rien a reperer.")
json.dump({str(k): v for k, v in agg.items()}, open(LEV + "/eclaireur_fibua_%s.json" % PREF, "w"), indent=1)
print("-> leviathan/eclaireur_fibua_%s.json" % PREF)
print("AGGECL_DONE")
