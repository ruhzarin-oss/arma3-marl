"""
Gymnase de decisions CHACAL v0 - construction, portes pre-enregistrees, apprentissage.

Criteres : CRITERES_GYMNASE_DECISIONS_V0.md ( commit 0fe722e, ecrit avant ce calcul ).

Le gymnase ne simule rien. Il rejoue les transitions qu Arma a produites :
  phase 5 : (monde, porte, delai)          -> (charges, vivants) d un episode Arma reel
  phase 6 : (monde, classe de vivants)     -> succes, probabilite mesuree dans Arma
Un choix jamais joue dans Arma est interdit.
"""
import collections, glob, json, math, sys
import numpy as np, pyarrow.parquet as pq

DONNEES = "/mnt/data/hmt/gymnase_decisions/donnees/phases.parquet"
SORTIE = "/mnt/data/hmt/gymnase_decisions/resultats_v0.json"
MONDES = [7, 8, 11, 12]
CONSTR_P5 = {"REFERENCE-PROPRE-13-09", "REFERENCE-JAMBES-13-09", "DELAI-PORTEUR-14-09",
             "PORTE-A-CONTRE-PORTE-B-14-09", "PORTE-B-CONTROLE-14-09", "PORTE-HUIT-MONDES-15-09"}
CONSTR_P6 = {"REFERENCE-PROPRE-13-09", "REFERENCE-JAMBES-13-09"}
TEST = "CONFIRMATION-MISSION-15-09"
POIDS_RETRECI = 4
N_BOOT = 2000
REFERENCE_NAIVE = 0.528
OPTIONS = [(45, "A"), (45, "B"), (180, "A")]      # (180, B) : jamais joue dans Arma -> interdit

versions = {}
for run in glob.glob("/mnt/data/hmt/runs/*/"):
    try: versions[run.rstrip("/").split("/")[-1]] = json.load(open(run + "job.json")).get("version") or ""
    except Exception: pass

def dans_la_base(r):
    return (r["verdict"] == "ACCEPTE" and r["erreurs_sqf"] == 0 and r["lev_palier"] == 4 and r["lev_socle"] == 1
            and r["lev_effectif"] == 10 and r["lev_depart"] == 5 and r["graine"] in MONDES
            and r["lev_oracle"] in (0, None) and r["lev_ablation"] in (0, None) and r["lev_banc_appui"] in (0, None)
            and r["lev_placeur"] in (0, None) and r["lev_immortel"] in (0, None) and r["lev_jour"] in (0, None)
            and r["lev_tactique"] == 0 and r["lev_appui_feu"] == 0 and r["lev_feu_avant"] == 0
            and r["lev_mg_assaut"] == 0 and r["lev_appui_fixe"] == 0
            and r["lev_partage"] is None and r["lev_qrf_n"] is None and r["lev_situation"] is None and r["lev_acc"] is None)

def classe(v): return 0 if v <= 6 else (1 if v <= 8 else 2)

