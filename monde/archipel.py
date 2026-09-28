"""L ARCHIPEL ( plans/plan-archipel.md, phase D ) : six pays, six processus, un pont, une horloge.

Chaque ile est un monde complet ( moteur + domaines ) dans SON processus. Le pont tient l horloge maitresse : a chaque
pas de 10 minutes il donne a chaque ile le courrier qui lui arrive, attend que les SIX aient joue leur pas, ramasse
leur courrier sortant et le range, dans un ordre fixe ( pas, ile d origine, numero d ordre ). Le resultat ne depend
donc ni du nombre de coeurs ni de l ordre dans lequel les processus finissent.

Deux vitesses, une seule regle : au plus vite ( personne n est la ), ou un pas = SECONDES_TEMPS_REEL secondes
d horloge murale des qu un humain est connecte ( le fichier HUMAIN existe ; plus tard : la liste des joueurs des
serveurs Arma ). On change de vitesse a la frontiere d un pas, jamais au milieu.

Instantane : les six iles et le pont, au meme pas ; reprise : on repart de la. En mode SEQUENTIEL, les six iles
tournent dans le meme processus : c est le juge du mode parallele ( porte G3 ).

Phase D : le pont FERME ( aucun courrier ). Phase E1 : OUVERT, les visiteurs traversent ( monde.partir,
recevoir_courrier : arrivee, retour, refoule ).

   python -m monde.archipel --jours 2 --echelle 4"""
import argparse, hashlib, os, pickle, sys, time
import multiprocessing as mp
import numpy as np
from . import monde as W, tests as T, config as C, or_reel as OR, enregistreur as ENR, population as PO
from .pays import pays as P
from .porte_domaines import LIVRES, empreinte

DOSSIER = "/mnt/data/hmt/archipel"
HUMAIN = os.path.join(DOSSIER, "HUMAIN")          # present = un humain est connecte : le temps reel
SECONDES_TEMPS_REEL = C.MINUTES_PAR_PAS * 60.0


def graine_ile(graine, ile):
    """La graine d une ile : derivee de celle de l archipel et du NOM de l ile ( la meme ile seule a la meme graine )."""
    return int.from_bytes(hashlib.sha256(f"{graine}:{ile}".encode()).digest()[:4], "little")


def creer_ile(ile, graine, echelle, llm=False, demographie=None):
    """Un pays : son monde, ses domaines, son etalon-or ( F1 ) ; avec `llm`, son gouvernement est joue par Qwen, qui
    sait de quel pays il est le gouvernement et dans quelle monnaie il compte. `demographie` : voir population.generer."""
    w = W.Monde(graine=graine_ile(graine, ile), iles=(ile,), echelle=echelle, cerveau="llm" if llm else "regles",
                demographie=demographie)
    w.echelle_convois = float(echelle)
    P.installer(w, LIVRES)
    OR.installer(w, w.pays)
    if llm and w.cerveau is not None and hasattr(w.cerveau, "consigne"):
        c = w.cerveau
        c.consigne = c.consigne.replace("Tu es le gouvernement du pays :",
                                        f"Tu es le gouvernement de {ile}, un pays insulaire ( sa monnaie : le {C.MONNAIES[ile]}, "
                                        f"definie par un poids d or ; cinq autres iles-pays sont ses voisins ) :", 1)
        import hashlib
        c.empreinte = hashlib.sha256(c.consigne.encode()).hexdigest()[:12]
    return w


# Les noms qu un instantane d avant la fusion du tronc ( 27/09 ) peut porter et qui n existent plus : la mort de faim de
# la branche ( remplacee par celle du tronc, SEUILS_FAIM ). Relus comme une routine vide, puis retires des routines.
DISPARUS = {("monde.pays.d01_population", "_faim_mortelle")}


def _routine_disparue(p): return None


class _Relecteur(pickle.Unpickler):
    def find_class(self, module, nom):
        if (module, nom) in DISPARUS: return _routine_disparue
        return super().find_class(module, nom)


def charger(chemin):
    """Relit l instantane d une ile ; les routines disparues sont retirees de son pays."""
    with open(chemin, "rb") as f: w = _Relecteur(f).load()
    p = getattr(w, "pays", None)
    if p is not None:
        for m in list(p.routines):
            p.routines[m] = [r for r in p.routines[m] if r[2] is not _routine_disparue]
    return w


