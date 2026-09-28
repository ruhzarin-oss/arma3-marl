"""DOMAINE 20 - ASSURANCES : AUTO, HABITATION, SANTE COMPLEMENTAIRE, RECOLTE ( ELGA ), PROVISIONS, PLACEMENTS,
REASSURANCE, SOLVABILITE.

FICHE
1. Classes. Les detenteurs d argent : Assureur ( une compagnie : caisse, provisions, placements, solvabilite ;
   famille `assureurs`, secteur financier ), FondsGarantie ( le fonds auxiliaire des victimes de vehicules non assures
   et des assureurs en faillite, l Epikouriko Kefalaio grec : famille `fonds_garantie` ), Elga ( l assureur public et
   obligatoire des recoltes, ELGA : famille `elga`, administrations ). L etat : TableContrats ( les contrats en
   STRUCTURE DE TABLEAUX : une ligne par contrat, recyclee a sa fin ), Declaration ( un sinistre declare : table eparse,
   quelques-uns par jour ), Obligation ( un bon du Tresor detenu par un assureur ), ContexteTarif, Couvrir ( l objet
   appelable que le transport appelle a chaque reparation d un vehicule accidente ), Assurances ( l etat du domaine ).
   Colonnes par menage : as_auto0, as_auto1, as_auto2 ( la ligne du contrat auto de chaque emplacement de vehicule du
   domaine 14, -1 aucun ), as_hab, as_sante ( idem ), as_bm ( sinistres responsables recents : le fichier commun des
   sinistres, que tout assureur lit ), as_retry, as_retry_v ( le jour ou un menage sans contrat en redemande un :
   obligatoire, volontaire ), as_prop ( la VERITE CACHEE : ce que le menage veut bien assurer - bit 0 rouler assure,
   bit 1 son logement, bit 2 sa sante, bit 7 tire ; aucun assureur ne la lit ).
   REPRESENTATION. Un contrat par vehicule assure ( ~ 90 % des vehicules ), par logement assure ( ~ 15 % des
   proprietaires ) et par menage couvert en sante ( ~ 12 % ) : ~ 0,9 contrat par menage, et TOUS les contrats sont lus
   chaque jour par des calculs vectorises ( echeances, provisions pour primes non acquises, solvabilite ). D ou une table
   dense de 25 champs numeriques ( ~ 130 octets par contrat, ~ 2,3 Go a 50 millions d habitants, ~ 18 millions de
   contrats ; un objet Python par contrat en couterait ~ 5 fois plus ), recyclee par une liste de lignes libres : la
   memoire suit le portefeuille, pas le temps. Les menages portent un pointeur par garantie ( 5 x 4 octets ). Les
   sinistres, rares ( ~ 7 par an pour 100 vehicules ), sont des objets en table eparse.
2. Invariants et ce que le domaine detient. ARGENT : les caisses des assureurs, du fonds de garantie et d ELGA, tout par
   le grand livre sous les motifs du domaine. PRIMES au centime : chaque prime encaissee est le prix cote ( niveau x
   prime de reference ), et le grand livre voit sous `prime_assurance` exactement la somme des primes des contrats ;
   la taxe sur les primes est `TAXE` fois la prime. PROVISIONS : la provision pour sinistres a payer de chaque payeur
   est EXACTEMENT la somme des montants provisionnes des sinistres declares non payes ; la provision pour primes non
   acquises se recalcule chaque soir sur la table. INDEMNITES : aucune indemnite sans sinistre declare ( le grand livre
   sous `indemnite_assurance` = la somme des sinistres payes, hors TVA ), aucun sinistre sans contrat qui couvre la
   garantie au jour du sinistre ( ou le fonds de garantie, ou ELGA, chacun pour ce qu il couvre ) ( `audit` ).
   CONSERVATION : la reassurance passe par l exterieur ( domaine 7 : `payer_reassurance`, `recevoir_reassurance` ), le
   capital d ouverture est un investissement direct etranger ( motif du domaine 7 ).
3. Decision `tarifer` ( chaque contrat a sa souscription et a chaque renouvellement annuel, groupes a 9 h : ~ 1 / 365
   du portefeuille par jour plus les nouveaux vehicules, logements et menages ) : refuser, ou coter l un des sept
   niveaux 0,5 ; 0,7 ; 1,0 ; 1,4 ; 2,0 ; 2,8 ; 4,0 fois la prime de reference de la branche et de la formule de
   garanties. Traits : branche ( deux ), risque observe ( prime technique de l assureur sur la reference : statistiques
   du marche par categorie de vehicule, valeur, lieu, age du plus jeune conducteur declare, age du batiment, ages et
   maladies chroniques declarees ), sinistres passes ( bonus-malus du fichier commun ), age ( conducteur, batiment ou
   moyen des assures ), valeur assuree, client deja en portefeuille, ratio de solvabilite de l assureur. JAMAIS la
   propension cachee du menage ni l avenir. Note ( horizon 30 jours : une prime s acquiert jour apres jour, un sinistre
   auto se regle en quelques semaines, un menage non couvert l est des le premier jour ) : chaque jour, pour CE contrat,
   s il couvre : ( prime acquise nette de frais - sinistres payes du jour, bornes a 30 jours de prime ) sur la prime de
   reference journaliere, plus 1 ; si le menage est parti chez un concurrent qui le couvre : 1 ; s il n est couvert
   nulle part alors que le besoin existe ( vehicule qui roule, logement habite, menage ) : -2 en auto ( obligatoire ),
   -1 sinon ; 0 si le besoin a disparu. Ni le seul profit ( un prix trop haut fait partir le client ou le laisse sans
   couverture, un prix trop bas perd sur les sinistres ), ni une moyenne nationale. Regle : le niveau le plus proche de la prime
   technique ( perte attendue sur 65 % de ratio sinistres a primes, plus 25 euros de frais par contrat ) ; refus
   au-dela de 5 fois la reference, ou d un nouveau client si l assureur est sous 100 % de solvabilite. Temoin : la prime
   unique pour tous ( niveau 1,0 ).
   Le MENAGE decide sans point de decision ( regle ) : refuse, ou cote a plus de 1,25 fois le prix du marche, il
   compare les offres 7 fois sur 10 et signe chez un concurrent au prix du marche ( la regle ) ; sinon il accepte la
   cote avec la probabilite 1 / ( 1 + ( prime TTC / revenu annuel / R50 )^2 ) s il peut la payer sans toucher sa
   semaine de nourriture ; ceux qui ne veulent pas ( propension cachee ) ne demandent rien. Sans contrat, il redemande
   dans 60 jours ( auto ) ou 180 jours.
4. Evenements. Individuels : faillite_assureur, catastrophe_assuree, fraude_signalee. Comptes : souscription,
   renouvellement, resiliation, refus_assureur, refus_menage, depart_concurrent, sinistre_declare, sinistre_paye,
   sinistre_refuse,
   sinistre_sous_franchise, sinistre_non_couvert, recours_fonds_garantie, indemnite_elga, cotisation_elga,
   obligation_achetee, decision_tarif.
5. Liens. Transport ( 14 ) : `brancher_assurance` ( Couvrir : a la reparation d un vehicule accidente, l assureur
   paie au garage ce qu il couvre, TTC, le lendemain seulement si la reparation est lancee ), `sinistres`
   ( materiels, corporels, vols ), colonnes vh_m, vh_ne, vh_km, vh_lieu ; ses taux publics ( frequences, vols,
   responsabilite ) font le tarif. Un accident dont le menage n est pas responsable a ete cause par un TIERS : un
   vehicule tire au hasard dans le pays, pondere par le risque de sa categorie ; son assureur de responsabilite civile
   paie, et son bonus-malus monte ; si ce tiers n est pas assure, le fonds de garantie paie. Immobilier ( 13 ) :
   `sinistres` ( seisme ou incendie : la cause se lit au journal, evenement seisme_dommages du lieu et du jour ),
   `proprietaire`, table des batiments ( surface, annee ), `cout_m2`, `disponible` ( la semaine de nourriture ).
   Hopitaux ( 17 ) : les factures ( participation du malade en clinique, remboursee a 80 % ). Agriculture ( 9 ) : les
   campagnes closes ( climat de la campagne ) pour ELGA, la valeur de reference de chaque ferme pour sa cotisation.
   Banques ( 2 ) : `ouvrir_compte` des assureurs et du fonds. Etat ( 6 ) : taxe sur les primes ( motif du domaine :
   `percevoir` ne l accepte pas ), `taux_des_bons` et `assurer` avant chaque remboursement d obligation, TVA des
   reparations ( `percevoir_tva` ). Exterieur ( 7 ) : reassurance ( quote-part habitation et excedent de sinistre
   seisme, excedent par risque au-dela de 10 % des fonds propres ), capital d ouverture ( investissement_direct ),
   dividendes des maisons meres. Justice ( 21, si installee ) :
   `signaler_fraude_assurance` pour chaque fraude soupconnee ( vraie ou fausse alerte ). Paie et recoit : primes
   ( menage -> assureur ), taxe ( menage -> Etat ), contribution au fonds ( assureur -> fonds ), cessions et
   recuperations ( assureur <-> exterieur ), indemnites ( assureur, fonds -> menage, garage ), ristournes ( assureur ->
   menage ), placements, coupons et remboursements ( assureur <-> Etat ), cotisations et indemnites ELGA ( ferme <->
   ELGA ), dotation d ELGA ( Etat -> ELGA ), liquidation ( assureur -> fonds ). Ne remplace aucune methode du moteur.
6. Portes : tests_d20_assurances.py.
7. Arma : aucun objet ( un assureur est un bureau, un expert un civil : rien a incarner ; arma_preuve sans objet ).
8. Cout. Chaque jour : une passe vectorisee des colonnes des menages ( besoins nouveaux, vehicules vendus ou changes,
   logements quittes ), une passe de la table des contrats ( echeances, provisions, solvabilite par np.bincount ) ; les
   boucles Python ne visitent que les decisions du jour ( ~ 1 / 365 du portefeuille ), les notes en attente ( 30 jours
   de decisions ) et les sinistres du jour. Mesure du 26/09 ( test_cout, coeur Rust, 10 005 habitants, 8 022
   contrats ) : routines propres 3,5 a 7,5 ms par jour, 1 a 2 % d une journee du moteur seul ( 0,3 a 0,4 s ) ;
   installation 0,013 s a 10 000 habitants, 0,09 a 0,12 s a 100 000 ( 78 970 contrats ) : x 5 a x 9, lineaire. A 50
   millions : ~ 40 millions de contrats en table ( ~ 5 Go en Python, ~ 2 Go en Rust ), ~ 110 000 decisions par jour."""
import collections, importlib, math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D
from . import pays as PAYS, d02_banques as BQ, d06_etat as ET, d07_exterieur as EXT, d13_immobilier as IM
from . import d09_agriculture as AG, d14_transport as TR, d17_hopitaux as HO

JOURS_AN = 365.0
EPS = 1e-9
TOL = 1e-6
DR = 1.0 / PAYS.EUROS_PAR_DRACHME            # un euro, en drachmes
PAS_J = C.PAS_PAR_JOUR

# ================================================================== le marche grec
# EAEE ( Association hellenique des entreprises d assurance ), rapport 2023 : primes emises ~ 5,2 Md EUR ( vie ~ 2,6 ;
# non-vie ~ 2,6 ), ~ 2,3 % du PIB ( 220 Md EUR ) ; ~ 40 compagnies, les six premieres ~ 60 % du non-vie, le reste tres
# eclate ( ici une septieme compagnie les represente ). Noms fictifs ; parts a verifier.
ASSUREURS = (("Aigis", 0.15), ("Kyma", 0.13), ("Pyrgos", 0.12), ("Delos", 0.10), ("Thetis", 0.09),
             ("Naxos Mutuelle", 0.08), ("Petites compagnies", 0.33))
AUTO, HAB, SANTE = 0, 1, 2
BRANCHES = ("auto", "habitation", "sante")
RC, VOL, DOMMAGES = 1, 2, 4                   # garanties auto ( bits )
INCENDIE, SEISME = 1, 2                       # garanties habitation
HOSPI = 1                                     # garantie sante
LIBRE, ACTIF, SANS, RESILIE = 0, 1, 2, 3      # etats d une ligne de la table des contrats
FONDS, ELGA_P = -2, -3                        # payeurs qui ne sont pas des assureurs
OUVERT, ATTENTE_GARAGE, PAYE, REFUSE, SANS_SUITE = 0, 1, 2, 3, 4

# ================================================================== l auto
# Responsabilite civile obligatoire ( loi 489/1976, directive 2009/103/CE ). Non-assures : EAEE et police routiere,
# ~ 10 a 12 % des vehicules en circulation roulent sans assurance ( a verifier ) : une propension cachee de 8 % ( plus
# forte chez les pauvres ), plus ceux que le prix ou la caisse arretent ( porte : 7 a 16 % ).
PART_NON_ASSURES = 0.08
NON_ASSURE_CLASSE = np.array([0.5, 0.8, 1.0])      # aisee, moyenne, populaire ( a calibrer )
BANDE_AUTO = (0.84, 0.93)                          # part des vehicules assures
P_VOL_OPTION = 0.25                                # formule vol et incendie ( a calibrer )
P_DOMMAGES_NEUF, P_DOMMAGES_VIEUX, AGE_NEUF = 0.40, 0.05, 5.0   # tous risques : surtout les voitures de moins de 5 ans
COUT_MATERIEL = 1500.0 * DR * 1.24          # sinistre materiel moyen TTC ( ~ devis du domaine 14 ) ( a calibrer )
COUT_BLESSE = 15000.0 * DR                  # indemnite moyenne d un blesse ( frais, perte de revenu, prejudice moral ;
COUT_DECES = 250000.0 * DR                  # tribunaux grecs, ordres de grandeur a calibrer ) ; d un deces ( ayants droit )
FRANCHISE_DOMMAGES = 300.0 * DR
FRANCHISE_VOL = 0.10                        # part de la valeur venale
F_LIEU = {"capitale": 1.25, "ville": 1.0, "village": 0.8}   # zones tarifaires grecques ( a calibrer )
BM_PAS, BM_MAX = 0.25, 8                    # +25 % par sinistre responsable recent ( bonus-malus grec, a calibrer )
AGE_JEUNE, F_JEUNE = 25.0, 1.5              # surprime jeune conducteur ( pratique du marche )
VEHICULES_PAR_HAB = 0.86                    # domaine 14 : 560 voitures et ~ 300 autres pour 1 000 habitants
CONTRIB_FONDS = 0.03                        # contribution au fonds auxiliaire, part des primes auto ( a calibrer )

