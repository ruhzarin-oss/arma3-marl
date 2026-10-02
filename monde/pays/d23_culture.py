"""DOMAINE 23 - CULTURE, RELIGION, LOISIRS, MORAL COLLECTIF.

FICHE
1. Classes. Paroisse ( une paroisse orthodoxe par lieu habite, et par ile une communaute par confession minoritaire
   dans sa capitale : dons, services religieux, fete patronale et son panigyri, entraide ; famille `paroisses`,
   secteur S.15 ), Etablissement ( kafeneio et taverne dans chaque lieu habite, cinema et theatre dans les capitales :
   une affaire familiale, son menage proprietaire, sa TVA, ses fournisseurs ; famille `etablissements_loisir`, S.11 ),
   Association ( club sportif et culturel des villes et des capitales : cotisations, entraineur, entretien ; famille
   `associations_loisir`, S.15 ), ContexteLoisirs, Culture ( l etat du domaine ). Colonnes par habitant :
   cul_confession, cul_base ( temperament ), cul_lent ( la part lente du moral : les causes durables, lissees ),
   cul_deuil et cul_fete ( les chocs, qui s eteignent ), cul_moral ( = base + lent + deuil + fete, borne a [0 ; 1] ),
   cul_sorties7 ( les soirs de la semaine ou il a vu du monde, en bits ), cul_deuil_vu ( un deces deja pleure ),
   cul_club ( son club, -1 ). Par menage : cul_choix ( la decision de la semaine ), cul_deuil_j, cul_depense ( cumul
   des sorties payees ), cul_dons ( cumul des dons ). Zero objet par habitant : 23 octets par habitant, 25 par menage.
2. Invariants et ce que le domaine detient. ARGENT : les caisses des paroisses, des etablissements et des clubs, par
   le grand livre seulement ( rapprochement nul des trois familles ). Un menage ne paie une sortie qu au-dela d une
   reserve de jours de nourriture ( 7 jours ; 1 jour s il a choisi la fete : c est un choix, et il peut le payer de sa
   faim ) ; un don au-dela de 3 jours. La TVA collectee est exactement taux / ( 1 + taux ) du prix paye et reversee
   chaque soir. Aucun bien du catalogue : ce que consomment cafes, tavernes et panigyria est achete aux marches en
   argent ( consommation intermediaire ), sans toucher aux stocks de nourriture qui font la faim du pays.
   MORAL : pour chaque vivant, cul_moral = borne( base + lent + deuil + fete ) a l identique ( `anomalies` : un moral
   ecrit hors de ses causes se voit ) ; le moral collectif d un lieu est la moyenne exacte de ses residents.
   REGLE 3 : le moral lit les CROYANCES du domaine 22 ( `climat` ), jamais les faits : une catastrophe que personne
   ne sait ne pese rien, une rumeur fausse que le village croit pese.
3. Decision `loisirs` ( chaque menage, une fois par semaine, son jour : numero modulo 7 ) : rester ( pas de sortie de
   loisir : ni cafe ni fete ; l eglise reste ), sortir ( les sorties que l agenda lui donne, payees ), fete ( en plus,
   le repas de famille a la taverne les veilles de repos, paye jusqu a un jour de nourriture pres ), economiser ( les
   memes sorties - la volta, la place, le banc du kafeneio - sans rien payer ni donner ). Traits ( ce que le menage
   sait de lui-meme et du calendrier ) : jours de nourriture que paie sa caisse, jours de faim de la semaine, son moral,
   son revenu, une fete proche ( panigyri de son village, grande fete ), son deuil, ce qui se dit de mauvais dans son
   lieu. Note ( horizon 7 jours : la semaine du choix ) : chaque jour, pour CE menage, ( moral moyen de ses membres +
   a-t-il mange ) / 2. Regle : deuil de moins de 40 jours -> rester ( la coutume grecque ) ; faim dans la semaine ou
   moins de 10 jours de caisse -> economiser ; fete proche et 30 jours de caisse -> fete ; sinon sortir. Temoin :
   toujours rester.
4. Evenements. Individuels : panigyri, fete_religieuse. Comptes : sortie_payee, don_religieux, service_religieux,
   aide_paroissiale, cotisation_club, decision_loisirs, deuil.
5. Liens. Population ( 1 ) : ages, menages, deces ( deces_j ), filiation et conjoint ( le deuil touche le menage et
   les proches ), la faim de la semaine ( faim7 ). Agenda ( 5 ) : ETEND ses tours sans les dupliquer - lit la pratique
   du dimanche ( agenda_pratiquant ) et les sorties realisees du plan ( culte, loisir de jour, loisir du soir ) ;
   annule les sorties de loisir d un menage qui reste ; ajoute le repas de fete, la liturgie des grandes fetes et du
   saint patron, le panigyri du soir, avec les primitives de l agenda ( `_trajets`, `_tour_simple`, `_relire` ).
   Medias ( 22 ) : `climat( p, lieu )` chaque soir, pour chaque lieu habite. Economie ( 3 ) : le revenu lisse
   ( eco_revenu ), le chomage ( actif sans lieu de travail ) ; la division COICOP 09 ( loisirs ) et une part de la 11
   ( cafes, tavernes ) sont SERVIES ici par des prestataires ( voir 8 et le rapport ). Medecine ( 16, optionnel ) : la
   depression ( med_mental ) pese sur le moral ; `risque_relatif_mental` rend l effet inverse. Banques ( 2 ) :
   `ouvrir_compte` de chaque paroisse, etablissement, club. Paie et recoit : menages -> etablissements ( sorties ),
   -> paroisses ( dons, funerailles, panigyri ), -> clubs ( cotisations ) ; etablissements -> marches
   ( approvisionnement ), -> exterieur ( droits des films ), -> menages d artistes ( cachets ), -> menage proprietaire
   ( revenu d exploitant ), -> Etat ( TVA ) ; paroisses -> menages affames de leur lieu ( entraide ), -> musiciens
   ( cachets ), -> marches ( fournitures ) ; clubs -> entraineur ( salaire ), -> marches ( entretien ). Ne remplace
   aucune methode du moteur. API en fin de fichier : moral, moral_collectif, moral_des_lieux, facteur_productivite
   ( 4 ), risque_greve ( 4 ), facteur_desobeissance ( 5, 21 ), risque_relatif_mental ( 16 ), discipline ( 25-27 ),
   humeur_politique ( 24 ), confession, etablissements, depense_du_jour.
6. Portes : tests_d23_culture.py.
7. Arma : aucun corps propre. Les lieux sont des batiments du domaine 13 : eglise Land_Church_01_V1_F, chapelle
   Land_Chapel_V1_F, kafeneio et taverne Land_i_Shop_01_V1_F ( arma_preuve = None : personne ne les a vus servir ).
8. Cout. Le matin : les traits d un septieme des menages ( colonnes ), les tours de fete ajoutes en tableaux. Le
   soir : les sorties realisees lues dans le plan de l agenda ( colonnes ), un paiement par couple ( menage,
   etablissement ) du jour, le climat de chaque lieu habite ( une lecture de la memoire des medias par lieu ), le moral
   de tous en une passe vectorisee, une note par menage qui attend. Lineaire en habitants ; les lieux sont ceux de la
   carte. Mesures : voir test_cout."""
import collections, math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, calendrier as CAL
from . import pays as P, d01_population as POP, d05_agenda as AG, d22_medias as ME

DOMAINE = "culture"
EUROS = P.EUROS_PAR_DRACHME
MOIS_J = 30
JOURS_AN = 365.0

# ================================================================== la religion
# Pew Research Center ( 2017, Religious Belief and National Belonging in Central and Eastern Europe ) : Grece,
# orthodoxes 90 %, sans religion 4 %, musulmans 2 % ( la minorite de Thrace ), autres 4 % ( catholiques ~1 %,
# protestants, temoins de Jehovah... ; a verifier ). ELSTAT ne demande pas la religion au recensement.
ORTHODOXE, MUSULMAN, CATHOLIQUE, AUTRE, SANS = range(5)
CONFESSIONS = ("orthodoxe", "musulman", "catholique", "autre", "sans")
PARTS_CONFESSION = np.array([0.90, 0.02, 0.01, 0.03, 0.04])
MINORITES = (MUSULMAN, CATHOLIQUE, AUTRE)
# La pratique du dimanche est celle de l agenda ( PRATIQUE : 10 a 30 % des adultes selon l age ; Pew 2017 : environ
# 17 % des Grecs a l office chaque semaine, a verifier ). Les grandes fetes remplissent les eglises : part des
# orthodoxes NON pratiquants qui y vont ( a calibrer : la nuit de Paques est la plus suivie de l annee ).
FETES_RELIGIEUSES = {"paques": 0.60, "vendredi_saint": 0.45, "dormition": 0.30, "noel": 0.30, "theophanie": 0.20,
                     "lundi_pur": 0.05, "lundi_de_paques": 0.05, "lundi_de_pentecote": 0.05, "synaxe_theotokos": 0.05}
FETES_MAJEURES = ("paques", "vendredi_saint", "dormition", "noel")   # celles qui font une semaine de fete ( trait )
P_FETE_PATRONALE = 0.40      # non pratiquants a la liturgie du saint patron de leur village ( a calibrer )
P_PANIGYRI = 0.60            # residents de 6 ans et plus au panigyri du soir ( a calibrer : la fete de l annee )
# Les fetes patronales : ( mois, jour, saint, poids ). Dates fixes du calendrier orthodoxe ; la Dormition ( Panagia,
# 15 aout ) est la plus frequente des eglises de village. Saint Georges ( 23 avril ) est reporte apres Paques quand il
# tombe en careme : non modelise. Poids : a calibrer.
FETES_PATRONALES = ((6, 24, "genethlio_prodromou", 1), (6, 29, "agioi_apostoloi", 1), (7, 17, "agia_marina", 2),
                    (7, 20, "profitis_ilias", 2), (7, 26, "agia_paraskevi", 2), (7, 27, "agios_panteleimon", 1),
                    (8, 6, "metamorfosi", 1), (8, 15, "koimisi_theotokou", 4), (8, 29, "apotomi_prodromou", 1),
                    (9, 8, "genethlio_theotokou", 1), (9, 14, "timios_stavros", 1), (10, 26, "agios_dimitrios", 2),
                    (11, 8, "taxiarches", 1), (12, 6, "agios_nikolaos", 2), (4, 23, "agios_georgios", 2),
                    (5, 21, "agioi_konstantinos_eleni", 1))
