"""LES ACTEURS DEVIENNENT DES AGENTS ( plans/plan-agents-partout.md ).

Chaque groupe - travailleurs, fraudeurs, entreprises, marches, commerce, armee, voyageurs - prend une decision la ou
une regle la prenait. Meme mecanique que les menages, qui a fait tomber la faim de 20 % a 7,9 % :
  - une DOCTRINE commune au groupe ( bandit contextuel lineaire, poids partages, ecrits sur disque ) ;
  - une MEMOIRE propre a chaque agent : ses choix en attente de leur note ;
  - une note qui revient a celui qui a choisi, LUE SUR TROIS JOURS : une note lue le soir meme apprend a ne rien faire.

Trois modes par groupe : « appris » ( il apprend en vivant ), « fige » ( il agit sans apprendre : c est l examen ),
« hasard » ( le temoin ). Un groupe absent du monde laisse la regle d origine decider.

Ce que chaque agent voit est borne : des prix, des stocks, sa propre situation, ce que sa region a vecu hier.
Jamais l avenir, jamais la verite cachee du monde."""
import math
from . import agents as A, config as C

HORIZON = 3


# ================================================================== le socle commun
class Memoire:
    """Les choix d un agent qui attendent leur note : [traits, action, jours ecoules, somme des notes]."""
    __slots__ = ("attente",)

    def __init__(self): self.attente = []

    def poser(self, x, a): self.attente.append([x, a, 0, 0.0])

    def ajouter(self, valeur):
        """Une consequence connue tout de suite ( une amende, une marge ) s ajoute au dernier choix."""
        if self.attente: self.attente[-1][3] += valeur

    def jour(self, r):
        mures, restent = [], []
        for e in self.attente:
            e[2] += 1; e[3] += r
            (mures if e[2] >= HORIZON else restent).append(e)
        self.attente = restent
        return [(x, a, s / HORIZON) for x, a, j, s in mures]


class Groupe:
    """Un groupe d agents : sa doctrine commune, la memoire de chacun, et ce qu il a decide aujourd hui."""

    def __init__(self, nom, n_actions, n_traits, mode="appris", doctrine=None, epsilon=0.15):
        assert mode in ("appris", "fige", "hasard")
        self.nom, self.mode = nom, mode
        self.doctrine = doctrine or A.Doctrine(n_actions=n_actions, n_traits=n_traits, nom=nom, epsilon=epsilon)
        if mode == "hasard": self.doctrine.epsilon = 1.0
        if mode == "fige": self.doctrine.epsilon = 0.0
        self.memoire = {}
        self.choix = {}
        self.etat = {}            # ce que le groupe retient d un moment a l autre de la journee ( caisses du matin... )

    @property
    def apprend(self): return self.mode == "appris"

    def choisir(self, cle, x):
        k = self.doctrine.choisir(x, explorer=self.mode != "fige")
        self.memoire.setdefault(cle, Memoire()).poser(x, k)
        self.choix[cle] = k
        return k

    def ajouter(self, cle, valeur):
        m = self.memoire.get(cle)
        if m is not None: m.ajouter(valeur)

    def noter(self, cle, r):
        m = self.memoire.get(cle)
        if m is None: return
        for x, a, rr in m.jour(r):
            if self.apprend: self.doctrine.apprendre(x, a, rr)


def borne(v, a=-1.0, b=1.0): return max(a, min(b, v))


def nourris(w, marche_id): return 1.0 - w.faim_region.get(marche_id, 0.0)


# ================================================================== les travailleurs
# Chaque matin, chaque adulte qui a un poste choisit : aller travailler ( 0 ) ou rester chez lui ( 1 ).
# C est ce choix qui couvre desormais la quarantaine violee et l epuisement : il n y a plus de regle, il y a un choix.
TRAVAILLEURS = dict(n_actions=2, n_traits=8)


