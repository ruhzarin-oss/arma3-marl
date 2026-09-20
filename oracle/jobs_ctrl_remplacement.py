"""Remplacement des 4 jobs de non-triche joues avec la version defectueuse du controle ( case d arrivee = SITE ).
Amendement 1 de oracle/CRITERES_CONTROLES_ORACLE.md : on ne rejoue PAS a l identique. Les paires touchees
( 6-7 et 11-12 ) sont reprises avec des situations que la campagne n a pas jouees ( 3 et 4 )."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CONTROLES-ORACLE-20-09" and g.get("oracle_ctrl") == 3:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
INSTANCES = [1, 2, 3, 4]
L = []
for s in (3, 4):
    for paire in ([6, 7], [11, 12]):
        L.append(dict(g, graines=paire, situation=s,
                      version=f"CTRL-NONTRICHE-s{s}-g{paire[0]}g{paire[1]}",
                      note="Remplacement des episodes joues avec la case d arrivee SITE ( controle vacant ). Situation neuve, aucun rejeu."))
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
print(f"{len(L)} jobs, {2 * len(L)} episodes", "POSES" if poser else "A BLANC : tous les controles passent")
