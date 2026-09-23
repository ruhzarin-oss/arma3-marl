"""DOMAINE 6 - ETAT : ADMINISTRATION, FISCALITE, BUDGET, DETTE PUBLIQUE, STATISTIQUE PUBLIQUE.

FICHE
1. Classes. Fisc ( la loi fiscale en vigueur - TVA par categorie du catalogue, bareme et reduction de l impot sur le
   revenu, impot sur les societes, retenue sur dividendes - et ce que le fisc sait des contribuables ), DossierUnite
   ( le dossier fiscal d une entreprise ou d un marche : declarations, pertes reportables, controles ), ControleOuvert
   ( un controle dont la note attend ), Tresor ( le compte du Tresor - la caisse du Gouvernement du moteur - et sa
   gestion : coussin, bons du Tresor, avances de la banque centrale ; l identite budgetaire tenue chaque soir ), Budget
   ( la loi de finances de l exercice civil : credits par ligne et par nature, recettes prevues, execution jour par
   jour, ecart ), Administration ( fonctionnaires par ministere, masse salariale publique, achats publics suivis ),
   Statistique ( ce que l Etat SAIT, avec retard, echantillon et erreur : etat civil, recensement hospitalier, enquete
   aupres des menages, indice des prix, comptes nationaux ), ContexteControle, CerveauEtat ( le gouvernement LLM au
   catalogue etendu ), RemplaceGouverner et RemplaceSitrep ( les methodes du moteur reprises, en objets picklables ),
   Etat ( l etat du domaine ).
   Colonnes par habitant : fisc_revenu ( revenu imposable declare de l exercice ), fisc_sal ( dont salaires et
   pensions ), fisc_retenu ( impot preleve ou mis en recouvrement ), fisc_cache ( revenu non salarial NON declare :
   la verite cachee ), fisc_enfants ( enfants a charge ). Par menage : fisc_propension ( part du revenu non salarial
   que le menage ne declare pas : cachee ), fisc_arrieres ( impot elude des exercices clos : cache ), fisc_controle_j,
   fisc_redresse, fisc_ns_n ( apporteurs non salaries ), fisc_nonsal_ema et fisc_revenu_ema ( declarations lissees ).
2. Invariants. Le domaine ne DETIENT ni argent ni bien : le Tresor est la caisse du Gouvernement du moteur ( famille
   `gouvernement` du registre ) ; les titres et les avances sont des objets du domaine 2 ; les redressements et les
   impots impayes sont des creances du socle ( creancier : le Gouvernement ). Tout paiement passe par le grand livre.
   IDENTITE BUDGETAIRE, chaque soir, au centime : solde = recettes - depenses = - variation de la dette nette ( dette
   brute - caisse ), la dette brute etant lue a part ( avances de la banque centrale + prix des bons non rembourses ).
   Chaque mouvement de la caisse du Tresor est range : recette, depense ( par ligne et par nature ), ou financement ;
   ce que le moteur ecrit a la main ( importer, exporter_or ) est attribue a l appel qui l a fait ; un reste non
   attribue se voit dans l identite. La caisse ne descend jamais sous ce qu il faut : chaque matin un coussin de jours
   de depenses, a 17 h 50 la paie du soir ; un manque est emprunte ( bons, puis avance ) - jamais un impaye de l Etat.
   Le sitrep du gouvernement ne lit que la statistique publiee et ce que l Etat possede ( sa caisse, ses stocks, son
   armee, ses lois ) et les prix AFFICHES ; jamais une incubation, jamais la faim ou le chomage exacts.
   Impot sur le revenu : le revenu impose de chacun ( colonnes ) est exactement ce que la paie a verse a son menage,
   motif par motif ( porte test_ir_par_tranches ) ; la retenue cumulee au bareme est prelevee au centime.
3. Decision `controle_fiscal` ( chaque jour a 10 h ; la moitie des policiers presents, la police financiere comme le
   SDOE grec ; une action du gouvernement regle cette part ) : chaque controleur recoit un lot de sa region ( 6 menages,
   3 unites, pas deja controles ce jour ) et choisit un CRITERE de selection : le menage au plus grand ecart a ses
   pairs, le plus gros menage, l unite au plus grand ecart, la plus grosse unite, un dossier au hasard. Traits ( les
   declarations, jamais la fraude ) des quatre dossiers designes : taille declaree, part non salariale ( menage ) ou
   marge declaree ( unite ), ecart a la mediane declaree des pairs de la region, anciennete du dernier controle,
   antecedents. Note ( horizon 7 jours : le redressement est exigible tout de suite, le reste est saisi sur les
   encaissements de la semaine ; delai legal reel plus long, a calibrer ) : ce que CE controle fait entrer ( impot
   elude et penalite encaisses ) moins la journee du controleur, sur 100 drachmes. Regle : les plus gros ( le plus
   gros menage ou la plus grosse unite, en drachmes par jour declarees ). Temoin : un dossier au hasard.
   Pourquoi des criteres et pas des dossiers : quand l action etait " le dossier k " d un lot tire au hasard, les
   actions etaient interchangeables et la note ne dependait pas du choix ( porte, premiere version ). Le passe fiscal :
   a l installation, le dernier controle de chacun date de 0 a 5 ans ( connu du fisc ) ; un fraudeur a fraude depuis
   au rythme mesure ensuite ( cache ) ; sans lui, un controle ne trouvait que les quelques jours du monde.
4. Evenements. Individuels : controle_fiscal, emission_dette, vote_budget, loi_fiscale. Comptes : retenue_ir,
   remboursement_ir, impot_societes, retenue_dividende, redressement, recouvrement, enquete_menages.
5. Liens. Remplace Monde.gouverner et Monde.sitrep ( proprietaire ) ; remplace le cerveau LLM du moteur par
   CerveauEtat ( meme modele, catalogue etendu ). Neutralise par des donnees : Gouvernement.impot_revenu = 0 ( la
   retenue a la source est ici, au bareme ) ; Gouvernement.tva = le taux equivalent des categories sur le panier de
   l indice des prix ( taux unique transitoire du moteur, du domaine 3 et des soins, tant qu ils n appellent pas
   `taux_tva` ) ; la base de l indice des prix du domaine 2 est reprise au taux en vigueur ( les prix de reference sont
   ceux du regime fiscal du recensement ). Lit : population ( etat civil, ages, enfants ), banques ( reserves, titres,
   avances, taux, indice des prix ), economie ( assiette de l IS, dividendes du mois, chiffres d affaires, licencier
   pour les portes ), la paie du moteur ( 18 h ), les convois et commandes publiques du moteur. Paie et recoit :
   retenues et remboursements d IR ( menage <-> Etat ), IS, retenue sur dividendes, redressements et penalites,
   TVA, douanes, ENFIA, amendes ; emprunte par `souscrire_titre` et `avance_a_l_etat`. Donne ( API en fin de
   fichier ) : domaine 3 taux_tva, prix_ttc, percevoir_tva, taux_tva_equivalent ; domaine 7 taxes_import,
   percevoir_douane, balance_des_paiements ; domaine 12 percevoir, taxe_locale ; domaine 13 enfia, percevoir_enfia,
   droits_permis, DELAI_PERMIS_J ; domaine 21 infliger_amende, creances_de_l_etat, recouvrer ; domaine 22
   publications ; domaine 24 CATALOGUE_ETAT, appliquer, voter_budget, sitrep ; tous : dette_brute, execution_budget.
6. Portes : tests_d06_etat.py.
7. Arma : aucun objet ( un ministere, un bureau des impots sont des batiments, domaine 13 ; le controleur a le corps
   du policier ).
8. Cout. 17 h 50 : une photo des caisses et des heures ; 18 h : trois passes vectorisees sur les habitants, un
   paiement par menage dont l impot du jour depasse un centime ; 10 h : un index des menages par region, un point de
   decision par controleur ; soir : le recensement hospitalier ( une passe ), l enquete ( quelques menages ), les
   comptes du jour ( lignes du grand livre ), la tenue du budget. Mesure du 23/09 ( test_cout, 10 000 habitants ) :
   66 ms par jour, 3,9 % d une journee du moteur, 6,6 us par habitant ( controles 41 ms, paie fiscale 15, cloture 7 ) ;
   lineaire en habitants et en controleurs : ~ 7 s par jour a 1 million, ~ 5,5 minutes a 50 millions ( les controles
   dominent : un lot et ses traits par controleur ; a reduire par un tirage des controleurs a cette echelle )."""
import datetime as dt, hashlib, json, math, time, urllib.request
from collections import deque
import numpy as np
from .. import config as C, population as PO, gouvernement as G
from ..socle import decision as D
from . import d01_population as POP, d02_banques as BQ, d03_economie as EC

JOURS_AN = 365.0
EPS = 1e-9
PAS_H = C.MINUTES_PAR_PAS / 60.0

# ================================================================== la loi fiscale ( Grece prise pour modele )
# TVA : Code de la TVA ( loi 2859/2000, art. 21 et annexe III ) ; taux en vigueur depuis juin 2016 : normal 24 %,
# reduit 13 % ( alimentation, eau, energie domestique ), super-reduit 6 % ( medicaments, livres ). Les taux insulaires
# reduits de 30 % ont ete supprimes pour la plupart des iles de 2016 a 2019 : non modelises.
TAUX_TVA = {"normale": 0.24, "reduite": 0.13, "super_reduite": 0.06, "exoneree": 0.0}
# Bornes d action : directive 2006/112/CE ( normal >= 15 %, reduit >= 5 % ) ; plafond de l Union ( 27 %, Hongrie ).
BORNES_TVA = {"normale": (0.15, 0.27), "reduite": (0.05, 0.17), "super_reduite": (0.0, 0.10), "exoneree": (0.0, 0.0)}
# Impot sur le revenu des personnes : loi 4172/2013 art. 15, bareme de la loi 4646/2019 ( exercices 2020 et suivants ) :
# 9 % jusqu a 10 000, 22 % jusqu a 20 000, 28 % jusqu a 30 000, 36 % jusqu a 40 000, 44 % au-dela ( drachmes = euros ).
TRANCHES_IR = (10000.0, 20000.0, 30000.0, 40000.0)
TAUX_IR = (0.09, 0.22, 0.28, 0.36, 0.44)
BORNES_TAUX_IR = (0.0, 0.55)
# Reduction d impot des salaries et retraites ( art. 16 ) : 777 sans enfant, 810, 900, 1 120, 1 340 avec 1 a 4 enfants,
# + 220 par enfant au-dela ; diminuee de 20 par 1 000 de revenu salarial au-dela de 12 000 ( pas de diminution a partir
# de 5 enfants ). Limitee a l impot du revenu salarial ( partage au prorata des revenus ). A verifier par Younes.
REDUCTION_IR = (777.0, 810.0, 900.0, 1120.0, 1340.0)
REDUCTION_PAR_ENFANT_SUP = 220.0
SEUIL_DEGRESSIVITE = 12000.0
DEGRESSIVITE = 0.02
TAUX_DIVIDENDE = 0.05              # retenue liberatoire sur dividendes ( art. 64, 5 % depuis 2020 )
# Impot sur les societes : art. 58, 22 % depuis l exercice 2021 ( loi 4799/2021 ) ; cooperatives agricoles 10 % ( a
# verifier ) ; pertes reportables 5 ans ( art. 27 ). L acompte grec de 80 % n est pas modelise : l impot est liquide
# chaque mois sur le resultat du mois clos ( assiette du domaine 3 ).
TAUX_IS = 0.22
TAUX_IS_COOPERATIVE = 0.10
BORNES_IS = (0.10, 0.35)
REPORT_PERTES_J = 5 * 365
# Penalite d inexactitude ( Code de procedure fiscale, loi 4987/2022, art. 58 ) : 10 % de l impot elude s il fait de
# 5 a 20 % de l impot declare, 25 % de 20 a 50 %, 50 % au-dela ; rien sous 5 %. Interets de retard non modelises.
PENALITES = ((0.05, 0.0), (0.20, 0.10), (0.50, 0.25), (math.inf, 0.50))
# Douanes ( pour le domaine 7 ) : ordre de grandeur du tarif exterieur commun ( TARIC ) par famille de biens, a calibrer
# bien par bien ; la TVA a l importation porte sur la valeur en douane plus le droit.
DROITS_DOUANE = {"aliment": 0.10, "eau": 0.0, "matiere_premiere": 0.0, "energie": 0.0, "materiau": 0.03,
                 "chimie": 0.045, "produit_fini": 0.04, "piece": 0.03, "sante": 0.0, "munition": 0.0}
# ENFIA ( loi 4223/2013, art. 4 ) : impot principal = surface x tarif de base de la zone ( drachmes par m2, selon la
# valeur de zone en drachmes par m2 ) x coefficients ( age, etage, facades : 1 par defaut ). Tableau de 2014, a verifier ;
# l impot complementaire et les baisses de 2019-2022 ne sont pas modelises.
ENFIA_ZONES = ((550.0, 2.0), (750.0, 2.8), (1050.0, 2.9), (1500.0, 3.7), (2000.0, 4.5), (2500.0, 6.0), (3000.0, 6.8),
               (3500.0, 7.5), (4000.0, 9.0), (4500.0, 9.5), (5000.0, 10.2), (math.inf, 11.1))
DROITS_PERMIS = 0.005             # droits d un permis de construire, part du devis ( a calibrer )
DELAI_PERMIS_J = 90               # instruction d un permis ( a calibrer )
TAXE_LOCALE_M2_AN = 1.5           # taxes communales de proprete et d eclairage, drachmes par m2 et par an ( a calibrer )

# ================================================================== la fraude ( verite cachee, a calibrer )
# Menages non salaries : Artavanis, Morse et Tsoutsoura ( QJE 2016 ) estiment que les independants grecs declarent
# 55 a 57 % de leur revenu. Ici : 20 % d honnetes, les autres cachent une part Beta( 3 ; 2,5 ) ( moyenne 0,55 ) :
# 0,44 en moyenne. Les salaires et pensions sont retenus a la source par le payeur : rien a cacher.
PART_HONNETES_MENAGES = 0.2
BETA_MENAGES = (3.0, 2.5)
# Unites ( IS ) : 30 % d honnetes, les autres cachent une part Beta( 2 ; 5 ) du resultat ( moyenne 0,29 ).
PART_HONNETES_UNITES = 0.3
BETA_UNITES = (2.0, 5.0)
DISSUASION = 0.5                  # un contribuable redresse cache ensuite deux fois moins ( Kleven et al. 2011, a calibrer )
# Le passe fiscal : a l installation, le dernier controle de chaque contribuable date de 0 a 5 ans ( la prescription,
# loi 4987/2022 art. 36 ) - une date que le fisc connait ; un fraudeur a fraude depuis, au rythme qu on lui mesure
# aujourd hui. Sans ce passe, tout le pays partait d une ardoise vierge et un controle ne trouvait que quelques jours.
PASSE_MAX_ANS = 5.0
NON_SALARIAUX = ("paysan", "marchand", "patron")

