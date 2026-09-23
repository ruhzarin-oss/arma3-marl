"""DOMAINE 2 - MONNAIE, BANQUES, FINANCE.

FICHE
1. Classes. Banque ( une banque commerciale : caisse propre, reserves a la banque centrale, refinancement, titres,
   fonds propres ), BanqueCentrale ( taux directeur, reserves obligatoires, refinancement, avances au Tresor, avoirs
   exterieurs, indice des prix ), Pret ( credit amortissable a mensualites constantes : impayes, retard, defaut,
   provision ), Titre ( bon du Tresor a escompte ), IndicePrix ( l indice des prix a la consommation que la banque
   centrale calcule sur les prix AFFICHES des marches ), SuiviEntreprise ( ce que la banque voit du compte d une
   entreprise ), Demande et ContexteOctroi ( une demande de credit, et ce que la banque en voit ), Banques ( l etat du
   domaine ). Par menage, en colonnes : banque, revenu, revenu_n, incidents, demande_j. Entreprises et marches : table
   eparse `comptes` ( detenteur -> banque ). Aucune classe du moteur n est touchee.
   Pret n est pas une creance du socle : une creance se regle par TRANSFERT ( Creances.regler ), le principal d un pret
   se regle par DESTRUCTION de monnaie. Un pret radie, lui, devient une creance du socle ( motif recouvrement_pret ),
   que le domaine 21 pourra recouvrer.
2. Invariants. DEUX MONNAIES, DEUX CONTROLES.
   - La monnaie des detenteurs ( toutes les caisses du registre ) se conserve dans le socle. Elle ne nait que par
     `emettre` ( credit, avance de la banque centrale au Tresor, souscription d un titre ) et ne meurt que par
     `detruire_monnaie` ( principal rembourse, avance ou titre rembourse ), toujours sous un motif du domaine :
     M = depart + credits - principal rembourse + titres souscrits - titres rembourses + avances nettes + exterieur.
   - La monnaie centrale ( reserves des banques + comptes a la banque centrale : Tresor, banque centrale, familles sans
     banque ) n entre que par l exterieur, le refinancement, les avances au Tresor et la remuneration des reserves.
   Chaque detenteur appartient a UN cercle : celui de sa banque ( ses clients et la caisse propre de la banque ), ou
   celui de la banque centrale. Reglement interbancaire du soir : la variation d un cercle, moins la monnaie que sa
   banque y a creee ( prets ), plus celle qu elle y a detruite ( principal ), est ce que les autres cercles lui ont
   paye ; ses reserves bougent d autant. Un parcours des caisses par jour, exact ( math.fsum ).
   Bilans verifies chaque soir, chaque poste tenu a part : banque : reserves + prets - provisions + titres = depots +
   refinancement + fonds propres ( fonds propres = fonds propres d emetteur + caisse propre ) ; banque centrale :
   avoirs de depart + exterieur net + refinancements + avances = reserves + cercle de la banque centrale + fonds propres.
   Le domaine detient de l argent ( caisses des banques et de la banque centrale : familles `banques` et
   `banque_centrale` du registre ), aucun bien.
3. Decision `octroi_credit` ( une par demande, les jours ouvres a 9 h ) : refuser, accorder la moitie, accorder.
   Traits : capacite ( flux libre du compte sur la mensualite ), solde, endettement et incidents ( fichier Tiresias ),
   taille, entreprise, taux propose, montant. Jamais la probabilite vraie de defaut. Note : ce que CE pret rapporte a
   la banque sur 30 jours ( interets encaisses moins dotations aux provisions ), en rendement annuel du montant demande ;
   0 pour un refus. Horizon 30 jours : le maximum du socle ; la premiere mensualite tombe au 30e jour. Regle : un score
   a seuil ( accorder ce que le flux libre rembourse ). Temoin : tout accorder.
4. Evenements. Individuels : defaut_de_paiement, radiation, decision_taux, avance_etat, titre_souscrit. Comptes :
   demande_credit, pret_accorde, pret_refuse, refus_reglementaire, mensualite_echue, mensualite_impayee, pret_solde,
   refinancement, depense_exceptionnelle, depense_renoncee.
5. Liens. Lit la population ( dissous, age ), les prix affiches et la TVA ( moteur E1 ), la paie ( 18 h ). Paie et
   recoit : interets ( menages, entreprises -> banques ), dividendes ( banques -> menages actionnaires ), interets des
   depots, avances et benefice de la banque centrale ( Tresor ), coupons des titres, depense exceptionnelle
   ( menage -> marche ). Donne aux autres ( API en fin de fichier ) : banque_de, ouvrir_compte, demander_credit,
   preter, rembourser_par_anticipation, dette_de, taux_directeur, fixer_taux_directeur, taux_credit, indice_des_prix,
   inflation, avance_a_l_etat, rembourser_avance, souscrire_titre, bilan, bilan_bc, masse_monetaire. Ne remplace aucune
   methode du moteur ; couvre chaque soir un decouvert du Tresor par une avance de la banque centrale.
6. Portes : tests_d02_banques.py.
7. Arma : aucun objet ( une agence bancaire serait un batiment, domaine 13 ).
8. Cout : trois parcours vectorises des caisses des menages par jour ( 17 h 50, 18 h, 23 h 50 ), un de plus a 9 h
   pour trouver les demandeurs ; le reste suit le nombre de prets, de demandes et d entreprises, pas la population."""
import math
from collections import deque
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, registre as R, echeancier as E

JOURS_AN = 365.0
MOIS_J = 30                        # un mois bancaire : une mensualite tous les 30 jours du monde
PAS_MOIS = MOIS_J * C.PAS_PAR_JOUR
EPS = 1e-9                         # drachmes : en dessous, un reste est de l arrondi

# ================================================================== les banques commerciales
# Quatre banques, comme les quatre banques systemiques grecques ( ~95 % des depots ) ; noms fictifs, parts de depots
# de l ordre de celles de 2024 ( Banque de Grece, a calibrer ).
BANQUES = (("Banque Nationale", 0.30), ("Banque du Commerce", 0.28), ("Banque Agricole", 0.22), ("Caisse d Epargne", 0.20))
FONDS_PROPRES_INITIAUX = 0.10      # fonds propres de depart, en part des depots ( banques grecques ~ 10 % du bilan en 2024, a calibrer )
DIVIDENDE_PART = 0.5               # part de la caisse propre versee chaque mois ( politique ~ 50 % des banques grecques en 2024, a calibrer )
TAUX_DEPOTS_VUE = 0.0005           # depots a vue des menages grecs : 0,02 a 0,05 % en 2024 ( Banque de Grece ) : borne haute
RATIO_FONDS_PROPRES_MIN = 0.105    # Bale III : 8 % + coussin de conservation 2,5 % ( CRR art. 92, CRD art. 129 )

# ================================================================== la banque centrale
TAUX_DIRECTEUR_0 = 0.0215          # taux des operations principales de refinancement de la BCE depuis le 11 juin 2025
ECART_FACILITE_DEPOT = 0.0015      # facilite de depot = taux directeur - 15 points de base ( BCE, depuis septembre 2024 )
RATIO_RESERVES = 0.01              # reserves obligatoires : 1 % des depots ( BCE, depuis janvier 2012 ), remunerees a 0 %
REUNION_J = 42                     # la BCE se reunit toutes les six semaines
PI_CIBLE = 0.02                    # cible d inflation de la BCE
R_NEUTRE = 0.005                   # taux reel neutre ( estimations BCE : 0 a 1 %, a calibrer )
PHI_PI = 0.5                       # regle de Taylor ( 1993 )
PAS_TAUX_MAX = 0.005               # au plus 50 points de base par reunion
TAUX_MAX = 0.25
AVANCE_AUTOMATIQUE = True          # un decouvert du Tresor en fin de journee devient une avance de la banque centrale
# Poids de l indice : les quatre biens que les menages du moteur E1 achetent, dans l ordre de grandeur de l IPCH grec
# ( ELSTAT : alimentation ~ 20 %, carburants ~ 4 %, produits de sante ~ 3,5 % du panier ) ramene a ces quatre biens ( a calibrer ).
POIDS_INDICE = {"nourriture": 0.70, "carburant": 0.15, "remedes": 0.10, "outils": 0.05}
INDICE_MEMOIRE_J = 800

