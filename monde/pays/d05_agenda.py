"""DOMAINE 5 - VIE QUOTIDIENNE : AGENDA ET MOBILITE DES PERSONNES.

FICHE
1. Classes. TypeDeJour ( ce que le calendrier du socle dit d une journee du monde : ouvree, samedi, repos, culte,
   veille de repos ), Releve ( ce que le plan lit des habitants, une fois par jour ), Plan ( le planning du jour de
   chaque habitant, en colonnes numpy : au plus six tours partis de la maison et qui y reviennent - report de la nuit,
   culte, travail ou ecole, courses, loisir de jour, loisir du soir -, chacun avec son depart, son arrivee, sa fin et
   son retour en minutes depuis 6 h, sa destination, son activite et son mode ), Agenda ( l etat du domaine : lieux,
   distances, plan du jour, presences par lieu et par cadre, rumeur ), ContexteSortie, RemplaceDeplacer ( prend la
   place de Monde.deplacer ). Colonnes par habitant : agenda_lieu et agenda_activite ( le miroir de ou il est ),
   agenda_pas_travail, agenda_pas_prevus, agenda_indocile, agenda_pratiquant ; par menage : agenda_jour_marche.
2. Invariants. Chaque habitant vivant, hors de la mer et des sejours, est au pas pres la ou son plan le met, dans un
   lieu que ses activites expliquent ( `incoherences` vide ) ; le miroir dit la meme chose que Habitant.lieu et poste
   ( `ecarts_miroir` vide ). La presence au travail couvre exactement les pas ou Habitant.au_travail est vrai, les jours
   ou son horaire ouvre : la production du moteur, qui compte les presents avec cette horloge, reste juste. Les tours
   d un habitant ne se chevauchent pas. Tout trajet a une duree que sa distance et son mode expliquent
   ( `trajets_incoherents` vide ). Le domaine ne DETIENT rien : ni argent, ni bien.
3. Decision `sortir` ( chaque adulte, chaque matin a 6 h, tant que l epidemie du moteur court : un E ou un I vivant ) :
   rester chez soi ou sortir ( travail, culte, loisirs, courses ). Traits : ses symptomes ( I se sent, E non ), les
   malades connus de son lieu hier ( la rumeur : la moitie des malades, pas la verite ), la quarantaine sur son lieu,
   sa faim, les jours de nourriture que paie la caisse de son menage, s il travaille aujourd hui. Note, pour SON
   menage, chaque jour : ( part des membres ni E ni I + part des heures de travail prevues faites + a mange ) / 3,
   moyennee sur 7 jours ( incubation 2 j + maladie 5 j : une contamination du jour pese sur toute la fenetre ) ;
   un decideur mort note 0. Regle : rester si symptomes, ou si la quarantaine vise son lieu et qu il n est pas
   indocile ( la desobeissance du moteur, config.QUARANTAINE_VIOLEE, devenue un temperament stable ). Temoin :
   toujours sortir. Hors epidemie, la regle s applique sans decideur. Les mineurs ne decident pas : ils restent si
   malades, confines, ou si tous les adultes de leur menage restent.
4. Evenements ( comptes, un appel par jour dont la somme porte le nombre ) : agenda_decisions, agenda_rester,
   agenda_sans_acheteur, agenda_hors_ile, agenda_culte, agenda_loisir, agenda_km_vehicule, agenda_revision.
5. Liens. Lit la population ( ages, menages : domaine 1 ), le calendrier du socle ( semaine, feries grecs ), les lois
   ( quarantaine, couvre-feu ), la sante du moteur ( etat, gravite ), la faim, les agents travailleurs s ils sont la.
   Remplace Monde.deplacer en gardant tout ce qu il faisait ( voyage en mer, sejours, hopital, quarantaine et sa
   desobeissance, faim qui empeche de travailler, agents travailleurs, heures payees des fonctionnaires ). Donne aux
   autres : `planning`, `position`, `qui_est_la`, `contacts_par_lieu` ( la medecine, domaine 16 ), `trafic`
   ( transport, energie ), `lieux_de_loisir` ( culture, domaine 23 ), `tours_du_jour`, `replanifier` ( a appeler par
   un domaine qui deplace ou hospitalise quelqu un en cours de journee ), `incoherences`, `ecarts_miroir`,
   `trajets_incoherents`, et les colonnes agenda_lieu / agenda_activite pour une contagion vectorisee.
6. Portes : tests_d05_agenda.py.
7. Arma. Pendant un trajet, Habitant.lieu est DEJA la destination et le poste vaut `trajet` : la bulle recoit l ordre
   de marche au depart, avec sa destination ( lecon payee : un agent ne bouge qu avec une destination posee avant
   l ordre ). `position` interpole le trajet pour poser un corps entre deux lieux. Les departs sont etales ( decalage
   personnel de +/- 30 min, heures tirees au hasard pour le culte, les courses et les loisirs ) : porte test_departs.
   Le vehicule du trajet ( voiture, bus scolaire ) appartient au transport ( domaine 14 ) : aucun classname ici.
8. Cout. Un plan par jour, a 6 h : une lecture des habitants ( une boucle ), des tours calcules en numpy, une passe
   vectorisee par menage pour les courses ; puis, a chaque pas, seuls les habitants dont l etat change sont touches
   ( environ 6 par habitant et par jour, contre 144 pour Monde.deplacer ). Memoire : environ 100 octets par habitant
   pour le plan du jour. Mesure du 23/09 ( test_cout, 10 000 habitants, jours 0 a 4 ) : moteur et population 1,69 s
   par jour, avec l agenda 0,78 s ( -54 % : Monde.deplacer coutait a lui seul 1,04 s par jour ) ; l agenda lui-meme
   0,24 s par jour, 24 us par habitant. Tout est lineaire en habitants : environ 25 s par jour a 1 million ( contre
   ~100 s pour Monde.deplacer ), 20 minutes a 50 millions, avant portage en Rust.
   Limite connue : Monde.produire compte present a son travail qui est dans le LIEU de son travail ; un paysan vit dans
   le village de sa ferme, il y est donc compte le dimanche meme chez lui ( porte test_travail_fait, echec explique )."""
import datetime as dt
import numpy as np
from .. import config as C
from ..socle import decision as D
from . import d01_population as POP
from .. import population as MPOP      # les colonnes du moteur ( monde.table ) : l agenda y lit et y ecrit directement

# ================================================================== le temps du domaine
MINUTE_AUBE = 6 * 60          # la journee du monde va de l aube du moteur ( Monde.aube, 6 h ) au lendemain 6 h
PAS_MIN = C.MINUTES_PAR_PAS
PAS_JOUR = C.PAS_PAR_JOUR
MINUTES_JOUR = 24 * 60
PAS_H = PAS_MIN / 60.0
K_REVISION = (20 * 60 + 10 - MINUTE_AUBE) // PAS_MIN     # 20 h 10 : le repas de 20 h a change la faim

# ================================================================== les activites ( codes du miroir agenda_activite )
MAISON, TRAJET, TRAVAIL, ECOLE, COURSES, LOISIR, CULTE, HOPITAL, VOYAGE = range(9)
HORS = -1                     # mort, ou pas encore place
ACTIVITES = ("maison", "trajet", "travail", "ecole", "courses", "loisir", "culte", "hopital", "voyage")
# le poste du moteur : l ecole reste `travail`, comme dans Monde.deplacer ( la bulle y cherche le batiment du role )
POSTES = ("maison", "trajet", "travail", "travail", "courses", "loisir", "culte", "hopital", "voyage")
CODE_POSTE_MOTEUR = np.array([MPOP.CODE_POSTE[x] for x in POSTES], np.uint8)     # activite -> code du poste du moteur
POSTE_VOYAGE = MPOP.CODE_POSTE["voyage"]
NA = len(ACTIVITES)
# une destination : un indice de lieu ( >= 0 ), ou un lieu relu sur l habitant au moment ou il part ( un demenagement
# ou une embauche du jour sont alors suivis sans refaire le plan )
DOMICILE, MARCHE, LIEU_TRAVAIL = -2, -3, -4
# les tours du jour : chacun part de la maison et y revient
REPORT, T_CULTE, T_TRAVAIL, T_COURSES, T_LOISIR_JOUR, T_LOISIR_SOIR = range(6)
TOURS = ("report", "culte", "travail", "courses", "loisir_jour", "loisir_soir")
NS = len(TOURS)
DEP, ARR, FIN, RET = range(4)
A_PIED, EN_VEHICULE = 0, 1
MODES = ("marche", "vehicule")

# ================================================================== les horaires du moteur, et les jours ou ils ouvrent
HORAIRES = ("jour", "bureau", "ecole", "marche", "garde", "nuit")      # code = rang + 1 ; 0 : aucun horaire
CODE_HORAIRE = {None: 0, **{h: k + 1 for k, h in enumerate(HORAIRES)}}
HORAIRE_DU_MOTEUR = np.array([CODE_HORAIRE.get(MPOP.HORAIRE_DE_CODE[c], 0) for c in range(-1, max(MPOP.HORAIRE_DE_CODE) + 1)],
                             np.float64)
SEMAINE = ("jour", "bureau", "ecole")    # fermes le samedi, le dimanche et les jours feries
DU_LUNDI_AU_SAMEDI = ("marche",)          # hors jours feries
CONTINUS = ("garde", "nuit")             # tous les jours : trois equipes de 8 h, ou la nuit
DEBUT_EQUIPE_H = (6, 14, 22)             # Habitant.au_travail
DUREE_EQUIPE_MIN = 8 * 60

