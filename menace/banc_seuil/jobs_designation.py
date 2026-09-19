"""DESIGNATION-19-09 ( criteres : CRITERES_DESIGNATION_19-09.md ). Mode 5 ( doWatch sur l unite ) contre mode 9 ( doWatch sur sa position ), apparies."""
import json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
g = json.load(open(f"{H}/queue/faits/2026-09-18_MONDE_m4-5_150m.json")); g = {k: v for k, v in g.items() if k != "note"}
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
CAS = [(mode, d, m) for mode in (5, 9) for d in (150, 200) for m in ([4, 5], [6, 7], [8, 9], [11, 12])]
random.Random(1939).shuffle(CAS); L = []
for k, (mode, d, m) in enumerate(CAS):
    L.append((f"2026-09-19_BANC3_DES_mode{mode}_{d}m_m{m[0]}.json", dict(g, campagne="DESIGNATION-19-09", version=f"DES-mode{mode}_{d}m_m{m[0]}", instance=INST[k % 12], graines=m,
              controle_perception=mode, controle_posture=0, controle_az=0, controle_dist=d, observation=600, note=f"Designation : mode {mode}, {d} m, mondes {m}.")))
poser = "--poser" in sys.argv; os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - 9000
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    if rang < 3 or not poser:
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        if "CONTROLE OK" not in r.stdout: print(f, "REFUS", r.stdout[-300:]); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print(len(L), "jobs", "POSES" if poser else "A BLANC : tous controles OK, rien pose")
