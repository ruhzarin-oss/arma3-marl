#!/usr/bin/env python3
"""hysteresis — LA LAME REJOUEE. Le 55,8 % de bascule etait SANS hysteresis.

⟨Fable⟩ « Rejoue la table avec hysteresis sur les logs EXISTANTS. Si le taux tombe sous 10 %,
la lame re-tranche AVANT la campagne, gratuitement. »

Rien de neuf n est mesure ici : on relit les 128 etats deja enregistres. C est une lame, pas
une experience — elle ne peut que TUER la brique, jamais la valider.

DEUX VERROUS, ecrits avant de lire le resultat :
  1. une bascule n est autorisee que si la forme courante a eu le temps d etre ATTEINTE
     (delai = le temps d assemblage MESURE, pas choisi) ;
  2. le nouveau regime doit etre confirme sur DEUX lectures consecutives.

SEUIL DE MORT : < 10 % de bascule => la regle ne dit presque jamais rien d autre que « reste »,
et la campagne comparerait deux bras identiques. On ne paie pas 26 h pour ca.
"""
import json, sys
import numpy as np

ETATS = json.load(open('/mnt/data/desaccord_formation.json'))['etats']
try:
    DELAI = json.load(open('/mnt/data/assemblage.json'))['mediane']
except Exception:
    DELAI = float(sys.argv[1]) if len(sys.argv) > 1 else None

# La table, TELLE QUE DEPOSEE (terciles seuls), avec la correspondance eventail -> cercle.
def regime(intensite, entropie):
    if intensite <= 8.0:  return "colonne"
    if intensite >= 15.1: return "losange" if entropie >= 0.88 else "ligne"
    return "coin" if entropie < 0.88 else "cercle"

def rejouer(delai, confirmation=2):
    """Renvoie (taux de bascule, occupations, nb de decisions)."""
    bascules = decisions = 0
    occ = {}
    for sc in sorted({e["sc"] for e in ETATS}):
        série = sorted((e for e in ETATS if e["sc"] == sc), key=lambda e: e["t"])
        courante = None; t_pose = -1e9; candidat = None; n_conf = 0
        for e in série:
            r = regime(e["intensite"], e["entropie"])
            if courante is None:                      # la premiere prise n est pas une bascule
                courante = r; t_pose = e["t"]; occ[r] = occ.get(r, 0) + 1; continue
            decisions += 1
            occ[courante] = occ.get(courante, 0) + 1
            if r == courante:
                candidat = None; n_conf = 0; continue
            n_conf = n_conf + 1 if r == candidat else 1
            candidat = r
            if n_conf >= confirmation and (e["t"] - t_pose) >= delai:   # VERROU 1 et VERROU 2
                courante = r; t_pose = e["t"]; bascules += 1; candidat = None; n_conf = 0
    return (bascules / decisions if decisions else 0.0), occ, decisions

if __name__ == "__main__":
    if DELAI is None:
        sys.exit("le temps d assemblage n est pas encore mesure — la lame ne peut pas etre reglee")
    print("=" * 92); print(" LA LAME REJOUEE — table + hysteresis dimensionnee"); print("=" * 92)
    print("  %d etats sur %d scenes | delai MESURE = %.0f s | confirmation = 2 lectures"
          % (len(ETATS), len({e["sc"] for e in ETATS}), DELAI))
    print("\n  temoin — SANS hysteresis (le chiffre d hier) :")
    t0, o0, d0 = rejouer(0.0, 1)
    print("    taux de bascule %.1f %%  sur %d decisions" % (100 * t0, d0))
    print("\n  AVEC les deux verrous :")
    t, o, d = rejouer(DELAI, 2)
    tot = sum(o.values())
    print("    ⭐ taux de bascule %.1f %%  sur %d decisions" % (100 * t, d))
    print("    occupation des regimes :")
    for k, v in sorted(o.items(), key=lambda kv: -kv[1]):
        part = 100 * v / tot
        drap = "   ⚠️ INFALSIFIABLE (< 5 %)" if part < 5.0 else ""
        print("      %-9s %5.1f %%%s" % (k, part, drap))
    print("\n  sensibilite au delai (la lame doit tenir sur la plage, pas sur un point) :")
    for dl in (0.5 * DELAI, DELAI, 1.5 * DELAI, 2.0 * DELAI):
        tt, _, dd = rejouer(dl, 2)
        print("      delai %5.0f s -> %5.1f %%" % (dl, 100 * tt))
    print("\n" + "─" * 92)
    if t < 0.10:
        print("  ⛔ LA LAME TRANCHE : %.1f %% < 10 %%. Avec le temps d assemblage reel, la regle ne dit" % (100 * t))
        print("     presque jamais autre chose que « reste ». La campagne comparerait deux bras")
        print("     identiques. LA BRIQUE MEURT ICI — une heure payee au lieu de vingt-six.")
    else:
        print("  ✅ la lame ne tranche pas : %.1f %% ≥ 10 %%. La regle bascule encore assez pour" % (100 * t))
        print("     que `bascule` et `eventail_fixe` soient deux bras DIFFERENTS. On peut hacher.")
    json.dump({"taux_sans": t0, "taux_avec": t, "delai": DELAI, "occ": o, "decisions": d},
              open('/mnt/data/hysteresis.json', 'w'), indent=1)