# ================================================================== se deplacer
VITESSE_MARCHE_KMH = 4.8        # Bohannon ( 1997, Age and Ageing 26 ) : marche confortable de l adulte, 1,3 a 1,46 m/s
VITESSE_VEHICULE_KMH = 40.0     # celle des convois du moteur sur les routes d Altis ( config.VITESSE_CONVOI_KMH ) ; a calibrer pour une voiture
ACCES_VEHICULE_MIN = 5          # rejoindre la voiture ou attendre le bus, se garer ( a calibrer )
SEUIL_MARCHE_KM = 1.5           # au-dela, un vehicule ( a calibrer : hors des centres, la voiture domine les trajets grecs )
FACTEUR_INTRA = 128.0 / (45.0 * np.pi)   # distance moyenne entre deux points d un disque de rayon R : 0,905 R
INTRA_MIN_KM = 0.15             # lieu sans rayon connu ( site industriel ) : 150 m entre deux batiments ( a calibrer )
BORNES_VITESSE = {A_PIED: (2.5, 7.0), EN_VEHICULE: (8.0, 70.0)}   # km/h de porte a porte, pour le controle
PIED_MAX_KM = 3.0               # personne ne marche plus de 3 km pour aller travailler dans ce modele
DUREE_MAX_TRAJET_MIN = 180

# ================================================================== les courses
DUREE_COURSES_MIN = 30          # temps passe au marche ou a l epicerie ( a calibrer )
MARCHE_PROCHE_KM = 2.0          # a moins de 2 km du marche, on y fait ses courses chaque jour ; plus loin, a l epicerie
                                # du village, et au marche une fois par semaine, son jour ( a calibrer )
COURSES_MATIN = (9 * 60, 180)   # qui ne travaille pas part entre 9 h et 12 h ( a calibrer )
COURSES_APRES_MIN = 30          # sinon dans la demi-heure qui suit le retour du travail
FIN_COURSES = 19 * 60 - MINUTE_AUBE     # les achats du moteur tombent a 19 h : les courses sont finies avant
JOURS_MARCHE = 6                # du lundi au samedi : les commerces grecs ferment le dimanche ( hors zones touristiques )

# ================================================================== les loisirs ( parts : a calibrer )
# Ordres de grandeur retenus en attendant l enquete emploi du temps d ELSTAT : sortir un soir de semaine est
# minoritaire, la veille d un jour de repos beaucoup moins ; le kafeneio de l apres-midi est l affaire des retraites.
P_SOIR_SEMAINE = 0.20
P_SOIR_VEILLE = 0.40
P_JOUR_REPOS = 0.35
P_CAFE_RETRAITE = 0.35
P_VILLE_JEUNES = 0.40           # la veille d un repos, une sortie de jeune ( 18-34 ans ) sur 2,5 se fait en ville
AGE_SOIR = 15
JEUNES = (18, 35)
# ( debut au plus tot en minutes du jour, etalement du debut, duree minimale, etalement de la duree )
SOIR_SEMAINE = (19 * 60 + 30, 120, 60, 90)
SOIR_VEILLE = (20 * 60 + 30, 120, 90, 120)
CAFE = (17 * 60, 120, 60, 90)
JOUR_REPOS = ((11 * 60, 17 * 60), 120, 90, 90)

# ================================================================== le culte ( a calibrer )
# Ordre de grandeur : Pew Research Center ( 2017, Europe centrale et orientale ) - de l ordre d un quart des Grecs
# disent aller a l office au moins une fois par mois ; la pratique hebdomadaire est minoritaire et croit avec l age.
PRATIQUE = ((65, 0.30), (45, 0.15), (18, 0.10))     # age minimal, part qui va a la liturgie du dimanche
SUIVRE_PARENT = 0.6             # un mineur accompagne un parent pratiquant
OFFICE = (8 * 60 + 30, 60, 60, 40)                   # arrivee entre 8 h 30 et 9 h 30, 60 a 100 min ( fin vers 10 h 30 )
FERIES_CIVILS = ("fete_nationale", "fete_du_travail", "jour_du_non")   # les autres feries ont leur liturgie

# ================================================================== la decision `sortir`
GRAVITE_HOPITAL = 0.3           # Monde.deplacer : un malade I de gravite > 0,3 est a l hopital de sa capitale
P_RUMEUR = 0.5                  # part des malades ( I ) que le voisinage et les collegues connaissent ( a calibrer )
ECHELLE_RUMEUR = 10.0           # 10 % de malades connus parmi ceux qui frequentent le lieu : le trait vaut 1
FAIM_PLEINE = 3.0               # Habitant.faim ( rations manquees accumulees ) qui sature le trait
JOURS_CAISSE_PLEINS = 30.0
HORIZON_SORTIR = int(C.INCUBATION_J + C.MALADIE_J)   # 7 jours

ETATS = {"S": 0, "E": 1, "I": 2, "R": 3}
ETAT_E, ETAT_I = 1, 2
ENFANT, RETRAITE, PUBLIC = 1, 2, 4
ROLES = {r: (ENFANT if r == "enfant" else RETRAITE if r == "retraite" else 0) | (PUBLIC if v[2] else 0)
         for r, v in C.ROLES.items()}
# codes du moteur -> codes de l agenda ( indice : code du moteur + 1, le -1 du moteur voulant dire « aucun » )
ROLE_DU_MOTEUR = np.array([0] + [ROLES.get(r, 0) for r in MPOP.ROLES], np.float64)
ETAT_DU_MOTEUR = np.array([ETATS[e] for e in MPOP.ETATS], np.float64)


# ================================================================== le calendrier d une journee du monde
class TypeDeJour:
    """Ce que le calendrier du socle dit de la journee qui commence a 6 h : c est lui, et lui seul, qui connait la
    semaine et les feries grecs."""
    __slots__ = ("date", "semaine", "ferie", "ouvre", "marche", "repos", "culte", "veille")

    def __init__(self, cal, fen):
        d = cal.date(fen * PAS_JOUR).date()
        demain = d + dt.timedelta(days=1)
        self.date, self.semaine, self.ferie = d, d.weekday(), cal.ferie(d)
        self.ouvre = self.semaine < 5 and self.ferie is None                 # jour, bureau, ecole
        self.marche = self.semaine < JOURS_MARCHE and self.ferie is None     # marche, commerces, courses
        self.repos = not self.ouvre                                          # samedi, dimanche, ferie
        self.culte = self.semaine == 6 or (self.ferie is not None and self.ferie not in FERIES_CIVILS)
        self.veille = demain.weekday() >= 5 or cal.ferie(demain) is not None

    def ouvert(self, horaire):
        if horaire in SEMAINE: return self.ouvre
        if horaire in DU_LUNDI_AU_SAMEDI: return self.marche
        return True


# ================================================================== la decision
class ContexteSortie:
    """Ce qu un adulte voit le matin ou il se demande s il sort : son corps, la rumeur de son lieu, la loi, son ventre,
    sa bourse, son agenda. Et son temperament, que seule la regle lit."""
    __slots__ = ("traits", "indocile")

    def __init__(self, traits, indocile):
        self.traits, self.indocile = traits, indocile


def _observer_sortir(ctx): return ctx.traits


def _regle_sortir(x, ctx):
    return 0 if x[0] >= 0.5 or (x[2] >= 0.5 and not ctx.indocile) else 1


def _temoin_sortir(x, ctx, rng): return 1


POINT_SORTIR = D.PointDeDecision(
    "sortir", "agenda",
    traits=(("symptomes", "son propre corps : la fievre d un malade I se sent, l incubation E ne se sent pas"),
            ("malades_connus", "les malades de son lieu que la rumeur lui a appris hier, sur ceux qui le frequentent, x10"),
            ("quarantaine", "la loi publiee : son domicile ou son lieu de travail est en quarantaine"),
            ("faim", "son ventre : les rations manquees accumulees, sur 3"),
            ("jours_de_caisse", "la caisse de son menage en jours de nourriture au prix affiche, sur 30"),
            ("travail_prevu", "son agenda : il travaille aujourd hui")),
    actions=("rester", "sortir"),
    observer=_observer_sortir, regle=_regle_sortir, temoin=_temoin_sortir,
    note="pour SON menage, chaque jour : part des membres ni E ni I, part des heures de travail prevues faites, a mange",
    horizon_j=HORIZON_SORTIR)


# ================================================================== l etat du domaine
class Releve:
    """Ce que le plan lit des habitants a 6 h, en colonnes : une seule boucle par jour sur la population."""
    __slots__ = ("n", "vivant", "hors", "dom", "trav", "hor", "equipe", "decalage", "menage", "etat", "gravite",
                 "faim", "role", "age")


class Plan:
    """Le planning d une journee du monde ( 6 h -> 6 h ), pour les `n` habitants connus a 6 h. Une minute `t` se compte
    depuis 6 h ; un tour qui deborde apres 6 h le lendemain ( garde de nuit ) est repris par le plan suivant."""
    __slots__ = ("fen", "jt", "n", "actif", "tt", "dest", "act", "mode", "coupe", "dom", "trav", "hopital", "hors",
                 "public", "rester", "epuise", "gt", "cand", "cand_mode", "cand_ok", "ev_off", "ev_id", "extra",
                 "trafic", "departs", "stats")

    def __init__(self, fen, jt, n):
        self.fen, self.jt, self.n = fen, jt, n
        self.actif = np.zeros((n, NS), bool)
        self.tt = np.zeros((n, NS, 4), np.int16)       # minutes depuis 6 h : depart, arrivee, fin, retour
        self.dest = np.zeros((n, NS), np.int16)
        self.act = np.zeros((n, NS), np.int8)
        self.mode = np.zeros((n, NS), np.int8)
        self.coupe = np.zeros((n, NS), bool)            # tour interrompu en route : sa duree n est plus celle du trajet
        self.dom = np.zeros(n, np.int16); self.trav = np.full(n, -1, np.int16)
        self.hopital = np.zeros(n, bool); self.hors = np.zeros(n, bool)
        self.public = b""
        self.rester = np.zeros(n, bool); self.epuise = np.zeros(n, bool); self.gt = np.zeros(n, bool)
        self.cand = np.zeros((n, 4), np.int16); self.cand_mode = np.zeros(n, np.int8); self.cand_ok = np.zeros(n, bool)
        self.ev_off = np.zeros(PAS_JOUR + 1, np.int64); self.ev_id = np.zeros(0, np.int32)
        self.extra = {}                                  # pas -> [ habitants a relire ] ( revisions en cours de journee )
        self.trafic = np.zeros((2, PAS_JOUR), np.int32)
        self.departs = np.zeros(PAS_JOUR, np.int32)
        self.stats = {}


