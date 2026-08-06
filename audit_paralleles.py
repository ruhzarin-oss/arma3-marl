#!/usr/bin/env python3
"""audit_paralleles.py — ORDRE 2 de Fable, etendu aux douze serveurs paralleles.

Les serverP0..P11 portent 121 a 146 accrochages chacun. C est SOUS le seuil ou v12 est mort
(235), mais le seuil depend du nombre de groupes fuis PAR accrochage : un banc qui en fuit
deux fois plus meurt deux fois plus tot. On ne suppose pas, on mesure.

Trois sorties possibles par journal, et une seule est une conclusion :
  propre       aucun accrochage ne porte la signature du vide
  VIDES        des accrochages vides, avec le rang du premier
  INAUDITABLE  le format des lignes fin ne permet pas de lire dmin -> on ne devine pas

CONTROLE POSITIF OBLIGATOIRE : le journal degenere connu doit rendre ~185 vides. S il n en
rend pas, le detecteur est casse et RIEN de ce qui suit ne se lit.
"""
import re, glob, os

REP = '/mnt/data/harmattan-sandbox/logs'
FIN = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|(\d+)\|(\w+)\|(?:\d+\|){6}(\d+)(?:\||\")')   # « | » (format v12, 12 champs) OU « \" » (format ancien, 11)
FIN_BRUT = re.compile(r'HMT\|G\|fin\|')


def lire(ch):
    n_brut = n = vides = 0
    premier = None
    durees = []
    for l in open(ch, errors='ignore'):
        if FIN_BRUT.search(l):
            n_brut += 1
            m = FIN.search(l)
            if m:
                n += 1
                d, dmin = int(m.group(2)), int(m.group(4))
                durees.append(d)
                if d <= 10 and dmin == 9999:
                    vides += 1
                    if premier is None:
                        premier = n
    return n_brut, n, vides, premier, durees


# --- controle positif du detecteur, AVANT tout le reste
tem = f'{REP}/serverBA_replication_apres_seuil.out'
_, _, v_tem, _, _ = lire(tem)
print(f"\n  CONTROLE POSITIF : le journal degenere connu rend {v_tem} vides -> "
      f"{'OK' if v_tem > 100 else 'ECHEC — detecteur casse, on s arrete'}")
if v_tem <= 100:
    raise SystemExit(1)

print(f"\n  {'JOURNAL':<22} {'FIN':>5} {'LUS':>5} {'VIDES':>6} {'1er':>5} "
      f"{'duree med':>10} {'min':>5}   ETAT")
print("  " + "-" * 82)
for ch in sorted(glob.glob(f'{REP}/serverP*.out'),
                 key=lambda p: int(re.search(r'P(\d+)', p).group(1))):
    nb, n, v, pr, dur = lire(ch)
    if nb == 0:
        continue
    if n < nb:
        etat = f'INAUDITABLE ({nb-n} lignes fin illisibles)'
        med = mn = 0
    else:
        dur.sort()
        med = dur[len(dur) // 2] if dur else 0
        mn = dur[0] if dur else 0
        etat = 'propre' if v == 0 else 'VIDES DETECTES'
    print(f"  {os.path.basename(ch):<22} {nb:>5} {n:>5} {v:>6} {str(pr or '.'):>5} "
          f"{med:>10} {mn:>5}   {etat}")
print("  " + "-" * 82)
print()
