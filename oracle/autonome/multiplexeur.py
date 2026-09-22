"""LE MULTIPLEXEUR ( 22/09, Younes : « lance les vraies choses maintenant » ). La boucle de l Oracle continue de fabriquer
des jobs du banc seul ; le multiplexeur les JOUE sur le banc multiple ( bancs/chacalmulti ), plusieurs cellules par
serveur, puis rend a la boucle des runs au format qu elle lit deja ( donnees.py, lire_confirmation.py inchanges ).

  empaqueter()  jobs de l Oracle poses dans queue/multiplexes/ -> cellules ( un job, une graine ) -> episodes multiples
                ( au plus K_SERVICE cellules, mondes deux a deux a >= ESPACEMENT m, meme heure du jour, qui est globale )
                -> jobs chacalmulti dans queue/. Un temoin negatif ( palier 9, monde hors A ) complete un episode sur deux
                quand un monde compatible existe ( controle C1 de Fable ).
  depaqueter()  episodes multiples finis -> runs virtuels runs/<date>_<version>_multi/ : job.json d origine, g<graine>/
                resultat.json et serveur.rpt de la cellule. Une cellule est rendue REFUSEE si son POULS a decroche
                ( ordonnanceur SQF, amendement 3 de multi/CRITERES_MULTI.md ), si l episode porte une erreur SQF, ou si le
                journal croise y a vu une connaissance ennemie entre cellules.
La boucle compte les jobs de queue/multiplexes/ comme « en vol » jusqu a ce que toutes leurs cellules soient rendues.
"""
import glob, json, os, shutil, time
from . import config as C, gardes as G

MUX = f"{C.QUEUE}/multiplexes"
ETAT_MUX = f"{C.ETAT_DIR}/multiplexeur.json"
EMPRISES = f"{C.DEPOT}/multi/emprises.json"
PAR_CELLULE = ["graine", "situation", "menace_p2", "traversee", "palier", "effectif", "avant", "observation", "qrf_n",
               "qrf_delai", "hmg", "portee_son", "balayage", "oracle_cmd", "oracle_ctrl", "oracle_b", "oracle_nu",
               "oracle_eps", "oracle_delta"]
# ce qui ne peut PAS varier d une cellule a l autre dans un meme serveur : l heure du monde est commune a toute l ile
GLOBAUX = ["jour"]
IGNORES = {"graines", "version", "note", "instance", "campagne", "repetitions", "plafond_s"}


def charger_etat():
    if os.path.exists(ETAT_MUX): return json.load(open(ETAT_MUX))
    return {"cellules": {}, "multi_jobs": {}, "runs_depaquetes": [], "compteur": 0}


def sauver_etat(e):
    tmp = ETAT_MUX + ".tmp"; json.dump(e, open(tmp, "w"), indent=1); os.replace(tmp, ETAT_MUX)


def distances():
    d = json.load(open(EMPRISES))["distances"]
    return {tuple(sorted(map(int, k.split("-")))): v for k, v in d.items()}


def compatibles(ep, w, D):
    return all(x != w and D.get(tuple(sorted((x, w))), 0) >= C.MULTI_ESPACEMENT for x in ep)


