"""Ajustement de l equation de l Architecte en phase 2 ( criteres : oracle/CRITERES_EQUATION_P2.md, fca5d5d ).
Calcule TOUT ( constante, logistique, reseau, EvoGP ; 16 plis par monde ) et ecrit les predictions hors pli dans
equation/p2/predictions.csv. N AFFICHE AUCUN SCORE : la lecture unique est faite par lire_equation_p2.py.
  python ajuster_p2.py [--jeu A|B] [--fumee]"""
import csv, json, os, sys, time, re
import numpy as np, torch
H = "/mnt/data/hmt"; D = f"{H}/equation/p2"
JEU = sys.argv[sys.argv.index("--jeu") + 1] if "--jeu" in sys.argv else "A"
FUMEE = "--fumee" in sys.argv
GRAINE = 20260921
POP_CV, GEN_CV, GRAINES_CV = (3000, 5, 1) if FUMEE else (300000, 300, 5)
PARCIMONIES = (0.0, 1e-4, 1e-3)

rows = list(csv.DictReader(open(f"{D}/table_p2.csv")))
f = lambda r, k, d=None: (float(r[k]) if r.get(k) not in (None, "", "None") else d)
rows = [r for r in rows if r["atteint_decision"] == "1" and f(r, "compromis_avant", 0) == 0 and f(r, "option") in (1.0, 2.0)]
A_BASE = ["alarme", "depuis_alarme", "vivants_avant", "defenseurs_connus", "vehicule_vu", "vehicule_connu", "menace_percue",
          "menaces_vues", "menaces_connues", "menaces_camp", "menaces_homme", "distance_menace", "menace_mobile", "vue_depuis"]
A_ETENDU = ["moteur_entendu", "distance_moteur", "vue_vehicule", "n_vues_menace", "menace_mobile_vue", "moteur_depuis_fenetre"]
INTERDITS = {"moteur_allume", "erreur_position", "verite_distance_menace", "verite_menaces"}
noms, cols = [], []
def ajoute(nom, v): noms.append(nom); cols.append(v)
attendre = np.array([1.0 if f(r, "option") == 2.0 else 0.0 for r in rows])
ajoute("attendre", attendre)
for k in A_BASE:
    ajoute(k, np.array([f(r, k, -1.0) if f(r, k) is not None else -1.0 for r in rows]))
etendu = np.array([1.0 if f(r, "moteur_entendu") is not None else 0.0 for r in rows])
ajoute("perception_etendue", etendu)
for k in A_ETENDU:
    ajoute(k, np.array([f(r, k) if f(r, k) is not None else 0.0 for r in rows]))
if JEU == "B":
    ajoute("oracle", np.array([f(r, "oracle", 0) for r in rows]))
    ajoute("oracle_rapide", np.array([1.0 if f(r, "oracle", 0) == 1 and f(r, "oracle_delta") == 30 else 0.0 for r in rows]))
    ajoute("jour", np.array([f(r, "jour", 0) for r in rows]))
    for ty in ("PATROUILLE_ROUTE", "POSTE"):
        ajoute("type_" + ty.lower(), np.array([1.0 if ty in (r.get("types") or "") else 0.0 for r in rows]))
    ajoute("portee_son", np.array([f(r, "portee_son", 0) for r in rows]))
assert not (set(noms) & INTERDITS)
X = np.column_stack(cols).astype(np.float64)
Y = np.array([int(r["compromis"]) for r in rows])
mondes = np.array([int(r["monde"]) for r in rows])
MONDES = sorted(set(mondes))
# on ne garde que les variables qui varient
v = X.std(axis=0) > 0; X = X[:, v]; noms = [n for n, k in zip(noms, v) if k]
# les interactions option x perception pour la logistique : la regle de l Architecte est QUELLE option selon ce qu il voit
iatt = noms.index("attendre")


def standardiser(Xtr, Xte):
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1
    return (Xtr - mu) / sd, (Xte - mu) / sd


def avec_interactions(Z):
    a = Z[:, [iatt]]; autres = np.delete(Z, iatt, axis=1)
    return np.column_stack([Z, a * autres])


def logistique(Xtr, Ytr, Xte):
    from sklearn.linear_model import LogisticRegressionCV
    Ztr, Zte = standardiser(Xtr, Xte)
    m = LogisticRegressionCV(Cs=20, cv=5, penalty="l2", scoring="neg_log_loss", max_iter=5000,
                             random_state=GRAINE).fit(avec_interactions(Ztr), Ytr)
    return m.predict_proba(avec_interactions(Zte))[:, 1]