# ================================================================== le Tresor et la dette
TRESORERIE_PAR_HABITANT = 400.0   # la dotation du moteur ( 200 000 ) rapportee a sa population de reference ( 500 )
PROPORTIONNER_TRESORERIE = True   # une donnee : a l installation, la caisse du Tresor suit la population
FINANCEMENT_AUTOMATIQUE = True    # le Tresor emprunte ce qui lui manque ( les portes le coupent pour le controle positif )
JOURS_COUSSIN = 7                 # jours de depenses gardes en caisse chaque matin ( a calibrer ; l agence grecque de
                                  # la dette tient un coussin de plusieurs mois depuis 2018 )
DUREE_BONS_J = 91                 # bons du Tresor a 13 semaines ( PDMA : 13, 26 et 52 semaines )
DUREES_BONS = (91, 182, 364)
PRIME_BONS = 0.0010               # rendement des bons : facilite de depot + 10 points de base ( a calibrer )
LOT_MIN_BONS = 100.0
MARGE_RESERVES = 0.02             # part de ses depots qu une banque garde libre au-dela des reserves obligatoires
MOTIFS_FINANCEMENT = ("avance_bc", "remboursement_avance_bc", "souscription_titre", "remboursement_titre")
MOTIFS_ETAT_SEUL = ("salaire public", "pension", "commande publique", "subvention", "remboursement_ir",
                    "interet_titre", "interet_avance_bc")    # ce que seul l Etat paie : un impaye ici, c est le Tresor a sec

# ================================================================== le budget
LIGNES = ("presidence",) + tuple(C.MINISTERES) + ("pensions", "subventions", "dette", "autres")
NATURES_DEPENSE = ("personnel", "achats", "transferts", "interets")
CATEGORIES_RECETTES = ("tva", "ir", "is", "dividendes", "douanes", "enfia", "amendes", "controle_fiscal", "electricite",
                       "vente_or", "domaine", "autres")
MINISTERE_DU_ROLE = {"chef_gouvernement": "presidence", "officier": "defense", "soldat": "defense",
                     "policier": "interieur", "medecin": "sante", "infirmier": "sante", "enseignant": "education"}
LIGNE_DESTINATION = {"hopitaux": "sante", "armee": "defense", "reserve": "interieur", "population": "interieur"}
LIGNE_BIEN = {"remedes": "sante", "carburant": "defense"}
RECETTE_DU_MOTIF = {"tva": "tva", "tva_import": "tva", "impot sur le revenu": "ir", "impot": "ir", "retenue_ir": "ir",
                    "impot_societes": "is", "retenue_dividende": "dividendes", "droit_de_douane": "douanes",
                    "enfia": "enfia", "taxe_locale": "autres", "droits_permis": "autres", "amende": "amendes",
                    "penalite_fiscale": "amendes", "redressement_fiscal": "controle_fiscal", "electricite": "electricite",
                    "desherence": "domaine", "dividende_banque": "domaine", "benefice_bc": "domaine"}
HEURES_HORAIRE = {"bureau": 9.0, "garde": 8.0, "ecole": 7.0, "jour": 8.0, "marche": 11.0}
REMEDES_PAR_HABITANT_AN = 0.5     # traitements achetes par l Etat, par habitant et par an ( provision, a calibrer )
PROVISION_ACHATS = 0.05           # achats courants d un ministere, en part de sa masse salariale ( a calibrer )
PROVISION_SUBVENTIONS = 0.02      # subventions, en part de la masse salariale publique ( a calibrer )

# ================================================================== la statistique publique
TAUX_ENQUETE_J = 6.6e-5           # menages interroges par jour : ~0,6 % par trimestre, comme l enquete emploi d ELSTAT
ENQUETE_MIN_J = 4                 # ... mais un petit pays interroge au moins 120 menages par mois ( precision, a calibrer )
FENETRE_CHOMAGE_J = 30
FENETRE_FAIM_J = 7
FENETRE_COMPTES_J = 30
Z95 = 1.959964

# ================================================================== la decision
HORIZON_CONTROLE = 7
LOT_MENAGES, LOT_UNITES = 6, 3    # les dossiers du jour d un controleur, tires dans sa region ( a calibrer )
CRITERES = ("menage_ecart", "menage_gros", "unite_ecart", "unite_grosse", "au_hasard")
AU_HASARD = CRITERES.index("au_hasard")
PART_CONTROLEURS = 0.5            # part des policiers presents a 10 h affectee au controle fiscal
NORME_CONTROLE = 100.0            # drachmes : l unite de la note
COUT_CONTROLE = 8.0 * PO.SALAIRE_HORAIRE["policier"]   # la journee du controleur ( 8 h ), drachmes
REF_REVENU_J = 200.0              # drachmes par jour : un revenu declare au-dela est un gros dossier
REF_CA_MOIS = 60000.0             # drachmes par mois : un chiffre d affaires au-dela est un gros dossier
PART_SAISIE = 0.5                 # part de ce qui est saisissable prise chaque jour ( a calibrer )
RESERVE_INSAISISSABLE_J = 7       # jours de nourriture laisses au menage

# ================================================================== le gouvernement : actions bornees
BORNES_INTENSITE = (0.5, 3.0)
CATALOGUE_ETAT = """Actions permises ( JSON, une liste ; toute action hors bornes est refusee ) :
- {"type": "fixer_tva", "categorie": "normale" | "reduite" | "super_reduite", "valeur": nombre}
      ( normale 0,15-0,27 ; reduite 0,05-0,17 ; super_reduite 0-0,10 ; super_reduite <= reduite <= normale )
- {"type": "fixer_ir", "tranche": 0 a 4, "taux": nombre}
      ( 0-0,55 ; les taux ne baissent jamais d une tranche a la suivante )
- {"type": "fixer_is", "valeur": nombre}                             ( 0,10-0,35 )
- {"type": "fixer_budget", "ligne": ligne, "montant": nombre}
      ( credits d achats de la ligne : au moins l engage, au plus 3 fois le vote )
- {"type": "emettre_dette", "montant": nombre, "duree_j": 91 | 182 | 364}   ( bons du Tresor, au plus 60 jours de depenses )
- {"type": "rembourser_avance", "montant": nombre}                   ( au plus la caisse au-dela du coussin )
- {"type": "fixer_controle", "part": nombre}          ( part des policiers presents affectes au controle fiscal, 0-1 )
- {"type": "fixer_intensite_controle", "valeur": nombre}              ( controles de la fraude a la TVA, 0,5-3 )
- {"type": "fixer_salaires_publics", "facteur": nombre}              ( 0,5-2,0 )
- {"type": "acheter", "bien": bien, "quantite": nombre, "destination": "hopitaux" | "armee" | "reserve" | "population"}
      ( dans les credits d achats du ministere : hopitaux -> sante, armee -> defense, reserve et population -> interieur )
- {"type": "importer", "bien": bien, "quantite": nombre}               ( prix mondial + 20 %, dans les credits )
- {"type": "exporter_or", "quantite": nombre}
- {"type": "couvre_feu", "debut": heure, "fin": heure}  ou  {"type": "couvre_feu", "debut": null}
- {"type": "quarantaine", "lieu": lieu, "levee": false}
- {"type": "rationnement", "par_jour": nombre | null}
- {"type": "subvention", "cible": "menages_pauvres" | "fermes" | "hopitaux", "montant": nombre}
      ( dans les credits de la ligne subventions ; hopitaux : dans ceux de la sante )
- {"type": "rien"}
Lignes budgetaires : """ + ", ".join(LIGNES)


# ================================================================== la loi, en fonctions pures
def _sortie(x):
    x = np.asarray(x, dtype=np.float64)
    return float(x) if x.ndim == 0 else x


def bareme_ir(revenu, taux=TAUX_IR, tranches=TRANCHES_IR):
    """L impot du bareme sur un revenu ANNUEL ( drachmes ), scalaire ou tableau : chaque tranche a son taux."""
    y = np.asarray(revenu, dtype=np.float64)
    t = np.zeros_like(y); bas = 0.0
    for k, haut in enumerate(tuple(tranches) + (math.inf,)):
        t = t + taux[k] * np.clip(y - bas, 0.0, haut - bas)
        bas = haut
    return _sortie(t)


def reduction_ir(revenu_sal, enfants):
    """La reduction d impot des salaries et retraites ( art. 16 ), selon le revenu salarial annuel et les enfants a charge."""
    ys = np.asarray(revenu_sal, dtype=np.float64)
    e = np.asarray(enfants, dtype=np.int64)
    base = np.asarray(REDUCTION_IR)[np.minimum(e, 4)] + REDUCTION_PAR_ENFANT_SUP * np.maximum(0, e - 4)
    degr = np.where(e >= 5, 0.0, DEGRESSIVITE * np.maximum(0.0, ys - SEUIL_DEGRESSIVITE))
    return _sortie(np.maximum(0.0, base - degr))


def impot_annuel(revenu, revenu_sal, enfants=0, taux=TAUX_IR, tranches=TRANCHES_IR):
    """L impot d un exercice : le bareme sur tout le revenu, moins la reduction, dans la limite de la part de l impot
    qui revient aux salaires et pensions ( partage au prorata des revenus )."""
    y = np.asarray(revenu, dtype=np.float64)
    ys = np.minimum(np.asarray(revenu_sal, dtype=np.float64), y)
    b = np.asarray(bareme_ir(y, taux, tranches), dtype=np.float64)
    part = np.divide(ys, y, out=np.zeros_like(y * 1.0), where=y > 0)
    r = np.minimum(b * part, np.asarray(reduction_ir(ys, enfants), dtype=np.float64))
    return _sortie(np.maximum(0.0, b - r))


def impot_cumule(revenu, revenu_sal, enfants, d, duree, taux=TAUX_IR, tranches=TRANCHES_IR):
    """La retenue cumulee due apres `d` jours d un exercice de `duree` jours ( methode cumulative, comme le prelevement a
    la source des salaires ) : le revenu de la periode est extrapole a l exercice, l impot de l exercice est ramene aux
    jours ecoules. Au dernier jour ( d = duree ) c est l impot exact de l exercice : la regularisation est faite."""
    if not 1 <= d <= duree: raise ValueError(f"jour {d} hors de l exercice de {duree} jours")
    a = duree / d
    return _sortie(np.asarray(impot_annuel(np.asarray(revenu) * a, np.asarray(revenu_sal) * a, enfants, taux, tranches))
                   * (d / duree))


def taux_penalite(elude, declare):
    """Le taux de la penalite d inexactitude : selon l impot elude rapporte a l impot declare."""
    if elude <= EPS: return 0.0
    ratio = elude / declare if declare > EPS else math.inf
    for seuil, taux in PENALITES:
        if ratio < seuil or seuil == math.inf: return taux
    return PENALITES[-1][1]


def impot_societes(base, pertes, jour, taux=TAUX_IS):
    """L IS d un mois : une perte entre aux reports ( `pertes` : [ jour, montant ], modifiee sur place ) ; un benefice
    impute d abord les pertes de moins de 5 ans, les plus vieilles en premier. Rend ( impot, base imposable )."""
    pertes[:] = [x for x in pertes if jour - x[0] <= REPORT_PERTES_J and x[1] > EPS]
    if base <= 0.0:
        if base < -EPS: pertes.append([jour, -base])
        return 0.0, 0.0
    reste = base
    for x in pertes:
        imp = min(reste, x[1]); x[1] -= imp; reste -= imp
        if reste <= EPS: break
    pertes[:] = [x for x in pertes if x[1] > EPS]
    return taux * reste, reste


def enfia(surface_m2, valeur_zone_m2, coefficient=1.0):
    """L impot principal ENFIA d un batiment, en drachmes par an."""
    if not surface_m2 >= 0 or not valeur_zone_m2 >= 0 or not coefficient > 0: raise ValueError("ENFIA : donnees invalides")
    tarif = next(t for borne, t in ENFIA_ZONES if valeur_zone_m2 <= borne)
    return surface_m2 * tarif * coefficient


def droits_permis(valeur_travaux):
    if not valeur_travaux >= 0: raise ValueError("devis negatif")
    return DROITS_PERMIS * valeur_travaux


def taxe_locale(surface_m2, jours=1):
    """Les taxes communales d un logement ou d un local, pour `jours` jours ( domaine 12 )."""
    return TAXE_LOCALE_M2_AN * surface_m2 * jours / JOURS_AN


# ================================================================== les classes
class DossierUnite:
    """Le dossier fiscal d une entreprise ou d un marche.
      propension          part du resultat que l unite ne declare pas ( VERITE CACHEE )
      elude               IS elude non redresse, drachmes ( cache )
      pertes              [ jour, montant ] : pertes reportables
      ca, resultat, impot le dernier mois declare : chiffre d affaires, resultat declare, IS declare
      controle_j, redresse le dernier controle, le nombre de redressements"""
    __slots__ = ("id", "propension", "elude", "pertes", "ca", "resultat", "impot", "controle_j", "redresse", "cooperative")

    def __init__(self, id, propension, cooperative):
        if not 0.0 <= propension <= 1.0: raise ValueError(f"{id} : propension hors [0 ; 1]")
        self.id, self.propension, self.cooperative = id, float(propension), cooperative
        self.elude = 0.0
        self.pertes = []
        self.ca = self.resultat = self.impot = 0.0
        self.controle_j, self.redresse = -100000, 0


class Fisc:
    """La loi fiscale en vigueur, les dossiers, les creances fiscales, les controles ouverts."""
    __slots__ = ("tva", "taux_ir", "tranches_ir", "taux_is", "taux_is_coop", "taux_dividende", "debut", "fin", "jour0",
                 "caisse_1750", "heures_1750", "unites", "creances", "controles", "prochain_controle", "part_controleurs",
                 "revenus", "compte", "notes")

    def __init__(self, debut, fin):
        self.tva = dict(TAUX_TVA)
        self.taux_ir, self.tranches_ir = tuple(TAUX_IR), tuple(TRANCHES_IR)
        self.taux_is, self.taux_is_coop, self.taux_dividende = TAUX_IS, TAUX_IS_COOPERATIVE, TAUX_DIVIDENDE
        self.debut, self.fin = debut, fin          # l exercice fiscal : jours du monde, bornes comprises
        self.jour0 = debut                          # l installation : avant, le passe fiscal ( cache )
        self.caisse_1750 = self.heures_1750 = None
        self.unites = {}            # id d unite -> DossierUnite
        self.creances = []          # creances fiscales de l Etat, dans l ordre de leur naissance
        self.controles = {}         # cle -> ControleOuvert
        self.prochain_controle = 0
        self.part_controleurs = PART_CONTROLEURS
        self.revenus = {k: 0.0 for k in ("salaires", "pensions", "non_salarial", "declare", "non_attribue")}
        self.compte = {k: 0.0 for k in ("retenue_ir", "remboursement_ir", "impot_societes", "is_elude", "dividendes",
                                         "redressements", "penalites", "recouvre", "controles", "controles_positifs")}
        self.notes = deque(maxlen=20000)   # ( jour ou la note murit, dossier choisi, note ) : la mesure de la decision

    def jours_exercice(self, jour):
        return jour - self.debut + 1, self.fin - self.debut + 1