def wilson(s, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = s / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

T = [r for r in pq.read_table(DONNEES).to_pylist() if dans_la_base(r)]
for r in T:
    r["porte"] = "B" if "-B-" in versions.get(r["episode_id"].split("/")[0], "") else "A"
    r["monde"] = int(r["graine"]); r["delai"] = int(r["lev_delai_porteur"])

# --- controle : une graine = un site, et des sites distincts ----------------------------------------
sites = collections.defaultdict(set)
for r in T: sites[r["monde"]].add(r.get("site"))
assert all(len(s) == 1 for s in sites.values()), f"une graine porte plusieurs sites : {dict(sites)}"
assert len({next(iter(s)) for s in sites.values()}) == len(MONDES), "deux mondes partagent un site"

# --- construction phase 5 ------------------------------------------------------------------------------
p5 = collections.defaultdict(list); sans_fin = collections.Counter()
porte_par_campagne = collections.Counter()
for r in T:
    if r["campagne"] not in CONSTR_P5 or r.get("p5_debut_t") is None: continue
    porte_par_campagne[(r["campagne"], r["porte"], r["delai"])] += 1
    if r.get("p5_fin_t") is None or r.get("p5_fin_charges") is None or r.get("p5_fin_vivants") is None:
        sans_fin[r["campagne"]] += 1; continue
    p5[(r["monde"], r["porte"], r["delai"])].append((int(r["p5_fin_charges"]), int(r["p5_fin_vivants"])))
print("== construction phase 5 : episodes par campagne, porte, delai")
for k, v in sorted(porte_par_campagne.items()): print(f"   {v:4d}  {k}")
print("   assauts sans ligne de fin ( exclus ) :", dict(sans_fin))
print("== cellules phase 5 (monde, porte, delai) : n")
for k in sorted(p5): print(f"   {k}  n={len(p5[k])}  3 charges={sum(c == 3 for c, _ in p5[k])}")
for m in MONDES:
    for d, p in OPTIONS:
        assert len(p5[(m, p, d)]) >= 5, f"cellule phase 5 trop maigre : {(m, p, d)} n={len(p5[(m, p, d)])}"

# --- construction phase 6 ------------------------------------------------------------------------------
p6 = collections.defaultdict(list)
for r in T:
    if r["campagne"] not in CONSTR_P6 or r.get("p6_debut_t") is None: continue
    succes = r["fini_issue"] == "SUCCES"
    if succes and r.get("p5_fin_charges") != 3:
        sys.exit(f"ARRET : succes a moins de 3 charges dans la construction : {r['episode_id']}")
    if r.get("p5_fin_charges") == 3:
        p6[(r["monde"], classe(int(r["p5_fin_vivants"])))].append(1 if succes else 0)
print("== cellules phase 6 (monde, classe de vivants) : succes / n")
for k in sorted(p6): print(f"   {k}  {sum(p6[k])}/{len(p6[k])}")

def taux_p6(cellules):
    pool = {c: (sum(sum(v) for (m, cc), v in cellules.items() if cc == c), sum(len(v) for (m, cc), v in cellules.items() if cc == c)) for c in range(3)}
    taux = {}
    for m in MONDES:
        for c in range(3):
            s, n = pool[c]
            pp = s / n if n else 0.0
            v = cellules.get((m, c), [])
            taux[(m, c)] = (sum(v) + POIDS_RETRECI * pp) / (len(v) + POIDS_RETRECI)
    return taux, pool

def predire(c5, t6):
    """valeur exacte de chaque option : moyenne des mondes a poids egaux"""
    val, trois = {}, {}
    for d, p in OPTIONS:
        par_monde = []; tr = []
        for m in MONDES:
            ep = c5[(m, p, d)]
            par_monde.append(sum(t6[(m, classe(v))] for c, v in ep if c == 3) / len(ep))
            tr.append(sum(1 for c, _ in ep if c == 3) / len(ep))
        val[(d, p)] = (float(np.mean(par_monde)), par_monde); trois[(d, p)] = float(np.mean(tr))
    return val, trois

t6, pool = taux_p6(p6)
print("   taux poole par classe :", {c: f"{s}/{n}" for c, (s, n) in pool.items()})
val, trois = predire(p5, t6)

# --- bootstrap : incertitude des donnees Arma dans chaque cellule -----------------------------------
rng = np.random.default_rng(20260916)
boot = collections.defaultdict(list); boot_mondes = collections.defaultdict(list)
for _ in range(N_BOOT):
    c5 = {k: [v[i] for i in rng.integers(0, len(v), len(v))] for k, v in p5.items()}
    c6 = {k: [v[i] for i in rng.integers(0, len(v), len(v))] for k, v in p6.items()}
    tb, _ = taux_p6(c6)
    vb, trb = predire(c5, tb)
    for o in OPTIONS:
        boot[o].append(vb[o][0]); boot[("trois", o)].append(trb[o])
        for i, m in enumerate(MONDES): boot_mondes[(o, m)].append(vb[o][1][i])
def ic(x): return (float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5)))
def ic_diff(a, b): return ic(np.array(boot[a]) - np.array(boot[b]))

# --- le test : CONFIRMATION-MISSION-15-09 --------------------------------------------------------------
test = [r for r in T if r["campagne"] == TEST]
arma = {}
for d in (45, 180):
    bras = [r for r in test if r["delai"] == d]
    s = sum(r["fini_issue"] == "SUCCES" for r in bras); n = len(bras)
    s3 = sum(r.get("p5_fin_charges") == 3 for r in bras)
    arma[d] = dict(n=n, succes=s, taux=s / n, ic=wilson(s, n), trois=s3 / n, ic_trois=wilson(s3, n),
                   portes=dict(collections.Counter(r["porte"] for r in bras)),
                   mondes=dict(collections.Counter(r["monde"] for r in bras)))
