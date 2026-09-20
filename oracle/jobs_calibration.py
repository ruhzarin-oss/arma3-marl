"""CALIBRATION-ADVERSAIRE-20-09 ( criteres : oracle/CRITERES_CALIBRATION.md, ecrits avant ).
Quatre bras entrelaces : T temoin, N negatif ( B = 0 ), R reference ( B 6, delta 60 ), F frequent ( B 6, delta 30 ).
8 mondes x 4 situations x 4 bras = 128 episodes, 64 jobs, 12 instances. Option equilibree : s1-s2 traverser,
s3-s4 attendre - elle ne sera pas lue."""
import glob, json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "ORACLE-P2-19-09" and g.get("oracle_cmd") == 1:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
BRAS = [("T", 0, 6, 60), ("N", 1, 0, 60), ("R", 1, 6, 60), ("F", 1, 6, 30)]
L = []
for nom, cmd, b, delta in BRAS:
    for s in (1, 2, 3, 4):
        for paire in PAIRES:
            L.append(dict(g, campagne="CALIBRATION-ADVERSAIRE-20-09", graines=paire, situation=s, menace_p2=4,
                          traversee=(1 if s in (1, 2) else 2), oracle_cmd=cmd, oracle_ctrl=0,
                          oracle_b=b, oracle_delta=delta, oracle_nu=15, oracle_eps=15,
                          portee_son=900, sonde_perception=1, jour=0,
                          version=f"CAL-{nom}-s{s}-g{paire[0]}g{paire[1]}",
                          note=f"Bras {nom} : oracle_cmd {cmd}, budget {b}, periode {delta} s, situation {s}, mondes {paire}."))
random.Random(2009).shuffle(L)
for rang, j in enumerate(L): j["instance"] = INSTANCES[rang % len(INSTANCES)]
poser = "--poser" in sys.argv; t0 = time.time() - 10800
for rang, j in enumerate(L):
    nom = f"2026-09-20_{j['version'].replace('-', '_')}.json"
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout:
        print(nom, "REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l) or r.stdout[-300:]); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
from collections import Counter
print(f"{len(L)} jobs, {2 * len(L)} episodes ; par bras "
      f"{dict(Counter((j['oracle_cmd'], j['oracle_b'], j['oracle_delta']) for j in L))} ; "
      f"options {dict(Counter(j['traversee'] for j in L))}",
      "POSES" if poser else "A BLANC : tous les controles passent")
