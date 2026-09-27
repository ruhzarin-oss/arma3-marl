"""DOMAINE 22 - COMMUNICATION, INFORMATION, MEDIAS, RUMEUR : LE TRANSPORT DE L INFORMATION.

FICHE
1. Classes. Memoire ( la table des FAITS et des CROYANCES, en colonnes numpy : une ligne par fait, une colonne par
   cellule ), Reseau ( l etat des telecommunications par lieu : courant, batteries des relais, pannes ), Operateur
   ( un operateur de telecommunications : parts de marche, salaries, caisse ; famille `operateurs_telecom` ), Media
   ( un journal, une radio, une chaine, un site : genre, zone, audience, ligne editoriale, sensationnalisme,
   credibilite, capacite de verification, salaries, caisse ; famille `medias_prives` ) et MediaPublic ( la radio-
   television publique, financee par l Etat ; famille `audiovisuel_public`, secteur administrations ),
   ContextePublication, Medias ( l etat du domaine ).
   UN FAIT est un evenement du monde, vrai, date, localise : pris au journal du socle ( NOUVELLES : deces, incendies,
   seismes, pannes, greves, faillites, lois... ), aux publications de l Etat ( chomage, prix, dette, faim ), ou pose par
   un autre domaine ( `constater` ). Une FAUSSE NOUVELLE est une ligne de la meme table, `vrai` faux, sans valeur vraie.
   Les faits frequents sont AGREGES par ( sujet, lieu, jour ) : trois deces du meme village le meme jour font un fait de
   valeur 3. UNE CROYANCE est ce qu une CELLULE tient pour vrai d un fait : part de ses habitants qui le savent, valeur
   crue ( en log : la deformation est multiplicative ), nombre moyen de relais, date de la premiere personne informee,
   source ( temoin, bouche a oreille, telephone, Etat, renseignement, media ), confiance, lieu cru ( qui peut etre
   faux ). Une cellule est un LIEU de la carte ( ses residents ) ou un GROUPE inscrit par un autre domaine ( un camp,
   un etat-major, un gouvernement : `inscrire_groupe` ).
   POURQUOI PAS UNE CROYANCE PAR HABITANT : 50 millions d habitants et quelques milliers de faits vivants feraient
   10^11 couples. Le bouche a oreille se fait entre gens qui se croisent, et les gens qui se croisent vivent, travaillent
   et font leurs courses dans des lieux : la cellule-lieu tient la dynamique, la part tient la proportion. Un individu
   n est fabrique que quand on le demande ( `sait` ) : il sait si un tirage fixe de SON MENAGE ( melange entier de la
   graine, du menage et du fait, sans memoire ) est sous la part de son lieu. Le menage sait ensemble ; ceux qui
   savent a 10 % savent encore a 20 % ( monotone ). Zero octet par habitant.
   MEMOIRE A 50 MILLIONS : croyances = faits vivants x cellules x 30 octets ( part, valeur, relais : 4 ; date : 8 ;
   source : 2 ; confiance, lieu cru : 4 ). Les cellules sont les lieux de la carte ( 68 a Altis, ~ 400 pour l archipel )
   et non les habitants ; les faits vivants sont bornes par l oubli et par CAP_MAX = 4 096 ( le moins saillant et le
   moins connu est oublie de force au-dela ) : 4 096 x 420 x 30 = 52 Mo, quelle que soit la population. Par menage :
   6 octets ( tel_equipement, tel_mobiles, tel_operateur, tel_retard : 1 chacun ; presse_abos : 2 ) - 20 millions de
   menages ( 2,5 personnes ), 120 Mo. Par habitant : rien. Tables eparses : les salaries des operateurs et des medias ( ~ 1 pour 1 000 ).
2. Invariants et ce que le domaine detient. Une croyance n est JAMAIS datee avant son fait ( `anomalies` ) ; une part
   est dans [0 ; 1] ; une cellule ne sait rien d un fait tant qu une personne au moins ne l a pas appris ( graine
   discrete : pas de connaissance fantome de 10^-12 ). ARGENT : les caisses des operateurs et des medias, par le grand
   livre seulement : abonnements des menages ( telephone fixe, mobiles, internet, television payante, journaux et sites
   payants ), TVA reversee a l Etat ( 24 % telecoms et publicite, 6 % presse ), publicite payee par les marches, dotation
   de l Etat a l audiovisuel public, aide a la presse, salaires des salaries inscrits, sous-traitance payee aux marches,
   equipements et papier importes, dividendes des operateurs a leurs actionnaires etrangers, fonds propres initiaux
   venus de l exterieur. Aucun bien du catalogue. Un abonnement impaye n est pas une creance du socle ( une par menage
   ferait des millions d objets ) : il se compte en mois de retard ( tel_retard ) ; a deux mois, l operateur suspend
   le fixe, internet, la television payante et la presse ( les mobiles, prepayes, restent ).
3. Decision `publication` ( chaque media, chaque jour a 9 h, conference de redaction : au plus K_MAX nouvelles, les plus
   saillantes qu il a vues et pas encore traitees ) : publier tout de suite ( a son creneau : site 10 h, radio l heure
   suivante, television 20 h, journal le lendemain 7 h ), verifier ( un jour de journaliste : le lendemain, le vrai est
   publie a sa vraie valeur, sans relais ; le faux est tue ; une verification sur dix ne conclut pas ), ignorer.
   Traits ( ce que la redaction voit, jamais si c est vrai ) : saillance annoncee ( sur la valeur crue ), confiance de
   la source, source officielle, relais de la version, concurrents qui l ont deja publiee, part du pays qui en parle
   ( veille des reseaux ), age de la version, sa propre credibilite, son sensationnalisme, sa charge de verification.
   Note ( horizon 3 jours : un dementi tombe en un a trois jours ) : chaque jour, pour CE media et CETTE nouvelle, les
   personnes qui l ont apprise PAR LUI sur son audience du jour, moins K_FAUX si elle est dementie ce jour apres qu il
   l a publiee, moins C_VERIF le jour ou il la verifie. Regle : officiel -> publier ; peu saillant ou deja su de tous ->
   ignorer ; source sure et peu relayee -> publier ; saillant et incertain -> verifier ; sinon ignorer. Temoin : tout
   publier. MESURE DU 26/09 ( test_decision, scenario de 12 nouvelles par jour dont 35 % fausses, 12 medias, 10 jours ) :
   au hasard, part du choix 0,177, p 0,005 ; note moyenne regle 0,049, temoin 0,017, hasard 0,016. Verifier rapporte
   peu ( 0,002 au hasard ) : a 2 500 habitants, un jour de retard suffit pour que les concurrents et la rumeur aient
   tout dit ; ce qu elle achete, c est d eviter K_FAUX.
4. Evenements. Individuels : panne_telecom, telecom_retabli, fausse_nouvelle, dementi. Comptes : fait_constate,
   fait_oublie, publication, verification, nouvelle_ignoree, nouvelle_tuee, facture_telecom, abonnement_suspendu,
   publicite, salaire_medias.
5. Liens. Etat ( 6, dependance dure ) : `publications` ( la statistique de la veille, le budget, la dette -> faits
   officiels ), `assurer` avant chaque paiement de l Etat, la TVA ( motif tva du moteur, w.tva_percue ). Banques ( 2 ) :
   `ouvrir_compte` des operateurs et des medias. Journal du socle : TOUS les types individuels de NOUVELLES, lus a chaque
   heure ( et ceux de la justice, 21, s il est installe ). Energie ( 11, optionnel ) : `coupure_en_cours` par lieu,
   chaque heure ( les relais tiennent AUTONOMIE_H heures sur batterie ; la television meurt avec le courant, la radio a
   piles non ). Agenda ( 5, optionnel ) : les presences de la veille ( culte, loisirs, courses ) font varier les contacts
   du lieu. Medecine ( 16 ) : la rumeur des malades reste celle de l agenda ( `contacts_par_lieu`, `a.connus` ), non
   dupliquee ; une epidemie declaree devient un fait. Paie et recoit : menages -> operateurs, medias ( abonnements ) ;
   marches -> medias ( publicite ) ; Etat -> audiovisuel public, journaux ( dotation, aide ) ; operateurs, medias ->
   Etat ( tva ), -> menages de leurs salaries ( salaires ), -> marches ( sous-traitance ), -> exterieur ( equipements,
   papier, dividendes ). Ne remplace aucune methode du moteur. API en fin de fichier.
   LIMITE DU MOTEUR : pas de metier journaliste ni technicien telecom ( config.ROLES ) : les salaries sont des adultes
   inscrits au registre de leur employeur, qui GARDENT leur metier du moteur ( comme les pompiers du domaine 18 ) ; leur
   salaire ici n est pas retenu a la source par le domaine 6.
6. Portes : tests_d22_medias.py ( 12 / 13 le 26/09 ). ECHEC EXPLIQUE : test_deformation_relais ( le monde, 12
   incendies de saillance 0,9, 4 jours ) exige 20 croyances sous 1,5 relais et une correlation des rangs de 0,3 ; il
   n y en a que 10 ( les lieux d origine ) et 0,25 : dans ce modele la profondeur moyenne des relais croit comme
   beta x t ( une nouvelle saillante passe 3 relais dans presque tous les lieux en moins d un jour ; mesure a 1 jour :
   12 croyances, 0,18 ), et le bruit de derive de chaque cohorte horaire dilue les rangs. L erreur, elle, croit :
   0,06 sous 1,5 relais, 0,26 a 3 et plus ; 0,04 et 0,04 sans deformation. La porte test_deformation_chaine ( ecrite
   apres cet echec, seuils poses avant sa mesure ) controle la profondeur : erreur 0,05 a 1,09 le long de 8 lieux,
   6 hausses sur 6, plate sans deformation.
7. Arma : aucun corps propre. Un relais de telephonie est un batiment du domaine 13 ( Land_TTowerSmall_1_F,
   Land_TTowerBig_1_F, arma_preuve = None ) ; un journaliste a le corps de son habitant.
8. Cout. Chaque heure : l etat du reseau par lieu ( L appels a l energie ), la lecture des nouvelles lignes du journal,
   les diffusions dues, et de 7 h a 22 h un pas de rumeur : deux produits ( faits x lieux ) par ( lieux x lieux ) et des
   operations elementaires sur ( faits x lieux ) - independant de la population. Chaque jour : une passe vectorisee sur
   les habitants ( population et equipement par lieu, bincount ), la facture d un menage sur 30, les salaires d un
   salarie sur 30, la conference de redaction ( au plus K_MAX decisions par media ). Chaque semaine : les matrices de
   contact ( bincount sur les habitants ). Lineaire en habitants ; la rumeur en ( faits x lieux^2 ). Mesure du 26/09
   ( test_cout, coeur Rust, 10 000 habitants, 43 faits vivants ) : 50 ms par jour, 16 % d une journee du moteur seul
   ( 0,31 s ) ; installation 0,03 s a 10 000 habitants, 0,21 s a 100 000 ( x6,3 ). A 50 millions : la facture ( un
   menage sur 30, ~ 700 000 paiements par jour, ~ 7 s ), les salaires ( ~ 2 000 par jour ), la rumeur ( 4 096 faits x
   420^2 lieux, 16 pas : ~ 2 s ) - de l ordre du pour cent d une journee du moteur a cette echelle.
   A 2 500 habitants, un salarie au moins par media coute plus que ce que son audience rapporte : les caisses des
   petits medias baissent ( ~ 20 % en un mois ) ; les effectifs par habitant sont a calibrer a l echelle."""
import math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D
from . import pays as P, d02_banques as BQ, d06_etat as ET

EUROS = P.EUROS_PAR_DRACHME
JOURS_AN = 365.0
PAS_JOUR = C.PAS_PAR_JOUR
MOIS_J = 30
DOMAINE = "medias"

# ================================================================== le temps
# Le jour du moteur ( w.jour ) change a minuit ; le monde part du jour 0 a 6 h. Le temps absolu d un fait ou d une
# croyance, en jours depuis le depart : t = jour + ( heure - 6 ) / 24 ( = w.pas / 144 ).
def _t(p): return p.w.pas / PAS_JOUR


def _t_de(jour, heure): return float(jour) + (float(heure) - 6.0) / 24.0


# ================================================================== la rumeur ( sources et hypotheses )
# Contacts : POLYMOD ( Mossong et al. 2008, PLoS Medicine 5:e74 ) : 13,4 contacts par personne et par jour en moyenne ;
# a la maison ~ 23 %, au travail et a l ecole ~ 35 %, ailleurs ( commerces, loisirs, transports ) le reste. Part des
# contacts ou l on parle d une nouvelle de saillance 1 : a calibrer ( 0,3 ). La vitesse DECLAREE du bouche a oreille :
# BETA_BAO x saillance transmissions par personne informee et par jour ( ~ 4 pour une nouvelle de saillance 1 : moitie
# d un village de 1 000 habitants en ~ 1,7 jour sans telephone ni media ).
CONTACTS_J = 13.4
P_PARLER = 0.3
BETA_BAO = CONTACTS_J * P_PARLER
BETA_TEL = 2.0                    # appels et messages vers d autres lieux, par personne informee et equipee ( a calibrer )
HEURE_EVEIL, HEURE_COUCHER = 7, 22   # un pas de rumeur par heure de 7 h a 22 h : 16 pas
DT = 1.0 / (HEURE_COUCHER - HEURE_EVEIL + 1)
W_DOM_ACTIF, W_TRAV = 0.23, 0.35  # poids des contacts : maison, travail ( POLYMOD ) ; le reste au marche de son lieu
W_DOM_INACTIF = 0.40              # sans travail : plus de contacts a la maison et au voisinage ( a calibrer )
D_TEL_KM = 20.0                   # les liens telephoniques decroissent avec la distance ( a calibrer )
LIEN_LOINTAIN = 0.02              # plancher : famille et amis au loin, sur une autre ile ( a calibrer )
# Deformation ( Allport et Postman 1947, The Psychology of Rumor : nivellement et accentuation ; les chaines de
# transmission de Bartlett 1932 ) : a chaque relais la valeur derive en log de MU ( exageration ) plus SIGMA x N(0,1).
MU_RELAIS = 0.06                  # + 6 % par relais en moyenne ( a calibrer )
SIGMA_RELAIS = 0.15               # ( a calibrer )
SIGMA_TEMOIN = 0.05               # un temoin se trompe peu sur ce qu il a vu ( a calibrer )
Q_LIEU = 0.05                     # par relais, le lieu est confondu avec un lieu voisin ( a calibrer )
CONF_TEMOIN, CONF_RELAIS = 0.95, 0.9   # confiance d un temoin ; ce qu en garde chaque relais ( a calibrer )
# Oubli ( Ebbinghaus 1885 pour la forme ; a calibrer ) : demi-vie de la part qui s en souvient, plus longue pour une
# nouvelle saillante ; un dementi la divise par 4 et reduit par 3 l envie de la repeter.
DEMI_VIE_BASE_J, DEMI_VIE_PENTE_J = 2.0, 40.0
FACTEUR_OUBLI_DEMENTI, PARTAGE_DEMENTI = 4.0, 0.3
AGE_MAX_J = 120
CAP_INITIALE, CAP_MAX = 256, 4096
VALEUR_MIN = 1e-3
# Sources d une croyance ( la premiere qui a informe la cellule )
TEMOIN, BOUCHE, TELEPHONE, OFFICIEL, RENSEIGNEMENT, ORIGINE = range(6)
MEDIA0 = 10                       # source = MEDIA0 + indice du media
NOMS_SOURCES = ("temoin", "bouche_a_oreille", "telephone", "etat", "renseignement", "origine_rumeur")

