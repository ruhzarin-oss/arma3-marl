#!/usr/bin/env python3
"""LE BANC A-T-IL UN ADVERSAIRE ? — decoupe les deux nuits deposees selon le nombre de
defenseurs VIVANTS au pas 0.

⚠️ ON N ECRIT PAS UN LECTEUR DE PLUS. On appelle `lire_natif.lire`, le lecteur DEPOSE,
et on n ajoute qu une COUPE. Comparer un chiffre neuf a un chiffre depose en changeant
l instrument entre les deux est exactement la faute que ce projet paie le plus cher.
La reproduction des deux totaux deposes (59,6 % et 44,2 %) est la condition de lecture :
si elle rate, rien de ce qui suit ne se cite.
"""
import re, glob, sys
sys.path.insert(0, "/home/younes/arma3-marl")
print("═══ le lecteur DEPOSE tourne d abord, ses chiffres doivent reapparaitre ═══")
import lire_natif as LN     # son code de module s execute : c est la reproduction

RE0 = re.compile(r'^\s+0\s+\d+\s+\d+\s+(\d+)\s+-?\d+', re.M)

def def0(f):
    m = RE0.search(open(f, errors="ignore").read())
    return int(m.group(1)) if m else None

def nuit(dos):
    out = []
    for f in sorted(glob.glob("%s/p*_e*.txt" % dos)):
        e = LN.lire(f)
        if not e or e.get("etat") != "ok": continue
        d = def0(f)
        if d is None: continue
        out.append((d, bool(e["prise"])))
    return out

print("\n═══ LA COUPE : y avait-il un adversaire au depart ? ═══")
print("\n  %-12s %26s %26s %14s" % ("nuit", "SANS defenseur", "AVEC >= 1 defenseur", "total"))
tab = {}
for nom, dos in [("NATIF", "/mnt/data/natif"), ("POLITIQUE", "/mnt/data/politique")]:
    v = nuit(dos)
    z = [p for d, p in v if d == 0]; u = [p for d, p in v if d >= 1]
    tz = 100.0*sum(z)/len(z) if z else float("nan")
    tu = 100.0*sum(u)/len(u) if u else float("nan")
    tt = 100.0*sum(p for _, p in v)/len(v) if v else float("nan")
    tab[nom] = (tz, len(z), tu, len(u), tt, len(v))
    print("  %-12s %12.1f %% (n=%3d) %14.1f %% (n=%3d) %8.1f %% (n=%3d)"
          % (nom, tz, len(z), tu, len(u), tt, len(v)))

if "NATIF" in tab and "POLITIQUE" in tab:
    en = tab["NATIF"][4] - tab["POLITIQUE"][4]
    ed = tab["NATIF"][2] - tab["POLITIQUE"][2]
    print("\n  ecart NATIF - POLITIQUE, tout compris          : %+.1f points" % en)
    print("  ecart NATIF - POLITIQUE, adversaire present     : %+.1f points" % ed)
    print("\n  part du banc SANS adversaire : natif %.0f %%, politique %.0f %%"
          % (100.0*tab["NATIF"][1]/tab["NATIF"][5], 100.0*tab["POLITIQUE"][1]/tab["POLITIQUE"][5]))
