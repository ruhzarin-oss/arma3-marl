"""Ce qui manque aux CONTROLES-ORACLE-20-09 apres l echec de deploiement du 20/09 16 h 17.
Cible : 8 mondes x 2 situations par bras. On ne pose QUE les ( monde, situation ) sans episode valide,
graine par graine : aucun rejeu d une combinaison deja valide."""
import glob, json, os, re, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
MANQUE = {1: {1: [[5, 7], [9, 12]], 2: [[5, 7], [9, 12]]},
          3: {1: [[4, 5], [6, 7], [8, 9], [11, 12]], 2: [[4, 5], [6, 8], [9, 12]]}}
gab = {}
for jf in sorted(glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") == "CONTROLES-ORACLE-20-09": gab[j["oracle_ctrl"]] = {k: v for k, v in j.items() if k != "note"}
if set(gab) != {1, 3}: raise SystemExit("gabarits introuvables")
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
L = []
for ctrl, parsit in MANQUE.items():
    nom = "POSITIF" if ctrl == 1 else "NONTRICHE"
    for s, lots in parsit.items():
        for lot in lots:
            L.append(dict(gab[ctrl], graines=lot, situation=s, oracle_ctrl=ctrl,
                          version=f"CTRL-{nom}-s{s}-g{'g'.join(str(x) for x in lot)}-B",
                          note="Manquant apres l echec de deploiement ( mission modifiee pendant que les serveurs tournaient )."))
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
print(f"{len(L)} jobs, {sum(len(j['graines']) for j in L)} episodes", "POSES" if poser else "A BLANC : tous les controles passent")