# ================================================================== l habitation
# EAEE 2023 : ~ 15 % des logements assures contre l incendie et les catastrophes ( a verifier ) ; le seisme est une
# extension souscrite par la plupart ( a calibrer ). Assurance obligatoire des entreprises depuis 2025 : hors domaine.
PART_HAB = np.array([0.35, 0.22, 0.16])     # propension par classe ( aisee, moyenne, populaire ) ( a calibrer )
BANDE_HAB = (0.10, 0.22)                    # part des logements de proprietaires occupants assures
P_SEISME_OPTION = 0.70
TAUX_INCENDIE_AN = 0.0012                   # incendies de logement par an ( pompiers grecs ~ 1 pour 1 000, a calibrer )
DEGAT_INCENDIE = 0.25                       # part de la valeur a neuf detruite par un incendie moyen ( a calibrer )
PAE_SEISME = 0.0010                         # perte annuelle moyenne seisme sur valeur a neuf ( modeles cat Egee ~ 0,5 a 1,5 pour mille )
F_VULN, ANNEE_CODE = 1.6, 1985              # un batiment d avant le code parasismique de 1985 ( a calibrer )
FRANCHISE_INCENDIE = 200.0 * DR
FRANCHISE_SEISME = 0.02                     # 2 % de la somme assuree ( usage grec : 2 a 5 % )

# ================================================================== la sante complementaire
# ~ 1,4 million de Grecs couverts par une assurance sante privee ( individuelle ou collective ), ~ 13 % ( EAEE, a
# verifier ). Elle rembourse ici ce que le malade paie en clinique au-dela du forfait EOPYY ( domaine 17 ).
PART_SANTE = np.array([0.35, 0.15, 0.10])   # propension des menages par classe ( a calibrer )
BANDE_SANTE = (0.08, 0.18)                  # part des personnes couvertes
REMB_SANTE = 0.80
PLAFOND_SANTE = 30000.0 * DR                # par personne et par an
P_CLINIQUE = 0.30                           # part des sejours en clinique privee ( a calibrer )
DUREE_SEJOUR_J = 5.0

# ================================================================== la recolte : ELGA
# ELGA ( loi 3877/2010 ) : assureur public et obligatoire des recoltes contre les aleas du climat ; cotisation
# speciale de 3 % des ventes vegetales et 0,5 % des ventes animales ( ~ 2 % en moyenne ) ; indemnise au-dela d un seuil
# de perte ( ~ 20 % ), a ~ 80 % de la valeur perdue ( a calibrer ). Les pertes de gestion ( non recolte, retard ) ne
# sont pas couvertes. L Etat couvre son deficit.
TAUX_ELGA = 0.02
SEUIL_ELGA = 0.20
COUV_ELGA = 0.80
DELAI_ELGA_J = 60

# ================================================================== tarif, frais, taxe
LR_CIBLE = 0.65                             # ratio sinistres a primes vise ( non-vie grec : ~ 55 a 65 %, a calibrer )
FRAIS = 0.30                                # frais d acquisition et de gestion en part des primes ( EIOPA, Grece ~ 30 % )
FRAIS_FIXES = 25.0 * DR                     # par contrat et par an
TAXE = (0.15, 0.15, 0.15)                   # taxe sur les primes non-vie ( 15 %, loi 2166/1993 ; incendie 20 % non modele )
FRAIS_ANNULATION = 0.10                     # retenue sur la ristourne d une resiliation
DUREE_J = 365

# ================================================================== reassurance, placements, solvabilite
QP_HAB = 0.50                               # quote-part cedee en habitation ( assureurs grecs : ~ 50 a 60 % des primes de dommages )
COMMISSION_CESSION = 0.30
XL_PRIORITE, XL_LIMITE, XL_TAUX = 0.01, 0.08, 0.03   # excedent de sinistre seisme par evenement : en part de la somme
#                                              assuree seisme retenue ; prime annuelle en part de la limite ( a calibrer )
# L excedent de sinistre PAR RISQUE : un assureur ne garde d un sinistre que RETENTION de ses fonds propres ( usage :
# 2 a 10 % ) ; au-dela, le reassureur paie. Sans lui, un deces ( 250 000 EUR ) ruine un assureur d un pays de 3 000
# habitants. Prime : une part des primes annuelles ( a calibrer ).
RETENTION, XL_RISQUE_TAUX = 0.10, 0.04
SIGMA = (0.10, 0.08, 0.05)                  # risque de primes par branche ( formule standard simplifiee : RC auto 10 %,
SIGMA_RES = 0.09                            # incendie 8 %, sante 5 % ) ; risque de reserve
CAT_200 = 0.10                              # perte seisme bicentennale en part de la somme assuree ( une seule ile : concentre )
OP_RISQUE = 0.03
MCR_PART = 0.35
CIBLE_SOLVA = 1.8                           # EIOPA 2023 : ratio de couverture du SCR des assureurs grecs ~ 180 a 200 %
DUREE_OBLIG_J = 182                         # bons du Tresor a 26 semaines
LIQUIDITE = 0.30                            # part des provisions gardee en caisse
DIVIDENDE_PART, DIVIDENDE_RATIO = 0.5, 1.5

# ================================================================== sinistres
DELAI = {"auto_especes": 15, "corporel": 90, "vol": 10, "incendie": 30, "seisme": 14, "sante": 15}
ATTENTE_GARAGE_J = 45                       # un vehicule jamais repare : l indemnite est versee au menage
P_FRAUDE = {"incendie": 0.10, "seisme": 0.08, "corporel": 0.12}   # Insurance Europe : ~ 10 % des couts ( a calibrer )
P_DETECTION = 0.35
P_FAUSSE_ALERTE = 0.005

# ================================================================== la decision
MULT = (0.0, 0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0)
ACTIONS = ("refuser", "p050", "p070", "p100", "p140", "p200", "p280", "p400")
I_UNIQUE = ACTIONS.index("p100")
HORIZON = 30
CAP_JOURS = 30.0                            # une perte d un jour est bornee a 30 jours de prime de reference
BONUS_COUVERT = 1.0
PENALITE = (2.0, 1.0, 1.0)
R50 = (0.05, 0.03, 0.04)                    # part du revenu annuel ou la moitie des menages refuse ( a calibrer )
# La concurrence : un menage refuse, ou a qui l on cote plus de CONCURRENCE fois le prix du marche, compare les offres
# ( comparateurs en ligne, courtiers ) avec la probabilite P_COMPARER, et signe chez un concurrent au prix du marche ( la
# regle ). Sans elle, la note recompensait le prix le plus fort ( 26/09 : note croissante de 1,34 a 2,29 du niveau 0,5
# au niveau 4 ) : un assureur seul face a des menages captifs. ( a calibrer )
CONCURRENCE, P_COMPARER = 1.25, 0.70
RETRY = (60, 180)
REFUS_RATIO = 5.0
TRAITS = (("auto", "le contrat demande"), ("habitation", "le contrat demande"),
          ("risque", "tarif technique : statistiques du marche et profil declare"),
          ("sinistres", "fichier commun des sinistres ( bonus-malus )"),
          ("age", "declaration : conducteur, batiment, assures"), ("valeur", "carte grise, cadastre, declaration"),
          ("client", "portefeuille de l assureur"), ("solvabilite", "bilan de l assureur"))

MOTIFS = (("prime_assurance", "transfert_courant"), ("taxe_primes_assurance", "impot_production"),
          ("indemnite_assurance", "transfert_courant"), ("ristourne_prime", "transfert_courant"),
          ("contribution_fonds_garantie", "transfert_courant"), ("cotisation_elga", "transfert_courant"),
          ("indemnite_elga", "transfert_courant"), ("dotation_elga", "transfert_courant"),
          ("placement_obligation", "financier"), ("remboursement_obligation", "financier"),
          ("coupon_obligation", "revenu_propriete"), ("liquidation_assureur", "financier"),
          ("dividende_assureur", "revenu_propriete"))
SUIVIS = tuple(m for m, _ in MOTIFS) + ("prime_reassurance", "indemnite_reassurance", "investissement_direct")


# ================================================================== les detenteurs
class Assureur:
    """Une compagnie : sa caisse ( depot en banque ), ses provisions ( sinistres a payer : psap ; primes non acquises :
    ppna ), ses obligations, sa solvabilite ( fonds propres, SCR, MCR ), sa couverture de reassurance seisme."""
    __slots__ = ("id", "nom", "part", "caisse", "psap", "ppna", "fp", "scr", "mcr", "ratio", "vivant", "primes_an",
                 "si_seisme", "xl_priorite", "xl_limite", "resultat", "faillite_j", "oblig", "retention", "reassure")

    def __init__(self, id, nom, part):
        if not 0.0 < part < 1.0: raise ValueError(f"{nom} : part de marche hors bornes")
        self.id, self.nom, self.part = id, nom, part
        self.caisse = self.psap = self.ppna = self.fp = self.scr = self.mcr = 0.0
        self.ratio = 0.0; self.vivant = True
        self.primes_an = [0.0, 0.0, 0.0]
        self.si_seisme = self.xl_priorite = self.xl_limite = 0.0
        self.resultat = 0.0          # primes - sinistres - frais de l annee en cours ( dividende )
        self.faillite_j = -1
        self.oblig = 0.0             # prix des obligations detenues
        self.retention = math.inf    # ce qu il garde d un sinistre ( excedent par risque )
        self.reassure = 1.0          # 0 : ses traites sont resilies ( reassureur defaillant )


class FondsGarantie:
    """Le fonds auxiliaire ( Epikouriko Kefalaio ) : paie les victimes des vehicules non assures et les sinistres des
    assureurs liquides ; finance par une contribution sur les primes auto et par les actifs des liquidations."""
    __slots__ = ("caisse", "psap", "oblig")

    def __init__(self): self.caisse = self.psap = self.oblig = 0.0


class Elga:
    """ELGA : l assureur public des recoltes."""
    __slots__ = ("caisse", "psap", "cotisations", "indemnites", "dotations")

    def __init__(self): self.caisse = self.psap = self.cotisations = self.indemnites = self.dotations = 0.0


def _membres_assureurs(w): return w.pays.domaines["assurances"].assureurs
def _membres_fonds(w): return (w.pays.domaines["assurances"].fonds,)
def _membres_elga(w): return (w.pays.domaines["assurances"].elga,)


class TableContrats:
    """Les contrats en colonnes ; une ligne libre est reprise par le contrat suivant. `p_*` : la periode precedente
    ( un sinistre declare apres un renouvellement se juge sur la periode ou il est survenu ). `refs` : les sinistres
    ouverts qui citent la ligne ( elle n est pas recyclee avant leur cloture )."""
    CHAMPS = {"branche": (np.int8, -1), "etat": (np.int8, LIBRE), "menage": (np.int32, -1), "slot": (np.int8, -1),
              "objet": (np.int32, -1), "modele": (np.int16, -1), "assureur": (np.int8, -1), "debut": (np.int32, 0),
              "fin": (np.int32, 0), "prime": (np.float64, 0.0), "ref": (np.float64, 0.0), "garanties": (np.uint8, 0),
              "franchise": (np.float64, 0.0), "plafond": (np.float64, 0.0), "unites": (np.float32, 0.0),
              "niveau": (np.int8, -1), "encaisse": (np.float64, 0.0), "paye": (np.float64, 0.0),
              "fautes": (np.int8, 0), "note_j": (np.int32, -1), "refs": (np.int32, 0), "p_debut": (np.int32, 0),
              "p_fin": (np.int32, -1), "p_gar": (np.uint8, 0), "p_menage": (np.int32, -1)}
    __slots__ = tuple(CHAMPS) + ("n", "cap", "libres")

    def __init__(self, cap=1024):
        self.n, self.cap, self.libres = 0, cap, []
        for nom, (dt, d) in self.CHAMPS.items(): setattr(self, nom, np.full(cap, d, dt))

    def _agrandir(self, besoin):
        cap = self.cap
        while cap < besoin: cap *= 2
        if cap == self.cap: return
        for nom, (dt, d) in self.CHAMPS.items():
            a = np.full(cap, d, dt); a[:self.cap] = getattr(self, nom); setattr(self, nom, a)
        self.cap = cap

    def nouvelle(self):
        if self.libres: return self.libres.pop()
        self._agrandir(self.n + 1)
        self.n += 1
        return self.n - 1

    def bloc(self, k):
        """k lignes neuves contigues ( le portefeuille initial )."""
        self._agrandir(self.n + k)
        r0 = self.n; self.n += k
        return np.arange(r0, r0 + k)

    def liberer(self, r):
        for nom, (dt, d) in self.CHAMPS.items(): getattr(self, nom)[r] = d
        self.libres.append(int(r))


