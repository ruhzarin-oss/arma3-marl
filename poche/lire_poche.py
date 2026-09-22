"""Lecture UNIQUE du monde de poche sur les mondes B ( CRITERES_POCHE.md, ecrit avant ). V3 a son propre lecteur.
  python -m poche.lire_poche   ( depuis le depot )"""
import csv, os, sys
import numpy as np
from scipy.stats import spearmanr
sys.path.insert(0, "/mnt/data/hmt/depot")
from oracle.autonome import config as C, donnees as Dn, monde as M
B = [0, 1, 2, 10, 25, 26, 27, 28, 29, 30, 31]
F = "/mnt/data/hmt/depot/poche/predictions_B.csv"
if not os.path.exists(F): print("pas encore de predictions de la poche sur B : rien n est lu."); sys.exit(0)
pred = {r["episode"]: float(r["p_compromis"]) for r in csv.DictReader(open(F))}
EB = [e for e in Dn.utilisables(Dn.episodes(lambda c: True)) if e["graine"] in B and e["dossier"] in pred]
EA = [e for e in Dn.utilisables(Dn.episodes(lambda c: True)) if e["graine"] not in B]
mondes = sorted({e["graine"] for e in EB})
if len(mondes) < 8 or min(sum(e["graine"] == w for e in EB) for w in mondes) < 40:
    print(f"B incomplet : {len(mondes)} mondes, il en faut 8 avec 40 episodes chacun. Rien n est lu."); sys.exit(0)
Y = np.array([e["compromis"] for e in EB], float); P = np.array([pred[e["dossier"]] for e in EB]); W = np.array([e["graine"] for e in EB])
n0 = np.full(len(Y), np.mean([e["compromis"] for e in EA]))
rng = np.random.default_rng(C.GRAINE); n1 = np.zeros(len(Y)); juge1 = np.zeros(len(Y), bool)
for w in mondes:
    idx = rng.permutation(np.where(W == w)[0]); h1, h2 = idx[: len(idx) // 2], idx[len(idx) // 2:]
    n1[h2] = Y[h1].mean(); juge1[h2] = True
m = M.Monde().apprendre(EA)
n2, _ = m.predire([{k: e[k] for k in C.ARMES} for e in EB], [e["graine"] for e in EB], [e["option"] for e in EB])
br = lambda p, y: float(np.mean((p - y) ** 2))
print(f"== MONDE DE POCHE sur B : {len(EB)} episodes, {len(mondes)} mondes")
print(f"   Brier poche {br(P, Y):.4f} | N0 {br(n0, Y):.4f} | N2 {br(n2, Y):.4f} | ( moitie jugee ) poche {br(P[juge1], Y[juge1]):.4f} contre N1 {br(n1[juge1], Y[juge1]):.4f}")
opt = np.array([e["option"] for e in EB])
ea = Y[opt == 2].mean() - Y[opt == 1].mean(); ep = P[opt == 2].mean() - P[opt == 1].mean()
print(f"   V1 ecart attendre - traverser : Arma {ea:+.3f}, poche {ep:+.3f} -> {'INVERSE : ECHEC' if np.sign(ea) != np.sign(ep) else 'meme signe'}")
rho = spearmanr([Y[W == w].mean() for w in mondes], [P[W == w].mean() for w in mondes]).statistic
print(f"   V2 niveau par monde neuf : Spearman {rho:.2f} ( seuil 0,6 ) -> {'PASSE' if rho >= 0.6 else 'ECHEC : la poche ne sera crue que sur les ecarts'}")