print("\n== TEST ( jamais lu par la construction ) :", TEST)
for d in (45, 180): print(f"   bras {d:3d} s : {arma[d]}")
assert all(arma[d]["n"] == 48 and arma[d]["portes"] == {"A": 48} and all(v == 12 for v in arma[d]["mondes"].values()) for d in (45, 180)), "le test n est pas celui ecrit dans les criteres"

portes = {}
def dit(nom, ok, texte): portes[nom] = dict(passe=bool(ok), detail=texte); print(f"   {nom}  {'PASSE ' if ok else 'ECHOUE'}  {texte}")
print("\n== PORTES")
for g, d in (("G1", 45), ("G2", 180)):
    pr = val[(d, "A")][0]; lo, hi = arma[d]["ic"]
    dit(g, lo <= pr <= hi, f"bras {d} s : gymnase {pr:.3f} (IC gymnase {ic(boot[(d, 'A')])[0]:.3f}-{ic(boot[(d, 'A')])[1]:.3f}) contre Arma {arma[d]['taux']:.3f} IC Wilson [{lo:.3f} ; {hi:.3f}]")
entres = [r for r in test if r.get("p6_debut_t") is not None and r.get("p5_fin_charges") == 3]
p = np.array([t6[(r["monde"], classe(int(r["p5_fin_vivants"])))] for r in entres])
O = sum(r["fini_issue"] == "SUCCES" for r in entres); E = float(p.sum()); sd = float(math.sqrt((p * (1 - p)).sum()))
z = (O - E) / sd
dit("G3", abs(z) <= 2, f"episodes test entres en phase 6 avec 3 charges : n={len(entres)}  succes observes {O}  attendus {E:.1f}  z={z:+.2f}")
for d in (45, 180):
    lo, hi = arma[d]["ic_trois"]
    dit(f"G4_{d}", lo <= trois[(d, 'A')] <= hi, f"3 charges, bras {d} s : gymnase {trois[(d, 'A')]:.3f} contre Arma {arma[d]['trois']:.3f} IC [{lo:.3f} ; {hi:.3f}]  (diagnostic)")
eg = val[(180, "A")][0] - val[(45, "A")][0]; ea = arma[180]["taux"] - arma[45]["taux"]
dit("G5", np.sign(eg) == np.sign(ea), f"ecart 180-45 : gymnase {eg:+.3f} IC {ic_diff((180, 'A'), (45, 'A'))[0]:+.3f} ; {ic_diff((180, 'A'), (45, 'A'))[1]:+.3f}  contre Arma {ea:+.3f}  (informative)")
lo, hi = ic_diff((45, "B"), (45, "A"))
dit("G6", lo <= 0 <= hi, f"porte B - A a 45 s : gymnase {val[(45, 'B')][0] - val[(45, 'A')][0]:+.3f} IC [{lo:+.3f} ; {hi:+.3f}]  (coherence)")
erreur_g = abs(val[(45, "A")][0] - arma[45]["taux"]) + abs(val[(180, "A")][0] - arma[180]["taux"])
erreur_n = abs(REFERENCE_NAIVE - arma[45]["taux"]) + abs(REFERENCE_NAIVE - arma[180]["taux"])
dit("N", erreur_g <= erreur_n, f"erreur absolue cumulee : gymnase {erreur_g:.3f} contre naif constant 52,8 % {erreur_n:.3f}  (informative)")
valide = portes["G1"]["passe"] and portes["G2"]["passe"] and portes["G3"]["passe"]
print(f"\n   GYMNASE V0 {'VALIDE' if valide else 'NON VALIDE'} ( G1 et G2 et G3 )")

res = dict(criteres_commit="0fe722e", test=TEST, arma={str(k): v for k, v in arma.items()},
           valeurs={f"{d}{p}": dict(valeur=val[(d, p)][0], ic=ic(boot[(d, p)]), par_monde=dict(zip(map(str, MONDES), val[(d, p)][1])),
                                     trois=trois[(d, p)]) for d, p in OPTIONS},
           portes=portes, valide=valide)