DON_CULTE_EUR = 1.5          # cierges et plateau, par adulte a l office ( ordre de grandeur, a calibrer )
DON_FETE_EUR = 3.0           # le jour d une grande fete ou du saint patron
SERVICE_FUNEBRE_EUR = 150.0  # la part de l eglise dans des obseques grecques ( a calibrer )
DEUIL_COUTUME_J = 40         # les quarante jours : pas de fete dans un menage en deuil ( coutume orthodoxe )
AIDE_JOURS = 7               # l entraide paroissiale donne une semaine de nourriture a un menage qui a faim
PART_AIDE = 0.5              # au plus la moitie de la caisse de la paroisse chaque dimanche ( a calibrer )
PART_FOURNITURES = 0.3       # cierges, huile, electricite de l eglise : part des dons du mois ( a calibrer )
RESERVE_PAROISSE_MOIS = 6.0  # au-dela de six mois de dons, la paroisse entretient son eglise
PART_MUSIQUE = 0.25          # le panigyri paie ses musiciens ( a calibrer )
PART_PANIGYRI_INTRANTS = 0.45   # viande, vin, pain achetes aux marches ( a calibrer )
MUSICIENS_PAR_ILE = 3        # menages de musiciens ( la kompania ) par ile, dans sa capitale

# ================================================================== les loisirs
# Prix ( euros TTC par personne, ordres de grandeur grecs 2023-2024, a calibrer ) ; un enfant de moins de 15 ans
# paie la moitie. Probabilites du lieu de la sortie : a calibrer ( ELSTAT, enquete emploi du temps, a lire ).
PRIX_EUR = {"cafe": 2.5, "cafe_soir": 4.5, "taverne": 15.0, "cinema": 8.5, "theatre": 18.0, "ville": 12.0,
            "panigyri": 12.0}
FACTEUR_ENFANT = 0.5
P_TAVERNE_MIDI = 0.40        # le jour de repos, le dejeuner a la taverne
P_TAVERNE_SOIR = 0.35        # le soir, la taverne plutot que le verre au kafeneio
P_CINEMA, P_THEATRE = 0.15, 0.04   # une sortie en ville des jeunes
# TVA grecque : restauration et cafe 13 % ; cinema 13 %, theatre 6 % ( a verifier ) ; sport 24 %.
TYPES_ETABLISSEMENT = {   # type : ( taux de TVA, part des intrants achetes aux marches, part versee a l exterieur, cachets )
    "kafeneio": (0.13, 0.35, 0.0, 0.0), "taverne": (0.13, 0.40, 0.0, 0.0),
    "cinema": (0.13, 0.10, 0.45, 0.0), "theatre": (0.06, 0.15, 0.0, 0.35)}
FONDS_ROULEMENT_MOIS = 0.5   # un etablissement garde un demi-mois de chiffre d affaires ( a calibrer )
ARTISTES_PAR_THEATRE = 4
RESERVE_SORTIE_J = 7         # jours de nourriture gardes avant de payer une sortie
RESERVE_FETE_J = 1           # ... quand le menage a choisi la fete
RESERVE_DON_J = 3
RESERVE_COTISATION_J = 14
# Clubs sportifs : Eurobarometre special 525 ( 2022, sport et activite physique ) : les Grecs parmi les moins actifs
# de l Union ; part des 18-64 ans membres d un club : 7 % ( a calibrer ). Cotisation 25 euros par mois.
P_CLUB = 0.07
COTISATION_EUR = 25.0
PART_ENTRAINEUR, PART_ENTRETIEN, RESERVE_CLUB_MOIS = 0.5, 0.3, 2.0
ARMA = {"paroisse": "Land_Church_01_V1_F", "chapelle": "Land_Chapel_V1_F", "kafeneio": "Land_i_Shop_01_V1_F",
        "taverne": "Land_i_Shop_01_V1_F"}   # batiments du domaine 13 ; arma_preuve = None

# ================================================================== le moral
# Echelle 0-1, lue comme la satisfaction de vie sur 10 : Eurostat ( EU-SILC 2018 ) Grece 6,2 sur 10, parmi les plus
# basses de l Union ( a verifier ). Les effets sont des ordres de grandeur de la litterature du bien-etre, a calibrer :
# Clark, Diener, Georgellis et Lucas ( 2008, Economic Journal ) : chomage et veuvage de -0,5 a -1 point sur 10 ;
# Frongillo et al. ( 2017, J. Nutrition ) : l insecurite alimentaire, un des plus forts correlats ; la frequence des
# rencontres ( ESS ) ~ 0,5 point entre jamais et chaque semaine ; les pratiquants un peu plus heureux ( Pew 2019 ).
BASE_MOY, BASE_SD, BASE_MIN, BASE_MAX = 0.60, 0.08, 0.25, 0.90
TAU_J = 5.0                  # le moral lent rejoint ses causes en quelques jours ( a calibrer )
K_FAIM_SEMAINE = 0.20        # x jours sans repas de son menage sur 7
K_FAIM_CORPS = 0.08          # x rations manquees accumulees, sur 3
FAIM_PLEINE = 3.0
K_CHOMAGE = 0.07
K_PAUVRE = 0.05              # caisse du menage sous 3 jours de nourriture
JOURS_PAUVRE = 3.0
K_MALADE = 0.06              # malade symptomatique ( I )
K_DEPRESSION = 0.12          # episode depressif ( domaine 16 )
K_MEDIAS_NEG, K_MEDIAS_POS = 0.15, 0.05   # x ce que le lieu croit de mauvais ( de bon ), sature a 1
K_LIENS = 0.10               # x ( min( 1, soirs avec du monde sur 7 / 3 ) - 0,4 ) : l isolement pese, les liens portent
LIENS_PLEINS, LIENS_REF = 3.0, 0.4
K_CULTE = 0.02               # un pratiquant
DEUIL_MENAGE, DEUIL_PROCHE, DEUIL_MIN = -0.15, -0.08, -0.40
DEMI_VIE_DEUIL_J = 90.0
# ( 03/10, HMT-194 3c ) un soldat au front de la guerre d Arma garde le moral de chez lui : la faim de son menage, un
# deuil chez lui, l isolement l atteignent ( lettres, telephone ; CHOIX : le jour meme, sans delai de courrier )
MORAL_AU_FRONT = True
FETE_PANIGYRI, FETE_RELIGIEUSE, FETE_SORTIE, PLAISIR_SORTIE, FETE_MAX = 0.06, 0.04, 0.03, 0.015, 0.15
DEMI_VIE_FETE_J = 4.0
MORAL_BAS = 0.35
MORAL_REF = 0.60             # le moral d un pays ordinaire, reference des effets rendus aux autres domaines
# Effets rendus ( a calibrer ) : Oswald, Proto et Sgroi ( 2015, J. Labor Econ. ) : +12 % de productivite apres un choc
# de bonheur ; Bellet, De Neve et Ward ( 2019 ) : +13 % de ventes les semaines heureuses.
ELAST_PRODUCTIVITE, BORNES_PRODUCTIVITE = 0.5, (0.85, 1.12)
K_GREVE, K_DESOBEISSANCE, K_MENTAL = 4.0, 2.0, 3.0

# ================================================================== la decision `loisirs`
RESTER, SORTIR, FETE, ECONOMISER = range(4)
ACTIONS = ("rester", "sortir", "fete", "economiser")
JOURS_TRAIT = 60.0
JOURS_ECONOMIE, JOURS_FETE = 10.0, 30.0
HORIZON_LOISIRS = 7
FENETRE_FETE_J = 7

# ================================================================== le temps du plan
M_SOIR = 23 * 60 + 50 - AG.MINUTE_AUBE     # 23 h 50, en minutes depuis 6 h : les sorties du jour sont finies
M_CAFE_FIN = 19 * 60 - AG.MINUTE_AUBE      # un retraite arrive avant 19 h : le cafe de l apres-midi
OFFICE_FETE = (8 * 60 + 30, 60, 60, 40)     # celui de l agenda ( AG.OFFICE )
PANIGYRI_SOIR = (21 * 60, 60, 150, 90)      # arrivee 21 h a 22 h, 2 h 30 a 4 h de fete
REPAS_FETE = (20 * 60 + 30, 60, 150, 60)    # le repas de famille a la taverne

POPCOUNT = np.array([bin(i).count("1") for i in range(256)], np.int64)


# ================================================================== les classes
class Paroisse:
    """Une paroisse ( ou une communaute minoritaire, dans la capitale de son ile ) : elle recoit les dons, les services
    religieux et le panigyri de son saint patron ; elle nourrit ceux qui ont faim dans son lieu ; ses fournitures et son
    entretien vont aux marches. Le pretre est paye par l Etat en Grece : non modelise ici ( domaine 6 )."""
    __slots__ = ("indice", "nom", "lieu", "ile", "confession", "fete", "saint", "caisse", "dons_mois", "dons_total",
                 "services_total", "panigyri_total", "aide_total", "sortie_total")

    def __init__(self, indice, nom, lieu, ile, confession, fete, saint):
        if confession not in range(len(CONFESSIONS) - 1): raise ValueError(f"{nom} : confession invalide {confession!r}")
        if fete is not None and not (1 <= fete[0] <= 12 and 1 <= fete[1] <= 31): raise ValueError(f"{nom} : fete {fete!r}")
        self.indice, self.nom, self.lieu, self.ile, self.confession = indice, nom, int(lieu), ile, confession
        self.fete, self.saint = fete, saint
        self.caisse = 0.0
        self.dons_mois = self.dons_total = self.services_total = self.panigyri_total = 0.0
        self.aide_total = self.sortie_total = 0.0


class Etablissement:
    """Un kafeneio, une taverne, un cinema, un theatre : une affaire familiale. Le menage proprietaire recoit ce qui
    reste chaque mois, au-dela du fonds de roulement."""
    __slots__ = ("indice", "type", "lieu", "ile", "proprietaire", "tva", "caisse", "recettes_ht_mois", "recettes_ttc",
                 "tva_due", "tva_versee", "clients", "artistes", "verse_proprietaire", "verse_marche", "verse_exterieur",
                 "cachets")

    def __init__(self, indice, type_, lieu, ile, proprietaire, artistes=()):
        if type_ not in TYPES_ETABLISSEMENT: raise ValueError(f"type d etablissement inconnu {type_!r}")
        self.indice, self.type, self.lieu, self.ile = indice, type_, int(lieu), ile
        self.proprietaire = int(proprietaire)
        self.tva = TYPES_ETABLISSEMENT[type_][0]
        self.caisse = 0.0
        self.recettes_ht_mois = self.recettes_ttc = self.tva_due = self.tva_versee = 0.0
        self.clients = 0
        self.artistes = tuple(int(x) for x in artistes)
        self.verse_proprietaire = self.verse_marche = self.verse_exterieur = self.cachets = 0.0


class Association:
    """Un club sportif et culturel : cotisations de ses membres, salaire de son entraineur, entretien."""
    __slots__ = ("indice", "type", "lieu", "ile", "entraineur", "caisse", "cotisations_mois", "cotisations_total",
                 "membres", "verse_total")

    def __init__(self, indice, lieu, ile, entraineur):
        self.indice, self.type, self.lieu, self.ile, self.entraineur = indice, "club_sportif", int(lieu), ile, int(entraineur)
        self.caisse = 0.0
        self.cotisations_mois = self.cotisations_total = self.verse_total = 0.0
        self.membres = 0


