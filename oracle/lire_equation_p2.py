"""Lecture UNIQUE de l equation P2 ( criteres : oracle/CRITERES_EQUATION_P2.md, fca5d5d ).
  python lire_equation_p2.py [--jeu A|B]"""
import csv, json, random, sys
import numpy as np
D = "/mnt/data/hmt/equation/p2"; JEU = sys.argv[sys.argv.index("--jeu") + 1] if "--jeu" in sys.argv else "A"
B, GRAINE = 10000, 20260921
P = list(csv.DictReader(open(f"{D}/predictions_{JEU}.csv"))); meta = json.load(open(f"{D}/meta_{JEU}.json"))
Y = np.array([float(r["Y"]) for r in P]); W = np.array([int(r["monde"]) for r in P]); M = sorted(set(W))
MOD = [k for k in P[0] if k not in ("episode", "monde", "Y", "attendre")]
pr = {k: np.clip(np.array([float(r[k]) for r in P]), 1e-4, 1 - 1e-4) for k in MOD}
brier = {k: (pr[k] - Y) ** 2 for k in MOD}
logl = {k: -(Y * np.log(pr[k]) + (1 - Y) * np.log(1 - pr[k])) for k in MOD}


def ic_ecart(a, b, score):
    r = random.Random(GRAINE); d = score[a] - score[b]; par = {w: d[W == w] for w in M}; t = []
    for _ in range(B):
        tir = [r.choice(M) for _ in M]; v = np.concatenate([par[w] for w in tir]); t.append(v.mean())
    t.sort(); return d.mean(), t[int(0.025 * B)], t[int(0.975 * B)]


print(f"== EQUATION DE L ARCHITECTE, PHASE 2 - jeu {JEU} : {meta['n']} episodes, {len(M)} mondes, "
      f"compromission {meta['taux']:.3f}, {len(meta['noms'])} variables")
print(f"   budget EvoGP en validation croisee : population {meta['budget']['pop']}, {meta['budget']['gen']} generations, "
      f"{meta['budget']['graines']} graines, parcimonies {meta['budget']['parcimonies']} ; duree {meta['duree_s'] / 3600:.1f} h\n")
print(f"   {'modele':<16} {'Brier':>8} {'log-perte':>10}   ecart de Brier a la constante, IC 95 % par monde")
bc = brier["constante"].mean()
retenus = []
for k in MOD:
    if k == "constante":
        print(f"   {k:<16} {brier[k].mean():>8.4f} {logl[k].mean():>10.4f}   —"); continue
    e, lo, hi = ic_ecart(k, "constante", brier)
    ok = hi < 0; retenus += [k] if ok and k != "reseau" else []
    print(f"   {k:<16} {brier[k].mean():>8.4f} {logl[k].mean():>10.4f}   {e:+.4f} [{lo:+.4f} ; {hi:+.4f}]  {'BAT LA CONSTANTE' if ok else ''}")
bn = brier["reseau"].mean()
print(f"\n   plafond ( reseau ) : {'bat la constante' if ic_ecart('reseau', 'constante', brier)[2] < 0 else 'NE bat PAS la constante'}")
if bn < bc:
    for k in MOD:
        if k in ("constante", "reseau"): continue
        print(f"   part du plafond captee par {k:<14} : {(bc - brier[k].mean()) / (bc - bn):+.2f}")
print(f"\n   VERDICT ( regle ecrite d avance ) : "
      + (f"equation(s) RETENUE(S) : {retenus}" if retenus else
         "AUCUNE equation ne bat la constante sur mondes neufs. "
         + ("Le reseau non plus : rien de previsible dans ces variables." if ic_ecart("reseau", "constante", brier)[2] >= 0 else
            "Le reseau, lui, bat la constante : il y a quelque chose, que les formules ne captent pas.")))
if JEU == "A":
    try:
        F = json.load(open(f"{D}/formule_finale_A.json"))
        R = list(csv.DictReader(open(f"{D}/formule_finale_A.csv")))
        pt = np.array([float(r["p_traverser"]) for r in R]); pa = np.array([float(r["p_attendre"]) for r in R])
        print(f"\n== FORMULE FINALE d EvoGP ( parcimonie {F['parcimonie_choisie']:g}, choisie par la validation croisee ; "
              f"{F['budget']['pop']} x {F['budget']['gen']} x {F['budget']['graines']} graines, {F['duree_s'] / 60:.0f} min )")
        print(f"   P(compromis) = {F['formule']}")
        print(f"   ce qu elle dit du choix : P moyenne sous traverser {pt.mean():.3f}, sous attendre {pa.mean():.3f} ; "
              f"elle conseille d attendre dans {np.mean(pa < pt - 1e-6):.1%} des episodes, de traverser dans {np.mean(pt < pa - 1e-6):.1%}, "
              f"indifferente dans {np.mean(abs(pa - pt) <= 1e-6):.1%}")
    except FileNotFoundError:
        print("\n   ( formule finale pas encore calculee )")
