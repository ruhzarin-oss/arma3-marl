#!/usr/bin/env python3
"""lire_smoke.py — LA FIXATION-PAR-LE-REGARD EXISTE-T-ELLE DANS ARMA ?

Les trois signatures ont ete ecrites AVANT le run :
  regard qui VISE les fixateurs   -> erreur vers la cible proche de 0°
  regard qui NE BOUGE PAS         -> erreur vers la cible ~30° (l'angle ou ils sont poses)
  derive spontanee                -> erreur large et dispersee

Et la question de Fable, qui tranche : LES ARCS SUIVENT-ILS ?
⟨certifie dans le projet : le cone ne pivote pas, il S'OUVRE. Des tetes qui bougent sans
 que les armes suivent ne seraient pas de la fixation, et tout banc d'escouade en
 perception pure serait mort-ne.⟩
"""
import re, sys
import numpy as np

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
R = {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|SMOKE\|releve\|(\w+)\|libre\|(\d)\|regard_cap\|(-?\d+)\|arme_cap\|(-?\d+)\|regard_cible\|(-?\d+)\|arme_cible\|(-?\d+)', l)
    if m:
        R.setdefault((m.group(1), m.group(2)), []).append(
            [int(m.group(i)) for i in (3, 4, 5, 6)])

NOM = {('A','0'): 'A  caps FORCES, personne        (controle nul)',
       ('B','1'): 'B  caps LIBERES, personne       (derive spontanee)',
       ('C','0'): 'C1 caps forces, fixateurs poses (avant liberation)',
       ('C','1'): 'C2 caps LIBERES au 1er tir      (LA MESURE)'}

print("  " + "="*82)
print("  phase                                        n   regard/cap  arme/cap  regard/cible  arme/cible")
print("  " + "-"*82)
for k in sorted(R):
    v = np.array(R[k]); md = np.median(v, axis=0)
    lib = "regard/cible" if md[2] >= 0 else ""
    print(f"  {NOM.get(k, str(k)):43s} {len(v):3d}   {md[0]:7.0f}°  {md[1]:7.0f}°"
          f"    {md[2]:8.0f}°   {md[3]:8.0f}°   " if md[2] >= 0 else
          f"  {NOM.get(k, str(k)):43s} {len(v):3d}   {md[0]:7.0f}°  {md[1]:7.0f}°           .          .")
print("  " + "="*82)

def med(k, i):
    return float(np.median([x[i] for x in R[k]])) if k in R else None

# ---------------------------------------------------------------- les controles
a = med(('A','0'), 0)
print(f"\n  CONTROLE NUL — phase A : ecart au cap {a:.0f}°", end='  ')
print("OK, le verrou verrouille" if a is not None and a < 5 else "ECHEC : le verrou ne tient pas")

b = med(('B','1'), 0)
print(f"  REFERENCE   — phase B : derive spontanee {b:.0f}° "
      f"(caps liberes, personne en vue)")

# ---------------------------------------------------------------- la mesure
c_rc = med(('C','1'), 2); c_ac = med(('C','1'), 3)
c1_rc = med(('C','0'), 2); c1_ac = med(('C','0'), 3)
print(f"\n  LA MESURE — apres liberation au premier tir")
print(f"     erreur du REGARD vers les fixateurs : {c1_rc:.0f}° avant  ->  {c_rc:.0f}° apres")
print(f"     erreur de l ARME  vers les fixateurs : {c1_ac:.0f}° avant  ->  {c_ac:.0f}° apres")

print("\n  LES TROIS SIGNATURES ECRITES AVANT :")
print(f"     vise la cible  -> proche de 0°     |  ne bouge pas -> ~30°  |  derive -> large")
vise = c_rc is not None and c_rc < 15
fige = c_rc is not None and 20 <= c_rc <= 45
arcs = c_ac is not None and c_ac < 15

print("\n  " + "="*82)
if vise and arcs:
    print("  LA FIXATION EXISTE, ET LES ARCS SUIVENT.")
    print("  Le regard ET l arme se tournent vers la base de feu. Un banc d escouade en")
    print("  perception pure peut donc voir le phenomene : la liberation conditionnelle tient.")
elif vise and not arcs:
    print("  LES TETES BOUGENT, LES ARCS NE SUIVENT PAS.")
    print("  C est exactement le cas prevu par Fable, et il est coherent avec le fait certifie")
    print("  que le cone NE PIVOTE PAS, il S OUVRE. La fixation-par-le-regard n explique donc")
    print("  pas l avantage du flanc : il faut porter le test sur le canal du FEU.")
elif fige:
    print("  LES REGARDS NE BOUGENT PAS, MEME LIBERES ET SOUS LE FEU.")
    print("  L erreur vers la cible reste celle de l angle ou les fixateurs sont poses.")
    print("  La fixation-par-le-regard N EXISTE PAS dans ce regime : un banc d escouade en")
    print("  perception pure est mort-ne. Le mecanisme de l avantage du flanc est ailleurs.")
else:
    print("  RESULTAT INTERMEDIAIRE — a lire ligne par ligne avant de conclure.")
print("  " + "="*82)
