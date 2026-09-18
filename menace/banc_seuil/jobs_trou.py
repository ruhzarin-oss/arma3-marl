"""Banc de perception, le trou 150-300 m de nuit et le jour ( 18/09, criteres : en-attente/CRITERES_BANC_TROU_18-09.md ).
Meme gabarit que menace/jobs_banc.py ; seuls controle_dist et jour changent. --poser pour mettre en file."""
import json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "BANC-TROU-18-09"
g = json.load(open(f"{H}/queue/faits/2026-09-18_BANC_150m.json"))
assert g["campagne"] == "BANC-PERCEPTION-18-09" and g["controle_perception"] == 5 and g["observation"] == 300
g = {k: v for k, v in g.items() if k != "note"}
NUIT = (225, 200, 250, 175, 275); JOUR = (300, 600, 150, 450, 800)
L = []
for rang in range(5):
    for inst, jour, d in ((1, 0, NUIT[rang]), (2, 1, JOUR[rang])):
        nom = "NUIT" if jour == 0 else "JOUR"
        j = dict(g, campagne=CAMPAGNE, instance=inst, jour=jour, controle_dist=d, version=f"TROU-{nom}-{d}m",
                 note=f"Banc de perception, {nom.lower()} : cible debout a {d} m, ligne de vue verifiee, regardee par tous les hommes.")
        L.append((f"2026-09-18_TROU_{nom}_{d}m.json", j))
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True)
t0 = time.time() - 7200
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "instance", j["instance"], "jour", j["jour"], "dist", j["controle_dist"],
          "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print("POSES" if poser else "A BLANC : rien pose")
