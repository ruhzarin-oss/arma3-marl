#!/usr/bin/env python3
"""lire_escouade.py — LE PILOTE D'ESCOUADE.

⟨RETROGRADE PAR ECRIT AVANT DEPOUILLEMENT, sur avis de Fable, 04/08 :
 ce run NE PEUT PAS CONCLURE sur la fixation. Trois raisons :
   · les caps sont LIBRES : les tetes partent de ~170° avant meme qu'un approchant soit
     pose. L'orientation, qui est LA variable, est du bruit non controle.
   · le chemin de flanc a ete optimise pour des caps qui n'existent plus : un echec ne
     distingue pas « la fixation n'explique rien » de « le chemin est faux pour ce monde ».
   · l'ORDRE DES BRAS est fixe et les defenseurs ne sont pas respawnes entre bras. Or la
     memoire du camp NE DECROIT JAMAIS (certifie). `flanc_seul` est le 4e bras : il affronte
     des hommes deja alertes par les trois precedents. L'appariement n'annule pas ce
     confondu-la. C'est le defaut que je n'avais pas vu.
 Ce qui reste lisible : le bruit de rejeu, la derive spontanee, et un signe a confirmer.⟩

Criteres de Fable, ecrits AVANT les resultats :
  1. VALIDITE : |deux_axes - bis| par config donne le bruit s. Si les ecarts inter-bras
     sont <= s, banc NUL — verdict sur le dispositif, aucune conclusion tactique permise.
  2. PRIMAIRE : deux_axes > flanc_seul, test des signes sur les paires DISCRIMINANTES
     (egalites exclues, fixe avant), et gain median > s.
  3. MECANISME : sur les configs gagnees, le regard doit etre davantage hors axe pendant
     deux_axes que pendant flanc_seul. Un effet sans mecanisme n'est pas certifiable.
  4. SECONDAIRE : deux_axes >= bloc_1axe, sinon scinder coute plus que ca ne rapporte.
"""
import re, sys
from math import comb
import numpy as np

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA_escouade_pilote.out'
BRAS = ['solo', 'bloc_1axe', 'deux_axes', 'flanc_seul', 'deux_axes_bis']

