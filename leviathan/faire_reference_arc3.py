#!/usr/bin/env python3
"""LA REFERENCE DU CONE DUR, POUR LA GEOMETRIE OU L'ARC EXISTE VRAIMENT.

`reverdict_arc2` ne fixait PAS `def_arc` : il prenait le defaut, un demi-angle de 180 deg.
Le cone couvrait le cercle entier, il n'y avait aucun angle mort, et le flanc ne pouvait pas
etre dehors — on mesurait un arc en testant l'absence d'arc. `reverdict_arc3` pose un cone
de 120 deg et une geometrie fixe.

Mais en corrigeant la geometrie, le TEMOIN a cesse d'etre comparable a sa reference figee
(19,3 % / 74,7 %), qui appartenait a l'ancienne. La contre-epreuve a echoue, et les criteres
ont donc refuse de conclure — ce qui est leur travail.

Ce script refait la reference POUR CETTE GEOMETRIE. Deux precautions pour qu'elle ne soit
pas une tautologie :

  - GRAINES DIFFERENTES de celles du re-verdict (11..16 contre 7,8,9). Reproduire une
    reference mesuree sur ses PROPRES graines ne prouverait rien.
  - PLUS D'EPISODES par graine, et la tolerance derivee de la DISPERSION observee entre
    graines, pas d'un chiffre choisi a la main.

Elle ne mesure QUE le cone dur : c'est le temoin, pas le monde qu'on juge.
"""
import sys
import json
import math
import time

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import torch  # noqa: F401  (importe par le module de re-verdict)

# On reutilise EXACTEMENT le monde et les doctrines du re-verdict : une reference mesuree
# avec un autre code ne serait pas une reference.
_CIBLE = "--cible" in sys.argv[1:]
sys.argv = ["reverdict_arc3.py", "--eval", "2048"] + (["--cible"] if _CIBLE else [])
import reverdict_arc3 as R

GRAINES = (11, 12, 13, 14, 15, 16)
OUT = "/home/younes/arma3-marl/leviathan/reference_arc3%s.json" % ("_cible" if _CIBLE else "")

if __name__ == "__main__":
    t0 = time.time()
    print("=== REFERENCE DU CONE DUR — geometrie a cone de 120 deg, fixe ===", flush=True)
    print("    %d graines (%s), %d episodes chacune | A=4 D=8"
          % (len(GRAINES), ",".join(str(g) for g in GRAINES), 2048), flush=True)
    print("    graines VOLONTAIREMENT differentes de celles du re-verdict (7,8,9)", flush=True)
    print("", flush=True)

    par_graine = {"frontal": [], "crochet": []}
    for g in GRAINES:
        f = R.joue(None, "frontal", g)
        c = R.joue(None, "flanc", g)
        par_graine["frontal"].append(f["prise"])
        par_graine["crochet"].append(c["prise"])
        print("  graine %2d : frontal %5.1f %%   crochet %5.1f %%"
              % (g, 100 * f["prise"], 100 * c["prise"]), flush=True)

    def stat(v):
        m = sum(v) / len(v)
        et = (sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1)) ** 0.5
        return m, et

    mf, ef = stat(par_graine["frontal"])
    mc, ec = stat(par_graine["crochet"])
    # Tolerance = 3 ecarts-types entre graines, plancher a 5 points. On ne choisit pas un
    # chiffre : on lit la dispersion que le monde produit deja tout seul.
    tol = max(0.05, 3.0 * max(ef, ec))

    print("", flush=True)
    print("  frontal : %5.1f %%  (ecart-type entre graines %.1f pt)" % (100 * mf, 100 * ef), flush=True)
    print("  crochet : %5.1f %%  (ecart-type entre graines %.1f pt)" % (100 * mc, 100 * ec), flush=True)
    print("  tolerance retenue : +-%.1f pt  (3 ecarts-types, plancher 5 pt)" % (100 * tol), flush=True)

    json.dump({"geometrie": "def_arc=pi/3 (cone 120 deg), def_rand=False, A=4, D=8",
               "graines": list(GRAINES), "episodes_par_graine": 2048,
               "frontal_prise": mf, "crochet_prise": mc,
               "ecart_type_frontal": ef, "ecart_type_crochet": ec,
               "tolerance": tol,
               "par_graine": par_graine},
              open(OUT, "w"), indent=1)
    print("", flush=True)
    print("-> %s  (%d s)" % (OUT, time.time() - t0), flush=True)
    print("REFERENCE_DONE", flush=True)
