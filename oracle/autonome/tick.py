"""UN TOUR DE LA BOUCLE DE L ORACLE. Lance toutes les 5 minutes par la tache Windows HMT_ORACLE ; chaque tour fait au plus une
etape de la machine a etats, puis rend la main. L etat vit sur disque : un plantage, un redemarrage ou une coupure
reprennent exactement la ou on en etait.
  REPOS -> POSE -> VOL -> LECTURE -> ( REPARATION -> VOL -> LECTURE ) -> APPRENTISSAGE -> REPOS
  python -m oracle.autonome.tick            un tour
  python -m oracle.autonome.tick --a-blanc  imagine et controle une iteration SANS rien poser
  python -m oracle.autonome.tick --etat     affiche l etat"""
import fcntl, json, os, shutil, subprocess, sys, time
import numpy as np
from scipy.stats import fisher_exact
from . import config as C, donnees as Dn, gardes as G, monde as M, architecte as A, generateur as Gen, motifs as Mo, multiplexeur as Mx

ETAT = f"{C.ETAT_DIR}/etat.json"
JOURNAL = f"{C.ETAT_DIR}/journal.md"


def charger():
    if os.path.exists(ETAT): return json.load(open(ETAT))
    return dict(phase="REPOS", iteration=0, campagne=None, propositions=[], jobs=[], empreinte=None, reparations=0,
                quarantaines_suite=0, sans_piege_suite=0, imagination_pire_suite=0, historique=[], a_confirmer=[],
                confirmes=[], infirmes=[], arret=None)


def sauver(e):
    os.makedirs(C.ETAT_DIR, exist_ok=True); tmp = ETAT + ".tmp"; json.dump(e, open(tmp, "w"), indent=1); os.replace(tmp, ETAT)


def journal(txt):
    os.makedirs(C.ETAT_DIR, exist_ok=True)
    with open(JOURNAL, "a") as f: f.write(txt.rstrip() + "\n")


def arreter(etat, raison):
    etat["arret"] = raison; sauver(etat)
    journal(f"\n**⛔ ARRET {time.strftime('%d/%m %H:%M')} : {raison}**\n"); print("ARRET", raison)


def est_oracle(c): return str(c or "").startswith(C.PREFIXES_HISTORIQUES)


def historique_propre(etat):
    """Episodes utilisables pour apprendre : l historique admissible + les iterations de l Oracle NON quarantainees."""
    sales = {h["campagne"] for h in etat["historique"] if h.get("quarantaine")}
    E = Dn.utilisables(Dn.episodes(lambda c: not (est_oracle(c) and c in sales)))
    return E


def deja_joue():
    return {(Gen.cle({k: e[k] for k in C.ARMES}), e["graine"], e["option_imposee"])
            for e in Dn.episodes(est_oracle) if e["verdict"] is not None}


def gabarit():
    import glob
    for jf in sorted(glob.glob(f"{C.RUNS}/2026-09-2*/job.json")):
        j = json.load(open(jf))
        if j.get("campagne") == "CALIBRATION-P2-V2-21-09" and j.get("oracle_cmd") == 1:
            return {k: v for k, v in j.items() if k != "note"}
    raise RuntimeError("gabarit introuvable")


def construire_jobs(etat, propositions):
    g0, jobs, rang = gabarit(), [], 0
    for k, p in enumerate(propositions):
        reps = C.REPETITIONS_CONFIRMATION if p["genre"] == "confirmation" else 1
        for o in (1, 2):
            for r in range(reps):
                j = dict(g0)
                j.update(p["situation"]); j.update(campagne=etat["campagne"], graines=list(p["graines"]), traversee=o,
                                                   oracle_ctrl=0, echelle=100, depart=2, arret=2,
                                                   instance=C.INSTANCES[rang % len(C.INSTANCES)],
                                                   version=f"ORA-{etat['iteration']:03d}-c{k:02d}-o{o}-r{r}",
                                                   note=f"Oracle autonome, iteration {etat['iteration']}, {p['genre']}, candidat {k}, option {o}.")
                jobs.append(j); rang += 1
    return jobs