# ================================================================== les fausses nouvelles
# Ellinika Hoaxes ( verificateur grec ) : de l ordre de 1 a 3 dementis publies par jour pour 10,4 millions ( a
# verifier ) : 0,2 fausse nouvelle nee par jour et par million d habitants ( a calibrer ). Une catastrophe fait naitre
# ses rumeurs : apres un fait vrai de saillance s >= 0,3, une rumeur jumelle ( exageree x ~3, ou d un lieu voisin ) nait
# avec la probabilite P_JUMELLE x s ( a calibrer ). Un dementi tombe chaque jour avec la probabilite P_DEMENTI_BASE,
# plus P_DEMENTI_VIRAL x ( 20 x part du pays qui y croit, bornee a 1 ), plus P_DEMENTI_PUBLIE si un media l a publiee
# ( les verificateurs visent ce qui circule : a calibrer ).
FAUX_PAR_MILLION_J = 0.2
P_JUMELLE = 0.25
EXAGERATION_JUMELLE = math.log(3.0)
PERSONNES_ORIGINE = 3
CONF_ORIGINE = 0.5
P_DEMENTI_BASE, P_DEMENTI_VIRAL, P_DEMENTI_PUBLIE = 0.25, 0.5, 0.2
FAUSSES = (("penurie", 0.30, 20.0), ("epidemie", 0.15, 30.0), ("faillite_banque", 0.10, 1.0),
           ("incendie", 0.15, 1.0), ("contamination_eau", 0.15, 1.0), ("meurtre", 0.15, 1.0))   # ( sujet, poids, valeur mediane )

# ================================================================== les sujets
# sujet : ( valence, touche le gouvernement, saillance de base, pente, mode, temoins, agregation )
#   saillance = base + pente x log10( 1 + valeur ) ( mode log ) ou base + pente x valeur ( mode lin ), bornee a [0,01 ; 1]
#   temoins : personnes qui voient le fait ( reparties selon qui frequente le lieu ), "lieu" ( 80 % de ses residents ),
#   "ile" ( 80 % de chaque lieu de l ile ), 0 ( officiel : seules les redactions l apprennent, par communique )
#   Toutes ces valeurs : a calibrer ( ordres de grandeur de l attention mediatique grecque ).
SUJETS = {
    "deces": (-0.2, False, 0.03, 0.03, "log", 15, "somme"),
    "mort_accident": (-0.5, False, 0.12, 0.10, "log", 20, "somme"),
    "meurtre": (-0.8, False, 0.35, 0.10, "log", 30, "somme"),
    "mort_combat": (-0.9, True, 0.50, 0.15, "log", 30, "somme"),
    "mort_de_faim": (-0.9, True, 0.45, 0.15, "log", 20, "somme"),
    "naissance": (0.3, False, 0.02, 0.0, "log", 10, "somme"),
    "budget": (0.0, True, 0.35, 0.0, "log", 0, "max"),
    "impots": (-0.4, True, 0.50, 0.0, "log", 0, "max"),
    "dette": (-0.3, True, 0.15, 0.0, "log", 0, "max"),
    "taux": (-0.1, True, 0.30, 0.0, "log", 0, "max"),
    "devaluation": (-0.8, True, 0.90, 0.0, "log", 0, "max"),
    "prix_mondiaux": (-0.4, False, 0.45, 0.0, "log", 0, "max"),
    "contrebande": (-0.2, False, 0.12, 0.02, "log", 5, "somme"),
    "emigration": (-0.3, True, 0.02, 0.02, "log", 10, "somme"),
    "seisme": (-0.8, False, -0.65, 0.25, "lin", "ile", "max"),
    "degats_seisme": (-0.8, False, 0.40, 0.10, "log", "lieu", "somme"),
    "inondation": (-0.6, False, 0.40, 0.05, "log", "lieu", "max"),
    "cyclone": (-0.8, False, 0.70, 0.0, "log", "ile", "max"),
    "risque_incendie": (-0.3, False, 0.25, 0.0, "log", 0, "max"),
    "secheresse": (-0.4, False, 0.30, 0.0, "log", "ile", "max"),
    "restriction_eau": (-0.4, True, 0.35, 0.0, "log", "lieu", "max"),
    "panne_electricite": (-0.3, True, 0.25, 0.0, "log", 0, "somme"),
    "delestage": (-0.6, True, 0.55, 0.0, "log", "ile", "max"),
    "coupure_courant": (-0.4, True, 0.35, 0.0, "log", "lieu", "max"),
    "accident_travail": (-0.5, False, 0.10, 0.10, "log", 20, "somme"),
    "expulsion": (-0.3, True, 0.05, 0.03, "log", 15, "somme"),
    "accident_route": (-0.5, False, 0.10, 0.12, "log", 20, "somme"),
    "vol": (-0.3, False, 0.03, 0.03, "log", 5, "somme"),
    "epidemie": (-0.8, True, 0.60, 0.10, "log", 0, "somme"),
    "hopital_sature": (-0.7, True, 0.45, 0.05, "log", 30, "max"),
    "penurie_medicaments": (-0.6, True, 0.30, 0.0, "log", 10, "somme"),
    "incendie": (-0.5, False, 0.12, 0.10, "log", 40, "somme"),
    "feu_de_foret": (-0.8, False, 0.20, 0.15, "log", "lieu", "somme"),
    "route_fermee": (-0.2, True, 0.15, 0.0, "log", 30, "somme"),
    "coupure_eau": (-0.4, True, 0.35, 0.0, "log", "lieu", "max"),
    "greve": (-0.3, True, 0.30, 0.05, "log", 30, "somme"),
    "faillite": (-0.4, False, 0.12, 0.08, "log", 20, "somme"),
    "licenciements": (-0.3, True, 0.03, 0.05, "log", 10, "somme"),
    "panne_telecom": (-0.3, False, 0.25, 0.0, "log", "lieu", "max"),
    "chomage": (-0.5, True, 0.25, 0.0, "log", 0, "max"),
    "prix": (-0.4, True, 0.20, 0.0, "log", 0, "max"),
    "faim": (-0.9, True, 0.30, 0.10, "log", 0, "max"),
    "penurie": (-0.7, True, 0.40, 0.05, "log", 20, "somme"),
    "faillite_banque": (-0.9, True, 0.70, 0.0, "log", 0, "max"),
    "contamination_eau": (-0.8, True, 0.50, 0.0, "log", 20, "max"),
}
SUJET_JUSTICE = (-0.4, True, 0.20, 0.05, "log", 10, "somme")   # un type individuel du domaine 21, lu par son nom
# type du journal : ( sujet, champ de la valeur ou None pour compter les evenements )
NOUVELLES = {
    "naissance": ("naissance", None), "vote_budget": ("budget", "depenses"), "loi_fiscale": ("impots", None),
    "emission_dette": ("dette", "montant"), "decision_taux": ("taux", "taux"), "avance_etat": ("dette", "montant"),
    "devaluation": ("devaluation", "part"), "choc_prix_mondial": ("prix_mondiaux", "facteur"),
    "saisie_douane": ("contrebande", "quantite"), "emigration": ("emigration", "personnes"),
    "seisme": ("seisme", "magnitude"), "seisme_dommages": ("degats_seisme", "touches"),
    "inondation": ("inondation", "pluie_mm"), "cyclone": ("cyclone", "vent_ms"),
    "alerte_incendie": ("risque_incendie", "indice"), "secheresse": ("secheresse", "indice"),
    "restriction_eau": ("restriction_eau", "niveau"), "panne_centrale": ("panne_electricite", "heures"),
    "delestage_electrique": ("delestage", "kwh"), "coupure_ligne": ("coupure_courant", "jours"),
    "accident_du_travail": ("accident_travail", None), "accident_mortel": ("mort_accident", None),
    "expulsion": ("expulsion", None), "accident_de_la_route": ("accident_route", "victimes"),
    "vol_de_vehicule": ("vol", None), "epidemie_declaree": ("epidemie", "cas"),
    "afflux_massif": ("hopital_sature", "victimes"), "plan_blanc": ("hopital_sature", None),
    "evacuation_hopital": ("hopital_sature", "patients"), "rupture_molecule": ("penurie_medicaments", None),
    "incendie": ("incendie", None), "feu_de_vegetation": ("feu_de_foret", "hectares"),
    "crue_secours": ("inondation", "evacues"), "route_fermee": ("route_fermee", None),
    "coupure_eau": ("coupure_eau", "part"), "greve_collecte": ("greve", "jours"), "greve_debut": ("greve", "grevistes"),
    "faillite": ("faillite", "salaries"), "licenciement": ("licenciements", None), "panne_telecom": ("panne_telecom", None),
}
SUJET_DU_DECES = {"accident": "mort_accident", "violence": "meurtre", "combat": "mort_combat", "faim": "mort_de_faim"}
CHAMPS_LIEU = ("lieu", "de", "site", "port", "etablissement", "origine")
# La statistique publiee par l Etat ( domaine 6 ) : ( sujet, chemin dans publications( p ), cadence en jours, echelle )
# ELSTAT publie le chomage et l indice des prix chaque mois ; la dette et le deficit chaque trimestre ( a calibrer ).
STATS = (("chomage", ("statistique", "enquete", "chomage"), 30, 100.0),
         ("prix", ("statistique", "prix", "indice"), 30, 1.0),
         ("dette", ("statistique", "finances", "dette_pib"), 90, 100.0),
         ("faim", ("statistique", "enquete", "faim_menages"), 30, 1.0))

# ================================================================== les telecommunications ( Grece, a verifier )
# EETT ( autorite grecque des telecoms ), rapports annuels 2022-2023 : trois operateurs ; parts des abonnements mobiles
# ~ 47 / 31 / 22 %, du fixe ~ 47 / 30 / 23 % ( a verifier ) ; effectifs des groupes en Grece ~ 7 500, 2 500, 2 000
# pour 10,4 millions d habitants ( a verifier ). Salaire brut moyen du secteur ~ 2 000 euros par mois, 14 mois ( a
# calibrer ). Actionnaires majoritairement etrangers ( part des dividendes qui sort : a calibrer ).
OPERATEURS = (("operateur_historique", 0.47, 7.2e-4, 0.5),
              ("operateur_2", 0.31, 2.4e-4, 1.0),
              ("operateur_3", 0.22, 1.9e-4, 1.0))   # ( nom, part des abonnements, salaries par habitant, part etrangere )
SALAIRE_TELECOM_EUR = 2000.0 * 14 / 12
# Equipement des menages : television ~ 97 % ( ELSTAT, enquete budget des familles, a verifier ) ; internet a la maison
# 87 % en 2023 ( Eurostat isoc_ci_in_h, a verifier ) ; ligne fixe ( ~ 4,9 millions de lignes EETT pour ~ 4,1 millions
# de menages et les entreprises : a calibrer ) ; television payante ~ 1,3 million d abonnes ( ~ 30 %, a verifier ) ;
# mobile par personne selon l age ( Eurostat, enquete TIC ; a calibrer ). Classes : aisee, moyenne, populaire.
P_TV = 0.97
P_FIXE = np.array([0.80, 0.72, 0.62])
P_INTERNET = np.array([0.97, 0.91, 0.82])
FACTEUR_INTERNET_AGES = 0.55      # menage dont tous les membres ont 65 ans et plus ( Eurostat : usage ~ 45 % a 65-74 ans )
P_TV_PAYANTE = np.array([0.45, 0.32, 0.22])
AGES_MOBILE = (12.0, 16.0, 65.0, 75.0)
P_MOBILE = (0.0, 0.80, 0.97, 0.88, 0.65)   # < 12, 12-15, 16-64, 65-74, 75 et plus
# Prix TTC par mois ( offres grecques 2023, ordres de grandeur ; a calibrer ) ; la TVA grecque : 24 % ( telecoms,
# publicite ), 6 % ( journaux ). Une facture de menage typique ( 2 mobiles, fixe, internet ) ~ 70 euros : ~ 4,5 % des
# 1 685 euros de depense mensuelle ( ELSTAT 2023 : communications ~ 4 a 5 %, a verifier ).
PRIX_MOBILE_EUR, PRIX_FIXE_EUR, PRIX_INTERNET_EUR, PRIX_TV_PAYANTE_EUR = 17.0, 12.0, 22.0, 25.0
TVA_TELECOM, TVA_PRESSE, TVA_PUB = 0.24, 0.06, 0.24
FIXE, INTERNET, TV, TV_PAYANTE = 1, 2, 4, 8
RATION_DR = 4.0                   # la ration a 4 drachmes ( pays.py ) : la reserve de nourriture qu un menage garde
RESERVE_J = 14                    # un menage ne paie ses abonnements qu au-dela de 14 jours de nourriture ( a calibrer )
MOIS_AVANT_SUSPENSION = 2         # delai grec usuel avant suspension pour impaye ( a calibrer )
# Relais : autonomie sur batterie des stations de base ( 2 a 8 h selon les sites ; a calibrer ) ; pannes propres du
# reseau ( coupure de fibre, equipement ) par lieu et par jour, duree mediane 4 h ( a calibrer ).
AUTONOMIE_H = 4.0
RECHARGE_H = 8.0
P_PANNE_TELECOM_J = 0.003
PANNE_MEDIANE_H = 4.0
# Couts des operateurs, sur leur chiffre d affaires hors taxes ( a calibrer : marge d EBITDA des operateurs grecs
# ~ 35 a 40 % ) : sous-traitance et services locaux 40 %, equipements importes 15 %.
PART_SOUS_TRAITANCE_TEL, PART_IMPORT_TEL = 0.40, 0.15
RESERVE_MOIS = 2.0                # fonds de roulement garde avant tout dividende

# ================================================================== les medias ( Grece, a calibrer )
# Reuters Institute, Digital News Report 2023, Grece : portee hebdomadaire des grandes chaines d information ~ 35 a
# 45 %, des grands sites ~ 25 a 30 %, de la presse ecrite ~ 10 % ; confiance dans l information 19 %, la plus basse
# d Europe ; portee QUOTIDIENNE prise a ~ la moitie de l hebdomadaire ( a calibrer ). Effectifs : ERT ~ 2 500 ; une
# chaine privee ~ 600 ; un quotidien national ~ 200 ; un site ~ 60 ; une radio ~ 50 ( a verifier ). Salaire brut d un
# journaliste ~ 1 400 euros, 14 mois ( a calibrer ). Capacite de verification : nouvelles par jour ( a calibrer ).
# ( nom, genre, audience quotidienne, credibilite, sensationnalisme, capacite, salaries par habitant, prix abonnement
#   euros par mois, ligne, part des abonnes parmi les menages )
MEDIAS = (("tv_publique", "tv", 0.12, 0.55, 0.2, 6, 2.4e-4, 0.0, "gouvernement", 0.0),
          ("tv_1", "tv", 0.30, 0.45, 0.6, 5, 6.0e-5, 0.0, "gouvernement", 0.0),
          ("tv_2", "tv", 0.26, 0.45, 0.5, 5, 6.0e-5, 0.0, "opposition", 0.0),
          ("tv_3", "tv", 0.20, 0.50, 0.4, 5, 6.0e-5, 0.0, "neutre", 0.0),
          ("radio_1", "radio", 0.12, 0.55, 0.3, 2, 5.0e-6, 0.0, "neutre", 0.0),
          ("radio_2", "radio", 0.08, 0.50, 0.5, 2, 5.0e-6, 0.0, "opposition", 0.0),
          ("journal_1", "journal", 0.03, 0.55, 0.3, 4, 2.0e-5, 18.0, "gouvernement", 0.020),
          ("journal_2", "journal", 0.02, 0.55, 0.3, 4, 2.0e-5, 18.0, "opposition", 0.015),
          ("site_1", "site", 0.25, 0.40, 0.7, 2, 6.0e-6, 0.0, "neutre", 0.0),
          ("site_2", "site", 0.18, 0.45, 0.5, 2, 6.0e-6, 5.0, "gouvernement", 0.010),
          ("site_3", "site", 0.12, 0.30, 0.9, 1, 3.0e-6, 0.0, "opposition", 0.0))