class Agenda:
    __slots__ = ("lieux", "index_lieu", "L", "pos", "ile", "intra_km", "marche", "km_marche", "km_paires", "decideur",
                 "plan", "k", "publics", "connus", "frequentation", "presence", "presence_hier", "epidemie")

    def __init__(self, w, decideur):
        self.lieux = list(w.carte.lieux.values())
        self.index_lieu = {l.id: k for k, l in enumerate(self.lieux)}
        # l indice d un lieu dans l agenda EST son numero dans les colonnes du moteur ( Carte.par_n, meme ordre ) :
        # l agenda ecrit `lieu` et lit `domicile`, `travail` sans traduction
        if any(l.n != k for k, l in enumerate(self.lieux)): raise RuntimeError("lieux de l agenda hors de l ordre du moteur")
        self.L = L = len(self.lieux)
        self.pos = np.array([l.pos[:2] for l in self.lieux], dtype=float)
        self.ile = [l.ile for l in self.lieux]
        r = np.array([(float(l.rayon[0] or 0), float(l.rayon[1] or 0)) if len(l.rayon) >= 2 else (0.0, 0.0)
                      for l in self.lieux])
        self.intra_km = np.maximum(INTRA_MIN_KM, FACTEUR_INTRA * np.sqrt(r[:, 0] * r[:, 1]) / 1000.0)
        self.marche = np.array([self.index_lieu[l.marche.id] for l in self.lieux], np.int32)
        self.km_paires = {}                      # paire de lieux -> km ( cache : la route ne change pas )
        self.km_marche = _km(self, w, np.arange(L, dtype=np.int32), self.marche)
        self.decideur = decideur
        self.plan = None
        self.k = 0                               # le dernier pas applique dans la journee du plan
        self.publics = set()                     # fonctionnaires au travail : payes a l heure, comme dans Monde.deplacer
        self.connus = np.zeros(L); self.frequentation = np.zeros(L)
        self.presence = np.zeros((24, L * NA), np.int32); self.presence_hier = np.zeros((24, L * NA), np.int32)
        self.epidemie = False


