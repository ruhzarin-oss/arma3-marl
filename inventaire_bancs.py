#!/usr/bin/env python3
"""inventaire_bancs.py — ORDRE 1 de Fable. Inventaire, SANS calcul et SANS interpretation.

Pour chaque journal de banc Arma : combien d accrochages, y a-t-il un battement de coeur
(SANTE), et la signature du vide est-elle DETECTABLE dans ce format ?

La signature du vide, mesuree le 06/08 sur le run degenere : duree <= 10 s ET dmin = 9999
(la sentinelle d init, jamais mise a jour parce qu aucun assaillant n a spawne).

Un journal ou l on ne sait pas compter les accrochages est INAUDITABLE. On ne devine pas.
"""
import re, glob, os, time
from collections import defaultdict

REP = '/mnt/data/harmattan-sandbox/logs'
# format emis : id|time|duree|cause|campDef|vainqueur|pris|duree_tenue|count_e|count_o|dmin|arrives
# dmin est donc le SEPTIEME champ apres la cause. Une premiere version en sautait cinq et
# lisait count_o : elle annoncait 0 vide sur le journal qui en contient 185. Controle positif
# obligatoire sur ce script : serverBA_replication_apres_seuil.out DOIT en sortir ~185.
FIN = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|(\d+)\|(\w+)\|(?:\d+\|){6}(\d+)\|')

lignes = []
for ch in sorted(glob.glob(f'{REP}/serverBA*.out')):
    nom = os.path.basename(ch)
    n = 0
    vides = 0
    premier_vide = None
    sante = 0
    dmin_lu = 0
    for l in open(ch, errors='ignore'):
        m = FIN.search(l)
        if m:
            n += 1
            duree, dmin = int(m.group(2)), int(m.group(4))
            dmin_lu += 1
            if duree <= 10 and dmin == 9999:
                vides += 1
                if premier_vide is None:
                    premier_vide = n
        elif 'HMT|G|SANTE' in l:
            sante += 1
    if n == 0:
        continue
    # la signature est lisible si le champ dmin a bien ete extrait pour tous les accrochages
    lisible = 'oui' if dmin_lu == n else 'NON'
    date = time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(ch)))
    lignes.append((nom, date, n, vides, premier_vide, sante, lisible))

print(f"\n  {len(lignes)} journaux porteurs d accrochages\n")
print(f"  {'JOURNAL':<40} {'DATE':<12} {'CLOS':>5} {'VIDES':>6} {'1er':>5} {'SANTE':>6} {'SIGN.':>6}")
print("  " + "-" * 90)
for nom, date, n, v, pv, s, li in lignes:
    print(f"  {nom:<40} {date:<12} {n:>5} {v:>6} {str(pv or '.'):>5} "
          f"{('oui' if s else 'non'):>6} {li:>6}")
print("  " + "-" * 90)
longs = [x for x in lignes if x[2] >= 150]
print(f"\n  LONGS (>= 150 accrochages, seuls concernes par l audit) : {len(longs)}")
for nom, date, n, v, pv, s, li in longs:
    etat = 'INAUDITABLE' if li == 'NON' else ('VIDES DETECTES' if v else 'propre')
    print(f"     {nom:<40} {n:>5} clos · {v:>4} vides · {etat}")
temoin = [x for x in lignes if x[0] == 'serverBA_replication_apres_seuil.out']
if temoin:
    v = temoin[0][3]
    print(f"  CONTROLE POSITIF DU DETECTEUR : le journal degenere connu rend {v} vides "
          f"-> {'OK' if v > 100 else 'ECHEC, le detecteur ne detecte rien'}")
else:
    print("  CONTROLE POSITIF ABSENT : le journal temoin n est pas la, resultats non fiables")
print()
