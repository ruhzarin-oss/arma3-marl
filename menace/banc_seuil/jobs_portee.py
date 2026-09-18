"""PORTEE-REGARD-CENTRE-18-09 ( criteres : CRITERES_PORTEE_18-09.md ). 40 jobs, 80 episodes, 12 instances, ordre melange."""
import json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "PORTEE-REGARD-CENTRE-18-09"
g = json.load(open(f"{H}/queue/faits/2026-09-18_MONDE_m4-5_150m.json"))
assert g["banc"] == "chacalvue" and g["controle_perception"] == 5 and g["observation"] == 600 and g["sonde"] == 1
g = {k: v for k, v in g.items() if k != "note"}
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
CAS = [(jour, d, m) for jour in (0, 1) for d in (250, 300, 400, 500, 600) for m in ([4, 5], [6, 7], [8, 9], [11, 12])]
random.Random(1841).shuffle(CAS)
L = []
for k, (jour, d, m) in enumerate(CAS):
    nom = f"{'JOUR' if jour else 'NUIT'}_m{m[0]}-{m[1]}_{d}m"
    L.append((f"2026-09-18_PORTEE_{nom}.json", dict(g, campagne=CAMPAGNE, instance=INST[k % 12], jour=jour, graines=m, controle_dist=d,
              version=f"PORTEE-{nom}", note=f"Portee regard centre, {'jour' if jour else 'nuit'}, mondes {m}, cible debout a {d} m.")))
if "--plan" in sys.argv:
    par = {}
    for f, j in L: par.setdefault(j["instance"], []).append(j["version"].replace("PORTEE-", ""))
    for i in INST: print(i, par[i])
    raise SystemExit
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - 7200
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    if rang < 3 or poser is False:   # le controle complet coute ~5 s par job : a blanc on les passe tous, a la pose on en repasse trois
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        if "CONTROLE OK" not in r.stdout: print(f, "REFUS", r.stdout[-300:]); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print(len(L), "jobs", "POSES" if poser else "A BLANC : tous controles OK, rien pose")
