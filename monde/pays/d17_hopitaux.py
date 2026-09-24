"""DOMAINE 17 - MEDECINE B : HOPITAUX, SOINS, PERSONNELS, CHAINE DU MEDICAMENT.

FICHE
1. Classes. EtablissementSante ( un hopital public ESY, une clinique privee, un hopital militaire : ses lits generaux et de
   reanimation, ses blocs, ses files d attente, son personnel par specialite, sa pharmacie hospitaliere - stock du
   socle, lots par peremption, au format des pharmacies du domaine 16 -, sa caisse, ses ambulances ), Passage ( le
   parcours d un malade : appel, transport, file des urgences, bloc, lit ou reanimation, sortie, renvoi ou deces ),
   Grossiste ( un par ile : il importe, garde un stock par lots, livre chaque matin les officines du domaine 16 et les
   pharmacies hospitalieres ), Eopyy ( la caisse nationale d assurance maladie : paie les sejours au forfait - KEN -
   et les medicaments des officines, financee par l Etat ), ContexteTriage, Hopitaux ( l etat du domaine ),
   RemplaceSoigner ( prend la place de Monde.soigner, que le domaine 16 avait pose par defaut ). Aucune colonne par
   habitant : les passages, le personnel, les rappels et la fatigue sont des tables eparses ( quelques pour mille des
   habitants ). Modeles du Parc : ambulance, respirateur, table_operation, scanner, analyseur_labo, groupe_electrogene.
2. Invariants et ce que le domaine detient. LITS : a chaque pas, pour chaque etablissement, lits occupes + lits libres =
   capacite declaree ; un lit occupe l est par un passage en etat LIT ( ou REA ) qui le designe, et un passage LIT ou
   REA a son lit ( `ecarts_lits` ). Un lit n est occupe que par un malade grave ( gravite > 0,3 ) : la sortie a lieu au
   premier pas ou la gravite repasse sous 0,3 ; le moteur E1 place ce malade au poste « hopital » ( Monde.deplacer,
   ou l agenda que la medecine replanifie ) : jamais un lit tenu par quelqu un que le moteur a renvoye chez lui.
   MEDICAMENTS : grossistes et pharmacies hospitalieres sont inscrits au registre ( familles `grossistes` et
   `etablissements_sante`, stock du socle ) ; tout entre par le grand livre ( importe, produit pour le sang donne ) et
   en sort par lui ( consomme, perime ) ou passe aux officines du domaine 16 ( deplace ) ; la somme des lots egale le
   stock ( `ecarts_lots_hopitaux` ) ; BILAN par molecule : stock = dotation + importe + dons - livre aux officines -
   dispense - perime, et commande = recu + annule + en route ( `bilan_medicaments` ). ARGENT : trois familles nouvelles
   ( etablissements_sante, grossistes, eopyy ), tout par le grand livre sous les motifs du domaine. Objets : ambulances
   et equipements nes au recensement ( initial ), conserves par le Parc.
3. Decision `triage` ( quand une ressource se libere - un medecin des urgences, un bloc, un lit, une ambulance - et que
   deux malades au moins l attendent, dont le premier arrive n est PAS le plus grave : le dilemme ) : premier_arrive,
   plus_grave, renvoyer_moins_grave ( servir le plus grave et renvoyer chez lui le moins grave de la file ). Traits :
   niveaux ESI du plus grave, du premier arrive et du moins grave ( le tri infirmier ), leurs attentes, longueur de la
   file, ressource, part libre de la ressource, personnel present, fatigue de l equipe, sang en banque pour le plus
   grave. Jamais la letalite vraie, ni
   l avenir. Note ( horizon 14 jours : la mort precoce d un blesse se joue en heures, mais la fin de sa phase aigue - ou il
   meurt s il n a jamais eu son soutien - tombe ISS / 2 jours apres l accident, 5 a 20 jours ; a 3 jours, la note ne
   voyait pas ce que coute un renvoi, et renvoyer semblait le meilleur choix )
   : chaque jour, pour CES malades - le premier arrive, le plus grave et le moins grave : ceux que l une des actions
   sert, ecarte ou renvoie -, la moyenne de 1 - gravite s il vit, 0 s il est mort. Ni la moyenne du pays, ni le seul
   servi : l effet du choix sur l ecarte compte autant. Le meme groupe quelle que soit l action ( lecon du 24/09 : noter
   le servi et SON ecarte faisait paraitre le renvoi meilleur, parce que le renvoye, moins grave, allait mieux de
   toute facon ). Regle : la priorite clinique ( le plus grave ) ; renvoyer le moins grave quand la file des urgences
   deborde ( 4 et plus ) et qu il est ESI 4 ou 5. Temoin : premier arrive, premier servi.
   MESURE DU 24/09 ( test_decision ) : la porte ECHOUE. En mode hasard, la note ne depend pas du choix ( part 0,000 ) ;
   la mortalite des blesses est la meme sous la regle et sous le temoin ( ISS 16-24 : 15 % contre 12 % ; ISS 25 et
   plus : ~ 93 % des deux cotes ). Trois causes, lues dans le modele : ( a ) la medecine fait mourir un blesse non
   soutenu par un seuil a 1, 3 ou 6 heures : un service de retard ( 40 min d ambulance, 30 min d examen ) franchit
   rarement ce seuil ; ( b ) parmi les malades graves, la letalite ne depend pas de la gravite visible : trier par ESI
   ne vise pas ceux que le soin sauve le plus ; ( c ) un ISS de 25 ou plus demande 4 culots, et un petit pays n a
   pas le sang ( 0,058 don par habitant et par an ) : ces blesses meurent quel que soit l ordre. Le premier resultat
   positif ( part 0,025 ) venait d une note biaisee, retiree.
4. Evenements. Individuels : rupture_molecule, afflux_massif, plan_blanc, transfert_patient, evacuation_hopital.
   Comptes : passage_urgences, admission_hopital, admission_rea, chirurgie, sortie_hopital, deces_hopital,
   renvoi_domicile, mission_ambulance, rappel_astreinte, livraison_grossiste, import_grossiste, peremption_hopital,
   jour_sans_molecule, heure_groupe, traitement_manque, consommables_manquants, soutien_manque.
5. Liens. Remplace Monde.soigner ( proprietaire : hopitaux, table des conventions ) : la medecine appelle w.soigner( h )
   pour chaque malade grave, chaque blesse d ISS >= 9, chaque hemorragie du post-partum ; ce domaine l appelle une
   ambulance ou le laisse venir par ses moyens, le trie ( ESI ), le fait examiner ( M.diagnostiquer, protocole
   M.PROTOCOLE_HOPITAL donne par M.traiter sur SA pharmacie ), opere, couche, et donne le soutien ( M.prise_en_charge )
   quand le lit, le bloc ou la reanimation, le kit du moteur ( remedes ), l oxygene, l anesthesique et le sang y sont.
   Le delai compte : un blesse grave qui n a pas son soutien avant la fin de sa phase aigue ( 1, 3 ou 6 heures, medecine )
   peut en mourir. Reprend la chaine du medicament ( M.reprendre_chaine ) : les officines du domaine 16 ne commandent
   plus, le grossiste de leur ile les livre ; on n ouvre pas un malade dont le sang manque ; le sang donne va aux banques de sang des hopitaux, qui se le cedent
   entre elles sur l ile ( coursier ) ; un plan blanc lance un appel aux dons ( une semaine de dons le lendemain ). Immobilier ( 13 ) : le
   batiment « hopital » de chaque capitale fait les lits ( IM.lits ; un seisme qui le rend inhabitable les retire et
   fait evacuer ) ; IM.construire pour agrandir. Industrie ( 10 ) : les consommables ( chimie : desinfectants, reactifs )
   par `commander` ( composee avec la commande des autres domaines, que `commander` ecraserait ) et `livrer`. Optionnels :
   exterieur ( 7 : les imports passent par importer_au_port, motif import_sante ), energie ( 11 : abonnement
   prioritaire, groupe electrogene pendant une coupure ), transport ( 14 : carburant des ambulances et du groupe par
   faire_le_plein ), travail ( 4 : un medecin en greve n est pas de garde ), etat ( 6 : assurer la tresorerie avant
   chaque paiement de l Etat ), banques ( 2 : comptes des grossistes et des cliniques ). Paie et recoit : Etat ->
   EOPYY ( financement ), EOPYY -> etablissements ( KEN ) et -> grossistes ( medicaments des officines ), menage ->
   clinique ( participation ), etablissements -> grossistes ( pharmacie hospitaliere ), Etat -> hopitaux publics
   ( dotation ESY, qui couvre les arrieres ; le surplus au-dela de deux fonds de roulement revient a l Etat, qui paie
   deja les salaires ), grossistes -> exterieur ( import ), etablissements -> marches ( carburant,
   kit ). Les salaires des medecins et infirmiers restent le salaire public du moteur ( ligne sante du domaine 6 ).
6. Portes : tests_d17_hopitaux.py.
7. Arma. L ambulance porte le classname C_Van_02_medevac_F ( van ambulance ; DLC d origine a verifier : Apex ou Laws of
   War ) ; jamais C_Van_01_box_F, qui naissait mort. Les equipements n ont pas de corps. Le malade garde le corps de
   l habitant ( M.vers_arma ). arma_preuve = None partout : rien n a ete vu vivre en jeu.
8. Cout. Chaque pas ne touche que les files, les lits, les blocs et les ambulances ( quelques dizaines d objets a
   10 000 habitants ) ; le personnel est relu une fois par jour, sa fatigue une fois par heure ; la chaine du
   medicament fait une passe par jour sur les molecules ( 22 ) des officines et des pharmacies hospitalieres. Memoire :
   ~ 150 octets par passage actif, ~ 1 Ko par etablissement. Mesure du 24/09 ( test_cout, 10 000 habitants ) :
   1,89 s par jour pour les dependances, 1,90 s avec les hopitaux ( + 1 % ) ; sous un accident de masse toutes les
   3 heures, le domaine prend ~ 13 % du pas ( files du bloc ), le deplacement du moteur l essentiel.

DIMENSIONNEMENT ( ce que les portes verifient ) et CONCILIATION avec le moteur E1.
  - Lits : 4,2 pour 1 000 habitants ( Eurostat hlth_rs_bds, Grece 2019 ), la regle du domaine 13 qui a construit
    l hopital de chaque capitale ( au moins 2 lits ). Reanimation : 6 pour 100 000 ( Grece avant 2020, ordre de
    grandeur OCDE ), prise sur les lits du batiment ; au moins 1 lit dans l hopital le plus peuple de chaque ile.
    Blocs : 1 pour 40 lits, au moins 1. Ambulances : 9 pour 100 000 ( a calibrer ; EKAB ~ 900 vehicules ), au moins 1
    par hopital.
  - Personnel : la Grece compte ~ 6,3 medecins et ~ 3,4 infirmiers pour 1 000 habitants ( Eurostat, OCDE 2021 ). Le
    moteur en pose 12 et 12 pour 1 000 ( 6 et 6 a 500 habitants ), tous de garde dans leur capitale ( trois equipes de
    8 h ). Ce domaine prend le moteur tel qu il est : chaque medecin et chaque infirmier du moteur est affecte a
    l hopital de sa capitale. La densite est deux a trois fois la grecque, mais le NOMBRE ABSOLU est ce qui manque : a
    500 habitants, un hopital a deux medecins, et il en faut cinq par ligne de garde pour une presence 24 h sur 24 ;
    les trous se comblent par l astreinte ( rappel a domicile, 30 minutes, dans la limite de 24 heures continues ).
    Les specialites suivent un plan de dotation : chirurgien, anesthesiste, urgentiste, interniste, obstetricien,
    pediatre d abord ( un bloc ne tourne qu avec un chirurgien ET un anesthesiste ), puis la repartition des
    specialites de l ESY ( a calibrer ).
  - Cliniques privees ( ~ 1 pour 70 000 habitants ) et centres de sante ruraux ( ~ 1 pour 50 000 ) : aucune a
    l echelle des essais ; `ouvrir_etablissement` les cree ( scenario, grande echelle ). Une clinique recoit les malades
    que l hopital public ne peut coucher ( lits conventionnes par l EOPYY ) ; le malade y paie sa participation."""
import collections, math
import numpy as np
from .. import config as C
from ..socle import decision as D, biens as B
from . import pays as PAYS, d01_population as POP, d16_medecine as M, d13_immobilier as IM, d10_industrie as IN

PAS_J = C.PAS_PAR_JOUR
MIN_PAS = C.MINUTES_PAR_PAS
EUR = PAYS.EUROS_PAR_DRACHME

# ================================================================== dimensionnement
LITS_1000 = 4.2                   # Eurostat hlth_rs_bds, Grece 2019 ( la regle du domaine 13 )
REA_100K = 6.0                    # lits de soins intensifs pour 100 000 habitants, Grece avant 2020 ( OCDE, ordre de grandeur )
LITS_PAR_BLOC = 40.0              # a calibrer
AMBULANCES_100K = 9.0             # a calibrer ( EKAB ~ 900 ambulances pour 10,4 millions )
MEDECINS_1000_GRECE = 6.3         # Eurostat 2021, medecins en exercice
INFIRMIERS_1000_GRECE = 3.4       # OCDE 2021, infirmiers en exercice
SCANNERS_PAR_HAB = 3.5e-5         # ~ 35 scanners par million ( OCDE ), a calibrer
TYPES = ("hopital", "clinique", "centre_sante", "militaire")
SPECIALITES = ("chirurgien", "anesthesiste", "urgentiste", "interniste", "obstetricien", "pediatre")
PLAN_DOTATION = SPECIALITES       # l ordre dans lequel un hopital pourvoit ses premiers postes
PART_SPECIALITES = {"interniste": 0.30, "chirurgien": 0.20, "anesthesiste": 0.12, "urgentiste": 0.10,
                    "pediatre": 0.10, "obstetricien": 0.08}   # repartition dans l ESY au-dela du plan ( a calibrer )
