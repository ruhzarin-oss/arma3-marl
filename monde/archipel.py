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
from . import monde as W, tests as T, config as C, or_reel as OR, enregistreur as ENR
from .pays import pays as P
from .porte_domaines import LIVRES, empreinte

DOSSIER = "/mnt/data/hmt/archipel"
HUMAIN = os.path.join(DOSSIER, "HUMAIN")          # present = un humain est connecte : le temps reel
SECONDES_TEMPS_REEL = C.MINUTES_PAR_PAS * 60.0


def graine_ile(graine, ile):
    """La graine d une ile : derivee de celle de l archipel et du NOM de l ile ( la meme ile seule a la meme graine )."""
    return int.from_bytes(hashlib.sha256(f"{graine}:{ile}".encode()).digest()[:4], "little")


def creer_ile(ile, graine, echelle, llm=False):
    """Un pays : son monde, ses domaines, son etalon-or ( F1 ) ; avec `llm`, son gouvernement est joue par Qwen, qui
    sait de quel pays il est le gouvernement et dans quelle monnaie il compte."""
    w = W.Monde(graine=graine_ile(graine, ile), iles=(ile,), echelle=echelle, cerveau="llm" if llm else "regles")
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
        if ordre == "instantane":
            with open(args[0], "wb") as f: pickle.dump(self.w, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        if ordre == "corps":                        # le recensement de l archipel : qui a un corps ici, qui est absent
            t = self.w.table; n = t.n
            viv = t.vivant[:n] == 1
            return {"residents": t.nia[:n][viv & (t.statut[:n] == 0)].tolist(),
                    "absents": t.nia[:n][viv & (t.statut[:n] == 1)].tolist(), "etrangers": sorted(self.w.etrangers)}
        if ordre == "etat":                         # le bulletin de la nuit
            w = self.w; t = w.table; n = t.n
            tenue, msg = w.pays.socle.conservation.tenue() if getattr(w, "pays", None) else (True, "")
            dec = next((e for e in reversed(w.evenements) if e.get("type") == "decision_gouvernement"), None)
            o = getattr(w, "etalon_or", {})
            return {"ile": self.nom, "jour": w.jour, "vivants": int(t.vivant[:n].sum()), "habitants": n,
                    "faim": w.stats_jour.get("menages_sans_nourriture", 0) / max(1, len(w.menages)),
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
        if ordre == "perturber":                    # controle positif des portes : un milliardieme de drachme
            self.w.table.menages.caisse[0] += 1e-9; return True
        raise ValueError(ordre)


def _processus_ile(nom, graine, echelle, reprise, tuyau, noms=None, ouvert=False, llm=False, enregistrer=None):
    w = pickle.load(open(reprise, "rb")) if reprise else creer_ile(nom, graine, echelle, llm)
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
                 llm=False, enregistrer=None):
        """`enregistrer` : un dossier ou chaque ile ecrit tout ce qui s y passe ( monde/enregistreur.py )."""
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
                p = ctx.Process(target=_processus_ile, args=(n, graine, echelle, chemin(n), b, self.noms, ouvert, llm, enregistrer), daemon=True)
                p.start(); self.tuyaux[n], self.proc[n] = a, p
            for n in self.noms: assert self.tuyaux[n].recv() == ("pret", n)
        else:
            self.iles = {n: Ile(n, pickle.load(open(chemin(n), "rb")) if reprise else creer_ile(n, graine, echelle, llm))
                         for n in self.noms}
            if ouvert:
                for i in self.iles.values(): i.w.archipel = {"noms": self.noms, "ouvert": True}
            if enregistrer:
                for n, i in self.iles.items(): ENR.brancher(i.w, enregistrer, n)

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
        with open(os.path.join(dossier, "pont.pkl"), "wb") as f:
            pickle.dump({"pas": self.pas, "mer": self.mer, "journal": self.journal, "noms": self.noms,
                         "graine": self.graine, "echelle": self.echelle}, f)

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