# ================================================================== les prets
# type : ( marge sur le taux directeur, duree en mois, perte en cas de defaut, ponderation de risque Bale III standard )
# Taux obtenus ( taux directeur 2,15 % ) : consommation 10,15 %, immobilier 3,95 %, entreprises 5,65 % - Banque de
# Grece, taux des nouveaux prets 2024 : consommation 10-12 %, immobilier ~ 4 %, entreprises 5-6 %.
# Perte en cas de defaut : 45 % ( Bale, approche NI fondation, creance senior non garantie ) ; 25 % pour l immobilier
# ( recouvrements grecs lents, a calibrer ).
TYPES = {"conso": (0.080, 36, 0.45, 0.75), "immo": (0.018, 300, 0.25, 0.35), "entreprise": (0.035, 12, 0.45, 1.00)}
# Part de la perte en cas de defaut provisionnee, par stade ( IFRS 9 simplifie, a calibrer sur les taux de couverture
# grecs : stade 1 ~ 0,5 %, stade 2 ~ 5-10 %, stade 3 ~ 40-50 % ) :
#   0 sain ; 1 sous surveillance ( un impaye de moins de 30 jours, ou un flux libre du client devenu negatif ) ;
#   2 retard de 30 a 89 jours ; 3 defaut.
PROVISION_STADE = (0.01, 0.10, 0.40, 1.00)
DEFAUT_J = 90                      # defaut : 90 jours de retard ( definition de l ABE, art. 178 CRR )
RADIATION_J = 360                  # un pret en defaut est radie un an plus tard ( a calibrer )
PRET_MIN = 10.0                    # drachmes : en dessous, pas de pret
HORIZON_OCTROI = 30                # le maximum du socle ; la premiere mensualite tombe au 30e jour

# ================================================================== la demande de credit
SEUIL_BESOIN_J = 7                 # un menage demande quand sa caisse ne paie plus 7 jours de nourriture
BESOIN_J = 30                      # ... de quoi manger 30 jours
DELAI_DEMANDE_J = 30               # une demande par mois au plus
TAILLE_BORNE = 12                  # pour le tri vectorise des menages a court ( taille maximale supposee )
# Depense exceptionnelle ( reparation, sante, fete ) : frequence et montant A CALIBRER ; le domaine 3 ( budget des
# menages ) la reprendra et pourra mettre EXCEPTIONNELLE_AN a 0.
EXCEPTIONNELLE_AN = 0.3            # par menage et par an
EXCEPTIONNELLE_SIGMA = 0.8         # le montant : un mois de revenu, fois une loi log-normale d ecart-type 0,8
EXCEPTIONNELLE_MIN = 100.0
TAUX_EFFORT_MAX = 0.40             # un menage ne s endette pas pour une depense non vitale au-dela de 40 % de son revenu
FDR_SEUIL_J = 5                    # une entreprise demande quand sa caisse ne couvre plus 5 jours de couts
FDR_BESOIN_J = 20                  # ... de quoi tenir 20 jours
ALPHA_REVENU = 1.0 / 30.0          # moyenne mobile des revenus observes : 30 jours
PART_PETIT = 0.5


def mensualite(montant, taux, duree):
    """Mensualite constante d un pret de `montant` drachmes au taux annuel `taux` ( proportionnel : taux / 12 par
    mois ) sur `duree` mois."""
    if duree < 1: raise ValueError(f"duree de pret invalide : {duree!r}")
    r = taux / 12.0
    if r == 0.0: return montant / duree
    return montant * r / (1.0 - (1.0 + r) ** -duree)


def echeance_du_mois(principal, du_principal, mensualite_, taux, restantes):
    """( interet, amortissement ) d une mensualite : l interet du mois court sur tout le principal restant, echu et
    impaye compris ; l amortissement suit le tableau sur la part non echue ; la derniere mensualite solde le tout."""
    r = taux / 12.0
    non_echu = principal - du_principal
    amort = non_echu if restantes <= 1 else min(non_echu, max(0.0, mensualite_ - non_echu * r))
    return principal * r, amort


def stade_provision(defaut, retard_j, flux_libre):
    """Le stade IFRS 9 d un pret : 3 en defaut, 2 a 30 jours de retard, 1 pour un impaye plus recent ou un client dont
    le flux libre observe est devenu negatif ( hausse significative du risque ), 0 sinon."""
    if defaut: return 3
    if retard_j is not None:
        return 2 if retard_j >= 30 else 1
    return 1 if flux_libre < 0.0 else 0


# ================================================================== les classes
class Banque:
    """Une banque commerciale. Ses postes de bilan sont tenus a part et verifies chaque soir ( verifier_bilans ) :
      caisse                  drachmes : sa monnaie propre, dans le registre ( interets encaisses, dividendes a verser )
      reserves                drachmes de monnaie centrale a la banque centrale : la contrepartie des depots, hors registre
      refinancement           drachmes pretees par la banque centrale
      titres                  drachmes : bons du Tresor detenus, au prix d achat
      fonds_propres_emetteur  drachmes : les fonds propres hors caisse ( capital de depart, moins dotations et pertes,
                              plus remuneration nette des reserves )
      cree_jour, detruit_jour monnaie creee ( prets ) et detruite ( principal ) aujourd hui dans son cercle
      solde_cercle            somme des caisses de son cercle au dernier reglement
      rwa                     encours pondere du risque ( Bale III standard ), refait chaque matin
      actionnaires            identifiants des menages qui recoivent ses dividendes"""
    __slots__ = ("indice", "nom", "part", "caisse", "reserves", "refinancement", "titres", "fonds_propres_emetteur",
                 "cree_jour", "detruit_jour", "cree", "detruit", "solde_cercle", "reglement", "rwa", "actionnaires",
                 "interets", "dotations", "pertes")

    def __init__(self, indice, nom, part):
        if not 0.0 < part <= 1.0: raise ValueError(f"{nom} : part de marche hors ]0 ; 1] : {part!r}")
        self.indice, self.nom, self.part = indice, nom, part
        self.caisse = 0.0
        self.reserves = self.refinancement = self.titres = self.fonds_propres_emetteur = 0.0
        self.cree_jour = self.detruit_jour = self.cree = self.detruit = 0.0
        self.solde_cercle = self.reglement = self.rwa = 0.0
        self.actionnaires = []
        self.interets = self.dotations = self.pertes = 0.0

    def fonds_propres(self): return self.fonds_propres_emetteur + self.caisse


class IndicePrix:
    """L indice des prix a la consommation ( base 100 a l installation ), calcule par la banque centrale sur les prix
    AFFICHES des marches, TVA comprise, ponderes par la population que chaque marche nourrit : ce que l office
    statistique voit, jamais la rarete cachee."""
    __slots__ = ("poids", "base", "valeurs")

    def __init__(self, poids, base):
        s = sum(poids.values())
        if abs(s - 1.0) > 1e-9 or any(v < 0 for v in poids.values()): raise ValueError(f"poids de l indice invalides : {poids}")
        if any(base[b] <= 0 for b in poids): raise ValueError("prix de base non positif")
        self.poids, self.base = dict(poids), dict(base)
        self.valeurs = deque(maxlen=INDICE_MEMOIRE_J)

    def calculer(self, prix):
        return 100.0 * math.fsum(w * prix[b] / self.base[b] for b, w in self.poids.items())

    def inflation(self, jours):
        """Inflation annualisee sur les `jours` derniers jours, ou None si l histoire est trop courte."""
        if jours < 1 or len(self.valeurs) <= jours: return None
        a, b = self.valeurs[-1 - jours], self.valeurs[-1]
        return (b / a) ** (JOURS_AN / jours) - 1.0


class BanqueCentrale:
    """La banque centrale du pays ( la drachme a la sienne ).
      caisse                  drachmes : son benefice du mois ( interets des avances ), reverse au Tresor
      taux_directeur          taux annuel du refinancement ; la facilite de depot est 15 points plus bas
      avances                 drachmes pretees au Tresor
      avoirs_depart           ses actifs a l installation : la contrepartie de toute la monnaie centrale d alors
      ext0                    le compteur exterieur du grand livre a l installation ( avoirs exterieurs nets )
      fonds_propres_emetteur  interets du refinancement moins remuneration des reserves, plus interets capitalises
      solde_cercle            caisses de son cercle ( Tresor, elle-meme, familles sans banque ) au dernier reglement"""
    __slots__ = ("caisse", "taux_directeur", "regle_active", "prochaine_reunion", "avances", "avoirs_depart", "ext0",
                 "fonds_propres_emetteur", "solde_cercle", "indice")

    def __init__(self, taux, prochaine_reunion, indice):
        if not 0.0 <= taux <= TAUX_MAX: raise ValueError(f"taux directeur hors [0 ; {TAUX_MAX}] : {taux!r}")
        self.caisse = 0.0
        self.taux_directeur, self.regle_active, self.prochaine_reunion = taux, True, prochaine_reunion
        self.avances = self.avoirs_depart = self.fonds_propres_emetteur = self.solde_cercle = 0.0
        self.ext0 = {"entree": 0.0, "sortie": 0.0}
        self.indice = indice

    def taux_depot(self): return self.taux_directeur - ECART_FACILITE_DEPOT