class Declaration:
    """Un sinistre declare. `payeur` : indice d assureur, FONDS ou ELGA_P. `contrat` : la ligne du contrat qui couvre
    ( celui du RESPONSABLE pour une responsabilite civile ), et sa periode telle qu elle etait ( c_* ). `vrai` : le
    dommage reel ; `declare` : ce que l assure declare ( gonfle s il fraude : la verite cachee `fraude` ) ; `estime` :
    ce que le payeur provisionne apres franchise et plafond ; `paye` : ce qu il a paye ( dont `tva` au Tresor )."""
    __slots__ = ("id", "branche", "nature", "payeur", "contrat", "assure", "c_debut", "c_fin", "c_gar", "garantie",
                 "benef", "ferme", "source", "jour", "echeance_j", "vrai", "declare", "estime", "paye", "tva", "etat",
                 "fraude", "part_qp", "part_xl", "objet", "tiers_non_assure", "plafond", "recupere")

    def __init__(self, id, branche, nature, payeur, jour):
        self.id, self.branche, self.nature, self.payeur, self.jour = id, branche, nature, payeur, jour
        self.contrat = self.assure = -1; self.c_debut = self.c_fin = -1; self.c_gar = 0; self.garantie = 0
        self.benef = self.ferme = -1; self.source = -1; self.echeance_j = jour
        self.vrai = self.declare = self.estime = self.paye = self.tva = 0.0
        self.etat = OUVERT; self.fraude = False; self.part_qp = self.part_xl = 0.0; self.objet = -1
        self.tiers_non_assure = False
        self.plafond = math.inf      # la somme assuree du contrat au jour de la declaration
        self.recupere = 0.0          # ce que les reassureurs ont deja rendu


class Obligation:
    __slots__ = ("id", "detenteur", "prix", "interet", "echeance_j")

    def __init__(self, id, detenteur, prix, interet, echeance_j):
        self.id, self.detenteur, self.prix, self.interet, self.echeance_j = id, detenteur, prix, interet, echeance_j


class ContexteTarif:
    __slots__ = ("traits", "ratio", "nouveau", "solvable")

    def __init__(self, traits, ratio, nouveau, solvable):
        self.traits, self.ratio, self.nouveau, self.solvable = traits, ratio, nouveau, solvable


class Couvrir:
    """Ce que le domaine 14 appelle a la reparation d un vehicule accidente : rend la part TTC prise en charge."""
    __slots__ = ()

    def __call__(self, p, s, ttc): return couvrir(p, s, ttc)


class Assurances:
    __slots__ = ("assureurs", "fonds", "elga", "T", "ouverts", "prochain", "par_source", "payes", "obligations",
                 "prochaine_oblig", "decideur", "paye_jour", "vu_tr", "vu_im", "jour_ho", "vu_ag", "cpt", "livre",
                 "base", "type_lieu", "stats", "scenario", "jour_install", "invalides", "non_couverts", "parts",
                 "vus_seisme", "prix_elga")

    def __init__(self):
        self.assureurs = [Assureur(k, n, s) for k, (n, s) in enumerate(ASSUREURS)]
        self.fonds, self.elga = FondsGarantie(), Elga()
        self.T = TableContrats()
        self.ouverts = {}                # id -> Declaration non close
        self.prochain = 0
        self.par_source = {}             # ( source, cle ) -> id de la declaration
        self.payes = collections.deque(maxlen=20000)
        self.obligations = {}
        self.prochaine_oblig = 0
        self.decideur = None
        self.paye_jour = {}              # ligne -> indemnites payees aujourd hui ( la note )
        self.vu_tr = self.vu_im = self.vu_ag = 0
        self.jour_ho = 0
        self.cpt = {m: 0.0 for m in SUIVIS}        # ce que le domaine a paye ou recu, par motif
        self.cpt["sinistres_ht"] = 0.0             # indemnites payees hors TVA, somme des declarations
        self.livre = {m: 0.0 for m in SUIVIS}      # ce que le grand livre a vu, par motif ( jours clos )
        self.base = {}
        self.type_lieu = None
        self.stats = collections.Counter()
        self.scenario = {"reassurance": 1.0, "fraude": 1.0}
        self.jour_install = 0
        self.invalides = []              # declarations refusees faute de contrat ( ne doit pas arriver )
        self.non_couverts = collections.deque(maxlen=20000)   # ( jour, menage, nature, montant, objet ) : sans garantie
        self.parts = None
        self.vus_seisme = set()
        self.prix_elga = {}              # bien -> prix de reference de l annee ( drachmes par unite du catalogue )


def _dom(p): return p.domaines["assurances"]


def _reass(D, A):
    """Le facteur de reassurance d un assureur : celui du marche ( scenario ) fois le sien."""
    return D.scenario["reassurance"] * A.reassure


def _payeur(D, k):
    if k == FONDS: return D.fonds
    if k == ELGA_P: return D.elga
    return D.assureurs[k]


# ================================================================== les tarifs ( vectorises )
FREQ_MAT = np.array([TR.MATERIELS_VOITURE_AN * TR.RISQUE_MATERIEL[c] for c in TR.CATEGORIES])
FREQ_CORP = np.array([TR.ACCIDENTS_CORPORELS_M_AN / 1e6 / VEHICULES_PAR_HAB * TR.RISQUE_CORPOREL[c] for c in TR.CATEGORIES])
MORT_ACC = np.array([TR.TUES_M_AN / TR.ACCIDENTS_CORPORELS_M_AN * TR.MORT_RELATIVE[c] for c in TR.CATEGORIES])
DETRUIT = np.array([TR.DETRUIT_CORPOREL[c] for c in TR.CATEGORIES])
VOL_C = np.array([TR.VOL_AN[c] for c in TR.CATEGORIES])
ECH = np.array([TR.ECHELLE_DEVIS[c] for c in TR.CATEGORIES])
HT = np.array([c.ht for c in TR.CARAC])
F_LIEU_ARR = np.array([F_LIEU.get(t, 1.0) for t in ("capitale", "ville", "village", "autre")])
TYPES = {"capitale": 0, "ville": 1, "village": 2}


def valeur_vehicule(jour, m, ne, km):
    age = np.maximum(0.0, (jour - ne) / JOURS_AN)
    us = np.minimum(1.0, np.maximum(0.0, km / TR.VIE_KM[m]))
    return HT[m] * np.maximum(TR.PLANCHER_VALEUR, TR.DEPREC_1 * TR.DEPREC_AN ** age) * (1.0 - 0.25 * us)


def prime_auto(jour, m, ne, km, tl, bm, agec, gar):
    """Prime technique annuelle ( drachmes HT ) : la perte attendue de chaque garantie, d apres les statistiques
    publiques du marche ( domaine 14 ) et ce que l assureur observe, sur le ratio vise, plus les frais du contrat."""
    m = np.asarray(m, np.int64); cat = TR.CAT_IDX[m]
    val = valeur_vehicule(jour, m, np.asarray(ne, float), np.asarray(km, float))
    f = F_LIEU_ARR[tl] * (1.0 + BM_PAS * np.asarray(bm, float)) * np.where(np.asarray(agec) < AGE_JEUNE, F_JEUNE, 1.0)
    fm, fc = FREQ_MAT[cat] * f, FREQ_CORP[cat] * f
    r = TR.RESPONSABLE
    corp = TR.VICTIMES_PAR_ACCIDENT * COUT_BLESSE + MORT_ACC[cat] * COUT_DECES
    e = fm * r * COUT_MATERIEL + fc * r * corp
    gar = np.asarray(gar)
    e = e + np.where(gar & VOL, VOL_C[cat] * (1.0 - TR.RETROUVE) * val * (1.0 - FRANCHISE_VOL), 0.0)
    e = e + np.where(gar & DOMMAGES, fm * (1.0 - r) * np.maximum(0.0, COUT_MATERIEL * ECH[cat] - FRANCHISE_DOMMAGES)
                     + fc * (1.0 - r) * DETRUIT[cat] * val, 0.0)
    return e / LR_CIBLE + FRAIS_FIXES, val


def prime_hab(si, annee_b, gar):
    si = np.asarray(si, float)
    vuln = np.where(np.asarray(annee_b) < ANNEE_CODE, F_VULN, 1.0)
    e = TAUX_INCENDIE_AN * DEGAT_INCENDIE * si + np.where(np.asarray(gar) & SEISME, PAE_SEISME * vuln * si, 0.0)
    return e / LR_CIBLE + FRAIS_FIXES


def perte_sante(age, nch):
    """Perte attendue par personne et par an : sejours attendus ( domaine 16 : ~ 1 jour d hopital par an, trois apres
    65 ans, + 50 % par maladie chronique ) x part en clinique x participation du malade x remboursement."""
    jours = np.where(np.asarray(age) < 65.0, 1.0, 3.0) * (1.0 + 0.5 * np.asarray(nch, float))
    return jours / DUREE_SEJOUR_J * P_CLINIQUE * HO.PARTICIPATION_CLINIQUE * (HO.KEN_SEJOUR + 0.2 * HO.KEN_CHIRURGIE) * REMB_SANTE


def _nch(bits):
    b = np.asarray(bits, np.int64)
    return sum(((b >> k) & 1) for k in range(8))


# ================================================================== la decision
def _observer(ctx): return ctx.traits


def _regle(x, ctx):
    """Le niveau le plus proche ( en rapport ) de la prime technique ; refus au-dela de REFUS_RATIO, ou d un nouveau
    client par un assureur insolvable."""
    if ctx.ratio > REFUS_RATIO or (ctx.nouveau and not ctx.solvable): return 0
    return _niveau_marche(ctx.ratio)


def _temoin(x, ctx, rng): return I_UNIQUE


POINT_TARIF = D.PointDeDecision(
    "tarifer", "assurances", TRAITS, ACTIONS, _observer, _regle, _temoin,
    "pour CE contrat, chaque jour : prime acquise nette de frais moins sinistres payes ( bornes ) sur la prime de "
    "reference, plus 1 s il couvre ; -2 ( auto ) ou -1 s il ne couvre pas un besoin qui existe ; 0 sans besoin",
    horizon_j=HORIZON)


# ================================================================== aides
def _classe_menages(tb, M):
    """La meilleure classe des membres vivants de chaque menage ( 0 aisee ... 2 populaire ; 2 si vide )."""
    n = tb.n
    mi = PO.menages_inscrits(tb, n)
    ok = (tb.vivant[:n] == 1) & (mi >= 0)
    cl = np.full(M, 2, np.int64)
    np.minimum.at(cl, mi[ok], tb.classe[:n][ok].astype(np.int64))
    return cl


def _vivants_par_menage(tb, M):
    n = tb.n
    mi = PO.menages_inscrits(tb, n)
    ok = (tb.vivant[:n] == 1) & (mi >= 0)
    return np.bincount(mi[ok], minlength=M)[:M]


def _age_cond(p, k):
    """L age du plus jeune conducteur declare ( adulte titulaire d un permis ) du menage k ; 45 ans si aucun."""
    tb = p.w.table; nj = p.col("habitant", "naissance_j"); pm = p.col("habitant", "vh_permis")
    a = 999.0
    for i in tb.menages.membres_ids(k):
        if not tb.vivant[i] or not pm[i]: continue
        x = (p.jour - int(nj[i])) / JOURS_AN
        if x >= 18.0: a = min(a, x)
    return a if a < 999.0 else 45.0


def _ages_sante(p, k):
    tb = p.w.table; nj = p.col("habitant", "naissance_j"); ch = p.col("habitant", "med_chroniques")
    ids = [i for i in tb.menages.membres_ids(k) if tb.vivant[i]]
    return np.array([(p.jour - int(nj[i])) / JOURS_AN for i in ids]), np.array([int(ch[i]) for i in ids], np.int64)


def _type_lieu(p, D, dom):
    return D.type_lieu[np.maximum(dom, 0)]


def _tirer_assureur(D, u, exclure=-1):
    vivants = [a for a in D.assureurs if a.vivant and a.id != exclure]
    if not vivants: return -1
    s = np.cumsum([a.part for a in vivants]); s = s / s[-1]
    return vivants[int(np.searchsorted(s, u, side="right").clip(0, len(vivants) - 1))].id


def _ref(D, br, gar, unites):
    return D.base[(br, int(gar))] * (unites if br == SANTE else 1.0)


def _ptr(br, slot):
    return f"as_auto{slot}" if br == AUTO else ("as_hab" if br == HAB else "as_sante")


# ================================================================== souscriptions et renouvellements ( 9 h )
def _tirer_propensions(p, D, M):
    """Les menages nouveaux ( nes d un divorce, immigres ) recoivent leur propension cachee."""
    pr = p.col("menage", "as_prop")
    neufs = np.nonzero((pr[:M] & 128) == 0)[0]
    if len(neufs) == 0: return
    cl = _classe_menages(p.w.table, M)[neufs]
    u = p.du_jour("assurances_propension").random((3, len(neufs)))
    b = np.full(len(neufs), 128, np.int64)
    b |= np.where(u[0] >= PART_NON_ASSURES * NON_ASSURE_CLASSE[cl], 1, 0)
    b |= np.where(u[1] < PART_HAB[cl], 2, 0)
    b |= np.where(u[2] < PART_SANTE[cl], 4, 0)
    pr[neufs] = b.astype(np.uint8)