def reseau(Xtr, Ytr, Xte, n=10):
    Ztr, Zte = standardiser(Xtr, Xte)
    dev = "cuda"
    xt = torch.tensor(Ztr, dtype=torch.float32, device=dev); yt = torch.tensor(Ytr, dtype=torch.float32, device=dev)
    xe = torch.tensor(Zte, dtype=torch.float32, device=dev)
    preds = []
    for s in range(n):
        g = torch.Generator().manual_seed(GRAINE + s); torch.manual_seed(GRAINE + s)
        perm = torch.randperm(len(xt), generator=g).to(dev); nv = max(1, len(xt) // 5)
        va, tr = perm[:nv], perm[nv:]
        net = torch.nn.Sequential(torch.nn.Linear(xt.shape[1], 64), torch.nn.ReLU(), torch.nn.Dropout(0.2),
                                  torch.nn.Linear(64, 32), torch.nn.ReLU(), torch.nn.Dropout(0.2), torch.nn.Linear(32, 1)).to(dev)
        opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
        perte = torch.nn.BCEWithLogitsLoss(); meilleur, etat, patience = 1e9, None, 0
        for ep in range(400):
            net.train(); opt.zero_grad(); l = perte(net(xt[tr]).squeeze(1), yt[tr]); l.backward(); opt.step()
            net.eval()
            with torch.no_grad(): lv = perte(net(xt[va]).squeeze(1), yt[va]).item()
            if lv < meilleur - 1e-4: meilleur, etat, patience = lv, {k: w.clone() for k, w in net.state_dict().items()}, 0
            else:
                patience += 1
                if patience > 30: break
        net.load_state_dict(etat); net.eval()
        with torch.no_grad(): preds.append(torch.sigmoid(net(xe).squeeze(1)).cpu().numpy())
    return np.mean(preds, axis=0)


def evogp_fit(Xtr, Ytr, pop, gen, graine, parcimonie):
    from evogp.tree import Forest, GenerateDescriptor
    from evogp.algorithm import GeneticProgramming, DefaultSelection, DefaultMutation, DefaultCrossover
    from evogp.problem import SymbolicRegression
    from evogp.pipeline import StandardPipeline

    class Parcimonieuse(SymbolicRegression):
        def evaluate(self, forest):
            return super().evaluate(forest) - parcimonie * forest.batch_subtree_size[:, 0].float()
    torch.manual_seed(graine); torch.cuda.manual_seed_all(graine)
    Xg = torch.tensor(np.ascontiguousarray(Xtr), dtype=torch.float32, device="cuda").contiguous()
    Yg = torch.tensor(Ytr.astype(np.float32), device="cuda")[:, None].contiguous()
    d = GenerateDescriptor(max_tree_len=64, input_len=Xtr.shape[1], output_len=1,
                           using_funcs=["+", "-", "*", "loose_div", "min", "max", "neg", ">", "<", "tanh", "exp", "loose_log", "abs"],
                           max_layer_cnt=6, const_samples=[-2.0, -1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0, 2.0])
    alg = GeneticProgramming(initial_forest=Forest.random_generate(pop_size=pop, descriptor=d), crossover=DefaultCrossover(),
                             mutation=DefaultMutation(mutation_rate=0.2, descriptor=d.update(max_layer_cnt=4)),
                             selection=DefaultSelection(survival_rate=0.3, elite_rate=0.01))
    best = StandardPipeline(alg, Parcimonieuse(datapoints=Xg, labels=Yg), generation_limit=gen, is_show_details=False).run()
    return best


def evogp_predire(best, X_):
    with torch.no_grad():
        out = best.forward(torch.tensor(np.ascontiguousarray(X_), dtype=torch.float32, device="cuda").contiguous())
    return np.clip(np.nan_to_num(out.reshape(-1).cpu().numpy(), nan=0.5), 0.0, 1.0)


def evogp_cv(Xtr, Ytr, Xte, parcimonie):
    # 5 graines ; on garde celle qui ajuste le mieux l entrainement ( jamais le pli de test )
    meilleurs = []
    for s in range(GRAINES_CV):
        b = evogp_fit(Xtr, Ytr, POP_CV, GEN_CV, GRAINE + s, parcimonie)
        p_tr = evogp_predire(b, Xtr); meilleurs.append((np.mean((p_tr - Ytr) ** 2), b))
    b = min(meilleurs, key=lambda x: x[0])[1]
    return evogp_predire(b, Xte), str(b.to_infix())


t0 = time.time()
out = {k: np.full(len(Y), np.nan) for k in ["constante", "logistique", "reseau"] + [f"evogp_p{p:g}" for p in PARCIMONIES]}
formules = {}
for k, w in enumerate(MONDES):
    te, tr = mondes == w, mondes != w
    out["constante"][te] = Y[tr].mean()
    out["logistique"][te] = logistique(X[tr], Y[tr], X[te])
    out["reseau"][te] = reseau(X[tr], Y[tr], X[te])
    for p in PARCIMONIES:
        pr, fx = evogp_cv(X[tr], Y[tr], X[te], p)
        out[f"evogp_p{p:g}"][te] = pr; formules[f"monde{w}_p{p:g}"] = fx
    print(f"pli {k + 1}/{len(MONDES)} ( monde {w} ) fait, {time.time() - t0:.0f} s", flush=True)
suffixe = ("_fumee" if FUMEE else "") + f"_{JEU}"
with open(f"{D}/predictions{suffixe}.csv", "w", newline="") as fo:
    wr = csv.writer(fo); wr.writerow(["episode", "monde", "Y", "attendre"] + list(out))
    for i in range(len(Y)):
        wr.writerow([rows[i]["episode"], mondes[i], Y[i], attendre[i]] + [f"{out[m][i]:.6f}" for m in out])
json.dump(dict(noms=noms, n=int(len(Y)), taux=float(Y.mean()), formules_cv=formules, jeu=JEU,
               budget=dict(pop=POP_CV, gen=GEN_CV, graines=GRAINES_CV, parcimonies=PARCIMONIES), duree_s=time.time() - t0),
          open(f"{D}/meta{suffixe}.json", "w"), indent=1)
print(f"FINI en {time.time() - t0:.0f} s ; {len(Y)} episodes, {len(noms)} variables : {noms}")
