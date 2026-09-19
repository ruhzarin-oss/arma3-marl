"""Fumee de l Oracle commandant v2 : bras PATROUILLE, option ATTENDRE ( la ou la patrouille compte le plus ), mondes 4 et 5.
Un job Oracle a 1, un job temoin a 0. Attentes ecrites avant :
  - 0 erreur SQF, episodes ACCEPTE, decision TRAVERSEE presente ;
  - Oracle a 1 : au moins une action PATROUILLE_*, le budget descend, et la distance patrouille_a DIMINUE apres l ordre ;
  - temoin a 0 : aucune ligne CHACAL|O|."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "P2-PERCUE-19-09" and g.get("menace_p2") == 4 and g.get("traversee") == 2:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
L = []
for rang, niveau in enumerate((1, 0)):
    j = dict(g, campagne="FUMEE-ORACLE-V2-19-09", graines=[4, 5], repetitions=1, situation=1, oracle_cmd=niveau,
             oracle_b=6, oracle_nu=15, oracle_eps=15, oracle_delta=60, instance=[1, 2][rang],
             version=f"FUMEE-ORACLE-V2-n{niveau}", note=f"Fumee de l Oracle v2, niveau {niveau}.")
    L.append((f"2026-09-19_FUMEE_ORACLE_V2_n{niveau}.json", j))
poser = "--poser" in sys.argv; t0 = time.time() - 3600
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout: print(nom, "REFUS", r.stdout[-300:]); raise SystemExit(1)
    print(nom, "instance", j["instance"], "oracle", j["oracle_cmd"], "OK")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print("POSES" if poser else "A BLANC")