def poser_jobs(jobs, a_blanc=False):
    t0 = time.time() - 10800; poses, refus = [], []
    for rang, j in enumerate(jobs):
        nom = f"{time.strftime('%Y-%m-%d')}_{j['version'].replace('-', '_')}.json"
        prep = f"{C.PREP}/{nom}"; json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
        ok, msg = G.controle_job(prep)
        if not ok: refus.append((nom, msg)); os.remove(prep); continue
        if a_blanc: os.remove(prep); poses.append(nom); continue
        # le multiplexeur ( 22/09 ) : les jobs vont dans queue/multiplexes/, jamais directement a la ferme
        dest = Mx.MUX if C.MULTIPLEXE else C.QUEUE
        os.makedirs(dest, exist_ok=True)
        os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{dest}/{nom}"); poses.append(nom)
    if C.MULTIPLEXE and poses and not a_blanc: Mx.empaqueter()
    return poses, refus


def candidat_de(e):
    try: return int(e["version"].split("-c")[1][:2])
    except Exception: return None


# ------------------------------------------------------------------------------------------------ la moitie Architecte
def architecte_en_cours():
    f = f"{C.ETAT_DIR}/architecte.pid"
    if not os.path.exists(f): return False
    try: os.kill(int(open(f).read().strip()), 0); return True
    except Exception: return False


def lancer_architecte(etat):
    """L Architecte reapprend EN ARRIERE-PLAN ( EvoGP sur la 3090, environ une heure ) : un tour ne dure que quelques
    secondes, on ne l y enferme pas. Son resultat est lu au debut d un tour de repos suivant."""
    if C.CONFIRMATION_ATTENDRE:
        journal("- l Architecte ne reapprend pas : confirmation de « toujours attendre » en cours, un seul regard a 480 paires"); return
    if architecte_en_cours(): journal("- l Architecte reapprend deja : pas de second lancement"); return
    log = open(f"{C.ETAT_DIR}/architecte.log", "a")
    p = subprocess.Popen([sys.executable, "-m", "oracle.autonome.architecte_apprend"], cwd=C.DEPOT, stdout=log, stderr=log,
                         start_new_session=True)
    open(f"{C.ETAT_DIR}/architecte.pid", "w").write(str(p.pid))
    journal(f"- 🏛️ l Architecte se remet a apprendre sur tous les episodes, pieges de l Oracle compris ( processus {p.pid} )")


def appliquer_architecte(etat):
    """Si l Architecte a fini d apprendre : il ne change de regle que si la nouvelle bat l ancienne sur des mondes neufs."""
    f = f"{C.ETAT_DIR}/architecte_resultat.json"
    if not os.path.exists(f): return
    try: r = json.load(open(f))
    except Exception: return
    if not r.get("fini") or r.get("id") in etat.setdefault("architecte_vus", []): return
    etat["architecte_vus"].append(r["id"])
    with open(f"{C.ETAT_DIR}/architecte_historique.jsonl", "a") as h: h.write(json.dumps(r) + "\n")
    cands = " | ".join(f"{k} {v['valeur']:.3f} ( ecart {v['ecart_a_la_courante']:+.3f} [{v['ic'][0]:+.3f} ; {v['ic'][1]:+.3f}] )"
                       for k, v in r["candidats"].items())
    if C.CONFIRMATION_ATTENDRE:
        journal(f"- resultat de l Architecte ( {r['id']} ) MIS DE COTE, jamais installe : confirmation en cours ( un seul regard ). {cands}")
        sauver(etat); return
    if r["adoptee"]:
        tmp = f"{C.ETAT_DIR}/architecte.json.tmp"; json.dump(r["regle"], open(tmp, "w"), indent=1)
        os.replace(tmp, f"{C.ETAT_DIR}/architecte.json")
        journal(f"\n**🏛️ L ARCHITECTE CHANGE DE REGLE** ( {time.strftime('%d/%m %H:%M')} ) : « {r['texte']} ». "
                f"Compromission si on la suit, sur mondes neufs : {r['candidats'][r['meilleur']]['valeur']:.3f} contre "
                f"{r['valeur_courante']:.3f} pour « {r['courante']} ». L Oracle chasse desormais les failles de CETTE regle.\n"
                f"- candidats : {cands}")
    else:
        journal(f"- l Architecte garde sa regle « {r['courante']} » : aucun candidat ne la bat sur des mondes neufs. {cands}")
    sauver(etat)


