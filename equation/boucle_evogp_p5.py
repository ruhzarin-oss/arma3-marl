"""
Boucle Arma <-> EvoGP sur le delai du porteur ( equation/PROTOCOLE_BOUCLE_EVOGP_P5.md ).
Un tour : apprendre sur les episodes d'exploration -> poser 12 jobs sur 12 serveurs ( 4 a 45 s, 4 a 180 s, 4 formule ) -> attendre ->
verifier que chaque episode FORMULE a joue exactement la formule -> journal. Arret : fichier STOP, N_TOURS, ou faute.
  /mnt/data/hmt/evogp/env/bin/python boucle_evogp_p5.py [ --fumee ] [ --tours 12 ]
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time
import numpy as np
import architecte_evogp as A
from formule import evaluer_codes

H = "/mnt/data/hmt"
CAMPAGNE = "BOUCLE-EVOGP-P5-17-09"
PILOTE = "PILOTE-P5-DELAI-SITUATION-16-09"
INSTANCE = 1                                            # fumee
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]    # tours : 12 serveurs ( Younes, 17/09 : « lance sur 12 serveurs » )
R_TOUR = 4                                              # repetitions par job : 2 mondes x 4 = 8 episodes, ~1 h
MONDES = [4, 5, 6, 7, 8, 11, 12]                      # le monde 9 est retire : son canari fait refuser l'episode
DOSSIER = f"{H}/equation/boucle"
JOURNAL = f"{DOSSIER}/journal.jsonl"
STOP = f"{DOSSIER}/STOP"
RX_ERREUR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
RX_DEC = re.compile(r'"CHACAL\|E\|decision\|([^"]*\|point\|DELAI_PORTEUR\|[^"]*)"')
RX_FINI = re.compile(r'"CHACAL\|FINI\|([^"]*)"')


def champs(texte):
    p = texte.split("|")
    return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def episodes(campagnes):
    """Lit les episodes directement dans les runs : perceptions, choix, decideur, issue ( 3 charges et >= 6 vivants )."""
    out = []
    for jf in glob.glob(f"{H}/runs/2026-09-[12][0-9]_*/job.json"):
        try: j = json.load(open(jf))
        except Exception: continue
        if j.get("campagne") not in campagnes: continue
        for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
            try:
                verdict = json.load(open(d + "resultat.json")).get("verdict")
                rpt = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            md, mf = RX_DEC.search(rpt), RX_FINI.search(rpt)
            if not md or not mf: continue
            dec, fini = champs(md.group(1)), champs(mf.group(1))
            try:
                x = [float(dec[k]) for k in A.PERCEPTIONS]
                choix = int(float(dec["choix"]))
                Y = int(int(fini["charges"]) == 3 and int(fini["vivants"]) >= 6)
            except Exception:
                continue
            out.append(dict(campagne=j["campagne"], version=j.get("version", ""), dossier=d, monde=int(re.match(r"g(\d+)", os.path.basename(d.rstrip("/"))).group(1)),
                            bras="MENACE" if j.get("menace_p5", 0) > 0 else "TEMOIN", decideur=dec.get("decideur"), choix=choix,
                            a=int(choix == 180), x=x, Y=Y, verdict=verdict, erreurs=len(RX_ERREUR.findall(rpt)),
                            valeur_formule=float(dec["valeur_formule"]) if "valeur_formule" in dec else None,
                            codes_lus=int(dec["codes_lus"]) if "codes_lus" in dec else None,
                            codes=[j.get(f"f{k}", 0) for k in range(int(j.get("f_len", 0)))]))
    return out


def verifier_formules(eps):
    """Chaque episode FORMULE doit avoir joue exactement la formule du job, sur les perceptions ecrites."""
    fautes = []
    for e in eps:
        if e["decideur"] != "FORMULE": continue
        v = evaluer_codes(e["codes"], e["x"])
        attendu = 180 if v > 0 else 45
        if e["choix"] != attendu or e["codes_lus"] != len(e["codes"]) or abs(e["valeur_formule"] - v) > 1e-3 * max(1, abs(v)):
            fautes.append(dict(dossier=e["dossier"], choix=e["choix"], attendu=attendu, valeur_mission=e["valeur_formule"], valeur_python=v,
                               codes_lus=e["codes_lus"], codes=len(e["codes"])))
    return fautes


def gabarit():
    for jf in sorted(glob.glob(f"{H}/runs/2026-09-16_*/job.json")):
        j = json.load(open(jf))
        if j.get("campagne") == PILOTE:
            return j
    raise SystemExit("gabarit du pilote introuvable")


def poser(nom, job, rang):
    prep = f"{H}/queue_preparation/{nom}"
    json.dump(job, open(prep, "w"), indent=1, ensure_ascii=True)
    r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
    if "CONTROLE OK" not in r.stdout:
        raise SystemExit(f"CONTROLE REFUSE {nom} :\n{r.stdout[-1500:]}\n{r.stderr[-500:]}")
    t = time.time() - 3600 + rang
    os.utime(prep, (t, t))
    shutil.move(prep, f"{H}/queue/{nom}")


def declencher(n=1, pause=25):
    for _ in range(n):
        try: subprocess.run(["/mnt/c/Windows/System32/schtasks.exe", "/run", "/tn", "HMT_RUN"], capture_output=True, timeout=60)
        except Exception: pass
        if n > 1: time.sleep(pause)


def en_file(nom):
    return os.path.exists(f"{H}/queue/{nom}")


def fini(nom):
    try: return f"FINI {nom}" in open(f"{H}/etat/file.log", encoding="utf-8", errors="ignore").read()
    except Exception: return False


def journal(ligne):
    ligne["heure"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(JOURNAL, "a") as f: f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    print(json.dumps(ligne, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tours", type=int, default=12)
    ap.add_argument("--fumee", action="store_true", help="un seul job FORMULE de 2 episodes, puis verification et arret")
    o = ap.parse_args()
    global JOURNAL
    os.makedirs(DOSSIER, exist_ok=True)
    if o.fumee:
        JOURNAL = f"{DOSSIER}/journal_fumee.jsonl"
    g = gabarit()
    deja = [json.loads(l)["tour"] for l in open(JOURNAL)] if os.path.exists(JOURNAL) else []
    debut = (max(deja) + 1) if deja else 0
    for tour in range(debut, 1 if o.fumee else o.tours):
        if os.path.exists(STOP):
            journal(dict(tour=tour, evenement="STOP trouve, arret")); return
        eps = episodes({PILOTE, CAMPAGNE})
        propres = [e for e in eps if e["verdict"] == "ACCEPTE" and e["erreurs"] == 0]
        fautes = verifier_formules([e for e in propres if e["campagne"] == CAMPAGNE])
        if fautes:
            journal(dict(tour=tour, evenement="FAUTE : une formule n'a pas ete jouee comme calculee, arret", fautes=fautes[:5])); return
        explo = [e for e in propres if e["decideur"] == "IMPOSE"]
        X = np.array([e["x"] for e in explo]); a = np.array([e["a"] for e in explo]); Y = np.array([e["Y"] for e in explo])
        m = np.array([e["monde"] for e in explo])
        t0 = time.time()
        res = A.apprendre(X, a, Y, m, 20260917 + tour)
        form = [e for e in propres if e["campagne"] == CAMPAGNE and e["decideur"] == "FORMULE"]
        boucle_explo = [e for e in explo if e["campagne"] == CAMPAGNE]
        taux = lambda L: (round(float(np.mean([e["Y"] for e in L])), 3), len(L)) if L else (None, 0)
        journal(dict(tour=tour, evenement="formule apprise", duree_apprentissage_s=round(time.time() - t0),
                     episodes_exploration=len(explo), dont_boucle=len(boucle_explo), episodes_formule=len(form),
                     parcimonie=res["parcimonie"], formule=res["formule"], codes=res["codes"], gain_croise=res["rapport"],
                     reussite_formule=taux(form), reussite_explo_45=taux([e for e in boucle_explo if e["choix"] == 45]),
                     reussite_explo_180=taux([e for e in boucle_explo if e["choix"] == 180]),
                     formule_a_joue_180=sum(e["choix"] == 180 for e in form)))
        base = {k: v for k, v in g.items() if not re.fullmatch(r"f\d+", k)}
        codes = res["codes"]
        jobs = []
        if o.fumee:
            w = [4, 5]
            b = dict(base, campagne="FUMEE-BOUCLE-EVOGP-17-09", instance=INSTANCE, graines=w, repetitions=1, menace_p5=3)
            jobs.append(("2026-09-17_BOUCLE_FUMEE_FORMULE.json",
                         dict(b, delai_mode=1, delai_porteur=45, f_len=len(codes), **{f"f{k}": c for k, c in enumerate(codes)},
                              version="FUMEE-BOUCLE-FORMULE", note=f"Fumee de la boucle EvoGP : formule {res['formule']}.")))
        else:
            for grp in range(4):
                menace = 3 if grp % 2 == 0 else 0
                k = tour * 4 + grp
                w = [MONDES[(2 * k) % len(MONDES)], MONDES[(2 * k + 1) % len(MONDES)]]
                b = dict(base, campagne=CAMPAGNE, graines=w, repetitions=R_TOUR, menace_p5=menace, delai_mode=0, f_len=0)
                for t, genre in enumerate(("E45", "E180", "FORMULE")):
                    inst = INSTANCES[grp * 3 + t]
                    if genre == "FORMULE":
                        job = dict(b, instance=inst, delai_mode=1, delai_porteur=45, f_len=len(codes), **{f"f{i}": c for i, c in enumerate(codes)},
                                   note=f"Boucle EvoGP tour {tour} : formule {res['formule']} ( parcimonie {res['parcimonie']} ), menace_p5 {menace}.")
                    else:
                        job = dict(b, instance=inst, delai_porteur=int(genre[1:]),
                                   note=f"Boucle EvoGP tour {tour} : exploration, delai impose {genre[1:]} s, menace_p5 {menace}.")
                    job["version"] = f"BOUCLE-T{tour:02d}-{genre}-M{menace}-g{w[0]}g{w[1]}"
                    jobs.append((f"2026-09-17_BOUCLE_T{tour:02d}_G{grp}_{genre}.json", job))
        for rang, (nom, job) in enumerate(jobs):
            poser(nom, job, rang)
        declencher(n=len(jobs) + 2)
        journal(dict(tour=tour, evenement="jobs poses", jobs=[n for n, _ in jobs], versions=[j["version"] for _, j in jobs]))
        t0 = time.time()
        while not all(fini(n) for n, _ in jobs):
            if time.time() - t0 > 5 * 3600:
                journal(dict(tour=tour, evenement="ATTENTE DEPASSEE ( 5 h ), arret")); return
            if os.path.exists(STOP):
                journal(dict(tour=tour, evenement="STOP trouve pendant l'attente, arret apres ces jobs")); return
            if any(en_file(n) for n, _ in jobs):
                declencher(1)                     # HMT_RUN ne prend qu'un job par declenchement
            time.sleep(120)
        if o.fumee:
            eps = [e for e in episodes({"FUMEE-BOUCLE-EVOGP-17-09"})]
            journal(dict(tour=tour, evenement="fumee finie", episodes=[{k: e[k] for k in ("monde", "decideur", "choix", "x", "valeur_formule", "codes_lus", "verdict", "erreurs", "Y")} for e in eps],
                         fautes=verifier_formules(eps)))
            return


if __name__ == "__main__":
    main()
