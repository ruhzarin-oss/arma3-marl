"""BANC-SEUIL-18-09 ( criteres : en-attente/CRITERES_BANC_SEUIL_18-09.md ). 9 jobs x 2 mondes, banc chacalvue, instances 2 3 4."""
import json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "BANC-SEUIL-18-09"
g = json.load(open(f"{H}/queue/faits/2026-09-18_BANC_150m.json"))
assert g["campagne"] == "BANC-PERCEPTION-18-09" and g["controle_perception"] == 5 and g["jour"] == 0
g = {k: v for k, v in g.items() if k != "note"}
BRAS = ((2, 0, [4, 5], (160, 155, 165)), (3, 0, [6, 7], (150, 175, 200)), (4, 1, [4, 5], (150, 300, 200)))
L = []
for rang in range(3):
    for inst, jour, graines, dists in BRAS:
        d = dists[rang]; nom = ("JOUR" if jour else "NUIT") + f"_m{graines[0]}{graines[1]}_{d}m"
        L.append((f"2026-09-18_SEUIL_{nom}.json", dict(g, banc="chacalvue", campagne=CAMPAGNE, instance=inst, jour=jour, graines=graines,
                  controle_dist=d, version=f"SEUIL-{nom}", note=f"Seuil de perception, {'jour' if jour else 'nuit'}, mondes {graines}, cible debout a {d} m, banc a recherche fine.")))
poser = "--poser" in sys.argv
os.makedirs(f"{H}/queue_preparation", exist_ok=True); t0 = time.time() - 7200
for rang, (f, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{f}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(f, "instance", j["instance"], "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{f}")
    else: os.remove(prep)
print("POSES" if poser else "A BLANC : rien pose")
