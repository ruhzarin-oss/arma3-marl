"""Le coeur du monde : l etat du pays et son pas de 10 minutes. Hors d Arma ( etape E1 ) : ici tout est donnee.
Invariants verifies par les tests : l argent et les biens se CONSERVENT - rien n apparait ni ne disparait sans une
cause ecrite au journal ( production, consommation, combustion, import, export, mort )."""
import collections, json, math
import numpy as np
from . import config as C, carte as K, population as P, economie as E, gouvernement as G, ecole as S, agents as A, roles as R
try:
    import coeur as COEUR          # le coeur Rust ( coeur_rust/ ) : les routines de masse sur tous les coeurs
except ImportError:                # sans lui, le monde tourne en Python, a l identique mais plus lentement
    COEUR = None

CATEGORIES_PUBLIQUES = ("hopitaux", "armee", "reserve", "population")


class ParMenage:
    """Une valeur par menage, lisible comme un dictionnaire ( `.get(menage, defaut)` ) ET comme un tableau ( `[i]`,
    `len` ). Les domaines du pays ( monde/pays/ ) l ont connue dictionnaire ; le moteur en colonnes la tient en tableau.
    Un menage hors du tableau ( ne apres le repas ) rend la valeur par defaut, comme une cle absente."""
    __slots__ = ("v",)

    def __init__(self, v): self.v = v
    def get(self, k, defaut=None): return bool(self.v[k]) if 0 <= k < len(self.v) else defaut
    def __getitem__(self, k): return bool(self.v[k])
    def __setitem__(self, k, x): self.v[k] = x
    def __len__(self): return len(self.v)
    def __contains__(self, k): return 0 <= k < len(self.v)


class ListeTravail(list):
    """Ceux qui travaillent a ( lieu, metier ), comme les rendait l ancien index `monde._par_travail` : une liste
    neuve, dont `append` et `remove` tiennent l index du moteur ( embauche, licenciement en cours de journee )."""
    __slots__ = ("_w", "_cle")

    def append(self, h):
        list.append(self, h); self._w._travail_ajouts.setdefault(self._cle, []).append(h.id)

    def remove(self, h):
        list.remove(self, h)
        ajouts = self._w._travail_ajouts.get(self._cle)
        if ajouts and h.id in ajouts: ajouts.remove(h.id)
        else: self._w._travail_retraits.setdefault(self._cle, set()).add(h.id)


class ParTravail:
    """L ancien index `monde._par_travail` - { ( id du lieu, metier ) : [ habitants ] } - pour le code ecrit avant les
    colonnes ( les domaines du pays, monde/pays/ ). Lire, ajouter et retirer passent par l index du moteur."""
    __slots__ = ("_w",)

    def __init__(self, w): self._w = w

    def _valide(self, cle):
        return isinstance(cle, tuple) and len(cle) == 2 and cle[0] in self._w.carte.lieux and cle[1] in P.CODE_ROLE

    def __getitem__(self, cle):
        if not self._valide(cle): raise KeyError(cle)
        w = self._w
        lieu = w.carte.lieux[cle[0]]
        l = ListeTravail(w.au_travail_de(lieu, cle[1]))
        l._w, l._cle = w, w._cle_travail(lieu, cle[1])
        return l

    def get(self, cle, defaut=None): return self[cle] if self._valide(cle) else defaut
    def setdefault(self, cle, defaut=None): return self[cle]
    def __contains__(self, cle): return self._valide(cle) and self._w.nombre_au_travail(self._w.carte.lieux[cle[0]], cle[1]) > 0


