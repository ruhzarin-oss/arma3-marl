"""CHOIX-P2-TYPES-19-09 ( criteres : CRITERES_P2_TYPES_19-09.md ). 2 options x 2 types x 4 paires de mondes x 4 graines de situation = 64 jobs, 128 episodes.
Usage : python3 jobs_p2_types.py --avant A --balayage B [--fumee] [--poser]    ( A et B = le reglage designe par la regle de variance )"""
import json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
AVANT = int(sys.argv[sys.argv.index("--avant") + 1]); BAL = int(sys.argv[sys.argv.index("--balayage") + 1])
g = json.load(open(f"{H}/queue/faits/2026-09-18_VS_P2_TYPE2_s1.json")); g = {k: v for k, v in g.items() if k != "note"}
assert g["observation"] == 90 and g["depart"] == 2 and g["arret"] == 2 and g["vignette"] == 1
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]; NOM = {4: "PATROUILLE", 5: "POSTE"}
if "--fumee" in sys.argv:
    CAMP = "FUMEE-P2-TYPES-19-09"; CAS = [(2, 4, [4, 5], 1), (1, 5, [4, 5], 1)]
else:
    CAMP = "CHOIX-P2-TYPES-19-09"; CAS = [(o, b, m, s) for o in (1, 2) for b in (4, 5) for m in ([4, 5], [6, 7], [8, 9], [11, 12]) for s in (1, 2, 3, 4)]
    random.Random(1929).shuffle(CAS)
L = []
for k, (o, b, m, s) in enumerate(CAS):
    nom = f"{NOM[b]}-traversee{o}-g{m[0]}g{m[1]}-s{s}"
    L.append((f"2026-09-19_P2N_{k:03d}_{nom}.json", dict(g, banc="chacalp2", campagne=CAMP, version=f"P2-{nom}", traversee=o, menace_p2=b, graines=m, situation=s, repetitions=1,
              avant=AVANT, balayage=BAL, instance=INST[k % 12], note=f"{CAMP} : option {o}, bras {NOM[b]} ( niveau {b} ), mondes {m}, situation {s}, observation depuis {AVANT} m, balayage {BAL}.")))
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - (12000 if "--fumee" in sys.argv else 6000)
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    if rang < 3 or not poser:
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        if "CONTROLE OK" not in r.stdout: print(f, "REFUS", r.stdout[-300:]); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print(len(L), "jobs", CAMP, "POSES" if poser else "A BLANC : tous controles OK, rien pose")
