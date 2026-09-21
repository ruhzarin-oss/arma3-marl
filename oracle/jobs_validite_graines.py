"""VALIDITE-GRAINES-21-09 ( regle : oracle/CRITERES_CALIBRATION_V2.md ). Un episode du bras R, situation 1,
option traverser, pour chaque graine candidate de 13 a 24. On ne lit AUCUNE issue : seulement la validite."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CALIBRATION-ADVERSAIRE-20-09" and g.get("oracle_cmd") == 1 and g.get("oracle_b") == 6 and g.get("oracle_delta") == 60:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
INSTANCES = [1, 2, 3, 4, 5, 6]
L = []
for k, paire in enumerate([[13, 14], [15, 16], [17, 18], [19, 20], [21, 22], [23, 24]]):
    L.append(dict(g, campagne="VALIDITE-GRAINES-21-09", graines=paire, situation=1, traversee=1, oracle_cmd=1,
                  oracle_b=6, oracle_delta=60, oracle_ctrl=0, instance=INSTANCES[k],
                  version=f"VAL-g{paire[0]}g{paire[1]}", note="Test de validite des graines neuves. Aucune issue lue."))
poser = "--poser" in sys.argv; t0 = time.time() - 10800
for rang, j in enumerate(L):
    nom = f"2026-09-21_{j['version'].replace('-', '_')}.json"
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout:
        print(nom, "REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l) or r.stdout[-300:]); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {2 * len(L)} episodes", "POSES" if poser else "A BLANC : tous les controles passent")