# ------------------------------------------------------------------------------------------------ les etapes
def etape_repos(etat, a_blanc=False):
    if not G.file_vide(): print("ATTENTE : la file n est pas vide ( une autre campagne vole ), l Oracle ne pose rien"); return
    if not G.depot_propre(): print("ATTENTE : depot non commite ( bancs, outils ou oracle/autonome )"); return
    if not a_blanc: appliquer_architecte(etat)            # la regle a attaquer est celle que l Architecte vient d adopter
    if not a_blanc:
        etat["iteration"] += 1
    it = etat["iteration"] if not a_blanc else etat["iteration"] + 1
    etat["campagne"] = f"{C.PREFIXE_CAMPAGNE}{it:03d}"
    E = historique_propre(etat)
    monde = M.Monde().apprendre(E)
    saine, raisons, sante = G.imagination_saine(monde, E)          # amendement 2 : intercepter une imagination cassee
    if not saine:
        if a_blanc: print("A BLANC - IMAGINATION MALADE :", raisons); return
        arreter(etat, "avant d imaginer : " + " ; ".join(raisons) + f" ( mesures {sante} )"); return
    regle = A.charger()
    props, bilan = Gen.proposer(monde, regle, E, deja_joue(), etat["a_confirmer"], np.random.default_rng(C.GRAINE + it))
    fautes = [f"candidat {k} : {f}" for k, p in enumerate(props) for f in G.armes_permises(p)]
    jobs = construire_jobs(etat, props)
    n_ep = 2 * len(jobs)
    fautes += G.budget(etat, n_ep)
    if fautes:
        if a_blanc: print("A BLANC - GARDE-FOUS EN ECHEC :", fautes); return
        arreter(etat, "garde-fou avant le vol : " + " ; ".join(fautes)); return
    poses, refus = poser_jobs(jobs, a_blanc=a_blanc)
    if refus:
        if a_blanc: print("A BLANC - REFUS DU CONTROLE :", refus[:3]); return
        arreter(etat, f"controle_avant_run a refuse {len(refus)} job(s) : {refus[0]}"); return
    resume = (f"\n## Iteration {it} — {time.strftime('%d/%m %H:%M')}{' ( A BLANC )' if a_blanc else ''}\n"
              f"Regle lue : `{regle}`. Appris sur {len(E)} episodes ( compromission {monde.taux:.3f} ). "
              f"Imagination saine : predit {sante['prediction_moyenne']:.3f} pour {sante['taux_reel']:.3f}, ecart-type {sante['ecart_type']:.3f}, "
              f"Brier {sante['brier']:.4f} contre {sante['brier_constante']:.4f}. "
              f"{bilan['imagines']} situations imaginees, {bilan['pieges_imagines']} pieges jouables imagines, regret max {bilan['regret_max']:.3f} ; "
              f"{bilan['valeurs_jamais_essayees']} valeurs d armes jamais essayees, {bilan['reste_a_explorer_apres']} apres ce lot.\n"
              + "\n".join(f"- {p['genre']:<12} {p['situation']} graines {p['graines']}"
                          + (f" : risque traverser {p['risque_traverser']:.2f}, attendre {p['risque_attendre']:.2f}, regret {p['regret_imagine']:.2f}, "
                             f"incertitude {p['incertitude']:.2f}, nouveaute {p['nouveaute']:.0f}" if p.get("risque_traverser") is not None else "")
                          for p in props)
              + f"\n{len(poses)} jobs, {n_ep} episodes.")
    if a_blanc: print(resume); print("A BLANC : tous les garde-fous et controles passent, RIEN n a ete pose."); return
    etat.update(phase="VOL", propositions=props, jobs=poses, empreinte=G.empreinte_mission(), reparations=0,
                # « l equation tient » ne se compte que lorsqu il ne reste plus rien a explorer : tant que des armes n ont
                # jamais ete essayees, l absence de piege imagine dit seulement que l imagination ne sait pas
                sans_piege_suite=(etat["sans_piege_suite"] + 1) if (bilan["pieges_imagines"] == 0 and bilan["valeurs_jamais_essayees"] == 0) else 0)
    etat["historique"].append(dict(iteration=it, campagne=etat["campagne"], debut_ts=time.time(), n_jobs=len(poses),
                                   n_episodes=n_ep, **bilan))
    sauver(etat); journal(resume); print(f"POSE iteration {it} : {len(poses)} jobs")


