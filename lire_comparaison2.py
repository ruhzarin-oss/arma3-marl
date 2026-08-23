#!/usr/bin/env python3
"""LA COMPARAISON SUR LE BANC REPARE — juge ECRIT AVANT QUE LA PASSE 2 EXISTE.

⚠️ Ecrit le 23/08 a 13 h 15, alors que la politique en est a 29 episodes sur 67 de sa
passe 2. Un juge ecrit apres coup se regle toujours un peu sur ce qu il doit dire.

Il n invente rien : il APPELLE `lire_natif.lire`, le lecteur depose, et applique le
predicat `DEPOT_NATIF.md` du 16/08 sans y toucher.

  · deux passes par bras, concordance exigee a moins de 10 points, sinon le bras ne se cite pas
  · conditions eliminatoires : prevol vert, le monde bouge (> 1 m/pas), l attaquant tire
  · les episodes qui n ont pas eu lieu se NOMMENT, ils ne comptent ni en prise ni en echec
  · resolution exigee : l ecart doit depasser 12 points OU son IC95 exclure zero
"""
import glob, math, collections, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

def bras(dos, nom):
    P = {}
    for pas in ("p1", "p2"):
        E = [e for e in (LN.lire(f) for f in sorted(glob.glob("%s/%s_e*.txt" % (dos, pas)))) if e]
        c = collections.Counter(e["etat"] for e in E)
        ok = [e for e in E if e["etat"] == "ok"]
        if not ok: return None
        mp = sorted(e["mpas"] for e in ok); med = mp[len(mp)//2]
        cps = sorted(e["coups"] for e in ok if e["coups"] >= 0)
        cmed = cps[len(cps)//2] if cps else -1
        print("  %-10s %s : n=%-3d  prises %5.1f %%   bouge %.2f m/pas %s   coups %d"
              % (nom, pas.upper(), len(ok), 100.0*sum(1 for e in ok if e["prise"])/len(ok),
                 med, "OK" if med > 1.0 else "⛔", cmed))
        for k, v in sorted(c.items()):
            if k != "ok": print("               ecarte : %-16s %d" % (k, v))
        if med <= 1.0:
            print("               ⛔ CONTROLE DU MONDE ECHOUE — ce bras ne se cite pas")
            return None
        P[pas] = ok
    ta = 100.0*sum(1 for e in P["p1"] if e["prise"])/len(P["p1"])
    tb = 100.0*sum(1 for e in P["p2"] if e["prise"])/len(P["p2"])
    if abs(ta - tb) >= 10:
        print("  %-10s ⛔ DISCORDANT (%.1f contre %.1f) — aucun des deux ne se cite" % (nom, ta, tb))
        return None
    tot = P["p1"] + P["p2"]; n = len(tot); k = sum(1 for e in tot if e["prise"])
    print("  %-10s ✓ concordant (ecart %.1f) -> %.1f %%  n=%d\n" % (nom, abs(ta-tb), 100.0*k/n, n))
    return k, n

print("\n═══ LES DEUX BRAS, BANC REPARE ═══\n")
A = bras("/mnt/data/natif2", "NATIF")
B = bras("/mnt/data/politique2", "POLITIQUE")
if not A or not B:
    print("⛔ LA COMPARAISON N EST PAS PERMISE — un bras au moins ne se cite pas."); sys.exit(0)

ka, na = A; kb, nb = B
pa, pb = ka/na, kb/nb
ica = 1.96*math.sqrt(pa*(1-pa)/na); icb = 1.96*math.sqrt(pb*(1-pb)/nb)
d = pa - pb; icd = 1.96*math.sqrt(pa*(1-pa)/na + pb*(1-pb)/nb)
print("═══ VERDICT ═══\n")
print("  NATIF     %5.1f %%  n=%-3d  IC95 [%.1f ; %.1f]" % (100*pa, na, 100*(pa-ica), 100*(pa+ica)))
print("  POLITIQUE %5.1f %%  n=%-3d  IC95 [%.1f ; %.1f]" % (100*pb, nb, 100*(pb-icb), 100*(pb+icb)))
print("\n  ECART (natif - politique) = %+.1f points   IC95 [%+.1f ; %+.1f]"
      % (100*d, 100*(d-icd), 100*(d+icd)))
exclut = (d - icd > 0) or (d + icd < 0)
print("  l IC95 de l ecart exclut zero : %s" % ("OUI" if exclut else "NON"))
print("  l ecart depasse la resolution de 12 points : %s" % ("OUI" if abs(100*d) > 12 else "NON"))
print()
if not exclut:
    print("  ➤ AUCUNE REVENDICATION. Les deux bras ne se departagent pas sur ce banc.")
elif d > 0:
    print("  ➤ L IA NATIVE reste devant, sur un banc qui ne lui donne plus rien.")
else:
    print("  ➤ LA POLITIQUE PASSE DEVANT L IA NATIVE — le signe depose le 22/08 s inverse")
    print("    une fois le banc repare. C etait le natif qui vivait du prevol.")
print("\n  ⚠️ Ce verdict ne dit RIEN du transfert : les deux bras sont mesures DANS Arma.")
print("     Il ne dit rien non plus d un niveau absolu — seulement lequel des deux prend")
print("     plus souvent un objectif tenu par quatre hommes.")
