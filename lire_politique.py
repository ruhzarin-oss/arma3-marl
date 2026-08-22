#!/usr/bin/env python3
"""DEPOUILLE DE LA POLITIQUE — LE MEME LECTEUR QUE LE NATIF, pointe ailleurs.

⚠️ C EST TOUT L INTERET : une grandeur comparee exige LE MEME INSTRUMENT dans les deux
bras. On importe `lire()` de `lire_natif.py` sans le recopier — une copie divergerait, et
la semaine entiere a montre ce que coutent deux copies d un meme acte.
"""
import glob, math, collections, importlib.util
_s = importlib.util.spec_from_file_location("ln", "/home/younes/arma3-marl/lire_natif.py")
_src = open("/home/younes/arma3-marl/lire_natif.py").read()
_ns = {}
exec(compile(_src[:_src.index("res = {}")], "ln", "exec"), _ns)
lire = _ns["lire"]

res = {}
for pas in ("p1", "p2"):
    E = [e for e in (lire(f) for f in sorted(glob.glob("/mnt/data/politique/%s_e*.txt" % pas))) if e]
    c = collections.Counter(e["etat"] for e in E)
    ok = [e for e in E if e["etat"] == "ok"]
    print("=== %s ===  %d episodes complets" % (pas.upper(), len(E)))
    for k, v in sorted(c.items()): print("   %-16s %d" % (k, v))
    cps = sorted(e["coups"] for e in ok if e["coups"] >= 0)
    if cps: print("   condition 3 · coups attaquants : mediane %d  (exige >= 1)" % cps[len(cps)//2])
    mp = sorted(e["mpas"] for e in ok)
    med = mp[len(mp)//2] if mp else 0.0
    print("   condition 2 · CONTROLE DU MONDE : mediane %.2f m/pas  ->  %s"
          % (med, "PASSE" if med > 1.0 else "⛔ LE MONDE NE BOUGE PAS"))
    res[pas] = ok if med > 1.0 else []
    if res[pas]:
        pr = sum(1 for e in res[pas] if e["prise"])
        print("   ➤ PRISES : %d / %d = %.1f %%" % (pr, len(res[pas]), 100.0*pr/len(res[pas])))

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
        print("  ✓ CONCORDANT\n\n  ➤ POLITIQUE = %.1f %%   n=%d   IC95 [%.1f ; %.1f]"
              % (100*p, n, 100*(p-s), 100*(p+s)))
        # ═══ LA COMPARAISON, avec le critere ecrit le 16/08 ═══
        NAT, nn = 0.596, 114
        print("\n═══ LA COMPARAISON ═══")
        print("  NATIF     = 59,6 %%   n=%d" % nn)
        print("  POLITIQUE = %.1f %%   n=%d" % (100*p, n))
        d = 100*p - 100*NAT
        se = math.sqrt(NAT*(1-NAT)/nn + p*(1-p)/n) * 100
        print("  ecart = %+.1f points   erreur-type %.1f   IC95 [%+.1f ; %+.1f]"
              % (d, se, d-1.96*se, d+1.96*se))
        print("\n  ⚠️ CRITERE DEPOSE LE 16/08, AVANT TOUT EPISODE :")
        print("     « un ecart inferieur a 12 points ne sera pas revendique, meme s il va")
        print("       dans le bon sens ».")
        if abs(d) < 12:
            print("  ➤ ECART SOUS LA RESOLUTION — AUCUNE REVENDICATION.")
        elif d > 0:
            print("  ➤ LA POLITIQUE DEPASSE LE NATIF de %.1f points." % d)
        else:
            print("  ➤ LE NATIF DEPASSE LA POLITIQUE de %.1f points." % (-d))
            print("     C est l issue que le predicat avait ACCEPTEE D AVANCE :")
            print("     « la politique n apporte rien sur ce banc, et le 44,8 % ne se cite plus ».")
    else:
        print("  ⛔ DIVERGENT — aucun des deux n est cite.")
