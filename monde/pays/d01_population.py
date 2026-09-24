"""DOMAINE 1 - POPULATION, DEMOGRAPHIE, FAMILLE, ETAT CIVIL.

FICHE
1. Classes. TableDeMortalite, TableDeFecondite ( les lois ), EtatCivil ( ce que l Etat SAIT ), Demographie ( l etat du
   domaine ), ContexteMigration ( ce qu un menage voit quand il decide de partir ). Les champs ajoutes a chaque
   habitant vivent en colonnes ( p.colonnes["habitant"] ) : sexe, naissance_j, mere, pere, conjoint, union_j,
   enceinte, conception_j, accouchement_j, deces_j, cause_deces, inscrit, deces_declare. Un etat se dit par un
   drapeau, jamais par une date sentinelle : une date du passe est negative ( bogue du 23/09 : aucune grossesse du
   recensement n allait a terme ). Par menage : dissous, faim7,
   demenage_j. Habitant et Menage ( moteur E1 ) ne sont pas touches.
2. Invariants. Personnes : vivants = vivants du depart + naissances - deces ( toutes causes, y compris les morts du
   moteur E1, reprises chaque soir ). Chaque deces est traite une fois ( deces_j pose une fois ). Aucun mineur vivant
   dans un menage sans adulte vivant ; aucun vivant dans un menage dissous. Argent : heritages, mises en commun,
   partages et demenagements passent par le grand livre ; le domaine ne DETIENT rien : ni argent, ni bien. Etat civil :
   inscrits vivants du registre = recompte exact des colonnes ( inscrit, deces_declare ).
3. Decision `migrer` ( menage, tous les 7 jours, s il a eu faim dans la semaine ) : rester ou partir vers le marche le
   moins cher de son ile. Traits : jours de faim sur 7, prix ici, prix la-bas, reserve, epargne, part de mineurs,
   distance. Note : jours ou le menage a mange sur 7 jours, moins le cout du demenagement. Regle : partir apres 3 jours
   de faim si la-bas est 20 % moins cher et payable. Temoin : toujours rester.
4. Evenements. Individuels : naissance, deces, union, divorce, placement, desherence, migration_interne. Comptes :
   conception, fausse_couche, heritage, declaration_naissance, declaration_deces, migration_impossible.
5. Liens. Recoit les morts des autres domaines par `deceder( p, h, cause )` ( maladie, accident, combat ). Donne aux
   autres : les colonnes d etat civil, `deceder`, `nouveau_menage`, `deplacer_membre`, `vivants()`, l etat civil
   ( source de la statistique publique, domaine 6 ). Paie : heritages, desherence -> Etat, demenagements -> marche
   de destination. Remplace Monde.demographie ( a retirer de monde.py a l integration ).
6. Portes : tests_d01_population.py.
7. Arma : aucun objet ; un habitant garde son identite quand il prend un corps ( sexe : le classname du corps en
   depend, domaine 25 et pont ).
8. Cout : mortalite et conceptions vectorisees ( numpy, une passe par jour ), vieillissement et reprise des morts en
   une boucle par jour, unions et divorces une fois par semaine, migration sur les seuls menages affames."""
import bisect, math
import numpy as np
from .. import config as C, population as P
from ..socle import decision as D

# ================================================================== les lois de la population
FEMME, HOMME = 0, 1
AGE_MAX = 110
AGE_MAJEUR = 18
AGE_ECOLE = 6
JOURS_AN = 365.0

# Mortalite : Gompertz-Makeham au-dela de 15 ans, calee sur l esperance de vie grecque ( Eurostat 2019 : environ
# 79,0 ans pour les hommes, 84,1 pour les femmes - a verifier ) ; mortalite infantile 3,5 pour mille ( Grece 2019,
# ordre de grandeur ). Pente 0,095 par an : q(65) = 1,3 % et q(80) = 5,4 % chez les hommes.
MORTALITE = {HOMME: {"q0": 0.0039, "q_enfant": 0.00012, "a": 0.0004, "b": 2.676e-05, "c": 0.095},
             FEMME: {"q0": 0.0033, "q_enfant": 0.00010, "a": 0.00015, "b": 1.732e-05, "c": 0.095}}
CIBLE_E0 = {HOMME: 79.0, FEMME: 84.1}

# Fecondite par groupe d age ( naissances par femme et par an ) : ISF 1,35 ( Grece 2019 : 1,34 ), age moyen a
# l accouchement 31 ans. Ordres de grandeur Eurostat, a calibrer.
ASFR = {15: 0.008, 20: 0.030, 25: 0.068, 30: 0.094, 35: 0.058, 40: 0.0105, 45: 0.0005}
FECONDITE_SOLO = 0.15        # une femme sans conjoint conçoit 0,15 fois moins : ~12 % des naissances hors couple ( a calibrer )
FAUSSE_COUCHE = 0.12         # grossesses reconnues perdues au premier trimestre ( 10-20 % dans la litterature, a calibrer )
GESTATION_J = (266.0, 12.0)  # conception -> naissance : moyenne, ecart-type ; bornee a [196 ; 294] jours
POST_PARTUM_J = 90           # pas de conception dans les 3 mois qui suivent un accouchement
JUMEAUX = 0.015
GARCON = 105.0 / 205.0       # 105 garcons pour 100 filles a la naissance
MORT_MATERNELLE = 3.0e-5     # par naissance ( Grece : quelques pour 100 000 )
DECLARATION_NAISSANCE_J = (1, 10)   # la loi grecque laisse 10 jours pour declarer une naissance
DECLARATION_DECES_J = 1

