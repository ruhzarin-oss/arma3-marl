"""Fumee de l Oracle commandant v1 sur la copie bancs/chacaloracle : un job TEMOIN ( niveau 0 ) et un job
ORACLE ( niveau 1 ), memes mondes, meme vignette P2. Attentes ecrites avant :
  - temoin : aucune ligne CHACAL|O|, episode ACCEPTE, 0 erreur SQF, meme deroulement qu aujourd hui ;
  - oracle : des lignes CHACAL|O|decision toutes les 60 s, 0 erreur SQF, episode termine, budget qui descend."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CHOIX-P2-TYPES-19-09" and g.get("menace_p2") == 4 and g.get("traversee") == 1:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit P2 introuvable")
L = []
for rang, niveau in enumerate((0, 1)):
    j = dict(g, banc="chacaloracle", campagne="FUMEE-ORACLE-19-09", graines=[4, 5], repetitions=1,
             situation=1, oracle_cmd=niveau, oracle_b=6, oracle_nu=15, oracle_eps=15, oracle_delta=60,
             instance=[10, 11][rang], version=f"FUMEE-ORACLE-n{niveau}",
             note=f"Fumee de l Oracle commandant, niveau {niveau} ( {'temoin' if niveau == 0 else 'il cherche'} ).")
    L.append((f"2026-09-19_FUMEE_ORACLE_n{niveau}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 3600
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "banc", j["banc"], "instance", j["instance"], "oracle_cmd", j["oracle_cmd"], ":", "OK" if ok else "REFUS")
    if not ok:
        print("\n".join(l for l in r.stdout.splitlines() if "REFUS" in l or "manque" in l.lower())); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {2 * len(L)} episodes", "POSES" if poser else "A BLANC")
