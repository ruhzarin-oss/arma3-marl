#!/usr/bin/env python3
"""juger_a2.py — LE BANC A2 DEDIE : le controle positif peut-il enfin REFUSER ?

Criteres deposes AVANT le lancement : CRITERES_BANC_A2_DEDIE.md (commit 3689294).

  PRIMAIRE   la TENUE. Le banc PASSE si l ecart deux_axes - frontal est >= +10 points
             avec p < 0,05. En dessous, ce n est pas l agent qui est en cause : c est
             l INSTRUMENT, et les +17,3 et +15,0 deviennent illisibles sur ce banc.
  PRESENCE   >= 95 % des accrochages doivent porter un journal FIGE. Sous ce seuil on n a
             pas mesure un controle positif, on a mesure un setDir qui ne prenait pas.
  TEMOIN     la part d hommes VUS par axe (SU x POS), choisie DANS les donnees. En fige,
             l axe 1 doit etre vu MOINS que l axe 0, celui que les defenseurs fixent.

FILTRE DE SANTE, et pourquoi il existe. Le 06/08 le banc a degenere au 235e accrochage :
limite Arma de 144 groupes par camp atteinte, plus rien ne spawne, et le journal continue
d ecrire des « fin » parfaitement formees de 5 secondes. Panne SILENCIEUSE. On rejette donc
tout accrochage de moins de 30 s ou sans defenseur — et on DIT combien on a rejete.
"""
import re, sys, math
from collections import defaultdict

J = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA_a2.out'