# --- apprentissage : seulement si valide ---------------------------------------------------------------
if valide:
    print("\n== APPRENTISSAGE : Q tabulaire, moyenne d echantillons, epsilon 0,1, 1 000 000 episodes, 5 graines")
    print("   ( mises a jour par lots de 1 000 episodes : politique figee dans le lot )")
    exact = np.array([val[o][0] for o in OPTIONS]); meilleur = int(exact.argmax())
    cell5 = {k: np.array(v) for k, v in p5.items()}
    tab6 = np.zeros((max(MONDES) + 1, 3))
    for (m, c), x in t6.items(): tab6[m, c] = x
    graines_res = []
    for g in range(5):
        r_ = np.random.default_rng(1000 + g)
        somme = np.zeros(3); nb = np.zeros(3)
        for _ in range(1000):
            n = 1000
            q = np.where(nb > 0, somme / np.maximum(nb, 1), 1.0)
            glouton = int(q.argmax())
            a = np.where(r_.random(n) < 0.1, r_.integers(0, 3, n), glouton)
            m = np.array(MONDES)[r_.integers(0, 4, n)]
            rec = np.zeros(n)
            for ai in range(3):
                for mi in MONDES:
                    idx = np.where((a == ai) & (m == mi))[0]
                    if not len(idx): continue
                    d, p = OPTIONS[ai]; ep = cell5[(mi, p, d)]
                    tir = ep[r_.integers(0, len(ep), len(idx))]
                    proba = np.where(tir[:, 0] == 3, tab6[mi, np.where(tir[:, 1] <= 6, 0, np.where(tir[:, 1] <= 8, 1, 2))], 0.0)
                    rec[idx] = (r_.random(len(idx)) < proba).astype(float)
            np.add.at(somme, a, rec); np.add.at(nb, a, 1)
        q = somme / nb
        graines_res.append(dict(graine=1000 + g, q=q.tolist(), choix=int(q.argmax()), n=nb.tolist()))
        print(f"   graine {1000 + g} : Q = {', '.join(f'{OPTIONS[i][0]}{OPTIONS[i][1]} {q[i]:.4f}' for i in range(3))}  -> choisit {OPTIONS[int(q.argmax())]}")
    print(f"   valeurs exactes : {', '.join(f'{OPTIONS[i][0]}{OPTIONS[i][1]} {exact[i]:.4f}' for i in range(3))}  -> {OPTIONS[meilleur]}")
    ecart_max = max(float(np.abs(np.array(x["q"]) - exact).max()) for x in graines_res)
    dit("L1", all(x["choix"] == meilleur for x in graines_res) and ecart_max < 0.01, f"5 graines sur le choix exact {OPTIONS[meilleur]} ; ecart max Q - exact {ecart_max:.4f}")
    ordre = np.argsort(-exact); second = int(ordre[1])
    lo, hi = ic_diff(OPTIONS[meilleur], OPTIONS[second])
    dit("L2", lo > 0, f"avance de {OPTIONS[meilleur]} sur {OPTIONS[second]} : {exact[meilleur] - exact[second]:+.3f} IC [{lo:+.3f} ; {hi:+.3f}]")
    lo, hi = ic_diff((45, "B"), (45, "A"))
    dit("L3", lo <= 0 <= hi, f"aucune preference etablie entre les portes : B - A IC [{lo:+.3f} ; {hi:+.3f}]")
    print("\n== diagnostic par monde ( la meilleure option change-t-elle d un monde a l autre ? )")
    for m in MONDES:
        ligne = []
        for o in OPTIONS:
            x = boot_mondes[(o, m)]; ligne.append(f"{o[0]}{o[1]} {val[o][1][MONDES.index(m)]:.2f} [{np.percentile(x, 2.5):.2f}-{np.percentile(x, 97.5):.2f}]")
        d = np.array(boot_mondes[((180, "A"), m)]) - np.array(boot_mondes[((45, "A"), m)])
        print(f"   monde {m:2d} : " + "   ".join(ligne) + f"   | 180-45 IC [{np.percentile(d, 2.5):+.2f} ; {np.percentile(d, 97.5):+.2f}]")
    res["apprentissage"] = dict(graines=graines_res, exact=exact.tolist(), options=[f"{d}{p}" for d, p in OPTIONS])

res["portes"] = portes
json.dump(res, open(SORTIE, "w"), indent=1, default=str)
print("\nresultats ->", SORTIE)