def decider_travailleurs(w, g):
    malades, presents = {}, {}
    for p in w.habitants:
        if p.vivant and p.travail is not None:
            presents[p.travail.id] = presents.get(p.travail.id, 0) + 1
            if p.etat == "I": malades[p.travail.id] = malades.get(p.travail.id, 0) + 1
    q = set(w.gouv.lois["quarantaine"])
    prix = {k: m.prix["nourriture"] * (1 + w.gouv.tva) for k, m in w.marches.items()}
    g.choix = {}
    for p in w.habitants:
        if not p.vivant or p.travail is None or p.role in ("enfant", "retraite") or p.poste == "voyage": continue
        mg = p.menage
        besoin = max(1e-6, C.NOURRITURE_PAR_JOUR * len(mg.membres))
        pr = prix.get(mg.domicile.marche.id, C.PRIX_MONDE["nourriture"])
        x = [1.0 if p.etat in ("E", "I") else 0.0,
             p.gravite if p.etat == "I" else 0.0,
             min(3.0, p.faim) / 3.0,
             min(10.0, mg.caisse / max(1e-6, pr * besoin)) / 10.0,
             1.0 if (p.domicile.id in q or p.travail.id in q) else 0.0,
             malades.get(p.travail.id, 0) / max(1, presents.get(p.travail.id, 1)),
             min(1.0, P_SALAIRE(p) / 30.0),
             1.0]
        g.choisir(p.id, x)


def P_SALAIRE(p):
    from . import population as P
    return P.SALAIRE_HORAIRE.get(p.role, 0)


def va_travailler(g, p):
    return g.choix.get(p.id, 0) == 0


def noter_travailleurs(w, g):
    """Le soir : son menage a-t-il mange ? est-il tombe malade aujourd hui ?"""
    for pid in list(g.memoire):
        p = w.par_id.get(pid)
        if p is None or not p.vivant: continue
        r = (1.0 if w.nourri_menage.get(p.menage.id, True) else 0.0) - 2.0 * (pid in w.infectes_du_jour)
        g.noter(pid, r)


# ================================================================== les fraudeurs ( les menages, a l achat )
# A chaque achat : payer la TVA ( 0 ) ou frauder ( 1 ). Une fraude peut etre controlee : l amende vaut trois fois la
# taxe evitee. Le controle depend de la police de la region et de l intensite voulue par l Etat.
FRAUDEURS = dict(n_actions=2, n_traits=5)


def traits_fraude(w, mg, m):
    besoin = max(1e-6, C.NOURRITURE_PAR_JOUR * len(mg.membres))
    prix = m.prix["nourriture"] * (1 + w.gouv.tva)
    return [min(1.0, w.gouv.tva / 0.5),
            min(1.0, w.probabilite_controle(m)),
            min(3.0, w.amendes_menage.get(mg.id, 0)) / 3.0,
            min(10.0, mg.caisse / max(1e-6, prix * besoin)) / 10.0,
            1.0]


def noter_fraudeurs(w, g):
    for k in list(g.memoire): g.noter(k, 0.0)        # tout se joue a l achat : gain ou amende, ajoutes sur le choix


# ================================================================== les entreprises
ACTIVITES = (0.1, 0.4, 0.7, 1.0)
ENTREPRISES = dict(n_actions=len(ACTIVITES), n_traits=8)


def entreprises_pilotables(w):
    for e in w.entreprises.values():
        if e.type == "centrale" or "or" in e.produits: continue       # comme la regle : ces deux-la ont leur logique
        yield e


def decider_entreprises(w, g):
    for e in entreprises_pilotables(w):
        m, b, recette, cout, cible = w.economie_entreprise(e)
        intrants = [e.stocks[x] / max(1e-6, q * 8) for x, q in e.intrants.items() if x != "electricite"]
        x = [min(3.0, recette / max(1e-6, cout)) / 3.0,
             min(3.0, m.stocks[b] / max(1.0, cible)) / 3.0,
             min(1.0, max(0.0, e.caisse) / 20000.0),
             min(1.0, min(intrants)) if intrants else 1.0,
             min(5.0, m.prix[b] / C.PRIX_MONDE[b]) / 5.0,
             w.faim_region.get(m.lieu.id, 0.0),
             e.activite,
             1.0]
        e.activite = ACTIVITES[g.choisir(e.id, x)]
        g.etat[e.id] = e.caisse


def noter_entreprises(w, g):
    """Son profit du jour, et sa region : une ferme qui s enrichit pendant que ses voisins ont faim n a pas tout gagne."""
    for e in entreprises_pilotables(w):
        if e.id not in g.memoire: continue
        profit = borne((e.caisse - g.etat.get(e.id, e.caisse)) / 2000.0)
        g.noter(e.id, profit + 0.5 * nourris(w, e.lieu.marche.id))


# ================================================================== les marches
FACTEURS = (0.9, 0.95, 1.0, 1.05, 1.1)
MARCHES = dict(n_actions=len(FACTEURS), n_traits=6)


def cible_marche(w, m, b):
    return w.reserve_marche(m, b) * 2 if b == "nourriture" else C.STOCK_CIBLE