def _membres_paroisses(w): return w.pays.domaines[DOMAINE].paroisses
def _membres_etablissements(w): return w.pays.domaines[DOMAINE].etablissements
def _membres_associations(w): return w.pays.domaines[DOMAINE].associations


class ContexteLoisirs:
    """Ce qu un menage sait de lui-meme le matin de sa decision de la semaine : sa bourse, sa faim, son humeur, son
    revenu, le calendrier des fetes, son deuil, ce qui se dit dans son lieu."""
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer_loisirs(ctx): return ctx.traits


def _regle_loisirs(x, ctx):
    if x[5] >= 0.5: return RESTER
    if x[1] > 0.0 or x[0] < JOURS_ECONOMIE / JOURS_TRAIT: return ECONOMISER
    if x[4] >= 0.5 and x[0] >= JOURS_FETE / JOURS_TRAIT: return FETE
    return SORTIR


def _regle_vect(X):
    """La regle, appliquee a un tableau de traits : la meme que `_regle_loisirs`, dans le meme ordre de priorite."""
    out = np.full(len(X), SORTIR, np.int64)
    out[(X[:, 4] >= 0.5) & (X[:, 0] >= JOURS_FETE / JOURS_TRAIT)] = FETE
    out[(X[:, 1] > 0.0) | (X[:, 0] < JOURS_ECONOMIE / JOURS_TRAIT)] = ECONOMISER
    out[X[:, 5] >= 0.5] = RESTER
    return out


def _temoin_loisirs(x, ctx, rng): return RESTER


POINT_LOISIRS = D.PointDeDecision(
    "loisirs", DOMAINE,
    traits=(("jours_de_caisse", "la caisse de son menage en jours de nourriture au prix affiche, sur 60"),
            ("faim_semaine", "les soirs sans repas de son menage sur 7 ( sa table )"),
            ("moral", "l humeur moyenne de son menage ( ce qu ils ressentent )"),
            ("revenu", "le revenu lisse de son menage sur 5 fois son besoin de nourriture"),
            ("fete_proche", "le calendrier public : panigyri de son village ou grande fete ( Paques, Dormition... ) dans 7 jours"),
            ("deuil", "un deces dans son menage depuis moins de 40 jours"),
            ("climat", "ce qui se dit de mauvais dans son lieu ( croyances, domaine 22 ), sature a 1")),
    actions=ACTIONS, observer=_observer_loisirs, regle=_regle_loisirs, temoin=_temoin_loisirs,
    note="chaque jour, pour CE menage : ( moral moyen de ses membres + a-t-il mange ) / 2",
    horizon_j=HORIZON_LOISIRS)


class Culture:
    __slots__ = ("paroisses", "etablissements", "associations", "decideur", "L", "lieu_ids", "n_du_lieu", "habitable",
                 "ile_de", "iles", "capitale_de", "marche_de", "paroisse_de", "communaute", "kafeneio_de", "taverne_de",
                 "cinema_de", "theatre_de", "club_de", "musiciens", "fete_mois", "fete_jour", "fete_proche",
                 "moral_lieu", "residents_lieu", "historique", "climat_neg", "climat_pos", "fete_ids", "panigyri_ids",
                 "panigyri_lieux", "fete_du_jour", "culte_fete_ids", "compte", "livre_motifs", "serie", "depense_jour")

    def __init__(self):
        self.paroisses, self.etablissements, self.associations = [], [], []
        self.communaute = {}          # ( ile, confession ) -> indice de paroisse
        self.musiciens = {}           # ile -> [ menages ]
        self.historique = collections.deque(maxlen=8)   # le moral des lieux, un tableau par soir
        self.fete_ids = self.panigyri_ids = self.culte_fete_ids = np.zeros(0, np.int64)
        self.panigyri_lieux = []
        self.fete_du_jour = None
        self.compte = collections.defaultdict(float)
        self.livre_motifs = collections.defaultdict(float)
        self.serie = collections.deque(maxlen=400)
        self.depense_jour = 0.0


def _dom(p): return p.domaines[DOMAINE]


# ================================================================== petits outils
def _composer(base, lent, deuil, fete):
    """Le moral : la somme de ses quatre parts, bornee. Le meme calcul pour ecrire et pour verifier."""
    return np.clip(base.astype(np.float64) + lent.astype(np.float64) + deuil.astype(np.float64)
                   + fete.astype(np.float64), 0.0, 1.0).astype(np.float32)


