#!/usr/bin/env bash
# etalon_j1_5graines.sh — PORTE E5 : consolidation de l etalon sur cinq graines.
# 6 doctrines x 2 verbes x 5 graines = 60 cellules, 61 440 episodes.
# Porte : ETENDUE (meilleure - pire graine) < 8 points par cellule. La variance connue du
# bac a sable est de 8,5 points sur douze graines ; au-dela, le monde n est pas assez stable
# pour juger un agent et le jalon 1 n est pas vert.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
for g in 3 4 5 6 7; do
  echo "########## GRAINE $g ##########"
  GRAINE=$g bash etalon_j1.sh 2>&1 | grep -E "succes|VERDICT|cellules|>>>" | head -14
done
echo ""
/home/younes/env_isaaclab/bin/python3 - <<'PY'
import json, glob, collections, statistics
LEV = '/home/younes/arma3-marl/leviathan'
cell = collections.defaultdict(dict)
for g in (3, 4, 5, 6, 7):
    for f in sorted(glob.glob('%s/journaux/j1_*_p0_g%d.jsonl' % (LEV, g))):
        recs = [json.loads(l) for l in open(f)]
        ent = [r for r in recs if r['type'] == 'entete']
        if not ent: continue
        run = ent[-1]['run']
        eps = [r for r in recs if r['type'] == 'episode' and r.get('run') == run]
        if not eps: continue
        nom = ent[-1]['pilote'].split(':')[1]
        par = collections.defaultdict(list)
        for e in eps: par[e['verbe_nom']].append(e)
        for v, lot in par.items():
            cell[(nom, v)][g] = 100.0 * sum(1 for e in lot if e['succes_monde']) / len(lot)

print('=== ETALON CONSOLIDE — 5 graines, 1024 episodes par cellule ===')
print('  %-22s %-10s %7s %7s %7s %7s %7s %8s %8s' %
      ('doctrine', 'verbe', 'g3', 'g4', 'g5', 'g6', 'g7', 'moyenne', 'etendue'))
hors = []
for (nom, v) in sorted(cell):
    d = cell[(nom, v)]
    vals = [d.get(g) for g in (3, 4, 5, 6, 7)]
    ok = [x for x in vals if x is not None]
    if len(ok) < 5:
        print('  %-22s %-10s  INCOMPLET (%d graines)' % (nom, v, len(ok))); continue
    et = max(ok) - min(ok)
    if et >= 8.0: hors.append((nom, v, et))
    print('  %-22s %-10s %6.1f%% %6.1f%% %6.1f%% %6.1f%% %6.1f%% %7.1f%% %7.1f%s'
          % (nom, v, vals[0], vals[1], vals[2], vals[3], vals[4],
             statistics.mean(ok), et, '  HORS' if et >= 8.0 else ''))
print('')
print('=== VERDICT E5 (porte : etendue < 8,0 points par cellule) ===')
print('  cellules : %d | hors porte : %d' % (len(cell), len(hors)))
for n, v, e in hors:
    print('    %-22s %-10s etendue %.1f' % (n, v, e))
if cell and not hors:
    print('  >>> LE MONDE EST ASSEZ STABLE POUR JUGER UN AGENT. Passage a E6.')
else:
    print('  >>> MONDE TROP INSTABLE : on ne peut pas juger un agent a cette echelle.')
    print('      Le jalon 1 n est pas vert. Il faut soit plus d episodes par cellule,')
    print('      soit comprendre d ou vient la dispersion avant d aller plus loin.')
PY
echo "ETALON_5G_DONE"
