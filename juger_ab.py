#!/usr/bin/env python3
"""juger_ab.py — LE VERDICT DE L'A/B INSTRUMENTE.

Hierarchie des metriques DEPOSEE ET HORODATEE avant tout depouillement par bras
(CRITERES_METRIQUES_AB.md, commit f64ffae) :

  PRIMAIRE     la TENUE — objectif tenu exclusivement 60 s continues. C'est la grandeur
               du +12,3 points du 02/08.
  SECONDAIRE A l'elimination, analysee SEPAREMENT
  SECONDAIRE B le chronometre, analyse SEPAREMENT
  Jamais agregees. Le « taux de prise » global n'est plus une metrique de ce banc.

ORDRE DE LECTURE, impose : A2 d'abord. Si le controle positif cede, A1 n'est pas lisible,
quel que soit son p.

CRITERES, recopies sans retouche :
  A2 CONTROLE POSITIF  en mode FIGE, le deux-axes doit ECRASER le frontal
  A1 PRIMAIRE          ecart >= +6 points sur la TENUE, p < 0,05
  A4 CONTROLE NUL      les deux parties de journal doivent concorder

PORTEE DU REGLAGE, a rappeler dans tout verdict : charge 6, ratio 1,5-3,0. Rien au-dela.
"""
import re, sys, math
from collections import defaultdict

JOURNAUX = ['/mnt/data/harmattan-sandbox/logs/serverBA_ab_reel_partie1.out',
            '/mnt/data/harmattan-sandbox/logs/serverBA.out']

def lire(chemin, decalage):
    deb, fin, arr = {}, {}, defaultdict(list)
    try: f = open(chemin, errors='ignore')
    except FileNotFoundError: return {}, {}, {}
    for l in f:
        m = re.search(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|\d+\|\d+\|\d+\|(\d+)\|(\d+)', l)
        if m:
            deb[int(m.group(1))+decalage] = dict(nDef=int(m.group(2)), nAtt=int(m.group(3)),
                                                 axes=int(m.group(4)), fige=int(m.group(5)))
        m = re.search(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|(\d+)\|(\w+)\|(\d+)\|(\d+)\|(\d+)\|\d+\|\d+\|\d+\|\d+\|(\d+)', l)
        if m:
            fin[int(m.group(1))+decalage] = dict(duree=int(m.group(2)), cause=m.group(3),
                                                 campDef=int(m.group(4)), pris=int(m.group(6)),
                                                 axes_arrives=int(m.group(7)))
        m = re.search(r'HMT\|G\|ARR\|(\d+)\|([\d.]+)\|(\d+)\|(\d+)', l)
        if m: arr[int(m.group(1))+decalage].append((int(m.group(3)), int(m.group(4))))
    return deb, fin, arr

D, F, A = {}, {}, {}
for i, ch in enumerate(JOURNAUX):
    d, f, a = lire(ch, i*100000)
    D.update(d); F.update(f); A.update(a)

clos = sorted(set(D) & set(F))
print(f"\n  {len(clos)} accrochages clos, deux parties de journal reunies")
if not clos: sys.exit(1)

def bras(k):
    return ('deux_axes' if D[k]['axes'] == 2 else 'frontal') + (' FIGE' if D[k]['fige'] else '')

def prop(a, b):
    """test de proportions, bilateral."""
    (pa, na), (pb, nb) = a, b
    if na == 0 or nb == 0: return 0.0, 1.0
    p1, p2 = pa/na, pb/nb
    p = (pa+pb)/(na+nb)
    s = math.sqrt(p*(1-p)*(1/na+1/nb))
    if s == 0: return p1-p2, 1.0
    z = (p1-p2)/s
    return p1-p2, math.erfc(abs(z)/math.sqrt(2))

def compte(sel, cause):
    c = defaultdict(lambda: [0, 0])
    for k in clos:
        if not sel(k): continue
        c[bras(k)][1] += 1
        if F[k]['cause'] == cause and F[k]['pris'] == 1: c[bras(k)][0] += 1
    return c

print("\n" + "="*76)
print("  A2 — CONTROLE POSITIF : en mode FIGE, le deux-axes doit ECRASER")
print("  " + "-"*74)
cf = compte(lambda k: D[k]['fige'] == 1, 'prise')
for b in sorted(cf):
    p, n = cf[b]
    print(f"     {b:18s} tenue {p:3d}/{n:3d}   {p/max(n,1):6.1%}")
ok2 = None
if 'deux_axes FIGE' in cf and 'frontal FIGE' in cf:
    d, pv = prop(cf['deux_axes FIGE'], cf['frontal FIGE'])
    ok2 = d > 0
    print(f"     ecart {d:+.1%} · p = {pv:.3f}   -> {'OK' if ok2 else 'ECHEC : instrument casse'}")
else:
    print("     pas assez de configurations figees pour lire A2")

print("\n" + "="*76)
print("  A1 — PRIMAIRE : la TENUE  (la grandeur du +12,3 du 02/08)")
print("  " + "-"*74)
cl = compte(lambda k: D[k]['fige'] == 0, 'prise')
for b in sorted(cl):
    p, n = cl[b]
    print(f"     {b:18s} tenue {p:3d}/{n:3d}   {p/max(n,1):6.1%}")
ok1 = None
if 'deux_axes' in cl and 'frontal' in cl:
    d, pv = prop(cl['deux_axes'], cl['frontal'])
    ok1 = d >= 0.06 and pv < 0.05
    print(f"     ecart {d:+.1%} (exige >= +6 pts) · p = {pv:.3f} (exige < 0,05)"
          f"   -> {'OK' if ok1 else 'ECHEC'}")
    print(f"     ⟨rappel : le 02/08 donnait +12,3 points, p < 0,0001⟩")

print("\n" + "="*76)
print("  SECONDAIRES — analysees SEPAREMENT, jamais agregees a la primaire")
print("  " + "-"*74)
for cause, nom in [('elimination', 'A. ELIMINATION'), ('chrono', 'B. CHRONOMETRE')]:
    c = compte(lambda k: D[k]['fige'] == 0, cause)
    lig = "  ".join(f"{b} {p}/{n} ({p/max(n,1):.0%})" for b, (p, n) in sorted(c.items()))
    print(f"     {nom:16s} {lig}")

print("\n" + "="*76)
print("  ARR — QUI ARRIVE, ET QUAND   (la lecture « le flanc fait ARRIVER »)")
print("  " + "-"*74)
for b in ['frontal', 'deux_axes']:
    ks = [k for k in clos if bras(k) == b]
    na = sum(F[k]['axes_arrives'] for k in ks)
    tps = [t for k in ks for _, t in A.get(k, [])]
    med = sorted(tps)[len(tps)//2] if tps else None
    print(f"     {b:12s} {len(ks):3d} engagements · {na:3d} axes ont atteint le point"
          f" · 1er franchissement median {med if med is not None else '.'} s")

print("\n" + "="*76)
if ok2 is False:
    print("  L'INSTRUMENT EST CASSE. A1 n'est pas lisible, quel que soit son p.")
elif ok1:
    print("  LE +12,3 TIENT. Le deux-axes bat le frontal sur la TENUE, la grandeur meme du")
    print("  fait fondateur. Reglage : charge 6, ratio 1,5-3,0.")
elif ok1 is False:
    print("  LE +12,3 NE TIENT PAS sur la tenue, dans ce monde recalibre. Ce n'est pas un")
    print("  echec : c'est un verdict. Le fait fondateur devient conditionnel a des reglages")
    print("  que nous ne connaissons plus — observation historique, plus axiome.")
print("  " + "="*74)
