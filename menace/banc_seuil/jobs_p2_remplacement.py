"""Remplacement des episodes refuses de CHOIX-P2-TYPES-19-09 ( amendement 2 des criteres, ecrit le 17/09 :
« remplacement des episodes refuses par l enregistreur » ). Huit episodes refuses pour hygiene de journal
( 4 canari_tir_journalise, 3 rien_apres_fini ). Un job porte une PAIRE de mondes : on repose donc les jobs
qui contiennent un monde refuse, tels quels, sans rien changer d autre.
Le monde 11 n est PAS repose : ses deux episodes sont ACCEPTES mais compromis avant la decision, ce qui est
deterministe ; il relevera du retrait de monde ( --sans-monde 11 ), l autre amendement."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
REFUSES = [(9, 4, 2, 4), (9, 5, 1, 2), (4, 5, 1, 2), (9, 4, 2, 2), (6, 5, 1, 4), (9, 4, 1, 1), (9, 5, 1, 1), (7, 5, 1, 2)]
besoin = {(m, o, s, tuple(sorted(p))) for w, m, o, s in REFUSES
          for p in ([[4, 5]] if w in (4, 5) else [[6, 7]] if w in (6, 7) else [[8, 9]] if w in (8, 9) else [[11, 12]])}
trouves = {}
for f in sorted(glob.glob(f"{H}/queue/faits/*_P2N_C*.json")):
    j = json.load(open(f))
    if j.get("campagne") != "CHOIX-P2-TYPES-19-09": continue
    cle = (j.get("menace_p2"), j.get("traversee"), j.get("situation"), tuple(sorted(j.get("graines", []))))
    if cle in besoin and cle not in trouves: trouves[cle] = (f, j)
manquants = besoin - set(trouves)
print(f"{len(trouves)} jobs retrouves sur {len(besoin)} ; manquants : {manquants or 'aucun'}")
if manquants: raise SystemExit("job d origine introuvable")
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8]
poser = "--poser" in sys.argv
t0 = time.time() - 3600
for rang, (cle, (f, j)) in enumerate(sorted(trouves.items())):
    j = dict(j, instance=INSTANCES[rang % len(INSTANCES)],
             note="Remplacement des episodes refuses pour hygiene de journal ( amendement 2 des criteres ). Meme reglage, meme graine de situation.")
    nom = os.path.basename(f).replace(".json", "_R.json")
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(f"{nom:52s} instance {j['instance']:2d} mondes {j['graines']} menace {j['menace_p2']} option {j['traversee']} "
          f"sit {j['situation']} : {'OK' if ok else 'REFUS'}")
    if not ok:
        print("\n".join(l for l in r.stdout.splitlines() if "REFUS" in l)); raise SystemExit("controle refuse")
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(trouves)} jobs, {2 * len(trouves)} episodes", "POSES" if poser else "A BLANC")
