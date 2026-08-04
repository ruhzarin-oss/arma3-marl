#!/usr/bin/env python3
"""signature_detour.py — A QUELLE DISTANCE l'agent achete-t-il son ecart ?

C'est le critere C2 du champ de risque, depose dans CRITERES_CHAMP_RISQUE.md avant le run.

LE DIAGNOSTIC QU'IL TESTE  ⟨mesure le 27/07, jamais invalide⟩
  crochet scripte  184 m       appris voyant  132 m
  appris aveugle   123 m       assaut frontal 118 m
  L'exposition n'a pas le meme prix partout : 0,07 par pas a 200 m, 0,20 a 25 m.
  Le crochet achete tout son ecart AU TARIF DU LONG puis rentre en ligne droite ;
  l'appris achete le meme ecart au milieu du terrain, AU TARIF FORT.

LA MESURE. Pour chaque pas : la composante du deplacement PERPENDICULAIRE a la direction
de l'objectif, ponderee par la distance a l'objectif a cet instant. La moyenne ponderee
donne la distance a laquelle le detour a reellement ete achete.

LE SEUIL, traduit AVANT toute donnee : 155 m sur un depart de 250 m = 62 % du rayon.
Sur un banc a 150 m, cela fait 93 m. C'est une traduction d'echelle, pas un assouplissement
— la fraction est identique. ⟨appris voyant : 53 % · crochet : 74 %⟩
"""
import json, sys
import numpy as np

SEUIL_FRACTION = 0.62

def signature(traj):
    """distance moyenne a laquelle le mouvement lateral est produit."""
    p = np.asarray(traj, float)
    if len(p) < 3: return None, None
    dp = np.diff(p, axis=0)
    pos = p[:-1]
    d = np.linalg.norm(pos, axis=1)
    ok = d > 1e-6
    if ok.sum() < 2: return None, None
    u = np.zeros_like(pos)
    u[ok] = -pos[ok] / d[ok, None]                 # direction vers l'objectif (a l'origine)
    radial = (dp * u).sum(axis=1)
    lateral = np.linalg.norm(dp - radial[:, None]*u, axis=1)
    if lateral.sum() < 1e-9: return 0.0, 0.0
    return float((lateral * d).sum() / lateral.sum()), float(lateral.sum())

def juger(fichier, nom):
    src = json.load(open(fichier))[:20]
    S, L, R = [], [], []
    for c in src:
        t = np.array(c['agent'], float)
        s, l = signature(t)
        if s is None: continue
        r = float(np.linalg.norm(t[0]))
        S.append(s); L.append(l); R.append(r)
    if not S: return None
    med = float(np.median(S)); ray = float(np.median(R))
    return dict(nom=nom, n=len(S), sig=med, rayon=ray, frac=med/ray,
                lat=float(np.median(L)))

FICHIERS = [('/mnt/data/corpus/trajectoires_agent150_sanschamp.json', 'SANS champ de risque'),
            ('/mnt/data/corpus/trajectoires_agent150.json',           'AVEC champ de risque')]

print("\n" + "="*76)
print("  C2 — LA SIGNATURE : a quelle distance le detour est-il achete ?")
print("  " + "-"*74)
print(f"  {'agent':24s} {'n':>3s} {'rayon':>8s} {'detour':>9s} {'fraction':>10s}  verdict")
res = []
for f, nom in FICHIERS:
    try:
        r = juger(f, nom)
    except FileNotFoundError:
        print(f"  {nom:24s}   fichier absent"); continue
    if r is None: continue
    res.append(r)
    ok = r['frac'] >= SEUIL_FRACTION
    print(f"  {r['nom']:24s} {r['n']:3d} {r['rayon']:7.0f}m {r['sig']:8.0f}m "
          f"{r['frac']:9.0%}   {'PASSE' if ok else 'ECHOUE'}")
print("  " + "-"*74)
print(f"  seuil : {SEUIL_FRACTION:.0%} du rayon de depart "
      f"(155 m sur 250 m, depose le 27/07 et traduit avant ce run)")
print(f"  reperes du 27/07 : appris voyant 53 % · crochet scripte 74 %")
print("="*76)

if len(res) == 2:
    a, b = res
    print(f"\n  DEPLACEMENT DU DETOUR : {a['sig']:.0f} m -> {b['sig']:.0f} m "
          f"({a['frac']:.0%} -> {b['frac']:.0%} du rayon)")
    if b['frac'] >= SEUIL_FRACTION:
        print("  -> LA SIGNATURE EST LA. Le champ de risque a repousse l'achat de l'ecart")
        print("     vers le tarif du long, ce qui est exactement ce que le diagnostic demandait.")
    elif b['sig'] > a['sig'] + 5:
        print("  -> le detour se deplace dans le BON SENS mais n'atteint pas le seuil.")
        print("     Un gain sans la signature : le canal perception est clos.")
    else:
        print("  -> AUCUN DEPLACEMENT. Le champ ne change pas OU l'agent achete son ecart.")
        print("     Le canal perception est clos, et le suspect devient l'ETAPE 5 :")
        print("     apprendre dans le rejeu au lieu d'apprendre en mourant.")
