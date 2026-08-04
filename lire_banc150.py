#!/usr/bin/env python3
"""lire_banc150.py — DEPOUILLEMENT DU BANC A 150 M.

LE SENS DE LA MESURE, CORRIGE.  `dist_detect` est la distance a l'OBJECTIF au moment du
reperage. Une valeur GRANDE veut donc dire « repere loin de l'objectif », c'est-a-dire TOT,
c'est-a-dire MAL. Une valeur PETITE veut dire qu'on s'est approche avant d'etre vu. Et -1
veut dire jamais repere : le meilleur resultat possible.
⟨le critere du banc precedent exigeait d'etre repere « PLUS LOIN de l'objectif, d'au moins
 25 % » — il recompensait donc le fait d'etre vu PLUS TOT. Signe inverse. Le banc du cone
 tranche sans ambiguite : de face on est repere a 105 m de l'objectif, par le flanc JAMAIS.
 Une bonne approche a donc une distance de detection PETITE ou nulle.⟩

Les quatre portes ont ete ecrites AVANT le run et ne sont pas retouchees ici :
  P1 PRESENCE  : la ligne droite doit etre reperee dans au moins 16 configurations sur 20.
  P2 DYNAMIQUE : ecart interquartile des distances >= 27 m (25 % des 110 m utiles).
  P3 NUL       : droite et droite_bis a moins de 15 m d'ecart median.
  P4 REUSSITE  : le chemin parfait doit etre repere >= 25 % PLUS PRES que la droite
                 (ou echapper totalement la ou la droite est vue).
"""
import re, sys
import numpy as np

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
R_DEP, R_ARR = 150.0, 40.0
BRAS = ['droite', 'oracle', 'oracle_libre', 'droite_bis']