PRESSE_REGIONALE = ("journal", 0.08, 0.60, 0.3, 2, 1.0e-5, 12.0, "neutre", 0.03)   # une par ile, sans le nom
SALAIRE_JOURNALISTE_EUR = 1400.0 * 14 / 12
PORTEE_MAX = 0.9
ELAST_CRED = 1.0                  # l audience suit la credibilite ( elasticite a calibrer )
ATTENTION_BASE, ATTENTION_PENTE = 0.3, 0.5   # part de l audience qui retient une nouvelle, selon sa saillance
BIAIS_LIGNE = {"gouvernement": -0.10, "opposition": 0.10, "neutre": 0.0}    # cadrage d un sujet gouvernemental, en log
SENSATION_LOG = 0.15              # une version non verifiee grossit de 0,15 x sensationnalisme ( en log )
K_CRED = 0.08                     # credibilite perdue par fausse nouvelle dementie ( a calibrer )
ETA_CRED = 0.002                  # credibilite regagnee par nouvelle vraie publiee ( a calibrer )
# Publicite : le marche publicitaire grec ~ 750 millions d euros pour ~ 220 milliards de PIB ( ~ 0,35 %, a verifier ),
# paye par les commerces ( marches du moteur ), reparti selon l audience et le prix du contact par genre ( a calibrer ).
PUB_PIB = 0.0035
PLAFOND_PUB = 0.01                # un marche ne paie jamais plus de 1 % de sa caisse par jour
PRIX_CONTACT = {"tv": 1.0, "radio": 0.5, "journal": 1.5, "site": 0.6}
DOTATION_PUBLIC_PIB = 0.0008      # ERT : ~ 180 millions d euros par an ( redevance ), ~ 0,08 % du PIB ( a verifier )
AIDE_PRESSE_PIB = 0.0001          # publicite d Etat et aides a la presse ( a calibrer )
PART_SOUS_TRAITANCE_MEDIA, PART_PAPIER = 0.20, 0.10
# La conference de redaction
K_MAX = 8                         # nouvelles examinees par media et par jour
SEUIL_VEILLE = 0.02               # un correspondant entend ce que 2 % d un lieu savent
P_VERIF_OK = 0.9                  # une verification conclut
C_VERIF = 0.05                    # cout d une verification, en audience du jour ( un journaliste une journee )
K_FAUX = 1.0                      # une fausse nouvelle dementie coute une audience du jour ( a calibrer )
HORIZON_PUBLICATION = 3
PUBLIER, VERIFIER, IGNORER = range(3)
NOUVEAU, IGNORE, EN_COURS, PUBLIE, TUE = range(5)       # etat d un fait pour un media ( Memoire.traite )
HEURE_REDACTION = 9.0
CRENEAU = {"tv": 20.0, "radio": None, "site": None, "journal": 7.0}   # None : l heure suivante


# ================================================================== les detenteurs
class Operateur:
    """Un operateur : un menage a UN operateur pour son fixe, son internet, ses mobiles et sa television payante
    ( offres groupees, la regle en Grece ; a calibrer ), tire selon les parts des abonnements mobiles."""
    __slots__ = ("indice", "nom", "part_mobile", "ratio", "part_etrangere", "caisse", "employes",
                 "recettes_ht_mois", "tva_due", "recu_total", "tva_total", "abonnes")

    def __init__(self, indice, nom, part_mobile, ratio, part_etrangere):
        if not (0 <= part_mobile <= 1 and ratio >= 0 and 0 <= part_etrangere <= 1):
            raise ValueError(f"operateur {nom} : parametres hors bornes")
        self.indice, self.nom, self.part_mobile = indice, nom, part_mobile
        self.ratio, self.part_etrangere = ratio, part_etrangere
        self.caisse = 0.0
        self.employes = np.zeros(0, np.int64)
        self.recettes_ht_mois = self.tva_due = self.recu_total = self.tva_total = 0.0
        self.abonnes = 0


class Media:
    __slots__ = ("indice", "nom", "genre", "zone", "base", "cred", "cred0", "sensation", "capacite", "ratio", "prix_abo",
                 "ligne", "part_abo", "bit_abo", "caisse", "employes", "portee", "cov", "aud_personnes", "verifs_jour",
                 "recettes_ht_mois", "tva_due", "publies", "faux_publies", "dementis", "recettes_pub", "recettes_abo",
                 "recettes_etat")

    def __init__(self, indice, nom, genre, zone, base, cred, sensation, capacite, ratio, prix_abo, ligne, part_abo):
        if genre not in CRENEAU: raise ValueError(f"media {nom} : genre inconnu {genre!r}")
        if ligne not in BIAIS_LIGNE: raise ValueError(f"media {nom} : ligne inconnue {ligne!r}")
        if not (0 < base <= PORTEE_MAX and 0 < cred <= 1 and 0 <= sensation <= 1 and capacite >= 1 and ratio >= 0
                and prix_abo >= 0 and 0 <= part_abo <= 1):
            raise ValueError(f"media {nom} : parametres hors bornes")
        self.indice, self.nom, self.genre, self.zone, self.base = indice, nom, genre, zone, base
        self.cred = self.cred0 = cred
        self.sensation, self.capacite, self.ratio, self.prix_abo, self.ligne = sensation, int(capacite), ratio, prix_abo, ligne
        self.part_abo, self.bit_abo = part_abo, -1
        self.caisse = 0.0
        self.employes = np.zeros(0, np.int64)
        self.portee = None; self.cov = None; self.aud_personnes = 0.0; self.verifs_jour = 0
        self.recettes_ht_mois = self.tva_due = 0.0
        self.publies = self.faux_publies = self.dementis = 0
        self.recettes_pub = self.recettes_abo = self.recettes_etat = 0.0


class MediaPublic(Media):
    """La radio-television publique : meme vie qu un media, autre secteur ( administrations ) et autre famille."""
    __slots__ = ()


def _membres_operateurs(w): return w.pays.domaines[DOMAINE].operateurs


def _membres_medias(w): return [m for m in w.pays.domaines[DOMAINE].medias if type(m) is Media]


def _membres_public(w): return [m for m in w.pays.domaines[DOMAINE].medias if type(m) is MediaPublic]


# ================================================================== la memoire des faits et des croyances
FAIT_CHAMPS = (("actif", np.bool_, False), ("fid", np.int64, -1), ("sujet", np.int16, -1), ("t", np.float64, np.nan),
               ("lieu", np.int32, -1), ("lv_vrai", np.float64, np.nan), ("saillance", np.float32, 0.0),
               ("vrai", np.bool_, True), ("officiel", np.bool_, False), ("evenements", np.int32, 0),
               ("dementi_t", np.float64, np.nan), ("publie_t", np.float64, np.nan), ("parent", np.int64, -1))
CROYANCE_CHAMPS = (("part", np.float32, 0.0), ("lv", np.float32, 0.0), ("relais", np.float32, 0.0),
                   ("appris", np.float64, np.nan), ("source", np.int16, -1), ("conf", np.float32, 0.0),
                   ("lieu_cru", np.int32, -1))


class Memoire:
    """Les faits ( une ligne chacun ) et leurs croyances ( ligne x cellule ). Les lignes liberees sont reprises ; un
    fait est designe hors d ici par son identifiant `fid`, jamais par sa ligne."""
    __slots__ = ("cap", "nc", "nm", "f", "c", "traite", "libres", "par_fid", "cles", "cle_de", "prochain_fid",
                 "oublies_force")

    def __init__(self, nc, nm, cap=CAP_INITIALE):
        self.cap, self.nc, self.nm = 0, nc, nm
        self.f, self.c = {}, {}
        self.traite = np.zeros((0, nm), np.int8)
        self.libres, self.par_fid, self.cles, self.cle_de = [], {}, {}, []
        self.prochain_fid = 0; self.oublies_force = 0
        self.agrandir(cap)

    def agrandir(self, cap):
        old = self.cap
        if cap <= old: return
        for nom, dt_, v in FAIT_CHAMPS:
            a = np.full(cap, v, dt_)
            if old: a[:old] = self.f[nom]
            self.f[nom] = a
        for nom, dt_, v in CROYANCE_CHAMPS:
            a = np.full((cap, self.nc), v, dt_)
            if old: a[:old] = self.c[nom]
            self.c[nom] = a
        t = np.zeros((cap, self.nm), np.int8); t[:old] = self.traite; self.traite = t
        self.cle_de.extend([None] * (cap - old))
        self.libres.extend(range(cap - 1, old - 1, -1))     # pop() rend la plus petite ligne libre
        self.cap = cap

    def cellules(self, nc):
        for nom, dt_, v in CROYANCE_CHAMPS:
            a = np.full((self.cap, nc), v, dt_); a[:, :self.nc] = self.c[nom]; self.c[nom] = a
        self.nc = nc

    def actifs(self): return np.nonzero(self.f["actif"])[0]

    def liberer(self, r):
        fid = int(self.f["fid"][r])
        self.par_fid.pop(fid, None)
        cle = self.cle_de[r]
        if cle is not None and self.cles.get(cle) == r: del self.cles[cle]
        self.cle_de[r] = None
        for nom, _, v in FAIT_CHAMPS: self.f[nom][r] = v
        for nom, _, v in CROYANCE_CHAMPS: self.c[nom][r] = v
        self.traite[r] = 0
        self.libres.append(r)


class Reseau:
    """Les telecommunications par lieu : le courant ( energie ), la batterie des relais en heures, la fin d une panne
    propre du reseau ( temps absolu ), l etat de marche, et depuis quand un lieu est coupe."""
    __slots__ = ("elec", "batterie_h", "panne_fin", "cause", "ok", "coupe_t", "heures_coupees")

    def __init__(self, L):
        self.elec = np.ones(L, bool); self.batterie_h = np.full(L, AUTONOMIE_H)
        self.panne_fin = np.full(L, -1.0); self.cause = [""] * L
        self.ok = np.ones(L, bool); self.coupe_t = np.full(L, np.nan); self.heures_coupees = np.zeros(L)


class ContextePublication:
    """Ce que voit une redaction d une nouvelle : la version qui lui parvient, la concurrence, la veille des reseaux,
    son etat. Jamais si la nouvelle est vraie."""
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer_publication(ctx): return ctx.traits


def _regle_publication(x, ctx):
    sal, conf, off, rel, conc, noto, age, cred, sens, charge = x
    if off >= 1.0: return PUBLIER if sal >= 0.05 else IGNORER
    if sal < 0.08 or noto >= 0.8: return IGNORER
    if conf >= 0.8 and rel <= 0.4: return PUBLIER
    if sal >= 0.15 and charge < 1.0: return VERIFIER
    return IGNORER


def _temoin_publication(x, ctx, rng): return PUBLIER


POINT_PUBLICATION = D.PointDeDecision(
    "publication", DOMAINE,
    traits=(("saillance", "l importance que la version annonce, sur l echelle de son sujet ( la depeche )"),
            ("confiance", "la confiance de ceux qui la rapportent ( le correspondant )"),
            ("officiel", "1 si la source est un communique officiel"),
            ("relais", "les relais de la version qui lui parvient, sur 5 ( le correspondant )"),
            ("concurrence", "la part des autres medias qui l ont deja publiee ( ce qu ils diffusent )"),
            ("notoriete", "la part du pays qui en parle deja ( veille des reseaux sociaux )"),
            ("age", "jours depuis que la version circule, sur 3"),
            ("credibilite", "sa propre credibilite ( enquetes de confiance )"),
            ("sensation", "son sensationnalisme ( sa ligne )"),
            ("charge", "verifications deja lancees aujourd hui sur sa capacite")),
    actions=("publier", "verifier", "ignorer"),
    observer=_observer_publication, regle=_regle_publication, temoin=_temoin_publication,
    note=("pour CE media et CETTE nouvelle, chaque jour : les personnes qui l ont apprise par lui sur son audience du "
          "jour, moins K_FAUX le jour ou elle est dementie s il l a publiee, moins C_VERIF le jour ou il la verifie"),
    horizon_j=HORIZON_PUBLICATION)


# ================================================================== l etat du domaine
class Medias:
    __slots__ = ("L", "nc", "lieu_ids", "n_du_lieu", "ile_de", "iles", "capitale_ile", "marche_de", "pos", "voisins",
                 "groupes", "taille", "poids_groupe", "suit_medias", "pop", "eq_tv", "eq_net", "eq_tel", "act", "M", "T",
                 "B", "mem", "sujets", "code_sujet", "table_sujets", "nouvelles", "reseau", "operateurs", "medias",
                 "decideur", "journal_vu", "file_pub", "file_verif", "suivi", "gains", "penalites", "couts",
                 "stats_vues", "poids_marche", "redactions_actives", "mu", "sigma", "q_lieu", "employes",
                 "suspendus", "compte")

    def __init__(self):
        self.groupes, self.taille, self.poids_groupe, self.suit_medias = [], [], [], []
        self.operateurs, self.medias = [], []
        self.journal_vu = None
        self.file_pub = []        # [ t de diffusion, media, fid, version ( lv, lieu cru, relais, verifie ) ]
        self.file_verif = []      # [ t du resultat, media, fid ]
        self.suivi = {}           # cle du decideur -> [ media, fid, notes deja donnees ]
        self.gains, self.penalites, self.couts = {}, {}, {}   # ( media, fid ) -> valeur du jour
        self.stats_vues = {}      # sujet statistique -> jour de la derniere publication devenue un fait
        self.redactions_actives = True   # les portes de propagation pure les eteignent ( mesure, pas le monde )
        self.mu, self.sigma, self.q_lieu = MU_RELAIS, SIGMA_RELAIS, Q_LIEU   # le falsificateur de la deformation les met a 0
        self.employes = set()
        self.suspendus = 0
        self.compte = {}


def _dom(p): return p.domaines[DOMAINE]


# ================================================================== la carte, la population, l equipement
def _carte(p, d):
    w = p.w
    lieux = sorted(w.carte.lieux.values(), key=lambda l: l.n)
    if any(l.n != k for k, l in enumerate(lieux)): raise RuntimeError("medias : lieux hors de l ordre du moteur")
    d.L = len(lieux)
    d.lieu_ids = [l.id for l in lieux]
    d.n_du_lieu = {l.id: l.n for l in lieux}
    d.ile_de = [l.ile for l in lieux]
    d.iles = sorted(set(d.ile_de), key=lambda i: min(k for k, x in enumerate(d.ile_de) if x == i))
    caps = {}
    for c in w.carte.capitales: caps.setdefault(c.ile, c.n)
    d.capitale_ile = {i: caps.get(i, min(k for k, x in enumerate(d.ile_de) if x == i)) for i in d.iles}
    d.marche_de = np.array([l.marche.n if getattr(l, "marche", None) is not None else l.n for l in lieux], np.int64)
    d.pos = np.array([l.pos[:2] for l in lieux], np.float64)
    dist = np.hypot(d.pos[:, None, 0] - d.pos[None, :, 0], d.pos[:, None, 1] - d.pos[None, :, 1])
    meme = np.array([[a == b for b in d.ile_de] for a in d.ile_de])
    dist = np.where(meme, dist, np.inf)
    np.fill_diagonal(dist, np.inf)
    d.voisins = np.argsort(dist, axis=1, kind="stable")[:, :3].astype(np.int32)   # les trois lieux les plus proches
    return dist


def _residents(p):
    """Les residents vivants presents ( numeros ), leur lieu de domicile et leur menage inscrit."""
    tb = p.w.table; n = tb.n
    mg = PO.menages_inscrits(tb, n)
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & (tb.domicile[:n] >= 0) & (mg >= 0))[0]
    return ids, tb.domicile[ids].astype(np.int64), mg[ids].astype(np.int64)


def _ages(p, ids): return (p.jour - p.col("habitant", "naissance_j")[ids].astype(np.float64)) / JOURS_AN