D, F, FIGE = {}, {}, set()
AXE = {}                       # (accrochage, homme) -> axe, depuis POS
VU = defaultdict(set)          # accrochage -> hommes vus au moins une fois
for l in open(J, errors='ignore'):
    m = re.search(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|\d+\|\d+\|\d+\|(\d+)\|(\d+)', l)
    if m:
        D[int(m.group(1))] = dict(nDef=int(m.group(2)), nAtt=int(m.group(3)),
                                  axes=int(m.group(4)), fige=int(m.group(5)))
    m = re.search(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|(\d+)\|(\w+)\|(\d+)\|(\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)', l)
    if m:
        F[int(m.group(1))] = dict(duree=int(m.group(2)), cause=m.group(3),
                                  pris=int(m.group(6)), nDefRest=int(m.group(7)))
    m = re.search(r'HMT\|G\|FIGE\|(\d+)\|', l)
    if m:
        FIGE.add(int(m.group(1)))
    m = re.search(r'HMT\|G\|POS\|(\d+)\|[\d.]+\|(\d+)\|\d+\|\d+\|\d+\|(-?\d+)', l)
    if m:
        a = int(m.group(3))
        if a >= 0:
            AXE[(int(m.group(1)), int(m.group(2)))] = a
    m = re.search(r'HMT\|G\|SU\|(\d+)\|[\d.]+\|(\d+)\|(\d+)\|', l)
    if m:
        VU[int(m.group(1))].add(int(m.group(3)))

clos = sorted(set(D) & set(F))
sain = [k for k in clos if F[k]['duree'] >= 30 and D[k]['nDef'] > 0]
rejet = len(clos) - len(sain)
print(f"\n  {len(clos)} accrochages clos · {len(sain)} retenus · {rejet} REJETES (degeneres)")
if rejet:
    print(f"  ⟨le filtre de sante a mordu {rejet} fois — c est ce qu il est la pour faire⟩")
if not sain:
    sys.exit(1)


def prop(a, b):
    (pa, na), (pb, nb) = a, b
    if na == 0 or nb == 0:
        return 0.0, 1.0
    p = (pa + pb) / (na + nb)
    s = math.sqrt(p * (1 - p) * (1 / na + 1 / nb))
    if s == 0:
        return pa / na - pb / nb, 1.0
    z = (pa / na - pb / nb) / s
    return pa / na - pb / nb, math.erfc(abs(z) / math.sqrt(2))


print("\n" + "=" * 76)
print("  PRESENCE — la manipulation a-t-elle vraiment eu lieu ?")
print("  " + "-" * 74)
nf = sum(1 for k in sain if k in FIGE)
tx = nf / len(sain)
okp = tx >= 0.95
print(f"     journal FIGE present sur {nf}/{len(sain)} = {tx:.1%}  (exige >= 95 %)"
      f"   -> {'OK' if okp else 'ECHEC'}")
nfige = sum(1 for k in sain if D[k]['fige'] == 1)
print(f"     accrochages tires en mode fige : {nfige}/{len(sain)}  (le banc en veut 100 %)")

print("\n" + "=" * 76)
print("  PRIMAIRE — la TENUE, en mode FIGE")
print("  " + "-" * 74)
c = defaultdict(lambda: [0, 0])
for k in sain:
    b = 'deux_axes' if D[k]['axes'] == 2 else 'frontal'
    c[b][1] += 1
    if F[k]['cause'] == 'prise' and F[k]['pris'] == 1:
        c[b][0] += 1
for b in sorted(c):
    p, n = c[b]
    print(f"     {b:12s} tenue {p:3d}/{n:3d}   {p/max(n,1):6.1%}")
ok1 = None
if 'deux_axes' in c and 'frontal' in c:
    d, pv = prop(c['deux_axes'], c['frontal'])
    ok1 = d >= 0.10 and pv < 0.05
    print(f"     ecart {d:+.1%} (exige >= +10 pts) · p = {pv:.4f} (exige < 0,05)"
          f"   -> {'OK' if ok1 else 'ECHEC'}")

print("\n" + "=" * 76)
print("  TEMOIN DE MECANISME — la part d hommes VUS, par axe")
print("  " + "-" * 74)
tot = defaultdict(lambda: [0, 0])
hommes_par_acc = defaultdict(lambda: defaultdict(set))
for (kk, h), a in AXE.items():
    hommes_par_acc[kk][a].add(h)
for k in sain:
    if D[k]['axes'] != 2:
        continue
    for a in (0, 1):
        hs = hommes_par_acc[k][a]
        if hs:
            tot[a][0] += len(hs & VU[k])
            tot[a][1] += len(hs)
for a in (0, 1):
    v, n = tot[a]
    nom = "axe 0 (celui que les defenseurs FIXENT)" if a == 0 else "axe 1 (hors du cone tenu)"
    print(f"     {nom:42s} {v:4d}/{n:4d} vus = {v/max(n,1):6.1%}")
ok3 = False
if tot[0][1] and tot[1][1]:
    ok3 = (tot[1][0] / tot[1][1]) < (tot[0][0] / tot[0][1])
    d3, p3 = prop((tot[1][0], tot[1][1]), (tot[0][0], tot[0][1]))
    print(f"     ecart {d3:+.1%} · p = {p3:.4f}   -> "
          f"{'le flanc est MOINS vu' if ok3 else 'PAS DANS LE SENS ATTENDU'}")

print("\n" + "=" * 76)
if not okp:
    print("  LA PRESENCE A CEDE. On n a pas mesure un controle positif : on a mesure un setDir")
    print("  qui ne prenait pas. Rien n est conclu, ni dans un sens ni dans l autre.")
elif ok1:
    print("  LA PORTE TIENT. Quand les defenseurs sont aveugles sur un flanc, le deux-axes")
    print("  ECRASE le frontal. L instrument discrimine — donc il pouvait juger l A/B, et les")
    print("  +17,3 et +15,0 se lisent.")
    if not ok3:
        print("  ⟨mais le temoin ne suit pas : on garde le chiffre, on n ecrit pas d histoire.⟩")
else:
    print("  LA PORTE CEDE. Le banc ne separe pas deux axes d un seul MEME quand les defenseurs")
    print("  sont structurellement aveugles. Ce n est pas l agent qui est en cause : c est")
    print("  L INSTRUMENT. Les +17,3 et +15,0 deviennent des observations d un dispositif qui")
    print("  ne discrimine pas — pas des verdicts.")
print("  " + "=" * 74)