class ControleOuvert:
    """Un controle dont la note attend : ce que ses creances font entrer, jour apres jour, pendant l horizon.
      encaisse, total   drachmes entrees depuis la derniere note ; depuis le controle ( notees )
      action            le dossier choisi ( indice ), -1 hors du point de decision"""
    __slots__ = ("cle", "controleur", "cible", "creances", "jour", "encaisse", "total", "jours", "redressement",
                 "penalite", "action")

    def __init__(self, cle, controleur, cible, jour, action=-1):
        self.cle, self.controleur, self.cible, self.jour, self.action = cle, controleur, cible, jour, action
        self.creances = []
        self.encaisse = self.total = self.redressement = self.penalite = 0.0
        self.jours = 0


class Tresor:
    """Le compte du Tresor ( la caisse du Gouvernement du moteur ) et la tenue de l identite budgetaire.
      financement         vrai : un manque est emprunte ( bons, puis avance de la banque centrale )
      coussin_j, duree_bons_j, prime_bons   la politique de tresorerie
      depense_moyenne     drachmes par jour ( moyenne mobile 30 jours des depenses ) : la mesure du coussin
      caisse_prec, dette_prec   au dernier soir : l identite se lit sur leurs variations
      base                les lignes du grand livre du jour de l installation, d avant l installation
      hors_livre          ( cle, montant signe ) : ce que le moteur ecrit a la main, attribue a l action qui l a fait
      serie               ( jour, recettes, depenses, solde, financement, dette, caisse, ecart, non attribue )"""
    __slots__ = ("financement", "coussin_j", "duree_bons_j", "prime_bons", "depense_moyenne", "caisse_prec", "dette_prec",
                 "base", "hors_livre", "serie", "pire_ecart", "ecart_cumule", "emis_bons", "emis_avances", "n_bons",
                 "ext_prec", "caisse0", "dette0", "ouverture", "paie_hier")

    def __init__(self, caisse, dette, ext):
        self.financement = FINANCEMENT_AUTOMATIQUE
        self.coussin_j, self.duree_bons_j, self.prime_bons = JOURS_COUSSIN, DUREE_BONS_J, PRIME_BONS
        self.depense_moyenne = 0.0
        self.caisse_prec = self.caisse0 = caisse
        self.dette_prec = self.dette0 = dette
        self.base = None
        self.hors_livre = []
        self.serie = deque(maxlen=800)
        self.pire_ecart = self.ecart_cumule = 0.0
        self.emis_bons = self.emis_avances = 0.0
        self.n_bons = 0
        self.ext_prec = dict(ext)
        self.ouverture = 0.0
        self.paie_hier = 0.0          # salaires publics et pensions payes hier : la paie a assurer ce soir


class Budget:
    """La loi de finances d un exercice civil.
      credits, votes      ( ligne, nature ) -> drachmes autorisees ; les credits de la loi initiale
      prevues             categorie -> recettes prevues
      depenses, recettes  l execution, jour par jour
      engage              ligne -> achats commandes non encore livres
      Les credits d achats sont LIMITATIFS ( une commande qui les depasse est refusee ) ; personnel, pensions, interets
      et achats du reseau electrique sont EVALUATIFS ( ils s executent, l ecart se lit )."""
    __slots__ = ("exercice", "debut", "jours", "credits", "votes", "prevues", "depenses", "recettes", "engage")

    def __init__(self, exercice, debut, jours, credits, prevues):
        self.exercice, self.debut, self.jours = exercice, debut, jours
        self.credits = dict(credits); self.votes = dict(credits)
        self.prevues = dict(prevues)
        self.depenses = {k: 0.0 for k in credits}
        self.recettes = {k: 0.0 for k in CATEGORIES_RECETTES}
        self.engage = {l: 0.0 for l in LIGNES}

    def disponible(self, ligne):
        return self.credits.get((ligne, "achats"), 0.0) - self.depenses.get((ligne, "achats"), 0.0) - self.engage.get(ligne, 0.0)


class Administration:
    """Les agents publics par ministere, la masse salariale, les achats publics suivis ( pour ventiler le budget )."""
    __slots__ = ("effectifs", "masse", "poids_salaires", "commandes", "convois", "dernier_convoi")

    def __init__(self):
        self.effectifs = {l: 0 for l in LIGNES}
        self.masse = {l: 0.0 for l in LIGNES}       # salaires publics verses depuis l installation, par ligne
        self.poids_salaires = {}                    # ligne -> salaires publics prevus aujourd hui ( la cle de ventilation )
        self.commandes = []                         # [ commande du moteur, ligne, quantite vue, prix unitaire estime ]
        self.convois = {}                           # ligne -> poids ( duree ) des convois payes par l Etat aujourd hui
        self.dernier_convoi = 0


class Statistique:
    """Ce que l Etat SAIT. `publie` est ce que le gouvernement lit : chaque soir, pour le lendemain."""
    __slots__ = ("publie", "population", "sante", "enquete", "comptes", "hospitalises", "base_naissances", "base_deces",
                 "base_morts_maladie", "n_menages")

    def __init__(self):
        self.publie = {}
        self.population = deque(maxlen=800)
        self.sante = deque(maxlen=800)
        self.enquete = deque(maxlen=FENETRE_CHOMAGE_J)    # ( jour, y chomeurs, x actifs, faim, taille ) par menage interroge
        self.comptes = deque(maxlen=800)
        self.hospitalises = set()
        self.base_naissances = self.base_deces = self.base_morts_maladie = 0
        self.n_menages = 0


class ContexteControle:
    """Ce qu un controleur voit de son lot : les traits des quatre dossiers que designent les criteres, ces dossiers
    ( None si le lot n en a pas ), leurs bases declarees en drachmes par jour ( -1 : absent )."""
    __slots__ = ("traits", "cibles", "tailles")

    def __init__(self, traits, cibles, tailles): self.traits, self.cibles, self.tailles = traits, cibles, tailles


class Etat:
    """L etat du domaine."""
    __slots__ = ("fisc", "tresor", "budget", "admin", "stat", "decideur", "chrono", "decisions")

    def __init__(self, fisc, tresor, budget, admin, stat):
        self.fisc, self.tresor, self.budget, self.admin, self.stat = fisc, tresor, budget, admin, stat
        self.decideur = None
        self.chrono = {}
        self.decisions = deque(maxlen=400)


def _chrono(e, nom, t0):
    e.chrono[nom] = e.chrono.get(nom, 0.0) + time.perf_counter() - t0


# ================================================================== le point de decision
def _observer_controle(ctx): return ctx.traits


def _regle_controle(x, ctx):
    """Les plus gros : le plus gros menage ou la plus grosse unite du lot, selon la base declaree en drachmes par jour."""
    return 3 if ctx.tailles[3] > ctx.tailles[1] else 1


def _temoin_controle(x, ctx, rng): return AU_HASARD


def _traits_declares():
    out = []
    for k, (c, g) in enumerate((("me", "le menage au plus grand ecart"), ("mg", "le plus gros menage"),
                                ("ue", "l unite au plus grand ecart"), ("ug", "la plus grosse unite"))):
        out += [(f"taille_{c}", f"{g} du lot : base declaree ( revenu du jour lisse, ou chiffre d affaires du mois ), bornee"),
                (f"part_{c}", f"{g} : part non salariale du revenu declare ( menage ) ou marge declaree ( unite )"),
                (f"ecart_{c}", f"{g} : ecart a la mediane declaree des pairs de la region ( 0 : comme eux )"),
                (f"anciennete_{c}", f"{g} : jours depuis son dernier controle, sur 365"),
                (f"antecedents_{c}", f"{g} : redressements passes, sur 3")]
    return tuple(out)


POINT_CONTROLE = D.PointDeDecision(
    "controle_fiscal", "etat", traits=_traits_declares(), actions=CRITERES,
    observer=_observer_controle, regle=_regle_controle, temoin=_temoin_controle,
    note="ce que CE controle fait entrer ( impot elude et penalite encaisses sur 7 jours ) moins la journee du "
         "controleur, sur 100 drachmes",
    horizon_j=HORIZON_CONTROLE)


# ================================================================== petits outils
def _etat(p): return p.domaine("etat")


def _net_gouv(p):
    return p.socle.livre.net_par_classe().get("Gouvernement", 0.0)


def _vivants(mg): return sum(1 for x in mg.membres if x.vivant)


def _saisissable(p, deb):
    """Ce que le fisc peut prendre aujourd hui : la moitie de la caisse, au-dela d une semaine de nourriture pour un menage."""
    w = p.w
    if type(deb) is PO.Menage:
        if p.col("menage", "dissous")[deb.id]: return 0.0
        prix = w.marches[deb.domicile.marche.id].prix["nourriture"] * (1.0 + w.gouv.tva)
        reserve = RESERVE_INSAISISSABLE_J * _vivants(deb) * C.NOURRITURE_PAR_JOUR * prix
        return max(0.0, PART_SAISIE * (deb.caisse - reserve))
    return max(0.0, PART_SAISIE * deb.caisse)


def _date(p, jour):
    return p.socle.calendrier.date(p.w.pas).date() + dt.timedelta(days=jour - p.jour)


def _fin_d_annee(p, jour):
    d = _date(p, jour)
    return jour + (dt.date(d.year, 12, 31) - d).days


def dette_brute(p):
    """La dette du Tresor, lue a part : avances de la banque centrale + prix d emission des bons non rembourses."""
    bq = p.domaine("banques")
    return math.fsum([bq.bc.avances] + [t.prix for t in bq.titres.values()])


def dette_nominale(p):
    """La dette au sens de Maastricht : les bons a leur valeur de remboursement."""
    bq = p.domaine("banques")
    return math.fsum([bq.bc.avances] + [t.prix + t.interet for t in bq.titres.values()])


def _ministere(h):
    if h.role == "ministre":
        suffixe = h.nom.rsplit("-", 1)[-1]
        return suffixe if suffixe in C.MINISTERES else "presidence"
    return MINISTERE_DU_ROLE.get(h.role, "autres")


# ================================================================== les roles, en tableaux
ROLES = tuple(C.ROLES)
ROLE_IDX = {r: k + 1 for k, r in enumerate(ROLES)}
SAL_ROLE = np.array([0.0] + [float(PO.SALAIRE_HORAIRE.get(r, 0)) for r in ROLES])
PUB_ROLE = np.array([False] + [bool(C.ROLES[r][2]) for r in ROLES])
# categorie de revenu : 0 aucun, 1 salarie, 2 retraite, 3 non salarie ( paysan, marchand, patron )
CAT_ROLE = np.array([0] + [2 if r == "retraite" else 3 if r in NON_SALARIAUX else 1 if PO.SALAIRE_HORAIRE.get(r, 0) > 0
                           else 0 for r in ROLES], dtype=np.int64)
I_MINISTRE = ROLE_IDX["ministre"]
MIN_ROLE = np.array([LIGNES.index("autres")] + [LIGNES.index(MINISTERE_DU_ROLE.get(r, "autres")) for r in ROLES],
                    dtype=np.int64)


# ================================================================== la TVA ( API du domaine 3 )
def taux_tva(p, bien):
    """Le taux de TVA d un bien : celui de sa categorie au catalogue ( Bien.categorie_tva )."""
    return _etat(p).fisc.tva[p.socle.catalogue[bien].categorie_tva]


def prix_ttc(p, bien, prix_ht): return prix_ht * (1.0 + taux_tva(p, bien))


def percevoir_tva(p, payeur, bien, montant_ht):
    """La TVA d un achat, au taux de la categorie du bien, payee a l Etat ( motif tva ). Rend ce qui a ete paye.
    Le domaine 3 remplace son taux unique par cet appel ( et `prix_ttc` dans le budget du menage ) : la TVA ne passe
    pas par le marche, son identite comptable ne bouge pas ; w.tva_percue reste tenu."""
    paye = p.socle.livre.transferer(payeur, p.w.gouv, montant_ht * taux_tva(p, bien), "tva")
    p.w.tva_percue += paye
    return paye


def taux_tva_equivalent(p):
    """Le taux unique qui leve la meme TVA que les categories sur le panier de l indice des prix ( domaine 2 ) : ce que
    le moteur applique tant qu il ne connait pas les categories."""
    return math.fsum(poids * taux_tva(p, b) for b, poids in BQ.POIDS_INDICE.items())


# ================================================================== le Tresor
def _capacites_bons(p):
    """Ce que chaque banque peut placer en bons : ses reserves au-dela des reserves obligatoires et d une marge."""
    out = []
    for b in p.domaine("banques").banques:
        depots = max(0.0, b.solde_cercle - b.caisse)
        out.append(max(0.0, b.reserves - (BQ.RATIO_RESERVES + MARGE_RESERVES) * depots))
    return out


def taux_des_bons(p):
    bc = p.domaine("banques").bc
    return max(0.0, bc.taux_depot() + _etat(p).tresor.prime_bons)


def emettre_bons(p, montant, duree_j=None):
    """Adjudication de bons du Tresor aux banques, au prorata de ce qu elles peuvent placer. Rend le prix encaisse."""
    e = _etat(p); tr = e.tresor
    d = int(duree_j or tr.duree_bons_j)
    caps = _capacites_bons(p)
    tot = math.fsum(caps)
    if tot < LOT_MIN_BONS or montant < LOT_MIN_BONS: return 0.0
    part = min(montant, tot)
    taux = taux_des_bons(p)
    recu = 0.0
    for b, c in zip(p.domaine("banques").banques, caps):
        x = part * c / tot
        if x < LOT_MIN_BONS: continue
        t = BQ.souscrire_titre(p, b, x * (1.0 + taux * d / JOURS_AN), taux, d)
        recu += t.prix; tr.n_bons += 1
    tr.emis_bons += recu
    if recu > 0: p.noter("emission_dette", instrument="bons", montant=round(recu, 2), taux=round(taux, 5), duree=d)
    return recu


