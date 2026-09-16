import collections, pyarrow.parquet as pq
T = pq.read_table("/mnt/data/hmt/gymnase_decisions/donnees/phases.parquet").to_pylist()
base = [r for r in T if r["verdict"] == "ACCEPTE" and r["erreurs_sqf"] == 0 and r["lev_palier"] == 4 and r["lev_socle"] == 1
        and r["lev_effectif"] == 10 and r["lev_oracle"] in (0, None) and r["lev_ablation"] in (0, None) and r["lev_banc_appui"] in (0, None)
        and r["lev_placeur"] in (0, None) and r["lev_immortel"] in (0, None) and r["lev_jour"] in (0, None)
        and r["lev_tactique"] == 0 and r["lev_appui_feu"] == 0 and r["lev_feu_avant"] == 0 and r["lev_mg_assaut"] == 0 and r["lev_appui_fixe"] == 0
        and r["lev_partage"] is None and r["lev_qrf_n"] is None and r["lev_situation"] is None and r["lev_acc"] is None]
print("base stricte", len(base))
graines = collections.defaultdict(set)
for r in base: graines[r.get("site")].add(int(r["graine"]))
nom = {s: "monde_" + "-".join(str(g) for g in sorted(gs)) for s, gs in graines.items()}
cell = collections.Counter()
for r in base:
    if r.get("p5_debut_t") is None: continue
    cell[(nom[r.get("site")], "p5", int(r["lev_delai_porteur"]), r["campagne"] == "CONFIRMATION-MISSION-15-09")] += 1
    if r.get("p6_debut_t") is not None:
        cell[(nom[r.get("site")], "p6", int(r["lev_exfil"] or 0), int(r["lev_depart"]), r["campagne"] == "CONFIRMATION-MISSION-15-09")] += 1
for k, v in sorted(cell.items()): print(f"{v:5d}  {k}")
print("== succes | p6 joue, charges=3, par vivants a l'entree (hors CONFIRMATION)")
t = collections.defaultdict(lambda: [0, 0])
for r in base:
    if r.get("p6_debut_t") is None or r["campagne"] == "CONFIRMATION-MISSION-15-09" or r.get("p5_fin_charges") != 3: continue
    k = (int(r["p6_debut_vivants"]), int(r["p6_debut_compromis"]), int(r["p6_debut_alarme"]), int(r["lev_depart"]))
    t[k][0] += r["fini_issue"] == "SUCCES"; t[k][1] += 1
for k, v in sorted(t.items()): print(f"  {k}  {v[0]}/{v[1]}")