class Pret:
    """Un credit amortissable a mensualites constantes.
      montant, principal       drachmes pretees ; principal restant du ( echu ou non )
      taux, duree, mensualite  taux annuel, duree en mois, mensualite constante
      restantes                mensualites pas encore echues
      du_interet, du_principal ce qui est echu et impaye
      retard_depuis            jour de la plus vieille echeance impayee, -1 si a jour
      defaut_j                 jour du defaut ( 90 jours de retard ), -1 sinon ; en defaut, tout le principal est exigible
      provision                drachmes provisionnees ( stade IFRS 9 )
      demande                  cle de la demande dont la note attend encore ce pret, -1 sinon
      paye_interet, paye_principal  drachmes encaissees par la banque sur ce pret ( la statistique, les portes )
      ticket, pas_echeance     la prochaine echeance posee dans l echeancier du socle"""
    __slots__ = ("id", "banque", "emprunteur", "type", "montant", "principal", "taux", "duree", "mensualite",
                 "restantes", "du_interet", "du_principal", "retard_depuis", "defaut_j", "provision", "octroi_j",
                 "demande", "ticket", "pas_echeance", "incident", "paye_interet", "paye_principal")

    def __init__(self, id, banque, emprunteur, type_, montant, taux, duree, jour, demande=-1):
        if type_ not in TYPES: raise ValueError(f"type de pret inconnu {type_!r} : {tuple(TYPES)}")
        if not 0.0 < montant < math.inf: raise ValueError(f"montant de pret invalide : {montant!r}")
        if not 0.0 <= taux <= 1.0: raise ValueError(f"taux hors [0 ; 1] : {taux!r}")
        if not (isinstance(duree, int) and 1 <= duree <= 600): raise ValueError(f"duree hors [1 ; 600] mois : {duree!r}")
        self.id, self.banque, self.emprunteur, self.type = id, banque, emprunteur, type_
        self.montant = self.principal = float(montant)
        self.taux, self.duree, self.mensualite = float(taux), duree, mensualite(montant, taux, duree)
        self.restantes = duree
        self.du_interet = self.du_principal = self.provision = 0.0
        self.retard_depuis = self.defaut_j = -1
        self.octroi_j, self.demande = jour, demande
        self.ticket = self.pas_echeance = -1
        self.incident = False
        self.paye_interet = self.paye_principal = 0.0


class Titre:
    """Un bon du Tresor a escompte, detenu par une banque : achete `prix`, rembourse `nominal` a l echeance ( le prix
    detruit, l escompte verse comme interet ). `prix` et `interet` : ce qui reste du."""
    __slots__ = ("id", "banque", "nominal", "prix", "interet", "taux", "emission_j", "duree_j")

    def __init__(self, id, banque, nominal, taux, duree_j, jour):
        if not 0.0 < nominal < math.inf: raise ValueError(f"nominal invalide : {nominal!r}")
        if not 0.0 <= taux <= 1.0: raise ValueError(f"taux hors [0 ; 1] : {taux!r}")
        if not (isinstance(duree_j, int) and 1 <= duree_j <= 3650): raise ValueError(f"duree hors [1 ; 3650] jours : {duree_j!r}")
        self.id, self.banque, self.nominal, self.taux, self.duree_j, self.emission_j = id, banque, float(nominal), taux, duree_j, jour
        self.prix = self.nominal / (1.0 + taux * duree_j / JOURS_AN)      # principal : ce que la banque a paye
        self.interet = self.nominal - self.prix                           # l escompte : l interet du a l echeance


class SuiviEntreprise:
    """Ce que la banque voit du compte d une entreprise : son flux net d exploitation ( variation de la caisse sur
    24 h, distributions rajoutees, flux des prets retires ), en moyenne mobile, et son histoire de credit."""
    __slots__ = ("flux", "n", "caisse_matin", "caisse_avant_paie", "salaires", "distribue", "flux_pret", "demande_j",
                 "incidents")

    def __init__(self, caisse):
        self.flux, self.n = 0.0, 0
        self.caisse_matin, self.caisse_avant_paie, self.salaires = None, caisse, 0.0
        self.distribue = self.flux_pret = 0.0
        self.demande_j, self.incidents = -100000, 0

    def flux_estime(self):
        return self.flux / (1.0 - (1.0 - ALPHA_REVENU) ** self.n) if self.n > 0 else 0.0


class Demande:
    __slots__ = ("id", "emprunteur", "entreprise", "banque", "type", "montant", "duree", "taux", "motif", "depense",
                 "reserve")

    def __init__(self, id, emprunteur, entreprise, banque, type_, montant, duree, taux, motif, depense=0.0, reserve=0.0):
        self.id, self.emprunteur, self.entreprise, self.banque, self.type = id, emprunteur, entreprise, banque, type_
        self.montant, self.duree, self.taux, self.motif, self.depense, self.reserve = montant, duree, taux, motif, depense, reserve


class ContexteOctroi:
    """Ce que la banque voit d une demande : ses traits, calcules par `_traits`, et la demande elle-meme."""
    __slots__ = ("traits", "demande")

    def __init__(self, traits, demande): self.traits, self.demande = traits, demande


class Banques:
    """L etat du domaine."""
    __slots__ = ("banques", "bc", "decideur", "prets", "prets_de", "en_retard", "titres", "comptes", "suivi",
                 "avant_paie", "ouvertes", "prochain_pret", "prochain_titre", "prochaine_demande", "emis_motif",
                 "controle", "serie", "compte", "non_verse")

    def __init__(self, banques, bc):
        self.banques, self.bc = banques, bc
        self.decideur = None
        self.prets = {}          # id -> Pret actif
        self.prets_de = {}       # emprunteur -> [ id ]
        self.en_retard = {}      # id -> None : les prets a surveiller chaque jour
        self.titres = {}         # id -> Titre
        self.comptes = {}        # detenteur ( hors menages ) -> indice de sa banque
        self.suivi = {}          # entreprise -> SuiviEntreprise
        self.avant_paie = None   # caisses des menages a 17 h 50
        self.ouvertes = {}       # cle de demande -> [ jour, montant demande, consequence du jour, id du pret ou -1 ]
        self.prochain_pret = self.prochain_titre = self.prochaine_demande = 0
        self.emis_motif = {}     # motif -> monnaie emise moins detruite, lue dans les comptes clos du grand livre
        self.controle = {"jours": 0, "pire_bilan": 0.0, "pire_bc": 0.0, "dernier": None}
        self.serie = deque(maxlen=INDICE_MEMOIRE_J)
        self.compte = {k: 0 for k in ("demandes", "accordes", "petits", "refuses", "refus_reglementaires", "defauts",
                                      "radiations", "exceptionnelles", "renoncees", "soldes")}
        self.compte.update(montant_demande=0.0, montant_accorde=0.0)
        self.non_verse = 0.0     # interets des depots dus mais non verses, faute de caisse propre


# ================================================================== le point de decision
def _observer_octroi(ctx): return ctx.traits


def score_octroi(x):
    """Le score de la regle : la capacite, un bonus pour le solde, un malus pour l endettement."""
    return x[0] + 0.1 * x[1] - 0.1 * x[2]


def _regle_octroi(x, ctx):
    """Accorder ce que le flux libre rembourse : capacite 0,5 = le flux libre couvre la mensualite, 0,375 = il en
    couvre la moitie ( donc la mensualite d un pret moitie moins grand ). Un incident passe ferme la porte."""
    if x[3] > 0.0: return 0
    s = score_octroi(x)
    return 2 if s >= 0.5 else 1 if s >= 0.375 else 0


def _temoin_octroi(x, ctx, rng): return 2


POINT_OCTROI = D.PointDeDecision(
    "octroi_credit", "banques",
    traits=(("capacite", "flux libre du compte sur la nouvelle mensualite, ( x + 1 ) / 4 borne : paie des 30 derniers "
                         "jours ( menage ) ou flux net d exploitation ( entreprise ), moins la nourriture au prix affiche "
                         "et les mensualites en cours du fichier Tiresias"),
            ("solde", "le solde du compte du client sur le montant demande, borne a 1"),
            ("endettement", "encours de ses prets ( fichier Tiresias, toutes banques ) sur encours plus un an de revenu"),
            ("incidents", "ses retards de 30 jours et plus et ses defauts passes ( fichier Tiresias ), sur 3"),
            ("taille", "les personnes du menage sur 8, ou les salaries de l entreprise sur 60"),
            ("entreprise", "1 si le demandeur est une entreprise ( sa declaration )"),
            ("taux", "le taux de la grille de la banque ( taux directeur + marge du type ), sur 25 %"),
            ("montant", "le montant demande sur montant plus un an de revenu")),
    actions=("refuser", "accorder_petit", "accorder"),
    observer=_observer_octroi, regle=_regle_octroi, temoin=_temoin_octroi,
    note="ce que CE pret rapporte a la banque sur 30 jours - interets encaisses moins dotations aux provisions - en "
         "rendement annuel du montant demande ; 0 pour un refus",
    horizon_j=HORIZON_OCTROI)


# ================================================================== le registre
def _membres_banques(w): return w.pays.domaines["banques"].banques
def _membres_banque_centrale(w): return (w.pays.domaines["banques"].bc,)


# ================================================================== petits outils
def _vivants(mg): return sum(1 for x in mg.membres if x.vivant)


def _prix_nourriture(w, mg):
    return w.marches[mg.domicile.marche.id].prix["nourriture"] * (1.0 + w.gouv.tva)


def _revenu_menage(p, i):
    """Revenu journalier observe a la paie ( moyenne mobile 30 jours, corrigee du demarrage )."""
    n = int(p.col("menage", "revenu_n")[i])
    return float(p.col("menage", "revenu")[i]) / (1.0 - (1.0 - ALPHA_REVENU) ** n) if n > 0 else 0.0