def emprunter(p, montant, duree_j=None):
    """Couvre un besoin de tresorerie : des bons d abord, le reste par une avance de la banque centrale."""
    if montant <= EPS: return 0.0
    tr = _etat(p).tresor
    recu = emettre_bons(p, montant, duree_j)
    reste = montant - recu
    if reste > EPS:
        BQ.avance_a_l_etat(p, reste); tr.emis_avances += reste
        p.noter("emission_dette", instrument="avance", montant=round(reste, 2), taux=round(BQ.taux_directeur(p), 5), duree=0)
    return montant


def assurer(p, besoin):
    """Avant un paiement de l Etat : si la caisse n y suffit pas, le manque est emprunte ( jamais un impaye )."""
    w = p.w; tr = _etat(p).tresor
    if tr.financement and w.gouv.caisse < besoin: emprunter(p, besoin - w.gouv.caisse)


def coussin(p):
    tr = _etat(p).tresor
    return tr.coussin_j * tr.depense_moyenne


def gerer_tresorerie(p):
    """Le matin : la caisse est remontee au coussin, ou l excedent rembourse les avances de la banque centrale."""
    w = p.w; tr = _etat(p).tresor
    if not tr.financement: return
    cible = coussin(p)
    bc = p.domaine("banques").bc
    if w.gouv.caisse < cible: emprunter(p, cible - w.gouv.caisse)
    elif w.gouv.caisse > 2.0 * cible and bc.avances > EPS:
        BQ.rembourser_avance(p, min(w.gouv.caisse - cible, bc.avances))


# ================================================================== l impot sur le revenu : la paie du moteur
def _photo_paie(p, cle, donnees):
    """17 h 50, apres les autres echeances du pas ( mensualites comprises ) : les caisses des menages et les heures de
    chacun avant la paie de 18 h ; et la paie du soir assuree dans la caisse du Tresor."""
    t0 = time.perf_counter()
    e = _etat(p); f = e.fisc; w = p.w
    f.caisse_1750 = np.fromiter((m.caisse for m in w.menages), np.float64, len(w.menages))
    f.heures_1750 = np.fromiter((h.heures_jour if h.vivant else 0.0 for h in w.habitants), np.float64, len(w.habitants))
    p.poser(C.PAS_PAR_JOUR - 1, "etat_photo_paie", 0)     # servie apres le pas : w.pas est deja le suivant
    paie = e.tresor.paie_hier if e.tresor.paie_hier > 0 else _paie_prevue(p)
    assurer(p, 1.25 * paie + 0.5 * e.tresor.depense_moyenne)
    _chrono(e, "photo_paie", t0)


def _paie_prevue(p):
    """La paie publique d une journee pleine : salaires publics et pensions ( la prevision du budget )."""
    w = p.w; tot = 0.0
    for h in w.habitants:
        if not h.vivant: continue
        if h.role == "retraite": tot += PO.PENSION_JOUR
        elif C.ROLES.get(h.role, (0, "", False))[2]:
            tot += PO.SALAIRE_HORAIRE.get(h.role, 0) * HEURES_HORAIRE.get(h.horaire, 8.0) * w.gouv.facteur_salaire_public
    return tot


def _paie_fiscale(p):
    """18 h, juste apres la paie du moteur : ce que chaque menage a recu ( sa caisse contre la photo de 17 h 50 ) est
    reparti entre ses membres - salaires et pensions prevus sur leurs heures, le reste aux non salaries - ; le revenu
    non salarial est declare ( une part cachee ) ; puis la retenue cumulee au bareme est prelevee ou remboursee."""
    t0 = time.perf_counter()
    e = _etat(p); f = e.fisc; w = p.w
    if f.caisse_1750 is None: return
    n = len(f.caisse_1750)
    maintenant = np.fromiter((w.menages[i].caisse for i in range(n)), np.float64, n)
    entree = np.maximum(0.0, maintenant - f.caisse_1750)
    f.caisse_1750 = None
    H = w.habitants; nh = len(f.heures_1750)
    mid = np.fromiter((H[i].menage.id if H[i].vivant and H[i].menage is not None and H[i].menage.id < n else -1
                       for i in range(nh)), np.int64, nh)
    rid = np.fromiter((ROLE_IDX.get(H[i].role, 0) for i in range(nh)), np.int64, nh)
    atw = np.fromiter((H[i].poste == "travail" for i in range(nh)), bool, nh)
    ok = mid >= 0
    ms = np.where(ok, mid, 0)
    cat = np.where(ok, CAT_ROLE[rid], 0); pub = PUB_ROLE[rid]
    heures = f.heures_1750 + np.where(pub & atw, PAS_H, 0.0)       # l heure payee de 18 h ( Monde.deplacer )
    fac = np.where(pub, w.gouv.facteur_salaire_public, 1.0)
    sal = np.where(cat == 1, SAL_ROLE[rid] * heures * fac, 0.0)
    pen = np.where(cat == 2, float(PO.PENSION_JOUR), 0.0)
    prevu = np.bincount(ms[ok], weights=(sal + pen)[ok], minlength=n)[:n]
    k = np.ones(n)
    np.divide(entree, prevu, out=k, where=prevu > entree)        # un payeur qui n a pas tout paye : on ne compte que le paye
    sal = sal * k[ms]; pen = pen * k[ms]
    surplus = np.maximum(0.0, entree - prevu)
    n_ns = np.bincount(ms[cat == 3], minlength=n)[:n]
    sal_m = np.bincount(ms[cat == 1], weights=sal[cat == 1], minlength=n)[:n]
    part_ns = np.divide(surplus, n_ns, out=np.zeros(n), where=n_ns > 0)
    nonsal = np.where(cat == 3, part_ns[ms], 0.0)
    # sans non salarie, le surplus est la part des salaires que les heures de 17 h 50 ne voyaient pas ( production de 18 h )
    vers_sal = np.divide(surplus, sal_m, out=np.zeros(n), where=(n_ns == 0) & (sal_m > 0))
    sal = sal * (1.0 + vers_sal[ms])
    perdu = float(surplus[(n_ns == 0) & (sal_m <= 0)].sum())
    f.revenus["non_attribue"] += perdu
    prop = p.col("menage", "fisc_propension")[:n].astype(np.float64)
    pm = np.where(ok, prop[ms], 0.0)
    decl = nonsal * (1.0 - pm)
    ch = p.colonnes["habitant"]
    ch["fisc_sal"][:nh] += sal + pen
    ch["fisc_revenu"][:nh] += sal + pen + decl
    ch["fisc_cache"][:nh] += nonsal * pm
    f.revenus["salaires"] += float(sal.sum()); f.revenus["pensions"] += float(pen.sum())
    f.revenus["non_salarial"] += float(nonsal.sum()); f.revenus["declare"] += float(decl.sum())
    # les declarations lissees ( les traits du controle ) et les apporteurs non salaries
    a = 1.0 / 30.0
    dm = np.bincount(ms[ok], weights=decl[ok], minlength=n)[:n]
    rm = np.bincount(ms[ok], weights=(sal + pen + decl)[ok], minlength=n)[:n]
    cm = p.colonnes["menage"]
    cm["fisc_nonsal_ema"][:n] = (1 - a) * cm["fisc_nonsal_ema"][:n] + a * dm
    cm["fisc_revenu_ema"][:n] = (1 - a) * cm["fisc_revenu_ema"][:n] + a * rm
    cm["fisc_ns_n"][:n] = np.minimum(100, n_ns)
    # la ventilation des salaires publics par ministere ( la cle du budget du soir )
    sel = pub & (cat == 1) & (sal > 0)
    mi = MIN_ROLE[rid]
    for i in np.nonzero(sel & (rid == I_MINISTRE))[0].tolist(): mi[i] = LIGNES.index(_ministere(H[i]))
    poids = np.bincount(mi[sel], weights=sal[sel], minlength=len(LIGNES))
    e.admin.poids_salaires = {l: float(poids[k]) for k, l in enumerate(LIGNES) if poids[k] > 0}
    _prelever(p, e, mid, n, nh)
    _chrono(e, "paie_fiscale", t0)


def _prelever(p, e, mid, n, nh):
    """La retenue du jour : pour chacun, l impot cumule du ( methode cumulative ) moins ce qui a deja ete preleve ;
    compensee par menage ; un centime pres ( un reste plus petit attend le lendemain )."""
    f = e.fisc; w = p.w; L = p.socle.livre
    d, duree = f.jours_exercice(p.jour)
    ch = p.colonnes["habitant"]
    Y, Ys, Rt = ch["fisc_revenu"][:nh], ch["fisc_sal"][:nh], ch["fisc_retenu"][:nh]
    enf = ch["fisc_enfants"][:nh]
    idx = np.nonzero((mid >= 0) & ((Y > 0) | (Rt != 0)))[0]
    if not len(idx): return
    cible = np.asarray(impot_cumule(Y[idx], Ys[idx], enf[idx], d, duree, f.taux_ir, f.tranches_ir))
    du = cible - Rt[idx]
    par_m = np.bincount(mid[idx], weights=du, minlength=n)[:n]
    phi = np.zeros(n)
    rembourser = -float(par_m[par_m <= -0.01].sum())
    if rembourser > 0: assurer(p, rembourser)
    for i in np.nonzero(np.abs(par_m) >= 0.01)[0].tolist():
        mg = w.menages[i]; x = float(par_m[i])
        if x > 0:
            paye = L.transferer(mg, w.gouv, x, "retenue_ir"); f.compte["retenue_ir"] += paye
            p.compter("retenue_ir", paye)
        else:
            paye = -L.transferer(w.gouv, mg, -x, "remboursement_ir"); f.compte["remboursement_ir"] -= paye
            p.compter("remboursement_ir", -paye)
        phi[i] = paye / x
    Rt[idx] += du * phi[mid[idx]]


def _compter_enfants(p):
    """Les enfants a charge de chaque parent : vivants, de moins de 18 ans ( les deux parents les declarent )."""
    w = p.w; d = p.domaine("population")
    nh = len(w.habitants)
    enf = p.col("habitant", "fisc_enfants")
    nj = p.col("habitant", "naissance_j")
    enf[:nh] = 0
    for parent, enfants in d.enfants_de.items():
        if parent >= nh: continue
        k = sum(1 for c in enfants if c < nh and w.habitants[c].vivant and p.jour - nj[c] < POP.AGE_MAJEUR * POP.JOURS_AN)
        enf[parent] = min(20, k)


def _nouvel_exercice(p, e):
    """Le 31 decembre au soir : l impot elude de l exercice passe en arrieres ( caches ) ; l exercice suivant s ouvre."""
    f = e.fisc; w = p.w
    nh = len(w.habitants); n = len(w.menages)
    ch = p.colonnes["habitant"]
    Y, Ys, Ca = ch["fisc_revenu"][:nh], ch["fisc_sal"][:nh], ch["fisc_cache"][:nh]
    enf = ch["fisc_enfants"][:nh]
    idx = np.nonzero(Ca > 0)[0]
    if len(idx):
        elude = (np.asarray(impot_annuel(Y[idx] + Ca[idx], Ys[idx], enf[idx], f.taux_ir, f.tranches_ir))
                 - np.asarray(impot_annuel(Y[idx], Ys[idx], enf[idx], f.taux_ir, f.tranches_ir)))
        mid = np.fromiter((w.habitants[i].menage.id if w.habitants[i].menage is not None else -1 for i in idx.tolist()),
                          np.int64, len(idx))
        ok = (mid >= 0) & (mid < n)
        np.add.at(p.col("menage", "fisc_arrieres"), mid[ok], elude[ok])
    for c in ("fisc_revenu", "fisc_sal", "fisc_retenu", "fisc_cache"): ch[c][:nh] = 0.0
    f.debut = f.fin + 1
    f.fin = _fin_d_annee(p, f.debut)
    _voter_budget(p, e, f.debut, f.fin)


# ================================================================== l IS et les dividendes ( fin de mois )
def _mois_fiscal(p):
    """10 h 10, le lendemain de la cloture d un mois par le domaine 3 : IS sur le resultat du mois clos ( part cachee ),
    retenue de 5 % sur les dividendes verses la veille au soir."""
    if p.jour == 0 or p.jour % EC.MOIS_J != 0: return
    t0 = time.perf_counter()
    e = _etat(p); f = e.fisc; w = p.w; L = p.socle.livre; K = p.socle.creances
    eco = p.domaine("economie")
    assiette = EC.assiette_is(p)
    for c in eco.unites:
        if c.liquidee: continue
        dos = f.unites.get(c.id)
        if dos is None: dos = f.unites[c.id] = DossierUnite(c.id, 0.0, getattr(c.unite, "type", "") == "ferme")
        u = c.unite
        dos.ca = float(c.mois_clos.get("valeur_production", 0.0) + c.mois_clos.get("ventes_menages_ht", 0.0))
        taux = f.taux_is_coop if dos.cooperative else f.taux_is
        impot_vrai, base = impot_societes(assiette.get(c.id, 0.0), dos.pertes, p.jour, taux)
        declare = base * (1.0 - dos.propension)
        dos.resultat = declare
        dos.impot = taux * declare
        dos.elude += impot_vrai - dos.impot
        f.compte["is_elude"] += impot_vrai - dos.impot
        if dos.impot > EPS:
            paye = L.transferer(u, w.gouv, dos.impot, "impot_societes")
            f.compte["impot_societes"] += paye; p.compter("impot_societes", paye)
            if dos.impot - paye > 1e-6:
                f.creances.append(K.constater(w.gouv, u, dos.impot - paye, "impot_societes", p.jour))
        h = eco.proprietaires.get(c.id)
        div = float(c.propres.get("dividendes", 0.0))
        if h is not None and h.menage is not None and div > EPS:
            x = L.transferer(h.menage, w.gouv, f.taux_dividende * div, "retenue_dividende")
            f.compte["dividendes"] += x; p.compter("retenue_dividende", x)
    _compter_enfants(p)
    _chrono(e, "mois_fiscal", t0)


# ================================================================== le controle fiscal ( 10 h )
def _regions_menages(p):
    """Les menages habites de chaque region ( le marche de leur domicile ), une passe."""
    w = p.w; dis = p.col("menage", "dissous")
    out = {}
    for mg in w.menages:
        if dis[mg.id] or mg.domicile is None or mg.domicile.marche is None or not any(x.vivant for x in mg.membres): continue
        out.setdefault(mg.domicile.marche.id, []).append(mg.id)
    return {k: np.array(v, dtype=np.int64) for k, v in out.items()}