def etape_vol(etat):
    if G.empreinte_mission() != etat["empreinte"]:
        etat["historique"][-1]["mission_modifiee_en_vol"] = True
        journal("- ⚠️ la mission a change pendant le vol : l iteration sera mise en quarantaine")
    import glob
    att = [f for f in glob.glob(f"{C.QUEUE}/*.json") if os.path.basename(f) in etat["jobs"]]
    vol_tous = len(glob.glob(f"{C.EN_COURS}/*.json"))
    vol = [f for f in glob.glob(f"{C.EN_COURS}/*.json") if os.path.basename(f) in etat["jobs"]]
    mux = Mx.en_vol(etat["jobs"]) if C.MULTIPLEXE else []
    att_mux = glob.glob(f"{C.QUEUE}/*MUX_*.json")
    a_nourrir = len(att) + len(att_mux)
    if a_nourrir and vol_tous < C.VOL_MAX: print(f"NOURRIR {min(C.VOL_MAX - vol_tous, a_nourrir)}")
    if not att and not vol and not mux: etat["phase"] = "LECTURE"; sauver(etat); print("VOL TERMINE")
    else: print(f"VOL : {len(vol)} en vol, {len(att)} en attente, {len(mux)} dans le multiplexeur ( {len(att_mux)} jobs multiples en attente )")


def etape_lecture(etat):
    E = Dn.episodes(lambda c: c == etat["campagne"])
    for e in E: e["candidat"] = candidat_de(e)
    q, arret, raisons = G.verifier_apres_vol(E, etat["campagne"])
    if etat["historique"][-1].get("mission_modifiee_en_vol"): q = True; raisons.append("mission modifiee pendant le vol")
    if arret: etat["historique"][-1].update(quarantaine=True, raisons=raisons); arreter(etat, "apres le vol : " + " ; ".join(raisons)); return
    vides = G.cases_vides(E, etat["propositions"])
    if vides and etat["reparations"] == 0 and not q:
        etat["reparations"] = 1
        props = [etat["propositions"][k] for k in sorted({k for k, _ in vides})]
        jobs = [j for j in construire_jobs(etat, etat["propositions"]) if (candidat_de(j), j["traversee"]) in set(vides)]
        for j in jobs: j["version"] += "-rep"
        poses, refus = poser_jobs(jobs)
        etat["jobs"] += poses; etat["phase"] = "VOL"; sauver(etat)
        journal(f"- reparation : {len(vides)} case(s) vide(s) rejouee(s), {len(poses)} job(s)"); print(f"REPARATION {len(poses)} jobs"); return
    etat["historique"][-1].update(quarantaine=q, raisons=raisons, cases_vides=len(vides))
    etat["quarantaines_suite"] = etat["quarantaines_suite"] + 1 if q else 0
    if q: journal(f"- **quarantaine** : {' ; '.join(raisons)} — on n apprend rien de cette iteration")
    if etat["quarantaines_suite"] >= C.ARRET_QUARANTAINES:
        arreter(etat, f"{etat['quarantaines_suite']} iterations en quarantaine de suite"); return
    etat["phase"] = "APPRENTISSAGE"; sauver(etat); print("LECTURE FAITE", "( quarantaine )" if q else "")