# Unions et divorces : hasard ANNUEL pour une personne seule, par age ; divorce : par couple et par an ( a calibrer
# sur ELSTAT : age moyen au premier mariage ~ 33 ans pour les hommes, 30 pour les femmes ).
UNION_AN = ((18, 0.05), (25, 0.12), (30, 0.14), (35, 0.10), (40, 0.06), (50, 0.03), (65, 0.01))
# Part des femmes en couple par age, pour le recensement initial ( ordre de grandeur ELSTAT, recensement 2021, a calibrer )
EN_COUPLE = ((18, 0.08), (25, 0.35), (30, 0.60), (35, 0.72), (50, 0.75), (65, 0.55), (80, 0.30))
# Les jeunes adultes grecs quittent tard le foyer parental ( Eurostat : ~30 ans en moyenne ). Part des celibataires
# qui vivent chez leurs parents, par age, au recensement ( a calibrer ). Le moteur E1 donnait a chacun son menage.
FOYER_PARENTAL = ((18, 0.85), (25, 0.60), (30, 0.25), (35, 0.0))
ECART_AGE_COUPLE = 3.0       # l homme a en moyenne 3 ans de plus
ECART_AGE_MAX = 12.0
DIVORCE_AN = 0.007
GARDE_A_LA_MERE = 0.85       # part des divorces ou les enfants restent avec la mere ( a calibrer )
HERITAGE_CONJOINT = 0.25     # code civil grec ( art. 1820 ) : le conjoint recoit 1/4 en presence d enfants

# Part d hommes par metier dans le recensement initial ( a calibrer sur ELSTAT ; le moteur E1 ne connait pas le sexe )
PART_HOMMES = {"chef_gouvernement": 0.6, "ministre": 0.7, "officier": 0.85, "soldat": 0.9, "policier": 0.8,
               "medecin": 0.5, "infirmier": 0.15, "enseignant": 0.3, "patron": 0.7, "paysan": 0.6, "mineur": 0.95,
               "petrolier": 0.9, "ouvrier": 0.7, "convoyeur": 0.9, "marchand": 0.5, "enfant": GARCON, "retraite": 0.45}

# Migration interne
TARIF_DEMENAGEMENT_KM = 2.0  # drachmes par km pour transporter un menage et ses affaires ( a calibrer )
FORFAIT_DEMENAGEMENT = 20.0
DELAI_ENTRE_MIGRATIONS_J = 30
HORIZON_MIGRER = 7           # un demenagement ne rapporte pas le lendemain : la note se lit sur une semaine
LIBRES = ("paysan", "mineur", "ouvrier", "convoyeur", "marchand", "petrolier")   # metiers qu on reprend ailleurs

CAUSES = ("inconnue", "naturelle", "maladie", "maternelle", "accident", "combat", "violence", "faim")


class TableDeMortalite:
    """q[sexe, age] : probabilite de mourir dans l annee, de 0 a 110 ans ( 1 a 110 )."""
    __slots__ = ("q",)

    def __init__(self, params=MORTALITE, facteur=1.0):
        self.q = np.zeros((2, AGE_MAX + 1))
        for s, k in params.items():
            for x in range(AGE_MAX + 1):
                v = k["q0"] if x == 0 else k["q_enfant"] if x < 15 else k["a"] + k["b"] * math.exp(k["c"] * x)
                self.q[s, x] = min(1.0, v * facteur)
            self.q[s, AGE_MAX] = 1.0

    def esperance_de_vie(self, sexe):
        l, e = 1.0, 0.0
        for v in self.q[sexe]:
            d = l * v; e += l - 0.5 * d; l -= d
        return e

    def q_jour(self, sexe, age):
        """Probabilite de mourir aujourd hui, pour des tableaux de sexes et d ages entiers."""
        return 1.0 - (1.0 - self.q[sexe, age]) ** (1.0 / JOURS_AN)


class TableDeFecondite:
    """asfr[age] : naissances par femme et par an, a chaque age entier."""
    __slots__ = ("asfr",)

    def __init__(self, groupes=ASFR, facteur=1.0):
        self.asfr = np.zeros(AGE_MAX + 1)
        for a, f in groupes.items(): self.asfr[a:a + 5] = f * facteur

    def isf(self): return float(self.asfr.sum())
    def age_moyen(self): return float(((np.arange(AGE_MAX + 1) + 0.5) * self.asfr).sum() / self.asfr.sum())

    def hasard_conception(self, age):
        """Le hasard journalier de conception d une femme NON enceinte : les naissances visees, corrigees des pertes et
        du temps passe enceinte ou apres l accouchement, pendant lequel elle ne peut pas concevoir."""
        f = self.asfr[age]
        occupee = f / (1.0 - FAUSSE_COUCHE) * (GESTATION_J[0] + POST_PARTUM_J) / JOURS_AN
        return f / (1.0 - FAUSSE_COUCHE) / np.maximum(0.05, 1.0 - occupee) / JOURS_AN


def tirer_deces(table, sexe, age, u):
    """Qui meurt aujourd hui : u < q_jour. Fonction pure, testable sur une cohorte synthetique."""
    return u < table.q_jour(sexe, age)


def tirer_conceptions(table, age, en_couple, u, k):
    """Qui conçoit aujourd hui parmi des femmes non enceintes. `k` recale le total : les couples conçoivent plus que
    les femmes seules, sans changer l ISF du pays."""
    h = table.hasard_conception(age) * np.where(en_couple, 1.0, FECONDITE_SOLO) * k
    return u < h


def facteur_couples(table, age, en_couple):
    """Le k qui garde le total des conceptions egal a celui d une fecondite sans distinction de couple."""
    base = table.hasard_conception(age)
    pondere = (base * np.where(en_couple, 1.0, FECONDITE_SOLO)).sum()
    return float(base.sum() / pondere) if pondere > 0 else 1.0


# ================================================================== l etat civil
class EtatCivil:
    """Ce que l Etat SAIT de sa population : les actes declares, avec leur retard. La statistique publique ( domaine 6 )
    partira d ici, jamais de la liste des habitants. Une naissance se declare dans les 10 jours, un deces le lendemain ;
    un enfant mort avant d etre declare est declare ne et mort ensemble."""
    __slots__ = ("inscrits_vivants", "naissances", "deces", "unions", "divorces")

    def __init__(self, recenses):
        self.inscrits_vivants = recenses
        self.naissances = self.deces = self.unions = self.divorces = 0

    def population_connue(self): return self.inscrits_vivants


