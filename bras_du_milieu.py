#!/usr/bin/env python3
"""LE BRAS DU MILIEU — courbe NEUVE, ÉQ. 1 ETEINTE.

Controle exige par Fable AVANT tout allumage : « sans lui, l allumage change deux choses a
la fois et aucun delta n est attribuable ; si un signe casse deja la, ÉQ. 1 n est pas
testable ». Meme reflexe que le controle de vacance avant un barreau.

A/B a une seule variable : la COURBE (+ son `degat_par_impact`, qui a change d unite avec
elle). ÉQ. 1 reste eteinte des deux cotes. Memes graines, memes doctrines SCRIPTEES —
jamais une politique apprise, qui melangerait le monde et l apprentissage.

SIGNES GELES A RETROUVER (mesures avant, ils ne sont pas negociables) :
  · flanc − frontal = +17,3 points
  · doctrine scriptee 91,0 % contre 35,0 % pour le cap tire au hasard
Si l un casse, ce n est pas ÉQ. 1 qui est en cause : c est la courbe, et on le saura AVANT
d avoir allume quoi que ce soit.
"""
import sys, json, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from monde_fidele import MONDE_ARMA, COURBE, DEGAT_PAR_IMPACT
from distillation import cible_shamal

LEV = "/home/younes/arma3-marl/leviathan"
ANCIENNE = LEV + "/courbe_toucher_monotone.json"
GRAINES = [901, 902, 903, 904, 905, 906]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 256
SORTIE = "/home/younes/arma3-marl/bras_du_milieu.json"

BRAS = {
    "ancienne (26/07, 0,233)": dict(MONDE_ARMA, courbe=ANCIENNE, degat_par_impact=0.233),
    "neuve (rang 1-10, 0,175)": dict(MONDE_ARMA),
}

def scripte(fn):
    def choisir(o, t):
        a = fn(B._E, t)
        z = torch.zeros(a.shape[0], device=a.device)
        return a, z, z
    return choisir

DOCTRINES = {
    "frontal": lambda e, t: B.frontal(e, t),
    "flanc": lambda e, t: B.flanc(e, t),
    "shamal": lambda e, t: cible_shamal(e),
    "shamal_hasard": lambda e, t: cible_shamal(e, hasard=True),
}

res = {}
for nom_bras, cfg in BRAS.items():
    B.CFG = cfg
    res[nom_bras] = {}
    for nom_d, fn in DOCTRINES.items():
        prises = []
        for g in GRAINES:
            e = B.monde(N, g)
            B._E = e
            st, *_ = B.jouer(e, scripte(fn))
            prises.append(st["prise"])
        m = sum(prises) / len(prises)
        et = (sum((x - m) ** 2 for x in prises) / max(len(prises) - 1, 1)) ** 0.5
        demi = 1.96 * et / len(prises) ** 0.5
        res[nom_bras][nom_d] = dict(moyenne=m, demi_ic=demi, par_graine=prises)
        print("  %-26s %-14s %5.1f %%  ± %.1f  (%s)"
              % (nom_bras, nom_d, m, demi, " ".join("%.0f" % x for x in prises)), flush=True)

print("\n  " + "=" * 72)
print("  SIGNES GELES")
for nom_bras in BRAS:
    r = res[nom_bras]
    ecart_flanc = r["flanc"]["moyenne"] - r["frontal"]["moyenne"]
    ecart_doct = r["shamal"]["moyenne"] - r["shamal_hasard"]["moyenne"]
    print("\n  %s" % nom_bras)
    print("    flanc − frontal ......... %+.1f pts   (gele : +17,3)" % ecart_flanc)
    print("    doctrine − hasard ....... %+.1f pts   (gele : 91,0 − 35,0 = +56,0)" % ecart_doct)
    print("    doctrine absolue ........ %.1f %%     (gele : 91,0 %%)" % r["shamal"]["moyenne"])
    print("    SIGNE flanc : %s · SIGNE doctrine : %s"
          % ("TENU" if ecart_flanc > 0 else "⛔ CASSE",
             "TENU" if ecart_doct > 0 else "⛔ CASSE"))
json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False)
print("\n  ecrit : %s" % SORTIE)
