#!/usr/bin/env python3
"""autopsie.py — DEUX LECTURES, ZERO RUN. ⟨Fable, 09/08⟩

  (a) LE +57 % DU TERRAIN 0 : artefact de ligne de base instable, ou couplage reel ?
      Si la dispersion INTRA-terrain est enorme, l epitaphe est « illisible ».
      Si elle est serree, le couplage alerte/suppression est reel et l epitaphe est
      « incoherent par lieu » — ce qui n est pas la meme chose.
  (b) L ESSAI TEMOIN A ZERO : 157 coups tires, zero impact delivre, presence qui dit « tous ».
      C est la signature de la famille qui a tue cinq versions : la panne silencieuse.
"""
import re, statistics
F = '/mnt/data/harmattan-sandbox/logs/serverAP.out'
pat = re.compile(r'HMT\|AP\|essai\|(\d+)\|(\d+)\|terrain\|(-?\d+)\|delivre\|(\d+)\|armes\|(\d+)'
                 r'\|cap0\|([\d,]+)\|cap1\|([\d,]+)\|coupsdef\|(\d+)\|coupsapp\|(\d+)'
                 r'\|murs\|(\d+)\|corps\|(\d+)\|angle\|([-\d.]+)\|refus\|(\d+)\|vise\|([-\d.]+)'
                 r'\|supp\|([-\d.]+)\|vivants\|(\d+)\|(\d+)')
E = []
for L in open(F, encoding='utf-8', errors='ignore'):
    m = pat.search(L)
    if m:
        g = m.groups()
        E.append(dict(bras=int(g[0]), rep=int(g[1]), ter=int(g[2]), dl=int(g[3]),
                      cap0=[int(x) for x in g[5].split(',')], cap1=[int(x) for x in g[6].split(',')],
                      cd=int(g[7]), ca=int(g[8]), murs=int(g[9]), corps=int(g[10]),
                      supp=float(g[14]), vd=int(g[15]), vv=int(g[16])))
E = [e for e in E if e['rep'] > 0]
noms = {0: 'temoin', 1: 'scripte', 2: 'natif'}

print("\n(a) LE +57 % DU TERRAIN 0 — essai par essai, pas en moyenne")
print("    %-9s%-9s%9s%9s%9s%7s%7s" % ("bras", "rep", "delivre", "coupsdef", "coupsapp", "murs", "supp"))
for b in (0, 1, 2):
    v = []
    for e in sorted([x for x in E if x['ter'] == 0 and x['bras'] == b], key=lambda x: x['rep']):
        print("    %-9s%-9d%9d%9d%9d%7d%7.2f" % (noms[b], e['rep'], e['dl'], e['cd'], e['ca'], e['murs'], e['supp']))
        v.append(e['dl'])
    if len(v) > 1:
        print("    %-9s%-9s%9.0f  ecart-type %.0f  soit %.0f %% de la moyenne\n"
              % ("", "moyenne", statistics.mean(v), statistics.stdev(v),
                 100 * statistics.stdev(v) / statistics.mean(v)))

print("  LECTURE : on compare la dispersion INTRA-terrain a l ecart ENTRE bras.")
for b in (0, 1, 2):
    v = [e['dl'] for e in E if e['ter'] == 0 and e['bras'] == b]
    print("    %-9s n=%d  moyenne %6.0f  ecart-type %6.0f" % (noms[b], len(v), statistics.mean(v),
          statistics.stdev(v) if len(v) > 1 else 0))

print("\n(b) L ESSAI TEMOIN A ZERO — et ses voisins, pour comparer")
z = [e for e in E if e['bras'] == 0 and e['dl'] == 0]
for e in z:
    print("    terrain %d rep %d : delivre %d · coupsdef %d · corps %d · murs %d"
          % (e['ter'], e['rep'], e['dl'], e['cd'], e['corps'], e['murs']))
    print("      capacites entree %s · sortie %s   [combattre,tirer,bouger,pret]"
          % (e['cap0'], e['cap1']))
    print("      vivants def %d / vic %d · suppression relevee %.3f" % (e['vd'], e['vv'], e['supp']))
    frat = [x for x in E if x['ter'] == e['ter'] and x['bras'] == 0 and x['rep'] != e['rep']]
    print("      les autres temoins du meme terrain : %s impacts delivres pour %s coups"
          % ([x['dl'] for x in frat], [x['cd'] for x in frat]))

print("\n  RAPPORT coups tires -> impacts delivres, tous les temoins :")
for e in sorted([x for x in E if x['bras'] == 0], key=lambda x: (x['ter'], x['rep'])):
    r = e['dl'] / e['cd'] if e['cd'] else -1
    print("    terrain %d rep %-3d %5d coups -> %4d impacts   rendement %.3f%s"
          % (e['ter'], e['rep'], e['cd'], e['dl'], r, "   <== L ESSAI MORT" if e['dl'] == 0 else ""))
