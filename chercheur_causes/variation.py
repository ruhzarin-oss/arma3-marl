import collections, pyarrow.parquet as pq
E = pq.read_table("/mnt/data/hmt/chercheur_causes/donnees/episodes.parquet").to_pylist()
E = [e for e in E if e["verdict"] == "ACCEPTE" and e["erreurs_sqf"] == 0]
leviers = sorted(k for k in E[0] if k.startswith("job|"))
print("episodes acceptes sans erreur", len(E))
print("== leviers qui VARIENT A L INTERIEUR d une campagne ET d un monde ( experiences entrelacees )")
for L in leviers:
    par = collections.defaultdict(collections.Counter)
    for e in E:
        par[(e["campagne"], e["site"])][e.get(L)] += 1
    camps = collections.Counter()
    for (c, s), cnt in par.items():
        if len([x for x in cnt if x is not None]) >= 2: camps[c] += sum(cnt.values())
    if camps: print(f"  {L:22s}", dict(camps))