def _est_menage(x): return type(x) is PO.Menage


def dette_de(p, emprunteur):
    """Encours de tous les prets de cet emprunteur ( ce que le fichier Tiresias montre a toute banque )."""
    d = p.domaine("banques")
    return math.fsum(d.prets[i].principal for i in d.prets_de.get(emprunteur, ()))


def _mensualites(d, emprunteur):
    return math.fsum(d.prets[i].mensualite for i in d.prets_de.get(emprunteur, ()) if d.prets[i].defaut_j < 0)


def _incidents(p, d, emp):
    if _est_menage(emp): return int(p.col("menage", "incidents")[emp.id])
    s = d.suivi.get(emp)
    return s.incidents if s is not None else 0


def _noter_incident(p, d, emp):
    if _est_menage(emp):
        c = p.col("menage", "incidents"); c[emp.id] = min(100, int(c[emp.id]) + 1)
    else:
        s = d.suivi.get(emp)
        if s is not None: s.incidents += 1


def _revenu_et_charges(p, d, emp):
    """( revenu mensuel observe, depense de subsistance mensuelle ) : la paie et la nourriture d un menage, le flux net
    d exploitation d une entreprise ( ses salaires sont deja dedans )."""
    if _est_menage(emp):
        return MOIS_J * _revenu_menage(p, emp.id), MOIS_J * _vivants(emp) * C.NOURRITURE_PAR_JOUR * _prix_nourriture(p.w, emp)
    s = d.suivi.get(emp)
    return (MOIS_J * s.flux_estime() if s is not None else 0.0), 0.0


def flux_libre(p, emprunteur):
    """Revenu mensuel observe moins subsistance moins mensualites en cours : ce qui reste pour une mensualite de plus."""
    d = p.domaine("banques")
    rev, charges = _revenu_et_charges(p, d, emprunteur)
    return rev - charges - _mensualites(d, emprunteur)


def banque_de(p, detenteur):
    """La banque du detenteur, ou None s il tient son compte a la banque centrale ( Tresor, familles sans banque )."""
    d = p.domaine("banques")
    k = int(p.col("menage", "banque")[detenteur.id]) if _est_menage(detenteur) else d.comptes.get(detenteur, -1)
    return d.banques[k] if k >= 0 else None


def ouvrir_compte(p, detenteur, banque=None):
    """Rattache un detenteur ( entreprise, assureur, hopital... ) a une banque ; sans banque nommee, tiree selon les
    parts de marche. Un detenteur jamais rattache tient son compte a la banque centrale. Rend la banque."""
    d = p.domaine("banques")
    k = banque.indice if banque is not None else _tirer_banque(d, p.du_jour("banques_ouverture"))
    if _est_menage(detenteur): p.col("menage", "banque")[detenteur.id] = k
    else: d.comptes[detenteur] = k
    return d.banques[k]


def _parts(d):
    a = np.array([b.part for b in d.banques], dtype=np.float64)
    return a / a.sum()


def _tirer_banque(d, rng): return int(rng.choice(len(d.banques), p=_parts(d)))


# ================================================================== les taux
def taux_directeur(p): return p.domaine("banques").bc.taux_directeur


def taux_credit(p, type_):
    """Le taux de la grille : taux directeur + marge du type."""
    return taux_directeur(p) + TYPES[type_][0]


def fixer_taux_directeur(p, taux, regle=False):
    """Fixe le taux directeur ( domaine 6, un gouvernement, une porte ). `regle` : garder ou non la regle de Taylor."""
    if not 0.0 <= taux <= TAUX_MAX: raise ValueError(f"taux directeur hors [0 ; {TAUX_MAX}] : {taux!r}")
    bc = p.domaine("banques").bc
    bc.taux_directeur, bc.regle_active = float(taux), bool(regle)


def regle_de_taylor(taux, inflation):
    """Le taux vise par la regle de Taylor, lisse : au plus PAS_TAUX_MAX de mouvement, dans [0 ; TAUX_MAX]."""
    vise = R_NEUTRE + inflation + PHI_PI * (inflation - PI_CIBLE)
    return min(TAUX_MAX, max(0.0, min(taux + PAS_TAUX_MAX, max(taux - PAS_TAUX_MAX, vise))))


def _prix_observes(w):
    """Prix affiches TVA comprise, moyens sur les marches ponderes par la population qu ils nourrissent."""
    pop = {k: w._pop_marche.get(k, 0) for k in w.marches}
    tot = sum(pop.values())
    out = {}
    for b in POIDS_INDICE:
        if tot > 0: out[b] = math.fsum(pop[k] * m.prix[b] for k, m in w.marches.items()) / tot * (1.0 + w.gouv.tva)
        else: out[b] = math.fsum(m.prix[b] for m in w.marches.values()) / len(w.marches) * (1.0 + w.gouv.tva)
    return out


def indice_des_prix(p):
    v = p.domaine("banques").bc.indice.valeurs
    return v[-1] if v else 100.0


def inflation(p, jours=365):
    """Inflation annualisee mesuree sur au plus `jours` jours ( l histoire disponible ), None avant 30 jours."""
    ind = p.domaine("banques").bc.indice
    k = min(jours, len(ind.valeurs) - 1)
    return ind.inflation(k) if k >= 30 else None


# ================================================================== les prets : octroi, echeances, recouvrement
def _provisionner(p, d, pr):
    """Ajuste la provision du pret a son stade ; la dotation ( ou la reprise ) passe en fonds propres."""
    b = d.banques[pr.banque]
    if pr.principal <= 0.0: cible = 0.0
    else:
        retard = p.jour - pr.retard_depuis if pr.retard_depuis >= 0 else None
        s = stade_provision(pr.defaut_j >= 0, retard, flux_libre(p, pr.emprunteur) if pr.defaut_j < 0 else 0.0)
        cible = PROVISION_STADE[s] * TYPES[pr.type][2] * pr.principal
    delta = cible - pr.provision
    if delta != 0.0:
        pr.provision = cible
        b.fonds_propres_emetteur -= delta; b.dotations += delta
        _consequence(d, pr, -delta)


def _consequence(d, pr, drachmes):
    if pr.demande >= 0:
        o = d.ouvertes.get(pr.demande)
        if o is not None: o[2] += drachmes


def _poser_echeance(p, pr):
    pr.pas_echeance = p.w.pas + PAS_MOIS - 1
    pr.ticket = p.poser(PAS_MOIS - 1, "banques_mensualite", pr.id)


def _debloquer(p, d, b, emp, montant, type_, duree, taux, demande=-1):
    """Le pret nait : la banque cree la monnaie sur le compte de l emprunteur ( emettre, motif credit )."""
    pr = Pret(d.prochain_pret, b.indice, emp, type_, montant, taux, duree, p.jour, demande)
    d.prochain_pret += 1
    p.socle.livre.emettre(emp, pr.montant, "credit")
    b.cree_jour += pr.montant
    s = d.suivi.get(emp)
    if s is not None: s.flux_pret += pr.montant
    d.prets[pr.id] = pr
    d.prets_de.setdefault(emp, []).append(pr.id)
    _poser_echeance(p, pr)
    _provisionner(p, d, pr)
    b.rwa += (pr.principal - pr.provision) * TYPES[type_][3]
    p.compter("pret_accorde", pr.montant)
    return pr


def _encaisser(p, d, pr):
    """Preleve ce qui est echu : les interets d abord ( transfert a la banque ), puis le principal ( detruit ). Met a
    jour le retard et la provision ; solde le pret s il est rembourse."""
    L = p.socle.livre
    b = d.banques[pr.banque]; emp = pr.emprunteur
    s = d.suivi.get(emp)
    if pr.du_interet > 0.0:
        x = L.transferer(emp, b, pr.du_interet, "interet_pret")
        pr.du_interet -= x; b.interets += x; pr.paye_interet += x
        if s is not None: s.flux_pret -= x
        _consequence(d, pr, x)
    if pr.du_principal > 0.0:
        y = L.detruire_monnaie(emp, pr.du_principal, "remboursement_principal")
        pr.du_principal -= y; pr.principal -= y; b.detruit_jour += y; pr.paye_principal += y
        if s is not None: s.flux_pret -= y
    if pr.du_interet + pr.du_principal > EPS:
        if pr.retard_depuis < 0:
            pr.retard_depuis = p.jour; d.en_retard[pr.id] = None
            p.compter("mensualite_impayee")
    else:
        pr.du_interet = 0.0                       # un reste d arrondi d interet n est pas un impaye
        if pr.retard_depuis >= 0:
            pr.retard_depuis = -1; d.en_retard.pop(pr.id, None)
        if pr.restantes == 0 and pr.du_principal <= EPS and pr.principal <= 1e-6:
            _solder(p, d, pr); return
    _provisionner(p, d, pr)


def _retirer(d, pr):
    del d.prets[pr.id]
    ids = d.prets_de[pr.emprunteur]; ids.remove(pr.id)
    if not ids: del d.prets_de[pr.emprunteur]
    d.en_retard.pop(pr.id, None)


