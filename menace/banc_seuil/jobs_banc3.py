"""BANC3-19-09 ( criteres : CRITERES_BANC3_19-09.md ). --fumee : 3 jobs ; sinon 40 jobs. --poser pour mettre en file."""
import json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
g = json.load(open(f"{H}/queue/faits/2026-09-18_MONDE_m4-5_150m.json"))
assert g["banc"] == "chacalvue" and g["controle_perception"] == 5 and g["observation"] == 600 and g["jour"] == 0
g = {k: v for k, v in g.items() if k != "note"}
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
if "--fumee" in sys.argv:
    CAMP = "FUMEE-BANC3-19-09"
    CAS = [("REGRESSION", 5, 0, 0, 150, 600, [4, 5]), ("ACCROUPIE", 5, 1, 0, 100, 600, [4, 5]), ("BALAYAGE", 8, 0, 45, 150, 90, [4, 5])]
else:
    CAMP = "BANC3-19-09"
    CAS = [(f"ACC_{d}m_m{m[0]}", 5, 1, 0, d, 600, m) for d in (100, 150, 200, 250, 300, 400) for m in ([4, 5], [6, 7], [8, 9], [11, 12])]
    CAS += [(f"BAL{mode}_az{az}_m{m[0]}", mode, 0, az, 200, 90, m) for mode in (7, 8) for az in (0, 45, 90, 135) for m in ([4, 5], [6, 7])]
    random.Random(1919).shuffle(CAS)
L = []
for k, (nom, mode, post, az, d, obs, m) in enumerate(CAS):
    L.append((f"2026-09-19_BANC3_{nom}.json", dict(g, campagne=CAMP, version=f"BANC3-{nom}", instance=INST[k % 12], graines=m, controle_perception=mode, controle_posture=post,
              controle_az=az, controle_dist=d, observation=obs, note=f"Banc v3 : mode {mode}, posture {post}, ecart {az} deg, {d} m, mondes {m}, fenetre {obs} s.")))
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - (9000 if "--fumee" in sys.argv else 3000)
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    if rang < 3 or not poser:
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        if "CONTROLE OK" not in r.stdout: print(f, "REFUS", r.stdout[-300:]); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print(len(L), "jobs", "POSES" if poser else "A BLANC : tous controles OK, rien pose")
