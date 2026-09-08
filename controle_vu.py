#!/usr/bin/env python3
"""HMT-19, CONTROLE (i) — le multiplicateur « etre vu » du gymnase entre-t-il dans l IC d Arma ?

Arma, certifie sur 563 000 observations : etre vu multiplie la mortalite par **1,75** (+75 %).
Le gymnase, lui, a ete mesure a **+856 %** (rapport 9,56) : le couvert y est un INTERRUPTEUR,
pas une attenuation. C est l ecart que `canal_cwr` est cense corriger.

⚠️ CE CONTROLE PEUT ECHOUER, et c est son interet. Fable, 08/09 :
    « Niveau dedans avec multiplicateur dehors = COMPENSATION -> refus. »
Un monde qui rend la bonne prise avec le mauvais multiplicateur a deux erreurs qui se
compensent — c est le piege exact de `26/07 . 0,233`.

L etiquette « vu » est prise sur `_vu_geo`, la visibilite GEOMETRIQUE relevee AVANT tout
bouton : sans ca l etiquette derive avec le traitement, et le contraste monte avec le bouton
qu on veut mesurer (856 % puis 4086 % au premier balayage du 16/08).
"""
import sys, json, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from monde_fidele import MONDE_ARMA
from assault_terrain import AssaultTerrain
from distillation import cible_shamal
import canal_cwr as CANAL

GRAINES = [901, 902, 903, 904, 905, 906]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 192
PAS = 92
ARMA_RATIO, ARMA_LO, ARMA_HI = 1.75, 1.60, 1.92   # +75 % certifie, bande de lecture
SORTIE = "/home/younes/arma3-marl/controle_vu.json"

BRAS = {
    "canal ETEINT (reference)": dict(),
    "canal ALLUME (mesure)": dict(canal_cwr=CANAL.constantes_arma3()),
}


def monde(n, seed, sur):
    cfg = dict(MONDE_ARMA, **sur)
    return AssaultTerrain(num_envs=n, seed=seed, device="cuda:0", max_steps=PAS,
                          A=8, D=4, R_spawn=220.0, terr_R=260.0, **cfg)


def mesurer(e):
    """Rend (degats subis par les VUS, leur nombre, degats des NON VUS, leur nombre)."""
    e.reset()
    dv = dn = 0.0; nv = nn = 0
    for t in range(PAS):
        a = cible_shamal(e)
        e.step(a, auto_reset=False)
        vu = (e._vu_geo > 0.5)
        viv = e._aalive()
        d = e.last_dmg_in
        dv += float((d * (vu & viv)).sum()); nv += int((vu & viv).sum())
        dn += float((d * (~vu & viv)).sum()); nn += int((~vu & viv).sum())
    return dv, nv, dn, nn


res = {}
for nom, sur in BRAS.items():
    DV = NV = DN = NN = 0.0
    for g in GRAINES:
        a, b, c, d = mesurer(monde(N, g, sur))
        DV += a; NV += b; DN += c; NN += d
    mv = DV / max(NV, 1); mn = DN / max(NN, 1)
    r = (mv / mn) if mn > 0 else float("inf")
    res[nom] = dict(dmg_vu=mv, dmg_non_vu=mn, rapport=r, n_vu=NV, n_non_vu=NN)
    print("  %-26s  vu %.5f · non vu %.5f · rapport %s"
          % (nom, mv, mn, ("%.2f" % r) if r != float("inf") else "INFINI"), flush=True)

print("\n  " + "=" * 70)
print("  ARMA, certifie sur 563 000 observations : rapport 1,75 (bande %.2f - %.2f)"
      % (ARMA_LO, ARMA_HI))
for nom, v in res.items():
    r = v["rapport"]
    dedans = (r != float("inf")) and (ARMA_LO <= r <= ARMA_HI)
    print("  %-26s rapport %-8s %s"
          % (nom, ("%.2f" % r) if r != float("inf") else "INFINI",
             "DANS la bande d Arma" if dedans else "HORS"))
r = res["canal ALLUME (mesure)"]["rapport"]
print()
if r == float("inf") or r > ARMA_HI:
    print("  ⛔ CONTROLE (i) ECHOUE : le couvert reste trop protecteur (%s contre 1,75)."
          % (("%.2f" % r) if r != float("inf") else "INTERRUPTEUR ABSOLU"))
    print("     Le canal ne suffit pas — le troisieme parametre est bien le COUVERT,")
    print("     et il faudra la nuit d extension de HitPart aux conditions de couvert.")
elif r < ARMA_LO:
    print("  ⛔ CONTROLE (i) ECHOUE dans l autre sens : le couvert ne protege plus assez (%.2f)." % r)
else:
    print("  ✔ CONTROLE (i) PASSE : rapport %.2f, dans la bande d Arma." % r)
    print("     ⚠️ Il reste le controle (ii), qui exige l ancre — il ne peut pas se jouer avant HMT-18.")
json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
print("  ecrit : %s" % SORTIE)