def _equiper(p, d, menages, rng):
    """Tire l equipement de menages ( numeros ) qui n en ont pas encore : a l installation, puis chaque menage nouveau."""
    if not len(menages): return
    tb = p.w.table; n = tb.n; nm = tb.menages.n
    cm = p.colonnes["menage"]; cm.assurer(nm)
    ids, dom, mg = _residents(p)
    age = _ages(p, ids)
    cible = np.zeros(nm, bool); cible[menages] = True
    sel = cible[mg]
    ids, mg, age = ids[sel], mg[sel], age[sel]
    k = np.searchsorted(np.array(AGES_MOBILE), age, side="right")
    mob = rng.random(len(ids)) < np.array(P_MOBILE)[k]
    nmob = np.bincount(mg[mob], minlength=nm)
    cl = np.full(nm, 2, np.int64)
    if len(ids): np.minimum.at(cl, mg, np.clip(tb.classe[ids].astype(np.int64), 0, 2))
    jeunes = np.bincount(mg[age < 65.0], minlength=nm) > 0
    m = np.asarray(menages, np.int64)
    u = rng.random((len(m), 6))
    c = cl[m]
    fixe = u[:, 0] < P_FIXE[c]
    net = u[:, 1] < P_INTERNET[c] * np.where(jeunes[m], 1.0, FACTEUR_INTERNET_AGES)   # fixe ou 4G a la maison
    tv = u[:, 2] < P_TV
    tvp = tv & (u[:, 3] < P_TV_PAYANTE[c])
    eq = (fixe * FIXE) | (net * INTERNET) | (tv * TV) | (tvp * TV_PAYANTE)
    parts = np.cumsum([o.part_mobile for o in d.operateurs]); parts = parts / parts[-1]
    op = np.searchsorted(parts, u[:, 4], side="right").clip(0, len(d.operateurs) - 1)
    abos = np.zeros(len(m), np.int64)
    ua = rng.random((len(m), max(1, len(d.medias))))
    for x in d.medias:
        if x.bit_abo >= 0: abos |= (ua[:, x.indice] < x.part_abo).astype(np.int64) << x.bit_abo
    cm["tel_equipement"][m] = eq; cm["tel_mobiles"][m] = np.minimum(nmob[m], 120)
    cm["tel_operateur"][m] = op; cm["tel_retard"][m] = 0; cm["presse_abos"][m] = abos


def _recenser(p, d):
    """Chaque aube : les residents de chaque lieu, et la part equipee ( television, internet, telephone ). Les menages
    nouveaux ( nes d une union, d une migration ) s equipent."""
    tb = p.w.table; nm = tb.menages.n
    cm = p.colonnes["menage"]; cm.assurer(nm)
    ids, dom, mg = _residents(p)
    habites = np.unique(mg)
    neufs = habites[cm["tel_operateur"][habites] < 0]
    if len(neufs): _equiper(p, d, neufs, p.du_jour("medias_equipement"))
    L = d.L
    pop = np.bincount(dom, minlength=L).astype(np.float64)
    eq = cm["tel_equipement"][mg].astype(np.int64); nmob = cm["tel_mobiles"][mg].astype(np.int64)
    tv = np.bincount(dom, weights=((eq & TV) > 0).astype(np.float64), minlength=L)
    net = np.bincount(dom, weights=((eq & INTERNET) > 0).astype(np.float64), minlength=L)
    tel = np.bincount(dom, weights=(((eq & FIXE) > 0) | (nmob > 0)).astype(np.float64), minlength=L)
    q = np.maximum(pop, 1.0)
    d.pop, d.eq_tv, d.eq_net, d.eq_tel = pop, tv / q, net / q, tel / q
    d.act = np.ones(L)
    if p.a("agenda"): d.act = _activite_agenda(p, d)


def _activite_agenda(p, d):
    """Les presences de la veille hors de la maison ( culte, loisirs, courses ) : un lieu ou l on sort plus parle plus.
    Facteur par lieu de domicile, borne a [0,5 ; 2] ( a calibrer )."""
    a = p.domaine("agenda")
    NA = len(a.presence_hier[0]) // max(1, a.L)
    if a.L != d.L or NA < 7: return np.ones(d.L)
    v = a.presence_hier.reshape(24, a.L, NA).sum(0).astype(np.float64)
    social = v[:, 4] + v[:, 5] + v[:, 6]                 # courses, loisir, culte ( codes du domaine 5 )
    if social.sum() <= 0: return np.ones(d.L)
    par_tete = social / np.maximum(1.0, d.pop.sum()) * d.L
    expo = d.B.T @ par_tete if d.B is not None else par_tete    # ce que les residents de chaque lieu frequentent
    return np.clip(1.0 + 0.5 * (expo - expo.mean()) / max(expo.mean(), 1e-9), 0.5, 2.0)


def _matrices(p, d, dist):
    """Les contacts : A ( lieu de domicile x lieu de contact : maison, travail, marche du lieu ), B ( qui est present
    dans un lieu, par lieu de domicile ), M = A . B^T ( la part des contacts des residents de i avec ceux de j ) ; T
    ( les liens telephoniques : population du lieu appele, decroissance avec la distance, un plancher au loin )."""
    tb = p.w.table; L = d.L
    ids, dom, mg = _residents(p)
    trav = tb.travail[ids].astype(np.int64)
    actif = (trav >= 0) & (trav != dom)
    wh = np.where(actif, W_DOM_ACTIF, W_DOM_INACTIF); wt = np.where(actif, W_TRAV, 0.0)
    wo = 1.0 - wh - wt
    A = (np.bincount(dom * L + dom, weights=wh, minlength=L * L)
         + np.bincount(dom[actif] * L + trav[actif], weights=wt[actif], minlength=L * L)
         + np.bincount(dom * L + d.marche_de[dom], weights=wo, minlength=L * L)).reshape(L, L)
    pop = np.bincount(dom, minlength=L).astype(np.float64)
    pres = A.sum(0)                                     # personnes-contacts presentes dans chaque lieu
    B = A / np.where(pres > 0, pres, 1.0)[None, :]      # B[ j, l ] : part de la presence en l venue du domicile j
    A = A / np.maximum(pop, 1.0)[:, None]
    d.M = A @ B.T
    d.B = B
    dd = np.where(np.isfinite(dist), dist / 1000.0, np.inf)
    T = pop[None, :] * (np.exp(-dd / D_TEL_KM) + LIEN_LOINTAIN)
    np.fill_diagonal(T, 0.0)
    s = T.sum(1)
    d.T = np.where(s[:, None] > 0, T / np.where(s > 0, s, 1.0)[:, None], 0.0)


# ================================================================== les faits
def _code_sujet(d, sujet):
    k = d.code_sujet.get(sujet)
    if k is None:
        if sujet not in d.table_sujets: raise KeyError(f"sujet inconnu {sujet!r}")
        k = d.code_sujet[sujet] = len(d.sujets); d.sujets.append(sujet)
    return k


def saillance(table, sujet, valeur):
    """La saillance d un fait de ce sujet et de cette valeur ( sur la valeur crue pour une redaction )."""
    base, pente, mode = table[sujet][2:5]
    v = max(float(valeur), 0.0)
    s = base + pente * (math.log10(1.0 + v) if mode == "log" else v)
    return min(1.0, max(0.01, s))


def _ligne(d):
    mem = d.mem
    if not mem.libres:
        if mem.cap < CAP_MAX: mem.agrandir(min(CAP_MAX, 2 * mem.cap))
        else:                                           # oubli force : le moins saillant et le moins su
            idx = mem.actifs()
            score = mem.f["saillance"][idx] * mem.c["part"][idx, :d.L].max(1)
            r = int(idx[np.lexsort((mem.f["fid"][idx], score))[0]])
            mem.liberer(r); mem.oublies_force += 1
    return mem.libres.pop()


def _nouveau_fait(p, d, sujet, lieu, valeur, t, vrai=True, officiel=False, cle=None, parent=-1, s=None):
    mem = d.mem
    r = _ligne(d)
    F = mem.f
    fid = mem.prochain_fid; mem.prochain_fid += 1
    v = max(float(valeur), VALEUR_MIN)
    F["actif"][r] = True; F["fid"][r] = fid; F["sujet"][r] = _code_sujet(d, sujet); F["t"][r] = t
    F["lieu"][r] = lieu; F["lv_vrai"][r] = math.log(v) if vrai else np.nan
    F["saillance"][r] = saillance(d.table_sujets, sujet, v) if s is None else min(1.0, max(0.01, s))
    F["vrai"][r] = vrai; F["officiel"][r] = officiel; F["evenements"][r] = 1; F["parent"][r] = parent
    mem.par_fid[fid] = r
    if cle is not None: mem.cles[cle] = r; mem.cle_de[r] = cle
    p.compter("fait_constate")
    return r


def _ajouter(C_, rows, cols, dp, lv, rel, cf, lc, src, t, pop):
    """Des personnes qui apprennent : ( ligne, cellule ) uniques, `dp` en part, avec leur version. La valeur, les
    relais, la confiance de la cellule sont la moyenne ponderee des anciens et des nouveaux ; la date et la source sont
    celles de la PREMIERE personne informee ; le lieu cru bascule si les nouveaux deviennent la majorite."""
    if not len(rows): return 0.0
    P0 = C_["part"][rows, cols].astype(np.float64)
    P1 = np.minimum(1.0, P0 + dp)
    d_ = P1 - P0
    ok = d_ > 0
    if not ok.any(): return 0.0
    rows, cols, P0, P1, d_ = rows[ok], cols[ok], P0[ok], P1[ok], d_[ok]
    lv, rel, cf, lc = (np.broadcast_to(np.asarray(x), ok.shape)[ok] for x in (lv, rel, cf, lc))
    w1 = d_ / P1; w0 = 1.0 - w1
    C_["lv"][rows, cols] = w0 * C_["lv"][rows, cols] + w1 * lv
    C_["relais"][rows, cols] = w0 * C_["relais"][rows, cols] + w1 * rel
    C_["conf"][rows, cols] = w0 * C_["conf"][rows, cols] + w1 * cf
    neuf = P0 <= 0.0
    if neuf.any():
        C_["appris"][rows[neuf], cols[neuf]] = t
        C_["source"][rows[neuf], cols[neuf]] = np.broadcast_to(np.asarray(src), neuf.shape)[neuf] if np.ndim(src) else src
    bascule = neuf | (w1 > 0.5)
    C_["lieu_cru"][rows[bascule], cols[bascule]] = lc[bascule]
    C_["part"][rows, cols] = P1
    return float(np.dot(d_, pop[cols]))


def _graines(dp, P0, pop, u):
    """La premiere personne d une cellule : sous une personne attendue, elle apprend avec cette probabilite ( une
    personne entiere ), sinon rien. Au-dela, la part attendue."""
    e = dp * pop
    premier = (P0 <= 0.0) & (e < 1.0)
    return np.where(premier, np.where(u < e, 1.0 / np.maximum(pop, 1.0), 0.0), dp)


def _temoins(p, d, r, temoins, t, rng, lv, lieu, conf=CONF_TEMOIN, src=TEMOIN):
    """Ceux qui voient le fait : `temoins` personnes reparties selon qui frequente le lieu ( B ), 80 % des residents du
    lieu ( "lieu" ) ou de chaque lieu de l ile ( "ile" )."""
    L = d.L; pop = d.pop
    if temoins == 0: return
    if temoins == "ile":
        e = np.where(np.array([i == d.ile_de[lieu] for i in d.ile_de]), 0.8 * pop, 0.0)
    elif temoins == "lieu":
        e = np.zeros(L); e[lieu] = 0.8 * pop[lieu]
        if pop[lieu] <= 0: e[d.marche_de[lieu]] = 0.8 * pop[d.marche_de[lieu]]
    else:
        col = d.B[:, lieu] if d.B[:, lieu].sum() > 0 else d.B[:, d.marche_de[lieu]]
        e = float(temoins) * col
    cells = np.nonzero(e > 0)[0]
    if not len(cells): return
    u = rng.random(len(cells)); z = rng.standard_normal(len(cells))
    P0 = d.mem.c["part"][r, cells].astype(np.float64)
    dp = np.where(e[cells] >= 1.0, e[cells] / np.maximum(pop[cells], 1.0), np.where(u < e[cells], 1.0 / np.maximum(pop[cells], 1.0), 0.0))
    dp = np.minimum(dp, 0.95 - np.minimum(P0, 0.95))
    _ajouter(d.mem.c, np.full(len(cells), r), cells, dp, lv + SIGMA_TEMOIN * z, 0.0, conf, lieu, src, t, pop)


def constater(p, sujet, lieu, valeur=1.0, temoins=None, officiel=None, t=None, s=None, cle=None, rng=None):
    """Un fait VRAI du monde ( un autre domaine, une porte ) : sujet de SUJETS, lieu ( identifiant ou numero ), valeur.
    Rend son identifiant. Les temoins par defaut sont ceux du sujet ; un fait sans temoin est officiel ( communique )."""
    d = _dom(p)
    if sujet not in d.table_sujets: raise KeyError(f"sujet inconnu {sujet!r}")
    n = d.n_du_lieu[lieu] if isinstance(lieu, str) else int(lieu)
    t = _t(p) if t is None else float(t)
    tem = d.table_sujets[sujet][5] if temoins is None else temoins
    off = (tem == 0) if officiel is None else bool(officiel)
    r = _nouveau_fait(p, d, sujet, n, valeur, t, True, off, cle, s=s)
    fid = int(d.mem.f["fid"][r])
    rng = rng if rng is not None else p.socle.hasard.sous_flux("medias_temoins", 3, fid)   # un flux par fait
    _temoins(p, d, r, tem, t, rng, float(d.mem.f["lv_vrai"][r]), n)
    return fid


def fabriquer_rumeur(p, sujet, lieu, valeur=1.0, personnes=PERSONNES_ORIGINE, parent=-1, t=None, rng=None):
    """Une FAUSSE nouvelle nait dans un lieu : quelques personnes y croient. Rend son identifiant."""
    d = _dom(p)
    n = d.n_du_lieu[lieu] if isinstance(lieu, str) else int(lieu)
    t = _t(p) if t is None else float(t)
    v = max(float(valeur), VALEUR_MIN)
    r = _nouveau_fait(p, d, sujet, n, v, t, vrai=False, parent=parent)
    rng = rng if rng is not None else p.socle.hasard.sous_flux("medias_origine", 3, int(d.mem.f["fid"][r]))
    pop = d.pop
    cell = n if pop[n] > 0 else int(d.marche_de[n])
    dp = min(1.0, personnes / max(pop[cell], 1.0))
    _ajouter(d.mem.c, np.array([r]), np.array([cell]), np.array([dp]), math.log(v) + SIGMA_TEMOIN * rng.standard_normal(1),
             0.0, CONF_ORIGINE, n, ORIGINE, t, pop)
    fid = int(d.mem.f["fid"][r])
    p.noter("fausse_nouvelle", fait=fid, sujet=sujet, lieu=d.lieu_ids[n])
    return fid


# ================================================================== le journal : ce qui devient une nouvelle
def _lieu_de(p, d, e):
    carte = p.w.carte.lieux
    for k in CHAMPS_LIEU:
        v = e.get(k)
        if isinstance(v, str) and v in carte: return carte[v].n, False
    h = e.get("habitant")
    tb = p.w.table
    if isinstance(h, (int, np.integer)) and 0 <= h < tb.n and tb.domicile[h] >= 0: return int(tb.domicile[h]), False
    m = e.get("menage")
    if isinstance(m, (int, np.integer)) and 0 <= m < tb.menages.n and tb.menages.domicile[m] >= 0:
        return int(tb.menages.domicile[m]), False
    i = e.get("ile")
    if isinstance(i, str) and i in d.capitale_ile: return d.capitale_ile[i], False
    return d.capitale_ile[d.iles[0]], True


