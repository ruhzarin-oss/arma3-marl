#!/usr/bin/env python3
"""depouille_bruit.py — D OU VIENT LE BRUIT DE LA LIGNE DE VUE ?

Trois lectures, dans cet ordre, et chacune separe deux coupables possibles :
  1. VARIANCE DANS une session (A contre B, 3 min d ecart) contre VARIANCE ENTRE sessions.
     Si le bruit est surtout ENTRE, la session elle-meme change quelque chose.
  2. MESURE A (tot) contre MESURE B (tard). Si A differe systematiquement de B, c est un
     monde pas encore charge — l INSTRUMENT — et ca se repare par un temps de chauffe.
  3. LES PAS QUI BASCULENT ont-ils plus de vegetation que les pas stables ? Si oui, c est le
     MONDE : le vent dans les feuilles fait scintiller la vue, pour mon geometre comme pour
     un guetteur reel. Alors un lieu n a pas UNE exposition, il en a une DISTRIBUTION.
"""
import re, glob, math

pat = re.compile(r'HMT\|BR\|masque\|(\d+)\|([AB])\|vus\|(\d+)\|sur\|(\d+)\|m\|([01]+)\|veg\|\[([^\]]*)\]')
D = {}
for f in sorted(glob.glob('/mnt/data/harmattan-sandbox/logs/bruit_s*.out')):
    s = int(re.search(r'bruit_s(\d+)', f).group(1))
    for L in open(f, encoding='utf-8', errors='ignore'):
        m = pat.search(L)
        if m:
            lieu, mes, vus, tot, mask, veg = m.groups()
            D[(int(lieu), s, mes)] = (int(vus), int(tot), mask,
                                      [int(x) for x in veg.replace(' ', '').split(',') if x])
lieux = sorted(set(k[0] for k in D)); sess = sorted(set(k[1] for k in D))
print(f"\n  {len(lieux)} lieux · {len(sess)} sessions · {len(D)} mesures")

def moy(v): return sum(v)/len(v) if v else 0.0
def ec(v):
    if len(v) < 2: return 0.0
    m = moy(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

print("\n  1. LA DISPERSION, lieu par lieu (% de pas vus)")
print(f"    {'lieu':>5} {'min':>6} {'max':>6} {'etendue':>8} {'ec-type':>8}  {'dans-session':>13}")
interne, externe = [], []
for L in lieux:
    v = []
    for s in sess:
        pa = D.get((L, s, 'A')); pb = D.get((L, s, 'B'))
        if pa and pb:
            a = 100*pa[0]/pa[1]; b = 100*pb[0]/pb[1]
            v += [a, b]; interne.append(abs(a-b))
            externe.append((a+b)/2)
    if v:
        di = moy([abs(100*D[(L,s,'A')][0]/D[(L,s,'A')][1] - 100*D[(L,s,'B')][0]/D[(L,s,'B')][1])
                  for s in sess if (L,s,'A') in D and (L,s,'B') in D])
        print(f"    {L:>5} {min(v):>6.0f} {max(v):>6.0f} {max(v)-min(v):>8.0f} {ec(v):>8.1f}  {di:>13.1f}")

print(f"\n  2. LES DEUX NATURES DU BRUIT")
print(f"    ecart moyen DANS une session (A vs B, 3 min)  : {moy(interne):.1f} points")
ent = []
for L in lieux:
    par_s = [moy([100*D[(L,s,m)][0]/D[(L,s,m)][1] for m in 'AB' if (L,s,m) in D])
             for s in sess if (L,s,'A') in D]
    if len(par_s) > 1: ent.append(ec(par_s))
print(f"    ecart-type ENTRE sessions (moyenne des lieux) : {moy(ent):.1f} points")

a_tot = [100*D[k][0]/D[k][1] for k in D if k[2]=='A']
b_tot = [100*D[k][0]/D[k][1] for k in D if k[2]=='B']
print(f"\n  3. LE MONDE EST-IL FROID AU DEMARRAGE ?")
print(f"    mesure A (tot dans la session)  : {moy(a_tot):.1f} %")
print(f"    mesure B (3 min plus tard)      : {moy(b_tot):.1f} %")
print(f"    ecart A-B : {moy(a_tot)-moy(b_tot):+.1f} points")

print(f"\n  4. LES PAS QUI BASCULENT SONT-ILS DANS LES FEUILLES ?")
vb, vs_ = [], []
for L in lieux:
    ms = [D[(L,s,m)] for s in sess for m in 'AB' if (L,s,m) in D]
    if len(ms) < 2: continue
    n = min(len(x[2]) for x in ms)
    for i in range(n):
        vals = set(x[2][i] for x in ms)
        veg = moy([x[3][i] for x in ms if i < len(x[3])])
        (vb if len(vals) > 1 else vs_).append(veg)
print(f"    pas STABLES  : {len(vs_):>4}  vegetation moyenne le long du rayon : {moy(vs_):.1f}")
print(f"    pas QUI BASCULENT : {len(vb):>4}  vegetation moyenne : {moy(vb):.1f}")
if vb and vs_:
    r = moy(vb)/moy(vs_) if moy(vs_) > 0 else float('inf')
    print(f"    rapport : x{r:.2f}")
    print("\n  LECTURE : " + ("le MONDE — le vent dans les feuilles fait scintiller la vue."
          if r > 1.5 else "PAS la vegetation — le bruit est ailleurs, a chercher."))