def _resilier(p, D, r, motif="resiliation"):
    """Le contrat de la ligne r prend fin avant son terme : ristourne de la prime non acquise, moins la retenue."""
    T = D.T; L = p.socle.livre
    if T.etat[r] != ACTIF: return
    mg = int(T.menage[r]); a = D.assureurs[int(T.assureur[r])]
    reste = max(0, int(T.fin[r]) - p.jour) / max(1, int(T.fin[r]) - int(T.debut[r]))
    x = float(T.prime[r]) * reste * (1.0 - FRAIS_ANNULATION)
    dis = int(p.col("menage", "dissous")[mg])
    if x > EPS and a.vivant and not dis:
        y = L.transferer(a, p.w.menages[mg], x, "ristourne_prime"); D.cpt["ristourne_prime"] += y
    col = p.col("menage", _ptr(int(T.branche[r]), int(T.slot[r])))
    if col[mg] == r: col[mg] = -1
    T.etat[r] = RESILIE; T.fin[r] = p.jour
    p.compter("resiliation")


def _candidats(p, D, M):
    """Les decisions du jour : renouvellements ( lignes echues ) puis besoins nouveaux, par branche. Rend une liste de
    ( branche, menage, emplacement, ligne ou -1, objet )."""
    T = D.T; n = T.n; cm = p.colonnes["menage"]; j = p.jour
    dis = cm["dissous"][:M] == 1; pr = cm["as_prop"][:M]
    out = []
    ren = np.nonzero((T.etat[:n] == ACTIF) & (T.fin[:n] <= j))[0]
    for r in ren.tolist():
        out.append((int(T.branche[r]), int(T.menage[r]), int(T.slot[r]), r, int(T.objet[r])))
    ra, rv = cm["as_retry"][:M] <= j, cm["as_retry_v"][:M] <= j
    for k in TR.K3:
        vm = cm[f"vh_m{k}"][:M]
        for i in np.nonzero((vm >= 0) & (cm[f"as_auto{k}"][:M] < 0) & ((pr & 1) != 0) & ra & ~dis)[0].tolist():
            out.append((AUTO, i, k, -1, int(cm[f"vh_ne{k}"][i])))
    st, lg = cm["im_statut"][:M], cm["im_logement"][:M]
    for i in np.nonzero((st == IM.PROPRIETAIRE) & (lg >= 0) & (cm["as_hab"][:M] < 0) & ((pr & 2) != 0) & rv & ~dis)[0].tolist():
        out.append((HAB, i, -1, -1, int(lg[i])))
    tb = p.w.table
    for i in np.nonzero((cm["as_sante"][:M] < 0) & ((pr & 4) != 0) & rv & ~dis)[0].tolist():
        if any(tb.vivant[x] for x in tb.menages.membres_ids(i)): out.append((SANTE, i, -1, -1, -1))
    return out


def _profil(p, D, br, i, k, r, objet, rng):
    """Le profil observable d un candidat : ( prime technique, garanties, franchise, plafond, unites, age, valeur,
    modele ). Les garanties demandees : celles du contrat en cours, sinon tirees ( choix du menage )."""
    cm = p.colonnes["menage"]; j = p.jour; T = D.T
    if br == AUTO:
        m = int(cm[f"vh_m{k}"][i]); ne = int(cm[f"vh_ne{k}"][i]); km = float(cm[f"vh_km{k}"][i])
        if r >= 0: gar = int(T.garanties[r])
        else:
            age_v = (j - ne) / JOURS_AN
            gar = RC | (VOL if rng.random() < P_VOL_OPTION else 0)
            if rng.random() < (P_DOMMAGES_NEUF if age_v < AGE_NEUF else P_DOMMAGES_VIEUX): gar |= VOL | DOMMAGES
        agec = _age_cond(p, i)
        tl = int(_type_lieu(p, D, np.array([int(p.w.table.menages.domicile[i])]))[0])
        tech, val = prime_auto(j, np.array([m]), np.array([ne]), np.array([km]), np.array([tl]),
                               np.array([int(cm["as_bm"][i])]), np.array([agec]), np.array([gar]))
        return float(tech[0]), gar, FRANCHISE_DOMMAGES, float(val[0]), 1.0, agec, float(val[0]), m, ne
    if br == HAB:
        d13 = IM._dom(p); b = objet
        si = float(d13.B["surface"][b]) * IM.cout_m2()
        an = int(d13.B["annee"][b])
        gar = int(T.garanties[r]) if r >= 0 else INCENDIE | (SEISME if rng.random() < P_SEISME_OPTION else 0)
        tech = float(prime_hab(np.array([si]), np.array([an]), np.array([gar]))[0])
        return tech, gar, FRANCHISE_INCENDIE, si, 1.0, float(IM.annee(p) - an), si, -1, b
    ages, ch = _ages_sante(p, i)
    u = max(1, len(ages))
    tech = float(perte_sante(ages, _nch(ch)).sum()) / LR_CIBLE + FRAIS_FIXES if len(ages) else FRAIS_FIXES
    return tech, HOSPI, 0.0, PLAFOND_SANTE * u, float(u), float(ages.mean()) if len(ages) else 40.0, 0.0, -1, -1


def _souscrire(p):
    """9 h : les contrats des vehicules vendus, des logements quittes et des menages dissous sont resilies ; un vehicule
    change garde son contrat ; puis chaque renouvellement et chaque besoin nouveau passe par la decision de l assureur
    et par le choix du menage."""
    D = _dom(p); w = p.w; tb = w.table; M = tb.menages.n; T = D.T; cm = p.colonnes["menage"]; L = p.socle.livre
    _tirer_propensions(p, D, M)
    dis = cm["dissous"][:M] == 1
    for k in TR.K3:
        c = cm[f"as_auto{k}"][:M]; vm = cm[f"vh_m{k}"][:M]
        has = c >= 0
        for i in np.nonzero(has & ((vm < 0) | dis))[0].tolist(): _resilier(p, D, int(c[i]))
        ch = np.nonzero(has & (vm >= 0))[0]
        if len(ch):
            rr = c[ch]
            T.objet[rr] = cm[f"vh_ne{k}"][ch]; T.modele[rr] = vm[ch]
    c = cm["as_hab"][:M]; has = c >= 0
    gone = has & ((cm["im_statut"][:M] != IM.PROPRIETAIRE) | (cm["im_logement"][:M] != T.objet[np.maximum(c, 0)]) | dis)
    for i in np.nonzero(gone)[0].tolist(): _resilier(p, D, int(c[i]))
    c = cm["as_sante"][:M]
    for i in np.nonzero((c >= 0) & dis)[0].tolist(): _resilier(p, D, int(c[i]))
    cands = _candidats(p, D, M)
    if not cands: return
    rng = p.hasard("assurances_garanties")
    u = p.du_jour("assurances_acceptation").random((3, len(cands)))
    rev = cm["eco_revenu"]
    dec = D.decideur
    for q, (br, i, k, r, objet) in enumerate(cands):
        mg = w.menages[i]
        tech, gar, fr, pl, unites, age, val, modele, obj = _profil(p, D, br, i, k, r, objet, rng)
        nouveau = r < 0
        if nouveau:
            a = _tirer_assureur(D, float(u[1, q]))
            if a < 0: continue
            r = T.nouvelle()
            T.branche[r] = br; T.menage[r] = i; T.slot[r] = k; T.assureur[r] = a; T.objet[r] = obj
            T.modele[r] = modele; T.garanties[r] = gar
        A = D.assureurs[int(T.assureur[r])]
        ref = _ref(D, br, gar, unites)
        ratio = tech / ref
        x = (1.0 if br == AUTO else 0.0, 1.0 if br == HAB else 0.0, min(1.0, ratio / REFUS_RATIO),
             min(1.0, int(cm["as_bm"][i]) / BM_MAX) if br == AUTO else 0.0, min(1.0, max(0.0, age) / 100.0),
             min(1.0, val / (5.0 * max(D.base[("valeur", br)], EPS))) if br != SANTE else min(1.0, unites / 8.0),
             0.0 if nouveau else 1.0, min(1.0, max(0.0, A.ratio) / 4.0))
        niveau = dec.decider(int(r), ContexteTarif(x, ratio, nouveau, A.ratio >= 1.0 or A.scr <= 0))
        p.compter("decision_tarif")
        prime = MULT[niveau] * ref
        T.note_j[r] = p.jour + HORIZON; T.niveau[r] = niveau; T.ref[r] = ref      # la cloture tombe au jour suivant
        if not nouveau:                                           # la periode ecoulee devient la precedente
            T.p_debut[r] = T.debut[r]; T.p_fin[r] = T.fin[r]; T.p_gar[r] = T.garanties[r]; T.p_menage[r] = T.menage[r]
            if br == AUTO:
                if T.fautes[r] == 0: cm["as_bm"][i] = max(0, int(cm["as_bm"][i]) - 1)
                T.fautes[r] = 0
        ttc = prime * (1.0 + TAXE[br])
        marche = MULT[_niveau_marche(ratio)] * ref              # ce que les concurrents coteraient ( leur regle )
        compare = float(u[2, q]) < P_COMPARER and ratio <= REFUS_RATIO
        dispo = IM.disponible(p, mg)
        pa = 1.0 / (1.0 + (ttc / (max(float(rev[i]), 1.0) * JOURS_AN) / R50[br]) ** 2)
        col = cm[_ptr(br, k)]
        if niveau > 0 and A.vivant and not (compare and prime > CONCURRENCE * marche):
            if float(u[0, q]) < pa and dispo >= ttc - EPS:
                _activer(p, D, r, A, prime, fr, pl, unites, nouveau)
                continue
            p.compter("refus_menage")
            B = None
        else:
            p.compter("refus_assureur" if niveau == 0 or not A.vivant else "depart_concurrent")
            B = _tirer_assureur(D, float(u[1, q]), A.id) if compare else -1
        T.etat[r] = SANS                                          # sans contrat chez cet assureur
        if not nouveau: T.fin[r] = p.jour
        if col[i] == r: col[i] = -1
        ttc_m = marche * (1.0 + TAXE[br])
        pa_m = 1.0 / (1.0 + (ttc_m / (max(float(rev[i]), 1.0) * JOURS_AN) / R50[br]) ** 2)
        if B is not None and B >= 0 and float(u[0, q]) < pa_m and dispo >= ttc_m - EPS:
            r2 = T.nouvelle()                                     # le concurrent l assure au prix du marche
            T.branche[r2] = br; T.menage[r2] = i; T.slot[r2] = k; T.assureur[r2] = B; T.objet[r2] = T.objet[r]
            T.modele[r2] = T.modele[r]; T.garanties[r2] = gar; T.ref[r2] = ref; T.niveau[r2] = _niveau_marche(ratio)
            _activer(p, D, r2, D.assureurs[B], marche, fr, pl, unites, True)
            continue
        if br == AUTO: cm["as_retry"][i] = p.jour + RETRY[0]
        else: cm["as_retry_v"][i] = p.jour + RETRY[1]


def _niveau_marche(ratio):
    """Le niveau que la regle du marche cote pour une prime technique de `ratio` fois la reference."""
    lr = math.log(max(ratio, 1e-6))
    return min(range(1, len(MULT)), key=lambda a: abs(math.log(MULT[a]) - lr))


def _activer(p, D, r, A, prime, fr, pl, unites, nouveau):
    """La ligne r devient un contrat actif d un an chez A : le menage paie la prime et la taxe ; l assureur verse la
    contribution au fonds ( auto ) ou cede la quote-part ( habitation )."""
    T = D.T; L = p.socle.livre; w = p.w
    br = int(T.branche[r]); i = int(T.menage[r]); mg = w.menages[i]
    y = L.transferer(mg, A, prime, "prime_assurance"); D.cpt["prime_assurance"] += y
    t = L.transferer(mg, w.gouv, prime * TAXE[br], "taxe_primes_assurance"); D.cpt["taxe_primes_assurance"] += t
    if br == AUTO:
        f = L.transferer(A, D.fonds, CONTRIB_FONDS * y, "contribution_fonds_garantie")
        D.cpt["contribution_fonds_garantie"] += f
    elif br == HAB:
        _ceder(p, D, A, y)
    T.etat[r] = ACTIF; T.debut[r] = p.jour; T.fin[r] = p.jour + DUREE_J; T.prime[r] = prime
    T.franchise[r] = fr; T.plafond[r] = pl; T.unites[r] = unites; T.encaisse[r] = y; T.paye[r] = 0.0
    p.col("menage", _ptr(br, int(T.slot[r])))[i] = r
    A.resultat += y * (1.0 - FRAIS)
    p.compter("souscription" if nouveau else "renouvellement", y)


def _ceder(p, D, A, prime):
    """La quote-part habitation : la part cedee de la prime, moins la commission du reassureur, part a l etranger."""
    x = QP_HAB * _reass(D, A) * prime * (1.0 - COMMISSION_CESSION)
    if x > EPS:
        y = EXT.payer_reassurance(p, A, x); D.cpt["prime_reassurance"] += y


# ================================================================== les sinistres
def _nouvelle_decl(p, D, br, nature, payeur, jour):
    d = Declaration(D.prochain, br, nature, payeur, jour); D.prochain += 1
    return d


def _lier(D, d, r):
    """La declaration cite le contrat de la ligne r, avec la periode qui couvre le jour du sinistre."""
    T = D.T
    d.contrat = int(r); d.assure = int(T.menage[r])
    if T.fin[r] > T.debut[r] and T.debut[r] <= d.jour <= T.fin[r]: d.c_debut, d.c_fin, d.c_gar = int(T.debut[r]), int(T.fin[r]), int(T.garanties[r])
    else: d.c_debut, d.c_fin, d.c_gar, d.assure = int(T.p_debut[r]), int(T.p_fin[r]), int(T.p_gar[r]), int(T.p_menage[r])
    T.refs[r] += 1


