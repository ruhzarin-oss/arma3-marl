"""Verification de variance avec les types SEPARES mais PROCHES ( niveaux 4 et 5 ) : 5 jobs, 20 episodes.
Meme critere qu au plan v2 : menace_percue > 0 dans 30 a 70 % des episodes au moment du choix."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "VARIANCE-PROCHE-18-09"
INST = [1, 2, 3, 4, 5]
G = {}
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1[78]_*/job.json")):
    j = json.load(open(jf))
    for c, f in (("P2", lambda x: x.get("campagne") == "CHOIX-P2-17-09" and x.get("traversee") == 1),
                 ("P1", lambda x: x.get("campagne") == "CHOIX-P1-17-09" and x.get("p1_attente") == 1),
                 ("P4", lambda x: x.get("campagne") == "CHOIX-P4-17-09" and x.get("itineraire") == 1)):
        if c not in G and f(j): G[c] = {k: v for k, v in j.items() if k != "note"}
assert len(G) == 3, G.keys()
CAS = [("P2_TYPE2", "P2", dict(menace_p2=5)), ("P1_TYPE1", "P1", dict(menace_p1=4)), ("P1_TYPE2", "P1", dict(menace_p1=5)),
       ("P4_TYPE1", "P4", dict(menace_p4=4)), ("P4_TYPE2", "P4", dict(menace_p4=5))]
L = []
for i, (nom, phase, ch) in enumerate(CAS):
    j = dict(G[phase], campagne=CAMPAGNE, graines=[4, 5], repetitions=2, observation=90, sonde=0, controle_perception=0,
             menace_p1=0, menace_p2=0, menace_p3=0, menace_p4=0, menace_p5=0, menace_p6=0, attente_test=0,
             instance=INST[i], version=f"VP-{nom}", note=f"Variance avec type separe mais proche ( niveaux 4 et 5 ) : {nom}.")
    j.update(ch)
    L.append((f"2026-09-18_VP_{nom}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 3600
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "instance", j["instance"], "m1/m2/m4", j["menace_p1"], j["menace_p2"], j["menace_p4"], "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