def _valeur(e, champ):
    if champ is None: return 1.0
    v = e.get(champ)
    try: v = float(v)
    except (TypeError, ValueError): return 1.0
    return v if math.isfinite(v) else 1.0


def _enregistrer(p, d, sujet, lieu, valeur, t, jour, rng):
    """Un evenement du journal devient un fait, ou grossit le fait du meme sujet, du meme lieu, du meme jour."""
    table = d.table_sujets
    agr = table[sujet][6]
    cle = (sujet, lieu, int(jour))
    mem = d.mem
    r = mem.cles.get(cle)
    tem = table[sujet][5]
    if r is not None and mem.f["actif"][r]:
        ancien = math.exp(float(mem.f["lv_vrai"][r]))
        v = ancien + valeur if agr == "somme" else max(ancien, valeur)
        mem.f["lv_vrai"][r] = math.log(max(v, VALEUR_MIN)); mem.f["evenements"][r] += 1
        mem.f["saillance"][r] = saillance(table, sujet, v)
        if tem != 0 and tem not in ("lieu", "ile"):
            _temoins(p, d, r, tem, t, rng, float(mem.f["lv_vrai"][r]), lieu)
        return r
    r = _nouveau_fait(p, d, sujet, lieu, valeur, t, True, tem == 0, cle)
    _temoins(p, d, r, tem, t, rng, float(mem.f["lv_vrai"][r]), lieu)
    return r


def _lire_journal(p, d):
    """Les lignes du journal ecrites depuis la derniere lecture ( de la plus recente vers la derniere vue ). Seuls les
    types de NOUVELLES ( et de la justice ) deviennent des faits."""
    rec = p.socle.journal.recents
    nouveaux = []
    for e in reversed(rec):
        if e is d.journal_vu: break
        nouveaux.append(e)
    if not nouveaux: return
    d.journal_vu = rec[-1]
    rng = None
    for e in reversed(nouveaux):
        ty = e["type"]
        if ty == "deces":
            sujet, champ = SUJET_DU_DECES.get(e.get("cause"), "deces"), None
        else:
            x = d.nouvelles.get(ty)
            if x is None: continue
            sujet, champ = x
        if rng is None: rng = p.socle.hasard.sous_flux("medias_journal", 1, p.jour, int(p.w.minutes % 1440))
        lieu, _ = _lieu_de(p, d, e)
        t = min(_t_de(e["jour"], e["heure"]), _t(p))
        _enregistrer(p, d, sujet, lieu, _valeur(e, champ), t, e["jour"], rng)


def _statistiques(p, d):
    """7 h : la statistique publiee la veille par l Etat devient un fait officiel, a la cadence de sa publication."""
    pub = ET.publications(p)
    t = _t(p)
    for sujet, chemin, cadence, echelle in STATS:
        dernier = d.stats_vues.get(sujet)
        if dernier is not None and p.jour - dernier < cadence: continue
        v = pub
        for k in chemin: v = v.get(k) if isinstance(v, dict) else None
        if v is None: continue
        try: v = float(v) * echelle
        except (TypeError, ValueError): continue
        if not math.isfinite(v) or v <= 0: continue
        d.stats_vues[sujet] = p.jour
        _nouveau_fait(p, d, sujet, d.capitale_ile[d.iles[0]], v, t, True, True, (sujet, -1, int(p.jour)))


def _rumeurs(p, d):
    """8 h : les fausses nouvelles du jour. Spontanees ( au prorata de la population ) et jumelles des faits vrais
    saillants nes la veille."""
    rng = p.du_jour("medias_rumeurs")
    mem = d.mem; t = _t(p)
    N = d.pop.sum()
    n = int(rng.poisson(FAUX_PAR_MILLION_J * N / 1e6))
    habites = np.nonzero(d.pop > 0)[0]
    if not len(habites): return
    poids = d.pop[habites] / d.pop[habites].sum()
    noms = [f[0] for f in FAUSSES]; pf = np.array([f[1] for f in FAUSSES]); pf = pf / pf.sum()
    for _ in range(n):
        k = int(rng.choice(len(noms), p=pf))
        lieu = int(habites[rng.choice(len(habites), p=poids)])
        fabriquer_rumeur(p, noms[k], lieu, FAUSSES[k][2] * math.exp(0.5 * rng.standard_normal()), rng=rng, t=t)
    idx = mem.actifs()
    idx = idx[mem.f["vrai"][idx] & (mem.f["t"][idx] > t - 1.0) & (mem.f["saillance"][idx] >= 0.3) & (mem.f["parent"][idx] < 0)]
    for r in idx.tolist():
        s = float(mem.f["saillance"][r])
        u = rng.random(3)
        if u[0] >= P_JUMELLE * s: continue
        lieu = int(mem.f["lieu"][r])
        if u[1] < 0.5: lieu = int(d.voisins[lieu, int(u[2] * 3) % 3])
        sujet = d.sujets[int(mem.f["sujet"][r])]
        v = math.exp(float(mem.f["lv_vrai"][r]) + EXAGERATION_JUMELLE + 0.5 * rng.standard_normal())
        fabriquer_rumeur(p, sujet, lieu, v, parent=int(mem.f["fid"][r]), rng=rng, t=t)


# ================================================================== la rumeur ( fonction pure, testee seule )
def diffuser(part, lv, rel, cf, lc, M, T, s, act, tel, pop, dt, beta_bao, beta_tel, z, u, v_lieu, voisins, mu, sigma,
             q_lieu, partage):
    """Un pas de bouche a oreille et de telephone sur des faits ( lignes ) et des lieux ( colonnes ). Rend ( part,
    valeur en log, relais, confiance, lieu cru, masque des cellules nouvellement informees ). Les nouveaux informes
    prennent la version moyenne de ceux qui les informent, deformee d un relais ( mu + sigma z ), et le lieu cru de la
    source dominante ( confondu avec un voisin avec la probabilite q_lieu ). Aucune entree n est modifiee."""
    X = part @ M.T                                              # exposition aux informes par les contacts
    Pt = part * tel[None, :]
    Y = Pt @ T.T                                                # appels recus d informes equipes
    rb = beta_bao * (s * partage)[:, None] * act[None, :] * X
    rt = beta_tel * (s * partage)[:, None] * tel[None, :] * Y
    tot = rb + rt
    dp = (1.0 - part) * (1.0 - np.exp(-tot * dt))
    dp = _graines(dp, part, pop[None, :], u)
    fb = np.where(tot > 0, rb / np.where(tot > 0, tot, 1.0), 1.0)
    lvb = np.where(X > 0, (part * lv) @ M.T / np.where(X > 0, X, 1.0), lv)
    lvt = np.where(Y > 0, (Pt * lv) @ T.T / np.where(Y > 0, Y, 1.0), lv)
    rlb = np.where(X > 0, (part * rel) @ M.T / np.where(X > 0, X, 1.0), rel)
    rlt = np.where(Y > 0, (Pt * rel) @ T.T / np.where(Y > 0, Y, 1.0), rel)
    cfb = np.where(X > 0, (part * cf) @ M.T / np.where(X > 0, X, 1.0), cf)
    cft = np.where(Y > 0, (Pt * cf) @ T.T / np.where(Y > 0, Y, 1.0), cf)
    lv_src = fb * lvb + (1.0 - fb) * lvt + mu + sigma * z
    rel_src = fb * rlb + (1.0 - fb) * rlt + 1.0
    cf_src = CONF_RELAIS * (fb * cfb + (1.0 - fb) * cft)
    P1 = np.minimum(1.0, part + dp)
    d_ = P1 - part
    w1 = np.where(P1 > 0, d_ / np.where(P1 > 0, P1, 1.0), 0.0)
    lv2 = (1.0 - w1) * lv + w1 * lv_src
    rel2 = (1.0 - w1) * rel + w1 * rel_src
    cf2 = (1.0 - w1) * cf + w1 * cf_src
    neuf = (part <= 0.0) & (d_ > 0)
    lc2 = lc.copy()
    if neuf.any():
        fs, cs = np.nonzero(neuf)
        par_tel = fb[fs, cs] < 0.5
        sb = M[cs, :] * part[fs, :]; st = T[cs, :] * Pt[fs, :]
        j = np.where(par_tel, np.argmax(st, axis=1), np.argmax(sb, axis=1))
        src = lc[fs, j]
        conf_lieu = v_lieu[fs, cs] < q_lieu
        if conf_lieu.any():
            k = (v_lieu[fs, cs][conf_lieu] / max(q_lieu, 1e-12) * voisins.shape[1]).astype(np.int64) % voisins.shape[1]
            src[conf_lieu] = voisins[np.maximum(src[conf_lieu], 0), k]
        lc2[fs, cs] = src
    return P1, lv2, rel2, cf2, lc2, neuf, fb


def _propager(p, d):
    """Un pas horaire de rumeur, pour tous les faits vivants, sur les lieux puis sur les groupes."""
    mem = d.mem
    idx = mem.actifs()
    if not len(idx): return
    L = d.L; t = _t(p)
    Cc = mem.c
    part = Cc["part"][idx, :L].astype(np.float64)
    if not part.any(): return
    lv = Cc["lv"][idx, :L].astype(np.float64); rel = Cc["relais"][idx, :L].astype(np.float64)
    cf = Cc["conf"][idx, :L].astype(np.float64); lc = Cc["lieu_cru"][idx, :L]
    s = mem.f["saillance"][idx].astype(np.float64)
    partage = np.where(np.isnan(mem.f["dementi_t"][idx]), 1.0, PARTAGE_DEMENTI)
    tel = d.eq_tel * d.reseau.ok
    rng = p.socle.hasard.sous_flux("medias_rumeur", 1, int(p.jour), int(p.heure))
    F = len(idx)
    z = rng.standard_normal((F, L)); u = rng.random((F, L)); vl = rng.random((F, L))
    P1, lv2, rel2, cf2, lc2, neuf, fb = diffuser(part, lv, rel, cf, lc, d.M, d.T, s, d.act, tel, d.pop, DT, BETA_BAO,
                                                  BETA_TEL, z, u, vl, d.voisins, d.mu, d.sigma, d.q_lieu, partage)
    Cc["part"][idx, :L] = P1; Cc["lv"][idx, :L] = lv2; Cc["relais"][idx, :L] = rel2; Cc["conf"][idx, :L] = cf2
    Cc["lieu_cru"][idx, :L] = lc2
    if neuf.any():
        fs, cs = np.nonzero(neuf)
        Cc["appris"][idx[fs], cs] = t
        Cc["source"][idx[fs], cs] = np.where(fb[fs, cs] >= 0.5, BOUCHE, TELEPHONE)
    G = len(d.groupes)
    if G: _propager_groupes(p, d, idx, part, lv, rel, cf, lc, s * partage, t, rng)


def _propager_groupes(p, d, idx, part, lv, rel, cf, lc, s, t, rng):
    """Un groupe apprend de ceux qu il cotoie ( ses poids par lieu ) ; il ne renvoie rien aux lieux."""
    L = d.L; Cc = d.mem.c
    W = np.array(d.poids_groupe)                       # G x L
    X = part @ W.T
    if not X.any(): return
    cols = L + np.arange(len(d.groupes))
    Pg = Cc["part"][idx][:, cols].astype(np.float64)
    taille = np.array(d.taille, np.float64)
    dp = (1.0 - Pg) * (1.0 - np.exp(-BETA_BAO * s[:, None] * X * DT))
    dp = _graines(dp, Pg, taille[None, :], rng.random(dp.shape))
    safe = np.where(X > 0, X, 1.0)
    lv_s = (part * lv) @ W.T / safe + d.mu + d.sigma * rng.standard_normal(dp.shape)
    rel_s = (part * rel) @ W.T / safe + 1.0
    cf_s = CONF_RELAIS * (part * cf) @ W.T / safe
    j = np.argmax(part[:, None, :] * W[None, :, :], axis=2)
    lc_s = np.take_along_axis(lc, j, axis=1)
    fs, gs = np.nonzero(dp > 0)
    if len(fs):
        pops = np.concatenate((d.pop, taille))
        _ajouter(Cc, idx[fs], cols[gs], dp[fs, gs], lv_s[fs, gs], rel_s[fs, gs], cf_s[fs, gs], lc_s[fs, gs], BOUCHE, t, pops)


# ================================================================== les medias : diffuser, verifier, dementir
def _attention(s): return ATTENTION_BASE + ATTENTION_PENTE * s


def _disponible(d, m):
    """La part de la portee d un media joignable a cette heure : la television avec le courant, un site avec le reseau."""
    if m.genre == "tv": return d.reseau.elec.astype(np.float64)
    if m.genre == "site": return d.reseau.ok.astype(np.float64)
    return np.ones(d.L)


def _version(p, d, m, r, verifie):
    """La version d une nouvelle telle que CE media la diffuserait : la verite ( communique, verification ), sinon la
    croyance du lieu de sa zone qui en sait le plus, grossie par son sensationnalisme ; un sujet gouvernemental est
    cadre par sa ligne. ( lv, lieu, relais, age de la version )."""
    mem = d.mem; F = mem.f; Cc = mem.c
    sujet = d.sujets[int(F["sujet"][r])]
    if bool(F["vrai"][r]) and (verifie or bool(F["officiel"][r])):
        lv, lieu, rel, t0 = float(F["lv_vrai"][r]), int(F["lieu"][r]), 0.0, float(F["t"][r])
    else:
        c = _mieux_informe(d, m, r)
        if Cc["part"][r, c] > 0:
            lv = float(Cc["lv"][r, c]) + SENSATION_LOG * m.sensation
            lieu = int(Cc["lieu_cru"][r, c]); rel = float(Cc["relais"][r, c]) + 1.0; t0 = float(Cc["appris"][r, c])
        else:                                       # personne dans sa zone : la rumeur telle qu elle est nee
            lv = float(Cc["lv"][r, :d.L].max()) if not F["vrai"][r] else float(F["lv_vrai"][r])
            lieu, rel, t0 = -1, 1.0, float(F["t"][r])
        if lieu < 0: lieu = int(F["lieu"][r])
        if not math.isfinite(t0): t0 = float(F["t"][r])
    if d.table_sujets[sujet][1]: lv += BIAIS_LIGNE[m.ligne]
    return lv, lieu, rel, t0


def _couverture(d, m):
    """Les lieux habites de la zone du media ( le pays, ou son ile ), refaits avec la portee du jour."""
    if m.cov is None: _audiences(d)
    return m.cov


def _mieux_informe(d, m, r):
    """Le lieu de la zone du media ou la nouvelle est la plus sue ( son correspondant le mieux place )."""
    cov = _couverture(d, m)
    if not len(cov): return int(d.mem.f["lieu"][r])
    return int(cov[np.argmax(d.mem.c["part"][r, cov])])


def _diffuser_media(p, d, m, r, version, rng):
    """Une diffusion : dans chaque lieu, la portee du media a cette heure fois l attention que la nouvelle retient.
    Les nouveaux informes prennent sa version ; les anciens exposes s y rallient a hauteur de sa credibilite. Rend les
    personnes nouvellement informees."""
    mem = d.mem; Cc = mem.c; L = d.L
    lv, lieu, rel, _ = version
    s = saillance(d.table_sujets, d.sujets[int(mem.f["sujet"][r])], math.exp(lv))
    R = m.portee * _disponible(d, m) * _attention(s)
    P0 = Cc["part"][r, :L].astype(np.float64)
    u = np.clip(R * m.cred, 0.0, 1.0)
    vieux = P0 > 0
    if vieux.any():
        c = np.nonzero(vieux)[0]
        Cc["lv"][r, c] += u[c] * (lv - Cc["lv"][r, c]); Cc["relais"][r, c] += u[c] * (rel - Cc["relais"][r, c])
        Cc["conf"][r, c] += u[c] * (m.cred - Cc["conf"][r, c])
        Cc["lieu_cru"][r, c[u[c] > 0.5]] = lieu
    dp = _graines((1.0 - P0) * R, P0, d.pop, rng.random(L))
    cells = np.nonzero(dp > 0)[0]
    pops = np.concatenate((d.pop, np.array(d.taille, np.float64)))
    gain = _ajouter(Cc, np.full(len(cells), r), cells, dp[cells], lv, rel, m.cred, lieu, MEDIA0 + m.indice, _t(p), pops)
    G = len(d.groupes)
    if G:
        W = np.array(d.poids_groupe); suit = np.array(d.suit_medias, bool)
        Rg = (W @ R) * suit
        cols = L + np.arange(G)
        Pg = Cc["part"][r, cols].astype(np.float64)
        dpg = _graines((1.0 - Pg) * Rg, Pg, np.array(d.taille, np.float64), rng.random(G))
        g = np.nonzero(dpg > 0)[0]
        _ajouter(Cc, np.full(len(g), r), cols[g], dpg[g], lv, rel, m.cred, lieu, MEDIA0 + m.indice, _t(p), pops)
    if np.isnan(mem.f["publie_t"][r]): mem.f["publie_t"][r] = _t(p)
    return gain


