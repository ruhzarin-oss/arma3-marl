#!/usr/bin/env python3
"""INJECTION DE LA COURBE MESUREE A `HitPart` DANS LE GYMNASE.

Source : `courbe_toucher_hitpart_B1/B2.json` (15 conditions) + `courbe_toucher_hitpart_200.json`
(les 3 conditions a 200 m, session dediee). Instrument : `HitPart` sur cible invulnerable,
UN impact par PROJECTILE, source appariee, tireur et cible invulnerables. Reproductible :
0,402 [0,371 ; 0,435] et 0,383 [0,335 ; 0,434] a 100 m debout.

DEUX REPARATIONS, ET UNE SEULE EST APPLIQUEE
1. POSTURE — monotonie imposee par PAVA pondere par les balles. « Une silhouette plus petite
   ne peut pas etre plus facile a toucher. » C est EXACTEMENT la reparation deja deposee et
   acceptee par le projet le 26/07 ; elle n est pas une invention d aujourd hui. Le BRUT est
   conserve a cote du repare.
2. DISTANCE — NON REPAREE. La mesure donne 0,562 a 25 m contre 0,631 a 50 m : le taux MONTE
   entre 25 et 50 m. Lisser reviendrait a effacer un fait pour faire joli. Et la config lue
   dans Arma 3 donne une explication mecanique : a 25 m l IA est dans le domaine du mode
   `FullAuto`, dont le `maxRangeProbab` tombe a 0,10 des 30 m. Le creux au tres proche est
   donc plausible. Il est INSCRIT, pas gomme.

⚠️ `degat_par_impact = 0,233` n a PAS ete re-derive : cette courbe change la FORME du risque,
pas son echelle absolue.
"""
import json, math, os, shutil, sys

R = "/home/younes/arma3-marl"
LEV = R + "/leviathan"
DIST = [25, 50, 75, 100, 150, 200]
POST = ["UP", "MIDDLE", "DOWN"]


