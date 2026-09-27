"""DOMAINE 24 - POLITIQUE : PARTIS, OPINION, SONDAGES, ELECTIONS, GOUVERNEMENT ELU, CONTESTATION.

FICHE
1. Classes. PartiPolitique ( une liste : famille, programme borne sur quatre axes - impots, depense sociale, ordre,
   immigration -, caisse, adherents ; une association, secteur S.15, famille `partis_politiques` ), Scrutin ( une
   election legislative : inscrits, votants ( emargements ), blancs et nuls, voix par bureau et par liste, sieges,
   prime ), Executif ( le gouvernement issu du Parlement : listes, chef, programme pondere par les sieges, voix a
   l election ), ContexteCampagne, Politique ( l etat du domaine ). Colonnes par habitant : pol_ident ( l
   identification partisane stable, -1 aucune, -2 pas encore tiree ), pol_ideo ( la position gauche-droite, sur 250 ),
   pol_adh ( adherent de son parti ), pol_emarge ( le numero du dernier scrutin ou il a signe la liste d emargement ).
   5 octets par habitant, aucun par menage : 250 Mo a 50 millions. LE VOTE EST SECRET : aucune colonne ne dit pour
   qui un habitant a vote ; seuls l emargement ( qui a vote ) et les voix par bureau existent, comme dans la loi.
   L OPINION est une representation par CELLULE : intentions[ lieu, groupe, liste ] ( somme des probabilites de vote ),
   votants attendus et inscrits par ( lieu, groupe ) ; groupe = classe ( 3 ) x age ( 17-34, 35-54, 55 et plus ).
   Memoire : lieux x 9 x 7 reels, independante de la population ( 420 lieux : 26 000 reels, 0,2 Mo ). L intention d un
   electeur n est pas gardee : elle se recalcule de ses colonnes et de celles de son lieu ( `probabilites` ).
2. Invariants et ce que le domaine detient. ARGENT : les caisses des partis, par le grand livre seulement ( famille
   `partis_politiques`, rapprochement nul ) : financement public ( Etat -> partis, cle des voix ), cotisations
   ( menages -> partis, au-dela d une reserve de 14 jours de nourriture ), depenses de campagne ( partis -> marches du
   lieu ). Aucun bien. SCRUTIN : dans chaque bureau ( un lieu ), voix des listes + blancs et nuls = votants ( les
   signatures ) <= inscrits ; le total des votants = les emargements de la colonne ; les sieges sont exactement ceux
   de la loi electorale appliquee aux voix valides ( `anomalies` : un vote sans electeur, un siege sans vote, une
   signature perdue se voient ). REGLE 3 : l opinion lit les CROYANCES du domaine 22 ( griefs contre le
   gouvernement, peur du crime, inquietude sociale et economique : ce que chaque lieu croit, jamais ce qui est ), le
   moral du domaine 23, et la situation PROPRE de l electeur ( chomage, faim de son menage, impot preleve, pauvrete :
   ce qu il vit, qu il sait ). Un fait vrai que personne ne sait ne pese rien ; une rumeur fausse crue pese.
   LE GOUVERNEMENT ELU AGIT PAR LE CATALOGUE BORNE DU DOMAINE 6 ( `ET.appliquer` ), jamais a la main.
3. Decision `campagne` ( chaque liste, dans chaque lieu habite d au moins 10 electeurs, tous les 3 jours - une tournee -
   a 9 h ) : rien, economie, social, ordre, attaque ( le gouvernement sortant ). Traits ( ce que le parti sait ) : son
   dernier sondage publie, son resultat dans ce bureau au dernier scrutin ( public ), les griefs, la peur du crime,
   l inquietude sociale que ce lieu croit ( sa section locale l entend ), le moral du lieu, s il gouverne, ses axes
   social et ordre, la periode officielle de campagne, sa caisse, la taille du lieu. Note ( horizon 3 jours, la
   tournee ) : chaque soir, pour CETTE liste dans CE lieu, les points d intention gagnes depuis la veille du choix, moins
   le cout d une tournee ( 0,3 point ). Pourquoi pas le vote de l electeur : un vote n est decisif qu avec une
   probabilite de l ordre de 1 sur 10 millions ( Gelman, Silver et Edlin 2012 ) ; aucune consequence dans le monde ne
   depend de ce choix, et une note de " satisfaction " serait une tautologie. La campagne, elle, change l intention de
   ceux qu elle touche. Regle : caisse vide -> rien ; opposition et griefs >= 0,15 -> attaque ; sinon le theme de son
   axe le plus fort ( social ou ordre ). Temoin : rien ( le parti qui ne fait pas campagne ). MESURE DU 26/09
   ( test_decision, 12 jours de campagne, 2 500 habitants ) : au hasard, part du choix 0,376, p 0,005 ; notes rien -0,69,
   economie -0,04, social -0,02, ordre -0,04, attaque +0,03 : le choix qui compte est de faire campagne ou non ( les
   preoccupations d un pays calme departagent peu les themes ). Les campagnes etant relatives, les moyennes de mondes
   differents ne se comparent pas ( regle -0,21, temoin -0,01 : si personne ne fait campagne, personne ne perd ).
4. Evenements. Individuels : sondage, dissolution, resultats_election, investiture, echec_formation,
   crise_gouvernement, manifestation, greve_generale. Comptes : cotisation_parti, financement_partis,
   depense_campagne, decision_campagne, participants_manifestation. Nouvelles ( domaine 22 ) : sondage, election,
   changement_gouvernement, crise_politique, manifestation.
5. Liens. Etat ( 6 ) : `appliquer` ( TVA, IR, IS, salaires publics, controle fiscal, budget de la defense,
   subventions : toujours bornes ), `publications` ( la faim publiee ), le budget ( recettes ordinaires, base du
   financement des partis ), `assurer` avant chaque paiement de l Etat, les colonnes fisc_revenu et fisc_retenu ( l impot
   preleve ). Medias ( 22 ) : la memoire des croyances ( lue en colonnes, identique a `climat` : porte ),
   `declarer_nouvelle` ( les evenements du domaine deviennent des faits que les redactions publient ). Culture ( 23 ) :
   le moral individuel ( cul_moral ) et du lieu, `risque_greve` ( la taille d une manifestation ). Population ( 1 ) :
   ages, menages, faim de la semaine ( faim7 ), filiation ( l identification se transmet par la mere ). Banques ( 2 ) :
   `ouvrir_compte` de chaque parti. Travail ( 4, optionnel ) : `declencher_greve` ( greve generale politique de 24 h
   des branches publiques, ADEDY ). Justice ( 21, optionnel ) : ses affaires, devenues croyances par le domaine 22,
   font la peur du crime. Ne remplace aucune methode du moteur ; ne touche pas w.cerveau ( le gouvernement du domaine 6,
   regles ou code de l agent codeur, reste l administration quotidienne ; l Executif elu ajoute son paquet de lois a
   l investiture et sa regle du matin, par le meme catalogue borne ). API en fin de fichier : intentions,
   probabilites, sonder, convoquer, repartir_sieges, sieges_pour, former_coalition, executif, parlement, legitimite,
   politique_de_defense ( domaine 25 ), lois_du_programme, croyances_politiques, anomalies.
6. Portes : tests_d24_politique.py ( 12 / 12 le 26/09 ). PAYS ENTIER ( les 24 domaines, 2 000 habitants, 15 jours,
   26/09 ) : les griefs crus montent a 1,7 par lieu ( delestages quotidiens du domaine 11 : 0,72 ; restrictions d eau :
   0,45 ; greves, delits ) et le sortant tombe de 40 % a 10 % ; aucun parti n a de majorite au scrutin du 9e jour, le
   gouvernement expedie les affaires courantes. Ce que le modele lit est vrai dans ce monde ; le regime de demarrage des
   autres domaines est a regarder ( voir le rapport ).
7. Arma : aucun corps propre. Un bureau de vote est l ecole ou la mairie du lieu ( batiments du domaine 13 ) ; un
   manifestant a le corps de son habitant ( les rassemblements ne sont pas incarnes : arma_preuve = None ).
8. Cout. Chaque soir : une passe vectorisee sur les electeurs ( 7 utilites, une probabilite de vote, 10 bincount ), par
   blocs de 2^20 electeurs ( ~ 200 Mo de travail par bloc ; a 50 millions, les numeros des electeurs et les colonnes
   des menages ajoutent ~ 0,8 Go transitoires ) ; la lecture des croyances en ( faits x lieux ). Le matin : une decision par ( liste, lieu ) tous les 3 jours, un paiement par tournee. A midi : un
   sondage de 1 000 personnes au plus ( ses seules probabilites ), les cotisations d un trentieme des adherents. Le jour
   du scrutin : une passe sur les electeurs. Lineaire en habitants. MESURE DU 26/09 ( test_cout, coeur Rust, 10 000
   habitants ) : 10 ms par jour, 3,4 % d une journee du moteur seul ( 0,30 s ) ; installation 0,39 s a 10 000 habitants,
   4,0 s a 100 000 ( x10,2 : le calage des constantes, 90 passes vectorisees ). A 50 millions : ~ 50 s par soir ( a
   mesurer ), autant le jour du scrutin."""
import collections, importlib, itertools, math
import numpy as np
from .. import config as C, population as PO, gouvernement as G
from ..socle import decision as D
from . import pays as P, d02_banques as BQ, d06_etat as ET, d22_medias as ME, d23_culture as CU

DOMAINE = "politique"
EUROS = P.EUROS_PAR_DRACHME
JOURS_AN = 365.0
MOIS_J = 30
BLOC = 1 << 20                     # electeurs traites ensemble : la memoire de travail reste bornee a 50 millions

# ================================================================== les partis ( noms fictifs, familles grecques )
# Parts de voix valides aux legislatives du 25 juin 2023 ( ministere de l Interieur ) : Nouvelle Democratie 40,56 %,
# SYRIZA 17,83 %, PASOK 11,84 %, KKE 7,69 %, Spartiates 4,68 % + Solution grecque 4,44 % + Niki 3,70 % ( droite
# nationaliste et religieuse, ici une liste ), Plefsi 3,17 %, MeRA25 2,46 %, autres. Axes dans [0 ; 1] : impots ( 1 :
# imposer plus ), social ( 1 : depenser plus ), ordre ( 1 : plus de police et de peines ), immigration ( 1 : restreindre ).
# Positions : ordres de grandeur du Chapel Hill Expert Survey 2019 pour les familles grecques ( a verifier ).
# ( nom, famille, impots, social, ordre, immigration, part cible, liste deposee, refuse toute coalition )
PARTIS = (("front_populaire_uni", "communiste", 0.80, 1.00, 0.10, 0.10, 0.077, True, True),
          ("gauche_nouvelle", "gauche_radicale", 0.70, 0.85, 0.25, 0.20, 0.178, True, False),
          ("rassemblement_social", "centre_gauche", 0.55, 0.70, 0.45, 0.40, 0.118, True, False),
          ("mouvement_ecologiste", "ecologiste", 0.50, 0.60, 0.35, 0.25, 0.035, True, False),
          ("union_liberale", "centre_droit", 0.35, 0.45, 0.70, 0.65, 0.406, True, False),
          ("voix_nationale", "droite_nationaliste", 0.30, 0.50, 0.90, 0.95, 0.128, True, False),
          ("divers", "petites_listes", 0.50, 0.50, 0.50, 0.50, 0.058, False, True))
