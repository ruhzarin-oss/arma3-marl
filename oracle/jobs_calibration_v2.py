"""CALIBRATION-P2-V2-21-09 ( criteres : oracle/CRITERES_CALIBRATION_V2.md, ecrits avant ).
Trois bras entrelaces : T temoin, R ( B 6, delta 60 ), F ( B 6, delta 30 ). Option FIXEE traverser.
16 mondes ( 8 connus + 8 neufs retenus par le test de validite ) x 4 situations x 3 bras = 192 episodes."""
import glob, json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
NEUFS = [int(x) for x in sys.argv[sys.argv.index("--neufs") + 1].split(",")]
assert len(NEUFS) == 8 and all(13 <= w <= 31 for w in NEUFS), "il faut exactement 8 graines neuves entre 13 et 31"
CONNUS = [4, 5, 6, 7, 8, 9, 11, 12]
MONDES = CONNUS + NEUFS
PAIRES = [MONDES[i:i + 2] for i in range(0, 16, 2)]
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CALIBRATION-ADVERSAIRE-20-09" and g.get("oracle_cmd") == 1:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
BRAS = [("T", 0, 6, 60), ("R", 1, 6, 60), ("F", 1, 6, 30)]
L = []
for nom, cmd, b, delta in BRAS:
    for s in (1, 2, 3, 4):
        for paire in PAIRES:
            L.append(dict(g, campagne="CALIBRATION-P2-V2-21-09", graines=paire, situation=s, menace_p2=4,
                          traversee=1, oracle_cmd=cmd, oracle_ctrl=0, oracle_b=b, oracle_delta=delta,
                          oracle_nu=15, oracle_eps=15, portee_son=900, sonde_perception=1, jour=0,
                          version=f"CAL2-{nom}-s{s}-g{paire[0]}g{paire[1]}",
                          note=f"Bras {nom} : oracle_cmd {cmd}, budget {b}, periode {delta} s, situation {s}, mondes {paire}, option traverser."))
random.Random(2109).shuffle(L)
for rang, j in enumerate(L): j["instance"] = INSTANCES[rang % len(INSTANCES)]
poser = "--poser" in sys.argv; t0 = time.time() - 10800
for rang, j in enumerate(L):
    nom = f"2026-09-21_{j['version'].replace('-', '_')}.json"
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout:
        print(nom, "REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l) or r.stdout[-300:]); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
from collections import Counter
print(f"{len(L)} jobs, {2 * len(L)} episodes ; mondes {MONDES} ; par bras "
      f"{dict(Counter((j['oracle_cmd'], j['oracle_delta']) for j in L))} ; options {dict(Counter(j['traversee'] for j in L))}",
      "POSES" if poser else "A BLANC : tous les controles passent")
