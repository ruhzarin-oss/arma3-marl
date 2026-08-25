#!/usr/bin/env python3
"""LA NUIT DE L HESITATION — lue UNE FOIS, contre les quatre issues deposees (80ac6e9).

Critere principal : hesitant - fige, MEME NUIT, memes graines d action au meme rang.
Lecteur DEPOSE (lire_natif.lire), inchange. Concordance recalculee pour le n reel : 14 points
sur des moities de ~31 (le seuil de 10 valait pour des passes de 67).
"""
import glob, math, collections, re, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import lire_natif as LN

D = "/mnt/data/hesitation"
R = {}
for dec in ("echantillon", "argmax"):
    E = []
    for f in sorted(glob.glob("%s/%s_e*.txt" % (D, dec)),
                    key=lambda x: int(re.search(r"_e(\d+)", x).group(1))):
        e = LN.lire(f)
        if e: E.append((int(re.search(r"_e(\d+)", f).group(1)), e))
    c = collections.Counter(e["etat"] for _, e in E)
    ok = [(i, e) for i, e in E if e["etat"] == "ok"]
    mp = sorted(e["mpas"] for _, e in ok); med = mp[len(mp)//2] if mp else 0
    cps = sorted(e["coups"] for _, e in ok if e["coups"] >= 0)
    n = len(ok); k = sum(1 for _, e in ok if e["prise"])
    h1 = [e["prise"] for i, e in ok if i <= 33]; h2 = [e["prise"] for i, e in ok if i > 33]
    t1 = 100.0*sum(h1)/len(h1) if h1 else 0; t2 = 100.0*sum(h2)/len(h2) if h2 else 0
    R[dec] = dict(n=n, k=k, taux=100.0*k/n, med=med,
                  coups=cps[len(cps)//2] if cps else -1, t1=t1, t2=t2, ok=dict(ok))
    print("\n  ══ %s ══" % dec.upper())
    for kk, v in sorted(c.items()): print("     %-16s %d" % (kk, v))
    print("     condition 2 · le monde bouge : %.2f m/pas -> %s" % (med, "OK" if med > 1 else "⛔"))
    print("     condition 3 · coups attaquants, mediane : %d" % R[dec]["coups"])
    print("     moities : %.1f %% (n=%d) et %.1f %% (n=%d)   ecart %.1f  (seuil recalcule : 14)"
          % (t1, len(h1), t2, len(h2), abs(t1-t2)))
    print("     ➤ PRISES : %d / %d = %.1f %%" % (k, n, R[dec]["taux"]))

a, b = R["echantillon"], R["argmax"]
pa, pb = a["k"]/a["n"], b["k"]/b["n"]
ic = lambda p, n: 1.96*math.sqrt(p*(1-p)/n)*100
d = (pa - pb)*100; icd = 1.96*math.sqrt(pa*(1-pa)/a["n"] + pb*(1-pb)/b["n"])*100
print("\n═══ VERDICT ═══\n")
print("  HESITANT %5.1f %%  n=%-3d IC95 [%.1f ; %.1f]" % (a["taux"], a["n"], a["taux"]-ic(pa,a["n"]), a["taux"]+ic(pa,a["n"])))
print("  FIGE     %5.1f %%  n=%-3d IC95 [%.1f ; %.1f]" % (b["taux"], b["n"], b["taux"]-ic(pb,b["n"]), b["taux"]+ic(pb,b["n"])))
print("\n  hesitant - fige = %+.1f points   IC95 [%+.1f ; %+.1f]" % (d, d-icd, d+icd))
print("  repere du gymnase pour cet artefact : -19,6 points")
print("\n  ── LES QUATRE ISSUES, TELLES QUE DEPOSEES ──")
fige_ok = abs(b["taux"] - 33.6) <= 12
print("  figé dans 33,6 +- 12 : %s (%.1f)" % ("OUI" if fige_ok else "NON", b["taux"]))
if not fige_ok:
    print("\n  ➤ ISSUE 4 — le banc a bouge. Tous les chiffres d avant expirent, natif inclus.")
    print("    La nuit reste lisible en interne : hesitant contre fige est immunise.")
elif d <= -25:
    print("\n  ➤ ISSUE 3 — PENALITE D HESITATION PROPRE A ARMA.")
    print("    Declencheur pre-inscrit : la decision du 24/08 repasse en delibere POUR ARMA.")
elif d >= -10:
    print("\n  ➤ ISSUE 2 — l effet du gymnase NE TRANSFERE PAS ; la decision est gratuite ici.")
else:
    print("\n  ➤ ISSUE 1 — le gymnase PREDIT l effet du decodeur dans Arma (~-20).")
if abs(d) < 20:
    print("\n  ⚠️ Et la puissance, ecrite d avance : a ce n, un effet sous ~20 points est")
    print("     NON RESOLU A CE BUDGET. C est une issue acceptee, pas un echec.")