GOUVERNEMENT_INITIAL = "union_liberale"   # le gouvernement de l installation ( comme la ND en 2023 )
AXES = ("impots", "social", "ordre", "immigration")
ECART_COALITION = 0.30             # ecart gauche-droite maximal dans une coalition ( a calibrer )

# ================================================================== la loi electorale
# Constitution grecque, art. 51 al. 1 : de 200 a 300 deputes, nombre fixe par la loi ( 300 depuis 1952 ) ; art. 51
# al. 5 : le vote est obligatoire, les sanctions ont ete abolies ( loi 3811/2009, a verifier ) ; art. 53 : legislature
# de 4 ans ; art. 37 : trois mandats exploratoires, puis dissolution ; art. 41 : elections anticipees.
# Loi 4804/2021 ( appliquee le 25 juin 2023 ) : seuil de 3 % des voix valides du pays ; le premier parti a 25 % ou plus
# recoit une prime de 20 sieges, plus un par 0,5 % au-dessus de 25 %, au plus 50 ( a 40 % ) ; les autres sieges se
# repartissent a la proportionnelle entre les listes au-dessus du seuil ( quotient de Hare, plus forts restes ).
# Loi 4406/2016 ( 21 mai 2023 ) : la meme proportionnelle, sans prime.
LOIS = ("4804/2021", "4406/2016")
SEUIL_LISTE = 0.03
PRIME_MIN, PRIME_MAX, PRIME_SEUIL, PRIME_PAS, PRIME_PLAFOND = 20, 50, 0.25, 0.005, 0.40
SIEGES_GRECE = 300
POPULATION_GRECE = 10_432_481      # recensement ELSTAT 2021
# Nombre de sieges d un pays plus petit : la loi de la racine cubique ( Taagepera 1972, Social Science Research 1 :
# 385-401 : la taille d une assemblee suit la racine cubique de la population ), calee sur la Grece ( 300 pour
# 10,4 millions : 1,373 x P^(1/3) ), bornee par la Constitution a [ 200 ; 300 ]. Un monde de 2 500 a un million
# d habitants a donc 200 sieges ( le minimum constitutionnel ), la prime devient 13 a 33 sieges ( la meme part ).
# Pourquoi pas moins : la Constitution copiee l interdit, et la prime de 20 a 50 sieges n a de sens qu en centaines ;
# pourquoi pas une personne par siege : les deputes ne sont pas des habitants ( 200 deputes a 2 500 habitants
# videraient les ateliers ) - un siege est une part du Parlement, pas un corps.
SIEGES_MIN, SIEGES_MAX = 200, 300
AGE_VOTE = 17                      # loi 4406/2016 : electeur l annee de ses 17 ans ( ici : 17 ans revolus )
P_BLANC_NUL = 0.02                 # blancs et nuls, ~ 2 % des votants en 2023 ( a verifier )
DUREE_LEGISLATURE_J = 4 * 365 + 1
AGE_LEGISLATURE_J = 820            # jours depuis le dernier scrutin a l installation ( a calibrer )
CAMPAGNE_J = 30                    # de la dissolution au scrutin ( elections de 2019 et 2023 : ~ 30 jours )
NOUVELLE_ELECTION_J = 28           # apres l echec des mandats ( 21 mai -> 25 juin 2023 : 35 jours )
MANDAT_J = 1                       # investiture le lendemain d une majorite ou d un accord
HEURE_SCRUTIN = 19.0               # les bureaux ferment a 19 h ; le depouillement suit

# ================================================================== l opinion ( modele de vote probabiliste, a calibrer )
# Utilite d une liste k pour l electeur i ( logit multinomial ; Adams, Merrill et Grofman 2005 ) :
#   constante_k + A x [ identifie a k ] - B x | ideologie - position_k | + SOC x situation x ( social_k - 0,5 )
#   + C x ( campagne ( k, lieu ) - campagne moyenne des listes dans le lieu ) + [ k gouverne ] x ( - G x griefs crus du
#   lieu - GL x griefs de la legislature - E x economie crue + M x ( moral du lieu - 0,6 ) - S x situation )
# Les constantes sont calees a l installation pour que les parts attendues soient celles de juin 2023. La campagne est
# relative : deux listes qui font autant campagne dans un lieu ne s y prennent rien ( les effets de campagne se
# neutralisent, Gelman et King 1993 ) ; l attaque du sortant est un theme de campagne, sans degat a part.
P_IDENTIFIE = 0.45                 # part des electeurs proches d un parti ( ELNES 2019 : ~ 50 %, a verifier )
TRANSMISSION = 0.5                 # un enfant prend l identification de sa mere ( Jennings et Niemi 1968, a calibrer )
SD_IDEO_IDENT, SD_IDEO = 0.10, 0.18
IDEO_CLASSE = (0.08, 0.0, -0.04)   # aisee, moyenne, populaire : un vote de classe faible en Grece ( a calibrer )
A_IDENT = 2.0
B_IDEO = 6.0
B_DIVERS = 0.5                     # les petites listes attirent de partout
SOC_SITU = 1.5
S_SITU = 1.0
G_GRIEF, G_CAP = 1.0, 2.0
G_LENT, TAU_LENT_J = 0.5, 30.0     # le vote retrospectif : les griefs de la legislature ( Fiorina 1981 )
M_MORAL = 2.0
MORAL_REF = 0.60
C_CAMP = 0.25                      # 26/09 : a 0,10 le gain d une tournee ( ~ 0,33 point ) egalait son cout ( 0,3 point ) et
                                   # la note ne dependait presque plus du choix ( epsilon carre 0,012 a 0,031 selon la
                                   # graine ) ; a 0,25, une liste qui cesse de faire campagne la ou les autres continuent
                                   # perd ~ 0,7 point en 3 jours ( ordre de grandeur des effets de terrain, a calibrer )
DEMI_VIE_CAMPAGNE_J = 5.0
# Situation propre ( 0 a ~ 2 ) : chomeur, faim de son menage sur 7 jours, impot preleve au-dela de 10 % de son revenu,
# menage sous 3 jours de nourriture.
K_CHOMAGE, K_FAIM, K_IMPOT, K_PAUVRE = 0.6, 0.8, 0.4, 0.3
TAUX_IMPOT_REF, TAUX_IMPOT_PLEIN = 0.10, 0.20
JOURS_PAUVRE = 3.0
# Participation ( logit ) : ELNES 2019 et 2023, jeunes moins votants ( a calibrer ) ; 60 % de votants ( abstention
# reelle ~ 40 % : les listes grecques gonflees par l emigration donnent 47 % en juin 2023 ).
PARTICIPATION = 0.60
T_AGE = (-0.5, 0.0, 0.3)           # 17-34, 35-54, 55 et plus
T_CLASSE = (0.3, 0.15, 0.0)
T_IDENT = 0.8
T_MOBIL, T_MOBIL_MAX = 0.01, 0.2   # la campagne mobilise un peu ( Gerber et Green 2000 )
T_ALIEN = 2.0                      # un moral bas eloigne des urnes
AGES_GROUPE = (35.0, 55.0)
GROUPES = 9

# ================================================================== les croyances qui font l opinion ( domaine 22 )
SUJETS_ORDRE = ("meurtre", "vol", "contrebande")
SUJETS_ECO = ("chomage", "licenciements", "faillite", "prix", "prix_mondiaux", "impots", "dette", "devaluation",
              "faillite_banque", "taux")
SUJETS_SOCIAL = ("mort_de_faim", "penurie", "hopital_sature", "penurie_medicaments", "expulsion", "epidemie")
# La statistique publique ( d22.STATS : chomage, prix, dette, faim ) est publiee chaque mois QUEL QUE SOIT son niveau,
# avec une saillance fixe : compter sa publication comme un grief ferait de chaque bulletin mensuel une crise ( mesure du
# 26/09 : les griefs passaient de 0,09 a 0,55 en cinq jours, sans rien de neuf dans le pays ). Ce qui pese, c est la
# VALEUR crue ( vote economique sociotropique, Kinder et Kiewiet 1981 ) : le chomage cru au-dela de 11 % ( Grece 2023 ),
# la hausse des prix crue au-dela de 2 % depuis la base de l indice. Ordres de grandeur ( Nannestad et Paldam 1994,
# fonctions de popularite ) : un point d inflation ou de chomage de plus coute au sortant de 0,5 a 1 point de
# popularite ; a ~ 25 % de part, un point de part vaut ~ 0,05 d utilite : 0,03 d utilite par point d inflation, 0,025
# par point de chomage ( a calibrer ).
SUJETS_STATS = tuple(s for s, _, _, _ in ME.STATS)
CHOMAGE_REF, K_CHOMAGE_CRU = 11.0, 0.025
INFLATION_REF, K_INFLATION_CRUE = 2.0, 0.03
E_SOCIO = 1.0
GRIEFS, ORDRE_, ECO_, SOCIAL_, SOCIO_ = range(5)
NOUVELLES = (("sondage", "sondage", "score_gouvernement", (0.0, True, 0.30, 0.0, "log", 0, "max")),
             ("resultats_election", "election", "participation", (0.0, True, 0.90, 0.0, "log", 0, "max")),
             ("dissolution", "election", None, (0.0, True, 0.90, 0.0, "log", 0, "max")),
             ("investiture", "changement_gouvernement", None, (0.1, True, 0.80, 0.0, "log", 0, "max")),
             ("crise_gouvernement", "crise_politique", None, (-0.5, True, 0.60, 0.0, "log", 0, "max")),
             ("manifestation", "manifestation", "participants", (-0.2, False, 0.15, 0.10, "log", 30, "somme")))
# Une manifestation est la CONSEQUENCE des griefs, pas un grief de plus : declaree gouvernementale, elle nourrissait les
# griefs qui la faisaient naitre ( pays entier, 26/09 : sujet manifestation a 3,8 par lieu au 15e jour, le sortant a
# 3 % ). Elle reste une nouvelle negative ( le moral du domaine 23 la lit ), hors des griefs politiques.

# ================================================================== les sondages
# Les instituts grecs ( Metron Analysis, Pulse, MRB, Marc... ) interrogent ~ 1 000 a 1 200 personnes ; le resultat
# publie est l estimation du vote ( parts des intentions exprimees ). Une fois par semaine, tous les deux jours en
# campagne ( a calibrer ). Le cout des instituts n est pas modelise ( aucune caisse ). Interdiction de publier la
# veille du scrutin ( a verifier ).
TAILLE_SONDAGE = 1000
Z95 = 1.959964