class RemplaceDeplacer:
    """Prend la place de Monde.deplacer ( appele a chaque pas par le moteur ) : un objet, pour rester picklable.
    L heure passee par le moteur est ignoree : le pas du monde dit ou en est la journee."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, heure=None): _pas(self.pays)


# ================================================================== distances et trajets
def _km(a, w, o, d):
    """Les km de route entre deux tableaux de lieux ; dans un meme lieu, la distance moyenne dans son disque ; entre deux
    iles, l infini ( on ne fait pas la navette par la mer )."""
    cle = o.astype(np.int64) * a.L + d
    u, inv = np.unique(cle, return_inverse=True)
    vals = np.empty(len(u))
    for j, c in enumerate(u.tolist()):
        v = a.km_paires.get(c)
        if v is None:
            x, y = divmod(c, a.L)
            if x == y: v = float(a.intra_km[x])
            elif a.ile[x] != a.ile[y]: v = float("inf")
            else: v = float(w.carte.km_route(a.lieux[x], a.lieux[y]))
            a.km_paires[c] = v
        vals[j] = v
    return vals[inv]


def duree_trajet(km):
    """( minutes, mode ) d un trajet de `km` : a pied jusqu a 1,5 km, en vehicule au-dela ( acces compris )."""
    km = np.asarray(km, float)
    pied = km <= SEUIL_MARCHE_KM
    minutes = np.where(pied, np.ceil(60.0 * km / VITESSE_MARCHE_KMH),
                       ACCES_VEHICULE_MIN + np.ceil(60.0 * km / VITESSE_VEHICULE_KMH))
    return np.maximum(1, minutes).astype(np.int32), np.where(pied, A_PIED, EN_VEHICULE).astype(np.int8)


def _trajets(a, w, o, d):
    km = _km(a, w, o, d)
    possible = np.isfinite(km)
    km = np.where(possible, km, 0.0)
    minutes, mode = duree_trajet(km)
    return minutes, mode, km, possible


def _dest_lieu(a, dom, trav, code):
    """L indice du lieu vise par un code de destination ( tableaux )."""
    return np.where(code >= 0, code, np.where(code == DOMICILE, dom, np.where(code == MARCHE, a.marche[dom], trav)))


# ================================================================== l etat d un habitant a une minute du plan
def _etat(pl, ids, t):
    """( activite, destination ) des habitants `ids` a la minute `t` ( depuis 6 h ). En trajet aller, la destination est
    le lieu du tour ; au retour, le domicile. Les tours ne se chevauchent pas : au plus un les contient."""
    n = len(ids)
    act = np.zeros(n, np.int8)
    dest = np.full(n, DOMICILE, np.int16)
    t = np.broadcast_to(np.asarray(t, np.int32), (n,))
    for s in range(NS):
        a = pl.actif[ids, s]
        if not a.any(): continue
        T = pl.tt[ids, s].astype(np.int32)
        dans = a & (T[:, DEP] <= t) & (t < T[:, RET])
        if not dans.any(): continue
        aller = dans & (t < T[:, ARR])
        sur = dans & ~aller & (t < T[:, FIN])
        retour = dans & (t >= T[:, FIN])
        d = pl.dest[ids, s]
        act[aller] = TRAJET; dest[aller] = d[aller]
        act[sur] = pl.act[ids, s][sur]; dest[sur] = d[sur]
        act[retour] = TRAJET
    h = pl.hopital[ids]
    act[h] = HOPITAL; dest[h] = MARCHE
    return act, dest


def _resoudre(a, h, code):
    if code >= 0: return a.lieux[code]
    if code == DOMICILE: return h.domicile
    if code == MARCHE: return h.domicile.marche
    return h.travail


def _appliquer(p, a, pl, ids, t):
    """Pose les habitants `ids` la ou le plan les met a la minute `t`. Un mort, un voyageur en mer, un visiteur en sejour
    sur une autre ile ne sont pas touches : le moteur les tient. EN COLONNES ( 24/09 ) : l agenda ecrit le lieu et le
    poste dans la table du moteur, sans fabriquer un habitant par personne ( 4,3 s par jour a 10 000 habitants en vues,
    profil du 24/09 ) ; la porte d identite des domaines ( monde/porte_domaines.py ) le tient pour identique."""
    if len(ids) == 0: return
    act, dest = _etat(pl, ids, t)
    w = p.w; tb = w.table; publics = a.publics
    ids = np.asarray(ids, np.int64)
    act = act.astype(np.int64); dest = dest.astype(np.int64)
    vivant = tb.vivant[ids] == 1
    en_mer = tb.poste[ids] == POSTE_VOYAGE
    sejour = np.isin(ids, np.fromiter(w.sejours, np.int64, len(w.sejours))) if w.sejours else np.zeros(len(ids), bool)
    hors = ~vivant | en_mer | sejour
    ql = np.full(len(ids), -1, np.int64)
    qa = np.full(len(ids), MAISON, np.int64)
    qa[~vivant] = HORS
    qa[vivant & en_mer] = VOYAGE
    m = vivant & ~en_mer & sejour
    ql[m] = tb.lieu[ids[m]]
    if hors.any(): publics.difference_update(ids[hors].tolist())
    ok = ~hors
    if ok.any():
        ii, ac, de = ids[ok], act[ok], dest[ok]
        dom, trav = tb.domicile[ii].astype(np.int64), tb.travail[ii].astype(np.int64)
        au_travail = (de < 0) & (de != DOMICILE) & (de != MARCHE)
        sans = au_travail & (trav < 0)               # plus de travail depuis 6 h ( retraite, depart ) : a la maison
        l = np.where(de >= 0, de, np.where(de == DOMICILE, dom, np.where(de == MARCHE, a.marche[dom], trav)))
        l = np.where(sans, dom, l)
        ac = np.where(sans, MAISON, ac)
        tb.lieu[ii] = l
        tb.poste[ii] = CODE_POSTE_MOTEUR[ac]
        ql[ok], qa[ok] = l, ac
        pub = np.frombuffer(pl.public, np.uint8)[ii] > 0
        publics.difference_update(ii[pub & (ac != TRAVAIL)].tolist())
        publics.update(ii[pub & (ac == TRAVAIL)].tolist())
    col = p.colonnes["habitant"]
    col["agenda_lieu"][ids] = ql
    col["agenda_activite"][ids] = qa


# ================================================================== le pas
def _pas(p):
    w = p.w; a = p.domaines["agenda"]
    fen, k = divmod(w.pas, PAS_JOUR)
    pl = a.plan
    if pl is None or pl.fen != fen:
        _planifier(p, a, fen, k)
    else:
        if k == K_REVISION: _revision_du_soir(p, a, pl, k)
        ids = pl.ev_id[pl.ev_off[k]:pl.ev_off[k + 1]]
        x = pl.extra.pop(k, None)
        if x: ids = np.unique(np.concatenate([ids, np.asarray(x, np.int32)]))
        _appliquer(p, a, pl, ids, PAS_MIN * k)
    a.k = k
    _fin_des_sejours(w)
    _accumuler(p, a, k)


def _fin_des_sejours(w):
    """Monde.deplacer : un visiteur dont le sejour est fini reprend le bateau vers son domicile."""
    if not w.sejours: return
    for i in sorted(i for i, fin in w.sejours.items() if w.pas >= fin):
        h = w.habitants[i]
        if not h.vivant or h.poste == "voyage": continue
        del w.sejours[i]
        w.embarquer(h, h.domicile)


def _accumuler(p, a, k):
    """Ce que chaque pas laisse : l heure payee des fonctionnaires presents ( Monde.deplacer ), les pas de travail faits
    ( la note de `sortir` ), et a l heure pleine - quand la contagion du moteur passe - les presences par lieu et cadre."""
    if a.publics:
        tb = p.w.table
        ids = np.fromiter(a.publics, np.int64, len(a.publics))
        tb.heures[ids[tb.vivant[ids] == 1]] += PAS_H
    col = p.colonnes["habitant"]
    n = a.plan.n
    act = col["agenda_activite"][:n]
    col["agenda_pas_travail"][:n] += act == TRAVAIL
    if (MINUTE_AUBE + PAS_MIN * k) % 60 == 0:
        lieu = col["agenda_lieu"][:n]
        m = (lieu >= 0) & (act >= 0)
        a.presence[k * PAS_MIN // 60] = np.bincount(lieu[m].astype(np.int64) * NA + act[m], minlength=a.L * NA)


# ================================================================== le plan du jour
def _rassembler(p, a):
    w = p.w; tb = w.table; n = tb.n
    # le releve du matin, lu dans les colonnes du moteur ( 24/09 ; il fabriquait un habitant par personne )
    hors = tb.poste[:n] == POSTE_VOYAGE
    if w.sejours: hors[np.fromiter((i for i in w.sejours if i < n), np.int64)] = True
    t = np.empty((n, 12))
    t[:, 0] = tb.vivant[:n]; t[:, 1] = hors
    t[:, 2] = tb.domicile[:n]; t[:, 3] = tb.travail[:n]
    t[:, 4] = HORAIRE_DU_MOTEUR[tb.horaire[:n].astype(np.int64) + 1]
    t[:, 5] = np.mod(tb.equipe[:n], 3); t[:, 6] = tb.decalage[:n]; t[:, 7] = tb.menage[:n]
    t[:, 8] = ETAT_DU_MOTEUR[tb.etat[:n]]; t[:, 9] = tb.gravite[:n]; t[:, 10] = tb.faim[:n]
    t[:, 11] = ROLE_DU_MOTEUR[tb.role[:n].astype(np.int64) + 1]
    g = Releve()
    g.n = n
    g.vivant = t[:, 0] > 0
    g.hors = (t[:, 1] > 0) | (t[:, 2] < 0) | (t[:, 7] < 0)
    g.dom = np.maximum(0, t[:, 2]).astype(np.int32); g.trav = t[:, 3].astype(np.int32)
    g.hor = t[:, 4].astype(np.int8); g.equipe = t[:, 5].astype(np.int8); g.decalage = t[:, 6].astype(np.int32)
    g.menage = t[:, 7].astype(np.int32); g.etat = t[:, 8].astype(np.int8); g.gravite = t[:, 9]; g.faim = t[:, 10]
    g.role = t[:, 11].astype(np.int8)
    g.age = (p.jour - p.col("habitant", "naissance_j")[:n]) / POP.JOURS_AN
    return g


def _tirer_traits(p, g):
    """Le temperament ( indocile ) et la pratique religieuse, tires une fois par habitant ; le jour du grand marche,
    une fois par menage. Les nouveaux venus ( naissances, menages neufs ) sont tires le matin qui suit."""
    col = p.colonnes["habitant"]; n = g.n
    ind, pra = col["agenda_indocile"], col["agenda_pratiquant"]
    neufs = np.nonzero(ind[:n] < 0)[0]
    if len(neufs):
        u = p.du_jour("agenda_traits").random((len(neufs), 3))
        ind[neufs] = (u[:, 0] < C.QUARANTAINE_VIOLEE).astype(np.int8)
        age = g.age[neufs]
        part = np.zeros(len(neufs))
        for a_min, v in PRATIQUE[::-1]: part[age >= a_min] = v
        adulte = age >= POP.AGE_MAJEUR
        pra[neufs[adulte]] = (u[adulte, 1] < part[adulte]).astype(np.int8)
        M = len(p.w.menages)
        ok = g.vivant & (g.menage >= 0) & (g.age >= POP.AGE_MAJEUR) & (pra[:n] == 1)
        parent = np.bincount(g.menage[ok], minlength=M) > 0
        mineur = np.nonzero(~adulte)[0]
        mg = g.menage[neufs[mineur]]
        pra[neufs[mineur]] = ((mg >= 0) & parent[np.maximum(mg, 0)] & (u[mineur, 2] < SUIVRE_PARENT)).astype(np.int8)
    jm = p.col("menage", "agenda_jour_marche"); M = len(p.w.menages)
    nm = np.nonzero(jm[:M] < 0)[0]
    if len(nm): jm[nm] = p.du_jour("agenda_menages").integers(0, JOURS_MARCHE, len(nm))


def _poser(pl, idx, s, dep, arr, fin, ret, dest, act, mode):
    if len(idx) == 0: return
    pl.actif[idx, s] = True
    pl.tt[idx, s, DEP] = dep; pl.tt[idx, s, ARR] = arr; pl.tt[idx, s, FIN] = fin; pl.tt[idx, s, RET] = ret
    pl.dest[idx, s] = dest; pl.act[idx, s] = act; pl.mode[idx, s] = mode


def _libre(pl, idx, dep, ret):
    """Le creneau [ dep ; ret [ ne touche aucun tour deja pose."""
    ok = np.ones(len(idx), bool)
    for s in range(NS):
        a = pl.actif[idx, s]
        if not a.any(): continue
        ok &= ~(a & (dep < pl.tt[idx, s, RET].astype(np.int32)) & (ret > pl.tt[idx, s, DEP].astype(np.int32)))
    return ok


def _hors_couvre_feu(w, dep, ret):
    """Le couvre-feu du gouvernement ( heures [ debut ; fin [ ) interdit les sorties de loisir, de culte et de courses ;
    le travail passe ( Monde.deplacer ne le connaissait pas du tout )."""
    cf = w.gouv.lois.get("couvre_feu")
    ok = np.ones(len(dep), bool)
    if not cf: return ok
    d, f = int(cf[0]), int(cf[1])
    duree = ((f - d) % 24) * 60
    if duree == 0: return ok
    for j in (-1, 0, 1):
        a = (d * 60 - MINUTE_AUBE) % MINUTES_JOUR + j * MINUTES_JOUR
        ok &= ~((dep < a + duree) & (ret > a))
    return ok


def _tours_travail(a, w, g, jt, idx):
    """Le tour de travail ( ou d ecole ) du jour pour les habitants `idx` : ( ok, dep, arr, fin, ret, mode, hors_ile ).
    La presence couvre exactement les minutes ou Habitant.au_travail est vrai : la production du moteur compte les
    presents avec cette horloge. Un tour appartient au jour de son DEPART : l equipe de 6 h qui part avant 6 h est
    posee la veille et reprise le matin ( report )."""
    hor = g.hor[idx]; eq = g.equipe[idx]; d = g.decalage[idx]
    S = np.zeros(len(idx), np.int32); E = np.zeros(len(idx), np.int32); ouvert = np.zeros(len(idx), bool)
    continu = np.zeros(len(idx), bool)
    for code, nom in enumerate(HORAIRES, start=1):
        m = hor == code
        if not m.any(): continue
        if nom == "garde":
            S[m] = np.array(DEBUT_EQUIPE_H)[eq[m]] * 60 + d[m] - MINUTE_AUBE
            E[m] = S[m] + DUREE_EQUIPE_MIN
        else:
            ha, hb = C.HORAIRES[nom]
            S[m] = ha * 60 + d[m] - MINUTE_AUBE
            E[m] = hb * 60 + d[m] - MINUTE_AUBE + (MINUTES_JOUR if hb < ha else 0)
        ouvert[m] = jt.ouvert(nom)
        continu[m] = nom in CONTINUS
    T, mode, km, possible = _trajets(a, w, g.dom[idx], g.trav[idx])
    dep = S - T
    tot = continu & (dep < 0)                       # part avant 6 h : c est le tour du lendemain matin
    S[tot] += MINUTES_JOUR; E[tot] += MINUTES_JOUR; dep[tot] += MINUTES_JOUR
    dep = np.maximum(dep, 0)
    trop_jeune = ((g.role[idx] & ENFANT) > 0) & (g.age[idx] < POP.AGE_ECOLE)
    ok = ouvert & possible & ~trop_jeune
    return ok, dep, S, E, E + T, mode, ouvert & ~possible


def _report(pl, ancien, libre, act_miroir, exiger_dehors=True):
    """Les tours d hier qui debordent apres 6 h ( gardes de nuit ) continuent, si l habitant y est encore."""
    m = min(ancien.n, pl.n)
    if m == 0: return
    deborde = ancien.actif[:m] & (ancien.tt[:m, :, RET].astype(np.int32) > MINUTES_JOUR)
    qui = np.nonzero(deborde.any(axis=1))[0]
    if not len(qui): return
    s = deborde[qui].argmax(axis=1)
    ok = libre[qui]
    if exiger_dehors: ok &= ~np.isin(act_miroir[qui], (MAISON, HORS, HOPITAL, VOYAGE))
    qui, s = qui[ok], s[ok]
    pl.actif[qui, REPORT] = True
    pl.tt[qui, REPORT] = (ancien.tt[qui, s].astype(np.int32) - MINUTES_JOUR).astype(np.int16)
    pl.dest[qui, REPORT] = ancien.dest[qui, s]; pl.act[qui, REPORT] = ancien.act[qui, s]
    pl.mode[qui, REPORT] = ancien.mode[qui, s]; pl.coupe[qui, REPORT] = ancien.coupe[qui, s]


def _report_initial(p, a, pl, g, fen, libre):
    """Le premier matin, personne n a de plan d hier : on refait celui d une veille ordinaire pour les equipes de nuit."""
    veille = Plan(fen - 1, TypeDeJour(p.socle.calendrier, fen - 1), g.n)
    idx = np.nonzero(libre & (g.hor > 0) & (g.trav >= 0))[0]
    ok, dep, arr, fin, ret, mode, _ = _tours_travail(a, p.w, g, veille.jt, idx)
    ci = idx[ok]
    act = np.where((g.role[ci] & ENFANT) > 0, ECOLE, TRAVAIL)
    _poser(veille, ci, T_TRAVAIL, dep[ok], arr[ok], fin[ok], ret[ok], LIEU_TRAVAIL, act, mode[ok])
    _report(pl, veille, libre, None, exiger_dehors=False)


def _pas_dans(arr, fin):
    """Nombre de pas de la journee ( minutes 0, 10, ... 1430 ) dans [ arr ; fin [."""
    a = (np.clip(arr, 0, MINUTES_JOUR) + PAS_MIN - 1) // PAS_MIN
    b = (np.clip(fin, 0, MINUTES_JOUR) + PAS_MIN - 1) // PAS_MIN
    return np.maximum(0, b - a)


def _tour_simple(pl, w, idx, s, arrivee, duree, T, mode, dest, act):
    """Pose un tour ( arrivee, duree ) avec son trajet, s il ne touche aucun autre tour ni le couvre-feu."""
    dep = arrivee - T; fin = arrivee + duree; ret = fin + T
    ok = (dep >= 0) & (dep < MINUTES_JOUR) & _libre(pl, idx, dep, ret) & _hors_couvre_feu(w, dep, ret)
    _poser(pl, idx[ok], s, dep[ok], arrivee[ok], fin[ok], ret[ok], dest[ok] if np.ndim(dest) else dest, act,
           mode[ok])
    return int(ok.sum())


def _loisirs_et_culte(p, a, pl, g, jt, libre, Ti, mi, Tm, mm):
    w = p.w; n = g.n
    u = p.du_jour("agenda_sorties").random((n, 10))
    col = p.colonnes["habitant"]
    nb_culte = nb_loisir = 0
    if jt.culte:
        idx = np.nonzero(libre & (col["agenda_pratiquant"][:n] == 1) & (g.age >= POP.AGE_ECOLE))[0]
        t0, et, dmin, dd = OFFICE
        arr = (t0 - MINUTE_AUBE + u[idx, 0] * et).astype(np.int32)
        duree = (dmin + u[idx, 1] * dd).astype(np.int32)
        nb_culte = _tour_simple(pl, w, idx, T_CULTE, arr, duree, Ti[idx], mi[idx], DOMICILE, CULTE)
    if jt.repos:
        idx = np.nonzero(libre & (g.age >= POP.AGE_ECOLE) & (u[:, 2] < P_JOUR_REPOS))[0]
        (h1, h2), et, dmin, dd = JOUR_REPOS
        arr = (np.where(u[idx, 3] < 0.5, h1, h2) - MINUTE_AUBE + u[idx, 4] * et).astype(np.int32)
        duree = (dmin + u[idx, 5] * dd).astype(np.int32)
        nb_loisir += _tour_simple(pl, w, idx, T_LOISIR_JOUR, arr, duree, Ti[idx], mi[idx], DOMICILE, LOISIR)
    retraite = (g.role & RETRAITE) > 0
    # le cafe de l apres-midi pour les retraites, la sortie du soir pour les autres
    for qui, prob, (t0, et, dmin, dd) in ((retraite, P_CAFE_RETRAITE, CAFE),
                                          (~retraite, P_SOIR_VEILLE if jt.veille else P_SOIR_SEMAINE,
                                           SOIR_VEILLE if jt.veille else SOIR_SEMAINE)):
        idx = np.nonzero(libre & qui & (g.age >= AGE_SOIR) & (u[:, 6] < prob))[0]
        if not len(idx): continue
        arr = (t0 - MINUTE_AUBE + u[idx, 7] * et).astype(np.int32)
        duree = (dmin + u[idx, 8] * dd).astype(np.int32)
        ville = np.zeros(len(idx), bool)
        if jt.veille:
            age = g.age[idx]
            ville = (age >= JEUNES[0]) & (age < JEUNES[1]) & (u[idx, 9] < P_VILLE_JEUNES) & ~retraite[idx]
        T = np.where(ville, Tm[idx], Ti[idx]); mode = np.where(ville, mm[idx], mi[idx])
        dest = np.where(ville, MARCHE, DOMICILE).astype(np.int16)
        nb_loisir += _tour_simple(pl, w, idx, T_LOISIR_SOIR, arr, duree, T, mode, dest, LOISIR)
    return nb_culte, nb_loisir


def _decider(p, a, pl, g, ai, sympt, quar, indoc):
    """Chaque adulte decide, par le decideur du point `sortir` ( regle, appris, fige, hasard, temoin )."""
    w = p.w; dec = a.decideur
    vise = np.where(pl.actif[ai, T_TRAVAIL], g.trav[ai], g.dom[ai])
    rum = np.minimum(1.0, ECHELLE_RUMEUR * a.connus[vise] / np.maximum(1.0, a.frequentation[vise]))
    faim = np.minimum(1.0, g.faim[ai] / FAIM_PLEINE)
    M = len(w.menages)
    viv_m = np.bincount(g.menage[g.vivant & (g.menage >= 0)], minlength=M)
    prix = {mid: m.prix["nourriture"] * (1 + w.gouv.tva) for mid, m in w.marches.items()}
    caisse = w.table.menages.caisse[:M].copy()
    prix_n = np.full(len(w.carte.par_n), float(C.PRIX_MONDE["nourriture"]))
    for mid, v in prix.items(): prix_n[w.carte.lieux[mid].n] = v
    dm = w.table.menages.domicile[:M].astype(np.int64)
    pm = np.where(dm >= 0, prix_n[w._marche_du_lieu[np.maximum(dm, 0)]], float(C.PRIX_MONDE["nourriture"]))
    jours = caisse / np.maximum(1e-6, pm * C.NOURRITURE_PAR_JOUR * np.maximum(1, viv_m))
    cj = np.minimum(1.0, jours / JOURS_CAISSE_PLEINS)[g.menage[ai]]
    x = np.column_stack([sympt[ai], rum, quar[ai], faim, cj, pl.actif[ai, T_TRAVAIL]]).astype(float)
    if _decideur_simple(dec) and ((x >= 0.0) & (x <= 1.0)).all():
        # EN COLONNES ( 24/09 ) : la regle ( ou le temoin, qui ne tire rien ) appliquee a tous d un coup, puis chaque
        # choix pose dans son attente exactement comme Decideur.decider le ferait ( traits bornes : verifies ci-dessus ;
        # hors bornes, le chemin un par un leve l erreur du decideur )
        if dec.mode == "regle": out = np.where((x[:, 0] >= 0.5) | ((x[:, 2] >= 0.5) & ~indoc[ai]), 0, 1)
        else: out = np.ones(len(ai), np.int64)
        attentes = dec.attentes; Attente = D.Attente
        for i, r, act in zip(ai.tolist(), x.tolist(), out.tolist()):
            r.append(1.0)
            att = attentes.get(i)
            if att is None: att = attentes[i] = Attente()
            att.choix.append([r, act, 0, 0.0])
        dec.n_decisions += len(ai)
        e = getattr(dec, "enregistreur", None)
        if e is not None: e.decisions_lot(dec.point.nom, ai, np.column_stack([x, np.ones(len(ai))]), out)
        return out.astype(np.int8)
    out = [dec.decider(i, ContexteSortie(tuple(r), bool(d))) for i, r, d in zip(ai.tolist(), x.tolist(), indoc[ai].tolist())]
    return np.array(out, np.int8)


def _decideur_simple(dec):
    """Le decideur du point `sortir` en mode regle ou temoin, tel que le socle le fait : sa decision se calcule en
    colonnes ( la regle ne lit que les traits et l indocilite ; le temoin rend toujours `sortir` sans tirer )."""
    pt = POINT_SORTIR
    return (type(dec) is D.Decideur and dec.point is pt and dec.mode in ("regle", "temoin")
            and pt.observer is _observer_sortir and pt.regle is _regle_sortir and pt.temoin is _temoin_sortir
            and type(dec).observer is D.Decideur.observer and len(pt.traits) == 6)


def _courses(p, a, pl, g, jt, libre, Ti, mi, Tm, mm):
    """Un membre adulte de chaque menage qui sort fait les courses avant les achats de 19 h : de preference celui qui ne
    travaille pas ( le matin ), sinon celui qui rentre le plus tot, sinon celui qui travaille l apres-midi ou la nuit
    ( le matin ), sinon celui qui travaille AU marche de son domicile ( le marchand achete sur place, sans tour ). Au
    marche de la capitale si le menage en est proche ou si c est son jour de grand marche, sinon a l epicerie de son
    lieu. Le dimanche et les feries, tout est ferme. Rend ( au marche, a l epicerie, sur le lieu de travail, sans
    acheteur )."""
    if not jt.marche: return 0, 0, 0, 0
    n = g.n
    u = p.du_jour("agenda_courses").random((n, 2))
    idx = np.nonzero(libre & ~pl.rester & (g.age >= POP.AGE_MAJEUR) & (g.menage >= 0))[0]
    habites = np.unique(g.menage[libre & (g.menage >= 0)])
    if not len(idx): return 0, 0, 0, len(habites)
    mg = g.menage[idx]
    jm = p.col("menage", "agenda_jour_marche")
    au_marche = (a.km_marche[g.dom[idx]] <= MARCHE_PROCHE_KM) | (jm[mg] == jt.semaine)
    T = np.where(au_marche, Tm[idx], Ti[idx]); mode = np.where(au_marche, mm[idx], mi[idx])
    report = pl.actif[idx, REPORT] & (pl.act[idx, REPORT] == TRAVAIL)
    travaille = pl.actif[idx, T_TRAVAIL] | report
    t0, et = COURSES_MATIN
    depA = (t0 - MINUTE_AUBE + u[idx, 0] * et).astype(np.int32)
    finA = depA + T + DUREE_COURSES_MIN
    okA = (finA <= FIN_COURSES) & _libre(pl, idx, depA, finA + T) & _hors_couvre_feu(p.w, depA, finA + T)
    # apres le travail : la garde de nuit qui finit le matin ( report ), ou le travail du jour
    depB = np.zeros(len(idx), np.int32); okB = np.zeros(len(idx), bool)
    for s, qui in ((REPORT, report), (T_TRAVAIL, pl.actif[idx, T_TRAVAIL])):
        d = pl.tt[idx, s, RET].astype(np.int32) + (u[idx, 1] * COURSES_APRES_MIN).astype(np.int32)
        f = d + T + DUREE_COURSES_MIN
        ok = qui & ~okB & (d >= 0) & (f <= FIN_COURSES) & _libre(pl, idx, d, f + T) & _hors_couvre_feu(p.w, d, f + T)
        depB[ok] = d[ok]; okB |= ok
    sur_place = (travaille & (a.marche[g.dom[idx]] == g.trav[idx])
                 & (pl.tt[idx, T_TRAVAIL, ARR].astype(np.int32) < FIN_COURSES))
    rang = np.where(okA & ~travaille, 0, np.where(okB, 1, np.where(okA, 2, np.where(sur_place, 3, 9))))
    dep = np.where(rang == 1, depB, depA)
    ordre = np.lexsort((idx, dep, rang, mg))
    premier = np.ones(len(ordre), bool)
    premier[1:] = mg[ordre][1:] != mg[ordre][:-1]
    choisi = ordre[premier & (rang[ordre] < 9)]
    c = choisi[rang[choisi] < 3]
    arr = dep[c] + T[c]
    dest = np.where(au_marche[c], MARCHE, DOMICILE).astype(np.int16)
    _poser(pl, idx[c], T_COURSES, dep[c], arr, arr + DUREE_COURSES_MIN, arr + DUREE_COURSES_MIN + T[c], dest,
           COURSES, mode[c])
    n_sur_place = len(choisi) - len(c)
    return int(au_marche[c].sum()), int((~au_marche[c]).sum()), n_sur_place, len(habites) - len(choisi)


def _reveils(pl, ids, apres):
    """( ids, pas ) ou l etat des habitants `ids` peut changer, strictement apres la minute `apres` : les instants de
    leurs tours, arrondis au pas suivant. Tries par pas."""
    qui, pas = [], []
    for s in range(NS):
        a = pl.actif[ids, s]
        for j in range(4):
            t = pl.tt[ids, s, j].astype(np.int32)
            m = a & (t > apres) & (t < MINUTES_JOUR)
            qui.append(ids[m]); pas.append((t[m] + PAS_MIN - 1) // PAS_MIN)
    qui = np.concatenate(qui).astype(np.int64); pas = np.concatenate(pas).astype(np.int64)
    cle = np.unique(pas * (1 << 32) + qui)
    return (cle & 0xFFFFFFFF).astype(np.int32), (cle >> 32).astype(np.int32)


def _trafic(a, w, pl):
    """Qui roule ou marche a chaque pas ( par mode ), qui part a chaque pas, et les km faits en vehicule."""
    diff = np.zeros((2, PAS_JOUR + 1), np.int64)
    departs = np.zeros(PAS_JOUR + 1, np.int64)
    km_veh = 0.0
    for s in range(NS):
        act = pl.actif[:, s]
        if not act.any(): continue
        T = pl.tt[:, s].astype(np.int32)
        for t0, t1 in ((DEP, ARR), (FIN, RET)):
            j0 = np.clip((T[:, t0] + PAS_MIN - 1) // PAS_MIN, 0, PAS_JOUR)
            j1 = np.clip((T[:, t1] + PAS_MIN - 1) // PAS_MIN, 0, PAS_JOUR)
            m = act & (j1 > j0)
            np.add.at(diff, (pl.mode[m, s], j0[m]), 1); np.add.at(diff, (pl.mode[m, s], j1[m]), -1)
            d = act & (T[:, t0] >= 0) & (T[:, t0] < MINUTES_JOUR)
            np.add.at(departs, (T[d, t0] + PAS_MIN - 1) // PAS_MIN, 1)
        v = np.nonzero(act & (pl.mode[:, s] == EN_VEHICULE) & (T[:, DEP] >= 0))[0]
        if len(v):
            km_veh += 2.0 * float(_km(a, w, pl.dom[v].astype(np.int32),
                                      _dest_lieu(a, pl.dom[v].astype(np.int32), pl.trav[v].astype(np.int32),
                                                 pl.dest[v, s].astype(np.int32))).sum())
    pl.trafic = np.cumsum(diff, axis=1)[:, :PAS_JOUR].astype(np.int32)
    pl.departs = departs[:PAS_JOUR].astype(np.int32)
    return km_veh


def _noter_sorties(p, a, g, fen):
    """6 h : la journee d hier est finie. Chaque adulte qui a des choix en attente recoit la consequence du jour pour son
    menage ; les choix murs ( 7 jours ) rendent leur note."""
    dec = a.decideur
    cles = [c for c, att in dec.attentes.items() if att.choix]
    if cles:
        n = g.n; col = p.colonnes["habitant"]; M = len(p.w.menages)
        v = g.vivant & (g.menage >= 0)
        mg = g.menage[v]
        vivants = np.bincount(mg, minlength=M)
        sains = np.bincount(g.menage[v & (g.etat != ETAT_E) & (g.etat != ETAT_I)], minlength=M)
        fait = np.bincount(mg, weights=col["agenda_pas_travail"][:n][v], minlength=M)
        prevu = np.bincount(mg, weights=col["agenda_pas_prevus"][:n][v], minlength=M)
        nourri = p.w.nourri_menage
        cl = np.array(cles)
        if cl.dtype.kind in "iu" and cl.min() >= 0:
            # EN COLONNES ( 24/09 ) : la note de chaque menage calculee d un coup ( memes operations, meme ordre ;
            # des np.float64 comme les lectures une a une ), puis notee cle par cle dans l ordre des attentes
            cl = cl.astype(np.int64)
            vi = np.nonzero(cl < n)[0]
            vi = vi[v[cl[vi]]]
            mv = g.menage[cl[vi]].astype(np.int64)
            fm, pm_ = fait[mv], prevu[mv]
            trav = np.where(pm_ > 0, np.minimum(1.0, fm / np.where(pm_ > 0, pm_, 1.0)), 1.0)
            nou = _nourris(nourri, mv)
            rv = (sains[mv] / np.maximum(1, vivants[mv]) + trav + nou) / 3.0
            rs = [0.0] * len(cles)
            for j, r in zip(vi.tolist(), rv): rs[j] = r
            if type(dec) is D.Decideur and type(dec).noter is D.Decideur.noter \
                    and D.Attente.jour is _JOUR_ATTENTE:
                _noter_tous(dec, cles, rs, fen - 1)
            else:
                for c, r in zip(cles, rs): dec.noter(c, r, fen - 1)
        else:
            for c in cles:
                if c >= n or not v[c]: r = 0.0
                else:
                    m = int(g.menage[c])
                    trav = min(1.0, fait[m] / prevu[m]) if prevu[m] > 0 else 1.0
                    r = (sains[m] / max(1, vivants[m]) + trav + (1.0 if nourri.get(m, True) else 0.0)) / 3.0
                dec.noter(c, r, fen - 1)
    for c in [c for c, att in dec.attentes.items() if not att.choix]: del dec.attentes[c]


_JOUR_ATTENTE = D.Attente.jour


def _nourris(nourri, mg):
    """`1.0 if nourri.get( m, True ) else 0.0` pour chaque menage de `mg`, lu dans le tableau de `Monde.nourri_menage`
    ( ParMenage : hors du tableau, la valeur par defaut ) ; un autre objet est lu menage par menage."""
    from .. import monde as MW
    if type(nourri) is MW.ParMenage and isinstance(nourri.v, np.ndarray):
        v = nourri.v
        dans = (mg >= 0) & (mg < len(v))
        nou = np.ones(len(mg))
        nou[dans] = np.where(v[mg[dans]].astype(bool), 1.0, 0.0)
        return nou
    return np.array([1.0 if nourri.get(m, True) else 0.0 for m in mg.tolist()])


def _noter_tous(dec, cles, rs, jour):
    """`Decideur.noter( c, r, jour )` pour chaque cle, dans l ordre, sans ses deux appels par cle ( Decideur.noter puis
    Attente.jour, recopies ici a l identique : memes operations, meme ordre ). 24/09 : la moitie du plan du matin."""
    horizon = dec.point.horizon_j; apprend = dec.apprend
    attentes = dec.attentes; stats = dec.stats; ech = dec.echantillon
    for c, r in zip(cles, rs):
        att = attentes.get(c)
        if att is None: continue
        if type(att) is not D.Attente:
            dec.noter(c, r, jour); continue
        murs, restent = [], []
        for e in att.choix:
            e[2] += 1; e[3] += r
            (murs if e[2] >= horizon else restent).append(e)
        att.choix = restent
        for x, a, note in [(x, a, s / horizon) for x, a, j, s in murs]:
            if apprend: dec.doctrine.apprendre(x, a, note)
            st = stats.get((jour, a))
            if st is None: stats[(jour, a)] = [1, note, note * note]
            else: st[0] += 1; st[1] += note; st[2] += note * note
            ech.append((jour, a, note))


def _planifier(p, a, fen, k):
    """6 h ( ou le premier pas ) : le plan de la journee du monde, puis chacun est pose ou le plan le met."""
    w = p.w
    jt = TypeDeJour(p.socle.calendrier, fen)
    g = _rassembler(p, a)
    n = g.n
    col = p.colonnes["habitant"]
    col.assurer(n); p.colonnes["menage"].assurer(len(w.menages))
    _tirer_traits(p, g)
    _noter_sorties(p, a, g, fen)
    ancien = a.plan
    pl = Plan(fen, jt, n)
    pl.dom = g.dom.astype(np.int16); pl.trav = g.trav.astype(np.int16)
    pl.hors = ~g.vivant | g.hors
    pl.hopital = ~pl.hors & (g.etat == ETAT_I) & (g.gravite > GRAVITE_HOPITAL)
    libre = ~pl.hors & ~pl.hopital
    pl.public = bytes(((g.role & PUBLIC) > 0).astype(np.uint8))
    # 1. le report de la nuit ( equipes de 22 h et de 6 h )
    if ancien is None: _report_initial(p, a, pl, g, fen, libre)
    else: _report(pl, ancien, libre, col["agenda_activite"])
    # 2. travail et ecole
    idx = np.nonzero(libre & (g.hor > 0) & (g.trav >= 0))[0]
    ok, dep, arr, fin, ret, mode, hors_ile = _tours_travail(a, w, g, jt, idx)
    ok &= _libre(pl, idx, dep, ret)
    ci = idx[ok]
    _poser(pl, ci, T_TRAVAIL, dep[ok], arr[ok], fin[ok], ret[ok], LIEU_TRAVAIL,
           np.where((g.role[ci] & ENFANT) > 0, ECOLE, TRAVAIL), mode[ok])
    pl.cand[ci] = np.column_stack([dep[ok], arr[ok], fin[ok], ret[ok]]); pl.cand_mode[ci] = mode[ok]; pl.cand_ok[ci] = True
    prevus = np.zeros(n, np.int64)
    for s in (REPORT, T_TRAVAIL):
        m = pl.actif[:, s] & (pl.act[:, s] == TRAVAIL)
        prevus[m] += _pas_dans(pl.tt[m, s, ARR].astype(np.int32), pl.tt[m, s, FIN].astype(np.int32))
    col["agenda_pas_prevus"][:n] = prevus
    col["agenda_pas_travail"][:n] = 0
    # 3. culte et loisirs ( candidats )
    Ti, mi, _, _ = _trajets(a, w, g.dom, g.dom)
    Tm, mm, _, _ = _trajets(a, w, g.dom, a.marche[g.dom])
    nb_culte, nb_loisir = _loisirs_et_culte(p, a, pl, g, jt, libre, Ti, mi, Tm, mm)
    # 4. rester ou sortir
    ql = np.zeros(a.L, bool)
    for lid in w.gouv.lois.get("quarantaine", ()):
        if lid in a.index_lieu: ql[a.index_lieu[lid]] = True
    sympt = g.etat == ETAT_I
    quar = ql[g.dom] | ((g.trav >= 0) & ql[np.maximum(g.trav, 0)])
    indoc = col["agenda_indocile"][:n] == 1
    rester = libre & (sympt | (quar & ~indoc))
    a.epidemie = bool((g.vivant & ((g.etat == ETAT_E) | (g.etat == ETAT_I))).any())
    n_dec = 0
    if a.epidemie:
        ai = np.nonzero(libre & (g.age >= POP.AGE_MAJEUR))[0]
        choix = _decider(p, a, pl, g, ai, sympt, quar, indoc)
        n_dec = len(ai)
        rester[ai] = choix == 0
        M = len(w.menages)
        mg_a = g.menage[ai]
        tous = np.bincount(mg_a[mg_a >= 0], minlength=M)
        restent = np.bincount(mg_a[(mg_a >= 0) & (choix == 0)], minlength=M)
        mineur = libre & (g.age < POP.AGE_MAJEUR) & (g.menage >= 0)
        confine = (tous > 0) & (restent == tous)
        rester[mineur] |= confine[g.menage[mineur]]
    pl.rester = rester
    for s in (T_CULTE, T_TRAVAIL, T_LOISIR_JOUR, T_LOISIR_SOIR): pl.actif[rester, s] = False
    for i in np.nonzero(rester & pl.actif[:, REPORT])[0].tolist():   # malade au matin de sa garde de nuit : il rentre
        _couper(pl, i, REPORT, PAS_MIN * k)
    # la faim empeche de travailler ; les agents travailleurs, s ils sont la, decident du travail a la place
    gt = w.agents.get("travailleurs")
    pl.epuise = g.faim > C.ABSENCE_FAIM
    if gt:
        pl.gt = libre & (g.trav >= 0) & ((g.role & (ENFANT | RETRAITE)) == 0)
        qui = np.nonzero(pl.gt)[0]
        va = np.fromiter((gt.choix.get(i, 0) == 0 for i in qui.tolist()), bool, len(qui))
        pl.actif[qui, T_TRAVAIL] = pl.cand_ok[qui] & va
    pl.actif[pl.epuise & ~pl.gt, T_TRAVAIL] = False
    # 5. les courses
    au_marche, au_village, sur_place, sans = _courses(p, a, pl, g, jt, libre, Ti, mi, Tm, mm)
    # 6. les reveils du jour, et chacun a sa place maintenant
    tous_ids = np.arange(n, dtype=np.int32)
    ev_id, ev_pas = _reveils(pl, tous_ids, PAS_MIN * k)
    pl.ev_id = ev_id
    pl.ev_off = np.searchsorted(ev_pas, np.arange(PAS_JOUR + 1)).astype(np.int64)
    a.plan = pl
    a.publics = set()
    _appliquer(p, a, pl, tous_ids, PAS_MIN * k)
    # 7. la rumeur de demain : les malades connus aujourd hui, par lieu ou ils vivent et ou ils travaillent
    v = g.vivant
    freq = np.bincount(g.dom[v], minlength=a.L) + np.bincount(g.trav[v & (g.trav >= 0)], minlength=a.L)
    malade = v & (g.etat == ETAT_I)
    connu = malade & (p.du_jour("agenda_rumeur").random(n) < P_RUMEUR)
    a.connus = (np.bincount(g.dom[connu], minlength=a.L)
                + np.bincount(g.trav[connu & (g.trav >= 0)], minlength=a.L)).astype(float)
    a.frequentation = freq.astype(float)
    a.presence_hier, a.presence = a.presence, np.zeros_like(a.presence)
    km_veh = _trafic(a, w, pl)
    pl.stats = {"decisions": n_dec, "rester": int((rester & libre & (g.age >= POP.AGE_MAJEUR)).sum()),
                "hopital": int(pl.hopital.sum()), "hors_ile": int(hors_ile.sum()), "culte": nb_culte,
                "loisir": nb_loisir, "courses_marche": au_marche, "courses_village": au_village,
                "courses_sur_place": sur_place, "sans_acheteur": sans, "km_vehicule": km_veh, "reveils": len(ev_id)}
    for t, v_ in (("agenda_decisions", n_dec), ("agenda_rester", pl.stats["rester"]), ("agenda_sans_acheteur", sans),
                  ("agenda_hors_ile", pl.stats["hors_ile"]), ("agenda_culte", nb_culte), ("agenda_loisir", nb_loisir),
                  ("agenda_km_vehicule", km_veh)):
        p.compter(t, float(v_))


def _couper(pl, i, s, t):
    """Interrompt le tour `s` de l habitant `i` a la minute `t` : il rentre maintenant ( ou ne part pas )."""
    dep, arr, fin, ret = (int(x) for x in pl.tt[i, s])
    if dep >= t:
        pl.actif[i, s] = False
    elif t < fin:
        trajet_retour = ret - fin
        if t < arr: trajet_retour = t - dep         # il fait demi-tour en route
        pl.tt[i, s] = (dep, min(arr, t), t, t + trajet_retour)
        pl.coupe[i, s] = True


def _revision_du_soir(p, a, pl, k):
    """20 h 10 : le repas de 20 h a change la faim. Monde.deplacer la relisait a chaque pas ; ici, seuls ceux dont le
    travail est encore a venir ou en cours sont relus, et leur plan corrige ( equipes de 14 h et de 22 h )."""
    t = PAS_MIN * k
    idx = np.nonzero(pl.cand_ok & ~pl.gt & ~pl.rester & ~pl.hors & ~pl.hopital
                     & (pl.cand[:, RET].astype(np.int32) > t))[0]
    if not len(idx): return
    H = p.w.habitants
    epuise = p.w.table.faim[idx] > C.ABSENCE_FAIM
    change = idx[epuise != pl.epuise[idx]]
    if not len(change): return
    for i in change.tolist():
        if not pl.epuise[i]:
            if pl.actif[i, T_TRAVAIL]: _couper(pl, i, T_TRAVAIL, t)
        elif int(pl.cand[i, DEP]) > t and _libre(pl, np.array([i]), pl.cand[i:i + 1, DEP].astype(np.int32),
                                                 pl.cand[i:i + 1, RET].astype(np.int32))[0]:
            pl.actif[i, T_TRAVAIL] = True; pl.tt[i, T_TRAVAIL] = pl.cand[i]; pl.mode[i, T_TRAVAIL] = pl.cand_mode[i]
        pl.epuise[i] = not pl.epuise[i]
    _relire(pl, change, k)
    p.compter("agenda_revision", float(len(change)))


def _relire(pl, ids, k):
    """Les habitants `ids` ont un plan corrige : ils sont relus a ce pas et a chacun de leurs nouveaux instants."""
    ids = np.asarray(ids, np.int32)
    pl.extra.setdefault(k, []).extend(ids.tolist())
    q, s = _reveils(pl, ids, PAS_MIN * k)
    for i, j in zip(q.tolist(), s.tolist()): pl.extra.setdefault(j, []).append(i)


# ================================================================== installation
def installer(p):
    w = p.w
    if C.MINUTES_PAR_PAS != 10 or C.DATE_DEPART[3] * 60 + C.DATE_DEPART[4] != MINUTE_AUBE:
        raise RuntimeError("agenda : la journee du plan est ancree sur l aube de 6 h et des pas de 10 minutes")
    ch, cm = p.colonnes["habitant"], p.colonnes["menage"]
    for nom, dtype, defaut in (("agenda_lieu", np.int32, -1), ("agenda_activite", np.int8, HORS),
                               ("agenda_pas_travail", np.int16, 0), ("agenda_pas_prevus", np.int16, 0),
                               ("agenda_indocile", np.int8, -1), ("agenda_pratiquant", np.int8, -1)):
        ch.ajouter(nom, dtype, defaut)
    cm.ajouter("agenda_jour_marche", np.int8, -1)
    ch.assurer(len(w.habitants)); cm.assurer(len(w.menages))
    J = p.socle.journal
    for t in ("agenda_decisions", "agenda_rester", "agenda_sans_acheteur", "agenda_hors_ile", "agenda_culte",
              "agenda_loisir", "agenda_km_vehicule", "agenda_revision"):
        J.declarer(t, "agenda", "compte")
    a = Agenda(w, p.decideur(POINT_SORTIR))
    w.deplacer = RemplaceDeplacer(p)
    return a


# ================================================================== ce que le domaine donne aux autres
def planning(p, hid):
    """Le planning du jour de `hid`, de 6 h au lendemain 6 h : [ ( debut, fin, activite, lieu ) ], heures du monde
    ( 25,5 = 1 h 30 le lendemain ). Le lieu est relu sur l habitant ( domicile, travail, marche de son domicile )."""
    a = p.domaine("agenda"); pl = a.plan; h = p.w.habitants[hid]
    if pl is None or hid >= pl.n or pl.hors[hid]:
        return [(6.0, 30.0, "hors", getattr(h.lieu, "id", None))]
    if pl.hopital[hid]: return [(6.0, 30.0, "hopital", h.domicile.marche.id)]
    segs, t = [], 0
    ordre = sorted((int(pl.tt[hid, s, DEP]), s) for s in range(NS) if pl.actif[hid, s])
    for dep, s in ordre:
        d0, a0, f0, r0 = (int(x) for x in pl.tt[hid, s])
        lieu = _resoudre(a, h, int(pl.dest[hid, s]))
        if dep > t: segs.append((t, dep, "maison", h.domicile.id))
        for x, y, nom, l in ((d0, a0, "trajet", lieu.id), (a0, f0, ACTIVITES[pl.act[hid, s]], lieu.id),
                             (f0, r0, "trajet", h.domicile.id)):
            if y > x: segs.append((x, y, nom, l))
        t = max(t, r0)
    if t < MINUTES_JOUR: segs.append((t, MINUTES_JOUR, "maison", h.domicile.id))
    return [(round((MINUTE_AUBE + x) / 60, 3), round((MINUTE_AUBE + y) / 60, 3), nom, l) for x, y, nom, l in segs]


def position(p, hid, minute=None):
    """Ou le plan met `hid` a la minute `minute` depuis 6 h ( par defaut : maintenant ). En trajet, la position est
    interpolee en ligne droite entre le lieu de depart et celui d arrivee ; la bulle y pose le corps."""
    a = p.domaine("agenda"); pl = a.plan; h = p.w.habitants[hid]
    t = PAS_MIN * a.k if minute is None else int(minute)
    if pl is None or hid >= pl.n or pl.hors[hid] or not h.vivant or h.poste == "voyage" or h.lieu is None:
        l = h.lieu
        return {"lieu": getattr(l, "id", None), "activite": h.poste, "x": l.pos[0] if l else None,
                "y": l.pos[1] if l else None, "ile": getattr(l, "ile", None)}
    act, dest = _etat(pl, np.array([hid]), t)
    ac, de = int(act[0]), int(dest[0])
    l = _resoudre(a, h, de) if ac != HOPITAL else h.domicile.marche
    r = {"lieu": l.id, "activite": ACTIVITES[ac], "x": float(l.pos[0]), "y": float(l.pos[1]), "ile": l.ile}
    if ac == TRAJET:
        for s in range(NS):
            if not pl.actif[hid, s]: continue
            d0, a0, f0, r0 = (int(x) for x in pl.tt[hid, s])
            loin = _resoudre(a, h, int(pl.dest[hid, s]))
            if d0 <= t < a0: o, v, t0, t1 = h.domicile, loin, d0, a0
            elif f0 <= t < r0: o, v, t0, t1 = loin, h.domicile, f0, r0
            else: continue
            f = (t - t0) / max(1, t1 - t0)
            r.update(x=float(o.pos[0] + f * (v.pos[0] - o.pos[0])), y=float(o.pos[1] + f * (v.pos[1] - o.pos[1])),
                     origine=o.id, fraction=round(f, 3), mode=MODES[int(pl.mode[hid, s])])
            break
    return r


def qui_est_la(p, lieu_id, activite=None):
    """Les habitants que le miroir met dans `lieu_id` ( et dans cette activite ) : la bulle d incarnation."""
    a = p.domaine("agenda"); n = a.plan.n if a.plan is not None else 0
    col = p.colonnes["habitant"]
    m = col["agenda_lieu"][:n] == a.index_lieu[lieu_id]
    if activite is not None: m &= col["agenda_activite"][:n] == ACTIVITES.index(activite)
    return np.nonzero(m)[0].tolist()


def contacts_par_lieu(p, heure=None, hier=False):
    """Les presences a l heure pleine ( quand passe la contagion ), par lieu et par cadre : { lieu : { activite : n } }.
    `heure` en heure du monde ( 6 a 29 ; par defaut la derniere heure pleine ). Ce que la medecine ( domaine 16 ) lit
    pour des contacts plus fins que le lieu : la maison, le travail, l ecole, le marche, le cafe, l eglise."""
    a = p.domaine("agenda")
    tab = a.presence_hier if hier else a.presence
    if heure is None: j = (PAS_MIN * a.k) // 60
    else: j = int(heure) - MINUTE_AUBE // 60
    if not 0 <= j < 24: raise ValueError(f"heure {heure} hors de la journee du monde ( 6 a 29 )")
    v = tab[j].reshape(a.L, NA)
    return {a.lieux[l].id: {ACTIVITES[c]: int(v[l, c]) for c in np.nonzero(v[l])[0]} for l in np.nonzero(v.sum(1))[0]}


def lieux_de_loisir(p):
    """Les cadres de la vie quotidienne par lieu habite : chacun a son cafe, sa place, son eglise, son epicerie ; les
    capitales ont en plus le marche et les sorties en ville des jeunes."""
    w = p.w
    out = {}
    for l in w.carte.habitables():
        out[l.id] = ("cafe", "place", "eglise", "epicerie") + (("marche", "sortie_en_ville") if l.type == "capitale" else ())
    return out


def trafic(p):
    """Le trafic du jour selon le plan : personnes en trajet a chaque pas ( a pied, en vehicule ), departs par pas."""
    pl = p.domaine("agenda").plan
    return {"marche": pl.trafic[A_PIED].tolist(), "vehicule": pl.trafic[EN_VEHICULE].tolist(),
            "departs": pl.departs.tolist(), "km_vehicule": pl.stats.get("km_vehicule", 0.0)}


def tours_du_jour(p):
    """{ nom du tour : habitants qui l ont aujourd hui }."""
    pl = p.domaine("agenda").plan
    return {nom: np.nonzero(pl.actif[:, s])[0].tolist() for s, nom in enumerate(TOURS)}


def replanifier(p, h, rentrer=False):
    """Un autre domaine a change la situation de `h` en cours de journee ( hospitalise, gueri, demenage ) : l agenda la
    relit maintenant. `rentrer` : ses sorties en cours ou a venir sont annulees, il rentre chez lui."""
    a = p.domaine("agenda"); pl = a.plan
    if pl is None or h.id >= pl.n: return
    i, k = h.id, a.k
    pl.hors[i] = not h.vivant or h.poste == "voyage" or i in p.w.sejours
    pl.hopital[i] = not pl.hors[i] and h.etat == "I" and h.gravite > GRAVITE_HOPITAL
    if rentrer:
        for s in range(NS):
            if pl.actif[i, s]: _couper(pl, i, s, PAS_MIN * k)
    _appliquer(p, a, pl, np.array([i], np.int32), PAS_MIN * k)
    q, s = _reveils(pl, np.array([i], np.int32), PAS_MIN * k)
    for j in s.tolist(): pl.extra.setdefault(j, []).append(i)


# ================================================================== controles ( pour les portes )
def incoherences(p):
    """Les habitants qui ne sont pas la ou le plan les met a ce pas ( `hors_plan` ), ou dans un lieu qu aucune de leurs
    activites n explique - ni leur domicile, ni leur travail, ni le marche de leur domicile ( `lieu_impossible` )."""
    a = p.domaine("agenda"); pl = a.plan
    if pl is None: return []
    H = p.w.habitants; sej = p.w.sejours
    ids = np.nonzero(~pl.hors)[0].astype(np.int32)
    act, dest = _etat(pl, ids, PAS_MIN * a.k)
    out = []
    for i, ac, de in zip(ids.tolist(), act.tolist(), dest.tolist()):
        h = H[i]
        if not h.vivant or h.poste == "voyage" or i in sej: continue
        attendu = _resoudre(a, h, de)
        if ac in (TRAVAIL, ECOLE) and attendu is None: attendu, ac = h.domicile, MAISON
        if h.lieu is None or not (h.lieu is h.domicile or h.lieu is h.domicile.marche or h.lieu is h.travail):
            out.append(("lieu_impossible", i))
        if h.lieu is not attendu or h.poste != POSTES[ac]: out.append(("hors_plan", i))
    return out


def ecarts_miroir(p):
    """Les habitants vivants et places dont le miroir ( colonnes agenda_lieu, agenda_activite ) ne dit pas ou ils sont."""
    a = p.domaine("agenda"); pl = a.plan
    if pl is None: return []
    col = p.colonnes["habitant"]; H = p.w.habitants; sej = p.w.sejours
    lieu, act = col["agenda_lieu"], col["agenda_activite"]
    out = []
    for i in range(pl.n):
        h = H[i]
        if not h.vivant or h.poste == "voyage" or i in sej or h.lieu is None: continue
        if lieu[i] != a.index_lieu[h.lieu.id] or act[i] < 0 or POSTES[act[i]] != h.poste: out.append(i)
    return out


def trajets_du_jour(p):
    """Chaque trajet du plan : ( habitant, tour, aller ou retour, km, minutes, mode, interrompu )."""
    a = p.domaine("agenda"); pl = a.plan; w = p.w
    out = []
    for s in range(NS):
        qui = np.nonzero(pl.actif[:, s])[0]
        if not len(qui): continue
        dom = pl.dom[qui].astype(np.int32)
        vers = _dest_lieu(a, dom, pl.trav[qui].astype(np.int32), pl.dest[qui, s].astype(np.int32))
        km = _km(a, w, dom, vers)
        T = pl.tt[qui, s].astype(np.int32)
        for j, (t0, t1) in enumerate(((DEP, ARR), (FIN, RET))):
            for i, k_, mn, md, c in zip(qui.tolist(), km.tolist(), (T[:, t1] - T[:, t0]).tolist(),
                                         pl.mode[qui, s].tolist(), pl.coupe[qui, s].tolist()):
                out.append((i, TOURS[s], ("aller", "retour")[j], k_, mn, MODES[md], c))
    return out


def trajets_incoherents(p, trajets=None):
    """Les trajets dont la duree ne s explique pas par la distance et le mode : vitesse de porte a porte hors bornes
    ( a pied 2,5 a 7 km/h, en vehicule 8 a 70 km/h ), marche de plus de 3 km, trajet de plus de 3 h."""
    out = []
    for i, tour, sens, km, mn, mode, coupe in (trajets_du_jour(p) if trajets is None else trajets):
        if coupe: continue
        lo, hi = BORNES_VITESSE[MODES.index(mode)]
        v = km / (mn / 60.0) if mn > 0 else float("inf")
        if not lo <= v <= hi or mn > DUREE_MAX_TRAJET_MIN or (mode == "marche" and km > PIED_MAX_KM):
            out.append((i, tour, sens, round(km, 2), mn, mode))
    return out
