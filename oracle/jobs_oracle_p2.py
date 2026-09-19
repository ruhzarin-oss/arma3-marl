"""ORACLE-P2-19-09 ( criteres : oracle/CRITERES_ORACLE_P2.md, ecrits avant ). Bras PATROUILLE seul.
2 niveaux d Oracle ( 0 temoin, 1 actif ) x 2 options x 8 mondes x 4 graines de situation = 128 episodes, 64 jobs
melanges sur 12 instances."""
import glob, json, os, random, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "P2-PERCUE-19-09" and g.get("menace_p2") == 4:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
L = []
for niveau in (0, 1):
    for opt in (1, 2):
        for s in (1, 2, 3, 4):
            for paire in PAIRES:
                L.append(dict(g, campagne="ORACLE-P2-19-09", graines=paire, situation=s, menace_p2=4, traversee=opt,
                              oracle_cmd=niveau, oracle_b=6, oracle_nu=15, oracle_eps=15, oracle_delta=60,
                              portee_son=900, sonde_perception=1,
                              version=f"OP2-n{niveau}-t{opt}-s{s}-g{paire[0]}g{paire[1]}",
                              note=f"Oracle {'actif' if niveau else 'temoin'}, option {opt}, situation {s}, mondes {paire}."))
random.Random(1929).shuffle(L)
for rang, j in enumerate(L): j["instance"] = INSTANCES[rang % len(INSTANCES)]
poser = "--poser" in sys.argv; t0 = time.time() - 10800
for rang, j in enumerate(L):
    nom = f"2026-09-19_{j['version'].replace('-', '_')}.json"
    prep = f"{H}/queue_preparation/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout: print(nom, "REFUS", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l)); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
from collections import Counter
print(f"{len(L)} jobs, {2 * len(L)} episodes ; par ( niveau, option ) {dict(Counter((j['oracle_cmd'], j['traversee']) for j in L))}",
      "POSES" if poser else "A BLANC : tous les controles passent")
