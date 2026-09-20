"""Remplacement des episodes manquants d ORACLE-P2-19-09 : les deux cases du monde 9 sous le seuil de trois.
Cinq jobs reposes tels quels ( amendement de remplacement des criteres )."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
BESOIN = {(0, 1, 1), (0, 1, 4), (1, 2, 1), (1, 2, 3), (1, 2, 4)}   # ( niveau, option, situation ), paire 8-9
trouves = {}
for f in sorted(glob.glob(f"{H}/queue/faits/2026-09-19_OP2_*.json")):
    j = json.load(open(f))
    if j.get("campagne") != "ORACLE-P2-19-09" or sorted(j.get("graines", [])) != [8, 9]: continue
    cle = (j["oracle_cmd"], j["traversee"], j["situation"])
    if cle in BESOIN and cle not in trouves: trouves[cle] = (f, j)
manque = BESOIN - set(trouves)
print(f"{len(trouves)} jobs retrouves sur {len(BESOIN)}" + (f" ; introuvables : {manque}" if manque else ""))
if manque: raise SystemExit("job d origine introuvable")
INSTANCES = [1, 2, 3, 4, 5]
poser = "--poser" in sys.argv; t0 = time.time() - 3600
for rang, (cle, (f, j)) in enumerate(sorted(trouves.items())):
    j = dict(j, instance=INSTANCES[rang % len(INSTANCES)],
             note="Remplacement : case du monde 9 sous le seuil de trois episodes apres les refus et la coupure de la station.")
    nom = os.path.basename(f).replace(".json", "_R.json")
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout: print(nom, "REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l)); raise SystemExit(1)
    print(f"   {nom} instance {j['instance']} niveau {j['oracle_cmd']} option {j['traversee']} situation {j['situation']} OK")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(trouves)} jobs, {2 * len(trouves)} episodes", "POSES" if poser else "A BLANC")