def _solder(p, d, pr):
    """Pret rembourse : un reste d arrondi du principal est passe en perte ( fonds propres ), la provision reprise."""
    b = d.banques[pr.banque]
    if pr.principal != 0.0:
        b.fonds_propres_emetteur -= pr.principal; pr.principal = 0.0; pr.du_principal = 0.0
    _provisionner(p, d, pr)
    _retirer(d, pr)
    d.compte["soldes"] += 1
    p.compter("pret_solde")


def _mensualite_echue(p, pid, donnees):
    """Une mensualite tombe : l interet du mois sur tout le principal restant ( echu compris ), l amortissement du
    tableau sur la part non echue ; puis le prelevement."""
    d = p.domaine("banques")
    pr = d.prets.get(pid)
    if pr is None or pr.defaut_j >= 0: return
    interet, amort = echeance_du_mois(pr.principal, pr.du_principal, pr.mensualite, pr.taux, pr.restantes)
    pr.du_interet += interet
    pr.du_principal += amort
    pr.restantes -= 1
    pr.ticket = pr.pas_echeance = -1
    p.compter("mensualite_echue")
    _encaisser(p, d, pr)
    if pr.id in d.prets and pr.restantes > 0 and pr.defaut_j < 0: _poser_echeance(p, pr)


def _defaut(p, d, pr):
    """90 jours de retard : le pret est en defaut, le terme est dechu ( tout le principal devient exigible ), les
    interets cessent de courir, la provision passe au stade 3."""
    pr.defaut_j = p.jour
    if pr.ticket >= 0:
        p.socle.echeancier.annuler(pr.ticket, pr.pas_echeance); pr.ticket = pr.pas_echeance = -1
    pr.du_principal = pr.principal; pr.restantes = 0
    _noter_incident(p, d, pr.emprunteur)                  # le defaut est un incident de plus au fichier
    d.compte["defauts"] += 1
    _provisionner(p, d, pr)
    p.noter("defaut_de_paiement", pret=pr.id, banque=pr.banque, categorie=pr.type, principal=round(pr.principal, 2))


def _radier(p, d, pr):
    """Un an apres le defaut : le reste est perdu pour la banque ( fonds propres ) et devient une creance du socle,
    que le domaine 21 pourra recouvrer."""
    b = d.banques[pr.banque]
    perte = pr.principal - pr.provision
    b.fonds_propres_emetteur -= perte; b.pertes += pr.principal
    _consequence(d, pr, -perte)
    du = pr.principal + pr.du_interet
    if du > EPS: p.socle.creances.constater(b, pr.emprunteur, du, "recouvrement_pret", p.jour)
    pr.principal = pr.provision = 0.0
    _retirer(d, pr)
    d.compte["radiations"] += 1
    p.noter("radiation", pret=pr.id, banque=pr.banque, perte=round(perte, 2))


def _recouvrer(p):
    """18 h 10, apres la paie : les prets en retard sont preleves de nouveau ; le retard vieillit ; a 30 jours c est un
    incident au fichier, a 90 jours un defaut, un an plus tard une radiation. Puis tous les prets sains sont revus :
    un client dont le flux libre est devenu negatif passe sous surveillance ( stade 1 )."""
    d = p.domaine("banques")
    for pid in list(d.en_retard):
        pr = d.prets.get(pid)
        if pr is None: d.en_retard.pop(pid, None); continue
        _encaisser(p, d, pr)
        if pid not in d.prets or pr.retard_depuis < 0: continue
        retard = p.jour - pr.retard_depuis
        if retard >= 30 and not pr.incident: pr.incident = True; _noter_incident(p, d, pr.emprunteur)
        if pr.defaut_j < 0 and retard >= DEFAUT_J: _defaut(p, d, pr)
        elif pr.defaut_j >= 0 and p.jour - pr.defaut_j >= RADIATION_J: _radier(p, d, pr)
    for pr in list(d.prets.values()):
        if pr.retard_depuis < 0: _provisionner(p, d, pr)


# ================================================================== les demandes et l octroi
def _traits(p, d, q):
    emp = q.emprunteur
    rev, charges = _revenu_et_charges(p, d, emp)
    m_new = mensualite(q.montant, q.taux, q.duree)
    x = (rev - charges - _mensualites(d, emp)) / m_new
    dette = dette_de(p, emp)
    rp = max(0.0, rev) * 12.0
    if q.entreprise:
        lieu, role = getattr(emp, "lieu", None), getattr(emp, "role", None)
        n = len([h for h in p.w.au_travail_de(lieu, role) if h.vivant]) if lieu is not None and role else 0
        taille = min(60, n) / 60.0
    else:
        taille = min(8, _vivants(emp)) / 8.0
    return (min(1.0, max(0.0, (x + 1.0) / 4.0)),
            min(1.0, max(0.0, emp.caisse / q.montant)),
            dette / (dette + rp) if dette + rp > 0.0 else 0.0,
            min(3, _incidents(p, d, emp)) / 3.0,
            taille,
            1.0 if q.entreprise else 0.0,
            min(1.0, q.taux / 0.25),
            q.montant / (q.montant + rp))


def _fonds_propres_suffisants(b, montant, poids):
    """Bale III : apres ce pret, fonds propres >= 10,5 % des actifs ponderes du risque."""
    return b.fonds_propres() >= RATIO_FONDS_PROPRES_MIN * (b.rwa + montant * poids)


def instruire(p, q):
    """Une demande passe au point de decision `octroi_credit`. Rend le Pret, ou None ( refus, ou refus reglementaire,
    qui n est pas une decision : le regulateur interdit )."""
    d = p.domaine("banques")
    b = d.banques[q.banque]
    d.compte["demandes"] += 1; d.compte["montant_demande"] += q.montant
    p.compter("demande_credit", q.montant)
    if not _fonds_propres_suffisants(b, q.montant, TYPES[q.type][3]):
        d.compte["refus_reglementaires"] += 1; p.compter("refus_reglementaire"); return None
    a = d.decideur.decider(q.id, ContexteOctroi(_traits(p, d, q), q))
    o = d.ouvertes[q.id] = [p.jour, q.montant, 0.0, -1]
    montant = (0.0, PART_PETIT, 1.0)[a] * q.montant
    if montant < PRET_MIN:
        d.compte["refuses"] += 1; p.compter("pret_refuse"); return None
    pr = _debloquer(p, d, b, q.emprunteur, montant, q.type, q.duree, q.taux, q.id)
    o[3] = pr.id
    d.compte["accordes" if a == 2 else "petits"] += 1; d.compte["montant_accorde"] += montant
    return pr


def _nouvelle_demande(p, d, emp, entreprise, type_, montant, motif, depense=0.0, reserve=0.0):
    b = banque_de(p, emp)
    if b is None or not montant >= 2 * PRET_MIN: return None
    q = Demande(d.prochaine_demande, emp, entreprise, b.indice, type_, float(montant), TYPES[type_][1],
                taux_credit(p, type_), motif, depense, reserve)
    d.prochaine_demande += 1
    return q


def _demandes_menages(p, d):
    """Les menages a court de nourriture, puis les depenses exceptionnelles du jour. Tri vectorise, calcul exact sur
    les seuls candidats."""
    w = p.w
    n = len(w.menages)
    caisse = np.fromiter((m.caisse for m in w.menages), np.float64, n)
    ok = (p.col("menage", "dissous")[:n] == 0) & (p.col("menage", "banque")[:n] >= 0)
    dj = p.col("menage", "demande_j")
    libre = ok & (p.jour - dj[:n] >= DELAI_DEMANDE_J)
    prix_max = max(m.prix["nourriture"] for m in w.marches.values()) * (1.0 + w.gouv.tva)
    borne = SEUIL_BESOIN_J * TAILLE_BORNE * C.NOURRITURE_PAR_JOUR * prix_max
    out, deja = [], set()
    for i in np.nonzero(libre & (caisse < borne))[0].tolist():
        mg = w.menages[i]
        v = _vivants(mg)
        if v == 0: continue
        cout_j = v * C.NOURRITURE_PAR_JOUR * _prix_nourriture(w, mg)
        if mg.caisse >= SEUIL_BESOIN_J * cout_j: continue
        q = _nouvelle_demande(p, d, mg, False, "conso", BESOIN_J * cout_j - mg.caisse, "besoin")
        if q is None: continue
        dj[i] = p.jour; deja.add(i); out.append(q)
    # les depenses exceptionnelles
    u = p.du_jour("banques_exceptionnel").random(n)
    tires = np.nonzero(ok & (u < EXCEPTIONNELLE_AN / JOURS_AN))[0]
    z = p.du_jour("banques_montant").lognormal(0.0, EXCEPTIONNELLE_SIGMA, len(tires))
    for i, f in zip(tires.tolist(), z.tolist()):
        if i in deja: continue
        mg = w.menages[i]
        v = _vivants(mg)
        if v == 0: continue
        rev_m = MOIS_J * _revenu_menage(p, i)
        A = max(EXCEPTIONNELLE_MIN, rev_m) * f
        reserve = SEUIL_BESOIN_J * v * C.NOURRITURE_PAR_JOUR * _prix_nourriture(w, mg)
        d.compte["exceptionnelles"] += 1; p.compter("depense_exceptionnelle", A)
        if mg.caisse - A >= reserve:
            p.socle.livre.transferer(mg, w.marches[mg.domicile.marche.id], A, "depense_exceptionnelle"); continue
        besoin = A - max(0.0, mg.caisse - reserve)
        effort = _mensualites(d, mg) + mensualite(besoin, taux_credit(p, "conso"), TYPES["conso"][1])
        if p.jour - dj[i] < DELAI_DEMANDE_J or effort > TAUX_EFFORT_MAX * rev_m:
            d.compte["renoncees"] += 1; p.compter("depense_renoncee"); continue
        q = _nouvelle_demande(p, d, mg, False, "conso", besoin, "exceptionnelle", A, reserve)
        if q is None: continue
        dj[i] = p.jour; out.append(q)
    return out