def _couvre(D, r, jour, bit, menage=None):
    """Vrai si la ligne r couvrait `bit` le jour `jour`, bornes comprises ( periode en cours, ou precedente ). Une
    periode vide ( ligne refusee, jamais active ) ne couvre rien."""
    if r is None or r < 0: return False
    T = D.T
    if r >= T.n or T.etat[r] == LIBRE: return False
    if T.fin[r] > T.debut[r] and T.debut[r] <= jour <= T.fin[r] and T.garanties[r] & bit \
            and (menage is None or T.menage[r] == menage):
        return True
    return bool(T.p_fin[r] > T.p_debut[r] and T.p_debut[r] <= jour <= T.p_fin[r] and T.p_gar[r] & bit
                and (menage is None or T.p_menage[r] == menage))


def _parts_reassurance(D, d):
    """La part du sinistre que les reassureurs rendront : la quote-part habitation, puis l excedent par risque au-dela
    de la retention de l assureur ( l excedent seisme par evenement s y ajoute apres )."""
    if d.payeur < 0: d.part_qp = d.part_xl = 0.0; return
    f = _reass(D, D.assureurs[d.payeur])
    d.part_qp = QP_HAB * f if d.branche == HAB else 0.0
    net = d.estime * (1.0 - d.part_qp)
    d.part_xl = f * max(0.0, net - D.assureurs[d.payeur].retention) / d.estime if d.estime > 0 else 0.0


def _ouvrir(p, D, d, estime):
    """La declaration entre au portefeuille des sinistres : le payeur provisionne `estime`."""
    d.estime = max(0.0, float(estime))
    _parts_reassurance(D, d)
    _payeur(D, d.payeur).psap += d.estime
    D.ouverts[d.id] = d
    p.compter("sinistre_declare", d.estime)
    return d


def _fraude(p, D, d, nature):
    """L assure gonfle-t-il sa declaration ? La verite cachee du sinistre ( jamais lue par l expert )."""
    pf = P_FRAUDE.get(nature, 0.0) * D.scenario["fraude"]
    rng = p.hasard("assurances_fraude")
    if pf > 0 and rng.random() < pf:
        d.fraude = True; d.declare = d.vrai * (1.3 + 0.7 * rng.random())
    else: d.declare = d.vrai


def _tiers(p, D, victime):
    """Le vehicule responsable d un accident subi : tire dans le pays, pondere par le risque de sa categorie. Rend
    ( menage, emplacement ) ou None."""
    cm = p.colonnes["menage"]; M = p.w.table.menages.n
    rng = p.hasard("assurances_tiers")
    for _ in range(200):
        i = int(rng.integers(0, M)); k = int(rng.integers(0, 3))
        m = int(cm[f"vh_m{k}"][i])
        if m < 0 or i == victime or cm["dissous"][i]: continue
        if rng.random() * FREQ_MAT.max() < FREQ_MAT[TR.CAT_IDX[m]]: return i, k
    return None


def _payeur_rc(p, D, d, victime):
    """Le payeur de la responsabilite civile d un tiers : son assureur, sinon le fonds de garantie."""
    t = _tiers(p, D, victime)
    cm = p.colonnes["menage"]
    if t is not None:
        i, k = t
        r = int(cm[f"as_auto{k}"][i])
        if r >= 0 and D.T.etat[r] == ACTIF and D.assureurs[int(D.T.assureur[r])].vivant:
            d.payeur = int(D.T.assureur[r]); _lier(D, d, r); d.garantie = RC
            cm["as_bm"][i] = min(BM_MAX, int(cm["as_bm"][i]) + 1); D.T.fautes[r] += 1
            return True
    d.payeur = FONDS; d.tiers_non_assure = True; d.garantie = RC
    p.compter("recours_fonds_garantie")
    return True


def _contrat_auto(p, D, i, k):
    if k is None or k < 0: return -1
    r = int(p.col("menage", f"as_auto{k}")[i])
    return r


def _decl_materielle(p, D, s, ttc_connu=None):
    """La part materielle d un accident ( reparation au garage ) : responsabilite civile du tiers si le menage n est
    pas responsable, sa garantie dommages sinon. Rend la declaration ou None ( non couvert )."""
    tr = TR._tr(p)
    cle = ("tr_mat", s.id)
    if cle in D.par_source: return D.ouverts.get(D.par_source[cle])
    mg = s.proprietaire
    if type(mg).__name__ != "Menage": return None
    i = mg.id
    tva = TR._tva(p)
    ttc = float(ttc_connu) if ttc_connu is not None else float(s.dommage) * (1.0 + tva)
    slot = tr.slot_de.get(s.objet, (i, -1))[1]
    d = _nouvelle_decl(p, D, AUTO, "rc_materiel" if not s.responsable else "dommages", -1, s.jour)
    d.source = s.id; d.benef = i; d.objet = s.objet; d.vrai = d.declare = ttc
    if not s.responsable:
        _payeur_rc(p, D, d, i); du = ttc
    else:
        r = _contrat_auto(p, D, i, slot)
        if not _couvre(D, r, s.jour, DOMMAGES, i):
            D.non_couverts.append((s.jour, i, "dommages", ttc, s.objet)); p.compter("sinistre_non_couvert")
            D.par_source[cle] = -1
            return None
        d.payeur = int(D.T.assureur[r]); _lier(D, d, r); d.garantie = DOMMAGES
        du = max(0.0, ttc - FRANCHISE_DOMMAGES)
        if du <= EPS:
            D.T.refs[r] -= 1; p.compter("sinistre_sous_franchise"); D.par_source[cle] = -1
            return None
    d.etat = ATTENTE_GARAGE; d.echeance_j = s.jour + ATTENTE_GARAGE_J
    D.par_source[cle] = d.id
    return _ouvrir(p, D, d, du)


def couvrir(p, s, ttc):
    """Domaine 14 : la part TTC d une reparation que les assureurs prennent en charge. Ils ne paient le garage que
    le lendemain, et seulement si la reparation a ete lancee ( sinon le menage n a pas pu payer sa part : rien n est
    du, la declaration attend )."""
    D = _dom(p)
    d = _decl_materielle(p, D, s, ttc)
    if d is None or d.etat != ATTENTE_GARAGE: return 0.0
    if abs(d.vrai - ttc) > EPS:                          # le devis du garage fait l expertise
        du = ttc if d.garantie == RC else max(0.0, ttc - FRANCHISE_DOMMAGES)
        P = _payeur(D, d.payeur); P.psap += du - d.estime; d.estime = du; d.vrai = d.declare = ttc
        _parts_reassurance(D, d)
    p.poser(0, "assurances_garage", d.id)
    return d.estime


def _payer_garage(p, cle, donnees):
    """Le pas suivant : la reparation est-elle lancee ? L assureur paie alors au garage la part couverte ( HT ) et la
    TVA correspondante au Tresor."""
    D = _dom(p); d = D.ouverts.get(cle)
    if d is None or d.etat != ATTENTE_GARAGE: return
    tr = TR._tr(p)
    rp = tr.reparations.get(d.objet)
    if rp is None or not rp.en_cours or rp.sinistre != d.source: return
    tva = TR._tva(p)
    ht = d.estime / (1.0 + tva)
    _regler(p, D, d, rp.garage, ht, tva_ht=ht)


def _regler(p, D, d, vers, montant, tva_ht=0.0):
    """Paie une declaration : recupere d abord la part du reassureur, puis paie `montant` a `vers` ( et la TVA de
    `tva_ht` au Tresor ). La provision tombe de ce qui est paye ; la declaration se clot quand tout est paye."""
    L = p.socle.livre; P = _payeur(D, d.payeur)
    if not getattr(P, "vivant", True):
        return
    brut = montant + (tva_ht * ET.taux_tva(p, "pieces_auto") if tva_ht > 0 else 0.0)
    if d.payeur >= 0 and d.part_qp + d.part_xl > 0:            # la part des reassureurs de tout ce qui aura ete paye
        du_r = (d.part_qp + d.part_xl) * (d.paye + brut) - d.recupere
        if du_r > EPS:
            y = EXT.recevoir_reassurance(p, P, du_r); D.cpt["indemnite_reassurance"] += y; d.recupere += y
    if d.payeur == ELGA_P and P.caisse < montant:
        manque = montant - P.caisse
        ET.assurer(p, manque)
        y = L.transferer(p.w.gouv, P, manque, "dotation_elga"); D.cpt["dotation_elga"] += y; P.dotations += y
    motif = "indemnite_elga" if d.payeur == ELGA_P else "indemnite_assurance"
    x = L.transferer(P, vers, montant, motif)
    t = ET.percevoir_tva(p, P, "pieces_auto", tva_ht * x / montant) if tva_ht > 0 and montant > 0 else 0.0
    D.cpt[motif] += x
    if motif == "indemnite_assurance": D.cpt["sinistres_ht"] += x
    else: P.indemnites += x
    tout = x + t
    d.paye += tout; d.tva += t
    P.psap -= min(d.estime, tout); d.estime = max(0.0, d.estime - tout)
    if d.payeur >= 0: D.assureurs[d.payeur].resultat -= tout
    if d.contrat >= 0: D.T.paye[d.contrat] += tout; D.paye_jour[d.contrat] = D.paye_jour.get(d.contrat, 0.0) + tout
    if d.estime <= TOL:
        P.psap -= d.estime; d.estime = 0.0
        _clore(p, D, d, PAYE)
        p.compter("sinistre_paye", d.paye)


def _clore(p, D, d, etat):
    d.etat = etat
    D.ouverts.pop(d.id, None)
    if d.contrat >= 0: D.T.refs[d.contrat] -= 1
    if etat == PAYE: D.payes.append(d)


def _decl_especes(p, D, br, nature, payeur_r, i, jour, vrai, franchise, plafond, garantie, source, delai, fraude=False,
                  objet=-1):
    """Une declaration payee en especes a l assure ( corporel, vol, vehicule detruit, logement, sante )."""
    d = _nouvelle_decl(p, D, br, nature, -1, jour)
    d.benef = i; d.source = source; d.vrai = float(vrai); d.objet = objet
    if fraude: _fraude(p, D, d, nature)
    else: d.declare = d.vrai
    d.garantie = garantie
    if payeur_r == "rc":
        _payeur_rc(p, D, d, i)
    else:
        r = payeur_r
        d.payeur = int(D.T.assureur[r]); _lier(D, d, r)
    d.plafond = float(plafond)
    du = max(0.0, min(d.declare, plafond) - franchise)
    if du <= EPS:
        if d.contrat >= 0: D.T.refs[d.contrat] -= 1
        p.compter("sinistre_sous_franchise"); return None
    d.echeance_j = p.jour + delai
    return _ouvrir(p, D, d, du)


def _declarer_transport(p, D):
    """Les accidents et vols du domaine 14 depuis la veille. La part materielle d un accident passe par le garage
    ( `couvrir`, appele a la reparation ) ; si aucune reparation n a ete tentee ( vehicule detruit ou abandonne ),
    elle est indemnisee en especes. La part corporelle : les victimes, indemnisees en especes. Un vol : la valeur
    venale apres l enquete, si le vehicule n est pas retrouve."""
    tr = TR._tr(p)
    ss = tr.sinistres
    for s in ss[D.vu_tr:]:
        mg = s.proprietaire
        if type(mg).__name__ != "Menage": continue
        i = mg.id
        slot = _slot_vehicule(p, D, s, i)
        if s.type in ("materiel", "corporel"):
            cle = ("tr_mat", s.id)
            if cle not in D.par_source and s.dommage > 0:
                D.par_source[cle] = -1
                if not s.responsable:
                    _decl_especes(p, D, AUTO, "auto_especes", "rc", i, s.jour, s.dommage, 0.0, math.inf, RC, s.id,
                                  DELAI["auto_especes"], objet=s.objet)
                else:
                    r = _contrat_auto(p, D, i, slot)
                    if _couvre(D, r, s.jour, DOMMAGES, i):
                        _decl_especes(p, D, AUTO, "auto_especes", r, i, s.jour, s.dommage, FRANCHISE_DOMMAGES, math.inf,
                                      DOMMAGES, s.id, DELAI["auto_especes"], objet=s.objet)
                    else: D.non_couverts.append((s.jour, i, "dommages", float(s.dommage), s.objet)); p.compter("sinistre_non_couvert")
        if s.type == "corporel":
            blesses = max(0, int(s.victimes) - int(s.tues))
            vrai = blesses * COUT_BLESSE + int(s.tues) * COUT_DECES
            if s.responsable: vrai *= max(0, int(s.victimes) - 1) / max(1, int(s.victimes))   # le conducteur fautif n est pas son propre tiers
            if vrai > EPS:
                if not s.responsable:
                    _decl_especes(p, D, AUTO, "corporel", "rc", i, s.jour, vrai, 0.0, math.inf, RC, s.id, DELAI["corporel"], True, s.objet)
                else:
                    r = _contrat_auto(p, D, i, slot)
                    if _couvre(D, r, s.jour, RC, i):
                        _decl_especes(p, D, AUTO, "corporel", r, i, s.jour, vrai, 0.0, math.inf, RC, s.id, DELAI["corporel"], True, s.objet)
                    else: D.non_couverts.append((s.jour, i, "corporel", vrai, s.objet)); p.compter("sinistre_non_couvert")
        elif s.type == "vol":
            r = _contrat_auto(p, D, i, slot)
            if _couvre(D, r, s.jour, VOL, i):
                _decl_especes(p, D, AUTO, "vol", r, i, s.jour, s.dommage, FRANCHISE_VOL * s.dommage, math.inf, VOL,
                              s.id, TR.ENQUETE_J + DELAI["vol"], objet=s.objet)
            else: D.non_couverts.append((s.jour, i, "vol", float(s.dommage), s.objet)); p.compter("sinistre_non_couvert")
    D.vu_tr = len(ss)


