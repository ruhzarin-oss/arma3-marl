"""VARIANCE-SITUATION-18-09 : la variance de perception doit venir de la GRAINE DE SITUATION, pas des repetitions.
Mesure du 18/09 ( VARIANCE-PROCHE-18-09, 20 episodes ) : dans un monde donne, les deux repetitions sont identiques -
monde 4 jamais percu, monde 5 toujours. La cause est dans 35_menaces.sqf : CHACAL_RNG_S ne depend que de
CHACAL_SITUATION, de la graine du monde et de la phase. Ici on fait varier CHACAL_SITUATION sur les memes mondes.
4 graines de situation x 2 mondes x 1 repetition = 8 episodes, vignette P2 niveau 5 ( un seul type, pose pres )."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "VARIANCE-SITUATION-18-09"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-18_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "VARIANCE-PROCHE-18-09" and g.get("version") == "VP-P2_TYPE2":
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit VP-P2_TYPE2 introuvable")
L = []
for rang, s in enumerate((1, 2, 3, 4)):
    j = dict(g, campagne=CAMPAGNE, graines=[4, 5], repetitions=1, situation=s, instance=rang + 1,
             version=f"VS-P2_TYPE2_s{s}",
             note=f"Variance par graine de situation : meme mondes, situation={s}, pour voir si le placement change la perception au choix.")
    L.append((f"2026-09-18_VS_P2_TYPE2_s{s}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 3600
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "instance", j["instance"], "situation", s, "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
    if not ok: raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {sum(len(j['graines']) * j['repetitions'] for _, j in L)} episodes", "POSES" if poser else "A BLANC")