def wilson(i, n):
    if n == 0: return (float("nan"),) * 3
    p = i / n; z = 1.96; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def pava_si_recouvrement(vals, poids, ics):
    """Monotonie non croissante imposee UNIQUEMENT la ou les IC se RECOUVRENT.

    ⭐ REGLE UNIQUE, imposee par Fable le 04/09 : PAVA est une HYPOTHESE (« une silhouette
    plus petite ne peut pas etre plus facile a toucher »), et **une hypothese ne survit pas a
    une mesure**. La premiere version lissait partout : a 25 m elle ecrasait les trois postures
    a la meme valeur alors que le couche y mesure 0,670 contre 0,562 debout, IC DISJOINTS.
    C etait deux poids deux mesures — on gardait brutes les non-monotonies de DISTANCE parce
    qu elles sont expliquees, et on ecrasait celle de POSTURE parce qu elle ne l est pas.
    Desormais : on lisse la ou le desaccord peut n etre que du bruit (IC qui se recouvrent),
    on GARDE LE BRUT la ou la mesure tranche. « Le gymnase replique Arma, pas la physique. »
    """
    v = [[x] for x in vals]; w = [[p] for p in poids]; c = [[k] for k in ics]
    moy = lambda bv, bw: sum(a * b for a, b in zip(bv, bw)) / max(sum(bw), 1e-9)
    def recouvrent(ba, bb):
        lo_a = min(x[0] for x in ba); hi_a = max(x[1] for x in ba)
        lo_b = min(x[0] for x in bb); hi_b = max(x[1] for x in bb)
        return not (hi_a < lo_b or hi_b < lo_a)
    i = 0
    while i < len(v) - 1:
        viole = moy(v[i], w[i]) < moy(v[i + 1], w[i + 1]) - 1e-12
        if viole and recouvrent(c[i], c[i + 1]):
            v[i] += v[i + 1]; w[i] += w[i + 1]; c[i] += c[i + 1]
            del v[i + 1], w[i + 1], c[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1                       # viole mais IC disjoints -> LA MESURE RESTE
    out = []
    for bv, bw in zip(v, w):
        out += [moy(bv, bw)] * len(bv)
    return out


# ---- collecte -------------------------------------------------------------
T, I = {}, {}
srcs = []
for f in ("courbe_toucher_hitpart_B1.json", "courbe_toucher_hitpart_B2.json",
          "courbe_toucher_hitpart_200.json"):
    p = "%s/%s" % (R, f)
    if not os.path.exists(p):
        print("  ⚠ absent, ignore : %s" % f); continue
    srcs.append(f)
    d = json.load(open(p))
    cond = [tuple(c) for c in d["cond"]]
    for k, v in d["tirs"].items():
        c = cond[int(k)]; T[c] = T.get(c, 0) + v
    for k, v in d["imps"].items():
        c = cond[int(k)]; I[c] = I.get(c, 0) + v

manquantes = [(d, p) for d in DIST for p in POST if T.get((d, p), 0) < 300]
print("  sources : %s" % ", ".join(srcs))
if manquantes:
    print("  ⛔ CONDITIONS SOUS n=300, LA COURBE N EST PAS COMPLETE :")
    for d, p in manquantes:
        print("     %4d m %-8s n=%d" % (d, p, T.get((d, p), 0)))
    sys.exit("  injection REFUSEE : on n injecte pas une courbe trouee sur le parametre "
             "qui a refuse de transferer trois fois.")

# ---- table brute ----------------------------------------------------------
brut, ic, n_par = {}, {}, {}
for d in DIST:
    brut[d] = []; ic[d] = []; n_par[d] = []
    for po in POST:
        n = T[(d, po)]; i = I[(d, po)]
        p, lo, hi = wilson(i, n)
        brut[d].append(100 * p); ic[d].append([100 * lo, 100 * hi]); n_par[d].append(n)

# ---- reparation POSTURE seulement ----------------------------------------
repare = {d: [100 * x for x in pava_si_recouvrement(
              [v / 100 for v in brut[d]], n_par[d], [[a / 100, b / 100] for a, b in ic[d]])]
          for d in DIST}
touchees = [d for d in DIST if any(abs(a - b) > 1e-9 for a, b in zip(brut[d], repare[d]))]

# ---- anomalie de DISTANCE, inscrite et non reparee ------------------------
anom_post = []
for d in DIST:
    for k in range(2):
        if repare[d][k] < repare[d][k + 1] - 1e-9:
            anom_post.append("%d m : %s %.1f%% < %s %.1f%% (IC disjoints, mesure gardee)"
                             % (d, POST[k], repare[d][k], POST[k + 1], repare[d][k + 1]))
anom = []
for pi, po in enumerate(POST):
    for a, b in zip(DIST, DIST[1:]):
        if repare[b][pi] > repare[a][pi] + 1e-9:
            anom.append("%s : %d m %.1f%% < %d m %.1f%%" % (po, a, repare[a][pi], b, repare[b][pi]))

sortie = {
    "skill": 0.5, "duree": 55, "reps": "B1+B2 (12+12 blocs) + session dediee 200 m",
    "zone": "positions tirees, terrain > 5 m d altitude",
    "distances": DIST, "postures": POST,
    "pct_au_but": {str(d): [round(x, 4) for x in repare[d]] for d in DIST},
    "balles": {str(d): n_par[d] for d in DIST},
    "alertes": [],
    "brut_pct_au_but": {str(d): [round(x, 4) for x in brut[d]] for d in DIST},
    "ic95_pct": {str(d): [[round(a, 2), round(b, 2)] for a, b in ic[d]] for d in DIST},
    "instrument": "HitPart sur cible invulnerable, UN impact par PROJECTILE, source appariee",
    "reproductibilite_100m_UP": "0,402 [0,371 ; 0,435] n=902 et 0,383 [0,335 ; 0,434] n=368",
    "reparation": {
        "quoi": "monotonie imposee EN POSTURE par PAVA pondere par les balles",
        "pourquoi": "une silhouette plus petite ne peut pas etre plus facile a toucher",
        "precedent": "meme reparation que la courbe du 26/07, deja deposee et acceptee",
        "regle": ("lisser SEULEMENT la ou les IC se recouvrent ; garder le brut la ou la "
                  "mesure tranche. Une hypothese ne survit pas a une mesure."),
        "distances_touchees": touchees,
        "NON_repare_posture": anom_post,
        "NON_repare_distance": anom,
        "pourquoi_non_repare": ("le taux MONTE entre 25 et 50 m ; lisser effacerait un fait. "
                                "Explication mecanique lue dans la config d Arma 3 : a 25 m "
                                "l IA est dans le domaine du mode FullAuto, dont le "
                                "maxRangeProbab tombe a 0,10 des 30 m."),
    },
    "reserve": ("degat_par_impact = 0,233 n a PAS ete re-derive : cette courbe change la FORME "
                "du risque, pas son echelle absolue."),
    "sources": srcs,
}
chem = LEV + "/courbe_toucher_hitpart.json"
json.dump(sortie, open(chem, "w"), indent=1, ensure_ascii=False)
print("\n  ecrit : %s" % chem)
print("\n  dist   debout        accroupi      couche        (repare ; brut entre parentheses)")
for d in DIST:
    print("  %4d  " % d + "  ".join("%5.1f (%5.1f) n=%4d" % (repare[d][k], brut[d][k], n_par[d][k])
                                    for k in range(3)))
print("\n  posture reparee sur : %s" % (touchees or "aucune distance"))
print("  posture NON reparee (IC disjoints, la mesure reste) : %s" % (anom_post or "aucune"))
print("  anomalies de DISTANCE inscrites, NON reparees : %s" % (anom or "aucune"))

# ---- branchement ----------------------------------------------------------
mf = R + "/monde_fidele.py"
s = open(mf, encoding="utf-8").read()
OLD = 'COURBE = LEV + "/courbe_toucher_monotone.json"   # la mesure du 26/07, monotonie reparee, alerte RESOLUE et non effacee'
NEW = ('COURBE = LEV + "/courbe_toucher_hitpart.json"   # ⭐ 04/09 : remesuree a `HitPart` (un impact\n'
       '# par PROJECTILE, source appariee), instrument REPRODUCTIBLE d une passe a l autre. La courbe\n'
       '# du 26/07 etait fausse de FORME — trop raide : x0,75 a 25 m et x1,91 a 150 m contre celle-ci.\n'
       '# Le gymnase punissait donc trop le rapprochement et payait trop la distance, sur LE parametre\n'
       '# qui a refuse de transferer trois fois. Ancienne : courbe_toucher_monotone.json.')
if OLD not in s:
    print("\n  ⚠ ancre de branchement introuvable dans monde_fidele.py — courbe ECRITE mais NON BRANCHEE")
else:
    shutil.copy2(mf, mf + ".avantcourbe_hitpart")
    open(mf, "w", encoding="utf-8").write(s.replace(OLD, NEW))
    print("\n  branchee dans monde_fidele.py (sauvegarde .avantcourbe_hitpart)")
