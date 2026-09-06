#!/usr/bin/env python3
"""INJECTION DE LA COURBE A RANG BORNE (coups 1-10) + `degat_par_impact` re-derive.

POURQUOI CETTE COURBE. Mesure du 04/09, cible invulnerable, 14 692 balles, 124 duels longs :
`p_touche` = 0,354 [0,328 ; 0,381] aux coups 1-10 contre 0,407 [0,394 ; 0,419] aux 31-80,
IC DISJOINTS, et la hausse persiste DANS les memes duels. Le tireur s ameliore au fil de
l engagement. La courbe precedente etait mesuree sur 6 135 coups tardifs contre 1 250
precoces : elle decrit un engagement INSTALLE. **Un assaut est fait de PREMIERS coups.**

`degat_par_impact` PART AVEC ELLE : 0,233 valait 0,7/3,00 impacts, comptes avec le capteur
qui rendait 2 164 impacts pour 1 759 balles. Re-mesure sur l ACTE DE MORT, capteur repare :
mediane 4,0 impacts, n=83 -> 0,175. Les injecter separement rendrait le produit faux.
"""
import json, math, os, shutil, sys, collections

R = "/home/younes/arma3-marl"
LEV = R + "/leviathan"
DIST = [25, 50, 75, 100, 150, 200]
POST = ["UP", "MIDDLE", "DOWN"]
RANG_MAX = 10
DEGAT = 0.70 / 4.0


def wilson(i, n):
    if n == 0: return (float("nan"),) * 3
    p = i / n; z = 1.96; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def pava_si_recouvrement(vals, poids, ics):
    v = [[x] for x in vals]; w = [[p] for p in poids]; c = [[k] for k in ics]
    moy = lambda bv, bw: sum(a * b for a, b in zip(bv, bw)) / max(sum(bw), 1e-9)
    def rec(ba, bb):
        return not (max(x[1] for x in ba) < min(x[0] for x in bb)
                    or max(x[1] for x in bb) < min(x[0] for x in ba))
    i = 0
    while i < len(v) - 1:
        if moy(v[i], w[i]) < moy(v[i + 1], w[i + 1]) - 1e-12 and rec(c[i], c[i + 1]):
            v[i] += v[i + 1]; w[i] += w[i + 1]; c[i] += c[i + 1]
            del v[i + 1], w[i + 1], c[i + 1]; i = max(i - 1, 0)
        else:
            i += 1
    out = []
    for bv, bw in zip(v, w):
        out += [moy(bv, bw)] * len(bv)
    return out


T, I, srcs = collections.Counter(), collections.Counter(), []
for f in ("courbe_rang1_10.json", "courbe_rang1_10_v2.json", "courbe_rang1_10_v3.json"):
    p = "%s/%s" % (R, f)
    if not os.path.exists(p):
        print("  absent, ignore : %s" % f); continue
    srcs.append(f); d = json.load(open(p)); cond = [tuple(c) for c in d["cond"]]
    for _, j, r in d["tirs"]:
        if r <= RANG_MAX: T[cond[j]] += 1
    for _, j, r in d["imps"]:
        if r <= RANG_MAX: I[cond[j]] += 1

manq = [(d, p) for d in DIST for p in POST if T[(d, p)] < 300]
if manq:
    sys.exit("  CONDITIONS SOUS n=300 : %s — injection REFUSEE" % manq)

brut, ic, npc = {}, {}, {}
for d in DIST:
    brut[d], ic[d], npc[d] = [], [], []
    for po in POST:
        p, lo, hi = wilson(I[(d, po)], T[(d, po)])
        brut[d].append(100 * p); ic[d].append([100 * lo, 100 * hi]); npc[d].append(T[(d, po)])
rep = {d: [100 * x for x in pava_si_recouvrement([v / 100 for v in brut[d]], npc[d],
                                                 [[a / 100, b / 100] for a, b in ic[d]])] for d in DIST}

anc = json.load(open(LEV + "/courbe_toucher_hitpart.json"))
diff = []
for d in DIST:
    for k, po in enumerate(POST):
        a = anc["pct_au_but"][str(d)][k]
        lo, hi = ic[d][k]
        if hi < a or lo > a:
            diff.append("%d m %-6s %.1f%% contre %.1f%% en service" % (d, po, rep[d][k], a))
print("  sources : %s" % ", ".join(srcs))
print("  conditions ou la courbe a rang borne DIFFERE au-dela de l IC : %d / 18" % len(diff))
for x in diff[:8]:
    print("     %s" % x)
if not diff:
    sys.exit("  le rang ne portait rien : on GARDE la courbe en service. Rien n est injecte.")

touchees = [d for d in DIST if any(abs(a - b) > 1e-9 for a, b in zip(brut[d], rep[d]))]
sortie = {
    "skill": 0.5, "duree": 20, "reps": "3 passes, blocs courts", "rang_max": RANG_MAX,
    "distances": DIST, "postures": POST,
    "pct_au_but": {str(d): [round(x, 4) for x in rep[d]] for d in DIST},
    "balles": {str(d): npc[d] for d in DIST},
    "alertes": [],
    "brut_pct_au_but": {str(d): [round(x, 4) for x in brut[d]] for d in DIST},
    "ic95_pct": {str(d): [[round(a, 2), round(b, 2)] for a, b in ic[d]] for d in DIST},
    "instrument": ("HitPart sur cible invulnerable, UN impact par PROJECTILE, source appariee, "
                   "COUPS DE RANG 1-10 SEULEMENT"),
    "pourquoi_rang_borne": ("p_touche croit avec le rang : 0,354 [0,328;0,381] aux coups 1-10 "
                            "contre 0,407 [0,394;0,419] aux 31-80, IC disjoints, hausse "
                            "persistante DANS les memes duels."),
    "reparation": {"quoi": "PAVA en posture UNIQUEMENT la ou les IC se recouvrent",
                   "distances_touchees": touchees},
    "degat_par_impact": round(DEGAT, 4),
    "degat_source": "mediane 4,0 impacts jusqu a la neutralisation, n=83, capteur repare",
    "sources": srcs,
}
chem = LEV + "/courbe_toucher_rang1_10.json"
json.dump(sortie, open(chem, "w"), indent=1, ensure_ascii=False)
print("\n  ecrit : %s" % chem)
print("\n  dist   debout        accroupi      couche      (repare ; brut)")
for d in DIST:
    print("  %4d  " % d + "  ".join("%5.1f (%5.1f) n=%4d" % (rep[d][k], brut[d][k], npc[d][k])
                                    for k in range(3)))
print("\n  posture reparee sur : %s" % (touchees or "aucune distance"))

mf = R + "/monde_fidele.py"
s = open(mf, encoding="utf-8").read()
shutil.copy2(mf, mf + ".avantrang")
n = 0
if 'COURBE = LEV + "/courbe_toucher_hitpart.json"' in s:
    s = s.replace('COURBE = LEV + "/courbe_toucher_hitpart.json"',
                  'COURBE = LEV + "/courbe_toucher_rang1_10.json"'); n += 1
if "DEGAT_PAR_IMPACT = 0.233" in s:
    s = s.replace("DEGAT_PAR_IMPACT = 0.233", "DEGAT_PAR_IMPACT = %.4f" % DEGAT); n += 1
open(mf, "w", encoding="utf-8").write(s)
print("\n  monde_fidele.py : %d ancre(s) changee(s) (sauvegarde .avantrang)" % n)
print("  degat_par_impact : 0,233 -> %.4f" % DEGAT)
