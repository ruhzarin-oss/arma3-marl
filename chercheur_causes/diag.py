import collections, json, pyarrow.parquet as pq, numpy as np
R = "/mnt/data/hmt/chercheur_causes/resultats"
M = pq.read_table(f"{R}/matrice.parquet").to_pylist()
print("== D2 : comparaisons du delai du porteur")
for r in M:
    if r["levier"] == "job|delai_porteur" and r["variable"] in ("fini|charges", "fini_issue=SUCCES"):
        print("  ", {k: r[k] for k in ("lecture", "a", "b", "variable", "n_a", "n_b", "strates", "moy_a", "moy_b", "z", "q", "decouverte")})
E = [e for e in pq.read_table("/mnt/data/hmt/chercheur_causes/donnees/episodes.parquet").to_pylist() if e["campagne"] in ("DELAI-PORTEUR-14-09", "PORTE-A-CONTRE-PORTE-B-14-09")]
cles = sorted(k for k in E[0] if k.startswith("job|"))
diff = {}
for k in cles:
    vals = {c: sorted({str(e.get(k)) for e in E if e["campagne"] == c}) for c in ("DELAI-PORTEUR-14-09", "PORTE-A-CONTRE-PORTE-B-14-09")}
    if vals["DELAI-PORTEUR-14-09"] != vals["PORTE-A-CONTRE-PORTE-B-14-09"]: diff[k] = vals
print("   champs de job qui separent DELAI-PORTEUR de PORTE-A-CONTRE-B :", json.dumps(diff, indent=0))
print("\n== D1 : les variables que les placebos ont 'decouvertes' sont-elles rares ?")
import hashlib, math
exec(open("/mnt/c/hmt/tmp/chercheur_causes/chercher.py").read().split("# ------------------------------------------------------------------ 1. comparaisons")[0])
src = open("/mnt/c/hmt/tmp/chercheur_causes/chercher.py").read()
exec(src.split("# ------------------------------------------------------------------ 1. comparaisons")[1].split('print("\\n== 1. recherche des causes")')[0])
vals = [float(hashlib.md5(f"{e['episode_id']}|placebo0".encode()).digest()[0] % 2) for e in ep]
(ab, strates), = [(k, s) for k, s in comparaisons("placebo_0", True, LEVIERS, vals).items()]
res, meta = tester(strates)
js = [j for j in MEDIATEURS if j in res]
q = bh([res[j]["p"] for j in js])
rows = meta["rows"]
dec = [(j, qq) for j, qq in zip(js, q) if qq <= 0.05]
print(f"   placebo_0 : {len(dec)} decouvertes ; episodes non nuls de chaque variable dans la comparaison :")
nonnuls = [int((X[rows, j] != 0).sum()) for j, _ in dec]
for (j, qq), nz in sorted(zip(dec, nonnuls), key=lambda t: t[1])[:15]: print(f"      non nuls {nz:4d} / {len(rows)}  z={res[j]['z']:+.1f}  {NOMS[j]}")
print("   mediane des non nuls parmi les decouvertes :", float(np.median(nonnuls)), " ; parmi toutes les variables testees :", float(np.median([(X[rows, j] != 0).sum() for j in js])))
# p empirique avec 20000 permutations pour les decouvertes
lab, sid = meta["lab"], meta["sid"]
W = 0; ca = np.zeros(len(rows)); cb = np.zeros(len(rows))
for s in range(sid.max() + 1):
    m = sid == s; na = (lab[m] == 0).sum(); nb = (lab[m] == 1).sum(); w = na * nb / (na + nb); W += w
    ca[m] = w / na; cb[m] = w / nb
Y = X[rows][:, [j for j, _ in dec]]
T = (lab * (ca + cb) - ca) @ Y / W
cnt = np.zeros(len(dec)); tot = 0
for _ in range(10):
    Lp = np.empty((2000, len(rows)))
    for s in range(sid.max() + 1):
        m = sid == s; Lp[:, m] = rng.permuted(np.tile(lab[m], (2000, 1)), axis=1)
    Tp = (Lp * (ca + cb) - ca) @ Y / W
    cnt += (np.abs(Tp - Tp.mean(0)) >= np.abs(T - Tp.mean(0)) - 1e-12).sum(0); tot += 2000
pe = (cnt + 1) / (tot + 1)
print("   p empiriques (20 000 permutations) des 'decouvertes' du placebo_0 :", np.round(np.sort(pe), 5)[:12], "... min", pe.min())
print("   p normaux correspondants :", np.round(np.sort([res[j]["p"] for j, _ in dec]), 7)[:12])