def empaqueter(a_blanc=False):
    """Transforme les jobs de l Oracle en attente dans queue/multiplexes/ en jobs chacalmulti. Idempotent."""
    os.makedirs(MUX, exist_ok=True)
    etat = charger_etat()
    D = distances()
    SITES = {w: v["site"] for w, v in json.load(open(EMPRISES))["mondes"].items()}
    nouveaux = []
    for jf in sorted(glob.glob(f"{MUX}/*.json")):
        nom = os.path.basename(jf); j = json.load(open(jf))
        for g in j["graines"]:
            cle = f"{nom}|{g}"
            if cle not in etat["cellules"]: nouveaux.append((nom, j, g))
    if not nouveaux: return []
    # le gabarit commun : tout ce qui n est pas surchargeable par cellule doit etre identique entre les jobs empaquetes
    base = {k: v for k, v in nouveaux[0][1].items() if k not in IGNORES and k not in PAR_CELLULE}
    groupes = {}
    for nom, j, g in nouveaux:
        diff = [k for k, v in j.items() if k not in IGNORES and k not in PAR_CELLULE and k not in GLOBAUX and base.get(k) != v]
        if diff:
            raise RuntimeError(f"{nom} : parametres communs differents du gabarit ( {diff} ) - non multiplexable")
        groupes.setdefault(tuple(j.get(k) for k in GLOBAUX), []).append((nom, j, g))
    episodes = []
    for glob_val, cel in groupes.items():
        restant = list(cel)
        while restant:
            ep = [restant.pop(0)]
            for c in list(restant):
                if len(ep) >= C.K_SERVICE: break
                if compatibles([x[2] for x in ep], c[2], D): ep.append(c); restant.remove(c)
            episodes.append((glob_val, ep))
    # temoins negatifs : un episode sur deux, un monde hors A compatible avec ceux de l episode
    hors_a = sorted({int(w) for p in D for w in p} - set(C.GRAINES) - set(C.MONDES_B))
    for i, (gv, ep) in enumerate(episodes):
        if i % 2 == 0 and len(ep) < C.K_SERVICE + 1:
            for w in hors_a:
                if compatibles([x[2] for x in ep], w, D): ep.append(("TEMOIN", None, w)); break
    # repartition en jobs chacalmulti : au moins deux episodes par job ( controle_avant_run ), au plus un job par instance
    n_jobs = max(1, min(len(C.INSTANCES), len(episodes) // 2))
    paquets = [episodes[i::n_jobs] for i in range(n_jobs)]
    if len(paquets[-1]) < 2 and len(paquets) > 1: paquets[-2] += paquets.pop()
    poses = []
    for r, paquet in enumerate(paquets):
        etat["compteur"] += 1
        mj = dict(base)
        for gv_k, gv in zip(GLOBAUX, paquet[0][0]): mj[gv_k] = gv
        mj.update(banc="chacalmulti", repetitions=1, plafond_s=5400, instance=C.INSTANCES[r % len(C.INSTANCES)],
                  multi_tmax=C.MULTI_TMAX, multi_sonde=1, multi_espacement=C.MULTI_ESPACEMENT,
                  campagne=nouveaux[0][1].get("campagne"), version=f"MUX-{etat['compteur']:04d}",
                  note="Multiplexeur de l Oracle : cellules du banc seul jouees sur le banc multiple.")
        eps = {}
        for e_i, (gv, ep) in enumerate(paquet, start=1):
            cells = []
            for nom, j, g in ep:
                if nom == "TEMOIN":
                    cells.append({"graine": g, "palier": 9, "menace_p2": 0, "oracle_cmd": 0, "traversee": 1, "situation": 1,
                                  "role": "temoin_negatif"})
                    continue
                c = {k: j[k] for k in PAR_CELLULE if k in j and k != "graine"}
                c.update(graine=g, role="oracle", origine=nom, version=j.get("version"))
                cells.append(c)
            # le site attendu de chaque monde ( table du banc seul ) : la mission annule la cellule si le monde tire s en ecarte
            for c in cells:
                s = SITES.get(str(c["graine"]))
                if s: c["site_x"], c["site_y"] = int(round(s[0])), int(round(s[1]))
            eps[str(e_i)] = cells
        mj["graines"] = list(range(1, len(eps) + 1)); mj["episodes"] = eps
        # si le paquet n a qu un episode ( tres petit lot ), on le double d un temoin pour passer la regle des deux episodes
        if len(eps) < 2:
            w = next((x for x in hors_a if x != eps["1"][0]["graine"]), hors_a[0])
            eps["2"] = [{"graine": w, "palier": 9, "menace_p2": 0, "oracle_cmd": 0, "traversee": 1, "situation": 1, "role": "temoin_negatif",
                         "site_x": int(round(SITES[str(w)][0])), "site_y": int(round(SITES[str(w)][1]))}]
            mj["graines"] = [1, 2]
        nom_mj = f"{time.strftime('%Y-%m-%d')}_{mj['version'].replace('-', '_')}.json"
        if a_blanc: poses.append((nom_mj, mj["instance"], {e: [(c["graine"], c.get("role")) for c in v] for e, v in eps.items()})); continue
        prep = f"{C.PREP}/{nom_mj}"; json.dump(mj, open(prep, "w"), indent=1, ensure_ascii=True)
        ok, msg = G.controle_job(prep)
        if not ok: os.remove(prep); raise RuntimeError(f"controle refuse le job multiple {nom_mj} : {msg}")
        shutil.move(prep, f"{C.QUEUE}/{nom_mj}"); poses.append(nom_mj)
        etat["multi_jobs"][nom_mj] = {"pose": time.time(), "episodes": {e: [c.get("origine") for c in v] for e, v in eps.items()}}
        for e, v in eps.items():
            for k, c in enumerate(v, start=1):
                if c.get("origine"): etat["cellules"][f"{c['origine']}|{c['graine']}"] = {"multi_job": nom_mj, "episode": e, "cellule": k, "statut": "posee"}
    if not a_blanc: sauver_etat(etat)
    return poses


def _verdict_cellule(res_ep, k, c):
    """La cellule compte-t-elle ? Les portes du banc seul ( lire.py ) plus trois portes du multiple."""
    m = res_ep.get("multi", {})
    if sum(int(v) for v in (m.get("erreurs_sqf") or {}).values()): return "REFUSE", "ERREUR_SQF_DANS_L_EPISODE"
    if m.get("croise", {}).get("ennemis", 0): return "REFUSE", "CONNAISSANCE_CROISEE_ENTRE_CELLULES"
    b = c.get("pouls_dans_bande")
    if b is None or b < C.POULS_BANDE_MIN: return "REFUSE", f"ORDONNANCEUR_SATURE ( pouls dans la bande {b} )"
    # ! LE MONDE DOIT ETRE CELUI DU BANC SEUL ( service du 22/09, 14 h 12 ) : 2 cellules sur 25 ont tire un autre monde
    # que leur graine dans le banc seul ( monde 7 : site a 13 km ; monde 15 : a 11 km ), et l une est tombee a 117 m du
    # temoin. Une cellule dont le site s ecarte de la table de plus de 5 m ne porte plus la graine qu elle annonce.
    e = c.get("monde_ecart_m")
    if e is None or e > 5: return "REFUSE", f"MONDE_NON_CONFORME ( ecart du site {e} m )"
    proches = [x for x in m.get("espacements", []) if k in (x[0], x[1]) and x[2] < C.ESPACEMENT_REFUS]
    if proches: return "REFUSE", f"CELLULE_TROP_PROCHE ( {proches} )"
    return None, None


def depaqueter():
    """Rend a la boucle les cellules des episodes multiples finis. Idempotent."""
    etat = charger_etat(); rendus = 0
    for fin in glob.glob(f"{C.RUNS}/2026-*chacalmulti*/FIN.json"):
        run = os.path.dirname(fin)
        if run in etat["runs_depaquetes"]: continue
        try: job = json.load(open(f"{run}/job.json"))
        except Exception: continue
        if not str(job.get("version", "")).startswith("MUX-"): etat["runs_depaquetes"].append(run); continue
        for e, cells in job["episodes"].items():
            try: res = json.load(open(f"{run}/g{e}/resultat.json"))
            except Exception: res = {"verdict": "REFUSE", "cause": "EPISODE_SANS_RESULTAT", "cellules": {}, "multi": {}}
            for k, spec in enumerate(cells, start=1):
                if not spec.get("origine"): continue
                ori = f"{MUX}/{spec['origine']}"
                if not os.path.exists(ori): continue
                j0 = json.load(open(ori))
                vdir = f"{C.RUNS}/{spec['origine'][:10]}_{j0['version'].replace('-', '_')}_multi"
                os.makedirs(f"{vdir}/g{spec['graine']}", exist_ok=True)
                if not os.path.exists(f"{vdir}/job.json"):
                    jv = dict(j0); jv["banc_joue"] = "chacalmulti"; json.dump(jv, open(f"{vdir}/job.json", "w"), indent=1)
                    open(f"{vdir}/run.log", "w").write(f"run virtuel du multiplexeur : cellules jouees sur le banc multiple\n")
                src = f"{run}/g{e}/c{k}"
                try: r = json.load(open(f"{src}/resultat.json"))
                except Exception: r = {"verdict": "REFUSE", "cause": "CELLULE_SANS_RESULTAT"}
                c = res.get("cellules", {}).get(str(k), {})
                v, cause = _verdict_cellule(res, k, c)
                if v and r.get("verdict") == "ACCEPTE": r["verdict"] = v; r["cause_refus"] = cause
                r["multi"] = {"run": run, "episode": e, "cellule": k, "pouls_dans_bande": c.get("pouls_dans_bande"),
                              "k": len(cells), "fps": res.get("multi", {}).get("fps_toutes_actives")}
                json.dump(r, open(f"{vdir}/g{spec['graine']}/resultat.json", "w"), indent=1, ensure_ascii=False)
                if os.path.exists(f"{src}/serveur.rpt"): shutil.copy(f"{src}/serveur.rpt", f"{vdir}/g{spec['graine']}/serveur.rpt")
                etat["cellules"].setdefault(f"{spec['origine']}|{spec['graine']}", {})["statut"] = "rendue"
                rendus += 1
                # un job d origine est fini quand toutes ses graines sont rendues
                if all(etat["cellules"].get(f"{spec['origine']}|{g}", {}).get("statut") == "rendue" for g in j0["graines"]):
                    json.dump({"verdict": "COMPLET", "multiplexe": True, "duree_s": 0, "resultats": {}, "fin": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(f"{vdir}/FIN.json", "w"))
                    os.makedirs(f"{C.QUEUE}/faits", exist_ok=True); shutil.move(ori, f"{C.QUEUE}/faits/{spec['origine']}")
        etat["runs_depaquetes"].append(run)
    # un job multiple REFUSE par le controle ne cree aucun run : ses cellules sont rendues refusees, la boucle les reparera
    for nom_mj, info in etat["multi_jobs"].items():
        if info.get("refus_traite") or not os.path.exists(f"{C.QUEUE}/refuses/{nom_mj}"): continue
        for e, origines in info["episodes"].items():
            for ori in origines:
                if not ori or not os.path.exists(f"{MUX}/{ori}"): continue
                j0 = json.load(open(f"{MUX}/{ori}"))
                vdir = f"{C.RUNS}/{ori[:10]}_{j0['version'].replace('-', '_')}_multi"
                for g in j0["graines"]:
                    cle = f"{ori}|{g}"
                    if etat["cellules"].get(cle, {}).get("multi_job") != nom_mj or etat["cellules"][cle].get("statut") == "rendue": continue
                    os.makedirs(f"{vdir}/g{g}", exist_ok=True)
                    if not os.path.exists(f"{vdir}/job.json"):
                        json.dump(dict(j0, banc_joue="chacalmulti"), open(f"{vdir}/job.json", "w"), indent=1)
                        open(f"{vdir}/run.log", "w").write("run virtuel du multiplexeur\n")
                    json.dump({"verdict": "REFUSE", "cause_refus": "JOB_MULTIPLE_REFUSE_PAR_LE_CONTROLE"}, open(f"{vdir}/g{g}/resultat.json", "w"))
                    etat["cellules"][cle]["statut"] = "rendue"; rendus += 1
                if all(etat["cellules"].get(f"{ori}|{g}", {}).get("statut") == "rendue" for g in j0["graines"]):
                    json.dump({"verdict": "ECHEC", "multiplexe": True, "duree_s": 0, "resultats": {}}, open(f"{vdir}/FIN.json", "w"))
                    os.makedirs(f"{C.QUEUE}/faits", exist_ok=True); shutil.move(f"{MUX}/{ori}", f"{C.QUEUE}/faits/{ori}")
        info["refus_traite"] = True
    sauver_etat(etat)
    return rendus


def en_vol(noms):
    """Jobs d origine encore dans le multiplexeur ( poses, pas encore tous rendus )."""
    return [n for n in noms if os.path.exists(f"{MUX}/{n}")]