def decider_marches(w, g):
    """A l aube, chaque marche fixe le prix de chaque bien, au lieu de suivre l offre et la demande d une formule."""
    for m in w.marches.values():
        g.etat[m.lieu.id] = m.caisse
        for b in C.BIENS:
            d, o = m.demande[b], m.offre[b] + m.stocks[b]
            if d + o <= 0: continue
            x = [d / (d + o),
                 min(3.0, m.stocks[b] / max(1.0, cible_marche(w, m, b))) / 3.0,
                 min(5.0, m.prix[b] / C.PRIX_MONDE[b]) / 5.0,
                 w.faim_region.get(m.lieu.id, 0.0),
                 1.0 if b == "nourriture" else 0.0,
                 1.0]
            k = g.choisir((m.lieu.id, b), x)
            m.prix[b] = min(5 * C.PRIX_MONDE[b], max(0.2 * C.PRIX_MONDE[b], m.prix[b] * FACTEURS[k]))
            m.demande[b] = 0.0; m.offre[b] = 0.0


def noter_marches(w, g):
    for (mid, b) in list(g.memoire):
        m = w.marches.get(mid)
        if m is None: continue
        cible = cible_marche(w, m, b)
        bande = 1.0 if 0.5 * cible <= m.stocks[b] <= 2 * cible else 0.0
        base = nourris(w, mid) if b == "nourriture" else 0.5
        caisse = borne((m.caisse - g.etat.get(mid, m.caisse)) / 5000.0)
        g.noter((mid, b), base + 0.5 * bande + 0.1 * caisse)


# ================================================================== le commerce entre marches
# Trois fois par jour, par marche et par bien en surplus : rien ( 0 ), vers le plus cher ( 1 ), vers le moins pourvu
# ( 2 ), vers le plus proche ( 3 ).
COMMERCE = dict(n_actions=4, n_traits=8)
HEURES_COMMERCE = (8, 11, 14)


def commerce_agents(w, g, h):
    if int(h) not in HEURES_COMMERCE: return
    marches = list(w.marches.values())
    for a in marches:
        autres = [x for x in marches if x is not a]
        if not autres: continue
        for b in C.BIENS_COMMERCE:
            surplus = a.stocks[b] - w.reserve_marche(a, b)
            if surplus < 10: continue
            pm = C.PRIX_MONDE[b]
            ratios = [x.stocks[b] / max(1.0, w.reserve_marche(x, b)) for x in autres]
            couts = [2 * w.carte.km_route(a.lieu, x.lieu) * C.CARBURANT_PAR_KM * a.prix["carburant"] / C.CAPACITE_CAMION
                     for x in autres]
            x = [min(5.0, a.prix[b] / pm) / 5.0,
                 min(5.0, max(y.prix[b] for y in autres) / pm) / 5.0,
                 min(3.0, min(ratios)) / 3.0,
                 min(1.0, surplus / (5 * C.CAPACITE_CAMION)),
                 min(5.0, (sum(couts) / len(couts)) / pm) / 5.0,
                 max(w.faim_region.get(y.lieu.id, 0.0) for y in autres),
                 1.0 if b == "nourriture" else 0.0,
                 1.0]
            k = g.choisir((a.lieu.id, b), x)
            if k == 0: continue
            if k == 1: cible = max(autres, key=lambda y: y.prix[b])
            elif k == 2: cible = min(autres, key=lambda y: y.stocks[b] / max(1.0, w.reserve_marche(y, b)))
            else: cible = min(autres, key=lambda y: w.carte.km_route(a.lieu, y.lieu))
            q = min(surplus, C.CAPACITE_CAMION)
            if w.lancer_convoi(a.lieu, cible.lieu, {b: q}, a, "commerce", a):
                a.stocks[b] -= q
                g.ajouter((a.lieu.id, b), borne((cible.prix[b] * (1 - cible.marge) - a.prix[b]) * q / 2000.0))


def noter_commerce(w, g):
    """Les regions que ce marche peut nourrir ont-elles mange ?"""
    for (mid, b) in list(g.memoire):
        autres = [k for k in w.marches if k != mid]
        g.noter((mid, b), sum(nourris(w, k) for k in autres) / max(1, len(autres)))


# ================================================================== l armee
STOCKS_VISES = (0, 3, 5, 8)          # en jours de patrouilles
ARMEE = dict(n_actions=len(STOCKS_VISES), n_traits=5)


