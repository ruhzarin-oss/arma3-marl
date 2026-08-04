#!/usr/bin/env python3
"""lire_escouade2.py — LE BANC D'ESCOUADE, DISPOSITIF CORRIGE.

Corrections par rapport au pilote : weaponDirection au lieu d'eyeDirection · defenseurs
RECREES entre chaque bras · ordre BRASSE · liberation conditionnelle au premier tir.

LA COMPARAISON PRINCIPALE EST A EFFECTIF EGAL : deux_axes (3 manoeuvrants) contre
flanc_seul (3 manoeuvrants), meme chemin de flanc, meme configuration. Seule la presence
de la base de feu change. ⟨solo et bloc_1axe n'ont PAS cet effectif : la metrique punit le
nombre par construction — un groupe est repere des qu'UN homme l'est — donc leurs scores
ne se comparent pas directement. Ils sont la pour le contexte, pas pour la these.⟩

CRITERES DE FABLE, ECRITS AVANT LES RESULTATS :
  P0 VALIDITE  |deux_axes - bis| donne le bruit. Si l'ecart entre bras ne le depasse pas
               NETTEMENT, banc nul — verdict sur le dispositif, rien de tactique.
  P1 PRESENCE  bloc_1axe doit etre repere.
  P2 FIXATION  deux_axes > flanc_seul, test des signes p < 0,05, gain median > bruit.
  P3 MECANISME arme_vers_manoeuvrant plus GRAND pendant deux_axes que pendant flanc_seul.
               Un effet sans mecanisme n'est pas certifiable.
  P4 TIR       les fixateurs doivent avoir tire, et les autres bras non.
"""
import re, sys
from math import comb
import numpy as np

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
BRAS = ['solo', 'bloc_1axe', 'deux_axes', 'flanc_seul', 'deux_axes_bis']

