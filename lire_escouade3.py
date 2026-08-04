#!/usr/bin/env python3
"""lire_escouade3.py — LE TEST « NOMBRE D'HOMMES VUS », sur donnees neuves.

Les criteres ont ete deposes dans CRITERES_HOMMES_VUS.md AVANT ce run, alors qu'aucune
de ses donnees n'existait. Ils sont recopies ici sans retouche :

  C0 VALIDITE  le bruit est mesure par DEUX paires de rejeux identiques (deux_axes/bis et
               flanc_seul/bis). L'effet doit depasser le DOUBLE du plus grand des deux.
  C1 PRINCIPAL deux_axes a une part reperee strictement inferieure a flanc_seul dans au
               moins 14 configurations sur 20, test des signes p < 0,05, et ecart median
               superieur au bruit.
  C2 NEGATIF   l'effet ne doit PAS apparaitre entre flanc_seul et flanc_seul_bis — deux
               bras identiques, tous deux sans base de feu.
  C3 DOSE      l'effet doit etre PLUS MARQUE pres de l'objectif qu'a 120 m, ou la base de
               feu n'a pas encore engage. Un effet identique partout serait suspect.
  C4 TIR       deux_axes doit avoir tire, flanc_seul non.
"""
import re, sys
from math import comb
import numpy as np

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
BRAS = ['solo', 'bloc_1axe', 'deux_axes', 'deux_axes_bis', 'flanc_seul', 'flanc_seul_bis']
JALONS = [120, 90, 60, 40]