# ================================================================== l argent des partis
# Loi 3023/2002 art. 2 ( a verifier, les baisses de la crise ne sont pas modelisees ) : financement ordinaire annuel de
# 1,02 pour mille des recettes ordinaires de l Etat ; 90 % aux partis representes, au prorata des voix ; 10 % aux
# listes de 1,5 % et plus sans siege ; en annee electorale, 0,2 pour mille de plus, meme cle. Paye par mois.
TAUX_FINANCEMENT = 1.02e-3
SUPPLEMENT_ELECTORAL = 0.20e-3
PART_REPRESENTES = 0.90
SEUIL_FINANCEMENT = 0.015
DOTATION_INITIALE_MOIS = 6         # la reserve des partis a l installation : six mois de financement, payes par l Etat
P_ADHERENT = 0.07                  # part des identifies adherents : ~ 3 % des electeurs ( a calibrer )
COTISATION_EUR = 2.0               # par mois ( a calibrer : quelques euros, davantage au parti communiste )
RESERVE_COTISATION_J = 14
# Campagne : 0,015 euro par electeur et par jour de tournee a pleine intensite ( 2,5 euros par electeur pour 30 jours
# et six listes : ordre de grandeur des depenses declarees en 2019, a verifier ) ; hors campagne officielle, les
# sections militent a un quart ( a calibrer ).
COUT_CAMPAGNE_EUR = 0.015
INTENSITE_HORS_CAMPAGNE = 0.25
RESERVE_PARTI_MOIS = 1.0           # hors campagne, un parti garde un mois de financement

# ================================================================== la decision `campagne`
RIEN, ECONOMIE, SOCIAL, ORDRE, ATTAQUE = range(5)
THEMES = ("rien", "economie", "social", "ordre", "attaque")
TOURNEE_J = 3
ELECTEURS_MIN_CAMPAGNE = 10
EFFET_BASE = 0.3                   # une tournee se voit, quel que soit son theme ; le reste depend de l accord
AFFINITE_ECONOMIE = 0.6
COUT_POINTS = 0.3                  # le prix d une tournee, en points d intention ( la note )
SEUIL_ATTAQUE = 0.15

# ================================================================== le gouvernement elu ( a calibrer )
# Le paquet de lois de l investiture : ecart des axes du programme a celui du gouvernement de l installation, fois une
# pente ; chaque cible est bornee par le domaine 6 ( et refusee par lui sinon ).
PENTE_TVA, PENTE_IR, PENTE_IS, PENTE_SALAIRES = 0.08, 0.15, 0.10, 0.15
PENTE_CONTROLE_IMPOTS, PENTE_CONTROLE_ORDRE, PENTE_DEFENSE = 0.40, -0.20, 0.30
SOCIAL_SUBVENTION = 0.60           # un programme social subventionne les menages pauvres des que la faim se publie
FAIM_SUBVENTION = 5.0              # menages sans nourriture publies, pour 500 habitants
QUITTER = 0.6                      # un partenaire quitte la coalition quand ses intentions tombent sous 60 % de ses voix
GRACE_J = 90                       # ... pas avant trois mois de gouvernement ( l etat de grace, a calibrer )

# ================================================================== la contestation ( a calibrer )
G_MANIF, G_MANIF_ECHELLE = 0.20, 0.30
R_MANIF = 0.03                     # au plus 3 % des adultes d un lieu dans la rue ( Syntagma 2011 : ~ 2 % d Athenes )
MANIF_MIN = 3
G_GREVE = 0.30                     # griefs crus du pays qui font appeler une greve generale de 24 h
GREVE_ESPACEMENT_J = 30
ROLES_ADEDY = ("enseignant", "medecin", "infirmier")
POP_MAJEUR = 18                    # manifester : un adulte

POPCOUNT = np.array([bin(i).count("1") for i in range(256)], np.int64)


# ================================================================== les classes
class PartiPolitique:
    """Un parti : une association ( S.15 ) qui recoit le financement public et les cotisations, et paie ses tournees."""
    __slots__ = ("indice", "nom", "famille", "axes", "gauche_droite", "cible", "liste", "refuse", "caisse",
                 "adherents", "recu_public", "recu_cotisations", "depense_campagne")

    def __init__(self, indice, nom, famille, axes, cible, liste, refuse):
        axes = tuple(float(x) for x in axes)
        if len(axes) != len(AXES) or any(not 0.0 <= x <= 1.0 for x in axes):
            raise ValueError(f"{nom} : programme hors [0 ; 1] sur {AXES} : {axes!r}")
        if not 0.0 < cible < 1.0: raise ValueError(f"{nom} : part cible hors ]0 ; 1[")
        self.indice, self.nom, self.famille, self.axes = indice, nom, famille, axes
        self.gauche_droite = ((1.0 - axes[0]) + (1.0 - axes[1]) + axes[2] + axes[3]) / 4.0
        self.cible, self.liste, self.refuse = float(cible), bool(liste), bool(refuse)
        self.caisse = 0.0
        self.adherents = 0
        self.recu_public = self.recu_cotisations = self.depense_campagne = 0.0


class Scrutin:
    """Une election legislative : ce que disent les proces-verbaux des bureaux ( un bureau par lieu ) et le Parlement."""
    __slots__ = ("numero", "jour", "loi", "S", "inscrits", "votants", "blancs", "voix", "voix_nat", "valides", "sieges",
                 "prime", "premier", "anticipe")

    def __init__(self, numero, jour, loi, S, L, K, anticipe):
        if loi not in LOIS: raise ValueError(f"loi electorale inconnue {loi!r}")
        if not SIEGES_MIN <= S <= SIEGES_MAX: raise ValueError(f"{S} sieges hors [{SIEGES_MIN} ; {SIEGES_MAX}]")
        self.numero, self.jour, self.loi, self.S, self.anticipe = numero, jour, loi, S, anticipe
        self.inscrits = np.zeros(L, np.int64); self.votants = np.zeros(L, np.int64); self.blancs = np.zeros(L, np.int64)
        self.voix = np.zeros((L, K), np.int64)
        self.voix_nat = np.zeros(K, np.int64); self.valides = 0
        self.sieges = np.zeros(K, np.int64); self.prime = 0; self.premier = -1


class Executif:
    """Le gouvernement : ses listes ( le chef d abord ), son programme ( axes ponderes par les sieges ), sa date."""
    __slots__ = ("partis", "chef", "programme", "depuis", "origine", "voix", "sieges")

    def __init__(self, partis, programme, depuis, origine, voix, sieges):
        if not partis: raise ValueError("un gouvernement sans parti")
        if any(not 0.0 <= x <= 1.0 for x in programme): raise ValueError(f"programme hors bornes {programme!r}")
        self.partis, self.chef = tuple(int(k) for k in partis), int(partis[0])
        self.programme, self.depuis, self.origine = tuple(programme), depuis, origine
        self.voix, self.sieges = dict(voix), int(sieges)


class ContexteCampagne:
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer_campagne(ctx): return ctx.traits


def _regle_campagne(x, ctx):
    if x[10] < 0.05: return RIEN
    if x[6] < 0.5 and x[2] >= SEUIL_ATTAQUE: return ATTAQUE
    return SOCIAL if x[7] >= x[8] else ORDRE


def _temoin_campagne(x, ctx, rng): return RIEN


POINT_CAMPAGNE = D.PointDeDecision(
    "campagne", DOMAINE,
    traits=(("sondage", "son dernier sondage publie ( part nationale, sur 0,5 )"),
            ("resultat_bureau", "sa part dans ce bureau au dernier scrutin ( proces-verbal public, sur 0,6 )"),
            ("griefs", "ce que le lieu croit de mauvais contre le gouvernement ( domaine 22 ), sature a 1"),
            ("peur_crime", "ce que le lieu croit des crimes ( domaine 22 ), sature a 1"),
            ("inquietude_sociale", "ce que le lieu croit de la faim, des penuries, des hopitaux ( domaine 22 ), sature a 1"),
            ("moral", "le moral collectif du lieu ( domaine 23 )"),
            ("gouverne", "1 si le parti est au gouvernement"),
            ("axe_social", "son programme : depense sociale"),
            ("axe_ordre", "son programme : ordre"),
            ("campagne_officielle", "1 pendant les 30 jours avant le scrutin ( le decret de dissolution )"),
            ("caisse", "sa caisse sur 30 jours de tournees partout, saturee a 1"),
            ("taille", "les electeurs du lieu sur ceux du plus grand lieu ( listes electorales )")),
    actions=THEMES, observer=_observer_campagne, regle=_regle_campagne, temoin=_temoin_campagne,
    note=("chaque soir, pour CETTE liste dans CE lieu : les points d intention gagnes depuis la veille du choix, moins "
          "0,3 point pour une tournee"),
    horizon_j=TOURNEE_J)


class Politique:
    __slots__ = ("partis", "K", "L", "lieu_ids", "n_du_lieu", "habitable", "marche_de", "capitale", "lr", "axes",
                 "cible", "liste", "refuse", "poids_ideo", "constante", "t0", "gouv", "camp", "croyances",
                 "griefs", "g_lent", "moral_l", "taux", "electeurs_l", "intent", "attendus", "inscrits", "part_lieu",
                 "part_nat", "participation", "resultat_lieu", "voix_ref", "S", "sieges", "executif", "scrutins",
                 "numero", "prochaine", "derniere", "anticipee", "investiture_j", "formation", "loi", "dernier_sondage",
                 "sondages", "decideur", "choix", "ref", "lois_ref", "compte", "livre_motifs", "financements", "manifs",
                 "derniere_greve", "greves", "refus", "actions", "serie", "lieux_campagne", "calibrage", "dissous_j",
                 "programme_ref")

    def __init__(self):
        self.partis = []
        self.scrutins = []
        self.numero = 0
        self.executif = None
        self.investiture_j = None
        self.formation = None
        self.anticipee = False
        self.dissous_j = None
        self.dernier_sondage = None
        self.sondages = collections.deque(maxlen=200)
        self.ref = {}
        self.compte = collections.defaultdict(float)
        self.livre_motifs = collections.defaultdict(float)
        self.financements = collections.deque(maxlen=100)
        self.manifs = collections.deque(maxlen=2000)
        self.derniere_greve = -10 ** 6
        self.greves = []
        self.refus = []
        self.actions = collections.deque(maxlen=400)
        self.serie = collections.deque(maxlen=800)
        self.calibrage = {}


def _dom(p): return p.domaines[DOMAINE]


def _membres_partis(w): return w.pays.domaines[DOMAINE].partis


MOTIFS = (("financement_partis", "transfert_courant"), ("cotisation_parti", "transfert_courant"),
          ("campagne_electorale", "achat"))
COLONNES_HABITANT = (("pol_ident", np.int8, -2), ("pol_ideo", np.uint8, 125), ("pol_adh", np.int8, 0),
                     ("pol_emarge", np.uint16, 0))


# ================================================================== la loi electorale ( fonctions pures )
def sieges_pour(population):
    """Le nombre de sieges d un pays de cette population : racine cubique calee sur la Grece, bornee par la Constitution."""
    if not population >= 0: raise ValueError("population negative")
    s = SIEGES_GRECE * (population / POPULATION_GRECE) ** (1.0 / 3.0)
    return int(min(SIEGES_MAX, max(SIEGES_MIN, round(s))))


def prime(part, loi="4804/2021", S=SIEGES_GRECE):
    """La prime du premier parti : 20 sieges a 25 %, un de plus par 0,5 %, 50 au plus ( sur 300 ) ; rien sous 25 % ou
    sous la loi 4406/2016. Sur S sieges : la meme part du Parlement, arrondie."""
    if loi == "4406/2016" or part < PRIME_SEUIL - 1e-12: return 0
    b = min(PRIME_MAX, PRIME_MIN + int(math.floor((part - PRIME_SEUIL) / PRIME_PAS + 1e-9)))
    return b if S == SIEGES_GRECE else int(round(b * S / SIEGES_GRECE))