def decider_armee(w, g, base):
    gar = w.garnisons[base.id]
    besoin = max(1e-6, w.besoin_patrouille(base))
    besoin_total = sum(w.besoin_patrouille(b) for b in w.carte.de_type("base"))
    x = [min(1.0, gar["carburant"] / (8 * besoin)),
         min(1.0, w.publics["armee"]["carburant"] / max(1e-6, 5 * besoin_total)),
         min(1.0, (w.jour - w.derniere_livraison.get(base.id, 0)) / 5.0),
         1.0 if w.livraison_ratee.get(base.id) else 0.0,
         1.0]
    return STOCKS_VISES[g.choisir(base.id, x)]


def noter_armee(w, g):
    """Le lendemain matin : patrouilles tenues, patrouilles annulees, et le prix d un stock qui dort."""
    for base in w.carte.de_type("base"):
        if base.id not in g.memoire: continue
        faites, annulees = w.patrouilles_jour.get(base.id, (0, 0))
        stock = w.garnisons[base.id]["carburant"] / max(1e-6, w.besoin_patrouille(base))
        g.noter(base.id, faites - annulees - 0.1 * stock / 5.0)


# ================================================================== les voyageurs ( le premier fret maritime )
CARGAISONS = (None, "nourriture", "carburant", "remedes")
VOYAGEURS = dict(n_actions=len(CARGAISONS), n_traits=8)
CAPACITE_BATEAU = 120.0


def marches_de_l_ile(w, ile):
    return [m for m in w.marches.values() if m.lieu.ile == ile]


def decider_voyageurs(w, g, aveugle=False):
    """Chaque matin, chaque ile decide si un de ses marchands part, et avec quoi, vers l ile ou ce bien vaut le plus."""
    for ile in w.carte.iles:
        ici = marches_de_l_ile(w, ile)
        ailleurs = [m for m in w.marches.values() if m.lieu.ile != ile]
        if not ici or not ailleurs: continue

        def ecart(b):
            return (max(m.prix[b] for m in ailleurs) - min(m.prix[b] for m in ici)) / C.PRIX_MONDE[b]
        surplus_n = max(m.stocks["nourriture"] - w.reserve_marche(m, "nourriture") for m in ici)
        faim_ici = sum(w.faim_region.get(m.lieu.id, 0.0) for m in ici) / len(ici)
        x = [min(5.0, min(m.prix["nourriture"] for m in ici) / C.PRIX_MONDE["nourriture"]) / 5.0,
             min(5.0, max(m.prix["nourriture"] for m in ailleurs) / C.PRIX_MONDE["nourriture"]) / 5.0,
             borne(surplus_n / (5 * CAPACITE_BATEAU), 0.0, 1.0),
             borne(ecart("carburant") / 5.0),
             borne(ecart("remedes") / 5.0),
             faim_ici,
             max(w.faim_region.get(m.lieu.id, 0.0) for m in ailleurs),
             1.0]
        k = 1 if aveugle else g.choisir(ile, x)
        b = CARGAISONS[k]
        if b is None: continue
        origine = max(ici, key=lambda m: m.stocks[b] - w.reserve_marche(m, b))
        dest = max(ailleurs, key=lambda m: m.prix[b])
        q = min(origine.stocks[b] - w.reserve_marche(origine, b), CAPACITE_BATEAU)
        if q < 10: continue
        marchand = w.marchand_libre(ile)
        if marchand is None: continue
        origine.stocks[b] -= q
        w.embarquer(marchand, dest.lieu, sejour_jours=1.0,
                    cargaison={b: q}, marche_origine=origine.lieu.id, marche_dest=dest.lieu.id)
        if not aveugle:
            g.ajouter(ile, borne((dest.prix[b] * (1 - dest.marge) - origine.prix[b]) * q / 3000.0))


def noter_voyageurs(w, g):
    """Le pays entier : combien d iles ont mange ? Un bateau sert autant ceux qui le recoivent que ceux qui l envoient."""
    toutes = list(w.marches)
    national = sum(nourris(w, k) for k in toutes) / max(1, len(toutes))
    for ile in list(g.memoire): g.noter(ile, national)


# ================================================================== le registre
FORMES = {"travailleurs": TRAVAILLEURS, "fraudeurs": FRAUDEURS, "entreprises": ENTREPRISES, "marches": MARCHES,
          "commerce": COMMERCE, "armee": ARMEE, "voyageurs": VOYAGEURS}


def groupe(nom, mode="appris", doctrine=None):
    return Groupe(nom, mode=mode, doctrine=doctrine, **FORMES[nom])