def _slot_vehicule(p, D, s, i):
    """L emplacement du vehicule du sinistre : celui de son individu s il est encore chez le menage, sinon celui dont
    le contrat assurait ce modele ( un vehicule vole ou detruit a quitte l emplacement )."""
    tr = TR._tr(p)
    sd = tr.slot_de.get(s.objet)
    if sd is not None and sd[0] == i: return sd[1]
    f = tr.fiches.get(s.objet)
    cm = p.colonnes["menage"]
    for k in TR.K3:
        r = int(cm[f"as_auto{k}"][i])
        if r >= 0 and int(D.T.modele[r]) == int(s.modele) and (f is None or int(D.T.objet[r]) == int(f.ne)): return k
    return -1


def _seismes_du_jour(p, D):
    for e in p.socle.journal.derniers("seisme_dommages", 10000):
        D.vus_seisme.add((e["jour"], e["lieu"]))


def _declarer_immobilier(p, D):
    """Les sinistres des batiments ( seisme, incendie ) depuis la veille : un logement de proprietaire occupant assure
    est indemnise en especes a son proprietaire, apres expertise."""
    d13 = IM._dom(p); ss = d13.sinistres
    if D.vu_im >= len(ss): return
    _seismes_du_jour(p, D)
    cm = p.colonnes["menage"]
    jours = {}
    for jour, b, dommage, cout in ss[D.vu_im:]:
        o = IM.proprietaire(p, b)
        lieu = d13.lieux[int(d13.B["lieu"][b])]
        nature = "seisme" if (jour, lieu) in D.vus_seisme else "incendie"
        bit = SEISME if nature == "seisme" else INCENDIE
        if o is None or type(o).__name__ != "Menage": continue
        i = o.id
        r = int(cm["as_hab"][i])
        if r < 0 or int(D.T.objet[r]) != b or not _couvre(D, r, jour, bit, i):
            D.non_couverts.append((jour, i, nature, float(cout), b)); p.compter("sinistre_non_couvert"); continue
        fr = FRANCHISE_SEISME * float(D.T.plafond[r]) if nature == "seisme" else FRANCHISE_INCENDIE
        d = _decl_especes(p, D, HAB, nature, r, i, jour, cout, fr, float(D.T.plafond[r]), bit, b, DELAI[nature], True, b)
        if d is None: continue
        if nature == "seisme": jours.setdefault((jour, d.payeur), []).append(d)
    D.vu_im = len(ss)
    for (jour, a), ds in sorted(jours.items()):                   # l excedent de sinistre, par evenement et assureur
        A = D.assureurs[a]
        brut = math.fsum(d.estime for d in ds)
        retenu = math.fsum(d.estime * (1.0 - d.part_qp - d.part_xl) for d in ds)
        rec = min(A.xl_limite, max(0.0, retenu - A.xl_priorite)) * _reass(D, A)
        for d in ds: d.part_xl += rec / brut if brut > 0 else 0.0
        p.noter("catastrophe_assuree", assureur=A.nom, sinistres=len(ds), brut=round(brut, 2), recuperable=round(
            math.fsum(d.estime * (d.part_qp + d.part_xl) for d in ds), 2))


def _declarer_sante(p, D):
    """Les passages factures des jours clos : la participation d un malade de clinique couvert est remboursee."""
    H = HO._dom(p); j = p.jour
    lot = []
    for f in reversed(H.factures):
        if f[0] < D.jour_ho: break
        if f[0] < j: lot.append(f)
    D.jour_ho = j
    if not lot: return
    tb = p.w.table; cm = p.colonnes["menage"]
    for f in reversed(lot):
        jour, hid, _, prive, _, part = f[:6]
        if part <= 0: continue
        i = int(tb.menage[hid])
        if i < 0: continue
        r = int(cm["as_sante"][i])
        if not _couvre(D, r, jour, HOSPI, i):
            D.non_couverts.append((jour, i, "sante", float(part), int(hid))); continue
        reste = max(0.0, float(D.T.plafond[r]) - float(D.T.paye[r]))
        _decl_especes(p, D, SANTE, "sante", r, i, jour, REMB_SANTE * part, 0.0, reste, HOSPI, hid, DELAI["sante"], objet=int(hid))


def _declarer_recoltes(p, D):
    """Les campagnes closes : une perte climatique au-dela du seuil est indemnisee par ELGA ( 80 % de la valeur )."""
    AGm = AG
    A = p.domaine("agriculture"); cps = A.champs.campagnes; cat = p.socle.catalogue
    for idx in range(D.vu_ag, len(cps)):
        jour, g, c, ha, kg, perdu, fr, clim, eng = cps[idx]
        cu = AGm.CULTURES[c]
        if cu.bien is None or clim >= 1.0 - SEUIL_ELGA: continue
        perte_kg = (kg + perdu) * (1.0 - clim) / max(clim, 0.05)
        b = cat[cu.bien]
        vrai = COUV_ELGA * perte_kg / max(b.masse_kg, EPS) * D.prix_elga.get(cu.bien, b.prix_monde)
        d = _nouvelle_decl(p, D, -1, "recolte", ELGA_P, jour)
        d.ferme = g; d.source = idx; d.vrai = d.declare = vrai; d.echeance_j = p.jour + DELAI_ELGA_J
        _ouvrir(p, D, d, vrai)
    D.vu_ag = len(cps)


def _expertiser(p, D):
    """Les declarations arrivees a echeance : expertise ( fraude soupconnee : refus et signalement a la justice ),
    puis paiement ; un vehicule jamais repare est indemnise en especes ; un vol retrouve n est pas indemnise."""
    j = p.jour; w = p.w
    rng = p.hasard("assurances_expertise")
    for d in [d for d in D.ouverts.values() if d.echeance_j <= j]:
        if d.etat == ATTENTE_GARAGE:
            d.etat = OUVERT                                     # jamais repare : especes au menage
        if d.nature == "vol":
            v = next((v for v in reversed(TR._tr(p).vols) if v.objet == d.objet and v.jour == d.jour), None)
            if v is not None and v.issue == "retrouve":
                _payeur(D, d.payeur).psap -= d.estime; d.estime = 0.0; _clore(p, D, d, SANS_SUITE); continue
        if not valide(p, D, d):
            D.invalides.append(d.id); _payeur(D, d.payeur).psap -= d.estime; d.estime = 0.0
            _clore(p, D, d, REFUSE); p.compter("sinistre_refuse"); continue
        if d.nature in P_FRAUDE:
            soupcon = rng.random() < (P_DETECTION if d.fraude else P_FAUSSE_ALERTE)
            if soupcon:
                _signaler(p, D, d)
                _payeur(D, d.payeur).psap -= d.estime; d.estime = 0.0
                _clore(p, D, d, REFUSE); p.compter("sinistre_refuse"); continue
        if d.payeur == ELGA_P:
            ex = p.domaine("agriculture").liste[d.ferme]
            _regler(p, D, d, ex.ferme, d.estime)
        elif d.benef >= 0:
            _regler(p, D, d, w.menages[d.benef], d.estime)


def _signaler(p, D, d):
    tb = p.w.table
    ids = [i for i in tb.menages.membres_ids(d.benef) if tb.vivant[i]] if d.benef >= 0 else []
    montant = d.declare - d.vrai if d.fraude else d.declare
    p.noter("fraude_signalee", declaration=d.id, menage=d.benef, montant=round(montant, 2), vraie=bool(d.fraude))
    D.stats["fraudes_vraies" if d.fraude else "fausses_alertes"] += 1
    if ids and p.a("justice"):
        JU = importlib.import_module(".d21_justice", __package__)
        JU.signaler_fraude_assurance(p, ids[0], _payeur(D, d.payeur), montant, 0.6, bool(d.fraude))


def valide(p, D, d):
    """Une declaration a-t-elle un payeur legitime ? Un assureur : un contrat qui couvrait la garantie au jour du
    sinistre ( periode enregistree dans la declaration ET ligne de la table ) ; le fonds : un tiers non assure ou un
    assureur liquide ; ELGA : une ferme."""
    if d.payeur == ELGA_P: return d.ferme >= 0 and d.nature == "recolte"
    if d.payeur == FONDS:
        if d.tiers_non_assure: return d.garantie == RC and d.contrat < 0
        if d.contrat < 0: return False
    if d.contrat < 0 or not (d.c_debut <= d.jour <= d.c_fin) or not (d.c_gar & d.garantie): return False
    return _couvre(D, d.contrat, d.jour, d.garantie, d.assure)


# ================================================================== ELGA
def _prix_elga(p, D):
    """Les prix de reference des cultures, fixes pour l annee ( ELGA indemnise aux prix indicatifs arretes chaque annee
    par le ministere, pas au cours du jour de la recolte )."""
    cat = p.socle.catalogue
    D.prix_elga = {cu.bien: float(cat[cu.bien].prix_monde) for cu in AG.CULTURES if cu.bien is not None}


def _elga_cotisations(p):
    """17 h 40, avant la paie : chaque ferme verse sa cotisation du jour ( ce que sa caisse ne paie pas devient une
    dette envers ELGA )."""
    D = _dom(p); L = p.socle.livre; E = D.elga
    for ex in p.domaine("agriculture").liste:
        x = TAUX_ELGA * ex.valeur_ref
        if x <= EPS: continue
        paye, _ = L.payer_ou_devoir(ex.ferme, E, x, "cotisation_elga", p.socle.creances, p.jour)
        D.cpt["cotisation_elga"] += paye; E.cotisations += paye
        if paye > 0: p.compter("cotisation_elga", paye)


# ================================================================== placements
def _placements(p):
    """10 h, tous les 30 jours : ce que la caisse a au-dela de sa reserve de liquidite part en bons du Tresor."""
    if (p.jour - _dom(p).jour_install) % 30: return
    D = _dom(p); L = p.socle.livre
    taux = ET.taux_des_bons(p)
    for A in D.assureurs:
        if not A.vivant: continue
        cible = LIQUIDITE * (A.psap + A.ppna) + 0.05 * sum(A.primes_an)
        x = A.caisse - cible
        if x < 0.02 * max(cible, 1.0): continue
        y = L.transferer(A, p.w.gouv, x, "placement_obligation"); D.cpt["placement_obligation"] += y
        o = Obligation(D.prochaine_oblig, A.id, y, y * taux * DUREE_OBLIG_J / JOURS_AN, p.jour + DUREE_OBLIG_J)
        D.prochaine_oblig += 1; D.obligations[o.id] = o; A.oblig += y
        p.poser(DUREE_OBLIG_J * PAS_J - 1, "assurances_obligation", o.id)
        p.compter("obligation_achetee", y)


def _obligation_echue(p, oid, donnees):
    D = _dom(p); L = p.socle.livre; w = p.w
    o = D.obligations.pop(oid, None)
    if o is None: return
    h = _payeur(D, o.detenteur)
    ET.assurer(p, o.prix + o.interet)
    x = L.transferer(w.gouv, h, o.prix, "remboursement_obligation"); D.cpt["remboursement_obligation"] += x
    y = L.transferer(w.gouv, h, o.interet, "coupon_obligation"); D.cpt["coupon_obligation"] += y
    h.oblig -= o.prix
    if o.detenteur >= 0: D.assureurs[o.detenteur].resultat += y
    if x + y < o.prix + o.interet - TOL:                  # le Tresor n a pas pu : le reste est represente demain
        o.prix -= x; o.interet -= y; h.oblig += o.prix; D.obligations[o.id] = o
        p.poser(PAS_J - 1, "assurances_obligation", o.id)


# ================================================================== solvabilite, faillite, notes : la cloture
def solvabilite(p, D=None):
    """Provisions pour primes non acquises, fonds propres, SCR et MCR de chaque assureur ( formule standard
    simplifiee ). Rend { assureur : ( fonds propres, scr, ratio ) }."""
    D = D or _dom(p); T = D.T; n = T.n; j = p.jour
    act = T.etat[:n] == ACTIF
    a = np.where(act, T.assureur[:n], 0).astype(np.int64)
    dur = np.maximum(1, T.fin[:n] - T.debut[:n])
    nonacq = np.where(act, T.prime[:n] * np.maximum(0, T.fin[:n] - j) / dur, 0.0)
    NA = len(D.assureurs)
    ppna = np.bincount(a, weights=nonacq, minlength=NA)
    br = T.branche[:n].astype(np.int64)
    primes = [np.bincount(a, weights=np.where(act & (br == b), T.prime[:n], 0.0), minlength=NA) for b in (AUTO, HAB, SANTE)]
    seis = act & (br == HAB) & ((T.garanties[:n] & SEISME) != 0)
    si = np.bincount(a, weights=np.where(seis, T.plafond[:n], 0.0), minlength=NA)
    rec = np.zeros(NA)
    for d in D.ouverts.values():
        if d.payeur >= 0: rec[d.payeur] += d.estime * (d.part_qp + d.part_xl)
    out = {}
    for A in D.assureurs:
        k = A.id
        A.ppna = float(ppna[k]); A.primes_an = [float(x[k]) for x in primes]
        A.si_seisme = float(si[k])
        f = _reass(D, A)
        retenu = A.si_seisme * (1.0 - QP_HAB * f)
        A.xl_priorite = XL_PRIORITE * retenu; A.xl_limite = XL_LIMITE * retenu
        cat = max(0.0, CAT_200 * retenu - A.xl_limite * f)
        prem = [SIGMA[b] * A.primes_an[b] for b in range(3)]
        A.scr = math.sqrt(sum(x * x for x in prem) + (SIGMA_RES * A.psap) ** 2 + cat * cat) + OP_RISQUE * sum(A.primes_an)
        A.mcr = MCR_PART * A.scr
        A.fp = A.caisse + A.oblig + float(rec[k]) - A.ppna - A.psap
        A.ratio = A.fp / A.scr if A.scr > EPS else 9.99
        out[A.nom] = (A.fp, A.scr, A.ratio)
    return out