def repartir_sieges(voix, listes=None, S=SIEGES_GRECE, loi="4804/2021"):
    """Les sieges de chaque liste pour ses voix valides ( entiers ) : seuil de 3 % des voix valides du pays, prime au
    premier, proportionnelle de Hare aux plus forts restes ( a egalite de reste, la liste qui a le plus de voix ).
    Rend ( sieges, prime, premier )."""
    v = np.asarray(voix, np.int64)
    K = len(v)
    lst = np.ones(K, bool) if listes is None else np.asarray(listes, bool)
    if (v < 0).any(): raise ValueError("voix negatives")
    tot = int(v.sum())
    out = np.zeros(K, np.int64)
    if tot <= 0: return out, 0, -1
    ok = lst & (v * 1.0 >= SEUIL_LISTE * tot - 1e-9)
    if not ok.any(): return out, 0, -1
    cand = np.nonzero(ok)[0]
    premier = int(cand[np.lexsort((cand, -v[cand]))[0]])
    b = prime(v[premier] / tot, loi, S)
    reste = S - b
    vq = v[cand]; sq = int(vq.sum())
    q = vq * reste
    base = q // sq
    r = q - base * sq                                   # restes exacts, en entiers
    manque = reste - int(base.sum())
    ordre = np.lexsort((cand, -vq, -r))[:manque]
    base[ordre] += 1
    out[cand] = base
    out[premier] += b
    return out, b, premier


def former_coalition(sieges, gauche_droite, refuse, majorite):
    """Les mandats exploratoires ( art. 37 ) : le premier, puis le deuxieme, puis le troisieme parti. Un parti majoritaire
    gouverne seul ; sinon il cherche la coalition majoritaire compatible ( ecart gauche-droite <= ECART_COALITION, sans
    parti qui refuse toute alliance ) au plus petit nombre de partenaires, puis au plus petit ecart, puis au moins de
    sieges ( coalition minimale connexe, Axelrod 1970 ). Rend le tuple des partis ( le chef d abord ) ou None."""
    s = np.asarray(sieges, np.int64); lr = np.asarray(gauche_droite, np.float64); rf = np.asarray(refuse, bool)
    K = len(s)
    mandats = [int(k) for k in np.lexsort((np.arange(K), -s)) if s[k] > 0][:3]
    for m in mandats:
        if s[m] >= majorite: return (m,)
        if rf[m]: continue
        autres = [k for k in range(K) if k != m and s[k] > 0 and not rf[k]]
        best = None
        for r in range(1, len(autres) + 1):
            for combo in itertools.combinations(autres, r):
                c = (m,) + combo
                tot = int(s[list(c)].sum())
                if tot < majorite: continue
                ec = float(lr[list(c)].max() - lr[list(c)].min())
                if ec > ECART_COALITION + 1e-12: continue
                cle = (r, ec, tot, combo)
                if best is None or cle < best[0]: best = (cle, c)
            if best is not None: return best[1]
    return None


# ================================================================== l installation
def _carte(p, d):
    w = p.w
    lieux = sorted(w.carte.lieux.values(), key=lambda l: l.n)
    if any(l.n != k for k, l in enumerate(lieux)): raise RuntimeError("politique : lieux hors de l ordre du moteur")
    d.L = len(lieux)
    d.lieu_ids = [l.id for l in lieux]
    d.n_du_lieu = {l.id: l.n for l in lieux}
    d.habitable = np.array([l.type in ("capitale", "ville", "village") for l in lieux])
    d.marche_de = np.array([l.marche.n if getattr(l, "marche", None) is not None else l.n for l in lieux], np.int64)
    caps = sorted(w.carte.capitales, key=lambda l: l.n)
    d.capitale = caps[0].n if caps else 0


def _partis(d):
    for k, (nom, fam, i, s, o, m, cible, liste, refuse) in enumerate(PARTIS):
        d.partis.append(PartiPolitique(k, nom, fam, (i, s, o, m), cible, liste, refuse))
    d.K = len(d.partis)
    d.lr = np.array([x.gauche_droite for x in d.partis])
    d.axes = np.array([x.axes for x in d.partis])
    d.cible = np.array([x.cible for x in d.partis]); d.cible /= d.cible.sum()
    d.liste = np.array([x.liste for x in d.partis])
    d.refuse = np.array([x.refuse for x in d.partis])
    d.poids_ideo = np.where(d.liste, 1.0, B_DIVERS)