def _creneau(p, m):
    """Le temps absolu de la prochaine diffusion du media."""
    t = _t(p)
    h = CRENEAU[m.genre]
    if h is None: return t + 1.0 / 24.0 - 1e-9     # la prochaine heure pleine ( la routine horaire suivante )
    dec = ((h - 6.0) % 24.0) / 24.0                 # les occurrences de l heure h : k + dec, k entier
    return math.floor(t - dec) + 1.0 + dec


def publier(p, fait, media, verifie=False, immediat=False):
    """Un media publie un fait ( identifiant ) : a son prochain creneau, ou tout de suite ( `immediat` : un communique
    lu a l antenne, une porte ). Rend le temps de diffusion, ou None si le fait est oublie."""
    d = _dom(p)
    m = d.medias[media] if isinstance(media, (int, np.integer)) else next(x for x in d.medias if x.nom == media)
    r = d.mem.par_fid.get(int(fait))
    if r is None: return None
    version = _version(p, d, m, r, verifie)
    d.mem.traite[r, m.indice] = EN_COURS
    if immediat:
        _diffusion(p, d, m, r, version, p.socle.hasard.sous_flux("medias_diffusion", 2, int(fait), m.indice))
        return _t(p)
    tp = _creneau(p, m)
    d.file_pub.append([tp, m.indice, int(fait), version])
    return tp


def _diffusion(p, d, m, r, version, rng):
    gain = _diffuser_media(p, d, m, r, version, rng)
    d.mem.traite[r, m.indice] = PUBLIE
    m.publies += 1
    fid = int(d.mem.f["fid"][r])
    if not d.mem.f["vrai"][r]: m.faux_publies += 1
    else: m.cred += ETA_CRED * (1.0 - m.cred)
    k = (m.indice, fid)
    d.gains[k] = d.gains.get(k, 0.0) + gain / max(m.aud_personnes, 1.0)
    p.compter("publication")


def _diffusions_dues(p, d):
    if not d.file_pub: return
    t = _t(p)
    dues = [e for e in d.file_pub if e[0] <= t + 1e-9]
    if not dues: return
    d.file_pub = [e for e in d.file_pub if e[0] > t + 1e-9]
    rng = p.socle.hasard.sous_flux("medias_diffusion", 1, int(p.jour), int(p.heure))
    for tp, mi, fid, version in dues:
        r = d.mem.par_fid.get(fid)
        if r is None: continue
        if not d.mem.f["vrai"][r] and not np.isnan(d.mem.f["dementi_t"][r]):   # dementie avant l antenne : retiree
            d.mem.traite[r, mi] = TUE; p.compter("nouvelle_tuee"); continue
        _diffusion(p, d, d.medias[mi], r, version, rng)


def dementir(p, fait):
    """Une fausse nouvelle est dementie ( verificateurs, communique ) : la confiance de ceux qui y croient s effondre,
    on la repete moins, on l oublie plus vite ; chaque media qui l a publiee perd de sa credibilite."""
    d = _dom(p)
    r = d.mem.par_fid.get(int(fait))
    if r is None or d.mem.f["vrai"][r] or not np.isnan(d.mem.f["dementi_t"][r]): return False
    mem = d.mem
    mem.f["dementi_t"][r] = _t(p)
    mem.c["conf"][r] *= 0.3
    for m in d.medias:
        if mem.traite[r, m.indice] == PUBLIE:
            m.cred *= (1.0 - K_CRED); m.dementis += 1
            k = (m.indice, int(fait))
            d.penalites[k] = d.penalites.get(k, 0.0) + K_FAUX
    part = float(np.dot(mem.c["part"][r, :d.L], d.pop) / max(d.pop.sum(), 1.0))
    p.noter("dementi", fait=int(fait), sujet=d.sujets[int(mem.f["sujet"][r])], part=round(part, 4))
    return True


def _dementis(p, d):
    """9 h : les fausses nouvelles qui circulent sont dementies avec une probabilite qui croit avec leur diffusion."""
    mem = d.mem
    idx = mem.actifs()
    idx = idx[~mem.f["vrai"][idx] & np.isnan(mem.f["dementi_t"][idx])]
    if not len(idx): return
    rng = p.du_jour("medias_dementi")
    u = rng.random(len(idx))
    nat = mem.c["part"][idx, :d.L].astype(np.float64) @ d.pop / max(d.pop.sum(), 1.0)
    publie = ~np.isnan(mem.f["publie_t"][idx])
    pd_ = P_DEMENTI_BASE + P_DEMENTI_VIRAL * np.minimum(1.0, 20.0 * nat) + P_DEMENTI_PUBLIE * publie
    for r in idx[u < pd_].tolist(): dementir(p, int(mem.f["fid"][r]))


def _verifications(p, d):
    """9 h : les verifications lancees la veille rendent leur resultat."""
    t = _t(p)
    dues = [e for e in d.file_verif if e[0] <= t + 1e-9]
    if not dues: return
    d.file_verif = [e for e in d.file_verif if e[0] > t + 1e-9]
    rng = p.du_jour("medias_verif")
    u = rng.random(len(dues))
    for (tv, mi, fid), x in zip(dues, u.tolist()):
        r = d.mem.par_fid.get(fid)
        if r is None: continue
        m = d.medias[mi]
        if x < P_VERIF_OK and not d.mem.f["vrai"][r]:
            d.mem.traite[r, mi] = TUE; p.compter("nouvelle_tuee"); continue
        version = _version(p, d, m, r, verifie=x < P_VERIF_OK)
        d.file_pub.append([_creneau(p, m), mi, fid, version])


# ================================================================== la conference de redaction
def _candidats(d, m):
    """Les faits vivants que ce media n a pas traites et qu il voit : un communique, ou 2 % d un lieu de sa zone."""
    mem = d.mem
    idx = mem.actifs()
    if not len(idx): return idx
    idx = idx[mem.traite[idx, m.indice] == NOUVEAU]
    if not len(idx): return idx
    cov = _couverture(d, m)
    vu = mem.f["officiel"][idx] | (mem.c["part"][idx][:, cov].max(1) >= SEUIL_VEILLE if len(cov) else False)
    return idx[vu]


def _traits(p, d, m, r, nat_r, charge, version):
    mem = d.mem; F = mem.f
    lv, lieu, rel, t0 = version
    sujet = d.sujets[int(F["sujet"][r])]
    c = _mieux_informe(d, m, r)
    off = bool(F["officiel"][r])
    conf = 1.0 if off else float(mem.c["conf"][r, c])
    autres = [x.indice for x in d.medias if x.indice != m.indice]
    conc = float(np.mean(mem.traite[r, autres] == PUBLIE)) if autres else 0.0
    return (saillance(d.table_sujets, sujet, math.exp(lv)), min(1.0, max(0.0, conf)), 1.0 if off else 0.0,
            min(1.0, rel / 5.0), conc, min(1.0, max(0.0, nat_r)), min(1.0, max(0.0, (_t(p) - t0) / 3.0)),
            min(1.0, max(0.0, m.cred)), m.sensation, min(1.0, charge))


def _redaction(p, d):
    """9 h : verifications rendues, dementis, puis chaque media examine ses K_MAX nouvelles les plus saillantes."""
    _verifications(p, d)
    _dementis(p, d)
    if not d.redactions_actives: return
    mem = d.mem
    dec = d.decideur
    slot0 = (p.jour % (HORIZON_PUBLICATION + 1)) * K_MAX
    tot = max(d.pop.sum(), 1.0)
    for m in d.medias:
        m.verifs_jour = 0
        idx = _candidats(d, m)
        if not len(idx): continue
        nat = mem.c["part"][idx, :d.L].astype(np.float64) @ d.pop / tot
        versions = [_version(p, d, m, r, False) for r in idx.tolist()]
        s_vu = np.array([saillance(d.table_sujets, d.sujets[int(mem.f["sujet"][r])], math.exp(v[0]))
                         for r, v in zip(idx.tolist(), versions)])
        ordre = np.lexsort((mem.f["fid"][idx], -s_vu))[:K_MAX]
        for k, o in enumerate(ordre.tolist()):
            r = int(idx[o]); fid = int(mem.f["fid"][r])
            x = _traits(p, d, m, r, float(nat[o]), m.verifs_jour / m.capacite, versions[o])
            cle = m.indice * (HORIZON_PUBLICATION + 1) * K_MAX + slot0 + k
            a = dec.decider(cle, ContextePublication(x))
            d.suivi[cle] = [m.indice, fid, 0]
            if a == PUBLIER:
                mem.traite[r, m.indice] = EN_COURS
                d.file_pub.append([_creneau(p, m), m.indice, fid, versions[o]])
            elif a == VERIFIER:
                mem.traite[r, m.indice] = EN_COURS
                surcharge = 1.0 if m.verifs_jour >= m.capacite else 0.0
                m.verifs_jour += 1
                d.file_verif.append([_t(p) + 1.0 + surcharge - 1e-6, m.indice, fid])
                d.couts[(m.indice, fid)] = d.couts.get((m.indice, fid), 0.0) + C_VERIF
                p.compter("verification")
            else:
                mem.traite[r, m.indice] = IGNORE; p.compter("nouvelle_ignoree")


def _noter(p, d):
    """22 h 30 : chaque decision en attente recoit la consequence du jour pour son media et sa nouvelle."""
    dec = d.decideur
    for cle in sorted(d.suivi):
        mi, fid, n = d.suivi[cle]
        k = (mi, fid)
        v = d.gains.get(k, 0.0) - d.penalites.get(k, 0.0) - d.couts.get(k, 0.0)
        dec.noter(cle, v, p.jour)
        d.suivi[cle][2] = n + 1
        if n + 1 >= HORIZON_PUBLICATION: del d.suivi[cle]
    d.gains, d.penalites, d.couts = {}, {}, {}


# ================================================================== le reseau de telecommunications
def _reseau_heure(p, d):
    """Chaque heure : le courant de chaque lieu ( energie ), la batterie des relais, les pannes propres ; une coupure
    et un retablissement sont notes au journal."""
    R = d.reseau; L = d.L; t = _t(p)
    if p.a("energie"):
        EN = _energie()
        elec = np.array([not EN.coupure_en_cours(p, lid) for lid in d.lieu_ids])
    else: elec = np.ones(L, bool)
    R.elec = elec
    R.batterie_h = np.where(elec, np.minimum(AUTONOMIE_H, R.batterie_h + AUTONOMIE_H / RECHARGE_H), np.maximum(0.0, R.batterie_h - 1.0))
    panne = R.panne_fin > t
    ok = (elec | (R.batterie_h > 0)) & ~panne
    for k in np.nonzero(R.ok & ~ok)[0].tolist():
        R.coupe_t[k] = t
        R.cause[k] = "equipement" if panne[k] else "electricite"
        p.noter("panne_telecom", lieu=d.lieu_ids[k], cause=R.cause[k])
    for k in np.nonzero(~R.ok & ok)[0].tolist():
        h = (t - R.coupe_t[k]) * 24.0
        R.heures_coupees[k] += h
        p.noter("telecom_retabli", lieu=d.lieu_ids[k], heures=round(h, 1))
    R.ok = ok


def _energie():
    from . import d11_energie as EN       # optionnel : importe seulement quand l energie est installee
    return EN


def _pannes_du_jour(p, d):
    rng = p.du_jour("medias_telecom")
    u = rng.random(d.L); dur = PANNE_MEDIANE_H * np.exp(0.8 * rng.standard_normal(d.L))
    t = _t(p)
    touche = (u < P_PANNE_TELECOM_J) & (d.pop > 0)
    d.reseau.panne_fin = np.where(touche, np.maximum(d.reseau.panne_fin, t + dur / 24.0), d.reseau.panne_fin)


# ================================================================== l argent
def _menage(tb, k): return PO.Menage(int(k), tb.menages)


def _prix_dr(eur): return eur / EUROS


def _facturer(p, d):
    """11 h : un menage sur trente recoit sa facture du mois ( son numero modulo 30 ). Il paie ce que sa caisse permet
    au-dela de RESERVE_J jours de nourriture ; un impaye ajoute un mois de retard, deux mois suspendent le fixe,
    internet, la television payante et la presse."""
    w = p.w; tb = w.table; nm = tb.menages.n; n = tb.n; L = p.socle.livre
    cm = p.colonnes["menage"]; cm.assurer(nm)
    mg = PO.menages_inscrits(tb, n)
    vivants = np.bincount(mg[(tb.vivant[:n] == 1) & (mg >= 0)], minlength=nm)
    ks = np.nonzero((np.arange(nm) % MOIS_J == p.jour % MOIS_J) & (vivants > 0) & (cm["tel_operateur"][:nm] >= 0))[0]
    d.compte["factures"] = int(len(ks))
    if not len(ks): return
    eq = cm["tel_equipement"][ks].astype(np.int64); nmob = np.minimum(cm["tel_mobiles"][ks].astype(np.int64), vivants[ks])
    tel = (nmob * PRIX_MOBILE_EUR + ((eq & FIXE) > 0) * PRIX_FIXE_EUR + ((eq & INTERNET) > 0) * PRIX_INTERNET_EUR
           + ((eq & TV_PAYANTE) > 0) * PRIX_TV_PAYANTE_EUR) / EUROS
    abos = cm["presse_abos"][ks].astype(np.int64)
    presse = [(x, x.bit_abo, _prix_dr(x.prix_abo)) for x in d.medias if x.bit_abo >= 0]
    caisse = tb.menages.caisse
    for j, k in enumerate(ks.tolist()):
        dispo = max(0.0, float(caisse[k]) - RESERVE_J * RATION_DR * float(vivants[k]))
        du_tel = float(tel[j])
        lignes = [(x, prix) for x, bit, prix in presse if (abos[j] >> bit) & 1]
        du = du_tel + sum(pr for _, pr in lignes)
        if du <= 0: continue
        paye_tout = dispo >= du - 1e-9
        vue = None
        if du_tel > 0 and dispo > 0:
            op = d.operateurs[int(cm["tel_operateur"][k])]
            vue = _menage(tb, k)
            x = L.transferer(vue, op, min(du_tel, dispo), "abonnement_telecom")
            dispo -= x; op.recettes_ht_mois += x / (1.0 + TVA_TELECOM); op.tva_due += x * TVA_TELECOM / (1.0 + TVA_TELECOM)
            op.recu_total += x
        for x_, prix in lignes:
            if dispo <= 0: break
            vue = vue or _menage(tb, k)
            y = L.transferer(vue, x_, min(prix, dispo), "abonnement_presse")
            dispo -= y; x_.recettes_ht_mois += y / (1.0 + TVA_PRESSE); x_.tva_due += y * TVA_PRESSE / (1.0 + TVA_PRESSE)
            x_.recettes_abo += y
        p.compter("facture_telecom", du)
        if paye_tout: cm["tel_retard"][k] = 0
        else:
            cm["tel_retard"][k] = min(100, int(cm["tel_retard"][k]) + 1)
            if cm["tel_retard"][k] >= MOIS_AVANT_SUSPENSION and (int(eq[j]) & (FIXE | INTERNET | TV_PAYANTE) or abos[j]):
                cm["tel_equipement"][k] = int(eq[j]) & TV
                cm["presse_abos"][k] = 0
                d.suspendus += 1; p.compter("abonnement_suspendu")
    for x in list(d.operateurs) + list(d.medias): _reverser_tva(p, x)