def _liquider(p, D, A):
    """Faillite : fonds propres sous le MCR. Les contrats cessent ( la prime non acquise est perdue pour l assure,
    creance de liquidation non modelisee ) ; les sinistres ouverts, la caisse et les obligations passent au fonds de
    garantie, qui paie a la place ; les menages cherchent un autre assureur des le lendemain."""
    L = p.socle.livre; T = D.T; n = T.n; cm = p.colonnes["menage"]
    A.vivant = False; A.faillite_j = p.jour
    p.noter("faillite_assureur", assureur=A.nom, fonds_propres=round(A.fp, 2), scr=round(A.scr, 2))
    rows = np.nonzero((T.etat[:n] == ACTIF) & (T.assureur[:n] == A.id))[0]
    for r in rows.tolist():
        br = int(T.branche[r]); i = int(T.menage[r])
        col = cm[_ptr(br, int(T.slot[r]))]
        if col[i] == r: col[i] = -1
        T.etat[r] = RESILIE; T.fin[r] = p.jour
        cm["as_retry" if br == AUTO else "as_retry_v"][i] = p.jour + 1
    for d in D.ouverts.values():
        if d.payeur == A.id:
            A.psap -= d.estime; D.fonds.psap += d.estime; d.payeur = FONDS; d.part_qp = d.part_xl = 0.0
    A.psap = 0.0                                           # tout est parti : un reste n est que de l arrondi
    for o in D.obligations.values():
        if o.detenteur == A.id: o.detenteur = FONDS; A.oblig -= o.prix; D.fonds.oblig += o.prix
    y = L.transferer(A, D.fonds, A.caisse, "liquidation_assureur"); D.cpt["liquidation_assureur"] += y


def _noter(p, D):
    """Les notes du jour des decisions en attente ( vectorisees, puis une par ligne )."""
    T = D.T; n = T.n; j = p.jour; cm = p.colonnes["menage"]; M = p.w.table.menages.n
    rows = np.nonzero((T.note_j[:n] >= j) & (T.etat[:n] != LIBRE))[0]
    if len(rows) == 0: return
    br = T.branche[rows].astype(np.int64); mg = np.minimum(T.menage[rows], M - 1); sl = np.maximum(T.slot[rows], 0)
    dis = cm["dissous"][mg] == 1
    vh = np.stack([cm[f"vh_m{k}"][:M] for k in TR.K3])
    besoin = np.where(br == AUTO, vh[sl, mg] >= 0,
                      np.where(br == HAB, (cm["im_statut"][mg] == IM.PROPRIETAIRE) & (cm["im_logement"][mg] == T.objet[rows]), True)) & ~dis
    couvert = (T.etat[rows] == ACTIF) & (T.debut[rows] <= j) & (T.fin[rows] > j)
    ptr = np.where(br == AUTO, np.stack([cm[f"as_auto{k}"][:M] for k in TR.K3])[sl, mg],
                   np.where(br == HAB, cm["as_hab"][mg], cm["as_sante"][mg]))
    ailleurs = besoin & (ptr >= 0) & (ptr != rows)
    refj = np.maximum(T.ref[rows], EPS) / JOURS_AN
    paye = np.array([D.paye_jour.get(int(r), 0.0) for r in rows.tolist()])
    marge = ((1.0 - FRAIS) * T.prime[rows] / JOURS_AN - np.minimum(paye, CAP_JOURS * refj)) / refj + BONUS_COUVERT
    pen = np.array(PENALITE)[br]
    note = np.where(couvert, marge, np.where(ailleurs, BONUS_COUVERT, np.where(besoin, -pen, 0.0)))
    dec = D.decideur
    for r, x in zip(rows.tolist(), note.tolist()): dec.noter(r, x, j)


def _cloture(p, comptes):
    D = _dom(p); L = p.socle.livre; T = D.T
    for m, pa, re, s, _ in comptes["argent"]:
        if m in D.livre and _suivi(m, pa, re): D.livre[m] += s
    _noter(p, D)
    D.paye_jour = {}
    n = T.n
    for r in np.nonzero(((T.etat[:n] == SANS) | (T.etat[:n] == RESILIE)) & (T.note_j[:n] < p.jour) & (T.refs[:n] == 0))[0].tolist():
        T.liberer(r)
    solvabilite(p, D)
    for A in D.assureurs:
        if A.vivant and A.scr > EPS and A.fp < A.mcr: _liquider(p, D, A)
    ecoule = p.jour - D.jour_install
    if ecoule > 0 and ecoule % 30 == 0:                   # les primes des excedents de sinistre, chaque mois
        for A in D.assureurs:
            x = (XL_TAUX * A.xl_limite + XL_RISQUE_TAUX * sum(A.primes_an)) * 30.0 / JOURS_AN * _reass(D, A)
            if A.vivant and x > EPS:
                y = EXT.payer_reassurance(p, A, x); D.cpt["prime_reassurance"] += y; A.resultat -= y
            if A.vivant and A.fp > 0: A.retention = RETENTION * A.fp
    if ecoule > 0 and ecoule % 30 == 0:                   # la memoire des sinistres du domaine 14 deja vus
        ss = TR._tr(p).sinistres
        for cle in [c for c in D.par_source if ss[c[1]].jour < p.jour - 60]: del D.par_source[cle]
    if ecoule > 0 and ecoule % DUREE_J == 0:              # le dividende annuel aux maisons meres
        for A in D.assureurs:
            if A.vivant and A.ratio > DIVIDENDE_RATIO and A.resultat > 0:
                y = EXT.payer_en_devises(p, A, min(DIVIDENDE_PART * A.resultat, max(0.0, A.fp - DIVIDENDE_RATIO * A.scr)),
                                         "dividende_assureur")
                D.cpt["dividende_assureur"] += y
            A.resultat = 0.0
        _prix_elga(p, D)


def _matin(p):
    """8 h 50 : les sinistres de la veille ( et de la nuit ) sont declares, puis ceux qui sont a echeance expertises
    et payes. Avant 9 h : un contrat resilie a 9 h couvre encore le sinistre de la veille."""
    D = _dom(p)
    _declarer_transport(p, D)
    _declarer_immobilier(p, D)
    _declarer_sante(p, D)
    _declarer_recoltes(p, D)
    _expertiser(p, D)


# ================================================================== installation
def _portefeuille_initial(p, D):
    """Le portefeuille du jour 0 : les contrats en cours, souscrits au fil de l annee passee ( echeances etalees ),
    tarifes par la regle, primes deja payees ( avant le monde ). Tout vectorise."""
    w = p.w; tb = w.table; M = tb.menages.n; cm = p.colonnes["menage"]; T = D.T; j = p.jour
    rng = p.hasard("assurances_installation")
    cl = _classe_menages(tb, M)
    dis = cm["dissous"][:M] == 1
    pr = cm["as_prop"][:M]
    u = rng.random((3, M))
    pr[:] = (128 | np.where(u[0] >= PART_NON_ASSURES * NON_ASSURE_CLASSE[cl], 1, 0) | np.where(u[1] < PART_HAB[cl], 2, 0)
             | np.where(u[2] < PART_SANTE[cl], 4, 0)).astype(np.uint8)
    n = tb.n
    nj = p.col("habitant", "naissance_j")[:n]; per = p.col("habitant", "vh_permis")[:n]
    mi = PO.menages_inscrits(tb, n)
    age = (j - nj) / JOURS_AN
    ok = (tb.vivant[:n] == 1) & (mi >= 0)
    agec = np.full(M, 999.0)
    sel = ok & (per != 0) & (age >= 18.0)
    np.minimum.at(agec, mi[sel], age[sel])
    agec[agec >= 999.0] = 45.0
    tl = _type_lieu(p, D, tb.menages.domicile[:M])
    rev = cm["eco_revenu"][:M]
    parts = np.cumsum([a.part for a in D.assureurs]); parts = parts / parts[-1]
    lots = []
    # --- auto
    for k in TR.K3:
        vm = cm[f"vh_m{k}"][:M].astype(np.int64)
        idx = np.nonzero((vm >= 0) & ((pr & 1) != 0) & ~dis)[0]
        if not len(idx): continue
        m = vm[idx]; ne = cm[f"vh_ne{k}"][idx].astype(float); km = cm[f"vh_km{k}"][idx].astype(float)
        age_v = (j - ne) / JOURS_AN
        g = rng.random((2, len(idx)))
        gar = RC | np.where(g[0] < P_VOL_OPTION, VOL, 0)
        gar = gar | np.where(g[1] < np.where(age_v < AGE_NEUF, P_DOMMAGES_NEUF, P_DOMMAGES_VIEUX), VOL | DOMMAGES, 0)
        tech, val = prime_auto(j, m, ne, km, tl[idx], np.zeros(len(idx)), agec[idx], gar)
        lots.append((AUTO, idx, np.full(len(idx), k), cm[f"vh_ne{k}"][idx].astype(np.int64), m, gar, tech,
                     np.full(len(idx), FRANCHISE_DOMMAGES), val, np.ones(len(idx))))
    # --- habitation
    d13 = IM._dom(p)
    st, lg = cm["im_statut"][:M], cm["im_logement"][:M]
    idx = np.nonzero((st == IM.PROPRIETAIRE) & (lg >= 0) & ((pr & 2) != 0) & ~dis)[0]
    if len(idx):
        b = lg[idx].astype(np.int64)
        si = d13.B["surface"][b].astype(float) * IM.cout_m2()
        gar = INCENDIE | np.where(rng.random(len(idx)) < P_SEISME_OPTION, SEISME, 0)
        tech = prime_hab(si, d13.B["annee"][b], gar)
        lots.append((HAB, idx, np.full(len(idx), -1), b, np.full(len(idx), -1), gar, tech,
                     np.full(len(idx), FRANCHISE_INCENDIE), si, np.ones(len(idx))))
    # --- sante
    viv = _vivants_par_menage(tb, M)
    idx = np.nonzero((viv > 0) & ((pr & 4) != 0) & ~dis)[0]
    if len(idx):
        ch = p.col("habitant", "med_chroniques")[:n]
        e = np.where(ok, perte_sante(age, _nch(ch)), 0.0)
        pm = np.bincount(mi[ok], weights=e[ok], minlength=M)[:M]
        tech = pm[idx] / LR_CIBLE + FRAIS_FIXES
        u_ = viv[idx].astype(float)
        lots.append((SANTE, idx, np.full(len(idx), -1), np.full(len(idx), -1), np.full(len(idx), -1),
                     np.full(len(idx), HOSPI), tech, np.zeros(len(idx)), PLAFOND_SANTE * u_, u_))
    _bases(p, D)
    for br, idx, sl, obj, mod, gar, tech, fr, pl, un in lots:
        ref = np.array([D.base[(br, int(g))] for g in gar]) * (un if br == SANTE else 1.0)
        lr = np.log(np.maximum(tech / ref, 1e-6))
        niv = 1 + np.argmin(np.abs(np.log(np.array(MULT[1:]))[None, :] - lr[:, None]), axis=1)
        prime = np.array(MULT)[niv] * ref
        ttc = prime * (1.0 + TAXE[br])
        pa = 1.0 / (1.0 + (ttc / (np.maximum(rev[idx], 1.0) * JOURS_AN) / R50[br]) ** 2)
        acc = (rng.random(len(idx)) < pa) & (tech / ref <= REFUS_RATIO)
        a = np.searchsorted(parts, rng.random(len(idx)), side="right").clip(0, len(parts) - 1)
        deb = j - rng.integers(0, DUREE_J, len(idx))
        q = np.nonzero(acc)[0]
        rr = T.bloc(len(q))
        T.branche[rr] = br; T.etat[rr] = ACTIF; T.menage[rr] = idx[q]; T.slot[rr] = sl[q]; T.objet[rr] = obj[q]
        T.modele[rr] = mod[q]; T.assureur[rr] = a[q]; T.debut[rr] = deb[q]; T.fin[rr] = deb[q] + DUREE_J
        T.prime[rr] = prime[q]; T.ref[rr] = ref[q]; T.garanties[rr] = gar[q]; T.franchise[rr] = fr[q]
        T.plafond[rr] = pl[q]; T.unites[rr] = un[q]; T.niveau[rr] = niv[q]; T.encaisse[rr] = prime[q]
        cm[_ptr(br, int(sl[0]) if len(sl) else 0)][idx[q]] = rr
        refus = np.nonzero(~acc)[0]
        cm["as_retry" if br == AUTO else "as_retry_v"][idx[refus]] = j + rng.integers(1, RETRY[0 if br == AUTO else 1], len(refus))