def _convois(w, echelle):
    """Une ile reprise d un instantane d avant le 27/09 n a pas l echelle de ses convois ( celle de l archipel ) ni
    l autoconsommation paysanne ( domaine 9 ) : les lui poser."""
    if "echelle_convois" not in vars(w): w.echelle_convois = float(echelle)
    if getattr(w, "pays", None) is not None and w.pays.a("agriculture"):
        from .pays import d09_agriculture as AG
        AG.brancher_autoconsommation(w.pays)             # idempotent : une ile d avant le 27/09 ne l a pas
    if getattr(w, "pays", None) is not None and w.pays.a("exterieur"):
        from .pays import d07_exterieur as X
        X.brancher_devises(w.pays)                       # idempotent : une ile d avant HMT-131 n a pas devises_refusees
    if getattr(w, "pays", None) is not None and w.pays.a("travail"):
        from .pays import d04_travail as TV
        TV.brancher_impayes(w.pays)                      # idempotent : une ile d avant HMT-126 a n a pas tr_paye_j
    return w


# ------------------------------------------------------------------ une ile
class Ile:
    """Le cote ile du pont : un monde, son courrier entrant, son courrier sortant."""

    def __init__(self, nom, w):
        self.nom, self.w, self.sortant = nom, w, []

    def pas(self, entrant):
        for m in entrant: self.w.recevoir_courrier(m)
        self.w.pas_suivant()
        e = getattr(self.w, "enregistreur", None)
        if e is not None and self.w.pas % C.PAS_PAR_JOUR == 0: e.fin_de_jour((self.w.pas - 1) // C.PAS_PAR_JOUR)
        s, self.w.courrier_sortant = self.w.courrier_sortant, []
        return s

    def commande(self, ordre, *args):
        if ordre == "empreinte": return empreinte(self.w)
        if ordre == "resume":
            t = self.w.table; n = t.n
            return {"ile": self.nom, "jour": self.w.jour, "pas": self.w.pas, "habitants": n, "vivants": int(t.vivant[:n].sum())}
        if ordre == "instantane":                   # ecrit a cote puis renomme : un lecteur ne voit jamais une ile a moitie
            with open(args[0] + ".tmp", "wb") as f: pickle.dump(self.w, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(args[0] + ".tmp", args[0])
            return True
        if ordre == "corps":                        # le recensement de l archipel : qui a un corps ici, qui est absent
            t = self.w.table; n = t.n
            viv = t.vivant[:n] == 1
            ici = t.statut[:n] == 0
            # un detenu ( domaine 21 ) est marque ABSENT pour que le moteur le sorte de son travail et de son menage,
            # mais son corps est ICI, en prison ( 27/09 : la porte G4 le comptait absent, sans corps ailleurs )
            p = getattr(self.w, "pays", None)
            if p is not None and "ju_detenu" in p.colonnes["habitant"]: ici = ici | (p.col("habitant", "ju_detenu")[:n] > 0)
            return {"residents": t.nia[:n][viv & ici].tolist(), "absents": t.nia[:n][viv & ~ici].tolist(),
                    "etrangers": sorted(self.w.etrangers)}
        if ordre == "etat":                         # le bulletin de la nuit
            w = self.w; t = w.table; n = t.n
            tenue, msg = w.pays.socle.conservation.tenue() if getattr(w, "pays", None) else (True, "")
            dec = next((e for e in reversed(w.evenements) if e.get("type") == "decision_gouvernement"), None)
            o = getattr(w, "etalon_or", {})
            # la faim sur les menages qui ont un vivant ( ~29 % de la liste sont vides : 71 % sur la liste = 100 % des
            # menages vivants, 26/09 ) ; « faim_liste » garde l ancien rapport pour comparer aux nuits d avant
            ins = PO.menages_inscrits(t, n)
            habites = int((np.bincount(ins[(t.vivant[:n] == 1) & (ins >= 0)], minlength=len(w.menages)) > 0).sum())
            sans = w.stats_jour.get("menages_sans_nourriture", 0)
            return {"ile": self.nom, "jour": w.jour, "vivants": int(t.vivant[:n].sum()), "habitants": n,
                    "faim": sans / max(1, habites), "faim_liste": sans / max(1, len(w.menages)), "menages_habites": habites,
                    "conservation": bool(tenue), "monnaie": o.get("monnaie"), "euros_par_unite": o.get("dernier_taux"),
                    "or_euros_g": o.get("cours"), "etrangers": len(w.etrangers), "absents": len(w.absents),
                    "gouvernement": None if dec is None else {"cerveau": dec.get("cerveau"), "motifs": str(dec.get("motifs"))[:160],
                                                              "actions": len(dec.get("actions", [])),
                                                              "acceptees": sum(1 for a in dec.get("actions", []) if a.get("acceptee"))}}
        if ordre == "etrangers":
            return [(c["nia"], c["origine"], c["depart_pas"], c["arrivee_pas"]) for c in self.w.etrangers.values()]
        if ordre == "tenue":
            return self.w.pays.socle.conservation.tenue() if getattr(self.w, "pays", None) else (True, "sans socle")
        if ordre == "frontiere":                    # ( ouverte, iles refusees )
            self.w.frontiere = {"ouverte": args[0], "refuses": set(args[1])}; return True
        if ordre == "guerre_releve":                # la guerre des iles ( guerre/ ) : ce que l Etat a percu depuis la releve
            from guerre import moteur as GM
            return GM.releve_de_guerre(self.w)
        if ordre == "occuper":                      # une zone tenue par l envahisseur dans Arma : ses sites ne produisent plus
            from guerre import moteur as GM
            return GM.occuper(self.w, *args)
        if ordre == "guerre_gouverner":             # le conseil de guerre a adopte un nouveau gouvernement ( guerre/conseil.py )
            from guerre import moteur as GM
            return GM.gouverner_par(self.w, *args)
        if ordre == "guerre_voir":                  # le gouvernement de l ile voit la guerre dans son bulletin ( guerre/moteur.py )
            from guerre import moteur as GM
            return GM.voir_la_guerre(self.w)
        if ordre in ("guerre_mobiliser", "guerre_suivre", "guerre_morts", "guerre_payer"):   # soldats au front, achats ( guerre/moteur.py )
            from guerre import moteur as GM
            f = {"guerre_mobiliser": GM.mobiliser, "guerre_suivre": GM.suivre, "guerre_morts": GM.morts_au_combat,
                 "guerre_payer": GM.payer_la_guerre}[ordre]
            return f(self.w, *args)
        if ordre == "tourisme_risque":              # l avis aux voyageurs de l ile ( domaine 28 ; guerre/horloge.py )
            from monde.pays import d28_tourisme as TO
            return TO.fixer_risque(self.w.pays, *args)
        if ordre == "tourisme_etat":
            from monde.pays import d28_tourisme as TO
            return TO.etat_tourisme(self.w.pays)
        if ordre == "perturber":                    # controle positif des portes : un milliardieme de drachme
            self.w.table.menages.caisse[0] += 1e-9; return True
        raise ValueError(ordre)


def gouvernements(spec, noms):
    """{ ile : source } du gouvernement de chaque ile ( 26/09 : les decisions sont du code ). `spec` : None ( les
    regles du domaine 6 ), un dict { ile : source }, le chemin d un .py ( le meme code partout ) ou d un dossier
    ( <dossier>/<Ile>.py ; une ile sans fichier garde les regles )."""
    if not spec: return {}
    if isinstance(spec, dict): return dict(spec)
    if os.path.isdir(spec):
        return {n: open(os.path.join(spec, f"{n}.py")).read() for n in noms if os.path.exists(os.path.join(spec, f"{n}.py"))}
    src = open(spec).read()
    return {n: src for n in noms}


def poser_gouvernement(w, nom, source):
    """Le code gouverne le pays ( CerveauCode, bac a sable ) ; sans code, les regles."""
    if source is None: return
    from . import agent_codeur as AC                   # ( import tardif : agent_codeur importe archipel )
    w.cerveau = AC.CerveauCode(source, nom=nom)


def _processus_ile(nom, graine, echelle, reprise, tuyau, noms=None, ouvert=False, llm=False, enregistrer=None, gouv=None):
    # 27/09 : le domaine 22 fait des produits de matrices ( faits x lieux x lieux ) ; six iles qui prennent chacune tous
    # les coeurs se marchent dessus ( 120 fils pour 20 coeurs ). Chaque ile garde sa part ( HMT_FILS_PAR_ILE pour forcer ) ;
    # le nombre de fils ne change pas les resultats ( porte des 27 domaines identique a 3 fils et a 20 )
    from threadpoolctl import threadpool_limits
    n_iles = max(1, len(noms) if noms else 1)
    threadpool_limits(int(os.environ.get("HMT_FILS_PAR_ILE", max(1, (os.cpu_count() or 1) // n_iles))), user_api="blas")
    w = _convois(charger(reprise), echelle) if reprise else creer_ile(nom, graine, echelle, llm)
    poser_gouvernement(w, nom, gouv)
    if ouvert: w.archipel = {"noms": tuple(noms), "ouvert": True}
    if enregistrer: ENR.brancher(w, enregistrer, nom)
    ile = Ile(nom, w)
    tuyau.send(("pret", nom))
    while True:
        m = tuyau.recv()
        if m[0] == "pas": tuyau.send(ile.pas(m[1]))
        elif m[0] == "fin":
            if getattr(w, "enregistreur", None) is not None: w.enregistreur.fermer()
            tuyau.send("fin"); return
        else: tuyau.send(ile.commande(*m))


# ------------------------------------------------------------------ le pont
class Archipel:
    def __init__(self, iles=C.ILES_ARCHIPEL, graine=C.GRAINE, echelle=4.0, parallele=True, reprise=None, ouvert=False,
                 llm=False, enregistrer=None, gouvernement=None):
        """`enregistrer` : un dossier ou chaque ile ecrit tout ce qui s y passe ( monde/enregistreur.py ).
        `gouvernement` : le code qui gouverne chaque ile ( voir gouvernements() ) ; sans, les regles ou le LLM."""
        gv = gouvernements(gouvernement, tuple(iles))
        self.noms, self.graine, self.echelle, self.parallele, self.ouvert = tuple(iles), graine, echelle, parallele, ouvert
        self.pas = 0
        self.mer = []                      # ( pas d arrivee, ile d origine, n d ordre, destination, message )
        self.journal = []                  # tout ce qui a traverse ( phase E )
        self.pas_temps_reel = 0
        if reprise:
            etat = pickle.load(open(os.path.join(reprise, "pont.pkl"), "rb"))
            self.pas, self.mer, self.journal = etat["pas"], etat["mer"], etat["journal"]
        chemin = (lambda n: os.path.join(reprise, f"{n}.pkl")) if reprise else (lambda n: None)
        if parallele:
            ctx = mp.get_context("fork")
            self.tuyaux, self.proc = {}, {}
            for n in self.noms:
                a, b = ctx.Pipe()
                p = ctx.Process(target=_processus_ile, args=(n, graine, echelle, chemin(n), b, self.noms, ouvert, llm, enregistrer, gv.get(n)), daemon=True)
                p.start(); self.tuyaux[n], self.proc[n] = a, p
            for n in self.noms: assert self.tuyaux[n].recv() == ("pret", n)
        else:
            self.iles = {n: Ile(n, _convois(charger(chemin(n)), echelle) if reprise else creer_ile(n, graine, echelle, llm))
                         for n in self.noms}
            if ouvert:
                for i in self.iles.values(): i.w.archipel = {"noms": self.noms, "ouvert": True}
            if enregistrer:
                for n, i in self.iles.items(): ENR.brancher(i.w, enregistrer, n)
            for n, i in self.iles.items(): poser_gouvernement(i.w, n, gv.get(n))

    # --- la vitesse : temps reel si un humain est la ---
    def temps_reel(self): return os.path.exists(HUMAIN)

    def _envoyer_a_tous(self, message_par_ile):
        if self.parallele:
            for n in self.noms: self.tuyaux[n].send(message_par_ile(n))
            return {n: self.tuyaux[n].recv() for n in self.noms}
        return {n: self._local(n, message_par_ile(n)) for n in self.noms}

    def _local(self, n, m):
        if m[0] == "pas": return self.iles[n].pas(m[1])
        return self.iles[n].commande(*m)

    def un_pas(self):
        t0 = time.time()
        reel = self.temps_reel()
        # le courrier qui arrive a ce pas, dans l ordre ( ile d origine, numero d ordre )
        arrive = sorted((x for x in self.mer if x[0] <= self.pas), key=lambda x: (x[0], x[1], x[2]))
        if self.pas in getattr(self, "inverser_au_pas", ()): arrive = arrive[::-1]     # controle positif de G3
        self.mer = [x for x in self.mer if x[0] > self.pas]
        entrant = {n: [x[4] for x in arrive if x[3] == n] for n in self.noms}
        sortant = self._envoyer_a_tous(lambda n: ("pas", entrant[n]))
        for n in self.noms:                               # ordre fixe des iles, puis ordre d emission
            for k, (dest, delai_pas, msg) in enumerate(sortant[n]):
                self.mer.append((self.pas + delai_pas, n, k, dest, msg)); self.journal.append((self.pas, n, dest, msg))
        self.pas += 1
        if reel:
            self.pas_temps_reel += 1
            reste = SECONDES_TEMPS_REEL - (time.time() - t0)
            if reste > 0: time.sleep(reste)

    def jours(self, n):
        for _ in range(n * C.PAS_PAR_JOUR): self.un_pas()

    def empreintes(self): return self._envoyer_a_tous(lambda n: ("empreinte",))
    def resumes(self): return self._envoyer_a_tous(lambda n: ("resume",))

    def instantane(self, dossier):
        """Une ile APRES l autre : 25/09, six sauvegardes simultanees d iles d un million d habitants ont depasse la
        memoire de WSL ( 47 Go ) et fige la station - chaque sauvegarde a son propre pic."""
        os.makedirs(dossier, exist_ok=True)
        for n in self.noms: self.commande(n, "instantane", os.path.join(dossier, f"{n}.pkl"))
        with open(os.path.join(dossier, "pont.pkl.tmp"), "wb") as f:
            pickle.dump({"pas": self.pas, "mer": self.mer, "journal": self.journal, "noms": self.noms,
                         "graine": self.graine, "echelle": self.echelle}, f)
        os.replace(os.path.join(dossier, "pont.pkl.tmp"), os.path.join(dossier, "pont.pkl"))

    def commande(self, ile, *m):
        if self.parallele: self.tuyaux[ile].send(m); return self.tuyaux[ile].recv()
        return self.iles[ile].commande(*m)

    def en_mer(self):
        """Les corps en traversee : ( numero d archipel, genre, depart, arrivee prevue, destination )."""
        return [(x[4][1]["nia"], x[4][0], x[1], x[0], x[3]) for x in self.mer]

    def perturber(self, ile):
        if self.parallele: self.tuyaux[ile].send(("perturber",)); return self.tuyaux[ile].recv()
        return self.iles[ile].commande("perturber")

    def fermer(self):
        if not self.parallele:
            for i in self.iles.values():
                if getattr(i.w, "enregistreur", None) is not None: i.w.enregistreur.fermer()
        if self.parallele:
            for n in self.noms:
                try: self.tuyaux[n].send(("fin",)); self.tuyaux[n].recv()
                except Exception: pass
            for p in self.proc.values(): p.join(timeout=10)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--jours", type=int, default=2)
    a.add_argument("--echelle", type=float, default=4.0)
    a.add_argument("--sequentiel", action="store_true")
    x = a.parse_args()
    t0 = time.time()
    arc = Archipel(echelle=x.echelle, parallele=not x.sequentiel)
    print(f"archipel pret en {time.time() - t0:.1f} s ( {'sequentiel' if x.sequentiel else 'six processus'} )", flush=True)
    for j in range(x.jours):
        t0 = time.time(); arc.jours(1)
        r = arc.resumes()
        print(f"jour {j + 1} : {time.time() - t0:.1f} s | " + " | ".join(f"{n} {v['vivants']}" for n, v in r.items()), flush=True)
    arc.fermer()
    return 0


if __name__ == "__main__":
    sys.exit(main())