# ================================================================== le domaine
class ContexteMigration:
    """Ce qu un menage voit le soir ou il se demande s il part. Rien d autre : pas la faim des autres regions, pas le
    stock des marches - des prix affiches, son garde-manger, sa bourse, ses enfants, sa propre faim."""
    __slots__ = ("traits", "destination", "cout")

    def __init__(self, traits, destination, cout):
        self.traits, self.destination, self.cout = traits, destination, cout


def _observer_migrer(ctx): return ctx.traits


def _regle_migrer(x, ctx):
    faim, prix_ici, prix_la, reserve, epargne = x[0], x[1], x[2], x[3], x[4]
    return 1 if faim >= 3 / 7 and prix_la < 0.8 * prix_ici and epargne >= 0.2 else 0


def _temoin_migrer(x, ctx, rng): return 0


POINT_MIGRER = D.PointDeDecision(
    "migrer", "population",
    traits=(("faim_semaine", "les soirs sans repas de son menage sur 7 jours"),
            ("prix_ici", "le prix affiche de la nourriture a son marche, sur 5 fois le prix mondial"),
            ("prix_la_bas", "le prix affiche au marche le moins cher de son ile ( les prix sont publics )"),
            ("reserve", "son garde-manger en jours de besoin, sur 5"),
            ("epargne", "sa caisse sur un mois de nourriture, bornee a 1"),
            ("mineurs", "la part de mineurs dans son menage"),
            ("distance", "les km de route jusqu au marche vise, sur 60")),
    actions=("rester", "partir"),
    observer=_observer_migrer, regle=_regle_migrer, temoin=_temoin_migrer,
    note="les soirs ou CE menage a mange sur les 7 jours qui suivent, moins ce que le demenagement lui a coute",
    horizon_j=HORIZON_MIGRER)