ess = {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|ESC2\|essai\|(\d+)\|(\w+)\|man\|([\d.]+)\|fix\|([\d.]+)\|jalons\|\[([-\d,]+)\]\|vus\|(\d+)\|sur\|(\d+)\|pas\|(\d+)\|tirs\|(\d+)\|arme_vers_man\|(-?\d+)\|regard_vers_man\|(-?\d+)', l)
    if m:
        ess.setdefault(int(m.group(1)), {})[m.group(2)] = dict(
            man=float(m.group(3)), fix=float(m.group(4)),
            jal=[int(v) for v in m.group(5).split(',')],
            vus=int(m.group(6)), sur=int(m.group(7)), pas=int(m.group(8)),
            tirs=int(m.group(9)), arme=int(m.group(10)), regard=int(m.group(11)))

comp = sorted(c for c in ess if all(b in ess[c] for b in BRAS))
print(f"  configurations completes : {len(comp)} / 20")
if not comp:
    print(f"  ({sum(len(v) for v in ess.values())} essais — le run n'est pas fini)"); sys.exit(1)
sc = lambda c, b: sum(1 for v in ess[c][b]['jal'] if v == 1)

print("\n  " + "="*80)
print("  SURVIE DU GROUPE MANOEUVRANT AUX JALONS 120/90/60/40   (score /4)")
print("  " + "-"*80)
print("  bras            effectif  score median  total  hommes vus   tirs   arme/manoeuvrant")
for b in BRAS:
    s = [sc(c, b) for c in comp]
    eff = int(np.median([ess[c][b]['sur'] for c in comp]))
    vus = sum(ess[c][b]['vus'] for c in comp); sur = sum(ess[c][b]['sur'] for c in comp)
    t = int(np.median([ess[c][b]['tirs'] for c in comp]))
    a = float(np.median([ess[c][b]['arme'] for c in comp]))
    print(f"  {b:14s}    {eff:2d}       {np.median(s):5.1f}      {sum(s):3d}   {vus:3d}/{sur:3d}"
          f"     {t:4d}       {a:5.0f}°")
print("  " + "="*80)

def signes(a, b):
    g = sum(1 for c in comp if sc(c, a) > sc(c, b))
    p = sum(1 for c in comp if sc(c, a) < sc(c, b))
    n = g + p
    if n == 0: return g, p, 1.0
    k = min(g, p)
    return g, p, min(2*sum(comb(n, i) for i in range(k+1))/(2**n), 1.0)

# ---------------------------------------------------------------- P0 VALIDITE
bruit = [abs(sc(c,'deux_axes') - sc(c,'deux_axes_bis')) for c in comp]
b_moy = float(np.mean(bruit)); b_dif = sum(1 for x in bruit if x > 0)
ec = [abs(sc(c,'deux_axes') - sc(c,'flanc_seul')) for c in comp]
e_moy = float(np.mean(ec))
print(f"\n  P0 VALIDITE — le meme bras rejoue deux fois")
print(f"     bruit  deux_axes / bis        : {b_moy:.2f} point · differe sur {b_dif}/{len(comp)}")
print(f"     effet  deux_axes / flanc_seul : {e_moy:.2f} point")
print(f"     ⟨le pilote donnait bruit 0,80 pour effet 0,85 : indiscernable, banc nul⟩")
p0 = e_moy > 2*b_moy if b_moy > 0 else e_moy > 0
print(f"     -> {'OK, l effet domine le bruit' if p0 else 'BANC NUL : le bruit mange l effet'}")

# ---------------------------------------------------------------- P1 PRESENCE
vu1 = sum(1 for c in comp if sc(c,'bloc_1axe') < 4)
p1 = vu1 >= int(0.8*len(comp))
print(f"\n  P1 PRESENCE — bloc_1axe repere dans {vu1}/{len(comp)}  -> {'OK' if p1 else 'ECHEC'}")

# ---------------------------------------------------------------- P2 FIXATION
print(f"\n  P2 FIXATION — deux_axes contre flanc_seul  (MEME chemin, MEME effectif de 3,")
print(f"                seule la base de feu change)")
g, p, pv = signes('deux_axes', 'flanc_seul')
med = float(np.median([sc(c,'deux_axes') - sc(c,'flanc_seul') for c in comp]))
print(f"     gagne {g} · perd {p} · egalite {len(comp)-g-p}  ·  p = {pv:.3f}")
print(f"     gain median {med:+.1f} point (exige > {b_moy:.2f})")
p2 = pv < 0.05 and med > b_moy
print(f"     -> {'OK' if p2 else 'ECHEC'}")

# ---------------------------------------------------------------- P3 MECANISME
a_dx = [ess[c]['deux_axes']['arme'] for c in comp]
a_fs = [ess[c]['flanc_seul']['arme'] for c in comp]
d_arme = float(np.median(a_dx)) - float(np.median(a_fs))
plus = sum(1 for c in comp if ess[c]['deux_axes']['arme'] > ess[c]['flanc_seul']['arme'])
print(f"\n  P3 MECANISME — les armes pointent-elles PLUS LOIN du manoeuvrant avec base de feu ?")
print(f"     deux_axes {np.median(a_dx):5.0f}°  ·  flanc_seul {np.median(a_fs):5.0f}°  "
      f"·  ecart {d_arme:+.0f}°")
print(f"     plus loin dans {plus}/{len(comp)} configurations")
p3 = d_arme > 5 and plus >= int(0.6*len(comp))
print(f"     -> {'OK, la base de feu detourne les armes' if p3 else 'ECHEC : elle ne les detourne pas'}")
if d_arme < -5:
    print(f"     ⟨et l'ecart est NEGATIF : avec base de feu les armes sont PLUS PRES du flanc.")
    print(f"      La fixation reoriente le secteur sans le liberer — l'inverse de ma these.⟩")

# ---------------------------------------------------------------- P4 TIR
t_dx = int(np.median([ess[c]['deux_axes']['tirs'] for c in comp]))
t_fs = int(np.median([ess[c]['flanc_seul']['tirs'] for c in comp]))
p4 = t_dx > 0 and t_fs == 0
print(f"\n  P4 TIR — deux_axes {t_dx} coups · flanc_seul {t_fs} coups  -> {'OK' if p4 else 'ECHEC'}")

# ---------------------------------------------------------------- contexte
print(f"\n  CONTEXTE (effectifs differents — NE PAS comparer directement a la these)")
for adv in ['bloc_1axe', 'solo']:
    g2, p2b, pv2 = signes('deux_axes', adv)
    eff = int(np.median([ess[c][adv]['sur'] for c in comp]))
    print(f"     deux_axes (3) contre {adv:10s} ({eff}) : gagne {g2}, perd {p2b}, p = {pv2:.3f}")
print(f"     ⟨la metrique punit le nombre : un groupe est repere des qu UN homme l est.")
print(f"      Seule la comparaison deux_axes / flanc_seul est immunisee — meme effectif.⟩")

print("\n  " + "="*80)
if not p0:
    print("  BANC NUL. Aucune conclusion tactique autorisee.")
elif p2 and p3:
    print("  LA FIXATION EXISTE ET PROTEGE LE FLANC. Effet ET mecanisme.")
    print("  La these collective tient : le contournement paie quand quelqu un fixe.")
elif p2 and not p3:
    print("  EFFET SANS MECANISME. Le flanc survit mieux avec une base de feu, mais les armes")
    print("  ne sont pas detournees : la cause est ailleurs. Non certifiable en l etat.")
elif not p2 and p3:
    print("  MECANISME SANS EFFET. Les armes se detournent, mais le flanc n en profite pas.")
    print("  Fixer reoriente sans proteger — la these collective ne tient pas ici.")
else:
    print("  NI EFFET NI MECANISME. Dans ce regime, une base de feu ne protege pas le flanc.")
    print("  Ce n est pas une refutation du collectif : c est que la PERCEPTION n est pas le")
    print("  canal. Le prochain test doit porter sur le FEU — qui tire sur qui, et quand.")
print("  " + "="*80)
