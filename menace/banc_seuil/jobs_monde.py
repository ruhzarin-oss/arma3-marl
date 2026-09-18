"""SEUIL-PAR-MONDE-18-09 ( criteres : CRITERES_SEUIL_PAR_MONDE_18-09.md ). --fumee : 2 jobs ; sinon 17 jobs. --poser pour mettre en file."""
import json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
g = json.load(open(f"{H}/queue/faits/2026-09-18_BANC_150m.json"))
assert g["campagne"] == "BANC-PERCEPTION-18-09" and g["controle_perception"] == 5 and g["jour"] == 0
g = {k: v for k, v in g.items() if k != "note"}
INST = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
if "--fumee" in sys.argv:
    CAMPAGNE = "FUMEE-BANC-JOURNAL-18-09"; CAS = [([4, 5], 150, "A"), ([4, 5], 250, "B")]
else:
    CAMPAGNE = "SEUIL-PAR-MONDE-18-09"
    D = {(4, 5): (150, 157, 164, 171), (6, 7): (170, 185, 200, 215), (8, 9): (150, 170, 190, 210), (11, 12): (150, 170, 190, 210)}
    # ! ENTRELACER sur 12 instances ( Younes, 18/09 22 h 10 : « fais tourner sur 14 serveurs » ; la file plafonne a 12, la 9 est le labo,
    # la 0 le gymnase ). Tour 1 : 12 jobs, un par instance. Tour 2 : 4 jobs + le rejeu, chacun sur une instance qui a joue une AUTRE
    # paire de mondes. Les rangs de distance sont meles ( 0, 2, 3 puis 1 ) : aucun tour ne porte que des distances proches.
    P = list(D); RANGS = [0, 2, 3, 1]
    CAS = [(list(P[k % 4]), D[P[k % 4]][RANGS[k // 4]], "", INST[k] if k < 12 else INST[(k - 12 + 1) % 4]) for k in range(16)]
    CAS += [([4, 5], 157, "REJEU", INST[6])]                                                                     # determinisme
L = []
if "--fumee" in sys.argv: CAS = [(m, d, suf, INST[k]) for k, (m, d, suf) in enumerate(CAS)]
for rang, (mondes, d, suf, inst) in enumerate(CAS):
    nom = f"m{mondes[0]}-{mondes[1]}_{d}m" + (f"_{suf}" if suf else "")
    L.append((f"2026-09-18_MONDE_{nom}.json" if CAMPAGNE.startswith("SEUIL") else f"2026-09-18_JOURNAL_{nom}.json",
              dict(g, banc="chacalvue", campagne=CAMPAGNE, instance=inst, graines=mondes, controle_dist=d, observation=600, sonde=1,
                   version=f"MONDE-{nom}", note=f"Seuil par monde, nuit, mondes {mondes}, cible debout a {d} m, fenetre 600 s, sonde 1 s, checkVisibility continu.")))
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
