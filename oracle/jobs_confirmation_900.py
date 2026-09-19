"""CONFIRMATION-900-19-09 ( criteres : oracle/CRITERES_CONFIRMATION_900.md, ecrits avant ).
Portee 900 m, canal moteur_depuis_fenetre, GRAINES DE SITUATION NEUVES ( 5, 6, 7 ) : la confirmation ne rejoue pas
les situations qui ont servi a choisir le reglage. 24 patrouille + 24 poste + 8 aucune = 56 episodes."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "GRILLE-PERCEPTION-19-09" and g.get("menace_p2") == 4:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit de grille introuvable")
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
L = []
for menace, sits in ((4, (5, 6, 7)), (5, (5, 6, 7)), (0, (5,))):
    nom = {4: "PATROUILLE", 5: "POSTE", 0: "AUCUNE"}[menace]
    for s in sits:
        for paire in PAIRES:
            j = dict(g, campagne="CONFIRMATION-900-19-09", graines=paire, situation=s, menace_p2=menace,
                     portee_son=900, sonde_perception=1, instance=INSTANCES[len(L) % len(INSTANCES)],
                     version=f"C900-{nom}-s{s}-g{paire[0]}g{paire[1]}",
                     note=f"Confirmation a 900 m, canal memoire de fenetre : bras {nom}, situation NEUVE {s}, mondes {paire}.")
            L.append((f"2026-09-19_C900_{nom}_s{s}_g{paire[0]}g{paire[1]}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 7200
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout:
        print(nom, "REFUS :", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l)); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {2 * len(L)} episodes", "POSES" if poser else "A BLANC : tous les controles passent")