ess = {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|ESC\|essai\|(\d+)\|(\w+)\|man\|([\d.]+)\|fix\|([\d.]+)\|jalons\|\[([-\d,]+)\]\|vus\|(\d+)\|sur\|(\d+)\|pas\|(\d+)', l)
    if m:
        ess.setdefault(int(m.group(1)), {})[m.group(2)] = dict(
            man=float(m.group(3)), fix=float(m.group(4)),
            jal=[int(v) for v in m.group(5).split(',')],
            vus=int(m.group(6)), sur=int(m.group(7)), pas=int(m.group(8)))

comp = sorted(c for c in ess if all(b in ess[c] for b in BRAS))
print(f"  configurations completes : {len(comp)} / 20")
if not comp: sys.exit(1)
sc = lambda c, b: sum(1 for v in ess[c][b]['jal'] if v == 1)

print("\n  " + "="*72)
print("  SURVIE DU GROUPE MANOEUVRANT AUX JALONS 120/90/60/40   (score /4)")
print("  " + "-"*72)
print("  bras            score median   total   hommes vus   le groupe FIXANT est vu")
for b in BRAS:
    s = [sc(c, b) for c in comp]
    vus = sum(ess[c][b]['vus'] for c in comp); sur = sum(ess[c][b]['sur'] for c in comp)
    fx = [ess[c][b]['fix'] for c in comp]
    fvu = sum(1 for v in fx if v >= 1.5)
    print(f"  {b:14s}  {np.median(s):6.1f}       {sum(s):3d}    {vus:3d}/{sur:3d}"
          f"        {fvu:2d}/{len(comp)}  (know median {np.median(fx):.2f})")
print("  " + "="*72)

# ---------------------------------------------------------------- 1. VALIDITE
bruit = [abs(sc(c, 'deux_axes') - sc(c, 'deux_axes_bis')) for c in comp]
s_bruit = float(np.mean(bruit))
disc = sum(1 for b in bruit if b > 0)
print(f"\n  1. VALIDITE — le meme bras rejoue deux fois")
print(f"     ecart moyen deux_axes / bis : {s_bruit:.2f} point ; il differe sur {disc}/{len(comp)}")

ecart_princ = float(np.mean([abs(sc(c,'deux_axes') - sc(c,'flanc_seul')) for c in comp]))
print(f"     ecart moyen deux_axes / flanc_seul : {ecart_princ:.2f} point")
valide = ecart_princ > s_bruit
print(f"     -> {'l effet depasse le bruit' if valide else 'BANC NUL : l effet ne depasse pas le bruit de rejeu'}")

# ---------------------------------------------------------------- 2. PRIMAIRE
def signes(a, b):
    g = sum(1 for c in comp if sc(c, a) > sc(c, b))
    p = sum(1 for c in comp if sc(c, a) < sc(c, b))
    n = g + p
    if n == 0: return g, p, 1.0
    # test des signes bilateral, egalites exclues
    k = min(g, p)
    pv = 2 * sum(comb(n, i) for i in range(k+1)) / (2**n)
    return g, p, min(pv, 1.0)

print(f"\n  2. PRIMAIRE — deux_axes contre flanc_seul (apparie, egalites exclues)")
g, p, pv = signes('deux_axes', 'flanc_seul')
med = float(np.median([sc(c,'deux_axes') - sc(c,'flanc_seul') for c in comp]))
print(f"     deux_axes gagne {g}, perd {p}, egalite {len(comp)-g-p}  ·  p = {pv:.3f}")
print(f"     gain median {med:+.1f} point (exige > {s_bruit:.2f})")
primaire = pv < 0.05 and med > s_bruit
print(f"     -> {'OK' if primaire else 'ECHEC'}")

# ---------------------------------------------------------------- 4. SECONDAIRE
print(f"\n  4. SECONDAIRE — scinder paie-t-il ?")
for adv in ['bloc_1axe', 'solo']:
    g2, p2, pv2 = signes('deux_axes', adv)
    print(f"     deux_axes contre {adv:10s} : gagne {g2}, perd {p2}, p = {pv2:.3f}")

# ---------------------------------------------------------------- LE FIXANT JOUE-T-IL SON ROLE
fx = [ess[c]['deux_axes']['fix'] for c in comp]
print(f"\n  LE GROUPE FIXANT SE FAIT-IL VOIR ? c'est son role.")
print(f"     know median sur le fixant : {np.median(fx):.2f} · vu (>=1,5) dans "
      f"{sum(1 for v in fx if v >= 1.5)}/{len(comp)} configurations")
if np.median(fx) < 1.5:
    print("     -> IL NE SE FAIT PAS VOIR. Le bras ne teste alors PAS la fixation :")
    print("        une base de feu invisible ne fixe rien, et l'echec est celui du dispositif.")

# ---------------------------------------------------------------- L'ORDRE DES BRAS
print(f"\n  LE CONFONDU D'ORDRE (defenseurs jamais respawnes, memoire qui ne decroit pas)")
for i, b in enumerate(BRAS):
    print(f"     bras {i+1} {b:14s} score total {sum(sc(c,b) for c in comp):3d}")
print("     ⟨si les scores decroissent avec le rang, c'est l'alerte qui s'accumule,")
print("      pas la tactique qui differe. deux_axes est 3e, flanc_seul 4e.⟩")

print("\n  " + "="*72)
print("  CE PILOTE NE CERTIFIE RIEN — il a ete retrograde AVANT depouillement.")
print("  Il oriente le prochain dispositif, il ne tranche pas.")
print("  " + "="*72)
