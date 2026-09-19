"""Fumee des deux nouvelles perceptions ( menace_mobile_vue, moteur_entendu ) sur bancs/chacaloracle, Oracle a 0.
Attentes ECRITES AVANT :
  a. 0 erreur SQF, episodes ACCEPTE, ligne de decision TRAVERSEE presente ;
  b. moteur_entendu = 1 dans au moins un episode du bras PATROUILLE ;
  c. moteur_entendu = 0 dans TOUS les episodes du bras POSTE ( un poste a pied n a pas de moteur ) ;
  d. menace_mobile_vue vaut 0 ou 1 - et non -1 - dans au moins un episode ou une menace est vue.
Un seul echec et rien ne part."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    g = json.load(open(jf))
    if g.get("campagne") == "CHOIX-P2-TYPES-19-09" and g.get("menace_p2") == 4 and g.get("traversee") == 2:
        g = {k: v for k, v in g.items() if k != "note"}; break
else:
    raise SystemExit("gabarit P2 introuvable")
L = []
for rang, menace in enumerate((4, 5)):
    j = dict(g, banc="chacaloracle", campagne="FUMEE-PERCEPTION-19-09", graines=[4, 5], repetitions=1, situation=1,
             menace_p2=menace, traversee=2, oracle_cmd=0, portee_son=600, instance=[10, 11][rang],
             version=f"FUMEE-PERCEPTION-{'PATROUILLE' if menace == 4 else 'POSTE'}",
             note=f"Fumee des perceptions mobilite vue et moteur entendu, bras {'patrouille' if menace == 4 else 'poste'}, Oracle a 0.")
    L.append((f"2026-09-19_FUMEE_PERCEPTION_m{menace}.json", j))
poser = "--poser" in sys.argv
t0 = time.time() - 3600
for rang, (nom, j) in enumerate(L):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    ok = "CONTROLE OK" in r.stdout
    print(nom, "banc", j["banc"], "instance", j["instance"], "menace_p2", j["menace_p2"], ":", "OK" if ok else "REFUS")
    if not ok:
        print("\n".join(l for l in r.stdout.splitlines() if "REFUS" in l)); raise SystemExit(1)
    if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
    else: os.remove(prep)
print(f"{len(L)} jobs, {2 * len(L)} episodes", "POSES" if poser else "A BLANC")