def _bases(p, D):
    """Les primes de reference ( le temoin : une prime unique par branche et formule ) : le tarif d un profil moyen -
    une voiture de 8 ans et 100 000 km en ville, sans sinistre, conducteur de 40 ans ; un logement de 90 m2 de 1985 ;
    un adulte de 40 ans sans maladie chronique."""
    j = p.jour
    voit = [c.idx for c in TR.CARAC if c.categorie == "voiture"]
    m = voit[len(voit) // 2]
    for g in (RC, RC | VOL, RC | VOL | DOMMAGES):
        t, v = prime_auto(j, np.array([m]), np.array([j - 8 * 365.0]), np.array([100000.0]), np.array([1]),
                          np.array([0]), np.array([40.0]), np.array([g]))
        D.base[(AUTO, g)] = float(t[0])
    D.base[(AUTO, RC | DOMMAGES)] = D.base[(AUTO, RC | VOL | DOMMAGES)]
    D.base[("valeur", AUTO)] = float(v[0])
    si = 90.0 * IM.cout_m2()
    for g in (INCENDIE, INCENDIE | SEISME):
        D.base[(HAB, g)] = float(prime_hab(np.array([si]), np.array([ANNEE_CODE]), np.array([g]))[0])
    D.base[("valeur", HAB)] = si
    D.base[(SANTE, HOSPI)] = float(perte_sante(np.array([40.0]), np.array([0]))[0]) / LR_CIBLE + FRAIS_FIXES
    D.base[("valeur", SANTE)] = 1.0


def _capital(p, D):
    """Le capital d ouverture : chaque assureur recoit de sa maison mere ( investissement direct ) de quoi couvrir ses
    primes non acquises et CIBLE_SOLVA fois son SCR, plus sa part de la dotation du fonds de garantie ( 10 % des
    primes auto annuelles ) qu il y verse aussitot."""
    L = p.socle.livre
    solvabilite(p, D)
    for A in D.assureurs:
        fonds = 0.10 * A.primes_an[AUTO]
        x = A.ppna + CIBLE_SOLVA * A.scr + fonds
        y = L.recevoir_de_l_exterieur(A, x, "investissement_direct"); D.cpt["investissement_direct"] += y
        f = L.transferer(A, D.fonds, fonds, "contribution_fonds_garantie"); D.cpt["contribution_fonds_garantie"] += f
        BQ.ouvrir_compte(p, A)
    BQ.ouvrir_compte(p, D.fonds)
    solvabilite(p, D)
    for A in D.assureurs: A.retention = RETENTION * A.fp


def installer(p):
    w = p.w; L = p.socle.livre
    D = Assurances()
    p.domaines["assurances"] = D
    D.jour_install = p.jour
    for m, nat in MOTIFS: L.declarer_motif(m, nat, "assurances")
    J = p.socle.journal
    for t, champs in (("faillite_assureur", ("assureur", "fonds_propres", "scr")),
                      ("catastrophe_assuree", ("assureur", "sinistres", "brut", "recuperable")),
                      ("fraude_signalee", ("declaration", "menage", "montant", "vraie"))):
        J.declarer(t, "assurances", "individuel", champs)
    for t in ("souscription", "renouvellement", "resiliation", "refus_assureur", "refus_menage", "depart_concurrent",
              "sinistre_declare",
              "sinistre_paye", "sinistre_refuse", "sinistre_sous_franchise", "sinistre_non_couvert",
              "recours_fonds_garantie", "cotisation_elga", "obligation_achetee", "decision_tarif"):
        J.declarer(t, "assurances", "compte")
    cm = p.colonnes["menage"]
    for nom, dt, defaut in (("as_auto0", np.int32, -1), ("as_auto1", np.int32, -1), ("as_auto2", np.int32, -1),
                            ("as_hab", np.int32, -1), ("as_sante", np.int32, -1), ("as_prop", np.uint8, 0),
                            ("as_bm", np.int8, 0), ("as_retry", np.int32, 0), ("as_retry_v", np.int32, 0)):
        cm.ajouter(nom, dt, defaut)
    cm.assurer(w.table.menages.n)
    reg = p.socle.registre
    reg.inscrire("assureurs", "financier", _membres_assureurs, "caisse", None, "Assureur")
    reg.inscrire("fonds_garantie", "financier", _membres_fonds, "caisse", None, "FondsGarantie")
    reg.inscrire("elga", "administrations", _membres_elga, "caisse", None, "Elga")
    D.type_lieu = np.array([TYPES.get(l.type, 3) for l in w.carte.par_n], np.int64)
    D.decideur = p.decideur(POINT_TARIF)
    _portefeuille_initial(p, D)
    _capital(p, D)
    D.vu_ag = len(p.domaine("agriculture").champs.campagnes)
    _prix_elga(p, D)
    D.vu_tr = len(TR._tr(p).sinistres); D.vu_im = len(IM._dom(p).sinistres); D.jour_ho = p.jour
    TR.brancher_assurance(p, Couvrir())
    p.echeance("assurances_garage", _payer_garage)
    p.echeance("assurances_obligation", _obligation_echue)
    p.routine(8 + 50 / 60, 60, "assurances", _matin)
    p.routine(9.0, 60, "assurances", _souscrire)
    p.routine(10.0, 60, "assurances", _placements)
    p.routine(17 + 40 / 60, 60, "assurances", _elga_cotisations)
    p.cloture("assurances", _cloture)
    return D


# ================================================================== controles ( pour les portes )
def provisions(p):
    """{ payeur : ( provision tenue, somme des declarations ouvertes ) }."""
    D = _dom(p)
    acc = {}
    for d in D.ouverts.values(): acc[d.payeur] = acc.get(d.payeur, []) + [d.estime]
    out = {}
    for k in list(range(len(D.assureurs))) + [FONDS, ELGA_P]:
        out[k] = (_payeur(D, k).psap, math.fsum(acc.get(k, [])))
    return out


def _suivi(m, pa, re):
    """L investissement direct est aussi celui des domaines 7 et 14 : seul celui recu par un assureur est suivi ici."""
    return m != "investissement_direct" or re == "Assureur"


def livre_cumule(p, D=None):
    """Ce que le grand livre a vu sous chaque motif suivi, jour en cours compris."""
    D = D or _dom(p); L = p.socle.livre
    out = dict(D.livre)
    for (m, pa, re), (s, _) in L.jour_argent.items():
        if m in out and _suivi(m, pa, re): out[m] += s
    return out


def audit(p):
    """Les anomalies : provision differente des declarations ouvertes ; motif du grand livre different de ce que le
    domaine a paye ( une indemnite sans declaration, une prime sans contrat ) ; declaration ouverte sans contrat qui
    couvre ; pointeur de menage vers une ligne qui n est pas son contrat actif. Vide : tout est en ordre."""
    D = _dom(p); T = D.T; cm = p.colonnes["menage"]; M = p.w.table.menages.n
    out = {"provision": [], "livre": [], "sans_contrat": [], "pointeur": [], "invalides": list(D.invalides)}
    for k, (tenue, somme) in provisions(p).items():
        if abs(tenue - somme) > TOL * max(1.0, abs(somme)): out["provision"].append((k, tenue, somme))
    lv = livre_cumule(p, D)
    for m in SUIVIS:
        x = D.cpt["sinistres_ht"] if m == "indemnite_assurance" else D.cpt[m]
        if abs(lv[m] - x) > TOL * max(1.0, abs(x)): out["livre"].append((m, lv[m], x))
    for d in D.ouverts.values():
        if not valide(p, D, d): out["sans_contrat"].append(d.id)
    for br, noms in ((AUTO, ("as_auto0", "as_auto1", "as_auto2")), (HAB, ("as_hab",)), (SANTE, ("as_sante",))):
        for s, nom in enumerate(noms):
            c = cm[nom][:M]
            for i in np.nonzero(c >= 0)[0].tolist():
                r = int(c[i])
                if not (r < T.n and T.etat[r] == ACTIF and T.menage[r] == i and T.branche[r] == br
                        and (br != AUTO or T.slot[r] == s)):
                    out["pointeur"].append((nom, i, r))
    return out


def audit_propre(a): return not any(a.values())


def taux_de_souscription(p):
    """Les taux de couverture par branche : vehicules assures, logements de proprietaires occupants assures,
    personnes couvertes en sante, fermes cotisant a ELGA ( obligatoire ) ; et la penetration ( primes annuelles du
    portefeuille sur le revenu annuel des menages )."""
    D = _dom(p); T = D.T; n = T.n; cm = p.colonnes["menage"]; tb = p.w.table; M = tb.menages.n
    dis = cm["dissous"][:M] == 1
    veh = sum(int(((cm[f"vh_m{k}"][:M] >= 0) & ~dis).sum()) for k in TR.K3)
    ass = sum(int(((cm[f"vh_m{k}"][:M] >= 0) & (cm[f"as_auto{k}"][:M] >= 0) & ~dis).sum()) for k in TR.K3)
    pro = (cm["im_statut"][:M] == IM.PROPRIETAIRE) & (cm["im_logement"][:M] >= 0) & ~dis
    hab = int((pro & (cm["as_hab"][:M] >= 0)).sum())
    viv = _vivants_par_menage(tb, M)
    san = int(viv[(cm["as_sante"][:M] >= 0)].sum())
    act = T.etat[:n] == ACTIF
    primes = float(T.prime[:n][act].sum())
    revenu = float(cm["eco_revenu"][:M][~dis].sum()) * JOURS_AN
    fermes = len(p.domaine("agriculture").liste) if p.a("agriculture") else 0
    return {"auto": ass / max(1, veh), "habitation": hab / max(1, int(pro.sum())), "sante": san / max(1, int(viv.sum())),
            "recolte": 1.0 if fermes else 0.0, "penetration": primes / max(revenu, EPS),
            "vehicules": veh, "proprietaires": int(pro.sum()), "personnes": int(viv.sum()), "fermes": fermes}


def recalculer(p, d):
    """Ce qu une declaration payee devait valoir, recalcule depuis sa source et le contrat ( pour les portes )."""
    D = _dom(p)
    if d.nature in ("rc_materiel", "dommages"):
        return d.vrai if d.garantie == RC else max(0.0, d.vrai - FRANCHISE_DOMMAGES)
    if d.nature in ("incendie", "seisme"):
        pl = d.plafond
        fr = FRANCHISE_SEISME * pl if d.nature == "seisme" else FRANCHISE_INCENDIE
        return max(0.0, min(d.declare, pl) - fr)
    if d.nature == "vol": return max(0.0, d.vrai * (1.0 - FRANCHISE_VOL))
    if d.nature == "auto_especes":
        return max(0.0, d.vrai - (FRANCHISE_DOMMAGES if d.garantie == DOMMAGES else 0.0))
    return d.declare


# ================================================================== API pour les autres domaines et les scenarios
def scenario(p, **facteurs):
    """Scenarios et portes : `reassurance` ( 0 : aucun traite ), `fraude` ( multiplie la fraude )."""
    D = _dom(p)
    for k, v in facteurs.items():
        if k not in D.scenario or not 0.0 <= v < 1e6: raise ValueError(f"facteur invalide {k}={v!r}")
        D.scenario[k] = float(v)
    return dict(D.scenario)


def forcer_echeances(p, part, jours, rng):
    """Scenario ( portes ) : une part des contrats actifs arrive a echeance dans les `jours` jours ( renouvellements
    groupes )."""
    D = _dom(p); T = D.T; n = T.n
    for r in np.nonzero(T.etat[:n] == ACTIF)[0].tolist():
        if rng.random() < part: T.fin[r] = p.jour + 1 + int(rng.integers(0, max(1, jours)))


def retirer_reassurance(p, assureur):
    """Scenario : le reassureur d un assureur fait defaut, ses traites tombent ( quote-part et excedents ). Son SCR
    reprend tout le risque de catastrophe."""
    _dom(p).assureurs[assureur].reassure = 0.0


def distribuer(p, assureur, montant):
    """Scenario : un dividende exceptionnel verse a la maison mere ( il reduit les fonds propres )."""
    D = _dom(p); A = D.assureurs[assureur]
    y = EXT.payer_en_devises(p, A, montant, "dividende_assureur"); D.cpt["dividende_assureur"] += y
    return y


def contrat_de(p, menage, branche="auto", emplacement=0):
    """Domaines 14, 21 : le contrat d un menage ( dictionnaire ) ou None."""
    D = _dom(p); T = D.T; br = BRANCHES.index(branche)
    r = int(p.col("menage", _ptr(br, emplacement))[menage])
    if r < 0: return None
    return {"assureur": D.assureurs[int(T.assureur[r])].nom, "debut": int(T.debut[r]), "fin": int(T.fin[r]),
            "prime": float(T.prime[r]), "garanties": int(T.garanties[r]), "franchise": float(T.franchise[r]),
            "plafond": float(T.plafond[r])}


def assure(p, menage, branche="auto"):
    """Domaine 21 ( controles routiers : conduite sans assurance ) : vrai si le menage a au moins un contrat actif."""
    cm = p.colonnes["menage"]
    if branche == "auto": return any(int(cm[f"as_auto{k}"][menage]) >= 0 for k in TR.K3)
    return int(cm["as_hab" if branche == "habitation" else "as_sante"][menage]) >= 0


def bilan(p):
    """Domaines 2, 6 : { assureur : caisse, obligations, provisions, fonds propres, SCR, ratio, vivant }."""
    D = _dom(p)
    return {A.nom: {"caisse": A.caisse, "obligations": A.oblig, "psap": A.psap, "ppna": A.ppna, "fonds_propres": A.fp,
                    "scr": A.scr, "ratio": A.ratio, "vivant": A.vivant} for A in D.assureurs}


def obligations_detenues(p):
    """Domaine 6 : la dette du Tresor envers les assureurs et le fonds ( prix des bons non echus )."""
    return math.fsum(o.prix for o in _dom(p).obligations.values())


def sinistres_ouverts(p):
    """Domaines 21, 22 : les declarations en cours ( nature, payeur, jour, montant provisionne )."""
    D = _dom(p)
    return [(d.id, d.nature, d.payeur, d.jour, d.estime) for d in D.ouverts.values()]
