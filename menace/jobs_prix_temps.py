"""Campagne PRIX-DU-TEMPS-18-09 : vignette d4a6 ( assaut + exfiltration ), attente imposee de 0, 600 ou 1200 s avant la
phase 5, 8 mondes x 2 repetitions = 48 episodes. Test independant ; ne touche a aucune autre campagne."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "PRIX-DU-TEMPS-V2-18-09"
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1[78]_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CHOIX-P6-17-09":
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit P6 ( d4a6 ) introuvable")
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
L = []
for attente in (0, 600, 1200):
    for paire in PAIRES:
        j = dict(g, campagne=CAMPAGNE, graines=paire, repetitions=2, attente_test=attente, exfil=0,
                 observation=0, sonde=0, controle_perception=0, menace_p5=0, menace_p6=0,
                 instance=INSTANCES[len(L) % len(INSTANCES)], version=f"PRIX-{attente}s-g{paire[0]}g{paire[1]}",
                 note=f"Prix du temps : attente de {attente} s avant la phase 5, hors plafond de phase ( saisine de Fable, 18/09 ).")
        L.append((f"2026-09-18_PRIXV2_{attente}s_g{paire[0]}g{paire[1]}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 3600
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "instance", j["instance"], "attente", j["attente_test"], "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {sum(len(j['graines']) * j['repetitions'] for _, j in L)} episodes")
