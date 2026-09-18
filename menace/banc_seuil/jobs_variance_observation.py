"""VARIANCE-OBSERVATION-19-09 ( criteres : CRITERES_VARIANCE_OBSERVATION_19-09.md ). 6 reglages ( avant x balayage ) x 4 paires de mondes
x 2 graines de situation = 48 jobs, 96 episodes, P2 niveau 5, traverser tout de suite, fenetre 90 s. Une campagne PAR REGLAGE, pour que
menace/lire_variance.py ( inchange ) lise chaque reglage a part : VARIANCE-OBS-a<avant>-b<balayage>-19-09."""
import json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
g = json.load(open(f"{H}/queue/faits/2026-09-18_VS_P2_TYPE2_s1.json")); g = {k: v for k, v in g.items() if k != "note"}
assert g["menace_p2"] == 5 and g["traversee"] == 1 and g["observation"] == 90, (g["menace_p2"], g["traversee"], g["observation"])
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
CAS = [(a, b, m, s) for a in (260, 180, 120) for b in (0, 1) for m in ([4, 5], [6, 7], [8, 9], [11, 12]) for s in (1, 2)]
random.Random(1909).shuffle(CAS)
L = []
for k, (a, b, m, s) in enumerate(CAS):
    camp = f"VARIANCE-OBS-a{a}-b{b}-19-09"
    L.append((f"2026-09-19_VO_a{a}_b{b}_m{m[0]}-{m[1]}_s{s}.json", dict(g, banc="chacalp2", campagne=camp, version=f"VO-P2_TYPE2_a{a}b{b}_m{m[0]}s{s}", avant=a, balayage=b,
              graines=m, repetitions=1, situation=s, instance=INST[k % 12], note=f"Variance de perception : avant={a} m, balayage={b}, mondes {m}, situation {s}.")))
if "--plan" in sys.argv:
    par = {}
    for f, j in L: par.setdefault(j["instance"], []).append(f"a{j['avant']}b{j['balayage']}m{j['graines'][0]}s{j['situation']}")
    for i in INST: print(i, par[i])
    raise SystemExit
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - 6000
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    if rang < 3 or not poser:
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        if "CONTROLE OK" not in r.stdout: print(f, "REFUS", r.stdout[-300:]); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print(len(L), "jobs", "POSES" if poser else "A BLANC : tous controles OK, rien pose")