def etape_apprentissage(etat):
    h = etat["historique"][-1]
    if not h.get("quarantaine"):
        E_it = Dn.utilisables(Dn.episodes(lambda c: c == etat["campagne"]))
        for e in E_it: e["candidat"] = candidat_de(e)
        # 1. L IMAGINATION AVAIT-ELLE VU JUSTE ? modele appris SANS cette iteration, juge sur elle
        E_avant = [e for e in historique_propre(etat) if e["campagne"] != etat["campagne"]]
        m = M.Monde().apprendre(E_avant)
        saine, raisons, sante = G.imagination_saine(m, E_avant)
        if not saine: arreter(etat, "au moment de juger l imagination : " + " ; ".join(raisons)); return
        mu, _ = m.predire([{k: e[k] for k in C.ARMES} for e in E_it], [e["graine"] for e in E_it], [e["option"] for e in E_it])
        Y = np.array([e["compromis"] for e in E_it])
        b_mod, b_cst = float(np.mean((mu - Y) ** 2)), float(np.mean((m.taux - Y) ** 2))
        h.update(brier_imagination=b_mod, brier_constante=b_cst, n_utilisables=len(E_it))
        etat["imagination_pire_suite"] = etat["imagination_pire_suite"] + 1 if b_mod >= b_cst else 0
        # 2. CE QUE CHAQUE CANDIDAT A DONNE : regret observe, mur ou piege jouable
        regle = A.charger(); murs = 0
        for k, p in enumerate(etat["propositions"]):
            Ek = [e for e in E_it if e["candidat"] == k]
            if not Ek: continue
            taux = {o: np.mean([e["compromis"] for e in Ek if e["option_imposee"] == o]) if any(e["option_imposee"] == o for e in Ek) else None for o in (1, 2)}
            if None in taux.values(): continue
            o_regle = int(np.round(np.mean(A.choix(regle, Ek)))) if regle["type"] != "constante" else regle["option"]
            regret = taux[o_regle] - min(taux.values()); jouable = 1 - min(taux.values()) >= C.SEUIL_JOUABLE_OBSERVE
            murs += int(not jouable)
            p.update(taux_observe={str(o): float(v) for o, v in taux.items()}, regret_observe=float(regret), jouable_observe=bool(jouable), option_regle=o_regle)
            cle_p = (Gen.cle(p["situation"]), tuple(p["graines"]))
            if p["genre"] != "confirmation" and regret > C.REGRET_MIN_PIEGE and jouable and \
               cle_p not in {(Gen.cle(x["situation"]), tuple(x["graines"])) for x in etat["a_confirmer"] + etat["confirmes"] + etat["infirmes"]}:
                etat["a_confirmer"].append(dict(situation=p["situation"], graines=p["graines"], regret_observe=float(regret), option_regle=o_regle))
        # 3. LES CONFIRMATIONS : tout ce qui a ete joue de ce piege, cumule ; test exact de Fisher
        tous = Dn.utilisables(Dn.episodes(est_oracle))
        for p in list(etat["a_confirmer"]):
            Ep = [e for e in tous if Gen.cle({k: e[k] for k in C.ARMES}) == Gen.cle(p["situation"]) and e["graine"] in p["graines"]]
            o, a = p["option_regle"], 3 - p["option_regle"]
            n_o, c_o = sum(1 for e in Ep if e["option_imposee"] == o), sum(e["compromis"] for e in Ep if e["option_imposee"] == o)
            n_a, c_a = sum(1 for e in Ep if e["option_imposee"] == a), sum(e["compromis"] for e in Ep if e["option_imposee"] == a)
            if min(n_o, n_a) < 6: continue
            _, pv = fisher_exact([[c_o, n_o - c_o], [c_a, n_a - c_a]], alternative="greater")
            if pv < C.ALPHA_CONFIRMATION and (1 - c_a / n_a) >= C.SEUIL_JOUABLE_OBSERVE:
                etat["a_confirmer"].remove(p); p.update(p_fisher=float(pv), n=[n_o, n_a], compromis=[c_o, c_a]); etat["confirmes"].append(p)
                journal(f"- 🔮 **PIEGE CONFIRME** : {p['situation']} graines {p['graines']} — la regle choisit l option {o}, "
                        f"compromise {c_o}/{n_o}, contre {c_a}/{n_a} pour l autre ( Fisher p = {pv:.3f} )")
            elif min(n_o, n_a) >= 12:
                etat["a_confirmer"].remove(p); p.update(p_fisher=float(pv)); etat["infirmes"].append(p)
                journal(f"- piege infirme : {p['situation']} ( Fisher p = {pv:.3f} sur {n_o}+{n_a} episodes )")
        # 4. LES MOTIFS ( Younes, 21/09 : « ce que je veux c est reperer les patterns » ) : ceux que l imagination a
        # appris SANS cette iteration, mis a l epreuve SUR elle - un test prospectif, cumule d une iteration a l autre.
        mot = Mo.motifs_du_modele(m)
        for mo in mot: mo["compte"] = Mo.compter(mo, E_it)
        fj = f"{C.ETAT_DIR}/motifs.jsonl"
        with open(fj, "a") as f: f.write(json.dumps(dict(iteration=etat["iteration"], motifs=mot)) + "\n")
        cum = Mo.cumuler([json.loads(l) for l in open(fj)])
        lignes = []
        for cle, c in sorted(cum.items(), key=lambda kv: -kv[1]["vu"])[:6]:
            verdict, pv = Mo.epreuve(cle, c)
            if verdict == "CONFIRME" and list(cle) not in etat.setdefault("motifs_confirmes", []):
                etat["motifs_confirmes"].append(list(cle))
                journal(f"- 🔎 **MOTIF CONFIRME** : quand {cle[0]} = {cle[1]}, {'attendre SAUVE' if cle[2] == 'attendre_sauve' else 'attendre COUTE'} "
                        f"( prospectif : traverser {c['c_t']}/{c['n_t']}, attendre {c['c_a']}/{c['n_a']}, Fisher p = {pv:.3f} )")
            lignes.append(f"{cle[0]}={cle[1]} {'attendre sauve' if cle[2] == 'attendre_sauve' else 'attendre coute'} "
                          f"[vu {c['vu']} fois ; traverser {c['c_t']}/{c['n_t']}, attendre {c['c_a']}/{c['n_a']} ; {verdict}]")
        journal("- motifs appris puis eprouves sur cette iteration : " + " | ".join(lignes))
        h.update(murs=murs, pieges_confirmes_total=len(etat["confirmes"]), motifs_confirmes_total=len(etat.get("motifs_confirmes", [])))
        journal(f"- imagination : Brier {b_mod:.4f} contre constante {b_cst:.4f} "
                f"{'( elle voit mieux que le hasard )' if b_mod < b_cst else '( PAS mieux que la constante )'} ; "
                f"{murs} mur(s) ; {len(etat['a_confirmer'])} piege(s) a confirmer, {len(etat['confirmes'])} confirme(s)")
    if C.CONFIRMATION_ATTENDRE:
        try:
            from .lire_confirmation import paires, N as N_CONF
            journal(f"- paires de confirmation de « toujours attendre » : {len(paires())} / {N_CONF} ( le compte seulement )")
        except Exception as ex: journal(f"- compte des paires de confirmation impossible : {str(ex)[:80]}")
    if etat["iteration"] % C.ARCHITECTE_TOUS_LES == 0: lancer_architecte(etat)
    h["fin_ts"] = time.time(); etat["phase"] = "REPOS"; sauver(etat)
    if etat["sans_piege_suite"] >= C.ARRET_SANS_PIEGE:
        arreter(etat, f"l Oracle n imagine plus aucun piege depuis {etat['sans_piege_suite']} iterations : l equation tient"); return
    if etat["imagination_pire_suite"] >= C.ARRET_IMAGINATION_PIRE:
        arreter(etat, f"imagination pas meilleure que la constante {etat['imagination_pire_suite']} fois de suite"); return
    print(f"APPRENTISSAGE FAIT, iteration {etat['iteration']}")


