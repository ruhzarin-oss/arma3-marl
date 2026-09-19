"""GRILLE-PERCEPTION-19-09 ( criteres : oracle/CRITERES_GRILLE_PERCEPTION.md, ecrits avant ).
Trois bras : patrouille seule ( 32 ), poste seul ( 32 ), AUCUNE menace ( 8, controle negatif ).
8 mondes x 4 graines de situation ; option fixee a 1 ; sonde de decision active ; Oracle a 0."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CHOIX-P2-TYPES-19-09" and g.get("menace_p2") == 4 and g.get("traversee") == 1:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit P2 introuvable")
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
L = []
for menace, sits in ((4, (1, 2, 3, 4)), (5, (1, 2, 3, 4)), (0, (1,))):
    nom = {4: "PATROUILLE", 5: "POSTE", 0: "AUCUNE"}[menace]
    for s in sits:
        for paire in PAIRES:
            j = dict(g, banc="chacaloracle", campagne="GRILLE-PERCEPTION-19-09", graines=paire, repetitions=1,
                     situation=s, menace_p2=menace, traversee=1, oracle_cmd=0, portee_son=600, sonde_perception=1,
                     instance=INSTANCES[len(L) % len(INSTANCES)],
                     version=f"GP-{nom}-s{s}-g{paire[0]}g{paire[1]}",
                     note=f"Grille de perception : bras {nom}, graine de situation {s}, mondes {paire}.")
            L.append((f"2026-09-19_GP_{nom}_s{s}_g{paire[0]}g{paire[1]}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 7200
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    if not ok:
        print(nom, "REFUS :", " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l)); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {sum(len(j['graines']) for _, j in L)} episodes "
      f"( patrouille {sum(2 for _, j in L if j['menace_p2'] == 4)}, poste {sum(2 for _, j in L if j['menace_p2'] == 5)}, "
      f"aucune {sum(2 for _, j in L if j['menace_p2'] == 0)} )", "POSES" if poser else "A BLANC : tous les controles passent")
