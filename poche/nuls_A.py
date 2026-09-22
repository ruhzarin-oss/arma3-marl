"""Poche, etape 1 : les nuls a battre et le plancher provisoire, sur les mondes A ( deja joues ). Descriptif : la
certification se fera sur les mondes B, jamais touches. Les 480 paires de confirmation restent SCELLEES."""
import re, numpy as np
from oracle.autonome import config as C, donnees as Dn, monde as M
E = Dn.utilisables(Dn.episodes(lambda c: not str(c).startswith("ORACLE-I") or int(str(c)[8:] or 0) < 12))
Y = np.array([e["compromis"] for e in E], dtype=float); W = np.array([e["graine"] for e in E])
print(f"mondes A : {sorted(set(W.tolist()))} ; {len(E)} episodes ( paires de confirmation exclues, scellees )")
b = {"N0 constante": [], "N1 taux par monde ( moitie-moitie )": [], "N2 imagination de l Oracle": []}
rng = np.random.default_rng(C.GRAINE)
for w in sorted(set(W)):
    te = W == w; tr = ~te
    if te.sum() < 20: continue
    Etr = [e for e, k in zip(E, tr) if k]; Ete = [e for e, k in zip(E, te) if k]
    b["N0 constante"] += list((Y[tr].mean() - Y[te]) ** 2)
    idx = rng.permutation(np.where(te)[0]); h1, h2 = idx[: len(idx) // 2], idx[len(idx) // 2:]
    b["N1 taux par monde ( moitie-moitie )"] += list((Y[h1].mean() - Y[h2]) ** 2)
    m = M.Monde().apprendre(Etr)
    mu, _ = m.predire([{k: e[k] for k in C.ARMES} for e in Ete], [e["graine"] for e in Ete], [e["option"] for e in Ete])
    b["N2 imagination de l Oracle"] += list((mu - Y[te]) ** 2)
print("Brier, un monde laisse de cote ( N1 : moitie des episodes du monde pour apprendre, l autre pour juger ) :")
for k, v in b.items(): print(f"   {k:<38} {np.mean(v):.4f}  ( n {len(v)} )")
# le plancher provisoire : les paires d EXPLORATION de l Oracle ( iterations 1 a 11 )
P = {}
for e in Dn.utilisables(Dn.episodes(lambda c: str(c).startswith(C.PREFIXES_HISTORIQUES))):
    mm = re.match(r"(DIA|ORA)-(\d+)-c(\d+)-o(\d)-r(\d)", str(e["version"]))
    if mm and int(mm.group(2)) < 12: P.setdefault((mm.group(2), mm.group(3), mm.group(5), e["graine"]), {})[int(mm.group(4))] = e["compromis"]
p = np.array([[v[1], v[2]] for v in P.values() if 1 in v and 2 in v], dtype=float); d = p[:, 1] - p[:, 0]
print(f"\nplancher provisoire : {len(d)} paires d exploration, variance d une difference appariee {d.var():.3f}")
for n in (40, 55, 100, 480): print(f"   ecart-type d un ecart moyen a {n:>3} paires : {np.sqrt(d.var() / n):.3f}")
