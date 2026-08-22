#!/usr/bin/env python3
"""LES ECHECS EN MONDE VIDE — deux modes vus a l oeil sur deux episodes, ici COMPTES.

Un monde vide n a pas d adversaire : l episode ne demande plus que de MARCHER jusqu au
point. Chaque echec y est donc une panne de navigation pure, et elle se nomme.

  GEL          la distance ne bouge presque pas de tout l episode
  DEPASSEMENT  l escouade approche puis REPART, et finit plus loin que son minimum
  LENT         elle avance, regulierement, mais n arrive pas dans les 60 pas
"""
import re, glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

RE_L = re.compile(r'^\s+(\d+)\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', re.M)

def trace(f):
    t = open(f, errors="ignore").read()
    lg = [(int(a), int(c), int(d)) for a, b, c, d in RE_L.findall(t)]
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(-?\d+)', t)
    if fin: lg.append((int(fin.group(1)), int(fin.group(2)), int(fin.group(3))))
    return lg

for nom, dos in [("NATIF", "/mnt/data/natif"), ("POLITIQUE", "/mnt/data/politique")]:
    modes = {"GEL": 0, "DEPASSEMENT": 0, "LENT": 0, "autre": 0}
    n = 0
    for f in sorted(glob.glob("%s/p*_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok" or e["prise"]: continue
        lg = trace(f)
        if len(lg) < 3 or lg[0][1] != 0: continue        # on ne garde que les mondes VIDES
        n += 1
        ds = [d for _, _, d in lg if d >= 0]
        if len(ds) < 3: modes["autre"] += 1; continue
        dmin = min(ds); parcouru = ds[0] - dmin
        if parcouru < 20:                      modes["GEL"] += 1
        elif ds[-1] - dmin > 10:               modes["DEPASSEMENT"] += 1
        else:                                  modes["LENT"] += 1
    print("\n  %s — %d echecs en monde VIDE" % (nom, n))
    for k in ["GEL", "DEPASSEMENT", "LENT", "autre"]:
        if modes[k]: print("    %-12s %d" % (k, modes[k]))
