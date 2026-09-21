"""Formule finale d EvoGP pour l equation P2 ( criteres fca5d5d ). Choix MECANIQUE de la parcimonie : celle dont les
predictions hors pli ( jeu A ) ont le meilleur Brier - regle ecrite d avance, aucun score n est affiche. Puis
reajustement sur toutes les donnees : population 1 000 000, 600 generations, 10 graines, meilleure fitness gardee.
On sauve la formule, et les probabilites predites sous « traverser » et sous « attendre » pour chaque episode."""
import csv, json, sys, time
import numpy as np, torch
sys.argv = [sys.argv[0], "--jeu", "A"] + (["--fumee"] if "--fumee" in sys.argv else [])
FUMEE = "--fumee" in sys.argv
import importlib.util
spec = importlib.util.spec_from_file_location("aj", "/mnt/data/hmt/depot/oracle/ajuster_equation_p2.py")
# on ne relance pas la validation croisee : on ne recupere que la table et les fonctions
src = open("/mnt/data/hmt/depot/oracle/ajuster_equation_p2.py").read().split("t0 = time.time()")[0]
g = {"__name__": "aj"}; exec(src, g)
X, Y, noms, D = g["X"], g["Y"], g["noms"], g["D"]
suf = ("_fumee" if FUMEE else "") + "_A"
pred = list(csv.DictReader(open(f"{D}/predictions{suf}.csv")))
Yp = np.array([float(r["Y"]) for r in pred])
cands = [k for k in pred[0] if k.startswith("evogp_p")]
brier = {k: float(np.mean((np.array([float(r[k]) for r in pred]) - Yp) ** 2)) for k in cands}
choisi = min(brier, key=brier.get); parc = float(choisi.replace("evogp_p", ""))
POP, GEN, NG = (5000, 5, 2) if FUMEE else (1000000, 600, 10)
t0 = time.time(); res = []
for s in range(NG):
    b = g["evogp_fit"](X, Y, POP, GEN, g["GRAINE"] + 100 + s, parc)
    p = g["evogp_predire"](b, X); res.append((float(np.mean((p - Y) ** 2)), s, b))
    print(f"graine {s + 1}/{NG} faite, {time.time() - t0:.0f} s", flush=True)
res.sort(key=lambda x: x[0]); best = res[0][2]
txt = str(best.to_infix())
import re
for j in sorted({int(m) for m in re.findall(r"\bx(\d+)\b", txt)}, reverse=True):
    txt = re.sub(rf"\bx{j}\b", noms[j], txt)
ia = noms.index("attendre")
X1 = X.copy(); X1[:, ia] = 0.0; X2 = X.copy(); X2[:, ia] = 1.0
p_trav, p_att = g["evogp_predire"](best, X1), g["evogp_predire"](best, X2)
with open(f"{D}/formule_finale{suf}.csv", "w", newline="") as fo:
    w = csv.writer(fo); w.writerow(["i", "Y", "attendre", "p_traverser", "p_attendre"])
    for i in range(len(Y)): w.writerow([i, int(Y[i]), X[i, ia], f"{p_trav[i]:.6f}", f"{p_att[i]:.6f}"])
json.dump(dict(parcimonie_choisie=parc, colonne=choisi, formule=txt, formules_toutes=[str(r[2].to_infix()) for r in res],
               taille=int(best.batch_subtree_size[0].item()) if hasattr(best, "batch_subtree_size") else None,
               budget=dict(pop=POP, gen=GEN, graines=NG), duree_s=time.time() - t0),
          open(f"{D}/formule_finale{suf}.json", "w"), indent=1)
print("FORMULE FINALE ECRITE ( non affichee ici )")