class RemplaceDemographie:
    """Prend la place de Monde.demographie ( appelee par l aube du moteur ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _demographie(self.pays)


class Demographie:
    __slots__ = ("mortalite", "fecondite", "etat_civil", "enfants_de", "decideur", "prochain_habitant",
                 "naissances", "deces", "unions", "divorces", "migrations", "placements", "vivants_depart")

    def __init__(self, mortalite, fecondite, etat_civil, decideur, prochain_habitant, vivants_depart):
        self.mortalite, self.fecondite, self.etat_civil, self.decideur = mortalite, fecondite, etat_civil, decideur
        self.enfants_de = {}              # parent -> [ enfants ] : l heritage et le placement des orphelins
        self.prochain_habitant = prochain_habitant
        self.naissances = self.deces = self.unions = self.divorces = self.migrations = self.placements = 0
        self.vivants_depart = vivants_depart


# ------------------------------------------------------------------ petits outils
def _age_ans(p, ids):
    return np.clip((p.jour - p.col("habitant", "naissance_j")[ids]) // 365, 0, AGE_MAX).astype(np.int64)


def age_de(p, h):
    return (p.jour - int(p.col("habitant", "naissance_j")[h.id])) / JOURS_AN


def adultes_vivants(p, mg, sauf=None):
    return [x for x in mg.membres if x.vivant and x is not sauf and age_de(p, x) >= AGE_MAJEUR]


def vivants(w):
    return [h for h in w.habitants if h.vivant]


def nouveau_menage(p, domicile):
    """Un menage vide ( divorce, orphelin sans famille, jeune qui part ) : une classe du moteur, une place dans ses
    colonnes. Identifiants denses, comme ceux du moteur."""
    w = p.w
    mg = P.Menage(len(w.menages), domicile)
    w.menages.append(mg)
    p.colonnes["menage"].assurer(len(w.menages))
    return mg


def deplacer_membre(p, h, dest, garde_manger=True):
    """Un habitant change de menage : avec lui, sa part du garde-manger ( un deplacement de bien entre detenteurs
    inscrits : la conservation ne bouge pas )."""
    old = h.menage
    if old is dest: return
    if garde_manger:
        n = sum(1 for x in old.membres if x.vivant)
        part = old.garde_manger / n if n else 0.0
        old.garde_manger -= part; dest.garde_manger += part
    old.membres.remove(h); dest.membres.append(h)
    h.menage = dest
    rentre = h.lieu is h.domicile or h.lieu is None
    h.domicile = dest.domicile
    if rentre and h.vivant: h.lieu = dest.domicile
    if h.vivant and h.role == "enfant" and h.horaire == "ecole": h.travail = dest.domicile.marche


def _dissoudre_si_vide(p, mg):
    """Un menage sans vivant est dissous : ce qui lui reste d argent et de vivres a deja ete remis ( heritage )."""
    if not any(x.vivant for x in mg.membres): p.col("menage", "dissous")[mg.id] = 1


# ================================================================== naissances
def _concevoir(p, d, ids, age, sexe):
    H = p.col("habitant", "conception_j"); A = p.col("habitant", "accouchement_j"); E = p.col("habitant", "enceinte")
    conj = p.col("habitant", "conjoint")
    f = (sexe == FEMME) & (age >= 15) & (age <= 49) & (E[ids] == 0) & (p.jour - A[ids] >= POST_PARTUM_J)
    cand = ids[f]
    if len(cand) == 0: return
    en_couple = conj[cand] >= 0
    k = facteur_couples(d.fecondite, age[f], en_couple)
    rng = p.du_jour("population_conception")
    u = rng.random(len(cand))
    for i in cand[tirer_conceptions(d.fecondite, age[f], en_couple, u, k)].tolist():
        H[i] = p.jour; E[i] = 1
        pere = int(conj[i])
        p.compter("conception")
        if rng.random() < FAUSSE_COUCHE:
            p.poser(int(rng.integers(42, 85)) * C.PAS_PAR_JOUR + int(rng.integers(0, C.PAS_PAR_JOUR)),
                    "fin_de_grossesse", i, (0, pere, 0))
        else:
            g = int(min(294, max(196, rng.normal(*GESTATION_J))))
            p.poser(g * C.PAS_PAR_JOUR + int(rng.integers(0, C.PAS_PAR_JOUR)), "fin_de_grossesse", i,
                    (1, pere, 2 if rng.random() < JUMEAUX else 1))


def _fin_de_grossesse(p, mere_id, donnees):
    issue, pere, n = donnees
    w = p.w; d = p.domaine("population")
    E = p.col("habitant", "enceinte")
    mere = w.habitants[mere_id]
    if not mere.vivant or not E[mere_id]: return            # la grossesse s est arretee avec la mere
    E[mere_id] = 0
    if issue == 0:
        p.compter("fausse_couche"); return
    p.col("habitant", "accouchement_j")[mere_id] = p.jour
    rng = p.hasard("population_naissance")
    for _ in range(n): _naitre(p, d, mere, pere, rng)
    if rng.random() < MORT_MATERNELLE: deceder(p, mere, "maternelle")


def _naitre(p, d, mere, pere, rng):
    w = p.w
    b = P.Habitant(d.prochain_habitant, "enfant", mere.classe, 0)
    d.prochain_habitant += 1
    if b.id != len(w.habitants): raise RuntimeError("identifiants d habitants non denses : les colonnes ne suivent plus")
    mg = mere.menage
    b.menage, b.domicile, b.lieu, b.poste = mg, mg.domicile, mg.domicile, "maison"
    b.horaire, b.travail = None, None                      # un nourrisson ne va pas a l ecole ( il ira a 6 ans )
    b.decalage = float(rng.integers(-30, 31))
    w.habitants.append(b); mg.membres.append(b)
    p.colonnes["habitant"].assurer(len(w.habitants))
    col = p.colonnes["habitant"]
    col["sexe"][b.id] = HOMME if rng.random() < GARCON else FEMME
    col["naissance_j"][b.id] = p.jour
    col["mere"][b.id] = mere.id; col["pere"][b.id] = pere
    col["inscrit"][b.id] = 0
    d.enfants_de.setdefault(mere.id, []).append(b.id)
    if pere >= 0: d.enfants_de.setdefault(pere, []).append(b.id)
    d.naissances += 1
    p.poser(int(rng.integers(DECLARATION_NAISSANCE_J[0], DECLARATION_NAISSANCE_J[1] + 1)) * C.PAS_PAR_JOUR,
            "declarer_naissance", b.id)
    p.noter("naissance", enfant=b.id, mere=mere.id, pere=pere, lieu=mg.domicile.id)


def _declarer_naissance(p, hid, donnees):
    ins = p.col("habitant", "inscrit")
    if ins[hid]: return                    # deja declare ( ne et mort avant sa declaration )
    ins[hid] = 1
    ec = p.domaine("population").etat_civil
    ec.naissances += 1; ec.inscrits_vivants += 1
    p.compter("declaration_naissance")


# ================================================================== deces
def deceder(p, h, cause):
    """LE chemin de toute mort, quel que soit le domaine qui la cause. Ferme la vie, puis traite ses suites."""
    if not h.vivant and p.col("habitant", "deces_j")[h.id] >= 0: return
    h.vivant = False; h.lieu = None
    _apres_deces(p, h, cause)


def _apres_deces(p, h, cause):
    d = p.domaine("population")
    col = p.colonnes["habitant"]
    col["deces_j"][h.id] = p.jour
    col["cause_deces"][h.id] = CAUSES.index(cause)
    col["enceinte"][h.id] = 0
    c = int(col["conjoint"][h.id])
    conjoint_vivant = c >= 0 and p.w.habitants[c].vivant
    if c >= 0: col["conjoint"][c] = -1                      # le conjoint devient veuf ; le defunt garde son lien
    d.deces += 1
    p.poser(DECLARATION_DECES_J * C.PAS_PAR_JOUR, "declarer_deces", h.id)
    p.noter("deces", habitant=h.id, age=round(age_de(p, h), 1), cause=cause)
    _heriter(p, d, h, conjoint_vivant)


def _declarer_deces(p, hid, donnees):
    col = p.colonnes["habitant"]
    if col["deces_declare"][hid]: return
    ec = p.domaine("population").etat_civil
    if not col["inscrit"][hid]:                              # ne et mort avant d etre declare : les deux actes ensemble
        col["inscrit"][hid] = 1; ec.naissances += 1; ec.inscrits_vivants += 1
    col["deces_declare"][hid] = 1
    ec.deces += 1; ec.inscrits_vivants -= 1
    p.compter("declaration_deces")


def _heritiers(p, d, h):
    """Les enfants vivants ; a defaut les parents vivants. ( Freres, soeurs et au-dela : non modelises, l Etat herite. )"""
    w = p.w
    enfants = [w.habitants[i] for i in d.enfants_de.get(h.id, ()) if w.habitants[i].vivant]
    if enfants: return enfants
    col = p.colonnes["habitant"]
    return [w.habitants[int(col[k][h.id])] for k in ("mere", "pere") if col[k][h.id] >= 0 and w.habitants[int(col[k][h.id])].vivant]


def _heriter(p, d, h, conjoint_vivant):
    """Code civil grec simplifie. Si le menage garde un adulte, seule la part du defunt ( caisse / adultes ) va aux
    enfants qui vivent AILLEURS ( 3/4 s il laisse un conjoint ). Sinon les mineurs sont places, et tout le menage va
    aux heritiers ; sans heritier, a l Etat ( desherence, art. 1824 )."""
    w = p.w; L = p.socle.livre
    mg = h.menage
    restants = adultes_vivants(p, mg)
    heritiers = _heritiers(p, d, h)
    if restants:
        if age_de(p, h) < AGE_MAJEUR: return               # un mineur ne possede pas la caisse du menage
        enfants = [w.habitants[i] for i in d.enfants_de.get(h.id, ()) if w.habitants[i].vivant]
        if not enfants: return                             # conjoint et co-residents gardent le menage
        part = mg.caisse / (len(restants) + 1)
        quote = part * ((1 - HERITAGE_CONJOINT) if conjoint_vivant else 1.0) / len(enfants)
        for e in enfants:
            if e.menage is not mg and quote > 0:
                L.transferer(mg, e.menage, quote, "heritage"); p.compter("heritage", quote)
        return
    # plus aucun adulte : les mineurs d abord
    rng = p.hasard("population_placement")
    for x in [x for x in mg.membres if x.vivant]: _placer(p, d, x, rng)
    beneficiaires = [x.menage for x in heritiers if x.menage is not mg] if heritiers else []
    if beneficiaires:
        quote = mg.caisse / len(beneficiaires)
        for b in beneficiaires: L.transferer(mg, b, quote, "heritage"); p.compter("heritage", quote)
        beneficiaires[0].garde_manger += mg.garde_manger; mg.garde_manger = 0.0
    else:
        montant = L.transferer(mg, w.gouv, mg.caisse, "desherence")
        w.publics["population"]["nourriture"] += mg.garde_manger; mg.garde_manger = 0.0
        if montant > 0: p.noter("desherence", menage=mg.id, montant=round(montant, 2))
    _dissoudre_si_vide(p, mg)


def _placer(p, d, x, rng):
    """Un mineur sans adulte : l autre parent, un grand-parent, un frere ou une soeur majeur, sinon une famille
    d accueil de son lieu. Jamais un enfant seul dans un menage vide."""
    w = p.w; col = p.colonnes["habitant"]
    candidats = []
    parents = [int(col[k][x.id]) for k in ("mere", "pere") if col[k][x.id] >= 0]
    for i in parents: candidats.append((w.habitants[i], "parent"))
    for i in parents:
        for k in ("mere", "pere"):
            g = int(col[k][i])
            if g >= 0: candidats.append((w.habitants[g], "grand_parent"))
    for i in parents:
        for s in d.enfants_de.get(i, ()):
            if s != x.id: candidats.append((w.habitants[s], "fratrie"))
    for c, lien in candidats:
        if c.vivant and c.menage is not x.menage and age_de(p, c) >= AGE_MAJEUR and not p.col("menage", "dissous")[c.menage.id]:
            deplacer_membre(p, x, c.menage); d.placements += 1
            p.noter("placement", enfant=x.id, menage=c.menage.id, lien=lien); return
    accueil = [m for m in w.menages if m.domicile is x.domicile and m is not x.menage and adultes_vivants(p, m)]
    if not accueil:
        accueil = [m for m in w.menages if m is not x.menage and adultes_vivants(p, m)]
    m = accueil[int(rng.integers(0, len(accueil)))]
    deplacer_membre(p, x, m); d.placements += 1
    p.noter("placement", enfant=x.id, menage=m.id, lien="accueil")


def _reprendre_les_morts(p):
    """Chaque soir : les morts que le moteur E1 a causees sans passer par `deceder` ( l epidemie ) sont traitees."""
    dj = p.col("habitant", "deces_j")
    for h in p.w.habitants:
        if not h.vivant and dj[h.id] < 0: _apres_deces(p, h, "maladie")


# ================================================================== unions et divorces
def _hasard_union(age):
    r = 0.0
    for a, v in UNION_AN:
        if age >= a: r = v
    return r


def _apparentes(col, a, b):
    """Parent et enfant, ou freres et soeurs ( une mere ou un pere commun connu )."""
    if col["mere"][b] == a or col["pere"][b] == a or col["mere"][a] == b or col["pere"][a] == b: return True
    return any(col[k][a] >= 0 and col[k][a] == col[k][b] for k in ("mere", "pere"))


def _apparier(p, d, femmes, hommes, forme, col):
    """Chaque femme retenue par `forme( age )` epouse l homme libre de son lieu dont l age est le plus proche du sien
    + 3 ans ( a 12 ans pres ). Recherche par dichotomie sur les ages tries : le cout suit le nombre d unions, pas le
    produit des celibataires ( a 50 millions d habitants, une capitale en compte des centaines de milliers )."""
    hommes = sorted(hommes)                                 # ( age, identifiant )
    ages = [a for a, _ in hommes]
    w = p.w
    for i, a in femmes:
        if not hommes or not forme(a): continue
        cible = a + ECART_AGE_COUPLE
        k = bisect.bisect_left(ages, cible)
        choix = [j for j in (k - 1, k) if 0 <= j < len(hommes) and abs(ages[j] - cible) <= ECART_AGE_MAX
                 and not _apparentes(col, i, hommes[j][1])]
        if not choix: continue
        j = min(choix, key=lambda j: (abs(ages[j] - cible), hommes[j][1]))
        if _unir(p, d, w.habitants[i], w.habitants[hommes[j][1]]):
            del hommes[j]; del ages[j]


def _peut_partir(p, h, emmene):
    """h peut-il quitter son menage ( avec les mineurs `emmene` ) sans y laisser un mineur seul ?"""
    reste = [x for x in h.menage.membres if x.vivant and x is not h and x not in emmene]
    return not reste or any(age_de(p, x) >= AGE_MAJEUR for x in reste)


def _ses_mineurs(p, h):
    col = p.colonnes["habitant"]
    return [x for x in h.menage.membres if x.vivant and age_de(p, x) < AGE_MAJEUR
            and (col["mere"][x.id] == h.id or col["pere"][x.id] == h.id)]


def _rejoindre(p, h, dest, motif):
    """h ( et ses mineurs ) rejoignent le menage `dest`, avec sa part de la caisse ; un menage qui se vide remet tout."""
    L = p.socle.livre; old = h.menage
    mineurs = _ses_mineurs(p, h)
    adultes = len(adultes_vivants(p, old))
    part = old.caisse / max(1, adultes)
    for x in [h] + mineurs: deplacer_membre(p, x, dest)
    if not any(x.vivant for x in old.membres):
        L.transferer(old, dest, old.caisse, motif)
        dest.garde_manger += old.garde_manger; old.garde_manger = 0.0
        p.col("menage", "dissous")[old.id] = 1
    elif part > 0:
        L.transferer(old, dest, part, motif)


def _unir(p, d, f, m):
    col = p.colonnes["habitant"]
    if f.menage is not m.menage:
        cand = sorted(((f, m), (m, f)), key=lambda c: sum(1 for x in c[0].menage.membres if x.vivant))
        for qui, vers in cand:
            if _peut_partir(p, qui, _ses_mineurs(p, qui)):
                _rejoindre(p, qui, vers.menage, "union_des_biens"); break
        else:
            return False
    col["conjoint"][f.id] = m.id; col["conjoint"][m.id] = f.id
    col["union_j"][f.id] = col["union_j"][m.id] = p.jour
    d.unions += 1; d.etat_civil.unions += 1
    p.noter("union", femme=f.id, homme=m.id, lieu=f.domicile.id)
    return True


def _separer(p, d, f, m, rng):
    """Le parent qui garde les enfants garde le menage ; l autre part, avec la moitie de la caisse du couple."""
    col = p.colonnes["habitant"]
    L = p.socle.livre
    garde = f if rng.random() < GARDE_A_LA_MERE else m
    part = m if garde is f else f
    old = garde.menage
    if part.menage is old:
        neuf = nouveau_menage(p, old.domicile)
        adultes = len(adultes_vivants(p, old))
        moitie = old.caisse * (0.5 if adultes <= 2 else 1.0 / adultes)
        deplacer_membre(p, part, neuf)
        L.transferer(old, neuf, moitie, "partage_des_biens")
    col["conjoint"][f.id] = col["conjoint"][m.id] = -1
    d.divorces += 1; d.etat_civil.divorces += 1
    p.noter("divorce", femme=f.id, homme=m.id)


def _unions_et_divorces(p, d, ids, age, sexe):
    w = p.w; col = p.colonnes["habitant"]
    rng = p.du_jour("population_union")
    conj = col["conjoint"][ids]
    seuls = (conj < 0) & (age >= AGE_MAJEUR)
    par_lieu = {}
    for i, a, s in zip(ids[seuls].tolist(), age[seuls].tolist(), sexe[seuls].tolist()):
        h = w.habitants[i]
        par_lieu.setdefault(h.domicile.id, ([], []))[s].append((i, a))
    tirage = _TirageUnion(rng)
    for lid in sorted(par_lieu):
        femmes, hommes = par_lieu[lid]
        if femmes and hommes: _apparier(p, d, femmes, [(a, i) for i, a in hommes], tirage, col)
    # divorces : chaque couple une fois ( par la femme )
    for i in ids[(sexe == FEMME) & (conj >= 0)].tolist():
        if rng.random() < DIVORCE_AN * 7.0 / JOURS_AN:
            f, m = w.habitants[i], w.habitants[int(col["conjoint"][i])]
            if f.vivant and m.vivant: _separer(p, d, f, m, rng)


class _TirageUnion:
    """Une femme seule forme-t-elle une union cette semaine ?"""
    __slots__ = ("rng",)
    def __init__(self, rng): self.rng = rng
    def __call__(self, age): return self.rng.random() < _hasard_union(age) * 7.0 / JOURS_AN


class _TirageRecensement:
    """Une femme du recensement vit-elle en couple ? La part par age d EN_COUPLE."""
    __slots__ = ("rng",)
    def __init__(self, rng): self.rng = rng
    def __call__(self, age):
        r = 0.0
        for a, v in EN_COUPLE:
            if age >= a: r = v
        return self.rng.random() < r


# ================================================================== la journee demographique ( a l aube )
def _demographie(p):
    w = p.w; d = p.domaine("population")
    H = w.habitants; n = len(H)
    vivant = np.fromiter((h.vivant for h in H), dtype=bool, count=n)
    ids = np.nonzero(vivant)[0]
    col = p.colonnes["habitant"]
    sexe = col["sexe"][ids].astype(np.int64)
    age = _age_ans(p, ids)
    # 1. les morts naturelles
    u = p.du_jour("population_mort").random(len(ids))
    for i in ids[tirer_deces(d.mortalite, sexe, age, u)].tolist(): deceder(p, H[i], "naturelle")
    # 2. vieillir : l age du moteur suit la date de naissance ; l ecole a 6 ans, le metier a 16, la retraite a 65
    nj = col["naissance_j"]
    for i in ids.tolist():
        h = H[i]
        if not h.vivant: continue
        h.age = (p.jour - int(nj[i])) / JOURS_AN
        if h.age >= C.AGE_RETRAITE and h.role not in ("retraite", "enfant"):
            w.noter("retraite", habitant=h.id, age=round(h.age, 1), ancien_role=h.role)
            h.role, h.travail, h.horaire = "retraite", None, None
        elif h.role == "enfant":
            if h.age >= C.AGE_TRAVAIL: w.embaucher(h)
            elif h.age >= AGE_ECOLE and h.horaire is None: h.horaire, h.travail = "ecole", h.domicile.marche
    # 3. les conceptions, puis une fois par semaine les unions et les divorces
    vivant = np.fromiter((h.vivant for h in H), dtype=bool, count=n)
    ids = np.nonzero(vivant)[0]
    sexe = col["sexe"][ids].astype(np.int64); age = _age_ans(p, ids)
    _concevoir(p, d, ids, age, sexe)
    if p.jour % 7 == 0: _unions_et_divorces(p, d, ids, age, sexe)


# ================================================================== migrer
def _besoin(mg): return max(1e-6, C.NOURRITURE_PAR_JOUR * sum(1 for x in mg.membres if x.vivant))


def demenager(p, mg, dest):
    """Le menage paie le transport au marche d arrivee, puis s installe : les enfants changent d ecole, les adultes des
    metiers libres reprennent le metier qui manque la-bas ; les agents publics gardent leur poste."""
    w = p.w; L = p.socle.livre
    cout = FORFAIT_DEMENAGEMENT + TARIF_DEMENAGEMENT_KM * w.carte.km_route(mg.domicile, dest)
    if mg.caisse < cout:
        p.compter("migration_impossible"); return 0.0
    L.transferer(mg, w.marches[dest.marche.id], cout, "demenagement")
    de = mg.domicile
    mg.domicile = dest
    for h in mg.membres:
        if not h.vivant: continue
        h.domicile = dest
        if h.poste == "maison": h.lieu = dest
        if h.role == "enfant" and h.horaire == "ecole": h.travail = dest.marche
        elif h.role in LIBRES: w.embaucher(h)
    p.col("menage", "demenage_j")[mg.id] = p.jour
    p.domaine("population").migrations += 1
    p.noter("migration_interne", menage=mg.id, de=de.id, vers=dest.id, cout=round(cout, 2))
    return cout


def _soir(p):
    """20 h 10, apres le repas : la faim du jour entre dans la memoire de chaque menage, les choix de migration en
    attente recoivent leur note, et les menages affames de la semaine se demandent s ils partent."""
    w = p.w; d = p.domaine("population")
    f7 = p.col("menage", "faim7"); dis = p.col("menage", "dissous"); dem = p.col("menage", "demenage_j")
    nourri = w.nourri_menage
    for mg in w.menages:
        if dis[mg.id]: continue
        a_faim = 0 if nourri.get(mg.id, True) else 1
        f7[mg.id] = ((int(f7[mg.id]) << 1) | a_faim) & 0x7F
    dec = d.decideur
    for cle in [k for k, a in dec.attentes.items() if a.choix]:
        dec.noter(cle, 1.0 if nourri.get(cle, True) else 0.0, p.jour)
    for cle in [k for k, a in dec.attentes.items() if not a.choix]: del dec.attentes[cle]
    for mg in w.menages:
        if dis[mg.id] or not f7[mg.id] or (mg.id - p.jour) % 7 or p.jour - dem[mg.id] < DELAI_ENTRE_MIGRATIONS_J: continue
        adultes = adultes_vivants(p, mg)
        if not adultes: continue
        ici = w.marches[mg.domicile.marche.id]
        autres = [m for m in w.marches.values() if m.lieu.ile == mg.domicile.ile and m is not ici]
        if not autres: continue
        la = min(autres, key=lambda m: (m.prix["nourriture"], m.lieu.id))
        pm = 5 * C.PRIX_MONDE["nourriture"]
        besoin = _besoin(mg)
        km = w.carte.km_route(mg.domicile, la.lieu)
        cout = FORFAIT_DEMENAGEMENT + TARIF_DEMENAGEMENT_KM * km
        membres = [x for x in mg.membres if x.vivant]
        traits = (bin(int(f7[mg.id])).count("1") / 7.0,
                  min(1.0, ici.prix["nourriture"] / pm), min(1.0, la.prix["nourriture"] / pm),
                  min(5.0, mg.garde_manger / besoin) / 5.0,
                  min(1.0, mg.caisse / max(1e-6, 30 * besoin * ici.prix["nourriture"])),
                  sum(1 for x in membres if age_de(p, x) < AGE_MAJEUR) / len(membres),
                  min(1.0, km / 60.0))
        if dec.decider(mg.id, ContexteMigration(traits, la.lieu, cout)) == 1:
            paye = demenager(p, mg, la.lieu)
            if paye > 0: dec.ajouter(mg.id, -paye / max(1e-6, 7 * besoin * ici.prix["nourriture"]))


# ================================================================== installation
def _recensement(p, d, rng):
    """Le jour de l installation : sexe, date de naissance, couples et filiations du pays que le moteur a genere
    ( des adultes tous seuls, des enfants et des retraites repartis au hasard ). Un recensement, pas une histoire."""
    w = p.w; col = p.colonnes["habitant"]
    for h in w.habitants:
        col["sexe"][h.id] = HOMME if rng.random() < PART_HOMMES.get(h.role, 0.5) else FEMME
        col["naissance_j"][h.id] = p.jour - int(round(h.age * JOURS_AN)) - int(rng.integers(0, 365))
        col["inscrit"][h.id] = 1
        h.age = (p.jour - int(col["naissance_j"][h.id])) / JOURS_AN
        if h.role == "enfant" and h.age < AGE_ECOLE: h.horaire, h.travail = None, None
    # couples : la part des adultes en couple suit un hasard par age, le partenaire est pris dans le meme lieu
    par_lieu = {}
    for h in w.habitants:
        if h.age >= AGE_MAJEUR: par_lieu.setdefault(h.domicile.id, ([], []))[int(col["sexe"][h.id])].append((h.id, int(h.age)))
    tirage = _TirageRecensement(rng)
    for lid in sorted(par_lieu):
        femmes, hommes = par_lieu[lid]
        if femmes and hommes: _apparier(p, d, femmes, [(a, i) for i, a in hommes], tirage, col)
    d.unions = d.etat_civil.unions = 0                       # les couples du recensement ne sont pas des unions du jour
    # les jeunes celibataires chez leurs parents : une femme du meme lieu, de 18 a 45 ans leur ainee, devient leur mere
    meres = {}
    for m in w.menages:
        for x in m.membres:
            if col["sexe"][x.id] == FEMME and x.age >= 36: meres.setdefault(m.domicile.id, []).append(x)
    for h in w.habitants:
        r = next((v for a, v in reversed(FOYER_PARENTAL) if h.age >= a), 0.0) if h.age >= AGE_MAJEUR else 0.0
        if col["conjoint"][h.id] >= 0 or d.enfants_de.get(h.id) or rng.random() >= r: continue
        cands = [x for x in meres.get(h.domicile.id, ()) if 18 <= x.age - h.age <= 45 and x.menage is not h.menage
                 and not d.enfants_de.get(h.id)]
        if not cands or not _peut_partir(p, h, ()): continue
        mere = cands[int(rng.integers(0, len(cands)))]
        _rejoindre(p, h, mere.menage, "mise_en_commun")
        col["mere"][h.id] = mere.id; d.enfants_de.setdefault(mere.id, []).append(h.id)
        c = int(col["conjoint"][mere.id])
        if c >= 0 and 18 <= w.habitants[c].age - h.age <= 55:
            col["pere"][h.id] = c; d.enfants_de.setdefault(c, []).append(h.id)
    # filiations : un enfant a pour mere une femme de son menage de 18 a 45 ans de plus, pour pere son conjoint
    for h in w.habitants:
        if h.age >= AGE_MAJEUR: continue
        for x in h.menage.membres:
            if x is not h and col["sexe"][x.id] == FEMME and 18 <= x.age - h.age <= 45:
                col["mere"][h.id] = x.id; d.enfants_de.setdefault(x.id, []).append(h.id)
                c = int(col["conjoint"][x.id])
                if c >= 0 and 18 <= w.habitants[c].age - h.age <= 55:
                    col["pere"][h.id] = c; d.enfants_de.setdefault(c, []).append(h.id)
                break
    # grossesses en cours : autant qu en regime permanent, a un terme tire au hasard
    for h in w.habitants:
        a = int(h.age)
        if col["sexe"][h.id] != FEMME or not 15 <= a <= 49: continue
        if rng.random() < d.fecondite.asfr[a] * GESTATION_J[0] / JOURS_AN:
            reste = int(rng.integers(1, int(GESTATION_J[0])))
            col["conception_j"][h.id] = p.jour - (int(GESTATION_J[0]) - reste); col["enceinte"][h.id] = 1
            p.poser(reste * C.PAS_PAR_JOUR + int(rng.integers(0, C.PAS_PAR_JOUR)), "fin_de_grossesse", h.id,
                    (1, int(col["conjoint"][h.id]), 2 if rng.random() < JUMEAUX else 1))


def installer(p):
    w = p.w
    if any(h.id != k for k, h in enumerate(w.habitants)) or any(m.id != k for k, m in enumerate(w.menages)):
        raise RuntimeError("population : les identifiants du moteur doivent etre denses ( rang = identifiant )")
    ch, cm = p.colonnes["habitant"], p.colonnes["menage"]
    for nom, dt, defaut in (("sexe", np.int8, -1), ("naissance_j", np.int32, 0), ("mere", np.int32, -1),
                            ("pere", np.int32, -1), ("conjoint", np.int32, -1), ("union_j", np.int32, -1),
                            ("enceinte", np.int8, 0), ("conception_j", np.int32, 0), ("accouchement_j", np.int32, -100000),
                            ("deces_j", np.int32, -1), ("cause_deces", np.int8, 0), ("inscrit", np.int8, 0),
                            ("deces_declare", np.int8, 0)):
        ch.ajouter(nom, dt, defaut)
    for nom, dt, defaut in (("dissous", np.int8, 0), ("faim7", np.int8, 0), ("demenage_j", np.int32, -100000)):
        cm.ajouter(nom, dt, defaut)
    ch.assurer(len(w.habitants)); cm.assurer(len(w.menages))
    L = p.socle.livre
    for m in ("heritage", "desherence", "union_des_biens", "partage_des_biens", "mise_en_commun"):
        L.declarer_motif(m, "transfert_capital", "population")
    L.declarer_motif("demenagement", "achat", "population")
    J = p.socle.journal
    for t, champs in (("naissance", ("enfant", "mere", "pere", "lieu")), ("deces", ("habitant", "age", "cause")),
                      ("union", ("femme", "homme")), ("divorce", ("femme", "homme")),
                      ("placement", ("enfant", "menage", "lien")), ("desherence", ("menage", "montant")),
                      ("migration_interne", ("menage", "de", "vers"))):
        J.declarer(t, "population", "individuel", champs)
    for t in ("conception", "fausse_couche", "heritage", "declaration_naissance", "declaration_deces", "migration_impossible"):
        J.declarer(t, "population", "compte")
    p.echeance("fin_de_grossesse", _fin_de_grossesse)
    p.echeance("declarer_naissance", _declarer_naissance)
    p.echeance("declarer_deces", _declarer_deces)
    vivants0 = sum(1 for h in w.habitants if h.vivant)
    d = Demographie(TableDeMortalite(), TableDeFecondite(), EtatCivil(vivants0), p.decideur(POINT_MIGRER),
                    len(w.habitants), vivants0)
    p.domaines["population"] = d                            # le recensement a besoin du domaine deja visible
    _recensement(p, d, p.hasard("population_recensement"))
    w.demographie = RemplaceDemographie(p)
    p.routine(20 + 10 / 60, 10, "population", _soir)
    p.routine(23 + 50 / 60, 90, "population", _reprendre_les_morts)
    return d


# ================================================================== controles ( pour les portes )
def anomalies_familles(p):
    """Les incoherences de la population : un vivant dans un menage dissous, un mineur sans adulte, un habitant absent
    de son propre menage, un conjoint non reciproque, un mort non traite."""
    w = p.w; col = p.colonnes["habitant"]; dis = p.col("menage", "dissous")
    out = []
    for h in w.habitants:
        if h not in h.menage.membres: out.append(("hors_de_son_menage", h.id))
        if h.vivant:
            if dis[h.menage.id]: out.append(("vivant_dans_menage_dissous", h.id))
            c = int(col["conjoint"][h.id])
            if c >= 0 and (not w.habitants[c].vivant or int(col["conjoint"][c]) != h.id): out.append(("conjoint", h.id))
        elif col["deces_j"][h.id] < 0: out.append(("mort_non_traite", h.id))
    for m in w.menages:
        v = [x for x in m.membres if x.vivant]
        if v and not any(age_de(p, x) >= AGE_MAJEUR for x in v): out.append(("mineurs_seuls", m.id))
    return out


def recompte_etat_civil(p):
    col = p.colonnes["habitant"]; n = len(p.w.habitants)
    return int(((col["inscrit"][:n] == 1) & (col["deces_declare"][:n] == 0)).sum())
