"""LE CHEF D'ÉTAT-MAJOR QWEN ( 03/10, Younes : « un chef d'état-major qui maîtrise l'entièté des domaines de la guerre » ).

La méthode d'un vrai état-major ( COPD de l'OTAN, MEDO française ), à chaque période et pour chaque camp :
  1. SITUATION : le moteur rédige l'état réel tel que le camp le CONNAÎT ( forces, bases, carte des menaces, missions et
     leurs résultats, réserves, pertes de la fenêtre ).
  2. MODES D'ACTION : trois propositions ( poursuivre, concentrer, défendre ), chacune JOUÉE SUR UNE COPIE : un estimateur
     nourri des taux réellement observés ( dégâts par frappeur et par tour, pertes par frappeur et par tour, échanges en
     combat aérien ) prédit dégâts infligés et pertes à l'horizon.
  3. DÉCISION : Qwen ( local, Ollama ) lit la situation, les trois modes joués, les fiches de connaissance pertinentes et
     la fiche de commandement ; il choisit et justifie, en JSON. Ses leviers sont STRATÉGIQUES et bornés : cible
     prioritaire, multiplicateurs des ratios de chasse et de frappe, engagement ou garde des réserves. La tactique reste à
     CMO et au moteur.
  4. EXÉCUTION puis BILAN : à l'horizon, le résultat obtenu est comparé à la prévision ; l'estimateur se recale.

Qwen tourne dans un fil à part : la guerre n'attend jamais sa réponse. Chaque échange ( invite, réponse, prévision,
résultat ) est archivé en JSONL pour la supervision et pour la future LoRA.
"""
import json
import os
import threading
import time
import urllib.request

OLLAMA = "http://localhost:11434/api/chat"
MODELE = "qwen3.8:27b"
PERIODE_TOURS = 30                                        # une décision par camp toutes les 30 min de jeu ( 1 tour = 1 min )
HORIZON_TOURS = 30                                        # le bilan prévision / résultat se fait 30 tours après la décision
MULT_MIN, MULT_MAX = 0.5, 2.0                             # bornes des multiplicateurs que Qwen peut demander
APPRENDRE = 0.3                                           # pas du recalage de l'estimateur
SYSTEME = ("Tu es le chef d'état-major du camp {camp} dans une guerre réelle simulée par Command: Modern Operations. Tu "
           "décides la STRATÉGIE ; la tactique est exécutée par CMO. Objectif : détruire la capacité militaire adverse ( bases "
           "aériennes, défenses, flotte ) en préservant tes forces, dont les réserves sont FINIES. Tes leviers : « cible » = "
           "index d'une base adverse à frapper en priorité ( null = le choix de ton état-major ) ; « mult_frappe » multiplie le "
           "nombre de frappeurs engagés par cible ; « mult_aa » multiplie le nombre de chasseurs par avion adverse menaçant ; "
           "« reserves » = engager ( faire venir des renforts de la réserve nationale ) ou garder ; « posture_terre » = "
           "offensive ( attaquer dès 2 contre 1 ), doctrine ( 3 contre 1 ) ou defensive ( aucune attaque ) ; « posture_mer » "
           "= offensive ( frappes antinavire jusqu'à 600 km ), doctrine ( 400 km ) ou defensive ( 200 km ). Méthode : lis la situation "
           "( synthese, taux observés sur l'heure écoulée ), compare les modes d'action et leurs prévisions jouées sur une copie "
           "calée sur ces taux, choisis-en un ou ajuste-le dans les bornes. Réponds UNIQUEMENT en JSON : "
           '{{"mode": "<id>", "raison": "<3 phrases au plus>", "cible": <index de base ou null>, '
           '"mult_aa": <0.5 à 2>, "mult_frappe": <0.5 à 2>, "reserves": "engager" ou "garder", '
           '"posture_terre": "offensive" | "doctrine" | "defensive", "posture_mer": "offensive" | "doctrine" | "defensive"}}')
FENETRE_TAUX = 60                                         # tours ( 1 h de jeu ) sur lesquels les taux sont observés
# Élasticités de la copie ( choix à valider ) : dégâts ~ mult_frappe^1 ; pertes ~ mult_frappe^0,6 x mult_aa^-0,3


