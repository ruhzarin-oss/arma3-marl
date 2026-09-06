#!/usr/bin/env python3
"""POINT 2 DE FABLE — COMPARER LES NIVEAUX, PAS LES SIGNES.

« Rejoue A/B/C dans le gymnase, meme 8 contre 4, 220 m, 300 s, et rends les six chiffres
cote a cote : c est l ecart de NIVEAU qui departage les courbes, pas le signe. »

Ce qu Arma a rendu, a scenario egal (14 episodes par bras, canari et controle passes) :
    A frontal            0,357  [0,163 ; 0,612]
    B fixeurs + frontal  0,214  [0,076 ; 0,476]
    C fixeurs + flanc    0,214  [0,076 ; 0,476]

Une courbe du gymnase qui rend 73 % ou 99 % sur ce dispositif est REFUTEE PAR LE NIVEAU,
meme si son signe est juste — ces valeurs tombent hors des IC d Arma. C est ce test-la qui
departage, et il ne coute pas une minute d Arma.

⚠️ Le gymnase joue 4 contre 4 par defaut : on le met a 8 contre 4, a 220 m, sur 92 pas
(300 s / 3,28 s par pas), pour que la comparaison soit a dispositif EGAL.
"""
import sys, json, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from monde_fidele import MONDE_ARMA
from assault_terrain import AssaultTerrain

LEV = "/home/younes/arma3-marl/leviathan"
ANCIENNE = LEV + "/courbe_toucher_monotone.json"
GRAINES = [901, 902, 903, 904, 905, 906]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 256
PAS = 92                     # 300 s / 3,28 s par pas — la duree d Arma
SORTIE = "/home/younes/arma3-marl/niveaux_abc_croise.json"

ARMA = {"A frontal": (0.357, 0.163, 0.612),
        "B fixeurs+frontal": (0.214, 0.076, 0.476),
        "C fixeurs+flanc": (0.214, 0.076, 0.476)}

# POINT 3 DE FABLE, FAIT PAR MESURE ET NON PAR PONDERATION DEVINEE.
# L ancienne courbe passe le test de niveau APPARIEE a `degat_par_impact` = 0,233 — et les
# deux viennent du compteur qui SUR-COMPTAIT. Deux erreurs qui se compensent produisent aussi
# un bon niveau. On teste donc les appariements CROISES pour isoler lequel des deux composants
# est en cause, au lieu de declarer l ancienne courbe correcte sur un accord global.
HITPART = LEV + "/courbe_toucher_hitpart.json"        # remesuree, TOUS RANGS
RANG = LEV + "/courbe_toucher_rang1_10.json"          # remesuree, coups 1-10 seulement
COURBES = {
    "26/07 · 0,233": dict(courbe=ANCIENNE, degat_par_impact=0.233),
    "26/07 · 0,175": dict(courbe=ANCIENNE, degat_par_impact=0.175),
    "HitPart tous rangs · 0,233": dict(courbe=HITPART, degat_par_impact=0.233),
    "HitPart tous rangs · 0,175": dict(courbe=HITPART, degat_par_impact=0.175),
    "rang 1-10 · 0,233": dict(courbe=RANG, degat_par_impact=0.233),
    "rang 1-10 · 0,175": dict(courbe=RANG, degat_par_impact=0.175),
}


def monde(n, seed, sur):
    cfg = dict(MONDE_ARMA, **sur)
    return AssaultTerrain(num_envs=n, seed=seed, device="cuda:0", max_steps=PAS,
                          A=8, D=4, R_spawn=220.0, terr_R=260.0, **cfg)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def voie_A(e, t):
    return cap(-e.apx, -e.apy)


def voie_B(e, t, n_fixe=4):
    a = cap(-e.apx, -e.apy)
    a[:, :n_fixe] = 9                       # les 4 premiers FIXENT (tirent), les 4 autres assaillent de face
    return a


def voie_C(e, t, n_fixe=4, bascule=14):     # 45 s / 3,28 s ~ 14 pas
    a = cap(-e.apx, -e.apy)
    a[:, :n_fixe] = 9
    if t < bascule:                         # les debordants vont d abord SUR LE COTE
        ang = torch.atan2(-e.apx, -e.apy) + math.pi / 2.0
        lat = (torch.round(ang / (math.pi / 4.0)).long() % 8)
        a[:, n_fixe:] = lat[:, n_fixe:]
    return a


VOIES = {"A frontal": voie_A, "B fixeurs+frontal": voie_B, "C fixeurs+flanc": voie_C}


def jouer(e, fn):
    e.reset()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(PAS):
        a = fn(e, t)
        _, _, done, info = e.step(a, auto_reset=False)
        pris |= info["took"] & ~fini
        fini |= done.bool()
        if bool(fini.all()):
            break
    return 100.0 * float(pris.float().mean())


def wil(p, n):
    z = 1.96; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


res = {}
for nomc, sur in COURBES.items():
    res[nomc] = {}
    for nomv, fn in VOIES.items():
        pr = []
        for g in GRAINES:
            e = monde(N, g, sur)
            pr.append(jouer(e, fn))
        m = sum(pr) / len(pr)
        et = (sum((x - m) ** 2 for x in pr) / max(len(pr) - 1, 1)) ** 0.5
        res[nomc][nomv] = dict(moyenne=m, demi_ic=1.96 * et / len(pr) ** 0.5, par_graine=pr)
        print("  %-26s %-19s %5.1f %%  ± %.1f" % (nomc, nomv, m, res[nomc][nomv]["demi_ic"]),
              flush=True)

print("\n  " + "=" * 78)
print("  LES SIX CHIFFRES CONTRE ARMA — dispositif EGAL (8 contre 4, 220 m, 300 s)")
print("  voie                 Arma            ancienne courbe      courbe neuve")
compat = {}
for nomv in VOIES:
    pa, lo, hi = ARMA[nomv]
    ligne = "  %-18s %.3f" % (nomv, pa)
    for nomc in COURBES:
        v = res[nomc][nomv]["moyenne"] / 100.0
        dedans = lo <= v <= hi
        compat.setdefault(nomc, []).append(dedans)
        ligne += " %.3f%s" % (v, "✔" if dedans else "✗")
    print(ligne)
print()
for nomc in COURBES:
    k = sum(compat[nomc])
    print("  %-26s : %d / 3 voies DANS l IC d Arma" % (nomc, k))
print()
print("  ⚠️ Ce test departage par le NIVEAU. Il ne dit rien du SIGNE : a n=14 la puissance")
print("     d Arma etait de 17 %, seul un effet de ~50 pts y serait visible.")
json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False)
print("  ecrit : %s" % SORTIE)