ORDRE_URGENCES = ("urgentiste", "interniste", "pediatre", "obstetricien", "chirurgien", "anesthesiste")

# ================================================================== le parcours
APPEL, TRANSPORT, ATT_MED, ATT_BLOC, BLOC, ATT_LIT, ATT_REA, LIT, REA = range(9)
ETATS = ("appel", "transport", "attente_medecin", "attente_bloc", "bloc", "attente_lit", "attente_rea", "lit", "rea")
SORTI, RENVOYE, DECEDE, TRANSFERE = "sorti", "renvoye", "decede", "transfere"
GRAVITE_LIT = M.GRAVITE_HOPITAL   # 0,3 : au-dela, le moteur tient le malade a l hopital
GRAVITE_REA = M.G_CRITIQUE[0]     # 0,8
# Duree d examen aux urgences par niveau ESI ( minutes ; a calibrer : 30 a 60 min pour un ESI 1-2 )
DUREE_EXAMEN_MIN = {1: 45, 2: 40, 3: 30, 4: 20, 5: 10}
CHIRURGIE_MIN = (60.0, 4.0)       # duree d une intervention : 60 min + 4 min par point d ISS ( a calibrer )
CHIRURGIE_MEDICALE_MIN = 90.0
# Ambulances ( EKAB : objectif 15-20 min en ville, bien plus a la campagne ; a calibrer )
DECROCHE_MIN, SUR_PLACE_MIN, NETTOYAGE_MIN = 3.0, 15.0, 15.0
VITESSE_AMBULANCE_KMH = 50.0
VITESSE_PROPRE_KMH = 30.0         # un proche qui conduit le malade, ou lui-meme
ATTENTE_DEPART_MIN = 15.0
KM_URBAIN = 3.0                   # une capitale n est pas un point : trajet minimal
L_PAR_KM_AMBULANCE = 0.15         # van diesel ~ 15 L / 100 km ( a calibrer )
PART_PROPRES_MOYENS = 0.6         # blesses legers et malades ESI 3+ qui viennent seuls ( catastrophes : 50-80 %, a calibrer )
# Personnel
RAPPEL_PAS = 3                    # 30 minutes pour qu un medecin d astreinte arrive
DUREE_RAPPEL_PAS = 48             # un rappel couvre 8 heures
MAX_CONTINU_H = 24.0              # garde maximale continue ( pratique grecque des gardes de 24 h ; a calibrer )
FATIGUE_H = 16.0                  # au-dela, l equipe ralentit ( Lockley 2004 : +36 % d erreurs graves apres 24 h )
FACTEUR_FATIGUE = 1.25
REPOS_H = 8.0                     # un repos de 8 h remet le compteur de garde a zero
SEUIL_PLAN_BLANC = 4              # malades en attente aux urgences et au bloc qui declenchent le rappel general
PATIENTS_PAR_INFIRMIER_REA = 2    # norme europeenne des soins intensifs ( ESICM : 1 pour 1 a 2 )
# ESI ( Emergency Severity Index v4, Gilboy 2012 ) projete sur les besoins de la medecine
DUREE_URGENCE_MAX_PAS = 36        # 6 heures : l echelle des traits d attente

# ================================================================== la chaine du medicament
HOSPITALIERES = ("sang", "anesthesique", "oxygene", "morphine", "ceftriaxone", "sulfate_magnesium", "oxytocine",
                 "corticoide")   # ce qu une officine ne vend pas : elle ne les recommande plus
# Consommation hospitaliere attendue par 1 000 habitants et par jour ( a calibrer ; relayee par la mesure )
CONSO_HOPITAL_1000 = {"anesthesique": 0.3, "sang": 0.16, "oxygene": 0.5, "morphine": 0.3, "ceftriaxone": 0.5,
                      "corticoide": 0.3, "sulfate_magnesium": 0.01, "oxytocine": 0.05, "insuline": 0.3,
                      "antihypertenseur": 1.0, "bronchodilatateur": 0.5, "amoxicilline": 0.5, "antituberculeux": 0.02,
                      "oseltamivir": 0.2, "sro": 0.2, "paracetamol": 1.0, "antiviral_covid": 0.02,
                      "antidiabetique": 0.3, "antidepresseur": 0.2}
# Dotation minimale d une pharmacie hospitaliere, quelle que soit sa population : le protocole de quatre malades
# ( trousse de catastrophe ; a calibrer )
STOCK_MIN = {"anesthesique": 6.0, "sang": 4.0, "oxygene": 40.0, "morphine": 12.0, "ceftriaxone": 28.0,
             "corticoide": 20.0, "sulfate_magnesium": 8.0, "oxytocine": 8.0, "insuline": 28.0, "antihypertenseur": 28.0,
             "bronchodilatateur": 28.0, "amoxicilline": 28.0, "antituberculeux": 30.0, "oseltamivir": 20.0,
             "sro": 12.0, "paracetamol": 30.0, "antiviral_covid": 5.0}
STOCK_PUI_J = 30                  # jours de consommation que vise une pharmacie hospitaliere ( a calibrer )
DOTATION_GROSSISTE_J = 30
POINT_COMMANDE_J = 20
CIBLE_GROSSISTE_J = 45
DELAI_IMPORT_J = 5                # du fabricant etranger au grossiste ( a calibrer : une a deux semaines )
MARGE_GROSSISTE = 0.054           # marge reglementee du grossiste en Grece ( ~ 5,4 %, a verifier )
APPEL_DONS_JOURS = 7.0            # un appel aux dons apres un plan blanc rapporte une semaine de dons en un jour
                                  # ( les dons affluent apres une catastrophe : Madrid 2004, Boston 2013 ; a calibrer )
DELAI_APPEL_DONS_PAS = PAS_J      # collecte, qualification biologique : le lendemain
CHIMIE_T_PAR_LIT_J = 0.0005       # desinfectants et reactifs : ~ 0,5 kg par lit et par jour ( a calibrer )
# ================================================================== le financement ( euros convertis )
KEN_URGENCE = 50.0 / EUR          # passage aux urgences sans hospitalisation ( a calibrer )
KEN_SEJOUR = 1300.0 / EUR         # KEN ( DRG grec ) moyen d un sejour medical ( a calibrer )
KEN_CHIRURGIE = 2800.0 / EUR      # supplement d un sejour chirurgical ( a calibrer )
KEN_REA_JOUR = 1000.0 / EUR       # journee de soins intensifs ( a calibrer )
PARTICIPATION_CLINIQUE = 0.30     # ce que le malade paie en clinique au-dela du forfait EOPYY ( a calibrer )
FONDS_ROULEMENT_J = 30            # jours d achats que l Etat laisse a un hopital public
# ================================================================== l energie
KW_PAR_LIT = 3.5                  # ~ 30 MWh par lit et par an ( a calibrer )
L_GAZOLE_PAR_KWH = 0.28           # groupe diesel a charge moyenne
LITRES_UNITE = 10.0               # une unite de carburant du moteur ( domaine 11 )

# ================================================================== le point de decision
PREMIER, PLUS_GRAVE, RENVOYER = 0, 1, 2
RESSOURCES = {"medecin": 0.0, "bloc": 1 / 3, "lit": 2 / 3, "ambulance": 1.0}
HORIZON_TRIAGE = 14               # la fin de la phase aigue d une lesion tombe ISS / 2 jours apres l accident ( medecine ) :
                                  # 5 a 20 jours ; un malade renvoye ou servi trop tard y meurt, pas dans les 3 premiers jours
# Une catastrophe ( seisme, accident de masse ) : ISS des blesses ( a calibrer ; les registres de catastrophe donnent
# ~ 70 % de blesses legers ). Les ISS < 9 ne vont pas a l hopital ( medecine ).
ISS_CATASTROPHE = (((1, 8), 0.40), ((9, 15), 0.25), ((16, 24), 0.20), ((25, 40), 0.15))

MODELES = (   # nom, famille, prix ( euros ), masse ( kg ), vie ( h ), classname Arma, source
    ("ambulance", "vehicule", 90000.0, 3500.0, 20000.0, "C_Van_02_medevac_F",
     "van ambulance type B ~ 90 000 euros ( a calibrer ) ; classname a verifier en jeu"),
    ("respirateur", "equipement", 25000.0, 30.0, 50000.0, None, "respirateur de reanimation ( a calibrer )"),
    ("table_operation", "equipement", 30000.0, 200.0, 60000.0, None, "table et colonne d anesthesie ( a calibrer )"),
    ("scanner", "equipement", 600000.0, 2000.0, 60000.0, None, "scanner 64 barrettes ( a calibrer )"),
    ("analyseur_labo", "equipement", 100000.0, 300.0, 50000.0, None, "automate de biologie ( a calibrer )"),
    ("groupe_electrogene", "machine", 80000.0, 5000.0, 30000.0, None, "groupe diesel 500 kVA ( a calibrer )"),
)


# ================================================================== les classes
class EtablissementSante:
    """Un etablissement de sante. lits_occ / rea_occ : l habitant couche dans chaque lit ( -1 libre ) ; bloc_occ et
    bloc_fin : l opere de chaque bloc et le pas ou il en sort ; files : identifiants d habitants dans l ordre ou ils y
    sont entres ; stock et lots : sa pharmacie ( lots [ quantite, jour de peremption ], ranges par peremption ) ;
    conso : consommation mesuree par molecule ( unites par jour, moyenne mobile sur 30 jours ) ; medecins, infirmiers :
    identifiants ; specialite : medecin -> specialite ; ambulances : numeros d objets du Parc."""
    __slots__ = ("id", "nom", "type", "prive", "lieu", "ile", "region", "batiment", "caisse", "stock", "lots",
                 "lits_occ", "rea_occ", "bloc_occ", "bloc_fin", "file_med", "file_bloc", "file_lit", "file_rea",
                 "medecins", "infirmiers", "specialite", "ambulances", "conso", "conso7", "sortie_jour", "pop", "labo",
                 "contrat", "sans_courant", "heures_groupe", "ouvert", "bloc_ferme_jusqu", "plan_blanc_jusqu",
                 "depense_moy", "achats_jour")

    def __init__(self, id, nom, type_, prive, lieu, ile, region, batiment, n_mol):
        if type_ not in TYPES: raise ValueError(f"type d etablissement inconnu {type_!r}")
        self.id, self.nom, self.type, self.prive, self.lieu, self.ile = id, nom, type_, bool(prive), lieu, ile
        self.region, self.batiment = region, batiment
        self.caisse = 0.0
        self.stock = B.Stock(); self.lots = {}
        self.lits_occ, self.rea_occ, self.bloc_occ, self.bloc_fin = [], [], [], []
        self.file_med, self.file_bloc, self.file_lit, self.file_rea = [], [], [], []
        self.medecins, self.infirmiers, self.specialite, self.ambulances = [], [], {}, []
        self.conso = np.zeros(n_mol); self.conso7 = np.zeros(n_mol); self.sortie_jour = np.zeros(n_mol); self.pop = 0
        self.labo = True; self.contrat = None; self.sans_courant = False; self.heures_groupe = 0
        self.ouvert = True; self.bloc_ferme_jusqu = -1; self.plan_blanc_jusqu = -1
        self.depense_moy = 0.0; self.achats_jour = 0.0


class Passage:
    """Le parcours d un malade dans le systeme de soins, de l appel a la sortie. Temps en pas du monde."""
    __slots__ = ("id", "hid", "etab", "etat", "esi", "t_appel", "t_arrivee", "t_file", "t_vu", "t_soutien", "lit",
                 "origine", "vu", "opere", "soutien", "kit", "transfuse", "rea_jours", "admis", "ambulance",
                 "attend_rea", "prive", "iss", "diag", "sang")

    def __init__(self, id, hid, etab, t, origine):
        self.id, self.hid, self.etab, self.etat, self.esi = id, hid, etab, APPEL, 5
        self.t_appel, self.t_arrivee, self.t_file, self.t_vu, self.t_soutien = t, -1, t, -1, -1
        self.lit, self.origine = -1, origine
        self.vu = self.opere = self.soutien = self.kit = self.transfuse = self.admis = self.attend_rea = False
        self.rea_jours, self.ambulance, self.prive, self.iss, self.diag = 0, -1, False, 0, None
        self.sang = 0.0                     # culots que ses lesions demandent ( fixe pendant le passage )


class Grossiste:
    """Le grossiste repartiteur d une ile : il importe, garde, livre. en_route : unites commandees a l etranger ;
    manque : le reliquat de la derniere tournee ( commandes non servies )."""
    __slots__ = ("id", "ile", "lieu", "caisse", "stock", "lots", "en_route", "manque")

    def __init__(self, id, ile, lieu, n_mol):
        self.id, self.ile, self.lieu = id, ile, lieu
        self.caisse = 0.0; self.stock = B.Stock(); self.lots = {}; self.en_route = np.zeros(n_mol)
        self.manque = np.zeros(n_mol)       # ce que la tournee du jour n a pas pu livrer : le reliquat a importer


class Eopyy:
    """La caisse nationale d assurance maladie ( EOPYY ) : elle paie, l Etat la finance au fil de ses paiements."""
    __slots__ = ("caisse", "paye_ken", "paye_officines", "recu_etat")

    def __init__(self):
        self.caisse = 0.0; self.paye_ken = 0.0; self.paye_officines = 0.0; self.recu_etat = 0.0


