#!/usr/bin/env python3
"""admission.py — QUELS TERRAINS ONT LE DROIT DE JUGER ?

Un terrain n est admis que si SA LIGNE DE BASE EST REPRODUCTIBLE — deux mesures du temoin,
dans DEUX SESSIONS SEPAREES, qui s accordent a la tolerance deposee EN AVEUGLE avant d avoir
vu le moindre candidat. ⟨PROTOCOLE_ETAGE1_APPUI.md, 09/08⟩

  TOLERANCE DEPOSEE : +/- 35 % de la moyenne des deux mesures.

⟨Fable⟩ « L ennemi de ce banc est de session. Deux runs adosses peuvent s accorder et mentir
ensemble. » D ou deux serveurs distincts, lances a une heure d intervalle.

ON N ELARGIT JAMAIS LA TOLERANCE APRES COUP. Si trop de terrains tombent, on crible plus de
candidats — et si plus de 3 sur 9 tombent, ce ne sont plus les terrains qu on accuse, c est le
geometre qui les qualifie de « plats et degages ».
"""
import re, sys, statistics

TOL = 0.35
def lire(f, phase):
    """rend {terrain: (delivre, delivre2)} pour les essais de ligne de base"""
    out = {}
    pat = re.compile(r'HMT\|AP\|essai\|0\|1\|terrain\|(\d+)\|delivre\|(\d+)\|delivre2\|(\d+)')
    for L in open(f, encoding='utf-8', errors='ignore'):
        m = pat.search(L)
        if m:
            out[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
    return out

A = lire('/mnt/data/harmattan-sandbox/logs/phase1_bases.out', 1)
B = lire('/mnt/data/harmattan-sandbox/logs/serverAP.out', 2)
print(f"\n  phase 1 : {len(A)} terrains · phase 2 : {len(B)} terrains")
if not A or not B:
    print("  une des deux phases manque — pas d admission"); sys.exit(0)

print(f"\n  {'terrain':<9}{'base 1':>9}{'base 2':>9}{'moyenne':>10}{'ecart':>9}{'':>4}{'verdict'}")
print("  " + "-" * 62)
admis, recales = [], []
rapports = []
for t in sorted(set(A) & set(B)):
    a, b = A[t][0], B[t][0]
    m = (a + b) / 2
    if m == 0:
        print(f"  {t:<9}{a:>9}{b:>9}{m:>10.0f}{'—':>9}    RECALE — ne delivre rien")
        recales.append(t); continue
    e = abs(a - b) / m
    ok = e <= TOL
    print(f"  {t:<9}{a:>9}{b:>9}{m:>10.0f}{100*e:>8.0f}%    {'admis' if ok else 'RECALE'}")
    (admis if ok else recales).append(t)
    for v in (A[t], B[t]):
        if v[0] > 0: rapports.append(v[1] / v[0])

print("  " + "-" * 62)
print(f"  {len(admis)} admis · {len(recales)} recales  sur {len(set(A) & set(B))} candidats")

# ── LE DOUBLE CHEMIN ⟨regle 11⟩ : le RAPPORT doit etre stable a +/- 20 % de sa mediane
if rapports:
    med = statistics.median(rapports)
    pire = max(abs(r - med) / med for r in rapports)
    print(f"\n  DOUBLE CHEMIN — rapport HandleDamage / HitPart")
    print(f"    mediane {med:.2f} · ecart maximal {100*pire:.1f} %  (tolerance deposee : 20 %)")
    print(f"    -> {'les deux chemins voient les memes evenements' if pire <= 0.20 else 'INSTRUMENT EN PANNE : on cherche la cause, on ne reconcilie pas'}")

print(f"\n  CE QUI SUIT, selon le protocole depose :")
if len(admis) >= 5:
    print(f"    la campagne tourne sur les {len(admis)} terrains admis — moins que les 8 voulus,")
    print(f"    et on le DIT plutot que de compenser.")
    print(f"    terrains : {admis}")
elif len(recales) > 3:
    print(f"    {len(recales)} recales : ce ne sont plus les terrains qu on accuse, c est le")
    print(f"    GEOMETRE qui les qualifie de « plats et degages ». On retourne le voir AVANT")
    print(f"    de bruler des nuits. ⟨clause de Fable, deposee avant⟩")
else:
    print(f"    trop peu de terrains admis pour une campagne appariee. On crible plus de")
    print(f"    candidats — on n elargit JAMAIS la tolerance apres coup.")