def _demandes_entreprises(p, d):
    """Les entreprises ( hors fermes cooperatives, qui distribuent toute leur caisse ) dont la caisse ne couvre plus
    5 jours de couts demandent un credit de fonds de roulement pour en tenir 20."""
    w = p.w
    out = []
    for e, s in d.suivi.items():
        if e.type == "ferme" or p.jour - s.demande_j < DELAI_DEMANDE_J or d.comptes.get(e, -1) < 0: continue
        _, _, _, cout_h, _ = w.economie_entreprise(e)
        n = len([h for h in w.au_travail_de(e.lieu, e.role) if h.vivant])
        cout_j = cout_h * n * 8.0 * max(0.1, e.activite)
        if cout_j <= 0.0 or e.caisse >= FDR_SEUIL_J * cout_j: continue
        q = _nouvelle_demande(p, d, e, True, "entreprise", FDR_BESOIN_J * cout_j - e.caisse, "fonds_de_roulement")
        if q is None: continue
        s.demande_j = p.jour; out.append(q)
    return out


def _suivre_entreprises_matin(p, d):
    for e, s in d.suivi.items():
        if s.caisse_matin is not None:
            flux = e.caisse - s.caisse_matin + s.distribue - s.flux_pret
            s.flux = s.flux * (1.0 - ALPHA_REVENU) + ALPHA_REVENU * flux; s.n = min(30000, s.n + 1)
        s.caisse_matin = e.caisse; s.distribue = 0.0; s.flux_pret = 0.0


def _rwa(d):
    acc = [[] for _ in d.banques]
    for pr in d.prets.values(): acc[pr.banque].append((pr.principal - pr.provision) * TYPES[pr.type][3])
    for b, v in zip(d.banques, acc): b.rwa = math.fsum(v)


def _guichet(p):
    """9 h : le flux des entreprises est releve chaque jour ; les jours ouvres, les demandes du jour sont instruites
    ( menages, puis entreprises, dans l ordre des identifiants )."""
    d = p.domaine("banques"); w = p.w
    _suivre_entreprises_matin(p, d)
    cal = p.socle.calendrier
    if not cal.ouvre(cal.date(w.pas)): return
    _rwa(d)
    for q in _demandes_menages(p, d) + _demandes_entreprises(p, d):
        pr = instruire(p, q)
        if q.motif != "exceptionnelle": continue
        mg = q.emprunteur
        if pr is not None and mg.caisse - q.depense >= q.reserve:
            p.socle.livre.transferer(mg, w.marches[mg.domicile.marche.id], q.depense, "depense_exceptionnelle")
        else:
            d.compte["renoncees"] += 1; p.compter("depense_renoncee")


# ================================================================== la paie observee
def _avant_paie(p):
    d = p.domaine("banques"); w = p.w
    d.avant_paie = np.fromiter((m.caisse for m in w.menages), np.float64, len(w.menages))
    for e, s in d.suivi.items():
        s.caisse_avant_paie = e.caisse
        s.salaires = math.fsum(PO.SALAIRE_HORAIRE.get(h.role, 0) * h.heures_jour
                               for h in w.au_travail_de(e.lieu, e.role) if h.vivant)


def _apres_paie(p):
    """18 h : ce que la paie a verse a chaque menage entre dans sa moyenne mobile ; ce qu une entreprise a verse au-dela
    de ses salaires ( dividendes, revenu agricole ) est une distribution, rajoutee a son flux d exploitation."""
    d = p.domaine("banques"); w = p.w
    if d.avant_paie is None: return
    n = len(d.avant_paie)
    maintenant = np.fromiter((w.menages[i].caisse for i in range(n)), np.float64, n)
    entree = np.maximum(0.0, maintenant - d.avant_paie)
    ok = p.col("menage", "dissous")[:n] == 0
    rv, rn = p.col("menage", "revenu"), p.col("menage", "revenu_n")
    rv[:n] = np.where(ok, rv[:n] * (1.0 - ALPHA_REVENU) + ALPHA_REVENU * entree, rv[:n])
    rn[:n] = np.where(ok, np.minimum(30000, rn[:n] + 1), rn[:n])
    d.avant_paie = None
    for e, s in d.suivi.items():
        s.distribue += max(0.0, (s.caisse_avant_paie - e.caisse) - s.salaires)


# ================================================================== la banque centrale : prix, taux, Tresor
def _matin(p):
    """6 h 10, apres l aube du moteur : la banque centrale releve les prix affiches ; les jours de reunion, elle fixe
    son taux par la regle de Taylor sur l inflation MESUREE."""
    d = p.domaine("banques"); bc = d.bc
    bc.indice.valeurs.append(bc.indice.calculer(_prix_observes(p.w)))
    if bc.regle_active and p.jour >= bc.prochaine_reunion:
        bc.prochaine_reunion = p.jour + REUNION_J
        pi = inflation(p)
        if pi is None: return
        ancien = bc.taux_directeur
        bc.taux_directeur = round(regle_de_taylor(ancien, pi), 4)
        p.noter("decision_taux", taux=bc.taux_directeur, ancien=ancien, inflation=round(pi, 4))


def avance_a_l_etat(p, montant):
    """La banque centrale prete au Tresor : elle cree la monnaie sur son compte ( emettre, motif avance_bc )."""
    if not 0.0 < montant < math.inf: raise ValueError(f"avance invalide : {montant!r}")
    d = p.domaine("banques")
    p.socle.livre.emettre(p.w.gouv, montant, "avance_bc")
    d.bc.avances += montant
    p.noter("avance_etat", montant=round(montant, 2))
    return montant


def rembourser_avance(p, montant):
    """Le Tresor rembourse ( au plus ce qu il doit et ce qu il a ) : la monnaie est detruite. Rend le montant rembourse."""
    d = p.domaine("banques")
    x = p.socle.livre.detruire_monnaie(p.w.gouv, min(montant, d.bc.avances), "remboursement_avance_bc")
    d.bc.avances -= x
    return x


def souscrire_titre(p, banque, nominal, taux, duree_j):
    """Une banque achete un bon du Tresor neuf : elle paie en reserves, le Tresor recoit la monnaie ( emettre, motif
    souscription_titre ). A l echeance, le Tresor rembourse le prix ( detruit ) et paie l interet ( transfert )."""
    d = p.domaine("banques")
    t = Titre(d.prochain_titre, banque.indice, nominal, taux, duree_j, p.jour)
    d.prochain_titre += 1
    p.socle.livre.emettre(p.w.gouv, t.prix, "souscription_titre")
    banque.reserves -= t.prix; banque.titres += t.prix
    d.titres[t.id] = t
    p.poser(duree_j * C.PAS_PAR_JOUR - 1, "banques_titre", t.id)
    p.noter("titre_souscrit", titre=t.id, banque=banque.indice, nominal=round(nominal, 2))
    return t


def _titre_echu(p, tid, donnees):
    """Echeance d un titre : le Tresor detruit le prix ( les reserves de la banque remontent d autant ) et verse
    l escompte. S il ne peut pas payer, le reste est represente le lendemain."""
    d = p.domaine("banques"); w = p.w; L = p.socle.livre
    t = d.titres.get(tid)
    if t is None: return
    b = d.banques[t.banque]
    du = t.prix + t.interet
    if AVANCE_AUTOMATIQUE and w.gouv.caisse < du: avance_a_l_etat(p, du - max(0.0, w.gouv.caisse))
    y = L.detruire_monnaie(w.gouv, t.prix, "remboursement_titre")
    b.reserves += y; b.titres -= y; t.prix -= y
    x = L.transferer(w.gouv, b, t.interet, "interet_titre")
    t.interet -= x
    if t.prix > EPS or t.interet > EPS:
        p.poser(C.PAS_PAR_JOUR - 1, "banques_titre", t.id); return
    if t.prix != 0.0: b.titres -= t.prix; b.fonds_propres_emetteur -= t.prix      # un reste d arrondi, passe en perte
    del d.titres[tid]


