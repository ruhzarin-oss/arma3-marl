#!/usr/bin/env python3
"""COMBIEN DE METRES UN PAS FAIT-IL VRAIMENT DANS ARMA ?

Le gymnase joue `move=14.0 m` par pas (gardien de parametres). La couture commande
`MOVE_SPD=6.0 m/s` pendant `SEC_PAR_PAS=3.28 s`, soit 19,7 m si l ordre passait entier.
On ne suppose ni l un ni l autre : on mesure le RAPPROCHEMENT reel, intervalle par
intervalle, sur les deux nuits.

⚠️ On mesure le rapprochement vers l objectif, pas le chemin parcouru : un homme qui
contourne se rapproche moins qu il ne marche. On prend donc le 90e CENTILE des intervalles
— « quand elle avance droit, elle avance de combien ? » — et non la moyenne, qui melange
la marche, l arret, le contournement et la mort.
"""
import re, glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

RE_L = re.compile(r'^\s+(\d+)\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', re.M)

def inter(f):
    t = open(f, errors="ignore").read()
    lg = [(int(p), int(v), int(d)) for p, v, _, d in RE_L.findall(t)]
    out = []
    for (p0, v0, d0), (p1, v1, d1) in zip(lg, lg[1:]):
        if v0 > 0 and v1 > 0 and d0 >= 0 and d1 >= 0 and p1 > p0:
            out.append((d0 - d1) / float(p1 - p0))      # metres gagnes PAR PAS
    return out

print("\n  %-11s %10s %12s %12s %12s %10s" % ("nuit", "n interv.", "mediane", "90e cent.",
                                              "max", "> 10 m"))
for nom, dos in [("NATIF", "/mnt/data/natif"), ("POLITIQUE", "/mnt/data/politique")]:
    v = []
    for f in sorted(glob.glob("%s/p*_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok": continue
        v += inter(f)
    v.sort()
    if not v: continue
    med = v[len(v)//2]; p90 = v[int(0.90*len(v))]; mx = v[-1]
    gros = 100.0*sum(1 for x in v if x > 10)/len(v)
    print("  %-11s %10d %10.2f m %10.2f m %10.2f m %8.1f %%" % (nom, len(v), med, p90, mx, gros))
print("\n  pour memoire — ce que chaque monde CROIT qu un pas vaut :")
print("    gymnase   move = 14,00 m par pas   (gardien de parametres)")
print("    couture   6,0 m/s x 3,28 s = 19,68 m par pas si l ordre passait entier")