def _medianes_menages(p, regions):
    """Par region : la mediane du revenu non salarial declare par apporteur, chez les menages qui en ont."""
    cm = p.colonnes["menage"]
    out = {}
    for r, ids in regions.items():
        ns = cm["fisc_ns_n"][ids]; v = cm["fisc_nonsal_ema"][ids]
        sel = (ns > 0) & (v > 0)
        out[r] = float(np.median(v[sel] / ns[sel])) if sel.any() else 0.0
    return out


def _medianes_unites(p, f):
    """Par type d unite : la mediane de la marge declaree ( resultat declare sur chiffre d affaires ) des unites
    beneficiaires ; une unite en perte ne se compare pas ( une cooperative qui distribue tout n a pas de marge )."""
    par = {}
    eco = p.domaine("economie")
    for c in eco.unites:
        dos = f.unites.get(c.id)
        if dos is None or c.liquidee or dos.ca <= EPS or dos.resultat <= EPS: continue
        par.setdefault(getattr(c.unite, "type", "marche"), []).append(dos.resultat / dos.ca)
    return {k: float(np.median(v)) for k, v in par.items()}


def _traits_menage(p, i, med, jour):
    cm = p.colonnes["menage"]
    rev = float(cm["fisc_revenu_ema"][i]); ns = float(cm["fisc_nonsal_ema"][i]); nn = int(cm["fisc_ns_n"][i])
    part = ns / rev if rev > EPS else 0.0
    if nn > 0 and med > EPS: ecart = 1.0 - min(1.0, (ns / nn) / med)
    else: ecart = 0.0
    anc = min(1.0, (jour - int(cm["fisc_controle_j"][i])) / JOURS_AN)
    return [min(1.0, rev / REF_REVENU_J), min(1.0, max(0.0, part)), ecart, anc, min(1.0, int(cm["fisc_redresse"][i]) / 3.0)], rev


def _traits_unite(c, dos, med, jour):
    marge = max(0.0, dos.resultat) / dos.ca if dos.ca > EPS else 0.0
    m0 = med.get(getattr(c.unite, "type", "marche"), 0.0)
    ecart = 1.0 - min(1.0, marge / m0) if m0 > EPS and marge > EPS else 0.0
    anc = min(1.0, (jour - dos.controle_j) / JOURS_AN)
    return [min(1.0, dos.ca / REF_CA_MOIS), min(1.0, marge), ecart, anc, min(1.0, dos.redresse / 3.0)], dos.ca / EC.MOIS_J


def _controleurs(p):
    """Les policiers presents a leur poste, par identifiant ; une part d entre eux controle."""
    w = p.w
    presents = []
    for cap in w.carte.capitales:
        presents += [h for h in w.au_travail_de(cap, "policier") if h.vivant and h.poste == "travail"]
    presents.sort(key=lambda h: h.id)
    k = int(math.ceil(_etat(p).fisc.part_controleurs * len(presents)))
    return presents[:k]


def _controles_du_jour(p):
    """10 h : chaque controleur recoit son lot ( des menages et des unites de sa region, pas encore controles
    aujourd hui ), voit les dossiers que designe chaque critere, choisit un critere, controle."""
    t0 = time.perf_counter()
    e = _etat(p); f = e.fisc; w = p.w; dec = e.decideur
    ctrl = _controleurs(p)
    if not ctrl: return
    regions = _regions_menages(p)
    med_m = _medianes_menages(p, regions)
    med_u = _medianes_unites(p, f)
    eco = p.domaine("economie")
    unites_r = {}
    for c in eco.unites:
        if not c.liquidee and c.id in f.unites: unites_r.setdefault(c.marche_id, []).append(c)
    cj = p.col("menage", "fisc_controle_j")
    rng = p.du_jour("etat_dossiers")
    zero = [0.0] * 5
    for ag in ctrl:
        r = ag.travail.id
        mids = regions.get(r, np.array([], dtype=np.int64))
        mids = mids[cj[mids] != p.jour]
        us = [c for c in unites_r.get(r, []) if f.unites[c.id].controle_j != p.jour]
        if not len(mids) and not us: continue
        lot_m = mids[rng.choice(len(mids), min(LOT_MENAGES, len(mids)), replace=False)].tolist() if len(mids) else []
        lot_u = [us[j] for j in rng.choice(len(us), min(LOT_UNITES, len(us)), replace=False).tolist()] if us else []
        tm = [(i,) + tuple(_traits_menage(p, i, med_m.get(r, 0.0), p.jour)) for i in lot_m]
        tu = [(c,) + tuple(_traits_unite(c, f.unites[c.id], med_u, p.jour)) for c in lot_u]
        me = max(tm, key=lambda z: (z[1][2], z[1][1], -z[0])) if tm else None
        mg = max(tm, key=lambda z: (z[2], -z[0])) if tm else None
        ue = max(tu, key=lambda z: (z[1][2], -z[1][1], z[0].id)) if tu else None
        ug = max(tu, key=lambda z: (z[2], z[0].id)) if tu else None
        cibles = [("menage", w.menages[me[0]]) if me else None, ("menage", w.menages[mg[0]]) if mg else None,
                  ("unite", ue[0]) if ue else None, ("unite", ug[0]) if ug else None, None]
        traits = sum(((list(z[1]) if z else zero) for z in (me, mg, ue, ug)), [])
        tailles = [z[2] if z else -1.0 for z in (me, mg, ue, ug)] + [-1.0]
        cle = f.prochain_controle; f.prochain_controle += 1
        a = dec.decider(cle, ContexteControle(traits, cibles, tailles))
        cible = cibles[a]
        if cible is None:                       # au hasard, ou un critere sans dossier dans le lot : un dossier tire
            lot = [("menage", w.menages[i]) for i in lot_m] + [("unite", c) for c in lot_u]
            cible = lot[int(rng.integers(0, len(lot)))]
        dec.ajouter(cle, -COUT_CONTROLE / NORME_CONTROLE)
        controler(p, ag, cible, cle, a)
    _chrono(e, "controles", t0)


def controler(p, controleur, cible, cle=None, action=-1):
    """Un controle : l impot elude du dossier est redresse ( creance de l Etat ), avec sa penalite ; ce que la caisse du
    contribuable permet est encaisse tout de suite. Le contribuable redresse cache ensuite moins. Rend le ControleOuvert."""
    e = _etat(p); f = e.fisc; w = p.w; L = p.socle.livre; K = p.socle.creances
    genre, x = cible
    if cle is None: cle = f.prochain_controle; f.prochain_controle += 1
    o = ControleOuvert(cle, controleur.id if controleur is not None else -1, (genre, getattr(x, "id", None)), p.jour, action)
    if genre == "menage":
        mg = x; debiteur = mg
        ids = np.array([h.id for h in mg.membres], dtype=np.int64)
        ch = p.colonnes["habitant"]
        d, duree = f.jours_exercice(p.jour)
        Y, Ys, Ca, enf = ch["fisc_revenu"][ids], ch["fisc_sal"][ids], ch["fisc_cache"][ids], ch["fisc_enfants"][ids]
        vrai = np.asarray(impot_cumule(Y + Ca, Ys, enf, d, duree, f.taux_ir, f.tranches_ir))
        declare = np.asarray(impot_cumule(Y, Ys, enf, d, duree, f.taux_ir, f.tranches_ir))
        elude_i = np.maximum(0.0, vrai - declare)
        arr = float(p.col("menage", "fisc_arrieres")[mg.id])
        # le passe : depuis le dernier controle d avant l installation, au rythme mesure depuis l installation
        avant = min(PASSE_MAX_ANS, max(0.0, (f.jour0 - int(p.col("menage", "fisc_controle_j")[mg.id])) / JOURS_AN))
        ecoule = max(1, p.jour - f.jour0 + 1)
        arr += float(elude_i.sum()) / ecoule * JOURS_AN * avant
        redr = float(elude_i.sum()) + arr
        taux = taux_penalite(float(elude_i.sum()), float(declare.sum()))
        ch["fisc_revenu"][ids] = Y + Ca; ch["fisc_cache"][ids] = 0.0
        ch["fisc_retenu"][ids] += elude_i
        p.col("menage", "fisc_arrieres")[mg.id] = 0.0
        p.col("menage", "fisc_controle_j")[mg.id] = p.jour
        if redr > EPS:
            p.col("menage", "fisc_redresse")[mg.id] = min(100, int(p.col("menage", "fisc_redresse")[mg.id]) + 1)
            p.col("menage", "fisc_propension")[mg.id] *= DISSUASION
    else:
        c = x; dos = f.unites[c.id]; debiteur = c.unite
        avant = min(PASSE_MAX_ANS, max(0.0, (f.jour0 - dos.controle_j) / JOURS_AN))
        mois = max(1.0, (p.jour - f.jour0) / EC.MOIS_J)
        redr = dos.elude * (1.0 + 12.0 * avant / mois)
        taux = taux_penalite(redr, dos.impot)
        dos.elude = 0.0; dos.controle_j = p.jour
        if redr > EPS: dos.redresse += 1; dos.propension *= DISSUASION
    penal = taux * redr
    o.redressement, o.penalite = redr, penal
    for montant, motif in ((redr, "redressement_fiscal"), (penal, "penalite_fiscale")):
        if montant > 1e-6:
            cr = K.constater(w.gouv, debiteur, montant, motif, p.jour)
            f.creances.append(cr); o.creances.append(cr)
            o.encaisse += K.regler(cr, L, min(montant, _saisissable(p, debiteur)))
    f.compte["controles"] += 1; f.compte["redressements"] += redr; f.compte["penalites"] += penal
    if redr > EPS: f.compte["controles_positifs"] += 1
    f.compte["recouvre"] += o.encaisse
    f.controles[cle] = o
    p.compter("redressement", redr)
    p.noter("controle_fiscal", controleur=o.controleur, cible=f"{genre}:{o.cible[1]}", montant=round(redr + penal, 2))
    return o


def _recouvrer(p):
    """18 h 20, apres la paie et la retenue : les creances fiscales de l Etat sont saisies sur ce qui est saisissable ;
    puis chaque controle ouvert recoit la consequence du jour ( pas le jour meme : elle entre le lendemain )."""
    t0 = time.perf_counter()
    e = _etat(p); f = e.fisc; L = p.socle.livre; K = p.socle.creances
    actives = K.actives
    par_cr = {}
    for o in f.controles.values():
        for cr in o.creances: par_cr[cr.id] = o
    garde = []
    for cr in f.creances:
        if actives.get(cr.id) is not cr: continue
        deb = cr.debiteur
        if type(deb) is PO.Menage and p.col("menage", "dissous")[deb.id]:
            K.abandonner(cr, "dissolution"); continue
        x = K.regler(cr, L, min(cr.montant, _saisissable(p, deb))) if deb.caisse > EPS else 0.0
        if x > 0:
            f.compte["recouvre"] += x; p.compter("recouvrement", x)
            o = par_cr.get(cr.id)
            if o is not None: o.encaisse += x
        if actives.get(cr.id) is cr: garde.append(cr)
    f.creances = garde
    dec = e.decideur
    for cle in list(f.controles):
        o = f.controles[cle]
        if o.jour >= p.jour: continue
        dec.noter(cle, o.encaisse / NORME_CONTROLE, p.jour)
        o.total += o.encaisse; o.encaisse = 0.0; o.jours += 1
        if o.jours >= dec.point.horizon_j:
            if o.action >= 0:
                f.notes.append((p.jour, o.action, (o.total - COUT_CONTROLE) / (NORME_CONTROLE * dec.point.horizon_j)))
            dec.attentes.pop(cle, None); del f.controles[cle]
    _chrono(e, "recouvrer", t0)


# ================================================================== l administration : convois et commandes publiques
def _suivre_convois(p):
    """Chaque heure pleine ( les convois du moteur partent a l heure pleine ) : les convois payes par l Etat, pour
    ventiler leur carburant entre les ministeres."""
    e = _etat(p); w = p.w; a = e.admin
    for c in reversed(w.convois):
        if c.id <= a.dernier_convoi: break
        if c.payeur is w.gouv:
            ligne = "defense" if c.motif == "ravitaillement_base" else \
                LIGNE_DESTINATION.get(c.motif[len("commande_"):], "interieur") if c.motif.startswith("commande_") else "autres"
            a.convois[ligne] = a.convois.get(ligne, 0.0) + max(1, c.arrivee - c.depart)
    a.dernier_convoi = w.n_convoi


def _suivre_commandes(p, e):
    """Les commandes publiques que ce domaine a passees : ce qui a ete livre aujourd hui ( la cle de ventilation ) et
    ce qui reste engage."""
    a = e.admin; w = p.w
    livre, engage, garde = {}, {l: 0.0 for l in LIGNES}, []
    en_cours = {id(c) for c in w.gouv.commandes}
    for t in a.commandes:
        cmd, ligne, vu, pu = t
        q = max(0.0, float(cmd["quantite"])) if id(cmd) in en_cours else 0.0
        if vu - q > EPS: livre[ligne] = livre.get(ligne, 0.0) + (vu - q) * pu
        t[2] = q
        if q > EPS and id(cmd) in en_cours:
            engage[ligne] += q * pu; garde.append(t)
    a.commandes = garde
    e.budget.engage = engage
    return livre


def _suivre_nouvelles_commandes(p, e, avant):
    """Les commandes qu une action vient d ajouter au moteur ( acheter, subvention aux hopitaux )."""
    w = p.w
    for cmd in w.gouv.commandes:
        if id(cmd) in avant: continue
        ligne = LIGNE_DESTINATION.get(cmd.get("destination"), "interieur")
        pu = w.prix_moyen(cmd["bien"]) * 1.1
        e.admin.commandes.append([cmd, ligne, float(cmd["quantite"]), pu])
        e.budget.engage[ligne] = e.budget.engage.get(ligne, 0.0) + float(cmd["quantite"]) * pu


# ================================================================== le budget
def _heures_jour(h): return HEURES_HORAIRE.get(h.horaire, 8.0)