def appeler_ollama(messages, modele=MODELE, delai=600):
    # mode RÉFLEXION ( 03/10 : sans lui, Qwen lisait « supériorité adverse » à 106 chasseurs contre 50 ) : il raisonne
    # d'abord ( message.thinking ), puis rend le JSON ( message.content ) ; il a 30 min de jeu pour décider
    corps = json.dumps({"model": modele, "messages": messages, "stream": False, "format": "json", "keep_alive": -1,
                        "think": True, "options": {"temperature": 0.2, "num_predict": 3000}}).encode()
    req = urllib.request.Request(OLLAMA, data=corps, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=delai) as r:
        return json.loads(r.read())["message"]["content"]


class ChefQwen:
    def __init__(self, g, appeler=None, savoir=None, dossier=None):
        self.g = g
        self.appeler = appeler or appeler_ollama
        self.savoir = savoir                             # rechercher(question, k) -> [ fiches ] ( base de connaissance )
        self.dossier = dossier
        self.coef = {c: {"e_degats": 1.0, "e_pertes_frappe": 0.6, "e_pertes_chasse": -0.3, "biais_degats": 1.0, "biais_pertes": 1.0}
                     for c in g.camps}
        self.en_cours = {}                               # camp -> fil Qwen en vol
        self.reponses = {}                               # camp -> ( décision brute, contexte ) prête à appliquer
        self.decisions = []                              # historique : décision, prévision, bilan
        self.verrou = threading.Lock()

    # ---- 1. la situation, telle que le camp la connaît
    def situation(self, camp):
        g, em = self.g, self.g.em
        forces = {}
        for a in g.avions.values():
            if a["camp"] == camp:
                forces[a["role"]] = forces.get(a["role"], 0) + 1
        adverses = {}
        for a in g.avions.values():
            if a["camp"] != camp:
                adverses[a["role"]] = adverses.get(a["role"], 0) + 1
        bases_adv = []
        for i, b in g.bases.items():
            if b["camp"] != camp and b["pos"]:
                n = sum(1 for a in g.avions.values() if a["base"] == i)
                bases_adv.append({"index": i, "nom": os.path.basename(b["fichier"])[:40], "operationnelle_percue": g.op_percu(camp, i),
                                  "avions_estimes": n})
        t0 = g.tours - HORIZON_TOURS
        pertes = {"avions": sum(1 for m in g.morts if m["genre"] == "avion" and g.camp_de_pays(m["pays"]) == camp and m["tour"] > t0),
                  "elements": sum(1 for d in g.detruits if d["camp"] == camp and d["tour"] > t0)}
        infligees = {"avions": sum(1 for m in g.morts if m["genre"] == "avion" and g.camp_de_pays(m["pays"]) != camp and m["tour"] > t0),
                     "elements": sum(1 for d in g.detruits if d["camp"] != camp and d["tour"] > t0)}
        fr = g.frappe.get(camp)
        synth = lambda f: {"chasseurs": f.get("aa", 0), "frappeurs": sum(f.get(r, 0) for r in ("frappe", "dead", "bombardier")),   # noqa: E731
                           "soutien": sum(f.get(r, 0) for r in ("guet", "ravitailleur", "brouilleur", "sead", "reco", "elint"))}
        def taux_depuis(t1):
            n = max(1, g.tours - t1)
            return {"elements_adverses_detruits_par_tour": round(sum(1 for d in g.detruits if d["camp"] != camp and d["tour"] > t1) / n, 3),
                    "avions_perdus_par_tour": round(sum(1 for m in g.morts if m["genre"] == "avion" and g.camp_de_pays(m["pays"]) == camp
                                                        and m["tour"] > t1) / n, 3),
                    "avions_adverses_abattus_par_tour": round(sum(1 for m in g.morts if m["genre"] == "avion"
                                                                  and g.camp_de_pays(m["pays"]) != camp and m["tour"] > t1) / n, 3)}
        heure, guerre = taux_depuis(max(0, g.tours - FENETRE_TAUX)), taux_depuis(0)
        # la copie mêle l'heure écoulée et toute la guerre : une heure creuse ne condamne pas l'offensive ( 03/10 )
        taux = {k: round(0.5 * heure[k] + 0.5 * guerre[k], 3) for k in heure}
        s_moi, s_lui = synth(forces), synth(adverses)
        bases_adv_op = sum(1 for b in bases_adv if b["operationnelle_percue"])
        rapport = {"chasse": f"{s_moi['chasseurs']} contre {s_lui['chasseurs']} ( "
                             + ("AVANTAGE À NOUS" if s_moi["chasseurs"] > 1.2 * s_lui["chasseurs"] else
                                "AVANTAGE À L'ADVERSAIRE" if s_lui["chasseurs"] > 1.2 * s_moi["chasseurs"] else "équilibre") + " )",
                   "frappe": f"{s_moi['frappeurs']} contre {s_lui['frappeurs']}"}
        objectif = {"bases_aeriennes_adverses_operationnelles_percues": bases_adv_op, "bases_aeriennes_adverses": len(bases_adv),
                    "elements_adverses_detruits_depuis_le_debut": sum(1 for d in g.detruits if d["camp"] != camp),
                    "nos_elements_detruits_depuis_le_debut": sum(1 for d in g.detruits if d["camp"] == camp)}
        return {"camp": camp, "tour": g.tours, "phase_tempo": "surge" if g.tempo == 0 else "soutenu",
                "rapport_de_forces": rapport, "objectif": objectif,
                "synthese": s_moi, "synthese_adverse_estimee": s_lui, "taux_heure_ecoulee": taux,
                "taux_detail": {"heure_ecoulee": heure, "toute_la_guerre": guerre},
                "forces": forces, "forces_adverses_estimees": adverses,
                "bases_adverses": sorted(bases_adv, key=lambda x: -x["avions_estimes"])[:8],
                "menaces_sol_air_connues": len(em.memoire.get(camp, {})),
                "mission_en_cours": fr and {"type": fr.get("type"), "base": fr.get("base"), "cibles": len(fr.get("cibles", []))},
                "ratios": em.ratio.get(camp), "part_dead": round(em.part_dead.get(camp, 0.5), 2),
                "reserve": {k: int(v) for k, v in g.reserve.items() if g.camp_de_pays(k.rsplit("|", 1)[0]) == camp and v >= 2},
                "pertes_fenetre": pertes, "infligees_fenetre": infligees,
                "terre": [x for x in em.journal if x.get("camp") == camp and "terre" in x][-1:] and
                         [x for x in em.journal if x.get("camp") == camp and "terre" in x][-1]["terre"],
                "mer": {"nos_navires": sum(1 for n in g.navires.values() if n["camp"] == camp),
                        "navires_ennemis_connus": sum(1 for k in em.memoire.get(camp, {}) if k in g.navires),
                        "navires_perdus": sum(1 for m in g.morts if m["genre"] == "navire" and g.camp_de_pays(m["pays"]) == camp),
                        "navires_ennemis_coules": sum(1 for m in g.morts if m["genre"] == "navire" and g.camp_de_pays(m["pays"]) != camp),
                        "frappe_antinavire_cibles": len(((em.antinav or {}).get(camp) or {}).get("cibles", []))},
                "postures": {"terre": em.posture_terre.get(camp), "mer": em.posture_mer.get(camp)}}

    # ---- 2. les modes d'action, joués sur une copie ( l'estimateur )
    def modes(self, camp, sit):
        cible_max = sit["bases_adverses"][0]["index"] if sit["bases_adverses"] else None
        return [{"id": "poursuivre", "cible": None, "mult_aa": 1.0, "mult_frappe": 1.0, "reserves": "engager",
                 "posture_terre": "doctrine", "posture_mer": "doctrine"},
                {"id": "concentrer", "cible": cible_max, "mult_aa": 1.0, "mult_frappe": 1.5, "reserves": "engager",
                 "posture_terre": "offensive", "posture_mer": "offensive"},
                {"id": "defendre", "cible": None, "mult_aa": 1.5, "mult_frappe": 0.7, "reserves": "garder",
                 "posture_terre": "defensive", "posture_mer": "defensive"}]

    def jouer(self, camp, mode, sit):
        """La copie : l'issue à l'horizon d'un mode d'action, à partir des taux OBSERVÉS sur l'heure écoulée ( dégâts
        infligés, avions perdus par tour ), modulés par les multiplicateurs du mode ( élasticités ) et par le biais appris
        aux bilans précédents ( prévu contre obtenu )."""
        c, t = self.coef[camp], sit["taux_heure_ecoulee"]
        mf, ma = mode["mult_frappe"], mode["mult_aa"]
        degats = t["elements_adverses_detruits_par_tour"] * HORIZON_TOURS * mf ** c["e_degats"] * c["biais_degats"]
        pertes = t["avions_perdus_par_tour"] * HORIZON_TOURS * mf ** c["e_pertes_frappe"] * ma ** c["e_pertes_chasse"] * c["biais_pertes"]
        if mode.get("reserves") == "garder":
            pertes *= 1.0                                # garder ne change pas l'heure qui vient ; il préserve la suite
        return {"elements_detruits": round(degats, 2), "avions_perdus": round(pertes, 2)}

    # ---- 3. la décision ( fil à part )
    def demander(self, camp):
        if camp in self.en_cours and self.en_cours[camp].is_alive():
            return
        sit = self.situation(camp)
        modes = self.modes(camp, sit)
        for m in modes:
            m["prevision"] = self.jouer(camp, m, sit)
        fiches = []
        if self.savoir:
            try:                                         # la base de connaissance ( 18 944 fiches, porte du 03/10 franchie )
                mission = (sit.get("mission_en_cours") or {}).get("type") or "oca"
                fiches = self.savoir(f"doctrine {mission} supériorité aérienne défense aérienne réserves rapport de forces", 3)
                fiches += self.savoir("lutte antinavire contrôle de la mer sous-marins doctrine", 1)
                fiches += self.savoir("manœuvre terrestre rapport de forces appui feu", 1)
                cmd = getattr(self, "commandement", None)
                if cmd:
                    fiches = [cmd] + fiches
            except Exception:                            # la base de connaissance est un plus, jamais une panne
                fiches = []
        messages = [{"role": "system", "content": SYSTEME.format(camp=camp)},
                    {"role": "user", "content": json.dumps({"situation": sit, "modes_d_action": modes,
                                                            "fiches": [{"titre": f.get("titre"), "texte": f.get("texte", "")[:1200]} for f in fiches]},
                                                           ensure_ascii=False)}]

        def fil():
            t = time.time()
            try:
                brut = self.appeler(messages)
            except Exception as e:
                brut = json.dumps({"erreur": f"{type(e).__name__}: {e}"[:200]})
            with self.verrou:
                self.reponses[camp] = (brut, {"situation": sit, "modes": modes, "messages": messages, "duree_s": round(time.time() - t, 1)})
        th = threading.Thread(target=fil, daemon=True)
        self.en_cours[camp] = th
        th.start()

    def _valider(self, camp, brut, modes):
        """La décision de Qwen, BORNÉE ; illisible ou hors bornes : le mode « poursuivre »."""
        try:
            d = json.loads(brut)
        except Exception:
            return dict(modes[0], raison="réponse illisible : on poursuit", valide=False)
        base = next((m for m in modes if m["id"] == d.get("mode")), modes[0])
        out = dict(base)
        cible = d.get("cible", base["cible"])
        g = self.g
        out["cible"] = cible if isinstance(cible, int) and cible in g.bases and g.bases[cible]["camp"] != camp else None
        for k in ("mult_aa", "mult_frappe"):
            try:
                out[k] = min(MULT_MAX, max(MULT_MIN, float(d.get(k, base[k]))))
            except (TypeError, ValueError):
                out[k] = base[k]
        out["reserves"] = d.get("reserves") if d.get("reserves") in ("engager", "garder") else base["reserves"]
        for k in ("posture_terre", "posture_mer"):
            out[k] = d.get(k) if d.get(k) in ("offensive", "doctrine", "defensive") else base[k]
        out["raison"] = str(d.get("raison", ""))[:400]
        out["valide"] = "erreur" not in d and d.get("mode") in [m["id"] for m in modes]
        return out

    def appliquer(self):
        """Dans la boucle du moteur : les décisions arrivées sont appliquées ( leviers stratégiques ), datées et archivées."""
        with self.verrou:
            prets, self.reponses = self.reponses, {}
        em = self.g.em
        for camp, (brut, ctx) in prets.items():
            d = self._valider(camp, brut, ctx["modes"])
            em.cible_imposee[camp] = d["cible"]
            em.mult_chef[camp] = {"aa": d["mult_aa"], "frappe": d["mult_frappe"]}
            em.reserves_gardees[camp] = d["reserves"] == "garder"
            em.posture_terre[camp] = d["posture_terre"]
            em.posture_mer[camp] = d["posture_mer"]
            prevu = self.jouer(camp, d, ctx["situation"])
            rec = {"camp": camp, "tour": self.g.tours, "decision": d, "prevision": prevu, "brut": brut[:2000],
                   "duree_s": ctx["duree_s"], "bilan": None, "forces": ctx["situation"]["forces"], "messages": ctx["messages"]}
            self.decisions.append(rec)
            em.journal.append({"camp": camp, "tour": self.g.tours, "chef_qwen": {k: d[k] for k in ("id", "cible", "mult_aa", "mult_frappe", "reserves",
                                                                                                   "posture_terre", "posture_mer", "valide")},
                               "raison": d["raison"][:200], "prevision": prevu})
            self._archiver(rec)

    # ---- 4. le bilan : prévu contre obtenu, et l'estimateur se recale
    def bilans(self):
        g = self.g
        for rec in self.decisions:
            if rec["bilan"] is not None or g.tours < rec["tour"] + HORIZON_TOURS:
                continue
            camp, t0, t1 = rec["camp"], rec["tour"], rec["tour"] + HORIZON_TOURS
            obtenu = {"elements_detruits": sum(1 for d in g.detruits if d["camp"] != camp and t0 < d["tour"] <= t1),
                      "avions_perdus": sum(1 for m in g.morts if m["genre"] == "avion" and g.camp_de_pays(m["pays"]) == camp and t0 < m["tour"] <= t1)}
            rec["bilan"] = obtenu
            c = self.coef[camp]
            # le recalage : le biais de la copie suit le rapport obtenu / prévu ( borné, pour qu'un zéro ne l'efface pas )
            for cle, k in (("elements_detruits", "biais_degats"), ("avions_perdus", "biais_pertes")):
                prevu, vu = rec["prevision"][cle], obtenu[cle]
                rapport = (vu + 0.5) / (prevu + 0.5)
                c[k] = min(4.0, max(0.25, c[k] * rapport ** APPRENDRE))
            g.em.journal.append({"camp": camp, "tour": g.tours, "bilan_chef": {"prevu": rec["prevision"], "obtenu": obtenu,
                                                                              "coef": {k: round(v, 4) for k, v in c.items()}}})
            self._archiver({"camp": camp, "tour": g.tours, "bilan_de": t0, "prevu": rec["prevision"], "obtenu": obtenu})

    def tour(self):
        """Appelé à chaque tour par le moteur : appliquer ce qui est arrivé, faire les bilans, demander à l'heure."""
        self.appliquer()
        self.bilans()
        if self.g.tours % PERIODE_TOURS == 2:
            for camp in self.g.camps:
                self.demander(camp)

    def _archiver(self, rec):
        if not self.dossier:
            return
        os.makedirs(self.dossier, exist_ok=True)
        with open(os.path.join(self.dossier, "chef_qwen.jsonl"), "a") as h:
            h.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def etat(self):
        return {"coef": self.coef, "decisions": [{k: v for k, v in r.items() if k != "messages"} for r in self.decisions[-40:]]}

    def charger(self, e):
        for camp, v in (e.get("coef") or {}).items():    # un état d'avant la copie calée sur les taux est ignoré
            if camp in self.coef and "e_degats" in v:
                self.coef[camp] = v