# ================================================================== le soir : reglement, reserves, controles
def _ouvrir_comptes(p, d):
    """Les detenteurs nouveaux ( menages nes d un divorce, entreprises creees ) recoivent une banque."""
    w = p.w
    n = len(w.menages)
    bq = p.col("menage", "banque")
    sans = np.nonzero(bq[:n] < 0)[0]
    rng = None
    if len(sans):
        rng = p.du_jour("banques_ouverture")
        bq[sans] = rng.choice(len(d.banques), len(sans), p=_parts(d))
    for nom in ("entreprises", "marches"):
        f = p.socle.registre.familles.get(nom)
        if f is None: continue
        for x in f.membres(w):
            if x not in d.comptes:
                if rng is None: rng = p.du_jour("banques_ouverture")
                d.comptes[x] = _tirer_banque(d, rng)
                if nom == "entreprises" and x not in d.suivi: d.suivi[x] = SuiviEntreprise(x.caisse)


def soldes_des_cercles(p):
    """La somme exacte des caisses de chaque cercle : une par banque ( ses clients et sa caisse propre ), puis celle
    de la banque centrale ( Tresor, elle-meme, toute famille dont les membres n ont pas de banque )."""
    d = p.domaine("banques"); w = p.w
    K = len(d.banques)
    par = [[] for _ in range(K + 1)]
    for f in p.socle.registre.familles.values():
        if f.argent is None: continue
        if f.nom == "menages":
            n = len(w.menages)
            caisse = np.fromiter((m.caisse for m in w.menages), np.float64, n)
            bq = p.col("menage", "banque")[:n]
            for k in range(K): par[k].extend(caisse[bq == k].tolist())
            par[K].extend(caisse[bq < 0].tolist())
        elif f.nom == "banques":
            for b in d.banques: par[b.indice].append(b.caisse)
        else:
            for x in f.membres(w):
                k = d.comptes.get(x, -1)
                par[k if k >= 0 else K].append(getattr(x, f.argent))
    return [math.fsum(v) for v in par]


def _regler(p, d):
    """Le reglement interbancaire : ce qu un cercle a gagne, hors la monnaie que sa banque y a creee ou detruite, lui
    vient des autres cercles ; ses reserves bougent d autant."""
    S = soldes_des_cercles(p)
    for b in d.banques:
        net = (S[b.indice] - b.solde_cercle) - b.cree_jour + b.detruit_jour
        b.reserves += net; b.reglement = net
        b.solde_cercle = S[b.indice]
        b.cree += b.cree_jour; b.detruit += b.detruit_jour
        b.cree_jour = b.detruit_jour = 0.0
    d.bc.solde_cercle = S[-1]
    return S


def _reserves(p, d):
    """Interets du refinancement ( au taux directeur ) et remuneration de l excedent de reserves ( facilite de depot ),
    en reserves ; puis les reserves obligatoires : un manque est refinance, un excedent rembourse le refinancement."""
    bc = d.bc
    for b in d.banques:
        requis = RATIO_RESERVES * (b.solde_cercle - b.caisse)
        if b.refinancement > 0.0:
            i = b.refinancement * bc.taux_directeur / JOURS_AN
            b.reserves -= i; b.fonds_propres_emetteur -= i; bc.fonds_propres_emetteur += i
        exces = b.reserves - requis
        if exces > 0.0:
            i = exces * bc.taux_depot() / JOURS_AN
            b.reserves += i; b.fonds_propres_emetteur += i; bc.fonds_propres_emetteur -= i
        if b.reserves < requis:
            x = requis - b.reserves
            b.reserves += x; b.refinancement += x
            p.compter("refinancement", x)
        elif b.refinancement > 0.0:
            x = min(b.refinancement, b.reserves - requis)
            b.reserves -= x; b.refinancement -= x


def _fin_de_mois(p, d):
    """Tous les 30 jours : interets des depots ( de la caisse propre de la banque ), dividendes, interets des avances
    du Tresor et benefice de la banque centrale reverse au Tresor."""
    w = p.w; L = p.socle.livre
    f = TAUX_DEPOTS_VUE * MOIS_J / JOURS_AN
    n = len(w.menages)
    bq = p.col("menage", "banque")[:n]; dis = p.col("menage", "dissous")[:n]
    clients = [[] for _ in d.banques]
    for i in np.nonzero((bq >= 0) & (dis == 0))[0].tolist(): clients[int(bq[i])].append(w.menages[i])
    for x, k in d.comptes.items():
        if k >= 0: clients[k].append(x)
    for b in d.banques:
        dus = [(x, x.caisse * f) for x in clients[b.indice] if x.caisse > 0.0]
        total = math.fsum(v for _, v in dus)
        if total > 0.0:
            k = min(1.0, b.caisse / total)
            for x, v in dus:
                if v * k > 0.0: L.transferer(b, x, v * k, "interet_depot")
            d.non_verse += total * (1.0 - k)
        div = DIVIDENDE_PART * b.caisse
        if div > 0.0:
            vivants = [w.menages[i] for i in b.actionnaires if not p.col("menage", "dissous")[i]]
            if vivants:
                for mg in vivants: L.transferer(b, mg, div / len(vivants), "dividende_banque")
            else: L.transferer(b, w.gouv, div, "dividende_banque")
    bc = d.bc
    if bc.avances > 0.0:
        du = bc.avances * bc.taux_directeur * MOIS_J / JOURS_AN
        if AVANCE_AUTOMATIQUE and w.gouv.caisse < du: avance_a_l_etat(p, du - max(0.0, w.gouv.caisse))
        L.transferer(w.gouv, bc, du, "interet_avance_bc")
    if bc.caisse > 0.0: L.transferer(bc, w.gouv, bc.caisse, "benefice_bc")


def verifier_bilans(p, S=None):
    """Chaque poste de chaque bilan, calcule a part : encours et provisions sur les prets, depots sur les caisses des
    clients, reserves et fonds propres sur leurs comptes. Exact a toute heure : les reserves y sont celles d un
    reglement fait a l instant. Rend ( pire ecart des banques en tolerances, ecart de la banque centrale en tolerances,
    details ). Un ecart de plus d une tolerance ( registre.tolerance ) est une faute."""
    d = p.domaine("banques"); L = p.socle.livre
    if S is None: S = soldes_des_cercles(p)
    enc = [[] for _ in d.banques]; prov = [[] for _ in d.banques]
    for pr in d.prets.values(): enc[pr.banque].append(pr.principal); prov[pr.banque].append(pr.provision)
    pire, details, reserves = 0.0, [], []
    for b in d.banques:
        P, Pv = math.fsum(enc[b.indice]), math.fsum(prov[b.indice])
        depots = S[b.indice] - b.caisse
        # les reserves apres le reglement qui aurait lieu maintenant ( zero de plus a 23 h 50, juste apres le reglement )
        r = b.reserves + ((S[b.indice] - b.solde_cercle) - b.cree_jour + b.detruit_jour)
        reserves.append(r)
        actif = math.fsum((r, P, -Pv, b.titres))
        passif = math.fsum((depots, b.refinancement, b.fonds_propres_emetteur, b.caisse))
        e = actif - passif
        pire = max(pire, abs(e) / R.tolerance(actif))
        details.append({"banque": b.nom, "reserves": r, "prets": P, "provisions": Pv, "titres": b.titres,
                        "depots": depots, "refinancement": b.refinancement, "fonds_propres": b.fonds_propres(),
                        "ecart": e})
    bc = d.bc
    ext = (L.ext["entree"] - bc.ext0["entree"]) - (L.ext["sortie"] - bc.ext0["sortie"])
    actif = math.fsum([bc.avoirs_depart, ext, bc.avances] + [b.refinancement for b in d.banques])
    passif = math.fsum(reserves + [S[-1], bc.fonds_propres_emetteur])
    e_bc = actif - passif
    details.append({"banque": "banque centrale", "avoirs_exterieurs": bc.avoirs_depart + ext, "avances": bc.avances,
                    "reserves": math.fsum(reserves), "cercle": S[-1], "ecart": e_bc})
    return pire, abs(e_bc) / R.tolerance(actif), details


def _noter_octrois(p, d):
    """Chaque demande ouverte encaisse la consequence du jour ( interets moins dotations, rapportes au montant demande,
    annualises ) ; la note murit au 30e jour. Pas de note le jour de la decision : elle entre dans le lendemain."""
    dec = d.decideur; j = p.jour
    for cle in list(d.ouvertes):
        o = d.ouvertes[cle]
        if o[0] >= j: continue
        dec.noter(cle, o[2] / o[1] * JOURS_AN, j); o[2] = 0.0
        att = dec.attentes.get(cle)
        if att is None or not att.choix:
            dec.attentes.pop(cle, None); del d.ouvertes[cle]
            pr = d.prets.get(o[3])
            if pr is not None: pr.demande = -1


def masse_monetaire(p):
    """Les agregats du soir : base monetaire ( reserves ), M1 ( depots des clients des banques ), credit, prets en
    defaut, avances au Tresor, titres."""
    d = p.domaine("banques")
    enc = math.fsum(pr.principal for pr in d.prets.values())
    npl = math.fsum(pr.principal for pr in d.prets.values() if pr.defaut_j >= 0)
    return {"base": math.fsum(b.reserves for b in d.banques),
            "m1": math.fsum(b.solde_cercle - b.caisse for b in d.banques),
            "credit": enc, "npl": npl / enc if enc > 0 else 0.0, "avances": d.bc.avances,
            "titres": math.fsum(b.titres for b in d.banques), "taux": d.bc.taux_directeur}