ess = {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|ESC3\|essai\|(\d+)\|(\w+)\|man\|([\d.]+)\|fix\|([\d.]+)\|jalons\|\[([-\d,]+)\]\|vus\|(\d+)\|sur\|(\d+)\|pas\|(\d+)\|tirs\|(\d+)\|arme_vers_man\|(-?\d+)\|regard_vers_man\|(-?\d+)\|vus_jalons\|\[([-\d,]+)\]', l)
    if m:
        ess.setdefault(int(m.group(1)), {})[m.group(2)] = dict(
            jal=[int(v) for v in m.group(5).split(',')],
            vus=int(m.group(6)), sur=int(m.group(7)), tirs=int(m.group(9)),
            arme=int(m.group(10)), vusjal=[int(v) for v in m.group(12).split(',')])

comp = sorted(c for c in ess if all(b in ess[c] for b in BRAS))
print(f"  configurations completes : {len(comp)} / 20   ({len(BRAS)} bras)")
if not comp:
    print(f"  ({sum(len(v) for v in ess.values())} essais — le run n'est pas fini)"); sys.exit(1)

# LA MESURE : part d'hommes du groupe manoeuvrant reperes, a l'arrivee
part = lambda c, b: ess[c][b]['vus'] / max(ess[c][b]['sur'], 1)

print("\n  " + "="*78)
print("  PART DES HOMMES DU GROUPE MANOEUVRANT REPERES")
print("  " + "-"*78)
print("  bras              effectif   hommes vus     part    tirs   score jalons")
for b in BRAS:
    vus = sum(ess[c][b]['vus'] for c in comp); sur = sum(ess[c][b]['sur'] for c in comp)
    eff = int(np.median([ess[c][b]['sur'] for c in comp]))
    t = int(np.median([ess[c][b]['tirs'] for c in comp]))
    s = np.median([sum(1 for v in ess[c][b]['jal'] if v == 1) for c in comp])
    print(f"  {b:16s}   {eff:2d}      {vus:3d} / {sur:3d}     {vus/sur:5.0%}   {t:4d}      {s:4.1f}")
print("  " + "="*78)

def signes(a, b):
    """test des signes bilateral, egalites exclues. a MEILLEUR = part plus FAIBLE."""
    g = sum(1 for c in comp if part(c, a) < part(c, b))
    p = sum(1 for c in comp if part(c, a) > part(c, b))
    n = g + p
    if n == 0: return g, p, 1.0
    k = min(g, p)
    return g, p, min(2*sum(comb(n, i) for i in range(k+1))/(2**n), 1.0)

# ---------------------------------------------------------------- C0 VALIDITE
b1 = float(np.mean([abs(part(c,'deux_axes') - part(c,'deux_axes_bis')) for c in comp]))
b2 = float(np.mean([abs(part(c,'flanc_seul') - part(c,'flanc_seul_bis')) for c in comp]))
bruit = max(b1, b2)
effet = float(np.mean([abs(part(c,'deux_axes') - part(c,'flanc_seul')) for c in comp]))
print(f"\n  C0 VALIDITE")
print(f"     bruit deux_axes / bis      : {b1:.3f}")
print(f"     bruit flanc_seul / bis     : {b2:.3f}")
print(f"     effet deux_axes / flanc_seul : {effet:.3f}   (exige > {2*bruit:.3f})")
c0 = effet > 2*bruit
print(f"     -> {'OK' if c0 else 'BANC NUL : le bruit mange l effet, rien n est conclu'}")

# ---------------------------------------------------------------- C1 PRINCIPAL
g, p, pv = signes('deux_axes', 'flanc_seul')
med = float(np.median([part(c,'flanc_seul') - part(c,'deux_axes') for c in comp]))
c1 = g >= 14 and pv < 0.05 and med > bruit
print(f"\n  C1 PRINCIPAL — deux_axes a-t-il MOINS d hommes vus que flanc_seul ?")
print(f"     moins vu dans {g}/{len(comp)} (exige >= 14) · plus vu dans {p} · "
      f"egalite {len(comp)-g-p}")
print(f"     p = {pv:.4f} (exige < 0,05) · reduction mediane {med:+.3f} (exige > {bruit:.3f})")
print(f"     -> {'OK' if c1 else 'ECHEC'}")

# ---------------------------------------------------------------- C2 NEGATIF
g2, p2, pv2 = signes('flanc_seul', 'flanc_seul_bis')
c2 = pv2 >= 0.05
print(f"\n  C2 CONTROLE NEGATIF — deux bras IDENTIQUES, tous deux sans base de feu")
print(f"     ecart dans {g2}+{p2} configurations · p = {pv2:.4f}")
print(f"     -> {'OK, aucun effet entre bras identiques' if c2 else 'ECHEC : l ecart apparait AUSSI entre bras identiques -> artefact d ordre'}")

# ---------------------------------------------------------------- C3 DOSE
print(f"\n  C3 DOSE — l effet grandit-il en approchant de l objectif ?")
dose = []
for i, j in enumerate(JALONS):
    a = [ess[c]['deux_axes']['vusjal'][i] for c in comp if ess[c]['deux_axes']['vusjal'][i] >= 0]
    b = [ess[c]['flanc_seul']['vusjal'][i] for c in comp if ess[c]['flanc_seul']['vusjal'][i] >= 0]
    if a and b:
        d = float(np.mean(b) - np.mean(a))
        dose.append(d)
        print(f"     jalon {j:3d} m : deux_axes {np.mean(a):.2f} hommes vus · "
              f"flanc_seul {np.mean(b):.2f} · ecart {d:+.2f}")
c3 = len(dose) >= 2 and dose[-1] > dose[0]
print(f"     -> {'OK, l effet grandit en approchant' if c3 else 'ECHEC : l effet ne suit pas l engagement'}")

# ---------------------------------------------------------------- C4 TIR
t1 = int(np.median([ess[c]['deux_axes']['tirs'] for c in comp]))
t2 = int(np.median([ess[c]['flanc_seul']['tirs'] for c in comp]))
c4 = t1 > 0 and t2 == 0
print(f"\n  C4 TIR — deux_axes {t1} coups · flanc_seul {t2}  -> {'OK' if c4 else 'ECHEC'}")

print("\n  " + "="*78)
if not c0:
    print("  BANC NUL. Le dispositif ne separe pas, aucune conclusion tactique.")
elif not c2:
    print("  ARTEFACT D ORDRE. L ecart apparait entre deux bras identiques : ce n est pas")
    print("  la base de feu qui agit. C1 ne vaut rien, quel que soit son p.")
elif c1 and c3:
    print("  L EFFET EXISTE, ET IL SUIT L ENGAGEMENT.")
    print("  Une base de feu reduit le NOMBRE d hommes reperes dans le groupe qui manoeuvre,")
    print("  et l effet grandit a mesure qu on approche. La these collective tient sur cette")
    print("  grandeur — alors qu elle echouait sur la survie du groupe pris comme un tout.")
    print("  Reste a trouver le MECANISME : les armes ne sont pas detournees (+8°, 9/20).")
elif c1 and not c3:
    print("  EFFET SANS DOSE. La reduction existe mais ne suit pas l engagement : elle est")
    print("  la des 120 m, avant que la base de feu ait pu agir. Suspect — chercher un")
    print("  confondu avant de conclure quoi que ce soit.")
else:
    print("  PAS D EFFET. Sur donnees neuves et critere ecrit avant, une base de feu ne")
    print("  reduit pas le nombre d hommes reperes. L ecart 31/60 contre 51/60 du run")
    print("  precedent NE SE REPLIQUE PAS : c etait du bruit trouve apres coup.")
print("  " + "="*78)