def _voter_budget(p, e, debut, fin):
    """La loi de finances de l exercice ( ou de ce qui en reste ) : la regle du gouvernement, a calibrer. Personnel et
    pensions sur les effectifs, achats de l armee sur le carburant des patrouilles, provisions ailleurs, interets sur la
    dette et le taux ; recettes sur les salaires, le panier et les taux en vigueur."""
    w = p.w; f = e.fisc
    jours = fin - debut + 1
    cred = {}
    for l in LIGNES:
        for nat in NATURES_DEPENSE: cred[(l, nat)] = 0.0
    eff = {l: 0 for l in LIGNES}
    salaires_prives = 0.0; n_sal = 0
    for h in w.habitants:
        if not h.vivant: continue
        if h.role == "retraite": cred[("pensions", "transferts")] += PO.PENSION_JOUR * jours; continue
        s = PO.SALAIRE_HORAIRE.get(h.role, 0) * _heures_jour(h)
        if C.ROLES.get(h.role, (0, "", False))[2]:
            l = _ministere(h); eff[l] += 1
            cred[(l, "personnel")] += s * w.gouv.facteur_salaire_public * jours
        elif s > 0: salaires_prives += s * jours; n_sal += 1
    e.admin.effectifs = eff
    for l in LIGNES:
        cred[(l, "achats")] += PROVISION_ACHATS * cred[(l, "personnel")]
    carb = sum(w.besoin_patrouille(b) for b in w.carte.de_type("base"))
    cred[("defense", "achats")] += carb * w.prix_moyen("carburant") * 1.1 * jours
    vivants = sum(1 for h in w.habitants if h.vivant)
    cred[("sante", "achats")] += REMEDES_PAR_HABITANT_AN * vivants * w.prix_moyen("remedes") * 1.1 * jours / JOURS_AN
    masse = sum(v for (l, n), v in cred.items() if n == "personnel")
    cred[("subventions", "transferts")] = PROVISION_SUBVENTIONS * masse
    cred[("dette", "interets")] = dette_nominale(p) * BQ.taux_directeur(p) * jours / JOURS_AN
    publics = masse / jours
    moyen = (salaires_prives + publics * jours) / max(1, n_sal + sum(eff.values())) / jours * JOURS_AN
    t_ir = impot_annuel(moyen, moyen, 0, f.taux_ir, f.tranches_ir) / moyen if moyen > 0 else 0.0
    conso = vivants * C.NOURRITURE_PAR_JOUR * w.prix_moyen("nourriture") * jours / BQ.POIDS_INDICE["nourriture"]
    prevues = {k: 0.0 for k in CATEGORIES_RECETTES}
    prevues["ir"] = t_ir * (salaires_prives + publics * jours)
    prevues["tva"] = taux_tva_equivalent(p) * conso
    b = Budget(_date(p, debut).year, debut, jours, cred, prevues)
    e.budget = b
    p.noter("vote_budget", exercice=b.exercice, depenses=round(sum(cred.values()), 2), recettes=round(sum(prevues.values()), 2))
    return b


def execution_budget(p):
    """{ ( ligne, nature ) : ( credit, execute, ecart au prorata ) } et { categorie : ( prevu, encaisse ) }, et le solde."""
    e = _etat(p); b = e.budget
    ecoule = min(1.0, max(0.0, (p.jour - b.debut + 1) / b.jours))
    dep = {k: (b.credits[k], b.depenses.get(k, 0.0), b.depenses.get(k, 0.0) - b.credits[k] * ecoule)
           for k in b.credits if b.credits[k] or b.depenses.get(k, 0.0)}
    rec = {k: (b.prevues.get(k, 0.0), b.recettes.get(k, 0.0)) for k in CATEGORIES_RECETTES}
    return {"depenses": dep, "recettes": rec, "ecoule": ecoule,
            "solde": math.fsum(b.recettes.values()) - math.fsum(b.depenses.values())}


def _ventiler(repartition, montant, defaut):
    """Un montant du grand livre reparti au prorata d une cle ( drachmes prevues, livrees, duree des convois )."""
    tot = math.fsum(v for v in repartition.values() if v > 0)
    if tot <= EPS: return {defaut: montant}
    return {k: montant * v / tot for k, v in repartition.items() if v > 0}


def _cloture(p, comptes):
    """Le soir, sur les comptes clos du jour : l identite budgetaire, l execution du budget, les comptes nationaux,
    la statistique publiee pour demain."""
    t0 = time.perf_counter()
    e = _etat(p); w = p.w; tr = e.tresor; b = e.budget; a = e.admin
    rec = {k: 0.0 for k in CATEGORIES_RECETTES}
    dep = {}
    fin = net = 0.0
    livraisons = _suivre_commandes(p, e)
    base = tr.base or {}
    for m, pa, re, s, _ in comptes["argent"]:
        if pa != "Gouvernement" and re != "Gouvernement": continue
        s -= base.get((m, pa, re), 0.0)
        if pa == re or s == 0.0: continue
        sg = 1.0 if re == "Gouvernement" else -1.0
        net += sg * s
        if m in MOTIFS_FINANCEMENT: fin += sg * s; continue
        if sg > 0: rec[RECETTE_DU_MOTIF.get(m, "autres")] += s; continue
        if m == "remboursement_ir": rec["ir"] -= s; continue
        if m == "salaire public": parts = {(l, "personnel"): x for l, x in _ventiler(a.poids_salaires, s, "autres").items()}
        elif m == "pension": parts = {("pensions", "transferts"): s}
        elif m == "commande publique": parts = {(l, "achats"): x for l, x in _ventiler(livraisons, s, "interieur").items()}
        elif m == "carburant du convoi": parts = {(l, "achats"): x for l, x in _ventiler(a.convois, s, "defense").items()}
        elif m == "electricite": parts = {("industrie", "achats"): s}
        elif m == "subvention": parts = {("subventions", "transferts"): s}
        elif m in ("interet_titre", "interet_avance_bc"): parts = {("dette", "interets"): s}
        else: parts = {("autres", "achats"): s}
        for k, x in parts.items(): dep[k] = dep.get(k, 0.0) + x
    tr.base = None
    caisse = w.gouv.caisse
    hors = (caisse - tr.caisse_prec) - net
    attribue = 0.0
    for cle, x in tr.hors_livre:
        attribue += x
        if x > 0: rec[cle if isinstance(cle, str) else "autres"] += x
        else:
            k = cle if isinstance(cle, tuple) else ("autres", "achats")
            dep[k] = dep.get(k, 0.0) - x
    tr.hors_livre = []
    recettes, depenses = math.fsum(rec.values()), math.fsum(dep.values())
    solde = recettes - depenses
    dette = dette_brute(p)
    ecart = solde + ((dette - caisse) - (tr.dette_prec - tr.caisse_prec))
    tr.ecart_cumule += ecart; tr.pire_ecart = max(tr.pire_ecart, abs(ecart))
    tr.serie.append((p.jour, recettes, depenses, solde, fin, dette, caisse, ecart, hors - attribue))
    tr.caisse_prec, tr.dette_prec = caisse, dette
    tr.depense_moyenne = depenses if tr.depense_moyenne <= 0 else tr.depense_moyenne + (depenses - tr.depense_moyenne) / 30.0
    for k, x in dep.items(): b.depenses[k] = b.depenses.get(k, 0.0) + x
    for k, x in rec.items(): b.recettes[k] += x
    for (l, nat), x in dep.items():
        if nat == "personnel": a.masse[l] = a.masse.get(l, 0.0) + x
    tr.paie_hier = math.fsum(x for (l, nat), x in dep.items() if nat == "personnel" or l == "pensions")
    a.poids_salaires = {}
    a.convois = {}
    _publier(p, e, comptes, dep, rec)
    if p.jour >= e.fisc.fin: _nouvel_exercice(p, e)
    _chrono(e, "cloture", t0)


# ================================================================== la statistique publique
def cadre_enquete(p):
    """Les menages habites ( la base de sondage : le repertoire des logements ), identifiants."""
    w = p.w; dis = p.col("menage", "dissous")
    return np.array([m.id for m in w.menages if not dis[m.id] and any(x.vivant for x in m.membres)], dtype=np.int64)


def repondre(p, ids):
    """Ce que les menages interroges declarent : ( chomeurs, actifs, faim d hier soir, personnes ). Au sens du BIT,
    comme le domaine 3 : actif = vivant de 16 a 64 ans, ni enfant ni retraite ; chomeur = actif sans lieu de travail."""
    w = p.w; nj = p.col("habitant", "naissance_j")
    y = np.zeros(len(ids)); x = np.zeros(len(ids)); fa = np.zeros(len(ids)); t = np.zeros(len(ids))
    for k, i in enumerate(ids.tolist()):
        mg = w.menages[i]
        for h in mg.membres:
            if not h.vivant: continue
            t[k] += 1
            if h.role in ("enfant", "retraite"): continue
            age = (p.jour - int(nj[h.id])) / POP.JOURS_AN
            if not C.AGE_TRAVAIL <= age < C.AGE_RETRAITE: continue
            x[k] += 1
            if h.travail is None: y[k] += 1
        fa[k] = 0.0 if w.nourri_menage.get(i, True) else 1.0
    return y, x, fa, t


def enqueter(p, n, rng, cadre=None):
    """Un sondage aleatoire simple sans remise de `n` menages dans le cadre : leurs reponses."""
    cadre = cadre_enquete(p) if cadre is None else cadre
    n = min(int(n), len(cadre))
    ids = cadre[rng.choice(len(cadre), n, replace=False)] if n else np.array([], dtype=np.int64)
    return repondre(p, ids)


def estimer_ratio(y, x, N):
    """Estimateur par le ratio ( chomeurs / actifs ) d un sondage de menages, et son ecart-type estime ( linearisation,
    correction de population finie )."""
    y = np.asarray(y, float); x = np.asarray(x, float); n = len(y)
    if n < 2 or x.sum() <= 0: return None, None
    r = y.sum() / x.sum()
    s2 = ((y - r * x) ** 2).sum() / (n - 1)
    var = (1.0 - n / max(N, n)) / n * s2 / (x.mean() ** 2)
    return float(r), float(math.sqrt(max(0.0, var)))


def sigma_theorique(y_pop, x_pop, n):
    """L ecart-type theorique de l estimateur par le ratio d un sondage de n menages parmi la population ( y, x )."""
    y = np.asarray(y_pop, float); x = np.asarray(x_pop, float); N = len(y)
    R = y.sum() / x.sum()
    S2 = ((y - R * x) ** 2).sum() / (N - 1)
    return float(math.sqrt((1.0 - n / N) / n * S2 / (x.mean() ** 2)))


def _publier(p, e, comptes, dep, rec):
    """Le soir : ce que l Etat publie pour demain. Etat civil ( avec ses retards de declaration ), recensement
    hospitalier ( les cas graves : les incubations et les cas benins sont invisibles ), enquete aupres des menages,
    comptes nationaux du jour, indice des prix, finances publiques."""
    w = p.w; st = e.stat; tr = e.tresor
    ec = p.domaine("population").etat_civil
    pop = {"inscrits": int(ec.population_connue()), "naissances": int(ec.naissances - st.base_naissances),
           "deces": int(ec.deces - st.base_deces)}
    st.population.append((p.jour, pop["inscrits"], pop["naissances"], pop["deces"]))
    H = w.habitants; nh = len(H)
    hop = np.fromiter((h.vivant and h.poste == "hopital" for h in H), bool, nh)
    ids = set(np.nonzero(hop)[0].tolist())
    admissions = len(ids - st.hospitalises); sorties = len(st.hospitalises - ids)
    st.hospitalises = ids
    col = p.colonnes["habitant"]
    mm = int(((col["deces_declare"][:nh] == 1) & (col["cause_deces"][:nh] == POP.CAUSES.index("maladie"))).sum())
    sante = {"hospitalises": len(ids), "admissions": admissions, "sorties": sorties,
             "morts_maladie": mm - st.base_morts_maladie}
    if p.a("medecine"):
        med = p.domaine("medecine")
        dcl = getattr(med, "declares", None)
        if dcl is not None: sante["cas_declares_7j"] = int(np.asarray(dcl)[:, :, :7].sum())
    st.sante.append((p.jour, sante["hospitalises"], admissions, sorties, sante["morts_maladie"]))
    # l enquete du jour
    cadre = cadre_enquete(p); N = len(cadre); st.n_menages = N
    n = max(ENQUETE_MIN_J, int(math.ceil(TAUX_ENQUETE_J * N)))
    y, x, fa, t = enqueter(p, n, p.du_jour("etat_enquete"), cadre)
    st.enquete.append((p.jour, y, x, fa, t))
    p.compter("enquete_menages", len(y))
    Y = np.concatenate([q[1] for q in st.enquete]); X = np.concatenate([q[2] for q in st.enquete])
    r, s = estimer_ratio(Y, X, N)
    faim_j = [q for q in st.enquete if q[0] > p.jour - FENETRE_FAIM_J]
    Fa = np.concatenate([q[3] for q in faim_j]) if faim_j else np.zeros(0)
    pf = float(Fa.mean()) if len(Fa) else 0.0
    sf = float(math.sqrt(max(0.0, pf * (1 - pf) / max(1, len(Fa) - 1) * (1 - len(Fa) / max(N, 1))))) if len(Fa) > 1 else 0.0
    enquete = {"chomage": None if r is None else round(r, 4), "chomage_marge": None if s is None else round(Z95 * s, 4),
               "echantillon": int(len(Y)), "faim_menages": round(pf * N, 1), "faim_marge": round(Z95 * sf * N, 1),
               "menages": N}
    # les comptes nationaux du jour
    L = p.socle.livre
    d_ent = L.ext["entree"] - tr.ext_prec["entree"]; d_sor = L.ext["sortie"] - tr.ext_prec["sortie"]
    tr.ext_prec = dict(L.ext)
    cn = comptes_nationaux(p, comptes, d_ent, d_sor)
    st.comptes.append((p.jour, cn))
    fenetre = list(st.comptes)[-FENETRE_COMPTES_J:]
    pib_f = math.fsum(c["pib"] for _, c in fenetre)
    pib_an = pib_f * JOURS_AN / len(fenetre)
    serie = list(tr.serie)[-FENETRE_COMPTES_J:]
    rec_f = math.fsum(s_[1] for s_ in serie); dep_f = math.fsum(s_[2] for s_ in serie)
    deficit_an = (dep_f - rec_f) * JOURS_AN / max(1, len(serie))
    dette = dette_nominale(p)
    st.publie = {
        "jour": p.jour, "population": pop, "sante": sante, "enquete": enquete,
        "prix": {"indice": round(BQ.indice_des_prix(p), 3),
                 "inflation": None if BQ.inflation(p) is None else round(BQ.inflation(p), 4)},
        "comptes": {k: round(v, 2) for k, v in cn.items()},
        "pib_annuel": round(pib_an, 2),
        "finances": {"recettes_30j": round(rec_f, 2), "depenses_30j": round(dep_f, 2),
                     "deficit_annuel": round(deficit_an, 2),
                     "deficit_pib": round(deficit_an / pib_an, 4) if pib_an > 0 else None,
                     "dette": round(dette, 2), "dette_pib": round(dette / pib_an, 4) if pib_an > 0 else None}}