def _reverser_tva(p, x):
    """La TVA collectee est reversee a l Etat ( motif tva du moteur ; w.tva_percue, comme percevoir_tva du domaine 6 )."""
    if x.tva_due <= 1e-9: return
    paye = p.socle.livre.transferer(x, p.w.gouv, x.tva_due, "tva")
    p.w.tva_percue += paye
    x.tva_due -= paye
    if isinstance(x, Operateur): x.tva_total += paye


def _pib_hier(p):
    try: return float(ET.publications(p)["statistique"]["comptes"]["pib"])
    except (KeyError, TypeError, ValueError): return 0.0


def _financer(p, d):
    """12 h : la publicite du jour ( les marches, selon leur caisse, aux medias selon leur audience ), la dotation de
    l audiovisuel public ; le premier du mois, l aide a la presse."""
    w = p.w; L = p.socle.livre
    pib = max(0.0, _pib_hier(p))
    if pib <= 0: return
    budget = PUB_PIB * pib
    poids = np.array([m.aud_personnes * PRIX_CONTACT[m.genre] for m in d.medias])
    if poids.sum() > 0:
        marches = sorted(w.marches.values(), key=lambda x: x.lieu.n)
        caisses = np.array([max(0.0, x.caisse) for x in marches])
        if caisses.sum() > 0:
            for mk, c in zip(marches, caisses.tolist()):
                part = min(budget * c / caisses.sum(), PLAFOND_PUB * c)
                for m, wm in zip(d.medias, (poids / poids.sum()).tolist()):
                    if m.zone is not None and m.zone != mk.lieu.ile: continue
                    x = L.transferer(mk, m, part * wm, "publicite")
                    m.recettes_pub += x; m.recettes_ht_mois += x / (1.0 + TVA_PUB); m.tva_due += x * TVA_PUB / (1.0 + TVA_PUB)
                    p.compter("publicite", x)
    for m in d.medias:
        if type(m) is MediaPublic:
            v = DOTATION_PUBLIC_PIB * pib
            ET.assurer(p, v)
            x = L.transferer(w.gouv, m, v, "dotation_audiovisuel_public"); m.recettes_etat += x; m.recettes_ht_mois += x
    if p.jour % MOIS_J == 0:
        journaux = [m for m in d.medias if m.genre == "journal"]
        tot = sum(m.aud_personnes for m in journaux)
        if tot > 0:
            v = AIDE_PRESSE_PIB * pib * MOIS_J
            ET.assurer(p, v)
            for m in journaux:
                x = L.transferer(w.gouv, m, v * m.aud_personnes / tot, "aide_presse"); m.recettes_etat += x; m.recettes_ht_mois += x