def _menages_vivants(p):
    """( numeros de menage inscrits des habitants, vivants residents par menage, nombre de menages )."""
    tb = p.w.table; n = tb.n; M = tb.menages.n
    mg = PO.menages_inscrits(tb, n)
    v = (tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & (mg >= 0)
    return mg, np.bincount(mg[v], minlength=M)[:M], M


def _plancher(p, cout):
    """( 28/09, HMT-126 e ) Ce qu un menage garde au moins avant une sortie, une fete, un don ou une cotisation : rien de
    plus que ses reserves propres s il a un revenu qui nourrit son menage ; JOURS_SANS_REVENU jours de nourriture
    ( domaine 3 ) sinon - un menage sans nourriture assuree ne va pas au cafe. La guerre des iles, Altis, 90 jours : les
    menages des enfants morts de faim avaient paye 802 drachmes de cafe et de taverne pour 2 590 de nourriture."""
    if not p.a("economie"): return np.zeros(len(cout))
    EC = __import__(__package__ + ".d03_economie", fromlist=["x"])
    return EC.plancher_discretionnaire(p, cout)


def _cout_jour(p, M, viv):
    """Le cout d un jour de nourriture de chaque menage, au prix TTC affiche de son marche."""
    w = p.w; tb = w.table
    pm0 = float(C.PRIX_MONDE["nourriture"])
    prix_n = np.full(len(w.carte.par_n), pm0)
    for mid, m in w.marches.items(): prix_n[w.carte.lieux[mid].n] = m.prix["nourriture"] * (1.0 + w.gouv.tva)
    dm = tb.menages.domicile[:M].astype(np.int64)
    pm = np.where(dm >= 0, prix_n[w._marche_du_lieu[np.maximum(dm, 0)]], pm0)
    return pm * C.NOURRITURE_PAR_JOUR * np.maximum(1, viv)


def _vue(tb, k): return PO.Menage(int(k), tb.menages)


def _payer(p, d, de, vers, montant, motif):
    """Un paiement du domaine, compte par motif ( le recoupement avec le grand livre )."""
    if montant <= 0.0: return 0.0
    x = p.socle.livre.transferer(de, vers, montant, motif)
    d.compte[motif] += x
    return x


def _grouper(cles, n_max):
    """( ordre, debuts ) : les indices tries par cle, et le debut de chaque cle de 0 a n_max."""
    ordre = np.argsort(cles, kind="stable")
    return ordre, np.searchsorted(cles[ordre], np.arange(n_max + 1))


def _dates_prochaines(date, n):
    import datetime as dt
    return [date + dt.timedelta(days=k) for k in range(n)]


def _fete_nationale(cal, date):
    """Le nom de la grande fete religieuse de ce jour, ou None ( Paques, dimanche, n est pas un ferie du socle )."""
    if date == CAL.paques_orthodoxe(date.year): return "paques"
    f = cal.ferie(date)
    return f if f in FETES_RELIGIEUSES else None


# ================================================================== l installation
def _carte(p, d):
    w = p.w
    lieux = sorted(w.carte.lieux.values(), key=lambda l: l.n)
    if any(l.n != k for k, l in enumerate(lieux)): raise RuntimeError("culture : lieux hors de l ordre du moteur")
    d.L = L = len(lieux)
    d.lieu_ids = [l.id for l in lieux]
    d.n_du_lieu = {l.id: l.n for l in lieux}
    d.habitable = np.array([l.type in ("capitale", "ville", "village") for l in lieux])
    d.ile_de = [l.ile for l in lieux]
    d.iles = sorted(set(d.ile_de), key=lambda i: min(k for k, x in enumerate(d.ile_de) if x == i))
    caps = {}
    for c in sorted(w.carte.capitales, key=lambda l: l.n): caps.setdefault(c.ile, c.n)
    d.capitale_de = {i: caps.get(i, min(k for k, x in enumerate(d.ile_de) if x == i)) for i in d.iles}
    d.marche_de = np.array([l.marche.n if getattr(l, "marche", None) is not None else l.n for l in lieux], np.int64)
    for nom in ("paroisse_de", "kafeneio_de", "taverne_de", "cinema_de", "theatre_de", "club_de"):
        setattr(d, nom, np.full(L, -1, np.int64))
    d.fete_mois = np.full(L, -1, np.int64); d.fete_jour = np.full(L, -1, np.int64)
    d.fete_proche = np.zeros(L, bool)
    d.moral_lieu = np.zeros(L); d.residents_lieu = np.zeros(L, np.int64)
    d.climat_neg = np.zeros(L); d.climat_pos = np.zeros(L)
    return lieux


def _proprietaires(p, rng, lieux_voulus, par_lieu, pris):
    """Un menage habite de chaque lieu demande, tire au hasard parmi ceux qui ne tiennent pas deja une affaire."""
    out = []
    ordre, debuts, cand = par_lieu
    for n in lieux_voulus:
        ks = cand[ordre[debuts[n]:debuts[n + 1]]]
        libres = [int(k) for k in ks.tolist() if int(k) not in pris] or [int(k) for k in ks.tolist()]
        if not libres: out.append(-1); continue
        k = libres[int(rng.integers(len(libres)))]
        pris.add(k); out.append(k)
    return out


def installer(p):
    w = p.w; L_ = p.socle.livre; tb = w.table
    d = Culture()
    p.domaines[DOMAINE] = d
    lieux = _carte(p, d)
    for m_, nature in MOTIFS: L_.declarer_motif(m_, nature, DOMAINE)
    J = p.socle.journal
    J.declarer("panigyri", DOMAINE, "individuel", ("lieu", "saint", "participants", "recettes"))
    J.declarer("fete_religieuse", DOMAINE, "individuel", ("fete", "fideles"))
    for t_ in ("sortie_payee", "don_religieux", "service_religieux", "aide_paroissiale", "cotisation_club",
               "decision_loisirs", "deuil"):
        J.declarer(t_, DOMAINE, "compte")
    ch, cm = p.colonnes["habitant"], p.colonnes["menage"]
    for nom, dt_, v in COLONNES_HABITANT: ch.ajouter(nom, dt_, v)
    for nom, dt_, v in COLONNES_MENAGE: cm.ajouter(nom, dt_, v)
    n = tb.n; M = tb.menages.n
    ch.assurer(n); cm.assurer(M)
    rng = p.hasard("culture_installation")
    # --- les menages habites, par lieu ( une passe triee : lineaire )
    mg, viv, M = _menages_vivants(p)
    dis = p.col("menage", "dissous")[:M] if "dissous" in cm else np.zeros(M, np.int8)
    dom_m = tb.menages.domicile[:M].astype(np.int64)
    cand = np.nonzero((viv > 0) & (dis == 0) & (dom_m >= 0))[0]
    o, deb = _grouper(dom_m[cand], d.L)
    par_lieu = (o, deb, cand)
    pris = set()
    habites = [l.n for l in lieux if d.habitable[l.n]]
    # --- les paroisses et leur saint patron
    poids = np.array([f[3] for f in FETES_PATRONALES], np.float64); poids /= poids.sum()
    choix = rng.choice(len(FETES_PATRONALES), size=len(habites), p=poids)
    for n_, k in zip(habites, choix.tolist()):
        mo, jo, saint, _ = FETES_PATRONALES[k]
        x = Paroisse(len(d.paroisses), f"paroisse_{d.lieu_ids[n_].lower()}", n_, d.ile_de[n_], ORTHODOXE, (mo, jo), saint)
        d.paroisses.append(x); d.paroisse_de[n_] = x.indice
        d.fete_mois[n_], d.fete_jour[n_] = mo, jo
    for ile in d.iles:
        cap = d.capitale_de[ile]
        for c in MINORITES:
            x = Paroisse(len(d.paroisses), f"communaute_{CONFESSIONS[c]}_{ile.lower()}", cap, ile, c, None, None)
            d.paroisses.append(x); d.communaute[(ile, c)] = x.indice
    # --- les etablissements ( kafeneio et taverne partout ; cinema et theatre dans les capitales )
    caps = sorted(set(d.capitale_de.values()))
    musiciens = {ile: _proprietaires(p, rng, [d.capitale_de[ile]] * MUSICIENS_PAR_ILE, par_lieu, pris) for ile in d.iles}
    d.musiciens = {ile: [k for k in v if k >= 0] for ile, v in musiciens.items()}
    for type_, lieux_t, table in (("kafeneio", habites, d.kafeneio_de), ("taverne", habites, d.taverne_de),
                                  ("cinema", caps, d.cinema_de), ("theatre", caps, d.theatre_de)):
        props = _proprietaires(p, rng, lieux_t, par_lieu, pris)
        for n_, k in zip(lieux_t, props):
            if k < 0: continue
            art = _proprietaires(p, rng, [n_] * ARTISTES_PAR_THEATRE, par_lieu, pris) if type_ == "theatre" else ()
            e = Etablissement(len(d.etablissements), type_, n_, d.ile_de[n_], k, [a for a in art if a >= 0])
            d.etablissements.append(e); table[n_] = e.indice
    # --- les clubs ( villes et capitales ) et leurs membres
    villes = [l.n for l in lieux if l.type in ("capitale", "ville")]
    for n_, k in zip(villes, _proprietaires(p, rng, villes, par_lieu, pris)):
        if k < 0: continue
        a = Association(len(d.associations), n_, d.ile_de[n_], k)
        d.associations.append(a); d.club_de[n_] = a.indice
    ages = tb.age[:n]
    dom_h = tb.domicile[:n].astype(np.int64)
    club_h = np.where(dom_h >= 0, d.club_de[np.maximum(dom_h, 0)], -1)
    club_h = np.where(club_h >= 0, club_h, np.where(dom_h >= 0, d.club_de[d.marche_de[np.maximum(dom_h, 0)]], -1))
    u = rng.random(n)
    membre = (tb.vivant[:n] == 1) & (ages >= 18) & (ages < 65) & (club_h >= 0) & (u < P_CLUB)
    ch["cul_club"][:n] = np.where(membre, club_h, -1).astype(np.int16)
    cnt = np.bincount(club_h[membre], minlength=len(d.associations))
    for a in d.associations: a.membres = int(cnt[a.indice])
    # --- le temperament de chacun ( la confession attend la pratique, que l agenda tire au premier matin )
    z = rng.standard_normal(n)
    b = np.clip(BASE_MOY + BASE_SD * z, BASE_MIN, BASE_MAX).astype(np.float32)
    ch["cul_base"][:n] = b; ch["cul_moral"][:n] = b
    # --- les comptes en banque, le registre
    reg = p.socle.registre
    reg.inscrire("paroisses", "associations", _membres_paroisses, "caisse", None, "Paroisse")
    reg.inscrire("etablissements_loisir", "entreprises", _membres_etablissements, "caisse", None, "Etablissement")
    reg.inscrire("associations_loisir", "associations", _membres_associations, "caisse", None, "Association")
    if p.a("banques"):
        from . import d02_banques as BQ
        bq = p.domaine("banques")
        parts = np.array([x.part for x in bq.banques], np.float64); parts /= parts.sum()
        rb = p.hasard("culture_banques")
        for x in d.paroisses + d.etablissements + d.associations:
            BQ.ouvrir_compte(p, x, bq.banques[int(rb.choice(len(parts), p=parts))])
    d.decideur = p.decideur(POINT_LOISIRS)
    p.routine(6.0, 40, DOMAINE, _matin)
    p.routine(23 + 50 / 60, 95, DOMAINE, _soir)
    p.cloture(DOMAINE, _cloture)
    return d


MOTIFS = (("sortie_cafe_taverne", "achat"), ("spectacle", "achat"), ("panigyri", "achat"),
          ("service_religieux", "achat"), ("don_religieux", "transfert_courant"),
          ("cotisation_club", "transfert_courant"), ("aide_paroissiale", "transfert_courant"),
          ("approvisionnement_loisirs", "achat"), ("fournitures_culte", "achat"), ("entretien_equipements", "achat"),
          ("droits_films", "achat"), ("cachet_artistes", "remuneration"), ("cachet_musiciens", "remuneration"),
          ("salaire_club", "remuneration"), ("revenu_exploitant_loisirs", "revenu_propriete"))
MOTIFS_MENAGES = ("sortie_cafe_taverne", "spectacle", "panigyri", "service_religieux", "don_religieux",
                  "cotisation_club")
COLONNES_HABITANT = (("cul_confession", np.int8, -1), ("cul_base", np.float32, -1.0), ("cul_lent", np.float32, 0.0),
                     ("cul_deuil", np.float32, 0.0), ("cul_fete", np.float32, 0.0), ("cul_moral", np.float32, 0.0),
                     ("cul_sorties7", np.uint8, 0), ("cul_deuil_vu", np.int8, 0), ("cul_club", np.int16, -1))
COLONNES_MENAGE = (("cul_choix", np.int8, -1), ("cul_deuil_j", np.int32, -100000), ("cul_depense", np.float64, 0.0),
                   ("cul_dons", np.float64, 0.0))


# ================================================================== le matin ( 6 h, apres le plan de l agenda )
def _nouveaux(p, d, n):
    """Les habitants sans confession ( tous au premier matin, puis les nouveau-nes ) : temperament, et confession
    tiree SACHANT la pratique de l agenda ( un pratiquant a une religion ; les parts du pays restent celles de Pew ).
    Un mineur prend la confession de sa mere."""
    col = p.colonnes["habitant"]; tb = p.w.table
    conf, base = col["cul_confession"], col["cul_base"]
    neufs = np.nonzero(conf[:n] < 0)[0]
    if not len(neufs): return
    rng = p.du_jour("culture_nouveaux")
    u = rng.random(len(neufs)); z = rng.standard_normal(len(neufs))
    sans_base = base[neufs] < 0
    b = np.clip(BASE_MOY + BASE_SD * z, BASE_MIN, BASE_MAX).astype(np.float32)
    base[neufs[sans_base]] = b[sans_base]
    col["cul_moral"][neufs[sans_base]] = b[sans_base]
    prat = col["agenda_pratiquant"][neufs] == 1
    q = min(0.5, float(prat.mean())) if len(prat) else 0.0
    rel = PARTS_CONFESSION.copy(); rel[SANS] = 0.0; rel /= rel.sum()
    non = np.maximum(0.0, PARTS_CONFESSION - q * rel); non /= non.sum()
    tire = np.where(prat, np.searchsorted(np.cumsum(rel), u, side="right"),
                    np.searchsorted(np.cumsum(non), u, side="right"))
    tire = np.minimum(tire, len(CONFESSIONS) - 1)
    age = tb.age[neufs]
    adulte = age >= POP.AGE_MAJEUR
    conf[neufs[adulte]] = tire[adulte]
    mineurs = neufs[~adulte]
    if len(mineurs):
        mere = col["mere"][mineurs].astype(np.int64)
        cm = np.where(mere >= 0, conf[np.maximum(mere, 0)], -1)
        ok = (cm >= 0) & ~((cm == SANS) & prat[~adulte])
        conf[mineurs] = np.where(ok, cm, tire[~adulte])


def _calendrier_des_fetes(p, d, date):
    """Les lieux dont le saint patron est fete aujourd hui ; la grande fete du jour ; les lieux ou une fete tombe
    dans les 7 jours ( le trait `fete_proche` : un calendrier public )."""
    cal = p.socle.calendrier
    proche = np.zeros(d.L, bool)
    nationale = False
    for k, x in enumerate(_dates_prochaines(date, FENETRE_FETE_J)):
        proche |= (d.fete_mois == x.month) & (d.fete_jour == x.day)
        nationale |= _fete_nationale(cal, x) in FETES_MAJEURES
    d.fete_proche = proche | (nationale & d.habitable)
    patron = np.nonzero((d.fete_mois == date.month) & (d.fete_jour == date.day))[0]
    return patron, _fete_nationale(cal, date)


def _traits(p, d, ks, mg, viv, M, cout):
    """Les traits des menages `ks`, en colonnes."""
    tb = p.w.table; n = tb.n
    col = p.colonnes["habitant"]
    caisse = tb.menages.caisse[:M]
    jours = np.maximum(0.0, caisse[ks]) / cout[ks]
    f7 = POPCOUNT[p.col("menage", "faim7")[ks].astype(np.int64) & 0x7F] / 7.0
    v = (tb.vivant[:n] == 1) & (mg >= 0)
    somme = np.bincount(mg[v], weights=col["cul_moral"][:n][v].astype(np.float64), minlength=M)[:M]
    moral_m = np.clip(somme[ks] / np.maximum(1, viv[ks]), 0.0, 1.0)
    rev = np.minimum(1.0, np.maximum(0.0, p.col("menage", "eco_revenu")[ks]) / (5.0 * cout[ks])) \
        if "eco_revenu" in p.colonnes["menage"] else np.zeros(len(ks))
    dom = tb.menages.domicile[ks].astype(np.int64)
    fete = np.where(dom >= 0, d.fete_proche[np.maximum(dom, 0)], False).astype(float)
    deuil = (p.jour - p.col("menage", "cul_deuil_j")[ks].astype(np.int64) < DEUIL_COUTUME_J).astype(float)
    climat = np.where(dom >= 0, np.minimum(1.0, d.climat_neg[np.maximum(dom, 0)]), 0.0)
    return np.column_stack([np.minimum(1.0, jours / JOURS_TRAIT), f7, moral_m, rev, fete, deuil, climat])


def _decider(p, d, mg, viv, M, cout):
    """Les menages dont c est le jour decident de leur semaine."""
    tb = p.w.table; n = tb.n
    dis = p.col("menage", "dissous")[:M]
    adultes = np.bincount(mg[(tb.vivant[:n] == 1) & (mg >= 0) & (tb.age[:n] >= POP.AGE_MAJEUR)], minlength=M)[:M]
    ks = np.nonzero((viv > 0) & (dis == 0) & (adultes > 0) & (np.arange(M) % 7 == p.jour % 7)
                    & (tb.menages.domicile[:M] >= 0))[0]
    if not len(ks): return 0
    X = _traits(p, d, ks, mg, viv, M, cout)
    dec = d.decideur
    simple = (type(dec) is D.Decideur and dec.point is POINT_LOISIRS and dec.mode in ("regle", "temoin")
              and type(dec).observer is D.Decideur.observer and ((X >= 0.0) & (X <= 1.0)).all())
    if simple:
        out = _regle_vect(X) if dec.mode == "regle" else np.full(len(ks), RESTER, np.int64)
        attentes = dec.attentes
        for k, r, a in zip(ks.tolist(), X.tolist(), out.tolist()):
            r.append(1.0)
            att = attentes.get(k)
            if att is None: att = attentes[k] = D.Attente()
            att.choix.append([r, a, 0, 0.0])
            if len(att.choix) > D.ATTENTE_MAX_HORIZONS * POINT_LOISIRS.horizon_j:
                del att.choix[0]; dec.abandonnes += 1
        dec.n_decisions += len(ks)
        e = getattr(dec, "enregistreur", None)
        if e is not None: e.decisions_lot(POINT_LOISIRS.nom, ks, np.column_stack([X, np.ones(len(ks))]), out)
    else:
        out = np.array([dec.decider(k, ContexteLoisirs(tuple(x))) for k, x in zip(ks.tolist(), X.tolist())], np.int64)
    p.col("menage", "cul_choix")[ks] = out.astype(np.int8)
    p.compter("decision_loisirs", float(len(ks)))
    return len(ks)


def _ajouter_tours(p, a, pl, idx, s, fenetre, act, rng_u):
    """Des tours ajoutes au plan de l agenda ( ses primitives : trajets, creneau libre, couvre-feu, reveils ).
    Rend les habitants qui l ont recu."""
    idx = idx[~pl.actif[idx, s]]
    if not len(idx): return idx
    T, mode, _, possible = AG._trajets(a, p.w, pl.dom[idx].astype(np.int32), pl.dom[idx].astype(np.int32))
    idx, T, mode, u = idx[possible], T[possible], mode[possible], rng_u[idx]
    t0, et, dmin, dd = fenetre
    arr = (t0 - AG.MINUTE_AUBE + u[:, 0] * et).astype(np.int32)
    duree = (dmin + u[:, 1] * dd).astype(np.int32)
    AG._tour_simple(pl, p.w, idx, s, arr, duree, T, mode, AG.DOMICILE, act)
    recu = idx[pl.actif[idx, s]]
    if len(recu): AG._relire(pl, recu.astype(np.int32), a.k)
    return recu


def _matin(p):
    d = _dom(p); w = p.w; tb = w.table; n = tb.n
    p.colonnes["habitant"].assurer(n); p.colonnes["menage"].assurer(tb.menages.n)
    a = p.domaine("agenda"); pl = a.plan
    d.fete_ids = d.panigyri_ids = d.culte_fete_ids = np.zeros(0, np.int64)
    d.panigyri_lieux = []; d.fete_du_jour = None
    if pl is None: return
    _nouveaux(p, d, n)
    patron, nationale = _calendrier_des_fetes(p, d, pl.jt.date)
    mg, viv, M = _menages_vivants(p)
    cout = _cout_jour(p, M, viv)
    _decider(p, d, mg, viv, M, cout)
    # --- la semaine choisie, appliquee au plan du jour
    N = pl.n
    col = p.colonnes["habitant"]
    mgp = mg[:N]
    choix = np.where(mgp >= 0, p.col("menage", "cul_choix")[np.maximum(mgp, 0)], -1)
    libre = ~pl.hors & ~pl.hopital & ~pl.rester
    reste = np.nonzero(choix == RESTER)[0]
    for s in (AG.T_LOISIR_JOUR, AG.T_LOISIR_SOIR): pl.actif[reste, s] = False
    u = p.du_jour("culture_tours").random((N, 8))
    age = tb.age[:N]
    if pl.jt.veille:
        fam = np.nonzero(libre & (choix == FETE) & (age >= POP.AGE_ECOLE))[0]
        _ajouter_tours(p, a, pl, fam, AG.T_LOISIR_SOIR, REPAS_FETE, AG.LOISIR, u[:, 0:2])
        d.fete_ids = fam[pl.actif[fam, AG.T_LOISIR_SOIR] & (pl.dest[fam, AG.T_LOISIR_SOIR] == AG.DOMICILE)].astype(np.int64)
    # --- les fetes : la liturgie des occasionnels, puis le panigyri du saint patron
    conf = col["cul_confession"][:N]; prat = col["agenda_pratiquant"][:N] == 1
    orth = libre & (conf == ORTHODOXE) & (age >= POP.AGE_ECOLE)
    deuil = np.where(mgp >= 0, p.jour - p.col("menage", "cul_deuil_j")[np.maximum(mgp, 0)] < DEUIL_COUTUME_J, False)
    culte = []
    if nationale is not None:
        cand = np.nonzero(orth & ~prat & (u[:, 2] < FETES_RELIGIEUSES[nationale]))[0]
        culte.append(_ajouter_tours(p, a, pl, cand, AG.T_CULTE, OFFICE_FETE, AG.CULTE, u[:, 3:5]))
        d.fete_du_jour = nationale
    if len(patron):
        chez = np.isin(pl.dom[:N].astype(np.int64), patron)
        cand = np.nonzero(chez & orth & (prat | (u[:, 2] < P_FETE_PATRONALE)))[0]
        culte.append(_ajouter_tours(p, a, pl, cand, AG.T_CULTE, OFFICE_FETE, AG.CULTE, u[:, 3:5]))
        va = np.nonzero(chez & libre & (age >= POP.AGE_ECOLE) & (choix != RESTER) & ~deuil & (u[:, 5] < P_PANIGYRI))[0]
        _ajouter_tours(p, a, pl, va, AG.T_LOISIR_SOIR, PANIGYRI_SOIR, AG.LOISIR, u[:, 6:8])
        d.panigyri_ids = va[pl.actif[va, AG.T_LOISIR_SOIR] & (pl.dest[va, AG.T_LOISIR_SOIR] == AG.DOMICILE)].astype(np.int64)
        d.panigyri_lieux = patron.tolist()
        if d.fete_du_jour is None: d.fete_du_jour = "fete_patronale"
    d.culte_fete_ids = np.unique(np.concatenate(culte)).astype(np.int64) if culte else np.zeros(0, np.int64)


# ================================================================== le soir ( 23 h 50 )
def _realises(pl, s):
    """Les habitants qui ont fait le tour `s` aujourd hui : arrives, et restes un moment."""
    T = pl.tt[:, s].astype(np.int32)
    return np.nonzero(pl.actif[:, s] & (T[:, AG.ARR] <= M_SOIR) & (T[:, AG.FIN] > T[:, AG.ARR]))[0]


def _deuils_poses(p, n):
    """( 03/10, HMT-194 3c ) Les deuils poses par un autre domaine dans w.deuils_poses ( [ ( habitants, part ) ] : la
    guerre y met les camarades d un soldat tue ) frappent le soir, comme ceux de la famille, bornes a DEUIL_MIN."""
    q = getattr(p.w, "deuils_poses", None)
    if not q: return
    de = p.colonnes["habitant"]["cul_deuil"]
    for ids, part in q:
        ids = np.asarray([int(i) for i in ids if 0 <= int(i) < n], np.int64)
        if len(ids): de[ids] = np.maximum(DEUIL_MIN, de[ids].astype(np.float64) + part).astype(np.float32)
    q.clear()


def _deuils(p, d, n, mg):
    """Les deces pas encore pleures : le menage du defunt et ses proches ( conjoint, parents, enfants ) sont frappes ;
    le menage paie les obseques a sa paroisse ( ce qu il peut )."""
    col = p.colonnes["habitant"]; tb = p.w.table
    _deuils_poses(p, n)                                  # ( 03/10, HMT-194 3c ) les camarades d un soldat tue
    morts = np.nonzero((col["deces_j"][:n] >= 0) & (col["cul_deuil_vu"][:n] == 0))[0]
    if not len(morts): return 0
    col["cul_deuil_vu"][morts] = 1
    vivant = (tb.vivant[:n] == 1)
    mg_m = tb.menage[morts].astype(np.int64)
    touche_m = np.isin(mg, mg_m[mg_m >= 0]) & vivant
    proches = set()
    for c in ("conjoint", "mere", "pere"):
        x = col[c][morts].astype(np.int64); proches.update(x[x >= 0].tolist())
    enfants = np.isin(col["mere"][:n], morts) | np.isin(col["pere"][:n], morts)
    touche_p = np.zeros(n, bool)
    if proches: touche_p[np.array(sorted(x for x in proches if x < n), np.int64)] = True
    touche_p = (touche_p | enfants) & vivant & ~touche_m
    de = col["cul_deuil"]
    de[:n] = np.where(touche_m, np.maximum(DEUIL_MIN, de[:n] + DEUIL_MENAGE), de[:n]).astype(np.float32)
    de[:n] = np.where(touche_p, np.maximum(DEUIL_MIN, de[:n] + DEUIL_PROCHE), de[:n]).astype(np.float32)
    ok = mg_m >= 0
    p.col("menage", "cul_deuil_j")[mg_m[ok]] = p.jour
    p.compter("deuil", float(len(morts)))
    for i, k in zip(morts.tolist(), mg_m.tolist()):
        c = int(col["cul_confession"][i])
        if k < 0 or c < 0 or c == SANS: continue
        par = _paroisse_de(d, int(tb.menages.domicile[k]), c)
        if par is None: continue
        x = _payer(p, d, _vue(tb, k), par, min(SERVICE_FUNEBRE_EUR / EUROS, max(0.0, float(tb.menages.caisse[k]))),
                   "service_religieux")
        par.services_total += x
        if x > 0: p.compter("service_religieux", x)
    return len(morts)


def _indice_paroisse(d, lieu, confession):
    x = _paroisse_de(d, lieu, confession)
    return x.indice if x is not None else -1


def _paroisse_de(d, lieu, confession):
    if lieu < 0: return None
    if confession == ORTHODOXE:
        k = d.paroisse_de[lieu]
        return d.paroisses[k] if k >= 0 else None
    k = d.communaute.get((d.ile_de[lieu], confession))
    return d.paroisses[k] if k is not None else None


def _payer_par_couple(p, d, mg_ids, cible, montant, objets, motif_de, reserve, caisse, sur_objet):
    """Les paiements du jour, un par couple ( menage, beneficiaire ), dans l ordre des numeros : chaque menage paie
    au plus ce que sa caisse a au-dela de sa reserve ; sa part est la meme pour tous ses beneficiaires. Rend le total
    paye et le paye par menage."""
    tb = p.w.table
    ok = (montant > 0) & (mg_ids >= 0) & (cible >= 0)
    if not ok.any(): return 0.0, {}
    mg_ids, cible, montant = mg_ids[ok], cible[ok], montant[ok]
    K = len(objets)
    cle = mg_ids * K + cible
    u, inv = np.unique(cle, return_inverse=True)
    somme = np.bincount(inv, weights=montant)
    hh, obj = u // K, u % K
    tot = np.bincount(np.searchsorted(np.unique(hh), hh), weights=somme)
    hu = np.unique(hh)
    dispo = np.maximum(0.0, caisse[hu] - reserve[hu])
    f = np.minimum(1.0, dispo / np.maximum(tot, 1e-12))
    fh = f[np.searchsorted(hu, hh)]
    total = 0.0; par_menage = {}
    vues = {}
    for k, j, x in zip(hh.tolist(), obj.tolist(), (somme * fh).tolist()):
        if x <= 1e-12: continue
        v = vues.get(k)
        if v is None: v = vues[k] = _vue(tb, k)
        o = objets[j]
        y = _payer(p, d, v, o, x, motif_de(o))
        sur_objet(o, y)
        total += y; par_menage[k] = par_menage.get(k, 0.0) + y
    return total, par_menage


def _encaisser_sortie(e, y):
    e.recettes_ttc += y; e.recettes_ht_mois += y / (1.0 + e.tva); e.tva_due += y * e.tva / (1.0 + e.tva)
    e.clients += 1


def _motif_etablissement(e): return "spectacle" if e.type in ("cinema", "theatre") else "sortie_cafe_taverne"


def _sorties(p, d, pl, mg, choix_m, caisse, cout, jours_loisir, jours_soir):
    """Les sorties realisees du jour, payees aux etablissements ; le panigyri, paye a la paroisse."""
    tb = p.w.table; N = pl.n
    u = p.du_jour("culture_depense").random((N, 2))
    age = tb.age[:N]
    enfant = np.where(age < 15, FACTEUR_ENFANT, 1.0)
    retraite = tb.role[:N] == PO.CODE_ROLE["retraite"]
    dom = pl.dom[:N].astype(np.int64)
    paniers = []   # ( habitants, etablissement, prix en euros )
    # le jour de repos : dejeuner a la taverne ou cafe
    j = jours_loisir
    tav = u[j, 0] < P_TAVERNE_MIDI
    paniers.append((j, np.where(tav, d.taverne_de[dom[j]], d.kafeneio_de[dom[j]]),
                    np.where(tav, PRIX_EUR["taverne"], PRIX_EUR["cafe"])))
    # le soir ( hors panigyri )
    s = jours_soir[~np.isin(jours_soir, d.panigyri_ids)]
    fete = np.isin(s, d.fete_ids)
    ville = pl.dest[s, AG.T_LOISIR_SOIR] == AG.MARCHE
    cafe_am = retraite[s] & (pl.tt[s, AG.T_LOISIR_SOIR, AG.ARR].astype(np.int32) < M_CAFE_FIN)
    c = d.marche_de[dom[s]]
    x = u[s, 1]
    et_v = np.where(x < P_CINEMA, d.cinema_de[c], np.where(x < P_CINEMA + P_THEATRE, d.theatre_de[c], d.taverne_de[c]))
    et_v = np.where(et_v >= 0, et_v, d.kafeneio_de[c])
    pr_v = np.where(x < P_CINEMA, PRIX_EUR["cinema"], np.where(x < P_CINEMA + P_THEATRE, PRIX_EUR["theatre"],
                                                                 PRIX_EUR["ville"]))
    tav = u[s, 0] < P_TAVERNE_SOIR
    et_l = np.where(fete | (~cafe_am & tav), d.taverne_de[dom[s]], d.kafeneio_de[dom[s]])
    pr_l = np.where(fete | (~cafe_am & tav), PRIX_EUR["taverne"], np.where(cafe_am, PRIX_EUR["cafe"], PRIX_EUR["cafe_soir"]))
    paniers.append((s, np.where(ville, et_v, et_l), np.where(ville, pr_v, pr_l)))
    ids = np.concatenate([q[0] for q in paniers]).astype(np.int64)
    et = np.concatenate([q[1] for q in paniers]).astype(np.int64)
    pr = np.concatenate([q[2] for q in paniers]) * enfant[ids] / EUROS
    mgs = mg[ids]
    ch = np.where(mgs >= 0, choix_m[np.maximum(mgs, 0)], -1)
    pr = np.where(ch == ECONOMISER, 0.0, pr)
    reserve = np.maximum(np.where(choix_m == FETE, RESERVE_FETE_J, RESERVE_SORTIE_J) * cout, _plancher(p, cout))   # HMT-126 e
    tot, par_m = _payer_par_couple(p, d, mgs, et, pr, d.etablissements, _motif_etablissement, reserve, caisse,
                                   _encaisser_sortie)
    payes = ids[np.isin(mgs, np.fromiter(par_m, np.int64, len(par_m)))] if par_m else np.zeros(0, np.int64)
    if tot > 0: p.compter("sortie_payee", tot)
    # le panigyri
    pani = 0.0
    if len(d.panigyri_ids):
        vi = d.panigyri_ids[np.isin(d.panigyri_ids, jours_soir)]
        mgv = mg[vi]
        ch = np.where(mgv >= 0, choix_m[np.maximum(mgv, 0)], -1)
        prix = np.where(ch == ECONOMISER, 0.0, PRIX_EUR["panigyri"] * enfant[vi] / EUROS)
        par = np.array([d.paroisse_de[l] for l in dom[vi].tolist()], np.int64)
        recu = collections.defaultdict(float)
        def _pani(o, y): recu[o.indice] += y; o.panigyri_total += y
        pani, _ = _payer_par_couple(p, d, mgv, par, prix, d.paroisses, _motif_panigyri,
                                    np.maximum(RESERVE_DON_J * cout, _plancher(p, cout)), caisse, _pani)
        for l in d.panigyri_lieux:
            x = d.paroisses[int(d.paroisse_de[l])]
            r = recu.get(x.indice, 0.0)
            _depenser_panigyri(p, d, x, r)
            p.noter("panigyri", lieu=d.lieu_ids[l], saint=x.saint, participants=int((dom[vi] == l).sum()),
                    recettes=round(r, 2))
    return tot + pani, par_m, payes


def _motif_panigyri(o): return "panigyri"


def _motif_don(o): return "don_religieux"


def _depenser_panigyri(p, d, x, r):
    """La paroisse paie ses musiciens et ses fournisseurs sur la recette du panigyri."""
    if r <= 0: return
    tb = p.w.table
    dis = p.col("menage", "dissous")
    mus = [k for k in d.musiciens.get(x.ile, []) if not dis[k]]
    if mus:
        part = PART_MUSIQUE * r / len(mus)
        for k in mus: _payer(p, d, x, _vue(tb, k), part, "cachet_musiciens")
    marche = p.w.marches[p.w.carte.par_n[int(d.marche_de[x.lieu])].id]
    x.sortie_total += _payer(p, d, x, marche, PART_PANIGYRI_INTRANTS * r, "approvisionnement_loisirs")


def _dons(p, d, pl, mg, choix_m, caisse, cout, culte_ids):
    """Les adultes a l office donnent a leur paroisse ( ou a leur communaute ) ; un menage qui economise ne donne rien."""
    tb = p.w.table; col = p.colonnes["habitant"]
    ids = culte_ids[tb.age[culte_ids] >= POP.AGE_MAJEUR]
    if not len(ids): return 0.0
    mgs = mg[ids]
    ch = np.where(mgs >= 0, choix_m[np.maximum(mgs, 0)], -1)
    fete = d.fete_du_jour is not None
    don = np.where(ch == ECONOMISER, 0.0, (DON_FETE_EUR if fete else DON_CULTE_EUR) / EUROS)
    conf = col["cul_confession"][ids].astype(np.int64)
    dom = pl.dom[ids].astype(np.int64)
    par = np.array([_indice_paroisse(d, l, c) for l, c in zip(dom.tolist(), conf.tolist())], np.int64)
    def _don(o, y): o.dons_mois += y; o.dons_total += y
    tot, par_m = _payer_par_couple(p, d, mgs, par, don, d.paroisses, _motif_don,
                                   np.maximum(RESERVE_DON_J * cout, _plancher(p, cout)), caisse, _don)
    cd = p.col("menage", "cul_dons")
    for k, y in par_m.items(): cd[k] += y
    if tot > 0: p.compter("don_religieux", tot)
    return tot


def _cotisations(p, d, mg, caisse, cout):
    tb = p.w.table; n = tb.n
    club = p.col("habitant", "cul_club")[:n]
    ids = np.nonzero((club >= 0) & (tb.vivant[:n] == 1) & (np.arange(n) % MOIS_J == p.jour % MOIS_J))[0]
    if not len(ids): return 0.0
    def _cot(o, y): o.cotisations_mois += y; o.cotisations_total += y
    tot, _ = _payer_par_couple(p, d, mg[ids], club[ids].astype(np.int64), np.full(len(ids), COTISATION_EUR / EUROS),
                               d.associations, _motif_cotisation, np.maximum(RESERVE_COTISATION_J * cout, _plancher(p, cout)),
                               caisse, _cot)
    if tot > 0: p.compter("cotisation_club", tot)
    return tot


def _motif_cotisation(o): return "cotisation_club"


def _marche_du(p, d, lieu):
    return p.w.marches[p.w.carte.par_n[int(d.marche_de[lieu])].id]


def _proprietaire_vivant(p, d, k, lieu, viv):
    """Le menage proprietaire s il vit encore ; sinon un menage habite du meme lieu reprend l affaire."""
    if 0 <= k < len(viv) and viv[k] > 0 and not p.col("menage", "dissous")[k]: return k
    tb = p.w.table; M = len(viv)
    c = np.nonzero((viv > 0) & (p.col("menage", "dissous")[:M] == 0) & (tb.menages.domicile[:M] == lieu))[0]
    return int(c[0]) if len(c) else -1


def _solder(p, d, viv):
    """Le jour de chacun ( son numero modulo 30 ) : etablissements, clubs et paroisses reglent leur mois. La TVA des
    etablissements est reversee chaque soir."""
    w = p.w; tb = w.table; L = p.socle.livre
    for e in d.etablissements:
        if e.tva_due > 1e-12:
            x = _payer(p, d, e, w.gouv, e.tva_due, "tva")
            w.tva_percue += x; e.tva_due -= x; e.tva_versee += x
        if e.indice % MOIS_J != p.jour % MOIS_J: continue
        ht = e.recettes_ht_mois; e.recettes_ht_mois = 0.0
        _, p_int, p_ext, p_cach = TYPES_ETABLISSEMENT[e.type]
        e.verse_marche += _payer(p, d, e, _marche_du(p, d, e.lieu), p_int * ht, "approvisionnement_loisirs")
        if p_ext > 0:
            from . import d07_exterieur as EX
            x = EX.payer_en_devises(p, e, p_ext * ht, "droits_films"); d.compte["droits_films"] += x; e.verse_exterieur += x
        art = [k for k in e.artistes if 0 <= k < len(viv) and viv[k] > 0]
        if p_cach > 0 and art:
            for k in art: e.cachets += _payer(p, d, e, _vue(tb, k), p_cach * ht / len(art), "cachet_artistes")
        e.proprietaire = _proprietaire_vivant(p, d, e.proprietaire, e.lieu, viv)
        exces = e.caisse - e.tva_due - FONDS_ROULEMENT_MOIS * ht
        if exces > 0 and e.proprietaire >= 0:
            e.verse_proprietaire += _payer(p, d, e, _vue(tb, e.proprietaire), exces, "revenu_exploitant_loisirs")
    for a in d.associations:
        if a.indice % MOIS_J != p.jour % MOIS_J: continue
        c = a.cotisations_mois; a.cotisations_mois = 0.0
        a.entraineur = _proprietaire_vivant(p, d, a.entraineur, a.lieu, viv)
        if a.entraineur >= 0: a.verse_total += _payer(p, d, a, _vue(tb, a.entraineur), PART_ENTRAINEUR * c, "salaire_club")
        ent = PART_ENTRETIEN * c + max(0.0, a.caisse - PART_ENTRETIEN * c - RESERVE_CLUB_MOIS * c)
        a.verse_total += _payer(p, d, a, _marche_du(p, d, a.lieu), min(ent, a.caisse), "entretien_equipements")
    for x in d.paroisses:
        if x.indice % MOIS_J != p.jour % MOIS_J: continue
        dm = x.dons_mois; x.dons_mois = 0.0
        f = PART_FOURNITURES * dm + max(0.0, x.caisse - PART_FOURNITURES * dm - RESERVE_PAROISSE_MOIS * dm)
        x.sortie_total += _payer(p, d, x, _marche_du(p, d, x.lieu), min(f, x.caisse), "fournitures_culte")


def _entraide(p, d, viv, cout, caisse):
    """Le dimanche soir : chaque paroisse orthodoxe donne une semaine de nourriture aux menages de son lieu qui ont eu
    faim cette semaine ou dont la caisse ne paie plus trois jours ( le pretre et les voisins le savent ), sur la moitie
    de sa caisse au plus."""
    tb = p.w.table; M = len(viv)
    f7 = p.col("menage", "faim7")[:M].astype(np.int64) & 0x7F
    dis = p.col("menage", "dissous")[:M]
    besoin = (viv > 0) & (dis == 0) & ((f7 != 0) | (caisse < JOURS_PAUVRE * cout))
    dom = tb.menages.domicile[:M].astype(np.int64)
    ks = np.nonzero(besoin & (dom >= 0))[0]
    if not len(ks): return 0.0
    o, deb = _grouper(dom[ks], d.L)
    tot = 0.0
    for x in d.paroisses:
        if x.confession != ORTHODOXE or x.caisse <= 1e-9: continue
        qui = ks[o[deb[x.lieu]:deb[x.lieu + 1]]]
        if not len(qui): continue
        budget = PART_AIDE * x.caisse
        part = budget / len(qui)
        for k in np.sort(qui).tolist():
            y = _payer(p, d, x, _vue(tb, k), min(AIDE_JOURS * float(cout[k]), part), "aide_paroissiale")
            x.aide_total += y; tot += y
    if tot > 0: p.compter("aide_paroissiale", tot)
    return tot


def _climat(p, d):
    """Ce que chaque lieu habite croit de mauvais et de bon ( domaine 22 ) : somme de part x saillance x valence."""
    neg = np.zeros(d.L); pos = np.zeros(d.L)
    for l in np.nonzero(d.habitable)[0].tolist():
        for sujet, (i, v) in ME.climat(p, int(l)).items():
            if v < 0: neg[l] += i * -v
            elif v > 0: pos[l] += i * v
    d.climat_neg, d.climat_pos = neg, pos


def _au_front(p, n):
    """( 03/10, HMT-194 3c ) Les habitants au front de la guerre d Arma ( w.absents, destination « front » ) : ils
    passent dans la passe du moral comme des residents. Les autres absents n y passent pas."""
    out = np.zeros(n, bool)
    if not MORAL_AU_FRONT: return out
    for i, a in getattr(p.w, "absents", {}).items():
        if 0 <= int(i) < n and isinstance(a, dict) and a.get("destination") == "front": out[int(i)] = True
    return out


def _moral_du_jour(p, d, n, mg, viv, cout, caisse, sortie, chocs):
    """La passe du moral : les causes durables ( faim, chomage, pauvrete, maladie, depression, croyances, liens,
    pratique ) tirent la part lente vers elles ; le deuil et la fete s eteignent ; le moral est leur somme bornee."""
    col = p.colonnes["habitant"]; tb = p.w.table
    v = np.nonzero((tb.vivant[:n] == 1) & ((tb.statut[:n] != PO.ABSENT) | _au_front(p, n))     # ( HMT-194 3c ) le front
                   & (col["cul_base"][:n] >= 0))[0]
    s7 = col["cul_sorties7"]
    s7[:n] = (((s7[:n].astype(np.int64) << 1) | sortie[:n]) & 0x7F).astype(np.uint8)
    if not len(v): return
    k = mg[v]; km = np.maximum(k, 0)
    M = len(viv)
    f7 = np.where(k >= 0, POPCOUNT[p.col("menage", "faim7")[:M].astype(np.int64)[km] & 0x7F], 0) / 7.0
    age = tb.age[v]
    role = tb.role[v]
    actif = ((role != PO.CODE_ROLE["enfant"]) & (role != PO.CODE_ROLE["retraite"]) & (age >= C.AGE_TRAVAIL)
             & (age < C.AGE_RETRAITE))
    chom = actif & (tb.travail[v] < 0)
    pauvre = (k >= 0) & (caisse[km] < JOURS_PAUVRE * cout[km])
    malade = tb.etat[v] == PO.CODE_ETAT["I"]
    dep = np.zeros(len(v), bool)
    if "med_mental" in p.colonnes["habitant"]: dep = (col["med_mental"][v] & 1) > 0
    dom = tb.domicile[v].astype(np.int64); dm = np.maximum(dom, 0)
    neg = np.where(dom >= 0, np.minimum(1.0, d.climat_neg[dm]), 0.0)
    pos = np.where(dom >= 0, np.minimum(1.0, d.climat_pos[dm]), 0.0)
    liens = np.where(age >= POP.AGE_ECOLE,
                     np.minimum(1.0, POPCOUNT[s7[v].astype(np.int64)] / LIENS_PLEINS) - LIENS_REF, 0.0)
    prat = col["agenda_pratiquant"][v] == 1
    cible = (-K_FAIM_SEMAINE * f7 - K_FAIM_CORPS * np.minimum(1.0, tb.faim[v] / FAIM_PLEINE) - K_CHOMAGE * chom
             - K_PAUVRE * pauvre - K_MALADE * malade - K_DEPRESSION * dep - K_MEDIAS_NEG * neg + K_MEDIAS_POS * pos
             + K_LIENS * liens + K_CULTE * prat)
    lent = col["cul_lent"][v].astype(np.float64)
    col["cul_lent"][v] = (lent + (cible - lent) / TAU_J).astype(np.float32)
    col["cul_deuil"][v] = (col["cul_deuil"][v].astype(np.float64) * 0.5 ** (1.0 / DEMI_VIE_DEUIL_J)).astype(np.float32)
    fe = col["cul_fete"][v].astype(np.float64) * 0.5 ** (1.0 / DEMI_VIE_FETE_J) + chocs[v]
    col["cul_fete"][v] = np.minimum(FETE_MAX, fe).astype(np.float32)
    col["cul_moral"][v] = _composer(col["cul_base"][v], col["cul_lent"][v], col["cul_deuil"][v], col["cul_fete"][v])


def _moral_des_lieux(p, d, n):
    """Le moral collectif de chaque lieu : la moyenne exacte de ses residents vivants."""
    tb = p.w.table; col = p.colonnes["habitant"]
    v = (tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & (tb.domicile[:n] >= 0) & (col["cul_base"][:n] >= 0)
    dom = tb.domicile[:n][v].astype(np.int64)
    cnt = np.bincount(dom, minlength=d.L)[:d.L]
    som = np.bincount(dom, weights=col["cul_moral"][:n][v].astype(np.float64), minlength=d.L)[:d.L]
    return np.where(cnt > 0, som / np.maximum(cnt, 1), 0.0), cnt


def _noter(p, d, mg, viv, M):
    """Chaque menage qui attend la note de sa semaine recoit celle du jour : ( moral moyen + a mange ) / 2."""
    dec = d.decideur
    cles = [k for k, att in dec.attentes.items() if att.choix]
    if cles:
        tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
        v = (tb.vivant[:n] == 1) & (mg >= 0)
        som = np.bincount(mg[v], weights=col["cul_moral"][:n][v].astype(np.float64), minlength=M)[:M]
        cl = np.array(cles, np.int64)
        nou = AG._nourris(p.w.nourri_menage, cl)
        vk = viv[np.minimum(cl, M - 1)] if M else np.zeros(len(cl))
        r = np.where((cl < M) & (vk > 0), 0.5 * som[np.minimum(cl, M - 1)] / np.maximum(1, vk) + 0.5 * nou, 0.0)
        for c, x in zip(cles, r.tolist()): dec.noter(c, x, p.jour)
    for c in [c for c, att in dec.attentes.items() if not att.choix]: del dec.attentes[c]


def _soir(p):
    d = _dom(p); w = p.w; tb = w.table; n = tb.n
    p.colonnes["habitant"].assurer(n); p.colonnes["menage"].assurer(tb.menages.n)
    col = p.colonnes["habitant"]
    mg, viv, M = _menages_vivants(p)
    cout = _cout_jour(p, M, viv)
    a = p.domaine("agenda"); pl = a.plan
    nb_deuils = _deuils(p, d, n, mg)
    caisse = tb.menages.caisse[:M]            # une vue : les paiements s y lisent au fil de l eau
    choix_m = p.col("menage", "cul_choix")[:M]
    sortie = np.zeros(n, np.int64); chocs = np.zeros(n)
    stats = {"jour": p.jour, "depense": 0.0, "dons": 0.0, "aide": 0.0, "culte_adultes": 0, "loisir": 0,
             "panigyri": 0, "fete": d.fete_du_jour, "deuils": nb_deuils}
    if pl is not None and pl.n > 0:
        N = pl.n
        c_ids = _realises(pl, AG.T_CULTE)
        j_ids = _realises(pl, AG.T_LOISIR_JOUR)
        s_ids = _realises(pl, AG.T_LOISIR_SOIR)
        for x in (c_ids, j_ids, s_ids): sortie[x] = 1
        dep, par_m, payes = _sorties(p, d, pl, mg, choix_m, caisse, cout, j_ids, s_ids)
        cdep = p.col("menage", "cul_depense")
        for k, y in par_m.items(): cdep[k] += y
        dons = _dons(p, d, pl, mg, choix_m, caisse, cout, c_ids)
        chocs[payes] += PLAISIR_SORTIE
        fe = d.fete_ids[np.isin(d.fete_ids, s_ids)]; chocs[fe] += FETE_SORTIE
        pa = d.panigyri_ids[np.isin(d.panigyri_ids, s_ids)]; chocs[pa] += FETE_PANIGYRI
        if d.fete_du_jour is not None:
            cf = c_ids[col["cul_confession"][c_ids] == ORTHODOXE]; chocs[cf] += FETE_RELIGIEUSE
            if d.fete_du_jour != "fete_patronale" or len(cf):
                p.noter("fete_religieuse", fete=d.fete_du_jour, fideles=int(len(cf)))
        adultes = (tb.vivant[:N] == 1) & (tb.age[:N] >= POP.AGE_MAJEUR)
        stats.update(depense=dep, dons=dons, culte_adultes=int(adultes[c_ids].sum()), adultes=int(adultes.sum()),
                     loisir=int(len(j_ids) + len(s_ids)), panigyri=int(len(pa)), semaine=int(pl.jt.semaine))
        if pl.jt.semaine == 6: stats["aide"] = _entraide(p, d, viv, cout, caisse)
    stats["cotisations"] = _cotisations(p, d, mg, caisse, cout)
    _solder(p, d, viv)
    _climat(p, d)
    _moral_du_jour(p, d, n, mg, viv, cout, caisse, sortie, chocs)
    d.moral_lieu, d.residents_lieu = _moral_des_lieux(p, d, n)
    d.historique.append(d.moral_lieu.copy())
    _noter(p, d, mg, viv, M)
    v = (tb.vivant[:n] == 1) & (col["cul_base"][:n] >= 0)
    stats["moral"] = float(col["cul_moral"][:n][v].astype(np.float64).mean()) if v.any() else 0.0
    d.depense_jour = stats["depense"]
    d.serie.append(stats)


def _cloture(p, comptes):
    """Le grand livre du jour, pour le recoupement au centime des motifs du domaine."""
    d = _dom(p)
    noms = {m for m, _ in MOTIFS}
    for mo, pa, re, s, _ in comptes["argent"]:
        if mo in noms: d.livre_motifs[mo] += s
        elif mo == "tva" and pa == "Etablissement": d.livre_motifs["tva"] += s


# ================================================================== ce que le domaine donne aux autres
def _cellule(d, x):
    if isinstance(x, (int, np.integer)): return int(x)
    return d.n_du_lieu[x]


def moral(p, ids):
    """Le moral individuel ( 0 a 1 ) d habitants, par leurs numeros."""
    return p.col("habitant", "cul_moral")[np.asarray(ids, np.int64)].astype(np.float64)


def moral_collectif(p, lieu_ou_ids):
    """Le moral collectif : d un lieu ( identifiant ou numero ; la moyenne de ses residents au dernier soir ), ou d un
    groupe donne par les numeros de ses membres ( une unite, un parti, un camp : la moyenne de ses vivants )."""
    d = _dom(p)
    if isinstance(lieu_ou_ids, (str, int, np.integer)): return float(d.moral_lieu[_cellule(d, lieu_ou_ids)])
    ids = np.asarray(lieu_ou_ids, np.int64)
    ids = ids[p.w.table.vivant[ids] == 1]
    return float(moral(p, ids).mean()) if len(ids) else 0.0


def moral_des_lieux(p):
    """{ lieu : ( moral collectif, residents, tendance sur 7 soirs ) } pour les lieux habites."""
    d = _dom(p)
    h = d.historique
    tend = d.moral_lieu - h[0] if len(h) >= 2 else np.zeros(d.L)
    return {d.lieu_ids[l]: (float(d.moral_lieu[l]), int(d.residents_lieu[l]), float(tend[l]))
            for l in np.nonzero(d.habitable)[0].tolist()}


def facteur_productivite(p, ids):
    """Domaine 4 : le facteur de productivite horaire que le moral donne ( 1 au moral de reference )."""
    lo, hi = BORNES_PRODUCTIVITE
    return np.clip(1.0 + ELAST_PRODUCTIVITE * (moral(p, ids) - MORAL_REF), lo, hi)


def risque_greve(p, lieu):
    """Domaine 4 : le risque relatif d une greve dans ce lieu, selon son moral collectif ( 1 a la reference )."""
    return float(np.clip(math.exp(K_GREVE * (MORAL_REF - moral_collectif(p, lieu))), 0.5, 3.0))


def facteur_desobeissance(p, ids):
    """Domaines 5 ( quarantaine ), 21 ( fraude ) : le facteur de la propension a desobeir ( 1 a la reference )."""
    return np.clip(1.0 + K_DESOBEISSANCE * (MORAL_REF - moral(p, ids)), 0.5, 2.0)


def risque_relatif_mental(p, ids):
    """Domaine 16 : le risque relatif d un episode depressif ou anxieux, selon le moral ( 1 a la reference )."""
    return np.clip(np.exp(K_MENTAL * (MORAL_REF - moral(p, ids))), 0.5, 3.0)


def discipline(p, ids):
    """Domaines 25 a 27 : le moral d une unite ( les numeros de ses membres ) et sa discipline dans [0 ; 1] : le moral
    moyen, moins la part de ses membres au moral bas ( ceux qui decrochent entrainent les autres ; a calibrer )."""
    ids = np.asarray(ids, np.int64)
    ids = ids[p.w.table.vivant[ids] == 1]
    if not len(ids): return {"moral": 0.0, "part_bas": 0.0, "discipline": 0.0, "n": 0}
    m = moral(p, ids)
    bas = float((m < MORAL_BAS).mean())
    return {"moral": float(m.mean()), "part_bas": bas,
            "discipline": float(np.clip(0.5 + 1.5 * (m.mean() - MORAL_REF) - 0.5 * bas, 0.0, 1.0)), "n": int(len(ids))}


def humeur_politique(p, lieu):
    """Domaine 24 : ce qui fera l opinion d un lieu - son moral collectif et sa tendance, la part de ses residents au
    moral bas, et ce qu il croit de mauvais sur des sujets qui touchent le gouvernement ( croyances, domaine 22 )."""
    d = _dom(p); l = _cellule(d, lieu)
    tb = p.w.table; n = tb.n
    res = np.nonzero((tb.vivant[:n] == 1) & (tb.domicile[:n] == l))[0]
    m = moral(p, res)
    table = p.domaine("medias").table_sujets
    gouv = sum(i * -v for s, (i, v) in ME.climat(p, l).items() if v < 0 and table[s][1])
    h = d.historique
    return {"moral": float(d.moral_lieu[l]), "tendance_7j": float(d.moral_lieu[l] - h[0][l]) if len(h) >= 2 else 0.0,
            "part_bas": float((m < MORAL_BAS).mean()) if len(m) else 0.0, "griefs_gouvernement": float(gouv)}


def confession(p, ids):
    """Les confessions ( noms ) d habitants."""
    c = p.col("habitant", "cul_confession")[np.asarray(ids, np.int64)]
    return [CONFESSIONS[x] if x >= 0 else None for x in c.tolist()]


def etablissements(p, lieu):
    """Les lieux de la vie sociale d un lieu habite, reels : { eglise, kafeneio, taverne, cinema, theatre, club }."""
    d = _dom(p); l = _cellule(d, lieu)
    out = {}
    if d.paroisse_de[l] >= 0: out["eglise"] = d.paroisses[d.paroisse_de[l]].nom
    for nom, t in (("kafeneio", d.kafeneio_de), ("taverne", d.taverne_de), ("cinema", d.cinema_de),
                   ("theatre", d.theatre_de), ("club", d.club_de)):
        if t[l] >= 0: out[nom] = int(t[l])
    return out


def depense_du_jour(p):
    """Domaine 3 : ce que les menages ont paye aujourd hui en sorties ( cafes, tavernes, spectacles, panigyri ) : la
    part servie des divisions COICOP 09 et 11."""
    return _dom(p).depense_jour


# ================================================================== controles ( pour les portes )
def anomalies(p):
    """Les incoherences : un moral qui n est pas la somme de ses parts ( ecrit hors de ses causes ), un moral de lieu
    qui n est pas la moyenne de ses residents, un pratiquant sans religion, une part hors bornes."""
    d = _dom(p); tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
    out = []
    v = np.nonzero((tb.vivant[:n] == 1) & (col["cul_base"][:n] >= 0))[0]
    attendu = _composer(col["cul_base"][v], col["cul_lent"][v], col["cul_deuil"][v], col["cul_fete"][v])
    for i in v[col["cul_moral"][v] != attendu].tolist(): out.append(("moral_hors_causes", i))
    for i in v[(col["cul_moral"][v] < 0) | (col["cul_moral"][v] > 1)].tolist(): out.append(("moral_hors_bornes", i))
    ml, _ = _moral_des_lieux(p, d, n)
    for l in np.nonzero(np.abs(ml - d.moral_lieu) > 1e-12)[0].tolist(): out.append(("moral_de_lieu", d.lieu_ids[l]))
    pr = (col["agenda_pratiquant"][:n] == 1) & (col["cul_confession"][:n] == SANS) & (tb.vivant[:n] == 1)
    for i in np.nonzero(pr)[0].tolist(): out.append(("pratiquant_sans_religion", i))
    return out


def scenario_loisirs(jours=21, mode="hasard", graine=7, echelle=5):
    """La porte de decision : un pays ordinaire, chaque menage decide sa semaine dans le mode demande."""
    from . import essais as T
    w, p = T.monde([DOMAINE], graine, echelle, modes={"loisirs": mode})
    T.jours(w, jours)
    return _dom(p).decideur, (w, p)