class ContexteTriage:
    """Ce que voit l infirmier organisateur de l accueil ( ou le regulateur des ambulances ) : la file et ses niveaux
    de tri, les attentes, la ressource, le personnel. Ni la letalite vraie, ni l avenir."""
    __slots__ = ("traits",)
    def __init__(self, traits): self.traits = traits


class Hopitaux:
    __slots__ = ("etabs", "grossistes", "eopyy", "actifs", "prochain", "appels", "occupe", "rappel", "continu",
                 "repos", "amb_libre", "amb_etab", "dec", "evts", "prochain_evt", "suivi", "historique", "attentes",
                 "factures", "bilan", "commande", "recu", "annule", "ruptures", "sans_molecule", "compteurs",
                 "id_mol", "ma_commande_chimie", "modeles", "rng", "etab_de_lieu", "sang_attendu", "sang_promis",
                 "dernier_appel_dons", "cache_sang", "demande_sang_pas")

    def compter(self, cle, v=1):
        self.compteurs[cle] = self.compteurs.get(cle, 0) + v


class RemplaceSoigner:
    """Prend la place de Monde.soigner( h ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)
    def __init__(self, pays): self.pays = pays
    def __call__(self, h): return soigner(self.pays, h)


# ================================================================== petits outils
def _dom(p): return p.domaines["hopitaux"]
def _etablissements_du_pays(w): return w.pays.domaines["hopitaux"].etabs
def _grossistes_du_pays(w): return w.pays.domaines["hopitaux"].grossistes
def _eopyy_du_pays(w): return (w.pays.domaines["hopitaux"].eopyy,)
def _t(p): return p.w.minutes / 1440.0


def _slots(p, h):
    """Les affections cliniques de h ( cles de la table de la medecine )."""
    return [a["cle"] for a in M.affections(p, h) if a["phase"] == "clinique" and a["gravite"] > 0]


def _iss(p, h):
    return max((a["iss"] for a in M.affections(p, h) if a["pathologie"].startswith("lesion_")), default=0)


def _grave(h):
    return h.vivant and h.etat == "I" and h.gravite > GRAVITE_LIT


def _critique(h):
    return h.vivant and h.etat == "I" and h.gravite >= GRAVITE_REA


def esi(p, h):
    """Le niveau de tri ESI ( 1 le plus grave, 5 le moins ) : ce que voit l infirmier d accueil - la gravite visible
    ( signes vitaux ), les besoins en ressources - projete sur priorite et besoins de la medecine."""
    pr = M.priorite(p, h)
    if pr == 0: return 5
    b = M.besoins(p, h)
    if pr in (1, 4) or b["reanimation"]: return 1
    if _iss(p, h) >= 16 or b["sang"] or b["oxygene"]: return 2
    if b["lit"]: return 3
    if b["chirurgie"]: return 4
    return 5


def issue_du_jour(p, h):
    """La consequence du jour pour un malade : 0 s il est mort, 1 - gravite s il vit."""
    if not h.vivant: return 0.0
    return 1.0 - (min(1.0, h.gravite) if h.etat == "I" else 0.0)


# ================================================================== les lots
def _ajouter_lot(lots, b, q, fin):
    l = lots.setdefault(b, [])
    k = len(l)
    while k > 0 and l[k - 1][1] > fin: k -= 1
    l.insert(k, [q, fin])


def _retirer_lots(holder, b, q):
    """Retire q unites des lots, les plus proches de la peremption d abord ; rend [ ( quantite, fin ) ] retires."""
    lots = holder.lots.get(b, [])
    out, reste = [], q
    while reste > 1e-12 and lots:
        l = lots[0]
        x = min(l[0], reste)
        l[0] -= x; reste -= x; out.append((x, l[1]))
        if l[0] <= 1e-12: lots.pop(0)
    if not lots and b in holder.lots and not holder.stock[b]: holder.lots.pop(b, None)
    return out


def _deplacer(p, src, dst, b, q, motif):
    """Un deplacement de stock a stock, lots compris ( la peremption suit la boite )."""
    pris = p.socle.livre.deplacer(src.stock, dst.stock, b, q, motif)
    if pris > 0:
        for x, fin in _retirer_lots(src, b, pris): _ajouter_lot(dst.lots, b, x, fin)
        if not src.stock[b]: src.lots.pop(b, None)
    return pris


def _entrer(p, H, holder, nom, q, nature, motif, bilan):
    if q <= 0: return 0.0
    b = H.id_mol[nom]
    L = p.socle.livre
    if nature == "importe": L.importer(holder.stock, b, q, motif)
    else: L.produire(holder.stock, b, q, motif)
    _ajouter_lot(holder.lots, b, q, p.jour + M.MOL[nom].conservation_j)
    H.bilan[nom][bilan] += q
    return q


def _prendre(p, H, e, nom, q, motif="soin_hopital"):
    """Sortir q unites de la pharmacie de l etablissement ( consommation, lots, usage des antibiotiques )."""
    if q <= 0: return 0.0
    pris = M.prendre(p, e, nom, q, motif, region=e.region)
    if pris > 0:
        e.sortie_jour[M.IMOL[nom]] += pris; H.bilan[nom][4] += pris
    return pris


def _donner(p, H, e, h, slots, nom, q, t):
    """Un traitement de la medecine donne sur la pharmacie de l etablissement."""
    pris, ok = M.traiter(p, h, slots, nom, q, e, "soin_hopital", t)
    if pris > 0:
        e.sortie_jour[M.IMOL[nom]] += pris; H.bilan[nom][4] += pris
    if pris < q - 1e-9:
        H.compter(("traitement_manque", nom)); p.compter("traitement_manque")
    return pris, ok


# ================================================================== l argent
def _financer_eopyy(p, H, montant):
    """L Etat verse a l EOPYY ce qui lui manque pour payer : l assurance maladie grecque est deficitaire et l Etat
    comble ( subvention d equilibre ). Le domaine 6 emprunte avant, s il le faut."""
    ey = H.eopyy; w = p.w
    manque = montant - ey.caisse
    if manque <= 1e-9: return
    if p.a("etat"):
        from . import d06_etat as ET
        ET.assurer(p, manque)
    ey.recu_etat += p.socle.livre.transferer(w.gouv, ey, manque, "financement_eopyy")


def _dotation_esy(p, H, e, montant):
    if montant <= 1e-9: return 0.0
    if p.a("etat"):
        from . import d06_etat as ET
        ET.assurer(p, montant)
    return p.socle.livre.transferer(p.w.gouv, e, montant, "dotation_esy")


def _carburant(p, e, litres, motif):
    """Du gazole brule aussitot ( ambulance, groupe electrogene ), achete a la station du marche de l etablissement
    ( domaine 14 ) ou, sans lui, au marche du moteur. Rend les litres servis."""
    if litres <= 0: return 0.0
    w = p.w; L = p.socle.livre
    if p.a("transport"):
        from . import d14_transport as TR
        return TR.faire_le_plein(p, e, "carburant", litres, e.lieu)
    m = w.marches.get(e.lieu)
    if m is None: return 0.0
    u = litres / LITRES_UNITE
    m.demande["carburant"] += u
    prix = m.prix["carburant"]; tva = w.gouv.tva
    u = min(u, m.stocks["carburant"], max(0.0, e.caisse) / max(1e-9, prix * (1.0 + tva)))
    if u <= 1e-12: return 0.0
    m.stocks["carburant"] -= u; L.flux["brule"]["carburant"] += u
    L.transferer(e, m, u * prix, motif)
    L.transferer(e, w.gouv, u * prix * tva, "tva")
    return u * LITRES_UNITE


def _kit(p, e):
    """Le kit de soins du moteur ( remedes ) : du stock public des hopitaux, sinon achete au marche par
    l etablissement ( a l hopital public, le malade ne paie pas )."""
    w = p.w; L = p.socle.livre
    if w.publics["hopitaux"]["remedes"] >= 1:
        w.publics["hopitaux"]["remedes"] -= 1; L.flux["consomme"]["remedes"] += 1; return True
    m = w.marches.get(e.lieu)
    if m is None: return False
    m.demande["remedes"] += 1
    prix = m.prix["remedes"]; tva = w.gouv.tva
    if m.stocks["remedes"] >= 1 and e.caisse >= prix * (1 + tva):
        m.stocks["remedes"] -= 1; L.flux["consomme"]["remedes"] += 1
        L.transferer(e, m, prix, "kit_hopital"); L.transferer(e, w.gouv, prix * tva, "tva")
        return True
    return False


def _kit_dispo(p, e):
    w = p.w
    if w.publics["hopitaux"]["remedes"] >= 1: return True
    m = w.marches.get(e.lieu)
    return m is not None and m.stocks["remedes"] >= 1 and e.caisse >= m.prix["remedes"] * (1 + w.gouv.tva)


# ================================================================== le personnel
def _present(p, H, hid, now):
    """De garde a ce pas : son equipe ( trois fois 8 h, moteur ) ou un rappel en cours ; ni mort, ni alite, ni en greve."""
    h = p.w.habitants[hid]
    if not h.vivant or (h.etat == "I" and h.gravite > M.GRAVITE_ALITE): return False
    r = H.rappel.get(hid)
    if r is not None and r[0] <= now < r[1]: return True
    if p.a("travail"):
        from . import d04_travail as TV
        if TV.en_greve(p, h): return False
    return h.au_travail(p.heure)


def _libres(p, H, e, specs, now):
    """Les medecins presents et libres de l etablissement, dans l ordre de preference des specialites."""
    out = []
    for s in specs:
        for hid in e.medecins:
            if e.specialite.get(hid) == s and H.occupe.get(hid, -1) <= now and _present(p, H, hid, now): out.append(hid)
    return out


def _facteur_fatigue(H, hids):
    return FACTEUR_FATIGUE if any(H.continu.get(x, 0.0) > FATIGUE_H for x in hids) else 1.0


def _rappelable(p, H, hid, now):
    h = p.w.habitants[hid]
    if not h.vivant or (h.etat == "I" and h.gravite > M.GRAVITE_ALITE): return False
    r = H.rappel.get(hid)
    if r is not None and r[1] > now: return False
    if _present(p, H, hid, now): return False
    return H.continu.get(hid, 0.0) + DUREE_RAPPEL_PAS * MIN_PAS / 60.0 <= MAX_CONTINU_H


def _rappeler(p, H, e, hids, now):
    n = 0
    for hid in hids:
        if _rappelable(p, H, hid, now):
            H.rappel[hid] = (now + RAPPEL_PAS, now + RAPPEL_PAS + DUREE_RAPPEL_PAS); n += 1
    if n: p.compter("rappel_astreinte", float(n)); H.compter("rappels", n)
    return n


def _rappeler_specialite(p, H, e, spec, now):
    """Rappelle UN medecin de cette specialite s il n y en a aucun qui arrive deja."""
    for hid in e.medecins:
        if e.specialite.get(hid) != spec: continue
        r = H.rappel.get(hid)
        if r is not None and now < r[0]: return 0      # il est en route
    cands = [hid for hid in e.medecins if e.specialite.get(hid) == spec]
    for hid in cands:
        if _rappelable(p, H, hid, now): return _rappeler(p, H, e, [hid], now)
    return 0


def _plan_blanc(p, H, e, now):
    """Le rappel general : tous les medecins et infirmiers qui peuvent venir viennent."""
    if e.plan_blanc_jusqu > now: return
    e.plan_blanc_jusqu = now + DUREE_RAPPEL_PAS
    n = _rappeler(p, H, e, e.medecins + e.infirmiers, now)
    p.noter("plan_blanc", etablissement=e.nom, file=len(e.file_med) + len(e.file_bloc))
    if e.type == "hopital" and H.dernier_appel_dons.get(e.id, -10 ** 9) <= p.jour - 7:
        H.dernier_appel_dons[e.id] = p.jour
        p.poser(DELAI_APPEL_DONS_PAS, "hopitaux_appel_dons", e.id, ())
    H.compter("plans_blancs")
    return n


def _affecter_personnel(p, H):
    """Chaque jour : les medecins et infirmiers vivants du moteur, a l hopital de leur capitale ( avec le domaine 4 :
    ceux qui ont la qualification du metier ) ; un nouveau medecin prend la specialite qui manque le plus au plan de
    dotation."""
    w = p.w
    par_lieu = {}
    qualif = None
    if p.a("travail"):
        from . import d04_travail as TV
        qualif = TV.peut_exercer
    for h in w.habitants:
        if not h.vivant or h.role not in ("medecin", "infirmier"): continue
        if qualif is not None and not qualif(p, h, h.role): continue      # un medecin sans diplome n exerce pas
        lieu = h.travail.id if h.travail is not None else h.domicile.marche.id
        par_lieu.setdefault((lieu, h.role), []).append(h.id)
    for e in H.etabs:
        if e.type != "hopital": continue
        e.medecins = sorted(par_lieu.get((e.lieu, "medecin"), []))
        e.infirmiers = sorted(par_lieu.get((e.lieu, "infirmier"), []))
        e.specialite = {hid: s for hid, s in e.specialite.items() if hid in set(e.medecins)}
        for hid in e.medecins:
            if hid in e.specialite: continue
            have = collections.Counter(e.specialite.values())
            manque = [s for s in PLAN_DOTATION if have.get(s, 0) == 0]
            if manque: e.specialite[hid] = manque[0]; continue
            n = len(e.specialite) + 1
            e.specialite[hid] = max(SPECIALITES, key=lambda s: (PART_SPECIALITES[s] * n - have.get(s, 0), -SPECIALITES.index(s)))


def _fatigue(p, H, now):
    """Chaque heure : les heures de garde continues de chaque soignant ; 8 heures de repos les remettent a zero."""
    for e in H.etabs:
        for hid in e.medecins + e.infirmiers:
            if _present(p, H, hid, now):
                H.continu[hid] = H.continu.get(hid, 0.0) + 1.0; H.repos[hid] = 0.0
            else:
                r = H.repos.get(hid, REPOS_H) + 1.0
                H.repos[hid] = r
                if r >= REPOS_H: H.continu.pop(hid, None)


def a_une_equipe_chirurgicale(e):
    s = set(e.specialite.values())
    return "chirurgien" in s and "anesthesiste" in s


# ================================================================== le point de decision
def _observer(ctx): return ctx.traits


def _regle_triage(x, ctx):
    esi_g, esi_p, esi_m, att_p, att_g, file, res, libres, pers, fat, sang = x
    if res == 0.0 and file >= 0.4 and esi_m <= 0.25: return RENVOYER
    return PLUS_GRAVE if esi_g > esi_p else PREMIER


def _temoin_triage(x, ctx, rng): return PREMIER


POINT_TRIAGE = D.PointDeDecision(
    "triage", "hopitaux",
    traits=(("esi_plus_grave", "le tri infirmier : niveau ESI du plus grave en attente, ( 5 - ESI ) / 4"),
            ("esi_premier", "le tri infirmier : niveau ESI du premier arrive, ( 5 - ESI ) / 4"),
            ("esi_moins_grave", "le tri infirmier : niveau ESI du moins grave, ( 5 - ESI ) / 4"),
            ("attente_premier", "le registre de l accueil : attente du premier arrive, sur 6 heures"),
            ("attente_plus_grave", "le registre de l accueil : attente du plus grave, sur 6 heures"),
            ("file", "le registre de l accueil : malades en attente de cette ressource, sur 10"),
            ("ressource", "la ressource qui se libere : medecin 0, bloc 1/3, lit 2/3, ambulance 1"),
            ("libres", "le tableau de service : part libre de la ressource"),
            ("personnel", "le tableau de service : medecins presents, sur 5"),
            ("fatigue", "le tableau de service : heures de garde continues du plus fatigue des presents, sur 24"),
            ("sang", "la banque de sang : culots en stock sur le besoin du plus grave ( 1 s il n en faut pas )")),
    actions=("premier_arrive", "plus_grave", "renvoyer_moins_grave"), observer=_observer, regle=_regle_triage,
    temoin=_temoin_triage,
    note="pour CES malades ( premier arrive, plus grave, moins grave : servis, ecartes ou renvoyes selon l action ), "
         "chaque jour : moyenne de 1 - gravite s il vit, 0 s il est mort",
    horizon_j=HORIZON_TRIAGE)


def _traits(p, H, e, cands, g, prem, moins, ressource, libres, now):
    pres = [hid for hid in e.medecins if _present(p, H, hid, now)] if e is not None else []
    fat = max((H.continu.get(x, 0.0) for x in pres), default=0.0)
    besoin = M.besoins(p, p.w.habitants[g.hid])["sang"] if not g.transfuse else 0
    sang = 1.0 if not besoin or e is None else min(1.0, e.stock[H.id_mol["sang"]] / besoin)
    return ((5 - g.esi) / 4.0, (5 - prem.esi) / 4.0, (5 - moins.esi) / 4.0,
            min(1.0, (now - prem.t_file) / DUREE_URGENCE_MAX_PAS), min(1.0, (now - g.t_file) / DUREE_URGENCE_MAX_PAS),
            min(1.0, len(cands) / 10.0), RESSOURCES[ressource], min(1.0, max(0.0, libres)), min(1.0, len(pres) / 5.0),
            min(1.0, fat / 24.0), sang)


def _choisir(p, H, e, file, ressource, libres, now):
    """Qui passe d abord. Sans dilemme ( le premier arrive est aussi grave que le plus grave ), le premier arrive ; avec
    un dilemme, le point de decision `triage`. Rend le passage servi ( retire de la file ), ou None."""
    W = p.w.habitants
    cands = [H.actifs[hid] for hid in file]
    if not cands: return None
    for ps in cands: ps.esi = esi(p, W[ps.hid])
    prem = min(cands, key=lambda s: (s.t_file, s.id))
    g = min(cands, key=lambda s: (s.esi, s.t_file, s.id))
    if len(cands) < 2 or g.esi >= prem.esi:
        file.remove(prem.hid); return prem
    moins = max(cands, key=lambda s: (s.esi, s.t_file, s.id))
    x = _traits(p, H, e, cands, g, prem, moins, ressource, libres, now)
    cle = H.prochain_evt; H.prochain_evt += 1
    a = H.dec.decider(cle, ContexteTriage(x))
    if a == PREMIER: choisi, ecarte = prem, g
    elif a == PLUS_GRAVE: choisi, ecarte = g, prem
    else: choisi, ecarte = g, moins
    H.evts[cle] = tuple(sorted({prem.hid, g.hid, moins.hid}))    # ceux que l une des actions sert ou ecarte
    H.suivi.append([cle, a, p.jour, ressource, choisi.hid, ecarte.hid, choisi.esi, ecarte.esi])
    if len(H.suivi) > 50000: del H.suivi[:10000]
    file.remove(choisi.hid)
    if a == RENVOYER and ecarte is not choisi and ecarte.hid in file:
        file.remove(ecarte.hid)
        _clore(p, H, ecarte, RENVOYE)
        p.compter("renvoi_domicile")
    return choisi


# ================================================================== l entree : Monde.soigner
def soigner(p, h):
    """Monde.soigner : un malade grave ou un blesse arrive dans le systeme de soins de sa capitale. Deja pris en charge :
    le soutien qui manque est retente. Rend vrai si le malade a son soutien."""
    if not h.vivant: return False
    H = _dom(p)
    ps = H.actifs.get(h.id)
    if ps is not None:
        if ps.etat in (LIT, REA) and not ps.soutien: _soutien(p, H, H.etabs[ps.etab], ps, bloc=False)
        return ps.soutien
    e = H.etab_de_lieu.get(h.domicile.marche.id)
    if e is None: return M.soigner_defaut(p, h)
    admettre(p, h, e, None)
    return False


def admettre(p, h, destination=None, origine=None, ambulance=None, delai_pas=None):
    """Domaines 18, 26, 27 : conduire h a un etablissement ( celui de sa capitale par defaut ) depuis le lieu `origine`
    ( son lieu actuel par defaut ). `ambulance` : None ( selon son etat : blesse grave, ESI 1-2, ou il ne vient pas
    seul ), vrai ou faux. `delai_pas` : le transport est fait par l appelant ( evacuation militaire, helicoptere ) et
    arrive dans ce nombre de pas. Rend le Passage, ou None s il est deja pris en charge."""
    H = _dom(p); w = p.w
    if not h.vivant or h.id in H.actifs: return None
    e = destination if destination is not None else H.etab_de_lieu.get(h.domicile.marche.id)
    if e is None: return None
    if isinstance(e, int): e = H.etabs[e]
    now = w.pas
    lieu = origine if origine is not None else (h.lieu.id if h.lieu is not None else h.domicile.id)
    ps = Passage(H.prochain, h.id, e.id, now, lieu); H.prochain += 1
    ps.esi = esi(p, h); ps.iss = _iss(p, h)
    H.actifs[h.id] = ps
    if delai_pas is not None:
        ps.etat = TRANSPORT
        p.poser(max(0, int(delai_pas)), "hopitaux_arrivee", h.id, (ps.id,))
        return ps
    if ambulance is None:
        ambulance = ps.esi <= 2 or ps.iss >= 16 or H.rng.random() >= PART_PROPRES_MOYENS
    if ambulance:
        ps.etat = APPEL; ps.t_file = now
        H.appels.setdefault(e.ile, []).append(h.id)
    else:
        km = max(KM_URBAIN, w.carte.km_route(w.carte.lieux[lieu], w.carte.lieux[e.lieu]))
        d = int(math.ceil((ATTENTE_DEPART_MIN + km / VITESSE_PROPRE_KMH * 60.0) / MIN_PAS))
        ps.etat = TRANSPORT
        p.poser(d, "hopitaux_arrivee", h.id, (ps.id,))
    return ps


def _arrivee(p, hid, donnees):
    H = _dom(p)
    ps = H.actifs.get(hid)
    if ps is None or ps.id != donnees[0] or ps.etat != TRANSPORT: return
    e = H.etabs[ps.etab]
    now = p.w.pas
    ps.t_arrivee = now; ps.t_file = now
    if ps.opere or ps.vu:                             # un transfert : il vient pour le bloc ou pour un lit
        b = M.besoins(p, p.w.habitants[hid])
        if b["chirurgie"] and not ps.opere: ps.etat = ATT_BLOC; e.file_bloc.append(hid)
        elif b["reanimation"]: ps.etat = ATT_REA; e.file_rea.append(hid)
        else: ps.etat = ATT_LIT; e.file_lit.append(hid)
    else:
        ps.etat = ATT_MED; e.file_med.append(hid)


# ================================================================== les ambulances
def _ambulances(p, H, now):
    w = p.w; lx = w.carte.lieux
    for ile in sorted(H.appels):
        file = H.appels[ile]
        if not file: continue
        libres = [(oid, e) for e in H.etabs if e.ile == ile and e.ouvert for oid in e.ambulances
                  if H.amb_libre.get(oid, -1) <= now]
        while libres and file:
            dest0 = H.etabs[H.actifs[file[0]].etab]
            ps = _choisir(p, H, dest0, file, "ambulance", len(libres) / max(1, len(libres) + len(file)), now)
            if ps is None: break
            o = lx[ps.origine]
            k = min(range(len(libres)), key=lambda i: (w.carte.km_route(lx[libres[i][1].lieu], o), libres[i][0]))
            oid, base = libres.pop(k)
            dest = H.etabs[ps.etab]
            d1 = max(KM_URBAIN, w.carte.km_route(lx[base.lieu], o))
            d2 = max(KM_URBAIN, w.carte.km_route(o, lx[dest.lieu]))
            d3 = w.carte.km_route(lx[dest.lieu], lx[base.lieu])
            v = VITESSE_AMBULANCE_KMH / 60.0
            arr = int(math.ceil((DECROCHE_MIN + d1 / v + SUR_PLACE_MIN + d2 / v) / MIN_PAS))
            H.amb_libre[oid] = now + arr + int(math.ceil((NETTOYAGE_MIN + d3 / v) / MIN_PAS))
            ps.etat = TRANSPORT; ps.ambulance = oid
            p.poser(arr, "hopitaux_arrivee", ps.hid, (ps.id,))
            _carburant(p, base, (d1 + d2 + d3) * L_PAR_KM_AMBULANCE, "carburant_ambulance")
            p.compter("mission_ambulance"); H.compter("missions")


# ================================================================== les urgences, le bloc, les lits
def _examiner(p, H, e, ps, now):
    """L examen aux urgences : diagnostic ( examens de l hopital s il a son laboratoire ), protocole de la medecine sur
    la pharmacie de l etablissement, antalgie et antibiotique des blesses, puis l orientation : bloc, reanimation, lit,
    ou sortie."""
    h = p.w.habitants[ps.hid]; t = _t(p)
    ps.vu = True; ps.t_vu = now
    H.attentes.append((p.jour, e.id, ps.esi, (now - ps.t_arrivee) * MIN_PAS))
    p.compter("passage_urgences"); H.compter("passages")
    cl = _slots(p, h)
    if not cl:
        _clore(p, H, ps, SORTI); return
    diag, _ = M.diagnostiquer(p, h, "hopital" if e.labo else "cabinet")
    ps.diag = diag
    med = p.domaine("medecine")
    declarer = getattr(M, "_declarer", None)
    if diag is not None and declarer is not None: declarer(med, e.region, diag)
    for mol, u, _ in M.PROTOCOLE_HOPITAL.get(diag, ()): _donner(p, H, e, h, cl, mol, u, t)
    for a in M.affections(p, h):
        if a["cle"] in cl and a["pathologie"].startswith("lesion_"):
            _prendre(p, H, e, "morphine" if a["iss"] >= 9 else "paracetamol", 3.0)
            if a["pathologie"][7:] in M.PENETRANTES: _donner(p, H, e, h, [a["cle"]], "amoxicilline", 5, t)
    M.prise_en_charge(p, h, soutien=False, slots=cl)
    _orienter(p, H, e, ps, now)


def _orienter(p, H, e, ps, now):
    h = p.w.habitants[ps.hid]
    if not h.vivant: _clore(p, H, ps, DECEDE); return
    b = M.besoins(p, h)
    ps.sang = float(b["sang"])
    ps.t_file = now
    if b["chirurgie"] and not ps.opere:
        if a_une_equipe_chirurgicale(e) and e.bloc_occ: ps.etat = ATT_BLOC; e.file_bloc.append(ps.hid); return
        autre = _etab_chirurgical(p, H, e)
        if autre is not None: _transferer(p, H, ps, e, autre, now); return
        ps.etat = ATT_BLOC; e.file_bloc.append(ps.hid); return
    if b["reanimation"] or b["lit"]:
        if not e.lits_occ and not e.rea_occ:
            autre = _etab_avec_lits(p, H, e)
            if autre is not None: _transferer(p, H, ps, e, autre, now); return
        if b["reanimation"]: ps.etat = ATT_REA; e.file_rea.append(ps.hid)
        else: ps.etat = ATT_LIT; e.file_lit.append(ps.hid)
        return
    _clore(p, H, ps, SORTI)


def _etab_chirurgical(p, H, e):
    w = p.w; lx = w.carte.lieux
    c = [x for x in H.etabs if x is not e and x.ouvert and x.ile == e.ile and x.bloc_occ and a_une_equipe_chirurgicale(x)]
    return min(c, key=lambda x: (w.carte.km_route(lx[e.lieu], lx[x.lieu]), x.id)) if c else None


def _etab_avec_lits(p, H, e):
    w = p.w; lx = w.carte.lieux
    c = [x for x in H.etabs if x is not e and x.ouvert and x.ile == e.ile and (x.lits_occ or x.rea_occ) and not x.prive]
    return min(c, key=lambda x: (w.carte.km_route(lx[e.lieu], lx[x.lieu]), x.id)) if c else None


def _etab_libre(p, H, e, arr_de):
    """L hopital public le plus proche de la meme ile qui a un lit libre du genre voulu et personne qui l attende ( ni
    en file, ni en route vers lui )."""
    w = p.w; lx = w.carte.lieux
    en_route = collections.Counter(H.actifs[x].etab for x in H.appels.get(e.ile, ()) if H.actifs[x].vu)
    c = [x for x in H.etabs if x is not e and x.ouvert and not x.prive and x.ile == e.ile
         and getattr(x, arr_de).count(-1) > en_route.get(x.id, 0) and not x.file_lit and not x.file_rea]
    return min(c, key=lambda x: (w.carte.km_route(lx[e.lieu], lx[x.lieu]), x.id)) if c else None


def _transferer(p, H, ps, de, vers, now):
    """Un transfert inter-hospitalier, en ambulance : le malade quitte la file de son hopital pour celle de l autre."""
    ps.etab = vers.id; ps.origine = de.lieu; ps.etat = APPEL; ps.t_file = now
    H.appels.setdefault(vers.ile, []).append(ps.hid)
    p.noter("transfert_patient", habitant=ps.hid, origine=de.nom, destination=vers.nom)
    H.compter("transferts")


def _urgences(p, H, e, now):
    if not e.file_med: return
    if len(e.file_med) + len(e.file_bloc) >= SEUIL_PLAN_BLANC: _plan_blanc(p, H, e, now)
    docs = _libres(p, H, e, ORDRE_URGENCES, now)
    if not docs:
        if not any(_present(p, H, x, now) for x in e.medecins) and not any(
                H.rappel.get(x, (0, -1))[0] > now for x in e.medecins):
            cand = sorted(e.medecins, key=lambda x: (ORDRE_URGENCES.index(e.specialite.get(x, "interniste")), x))
            for hid in cand:
                if _rappeler(p, H, e, [hid], now): break
        return
    while docs and e.file_med:
        ps = _choisir(p, H, e, e.file_med, "medecin", len(docs) / max(1, len(e.medecins)), now)
        if ps is None: break
        doc = docs.pop(0)
        H.occupe[doc] = now + int(math.ceil(DUREE_EXAMEN_MIN[ps.esi] * _facteur_fatigue(H, [doc]) / MIN_PAS))
        _examiner(p, H, e, ps, now)


def _blocs(p, H, e, now):
    for k in range(len(e.bloc_occ)):
        if e.bloc_occ[k] >= 0 and e.bloc_fin[k] <= now: _fin_chirurgie(p, H, e, k, now)
    if not e.file_bloc or e.sans_courant or e.bloc_ferme_jusqu > p.jour: return
    for k in range(len(e.bloc_occ)):
        if e.bloc_occ[k] >= 0 or not e.file_bloc: continue
        chir = _libres(p, H, e, ("chirurgien",), now); anes = _libres(p, H, e, ("anesthesiste",), now)
        if not chir: _rappeler_specialite(p, H, e, "chirurgien", now)
        if not anes: _rappeler_specialite(p, H, e, "anesthesiste", now)
        if not chir or not anes: return
        libres = sum(1 for x in e.bloc_occ if x < 0) / max(1, len(e.bloc_occ))
        if not _kit_dispo(p, e) and not any(H.actifs[x].kit for x in e.file_bloc): return
        if e.stock[H.id_mol["anesthesique"]] < 1.0 - 1e-9: return
        prets = [hid for hid in e.file_bloc if _pret_pour_bloc(p, H, e, H.actifs[hid])]
        if not prets: return
        ps = _choisir(p, H, e, prets, "bloc", libres, now)
        if ps is None: return
        if ps.hid in e.file_bloc: e.file_bloc.remove(ps.hid)
        h = p.w.habitants[ps.hid]
        iss = _iss(p, h)
        duree = (CHIRURGIE_MIN[0] + CHIRURGIE_MIN[1] * iss if iss else CHIRURGIE_MEDICALE_MIN) \
            * _facteur_fatigue(H, [chir[0], anes[0]])
        e.bloc_occ[k] = ps.hid; e.bloc_fin[k] = now + int(math.ceil(duree / MIN_PAS))
        H.occupe[chir[0]] = H.occupe[anes[0]] = e.bloc_fin[k]
        ps.etat = BLOC; ps.opere = True; ps.lit = k
        p.compter("chirurgie"); H.compter("chirurgies")
        _soutien(p, H, e, ps, bloc=True)


def _pret_pour_bloc(p, H, e, ps):
    """On n ouvre pas un malade dont le sang, l anesthesique ou le kit ne sont pas la : il attend ( et on lui cherche
    du sang ), le bloc prend le suivant. Sans cette verification, une intervention sans transfusion occupait le bloc
    trois heures pour rien ( mesure du 24/09 )."""
    ido = H.id_mol
    sang = ps.sang if not ps.transfuse else 0.0
    if sang and e.stock[ido["sang"]] < sang - 1e-9:
        _demander_sang(p, H, e, sang - e.stock[ido["sang"]]); return False
    if not ((ps.kit or _kit_dispo(p, e)) and e.stock[ido["anesthesique"]] >= 1.0 - 1e-9): return False
    return not M.besoins(p, p.w.habitants[ps.hid])["oxygene"] or e.stock[ido["oxygene"]] >= 5.0 - 1e-9


def _fin_chirurgie(p, H, e, k, now):
    hid = e.bloc_occ[k]
    e.bloc_occ[k] = -1
    ps = H.actifs.get(hid)
    if ps is None or ps.etat != BLOC: return
    ps.lit = -1
    _orienter(p, H, e, ps, now)


def _coucher(p, H, e, ps, rea, i, now):
    (e.rea_occ if rea else e.lits_occ)[i] = ps.hid
    ps.etat = REA if rea else LIT; ps.lit = i; ps.admis = True
    if not rea: ps.attend_rea = _critique(p.w.habitants[ps.hid])
    p.compter("admission_rea" if rea else "admission_hopital"); H.compter("admissions_rea" if rea else "admissions")
    _soutien(p, H, e, ps, bloc=False)


def _infirmiers_ok(p, H, e, n_rea, now):
    pres = sum(1 for x in e.infirmiers if _present(p, H, x, now))
    return n_rea <= PATIENTS_PAR_INFIRMIER_REA * pres


def _lits(p, H, e, now):
    W = p.w.habitants
    # ceux qui n ont plus besoin de la ressource qu ils attendent
    for hid in list(e.file_rea):
        h = W[hid]
        if not _critique(h):
            e.file_rea.remove(hid); ps = H.actifs[hid]
            if _grave(h): ps.etat = ATT_LIT; ps.t_file = now; e.file_lit.append(hid)
            else: _clore(p, H, ps, SORTI)
    for hid in list(e.file_lit):
        if not _grave(W[hid]): e.file_lit.remove(hid); _clore(p, H, H.actifs[hid], SORTI)
    # reanimation
    while e.file_rea and -1 in e.rea_occ:
        n = sum(1 for x in e.rea_occ if x >= 0) + 1
        if not _infirmiers_ok(p, H, e, n, now):
            _rappeler(p, H, e, [x for x in e.infirmiers if not _present(p, H, x, now)][:1], now); break
        ps = _choisir(p, H, e, e.file_rea, "lit", e.rea_occ.count(-1) / max(1, len(e.rea_occ)), now)
        if ps is None: break
        _coucher(p, H, e, ps, True, e.rea_occ.index(-1), now)
    # un malade de reanimation couche en salle monte des qu un lit de reanimation se libere
    for i, hid in enumerate(e.lits_occ):
        if hid >= 0 and -1 in e.rea_occ:
            ps = H.actifs[hid]
            if ps.attend_rea and _critique(W[hid]) and _infirmiers_ok(p, H, e, sum(1 for x in e.rea_occ if x >= 0) + 1, now):
                e.lits_occ[i] = -1
                _coucher(p, H, e, ps, True, e.rea_occ.index(-1), now)
    # lits generaux
    while e.file_lit and -1 in e.lits_occ:
        ps = _choisir(p, H, e, e.file_lit, "lit", e.lits_occ.count(-1) / max(1, len(e.lits_occ)), now)
        if ps is None: break
        _coucher(p, H, e, ps, False, e.lits_occ.index(-1), now)
    # debordement : la reanimation est pleine, un lit de salle vaut mieux qu un brancard
    while e.file_rea and -1 in e.lits_occ:
        hid = e.file_rea.pop(0); ps = H.actifs[hid]
        _coucher(p, H, e, ps, False, e.lits_occ.index(-1), now)
    # les lits conventionnes des cliniques de la meme capitale
    if e.file_lit and not e.prive:
        for c in H.etabs:
            if not (c.prive and c.ouvert and c.lieu == e.lieu): continue
            while e.file_lit and -1 in c.lits_occ:
                hid = e.file_lit.pop(0); ps = H.actifs[hid]
                ps.etab = c.id; ps.prive = True
                _coucher(p, H, c, ps, False, c.lits_occ.index(-1), now)
    # la regulation des lits : un malade qui attend un lit part vers l hopital de l ile qui en a un libre et personne
    # en attente ( un transfert par pas et par hopital : l ambulance le prend )
    if not e.prive:
        for file, arr_de in ((e.file_rea, "rea_occ"), (e.file_lit, "lits_occ")):
            if not file or -1 in getattr(e, arr_de): continue
            autre = _etab_libre(p, H, e, arr_de)
            if autre is not None:
                ps = H.actifs[file.pop(0)]
                _transferer(p, H, ps, e, autre, now)


def _soutien(p, H, e, ps, bloc):
    """Le soutien, tout ou rien ( comme la medecine ) : le kit du moteur, l oxygene d un malade respiratoire grave, le
    sang, l anesthesique au bloc ; en reanimation seulement pour qui en a besoin. Rien n est entame si quelque chose
    manque : on attend la livraison, le don, le lit."""
    h = p.w.habitants[ps.hid]
    if not h.vivant or ps.soutien: return ps.soutien
    b = M.besoins(p, h)
    if not bloc and b["reanimation"] and ps.etat != REA: return False
    if e.sans_courant and (bloc or ps.etat == REA): return False
    ido = H.id_mol
    sang = float(b["sang"]) if not ps.transfuse else 0.0
    ok = (ps.kit or _kit_dispo(p, e)) and (not b["oxygene"] or e.stock[ido["oxygene"]] >= 5.0 - 1e-9) \
        and (not sang or e.stock[ido["sang"]] >= sang - 1e-9) \
        and (not bloc or e.stock[ido["anesthesique"]] >= 1.0 - 1e-9)
    if not ok:
        if sang and e.stock[ido["sang"]] < sang - 1e-9: _demander_sang(p, H, e, sang - e.stock[ido["sang"]])
        H.compter("soutien_manque"); p.compter("soutien_manque"); return False
    if not ps.kit: ps.kit = _kit(p, e)
    if b["oxygene"]: _prendre(p, H, e, "oxygene", 5.0)
    if sang: _prendre(p, H, e, "sang", sang); ps.transfuse = True
    if bloc: _prendre(p, H, e, "anesthesique", 1.0)
    M.prise_en_charge(p, h, soutien=True, slots=_slots(p, h))
    ps.soutien = True; ps.t_soutien = p.w.pas
    return True


def _besoin_sang_propre(p, H, e):
    """Le plus petit besoin de sang qu un malade de l etablissement attend ( bloc, lit sans soutien ) : ce qu il faut
    pour en soigner un de plus ; 0 si personne n attend de sang. Calcule une fois par pas et par etablissement."""
    c = H.cache_sang.get(e.id)
    if c is not None and c[0] == p.w.pas: return c[1]
    out = 0.0
    for hid in e.file_bloc + [x for x in e.lits_occ + e.rea_occ if x >= 0]:
        ps = H.actifs.get(hid)
        if ps is None or ps.transfuse or ps.soutien: continue
        b = ps.sang
        if b > 0 and (out == 0.0 or b < out): out = b
    H.cache_sang[e.id] = (p.w.pas, out)
    return out


def _demander_sang(p, H, e, besoin):
    """La banque de sang regionale : un hopital a court demande aux autres hopitaux de l ile le sang qu ils ne peuvent
    pas employer eux-memes ( ce qui ne couvre pas le besoin d un de leurs malades ) ; il ne le demande que si, avec ce
    qui est disponible, il atteint le besoin : le sang se concentre la ou il permet d operer. Il arrive par coursier
    ( route a 50 km/h, plus une demi-heure ). Un hopital qui attend du sang n en cede pas ( ni l inverse ) : pas de
    va-et-vient. Mesure du 24/09 : une reserve fixe de 2 culots par hopital bloquait tout, chacun gardant 2 et
    attendant 4."""
    if H.sang_attendu.get(e.id, 0.0) > 1e-9 or H.sang_promis.get(e.id, 0.0) > 1e-9: return
    if H.demande_sang_pas.get(e.id) == p.w.pas: return          # une demande par pas et par hopital
    H.demande_sang_pas[e.id] = p.w.pas
    w = p.w; lx = w.carte.lieux; b = H.id_mol["sang"]
    dons = []
    for x in sorted((x for x in H.etabs if x is not e and x.ile == e.ile and x.ouvert),
                    key=lambda x: (w.carte.km_route(lx[e.lieu], lx[x.lieu]), x.id)):
        if H.sang_attendu.get(x.id, 0.0) > 1e-9: continue
        dispo = x.stock[b] - H.sang_promis.get(x.id, 0.0)
        propre = _besoin_sang_propre(p, H, x)
        if propre and dispo >= propre - 1e-9: dispo -= propre * math.floor(dispo / propre + 1e-9)
        if dispo > 1e-9: dons.append((x, dispo))
    if math.fsum(q for _, q in dons) < besoin - 1e-9: return
    reste = besoin
    for x, dispo in dons:
        if reste <= 1e-9: break
        q = min(reste, dispo)
        km = w.carte.km_route(lx[x.lieu], lx[e.lieu])
        d = int(math.ceil((30.0 + km / VITESSE_AMBULANCE_KMH * 60.0) / MIN_PAS))
        p.poser(d, "hopitaux_sang", e.id, (x.id, float(q)))
        H.sang_attendu[e.id] = H.sang_attendu.get(e.id, 0.0) + q
        H.sang_promis[x.id] = H.sang_promis.get(x.id, 0.0) + q
        reste -= q


def _sang_arrive(p, eid, donnees):
    H = _dom(p); src, q = donnees
    e, x = H.etabs[eid], H.etabs[src]
    H.sang_attendu[eid] = max(0.0, H.sang_attendu.get(eid, 0.0) - q)
    H.sang_promis[src] = max(0.0, H.sang_promis.get(src, 0.0) - q)
    b = H.id_mol["sang"]
    q = min(q, x.stock[b])
    if q > 1e-9:
        _deplacer(p, x, e, b, q, "sang_regional"); H.compter("sang_regional", q)


def _appel_aux_dons(p, eid, donnees):
    """Les dons qui affluent apres une catastrophe, a la banque de sang de l hopital qui a lance le plan blanc."""
    H = _dom(p); e = H.etabs[eid]
    q = M.DONS_SANG_AN * e.pop * APPEL_DONS_JOURS / 365.0
    if q > 0: _entrer(p, H, e, "sang", q, "produit", "don_du_sang", 2); H.compter("appel_aux_dons")


# ================================================================== la sortie
def tarif_sejour(admis, opere, rea_jours):
    """Le forfait EOPYY d un passage ( drachmes ) : urgence seule, ou sejour ( KEN ), chirurgie, journees de reanimation."""
    if not admis and not opere: return KEN_URGENCE
    return KEN_SEJOUR + (KEN_CHIRURGIE if opere else 0.0) + KEN_REA_JOUR * rea_jours


def _clore(p, H, ps, issue):
    """Fin d un passage : les ressources se liberent, l EOPYY paie le forfait, le malade de clinique sa participation."""
    e = H.etabs[ps.etab]
    hid = ps.hid
    for f in (e.file_med, e.file_bloc, e.file_lit, e.file_rea, H.appels.get(e.ile, [])):
        if hid in f: f.remove(hid)
    if ps.etat == LIT and 0 <= ps.lit < len(e.lits_occ) and e.lits_occ[ps.lit] == hid: e.lits_occ[ps.lit] = -1
    if ps.etat == REA and 0 <= ps.lit < len(e.rea_occ) and e.rea_occ[ps.lit] == hid: e.rea_occ[ps.lit] = -1
    if ps.etat == BLOC and 0 <= ps.lit < len(e.bloc_occ) and e.bloc_occ[ps.lit] == hid:
        e.bloc_occ[ps.lit] = -1
    ps.lit = -1
    H.actifs.pop(hid, None)
    montant = part = 0.0
    if ps.vu or ps.admis or ps.opere:
        L = p.socle.livre
        montant = tarif_sejour(ps.admis, ps.opere, ps.rea_jours)
        _financer_eopyy(p, H, montant)
        paye = L.transferer(H.eopyy, e, montant, "ken_eopyy"); H.eopyy.paye_ken += paye
        if e.prive and ps.admis:
            h = p.w.habitants[hid]
            if h.menage is not None:
                part = L.transferer(h.menage, e, PARTICIPATION_CLINIQUE * montant, "participation_hospitaliere")
        H.factures.append((p.jour, hid, e.id, e.prive, montant, part, ps.rea_jours, ps.opere, issue))
    H.historique.append((ps.id, hid, e.id, issue, ps.esi, ps.iss, ps.t_appel, ps.t_arrivee, ps.t_vu, ps.t_soutien,
                         ps.opere, ps.admis, ps.soutien, p.w.pas))
    if issue == DECEDE: p.compter("deces_hopital"); H.compter("deces")
    elif issue == SORTI: p.compter("sortie_hopital"); H.compter("sorties")
    H.compter(("issue", issue))


def _balayer(p, H, now):
    """A chaque pas : les morts liberent leur place ; un malade couche qui n est plus grave sort ; un malade de
    reanimation qui n est plus critique descend en salle s il y a un lit."""
    W = p.w.habitants
    for hid in list(H.actifs):
        ps = H.actifs.get(hid)
        if ps is None: continue
        h = W[hid]
        if not h.vivant: _clore(p, H, ps, DECEDE); continue
        if ps.etat == LIT and not _grave(h): _clore(p, H, ps, SORTI); continue
        if ps.etat == REA:
            if not _grave(h): _clore(p, H, ps, SORTI); continue
            e = H.etabs[ps.etab]
            if not _critique(h) and -1 in e.lits_occ:
                e.rea_occ[ps.lit] = -1
                i = e.lits_occ.index(-1); e.lits_occ[i] = hid; ps.etat = LIT; ps.lit = i; ps.attend_rea = False


# ================================================================== le pas
def _pas(p):
    H = _dom(p); now = p.w.pas
    if p.w.minutes % 60 == 0:
        _fatigue(p, H, now)
        _energie(p, H)
    _balayer(p, H, now)
    _ambulances(p, H, now)
    for e in H.etabs:
        if not e.ouvert: continue
        _urgences(p, H, e, now)
        _blocs(p, H, e, now)
        _lits(p, H, e, now)
        if p.w.minutes % 60 == 0:
            for hid in e.lits_occ + e.rea_occ:
                if hid >= 0:
                    ps = H.actifs.get(hid)
                    if ps is not None and not ps.soutien: _soutien(p, H, e, ps, bloc=False)


def _energie(p, H):
    """Chaque heure : sans courant ( ligne coupee, delestage ), le groupe electrogene tourne et brule son gazole ; sans
    gazole, le bloc et la reanimation s arretent."""
    if not p.a("energie"): return
    from . import d11_energie as EN
    for e in H.etabs:
        if e.contrat is None: continue
        if EN.coupure_en_cours(p, e.lieu):
            kw = KW_PAR_LIT * (len(e.lits_occ) + len(e.rea_occ))
            besoin = kw * L_GAZOLE_PAR_KWH
            servi = _carburant(p, e, besoin, "groupe_electrogene")
            e.sans_courant = servi < besoin - 1e-6
            if not e.sans_courant: e.heures_groupe += 1; p.compter("heure_groupe")
        else:
            e.sans_courant = False


# ================================================================== la chaine du medicament
def _demande_officine(ph, k, nom):
    return max(float(ph.conso[k]), M.CONSO_A_PRIORI.get(nom, 0.0) * ph.pop / 1000.0 * 0.25)


def _demande_pui(e, k, nom):
    """La demande d une pharmacie hospitaliere : la plus forte de la consommation des 30 jours, de celle des 7 jours
    ( une vague, un afflux : la moyenne a 30 jours reagissait trop tard, l anesthesique manquait des le deuxieme jour
    d un accident de masse, mesure du 24/09 ) et de l attendu par habitant."""
    return max(float(e.conso[k]), float(e.conso7[k]), CONSO_HOPITAL_1000.get(nom, 0.0) * e.pop / 1000.0)


def _livrer(p, H, g, dst, b, q, payeur, officine):
    """Le grossiste livre q unites ( ce qu il a ) ; le client paie au prix mondial plus la marge du grossiste."""
    q = min(q, g.stock[b])
    if q <= 1e-9: return 0.0
    q = _deplacer(p, g, dst, b, q, "livraison_grossiste")
    if q <= 0: return 0.0
    nom = p.socle.catalogue[b].nom
    montant = q * p.socle.catalogue[b].prix_monde * (1.0 + MARGE_GROSSISTE)
    L = p.socle.livre
    if officine:
        _financer_eopyy(p, H, montant)
        H.eopyy.paye_officines += L.transferer(H.eopyy, g, montant, "remboursement_officines")
        H.bilan[nom][3] += q
    else:
        L.payer_ou_devoir(payeur, g, montant, "achat_medicaments", p.socle.creances, p.jour)
        payeur.achats_jour += montant
    p.compter("livraison_grossiste")
    return q


def _grossiste_de(H, ile):
    for g in H.grossistes:
        if g.ile == ile: return g
    return H.grossistes[0] if H.grossistes else None


def _tournee(p):
    """10 h : le grossiste de chaque ile livre les officines ( domaine 16 ) et les pharmacies hospitalieres ; le lundi,
    les dons de sang arrivent aux banques de sang des hopitaux ; les consommables de l industrie."""
    H = _dom(p); med = p.domaine("medecine"); w = p.w
    demandes = {}                      # ( grossiste, bien ) -> [ ( client, quantite voulue, payeur, officine ) ]
    for ph in med.pharmacies:
        g = _grossiste_de(H, w.carte.lieux[ph.lieu].ile)
        for k, nom in enumerate(M.NOMS_MOL):
            if nom in HOSPITALIERES: continue
            b = H.id_mol[nom]
            voulu = M.STOCK_CIBLE_J * _demande_officine(ph, k, nom) - ph.stock[b]
            if voulu > 0.5: demandes.setdefault((g.id, b), []).append((ph, voulu, H.eopyy, True))
    for e in H.etabs:
        if not e.ouvert: continue
        g = _grossiste_de(H, e.ile)
        for k, nom in enumerate(M.NOMS_MOL):
            if nom == "sang": continue
            b = H.id_mol[nom]
            cible = max(STOCK_PUI_J * _demande_pui(e, k, nom), STOCK_MIN.get(nom, 0.0))
            voulu = cible - e.stock[b]
            if voulu > 1e-6: demandes.setdefault((g.id, b), []).append((e, voulu, e, False))
    # en penurie, le grossiste rationne au prorata des commandes ( sinon le premier client servi prenait tout : mesure
    # du 24/09, l anesthesique allait a Athira et manquait a Kavala et Pyrgos ) ; le reliquat nourrit son import
    for g in H.grossistes: g.manque[:] = 0.0
    for (gid, b), lst in demandes.items():
        g = H.grossistes[gid]
        total = math.fsum(v for _, v, _, _ in lst)
        part = min(1.0, g.stock[b] / total) if total > 0 else 0.0
        servi = 0.0
        for dst, voulu, payeur, officine in lst:
            servi += _livrer(p, H, g, dst, b, voulu * part, payeur, officine)
        g.manque[M.IMOL[p.socle.catalogue[b].nom]] = max(0.0, total - servi)
    if p.jour % 7 == 0:
        for e in H.etabs:
            if e.type == "hopital" and e.pop > 0:
                _entrer(p, H, e, "sang", M.DONS_SANG_AN * e.pop * 7.0 / 365.0, "produit", "don_du_sang", 2)
    _consommables(p, H)


def _consommables(p, H):
    """Desinfectants et reactifs ( chimie de l industrie ) : une semaine d avance, livree par le site le mieux pourvu
    et payee par l etablissement. La commande permanente du domaine s AJOUTE a celle des autres domaines."""
    if not p.a("industrie"): return
    cid = p.socle.catalogue.id("chimie")
    total = 0.0
    for e in H.etabs:
        if not e.ouvert: continue
        besoin = CHIMIE_T_PAR_LIT_J * (len(e.lits_occ) + len(e.rea_occ))
        total += besoin
        if e.stock[cid] < 3.0 * besoin: IN.livrer(p, "chimie", 7.0 * besoin - e.stock[cid], e.stock, e)
    ind = p.domaine("industrie")
    actuel = ind.commandes.get("chimie", 0.0)
    nouvelle = max(0.0, actuel - H.ma_commande_chimie + total)
    if abs(nouvelle - actuel) > 1e-12: IN.commander(p, "chimie", nouvelle)
    H.ma_commande_chimie = total


def _importer(p):
    """11 h : le grossiste compare son stock et ses commandes en route a la demande de son ile ( officines et pharmacies
    hospitalieres ) et au reliquat de sa tournee ; sous le point de commande, il commande a l etranger. La marchandise arrive DELAI_IMPORT_J jours plus
    tard, payee a l arrivee ( sauf rupture chez le fabricant )."""
    H = _dom(p); med = p.domaine("medecine"); w = p.w
    for g in H.grossistes:
        dem = np.zeros(len(M.NOMS_MOL))
        for ph in med.pharmacies:
            if w.carte.lieux[ph.lieu].ile != g.ile: continue
            for k, nom in enumerate(M.NOMS_MOL):
                if nom not in HOSPITALIERES: dem[k] += _demande_officine(ph, k, nom)
        for e in H.etabs:
            if e.ile == g.ile and e.ouvert:
                for k, nom in enumerate(M.NOMS_MOL): dem[k] += _demande_pui(e, k, nom)
        for k, nom in enumerate(M.NOMS_MOL):
            if nom == "sang" or (dem[k] <= 0 and g.manque[k] <= 0): continue
            b = H.id_mol[nom]
            pos = g.stock[b] + g.en_route[k] - g.manque[k]
            if pos < POINT_COMMANDE_J * dem[k]:
                q = CIBLE_GROSSISTE_J * dem[k] - pos
                if q > 0.5:
                    g.en_route[k] += q; H.commande[k] += q
                    p.poser(DELAI_IMPORT_J * PAS_J, "hopitaux_import", g.id, (b, float(q)))


def _import_arrive(p, gid, donnees):
    H = _dom(p); g = H.grossistes[gid]; L = p.socle.livre
    b, q = donnees
    nom = p.socle.catalogue[b].nom; k = M.IMOL[nom]
    g.en_route[k] -= q
    if H.ruptures.get(nom, -1) >= p.jour:
        H.annule[k] += q; H.compter(("import_annule", nom)); return
    if p.a("exterieur"):
        from . import d07_exterieur as EX
        recu, _ = EX.importer_au_port(p, g, g.stock, b, q, "import_sante")
    else:
        prix = p.socle.catalogue[b].prix_monde
        paye = L.payer_l_exterieur(g, q * prix, "import_grossiste")
        recu = paye / prix
        if recu > 0: L.importer(g.stock, b, recu, "import_grossiste")
    if recu > 0:
        _ajouter_lot(g.lots, b, recu, p.jour + M.MOL[nom].conservation_j)
        H.bilan[nom][1] += recu; H.recu[k] += recu
        p.compter("import_grossiste")
    H.annule[k] += q - recu


def _perimer(p):
    """5 h : ce qui est perime sort par le grand livre, dans les stocks du domaine."""
    H = _dom(p); L = p.socle.livre
    for x in list(H.grossistes) + list(H.etabs):
        for b, lots in list(x.lots.items()):
            q = sum(l[0] for l in lots if l[1] <= p.jour)
            if q > 0:
                lots[:] = [l for l in lots if l[1] > p.jour]
                pris = L.perimer(x.stock, b, q, "peremption_hopital")
                H.bilan[p.socle.catalogue[b].nom][5] += pris
                p.compter("peremption_hopital", pris)
            if not lots: x.lots.pop(b, None)


def _soir(p, comptes):
    """La cloture : les notes du triage, les journees de reanimation, les jours sans molecule, la consommation mesuree,
    la tresorerie des hopitaux publics ( l Etat couvre leurs arrieres ), les consommables."""
    H = _dom(p); W = p.w.habitants; L = p.socle.livre; med = p.domaine("medecine")
    dec = H.dec
    for cle in list(H.evts):
        att = dec.attentes.get(cle)
        if att is None or not att.choix:
            H.evts.pop(cle, None); dec.attentes.pop(cle, None); continue
        qui = H.evts[cle]
        dec.noter(cle, math.fsum(issue_du_jour(p, W[x]) for x in qui) / len(qui), p.jour)
        if not att.choix: H.evts.pop(cle, None); dec.attentes.pop(cle, None)
    for ps in H.actifs.values():
        if ps.etat == REA: ps.rea_jours += 1
    # jours sans molecule : officines et pharmacies hospitalieres
    detenteurs = [(ph, "officine") for ph in med.pharmacies] + [(e, "hopital") for e in H.etabs if e.ouvert]
    for x, genre in detenteurs:
        for k, nom in enumerate(M.NOMS_MOL):
            if genre == "officine" and nom in HOSPITALIERES: continue
            if genre == "hopital" and nom not in STOCK_MIN and nom != "sang": continue
            cle = (genre, x.lieu if genre == "officine" else x.id, nom)
            vide = x.stock[H.id_mol[nom]] <= 1e-9
            if vide:
                if cle not in H.sans_molecule:
                    p.noter("rupture_molecule", bien=nom, detenteur=genre, lieu=x.lieu)
                    H.sans_molecule[cle] = 0
                H.sans_molecule[cle] += 1
                H.compter(("jours_sans", genre, nom)); p.compter("jour_sans_molecule")
            elif cle in H.sans_molecule:
                H.compter(("episodes_rupture", genre, nom)); del H.sans_molecule[cle]
    cid = p.socle.catalogue.id("chimie") if p.a("industrie") else None
    for e in H.etabs:
        e.conso += (e.sortie_jour - e.conso) / 30.0; e.conso7 += (e.sortie_jour - e.conso7) / 7.0
        e.sortie_jour[:] = 0.0
        e.depense_moy += (e.achats_jour - e.depense_moy) / 30.0; e.achats_jour = 0.0
        if cid is not None:
            besoin = CHIMIE_T_PAR_LIT_J * sum(1 for x in e.lits_occ + e.rea_occ if x >= 0)
            if besoin > 0 and L.consommer(e.stock, cid, besoin, "consommables_hopital") < besoin - 1e-12:
                p.compter("consommables_manquants")
        dettes = p.socle.creances.de(e)
        du = math.fsum(c.montant for c in dettes)
        if not e.prive and e.type in ("hopital", "militaire"):
            fonds = FONDS_ROULEMENT_J * e.depense_moy
            _dotation_esy(p, H, e, du + fonds - e.caisse)
        for c in dettes:
            if e.caisse <= 1e-9: break
            p.socle.creances.regler(c, L)
        if not e.prive and e.type in ("hopital", "militaire"):
            surplus = e.caisse - 2.0 * FONDS_ROULEMENT_J * e.depense_moy - math.fsum(c.montant for c in p.socle.creances.de(e))
            if surplus > 1e-6: L.transferer(e, p.w.gouv, surplus, "reversement_esy")


# ================================================================== la capacite des etablissements
def _redimensionner(p, H, e, lits, rea, blocs, now):
    """La capacite change ( seisme, agrandissement ) : les lits en trop sont evacues vers la file du meme hopital ou
    transferes."""
    if e.batiment is None: return
    evacues = []
    while len(e.rea_occ) > rea:
        hid = e.rea_occ.pop()
        if hid >= 0: evacues.append(hid)
    while len(e.lits_occ) > lits:
        hid = e.lits_occ.pop()
        if hid >= 0: evacues.append(hid)
    e.rea_occ += [-1] * (rea - len(e.rea_occ)); e.lits_occ += [-1] * (lits - len(e.lits_occ))
    while len(e.bloc_occ) > blocs:
        hid = e.bloc_occ.pop(); e.bloc_fin.pop()
        if hid >= 0: evacues.append(hid)
    e.bloc_occ += [-1] * (blocs - len(e.bloc_occ)); e.bloc_fin += [-1] * (blocs - len(e.bloc_fin))
    for hid in evacues:
        ps = H.actifs.get(hid)
        if ps is None: continue
        ps.lit = -1
        autre = _etab_avec_lits(p, H, e) if not lits else None
        if autre is not None: _transferer(p, H, ps, e, autre, now)
        else: ps.etat = ATT_LIT; ps.t_file = now; e.file_lit.append(hid)
    if evacues: p.noter("evacuation_hopital", etablissement=e.nom, patients=len(evacues))


def capacites_declarees(p, e, pop_ile_max=False):
    """( lits generaux, lits de reanimation, blocs ) que le dimensionnement donne a un hopital : les lits du batiment
    ( IM.lits ), dont la reanimation ( 6 pour 100 000 ; au moins 1 dans l hopital le plus peuple de l ile ), 1 bloc pour
    40 lits ( au moins 1 )."""
    total = IM.lits(p, e.batiment) if e.batiment is not None and e.batiment >= 0 else 0
    if total <= 0: return 0, 0, 0
    rea = int(round(REA_100K * e.pop / 1e5))
    if pop_ile_max: rea = max(1, rea)
    rea = min(rea, max(0, total - 1))
    return total - rea, rea, max(1, int(round(total / LITS_PAR_BLOC)))


def _principal_de_l_ile(H, e):
    same = [x for x in H.etabs if x.ile == e.ile and x.type == "hopital"]
    return max(same, key=lambda x: (x.pop, -x.id)) is e if same else False


def _capacites(p):
    """0 h 10 : le personnel et la capacite ( un batiment endommage perd ses lits )."""
    H = _dom(p); med = p.domaine("medecine")
    _affecter_personnel(p, H)
    for e in H.etabs:
        if e.type == "hopital": e.pop = med.pharmacies[e.region].pop
    for e in H.etabs:
        if e.type != "hopital" or e.batiment is None: continue
        lits, rea, blocs = capacites_declarees(p, e, _principal_de_l_ile(H, e))
        if (lits, rea, blocs) != (len(e.lits_occ), len(e.rea_occ), len(e.bloc_occ)):
            _redimensionner(p, H, e, lits, rea, blocs, p.w.pas)
        e.ouvert = lits + rea > 0


# ================================================================== l installation
def installer(p):
    w = p.w; L = p.socle.livre; med = p.domaine("medecine")
    H = Hopitaux()
    p.domaines["hopitaux"] = H
    H.etabs, H.grossistes, H.eopyy = [], [], Eopyy()
    H.actifs, H.prochain, H.appels, H.occupe, H.rappel, H.continu, H.repos = {}, 0, {}, {}, {}, {}, {}
    H.amb_libre, H.amb_etab = {}, {}
    H.evts, H.prochain_evt, H.suivi = {}, 0, []
    H.historique = collections.deque(maxlen=200000); H.attentes = collections.deque(maxlen=200000)
    H.factures = collections.deque(maxlen=200000)
    n = len(M.NOMS_MOL)
    H.bilan = {nom: [0.0] * 6 for nom in M.NOMS_MOL}   # dotation, importe, dons, officines, dispense, perime
    H.commande, H.recu, H.annule = np.zeros(n), np.zeros(n), np.zeros(n)
    H.ruptures, H.sans_molecule, H.compteurs = {}, {}, {}
    H.id_mol = dict(med.id_mol)
    H.ma_commande_chimie = 0.0
    H.rng = p.hasard("hopitaux_arrivees")
    H.etab_de_lieu = {}
    H.sang_attendu, H.sang_promis, H.dernier_appel_dons, H.cache_sang, H.demande_sang_pas = {}, {}, {}, {}, {}
    for motif, nature in (("financement_eopyy", "transfert_courant"), ("dotation_esy", "transfert_courant"),
                          ("ken_eopyy", "achat"), ("remboursement_officines", "achat"),
                          ("participation_hospitaliere", "achat"), ("achat_medicaments", "achat"),
                          ("carburant_ambulance", "achat"), ("kit_hopital", "achat"), ("import_grossiste", "achat"),
                          ("groupe_electrogene", "achat"), ("reversement_esy", "transfert_courant")):
        L.declarer_motif(motif, nature, "hopitaux")
    J = p.socle.journal
    for t_, champs in (("rupture_molecule", ("bien", "detenteur", "lieu")), ("afflux_massif", ("lieu", "victimes")),
                       ("plan_blanc", ("etablissement", "file")),
                       ("transfert_patient", ("habitant", "origine", "destination")),
                       ("evacuation_hopital", ("etablissement", "patients"))):
        J.declarer(t_, "hopitaux", "individuel", champs)
    for t_ in ("passage_urgences", "admission_hopital", "admission_rea", "chirurgie", "sortie_hopital", "deces_hopital",
               "renvoi_domicile", "mission_ambulance", "rappel_astreinte", "livraison_grossiste", "import_grossiste",
               "peremption_hopital", "jour_sans_molecule", "heure_groupe", "traitement_manque",
               "consommables_manquants", "soutien_manque"):
        J.declarer(t_, "hopitaux", "compte")
    p.echeance("hopitaux_arrivee", _arrivee)
    p.echeance("hopitaux_import", _import_arrive)
    p.echeance("hopitaux_sang", _sang_arrive)
    p.echeance("hopitaux_appel_dons", _appel_aux_dons)
    parc = p.socle.parc
    H.modeles = {}
    for nom, fam, prix, masse, vie, arma, src in MODELES:
        H.modeles[nom] = parc.declarer_modele(nom, fam, prix / EUR, masse, vie, arma=arma, arma_preuve=None, source=src)
    # les familles d argent et de biens du domaine
    reg = p.socle.registre
    reg.inscrire("etablissements_sante", "administrations", _etablissements_du_pays, "caisse", "stock", "EtablissementSante")
    reg.inscrire("grossistes", "entreprises", _grossistes_du_pays, "caisse", "stock", "Grossiste")
    reg.inscrire("eopyy", "administrations", _eopyy_du_pays, "caisse", None, "Eopyy")
    # les hopitaux publics : le batiment de chaque capitale
    for cap in sorted(w.marches):
        bs = [b for b in IM.batiments(p, "hopital", lieu=cap)]
        b = bs[0] if bs else None
        e = EtablissementSante(len(H.etabs), f"hopital_{cap}", "hopital", False, cap, w.carte.lieux[cap].ile,
                          med.region_de_lieu[cap], b, n)
        e.pop = med.pharmacies[e.region].pop
        H.etabs.append(e); H.etab_de_lieu[cap] = e
    for ile in w.carte.iles:
        port = w.carte.port(ile)
        caps = [c.id for c in w.carte.capitales if c.ile == ile]
        lieu = port.id if port is not None else (caps[0] if caps else None)
        if lieu is None: continue
        H.grossistes.append(Grossiste(len(H.grossistes), ile, lieu, n))
    _affecter_personnel(p, H)
    for e in H.etabs:
        lits, rea, blocs = capacites_declarees(p, e, _principal_de_l_ile(H, e))
        e.lits_occ, e.rea_occ = [-1] * lits, [-1] * rea
        e.bloc_occ, e.bloc_fin = [-1] * blocs, [-1] * blocs
        e.ouvert = lits + rea > 0
        for k, nom in enumerate(M.NOMS_MOL): e.conso[k] = CONSO_HOPITAL_1000.get(nom, 0.0) * e.pop / 1000.0
        # objets : ambulances et equipements, nes au recensement
        for _ in range(max(1, int(round(AMBULANCES_100K * e.pop / 1e5)))):
            o = parc.creer(H.modeles["ambulance"], e, e.lieu, "initial", w.pas)
            e.ambulances.append(o.id); H.amb_libre[o.id] = -1; H.amb_etab[o.id] = e.id
        for nom, nb in (("respirateur", rea), ("table_operation", blocs), ("analyseur_labo", 1),
                        ("groupe_electrogene", 1), ("scanner", int(round(SCANNERS_PAR_HAB * e.pop)))):
            if nb > 0: parc.creer_cohorte(H.modeles[nom], e, e.lieu, nb, "initial")
    # les premiers stocks : dotation importee sans paiement, comme les stocks de depart du moteur et de la medecine
    for e in H.etabs:
        for k, nom in enumerate(M.NOMS_MOL):
            if nom == "sang":
                q = max(STOCK_MIN["sang"], 14.0 * M.DONS_SANG_AN * e.pop / 365.0)
                _entrer(p, H, e, nom, q, "produit", "dotation_initiale_sang", 0)
                continue
            q = max(STOCK_PUI_J * _demande_pui(e, k, nom), STOCK_MIN.get(nom, 0.0))
            _entrer(p, H, e, nom, q, "importe", "dotation_initiale_sante", 0)
    for g in H.grossistes:
        for k, nom in enumerate(M.NOMS_MOL):
            if nom == "sang": continue
            d = sum(_demande_officine(ph, k, nom) for ph in med.pharmacies
                    if w.carte.lieux[ph.lieu].ile == g.ile and nom not in HOSPITALIERES)
            d += sum(_demande_pui(e, k, nom) for e in H.etabs if e.ile == g.ile)
            _entrer(p, H, g, nom, DOTATION_GROSSISTE_J * d, "importe", "dotation_initiale_sante", 0)
    # le fonds de roulement des hopitaux publics : trente jours d achats attendus
    for e in H.etabs:
        e.depense_moy = math.fsum(float(e.conso[k]) * p.socle.catalogue[H.id_mol[nom]].prix_monde
                                  for k, nom in enumerate(M.NOMS_MOL))
        _dotation_esy(p, H, e, FONDS_ROULEMENT_J * e.depense_moy)
    if p.a("banques"):
        from . import d02_banques as BQ
        for g in H.grossistes: BQ.ouvrir_compte(p, g)
    if p.a("energie"):
        from . import d11_energie as EN
        for e in H.etabs:
            e.contrat = ("hopitaux", e.id)
            EN.abonner(p, e.contrat, e.lieu, e, KW_PAR_LIT * (len(e.lits_occ) + len(e.rea_occ)), prioritaire=True)
    H.dec = p.decideur(POINT_TRIAGE)
    M.reprendre_chaine(p)
    w.soigner = RemplaceSoigner(p)
    for k in range(PAS_J): p.routine(k * MIN_PAS / 60.0, 60, "hopitaux", _pas)
    p.routine(0 + 10 / 60, 60, "hopitaux", _capacites)
    p.routine(5.0, 60, "hopitaux", _perimer)
    p.routine(10.0, 60, "hopitaux", _tournee)
    p.routine(11.0, 60, "hopitaux", _importer)
    p.cloture("hopitaux", _soir)
    return H


# ================================================================== l API des autres domaines
def ouvrir_etablissement(p, type_, lieu, lits, rea=0, blocs=0, prive=True, nom=None):
    """Un etablissement nouveau ( scenario, grande echelle, domaines 18, 26 ) : une clinique privee conventionnee, un
    centre de sante, un hopital militaire de campagne. Locaux loues ( sans batiment du domaine 13, a calibrer ) ; sa
    pharmacie est livree des le lendemain ; une clinique ouvre un compte en banque. Rend l EtablissementSante."""
    H = _dom(p); w = p.w; med = p.domaine("medecine")
    if lieu not in w.carte.lieux: raise KeyError(f"lieu inconnu {lieu!r}")
    if not (isinstance(lits, int) and lits >= 0 and rea >= 0 and blocs >= 0): raise ValueError("capacite invalide")
    cap = w.carte.lieux[lieu].marche.id
    e = EtablissementSante(len(H.etabs), nom or f"{type_}_{lieu}_{len(H.etabs)}", type_, prive, lieu,
                      w.carte.lieux[lieu].ile, med.region_de_lieu[cap], None, len(M.NOMS_MOL))
    e.lits_occ, e.rea_occ = [-1] * lits, [-1] * rea
    e.bloc_occ, e.bloc_fin = [-1] * blocs, [-1] * blocs
    e.labo = type_ != "centre_sante"
    H.etabs.append(e)
    if prive and p.a("banques"):
        from . import d02_banques as BQ
        BQ.ouvrir_compte(p, e)
    return e


def affecter_personnel(p, e, medecins=(), infirmiers=(), specialites=None):
    """Domaines 25 a 27 ( et scenarios ) : le personnel d un etablissement qui n est pas un hopital de capitale ( ses
    soignants ne viennent pas du moteur ) : identifiants d habitants, et leur specialite ( le plan de dotation sinon )."""
    e.medecins = sorted(int(x) for x in medecins); e.infirmiers = sorted(int(x) for x in infirmiers)
    e.specialite = {}
    for k, hid in enumerate(e.medecins):
        s = (specialites or {}).get(hid) or PLAN_DOTATION[k % len(PLAN_DOTATION)]
        if s not in SPECIALITES: raise ValueError(f"specialite inconnue {s!r}")
        e.specialite[hid] = s


def hopital_militaire(p, lieu, lits, rea=0, blocs=1):
    """Domaines 26 et 27 : un hopital militaire ( ou de campagne ), public, finance par l Etat comme l ESY."""
    return ouvrir_etablissement(p, "militaire", lieu, lits, rea, blocs, prive=False)


def afflux(p, n, lieu, types=("ecrasement", "chute"), cause="accident", dist=ISS_CATASTROPHE, rng=None):
    """Un accident de masse ou un seisme ( scenario, domaine 18 ) : n habitants de la zone de la capitale `lieu`, pris
    au hasard, sont blesses ( M.blesser ) avec l ISS d une catastrophe. Rend leurs identifiants."""
    w = p.w
    rng = rng if rng is not None else p.hasard("hopitaux_afflux")
    cap = w.carte.lieux[lieu].marche.id
    cand = [h.id for h in w.habitants if h.vivant and h.domicile.marche.id == cap and h.poste not in ("hopital", "voyage")
            and h.id not in _dom(p).actifs]
    if not cand: return []
    ids = rng.choice(cand, min(n, len(cand)), replace=False).tolist()
    for hid in ids:
        u = rng.random(); c = 0.0; iss = dist[-1][0][1]
        for (a, b), pr in dist:
            c += pr
            if u < c: iss = int(rng.integers(a, b + 1)); break
        M.blesser(p, w.habitants[hid], types[int(rng.integers(0, len(types)))], iss, cause=cause)
    p.noter("afflux_massif", lieu=lieu, victimes=len(ids))
    return ids


def rupture_fournisseur(p, molecule, jours):
    """Scenario : le fabricant etranger ne livre plus `molecule` pendant `jours` jours ( penurie europeenne,
    exportations paralleles ) ; les commandes en route sont annulees a leur arrivee."""
    if molecule not in M.MOL: raise KeyError(molecule)
    _dom(p).ruptures[molecule] = p.jour + int(jours)


def fermer_bloc(p, etab_id, jours):
    """Scenario ( portes, domaine 27 : un hopital bombarde ) : les blocs de l etablissement ne prennent plus personne."""
    _dom(p).etabs[etab_id].bloc_ferme_jusqu = p.jour + int(jours)


def etablissements(p):
    return list(_dom(p).etabs)


def capacite(p, lieu=None):
    """Domaines 18, 26 : par etablissement, lits et lits libres, reanimation, blocs, files, ambulances libres."""
    H = _dom(p); now = p.w.pas
    return {e.nom: {"lieu": e.lieu, "lits": len(e.lits_occ), "lits_libres": e.lits_occ.count(-1),
                    "rea": len(e.rea_occ), "rea_libres": e.rea_occ.count(-1), "blocs": len(e.bloc_occ),
                    "blocs_libres": e.bloc_occ.count(-1), "file_urgences": len(e.file_med), "file_bloc": len(e.file_bloc),
                    "file_lit": len(e.file_lit) + len(e.file_rea),
                    "ambulances_libres": sum(1 for o in e.ambulances if H.amb_libre.get(o, -1) <= now),
                    "appels": len(H.appels.get(e.ile, ())), "prive": e.prive, "type": e.type}
            for e in H.etabs if lieu is None or e.lieu == lieu}


def etat_patient(p, h):
    """Domaines 18, 26, 27 : ou en est h ( None s il n est pas dans le systeme de soins )."""
    ps = _dom(p).actifs.get(h.id)
    if ps is None: return None
    return {"etat": ETATS[ps.etat], "etablissement": _dom(p).etabs[ps.etab].nom, "esi": ps.esi, "vu": ps.vu,
            "opere": ps.opere, "soutien": ps.soutien, "attente_min": (p.w.pas - ps.t_file) * MIN_PAS}


def couts_des_soins(p, depuis_j=0):
    """Domaine 20 : les passages factures depuis `depuis_j` : ( jour, habitant, etablissement, prive, forfait EOPYY,
    participation du malade, journees de reanimation, opere, issue )."""
    return [f for f in _dom(p).factures if f[0] >= depuis_j]


def attentes(p, depuis_j=0):
    """Les attentes mesurees aux urgences ( minutes, de l arrivee a l examen ) : { ESI : ( nombre, moyenne, max ) }."""
    acc = {}
    for j, _, n_esi, m in _dom(p).attentes:
        if j < depuis_j: continue
        a = acc.setdefault(n_esi, [0, 0.0, 0.0]); a[0] += 1; a[1] += m; a[2] = max(a[2], m)
    return {k: (v[0], v[1] / v[0], v[2]) for k, v in sorted(acc.items())}


def delais(p):
    """Les parcours ( clos et en cours ) : ( esi, iss, pas de l appel, de l arrivee, de l examen, du soutien, issue ;
    -1 : pas encore ), pour mesurer les attentes et le delai jusqu au soin."""
    H = _dom(p)
    out = [(x[4], x[5], x[6], x[7], x[8], x[9], x[3]) for x in H.historique]
    out += [(ps.esi, ps.iss, ps.t_appel, ps.t_arrivee, ps.t_vu, ps.t_soutien, "en_cours") for ps in H.actifs.values()]
    return out


def ambulances(p):
    """Le pont : ( numero, etablissement, libre a partir du pas, classname, preuve )."""
    H = _dom(p); m = H.modeles["ambulance"]
    return [(o, H.etabs[H.amb_etab[o]].nom, H.amb_libre.get(o, -1), m.arma, m.arma_preuve) for o in sorted(H.amb_libre)]


# ================================================================== controles ( pour les portes )
def ecarts_lits(p):
    """Les manquements a la conservation des lits : une capacite qui n est pas la declaree, un lit occupe sans le
    passage qui le designe ( ou par un malade qui n est pas hospitalise ), un malade hospitalise sans son lit, un
    malade dans deux lits."""
    H = _dom(p)
    out, vus = [], {}
    for e in H.etabs:
        for genre, arr, etat in (("lit", e.lits_occ, LIT), ("rea", e.rea_occ, REA)):
            occ = sum(1 for x in arr if x >= 0); lib = sum(1 for x in arr if x < 0)
            if occ + lib != len(arr): out.append(("comptage", e.nom, genre))
            for i, hid in enumerate(arr):
                if hid < 0: continue
                if hid in vus: out.append(("deux_lits", hid))
                vus[hid] = (e.id, genre, i)
                ps = H.actifs.get(hid)
                if ps is None or ps.etat != etat or ps.lit != i or ps.etab != e.id:
                    out.append(("lit_sans_patient", e.nom, genre, i, hid))
    for hid, ps in H.actifs.items():
        if ps.etat in (LIT, REA):
            e = H.etabs[ps.etab]
            arr = e.rea_occ if ps.etat == REA else e.lits_occ
            if not 0 <= ps.lit < len(arr) or arr[ps.lit] != hid: out.append(("hospitalise_sans_lit", hid))
    return out


def ecarts_capacite(p):
    """Les hopitaux dont la capacite n est pas celle du dimensionnement declare ( batiment, reanimation, blocs )."""
    H = _dom(p); out = []
    for e in H.etabs:
        if e.type != "hopital" or e.batiment is None: continue
        attendu = capacites_declarees(p, e, _principal_de_l_ile(H, e))
        if attendu != (len(e.lits_occ), len(e.rea_occ), len(e.bloc_occ)):
            out.append((e.nom, attendu, (len(e.lits_occ), len(e.rea_occ), len(e.bloc_occ))))
    return out


def ecarts_lots_hopitaux(p):
    H = _dom(p); out = []
    for x in list(H.grossistes) + list(H.etabs):
        for nom in M.NOMS_MOL:
            b = H.id_mol[nom]
            s, l = x.stock[b], sum(y[0] for y in x.lots.get(b, ()))
            if abs(s - l) > 1e-6 * max(1.0, s): out.append((type(x).__name__, x.id, nom, s, l))
    return out


def bilan_medicaments(p):
    """Par molecule, dans le perimetre du domaine ( grossistes et pharmacies hospitalieres ) : ( attendu, stock,
    ecart, commande - recu - annule - en route ). attendu = dotation + importe + dons - officines - dispense - perime."""
    H = _dom(p); out = {}
    for k, nom in enumerate(M.NOMS_MOL):
        b = H.id_mol[nom]
        d, im, dons, off, disp, per = H.bilan[nom]
        stock = math.fsum(x.stock[b] for x in list(H.grossistes) + list(H.etabs))
        attendu = d + im + dons - off - disp - per
        route = math.fsum(float(g.en_route[k]) for g in H.grossistes)
        out[nom] = (attendu, stock, stock - attendu, H.commande[k] - H.recu[k] - H.annule[k] - route)
    return out