def comptes_nationaux(p, comptes, entree_ext, sortie_ext):
    """Le PIB du jour par la depense ( SCN 2008 ), sur les comptes clos du grand livre, secteur par secteur ( le registre
    donne le secteur de chaque classe ) : consommation finale des menages ( achats et TVA ), des administrations
    ( remunerations, achats moins ventes ), formation brute de capital fixe, exportations moins importations ( les
    ventes au port que le moteur ecrit a la main comprises ). Les variations de stocks ne sont pas observees ( a
    mesurer : enquete de stocks ). Le cote des revenus : remunerations, impots sur la production, subventions, revenus
    de la propriete, impots sur le revenu, prestations."""
    L = p.socle.livre
    sect = {f.classe: f.secteur for f in p.socle.registre.familles.values() if f.classe}
    sect["Exterieur"], sect["Emission"] = "exterieur", "emission"
    c = {k: 0.0 for k in ("conso_menages", "conso_apu", "fbcf", "exportations", "importations", "remunerations",
                          "impots_production", "subventions", "revenus_propriete", "impots_revenu", "prestations")}
    for m, pa, re, s, _ in comptes["argent"]:
        if pa == re: continue
        spa, sre = sect.get(pa, "inconnu"), sect.get(re, "inconnu")
        mo = L.motifs.get(m); nat = mo.nature if mo is not None else "non_declare"
        if nat == "achat":
            if m == "investissement": c["fbcf"] += s
            elif spa == "menages" and sre != "menages": c["conso_menages"] += s
            elif spa == "administrations" and sre != "administrations": c["conso_apu"] += s
            elif sre == "administrations" and spa not in ("administrations", "exterieur"): c["conso_apu"] -= s
            if spa == "exterieur": c["exportations"] += s
            if sre == "exterieur": c["importations"] += s
        elif nat == "impot_production":
            c["impots_production"] += s
            if spa == "menages": c["conso_menages"] += s
        elif nat == "remuneration":
            c["remunerations"] += s
            if spa == "administrations": c["conso_apu"] += s
        elif nat == "subvention": c["subventions"] += s
        elif nat == "revenu_propriete": c["revenus_propriete"] += s
        elif nat == "impot_revenu": c["impots_revenu"] += s if sre == "administrations" else -s
        elif nat == "prestation": c["prestations"] += s
    # ce qui a franchi la frontiere hors du grand livre ( moteur E1 ) : entrees = exportations, sorties = importations
    ext_livre_e = math.fsum(s for m, pa, re, s, _ in comptes["argent"] if pa == "Exterieur")
    ext_livre_s = math.fsum(s for m, pa, re, s, _ in comptes["argent"] if re == "Exterieur")
    hors_e = max(0.0, entree_ext - ext_livre_e); hors_s = max(0.0, sortie_ext - ext_livre_s)
    c["exportations"] += hors_e; c["importations"] += hors_s
    c["conso_apu"] += hors_s        # les seules sorties a la main sont les importations de l Etat ( Monde.importer )
    c["pib"] = c["conso_menages"] + c["conso_apu"] + c["fbcf"] + c["exportations"] - c["importations"]
    return c


def publications(p):
    """Ce que l Etat publie ( domaine 22 ) : la derniere statistique du soir, l execution du budget, la dette."""
    e = _etat(p)
    ex = execution_budget(p)
    return {"statistique": json.loads(json.dumps(e.stat.publie)),
            "budget": {"exercice": e.budget.exercice, "solde": round(ex["solde"], 2), "ecoule": round(ex["ecoule"], 4)},
            "dette": {"brute": round(dette_brute(p), 2), "nominale": round(dette_nominale(p), 2),
                      "avances": round(p.domaine("banques").bc.avances, 2),
                      "bons": len(p.domaine("banques").titres)}}


def balance_des_paiements(p):
    """Ce que l Etat sait des echanges exterieurs ( domaine 7 ) : exportations et importations des comptes du jour,
    cumulees depuis l installation, et le solde commercial."""
    x = math.fsum(c["exportations"] for _, c in _etat(p).stat.comptes)
    m = math.fsum(c["importations"] for _, c in _etat(p).stat.comptes)
    return {"exportations": x, "importations": m, "solde_commercial": x - m}


# ================================================================== le sitrep : ce que le gouvernement sait
def sitrep(p):
    """Le bulletin du matin, construit sur la STATISTIQUE publiee la veille, sur ce que l Etat possede ( caisse, stocks
    publics, garnisons, reseau, lois ) et sur les prix affiches. Memes cles que le moteur, pour ses regles et son LLM."""
    e = _etat(p); w = p.w; st = e.stat.publie; f = e.fisc; tr = e.tresor
    pop = st.get("population", {}); sa = st.get("sante", {}); eq = st.get("enquete", {}); fi = st.get("finances", {})
    ex = execution_budget(p)
    budget = {}
    for (l, nat), (cr, exe, ec) in ex["depenses"].items():
        b = budget.setdefault(l, {"credit": 0.0, "execute": 0.0, "ecart": 0.0})
        b["credit"] = round(b["credit"] + cr); b["execute"] = round(b["execute"] + exe); b["ecart"] = round(b["ecart"] + ec)
    s = {
        "jour": w.jour, "heure": round(w.heure, 1),
        "population": {"vivants": int(pop.get("inscrits", 0)), "morts": int(pop.get("deces", 0)),
                       "naissances": int(pop.get("naissances", 0)),
                       "menages_sans_nourriture": int(round(eq.get("faim_menages", 0.0))),
                       "marge_faim": eq.get("faim_marge", 0.0), "menages": eq.get("menages", 0),
                       "source": "etat civil ( declarations ), enquete aupres des menages ( 7 jours )"},
        "sante": {"infectes": int(sa.get("hospitalises", 0)), "nouveaux_cas": int(sa.get("admissions", 0)),
                  "sortis": int(sa.get("sorties", 0)), "morts_maladie": int(sa.get("morts_maladie", 0)),
                  "source": "recensement hospitalier de la veille ( cas graves seulement )"},
        "emploi": {"chomage": eq.get("chomage"), "marge": eq.get("chomage_marge"), "echantillon": eq.get("echantillon", 0)},
        "prix": dict(st.get("prix", {"indice": 100.0, "inflation": None})),
        "marches": {m.lieu.id: {b: {"prix": round(m.prix[b], 2)} for b in ("nourriture", "carburant", "remedes", "fer", "outils")}
                    for m in w.marches.values()},
        "stocks_publics": {"remedes": round(w.publics["hopitaux"]["remedes"]), "or": round(w.publics["reserve"]["or"], 1),
                           "nourriture_population": round(w.publics["population"]["nourriture"])},
        "armee": {"carburant_depot": round(w.publics["armee"]["carburant"]),
                  "garnisons": {k: round(v["carburant"], 1) for k, v in w.garnisons.items()},
                  "patrouilles_annulees_hier": sum(1 for x in w.evenements[-400:] if x["type"] == "patrouille_annulee")},
        "finances": {"caisse": round(w.gouv.caisse), "impot_revenu": w.gouv.impot_revenu, "tva": round(w.gouv.tva, 4),
                     "tva_categories": dict(f.tva), "bareme_ir": [list(f.tranches_ir), list(f.taux_ir)],
                     "impot_societes": f.taux_is, "facteur_salaire_public": w.gouv.facteur_salaire_public,
                     "dette": fi.get("dette", 0.0), "dette_pib": fi.get("dette_pib"), "deficit_annuel": fi.get("deficit_annuel"),
                     "deficit_pib": fi.get("deficit_pib"), "recettes_30j": fi.get("recettes_30j"),
                     "depenses_30j": fi.get("depenses_30j"), "coussin": round(coussin(p)),
                     "avances_bc": round(p.domaine("banques").bc.avances), "budget": budget},
        "comptes_nationaux": {"pib_annuel": st.get("pib_annuel"), "pib_hier": (st.get("comptes") or {}).get("pib")},
        "reseau": {"electricite": round(w.reseau.stock)},
        "lois": w.gouv.lois,
    }
    return s


# ================================================================== le gouvernement : regles, LLM, actions bornees
def decider_regles_etat(s):
    """Le gouvernement par regles : celles du moteur, a l echelle du pays, sur la statistique ; le deficit est finance,
    les taux de la loi ne bougent pas ; l or des reserves rembourse la dette."""
    a = []
    k = max(1.0, s["population"]["vivants"] / 500.0)
    if s["sante"]["infectes"] > 20 * k and s["stocks_publics"]["remedes"] < 60 * k:
        a.append({"type": "acheter", "bien": "remedes", "quantite": min(2000, round(60 * k)), "destination": "hopitaux"})
    if s["armee"]["carburant_depot"] < 80 * k:
        a.append({"type": "acheter", "bien": "carburant", "quantite": min(2000, round(120 * k)), "destination": "armee"})
    if s["population"]["menages_sans_nourriture"] > 20 * k:
        a.append({"type": "subvention", "cible": "menages_pauvres", "montant": round(3000 * k)})
    if s["stocks_publics"]["or"] > 2 and (s["finances"]["dette"] or 0) > 0:
        a.append({"type": "exporter_or", "quantite": s["stocks_publics"]["or"]})
    return a or [{"type": "rien"}]