def _soir(p):
    """23 h 50, apres les routines des autres domaines : fin de mois, decouvert du Tresor, reglement, reserves,
    bilans, notes des decisions, agregats."""
    d = p.domaine("banques"); w = p.w
    if p.jour % MOIS_J == MOIS_J - 1: _fin_de_mois(p, d)
    if AVANCE_AUTOMATIQUE and w.gouv.caisse < 0.0: avance_a_l_etat(p, -w.gouv.caisse)
    _ouvrir_comptes(p, d)
    S = _regler(p, d)
    _reserves(p, d)
    pire, pire_bc, _ = verifier_bilans(p, S)
    c = d.controle
    c["jours"] += 1; c["pire_bilan"] = max(c["pire_bilan"], pire); c["pire_bc"] = max(c["pire_bc"], pire_bc)
    c["dernier"] = (p.jour, pire, pire_bc)
    _noter_octrois(p, d)
    m = masse_monetaire(p)
    d.serie.append((p.jour, m["base"], m["m1"], m["credit"], m["npl"], m["taux"], indice_des_prix(p)))


def _cloture(p, comptes):
    """Les comptes clos du grand livre : la monnaie emise et detruite, par motif ( l identite monetaire se lit la )."""
    d = p.domaine("banques")
    for m, payeur, receveur, s, n in comptes["argent"]:
        if receveur == "Emission": d.emis_motif[m] = d.emis_motif.get(m, 0.0) - s
        elif payeur == "Emission": d.emis_motif[m] = d.emis_motif.get(m, 0.0) + s


def emissions_par_motif(p):
    """Monnaie emise moins detruite depuis l installation, par motif, lue dans le grand livre ( jours clos et jour en
    cours ) : jamais dans les compteurs du domaine."""
    d = p.domaine("banques")
    out = dict(d.emis_motif)
    for (m, payeur, receveur), (s, n) in p.socle.livre.jour_argent.items():
        if receveur == "Emission": out[m] = out.get(m, 0.0) - s
        elif payeur == "Emission": out[m] = out.get(m, 0.0) + s
    return out


# ================================================================== API pour les autres domaines
def demander_credit(p, emprunteur, montant, type_="conso", motif="projet", duree=None):
    """Une demande de credit d un autre domaine ( immobilier 13, vehicule 14, budget 3 ) : elle passe par le point de
    decision, comme les autres. Rend le Pret ou None."""
    d = p.domaine("banques")
    q = _nouvelle_demande(p, d, emprunteur, not _est_menage(emprunteur), type_, montant, motif)
    if q is None: return None
    if duree is not None: q.duree = int(duree)
    _rwa(d)
    return instruire(p, q)


def preter(p, banque, emprunteur, montant, type_="conso", duree=None, taux=None):
    """Un pret direct, sans decision ( une porte, un pret garanti par l Etat ). L emprunteur doit etre client de
    `banque` : une banque ne cree de monnaie que sur les comptes qu elle tient."""
    d = p.domaine("banques")
    if banque_de(p, emprunteur) is not banque: raise ValueError("l emprunteur n est pas client de cette banque")
    return _debloquer(p, d, banque, emprunteur, float(montant), type_, int(duree or TYPES[type_][1]),
                      taux_credit(p, type_) if taux is None else float(taux))


def rembourser_par_anticipation(p, pret, montant=None):
    """L emprunteur rembourse d avance ( vente d un bien, heritage ) : l echu d abord, puis le principal. Rend le
    principal detruit."""
    d = p.domaine("banques")
    if d.prets.get(pret.id) is not pret: raise KeyError(f"pret {pret.id} inconnu ou solde")
    _encaisser(p, d, pret)
    if pret.id not in d.prets or pret.defaut_j >= 0: return 0.0
    voulu = pret.principal - pret.du_principal if montant is None else min(montant, pret.principal - pret.du_principal)
    y = p.socle.livre.detruire_monnaie(pret.emprunteur, voulu, "remboursement_principal")
    pret.principal -= y; pret.paye_principal += y; d.banques[pret.banque].detruit_jour += y
    s = d.suivi.get(pret.emprunteur)
    if s is not None: s.flux_pret -= y
    if pret.principal <= 1e-6 and pret.du_principal <= EPS and pret.du_interet <= EPS:
        if pret.ticket >= 0: p.socle.echeancier.annuler(pret.ticket, pret.pas_echeance)
        pret.restantes = 0; _solder(p, d, pret)
    else:
        pret.mensualite = mensualite(pret.principal - pret.du_principal, pret.taux, max(1, pret.restantes))
        _provisionner(p, d, pret)
    return y


def bilan(p, banque):
    return next(x for x in verifier_bilans(p)[2] if x["banque"] == banque.nom)


def bilan_bc(p): return verifier_bilans(p)[2][-1]


# ================================================================== installation
def installer(p):
    w = p.w
    L = p.socle.livre
    for m in ("credit", "remboursement_principal", "avance_bc", "remboursement_avance_bc", "souscription_titre",
              "remboursement_titre", "recouvrement_pret"):
        L.declarer_motif(m, "financier", "banques")
    for m in ("interet_pret", "interet_depot", "dividende_banque", "interet_avance_bc", "benefice_bc", "interet_titre"):
        L.declarer_motif(m, "revenu_propriete", "banques")
    L.declarer_motif("depense_exceptionnelle", "achat", "banques")
    J = p.socle.journal
    for t, champs in (("defaut_de_paiement", ("pret", "banque", "categorie", "principal")), ("radiation", ("pret", "banque", "perte")),
                      ("decision_taux", ("taux", "ancien", "inflation")), ("avance_etat", ("montant",)),
                      ("titre_souscrit", ("titre", "banque", "nominal"))):
        J.declarer(t, "banques", "individuel", champs)
    for t in ("demande_credit", "pret_accorde", "pret_refuse", "refus_reglementaire", "mensualite_echue",
              "mensualite_impayee", "pret_solde", "refinancement", "depense_exceptionnelle", "depense_renoncee"):
        J.declarer(t, "banques", "compte")
    cm = p.colonnes["menage"]
    for nom, dt, defaut in (("banque", np.int8, -1), ("revenu", np.float64, 0.0), ("revenu_n", np.int16, 0),
                            ("incidents", np.int8, 0), ("demande_j", np.int32, -100000)):
        cm.ajouter(nom, dt, defaut)
    cm.assurer(len(w.menages))
    indice = IndicePrix(POIDS_INDICE, _prix_observes(w))
    d = Banques([Banque(k, nom, part) for k, (nom, part) in enumerate(BANQUES)],
                BanqueCentrale(TAUX_DIRECTEUR_0, p.jour + REUNION_J, indice))
    p.domaines["banques"] = d
    rng = p.hasard("banques_comptes")
    n = len(w.menages)
    p.col("menage", "banque")[:n] = rng.choice(len(d.banques), n, p=_parts(d))
    for e in sorted(w.entreprises.values(), key=lambda e: e.id):
        d.comptes[e] = _tirer_banque(d, rng); d.suivi[e] = SuiviEntreprise(e.caisse)
    for m in sorted(w.marches.values(), key=lambda m: m.lieu.id): d.comptes[m] = _tirer_banque(d, rng)
    # les actionnaires : les menages aises, clients de la banque
    bq = p.col("menage", "banque")
    for mg in w.menages:
        if any(x.vivant and x.classe == "aisee" for x in mg.membres): d.banques[int(bq[mg.id])].actionnaires.append(mg.id)
    reg = p.socle.registre
    reg.inscrire("banques", "financier", _membres_banques, "caisse", None, "Banque")
    reg.inscrire("banque_centrale", "financier", _membres_banque_centrale, "caisse", None, "BanqueCentrale")
    # le bilan d ouverture : les caisses d hier deviennent des depots couverts un pour un par des reserves, plus les
    # fonds propres ; la banque centrale a pour actif la contrepartie de toute cette monnaie centrale
    S = soldes_des_cercles(p)
    for b in d.banques:
        b.solde_cercle = S[b.indice]
        b.fonds_propres_emetteur = FONDS_PROPRES_INITIAUX * S[b.indice]
        b.reserves = S[b.indice] + b.fonds_propres_emetteur
    d.bc.solde_cercle = S[-1]
    d.bc.avoirs_depart = math.fsum([b.reserves for b in d.banques] + [S[-1]])
    d.bc.ext0 = dict(L.ext)
    d.decideur = p.decideur(POINT_OCTROI)
    p.echeance("banques_mensualite", _mensualite_echue)
    p.echeance("banques_titre", _titre_echu)
    p.routine(6 + 10 / 60, 20, "banques", _matin)
    p.routine(9, 20, "banques", _guichet)
    p.routine(17 + 50 / 60, 20, "banques", _avant_paie)
    p.routine(18, 20, "banques", _apres_paie)
    p.routine(18 + 10 / 60, 20, "banques", _recouvrer)
    p.routine(23 + 50 / 60, 95, "banques", _soir)
    p.cloture("banques", _cloture)
    return d