def tour(a_blanc=False):
    os.makedirs(C.ETAT_DIR, exist_ok=True)
    verrou = open(f"{C.ETAT_DIR}/tick.lock", "w")
    try: fcntl.flock(verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: print("un autre tour est en cours"); return
    etat = charger()
    if not G.disque_monte(): print("ATTENTE : /mnt/data absent"); return
    if a_blanc: etape_repos(dict(etat), a_blanc=True); return
    if etat.get("arret"): print("ARRETE :", etat["arret"], "- supprimer la cle arret de etat.json pour reprendre"); return
    if G.stop_demande(): print("STOP demande ( fichier STOP ) : l Oracle ne pose plus rien") if etat["phase"] == "REPOS" else None
    if C.MULTIPLEXE:
        n = Mx.depaqueter()
        if n: journal(f"- multiplexeur : {n} cellule(s) rendue(s) a la boucle")
        p = Mx.empaqueter()
        if p: journal(f"- multiplexeur : {len(p)} job(s) multiple(s) pose(s)")
    # ! LES ETAPES S ENCHAINENT DANS LE MEME TOUR ( 22/09, Younes : « pourquoi y a plus rien ? » ) : une etape par tour
    # laissait la ferme vide ~15 min entre deux iterations ( lecture, apprentissage, pose : trois tours de 5 min ). Seul le
    # VOL attend : on enchaine jusqu a lui, puis on le lit une fois pour nourrir la ferme tout de suite.
    for _ in range(6):
        ph = etat["phase"]
        if ph == "REPOS":
            if G.stop_demande(): return
            etape_repos(etat)
        elif ph == "VOL": etape_vol(etat)
        elif ph == "LECTURE": etape_lecture(etat)
        elif ph == "APPRENTISSAGE": etape_apprentissage(etat)
        suivant = charger()
        if suivant.get("arret") or suivant["phase"] == ph: break
        etat = suivant


if __name__ == "__main__":
    if "--etat" in sys.argv: print(json.dumps({k: v for k, v in charger().items() if k not in ("propositions",)}, indent=1)[:4000])
    else: tour(a_blanc="--a-blanc" in sys.argv)
