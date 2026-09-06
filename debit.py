#!/usr/bin/env python3
"""debit — COMBIEN DE SECONDES COUTE UN EPISODE, MESURE AU RPT.

⚠️ POURQUOI PAS LES DUREES DE LOT DU JOURNAL. Elles existent (« 435 s »), mais elles ne
sont PAS stationnaires : la politique se condense, ses gestes raccourcissent, et le lot
est passe de 514 s a 306 s en vingt mises a jour SANS que rien d'exterieur ne change.
Comparer « avant » a « pendant » sur ces durees attribuerait a la parallelisation une
acceleration qui vient de l'apprentissage — et masquerait un ralentissement reel. Le
biais va donc dans le sens qui rassure, c'est le pire.

Cet instrument lit les horodatages du RPT et rend le temps de mur entre deux RESULT
consecutifs : le vrai cout d'un episode, remise a zero comprise. 24 fois plus de points
que le journal, et alignables a la minute sur les blocs d'un plan ABAB.

⚠️ Un episode a cheval sur minuit rendrait -86400 s. On corrige, on ne jette pas.
"""
import re, sys, argparse, datetime as dt

LIGNE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}) .*\[ECHP\] RESULT (\d+) ")

def resultats(rpt):
    out, prec = [], None
    for l in open(rpt, errors="ignore"):
        m = LIGNE.match(l)
        if not m: continue
        h, mi, s, uid = int(m[1]), int(m[2]), int(m[3]), int(m[4])
        t = h*3600 + mi*60 + s
        if prec is not None and t < prec: t += 86400      # passage de minuit
        prec = t
        out.append((t, uid))
    return out

def fenetre(res, t0, t1):
    """Durees d'episode dont le RESULT tombe dans [t0, t1)."""
    d = []
    for i in range(1, len(res)):
        if t0 <= res[i][0] < t1:
            dd = res[i][0] - res[i-1][0]
            if 0 < dd < 300: d.append(dd)                 # un ecart >5 min = coupure, pas un episode
    return d

def stat(d):
    if not d: return "aucun episode"
    n = len(d); m = sum(d)/n
    sd = (sum((x-m)**2 for x in d)/(n-1))**0.5 if n > 1 else 0.0
    se = sd/n**0.5 if n else 0.0
    return f"n={n:3d}  {m:5.2f} s/ep  ecart-type {sd:4.2f}  IC95 [{m-1.96*se:5.2f} ; {m+1.96*se:5.2f}]"

def hms(s):
    s = int(s) % 86400
    return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpt", required=True)
    ap.add_argument("--blocs", default="", help="t0-t1,t0-t1,... en HH:MM")
    ap.add_argument("--derniers", type=int, default=0, help="stat sur les N derniers episodes")
    a = ap.parse_args()
    res = resultats(a.rpt)
    if not res: print("aucun RESULT dans ce RPT"); return 1
    print(f"{len(res)} episodes, de {hms(res[0][0])} a {hms(res[-1][0])}")
    if a.derniers:
        d = [res[i][0]-res[i-1][0] for i in range(max(1,len(res)-a.derniers), len(res))]
        d = [x for x in d if 0 < x < 300]
        print(f"  {a.derniers} derniers : {stat(d)}")
    for b in filter(None, a.blocs.split(",")):
        g, h = b.split("-")
        t0 = int(g[:2])*3600 + int(g[3:5])*60
        t1 = int(h[:2])*3600 + int(h[3:5])*60
        print(f"  {g}-{h} : {stat(fenetre(res, t0, t1))}")
    return 0

sys.exit(main())
