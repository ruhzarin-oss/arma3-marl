"""Rejeu de l unique case restee vide : bras R, monde 6, situation 3. Ce n est pas un amendement, c est la
reparation que la porte K2 est ecrite pour permettre - elle compte des CASES, precisement pour qu un episode
perdu puisse etre rejoue."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
src = None
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") == "CALIBRATION-ADVERSAIRE-20-09" and j.get("version") == "CAL-R-s3-g6g7":
        src = {k: v for k, v in j.items() if k != "note"}; break
if not src: raise SystemExit("job introuvable")
src["version"] = "CAL-R-s3-g6g7-B"; src["instance"] = 1
src["note"] = "Rejeu de la case ( R, monde 6, situation 3 ) restee sans resultat. Reparation, pas amendement."
nom = f"2026-09-21_{src['version'].replace('-', '_')}.json"
prep = f"{H}/queue_preparation/{nom}"; json.dump(src, open(prep, "w"), indent=1, ensure_ascii=True)
r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
if "CONTROLE OK" not in r.stdout:
    print("REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l) or r.stdout[-300:]); raise SystemExit(1)
if "--poser" in sys.argv:
    t = time.time() - 10800; os.utime(prep, (t, t)); shutil.move(prep, f"{H}/queue/{nom}"); print("POSE", nom)
else:
    os.remove(prep); print("A BLANC : controle passe")
