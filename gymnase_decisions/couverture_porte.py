import collections, glob, json, pyarrow.parquet as pq
T = pq.read_table("/mnt/data/hmt/gymnase_decisions/donnees/phases.parquet").to_pylist()
ver = {}
for run in glob.glob("/mnt/data/hmt/runs/*/"):
    try: ver[run.rstrip('/').split('/')[-1]] = json.load(open(run + "job.json")).get("version") or ""
    except Exception: pass
c = collections.Counter()
for r in T:
    if r["verdict"] != "ACCEPTE" or r["erreurs_sqf"] or r["lev_depart"] != 5 or r["lev_palier"] != 4 or r["lev_socle"] != 1: continue
    if r["lev_partage"] is not None or r["lev_situation"] is not None or r["lev_qrf_n"] is not None: continue
    v = ver.get(r["episode_id"].split("/")[0], "")
    porte = "B" if "-B-" in v else ("A" if "-A-" in v else "script")
    c[(r["campagne"], int(r["graine"]), porte, int(r["lev_delai_porteur"]), int(r["lev_arret"]), r["lev_azimut"])] += 1
for k, v in sorted(c.items()): print(f"{v:4d} {k}")