class Monde:
    def __init__(self, graine=C.GRAINE, cerveau="regles", epidemie_jour=2, journal=None, eleve=None, iles=("Altis",),
                 echelle=1.0):
        self.rng = np.random.default_rng(graine)
        self.graine = graine
        self.carte = K.Carte(iles=tuple(iles))
        self.table = P.Table(self.carte.par_n)          # les habitants en colonnes ( ce que lit le coeur Rust )
        # le marche dont depend chaque lieu, par numero ( -1 : aucun ) - l index de la population par marche le lit
        self._marche_du_lieu = np.array([l.marche.n if l.marche is not None else -1 for l in self.carte.par_n], np.int64)
        self._ile_du_lieu = np.array([self.carte.iles.index(l.ile) for l in self.carte.par_n], np.int16)
        self.habitants, self.menages = P.generer(self.carte, self.rng, echelle, self.table)
        self.utiliser_coeur = COEUR is not None
        self._colonnes_fraiches = False                 # vrai quand `deplacer` a rempli la colonne « travaille » ce pas
        self.pas = 0
        self.journal_fichier = journal
        self.evenements = []
        # --- les entreprises : une ferme par village, un site par lieu industriel ---
        self.entreprises = {}
        for l in self.carte.de_type("village"): self.entreprises[l.id] = E.Entreprise(l, "ferme")
        for l in self.carte.de_type(*[t for t in C.RECETTES if t != "ferme"]): self.entreprises[l.id] = E.Entreprise(l, l.type)
        # le role qu attend l entreprise de chaque lieu ( -1 : pas d entreprise ) : la production en colonnes le lit
        self._role_entreprise = np.full(len(self.carte.par_n), -1, np.int16)
        for e in self.entreprises.values(): self._role_entreprise[e.lieu.n] = P.CODE_ROLE.get(e.role, -1)
        patrons = [h for h in self.habitants if h.role == "patron"]
        privees = [e for e in self.entreprises.values() if e.type != "ferme"]
        for k, e in enumerate(privees): e.proprietaire = patrons[k % len(patrons)]
        for e in self.entreprises.values():            # stock de depart : deux jours d intrants
            for b, q in e.intrants.items(): e.stocks[b] = 16 * q * 4
        # --- les marches, le reseau, l Etat ---
        self.marches = {c.id: E.Marche(c) for c in self.carte.capitales}
        for m in self.marches.values():
            m.stocks.update({"nourriture": 600.0, "carburant": 300.0, "remedes": 40.0, "fer": 100.0, "zinc": 60.0,
                             "petrole": 200.0, "outils": 10.0})
        self.reseau = E.Reseau()
        self.gouv = G.Gouvernement()
        self.gouv.membres = [h for h in self.habitants if h.role in ("chef_gouvernement", "ministre")]
        for k, h in enumerate([h for h in self.habitants if h.role == "ministre"]):
            h.nom += "-" + C.MINISTERES[k % len(C.MINISTERES)]      # un pays plus grand a plusieurs ministres par portefeuille
        self.publics = {c: {b: 0.0 for b in C.BIENS} for c in CATEGORIES_PUBLIQUES}
        self.publics["hopitaux"]["remedes"] = 30.0
        self.publics["armee"]["carburant"] = 150.0
        self.publics["reserve"]["or"] = 20.0
        self.depot_armee = self.carte.lieux["storage01"]
        # point 6 : chaque base tient SON carburant. Un depot national ne pouvait jamais etre coupe de quoi que ce soit.
        self.garnisons = {b.id: {"carburant": 0.0} for b in self.carte.de_type("base")}
        for b in self.carte.de_type("base"):        # cinq jours d autonomie : une base n est ni a sec ni intarissable
            self.garnisons[b.id]["carburant"] = 5 * self.besoin_patrouille(b)
        self.convois = []; self.n_convoi = 0
        self.conducteur_libre = {h.id: 0 for h in self.habitants if h.role == "convoyeur"}
        self._pop_marche = {}
        self.indexer()
        self.cerveau = G.CerveauLLM() if cerveau == "llm" else None
        self.marchand = None               # pose par monde/apprenti.py : le reseau qui apprend a expedier
        self.doctrine = None               # posee par monde/former.py : ce que les menages ont appris ( point 1 )
        self.agents = {}                   # groupes d agents installes ( roles.py ) : nom -> Groupe ; absent = la regle
        self.faim_region = {}; self.nourri_menage = ParMenage(np.ones(0, bool)); self.infectes_du_jour = set(); self.contagions_lieu = {}
        self.amendes_menage = {}; self.intensite_controle = 1.0
        self.patrouilles_jour = {}; self.derniere_livraison = {}; self.livraison_ratee = {}
        self.coupures = []                 # routes coupees pour un temps : [{ lieu, debut, jours }]
        self.fret_aveugle = False          # temoin des voyageurs : toujours la nourriture vers l ile la plus chere
        self.menagiers = {}                # la memoire propre de chaque menage
        self.memoire_gouv = ""
        self.epidemie_jour = epidemie_jour
        # --- les comptes : tout ce qui entre, sort, se cree ou se detruit ---
        self.ext = {"entree": 0.0, "sortie": 0.0}
        self.flux = {k: {b: 0.0 for b in C.BIENS} for k in ("produit", "consomme", "brule", "importe", "exporte")}
        self.argent_depart = self.argent_total()
        self.biens_depart = self.biens_totaux()
        self.stats_jour = {}
        self.ecole = S.Ecole(self, eleve) if eleve is not None else None
        self.tva_percue = 0.0; self.tva_fraudee = 0.0     # point 8 : ce que l Etat encaisse, et ce qui lui echappe
        self.apprentissage = True       # faux pendant une qualification : l agent agit, il n apprend plus
        self.voyages = []               # point 13 : ceux qui sont EN MER entre deux iles
        self.sejours = {}               # id -> pas de fin : ceux qui sont sur l autre ile, en visite
        self.chocs = []                 # secheresses : [{ debut, jours, lieux, facteur }] - le rendement des fermes baisse
        self.routes_coupees = set()     # lieux que plus aucun convoi ne peut atteindre ni quitter ( controle positif, E1 )

    # ------------------------------------------------------------------ le temps
    @property
    def minutes(self): return C.DATE_DEPART[3] * 60 + C.DATE_DEPART[4] + self.pas * C.MINUTES_PAR_PAS

    @property
    def jour(self): return self.minutes // (24 * 60)

    @property
    def heure(self): return (self.minutes % (24 * 60)) / 60.0

    def nuit(self): return not (C.LEVER <= self.heure < C.COUCHER)

    def noter(self, type_, **champs):
        e = {"jour": self.jour, "heure": round(self.heure, 2), "type": type_, **champs}
        self.evenements.append(e)
        if self.journal_fichier:
            with open(self.journal_fichier, "a") as f: f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ les comptes
    def argent_total(self):
        return (sum(m.caisse for m in self.menages) + sum(e.caisse for e in self.entreprises.values())
                + sum(m.caisse for m in self.marches.values()) + self.gouv.caisse)

    def biens_totaux(self):
        t = {b: 0.0 for b in C.BIENS}
        for e in self.entreprises.values():
            for b in C.BIENS: t[b] += e.stocks[b]
        for m in self.marches.values():
            for b in C.BIENS: t[b] += m.stocks[b]
        for p in self.publics.values():
            for b in C.BIENS: t[b] += p[b]
        for g in self.garnisons.values(): t["carburant"] += g["carburant"]
        for c in self.convois:
            for b, q in c.cargaison.items(): t[b] += q
        for v in getattr(self, "voyages", []):       # ce qui est en mer existe encore ( absent a la naissance du monde )
            for b, q in v.get("cargaison", {}).items(): t[b] += q
        t["nourriture"] += sum(m.garde_manger for m in self.menages)
        t["electricite"] += self.reseau.stock
        return t

    def transferer(self, de, vers, montant, motif):
        """Tout paiement interne passe ici. `de` et `vers` ont un attribut caisse. Rend le montant reellement paye."""
        montant = max(0.0, min(montant, de.caisse))
        de.caisse -= montant; vers.caisse += montant
        return montant

    def reserve_marche(self, m, b):
        """Ce qu un marche garde pour lui : trois jours de nourriture pour sa population, de quoi faire rouler ses convois."""
        if b == "nourriture":
            return 3 * C.NOURRITURE_PAR_JOUR * self._pop_marche.get(m.lieu.id, 0)
        if b == "carburant": return 120.0
        return 20.0

    def prix_moyen(self, b): return sum(m.prix[b] for m in self.marches.values()) / len(self.marches)

    # ------------------------------------------------------------------ le port et l Etat
    def importer(self, b, q, cout):
        self.gouv.caisse -= cout; self.ext["sortie"] += cout
        self.publics["reserve"][b] += q; self.flux["importe"][b] += q
        self.noter("import", bien=b, quantite=q, cout=round(cout))

    def exporter_or(self, q):
        q = min(q, self.publics["reserve"]["or"])
        if q <= 0: return False, "pas d or en reserve"
        gain = q * C.PRIX_MONDE["or"]
        self.publics["reserve"]["or"] -= q; self.flux["exporte"]["or"] += q
        self.gouv.caisse += gain; self.ext["entree"] += gain
        self.noter("export_or", quantite=round(q, 2), gain=round(gain)); return True, ""

    def subventionner(self, cible, montant):
        if cible == "menages_pauvres":
            pauvres = sorted(self.menages, key=lambda m: m.caisse)[:max(1, len(self.menages) // 5)]
            for m in pauvres: self.transferer(self.gouv, m, montant / len(pauvres), "subvention")
        elif cible == "fermes":
            fermes = [e for e in self.entreprises.values() if e.type == "ferme"]
            for e in fermes: self.transferer(self.gouv, e, montant / len(fermes), "subvention")
        elif cible == "hopitaux":
            self.gouv.commandes.append({"bien": "remedes", "quantite": montant / (self.prix_moyen("remedes") * 1.1),
                                        "destination": "hopitaux"})
        else: return False, f"cible inconnue {cible}"
        self.noter("subvention", cible=cible, montant=round(montant)); return True, ""

    # ------------------------------------------------------------------ un pas de 10 minutes
    def pas_suivant(self):
        h = self.heure
        debut_heure = (self.minutes % 60) == 0
        if self.minutes % (24 * 60) == 6 * 60: self.aube()
        self.deplacer(h)
        self.produire(h)
        if debut_heure:
            self.expedier(h)
            self.contagion()
        self.arrivees()
        if self.minutes % (24 * 60) == C.HEURE_PAIE * 60: self.paie()
        if self.minutes % (24 * 60) == 19 * 60: self.achats()
        if self.minutes % (24 * 60) == 20 * 60: self.repas()
        if self.minutes % (24 * 60) in (8 * 60, 20 * 60): self.patrouilles()
        if self.minutes % (24 * 60) == 7 * 60: self.ravitailler_bases()
        self.debarquer()
        if self.minutes % (24 * 60) == 8 * 60: self.commerce_exterieur()
        if self.ecole is not None:
            mm = self.minutes % (24 * 60)
            if mm == 8 * 60: self.ecole.instruction()
            elif mm == 11 * 60: self.ecole.exercice_du_jour()
            elif mm == 14 * 60: self.ecole.debrief()
            elif mm == 15 * 60 and self.jour % 3 == 2: self.ecole.qualification()
            elif mm == 19 * 60 + 10: self.ecole.observer_marche()
        self.pas += 1

    def economie_entreprise(self, e):
        """Ce qu une entreprise sait de son affaire : son marche, son produit principal, sa recette, son cout, sa cible."""
        m = self.marches[e.lieu.marche.id]
        b = max(e.produits, key=lambda x: e.produits[x] * C.PRIX_MONDE[x] if x != "or" else 0)
        recette = sum(q * m.prix[x] * (1 - m.marge) for x, q in e.produits.items())
        cout = P.SALAIRE_HORAIRE.get(e.role, 0) + sum(q * (self.reseau.tarif if x == "electricite" else m.prix[x])
                                                      for x, q in e.intrants.items())
        cible = self.reserve_marche(m, b) * 2 if b == "nourriture" else C.STOCK_CIBLE
        return m, b, recette, cout, cible

    def regler_activite(self):
        """Chaque matin, l entreprise regle son activite sur son marche : elle ralentit quand le stock de son produit
        principal y depasse sa cible, accelere quand il manque, et s arrete presque quand elle perd de l argent."""
        for e in self.entreprises.values():
            if e.type == "centrale": continue                       # la centrale suit deja le reseau
            if "or" in e.produits: e.activite = 1.0; continue       # l or se vend toujours, au prix mondial
            m, b, recette, cout, cible = self.economie_entreprise(e)
            # ! 22/09 : ni la moyenne des marches ( la raffinerie a 15 % pendant que Pyrgos manquait ) ni le marche le plus a
            # court ( le puits surproduisait un petrole que seule Athira emploie, et faisait faillite ). Une entreprise produit
            # tant que son PRIX couvre son COUT, et ralentit quand son propre marche deborde.
            if m.stocks[b] > 2 * cible or recette < 0.95 * cout: e.activite = max(0.1, e.activite - 0.25)
            elif m.stocks[b] < cible and recette > 1.05 * cout: e.activite = min(1.0, e.activite + 0.25)

    # --- point 13 : le voyage entre iles -------------------------------------------------------------------
    def marchand_libre(self, ile):
        """Le premier marchand ( dans l ordre des habitants ) vivant, a terre, pas en sejour, et sur cette ile."""
        t, n = self.table, self.table.n
        lieu = t.lieu[:n]
        ok = ((t.vivant[:n] == 1) & (t.role[:n] == P.CODE_ROLE["marchand"]) & (t.poste[:n] != P.CODE_POSTE["voyage"])
              & (lieu >= 0))
        ok &= self._ile_du_lieu[np.where(lieu >= 0, lieu, 0)] == self.carte.iles.index(ile)
        for i in np.nonzero(ok)[0]:
            if int(i) not in self.sejours: return P.Habitant(t, int(i))
        return None

    def embarquer(self, h, cible, demenage=False, sejour_jours=0.0, cargaison=None, marche_origine=None, marche_dest=None):
        """Un habitant quitte son ile. Pendant la traversee il n est nulle part : aucun corps, ni ici ni la-bas.
        C est la condition pour qu il n existe jamais en double."""
        km = self.carte.km_mer(h.lieu if h.lieu is not None else h.domicile, cible)
        minutes = 60.0 * km / K.VITESSE_MER_KMH
        pas = self.pas + max(1, int(minutes / C.MINUTES_PAR_PAS))
        self.voyages.append({"habitant": h, "arrivee": pas, "cible": cible, "demenage": demenage,
                             "sejour": sejour_jours, "cargaison": dict(cargaison or {}),
                             "marche_origine": marche_origine, "marche_dest": marche_dest})
        h.lieu, h.poste = None, "voyage"
        self.noter("embarquement", habitant=h.id, vers=cible.id, ile=cible.ile, km=round(km, 1),
                   heures=round(minutes / 60.0, 1))
        return pas

    def debarquer(self):
        for v in [v for v in self.voyages if v["arrivee"] <= self.pas]:
            self.voyages.remove(v)
            h, cible = v["habitant"], v["cible"]
            if v.get("cargaison"):
                # le fret arrive : le marche d arrivee recoit la marchandise et paie celui d origine a son prix
                dest, orig = self.marches[v["marche_dest"]], self.marches[v["marche_origine"]]
                for b, q in v["cargaison"].items():
                    dest.stocks[b] += q; dest.offre[b] += q
                    self.transferer(dest, orig, min(dest.caisse, q * orig.prix[b]), "fret maritime")
                self.noter("fret_arrive", vers=dest.lieu.id, cargaison={b: round(q, 1) for b, q in v["cargaison"].items()})
                v["cargaison"] = {}
            if not h.vivant: continue
            h.lieu, h.poste = cible, "maison"
            if v["demenage"]:
                h.domicile = cible
                if h.menage is not None: h.menage.domicile = cible
                h.travail = cible
            elif v["sejour"] > 0:
                # il est en visite : il reste sur place le temps prevu, puis reprend le bateau
                self.sejours[h.id] = self.pas + int(v["sejour"] * C.PAS_PAR_JOUR)
            self.noter("debarquement", habitant=h.id, lieu=cible.id, ile=cible.ile)

    def commerce_exterieur(self):
        """Point 13 : une raison de traverser. Chaque matin, un marchand disponible part vendre sur l autre ile et y
        reste deux jours. Sans cela le voyage serait une mecanique sans usage.
        Avec le groupe « voyageurs », chaque ile decide si elle envoie un bateau, et avec quelle cargaison."""
        gv = self.agents.get("voyageurs")
        if gv or self.fret_aveugle:
            R.decider_voyageurs(self, gv, aveugle=self.fret_aveugle and not gv)
            return
        autres = [i for i in self.carte.iles if i != self.carte.iles[0]]
        if not autres: return
        for ile in autres:
            cible = next((l for l in self.carte.lieux.values() if l.ile == ile and l.type == "capitale"), None)
            if cible is None: continue
            libre = self.marchand_libre(self.carte.iles[0])
            if libre is None: continue
            self.embarquer(libre, cible, sejour_jours=2.0)

    def demographie(self):
        """Point 5 : on nait, on vieillit, on part a la retraite, on meurt de vieillesse. Une fois par jour du monde.
        En colonnes quand la table est la ; `demographie_python` reste la reference, et la porte compare au centime.
        Les tirages suivent l ordre de la boucle Python : un par vivant, puis un par menage eligible. Les evenements
        rares ( morts, retraites, entrees dans la vie active ) sont traites un par un, dans l ordre des habitants :
        l embauche d un jeune depend des embauches qui la precedent."""
        if not self.utiliser_coeur: return self.demographie_python()
        t, n = self.table, self.table.n
        vivants = np.nonzero(t.vivant[:n] == 1)[0]
        t.age[vivants] += 1.0 / C.JOURS_PAR_AN
        age = t.age[vivants]
        limites = np.array([lim for lim, _ in C.MORTALITE_AN]); taux = np.array([r for _, r in C.MORTALITE_AN])
        risque = taux[np.minimum(np.searchsorted(limites, age, side="right"), len(taux) - 1)]
        morts = self.rng.random(vivants.size) < risque / C.JOURS_PAR_AN
        role = t.role[vivants]
        r_retraite, r_enfant = P.CODE_ROLE["retraite"], P.CODE_ROLE["enfant"]
        retraite = ~morts & (age >= C.AGE_RETRAITE) & (role != r_retraite) & (role != r_enfant)
        grandit = ~morts & ~retraite & (role == r_enfant) & (age >= C.AGE_TRAVAIL)
        rares = morts | retraite | grandit
        for i, mort, part in zip(vivants[rares], morts[rares], retraite[rares]):
            h = self.habitants[int(i)]
            if mort:
                h.vivant = False; h.lieu = None
                self.noter("mort_naturelle", habitant=h.id, age=round(h.age, 1), role=h.role)
            elif part:
                self.noter("retraite", habitant=h.id, age=round(h.age, 1), ancien_role=h.role)
                h.role, h.travail, h.horaire = "retraite", None, None
            else:
                self.embaucher(h)
        # les naissances : un tirage par menage qui a un adulte de moins de 45 ans, dans l ordre des menages
        n = t.n
        mm = P.menages_inscrits(t, n)
        adulte_jeune = (t.vivant[:n] == 1) & (t.role[:n] != r_enfant) & (t.age[:n] < 45) & (mm >= 0)
        eligibles = np.nonzero(np.bincount(mm[adulte_jeune], minlength=len(self.menages)))[0]
        nes = eligibles[self.rng.random(eligibles.size) < C.NAISSANCES_PAR_MENAGE_AN / C.JOURS_PAR_AN]
        for k in nes:
            mg = self.menages[int(k)]
            premier = next(x for x in mg.membres if x.vivant and x.role != "enfant" and x.age < 45)
            b = P.Habitant.nouveau(self.table, "enfant", premier.classe, 0)   # sa ligne est son numero
            b.menage, b.domicile, b.lieu = mg, mg.domicile, mg.domicile
            b.horaire, b.travail = "ecole", mg.domicile.marche
            mg.membres.append(b); self.habitants.append(b)
            self.noter("naissance", habitant=b.id, menage=mg.id, lieu=mg.domicile.id)

    def demographie_python(self):
        """La version d origine, une boucle sur chaque habitant : la reference de la porte des colonnes."""
        for h in self.habitants:
            if not h.vivant: continue
            h.age += 1.0 / C.JOURS_PAR_AN
            # la mort naturelle, par tranche d age
            risque = next(r for limite, r in C.MORTALITE_AN if h.age < limite)
            if self.rng.random() < risque / C.JOURS_PAR_AN:
                h.vivant = False; h.lieu = None
                self.noter("mort_naturelle", habitant=h.id, age=round(h.age, 1), role=h.role)
                continue
            # la retraite : il quitte son poste, son salaire devient une pension
            if h.age >= C.AGE_RETRAITE and h.role not in ("retraite", "enfant"):
                self.noter("retraite", habitant=h.id, age=round(h.age, 1), ancien_role=h.role)
                h.role, h.travail, h.horaire = "retraite", None, None
            # l enfant qui grandit : il prend un metier la ou il en manque le plus dans sa region
            elif h.role == "enfant" and h.age >= C.AGE_TRAVAIL:
                self.embaucher(h)
        # les naissances : un menage avec un adulte jeune, un nouveau-ne qui consomme et qui ira a l ecole
        for mg in list(self.menages):
            adultes = [x for x in mg.membres if x.vivant and x.role != "enfant" and x.age < 45]
            if not adultes: continue
            if self.rng.random() < C.NAISSANCES_PAR_MENAGE_AN / C.JOURS_PAR_AN:
                b = P.Habitant.nouveau(self.table, "enfant", adultes[0].classe, 0)   # sa ligne est son numero
                b.menage, b.domicile, b.lieu = mg, mg.domicile, mg.domicile
                b.horaire, b.travail = "ecole", mg.domicile.marche
                mg.membres.append(b); self.habitants.append(b)
                self.noter("naissance", habitant=b.id, menage=mg.id, lieu=mg.domicile.id)

    def embaucher(self, h):
        """Le premier marche du travail : le jeune prend le metier le plus depeuple de sa region, parmi les metiers
        libres ( un medecin ou un officier demande une qualification : ils ne s improvisent pas )."""
        # tout passe par les index du jour : un jeune qui recomptait le pays entier coutait, a 50 000 habitants,
        # 362 secondes sur les 386 d une journee ( profil du 23/09 ).
        libres = ("paysan", "mineur", "ouvrier", "convoyeur", "marchand", "petrolier", "soldat")
        manque = {r: self._compte_role.get(r, 0) / max(1, C.ROLES[r][0]) for r in libres}
        role = min(manque, key=manque.get)
        lieux = self._lieux_par_role.get(role, set())
        h.role, h.classe = role, C.ROLES[role][1]
        h.horaire = P.TRAVAIL[role][1]
        h.travail = min(lieux, key=lambda l: l.distance(h.domicile)) if lieux else h.domicile
        self._compte_role[role] = self._compte_role.get(role, 0) + 1           # il compte des maintenant
        self._compte_role["enfant"] = max(0, self._compte_role.get("enfant", 1) - 1)
        self._travail_ajouts.setdefault(self._cle_travail(h.travail, role), []).append(h.id)
        self.noter("entree_vie_active", habitant=h.id, role=role, lieu=getattr(h.travail, "id", None))

    def indexer(self):
        """Les index du pays, refaits une fois par jour, SUR LES COLONNES : population de chaque marche, habitants par
        ( lieu de travail, metier ) dans l ordre des habitants, compte par metier, lieux de chaque metier. Sans index,
        chaque marche et chaque entreprise reparcouraient toute la population a chaque pas ( 23/09 : 42 s par jour a
        50 000 habitants, 625 s a 200 000 )."""
        t, n = self.table, self.table.n
        vivant = t.vivant[:n] == 1
        mt = t.menages
        # la population de chaque marche : les vivants, comptes au marche du domicile de leur MENAGE
        mm = P.menages_inscrits(t, n)
        marche = self._marche_du_lieu[mt.domicile[:mt.n][mm[vivant & (mm >= 0)]]]
        comptes = np.bincount(marche[marche >= 0], minlength=len(self.carte.par_n))
        self._pop_marche = {self.carte.par_n[k].id: int(comptes[k]) for k in np.nonzero(comptes)[0]}
        # qui travaille ou : par ( lieu, metier ), dans l ordre des habitants ( tri stable )
        ro, tr, nr = t.role[:n], t.travail[:n], len(P.ROLES)
        par_role = np.bincount(ro[vivant & (ro >= 0)], minlength=nr)
        self._compte_role = {P.ROLES[r]: int(c) for r, c in enumerate(par_role) if c}
        occupes = np.nonzero(vivant & (tr >= 0))[0]
        cles = tr[occupes].astype(np.int64) * nr + ro[occupes]
        tri = np.argsort(cles, kind="stable")
        self._travail_ordre, cles = occupes[tri], cles[tri]
        uniques, debuts = np.unique(cles, return_index=True)
        fins = np.append(debuts[1:], len(cles))
        self._travail_tranches = {int(c): (int(d), int(f)) for c, d, f in zip(uniques, debuts, fins)}
        self._travail_ajouts = {}            # les embauches du jour, ajoutees a la fin de leur tranche
        self._travail_retraits = {}          # les departs du jour ( licenciements des domaines ), retires de leur tranche
        self._lieux_par_role = {}
        for c in uniques: self._lieux_par_role.setdefault(P.ROLES[int(c) % nr], set()).add(self.carte.par_n[int(c) // nr])

    def _cle_travail(self, lieu, role): return lieu.n * len(P.ROLES) + P.CODE_ROLE[role]

    @property
    def _par_travail(self): return ParTravail(self)

    def ids_au_travail(self, lieu, role):
        cle = self._cle_travail(lieu, role)
        d, f = self._travail_tranches.get(cle, (0, 0))
        ids = self._travail_ordre[d:f].tolist()
        partis = self._travail_retraits.get(cle)
        if partis: ids = [i for i in ids if i not in partis]
        return ids + self._travail_ajouts.get(cle, [])

    def au_travail_de(self, lieu, role):
        """Les habitants ( vues ) qui travaillent a ce lieu dans ce metier, dans l ordre des habitants."""
        t = self.table
        return [P.Habitant(t, i) for i in self.ids_au_travail(lieu, role)]

    def nombre_au_travail(self, lieu, role):
        cle = self._cle_travail(lieu, role)
        d, f = self._travail_tranches.get(cle, (0, 0))
        return (f - d) - len(self._travail_retraits.get(cle, ())) + len(self._travail_ajouts.get(cle, []))


    def aube(self):
        self.demographie()
        self.indexer()
        g = self.agents.get("armee")
        if g: R.noter_armee(self, g)          # les patrouilles d hier soir et de ce matin sont comptees
        self.patrouilles_jour = {}
        self.infectes_du_jour = set()
        self.contagions_lieu = {}             # nouvelles contaminations du jour, par lieu ( la note des travailleurs )
        self.routes_temporaires = {c["lieu"] for c in self.coupures if c["debut"] <= self.jour < c["debut"] + c["jours"]}
        g = self.agents.get("entreprises")
        if g: R.decider_entreprises(self, g)
        else: self.regler_activite()
        g = self.agents.get("marches")
        if g: R.decider_marches(self, g)
        else:
            for m in self.marches.values(): m.ajuster_prix()
        g = self.agents.get("travailleurs")
        if g: R.decider_travailleurs(self, g)
        self.reseau.tarif = max(0.5, C.MARGE_ELECTRICITE * (self.prix_moyen("carburant") + P.SALAIRE_HORAIRE["ouvrier"]) / 12.0)   # cout complet d une heure de centrale
        self.progression_maladie()
        if self.jour == self.epidemie_jour:
            cibles = self.rng.choice([h for h in self.habitants if h.domicile.id == "Pyrgos" and h.vivant], 3, replace=False)
            for h in cibles: h.etat, h.jours_etat = "E", 0.0
            self.noter("epidemie", patients_zero=[h.id for h in cibles], lieu="Pyrgos")
        self.gouverner()
        self.noter("aube", **self.resume_jour())

    # --- 1. les deplacements : au travail ou a la maison ( la quarantaine retient chez soi ) ---
    def deplacer(self, h):
        """Ou est chacun a ce pas : maison, travail, hopital. Par le coeur Rust sur les colonnes quand il est la ;
        la version Python ( `deplacer_python` ) reste la reference, et la porte compare les deux au centime."""
        if not self.utiliser_coeur or self.agents.get("travailleurs") is not None:
            self._colonnes_fraiches = False
            return self.deplacer_python(h)
        t, n = self.table, self.table.n
        # 1. les sejours arrives a terme, comme dans la boucle Python : vivant, pas en mer, dans l ordre des habitants
        if self.sejours:
            for pid in sorted(k for k, fin in self.sejours.items() if self.pas >= fin):
                p = self.habitants[pid]
                if p.vivant and p.poste != "voyage":
                    del self.sejours[pid]
                    self.embarquer(p, p.domicile)
        sauter = (t.poste[:n] == P.CODE_POSTE["voyage"]).astype(np.uint8)
        if self.sejours: sauter[np.fromiter(self.sejours, np.int64, len(self.sejours))] = 1
        # 2. la quarantaine : memes tirages, dans le meme ordre que la boucle Python ( rng.random(k) = k tirages )
        enferme = np.zeros(n, np.uint8)
        q = set(self.gouv.lois["quarantaine"])
        if q:
            qn = np.array([self.carte.lieux[x].n for x in q if x in self.carte.lieux], np.int32)
            dom_q = np.isin(t.domicile[:n], qn)
            trav_q = (t.travail[:n] >= 0) & np.isin(t.travail[:n], qn)
            hopital = (t.etat[:n] == P.CODE_ETAT["I"]) & (t.gravite[:n] > 0.3)
            k = np.nonzero((t.vivant[:n] == 1) & (sauter == 0) & ~hopital & (dom_q | trav_q))[0]
            if k.size: enferme[k] = self.rng.random(k.size) > C.QUARANTAINE_VIOLEE
        # 3. le coeur Rust, sur tous les coeurs
        COEUR.deplacer(h, C.ABSENCE_FAIM, C.MINUTES_PAR_PAS / 60.0, sauter, t.vivant[:n], t.etat[:n], t.gravite[:n],
                       t.horaire[:n], t.equipe[:n], t.decalage[:n], enferme, t.faim[:n], t.public[:n], t.travail[:n],
                       t.domicile[:n], t.hopital[:n], t.lieu[:n], t.poste[:n], t.heures[:n], t.travaille[:n])
        self._colonnes_fraiches = True

    def deplacer_python(self, h):
        q = set(self.gouv.lois["quarantaine"])
        for p in self.habitants:
            if not p.vivant: continue
            if p.poste == "voyage": continue            # il est en mer : ni maison, ni travail, ni corps
            if p.id in self.sejours:                    # en visite sur l autre ile : il y reste, puis il rentre
                if self.pas < self.sejours[p.id]: continue
                del self.sejours[p.id]
                self.embarquer(p, p.domicile)
                continue
            if p.etat == "I" and p.gravite > 0.3: p.lieu, p.poste = p.domicile.marche, "hopital"; continue
            enferme = (p.domicile.id in q or p.travail is not None and p.travail.id in q) \
                and self.rng.random() > C.QUARANTAINE_VIOLEE        # point 8 : une part de la population sort quand meme
            epuise = p.faim > C.ABSENCE_FAIM                        # on ne va pas travailler le ventre vide depuis deux jours
            gt = self.agents.get("travailleurs")
            veut = R.va_travailler(gt, p) if (gt and p.role not in ("enfant", "retraite")) else (not enferme and not epuise)
            if p.au_travail(h) and p.travail is not None and veut:
                p.lieu, p.poste = p.travail, "travail"
                if C.ROLES[p.role][2]: p.heures_jour += C.MINUTES_PAR_PAS / 60.0     # le fonctionnaire est paye a l heure
            else: p.lieu, p.poste = p.domicile, "maison"

    # --- 2. la production ---
    def produire(self, h):
        """Qui travaille sur chaque site, et ce que le site produit. En colonnes quand `deplacer` vient de les remplir :
        un ouvrier est present s il est vivant, a son lieu de travail, a son heure, et du metier du site. Les sites
        sont traites dans l ordre du premier ouvrier rencontre, comme le dictionnaire de la version Python : ils se
        partagent le reseau electrique, et l ordre des additions change les centimes."""
        if not self._colonnes_fraiches: return self.produire_python(h)
        t, n = self.table, self.table.n
        lieu = t.lieu[:n]
        idx = np.nonzero((t.vivant[:n] == 1) & (lieu == t.travail[:n]) & (t.travail[:n] >= 0) & (t.travaille[:n] == 1))[0]
        if idx.size == 0: return
        l = lieu[idx]
        garde = self._role_entreprise[l] == t.role[idx]
        idx, l = idx[garde], l[garde]
        if idx.size == 0: return
        sites, premier, compte = np.unique(l, return_index=True, return_counts=True)
        part = np.zeros(len(self.carte.par_n))
        for k in np.argsort(premier, kind="stable"):
            e = self.entreprises[self.carte.par_n[sites[k]].id]
            nb = int(compte[k])
            f = self._produire_site(e, nb)
            if f is not None: part[sites[k]] = f / nb
        t.heures[idx] += part[l]

    def produire_python(self, h):
        present = {}
        for p in self.habitants:
            if p.vivant and p.lieu is p.travail and p.travail is not None and p.lieu.id in self.entreprises \
                    and p.role == self.entreprises[p.lieu.id].role and p.au_travail(h):
                present.setdefault(p.lieu.id, []).append(p)
        for lid, ouvriers in present.items():
            f = self._produire_site(self.entreprises[lid], len(ouvriers))
            # paye pour le travail REELLEMENT fait : sans intrants, ou reseau plein, c est du chomage technique, non paye
            if f is not None:
                for p in ouvriers: p.heures_jour += f / len(ouvriers)

    def _produire_site(self, e, nb):
        """La production d un site ou travaillent `nb` ouvriers pendant ce pas. Rend le travail reellement fait, ou
        None si le site n a rien pu faire ( sans intrants, ou reseau plein )."""
        heures = nb * C.MINUTES_PAR_PAS / 60.0 * e.activite
        f = heures * self.facteur_choc(e.lieu)      # une secheresse coupe le RENDEMENT, pas les heures payees
        for b, q in e.intrants.items():          # les intrants limitent la production
            dispo = self.reseau.stock if b == "electricite" else e.stocks[b]
            f = min(f, dispo / q if q > 0 else f)
        if f <= 1e-9:
            return None
        if e.type == "centrale":                  # une centrale ne produit que ce que le reseau peut prendre
            f = min(f, max(0.0, self.reseau.capacite - self.reseau.stock) / e.produits["electricite"])
            if f <= 1e-9: return None
        bonus = 1 + C.BONUS_OUTILS if e.stocks["outils"] >= 1 else 1.0
        for b, q in e.intrants.items():
            if b == "electricite":
                self.reseau.stock -= q * f; self.transferer(e, self.gouv, q * f * self.reseau.tarif, "electricite")
            else: e.stocks[b] -= q * f
            self.flux["consomme"][b] += q * f
        for b, q in e.produits.items():
            e.stocks[b] += q * f * bonus; self.flux["produit"][b] += q * f * bonus; e.produit_du_jour[b] += q * f * bonus
        if e.stocks["or"] > 0:                    # redevance miniere : la moitie de l or revient a l Etat, en nature
            r = e.stocks["or"] * C.REDEVANCE_OR; e.stocks["or"] -= r; self.publics["reserve"]["or"] += r
        if e.type == "centrale":                  # la centrale injecte dans le reseau, l Etat la paie au tarif
            q = e.stocks["electricite"]; e.stocks["electricite"] = 0.0
            place = max(0.0, self.reseau.capacite - self.reseau.stock)
            injecte = min(q, place); self.reseau.stock += injecte
            perte = q - injecte
            if perte > 0: self.flux["consomme"]["electricite"] += perte      # ce que le reseau ne peut pas stocker
            self.transferer(self.gouv, e, injecte * self.reseau.tarif, "electricite")
        if e.stocks["outils"] >= 1:
            e.heures_outils += heures
            if e.heures_outils >= C.USURE_OUTIL_H:
                e.heures_outils -= C.USURE_OUTIL_H; e.stocks["outils"] -= 1; self.flux["consomme"]["outils"] += 1
        return f

    # --- 3. les convois ---
    def conducteur(self, capitale):
        """Le premier convoyeur libre de cette capitale, dans l ordre de l index. La liste de ceux qui sont EN SERVICE
        ( vivants, a leur heure ) est dressee une fois par pas : profil du 23/09, chaque convoi re-verifiait l horaire de
        tous les convoyeurs - 767 933 verifications pour 3 863 convois a 50 000 habitants. Un chauffeur parti ne
        redevient pas libre dans le meme pas : on le retire de la tete de file."""
        if getattr(self, "_chauffeurs_pas", None) != self.pas:
            self._chauffeurs_pas, self._chauffeurs = self.pas, {}
        file = self._chauffeurs.get(capitale.id)
        t = self.table
        if file is None:
            ids = np.array(self.ids_au_travail(capitale, "convoyeur"), np.int64)
            if self._colonnes_fraiches and ids.size:
                ids = ids[(t.vivant[ids] == 1) & (t.travaille[ids] == 1)]
            else:
                h = self.heure
                ids = np.array([i for i in ids.tolist() if P.Habitant(t, i).vivant and P.Habitant(t, i).au_travail(h)], np.int64)
            file = self._chauffeurs[capitale.id] = collections.deque(ids.tolist())
        while file and self.conducteur_libre.get(file[0], 0) > self.pas: file.popleft()
        return P.Habitant(t, file[0]) if file else None

    def lancer_convoi(self, origine, destination, cargaison, payeur, motif, marche_carburant, vendeur=None):
        coupees = self.routes_coupees | getattr(self, "routes_temporaires", set())
        if origine.id in coupees or destination.id in coupees:
            return False
        km = self.carte.km_route(origine, destination)
        chauffeur = self.conducteur(marche_carburant.lieu)
        carb = 2 * km * C.CARBURANT_PAR_KM          # aller et retour
        if chauffeur is None: return False
        if marche_carburant.stocks["carburant"] < carb:
            self.noter("penurie", bien="carburant", lieu=marche_carburant.lieu.id, motif=motif); return False
        # le carburant du convoi est achete au marche par celui qui paie le transport
        cout = carb * marche_carburant.prix["carburant"]
        if payeur.caisse < cout: return False
        self.transferer(payeur, marche_carburant, cout, "carburant du convoi")
        marche_carburant.stocks["carburant"] -= carb; self.flux["brule"]["carburant"] += carb
        marche_carburant.demande["carburant"] += carb
        duree = max(1, math.ceil(km / C.VITESSE_CONVOI_KMH * 60 / C.MINUTES_PAR_PAS))
        self.n_convoi += 1
        c = E.Convoi(self.n_convoi, origine, destination, cargaison, self.pas, self.pas + duree, payeur, motif, chauffeur.id)
        c.vendeur = vendeur if vendeur is not None else payeur
        self.convois.append(c); self.conducteur_libre[chauffeur.id] = self.pas + 2 * duree
        chauffeur.heures_jour += 2 * duree * C.MINUTES_PAR_PAS / 60.0
        return True

    def expedier(self, h):
        for e in self.entreprises.values():
            m = self.marches[e.lieu.marche.id]
            # vendre la production
            for b in e.produits:
                if b == "electricite": continue
                q = min(e.stocks[b], C.CAPACITE_CAMION)
                if q >= (C.CAPACITE_CAMION * 0.5 if b != "or" else 0.5):
                    cargo = {b: q}
                    # ! 22/09 : c est l ACHETEUR ( le marche ) qui paie le carburant. Les fermes cooperatives partent sans caisse :
                    # quand le vendeur payait le transport, aucune recolte ne quittait jamais le village.
                    if self.lancer_convoi(e.lieu, m.lieu, cargo, m, "vente", m, vendeur=e): e.stocks[b] -= q
            # s approvisionner
            for b, need in e.intrants.items():
                if b == "electricite": continue
                if e.stocks[b] < need * 8 and m.stocks[b] > 1:
                    q = min(C.CAPACITE_CAMION, m.stocks[b]); cout = q * m.prix[b] * (1 + self.gouv.tva)
                    if e.caisse >= cout:
                        m.demande[b] += q
                        if self.lancer_convoi(m.lieu, e.lieu, {b: q}, e, "approvisionnement", m):
                            m.stocks[b] -= q
                            self.transferer(e, m, q * m.prix[b], "achat intrant")
                            self.transferer(e, self.gouv, q * m.prix[b] * self.gouv.tva, "tva")
                    else: m.demande[b] += q
        # le commerce entre marches. La decision - quel bien part d ou vers ou, en quelle quantite - est REMPLACABLE :
        # `self.marchand` prend la main quand il est pose ( un reseau, par exemple ), sinon c est la regle ci-dessous.
        if 7 <= h < 15:
            gc = self.agents.get("commerce")
            if self.marchand is not None: self.marchand(self, h)
            elif gc: R.commerce_agents(self, gc, h)
            else: self.commerce_regle(h)
        # les commandes publiques
        for cmd in list(self.gouv.commandes):
            b, q, dest = cmd["bien"], cmd["quantite"], cmd["destination"]
            m = max(self.marches.values(), key=lambda x: x.stocks[b])
            q = min(q, m.stocks[b], C.CAPACITE_CAMION)
            m.demande[b] += cmd["quantite"]
            if q < 1: continue
            lieu_dest = self.depot_armee if dest == "armee" else self.carte.gouvernement
            cout = q * m.prix[b]
            if self.gouv.caisse < cout: continue
            if self.lancer_convoi(m.lieu, lieu_dest, {b: q}, self.gouv, "commande_" + dest, m):
                m.stocks[b] -= q; self.transferer(self.gouv, m, cout, "commande publique")
                cmd["quantite"] -= q; cmd["_dest"] = dest
                self.convois[-1].motif = "commande_" + dest
                if cmd["quantite"] < 1: self.gouv.commandes.remove(cmd)
        # l or : les marchands le vendent au port au prix mondial ; le surplus de nourriture aussi ( au-dela de 3 jours )
        for m in self.marches.values():
            if m.stocks["or"] > 0:
                gain = m.stocks["or"] * C.PRIX_MONDE["or"]
                self.flux["exporte"]["or"] += m.stocks["or"]; m.stocks["or"] = 0.0
                m.caisse += gain; self.ext["entree"] += gain
            besoin = 3 * C.NOURRITURE_PAR_JOUR * self._pop_marche.get(m.lieu.id, 0)
            surplus = m.stocks["nourriture"] - besoin
            if surplus > 50:
                gain = surplus * C.PRIX_MONDE["nourriture"] * 0.8
                m.stocks["nourriture"] -= surplus; self.flux["exporte"]["nourriture"] += surplus
                m.caisse += gain; self.ext["entree"] += gain; m.offre["nourriture"] += 0

    def probabilite_controle(self, m):
        """La chance qu une fraude soit controlee dans la region d un marche : ses policiers, rapportes a ses menages,
        fois l intensite voulue par l Etat."""
        policiers = self.nombre_au_travail(m.lieu, "policier")
        menages = max(1.0, self._pop_marche.get(m.lieu.id, 0) / 2.5)
        return min(0.9, C.CONTROLE_PAR_POLICIER * self.intensite_controle * policiers / max(1.0, menages / 10.0))

    def part_fraudeuse(self):
        """Point 8 : la part des achats qui echappe a la TVA. Nulle sous le seuil tolere, elle monte ensuite.
        Sans elle, un gouvernement pouvait taxer a 90 % sans que personne ne bronche."""
        exces = max(0.0, self.gouv.tva - C.TVA_TOLEREE)
        return min(C.FRAUDE_MAX, C.FRAUDE_PENTE * exces)

    def facteur_choc(self, lieu):
        """Le rendement d un lieu un jour donne : 1, sauf secheresse en cours."""
        for c in self.chocs:
            if c["debut"] <= self.jour < c["debut"] + c["jours"] and lieu.id in c["lieux"]: return c["facteur"]
        return 1.0

    def commerce_regle(self, h):
        """La regle d origine : un bien part vers le marche ou son prix couvre le transport et la marge. C est le temoin
        que tout marchand appris doit battre."""
        for a in self.marches.values():
            for b in C.BIENS_COMMERCE:
                garde = self.reserve_marche(a, b)
                surplus = a.stocks[b] - garde
                if surplus < 10: continue
                cible = max((x for x in self.marches.values() if x is not a), key=lambda x: x.prix[b] - a.prix[b])
                km = self.carte.km_route(a.lieu, cible.lieu)
                cout_u = 2 * km * C.CARBURANT_PAR_KM * a.prix["carburant"] / C.CAPACITE_CAMION
                if cible.prix[b] * (1 - cible.marge) - a.prix[b] > cout_u + 0.05 * a.prix[b]:
                    q = min(surplus, C.CAPACITE_CAMION)
                    if self.lancer_convoi(a.lieu, cible.lieu, {b: q}, a, "commerce", a): a.stocks[b] -= q

    def arrivees(self):
        for c in [c for c in self.convois if c.arrivee <= self.pas]:
            self.convois.remove(c)
            if c.motif == "ravitaillement_base":
                for b, q in c.cargaison.items(): self.garnisons[c.destination.id][b] += q
                self.derniere_livraison[c.destination.id] = self.jour
                continue
            if c.motif == "vente":
                m = self.marches[c.destination.id]
                for b, q in c.cargaison.items():
                    m.stocks[b] += q; m.offre[b] += q
                    self.transferer(m, c.vendeur, q * m.prix[b] * (1 - m.marge), "vente")
            elif c.motif == "commerce":
                m = self.marches[c.destination.id]
                for b, q in c.cargaison.items():
                    m.stocks[b] += q; m.offre[b] += q
                    self.transferer(m, c.payeur, q * m.prix[b] * (1 - m.marge), "commerce")
            elif c.motif == "approvisionnement":
                for b, q in c.cargaison.items(): c.payeur.stocks[b] += q
            elif c.motif.startswith("commande_"):
                dest = c.motif[len("commande_"):]
                for b, q in c.cargaison.items(): self.publics[dest][b] += q
            self.noter("convoi", id=c.id, motif=c.motif, de=c.origine.id, vers=c.destination.id,
                       cargaison={b: round(q, 1) for b, q in c.cargaison.items()})

    # --- 4. la paie ( echeance de 18 h ), les pensions, les dividendes ---
    def paie(self):
        g = self.gouv
        for p in self.habitants:
            if not p.vivant: continue
            if p.role == "retraite":
                self.transferer(g, p.menage, P.PENSION_JOUR, "pension"); continue
            if p.heures_jour <= 0: continue
            w = P.SALAIRE_HORAIRE.get(p.role, 0) * p.heures_jour
            if w <= 0: continue
            if C.ROLES[p.role][2]:
                brut = self.transferer(g, p.menage, w * g.facteur_salaire_public, "salaire public")
            else:
                e = self.entreprises.get(p.travail.id) if p.travail else None
                payeur = e if e is not None else self.marches.get(p.travail.id) if p.travail else None
                if p.role == "convoyeur": payeur = self.marches[p.travail.id]
                if payeur is None: continue
                brut = self.transferer(payeur, p.menage, w, "salaire")
            self.transferer(p.menage, g, brut * g.impot_revenu, "impot sur le revenu")
        # les marchands : la moitie du benefice du marche au-dessus de sa caisse de depart, en salaire
        for m in self.marches.values():
            marchands = self.au_travail_de(m.lieu, "marchand")
            exces = m.caisse - 20000.0
            if exces > 0 and marchands:
                for p in marchands:
                    brut = self.transferer(m, p.menage, 0.5 * exces / len(marchands), "benefice marchand")
                    self.transferer(p.menage, g, brut * g.impot_revenu, "impot")
        # les fermes cooperatives partagent leur caisse entre leurs paysans
        for e in self.entreprises.values():
            if e.type != "ferme": continue
            paysans = self.au_travail_de(e.lieu, "paysan")
            if paysans and e.caisse > 0:
                part = e.caisse / len(paysans)
                for p in paysans:
                    brut = self.transferer(e, p.menage, part, "revenu agricole")
                    self.transferer(p.menage, g, brut * g.impot_revenu, "impot")
        # dividendes des patrons : ce que l entreprise a au-dela de 10 000
        for e in self.entreprises.values():
            if e.proprietaire is not None and e.caisse > 10000:
                brut = self.transferer(e, e.proprietaire.menage, e.caisse - 10000, "dividende")
                self.transferer(e.proprietaire.menage, g, brut * g.impot_revenu, "impot")
        for p in self.habitants: p.heures_jour = 0.0

    # --- 5. les achats du soir et le repas ---
    def achats(self):
        ration = self.gouv.lois["rationnement_nourriture"] or C.NOURRITURE_PAR_JOUR
        for mg in self.menages:
            vivants = [p for p in mg.membres if p.vivant]
            if not vivants: continue
            m = self.marches[mg.domicile.marche.id]
            besoin_jour = max(1e-6, ration * len(vivants))
            if self.doctrine is None:
                cible = 1.5                                  # la regle d origine : un jour et demi, toujours
            else:
                ag = self.menagiers.get(mg.id)
                if ag is None: ag = self.menagiers[mg.id] = A.Menagier()
                x = ag.regarder(self, mg, m, besoin_jour)
                k = self.doctrine.choisir(x, explorer=self.apprentissage)
                ag.dernier_x, ag.derniere_action = x, k
                ag.dernier_prix = m.prix["nourriture"] * (1 + self.gouv.tva)
                ag.depense = 0.0
                ag.besoin_du_soir = besoin_jour
                cible = A.CIBLES[k]
            voulu = max(0.0, besoin_jour * cible - mg.garde_manger)
            m.demande["nourriture"] += voulu
            prix = m.prix["nourriture"] * (1 + self.gouv.tva)
            q = min(voulu, m.stocks["nourriture"], mg.caisse / prix if prix > 0 else 0)
            if q <= 0: continue
            m.stocks["nourriture"] -= q; mg.garde_manger += q
            gf = self.agents.get("fraudeurs")
            if gf: fraude = gf.choisir(mg.id, R.traits_fraude(self, mg, m)) == 1
            else: fraude = self.rng.random() < self.part_fraudeuse()      # point 8 : une taxe trop lourde se contourne
            if self.doctrine is not None: self.menagiers[mg.id].depense += q * m.prix["nourriture"] * (1 + self.gouv.tva)   # noqa
            self.transferer(mg, m, q * m.prix["nourriture"], "nourriture")
            du = q * m.prix["nourriture"] * self.gouv.tva
            if fraude:
                self.tva_fraudee += du
                pris = self.rng.random() < self.probabilite_controle(m)
                if pris:                                  # l amende : trois fois la taxe evitee
                    amende = self.transferer(mg, self.gouv, 3 * du, "amende")
                    self.amendes_menage[mg.id] = self.amendes_menage.get(mg.id, 0) + 1
                    self.amendes_totales = getattr(self, "amendes_totales", 0.0) + amende
                if gf:
                    norme = max(1e-6, m.prix["nourriture"] * C.NOURRITURE_PAR_JOUR * len(mg.membres))
                    gf.ajouter(mg.id, (du - (3 * du if pris else 0.0)) / norme)
            else: self.tva_percue += self.transferer(mg, self.gouv, du, "tva")
            # au-dela d une semaine de nourriture en epargne, le menage depense : biens manufactures et carburant
            reserve = 7 * ration * len(vivants) * prix
            budget = max(0.0, mg.caisse - reserve) * C.PROPENSION_DEPENSE
            for b, part, plafond in (("outils", 0.6, 1.0), ("carburant", 0.4, 0.3)):
                pb = m.prix[b] * (1 + self.gouv.tva)
                qb = min(budget * part / pb, plafond, m.stocks[b] - (120.0 if b == "carburant" else 0.0)) if pb > 0 else 0
                m.demande[b] += budget * part / pb if pb > 0 else 0
                if qb <= 0: continue
                m.stocks[b] -= qb; self.flux["consomme"][b] += qb
                self.transferer(mg, m, qb * m.prix[b], b); self.transferer(mg, self.gouv, qb * m.prix[b] * self.gouv.tva, "tva")
        if self.doctrine is not None:
            for mg in self.menages:
                ag = self.menagiers.get(mg.id)
                if ag is not None and ag.derniere_action is not None:
                    ag.poser(ag.dernier_x, ag.derniere_action, ag.depense, getattr(ag, "besoin_du_soir", 1.0))
                    ag.derniere_action = None

        # la ration de l Etat : ce que le gouvernement a achete pour la population est distribue aux menages affames
        stock = self.publics["population"]["nourriture"]
        if stock > 0:
            affames = [mg for mg in self.menages if mg.garde_manger < len(mg.membres) * 0.5]
            for mg in affames:
                q = min(stock, len(mg.membres) * 1.0)
                mg.garde_manger += q; stock -= q
            self.publics["population"]["nourriture"] = stock

    def repas(self):
        """Le repas du soir, EN COLONNES : chaque menage mange ce qu il a, jusqu a son besoin ; ses vivants ont faim s il
        manque. Le compteur de nourriture consommee est cumule dans l ordre des menages ( cumsum ), comme la boucle.
        Les menages formes ( doctrine ) gardent la version Python : leur note se lit menage par menage."""
        if not self.utiliser_coeur or self.doctrine is not None: return self.repas_python()
        t, n, mt = self.table, self.table.n, self.table.menages
        M = mt.n
        vivant = t.vivant[:n] == 1
        mm = P.menages_inscrits(t, n)
        membres = np.nonzero(vivant & (mm >= 0))[0]
        v = np.bincount(mm[membres], minlength=M)
        besoin = C.NOURRITURE_PAR_JOUR * v
        gm = mt.garde_manger[:M]
        mange = np.minimum(besoin, gm)
        mt.garde_manger[:M] = gm - mange
        self.flux["consomme"]["nourriture"] = float(np.cumsum(np.concatenate(([self.flux["consomme"]["nourriture"]], mange)))[-1])
        manque = besoin - mange
        affame = manque > 1e-6
        self.stats_jour["menages_sans_nourriture"] = int(affame.sum())
        region = self._marche_du_lieu[mt.domicile[:M]]
        dans = region >= 0
        tot = np.bincount(region[dans], minlength=len(self.carte.par_n))
        aff = np.bincount(region[dans & affame], minlength=len(self.carte.par_n))
        self.faim_region = {self.carte.par_n[k].id: int(aff[k]) / int(tot[k]) for k in np.nonzero(tot)[0]}
        self.nourri_menage = ParMenage(~affame)
        k = mm[membres]
        faim = t.faim[membres]
        t.faim[membres] = np.where(affame[k], faim + manque[k] / np.maximum(v[k], 1), np.maximum(0.0, faim - 1))
        for nom, noter in (("travailleurs", R.noter_travailleurs), ("entreprises", R.noter_entreprises),
                           ("marches", R.noter_marches), ("commerce", R.noter_commerce),
                           ("fraudeurs", R.noter_fraudeurs), ("voyageurs", R.noter_voyageurs)):
            g = self.agents.get(nom)
            if g: noter(self, g)

    def repas_python(self):
        sans = 0
        self.nourri_menage = ParMenage(np.ones(len(self.menages), bool))
        par_region, affames_region = {}, {}
        for mg in self.menages:
            vivants = [p for p in mg.membres if p.vivant]
            besoin = C.NOURRITURE_PAR_JOUR * len(vivants)
            mange = min(besoin, mg.garde_manger)
            mg.garde_manger -= mange; self.flux["consomme"]["nourriture"] += mange
            manque = besoin - mange
            if manque > 1e-6: sans += 1
            k = mg.domicile.marche.id if mg.domicile is not None and mg.domicile.marche is not None else None
            if k is not None:
                par_region[k] = par_region.get(k, 0) + 1
                if manque > 1e-6: affames_region[k] = affames_region.get(k, 0) + 1
            self.nourri_menage[mg.id] = manque <= 1e-6
            if self.doctrine is not None:                     # la consequence revient a celui qui a choisi, sur trois jours
                ag = self.menagiers.get(mg.id)
                if ag is not None:
                    for x, action, r in ag.journee(manque):
                        if self.apprentissage: self.doctrine.apprendre(x, action, r)
                        ag.recompenses.append(r)
            for p in vivants: p.faim = p.faim + manque / len(vivants) if manque > 1e-6 else max(0.0, p.faim - 1)
        self.stats_jour["menages_sans_nourriture"] = sans
        self.faim_region = {k: affames_region.get(k, 0) / n for k, n in par_region.items()}
        for nom, noter in (("travailleurs", R.noter_travailleurs), ("entreprises", R.noter_entreprises),
                           ("marches", R.noter_marches), ("commerce", R.noter_commerce),
                           ("fraudeurs", R.noter_fraudeurs), ("voyageurs", R.noter_voyageurs)):
            g = self.agents.get(nom)
            if g: noter(self, g)

    # --- 6. la sante ---
    def contagion(self):
        """Chaque lieu ou se trouve un malade contamine les sains presents. En colonnes quand la table est la : memes
        groupes, meme ordre des groupes ( celui du premier habitant rencontre ), memes tirages dans le meme ordre -
        la porte des colonnes compare au centime avec la boucle Python ( `contagion_python` )."""
        if not self.utiliser_coeur: return self.contagion_python()
        t, n = self.table, self.table.n
        lieu = t.lieu[:n]
        ici = np.nonzero((t.vivant[:n] == 1) & (lieu >= 0))[0]           # celui qui est en mer ne contamine personne
        if ici.size == 0: return
        l = lieu[ici]
        malades = np.bincount(l[t.etat[ici] == P.CODE_ETAT["I"]], minlength=len(self.carte.par_n))
        if not malades.any(): return
        # l ordre des groupes : celui du premier habitant de chaque lieu dans la liste
        sites, premier = np.unique(l, return_index=True)
        rang = np.empty(len(self.carte.par_n), np.int64); rang[sites] = np.argsort(np.argsort(premier, kind="stable"), kind="stable")
        # les candidats : sains, dans un lieu ou il y a au moins un malade ; tires groupe par groupe, en ordre de ligne
        cand = ici[(t.etat[ici] == P.CODE_ETAT["S"]) & (malades[l] > 0)]
        if cand.size == 0: return
        cand = cand[np.lexsort((cand, rang[lieu[cand]]))]
        proba = np.zeros(len(self.carte.par_n))
        for k in np.nonzero(malades)[0]: proba[k] = 1 - (1 - C.BETA_CONTACT) ** int(malades[k])
        seuil = proba[lieu[cand]] * np.where(t.faim[cand] > 1, 1.5, 1.0)
        touches = cand[self.rng.random(cand.size) < seuil]
        for i in touches:                                  # peu nombreux : on passe par l habitant, et par le journal
            p = self.habitants[int(i)]
            p.etat, p.jours_etat = "E", 0.0
            self.infectes_du_jour.add(p.id)
            self.contagions_lieu[p.lieu.id] = self.contagions_lieu.get(p.lieu.id, 0) + 1
            self.noter("infection", habitant=p.id, lieu=p.lieu.id)

    def contagion_python(self):
        groupes = {}
        for p in self.habitants:
            if p.vivant and p.lieu is not None: groupes.setdefault(p.lieu.id, []).append(p)   # celui qui est en mer ne contamine personne
        for gens in groupes.values():
            n_i = sum(1 for p in gens if p.etat == "I")
            if n_i == 0: continue
            proba = 1 - (1 - C.BETA_CONTACT) ** n_i
            for p in gens:
                if p.etat == "S" and self.rng.random() < proba * (1.5 if p.faim > 1 else 1.0):
                    p.etat, p.jours_etat = "E", 0.0
                    self.infectes_du_jour.add(p.id)
                    self.contagions_lieu[p.lieu.id] = self.contagions_lieu.get(p.lieu.id, 0) + 1
                    self.noter("infection", habitant=p.id, lieu=p.lieu.id)

    def progression_maladie(self):
        """Seuls les exposes et les malades sont parcourus, dans l ordre des habitants : le cout suit l epidemie, pas la
        taille du pays, et les tirages ( incubation, letalite ) gardent leur ordre exact."""
        t, n = self.table, self.table.n
        concernes = np.nonzero((t.vivant[:n] == 1) & ((t.etat[:n] == P.CODE_ETAT["E"]) | (t.etat[:n] == P.CODE_ETAT["I"])))[0]
        for i in concernes:
            p = P.Habitant(t, int(i))
            p.jours_etat += 1.0
            if p.etat == "E" and p.jours_etat >= C.INCUBATION_J:
                p.etat, p.jours_etat, p.gravite = "I", 0.0, float(self.rng.uniform(0.1, 1.0))
            elif p.etat == "I":
                if not p.remede and p.gravite > 0.3: self.soigner(p)
                duree = C.MALADIE_J * (C.EFFET_REMEDE_DUREE if p.remede else 1.0)
                if p.jours_etat >= duree:
                    letal = C.LETALITE * p.gravite * 2 / (5 if p.remede else 1)
                    if self.rng.random() < letal:
                        p.vivant = False; self.noter("mort", habitant=p.id, role=p.role, remede=p.remede)
                    else: p.etat, p.remede, p.gravite = "R", False, 0.0

    def soigner(self, p):
        """Un malade grave va a l hopital de sa capitale : remede public s il en reste, sinon achete au marche."""
        if self.publics["hopitaux"]["remedes"] >= 1:
            self.publics["hopitaux"]["remedes"] -= 1; self.flux["consomme"]["remedes"] += 1; p.remede = True; return
        m = self.marches[p.domicile.marche.id]
        m.demande["remedes"] += 1
        prix = m.prix["remedes"] * (1 + self.gouv.tva)
        if m.stocks["remedes"] >= 1 and p.menage.caisse >= prix:
            m.stocks["remedes"] -= 1; self.flux["consomme"]["remedes"] += 1; p.remede = True
            self.transferer(p.menage, m, m.prix["remedes"], "remede"); self.transferer(p.menage, self.gouv, m.prix["remedes"] * self.gouv.tva, "tva")
        else: self.noter("sans_remede", habitant=p.id)

    # --- 7. l armee en temps de paix : patrouilles qui brulent le carburant du depot ---
    def patrouilles(self):
        for base in self.carte.de_type("base"):
            ville = self.carte.plus_proche(base, ("ville", "capitale"))
            carb = 2 * self.carte.km_route(base, ville) * C.CARBURANT_PAR_KM * 3      # un vehicule blinde brule 3 fois plus
            g = self.garnisons[base.id]
            if g["carburant"] >= carb:
                g["carburant"] -= carb; self.flux["brule"]["carburant"] += carb
                f, a = self.patrouilles_jour.get(base.id, (0, 0)); self.patrouilles_jour[base.id] = (f + 1, a)
                self.patrouilles_faites = getattr(self, "patrouilles_faites", 0) + 1
                self.noter("patrouille", base=base.id, vers=ville.id, carburant=round(carb, 2))
            else:
                f, a = self.patrouilles_jour.get(base.id, (0, 0)); self.patrouilles_jour[base.id] = (f, a + 1)
                self.patrouilles_annulees = getattr(self, "patrouilles_annulees", 0) + 1
                self.noter("patrouille_annulee", base=base.id, cause="carburant")

    def besoin_patrouille(self, base):
        """Ce qu une base brule par jour : deux patrouilles vers la ville la plus proche."""
        ville = self.carte.plus_proche(base, ("ville", "capitale"))
        return 2 * (2 * self.carte.km_route(base, ville) * C.CARBURANT_PAR_KM * 3)

    def ravitailler_bases(self):
        """Point 6 : le depot national alimente les garnisons par CONVOI. Une route coupee assoiffe donc une base,
        et le delai se calcule : ce qu elle a en stock divise par ce qu elle brule."""
        ga = self.agents.get("armee")
        for base in self.carte.de_type("base"):
            g = self.garnisons[base.id]
            besoin = self.besoin_patrouille(base)
            if ga:
                vise = R.decider_armee(self, ga, base)
                if g["carburant"] >= vise * besoin: continue
                q = min(C.CAPACITE_CAMION, self.publics["armee"]["carburant"], vise * besoin - g["carburant"])
            else:
                if g["carburant"] >= 3 * besoin: continue
                q = min(C.CAPACITE_CAMION, self.publics["armee"]["carburant"], 5 * besoin - g["carburant"])
            if q < 1: continue
            if self.lancer_convoi(self.depot_armee, base, {"carburant": q}, self.gouv, "ravitaillement_base",
                                  self.marches[self.depot_armee.marche.id]):
                self.publics["armee"]["carburant"] -= q
                self.livraison_ratee[base.id] = False
                self.noter("ravitaillement_base", base=base.id, carburant=round(q, 1))
            else:
                self.livraison_ratee[base.id] = True

    # ------------------------------------------------------------------ le gouvernement
    def sitrep(self):
        t, n, mt = self.table, self.table.n, self.table.menages
        vivants = t.vivant[:n] == 1
        etat = t.etat[:n][vivants]
        nv = int(vivants.sum())
        return {
            "jour": self.jour, "heure": round(self.heure, 1),
            "population": {"vivants": nv, "morts": 500 - nv,
                           "menages_sans_nourriture": self.stats_jour.get("menages_sans_nourriture", 0),
                           "epargne_mediane": round(float(np.median(mt.caisse[:mt.n])))},
            "sante": {"infectes": int((etat == P.CODE_ETAT["I"]).sum()), "incubation": int((etat == P.CODE_ETAT["E"]).sum()),
                      "gueris": int((etat == P.CODE_ETAT["R"]).sum())},
            "marches": {m.lieu.id: {b: {"prix": round(m.prix[b], 2), "stock": round(m.stocks[b])} for b in
                        ("nourriture", "carburant", "remedes", "fer", "outils")} for m in self.marches.values()},
            "stocks_publics": {"remedes": round(self.publics["hopitaux"]["remedes"]), "or": round(self.publics["reserve"]["or"], 1),
                               "nourriture_population": round(self.publics["population"]["nourriture"])},
            "armee": {"carburant_depot": round(self.publics["armee"]["carburant"]),
                      "garnisons": {k: round(v["carburant"], 1) for k, v in self.garnisons.items()},
                      "patrouilles_annulees_hier": sum(1 for e in self.evenements[-400:] if e["type"] == "patrouille_annulee")},
            "finances": {"caisse": round(self.gouv.caisse), "impot_revenu": self.gouv.impot_revenu, "tva": self.gouv.tva,
                         "facteur_salaire_public": self.gouv.facteur_salaire_public},
            "reseau": {"electricite": round(self.reseau.stock)},
            "lois": self.gouv.lois,
        }

    def gouverner(self):
        s = self.sitrep()
        if self.cerveau is None: actions, motifs = G.decider_regles(s), "regles"
        else:
            try: actions, motifs = self.cerveau(s, self.memoire_gouv)
            except Exception as ex: actions, motifs = [{"type": "rien"}], f"cerveau indisponible : {ex}"
        res = []
        for a in actions[:8]:
            ok, raison = self.gouv.appliquer(a, self) if isinstance(a, dict) else (False, "action non JSON")
            res.append({"action": a, "acceptee": ok, "raison": raison})
        self.noter("decision_gouvernement", motifs=str(motifs)[:500], actions=res,
                   cerveau="regles" if self.cerveau is None else self.cerveau.modele,
                   consigne=None if self.cerveau is None else self.cerveau.empreinte)

    def resume_jour(self):
        s = self.sitrep()
        return {"vivants": s["population"]["vivants"], "infectes": s["sante"]["infectes"],
                "sans_nourriture": s["population"]["menages_sans_nourriture"], "caisse_etat": s["finances"]["caisse"],
                "prix_nourriture": {k: v["nourriture"]["prix"] for k, v in s["marches"].items()},
                "prix_carburant": {k: v["carburant"]["prix"] for k, v in s["marches"].items()},
                "electricite": s["reseau"]["electricite"], "carburant_armee": s["armee"]["carburant_depot"]}

    # ------------------------------------------------------------------ instantane
    def verifier_conservation(self):
        """Rend les ecarts de conservation : argent ( interne + exterieur ) et chaque bien."""
        d_arg = self.argent_total() - self.argent_depart - (self.ext["entree"] - self.ext["sortie"])
        t = self.biens_totaux()
        d_biens = {b: t[b] - self.biens_depart[b] - (self.flux["produit"][b] - self.flux["consomme"][b]
                   - self.flux["brule"][b] + self.flux["importe"][b] - self.flux["exporte"][b]) for b in C.BIENS}
        return d_arg, d_biens
