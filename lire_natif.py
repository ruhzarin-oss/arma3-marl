#!/usr/bin/env python3
"""DEPOUILLE DU NATIF — contre DEPOT_NATIF.md, ecrit le 16/08 AVANT tout episode.

PRISE = un attaquant VIVANT a moins de 25 m (assault_terrain.py:814).
Conditions ELIMINATOIRES : prevol vert ; le natif BOUGE (> 1 m/pas) ; le natif TIRE.
⚠️ Les episodes SANS ESCOUADE (morts pendant le prevol) N ONT PAS EU LIEU : ils sortent
   du compte, ils ne sont ni prise ni echec.

⚠️ LA SENTINELLE -1 N EST PAS UNE DISTANCE. Mon premier lecteur calculait le deplacement
sur la DERNIERE ligne : quand l escouade meurt, elle vaut -1, le deplacement tombait a 0,
et l episode etait ECARTE par la condition 2. J excluais donc systematiquement les
episodes ou les attaquants MEURENT — les echecs — et le taux montait mecaniquement a
91,9 %. UN LECTEUR QUI JETTE LES ECHECS MESURE UNE REUSSITE QU IL A FABRIQUEE.
On prend donc la derniere distance VALIDE, celle d avant la mort.
"""
import re, glob, math, collections

def lire(f):
    t = open(f, errors="ignore").read()
    if "BANC DE MONTAGE TERMINE" not in t: return None
    if "prevol VERT" not in t: return dict(etat="prevol rouge")
    if "ESCOUADE MORTE AVANT LE DEPART" in t: return dict(etat="sans escouade")
    lig = [re.search(r'^\s+(\d+)\s+\d+\s+(\d+)\s+(\d+)\s+(-?\d+)', L) for L in t.split("\n")]
    lig = [(int(m.group(1)), int(m.group(2)), int(m.group(4))) for m in lig if m]
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(-?\d+)', t)
    if fin: lig.append((int(fin.group(1)), int(fin.group(2)), int(fin.group(3))))
    if len(lig) < 2: return dict(etat="illisible")
    cp = re.search(r'COUPS\s+: att=(\d+) def=(\d+)', t)
    d0 = lig[0][2]
    valides = [d for _, _, d in lig if d >= 0]
    dfin = valides[-1] if valides else -1
    npas = max(1, lig[-1][0])
    return dict(etat="ok", npas=npas, viv=lig[-1][1], dfin=dfin,
                mpas=((d0 - dfin) / npas) if (d0 >= 0 and dfin >= 0) else 0.0,
                coups=int(cp.group(1)) if cp else -1,
                prise=(lig[-1][1] > 0 and 0 <= lig[-1][2] < 25))

res = {}
for pas in ("p1", "p2"):
    E = [e for e in (lire(f) for f in sorted(glob.glob("/mnt/data/natif/%s_e*.txt" % pas))) if e]
    c = collections.Counter(e["etat"] for e in E)
    ok = [e for e in E if e["etat"] == "ok"]
    # ⚠️ LA CONDITION 2 EST UN CONTROLE DU MONDE, PAS UN FILTRE D EPISODE — et la mesure
    # le tranche : les 36 episodes qu elle ecarte sont des ECHECS A 100 % (0 prise sur 36).
    # Appliquee par episode, elle ne retire QUE des echecs et gonfle le taux de 56 a 91 %.
    # C est un biais de selection de manuel, et c est la deuxieme fois ce soir que mon
    # lecteur fabrique une reussite en jetant les echecs.
    # ⚠️ SA RAISON D ETRE EST UN CONTROLE DU MONDE : ecrite le 15/08 apres une IA qui ne
    # bougeait PAS DU TOUT — 0,07 m/pas sur 18 episodes. Ici la mediane vaut 2,3 m/pas :
    # le monde bouge, le controle PASSE, et il n a pas a trier les episodes un par un.
    mp = sorted(e["mpas"] for e in ok)
    med_mpas = mp[len(mp)//2] if mp else 0.0
    monde_bouge = med_mpas > 1.0
    print("   condition 2 · CONTROLE DU MONDE : mediane %.2f m/pas  ->  %s"
          % (med_mpas, "PASSE" if monde_bouge else "⛔ LE MONDE NE BOUGE PAS"))
    bouge = ok if monde_bouge else []
    res[pas] = bouge
    print("=== %s ===  %d episodes complets" % (pas.upper(), len(E)))
    for k, v in sorted(c.items()): print("   %-16s %d" % (k, v))
    cps = sorted(e["coups"] for e in ok if e["coups"] >= 0)
    if cps: print("   condition 3 · coups attaquants : mediane %d  (exige >= 1)" % cps[len(cps)//2])
    if bouge:
        pr = sum(1 for e in bouge if e["prise"])
        print("   ➤ PRISES : %d / %d = %.1f %%" % (pr, len(bouge), 100.0*pr/len(bouge)))

a, b = res["p1"], res["p2"]
if a and b:
    ta = 100.0*sum(1 for e in a if e["prise"])/len(a)
    tb = 100.0*sum(1 for e in b if e["prise"])/len(b)
    print("\n═══ CONCORDANCE — critere depose : moins de 10 points ═══")
    print("  passe 1 : %.1f %% (n=%d)   passe 2 : %.1f %% (n=%d)   ecart : %.1f points"
          % (ta, len(a), tb, len(b), abs(ta-tb)))
    if abs(ta-tb) < 10:
        n = len(a)+len(b); p = (sum(1 for e in a if e["prise"])+sum(1 for e in b if e["prise"]))/n
        s = 1.96*math.sqrt(p*(1-p)/n)
        print("  ✓ CONCORDANT\n\n  ➤ NATIF = %.1f %%   n=%d   IC95 [%.1f ; %.1f]"
              % (100*p, n, 100*(p-s), 100*(p+s)))
    else:
        print("  ⛔ DIVERGENT — aucun des deux n est cite.")