class CerveauEtat:
    """Le gouvernement joue par un LLM ( Qwen, Ollama local ), comme CerveauLLM du moteur, avec le catalogue etendu.
    Toute action est reverifiee par `appliquer`. Consigne figee, empreinte journalisee."""
    __slots__ = ("modele", "hote", "consigne", "empreinte")

    def __init__(self, modele="qwen2.5:14b", hote="http://localhost:11434"):
        self.modele, self.hote = modele, hote
        self.consigne = ("Tu es le gouvernement du pays : un chef et six ministres ( finances, sante, interieur, defense, "
                         "education, industrie ). Ton pays est en paix. Ton but : que chaque habitant mange, soit soigne, "
                         "travaille et vive en securite, et que les finances publiques tiennent. Tu lis le bulletin du "
                         "matin, fait de la statistique publique ( elle a ses retards et ses marges d erreur ) et tu "
                         "decides. Reponds UNIQUEMENT par un objet JSON {\"motifs\": \"...\", \"actions\": [...]}.\n"
                         + CATALOGUE_ETAT)
        self.empreinte = hashlib.sha256(self.consigne.encode()).hexdigest()[:12]

    def __call__(self, sitrep_, memoire=""):
        corps = {"model": self.modele, "format": "json", "stream": False, "options": {"temperature": 0.2, "seed": 7},
                 "prompt": self.consigne + ("\n\nCe que tu as appris des jours passes :\n" + memoire if memoire else "")
                           + "\n\nBulletin du matin :\n" + json.dumps(sitrep_, ensure_ascii=False)}
        req = urllib.request.Request(self.hote + "/api/generate", data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json"})
        brut = json.loads(urllib.request.urlopen(req, timeout=300).read())["response"]
        try: d = json.loads(brut)
        except json.JSONDecodeError: return [{"type": "rien"}], "sortie illisible : " + brut[:200]
        return d.get("actions", [{"type": "rien"}]), d.get("motifs", "")


def _mesure(p): return p.w.gouv.caisse, _net_gouv(p)


def appliquer(p, action):
    """Applique UNE action du catalogue etendu. Rend ( acceptee, raison ). Hors catalogue ou hors bornes : refusee. Les
    actions du moteur passent par Gouvernement.appliquer ( ses bornes ), apres le controle des credits ; ce que le moteur
    ecrit alors a la main dans la caisse est attribue a l action ( identite budgetaire )."""
    e = _etat(p); w = p.w; f = e.fisc; b = e.budget
    if not isinstance(action, dict): return False, "action non JSON"
    t = action.get("type")
    try:
        if t == "fixer_tva":
            c, v = action["categorie"], float(action["valeur"])
            if c not in BORNES_TVA or c == "exoneree": return False, f"categorie inconnue {c}"
            lo, hi = BORNES_TVA[c]
            if not lo <= v <= hi: return False, f"tva {c}={v} hors [{lo} ; {hi}]"
            nv = dict(f.tva, **{c: v})
            if not nv["super_reduite"] <= nv["reduite"] <= nv["normale"]: return False, "super_reduite <= reduite <= normale"
            p.noter("loi_fiscale", quoi=f"tva_{c}", ancien=f.tva[c], nouveau=v)
            f.tva = nv; w.gouv.tva = taux_tva_equivalent(p); return True, ""
        if t == "fixer_ir":
            k, v = int(action["tranche"]), float(action["taux"])
            if not 0 <= k < len(f.taux_ir): return False, f"tranche {k} inconnue"
            lo, hi = BORNES_TAUX_IR
            if not lo <= v <= hi: return False, f"taux {v} hors [{lo} ; {hi}]"
            nv = list(f.taux_ir); nv[k] = v
            if any(nv[j] > nv[j + 1] for j in range(len(nv) - 1)): return False, "un bareme ne baisse pas d une tranche a la suivante"
            p.noter("loi_fiscale", quoi=f"ir_tranche_{k}", ancien=f.taux_ir[k], nouveau=v)
            f.taux_ir = tuple(nv); return True, ""
        if t == "fixer_is":
            v = float(action["valeur"]); lo, hi = BORNES_IS
            if not lo <= v <= hi: return False, f"is={v} hors [{lo} ; {hi}]"
            p.noter("loi_fiscale", quoi="is", ancien=f.taux_is, nouveau=v)
            f.taux_is = v; return True, ""
        if t == "fixer_budget":
            l, m = action["ligne"], float(action["montant"])
            if l not in LIGNES: return False, f"ligne inconnue {l}"
            deja = b.depenses.get((l, "achats"), 0.0) + b.engage.get(l, 0.0)
            haut = 3.0 * max(b.votes.get((l, "achats"), 0.0), 1000.0)
            if not deja <= m <= haut: return False, f"credits {m:.0f} hors [{deja:.0f} ; {haut:.0f}]"
            b.credits[(l, "achats")] = m; return True, ""
        if t == "emettre_dette":
            m, d = float(action["montant"]), int(action["duree_j"])
            if d not in DUREES_BONS: return False, f"duree {d} hors {DUREES_BONS}"
            haut = 60.0 * max(e.tresor.depense_moyenne, 1.0)
            if not 0 < m <= haut: return False, f"montant {m:.0f} hors ]0 ; {haut:.0f}]"
            recu = emettre_bons(p, m, d)
            return (recu > 0), ("" if recu >= m - 1e-6 else f"adjuge {recu:.0f} sur {m:.0f}")
        if t == "rembourser_avance":
            m = float(action["montant"]); haut = min(max(0.0, w.gouv.caisse - coussin(p)), p.domaine("banques").bc.avances)
            if not 0 < m <= haut: return False, f"montant {m:.0f} hors ]0 ; {haut:.0f}]"
            BQ.rembourser_avance(p, m); return True, ""
        if t == "fixer_controle":
            v = float(action["part"])
            if not 0.0 <= v <= 1.0: return False, f"part {v} hors [0 ; 1]"
            f.part_controleurs = v; return True, ""
        if t == "fixer_intensite_controle":
            v = float(action["valeur"]); lo, hi = BORNES_INTENSITE
            if not lo <= v <= hi: return False, f"intensite {v} hors [{lo} ; {hi}]"
            w.intensite_controle = v; return True, ""
        if t == "fixer_impot":
            return False, "remplacee : fixer_tva ( par categorie ), fixer_ir ( par tranche ), fixer_is"
        if t in ("acheter", "importer", "subvention"):
            if t == "acheter":
                bien, q = action["bien"], float(action["quantite"])
                dest = action.get("destination", "hopitaux" if bien == "remedes" else "armee" if bien == "carburant" else "reserve")
                ligne = LIGNE_DESTINATION.get(dest, "interieur")
                cout = q * w.prix_moyen(bien) * 1.1 if bien in C.BIENS else 0.0
                dispo = b.disponible(ligne)
            elif t == "importer":
                bien, q = action["bien"], float(action["quantite"])
                ligne = LIGNE_BIEN.get(bien, "interieur")
                cout = q * C.PRIX_MONDE.get(bien, 0.0) * 1.2
                dispo = b.disponible(ligne)
            elif action.get("cible") == "hopitaux":
                ligne, cout = "sante", float(action["montant"])
                dispo = b.disponible(ligne)
            else:
                ligne, cout = "subventions", float(action["montant"])
                dispo = b.credits.get(("subventions", "transferts"), 0.0) - b.depenses.get(("subventions", "transferts"), 0.0)
            if cout > dispo + 1e-6: return False, f"credits de {ligne} insuffisants ( {cout:.0f} > {max(0.0, dispo):.0f} )"
            if t in ("acheter", "importer"): assurer(p, cout)
        if t in ("acheter", "importer", "exporter_or", "couvre_feu", "quarantaine", "rationnement", "subvention",
                 "fixer_salaires_publics", "rien"):
            avant = {id(c) for c in w.gouv.commandes}
            c0, n0 = _mesure(p)
            ok, raison = w.gouv.appliquer(action, w)
            c1, n1 = _mesure(p)
            hors = (c1 - c0) - (n1 - n0)
            if abs(hors) > EPS:
                if t == "exporter_or" and hors > 0: cle = "vente_or"
                elif t == "importer": cle = (LIGNE_BIEN.get(action.get("bien"), "interieur"), "achats")
                else: cle = "autres" if hors > 0 else ("autres", "achats")
                e.tresor.hors_livre.append((cle, hors))
            if ok: _suivre_nouvelles_commandes(p, e, avant)
            return ok, raison
    except (KeyError, TypeError, ValueError) as ex:
        return False, f"action mal formee : {ex}"
    return False, f"action hors catalogue : {t}"


def _gouverner(p):
    """6 h, a l aube du moteur : le bulletin, la decision ( regles, ou LLM avec repli sur les regles ), les actions
    bornees, puis la tresorerie du jour."""
    t0 = time.perf_counter()
    e = _etat(p); w = p.w
    s = sitrep(p)
    if w.cerveau is None: actions, motifs = decider_regles_etat(s), "regles"
    else:
        try: actions, motifs = w.cerveau(s, w.memoire_gouv)
        except Exception as ex: actions, motifs = decider_regles_etat(s), f"cerveau indisponible : {ex} ; regles"
    res = []
    for a in (actions if isinstance(actions, list) else [actions])[:8]:
        ok, raison = appliquer(p, a)
        res.append({"action": a, "acceptee": ok, "raison": raison})
    w.noter("decision_gouvernement", motifs=str(motifs)[:500], actions=res,
            cerveau="regles" if w.cerveau is None else getattr(w.cerveau, "modele", "?"),
            consigne=None if w.cerveau is None else getattr(w.cerveau, "empreinte", None))
    e.decisions.append((p.jour, len(res), sum(1 for r in res if r["acceptee"])))
    gerer_tresorerie(p)
    _chrono(e, "gouverner", t0)


class RemplaceGouverner:
    """Prend la place de Monde.gouverner ( appele par l aube du moteur ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _gouverner(self.pays)


class RemplaceSitrep:
    """Prend la place de Monde.sitrep ( lu par gouverner et resume_jour ) : la statistique, jamais la verite."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): return sitrep(self.pays)


# ================================================================== API pour les autres domaines
def percevoir(p, payeur, montant, impot):
    """Un impot ou une redevance d un autre domaine ( enfia, taxe_locale, droits_permis, droit_de_douane, tva_import ),
    paye a l Etat ; ce que la caisse ne couvre pas devient une creance de l Etat. Rend ( paye, creance ou None )."""
    if impot not in ("enfia", "taxe_locale", "droits_permis", "droit_de_douane", "tva_import"):
        raise ValueError(f"impot inconnu {impot!r}")
    if not 0.0 <= montant < math.inf: raise ValueError(f"montant invalide {montant!r}")
    e = _etat(p); w = p.w
    paye = p.socle.livre.transferer(payeur, w.gouv, montant, impot)
    cr = None
    if montant - paye > 1e-6:
        cr = p.socle.creances.constater(w.gouv, payeur, montant - paye, impot, p.jour); e.fisc.creances.append(cr)
    return paye, cr


def percevoir_enfia(p, proprietaire, surface_m2, valeur_zone_m2, coefficient=1.0, jours=JOURS_AN):
    """L ENFIA d un batiment pour `jours` jours ( domaine 13 )."""
    return percevoir(p, proprietaire, enfia(surface_m2, valeur_zone_m2, coefficient) * jours / JOURS_AN, "enfia")


def taxes_import(p, bien, valeur_cif):
    """( droit de douane, TVA a l importation ) d une importation de `valeur_cif` drachmes ( domaine 7 )."""
    b = p.socle.catalogue[bien]
    droit = DROITS_DOUANE.get(b.famille, 0.0) * valeur_cif
    return droit, taux_tva(p, bien) * (valeur_cif + droit)


def percevoir_douane(p, importateur, bien, valeur_cif):
    droit, tva = taxes_import(p, bien, valeur_cif)
    return percevoir(p, importateur, droit, "droit_de_douane")[0], percevoir(p, importateur, tva, "tva_import")[0]


def infliger_amende(p, debiteur, montant, motif="amende"):
    """Une amende ( domaine 21 ) : payee a l Etat ce que la caisse permet, le reste en creance de l Etat."""
    if motif not in ("amende", "penalite_fiscale"): raise ValueError(f"motif d amende inconnu {motif!r}")
    e = _etat(p); w = p.w
    paye = p.socle.livre.transferer(debiteur, w.gouv, montant, motif)
    cr = None
    if montant - paye > 1e-6:
        cr = p.socle.creances.constater(w.gouv, debiteur, montant - paye, motif, p.jour); e.fisc.creances.append(cr)
    return paye, cr


def creances_de_l_etat(p):
    """Les creances fiscales et amendes actives de l Etat ( domaine 21 : recouvrement force, prescription )."""
    K = p.socle.creances
    return [c for c in _etat(p).fisc.creances if K.actives.get(c.id) is c]


def recouvrer(p, creance, montant=None):
    return p.socle.creances.regler(creance, p.socle.livre, montant)


def voter_budget(p, credits=None):
    """Le vote d un budget ( domaine 24 ) : la regle, puis les credits d achats votes par ligne ( { ligne : montant } )."""
    e = _etat(p)
    b = _voter_budget(p, e, max(p.jour, e.fisc.debut), e.fisc.fin)
    for l, m in (credits or {}).items():
        if l not in LIGNES or not m >= 0: raise ValueError(f"credit invalide {l} {m}")
        b.credits[(l, "achats")] = b.votes[(l, "achats")] = float(m)
    return b


# ================================================================== installation
def _tirer_propensions(p, e):
    w = p.w
    rng = p.hasard("etat_fraude")
    n = len(w.menages)
    u = rng.random(n); bta = rng.beta(*BETA_MENAGES, n)
    ns = np.array([any(x.vivant and x.role in NON_SALARIAUX for x in m.membres) for m in w.menages], dtype=bool)
    p.col("menage", "fisc_propension")[:n] = np.where(ns & (u >= PART_HONNETES_MENAGES), bta, 0.0)
    p.col("menage", "fisc_controle_j")[:n] = p.jour - (rng.random(n) * PASSE_MAX_ANS * JOURS_AN).astype(np.int32)
    for c in p.domaine("economie").unites:
        coop = getattr(c.unite, "type", "") == "ferme"
        prop = 0.0 if rng.random() < PART_HONNETES_UNITES else float(rng.beta(*BETA_UNITES))
        dos = e.fisc.unites[c.id] = DossierUnite(c.id, prop, coop)
        dos.controle_j = p.jour - int(rng.random() * PASSE_MAX_ANS * JOURS_AN)


def installer(p):
    w = p.w; L = p.socle.livre
    for m in ("retenue_ir", "remboursement_ir", "impot_societes", "retenue_dividende", "redressement_fiscal", "enfia"):
        L.declarer_motif(m, "impot_revenu", "etat")
    for m in ("droit_de_douane", "tva_import", "taxe_locale", "droits_permis"):
        L.declarer_motif(m, "impot_production", "etat")
    L.declarer_motif("penalite_fiscale", "transfert_courant", "etat")
    J = p.socle.journal
    for t, champs in (("controle_fiscal", ("controleur", "cible", "montant")),
                      ("emission_dette", ("instrument", "montant", "taux", "duree")),
                      ("vote_budget", ("exercice", "depenses", "recettes")), ("loi_fiscale", ("quoi", "ancien", "nouveau"))):
        J.declarer(t, "etat", "individuel", champs)
    for t in ("retenue_ir", "remboursement_ir", "impot_societes", "retenue_dividende", "redressement", "recouvrement",
              "enquete_menages"):
        J.declarer(t, "etat", "compte")
    ch, cm = p.colonnes["habitant"], p.colonnes["menage"]
    for nom, dt_, defaut in (("fisc_revenu", np.float64, 0.0), ("fisc_sal", np.float64, 0.0),
                             ("fisc_retenu", np.float64, 0.0), ("fisc_cache", np.float64, 0.0),
                             ("fisc_enfants", np.int8, 0)):
        ch.ajouter(nom, dt_, defaut)
    for nom, dt_, defaut in (("fisc_propension", np.float32, 0.0), ("fisc_arrieres", np.float64, 0.0),
                             ("fisc_controle_j", np.int32, -100000), ("fisc_redresse", np.int16, 0),
                             ("fisc_ns_n", np.int16, 0), ("fisc_nonsal_ema", np.float64, 0.0),
                             ("fisc_revenu_ema", np.float64, 0.0)):
        cm.ajouter(nom, dt_, defaut)
    ch.assurer(len(w.habitants)); cm.assurer(len(w.menages))
    debut = p.jour
    fisc = Fisc(debut, _fin_d_annee(p, debut))
    tr = Tresor(w.gouv.caisse, 0.0, L.ext)
    e = Etat(fisc, tr, None, Administration(), Statistique())
    p.domaines["etat"] = e
    tr.dette_prec = tr.dette0 = dette_brute(p)
    tr.base = {}
    for (m, pa, re), (s, _) in L.jour_argent.items():
        if pa == "Gouvernement" or re == "Gouvernement": tr.base[(m, pa, re)] = s
    # la loi en vigueur a la place des taux uniques du moteur ; l indice des prix repris au taux en vigueur
    ancien = w.gouv.tva
    w.gouv.tva = taux_tva_equivalent(p)
    ind = p.domaine("banques").bc.indice
    if not ind.valeurs:
        for b in list(ind.base): ind.base[b] *= (1.0 + w.gouv.tva) / (1.0 + ancien)
    w.gouv.impot_revenu = 0.0
    _tirer_propensions(p, e)
    _compter_enfants(p)
    _voter_budget(p, e, debut, fisc.fin)
    tr.depense_moyenne = math.fsum(e.budget.credits.values()) / e.budget.jours
    st = e.stat
    ec = p.domaine("population").etat_civil
    st.base_naissances, st.base_deces = ec.naissances, ec.deces
    col = p.colonnes["habitant"]; nh = len(w.habitants)
    st.base_morts_maladie = int(((col["deces_declare"][:nh] == 1) & (col["cause_deces"][:nh] == POP.CAUSES.index("maladie"))).sum())
    st.hospitalises = {h.id for h in w.habitants if h.vivant and h.poste == "hopital"}
    st.n_menages = len(cadre_enquete(p))
    st.publie = {"jour": p.jour - 1,
                 "population": {"inscrits": int(ec.population_connue()), "naissances": 0, "deces": 0},
                 "sante": {"hospitalises": len(st.hospitalises), "admissions": 0, "sorties": 0, "morts_maladie": 0},
                 "enquete": {"chomage": None, "chomage_marge": None, "echantillon": 0, "faim_menages": 0.0,
                             "faim_marge": 0.0, "menages": st.n_menages},
                 "prix": {"indice": 100.0, "inflation": None}, "comptes": {}, "pib_annuel": None,
                 "finances": {"dette": round(dette_nominale(p), 2), "dette_pib": None, "deficit_annuel": None,
                              "deficit_pib": None, "recettes_30j": None, "depenses_30j": None}}
    e.decideur = p.decideur(POINT_CONTROLE)
    w.gouverner = RemplaceGouverner(p)
    w.sitrep = RemplaceSitrep(p)
    if isinstance(w.cerveau, G.CerveauLLM): w.cerveau = CerveauEtat(w.cerveau.modele, w.cerveau.hote)
    # la caisse du Tresor proportionnee a la population ( par l emprunt : la monnaie ne nait que par la banque centrale )
    if PROPORTIONNER_TRESORERIE:
        cible = TRESORERIE_PAR_HABITANT * sum(1 for h in w.habitants if h.vivant)
        if cible > w.gouv.caisse + LOT_MIN_BONS:
            tr.ouverture = cible - w.gouv.caisse
            emprunter(p, tr.ouverture)
    p.echeance("etat_photo_paie", _photo_paie)
    minute = w.minutes % (24 * 60)
    p.poser(((17 * 60 + 50 - minute) % (24 * 60)) // C.MINUTES_PAR_PAS, "etat_photo_paie", 0)
    p.routine(18, 1, "etat", _paie_fiscale)
    p.routine(10, 40, "etat", _controles_du_jour)
    p.routine(10 + 10 / 60, 40, "etat", _mois_fiscal)
    p.routine(18 + 20 / 60, 40, "etat", _recouvrer)
    for h in range(24): p.routine(h, 99, "etat", _suivre_convois)
    p.cloture("etat", _cloture)
    return e
