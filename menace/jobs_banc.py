"""Banc de perception ( 18/09 ) : de nuit, cible posee a 50, 100, 150, 300 et 600 m, ligne de vue verifiee, REGARDEE
par tous les hommes ; fenetre de 300 s, une ligne toutes les 5 s. 5 jobs x 2 mondes = 10 episodes."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "BANC-PERCEPTION-18-09"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-17_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CHOIX-P2-17-09" and g.get("traversee") == 1:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit introuvable")
L = []
for i, d in enumerate((50, 100, 150, 300, 600)):
    j = dict(g, campagne=CAMPAGNE, graines=[4, 5], repetitions=1, observation=300, sonde=1, controle_perception=5,
             controle_dist=d, jour=0, menace_p1=0, menace_p2=0, menace_p3=0, menace_p4=0, menace_p5=0, menace_p6=0,
             instance=[1, 2, 3, 4, 5][i], version=f"BANC-{d}m",
             note=f"Banc de perception de nuit : cible debout a {d} m, ligne de vue verifiee, regardee par tous les hommes.")
    L.append((f"2026-09-18_BANC_{d}m.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 7200
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "instance", j["instance"], "dist", j["controle_dist"], "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
