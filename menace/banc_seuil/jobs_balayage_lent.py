"""BALAYAGE-LENT-19-09 ( criteres : CRITERES_BALAYAGE_LENT_19-09.md )."""
import json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
g = json.load(open(f"{H}/queue/faits/2026-09-18_MONDE_m4-5_150m.json")); g = {k: v for k, v in g.items() if k != "note"}
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
CAS = [(8, az, pas, m) for az in (0, 45) for pas in (10, 30) for m in ([4, 5], [6, 7], [8, 9], [11, 12])] + [(7, 0, 30, m) for m in ([4, 5], [6, 7], [8, 9], [11, 12])]
random.Random(1949).shuffle(CAS); L = []
for k, (mode, az, pas, m) in enumerate(CAS):
    L.append((f"2026-09-19_BANC3_LENT_mode{mode}_az{az}_pas{pas}_m{m[0]}.json", dict(g, campagne="BALAYAGE-LENT-19-09", version=f"LENT-mode{mode}_az{az}_pas{pas}_m{m[0]}", instance=INST[k % 12], graines=m,
              controle_perception=mode, controle_posture=0, controle_az=az, controle_pas=pas, controle_dist=200, observation=90, note=f"Balayage lent : mode {mode}, ecart {az} deg, pas {pas} s, 200 m, mondes {m}.")))
poser = "--poser" in sys.argv; os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - 1000   # plus recent que P2 : ne prend que les creux
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    if rang < 3 or not poser:
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        if "CONTROLE OK" not in r.stdout: print(f, "REFUS", r.stdout[-300:]); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print(len(L), "jobs", "POSES" if poser else "A BLANC : tous controles OK, rien pose")