def installer(p):
    w = p.w; L_ = p.socle.livre; tb = w.table
    d = Politique()
    p.domaines[DOMAINE] = d
    _carte(p, d)
    _partis(d)
    for m_, nature in MOTIFS: L_.declarer_motif(m_, nature, DOMAINE)
    J = p.socle.journal
    for t_, champs in (("sondage", ("lieu", "premier", "score_premier", "score_gouvernement", "n")),
                       ("dissolution", ("lieu", "scrutin_j", "anticipee")),
                       ("resultats_election", ("lieu", "numero", "participation", "premier", "sieges")),
                       ("investiture", ("lieu", "gouvernement", "chef", "sieges", "lois")),
                       ("echec_formation", ("lieu", "numero")),
                       ("crise_gouvernement", ("lieu", "parti")),
                       ("manifestation", ("lieu", "participants", "motif")),
                       ("greve_generale", ("lieu", "roles", "griefs"))):
        J.declarer(t_, DOMAINE, "individuel", champs)
    for t_ in ("cotisation_parti", "financement_partis", "depense_campagne", "decision_campagne",
               "participants_manifestation"):
        J.declarer(t_, DOMAINE, "compte")
    for type_, sujet, champ, spec in NOUVELLES: ME.declarer_nouvelle(p, type_, sujet, champ, spec)
    ch = p.colonnes["habitant"]
    for nom, dt_, v in COLONNES_HABITANT: ch.ajouter(nom, dt_, v)
    ch.assurer(tb.n)
    K, L = d.K, d.L
    d.camp = np.zeros((K, L))
    d.croyances = np.zeros((5, L)); d.griefs = np.zeros(L); d.g_lent = np.zeros(L); d.moral_l = np.full(L, MORAL_REF)
    d.taux = np.zeros((3, L)); d.electeurs_l = np.zeros(L, np.int64)
    d.intent = np.zeros((L, GROUPES, K)); d.attendus = np.zeros((L, GROUPES)); d.inscrits = np.zeros((L, GROUPES))
    d.part_lieu = np.zeros((K, L)); d.part_nat = d.cible.copy(); d.participation = PARTICIPATION
    d.choix = np.full((K, L), RIEN, np.int8)
    d.constante = np.zeros(K); d.t0 = 0.0
    d.gouv = np.zeros(K, bool)
    d.gouv[[x.nom for x in d.partis].index(GOUVERNEMENT_INITIAL)] = True
    # --- les electeurs : identification, ideologie, adhesion ( une passe tiree )
    _nouveaux(p, d, p.hasard("politique_installation"))
    # --- ce que le pays croit et vit ce jour, puis le calage des constantes sur juin 2023
    _lire_le_pays(p, d)
    _caler(p, d)
    _opinion(p, d)
    d.resultat_lieu = d.part_lieu.copy()
    d.voix_ref = d.cible.copy()
    # --- le Parlement sortant et son gouvernement
    vivants = int((tb.vivant[:tb.n] == 1).sum())
    d.S = sieges_pour(vivants)
    d.loi = "4804/2021"
    d.sieges, _, _ = repartir_sieges(np.round(d.cible * 1e7).astype(np.int64), d.liste, d.S, d.loi)
    # --- l argent : le registre, les banques, la reserve des partis
    p.socle.registre.inscrire("partis_politiques", "associations", _membres_partis, "caisse", None, "PartiPolitique")
    bq = p.domaine("banques")
    rb = p.hasard("politique_banques")
    parts = np.array([b.part for b in bq.banques], np.float64); parts /= parts.sum()
    for x in d.partis: BQ.ouvrir_compte(p, x, bq.banques[int(rb.choice(len(parts), p=parts))])
    d.lois_ref = lois_en_vigueur(p)
    coal = former_coalition(d.sieges, d.lr, d.refuse, d.S // 2 + 1)
    d.derniere = p.jour - AGE_LEGISLATURE_J
    _investir(p, d, coal if coal is not None else (int(np.nonzero(d.gouv)[0][0]),), "installation")
    d.programme_ref = d.executif.programme          # les lois de l installation sont celles de ce programme
    _financer(p, d, DOTATION_INITIALE_MOIS * TAUX_FINANCEMENT / 12.0, "dotation_initiale")
    d.prochaine = _dimanche(p, d.derniere + DUREE_LEGISLATURE_J - 6)
    d.lieux_campagne = np.zeros(0, np.int64)
    d.decideur = p.decideur(POINT_CAMPAGNE)
    p.routine(6 + 10 / 60, 50, DOMAINE, _matin)
    p.routine(9.0, 60, DOMAINE, _campagne)
    p.routine(10.0, 60, DOMAINE, _investiture_du_jour)
    p.routine(12.0, 60, DOMAINE, _midi)
    p.routine(18.0, 60, DOMAINE, _contestation)
    p.routine(HEURE_SCRUTIN, 60, DOMAINE, _scrutin_du_jour)
    p.routine(23 + 50 / 60, 97, DOMAINE, _soir)
    p.cloture(DOMAINE, _cloture)
    return d


# ================================================================== les electeurs
def _nouveaux(p, d, rng=None):
    """Les habitants sans traits politiques ( tous a l installation, puis les nouveau-nes ) : identification ( celle de
    la mere avec la probabilite TRANSMISSION, sinon tiree ), ideologie autour de celle du parti ou de sa classe,
    adhesion ( a l installation )."""
    tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
    ident = col["pol_ident"]
    neufs = np.nonzero(ident[:n] == -2)[0]
    if not len(neufs): return
    install = rng is not None
    rng = rng if install else p.du_jour("politique_nouveaux")
    m = len(neufs)
    u = rng.random((m, 4)); z = rng.standard_normal(m)
    listes = np.nonzero(d.liste)[0]
    w_ = d.cible[listes] / d.cible[listes].sum()
    tire = listes[np.minimum(np.searchsorted(np.cumsum(w_), u[:, 1], side="right"), len(listes) - 1)]
    idt = np.where(u[:, 0] < P_IDENTIFIE, tire, -1)
    if not install:
        mere = col["mere"][neufs].astype(np.int64)
        im = np.where(mere >= 0, ident[np.maximum(mere, 0)], -1)
        herite = (im >= 0) & (u[:, 2] < TRANSMISSION)
        idt = np.where(herite, im, np.where(im >= 0, -1, idt))
    classe = tb.classe[neufs].astype(np.int64)
    centre = np.where(idt >= 0, d.lr[np.maximum(idt, 0)], 0.5 + np.asarray(IDEO_CLASSE)[classe])
    sd = np.where(idt >= 0, SD_IDEO_IDENT, SD_IDEO)
    ideo = np.clip(centre + sd * z, 0.0, 1.0)
    ident[neufs] = idt.astype(np.int8)
    col["pol_ideo"][neufs] = np.round(ideo * 250).astype(np.uint8)
    if install:
        adh = (idt >= 0) & (tb.age[neufs] >= AGE_VOTE) & (u[:, 3] < P_ADHERENT)
        col["pol_adh"][neufs] = adh.astype(np.int8)
        cnt = np.bincount(idt[adh], minlength=d.K)
        for x in d.partis: x.adherents = int(cnt[x.indice])


def _electeurs(p, election=False):
    """Les inscrits : vivants de 17 ans et plus, domicilies ( un bureau ). Le jour du scrutin, les absents ( en mer, sur
    une autre ile ) ne votent pas : pas de vote par correspondance aux legislatives ( a verifier )."""
    tb = p.w.table; n = tb.n
    m = (tb.vivant[:n] == 1) & (tb.age[:n] >= AGE_VOTE) & (tb.domicile[:n] >= 0)
    if election: m &= tb.statut[:n] != PO.ABSENT
    return np.nonzero(m)[0]


class _Menages:
    """Ce que chaque menage vit, en colonnes, une fois par passe : faim de la semaine, pauvrete."""
    __slots__ = ("mg", "faim", "pauvre", "caisse", "cout")

    def __init__(self, p):
        w = p.w; tb = w.table; n = tb.n; M = tb.menages.n
        p.colonnes["menage"].assurer(M)
        self.mg = PO.menages_inscrits(tb, n)
        v = (tb.vivant[:n] == 1) & (self.mg >= 0)
        viv = np.bincount(self.mg[v], minlength=M)[:M]
        f7 = p.col("menage", "faim7")[:M].astype(np.int64) & 0x7F
        self.faim = POPCOUNT[f7] / 7.0
        prix = w.prix_moyen("nourriture") * (1.0 + w.gouv.tva)
        self.cout = prix * C.NOURRITURE_PAR_JOUR * np.maximum(1, viv)
        self.caisse = tb.menages.caisse[:M]
        self.pauvre = self.caisse < JOURS_PAUVRE * self.cout


def _entrees(p, d, ids, mn):
    """Les colonnes d electeurs dont le vote a besoin."""
    tb = p.w.table; col = p.colonnes["habitant"]
    age = tb.age[ids]
    band = (age >= AGES_GROUPE[0]).astype(np.int64) + (age >= AGES_GROUPE[1]).astype(np.int64)
    classe = tb.classe[ids].astype(np.int64)
    lieu = tb.domicile[ids].astype(np.int64)
    mg = mn.mg[ids]; km = np.maximum(mg, 0)
    role = tb.role[ids]
    actif = ((role != PO.CODE_ROLE["enfant"]) & (role != PO.CODE_ROLE["retraite"]) & (age >= C.AGE_TRAVAIL)
             & (age < C.AGE_RETRAITE))
    chom = actif & (tb.travail[ids] < 0)
    faim = np.where(mg >= 0, mn.faim[km], 0.0)
    pauvre = (mg >= 0) & mn.pauvre[km]
    rev = col["fisc_revenu"][ids]; ret = col["fisc_retenu"][ids]
    taux = np.divide(ret, rev, out=np.zeros(len(ids)), where=rev > 1e-9)
    imp = np.clip((taux - TAUX_IMPOT_REF) / TAUX_IMPOT_PLEIN, 0.0, 1.0)
    situ = K_CHOMAGE * chom + K_FAIM * faim + K_IMPOT * imp + K_PAUVRE * pauvre
    moral = col["cul_moral"][ids].astype(np.float64)
    return {"lieu": lieu, "groupe": classe * 3 + band, "band": band, "classe": classe,
            "ident": col["pol_ident"][ids].astype(np.int64), "ideo": col["pol_ideo"][ids] / 250.0, "situ": situ,
            "moral": moral, "chom": chom, "faim": faim, "pauvre": pauvre}


def _probas(d, E):
    """( T, P ) : la probabilite de voter de chaque electeur, et celle de choisir chaque liste s il vote."""
    n = len(E["lieu"]); K = d.K
    l = E["lieu"]; ideo = E["ideo"]; s = E["situ"]; idt = E["ident"]
    U = np.empty((n, K))
    cl = d.camp[:, l]
    rel = cl - cl[d.liste].mean(0)[None, :]
    for k in range(K):
        U[:, k] = (d.constante[k] - B_IDEO * d.poids_ideo[k] * np.abs(ideo - d.lr[k])
                   + SOC_SITU * s * (d.axes[k, 1] - 0.5) + (C_CAMP * rel[k] if d.liste[k] else 0.0))
    a = np.nonzero(idt >= 0)[0]
    U[a, idt[a]] += A_IDENT
    gv = np.nonzero(d.gouv)[0]
    if len(gv):
        t = (-G_GRIEF * d.griefs[l] - G_LENT * d.g_lent[l] - E_SOCIO * d.croyances[SOCIO_, l]
             + M_MORAL * (d.moral_l[l] - MORAL_REF) - S_SITU * s)
        U[:, gv] += t[:, None]
    U -= U.max(1, keepdims=True)
    np.exp(U, out=U)
    U /= U.sum(1, keepdims=True)
    mob = np.minimum(T_MOBIL_MAX, T_MOBIL * cl.sum(0))
    z = (d.t0 + np.asarray(T_AGE)[E["band"]] + np.asarray(T_CLASSE)[E["classe"]] + T_IDENT * (idt >= 0) + mob
         - T_ALIEN * np.maximum(0.0, MORAL_REF - E["moral"]))
    return 1.0 / (1.0 + np.exp(-z)), U


def probabilites(p, ids):
    """Domaines suivants et portes : ( probabilite de voter, probabilites des listes ) d habitants electeurs, avec
    l etat du pays de maintenant ( croyances et moral du dernier soir )."""
    d = _dom(p)
    ids = np.asarray(ids, np.int64)
    return _probas(d, _entrees(p, d, ids, _Menages(p)))


# ================================================================== ce que le pays croit et vit
def _tables_sujets(me):
    """Pour chaque code de sujet des medias : base, pente, mode log, valence, grief ( gouvernemental et pas une
    statistique ), categories ( ordre, economie, social ), statistique du chomage, des prix."""
    S = len(me.sujets)
    out = np.zeros((S, 10))
    for c, s in enumerate(me.sujets):
        v, gouv, base, pente, mode, _, _ = me.table_sujets[s]
        justice = me.table_sujets[s] == ME.SUJET_JUSTICE
        stat = s in SUJETS_STATS
        out[c] = (base, pente, 1.0 if mode == "log" else 0.0, v, 1.0 if (gouv and not stat) else 0.0,
                  1.0 if (s in SUJETS_ORDRE or justice) else 0.0, 1.0 if (s in SUJETS_ECO and not stat) else 0.0,
                  1.0 if s in SUJETS_SOCIAL else 0.0, 1.0 if s == "chomage" else 0.0, 1.0 if s == "prix" else 0.0)
    return out


def croyances_politiques(p):
    """Ce que chaque lieu croit, en colonnes ( 5 x lieux ) : griefs contre le gouvernement ( somme de part x saillance
    annoncee x | valence | des sujets gouvernementaux negatifs hors statistique publique : la quantite de
    `d23.humeur_politique` sans les bulletins mensuels ), peur du crime, inquietude economique, inquietude sociale,
    economie crue ( chomage et hausse des prix crus au-dela de la normale, fois la part qui les sait ). Lit la memoire
    du domaine 22 comme `ME.croyance` : la valeur CRUE, le seuil d une demi-personne, un fait dementi pese 0,3 ; pour
    une statistique, la valeur du bulletin le plus su du lieu ( `ME.rumeur_locale` )."""
    d = _dom(p); me = p.domaine("medias"); mem = me.mem; L = d.L
    out = np.zeros((5, L))
    idx = mem.actifs()
    if not len(idx): return out
    tab = _tables_sujets(me)
    pm = (0.5 / np.maximum(me.pop[:L], 1.0)).astype(np.float32)
    part32 = mem.c["part"][idx, :L]
    part = np.where(part32 >= pm[None, :], part32.astype(np.float64), 0.0)
    val = np.maximum(np.exp(mem.c["lv"][idx, :L].astype(np.float64)), 0.0)
    t = tab[mem.f["sujet"][idx].astype(np.int64)]
    base, pente, lg = t[:, 0:1], t[:, 1:2], t[:, 2:3]
    s = np.clip(base + pente * np.where(lg > 0, np.log10(1.0 + val), val), 0.01, 1.0)
    dem = np.where(np.isnan(mem.f["dementi_t"][idx]), 1.0, 0.3)[:, None]
    inten = part * s * dem
    neg = np.maximum(0.0, -t[:, 3])
    out[GRIEFS] = (inten * (neg * t[:, 4])[:, None]).sum(0)
    out[ORDRE_] = (inten * (neg * t[:, 5])[:, None]).sum(0)
    out[ECO_] = (inten * (neg * t[:, 6])[:, None]).sum(0)
    out[SOCIAL_] = (inten * (neg * t[:, 7])[:, None]).sum(0)
    socio = np.zeros(L)
    for j, ref, kx, dec in ((8, CHOMAGE_REF, K_CHOMAGE_CRU, 0.0), (9, INFLATION_REF, K_INFLATION_CRUE, 100.0)):
        r = np.nonzero(t[:, j] > 0)[0]
        if not len(r): continue
        pr = part[r]
        o = np.lexsort((mem.f["fid"][idx[r]][:, None].repeat(L, 1), -pr), axis=0)[0]   # le plus su ( rumeur_locale )
        su = pr[o, np.arange(L)]
        v = val[r][o, np.arange(L)] - dec
        socio += su * kx * np.maximum(0.0, v - ref)
    out[SOCIO_] = socio
    return out


def _lire_le_pays(p, d):
    """Le soir ( et a l installation ) : croyances des lieux, griefs de la legislature, moral des lieux."""
    tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
    d.croyances = croyances_politiques(p)
    d.griefs = np.minimum(G_CAP, d.croyances[GRIEFS])
    d.g_lent = d.g_lent + (d.griefs - d.g_lent) / TAU_LENT_J
    v = (tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & (tb.domicile[:n] >= 0) & (col["cul_base"][:n] >= 0)
    dom = tb.domicile[:n][v].astype(np.int64)
    cnt = np.bincount(dom, minlength=d.L)[:d.L]
    som = np.bincount(dom, weights=col["cul_moral"][:n][v].astype(np.float64), minlength=d.L)[:d.L]
    d.moral_l = np.where(cnt > 0, som / np.maximum(cnt, 1), MORAL_REF)


def _caler(p, d, iterations=40):
    """L installation : la participation attendue ( 60 % ) par l intercept, puis les constantes des listes pour que
    les parts attendues soient les parts cibles ( constantes propres a chaque alternative d un logit : Train 2009,
    ch. 2.8 ). Lineaire en electeurs par iteration."""
    ids = _electeurs(p)
    if not len(ids): return
    E = _entrees(p, d, ids, _Menages(p))
    lo, hi = -10.0, 10.0
    for _ in range(50):
        d.t0 = 0.5 * (lo + hi)
        T, _ = _probas(d, E)
        if T.mean() < PARTICIPATION: lo = d.t0
        else: hi = d.t0
    for _ in range(iterations):
        T, Pk = _probas(d, E)
        sh = (T[:, None] * Pk).sum(0) / T.sum()
        d.constante += np.log(d.cible / np.maximum(sh, 1e-12))
        d.constante -= d.constante[-1]
    T, Pk = _probas(d, E)
    sh = (T[:, None] * Pk).sum(0) / T.sum()
    d.calibrage = {"participation": float(T.mean()), "ecart_max": float(np.abs(sh - d.cible).max()), "t0": d.t0}


def _opinion(p, d):
    """La passe du soir : intentions par ( lieu, groupe, liste ), votants attendus, inscrits ; parts par lieu et du
    pays ; taux de chomage, de faim et de pauvrete des electeurs de chaque lieu ( ce que la campagne rencontre )."""
    L, K = d.L, d.K
    ids = _electeurs(p)
    mn = _Menages(p)
    LG = L * GROUPES
    intent = np.zeros((LG, K)); att = np.zeros(LG); ins = np.zeros(LG)
    taux = np.zeros((3, L)); el = np.zeros(L, np.int64)
    for a in range(0, len(ids), BLOC):
        blk = ids[a:a + BLOC]
        E = _entrees(p, d, blk, mn)
        T, Pk = _probas(d, E)
        cle = E["lieu"] * GROUPES + E["groupe"]
        ins += np.bincount(cle, minlength=LG)[:LG]
        att += np.bincount(cle, weights=T, minlength=LG)[:LG]
        for k in range(K): intent[:, k] += np.bincount(cle, weights=T * Pk[:, k], minlength=LG)[:LG]
        el += np.bincount(E["lieu"], minlength=L)[:L]
        for j, x in enumerate((E["chom"], E["faim"], E["pauvre"])):
            taux[j] += np.bincount(E["lieu"], weights=x.astype(np.float64), minlength=L)[:L]
    d.intent = intent.reshape(L, GROUPES, K); d.attendus = att.reshape(L, GROUPES); d.inscrits = ins.reshape(L, GROUPES)
    d.electeurs_l = el
    d.taux = taux / np.maximum(el, 1)[None, :]
    vl = d.intent.sum(1)                                       # L x K
    al = d.attendus.sum(1)
    d.part_lieu = np.where(al[None, :] > 0, vl.T / np.maximum(al, 1e-12)[None, :], 0.0)
    tot = al.sum()
    d.part_nat = vl.sum(0) / tot if tot > 0 else d.cible.copy()
    d.participation = float(tot / max(1.0, ins.sum()))


# ================================================================== le calendrier
def _dimanche(p, jour):
    """Le premier dimanche a partir de ce jour du monde."""
    wd = p.socle.calendrier.jour_semaine(p.w.pas)
    j = int(jour)
    return j + (6 - (wd + (j - p.jour)) % 7) % 7


def en_campagne(p):
    """La campagne officielle : du decret de dissolution au scrutin."""
    d = _dom(p)
    return d.dissous_j is not None and p.jour < d.prochaine


def convoquer(p, dans_j=CAMPAGNE_J, anticipee=True):
    """Dissolution et elections ( art. 41 ) : le premier dimanche a `dans_j` jours au moins. Le supplement electoral du
    financement est verse. Rend le jour du scrutin."""
    d = _dom(p)
    d.prochaine = _dimanche(p, p.jour + max(1, int(dans_j)))
    d.anticipee = bool(anticipee)
    _dissoudre(p, d)
    return d.prochaine


def _dissoudre(p, d):
    d.dissous_j = p.jour
    p.noter("dissolution", lieu=d.lieu_ids[d.capitale], scrutin_j=int(d.prochaine), anticipee=bool(d.anticipee))
    _financer(p, d, SUPPLEMENT_ELECTORAL, "supplement_electoral")


# ================================================================== l argent
def recettes_ordinaires(p):
    """Les recettes ordinaires annuelles de l Etat : celles que prevoit la loi de finances, ramenees a l annee."""
    b = p.domaine("etat").budget
    return math.fsum(b.prevues.values()) * JOURS_AN / max(1, b.jours)


def cles_financement(d):
    """La part de chaque liste dans le financement public : 90 % aux listes representees, 10 % aux listes de 1,5 % et
    plus sans siege, au prorata des voix du dernier scrutin. Une part sans beneficiaire n est pas versee."""
    v = d.voix_ref * d.liste
    rep = d.sieges > 0
    non = ~rep & d.liste & (d.voix_ref >= SEUIL_FINANCEMENT)
    out = np.zeros(d.K)
    if v[rep].sum() > 0: out[rep] = PART_REPRESENTES * v[rep] / v[rep].sum()
    if v[non].sum() > 0: out[non] = (1.0 - PART_REPRESENTES) * v[non] / v[non].sum()
    return out


def _financer(p, d, taux, quoi):
    """Un versement de l Etat aux partis : `taux` des recettes ordinaires annuelles, selon la cle des voix."""
    w = p.w
    total = taux * recettes_ordinaires(p)
    parts = cles_financement(d) * total
    if parts.sum() <= 0: return
    ET.assurer(p, float(parts.sum()))
    verse = {}
    for x in d.partis:
        m = float(parts[x.indice])
        if m <= 0: continue
        y = p.socle.livre.transferer(w.gouv, x, m, "financement_partis")
        x.recu_public += y; d.compte["financement_partis"] += y; verse[x.indice] = y
    d.financements.append((p.jour, quoi, total, verse, dict(enumerate(parts.tolist()))))
    p.compter("financement_partis", math.fsum(verse.values()))


def _cotisations(p, d):
    """Midi : les adherents dont c est le jour du mois ( numero modulo 30 ) paient leur parti, si la caisse de leur
    menage garde 14 jours de nourriture."""
    tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
    ids = np.nonzero((col["pol_adh"][:n] == 1) & (tb.vivant[:n] == 1) & (np.arange(n) % MOIS_J == p.jour % MOIS_J)
                     & (col["pol_ident"][:n] >= 0))[0]
    if not len(ids): return 0.0
    mn = _Menages(p)
    mg = mn.mg[ids]
    m = COTISATION_EUR / EUROS
    tot = 0.0
    for i, k in zip(ids.tolist(), mg.tolist()):
        if k < 0 or mn.caisse[k] - m < RESERVE_COTISATION_J * mn.cout[k]: continue
        x = d.partis[int(col["pol_ident"][i])]
        y = p.socle.livre.transferer(PO.Menage(int(k), tb.menages), x, m, "cotisation_parti")
        x.recu_cotisations += y; d.compte["cotisation_parti"] += y; tot += y
    if tot > 0: p.compter("cotisation_parti", tot)
    return tot


def _midi(p):
    d = _dom(p)
    p.colonnes["habitant"].assurer(p.w.table.n)
    _cotisations(p, d)
    if p.jour % MOIS_J == 0: _financer(p, d, TAUX_FINANCEMENT / 12.0, "mensuel")
    if d.prochaine - p.jour == CAMPAGNE_J and d.dissous_j is None:
        d.anticipee = False; _dissoudre(p, d)                  # la dissolution ordinaire, 30 jours avant
    camp = en_campagne(p)
    if d.prochaine - p.jour in (0, 1): return                  # la veille et le jour du scrutin : aucun sondage publie
    if (camp and p.jour % 2 == 0) or (not camp and p.jour % 7 == 3): publier_sondage(p)


# ================================================================== les sondages
def sonder(p, n=None, rng=None):
    """Un sondage : `n` electeurs tires sans remise ( 1 000 au plus, un quart des inscrits dans un petit pays ), chacun
    repond selon ses propres probabilites ( voter ou non, puis une liste ). Rend les parts des intentions exprimees,
    leur marge a 95 %, le nombre de repondants qui votent."""
    d = _dom(p)
    ids = _electeurs(p)
    N = len(ids)
    if n is None: n = min(TAILLE_SONDAGE, N // 4)
    n = int(min(max(1, n), N))
    rng = rng if rng is not None else p.du_jour("politique_sondage")
    sel = np.sort(rng.choice(N, size=n, replace=False))
    T, Pk = _probas(d, _entrees(p, d, ids[sel], _Menages(p)))
    u = rng.random((n, 2))
    vote = u[:, 0] < T
    liste = np.minimum((np.cumsum(Pk, 1) < u[:, 1:2]).sum(1), d.K - 1)
    nv = int(vote.sum())
    parts = np.bincount(liste[vote], minlength=d.K) / max(1, nv)
    return {"n": n, "N": N, "votants": nv, "parts": parts, "marges": Z95 * np.sqrt(parts * (1 - parts) / max(1, nv)),
            "jour": p.jour}


def publier_sondage(p):
    """Un institut publie : le journal le dit ( le domaine 22 en fait une nouvelle officielle que les redactions
    publient ), les partis le lisent."""
    d = _dom(p)
    s = sonder(p)
    d.dernier_sondage = s["parts"]; d.sondages.append(s)
    k = int(np.argmax(s["parts"]))
    gouv = float(s["parts"][d.gouv].sum())
    p.noter("sondage", lieu=d.lieu_ids[d.capitale], premier=d.partis[k].nom, score_premier=round(100 * s["parts"][k], 1),
            score_gouvernement=round(100 * gouv, 1), n=s["n"])
    return s


# ================================================================== la campagne ( decision )
def _lieux_campagne(d):
    return np.nonzero(d.habitable & (d.electeurs_l >= ELECTEURS_MIN_CAMPAGNE))[0]


def _traits(p, d, k, l, camp, cout_plein, emax):
    x = d.partis[k]
    sond = d.dernier_sondage[k] if d.dernier_sondage is not None else d.voix_ref[k]
    return (min(1.0, sond / 0.5), min(1.0, d.resultat_lieu[k, l] / 0.6), min(1.0, d.croyances[GRIEFS, l]),
            min(1.0, d.croyances[ORDRE_, l]), min(1.0, d.croyances[SOCIAL_, l]), min(1.0, max(0.0, d.moral_l[l])),
            1.0 if d.gouv[k] else 0.0, x.axes[1], x.axes[2], 1.0 if camp else 0.0,
            min(1.0, max(0.0, x.caisse) / max(1e-9, 30.0 * cout_plein)), min(1.0, d.electeurs_l[l] / max(1, emax)))


def _preoccupation(d, l, theme):
    """Ce qui fait qu un theme porte dans un lieu : ce que ses electeurs vivent et croient."""
    if theme == ECONOMIE: return min(1.0, 3.0 * d.taux[0, l] + 0.5 * (d.croyances[ECO_, l] + d.croyances[SOCIO_, l]))
    if theme == SOCIAL: return min(1.0, 2.0 * d.taux[1, l] + d.taux[2, l] + 0.5 * d.croyances[SOCIAL_, l])
    if theme == ORDRE: return min(1.0, 2.0 * d.croyances[ORDRE_, l])
    if theme == ATTAQUE: return min(1.0, 2.0 * d.croyances[GRIEFS, l])
    return 0.0


def _affinite(d, k, theme):
    if theme == ECONOMIE: return AFFINITE_ECONOMIE
    if theme == SOCIAL: return d.axes[k, 1]
    if theme == ORDRE: return d.axes[k, 2]
    if theme == ATTAQUE: return 0.0 if d.gouv[k] else 1.0
    return 0.0


def _campagne(p):
    """9 h : les tournees dont c est le jour sont decidees ( une par liste et par lieu tous les 3 jours ), puis chaque
    tournee en cours se paie et agit sur l intention du lieu."""
    d = _dom(p); w = p.w
    camp = en_campagne(p)
    inten = 1.0 if camp else INTENSITE_HORS_CAMPAGNE
    lieux = _lieux_campagne(d)
    d.lieux_campagne = lieux
    if not len(lieux): return
    cout_e = COUT_CAMPAGNE_EUR / EUROS
    tot_el = float(d.electeurs_l[lieux].sum())
    emax = int(d.electeurs_l[lieux].max())
    dec = d.decideur
    n_dec = 0
    for x in d.partis:
        if not x.liste: continue
        k = x.indice
        for l in lieux.tolist():
            if (p.jour + k + l) % TOURNEE_J: continue
            cle = k * d.L + l
            a = dec.decider(cle, ContexteCampagne(_traits(p, d, k, l, camp, cout_e * tot_el, emax)))
            d.choix[k, l] = a
            d.ref[cle] = float(d.part_lieu[k, l])
            if a != RIEN: dec.ajouter(cle, -COUT_POINTS * TOURNEE_J)
            n_dec += 1
    if n_dec: p.compter("decision_campagne", float(n_dec))
    # --- les tournees du jour : le paiement, puis l effet
    marches = {}
    for x in d.partis:
        if not x.liste: continue
        k = x.indice
        reserve = 0.0 if camp else RESERVE_PARTI_MOIS * TAUX_FINANCEMENT / 12.0 * recettes_ordinaires(p) * cles_financement(d)[k]
        for l in lieux.tolist():
            a = int(d.choix[k, l])
            if a == RIEN: continue
            cout = inten * cout_e * float(d.electeurs_l[l])
            dispo = max(0.0, x.caisse - reserve)
            if dispo <= 1e-9: continue
            n_ = int(d.marche_de[l])
            mk = marches.get(n_)
            if mk is None: mk = marches[n_] = w.marches[w.carte.par_n[n_].id]
            y = p.socle.livre.transferer(x, mk, min(cout, dispo), "campagne_electorale")
            x.depense_campagne += y; d.compte["campagne_electorale"] += y
            f = y / cout if cout > 0 else 0.0
            e = inten * f * (EFFET_BASE + (1.0 - EFFET_BASE) * _preoccupation(d, l, a) * _affinite(d, k, a))
            d.camp[k, l] += e
            p.compter("depense_campagne", y)


def _noter(p, d):
    """Le soir : chaque tournee en attente recoit les points d intention gagnes dans son lieu depuis la veille du choix."""
    dec = d.decideur
    for cle in sorted(d.ref):
        att = dec.attentes.get(cle)
        if att is None or not att.choix: continue
        k, l = divmod(cle, d.L)
        dec.noter(cle, 100.0 * (float(d.part_lieu[k, l]) - d.ref[cle]), p.jour)


# ================================================================== le gouvernement elu
def lois_en_vigueur(p):
    """Les lois que le programme d un gouvernement fait bouger ( domaine 6 )."""
    e = p.domaine("etat"); f = e.fisc; b = e.budget; w = p.w
    return {"tva_normale": f.tva["normale"], "tva_reduite": f.tva["reduite"], "ir_haut": f.taux_ir[-1],
            "ir_avant": f.taux_ir[-2], "is": f.taux_is, "salaires": w.gouv.facteur_salaire_public,
            "controle": f.part_controleurs, "defense": b.credits.get(("defense", "achats"), 0.0),
            "defense_vote": b.votes.get(("defense", "achats"), 0.0),
            "defense_deja": b.depenses.get(("defense", "achats"), 0.0) + b.engage.get("defense", 0.0)}


def cibles_du_programme(programme, ref_programme, lois_ref, lois):
    """Les lois qu un programme vise, bornees par le domaine 6 : ecart des axes au programme de reference, fois une
    pente, autour des lois de reference. Fonction pure."""
    dI = programme[0] - ref_programme[0]; dS = programme[1] - ref_programme[1]; dO = programme[2] - ref_programme[2]
    lo, hi = ET.BORNES_TVA["normale"]
    tva = min(hi, max(lo, lois["tva_reduite"], lois_ref["tva_normale"] + PENTE_TVA * dI))
    ir = min(ET.BORNES_TAUX_IR[1], max(lois["ir_avant"], lois_ref["ir_haut"] + PENTE_IR * dI))
    is_ = min(ET.BORNES_IS[1], max(ET.BORNES_IS[0], lois_ref["is"] + PENTE_IS * dI))
    slo, shi = G.BORNES["facteur_salaire_public"]
    sal = min(shi, max(slo, lois_ref["salaires"] * (1.0 + PENTE_SALAIRES * dS)))
    ctl = min(1.0, max(0.0, lois_ref["controle"] + PENTE_CONTROLE_IMPOTS * dI + PENTE_CONTROLE_ORDRE * dO))
    dv = lois["defense_vote"]
    dfn = min(3.0 * max(dv, 1000.0), max(lois["defense_deja"], dv * (1.0 + PENTE_DEFENSE * dO)))
    return {"tva_normale": tva, "ir_haut": ir, "is": is_, "salaires": sal, "controle": ctl, "defense": dfn}


def lois_du_programme(p, programme):
    """Les actions du catalogue du domaine 6 qui menent les lois en vigueur a celles du programme."""
    d = _dom(p)
    lois = lois_en_vigueur(p)
    c = cibles_du_programme(programme, d.programme_ref, d.lois_ref, lois)
    out = []
    if abs(c["tva_normale"] - lois["tva_normale"]) > 1e-9:
        out.append({"type": "fixer_tva", "categorie": "normale", "valeur": c["tva_normale"]})
    if abs(c["ir_haut"] - lois["ir_haut"]) > 1e-9:
        out.append({"type": "fixer_ir", "tranche": len(ET.TAUX_IR) - 1, "taux": c["ir_haut"]})
    if abs(c["is"] - lois["is"]) > 1e-9: out.append({"type": "fixer_is", "valeur": c["is"]})
    if abs(c["salaires"] - lois["salaires"]) > 1e-9: out.append({"type": "fixer_salaires_publics", "facteur": c["salaires"]})
    if abs(c["controle"] - lois["controle"]) > 1e-9: out.append({"type": "fixer_controle", "part": c["controle"]})
    if abs(c["defense"] - lois["defense"]) > 1e-6:
        out.append({"type": "fixer_budget", "ligne": "defense", "montant": c["defense"]})
    return out


def regle_du_gouvernement(publie, programme, vivants):
    """La regle du matin d un programme ( en plus de l administration du domaine 6 ) : un programme social ( axe >= 0,6 )
    subventionne les menages pauvres des que la statistique publie de la faim. Fonction pure, actions du catalogue."""
    k = max(1.0, vivants / 500.0)
    faim = float(((publie or {}).get("enquete") or {}).get("faim_menages") or 0.0)
    if programme[1] >= SOCIAL_SUBVENTION and faim > FAIM_SUBVENTION * k:
        return [{"type": "subvention", "cible": "menages_pauvres", "montant": round(1500.0 * k * programme[1])}]
    return []


def _indice(d, nom): return next(x.indice for x in d.partis if x.nom == nom)


def _appliquer(p, d, a, pourquoi):
    ok, raison = ET.appliquer(p, a)
    d.actions.append((p.jour, pourquoi, a, ok, raison))
    if not ok: d.refus.append((p.jour, pourquoi, a, raison))
    return ok


def _investir(p, d, partis, origine):
    """Un gouvernement prend ses fonctions : son programme ( axes des listes ponderes par leurs sieges ), puis son paquet
    de lois, action par action, par le catalogue borne du domaine 6."""
    partis = tuple(int(k) for k in partis)
    s = np.array([max(1, int(d.sieges[k])) for k in partis], np.float64)
    prog = tuple(float(v) for v in (d.axes[list(partis)] * s[:, None]).sum(0) / s.sum())
    d.executif = Executif(partis, prog, p.jour, origine, {k: float(d.voix_ref[k]) for k in partis},
                          int(d.sieges[list(partis)].sum()))
    d.gouv = np.zeros(d.K, bool); d.gouv[list(partis)] = True
    if origine == "installation": return
    n_ok = 0
    for a in lois_du_programme(p, prog): n_ok += _appliquer(p, d, a, "investiture")
    p.noter("investiture", lieu=d.lieu_ids[d.capitale], gouvernement="+".join(d.partis[k].nom for k in partis),
            chef=d.partis[partis[0]].nom, sieges=int(d.executif.sieges), lois=int(n_ok))


def _matin(p):
    """6 h 10, apres l administration du domaine 6 : la regle du programme au pouvoir."""
    d = _dom(p)
    if d.executif is None: return
    tb = p.w.table
    pub = ET.publications(p)["statistique"]
    for a in regle_du_gouvernement(pub, d.executif.programme, int((tb.vivant[:tb.n] == 1).sum())):
        _appliquer(p, d, a, "regle_du_programme")


def _investiture_du_jour(p):
    d = _dom(p)
    if d.investiture_j is None or p.jour != d.investiture_j or d.formation is None: return
    _investir(p, d, d.formation, "election")
    d.investiture_j = None; d.formation = None


def _crise(p, d):
    """Le soir, apres trois mois de gouvernement : un partenaire de coalition dont les intentions tombent sous 60 % de
    ses voix s en va. Si les autres gardent la majorite, ils gouvernent ( remaniement, par le catalogue ) ; sinon ils
    expedient les affaires courantes et le Parlement est dissous ( art. 41 )."""
    ex = d.executif
    if (ex is None or len(ex.partis) < 2 or d.investiture_j is not None or d.dissous_j is not None
            or p.jour - ex.depuis < GRACE_J):
        return
    for k in ex.partis[1:]:
        if d.part_nat[k] < QUITTER * ex.voix.get(k, 0.0):
            p.noter("crise_gouvernement", lieu=d.lieu_ids[d.capitale], parti=d.partis[k].nom)
            reste = tuple(x for x in ex.partis if x != k)
            if int(d.sieges[list(reste)].sum()) >= d.S // 2 + 1: _investir(p, d, reste, "remaniement")
            else:
                d.executif = Executif(reste, ex.programme, ex.depuis, "affaires_courantes", {x: ex.voix[x] for x in reste},
                                      int(d.sieges[list(reste)].sum()))
                d.gouv = np.zeros(d.K, bool); d.gouv[list(reste)] = True
                convoquer(p, CAMPAGNE_J)
            return


# ================================================================== le scrutin
def _scrutin_du_jour(p):
    d = _dom(p)
    if p.jour != d.prochaine: return
    voter(p)


def voter(p):
    """19 h, le jour du scrutin : chaque electeur present vote ou s abstient, selon ses probabilites ; il signe la liste
    d emargement de son bureau ; son bulletin tombe dans l urne du bureau ( blanc ou nul, ou une liste ). Puis le
    depouillement, les sieges, les mandats. Rend le Scrutin."""
    d = _dom(p); tb = p.w.table
    p.colonnes["habitant"].assurer(tb.n)
    d.numero += 1
    s = Scrutin(d.numero, p.jour, d.loi, d.S, d.L, d.K, d.anticipee)
    tous = _electeurs(p)
    s.inscrits = np.bincount(tb.domicile[tous].astype(np.int64), minlength=d.L)[:d.L]
    ids = _electeurs(p, election=True)
    mn = _Menages(p)
    rng = p.du_jour("politique_scrutin")
    em = p.col("habitant", "pol_emarge")
    for a in range(0, len(ids), BLOC):
        blk = ids[a:a + BLOC]
        E = _entrees(p, d, blk, mn)
        T, Pk = _probas(d, E)
        u = rng.random((len(blk), 3))
        vote = u[:, 0] < T
        blanc = vote & (u[:, 1] < P_BLANC_NUL)
        liste = np.minimum((np.cumsum(Pk, 1) < u[:, 2:3]).sum(1), d.K - 1)
        l = E["lieu"]
        s.votants += np.bincount(l[vote], minlength=d.L)[:d.L]
        s.blancs += np.bincount(l[blanc], minlength=d.L)[:d.L]
        ex = vote & ~blanc
        s.voix += np.bincount(l[ex] * d.K + liste[ex], minlength=d.L * d.K)[:d.L * d.K].reshape(d.L, d.K)
        em[blk[vote]] = s.numero
    _depouiller(p, d, s)
    return s


def _depouiller(p, d, s):
    s.voix_nat = s.voix.sum(0); s.valides = int(s.voix_nat.sum())
    s.sieges, s.prime, s.premier = repartir_sieges(s.voix_nat, d.liste, s.S, s.loi)
    d.scrutins.append(s)
    d.sieges = s.sieges.copy()
    d.voix_ref = s.voix_nat / max(1, s.valides)
    val = s.voix.sum(1)
    d.resultat_lieu = np.where(val[None, :] > 0, s.voix.T / np.maximum(val, 1)[None, :], d.resultat_lieu)
    part = float(s.votants.sum()) / max(1, int(s.inscrits.sum()))
    p.noter("resultats_election", lieu=d.lieu_ids[d.capitale], numero=s.numero, participation=round(100 * part, 1),
            premier=d.partis[s.premier].nom if s.premier >= 0 else None,
            sieges={d.partis[k].nom: int(v) for k, v in enumerate(s.sieges.tolist()) if v})
    d.derniere = p.jour
    d.anticipee = False
    coal = former_coalition(s.sieges, d.lr, d.refuse, s.S // 2 + 1)
    if coal is None:
        p.noter("echec_formation", lieu=d.lieu_ids[d.capitale], numero=s.numero)
        d.formation = None; d.investiture_j = None
        convoquer(p, NOUVELLE_ELECTION_J)
    else:
        d.formation = coal; d.investiture_j = p.jour + MANDAT_J
        d.dissous_j = None
        d.prochaine = _dimanche(p, p.jour + DUREE_LEGISLATURE_J - 6)


# ================================================================== la contestation
def _contestation(p):
    """18 h : dans chaque lieu ou les griefs crus depassent un seuil, une part des adultes descend dans la rue ( plus
    si le moral du lieu est bas : `risque_greve` du domaine 23, moins si le lieu soutient le gouvernement ). Quand les
    griefs du pays depassent G_GREVE, les syndicats publics appellent une greve generale de 24 h ( domaine 4 )."""
    d = _dom(p); tb = p.w.table; n = tb.n
    x = np.clip((d.griefs - G_MANIF) / G_MANIF_ECHELLE, 0.0, 1.0) * d.habitable
    lieux = np.nonzero(x > 0)[0]
    if len(lieux):
        v = (tb.vivant[:n] == 1) & (tb.age[:n] >= POP_MAJEUR) & (tb.domicile[:n] >= 0) & (tb.statut[:n] != PO.ABSENT)
        adultes = np.bincount(tb.domicile[:n][v].astype(np.int64), minlength=d.L)[:d.L]
        rng = p.du_jour("politique_manif")
        soutien = d.part_lieu[d.gouv].sum(0)
        for l in lieux.tolist():
            r = R_MANIF * x[l] * (1.0 - soutien[l]) * min(2.0, max(0.5, CU.risque_greve(p, l)))
            nb = int(rng.binomial(int(adultes[l]), min(1.0, r)))
            if nb < MANIF_MIN: continue
            p.noter("manifestation", lieu=d.lieu_ids[l], participants=nb, motif="gouvernement")
            p.compter("participants_manifestation", float(nb))
            d.manifs.append((p.jour, l, nb))
    el = d.electeurs_l.astype(np.float64)
    gn = float((d.griefs * el).sum() / el.sum()) if el.sum() > 0 else 0.0
    if gn >= G_GREVE and p.jour - d.derniere_greve >= GREVE_ESPACEMENT_J and p.a("travail"):
        TR = importlib.import_module(".d04_travail", __package__)
        faites = [r for r in ROLES_ADEDY if TR.declencher_greve(p, None, r, 1, motif="politique") is not None]
        if faites:
            d.derniere_greve = p.jour; d.greves.append((p.jour, tuple(faites), gn))
            p.noter("greve_generale", lieu=d.lieu_ids[d.capitale], roles=",".join(faites), griefs=round(gn, 3))


# ================================================================== le soir
def _soir(p):
    d = _dom(p)
    p.colonnes["habitant"].assurer(p.w.table.n)
    _nouveaux(p, d)
    _lire_le_pays(p, d)
    _opinion(p, d)
    _noter(p, d)
    f = 0.5 ** (1.0 / DEMI_VIE_CAMPAGNE_J)
    d.camp *= f
    _crise(p, d)
    d.serie.append({"jour": p.jour, "parts": d.part_nat.copy(), "participation": d.participation,
                    "griefs": float(d.griefs.mean()), "gouvernement": d.executif.partis if d.executif else ()})


def _cloture(p, comptes):
    d = _dom(p)
    noms = {m for m, _ in MOTIFS}
    for mo, pa, re, s, _ in comptes["argent"]:
        if mo in noms: d.livre_motifs[mo] += s


# ================================================================== ce que le domaine donne aux autres
def intentions(p, lieu=None, groupe=None):
    """Les intentions du dernier soir : { liste : part des votants attendus, "abstention" : part des inscrits }, du pays,
    d un lieu ( identifiant ou numero ) ou d un groupe ( 0 a 8 : classe x 3 + age )."""
    d = _dom(p)
    I = d.intent; A = d.attendus; N = d.inscrits
    if lieu is not None:
        l = d.n_du_lieu[lieu] if isinstance(lieu, str) else int(lieu)
        I, A, N = I[l:l + 1], A[l:l + 1], N[l:l + 1]
    if groupe is not None: I, A, N = I[:, groupe:groupe + 1], A[:, groupe:groupe + 1], N[:, groupe:groupe + 1]
    v = I.sum((0, 1)); a = A.sum(); nn = N.sum()
    out = {x.nom: float(v[x.indice] / a) if a > 0 else 0.0 for x in d.partis}
    out["abstention"] = float(1.0 - a / nn) if nn > 0 else 0.0
    return out


def executif(p):
    """Le gouvernement en place : { partis, chef, programme ( axes ), depuis, origine, sieges, majorite }."""
    d = _dom(p); e = d.executif
    return {"partis": [d.partis[k].nom for k in e.partis], "chef": d.partis[e.chef].nom,
            "programme": dict(zip(AXES, e.programme)), "depuis": e.depuis, "origine": e.origine, "sieges": e.sieges,
            "majorite": d.S // 2 + 1}


def parlement(p):
    d = _dom(p)
    return {x.nom: int(d.sieges[x.indice]) for x in d.partis}


def legitimite(p):
    """Le soutien du gouvernement dans les intentions, rapporte a ses voix au scrutin ( 1 : intact )."""
    d = _dom(p); e = d.executif
    v = sum(e.voix.values())
    return float(d.part_nat[list(e.partis)].sum() / v) if v > 0 else 0.0


def politique_de_defense(p):
    """Domaine 25 : ce que le gouvernement elu decide de la defense. L axe ordre de son programme, le facteur des
    credits d achats de la defense qu il a votes a l investiture ( 1 + 0,3 x ecart au programme de l installation,
    borne par le domaine 6 ), la posture qui en decoule, sa legitimite. Le domaine 25 lit, il ne vote pas."""
    d = _dom(p); e = d.executif
    f = 1.0 + PENTE_DEFENSE * (e.programme[2] - d.programme_ref[2])
    return {"gouvernement": [d.partis[k].nom for k in e.partis], "ordre": e.programme[2],
            "immigration": e.programme[3], "facteur_credits_defense": f,
            "posture": "renforcer" if f > 1.05 else ("reduire" if f < 0.95 else "maintenir"),
            "legitimite": legitimite(p)}


# ================================================================== controles ( pour les portes )
def anomalies(p):
    """Les incoherences : un bureau ou les bulletins depassent les signatures ( vote sans electeur ) ou l inverse ( bulletin
    perdu ), plus de votants que d inscrits, des emargements de la colonne qui ne font pas les votants du dernier
    scrutin, des sieges qui ne sont pas ceux de la loi ( siege sans vote ), des parts hors bornes."""
    d = _dom(p); out = []
    for s in d.scrutins:
        b = s.voix.sum(1) + s.blancs
        for l in np.nonzero(b > s.votants)[0].tolist(): out.append(("vote_sans_electeur", s.numero, d.lieu_ids[l]))
        for l in np.nonzero(b < s.votants)[0].tolist(): out.append(("bulletin_perdu", s.numero, d.lieu_ids[l]))
        for l in np.nonzero(s.votants > s.inscrits)[0].tolist(): out.append(("votants_sans_inscrits", s.numero, d.lieu_ids[l]))
        attendu, _, _ = repartir_sieges(s.voix.sum(0), d.liste, s.S, s.loi)
        for k in np.nonzero(attendu != s.sieges)[0].tolist(): out.append(("siege_sans_vote", s.numero, d.partis[k].nom))
    if d.scrutins:
        s = d.scrutins[-1]
        tb = p.w.table
        signes = int((p.col("habitant", "pol_emarge")[:tb.n] == s.numero).sum())
        if signes != int(s.votants.sum()): out.append(("emargement", s.numero, signes - int(s.votants.sum())))
        if (d.sieges != s.sieges).any(): out.append(("parlement", s.numero, None))
    if ((d.part_lieu < -1e-12) | (d.part_lieu > 1 + 1e-12)).any(): out.append(("part_hors_bornes", None, None))
    return out


def scenario_campagne(jours=12, mode="hasard", graine=7, echelle=5, dans_j=25):
    """La porte de decision : un pays en campagne ( elections convoquees dans `dans_j` jours ), chaque liste decide ses
    tournees dans le mode demande. Rend ( decideur, ( w, p ) )."""
    from . import essais as T
    w, p = T.monde([DOMAINE], graine, echelle, modes={"campagne": mode})
    convoquer(p, dans_j)
    T.jours(w, jours)
    return _dom(p).decideur, (w, p)
