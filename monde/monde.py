"""Le coeur du monde : l etat du pays et son pas de 10 minutes. Hors d Arma ( etape E1 ) : ici tout est donnee.
Invariants verifies par les tests : l argent et les biens se CONSERVENT - rien n apparait ni ne disparait sans une
cause ecrite au journal ( production, consommation, combustion, import, export, mort )."""
import json, math
import numpy as np
from . import config as C, carte as K, population as P, economie as E, gouvernement as G, ecole as S, agents as A

CATEGORIES_PUBLIQUES = ("hopitaux", "armee", "reserve", "population")


class Monde:
    def __init__(self, graine=C.GRAINE, cerveau="regles", epidemie_jour=2, journal=None, eleve=None):
        self.rng = np.random.default_rng(graine)
        self.graine = graine
        self.carte = K.Carte()
        self.habitants, self.menages = P.generer(self.carte, self.rng)
        self.pas = 0
        self.journal_fichier = journal
        self.evenements = []
        # --- les entreprises : une ferme par village, un site par lieu industriel ---
        self.entreprises = {}
        for l in self.carte.de_type("village"): self.entreprises[l.id] = E.Entreprise(l, "ferme")
        for l in self.carte.de_type(*[t for t in C.RECETTES if t != "ferme"]): self.entreprises[l.id] = E.Entreprise(l, l.type)
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
        for k, h in enumerate([h for h in self.habitants if h.role == "ministre"]): h.nom += "-" + C.MINISTERES[k]
        self.publics = {c: {b: 0.0 for b in C.BIENS} for c in CATEGORIES_PUBLIQUES}
        self.publics["hopitaux"]["remedes"] = 30.0
        self.publics["armee"]["carburant"] = 150.0
        self.publics["reserve"]["or"] = 20.0
        self.depot_armee = self.carte.lieux["storage01"]
        self.convois = []; self.n_convoi = 0
        self.conducteur_libre = {h.id: 0 for h in self.habitants if h.role == "convoyeur"}
        self.cerveau = G.CerveauLLM() if cerveau == "llm" else None
        self.marchand = None               # pose par monde/apprenti.py : le reseau qui apprend a expedier
        self.doctrine = None               # posee par monde/former.py : ce que les menages ont appris ( point 1 )
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
        self.apprentissage = True       # faux pendant une qualification : l agent agit, il n apprend plus
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
        for c in self.convois:
            for b, q in c.cargaison.items(): t[b] += q
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
            return 3 * C.NOURRITURE_PAR_JOUR * sum(len(x.membres) for x in self.menages if x.domicile.marche is m.lieu)
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
        if self.ecole is not None:
            mm = self.minutes % (24 * 60)
            if mm == 8 * 60: self.ecole.instruction()
            elif mm == 11 * 60: self.ecole.exercice_du_jour()
            elif mm == 14 * 60: self.ecole.debrief()
            elif mm == 15 * 60 and self.jour % 3 == 2: self.ecole.qualification()
            elif mm == 19 * 60 + 10: self.ecole.observer_marche()
        self.pas += 1

    def regler_activite(self):
        """Chaque matin, l entreprise regle son activite sur son marche : elle ralentit quand le stock de son produit
        principal y depasse sa cible, accelere quand il manque, et s arrete presque quand elle perd de l argent."""
        for e in self.entreprises.values():
            if e.type == "centrale": continue                       # la centrale suit deja le reseau
            if "or" in e.produits: e.activite = 1.0; continue       # l or se vend toujours, au prix mondial
            m = self.marches[e.lieu.marche.id]
            # ! 22/09 : ni la moyenne des marches ( la raffinerie a 15 % pendant que Pyrgos manquait ) ni le marche le plus a
            # court ( le puits surproduisait un petrole que seule Athira emploie, et faisait faillite ). Une entreprise produit
            # tant que son PRIX couvre son COUT, et ralentit quand son propre marche deborde.
            b = max(e.produits, key=lambda x: e.produits[x] * C.PRIX_MONDE[x] if x != "or" else 0)
            recette = sum(q * m.prix[x] * (1 - m.marge) for x, q in e.produits.items())
            cout = P.SALAIRE_HORAIRE.get(e.role, 0) + sum(q * (self.reseau.tarif if x == "electricite" else m.prix[x])
                                                          for x, q in e.intrants.items())
            cible = self.reserve_marche(m, b) * 2 if b == "nourriture" else C.STOCK_CIBLE
            if m.stocks[b] > 2 * cible or recette < 0.95 * cout: e.activite = max(0.1, e.activite - 0.25)
            elif m.stocks[b] < cible and recette > 1.05 * cout: e.activite = min(1.0, e.activite + 0.25)

    def aube(self):
        self.regler_activite()
        for m in self.marches.values(): m.ajuster_prix()
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
        q = set(self.gouv.lois["quarantaine"])
        for p in self.habitants:
            if not p.vivant: continue
            if p.etat == "I" and p.gravite > 0.3: p.lieu, p.poste = p.domicile.marche, "hopital"; continue
            if p.au_travail(h) and p.travail is not None and p.domicile.id not in q and p.travail.id not in q:
                p.lieu, p.poste = p.travail, "travail"
                if C.ROLES[p.role][2]: p.heures_jour += C.MINUTES_PAR_PAS / 60.0     # le fonctionnaire est paye a l heure
            else: p.lieu, p.poste = p.domicile, "maison"

    # --- 2. la production ---
    def produire(self, h):
        present = {}
        for p in self.habitants:
            if p.vivant and p.lieu is p.travail and p.travail is not None and p.lieu.id in self.entreprises \
                    and p.role == self.entreprises[p.lieu.id].role and p.au_travail(h):
                present.setdefault(p.lieu.id, []).append(p)
        for lid, ouvriers in present.items():
            e = self.entreprises[lid]
            heures = len(ouvriers) * C.MINUTES_PAR_PAS / 60.0 * e.activite
            f = heures * self.facteur_choc(e.lieu)      # une secheresse coupe le RENDEMENT, pas les heures payees
            for b, q in e.intrants.items():          # les intrants limitent la production
                dispo = self.reseau.stock if b == "electricite" else e.stocks[b]
                f = min(f, dispo / q if q > 0 else f)
            if f <= 1e-9:
                continue
            if e.type == "centrale":                  # une centrale ne produit que ce que le reseau peut prendre
                f = min(f, max(0.0, self.reseau.capacite - self.reseau.stock) / e.produits["electricite"])
                if f <= 1e-9: continue
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
            # paye pour le travail REELLEMENT fait : sans intrants, ou reseau plein, c est du chomage technique, non paye
            for p in ouvriers: p.heures_jour += f / len(ouvriers)

    # --- 3. les convois ---
    def conducteur(self, capitale):
        for p in self.habitants:
            if p.role == "convoyeur" and p.vivant and p.travail is capitale and self.conducteur_libre[p.id] <= self.pas \
                    and p.au_travail(self.heure):
                return p
        return None

    def lancer_convoi(self, origine, destination, cargaison, payeur, motif, marche_carburant, vendeur=None):
        if origine.id in self.routes_coupees or destination.id in self.routes_coupees:
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
            if self.marchand is not None: self.marchand(self, h)
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
            besoin = 3 * C.NOURRITURE_PAR_JOUR * sum(len(x.membres) for x in self.menages if x.domicile.marche is m.lieu)
            surplus = m.stocks["nourriture"] - besoin
            if surplus > 50:
                gain = surplus * C.PRIX_MONDE["nourriture"] * 0.8
                m.stocks["nourriture"] -= surplus; self.flux["exporte"]["nourriture"] += surplus
                m.caisse += gain; self.ext["entree"] += gain; m.offre["nourriture"] += 0

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
            marchands = [p for p in self.habitants if p.role == "marchand" and p.travail is m.lieu and p.vivant]
            exces = m.caisse - 20000.0
            if exces > 0 and marchands:
                for p in marchands:
                    brut = self.transferer(m, p.menage, 0.5 * exces / len(marchands), "benefice marchand")
                    self.transferer(p.menage, g, brut * g.impot_revenu, "impot")
        # les fermes cooperatives partagent leur caisse entre leurs paysans
        for e in self.entreprises.values():
            if e.type != "ferme": continue
            paysans = [p for p in self.habitants if p.role == "paysan" and p.travail is e.lieu and p.vivant]
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
            if self.doctrine is not None: self.menagiers[mg.id].depense += q * m.prix["nourriture"] * (1 + self.gouv.tva)   # noqa
            self.transferer(mg, m, q * m.prix["nourriture"], "nourriture")
            self.transferer(mg, self.gouv, q * m.prix["nourriture"] * self.gouv.tva, "tva")
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
        sans = 0
        for mg in self.menages:
            vivants = [p for p in mg.membres if p.vivant]
            besoin = C.NOURRITURE_PAR_JOUR * len(vivants)
            mange = min(besoin, mg.garde_manger)
            mg.garde_manger -= mange; self.flux["consomme"]["nourriture"] += mange
            manque = besoin - mange
            if manque > 1e-6: sans += 1
            if self.doctrine is not None:                     # la consequence revient a celui qui a choisi, sur trois jours
                ag = self.menagiers.get(mg.id)
                if ag is not None:
                    for x, action, r in ag.journee(manque):
                        if self.apprentissage: self.doctrine.apprendre(x, action, r)
                        ag.recompenses.append(r)
            for p in vivants: p.faim = p.faim + manque / len(vivants) if manque > 1e-6 else max(0.0, p.faim - 1)
        self.stats_jour["menages_sans_nourriture"] = sans

    # --- 6. la sante ---
    def contagion(self):
        groupes = {}
        for p in self.habitants:
            if p.vivant: groupes.setdefault(p.lieu.id, []).append(p)
        for gens in groupes.values():
            n_i = sum(1 for p in gens if p.etat == "I")
            if n_i == 0: continue
            proba = 1 - (1 - C.BETA_CONTACT) ** n_i
            for p in gens:
                if p.etat == "S" and self.rng.random() < proba * (1.5 if p.faim > 1 else 1.0):
                    p.etat, p.jours_etat = "E", 0.0
                    self.noter("infection", habitant=p.id, lieu=p.lieu.id)

    def progression_maladie(self):
        for p in self.habitants:
            if not p.vivant or p.etat in ("S", "R"): continue
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
            if self.publics["armee"]["carburant"] >= carb:
                self.publics["armee"]["carburant"] -= carb; self.flux["brule"]["carburant"] += carb
                self.noter("patrouille", base=base.id, vers=ville.id, carburant=round(carb, 2))
            else:
                self.noter("patrouille_annulee", base=base.id, cause="carburant")

    # ------------------------------------------------------------------ le gouvernement
    def sitrep(self):
        vivants = [p for p in self.habitants if p.vivant]
        return {
            "jour": self.jour, "heure": round(self.heure, 1),
            "population": {"vivants": len(vivants), "morts": 500 - len(vivants),
                           "menages_sans_nourriture": self.stats_jour.get("menages_sans_nourriture", 0),
                           "epargne_mediane": round(float(np.median([m.caisse for m in self.menages])))},
            "sante": {"infectes": sum(1 for p in vivants if p.etat == "I"), "incubation": sum(1 for p in vivants if p.etat == "E"),
                      "gueris": sum(1 for p in vivants if p.etat == "R")},
            "marches": {m.lieu.id: {b: {"prix": round(m.prix[b], 2), "stock": round(m.stocks[b])} for b in
                        ("nourriture", "carburant", "remedes", "fer", "outils")} for m in self.marches.values()},
            "stocks_publics": {"remedes": round(self.publics["hopitaux"]["remedes"]), "or": round(self.publics["reserve"]["or"], 1),
                               "nourriture_population": round(self.publics["population"]["nourriture"])},
            "armee": {"carburant_depot": round(self.publics["armee"]["carburant"]),
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
