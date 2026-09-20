"""CONTROLES-ORACLE-V2-20-09 ( criteres : oracle/CRITERES_CONTROLES_ORACLE.md, ecrits avant ).
Deux bras : positif ( on amene la patrouille sur eux, de jour ) et non-triche ( on les teleporte ).
4 paires de mondes x 2 situations x 2 bras = 16 jobs, 32 episodes, sur 12 instances."""
import glob, json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1*/job.json") + glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "ORACLE-P2-19-09" and g.get("oracle_cmd") == 1:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
BRAS = {1: ("POSITIF", 1), 3: ("NONTRICHE", 0)}   # oracle_ctrl -> ( nom, jour )
L = []
for ctrl, (nom, jour) in BRAS.items():
    for s in (1, 2):
        for paire in PAIRES:
            L.append(dict(g, campagne="CONTROLES-ORACLE-V2-20-09", graines=paire, situation=s, menace_p2=4,
                          traversee=1, oracle_cmd=1, oracle_ctrl=ctrl, jour=jour,
                          oracle_b=6, oracle_nu=15, oracle_eps=15, oracle_delta=60,
                          portee_son=900, sonde_perception=1,
                          version=f"CTRLV2-{nom}-s{s}-g{paire[0]}g{paire[1]}",
                          note=f"Controle {nom.lower()}, situation {s}, mondes {paire}."))
random.Random(2009).shuffle(L)
for rang, j in enumerate(L): j["instance"] = INSTANCES[rang % len(INSTANCES)]
poser = "--poser" in sys.argv; t0 = time.time() - 10800
for rang, j in enumerate(L):
    nom = f"2026-09-20_{j['version'].replace('-', '_')}.json"
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout:
        print(nom, "REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l) or r.stdout[-400:]); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
from collections import Counter
print(f"{len(L)} jobs, {2 * len(L)} episodes ; par bras {dict(Counter(j['oracle_ctrl'] for j in L))}",
      "POSES" if poser else "A BLANC : tous les controles passent")
