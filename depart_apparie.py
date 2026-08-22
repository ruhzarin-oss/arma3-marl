#!/usr/bin/env python3
"""LES DEUX NUITS NE PARTENT PAS DU MEME ENDROIT.

La scene pose les attaquants a 170 m dans les deux cas. Mais le premier etat est lu APRES
le prevol — 60 a 180 s de monde EVEILLE. Dans le bras NATIF, l IA d Arma est active : elle
MARCHE pendant ce temps. Dans le bras POLITIQUE, AUTOCOMBAT et FSM sont coupes : les hommes
attendent l ordre, immobiles.

Si c est vrai, le natif commence son episode plus pres, sur un budget de 60 pas qui MORD
(90e centile des arrivees : 52-56 pas). Ce serait un avantage d INSTRUMENT, pas de cerveau.

On mesure, puis on APPARIE : a distance de depart comparable, l ecart survit-il ?
"""
import re, glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

RE0 = re.compile(r'^\s+0\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', re.M)

def d0(f):
    m = RE0.search(open(f, errors="ignore").read())
    return (int(m.group(3)), int(m.group(2))) if m else (None, None)

N = {}
for nom, dos in [("NATIF", "/mnt/data/natif"), ("POLITIQUE", "/mnt/data/politique")]:
    v = []
    for f in sorted(glob.glob("%s/p*_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok": continue
        d, nd = d0(f)
        if d is None or d < 0: continue
        v.append((d, nd, bool(e["prise"])))
    N[nom] = v
    ds = sorted(x[0] for x in v)
    print("\n  %-10s n=%d   depart : min %d   mediane %d   max %d m"
          % (nom, len(v), ds[0], ds[len(ds)//2], ds[-1]))
    print("             deja a moins de 150 m au pas 0 : %d sur %d  (%.0f %%)"
          % (sum(1 for x in ds if x < 150), len(ds), 100.0*sum(1 for x in ds if x < 150)/len(ds)))

print("\n  ══ TAUX DE PRISE PAR BANDE DE DEPART ══")
print("\n  %-14s %22s %22s" % ("bande de depart", "NATIF", "POLITIQUE"))
bandes = [(0, 120), (120, 150), (150, 168), (168, 999)]
for lo, hi in bandes:
    lig = "  %-14s" % ("%d - %d m" % (lo, hi) if hi < 999 else "%d m et plus" % lo)
    t = {}
    for nom in ("NATIF", "POLITIQUE"):
        s = [p for d, _, p in N[nom] if lo <= d < hi]
        t[nom] = (100.0*sum(s)/len(s), len(s)) if s else (float("nan"), 0)
        lig += " %16.1f %% (n=%2d)" % t[nom]
    print(lig)

print("\n  ══ APPARIE : bande 150-168 m, la seule ou les deux nuits sont peuplees ══")
a = [p for d, _, p in N["NATIF"] if 150 <= d < 168]
b = [p for d, _, p in N["POLITIQUE"] if 150 <= d < 168]
if a and b:
    print("    NATIF     %.1f %% (n=%d)" % (100.0*sum(a)/len(a), len(a)))
    print("    POLITIQUE %.1f %% (n=%d)" % (100.0*sum(b)/len(b), len(b)))
    print("    ecart     %+.1f points   (contre +15,4 tout compris)"
          % (100.0*sum(a)/len(a) - 100.0*sum(b)/len(b)))
