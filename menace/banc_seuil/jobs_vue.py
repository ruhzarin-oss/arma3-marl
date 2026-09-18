"""Fumee de patch_banc_vue_fine ( criteres : en-attente/ACCEPTATION_BANC_VUE_FINE.md ). 3 jobs x 2 mondes, banc chacalvue."""
import json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "FUMEE-BANC-VUE-FINE-18-09"
g = json.load(open(f"{H}/queue/faits/2026-09-18_BANC_150m.json"))
assert g["campagne"] == "BANC-PERCEPTION-18-09" and g["controle_perception"] == 5 and g["jour"] == 0
g = {k: v for k, v in g.items() if k != "note"}
CAS = (("POSITIF", 2, 100, "positif : nuit, 100 m, doit etre connue en 10 s ou moins"),
       ("CAS225", 3, 225, "le cas qui echouait : nuit, 225 m, 0 ligne de vue sur 2 avant le patch"),
       ("NEGATIF", 4, 60000, "negatif : distance hors carte, aucun candidat possible, attendu banc_refuse + VOID rapide"))
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - 7200
for rang, (nom, inst, d, note) in enumerate(CAS):
    j = dict(g, banc="chacalvue", campagne=CAMPAGNE, instance=inst, controle_dist=d, version=f"VUE-{nom}", note="Fumee banc_vue_fine, " + note)
    f = f"2026-09-18_VUE_{nom}.json"; prep = f"{H}/queue_preparation/{f}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(f, "instance", inst, "dist", d, "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print("POSES" if poser else "A BLANC : rien pose")