def _eligibles(p):
    """Adultes de 20 a 60 ans, residents, hors metiers publics, enfants et retraites."""
    tb = p.w.table; n = tb.n
    pub = np.array([C.ROLES[r][2] or r in ("enfant", "retraite") for r in PO.ROLES] + [True])
    role = tb.role[:n].astype(np.int64)
    age = _ages(p, np.arange(n))
    return np.nonzero((tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & ~pub[role] & (age >= 20) & (age < 60))[0]


def _embaucher(p, d, x, n_voulu, rng, dans=None):
    """Complete l effectif d un employeur ( salaries inscrits : ils gardent leur metier du moteur )."""
    tb = p.w.table
    vivants = x.employes[(tb.vivant[x.employes] == 1)] if len(x.employes) else x.employes
    for i in set(x.employes.tolist()) - set(vivants.tolist()): d.employes.discard(i)
    manque = n_voulu - len(vivants)
    if manque > 0:
        el = _eligibles(p)
        if dans is not None: el = el[np.isin(tb.domicile[el], dans)]
        el = el[~np.isin(el, np.fromiter(d.employes, np.int64, len(d.employes)))] if d.employes else el
        pris = np.sort(rng.permutation(el)[:manque]) if len(el) else el
        vivants = np.concatenate((vivants, pris)).astype(np.int64)
        d.employes.update(pris.tolist())
    x.employes = vivants


def _effectif(x, N): return max(1, int(round(x.ratio * N)))


def _payer(p, d):
    """16 h : les salaires ( un salarie sur trente chaque jour, son mois ), puis, le jour de l employeur, ses depenses
    du mois : sous-traitance aux marches, importations, dividendes etrangers ; la TVA collectee est reversee."""
    w = p.w; tb = w.table; L = p.socle.livre; K = p.socle.creances
    for x in list(d.operateurs) + list(d.medias):
        sal = _prix_dr(SALAIRE_TELECOM_EUR if isinstance(x, Operateur) else SALAIRE_JOURNALISTE_EUR)
        motif = "salaire_telecom" if isinstance(x, Operateur) else "salaire_media"
        for j, i in enumerate(x.employes.tolist()):
            if (j + x.indice) % MOIS_J != p.jour % MOIS_J or tb.vivant[i] != 1 or tb.menage[i] < 0: continue
            L.payer_ou_devoir(x, _menage(tb, tb.menage[i]), sal, motif, K, p.jour)
            p.compter("salaire_medias", sal)
        if (x.indice + (0 if isinstance(x, Operateur) else 7)) % MOIS_J == p.jour % MOIS_J:
            _depenses_du_mois(p, d, x, sal)
        _reverser_tva(p, x)


def _depenses_du_mois(p, d, x, sal):
    w = p.w; L = p.socle.livre
    ht = x.recettes_ht_mois; x.recettes_ht_mois = 0.0
    tel = isinstance(x, Operateur)
    st = (PART_SOUS_TRAITANCE_TEL if tel else PART_SOUS_TRAITANCE_MEDIA) * ht
    marches = sorted(w.marches.values(), key=lambda m: m.lieu.n)
    poids = d.poids_marche
    for mk, pm in zip(marches, poids):
        if pm > 0 and st > 0: L.transferer(x, mk, st * pm, "sous_traitance_medias")
    imp = (PART_IMPORT_TEL * ht) if tel else (PART_PAPIER * ht if getattr(x, "genre", "") == "journal" else 0.0)
    if imp > 0: L.payer_l_exterieur(x, imp, "equipement_telecom" if tel else "papier_journal")
    if tel:
        charges = sal * len(x.employes) + st + imp
        exces = x.caisse - RESERVE_MOIS * charges
        if exces > 0 and x.part_etrangere > 0:
            L.payer_l_exterieur(x, exces * x.part_etrangere, "dividende_exterieur_telecom")


def _recruter(p, d):
    """Le premier du mois : les effectifs sont completes ( deces, departs ). Les medias recrutent dans la capitale de
    leur zone, les operateurs partout."""
    N = d.pop.sum()
    rng = p.du_jour("medias_embauche")
    for x in d.operateurs: _embaucher(p, d, x, _effectif(x, N), rng)
    for m in d.medias:
        caps = [d.capitale_ile[m.zone]] if m.zone is not None else sorted(d.capitale_ile.values())
        _embaucher(p, d, m, _effectif(m, N), rng, dans=np.array(caps))


# ================================================================== les routines
def _heure(p):
    d = _dom(p)
    _reseau_heure(p, d)
    _lire_journal(p, d)
    _diffusions_dues(p, d)
    if HEURE_EVEIL <= int(p.heure) <= HEURE_COUCHER: _propager(p, d)


def _aube(p):
    d = _dom(p)
    if p.jour % 7 == 0: _matrices(p, d, d_dist(d))
    _recenser(p, d)
    _audiences(d)
    _pannes_du_jour(p, d)
    if p.jour % MOIS_J == 0: _recruter(p, d)


def d_dist(d):
    dist = np.hypot(d.pos[:, None, 0] - d.pos[None, :, 0], d.pos[:, None, 1] - d.pos[None, :, 1])
    meme = np.array([[a == b for b in d.ile_de] for a in d.ile_de])
    dist = np.where(meme, dist, np.inf); np.fill_diagonal(dist, np.inf)
    return dist


def _audiences(d):
    """La portee du jour de chaque media, par lieu : audience de base, credibilite, equipement, zone."""
    un = np.ones(d.L)
    for m in d.medias:
        eq = d.eq_tv if m.genre == "tv" else d.eq_net if m.genre == "site" else un
        zone = un if m.zone is None else np.array([i == m.zone for i in d.ile_de], np.float64)
        a = min(PORTEE_MAX, m.base * (m.cred / m.cred0) ** ELAST_CRED)
        m.portee = a * eq * zone * (d.pop > 0)
        m.cov = np.nonzero((d.pop > 0) & (zone > 0))[0]
        m.aud_personnes = float(np.dot(m.portee, d.pop))


def _matin(p):
    d = _dom(p)
    _statistiques(p, d)


def _rumeurs_du_jour(p): _rumeurs(p, _dom(p))


def _redaction_du_jour(p): _redaction(p, _dom(p))


def _facturer_du_jour(p): _facturer(p, _dom(p))


def _financer_du_jour(p): _financer(p, _dom(p))


def _payer_du_jour(p): _payer(p, _dom(p))


def _soir(p):
    d = _dom(p)
    _noter(p, d)
    _audiences(d)


def _oublier(p):
    """23 h 50 : l oubli de la journee ( demi-vie selon la saillance, divisee apres un dementi ) ; une cellule ou moins
    d une demi-personne s en souvient l a oublie ; un fait que personne ne sait plus et qu aucun media n attend est
    libere, comme tout fait de plus de AGE_MAX_J jours."""
    d = _dom(p); mem = d.mem
    idx = mem.actifs()
    if not len(idx): return
    t = _t(p)
    s = mem.f["saillance"][idx].astype(np.float64)
    T = DEMI_VIE_BASE_J + DEMI_VIE_PENTE_J * s
    T = np.where(np.isnan(mem.f["dementi_t"][idx]), T, T / FACTEUR_OUBLI_DEMENTI)
    f = np.power(0.5, 1.0 / T)
    part = mem.c["part"][idx] * f[:, None]
    pops = np.concatenate((d.pop, np.array(d.taille, np.float64)))
    part[part * pops[None, :] < 0.5] = 0.0
    mem.c["part"][idx] = part
    attend = {e[2] for e in d.file_pub} | {e[2] for e in d.file_verif} | {v[1] for v in d.suivi.values()}
    vide = ~part.any(1)
    vieux = (t - mem.f["t"][idx]) > AGE_MAX_J
    for r, v_, o in zip(idx.tolist(), vide.tolist(), vieux.tolist()):
        if int(mem.f["fid"][r]) in attend: continue
        if o or (v_ and t - mem.f["t"][r] > 1.0):
            mem.liberer(r); p.compter("fait_oublie")


# ================================================================== installation
MOTIFS = (("abonnement_telecom", "achat"), ("abonnement_presse", "achat"), ("publicite", "achat"),
          ("sous_traitance_medias", "achat"), ("equipement_telecom", "achat"), ("papier_journal", "achat"),
          ("salaire_telecom", "remuneration"), ("salaire_media", "remuneration"),
          ("dividende_exterieur_telecom", "revenu_propriete"), ("dotation_audiovisuel_public", "transfert_courant"),
          ("aide_presse", "subvention"), ("fonds_propres_medias", "financier"))
COLONNES_MENAGE = (("tel_equipement", np.int8, 0), ("tel_mobiles", np.int8, 0), ("tel_operateur", np.int8, -1),
                   ("tel_retard", np.int8, 0), ("presse_abos", np.int16, 0))


def installer(p):
    w = p.w; L_ = p.socle.livre
    d = Medias()
    p.domaines[DOMAINE] = d
    dist = _carte(p, d)
    d.table_sujets = dict(SUJETS)
    d.nouvelles = dict(NOUVELLES)
    J = p.socle.journal
    for t_, spec in J.types.items():           # les verdicts et affaires du domaine 21, lus par leur nom
        if spec.domaine == "justice" and spec.niveau == "individuel" and t_ not in d.nouvelles:
            d.table_sujets[t_] = SUJET_JUSTICE; d.nouvelles[t_] = (t_, None)
    d.sujets, d.code_sujet = [], {}
    for s_ in d.table_sujets: _code_sujet(d, s_)
    for m_, nature in MOTIFS: L_.declarer_motif(m_, nature, DOMAINE)
    for t_, champs in (("panne_telecom", ("lieu", "cause")), ("telecom_retabli", ("lieu", "heures")),
                       ("fausse_nouvelle", ("fait", "sujet", "lieu")), ("dementi", ("fait", "sujet", "part"))):
        J.declarer(t_, DOMAINE, "individuel", champs)
    for t_ in ("fait_constate", "fait_oublie", "publication", "verification", "nouvelle_ignoree", "nouvelle_tuee",
               "facture_telecom", "abonnement_suspendu", "publicite", "salaire_medias"):
        J.declarer(t_, DOMAINE, "compte")
    cm = p.colonnes["menage"]
    for nom, dt_, v in COLONNES_MENAGE: cm.ajouter(nom, dt_, v)
    cm.assurer(w.table.menages.n)
    # les operateurs et les medias
    for k, (nom, pm, ratio, etr) in enumerate(OPERATEURS): d.operateurs.append(Operateur(k, nom, pm, ratio, etr))
    bit = 0
    for k, (nom, genre, base, cred, sens, cap, ratio, prix, ligne, pabo) in enumerate(MEDIAS):
        cls = MediaPublic if nom == "tv_publique" else Media
        d.medias.append(cls(k, nom, genre, None, base, cred, sens, cap, ratio, prix, ligne, pabo))
    for ile in d.iles:
        genre, base, cred, sens, cap, ratio, prix, ligne, pabo = PRESSE_REGIONALE
        d.medias.append(Media(len(d.medias), f"presse_{ile.lower()}", genre, ile, base, cred, sens, cap, ratio, prix, ligne, pabo))
    for m in d.medias:
        if m.prix_abo > 0 and m.part_abo > 0:
            if bit >= 15: raise RuntimeError("medias : plus de 15 abonnements dans presse_abos ( int16 )")
            m.bit_abo = bit; bit += 1
    reg = p.socle.registre
    reg.inscrire("operateurs_telecom", "entreprises", _membres_operateurs, "caisse", None, "Operateur")
    reg.inscrire("medias_prives", "entreprises", _membres_medias, "caisse", None, "Media")
    reg.inscrire("audiovisuel_public", "administrations", _membres_public, "caisse", None, "MediaPublic")
    bq = p.domaine("banques")
    rb = p.hasard("medias_banques")
    parts = np.array([b.part for b in bq.banques], np.float64); parts = parts / parts.sum()
    for x in list(d.operateurs) + list(d.medias):
        BQ.ouvrir_compte(p, x, bq.banques[int(rb.choice(len(parts), p=parts))])
    # la population, l equipement, les contacts, le reseau
    d.B = None
    d.groupes, d.taille, d.poids_groupe, d.suit_medias = [], [], [], []
    d.nc = d.L
    d.mem = Memoire(d.nc, len(d.medias))
    d.reseau = Reseau(d.L)
    rng = p.hasard("medias_recensement")
    ids, dom, mg = _residents(p)
    _equiper(p, d, np.unique(mg), rng)
    _matrices(p, d, dist)
    _recenser(p, d)
    _audiences(d)
    pm = np.zeros(len(w.marches))
    marches = sorted(w.marches.values(), key=lambda m: m.lieu.n)
    ids_m = {m.lieu.n: k for k, m in enumerate(marches)}
    for l, q in enumerate(d.pop.tolist()):
        k = ids_m.get(int(d.marche_de[l]))
        if k is not None: pm[k] += q
    d.poids_marche = (pm / pm.sum()).tolist() if pm.sum() > 0 else [1.0 / max(1, len(marches))] * len(marches)
    for o in d.operateurs:
        o.abonnes = int((cm["tel_operateur"][np.unique(mg)] == o.indice).sum())
    # les effectifs et les fonds propres ( deux mois de salaires, venus de l exterieur )
    N = d.pop.sum()
    re = p.hasard("medias_embauche")
    for x in d.operateurs: _embaucher(p, d, x, _effectif(x, N), re)
    for m in d.medias:
        caps = [d.capitale_ile[m.zone]] if m.zone is not None else sorted(d.capitale_ile.values())
        _embaucher(p, d, m, _effectif(m, N), re, dans=np.array(caps))
    for x in list(d.operateurs) + list(d.medias):
        sal = _prix_dr(SALAIRE_TELECOM_EUR if isinstance(x, Operateur) else SALAIRE_JOURNALISTE_EUR)
        L_.recevoir_de_l_exterieur(x, 2.0 * sal * len(x.employes), "fonds_propres_medias")
    rec = p.socle.journal.recents
    d.journal_vu = rec[-1] if rec else None
    d.decideur = p.decideur(POINT_PUBLICATION)
    for h in range(24): p.routine(h, 60, DOMAINE, _heure)
    p.routine(6 + 10 / 60, 60, DOMAINE, _aube)
    p.routine(7.0, 61, DOMAINE, _matin)
    p.routine(8.0, 61, DOMAINE, _rumeurs_du_jour)
    p.routine(HEURE_REDACTION, 61, DOMAINE, _redaction_du_jour)
    p.routine(11.0, 61, DOMAINE, _facturer_du_jour)
    p.routine(12.0, 61, DOMAINE, _financer_du_jour)
    p.routine(16.0, 61, DOMAINE, _payer_du_jour)
    p.routine(22.5, 61, DOMAINE, _soir)
    p.routine(23 + 50 / 60, 61, DOMAINE, _oublier)
    return d


# ================================================================== ce que le domaine donne aux autres
def _cellule(d, x):
    """Un lieu ( identifiant, numero ) ou un groupe ( son nom ) -> numero de cellule."""
    if isinstance(x, (int, np.integer)): return int(x)
    if x in d.n_du_lieu: return d.n_du_lieu[x]
    if x in d.groupes: return d.L + d.groupes.index(x)
    raise KeyError(f"ni lieu ni groupe : {x!r}")


def croyance(p, lieu_ou_groupe, sujet=None, avec_erreur=False, part_min=None):
    """CE QU UN OBSERVER A LE DROIT DE LIRE : ce qu une cellule croit des faits d un sujet ( tous si None ). Une liste
    de { fait, sujet, valeur, lieu, part, appris, age_j, source, confiance, relais }, les plus sus d abord. La valeur
    et le lieu sont CEUX QUI SONT CRUS. `avec_erreur` ajoute la verite ( vrai, erreur de valeur en log, erreur de lieu
    en km ) : pour les portes et les analyses, JAMAIS pour un observer()."""
    d = _dom(p); mem = d.mem
    c = _cellule(d, lieu_ou_groupe)
    pop = d.pop[c] if c < d.L else d.taille[c - d.L]
    pm = (0.5 / max(pop, 1.0)) if part_min is None else part_min
    idx = mem.actifs()
    if sujet is not None:
        k = d.code_sujet.get(sujet)
        if k is None: return []
        idx = idx[mem.f["sujet"][idx] == k]
    idx = idx[mem.c["part"][idx, c] >= pm]
    t = _t(p)
    out = []
    for r in idx[np.lexsort((mem.f["fid"][idx], -mem.c["part"][idx, c]))].tolist():
        lc = int(mem.c["lieu_cru"][r, c]); src = int(mem.c["source"][r, c])
        e = {"fait": int(mem.f["fid"][r]), "sujet": d.sujets[int(mem.f["sujet"][r])],
             "valeur": math.exp(float(mem.c["lv"][r, c])), "lieu": d.lieu_ids[lc] if lc >= 0 else None,
             "part": float(mem.c["part"][r, c]), "appris": float(mem.c["appris"][r, c]),
             "age_j": t - float(mem.c["appris"][r, c]),
             "source": NOMS_SOURCES[src] if 0 <= src < MEDIA0 else (d.medias[src - MEDIA0].nom if src >= MEDIA0 else None),
             "confiance": float(mem.c["conf"][r, c]), "relais": float(mem.c["relais"][r, c]),
             "dementi": not np.isnan(mem.f["dementi_t"][r])}
        if avec_erreur:
            vrai = bool(mem.f["vrai"][r]); lv = float(mem.f["lv_vrai"][r])
            e["vrai"] = vrai
            e["erreur_valeur"] = abs(float(mem.c["lv"][r, c]) - lv) if vrai else None
            lt = int(mem.f["lieu"][r])
            e["erreur_lieu_km"] = float(np.hypot(*(d.pos[lc] - d.pos[lt])) / 1000.0) if lc >= 0 else None
        out.append(e)
    return out


def rumeur_locale(p, lieu, sujet):
    """Pour un observer() : ce qui se dit dans ce lieu d un sujet. { part ( la plus haute ), valeur crue du fait le plus
    su, age_j, n ( faits du sujet sus ), confiance }. Tout a zero si rien ne se dit."""
    cs = croyance(p, lieu, sujet)
    if not cs: return {"part": 0.0, "valeur": 0.0, "age_j": 0.0, "n": 0, "confiance": 0.0}
    e = cs[0]
    return {"part": e["part"], "valeur": e["valeur"], "age_j": e["age_j"], "n": len(cs), "confiance": e["confiance"]}


def sait(p, ids, fait):
    """Les individus qui savent un fait ( booleens, pour des numeros d habitants ) : le tirage fixe de leur menage sous
    la part de leur lieu. Aucune memoire par habitant."""
    d = _dom(p); tb = p.w.table
    ids = np.asarray(ids, np.int64)
    r = d.mem.par_fid.get(int(fait))
    if r is None: return np.zeros(len(ids), bool)
    dom = tb.domicile[ids].astype(np.int64); mg = tb.menage[ids].astype(np.int64)
    ok = (dom >= 0) & (mg >= 0) & (tb.vivant[ids] == 1)
    part = np.where(ok, d.mem.c["part"][r, np.maximum(dom, 0)], 0.0)
    return ok & (_tirage(p.w.graine, np.maximum(mg, 0), int(fait)) < part)


def _tirage(graine, menages, fid):
    """Un uniforme fixe par ( graine, menage, fait ) : le melange splitmix64, sans etat."""
    with np.errstate(over="ignore"):
        x = (np.asarray(menages, np.uint64) * np.uint64(0x9E3779B97F4A7C15)) ^ np.uint64(int(graine) % (2 ** 64))
        x ^= np.uint64(fid * 0xD1B54A32D192ED03 % (2 ** 64))
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(31)
    return (x >> np.uint64(11)).astype(np.float64) / float(2 ** 53)


def inscrire_groupe(p, nom, poids=None, taille=1000, suit_medias=True):
    """Domaine 26 ( un camp, un etat-major ), 24 ( un parti ) : une cellule de croyance de plus. `poids` : { lieu :
    poids } ou se trouvent ses membres ( il apprend de ceux qu il cotoie ) ; `taille` : ses membres ; `suit_medias` :
    s il regarde les medias du pays. Rend le numero de sa cellule."""
    d = _dom(p)
    if nom in d.groupes or nom in d.n_du_lieu: raise ValueError(f"groupe {nom!r} deja une cellule")
    if not taille >= 1: raise ValueError("taille d un groupe : au moins 1")
    W = np.zeros(d.L)
    for l, x in (poids or {}).items(): W[_cellule(d, l)] += float(x)
    if W.sum() > 0: W /= W.sum()
    d.groupes.append(nom); d.taille.append(float(taille)); d.poids_groupe.append(W); d.suit_medias.append(bool(suit_medias))
    d.nc += 1; d.mem.cellules(d.nc)
    return d.nc - 1


def informer(p, groupe, fait, part=1.0, valeur=None, lieu=None, confiance=0.8, source=RENSEIGNEMENT):
    """Domaine 26 : un rapport ( renseignement, observation ) fait savoir un fait a un groupe, avec SA valeur et SON lieu
    ( une erreur de position est un lieu faux ). La date d apprentissage est maintenant."""
    d = _dom(p); mem = d.mem
    r = mem.par_fid.get(int(fait))
    if r is None: raise KeyError(f"fait {fait} oublie ou inconnu")
    c = _cellule(d, groupe)
    lv = float(mem.f["lv_vrai"][r]) if valeur is None and mem.f["vrai"][r] else math.log(max(float(valeur or 1.0), VALEUR_MIN))
    lc = int(mem.f["lieu"][r]) if lieu is None else _cellule(d, lieu)
    pops = np.concatenate((d.pop, np.array(d.taille, np.float64)))
    _ajouter(mem.c, np.array([r]), np.array([c]), np.array([float(part)]), lv, 0.0, confiance, lc, source, _t(p), pops)


def declarer_nouvelle(p, type_, sujet, champ=None, spec=None):
    """Un domaine installe apres celui-ci ( 24, 25 a 27 ) fait d un de ses evenements individuels une nouvelle :
    `sujet` de SUJETS, ou nouveau avec `spec` ( valence, gouvernemental, base, pente, mode, temoins, agregation )."""
    d = _dom(p)
    if sujet not in d.table_sujets:
        if spec is None or len(spec) != 7: raise ValueError(f"sujet nouveau {sujet!r} : spec de 7 champs exigee")
        d.table_sujets[sujet] = tuple(spec)
    d.nouvelles[type_] = (sujet, champ)


def fait(p, fid):
    """La verite d un fait ( pour les portes et les domaines qui l ont pose ; jamais un observer() )."""
    d = _dom(p); r = d.mem.par_fid.get(int(fid))
    if r is None: return None
    F = d.mem.f
    return {"fait": int(fid), "sujet": d.sujets[int(F["sujet"][r])], "lieu": d.lieu_ids[int(F["lieu"][r])],
            "valeur": math.exp(float(F["lv_vrai"][r])) if F["vrai"][r] else None, "t": float(F["t"][r]),
            "vrai": bool(F["vrai"][r]), "officiel": bool(F["officiel"][r]), "saillance": float(F["saillance"][r]),
            "dementi": not np.isnan(F["dementi_t"][r]), "publie_t": float(F["publie_t"][r])}


def part_nationale(p, fid):
    """La part des residents du pays qui savent ce fait."""
    d = _dom(p); r = d.mem.par_fid.get(int(fid))
    if r is None: return 0.0
    return float(d.mem.c["part"][r, :d.L].astype(np.float64) @ d.pop / max(d.pop.sum(), 1.0))


def telecom_ok(p, lieu):
    """Le reseau telephonique et internet marche-t-il dans ce lieu ( domaines 17, 18 : l appel au 112 ) ?"""
    d = _dom(p); return bool(d.reseau.ok[_cellule(d, lieu)])


def equipement(p, lieu):
    """Parts des residents equipes : television, internet a la maison ( fixe ou 4G ), telephone ( fixe ou mobile )."""
    d = _dom(p); c = _cellule(d, lieu)
    return {"tv": float(d.eq_tv[c]), "internet": float(d.eq_net[c]), "telephone": float(d.eq_tel[c])}


def medias(p):
    """Domaines 23, 24 : { nom : ( genre, zone, ligne, audience du jour en personnes, credibilite ) }."""
    return {m.nom: (m.genre, m.zone, m.ligne, m.aud_personnes, m.cred) for m in _dom(p).medias}


def exposition(p, lieu):
    """Domaines 23, 24 : la portee de chaque media dans ce lieu ( part des residents touches par jour )."""
    d = _dom(p); c = _cellule(d, lieu)
    return {m.nom: float(m.portee[c]) for m in d.medias}


def credibilite(p, media):
    d = _dom(p)
    return next(m.cred for m in d.medias if m.nom == media or m.indice == media)


def climat(p, lieu_ou_groupe):
    """Domaine 23 ( moral ) : pour chaque sujet cru, somme de part x saillance annoncee, et la valence du sujet ( ce que
    la cellule croit, pas ce qui est ) : { sujet : ( intensite, valence ) }."""
    d = _dom(p); out = {}
    for e in croyance(p, lieu_ou_groupe):
        s = saillance(d.table_sujets, e["sujet"], e["valeur"]) * (0.3 if e["dementi"] else 1.0)
        i, v = out.get(e["sujet"], (0.0, d.table_sujets[e["sujet"]][0]))
        out[e["sujet"]] = (i + e["part"] * s, v)
    return out


def anomalies(p):
    """Les croyances datees AVANT leur fait, les parts hors [0 ; 1], les cellules qui savent sans date : [ ( type,
    fait, cellule ) ]. Vide dans un monde sain."""
    d = _dom(p); mem = d.mem
    idx = mem.actifs(); out = []
    if not len(idx): return out
    P_ = mem.c["part"][idx]; A_ = mem.c["appris"][idx]; T_ = mem.f["t"][idx][:, None]
    for f, c in zip(*np.nonzero((P_ > 0) & (A_ < T_ - 1e-9))): out.append(("antidatee", int(mem.f["fid"][idx[f]]), int(c)))
    for f, c in zip(*np.nonzero((P_ < 0) | (P_ > 1.0 + 1e-6))): out.append(("part_hors_bornes", int(mem.f["fid"][idx[f]]), int(c)))
    for f, c in zip(*np.nonzero((P_ > 0) & np.isnan(A_))): out.append(("sans_date", int(mem.f["fid"][idx[f]]), int(c)))
    return out


# ================================================================== le scenario de la publication ( porte de decision )
SUJETS_SCENARIO = ("incendie", "accident_route", "greve", "faillite", "coupure_eau", "epidemie", "meurtre", "penurie",
                   "hopital_sature", "route_fermee")


def scenario_publication(jours=10, mode="hasard", graine=5, echelle=5, par_jour=12, part_faux=0.35):
    """Le monde avec ce domaine, ou chaque matin a 8 h naissent `par_jour` nouvelles ( une part fausses ) dans des lieux
    tires au prorata de la population : les redactions decident a 9 h ( mode donne ), la rumeur et les dementis vivent
    avec les fonctions du domaine. Rend ( decideur, pays ). Des nouvelles posees et pas celles du monde : a 2 500
    habitants, le monde n en fait naitre que quelques-unes par jour."""
    from . import essais as ES
    w, p = ES.monde([DOMAINE], graine, echelle, modes={"publication": mode})
    d = _dom(p)
    rng = np.random.default_rng(graine)
    for _ in range(jours):
        while not (p.w.heure >= 8.0 and p.w.heure < 8.0 + 1e-6 + C.MINUTES_PAR_PAS / 60.0):
            w.pas_suivant()
        hab = np.nonzero(d.pop > 0)[0]; pp = d.pop[hab] / d.pop[hab].sum()
        for _ in range(par_jour):
            sujet = SUJETS_SCENARIO[int(rng.integers(len(SUJETS_SCENARIO)))]
            lieu = int(hab[rng.choice(len(hab), p=pp)])
            v = float(np.exp(rng.normal(1.0, 1.0)))
            if rng.random() < part_faux: fabriquer_rumeur(p, sujet, lieu, v, personnes=int(rng.integers(3, 30)), rng=rng)
            else: constater(p, sujet, lieu, v, temoins=int(rng.integers(5, 60)), rng=rng)
        for _ in range(C.PAS_PAR_JOUR - 1): w.pas_suivant()
    return d.decideur, p
