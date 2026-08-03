#!/usr/bin/env python3
"""Lecture du banc Arma : l'angle mort tient-il dans le vrai moteur ?"""
import re, sys
from collections import defaultdict

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
d = defaultdict(list); caps = set()
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|BANC\|fin\|(\d+)\|(\w+)\|(\d+)\|dist_detect\|(-?\d+)\|temps_detect\|(-?[\d.]+)', l)
    if m: d[(int(m.group(1)), m.group(2))].append(int(m.group(4)))
    m = re.search(r'HMT\|BANC\|pas\|.*\|cap\|(\d+)', l)
    if m: caps.add(int(m.group(1)))

n = sum(len(v) for v in d.values())
print(f"  essais terminés : {n} / 45")
print(f"  caps observés chez les défenseurs : {sorted(caps)}"
      f"   -> {'TENU' if caps <= {0} else 'IL DÉRIVE — mesure invalide'}")
if not n: sys.exit()

NOM = {'UP':'debout', 'MIDDLE':'accroupi', 'DOWN':'couché'}
print(f"\n  {'azimut':>7s} {'posture':>9s} {'n':>3s}   distances de détection (m, -1 = jamais repéré)")
for k in sorted(d):
    print(f"  {k[0]:>7d} {NOM.get(k[1],k[1]):>9s} {len(d[k]):>3d}   {d[k]}")

pa = defaultdict(list); pp = defaultdict(list)
for (az, po), v in d.items():
    pa[az] += v; pp[po] += v

def bloc(titre, dic, cle):
    print(f"\n  {titre}")
    for k in sorted(dic, key=lambda x: (x if isinstance(x,int) else ['UP','MIDDLE','DOWN'].index(x))):
        v = dic[k]; det = [x for x in v if x > 0]
        jamais = sum(1 for x in v if x < 0)
        lib = f"{k}°" if isinstance(k,int) else NOM.get(k,k)
        moy = f"{sum(det)/len(det):5.0f} m" if det else "   —  "
        print(f"    {lib:>9s}  n={len(v):2d}   jamais repéré {jamais}/{len(v)}   "
              f"repéré en moyenne à {moy}")

bloc("PAR AZIMUT D'APPROCHE  (0° = plein devant eux, 180° = dans leur dos)", pa, 'az')
bloc("PAR POSTURE", pp, 'po')

# la question du projet
f = pa.get(0, []); dos = pa.get(180, [])
if f and dos:
    df = [x for x in f if x>0]; dd = [x for x in dos if x>0]
    print(f"\n  FRONTAL contre DOS")
    print(f"    frontal : repéré {len(df)}/{len(f)} fois"
          + (f", à {sum(df)/len(df):.0f} m en moyenne" if df else ""))
    print(f"    dos     : repéré {len(dd)}/{len(dos)} fois"
          + (f", à {sum(dd)/len(dd):.0f} m en moyenne" if dd else ""))
    if df and dd:
        print(f"    -> on est repéré {sum(df)/len(df)/max(sum(dd)/len(dd),1):.2f}x plus loin de face")

# la mesure qui manquait
up = pp.get('UP', []); dw = pp.get('DOWN', [])
if up and dw:
    du = [x for x in up if x>0]; dl = [x for x in dw if x>0]
    print(f"\n  SE COUCHER RETARDE-T-IL LE REPÉRAGE ?   ⟨la mesure qui manquait au simulateur⟩")
    print(f"    debout : repéré {len(du)}/{len(up)} fois"
          + (f", à {sum(du)/len(du):.0f} m" if du else ""))
    print(f"    couché : repéré {len(dl)}/{len(dw)} fois"
          + (f", à {sum(dl)/len(dl):.0f} m" if dl else ""))
    if du and dl:
        r = (sum(du)/len(du)) / max(sum(dl)/len(dl), 1)
        print(f"    -> se coucher fait repérer {r:.2f}x plus PRÈS"
              f"  {'-> LE RÉPERTOIRE EST RÉEL' if r > 1.2 else '-> pas d effet net'}")