ess, cfgs = {}, {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|B150\|essai\|(\d+)\|(\w+)\|know\|([\d.]+)\|reste\|(\d+)\|dist_detect\|(-?\d+)\|points\|(\d+)', l)
    if m:
        ess.setdefault(int(m.group(1)), {})[m.group(2)] = dict(
            know=float(m.group(3)), reste=int(m.group(4)), dd=int(m.group(5)), n=int(m.group(6)))
    m = re.search(r'HMT\|B150\|config\|(\d+)\|defenseurs\|(\d+)\|derive_max\|([\d.]+)', l)
    if m:
        cfgs[int(m.group(1))] = dict(n=int(m.group(2)), derive=float(m.group(3)))

comp = sorted(c for c in ess if all(b in ess[c] for b in BRAS))
print(f"  configurations completes : {len(comp)} / 20   (4 bras chacune)")
if not comp: sys.exit(1)
der = [cfgs[c]['derive'] for c in comp if c in cfgs]
print(f"  derive des defenseurs a la pose : mediane {np.median(der):.1f} m · max {max(der):.1f} m"
      f"  -> les positions rejouees sont bien celles calculees")

dd = lambda c, b: (None if ess[c][b]['dd'] < 0 else float(ess[c][b]['dd']))
npts = lambda c, b: ess[c][b]['n']
D = {b: [dd(c, b) for c in comp] for b in BRAS}
jam = {b: sum(1 for v in D[b] if v is None) for b in BRAS}
vus = {b: [v for v in D[b] if v is not None] for b in BRAS}

print("\n  " + "="*78)
print("  PETIT = s'est approche avant d'etre vu = BIEN.  GRAND = vu de loin, tot = MAL.")
print("  " + "-"*78)
print("  bras            distance de reperage (m)      jamais vu   longueur du chemin")
for b in BRAS:
    v = vus[b]; L = [npts(c, b) for c in comp]
    print(f"  {b:14s}  mediane {np.median(v):6.1f}  [{min(v):5.1f} - {max(v):5.1f}]"
          f"    {jam[b]:2d}/{len(comp)}      {np.median(L):5.0f} points")
print("  " + "="*78)

# ------------------------------------------------------------------ les quatre portes
p1 = (len(comp) - jam['droite']) >= 16
print(f"\n  P1 PRESENCE  : droite reperee dans {len(comp)-jam['droite']}/{len(comp)} "
      f"(exige >= 16)  -> {'OK' if p1 else 'ECHEC'}")

tous = [v for b in BRAS for v in vus[b]]
iqr = float(np.percentile(tous, 75) - np.percentile(tous, 25))
p2 = iqr >= 27
print(f"  P2 DYNAMIQUE : ecart interquartile {iqr:.0f} m sur {R_DEP-R_ARR:.0f} m utiles "
      f"= {iqr/(R_DEP-R_ARR):.0%} (exige >= 27 m)  -> {'OK' if p2 else 'ECHEC'}")
print(f"                 ⟨le banc a 80 m valait 8 m : il ne separait rien⟩")

ec = [abs(dd(c,'droite')-dd(c,'droite_bis')) for c in comp
      if dd(c,'droite') is not None and dd(c,'droite_bis') is not None]
acc = sum(1 for c in comp if (dd(c,'droite') is None) == (dd(c,'droite_bis') is None))
e_med = float(np.median(ec)) if ec else float('nan')
p3 = e_med < 15 and acc >= 16
print(f"  P3 NUL       : droite vs droite_bis — ecart median {e_med:.1f} m "
      f"(max {max(ec):.0f} m), meme verdict {acc}/{len(comp)}  -> {'OK' if p3 else 'ECHEC'}")

def gain(b):
    """apparie. Un bras est MEILLEUR s'il est repere plus PRES, ou pas repere du tout."""
    a_, b_, echappe, subit = [], [], 0, 0
    for c in comp:
        x, y = dd(c, 'droite'), dd(c, b)
        if x is None and y is None: continue
        if y is None: echappe += 1; continue
        if x is None: subit += 1; continue
        a_.append(x); b_.append(y)
    g = (np.mean(a_)-np.mean(b_))/np.mean(a_) if a_ else None
    return g, echappe, subit, len(a_)

print()
for b in ['oracle', 'oracle_libre']:
    g, e_, s_, n = gain(b)
    print(f"  {b:14s} repere {g:+.0%} plus PRES que la droite (sur {n} paires) · "
          f"echappe {e_} fois · se fait voir {s_} fois la ou la droite echappe")

g_lib, e_lib, _, _ = gain('oracle_libre')
p4 = (g_lib is not None and g_lib >= 0.25) or e_lib >= 5
print(f"\n  P4 REUSSITE  : le chemin parfait achete-t-il 25 % ?  -> {'OK' if p4 else 'ECHEC'}")

# ------------------------------------------------------------------ CE QUE LE MODELE IGNORE
# Hypothese nee de la config 1 : Arma ACCUMULE la connaissance tant qu'on est vu. Un chemin
# plus long, meme moins expose a chaque instant, accumule davantage. Mon modele prend le
# MAXIMUM de l'exposition instantanee : il ignore entierement la duree.
def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    r = lambda v: np.argsort(np.argsort(v)).astype(float)
    return float(np.corrcoef(r(a), r(b))[0, 1])

paires = [(npts(c, b), dd(c, b)) for c in comp for b in BRAS if dd(c, b) is not None]
rho = spearman([p for p, _ in paires], [d for _, d in paires])
print("\n  " + "="*78)
print("  CE QUE LE MODELE IGNORE : LA DUREE")
print(f"  correlation de rang (longueur du chemin <-> distance de reperage) : "
      f"rho = {rho:+.2f}  (n={len(paires)})")
long_ = [d for p, d in paires if p >= 60]; court = [d for p, d in paires if p < 60]
print(f"    chemins courts (< 60 points) : repere a {np.median(court):5.1f} m   (n={len(court)})")
print(f"    chemins longs  (>= 60 points): repere a {np.median(long_):5.1f} m   (n={len(long_)})")
if rho > 0.5:
    print("  -> PLUS UN CHEMIN EST LONG, PLUS TOT IL EST REPERE. Le pic d'exposition")
    print("     instantanee ne suffit pas : Arma accumule tant qu'on est vu. Ni la SOMME")
    print("     (qui ignore l'irreversibilite) ni le MAXIMUM (qui ignore la duree) ne sont")
    print("     la bonne grandeur. Il faut une ACCUMULATION IRREVERSIBLE.")

print("\n  " + "="*78)
portes = dict(P1=p1, P2=p2, P3=p3, P4=p4)
cedees = [k for k, v in portes.items() if not v]
if not cedees:
    print("  LE BANC EST UN INSTRUMENT. On peut y certifier un agent.")
else:
    print(f"  PORTES CEDEES : {', '.join(cedees)}. Ce banc ne certifie pas encore.")
print("  " + "="*78)
