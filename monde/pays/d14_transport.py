"""DOMAINE 14 - TRANSPORT ET VEHICULES : MODELES, PARC DU PAYS, CONCESSIONS, IMMATRICULATION, PERMIS, GARAGES ET
PIECES, STATIONS-SERVICE, USURE, PANNES, ACCIDENTS DE LA ROUTE, VOLS, CASSE ET FIN DE VIE.

FICHE
1. Classes. Les lois : Caracteristiques ( ce qu est un modele de vehicule : categorie, prix catalogue, carburant,
   consommation, reservoir donc autonomie, places, charge utile, vitesse, pannes par an, duree de vie en km, kilometrage
   annuel, cylindree, CO2, permis exige, pieces, heures et pneus d un entretien ; chaque chiffre avec sa source ou
   « a calibrer » ; et son Modele au Parc du socle, famille vehicule ). Les detenteurs : Concession ( un concessionnaire
   neuf et occasion par marche : caisse ; stock neuf en cohortes du Parc, stock d occasion en individus ), StationService
   ( une par marche : caisse, Stock du socle en gazole et essence ), Garage ( un par marche, garage et auto-ecole :
   caisse, Stock de pieces detachees importees, de pieces de l industrie et de pneus ), Reservoirs ( le carburant qui
   est DANS les reservoirs des vehicules des menages : un Stock du socle, reparti vehicule par vehicule en colonnes ).
   Les proprietaires sans argent : FlotteMenages ( le proprietaire en indivis des cohortes des menages : une cohorte
   par modele et par lieu, la colonne dit quel menage possede quoi ), Receleur ( les vehicules voles ). L etat : Fiche
   ( immatriculation, compteur, dernier entretien d un vehicule qui n est dans aucun menage ), Flotte ( les vehicules
   d une entreprise du moteur ou de l Etat : une cohorte du Parc ), Immatriculation ( le registre : entrees par
   recensement, import neuf, import d occasion ; sorties par rebut, destruction, export ), Vol, Sinistre, Reparation,
   ContexteAchat, ContexteReparation, Transport ( l etat du domaine ).
   Colonnes par menage ( trois emplacements k = 0, 1, 2 ) : vh_m{k} ( modele, -1 vide ), vh_ne{k} ( jour de premiere
   immatriculation ), vh_km{k} ( compteur, km ), vh_ks{k} ( compteur au dernier entretien ), vh_js{k} ( jour du dernier
   entretien ), vh_res{k} ( litres dans le reservoir ) ; vh_lieu ( le lieu ou ses vehicules sont inscrits au Parc ),
   vh_ind ( bit k : l emplacement k est materialise en individu ). Par habitant : vh_permis ( bits B, A, A1, C, D ).
   POURQUOI DES COLONNES ET PAS 25 MILLIONS D OBJETS. A 50 millions d habitants le pays a ~28 millions de vehicules
   ( 560 voitures et ~ 300 autres vehicules pour 1 000 habitants ). Un Objet du Parc coute ~ 230 octets ( objet, entree
   de dictionnaire, flottants ; mesure par test_cout ), une cohorte par menage autant : ~ 6 Go. Ici un vehicule de menage
   anonyme est un emplacement de colonnes : 21 octets ( modele 1, immatriculation 4, compteur 4, entretien 4 + 4,
   reservoir 4 ), 3 emplacements + 3 octets par menage = 66 octets, ~ 1,3 Go pour 20 millions de menages, et ~ 0,5 Go
   si l on ne garde que les emplacements occupes en Rust ; le Parc n en voit qu une cohorte par modele et par lieu
   ( quelques dizaines de milliers d objets ), et un individu seulement quand un evenement le touche ( panne, accident,
   vol, vente, requisition ) : quelques milliers a la fois. Un emplacement garde son age et son compteur propres ( la
   fin de vie, les pannes, la consommation en dependent ) : une cohorte n en garderait que la moyenne. Le permis : une
   colonne d un octet par habitant ( 50 Mo a 50 millions ) plutot qu une table eparse, parce que ~ 75 % des adultes en
   ont un : une table eparse couterait ~ 100 octets par titulaire.
2. Invariants et ce que le domaine detient. OBJETS, par modele du domaine : exemplaires vivants au Parc = recensement +
   importes ( neufs et d occasion ) - rebut - detruits - exportes, compte tenu par le registre d immatriculation, et
   Parc.verifier nul ; pour chaque ( modele, lieu ) : emplacements des menages inscrits a ce lieu = cohorte de la flotte
   des menages + individus des menages de ce lieu ; tout individu materialise d un menage est un objet vivant du Parc
   dont le proprietaire est ce menage ( `anomalies_parc` ). Un vehicule ne nait que par le recensement ou par un import
   ( `importer_vehicules`, `importer_occasion` ) ; une vente, une reprise, un vol, une requisition le cedent sans changer
   le nombre. ARGENT : tout par le grand livre, sous les motifs du domaine ; le domaine DETIENT les caisses des
   concessions, stations et garages ( familles concessions, stations_service, garages ). BIENS : gazole et essence des
   stations et des reservoirs, pieces et pneus des garages ( familles stations_service, garages, reservoirs_vehicules ) ;
   ils n entrent que par achat au domaine 11 ( `vendre_produit` ), par import ( domaine 7 ), par livraison de
   l industrie ( `livrer` ) ou par la dotation du jour du recensement ( le carburant deja dans les reservoirs, le stock
   de depart des stations et des garages : importes sans paiement, comme les stocks de depart du moteur ) ; ils ne
   sortent que brules ( litres = km x L/100 km / 100, motif carburant_route ), consommes par un entretien ou une
   reparation, ou perdus avec un vehicule qui sort ( motif reservoir_sorti ). Litres des colonnes = Stock des reservoirs.
3. Decisions. `acheter_vehicule` ( chaque menage qui a un permis : chaque semaine a son jour s il n a pas de vehicule
   utilisable, tous les 14 jours si le plus vieux a 18 ans ou 85 % de sa vie et a eu une panne ou un accident dans les 90
   jours ) : rien, occasion ( la moins chere du stock
   de SA concession dans la categorie qui lui va, ou une de 10 ans commandee pour lui ), neuf ( en stock ou commande, a
   credit au-dela de son apport : `demander_credit`, domaine 2 ) ; une commande est vendue a son arrivee ( 3 jours ) si
   le menage peut encore payer. Traits : revenu, epargne, vehicules, age et usure du principal, besoin de km, taille, prix de l occasion et du neuf sur son revenu
   annuel, mensualites en cours sur son revenu, pannes des 90 jours, permis. Note ( horizon 14 jours : la mobilite
   change le jour de l achat, l engagement de la mensualite et le tampon entame aussi ; la faim d une caisse videe se
   voit en deux semaines ) : chaque jour, pour CE menage, 0,5 x mobilite ( km faits dans ses vehicules sur ses km
   voulus : son trajet au travail et au marche, au moins 8 km ) + 0,5 x a mange - l exces de son taux d effort
   automobile au-dela de 35 %, borne a 1 ( mensualites des credits auto, carburant et entretien du jour, sur son revenu ;
   un achat ou une reparation pesent par le tampon ) - 0,5 si sa caisse ne tient plus 7 jours de nourriture. Regle : un vehicule qui roule se garde jusqu a deux
   pannes ou accidents en 90 jours ou 98 % de sa vie ; sans vehicule, rien si le menage a moins de 4 km a faire par jour et moins de 3 personnes ;
   sinon l occasion s il reste 30 jours de nourriture apres l avoir payee comptant ; sinon le neuf a credit si le revenu
   passe 150 drachmes par jour, que la mensualite tient dans 15 % du revenu et l apport dans la caisse ; sinon rien.
   Temoin : toujours l occasion la moins chere.
   `reparer_vehicule` ( chaque vehicule de menage en panne, a la panne ou a l accident, puis tous les 7 jours tant
   qu il est immobilise ) : reparer, occasion, neuf, abandonner ( au rebut ). Traits : devis sur valeur venale, devis
   sur caisse, age, usure, revenu, autres vehicules utilisables, besoin de km, mensualites, pannes des 90 jours. Note :
   la meme que l achat, sur 14 jours. Regle : reparer si le devis tient dans la
   caisse et coute moins que remplacer ( la plus grande de 60 % de la valeur et de la moitie de l occasion la moins
   chere ) ; sinon l occasion si elle est payable ; sinon la casse. Temoin : toujours reparer.
4. Evenements. Individuels : accident_de_la_route, vol_de_vehicule, vehicule_retrouve, vehicule_detruit. Comptes :
   vente_neuf, vente_occasion, reprise_vehicule, import_neuf, import_occasion, export_occasion, plein_carburant ( litres ),
   km_parcourus, station_a_sec, panne_vehicule, entretien_vehicule, reparation_vehicule, sinistre_materiel,
   blessure_route, tue_route, blessure_sans_medecine, vehicule_rebut, permis_obtenu, examen_echoue,
   taxe_circulation, taxe_circulation_impayee, credit_auto, credit_auto_refuse, achat_abandonne, penurie_pieces,
   benefice_transport.
5. Liens. Banques ( 2 ) : `ouvrir_compte` de chaque detenteur, `demander_credit` ( type conso, motif credit_auto, 60 mois
   pour le neuf, 48 pour l occasion ), `rembourser_par_anticipation` d un pret qui ne suffit pas. Exterieur ( 7 ) :
   `declarer_import` ( famille produit_fini, motif import_vehicules ) pour les vehicules neufs et d occasion ;
   `importer_au_port` pour les pieces, les pneus et le carburant qui manque ; l export des occasions invendues est paye
   par l etranger ( motif export_vehicules, nature achat : la balance le range en biens ; le domaine 7 n a pas de
   declaration d export pour un objet ). Industrie ( 10 ) : `commander` et `livrer` des pieces mecaniques ( acier
   usine ) ; ATTENTION : `commander` ecrase aujourd hui la commande d un autre domaine pour le meme bien ( un dict par
   bien ) - signale, pas corrige. Energie ( 11 ) : les stations achetent gazole et essence par `vendre_produit` au prix
   de depart. Etat ( 6, installe par le 7 ) : TVA par `percevoir_tva` ( carburant, pieces ) et au taux de la categorie
   normale sur les vehicules ; accise du carburant, taxe d immatriculation, taxe de circulation et frais de permis payes
   a l Etat sous les motifs du domaine ( `percevoir` du domaine 6 ne les accepte pas encore ) ; un impaye de taxe de
   circulation devient une creance de l Etat. Population ( 1 ) : `deceder( h, "accident" )` pour les tues ; ages, sexes,
   menages dissous. Medecine ( 16, si installee ) : `blesser( h, "route", ISS, "accident", lieu )`, et
   `reprendre_accidents( p, "route" )` des le premier matin ( la medecine s installe apres le transport ). Services
   publics ( 12, si installes ) : pour moitie `facteur_accident` du trajet domicile - marche de chaque lieu, pour moitie
   le facteur du reseau de son ile ( `troncons`, pondere par les km ) ; le trafic des voitures y est deja compte
   ( TRAFIC_VOITURE_HAB_J ou l agenda ) : seuls les camions et les bus du domaine passent par `passer`.
   Agenda ( 5, si installe ) : les km en vehicule du plan du jour de chaque menage remplacent le kilometrage moyen du
   premier vehicule. Economie ( 3 ) : NEUTRALISE PAR UNE DONNEE, le temps de l achat de 19 h, la part du gazole de marche
   dans la division transport ( PART_BIEN = 0 de 18 h 50 a 19 h ) : le menage fait desormais le plein a la station pour
   ses km reels ; le reste de la division reste une demande en attente que ce domaine sert par ses propres achats.
   Revenu lisse ( eco_revenu ) lu pour les decisions. Paie et recoit : ventes de vehicules ( menage -> concession ),
   reprises ( concession -> menage ), TVA et taxe d immatriculation ( -> Etat ), imports ( concession -> exterieur ),
   carburant ( menage ou entreprise -> station ; station -> raffinerie ; accise -> Etat ), entretien, reparations et
   lecons de conduite ( -> garage ), frais de permis et taxe de circulation ( -> Etat ), benefices ( detenteur -> son
   proprietaire, chaque mois ), rachat des vehicules d un menage eteint ( concession -> Etat ). Ne remplace aucune
   methode du moteur. Capital d ouverture des concessions : la moitie de leur stock neuf vise, investissement direct de
   l etranger ( motif du domaine 7 ; les importateurs grecs sont souvent des filiales de constructeurs ). Credit
   fournisseur : une entreprise dont la caisse ne paie pas une reparation la doit au garage ( creance du socle ). API en
   fin de fichier ( domaines 15, 17, 18, 20, 21, 25 ).
6. Portes : tests_d14_transport.py.
7. Arma. Chaque modele porte un classname du jeu de base, d Apex ou de CUP, JAMAIS le van C_Van_01_box_F ( il naissait
   mort ) ; `arma_preuve = None` partout : aucun n a ete vu vivre en jeu. Deux vehicules crees au meme point se detruisent :
   `emplacements( n )` rend des decalages espaces d au moins ESPACEMENT_M metres pour poser n vehicules d une concession,
   d un garage ou d une station. Un vehicule ne roule qu avec une destination posee avant l ordre de marche ( lecon
   payee du 22/09 ) : a la charge du pont.
8. Cout. Tout ce qui touche les vehicules des menages est vectorise sur les colonnes ( une passe par jour : roulage,
   carburant, usure, tirages des pannes, accidents, vols, rebuts, entretiens dus ) ; les boucles Python ne visitent que
   les evenements du jour ( pleins : ~ 1 vehicule sur 7 par jour ; entretiens ~ 1 sur 300 ; pannes, accidents, vols :
   quelques-uns pour 10 000 ), les decisions ( les candidats du jour, ~ 1 menage sur 15 ) et les notes en attente. Une
   passe par jour sur les habitants ( permis, ages, classes par menage ), comme le domaine 3. Mesure du 24/09 ( test_cout,
   10 005 habitants, 7 323 menages, 8 715 vehicules ) : le pays avec ses dependances 1,76 s par jour, avec le transport
   1,79 a 1,88 s ( +1 a +7 %, dans le bruit de la mesure ), soit 3 a 12 us par habitant : ~ 2 a 10 minutes par jour a
   50 millions. Colonnes : 66 octets par menage et 1 par habitant ( ~ 1,4 Go a 50 millions ) contre 158 octets par objet
   du Parc ( ~ 4,4 Go pour 28 millions de vehicules individuels )."""
import importlib, math
import numpy as np
from .. import config as C
from ..socle import decision as D, objets as O, biens as BI
from . import pays as PAYS, d01_population as POP, d02_banques as BQ, d03_economie as EC, d06_etat as ET
from . import d07_exterieur as EXT, d10_industrie as IND, d11_energie as ENE

JOURS_AN = 365.0
EPS = 1e-9
DR = 1.0 / PAYS.EUROS_PAR_DRACHME          # un euro, en drachmes
K3 = (0, 1, 2)                               # les emplacements de vehicules d un menage
LITRES_UNITE = ENE.LITRES_UNITE              # 1 unite de carburant du moteur = 10 litres ( domaine 11 )
ANNEE_0 = C.DATE_DEPART[0] + (C.DATE_DEPART[1] - 0.5) / 12.0   # l annee du jour 0 du monde ( mi-juin 2035 )

# ================================================================== les modeles de vehicules
# Prix : prix catalogue grec TTC ( TVA 24 % et taxe d immatriculation comprises ), ordre de grandeur des tarifs
# 2024-2025 des importateurs grecs ( Toyota Hellas, Hyundai Hellas, Skoda, Nissan, Ford, Mercedes, MAN, KTEL pour les
# autocars ; tracteurs : New Holland, John Deere ) - a verifier modele par modele. Consommation : cycle WLTP + ~10 %
# ( ecart d usage reel, ICCT 2019 ) ; camion : 24 l/100 km ( porteur 12-18 t en distribution, ACEA ) ; autocar 32
# ( KTEL, a calibrer ) ; tracteur : ~ 6 l par heure a ~ 10 km/h equivalents, soit 55 l aux 100 km-equivalents ( a
# calibrer ). Pannes : immobilisations au garage par an d un vehicule neuf ( a calibrer ; ADAC Pannenstatistik pour
# l ordre de grandeur : de 1 a 5 % d assistance routiere par an, auxquelles s ajoutent les pannes menees au garage ) ;
# elles croissent avec l usure ( x ( 1 + 4 u^2 ) ) et doublent quand l entretien est en retard. Kilometrage annuel :
# vehicule neuf ( Odyssee-Mure, Grece : ~ 11 000 km par voiture et par an en moyenne du parc, a verifier ) ; il baisse
# de 2 % par annee d age ( les vieilles voitures roulent moins ). Duree de vie : km avant l usure complete ( a calibrer ).
# CO2 : WLTP g/km ( taxe de circulation ). Pieces ( kg ) et heures d un entretien, pneus en equivalents de pneus de
# voiture pour un train complet, km d un train de pneus, intervalle d entretien ( km ).
#   nom, categorie, classname Arma, prix TTC euros, masse kg, carburant, l/100 km, reservoir l, places, charge kg,
#   vitesse km/h, pannes par an ( neuf ), vie km, km par an ( neuf ), cylindree cm3, CO2 g/km, permis,
#   pieces kg, heures, pneus, km par train de pneus, intervalle d entretien km
MODELES = (
    ("citadine", "voiture", "C_Hatchback_01_F", 16500.0, 1050.0, "essence", 5.9, 40.0, 5, 420.0, 170.0, 0.12,
     300000.0, 13000.0, 1100, 120, "B", 6.0, 1.5, 4.0, 40000.0, 15000.0),
    ("berline", "voiture", "CUP_C_Octavia_CIV", 26000.0, 1350.0, "essence", 6.6, 50.0, 5, 500.0, 205.0, 0.12,
     350000.0, 17000.0, 1500, 140, "B", 7.0, 1.8, 4.0, 40000.0, 15000.0),
    ("suv", "voiture", "C_SUV_01_F", 36000.0, 1550.0, "carburant", 6.3, 55.0, 5, 550.0, 195.0, 0.12,
     350000.0, 19000.0, 1700, 160, "B", 8.0, 2.0, 4.0, 45000.0, 20000.0),
    ("pick_up", "utilitaire_leger", "C_Offroad_01_F", 38000.0, 2050.0, "carburant", 8.7, 80.0, 5, 1000.0, 175.0, 0.15,
     450000.0, 18000.0, 2400, 225, "B", 10.0, 2.2, 4.0, 45000.0, 20000.0),
    ("utilitaire", "utilitaire_leger", "C_Van_01_transport_F", 34000.0, 2100.0, "carburant", 9.5, 90.0, 3, 1300.0,
     155.0, 0.20, 450000.0, 25000.0, 2300, 245, "B", 12.0, 2.5, 4.0, 50000.0, 25000.0),
    ("camion", "poids_lourd", "C_Truck_02_transport_F", 85000.0, 7500.0, "carburant", 24.0, 200.0, 3, 7000.0, 90.0,
     0.80, 1200000.0, 50000.0, 6700, 630, "C", 40.0, 5.0, 24.0, 100000.0, 40000.0),
    ("bus", "autocar", "CUP_C_Ikarus_Chernarus", 260000.0, 12500.0, "carburant", 32.0, 300.0, 55, 5000.0, 100.0, 1.20,
     1200000.0, 60000.0, 10500, 840, "D", 60.0, 8.0, 24.0, 100000.0, 40000.0),
    ("moto", "deux_roues", "CUP_C_TT650_CIV", 7500.0, 190.0, "essence", 4.6, 15.0, 2, 180.0, 165.0, 0.10,
     150000.0, 6000.0, 650, 107, "A", 2.0, 1.2, 2.0, 20000.0, 8000.0),
    # aucun scooter au jeu de base ni, a notre connaissance, dans CUP : le quad du jeu de base sert de corps de
    # substitution ( meme gabarit, deux places ) - a remplacer si un scooter est trouve
    ("scooter", "deux_roues", "C_Quadbike_01_F", 3200.0, 125.0, "essence", 2.6, 8.0, 2, 150.0, 100.0, 0.10,
     90000.0, 5000.0, 125, 60, "A1", 1.5, 1.0, 1.2, 15000.0, 5000.0),
    ("tracteur", "agricole", "CUP_C_Tractor_CIV", 60000.0, 4200.0, "carburant", 55.0, 150.0, 1, 2000.0, 40.0, 0.50,
     150000.0, 5000.0, 4400, 0, "B", 20.0, 4.0, 16.0, 30000.0, 5000.0),
)
NOMS = tuple(m[0] for m in MODELES)
NM = len(MODELES)
CATEGORIES = ("voiture", "utilitaire_leger", "poids_lourd", "autocar", "deux_roues", "agricole")
VOITURES = ("citadine", "berline", "suv")
DETAIL = ("citadine", "berline", "suv", "pick_up", "utilitaire", "moto", "scooter")   # ce que vend une concession
# vitesse moyenne d usage ( km/h ) : la conversion de la duree de vie en heures du Parc ( Modele.vie_h )
V_USAGE = {"voiture": 40.0, "utilitaire_leger": 40.0, "poids_lourd": 50.0, "autocar": 45.0, "deux_roues": 35.0,
           "agricole": 10.0}
PERMIS_BITS = {"B": 1, "A": 2, "A1": 4, "C": 8, "D": 16}
# Ce qu un titulaire peut conduire : un permis A vaut A1 ; le permis B ouvre les scooters de 125 cm3 ( Grece, loi
# 4850/2021 pour les boites automatiques - a verifier ).
PERMIS_OUVRE = {"B": 1, "A": 2, "A1": 1 | 2 | 4, "C": 8, "D": 16}

# ================================================================== la fiscalite ( Grece )
# Taxe de circulation ( teli kykloforias ) des voitures immatriculees depuis le 1/11/2010 : euros par g/km de CO2
# ( loi 3845/2010, modifiee par la loi 4389/2016 ; a verifier ) ; avant : selon la cylindree.
CO2_BAREME = ((90, 0.0), (100, 0.90), (120, 0.98), (140, 1.20), (160, 1.85), (180, 2.45), (200, 2.78), (250, 3.05),
              (math.inf, 3.72))
CC_BAREME = ((300, 22.0), (785, 55.0), (1071, 120.0), (1357, 135.0), (1548, 240.0), (1738, 265.0), (1928, 300.0),
             (2357, 615.0), (3000, 660.0), (4000, 800.0), (math.inf, 880.0))
MOTO_BAREME = ((200, 15.0), (300, 22.0), (400, 30.0), (600, 60.0), (800, 90.0), (math.inf, 150.0))
TAXE_CIRCULATION_FIXE = {"utilitaire_leger": 140.0, "poids_lourd": 600.0, "autocar": 360.0, "agricole": 0.0}   # a verifier
ANNEE_CO2 = 2010.83
# Taxe d immatriculation ( teli taxinomisis ) des voitures neuves, part de la valeur hors TVA selon le CO2 ( reforme de
# 2021, a verifier ) ; les autres categories n en paient pas ici ( a verifier ).
IMMAT_BAREME = ((120, 0.04), (140, 0.08), (160, 0.16), (180, 0.24), (math.inf, 0.32))
# Accise ( EFK ) : essence sans plomb 700 euros les 1 000 l, gazole 410 ( Grece, code des douanes, loi 2960/2001 art. 73,
# taux en vigueur depuis 2011 et 2016 ; a verifier ).
ACCISE_L = {"essence": 0.70 * DR, "carburant": 0.41 * DR}
FRAIS_PERMIS = 80.0 * DR              # paravola d examen ( ordre de grandeur, a verifier )
LECONS_PERMIS = 450.0 * DR            # auto-ecole : ~ 20 lecons ( a calibrer )
REUSSITE_EXAMEN = 0.55                # a calibrer ( taux de reussite de l epreuve pratique grecque ~ 50-60 % )
PASSAGE_PERMIS_AN = ((18, 0.25), (25, 0.10), (30, 0.03), (60, 0.0))   # sans permis B : chance de s y presenter par an

# ================================================================== le commerce
MARGE_NEUF = 0.08                     # marge brute d un concessionnaire sur le neuf ( 5-10 % en Europe, a calibrer )
MARGE_OCCASION = 0.15                 # sur l occasion ( 10-20 %, a calibrer )
DECOTE_REPRISE = 0.15                 # la reprise se paie 15 % sous la valeur venale ( a calibrer )
DECOTE_IMPORT_OCCASION = 0.85         # une occasion importee ( Allemagne ) coute 85 % de sa valeur grecque ( a calibrer )
DEPREC_AN = 0.90                      # valeur venale : 85 % du prix hors taxes la premiere annee, puis 10 % par an,
DEPREC_1 = 0.85                       # plancher 7 % ; moins 25 % a l usure complete ( marche grec de l occasion : les vieilles
PLANCHER_VALEUR = 0.07                # voitures y gardent leur valeur ; a calibrer )
VENTES_NEUF_1000_AN = 12.5            # voitures neuves vendues par an pour 1 000 habitants ( ~ 130 000 en Grece, SEAA 2023 )
VENTES_OCC_1000_AN = 20.0             # occasions vendues par un professionnel ( a calibrer )
STOCK_NEUF_J, STOCK_OCC_J = 45, 60    # jours de ventes en stock
STOCK_MIN_NEUF = {"citadine": 2, "berline": 1, "suv": 1, "pick_up": 1, "utilitaire": 1, "moto": 1, "scooter": 1}
STOCK_MIN_OCC = 3
DELAI_LIVRAISON_J = EXT.DELAI_MER_J + 1   # la mer, puis le dedouanement et la preparation
EXPORT_APRES_J = 120                  # une occasion invendue au-dela part a l export ( Balkans, a calibrer )
DUREE_CREDIT_NEUF, DUREE_CREDIT_OCC = 60, 48   # mois ( credit auto grec : 48 a 84 mois, a calibrer )
APPORT_MIN = 0.10
EFFORT_MAX_AUTO = 0.15                # une mensualite auto au plus 15 % du revenu mensuel ( regle ; a calibrer )
MARGE_STATION_L = 0.12 * DR           # marge brute d une station par litre ( a calibrer, ~ 10-15 centimes en Grece )
STOCK_STATION_J = 4.0
TAUX_HORAIRE_GARAGE = 35.0 * DR       # euros de l heure hors TVA, garage independant grec ( a calibrer )
MARKUP_PIECES = 1.6                   # prix de vente des pieces sur leur cout rendu ( a calibrer )
PART_PIECES_INDUSTRIE = 0.3           # part des pieces d un entretien que l acier usine du pays peut fournir ( a calibrer )
STOCK_GARAGE_J = 30.0
# pieces et pneus par habitant et par jour : ~ 0,85 vehicule par habitant ; un entretien par an ( ~ 7 kg ), ~ 0,3 panne
# ( ~ 15 kg ) et ~ 0,055 accident materiel ( ~ 60 kg ) par vehicule et par an ; un pneu par vehicule et par an
PIECES_HAB_J, PNEUS_HAB_J = 0.035, 0.0025
FDR_J = 30                            # jours d achats gardes en caisse ; le reste des benefices va au proprietaire
PART_DISTRIBUEE = 0.5
PRIX_PIECES_EUR_KG, PRIX_PNEU_EUR = 12.0, 60.0
RESERVE_ALIMENTAIRE_J = 7             # un menage ne depense pas pour son vehicule sa derniere semaine de nourriture
RESERVE_ACHAT_J = 30                  # ni, pour acheter un vehicule, son dernier mois

# ================================================================== le parc du pays ( recensement )
# ELSTAT, parc en circulation fin 2023 : ~ 5,8 millions de voitures, ~ 1,4 million de camions et utilitaires, ~ 27 000
# autocars, ~ 1,7 million de motocycles, pour 10,4 millions d habitants ; Eurostat ( road_eqs_carhab ) : ~ 560 voitures
# pour 1 000 habitants ( a verifier ). Age moyen des voitures ~ 17 ans ( ACEA, Vehicles on European roads 2024 : un des
# parcs les plus vieux de l Union ; a verifier ), des utilitaires ~ 20 ans.
VOITURES_1000 = 560.0
DEUX_ROUES_1000 = 160.0
PICKUP_PAYSAN = 0.5                   # un menage paysan a un pick-up ( l agrotiko ) avec cette chance ( a calibrer )
AGE_MOYEN = {"voiture": 17.0, "utilitaire_leger": 20.0, "poids_lourd": 20.0, "autocar": 17.0, "deux_roues": 15.0,
             "agricole": 25.0}
AGE_MAX = 45.0
VOITURES_PAR_QUINTILE = (0.55, 0.95, 1.30, 1.65, 2.05)   # voitures par menage selon son quintile de revenu ( a calibrer )
PART_MODELES_CLASSE = {0: (0.65, 0.30, 0.05), 1: (0.40, 0.45, 0.15), 2: (0.10, 0.45, 0.45)}   # citadine, berline, suv
PART_MOTO = 0.4                       # parmi les deux-roues d un titulaire du permis A ( a calibrer )
# Composition nationale pour 1 000 habitants ( l etalonnage des accidents ) : voitures en parts de PART_MODELES_CLASSE
# ( ~ 46 % de citadines, 37 % de berlines, 18 % de SUV ), le reste d ELSTAT ( a verifier ).
PARC_1000 = {"citadine": 257.0, "berline": 203.0, "suv": 100.0, "pick_up": 40.0, "utilitaire": 65.0, "camion": 25.0,
             "bus": 2.6, "moto": 64.0, "scooter": 96.0, "tracteur": 25.0}
PERMIS_B_AGE = {POP.HOMME: ((18, 0.60), (25, 0.90), (65, 0.75)), POP.FEMME: ((18, 0.50), (25, 0.70), (65, 0.30))}
PERMIS_A = {POP.HOMME: 0.35, POP.FEMME: 0.06}
PERMIS_A1 = 0.08
PERMIS_C_HOMMES, PERMIS_D_HOMMES = 0.06, 0.012
# flottes des entreprises du moteur : vehicules par travailleur ( a calibrer )
FLOTTE_TYPE = {"ferme": (("tracteur", 0.25),), "mine": (("camion", 0.125), ("utilitaire", 0.05)),
               "carriere": (("camion", 0.125), ("utilitaire", 0.05)), "raffinerie": (("utilitaire", 0.07),),
               "puits": (("utilitaire", 0.07),), "fonderie": (("utilitaire", 0.1),), "pharmacie": (("utilitaire", 0.1),),
               "centrale": (("utilitaire", 0.1),)}
UTILITAIRES_MARCHE_HAB = 250.0        # un utilitaire de livraison par marche pour 250 habitants servis
BUS_1000 = 2.6

# ================================================================== la vie des vehicules
FACTEUR_SEMAINE = (1.0, 1.0, 1.0, 1.0, 1.05, 0.9, 0.7)   # lundi..dimanche ( a calibrer )
BAISSE_KM_AN = 0.02
PLANCHER_KM = 0.45
SEUIL_PLEIN = 0.3                     # on fait le plein sous 30 % du reservoir
USURE_PANNE = 4.0
RETARD_ENTRETIEN = 2.0
JOURS_ENTRETIEN = 365
# Pannes : devis ( kg de pieces et heures ), loi log-normale ( mediane, sigma ) ; accidents materiels et corporels
DEVIS_PANNE = ((15.0, 0.8), (4.0, 0.6))
DEVIS_MATERIEL = ((60.0, 0.8), (12.0, 0.6))
DEVIS_CORPOREL = ((250.0, 0.6), (30.0, 0.5))
ECHELLE_DEVIS = {"voiture": 1.0, "utilitaire_leger": 1.3, "poids_lourd": 3.0, "autocar": 4.0, "deux_roues": 0.4,
                 "agricole": 2.0}
HEURES_JOUR_GARAGE = 8.0
REDECIDER_J = 7
REFUS_MAX = 3
# Fin de vie : chance annuelle de retrait Q / ( 1 + exp( -( age - A50 ) / S ) ), et 50 % par an a l usure complete
# ( ~ 2 % du parc par an en Grece, deimmatriculations ELSTAT, a verifier ).
REBUT_Q, REBUT_S = 0.30, 4.0
REBUT_A50 = {"voiture": 30.0, "utilitaire_leger": 32.0, "poids_lourd": 32.0, "autocar": 28.0, "deux_roues": 25.0,
             "agricole": 40.0}
REBUT_USE = 0.5

# ================================================================== accidents de la route ( Grece )
# ELSTAT ( accidents de la circulation 2022-2023 ) et ETSC ( PIN 2024 ) : ~ 10 000 accidents corporels, ~ 11 700
# victimes, ~ 600 tues a 30 jours par an pour 10,4 millions d habitants ; les usagers de deux-roues motorises font ~ un
# tiers des tues ( a verifier ).
ACCIDENTS_CORPORELS_M_AN = 950.0
VICTIMES_PAR_ACCIDENT = 1.19
TUES_M_AN = 57.0
RISQUE_CORPOREL = {"voiture": 1.0, "utilitaire_leger": 1.1, "poids_lourd": 1.5, "autocar": 1.0, "deux_roues": 9.0,
                   "agricole": 3.0}   # risque relatif par km ( a calibrer )
MORT_RELATIVE = {"voiture": 1.0, "utilitaire_leger": 1.2, "poids_lourd": 2.0, "autocar": 1.0, "deux_roues": 1.6,
                 "agricole": 2.5}
# les survivants : gravite ISS ( la table de la medecine sans les lesions insurvivables )
ISS_SURVIVANTS = (((1, 8), 0.80), ((9, 15), 0.13), ((16, 24), 0.05), ((25, 49), 0.02))
LETAL_ISS_SOIGNE = ((1, 0.0002), (4, 0.001), (9, 0.015), (16, 0.07), (25, 0.25), (41, 0.55), (75, 1.0))   # domaine 16
PASSAGER = 0.3                        # chance qu un autre membre du menage soit a bord
# Accidents materiels ( sinistres responsabilite civile ) : ~ 5,5 % des vehicules assures par an ( assureurs grecs,
# HAIC ; a verifier ), rapportes aux km d une voiture moyenne.
MATERIELS_VOITURE_AN = 0.055
RISQUE_MATERIEL = {"voiture": 1.0, "utilitaire_leger": 1.3, "poids_lourd": 2.0, "autocar": 2.0, "deux_roues": 0.6,
                   "agricole": 0.5}
DETRUIT_CORPOREL = {"voiture": 0.25, "utilitaire_leger": 0.2, "poids_lourd": 0.1, "autocar": 0.05, "deux_roues": 0.35,
                    "agricole": 0.15}
RESPONSABLE = 0.5
# Vols : police grecque, ~ 5 000 voitures et ~ 6 000 motos volees par an ( 2019, a verifier ) ; ~ 40 % retrouvees.
VOL_AN = {"voiture": 0.0009, "utilitaire_leger": 0.0012, "poids_lourd": 0.0004, "autocar": 0.0001, "deux_roues": 0.0035,
          "agricole": 0.0003}
RETROUVE = 0.4
ENQUETE_J = 30
EXPORT_VOLE = 0.6                     # un vehicule non retrouve part a l etranger, sinon il est depece ( a calibrer )

# ================================================================== decisions
HORIZON_ACHAT = 14
HORIZON_REPARER = 14
KM_MOBILITE_MIN = 8.0
SEUIL_EFFORT = 0.35
AGE_REMPLACER, USURE_REMPLACER = 18.0, 0.85   # a partir de la, le menage se pose la question
JOURS_SANS, JOURS_VIEUX = 7, 14                # sans vehicule : chaque semaine ; avec un vieux vehicule qui lache : tous
                                               # les 14 jours ( a calibrer )
AGE_COMMANDE = 10.0                            # l age d une occasion commandee pour un client ( a calibrer )
REMPLACEMENT_REF = 3000.0 * DR                 # une occasion bon marche, quand la concession n en a pas ( a calibrer )
PANNES_USE, USURE_USE = 2, 0.98                # la regle ne remplace un vehicule qui roule qu apres 2 pannes ou
                                               # accidents en 90 jours, ou a 98 % de sa vie ( a calibrer )
BESOIN_MIN_KM = 4.0                            # sans vehicule, la regle n achete que si le menage a des km a faire
ESPACEMENT_M = 8.0                    # deux vehicules poses a moins de 8 m l un de l autre risquent de se detruire


class Caracteristiques:
    """Un modele de vehicule civil, ses chiffres reels. `modele` : le Modele du Parc ( prix_monde = prix FOB au port,
    la reference de l import ). Derives : prix hors taxes de la concession, taxe d immatriculation, autonomie."""
    __slots__ = ("idx", "nom", "categorie", "arma", "prix_ttc", "masse_kg", "carburant", "l100", "reservoir_l",
                 "places", "charge_kg", "vitesse_kmh", "pannes_an", "vie_km", "km_an", "cc", "co2", "permis",
                 "pieces_kg", "heures", "pneus", "km_pneus", "intervalle_km", "taux_immat", "ht", "cout_rendu", "fob",
                 "modele")

    def __init__(self, idx, nom, categorie, arma, prix_ttc_eur, masse_kg, carburant, l100, reservoir_l, places,
                 charge_kg, vitesse_kmh, pannes_an, vie_km, km_an, cc, co2, permis, pieces_kg, heures, pneus, km_pneus,
                 intervalle_km):
        if categorie not in CATEGORIES: raise ValueError(f"{nom} : categorie inconnue {categorie!r}")
        if carburant not in ACCISE_L: raise ValueError(f"{nom} : carburant inconnu {carburant!r}")
        if permis not in PERMIS_BITS: raise ValueError(f"{nom} : permis inconnu {permis!r}")
        if arma == "C_Van_01_box_F": raise ValueError(f"{nom} : le van C_Van_01_box_F naissait mort ( 22/09 )")
        for v, q in ((prix_ttc_eur, "prix"), (masse_kg, "masse"), (l100, "consommation"), (reservoir_l, "reservoir"),
                     (vitesse_kmh, "vitesse"), (vie_km, "vie"), (km_an, "km par an"), (intervalle_km, "intervalle"),
                     (km_pneus, "km des pneus")):
            if not 0.0 < v < 1e8: raise ValueError(f"{nom} : {q} hors bornes {v!r}")
        if not 0.0 < pannes_an < 50.0 or not 1 <= places <= 120 or not 0.0 <= charge_kg < 1e5 or co2 < 0:
            raise ValueError(f"{nom} : chiffres hors bornes")
        self.idx, self.nom, self.categorie, self.arma = idx, nom, categorie, arma
        self.prix_ttc = prix_ttc_eur * DR
        self.masse_kg, self.carburant, self.l100, self.reservoir_l = masse_kg, carburant, l100, reservoir_l
        self.places, self.charge_kg, self.vitesse_kmh, self.pannes_an = places, charge_kg, vitesse_kmh, pannes_an
        self.vie_km, self.km_an, self.cc, self.co2, self.permis = vie_km, km_an, cc, co2, permis
        self.pieces_kg, self.heures, self.pneus, self.km_pneus, self.intervalle_km = pieces_kg, heures, pneus, km_pneus, intervalle_km
        self.taux_immat = bareme(IMMAT_BAREME, co2) if categorie == "voiture" else 0.0
        self.ht = self.prix_ttc / (1.0 + ET.TAUX_TVA["normale"]) / (1.0 + self.taux_immat)
        self.cout_rendu = self.ht / (1.0 + MARGE_NEUF)
        self.fob = self.cout_rendu / ((1.0 + EXT.FRET["produit_fini"]) * (1.0 + ET.DROITS_DOUANE["produit_fini"]))
        self.modele = None

    def autonomie_km(self): return self.reservoir_l * 100.0 / self.l100


def bareme(table, x):
    """La valeur de la premiere tranche dont le plafond atteint x."""
    for plafond, v in table:
        if x <= plafond: return v
    return table[-1][1]


CARAC = tuple(Caracteristiques(i, *m) for i, m in enumerate(MODELES))
IDX = {c.nom: c.idx for c in CARAC}
CAT_IDX = np.array([CATEGORIES.index(c.categorie) for c in CARAC], np.int64)
KM_AN = np.array([c.km_an for c in CARAC])
L100 = np.array([c.l100 for c in CARAC])
TANK = np.array([c.reservoir_l for c in CARAC])
VIE_KM = np.array([c.vie_km for c in CARAC])
PANNE_AN = np.array([c.pannes_an for c in CARAC])
INTERVALLE = np.array([c.intervalle_km for c in CARAC])
PERMIS_REQ = np.array([PERMIS_OUVRE[c.permis] for c in CARAC], np.int64)
FUEL_IDX = np.array([0 if c.carburant == "essence" else 1 for c in CARAC], np.int64)
FUELS = ("essence", "carburant")
IS_VOITURE = np.array([c.categorie == "voiture" for c in CARAC])


def _par_cat(d): return np.array([d[c] for c in CATEGORIES])


def facteur_age(age):
    """Les km d un vehicule de cet age sur ceux d un neuf."""
    return np.maximum(PLANCHER_KM, 1.0 - BAISSE_KM_AN * np.asarray(age, float))


def valeur_venale(c, age, usure):
    """Drachmes : ce que vaut un vehicule sur le marche de l occasion ( hors taxes )."""
    f = max(PLANCHER_VALEUR, DEPREC_1 * DEPREC_AN ** max(0.0, age))
    return c.ht * f * (1.0 - 0.25 * min(1.0, max(0.0, usure)))


def taxe_circulation(c, annee_immat):
    """Euros ( en drachmes ) de taxe de circulation annuelle d un vehicule immatricule en `annee_immat`."""
    if c.categorie == "voiture":
        e = bareme(CO2_BAREME, c.co2) * c.co2 if annee_immat >= ANNEE_CO2 else bareme(CC_BAREME, c.cc)
    elif c.categorie == "deux_roues":
        e = bareme(MOTO_BAREME, c.cc) if c.cc > 125 else 0.0
    else:
        e = TAXE_CIRCULATION_FIXE[c.categorie]
    return e * DR


def rebut_an(cat_idx, age, usure):
    """Chance annuelle de retrait ( tableaux ) : logistique en age, plus la moitie par an a l usure complete."""
    a50 = _par_cat(REBUT_A50)[cat_idx]
    q = REBUT_Q / (1.0 + np.exp(-(np.asarray(age, float) - a50) / REBUT_S))
    return np.where(np.asarray(usure) >= 1.0, np.maximum(q, REBUT_USE), q)


def _letalite_soignee(iss):
    v = 0.0
    for seuil, x in LETAL_ISS_SOIGNE:
        if iss >= seuil: v = x
    return v


def _letalite_moyenne_survivants():
    """La part des survivants de l accident qui meurent a l hopital ( lois de la medecine, a 45 ans ) : ce qui manque
    aux morts sur le coup pour faire les tues a 30 jours."""
    return sum(pr * np.mean([_letalite_soignee(i) for i in range(a, b + 1)]) for (a, b), pr in ISS_SURVIVANTS)


def _etalonner():
    """Les taux de base, par km pondere du risque, qui redonnent les chiffres grecs sur la composition nationale du parc.
    Deterministe, calcule une fois a l import. Rend ( corporel par km, materiel par km, mort sur le coup de reference )."""
    expo = expo_mat = 0.0
    victimes_mort = 0.0
    km = {}
    for c in CARAC:
        k = c.km_an * float(facteur_age(AGE_MOYEN[c.categorie])) * PARC_1000[c.nom] / 1000.0
        km[c.nom] = k
        expo += k * RISQUE_CORPOREL[c.categorie]
        expo_mat += k * RISQUE_MATERIEL[c.categorie]
        victimes_mort += k * RISQUE_CORPOREL[c.categorie] * MORT_RELATIVE[c.categorie]
    corporel = ACCIDENTS_CORPORELS_M_AN / 1e6 / expo
    km_voiture = sum(km[n] for n in VOITURES) / sum(PARC_1000[n] / 1000.0 for n in VOITURES)
    materiel = MATERIELS_VOITURE_AN / km_voiture
    victimes = ACCIDENTS_CORPORELS_M_AN * VICTIMES_PAR_ACCIDENT
    hop = _letalite_moyenne_survivants()
    # tues = victimes x ( m + ( 1 - m ) x hop ), m pondere par la mort relative des categories
    m_moy = (TUES_M_AN / victimes - hop) / (1.0 - hop)
    mort_ref = m_moy * expo / victimes_mort
    return corporel, materiel, mort_ref


TAUX_CORPOREL_KM, TAUX_MATERIEL_KM, MORT_REF = _etalonner()
RISQUE_C = _par_cat(RISQUE_CORPOREL)
RISQUE_M = _par_cat(RISQUE_MATERIEL)
MORT_C = _par_cat(MORT_RELATIVE) * MORT_REF
DETRUIT_C = _par_cat(DETRUIT_CORPOREL)
VOL_C = _par_cat(VOL_AN)


def tirer_accidents(rng, km, modeles, facteur_route):
    """Les accidents d une periode, pour des tableaux de vehicules ( km parcourus, indice de modele, facteur d accident
    de la route ). Fonction pure : la meme sert la journee du pays et la porte sur un parc synthetique.
    Rend ( indices des vehicules accidentes, corporel ( bool ), nombre de victimes, tues sur le coup, ISS des blesses
    ( listes par accident ) )."""
    cat = CAT_IDX[modeles]
    lam_c = np.asarray(km, float) * TAUX_CORPOREL_KM * RISQUE_C[cat] * np.asarray(facteur_route, float)
    lam_m = np.asarray(km, float) * TAUX_MATERIEL_KM * RISQUE_M[cat]
    nc = rng.poisson(lam_c)
    nm = rng.poisson(lam_m)
    idx_c = np.repeat(np.nonzero(nc)[0], nc[nc > 0])
    idx_m = np.repeat(np.nonzero(nm)[0], nm[nm > 0])
    victimes = 1 + rng.poisson(VICTIMES_PAR_ACCIDENT - 1.0, len(idx_c))
    pm = MORT_C[cat[idx_c]]
    tues, iss = [], []
    for v, p_ in zip(victimes.tolist(), pm.tolist()):
        u = rng.random(v)
        t = int((u < p_).sum())
        tues.append(t)
        iss.append([_tirer_iss(rng) for _ in range(v - t)])
    idx = np.concatenate([idx_c, idx_m]).astype(np.int64)
    corporel = np.concatenate([np.ones(len(idx_c), bool), np.zeros(len(idx_m), bool)])
    return idx, corporel, np.concatenate([victimes, np.zeros(len(idx_m), np.int64)]), tues + [0] * len(idx_m), iss + [[]] * len(idx_m)


def _tirer_iss(rng):
    u = rng.random(); c = 0.0
    for (a, b), pr in ISS_SURVIVANTS:
        c += pr
        if u < c: return int(rng.integers(a, b + 1))
    return int(rng.integers(ISS_SURVIVANTS[-1][0][0], ISS_SURVIVANTS[-1][0][1] + 1))


def emplacements(n, espacement=ESPACEMENT_M):
    """Des decalages ( dx, dy ) en metres pour poser n vehicules sans que deux se touchent ( lecon payee : deux vehicules
    crees au meme point se detruisent ) : une grille de pas `espacement`."""
    cote = max(1, math.ceil(math.sqrt(n)))
    return [((k % cote) * espacement, (k // cote) * espacement) for k in range(n)]


# ================================================================== les detenteurs et l etat
class Concession:
    """Un concessionnaire neuf et occasion : sa caisse ; son stock neuf est une cohorte du Parc par modele ( proprietaire
    = la concession, lieu = son marche ), ses occasions des individus ( `occasions` : numero -> jour d entree )."""
    __slots__ = ("nom", "marche", "caisse", "proprietaire", "occasions", "commandes", "occ_commandes", "cible_neuf",
                 "cible_occ", "marge_mois", "achats_mois")

    def __init__(self, marche, proprietaire):
        self.nom, self.marche, self.caisse, self.proprietaire = f"concession@{marche}", marche, 0.0, proprietaire
        self.occasions = {}
        self.commandes = [0] * NM          # neufs en mer, par modele
        self.occ_commandes = 0             # occasions en mer
        self.cible_neuf = [0] * NM
        self.cible_occ = STOCK_MIN_OCC
        self.marge_mois = 0.0              # marge brute du mois ( drachmes )
        self.achats_mois = 0.0             # achats du mois ( le fonds de roulement a garder )


class StationService:
    """Une station-service : caisse, Stock du socle ( gazole = « carburant » du moteur, essence ), ventes lissees ( unites
    de 10 litres par jour, par bien )."""
    __slots__ = ("nom", "marche", "caisse", "stock", "proprietaire", "ventes_jour", "ventes_ema", "marge_mois",
                 "achats_mois")

    def __init__(self, marche, proprietaire, stock):
        self.nom, self.marche, self.caisse, self.stock, self.proprietaire = f"station@{marche}", marche, 0.0, stock, proprietaire
        self.ventes_jour = {"essence": 0.0, "carburant": 0.0}
        self.ventes_ema = {"essence": 0.0, "carburant": 0.0}
        self.marge_mois = 0.0
        self.achats_mois = 0.0


class Garage:
    """Un garage ( et son auto-ecole ) : caisse, Stock de pieces detachees ( kg ), de pieces de l industrie ( tonnes ) et
    de pneus ; consommation lissee par bien."""
    __slots__ = ("nom", "marche", "caisse", "stock", "proprietaire", "conso_jour", "conso_ema", "marge_mois",
                 "achats_mois")

    def __init__(self, marche, proprietaire, stock):
        self.nom, self.marche, self.caisse, self.stock, self.proprietaire = f"garage@{marche}", marche, 0.0, stock, proprietaire
        self.conso_jour = {"pieces_auto": 0.0, "pneus": 0.0, "pieces": 0.0}
        self.conso_ema = {"pieces_auto": 0.0, "pneus": 0.0, "pieces": 0.0}
        self.marge_mois = 0.0
        self.achats_mois = 0.0


class Reservoirs:
    """Le carburant dans les reservoirs des vehicules des menages : un seul Stock du socle ( ce que la conservation
    compte ), reparti vehicule par vehicule dans les colonnes vh_res{k} ( litres )."""
    __slots__ = ("stock",)

    def __init__(self, stock): self.stock = stock


class FlotteMenages:
    """Le proprietaire en indivis des cohortes de vehicules des menages ( une par modele et par lieu ) : ce n est pas un
    detenteur d argent. Qui possede quoi est dans les colonnes des menages."""
    __slots__ = ("nom",)

    def __init__(self): self.nom = "menages"


class Receleur:
    """Les vehicules voles, le temps de l enquete."""
    __slots__ = ("nom",)

    def __init__(self): self.nom = "receleur"


class Fiche:
    """Un vehicule qui n est dans aucun menage ( occasion en stock, vole, requisitionne ) : jour d immatriculation,
    compteur, compteur et jour du dernier entretien."""
    __slots__ = ("ne", "km", "ks", "js")

    def __init__(self, ne, km, ks, js): self.ne, self.km, self.ks, self.js = int(ne), float(km), float(ks), int(js)


class Flotte:
    """Les vehicules d une entreprise du moteur ou de l Etat : une cohorte du Parc ( modele, proprietaire, lieu ) ; age
    moyen ( jour d immatriculation moyen ), et le jour de sa taxe de circulation."""
    __slots__ = ("proprietaire", "lieu", "modele", "ne", "jour_taxe", "gere")

    def __init__(self, proprietaire, lieu, modele, ne, jour_taxe, gere=True):
        self.proprietaire, self.lieu, self.modele, self.ne, self.jour_taxe, self.gere = proprietaire, lieu, modele, ne, jour_taxe, gere


class Immatriculation:
    """Le registre : par modele, les entrees ( recensement, import_neuf, import_occasion ) et les sorties ( rebut,
    detruit, exporte ). Ce que le Parc compte doit en etre exactement la difference."""
    __slots__ = ("entrees", "sorties")

    def __init__(self):
        self.entrees = {k: [0] * NM for k in ("recensement", "import_neuf", "import_occasion")}
        self.sorties = {k: [0] * NM for k in O.PUITS}

    def vivants(self, m):
        return sum(v[m] for v in self.entrees.values()) - sum(v[m] for v in self.sorties.values())


class Vol:
    __slots__ = ("id", "jour", "objet", "modele", "victime", "lieu", "valeur", "issue")

    def __init__(self, id, jour, objet, modele, victime, lieu, valeur):
        self.id, self.jour, self.objet, self.modele, self.victime, self.lieu, self.valeur = id, jour, objet, modele, victime, lieu, valeur
        self.issue = None          # retrouve, exporte, depece


class Sinistre:
    """Ce que l assurance ( domaine 20 ) lira : un accident ( materiel ou corporel ) ou un vol."""
    __slots__ = ("id", "jour", "type", "objet", "modele", "proprietaire", "lieu", "responsable", "dommage", "victimes",
                 "tues", "couvert")

    def __init__(self, id, jour, type_, objet, modele, proprietaire, lieu, responsable, dommage, victimes, tues):
        self.id, self.jour, self.type, self.objet, self.modele, self.proprietaire = id, jour, type_, objet, modele, proprietaire
        self.lieu, self.responsable, self.dommage, self.victimes, self.tues = lieu, responsable, dommage, victimes, tues
        self.couvert = 0.0


class Reparation:
    """Un vehicule immobilise : son devis ( kg de pieces, heures ), son garage, le sinistre qui l a cause, les refus."""
    __slots__ = ("objet", "garage", "pieces_kg", "heures", "sinistre", "refus", "en_cours")

    def __init__(self, objet, garage, pieces_kg, heures, sinistre):
        self.objet, self.garage, self.pieces_kg, self.heures, self.sinistre = objet, garage, pieces_kg, heures, sinistre
        self.refus = 0
        self.en_cours = False


class ContexteAchat:
    """Ce que le menage voit : ses traits, et les deux offres de sa concession ( occasion : prix, numero ou None si a
    commander, payable comptant, modele ; neuf : prix, modele, payable comptant, mensualite tenable, en stock )."""
    __slots__ = ("traits", "menage", "occasion", "neuf")

    def __init__(self, traits, menage, occasion, neuf):
        self.traits, self.menage, self.occasion, self.neuf = traits, menage, occasion, neuf


class ContexteReparation:
    __slots__ = ("traits", "menage", "objet", "devis", "valeur", "occasion", "neuf")

    def __init__(self, traits, menage, objet, devis, valeur, occasion, neuf):
        self.traits, self.menage, self.objet, self.devis, self.valeur, self.occasion, self.neuf = traits, menage, objet, devis, valeur, occasion, neuf


class Transport:
    __slots__ = ("mids", "idx_parc", "flotte", "receleur", "reservoirs", "concessions", "stations", "garages",
                 "par_marche", "lieux", "k_lieu", "ind", "slot_de", "fiches", "flottes", "registre", "reparations",
                 "vols", "sinistres", "requisitions", "prets_auto", "dec_achat", "dec_reparer", "scenario", "stats",
                 "part_d03", "km_menage", "depense_jour", "pannes_j", "km_cache", "assureur", "impayes", "bid",
                 "jour_install", "facteur_lieu", "commandes_clients")

    def __init__(self):
        self.mids = []                  # indice du domaine -> identifiant du Modele au Parc
        self.idx_parc = {}              # identifiant du Parc -> indice du domaine
        self.flotte, self.receleur = FlotteMenages(), Receleur()
        self.reservoirs = None
        self.concessions, self.stations, self.garages = [], [], []
        self.par_marche = {}            # marche -> ( concession, station, garage )
        self.lieux, self.k_lieu = [], {}
        self.ind = {}                   # ( menage, emplacement ) -> numero de l individu
        self.slot_de = {}               # numero -> ( menage, emplacement )
        self.fiches = {}                # numero -> Fiche ( vehicules hors menage )
        self.flottes = []
        self.registre = Immatriculation()
        self.reparations = {}           # numero -> Reparation
        self.vols = []
        self.sinistres = []
        self.requisitions = {}          # numero -> ( ancien proprietaire, beneficiaire, jour, valeur )
        self.prets_auto = {}            # menage -> [ Pret ]
        self.dec_achat = self.dec_reparer = None
        self.scenario = {"pannes": 1.0, "accidents": 1.0, "corporels": 1.0, "vols": 1.0, "rebut": 1.0}
        self.stats = {k: 0.0 for k in ("km", "litres_brules", "litres_achetes_d11", "litres_importes", "ventes_neuf",
                                       "ventes_occasion", "reprises", "accidents_corporels", "accidents_materiels",
                                       "victimes", "tues_sur_le_coup", "blesses", "pannes", "entretiens", "reparations",
                                       "vols", "retrouves", "rebuts", "detruits", "exportes", "permis", "examens",
                                       "taxe_circulation", "credits", "credits_refuses", "abandons", "vkm_corporel")}
        self.part_d03 = None
        self.km_menage = np.zeros(0)    # km faits hier par menage ( dans ses vehicules )
        self.depense_jour = {}          # menage -> drachmes depensees aujourd hui pour ses vehicules
        self.pannes_j = {}              # menage -> [ jours des pannes et accidents ]
        self.km_cache = {}              # ( lieu, lieu ) -> km de route
        self.assureur = None            # branche par le domaine 20 : objet appelable ( p, sinistre, montant ) -> pris en charge
        self.impayes = []               # creances de taxe de circulation ( domaine 21 )
        self.bid = {}                   # nom de bien -> identifiant au catalogue
        self.jour_install = 0
        self.facteur_lieu = None
        self.commandes_clients = {}     # menage -> jour de la commande d un vehicule qu il attend


def _tr(p): return p.domaine("transport")


def _membres_concessions(w): return w.pays.domaines["transport"].concessions
def _membres_stations(w): return w.pays.domaines["transport"].stations
def _membres_garages(w): return w.pays.domaines["transport"].garages
def _membres_reservoirs(w): return (w.pays.domaines["transport"].reservoirs,)


# ================================================================== les points de decision
def _observer(ctx): return ctx.traits


def _regle_achat(x, ctx):
    """Un vehicule qui roule encore se garde tant qu il n a pas eu PANNES_USE pannes ou accidents en 90 jours ni atteint
    USURE_USE de sa vie ( le parc grec est vieux : ~ 3 % des voitures remplacees par an ) ; sans vehicule, un menage sans km a faire ni enfants n achete pas ; sinon
    l occasion payable comptant en gardant un mois de nourriture, ou le neuf a credit pour un revenu d au moins 150
    drachmes par jour dont la mensualite tient."""
    revenu, epargne, vehicules, age, usure, besoin, taille, p_occ, p_neuf, mensu, pannes, permis, utilisable = x
    if permis <= 0.0: return 0
    if utilisable > 0.0 and pannes < PANNES_USE / 3.0 and usure < USURE_USE: return 0
    if utilisable <= 0.0 and besoin < BESOIN_MIN_KM / 60.0 and taille < 3.0 / 6.0: return 0
    if ctx.occasion is not None and ctx.occasion[2]: return 1
    if ctx.neuf is not None and ctx.neuf[3] and revenu >= 0.5: return 2
    return 0


def _temoin_achat(x, ctx, rng): return 1


POINT_ACHAT = D.PointDeDecision(
    "acheter_vehicule", "transport",
    traits=(("revenu", "le revenu lisse du menage ( sa paie ), sur 300 drachmes par jour"),
            ("epargne", "sa caisse sur 20 000 drachmes"),
            ("vehicules", "ses vehicules immatricules sur 3"),
            ("age", "l age de son vehicule le plus vieux ( sa carte grise ), sur 30 ans"),
            ("usure", "le compteur de ce vehicule sur sa duree de vie ( le constructeur la publie )"),
            ("besoin", "ses km voulus par jour ( travail et marche ) sur 60"),
            ("taille", "les personnes du menage sur 6"),
            ("prix_occasion", "le prix affiche de l occasion la moins chere de sa concession sur un an de revenu"),
            ("prix_neuf", "le prix catalogue du neuf qui lui va sur deux ans de revenu"),
            ("mensualites", "ses mensualites en cours sur son revenu mensuel"),
            ("pannes", "ses pannes et accidents des 90 derniers jours, sur 3"),
            ("permis", "1 si un adulte du menage a le permis qu il faut"),
            ("utilisable", "1 s il a un vehicule en etat de rouler")),
    actions=("rien", "occasion", "neuf"),
    observer=_observer, regle=_regle_achat, temoin=_temoin_achat,
    note="chaque jour pour CE menage : 0,5 x mobilite ( km faits dans ses vehicules sur ses km voulus ) + 0,5 x a mange - "
         "l exces du taux d effort automobile au-dela de 35 % ( borne a 1 ) - 0,5 si la caisse ne tient plus 7 jours de nourriture",
    horizon_j=HORIZON_ACHAT)


def _regle_reparer(x, ctx):
    """Reparer si la caisse paie et que le devis coute moins que remplacer ( la plus grande de 60 % de la valeur venale et
    de la moitie de l occasion la moins chere : une vieille voiture grecque se repare tant que c est moins cher que d en
    racheter une ) ; sinon l occasion si elle est payable ; sinon la casse."""
    devis_caisse = x[1]
    remplacer = max(0.6 * ctx.valeur, 0.5 * (ctx.occasion[0] if ctx.occasion is not None else REMPLACEMENT_REF))
    if devis_caisse < 1.0 and ctx.devis <= remplacer: return 0
    if ctx.occasion is not None and ctx.occasion[2]: return 1
    return 3


def _temoin_reparer(x, ctx, rng): return 0


POINT_REPARER = D.PointDeDecision(
    "reparer_vehicule", "transport",
    traits=(("devis_valeur", "le devis du garage sur la valeur venale ( cote de l occasion ), borne a 1"),
            ("devis_caisse", "le devis sur la caisse du menage moins sa semaine de nourriture, borne a 1"),
            ("age", "l age du vehicule sur 30 ans"),
            ("usure", "son compteur sur sa duree de vie"),
            ("revenu", "le revenu lisse du menage sur 300 drachmes par jour"),
            ("autres", "ses autres vehicules en etat de rouler, sur 2"),
            ("besoin", "ses km voulus par jour sur 60"),
            ("mensualites", "ses mensualites en cours sur son revenu mensuel"),
            ("pannes", "ses pannes et accidents des 90 derniers jours, sur 3")),
    actions=("reparer", "occasion", "neuf", "abandonner"),
    observer=_observer, regle=_regle_reparer, temoin=_temoin_reparer,
    note="la meme que l achat, pour CE menage, sur 14 jours : mobilite, a mange, exces d effort, tampon entame",
    horizon_j=HORIZON_REPARER)


# ================================================================== petits outils
def _cols(p, nom): return p.colonnes["menage"][nom]


def _slots(p, n):
    """Les colonnes des trois emplacements, lues pour n menages ( vues : une ecriture y touche la colonne )."""
    c = p.colonnes["menage"]
    return {f: [c[f"vh_{f}{k}"] for k in K3] for f in ("m", "ne", "km", "ks", "js", "res")}


def _lieu_de(p, tr, mg): return tr.k_lieu[mg.domicile.id]


def _km_route(p, tr, a, b):
    if a is b or a.id == b.id: return 0.0
    cle = (a.id, b.id)
    v = tr.km_cache.get(cle)
    if v is None: v = tr.km_cache[cle] = float(p.w.carte.km_route(a, b))
    return v


def _besoin_km(p, tr, mg):
    """Les km voulus par jour : le trajet de chaque actif ( aller-retour ), et le marche tous les deux jours."""
    km = 0.0
    for h in mg.membres:
        if h.vivant and h.travail is not None and h.role != "enfant": km += 2.0 * _km_route(p, tr, mg.domicile, h.travail)
    return km + _km_route(p, tr, mg.domicile, mg.domicile.marche)


def _revenu(p, i):
    c = p.colonnes["menage"]
    return float(c["eco_revenu"][i]) if "eco_revenu" in c else BQ._revenu_menage(p, i)


def _cout_nourriture(p, mg):
    v = sum(1 for x in mg.membres if x.vivant)
    return v * C.NOURRITURE_PAR_JOUR * p.w.marches[mg.domicile.marche.id].prix["nourriture"] * (1.0 + p.w.gouv.tva)


def _tva(p): return ET.taux_tva(p, "pieces_auto")


def _payer_tva_vehicule(p, payeur, ht):
    """La TVA d un vehicule ou d une marge d occasion, au taux de la categorie normale ( celle des pieces )."""
    x = p.socle.livre.transferer(payeur, p.w.gouv, ht * _tva(p), "tva")
    p.w.tva_percue += x
    return x


def _depenser(tr, mg, x):
    """Ce que les vehicules du menage lui coutent au jour le jour ( carburant, entretien ) : l effort de la note. L achat
    d un vehicule et une reparation, depenses d un jour, n y entrent pas : ils pesent par la mensualite et le tampon entame."""
    tr.depense_jour[mg.id] = tr.depense_jour.get(mg.id, 0.0) + x


def _cohorte(p, tr, m, proprio, lieu):
    return p.socle.parc.cohortes.get((tr.mids[m], proprio, lieu))


def _stock_neuf(p, tr, conc, m):
    c = _cohorte(p, tr, m, conc, conc.marche)
    return c.nombre if c is not None else 0


def _usure_slot(km, m): return min(1.0, float(km) / VIE_KM[m])


def _valeur_fiche(p, c, f): return valeur_venale(c, (p.jour - f.ne) / JOURS_AN, f.km / c.vie_km)


# ------------------------------------------------------------------ individus et emplacements
def individu(p, mg_id, k):
    """L individu de l emplacement k du menage : materialise s il est anonyme ( un evenement le touche ). Son usure est
    celle de son compteur ; son proprietaire, le menage ( une identification, pas une cession )."""
    tr = _tr(p); parc = p.socle.parc
    oid = tr.ind.get((mg_id, k))
    if oid is not None: return parc.objets[oid]
    m = int(_cols(p, f"vh_m{k}")[mg_id])
    if m < 0: raise KeyError(f"menage {mg_id} : emplacement {k} vide")
    lieu = tr.lieux[int(_cols(p, "vh_lieu")[mg_id])]
    c = parc.cohortes[(tr.mids[m], tr.flotte, lieu)]
    o = parc.materialiser(c, p.pas)
    o.usure = _usure_slot(_cols(p, f"vh_km{k}")[mg_id], m)
    o.proprietaire = p.w.menages[mg_id]
    tr.ind[(mg_id, k)] = o.id; tr.slot_de[o.id] = (mg_id, k)
    _cols(p, "vh_ind")[mg_id] |= (1 << k)
    return o


def anonymiser(p, o):
    """Un individu d un menage, revenu en service, rentre dans la cohorte de la flotte de son lieu."""
    tr = _tr(p)
    mg_id, k = tr.slot_de.pop(o.id)
    del tr.ind[(mg_id, k)]
    _cols(p, "vh_ind")[mg_id] &= ~(1 << k) & 0x7F
    o.proprietaire = tr.flotte
    p.socle.parc.fondre(o)


def _vider_slot(p, tr, mg_id, k, motif_reservoir="reservoir_sorti"):
    """L emplacement se vide ( le vehicule part : cede, vole, detruit, rebut ) : son carburant sort des reservoirs."""
    res = _cols(p, f"vh_res{k}")
    m = int(_cols(p, f"vh_m{k}")[mg_id])
    litres = float(res[mg_id])
    if litres > 0.0 and m >= 0:
        p.socle.livre.perdre(tr.reservoirs.stock, tr.bid[CARAC[m].carburant], litres / LITRES_UNITE, motif_reservoir)
    res[mg_id] = 0.0
    fiche = Fiche(_cols(p, f"vh_ne{k}")[mg_id], _cols(p, f"vh_km{k}")[mg_id], _cols(p, f"vh_ks{k}")[mg_id],
                  _cols(p, f"vh_js{k}")[mg_id])
    _cols(p, f"vh_m{k}")[mg_id] = -1
    if (mg_id, k) in tr.ind:
        oid = tr.ind.pop((mg_id, k)); tr.slot_de.pop(oid, None)
        _cols(p, "vh_ind")[mg_id] &= ~(1 << k) & 0x7F
    if not any(_cols(p, f"vh_m{j}")[mg_id] >= 0 for j in K3): _cols(p, "vh_lieu")[mg_id] = -1
    return fiche


def _slot_libre(p, mg_id):
    for k in K3:
        if _cols(p, f"vh_m{k}")[mg_id] < 0: return k
    return None


def _poser_dans_menage(p, tr, o, mg, fiche):
    """Un individu cede a un menage prend un emplacement libre ( ses colonnes viennent de sa fiche ), rejoint le lieu du
    menage, puis redevient anonyme s il est en service."""
    k = _slot_libre(p, mg.id)
    if k is None: raise ValueError(f"menage {mg.id} : trois vehicules deja")
    kl = _cols(p, "vh_lieu")
    if kl[mg.id] < 0: kl[mg.id] = _lieu_de(p, tr, mg)
    lieu = tr.lieux[int(kl[mg.id])]
    m = tr.idx_parc[o.modele]
    for nom, v in (("m", m), ("ne", fiche.ne), ("km", fiche.km), ("ks", fiche.ks), ("js", fiche.js), ("res", 0.0)):
        _cols(p, f"vh_{nom}{k}")[mg.id] = v
    if o.lieu != lieu: p.socle.parc.deplacer(o, lieu)
    tr.ind[(mg.id, k)] = o.id; tr.slot_de[o.id] = (mg.id, k)
    _cols(p, "vh_ind")[mg.id] |= (1 << k)
    tr.fiches.pop(o.id, None)
    if o.etat == O.SERVICE: anonymiser(p, o)
    return k


# ------------------------------------------------------------------ sorties
def _sortir(p, tr, o, puits):
    m = tr.idx_parc[o.modele]
    p.socle.parc.sortir(o, puits)
    tr.registre.sorties[puits][m] += 1
    tr.fiches.pop(o.id, None); tr.reparations.pop(o.id, None)
    tr.stats[{"rebut": "rebuts", "detruit": "detruits", "exporte": "exportes"}[puits]] += 1


# ================================================================== le commerce des vehicules
def prix_occasion(p, c, fiche):
    """( prix TTC affiche, marge hors taxes ) d une occasion vendue par une concession : regime de la marge ( TVA sur la
    seule marge, directive 2006/112/CE art. 313 )."""
    v = _valeur_fiche(p, c, fiche)
    marge = v * MARGE_OCCASION
    return v + marge * (1.0 + _tva(p)), marge


def prix_neuf(p, c):
    """( prix TTC, hors taxes, taxe d immatriculation ) au taux de TVA du jour."""
    immat = c.ht * c.taux_immat
    return c.ht * (1.0 + _tva(p)) + immat, c.ht, immat


def _occasions_de(p, tr, conc, categories=None):
    """Les occasions en stock d une concession : [ ( prix TTC, numero, indice de modele ) ], tri par prix."""
    parc = p.socle.parc; out = []
    for oid in conc.occasions:
        o = parc.objets.get(oid)
        if o is None or o.etat != O.SERVICE: continue
        m = tr.idx_parc[o.modele]
        if categories is not None and CARAC[m].nom not in categories: continue
        out.append((prix_occasion(p, CARAC[m], tr.fiches[oid])[0], oid, m))
    out.sort()
    return out


def importer_vehicules(p, acheteur, modele, n, lieu, arrivee=True, client=-1):
    """Un importateur ( concession, domaine 15... ) importe `n` vehicules neufs d un modele : devises, prix FOB, fret, droit
    ( domaine 7, `declarer_import` ). Ils entrent au Parc a leur arrivee ( DELAI_LIVRAISON_J jours ), dans la cohorte de
    l acheteur a `lieu` ; `client` : le menage pour qui la concession l a commande ( vendu a l arrivee ). Rend le nombre
    commande ( ce que la caisse paie )."""
    tr = _tr(p); c = CARAC[IDX[modele] if isinstance(modele, str) else modele]
    n = int(n)
    unit = c.fob * (1.0 + EXT.FRET["produit_fini"]) * (1.0 + ET.DROITS_DOUANE["produit_fini"])
    n = min(n, int(max(0.0, acheteur.caisse) / (unit * (1.0 + 1e-9))))
    if n <= 0: return 0
    paye = EXT.declarer_import(p, acheteur, n * c.fob, "produit_fini", "import_vehicules")
    if paye <= 0.0: return 0
    if isinstance(acheteur, Concession):
        acheteur.commandes[c.idx] += n; acheteur.achats_mois += paye
    if arrivee:
        p.poser(DELAI_LIVRAISON_J * C.PAS_PAR_JOUR, "transport_arrivage", c.idx,
                (0, n, _cle_detenteur(tr, acheteur), lieu, int(client)))
    p.compter("import_neuf", n)
    return n


def _cle_detenteur(tr, x):
    """Une cle simple ( pour une echeance ) : ( famille, rang )."""
    if isinstance(x, Concession): return ("concession", tr.concessions.index(x))
    raise ValueError("seules les concessions recoivent des arrivages differes")


def _detenteur_de_cle(tr, cle):
    fam, k = cle
    return tr.concessions[k]


def _arrivage(p, m, donnees):
    """Des vehicules importes arrivent : neufs ( une cohorte ), ou une occasion ( un individu et sa fiche )."""
    tr = _tr(p); parc = p.socle.parc
    genre, n, cle, lieu = donnees[:4]
    conc = _detenteur_de_cle(tr, cle)
    if genre == 0:
        parc.creer_cohorte(tr.mids[m], conc, lieu, int(n), "importe")
        tr.registre.entrees["import_neuf"][m] += int(n)
        conc.commandes[m] -= int(n)
        client, oid = donnees[4], None
    else:
        age, km, client = donnees[4], donnees[5], donnees[6]
        o = parc.creer(tr.mids[m], conc, lieu, "importe", p.pas, min(1.0, km / VIE_KM[m]))
        ne = p.jour - int(round(age * JOURS_AN))
        tr.fiches[o.id] = Fiche(ne, km, km, p.jour)
        conc.occasions[o.id] = p.jour
        tr.registre.entrees["import_occasion"][m] += 1
        conc.occ_commandes -= 1
        oid = o.id
    if client >= 0: _livrer_client(p, tr, conc, client, genre, m, oid)


def _livrer_client(p, tr, conc, client, genre, m, oid):
    """Le vehicule commande pour un menage arrive : il est vendu s il peut encore le payer ( comptant ou credit ), sinon
    il reste en stock."""
    tr.commandes_clients.pop(client, None)
    mg = p.w.menages[client]
    if not any(x.vivant for x in mg.membres): return
    reprise = None if _slot_libre(p, client) is not None else _slot_a_reprendre(p, tr, client)
    if reprise is not None and (client, reprise) in tr.ind and p.socle.parc.objets[tr.ind[(client, reprise)]].etat != O.SERVICE:
        return
    fait = vendre_occasion(p, conc, mg, oid, reprise) if genre else vendre_neuf(p, conc, mg, m, reprise)
    if fait <= 0.0: p.compter("achat_abandonne")


def importer_occasion(p, conc, m, age, km, client=-1):
    """Une concession importe une occasion ( Allemagne ) : sa valeur grecque decotee, en FOB ; pour un client ( vendue a
    l arrivee ) ou pour son stock. Rend 1 si commandee."""
    tr = _tr(p); c = CARAC[m]
    fob = valeur_venale(c, age, km / c.vie_km) * DECOTE_IMPORT_OCCASION
    if conc.caisse < fob * (1.0 + EXT.FRET["produit_fini"]) * (1.0 + ET.DROITS_DOUANE["produit_fini"]) * (1.0 + 1e-9): return 0
    paye = EXT.declarer_import(p, conc, fob, "produit_fini", "import_vehicules")
    if paye <= 0.0: return 0
    conc.achats_mois += paye
    conc.occ_commandes += 1
    p.poser(DELAI_LIVRAISON_J * C.PAS_PAR_JOUR, "transport_arrivage", m,
            (1, 1, _cle_detenteur(tr, conc), conc.marche, float(age), float(km), int(client)))
    p.compter("import_occasion")
    return 1


def _reprendre(p, tr, conc, mg, k):
    """La concession reprend le vehicule de l emplacement k : payee au menage, sous la valeur venale."""
    o = individu(p, mg.id, k)
    m = tr.idx_parc[o.modele]
    fiche = _vider_slot(p, tr, mg.id, k)
    v = valeur_venale(CARAC[m], (p.jour - fiche.ne) / JOURS_AN, fiche.km / CARAC[m].vie_km) * (1.0 - DECOTE_REPRISE)
    p.socle.parc.ceder(o, conc, "reprise")
    if o.lieu != conc.marche: p.socle.parc.deplacer(o, conc.marche)
    tr.fiches[o.id] = fiche
    if o.etat == O.SERVICE: conc.occasions[o.id] = p.jour
    else: tr.reparations.pop(o.id, None); _sortir(p, tr, o, "rebut"); v = 0.0     # une epave reprise part a la casse
    paye = p.socle.livre.transferer(conc, mg, v, "reprise_vehicule") if v > 0 else 0.0
    tr.stats["reprises"] += 1; p.compter("reprise_vehicule", paye)
    return paye


def _financer(p, tr, mg, reste, duree):
    """Le credit auto du reste a payer ( domaine 2, decision d octroi ). Rend le Pret si tout le reste est finance, sinon
    None ( un pret partiel est rembourse aussitot : l achat est abandonne )."""
    pr = BQ.demander_credit(p, mg, reste, "conso", "credit_auto", duree)
    if pr is None:
        tr.stats["credits_refuses"] += 1; p.compter("credit_auto_refuse"); return None
    if pr.montant < reste - 1e-6:
        BQ.rembourser_par_anticipation(p, pr)
        tr.stats["credits_refuses"] += 1; p.compter("credit_auto_refuse"); return None
    tr.prets_auto.setdefault(mg.id, []).append(pr)
    tr.stats["credits"] += 1; p.compter("credit_auto", pr.montant)
    return pr


def vendre_occasion(p, conc, mg, oid, reprise_k=None, credit=True):
    """Vend l occasion `oid` au menage. Reprise eventuelle de l emplacement `reprise_k`. Paie comptant ce que la caisse
    permet ( en gardant RESERVE_ALIMENTAIRE_J jours de nourriture ), le reste a credit. Rend le prix, ou 0 ( abandon )."""
    tr = _tr(p); parc = p.socle.parc; L = p.socle.livre
    o = parc.objets.get(oid)
    if o is None or oid not in conc.occasions: return 0.0
    m = tr.idx_parc[o.modele]; c = CARAC[m]
    prix, marge = prix_occasion(p, c, tr.fiches[oid])
    if reprise_k is None and _slot_libre(p, mg.id) is None: return 0.0
    reserve = RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, mg)
    valeur_reprise = 0.0
    if reprise_k is not None:
        f = Fiche(_cols(p, f"vh_ne{reprise_k}")[mg.id], _cols(p, f"vh_km{reprise_k}")[mg.id], 0, 0)
        mr = int(_cols(p, f"vh_m{reprise_k}")[mg.id])
        valeur_reprise = _valeur_fiche(p, CARAC[mr], f) * (1.0 - DECOTE_REPRISE)
    comptant = max(0.0, mg.caisse - reserve)
    pr = None
    if comptant + valeur_reprise < prix - 1e-9:
        if not credit: return 0.0
        pr = _financer(p, tr, mg, prix - valeur_reprise - comptant, DUREE_CREDIT_OCC)
        if pr is None: return 0.0
    if reprise_k is not None: _reprendre(p, tr, conc, mg, reprise_k)
    ht = prix - marge * _tva(p)
    L.transferer(mg, conc, ht, "vente_vehicule")
    _payer_tva_vehicule(p, mg, marge)
    del conc.occasions[oid]
    parc.ceder(o, mg, "vente")
    k = _poser_dans_menage(p, tr, o, mg, tr.fiches[oid])
    conc.marge_mois += marge
    _plein_slot(p, tr, mg, k)
    tr.stats["ventes_occasion"] += 1; p.compter("vente_occasion", prix)
    return prix


def vendre_neuf(p, conc, acheteur, m, reprise_k=None, credit=True, octroi=True, duree=DUREE_CREDIT_NEUF, apport_max=None):
    """Vend un vehicule neuf du stock de la concession. Un menage le recoit dans un emplacement ; une entreprise ou l Etat
    dans une Flotte. `octroi` : le credit passe par la decision de la banque ( sinon un pret direct, `preter` : les
    portes ). Rend le prix TTC, ou 0."""
    tr = _tr(p); parc = p.socle.parc; L = p.socle.livre
    c = CARAC[m]
    coh = _cohorte(p, tr, m, conc, conc.marche)
    if coh is None or coh.nombre < 1: return 0.0
    prix, ht, immat = prix_neuf(p, c)
    menage = type(acheteur).__name__ == "Menage"
    if menage and reprise_k is None and _slot_libre(p, acheteur.id) is None: return 0.0
    reserve = RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, acheteur) if menage else 0.0
    valeur_reprise = 0.0
    if menage and reprise_k is not None:
        f = Fiche(_cols(p, f"vh_ne{reprise_k}")[acheteur.id], _cols(p, f"vh_km{reprise_k}")[acheteur.id], 0, 0)
        mr = int(_cols(p, f"vh_m{reprise_k}")[acheteur.id])
        valeur_reprise = _valeur_fiche(p, CARAC[mr], f) * (1.0 - DECOTE_REPRISE)
    comptant = max(0.0, acheteur.caisse - reserve)
    if apport_max is not None: comptant = min(comptant, float(apport_max))    # un acheteur peut financer davantage
    manque = prix - valeur_reprise - comptant
    if manque > 1e-9:
        if not credit or not menage: return 0.0
        if octroi: pr = _financer(p, tr, acheteur, manque, duree)
        else:
            b = BQ.banque_de(p, acheteur)
            pr = BQ.preter(p, b, acheteur, manque, "conso", duree) if b is not None else None
            if pr is not None: tr.prets_auto.setdefault(acheteur.id, []).append(pr)
        if pr is None: return 0.0
    if menage and reprise_k is not None: _reprendre(p, tr, conc, acheteur, reprise_k)
    L.transferer(acheteur, conc, ht, "vente_vehicule")
    _payer_tva_vehicule(p, acheteur, ht)
    if immat > 0: L.transferer(acheteur, p.w.gouv, immat, "taxe_immatriculation")
    if menage:
        o = parc.materialiser(coh, p.pas)
        parc.ceder(o, acheteur, "vente")
        k = _poser_dans_menage(p, tr, o, acheteur, Fiche(p.jour, 0.0, 0.0, p.jour))
        _plein_slot(p, tr, acheteur, k)
    else:
        lieu = acheteur.lieu.id if hasattr(acheteur, "lieu") else conc.marche
        dest = parc.ceder_de_cohorte(coh, 1, acheteur, "vente")
        if lieu != conc.marche: parc.deplacer_de_cohorte(dest, 1, lieu)
        _ajouter_flotte(p, tr, acheteur, lieu, m, p.jour)
    conc.marge_mois += ht - c.cout_rendu
    tr.stats["ventes_neuf"] += 1; p.compter("vente_neuf", prix)
    return prix


def _ajouter_flotte(p, tr, proprio, lieu, m, ne, n=1):
    for f in tr.flottes:
        if f.proprietaire is proprio and f.lieu == lieu and f.modele == m:
            c = _cohorte(p, tr, m, proprio, lieu)
            tot = c.nombre if c is not None else n
            f.ne = (f.ne * (tot - n) + ne * n) / max(1, tot)
            return f
    f = Flotte(proprio, lieu, m, float(ne), len(tr.flottes) * 37 % 365)
    tr.flottes.append(f)
    return f


# ================================================================== la route : la journee des vehicules des menages
def _habitants(p, tr):
    """Une passe par jour sur les habitants : menage de chaque vivant, age, permis ; rend ( vivants par menage, bits de
    permis des adultes par menage, classe du menage )."""
    w = p.w; H = w.habitants; n = len(w.menages)
    mid = np.fromiter((h.menage.id if h.vivant and h.menage is not None else -1 for h in H), np.int64, len(H))
    cl = np.fromiter((EC.CLASSES.get(h.classe, 0) if h.role != "enfant" else -1 for h in H), np.int64, len(H))
    ok = mid >= 0
    nj = p.col("habitant", "naissance_j")[:len(H)]
    adulte = ok & ((p.jour - nj) >= POP.AGE_MAJEUR * JOURS_AN)
    v = np.bincount(mid[ok], minlength=n)[:n]
    bits = np.zeros(n, np.int64)
    pm = p.col("habitant", "vh_permis")[:len(H)].astype(np.int64)
    np.bitwise_or.at(bits, mid[adulte], pm[adulte])
    classe = np.zeros(n, np.int64)
    a = ok & (cl >= 0)
    np.maximum.at(classe, mid[a], cl[a])
    return v, bits, classe


def _facteur_route(p, tr, kl):
    """Le facteur d accident des routes que roulent les vehicules de chaque lieu ( services publics ; 1 sans eux ) : pour
    moitie le trajet vers son marche, pour moitie le reseau de son ile ( moyenne ponderee par les km ) - on ne roule pas
    que vers son marche, et un habitant du bourg du marche roule aussi sur les routes de l ile."""
    f = np.ones(len(tr.lieux))
    if p.a("services_publics"):
        SP = importlib.import_module(".d12_services_publics", __package__)
        cl = p.w.carte.lieux
        km_ile, fk_ile = {}, {}
        for t, de, vers, type_, km, etat, ferme, trafic, fv, fa in SP.troncons(p):
            ile = cl[de].ile
            km_ile[ile] = km_ile.get(ile, 0.0) + km; fk_ile[ile] = fk_ile.get(ile, 0.0) + km * fa
        for k, lid in enumerate(tr.lieux):
            l = cl[lid]
            reseau = fk_ile[l.ile] / km_ile[l.ile] if km_ile.get(l.ile, 0.0) > 0 else 1.0
            trajet = reseau
            if l.marche is not None and l.marche.id != lid:
                try: trajet = SP.facteur_accident(p, lid, l.marche.id)
                except KeyError: pass
            f[k] = 0.5 * trajet + 0.5 * reseau
    tr.facteur_lieu = f
    return f[np.maximum(kl, 0)]


def _km_agenda(p, n):
    """Les km en vehicule du plan du jour de chaque menage ( aller et retour ), ou None sans l agenda."""
    if not p.a("agenda") or p.domaine("agenda").plan is None: return None
    AG = importlib.import_module(".d05_agenda", __package__)
    a = p.domaine("agenda"); pl = a.plan; w = p.w
    km = np.zeros(n)
    hm = np.fromiter((h.menage.id if h.menage is not None else -1 for h in w.habitants), np.int64, len(w.habitants))
    for s in range(AG.NS):
        v = np.nonzero(pl.actif[:, s] & (pl.mode[:, s] == AG.EN_VEHICULE))[0]
        if not len(v): continue
        dom = pl.dom[v].astype(np.int32)
        dest = AG._dest_lieu(a, dom, pl.trav[v].astype(np.int32), pl.dest[v, s].astype(np.int32))
        k = AG._km(a, w, dom, dest)
        ok = np.isfinite(k) & (hm[v] >= 0)
        np.add.at(km, hm[v][ok], 2.0 * k[ok])
    return km


def _immobilises(p, tr, n):
    """Masque ( 3, n ) des emplacements materialises qui ne roulent pas ( panne, immobilise )."""
    out = np.zeros((3, n), bool)
    parc = p.socle.parc
    for (i, k), oid in tr.ind.items():
        o = parc.objets.get(oid)
        if i < n and (o is None or o.etat != O.SERVICE): out[k, i] = True
    return out


def _rouler(p, tr, n, v, bits):
    """Les km du jour de chaque vehicule des menages, le carburant brule, le compteur. Rend les km par emplacement."""
    S = _slots(p, n)
    M = np.stack([a[:n] for a in S["m"]]).astype(np.int64)
    has = M >= 0
    mi = np.where(has, M, 0)
    age = (p.jour - np.stack([a[:n] for a in S["ne"]]).astype(float)) / JOURS_AN
    fj = FACTEUR_SEMAINE[p.socle.calendrier.jour_semaine(p.w.pas)]
    voulu = KM_AN[mi] / JOURS_AN * facteur_age(age) * fj
    ka = _km_agenda(p, n)
    if ka is not None:     # le premier vehicule a quatre roues du menage fait les km du plan
        premier = np.argmax(has & ~(CAT_IDX[mi] == CATEGORIES.index("deux_roues")), axis=0)
        sel = has[premier, np.arange(n)]
        voulu[premier[sel], np.nonzero(sel)[0]] = ka[sel]
    permis_ok = (PERMIS_REQ[mi] & bits[None, :]) != 0
    ok = has & permis_ok & ~_immobilises(p, tr, n) & (v[None, :] > 0)
    res = np.stack([a[:n] for a in S["res"]]).astype(float)
    km = np.where(ok, np.minimum(voulu, res * 100.0 / L100[mi]), 0.0)
    litres = km * L100[mi] / 100.0
    L = p.socle.livre
    for f, nom in enumerate(FUELS):
        tot = float(litres[FUEL_IDX[mi] == f].sum())
        if tot > 0.0:
            x = L.bruler(tr.reservoirs.stock, tr.bid[nom], tot / LITRES_UNITE, "carburant_route")
            tr.stats["litres_brules"] += x * LITRES_UNITE
    for k in K3:
        S["res"][k][:n] = np.maximum(0.0, res[k] - litres[k]).astype(np.float32)
        S["km"][k][:n] = (S["km"][k][:n].astype(float) + km[k]).astype(np.float32)
    tr.stats["km"] += float(km.sum())
    p.compter("km_parcourus", float(km.sum()))
    tr.km_menage = km.sum(axis=0)
    return km, mi, has


def _station_de(tr, mg): return tr.par_marche[mg.domicile.marche.id][1]


def prix_station(p, st, bien):
    """Drachmes HT par unite ( 10 l ) a la pompe : prix de depart + accise + marge de la station."""
    return _prix_depart(p, bien) + ACCISE_L[bien] * LITRES_UNITE + MARGE_STATION_L * LITRES_UNITE


def _prix_depart(p, bien):
    try: return float(ENE.prix_depart(p, bien))
    except (KeyError, AttributeError): return p.socle.catalogue[bien].prix_monde


def vendre_carburant(p, st, acheteur, bien, unites, vers=None):
    """Le plein : `unites` ( 10 l ) de gazole ou d essence vendues par la station `st` a `acheteur`, au prix HT de la
    pompe plus la TVA ; livrees dans `vers` ( un Stock du socle ; None : brulees aussitot, un vehicule d entreprise ).
    Au plus ce que la station a et ce que la caisse paie. Rend les unites vendues."""
    tr = _tr(p); L = p.socle.livre
    ht = prix_station(p, st, bien)
    ttc = ht * (1.0 + ET.taux_tva(p, bien))
    q = min(unites, st.stock[tr.bid[bien]], max(0.0, acheteur.caisse) / ttc * (1.0 - 1e-12))
    if q <= EPS:
        if st.stock[tr.bid[bien]] <= EPS: p.compter("station_a_sec")
        return 0.0
    L.transferer(acheteur, st, q * ht, "carburant_station")
    ET.percevoir_tva(p, acheteur, bien, q * ht)
    if vers is None: L.bruler(st.stock, tr.bid[bien], q, "carburant_route_flottes")
    else: L.deplacer(st.stock, vers, tr.bid[bien], q, "plein_carburant")
    st.ventes_jour[bien] += q
    st.marge_mois += q * MARGE_STATION_L * LITRES_UNITE
    p.compter("plein_carburant", q * LITRES_UNITE)
    return q


def _plein_slot(p, tr, mg, k):
    """Le plein du vehicule de l emplacement k a la station du marche du menage : ce que la caisse permet en gardant sa
    semaine de nourriture, ce que la station a. Rend les litres."""
    col = _cols(p, f"vh_res{k}")
    m = int(_cols(p, f"vh_m{k}")[mg.id])
    if m < 0: return 0.0
    c = CARAC[m]
    litres = c.reservoir_l - float(col[mg.id])
    reserve = RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, mg)
    if litres <= 0.0 or mg.caisse <= reserve: return 0.0
    st = _station_de(tr, mg)
    ttc = prix_station(p, st, c.carburant) * (1.0 + ET.taux_tva(p, c.carburant))
    q = vendre_carburant(p, st, mg, c.carburant, min(litres / LITRES_UNITE, (mg.caisse - reserve) / ttc), tr.reservoirs.stock)
    if q > 0:
        col[mg.id] = np.float32(float(col[mg.id]) + q * LITRES_UNITE)
        _depenser(tr, mg, q * ttc)
    return q * LITRES_UNITE


def _pleins(p, tr, n, mi, has):
    """Les vehicules dont le reservoir est sous 30 % font le plein."""
    S = _slots(p, n); w = p.w
    res = np.stack([a[:n] for a in S["res"]]).astype(float)
    bas = has & (res < SEUIL_PLEIN * TANK[mi])
    for k, i in zip(*np.nonzero(bas)): _plein_slot(p, tr, w.menages[int(i)], int(k))


# ================================================================== evenements des vehicules des menages
def _victimes(p, tr, mg, k_places, tues, iss, lieu, conducteur_bit):
    """Les victimes d un accident d un vehicule de menage : le conducteur ( un adulte qui a le permis ), des membres a
    bord, un tiers du lieu. Morts par `deceder`, blesses par `blesser` ( medecine )."""
    w = p.w; rng = p.hasard("transport_victimes")
    col = p.col("habitant", "vh_permis")
    adultes = [h for h in mg.membres if h.vivant and h.poste not in ("hopital", "voyage")
               and POP.age_de(p, h) >= POP.AGE_MAJEUR and int(col[h.id]) & conducteur_bit]
    gens = []
    if adultes: gens.append(adultes[int(rng.integers(0, len(adultes)))])
    for h in mg.membres:
        if len(gens) >= k_places: break
        if h.vivant and h not in gens and h.poste not in ("hopital", "voyage") and rng.random() < PASSAGER: gens.append(h)
    return _frapper(p, tr, gens, tues, iss, lieu, rng)


def _frapper(p, tr, gens, tues, iss, lieu, rng):
    """Complete les victimes par des tiers du lieu ( pietons, autres vehicules ), puis tue et blesse."""
    w = p.w
    besoin = tues + len(iss)
    if len(gens) < besoin:
        tiers = [h for h in w.habitants if h.vivant and h.lieu is not None and h.lieu.id == lieu and h not in gens
                 and h.poste not in ("hopital", "voyage")] if besoin - len(gens) > 0 else []
        while len(gens) < besoin and tiers:
            gens.append(tiers.pop(int(rng.integers(0, len(tiers)))))
    med = p.a("medecine")
    MED = importlib.import_module(".d16_medecine", __package__) if med else None
    n_t = n_b = 0
    for j, h in enumerate(gens[:besoin]):
        if j < tues:
            POP.deceder(p, h, "accident"); n_t += 1; p.compter("tue_route")
        else:
            g = iss[j - tues]
            if med: MED.blesser(p, h, "route", g, "accident", lieu)
            else: p.compter("blessure_sans_medecine")
            n_b += 1; p.compter("blessure_route")
    tr.stats["tues_sur_le_coup"] += n_t; tr.stats["blesses"] += n_b; tr.stats["victimes"] += n_t + n_b
    return n_t, n_b


def _nouveau_sinistre(p, tr, type_, o, m, proprio, lieu, dommage, victimes, tues):
    s = Sinistre(len(tr.sinistres), p.jour, type_, o.id if o is not None else -1, m, proprio, lieu,
                 p.hasard("transport_victimes").random() < RESPONSABLE, dommage, victimes, tues)
    tr.sinistres.append(s)
    return s


def _devis(rng, loi, cat):
    (mp, sp), (mh, sh) = loi
    e = ECHELLE_DEVIS[cat]
    return float(mp * e * math.exp(sp * rng.normal())), float(mh * e * math.exp(sh * rng.normal()))


def cout_devis(p, garage, pieces_kg, heures):
    """Drachmes HT d un devis : pieces au prix de vente du garage, heures au taux horaire."""
    return pieces_kg * _prix_piece_kg(p) + heures * TAUX_HORAIRE_GARAGE


def _prix_piece_kg(p):
    cat = p.socle.catalogue["pieces_auto"]
    return cat.prix_monde * (1.0 + EXT.FRET["piece"]) * (1.0 + ET.DROITS_DOUANE["piece"]) * MARKUP_PIECES


def _panne(p, tr, o, garage, loi, sinistre=None):
    """Un vehicule tombe en panne ( ou est accidente ) : immobilise, devis du garage de son marche."""
    rng = p.hasard("transport_devis")
    m = tr.idx_parc[o.modele]
    pk, h = _devis(rng, loi, CARAC[m].categorie)
    p.socle.parc.mettre_en_etat(o, O.PANNE)
    tr.reparations[o.id] = Reparation(o.id, garage, pk, h, sinistre)
    return tr.reparations[o.id]


def _noter_panne(tr, mg_id, jour):
    l = tr.pannes_j.setdefault(mg_id, [])
    l.append(jour)
    while l and jour - l[0] > 90: l.pop(0)


def _evenements(p, tr, n, km, mi, has):
    """Pannes, accidents, vols et fins de vie du jour des vehicules des menages ( tirages vectorises )."""
    w = p.w; S = _slots(p, n); sc = tr.scenario
    kmv = km.reshape(-1); miv = mi.reshape(-1); hasv = has.reshape(-1)
    ne = np.stack([a[:n] for a in S["ne"]]).astype(float).reshape(-1)
    odo = np.stack([a[:n] for a in S["km"]]).astype(float).reshape(-1)
    ks = np.stack([a[:n] for a in S["ks"]]).astype(float).reshape(-1)
    js = np.stack([a[:n] for a in S["js"]]).astype(float).reshape(-1)
    u = np.minimum(1.0, odo / VIE_KM[miv])
    age = (p.jour - ne) / JOURS_AN
    retard = ((odo - ks) > 1.5 * INTERVALLE[miv]) | ((p.jour - js) > 1.5 * JOURS_ENTRETIEN)
    ind = np.stack([(p.col("menage", "vh_ind")[:n] >> k) & 1 for k in K3]).reshape(-1).astype(bool)
    kl = p.col("menage", "vh_lieu")[:n].astype(np.int64)
    klv = np.tile(kl, 3)
    fr = _facteur_route(p, tr, klv)
    # --- pannes ( vehicules qui ont roule, anonymes )
    lam = PANNE_AN[miv] / JOURS_AN * (1.0 + USURE_PANNE * u * u) * np.where(retard, RETARD_ENTRETIEN, 1.0) * sc["pannes"]
    rp = p.du_jour("transport_pannes").random(len(kmv))
    pan = np.nonzero(hasv & (kmv > 0) & ~ind & (rp < lam))[0]
    # --- accidents
    rng = p.du_jour("transport_accidents")
    idx, corp, vict, tues, iss = tirer_accidents(rng, np.where(hasv & (kmv > 0), kmv, 0.0) * sc["accidents"], miv,
                                                 fr * sc["corporels"])
    tr.stats["vkm_corporel"] += float((kmv * RISQUE_C[CAT_IDX[miv]] * fr).sum())
    # --- vols ( vehicules anonymes, gares ou en route )
    rv = p.du_jour("transport_vols").random(len(kmv))
    vol = np.nonzero(hasv & ~ind & (rv < VOL_C[CAT_IDX[miv]] / JOURS_AN * sc["vols"]))[0]
    # --- fin de vie
    rr = p.du_jour("transport_rebut").random(len(kmv))
    reb = np.nonzero(hasv & ~ind & (rr < rebut_an(CAT_IDX[miv], age, u) / JOURS_AN * sc["rebut"]))[0]
    touches = set()
    for j in reb.tolist():
        i, k = j % n, j // n
        if (i, k) in touches or _cols(p, f"vh_m{k}")[i] < 0: continue
        touches.add((i, k))
        _rebut_slot(p, tr, i, k)
    for j in vol.tolist():
        i, k = j % n, j // n
        if (i, k) in touches or _cols(p, f"vh_m{k}")[i] < 0: continue
        touches.add((i, k))
        voler(p, w.menages[i], k)
    for j, c_, nv, t, gs in zip(idx.tolist(), corp.tolist(), vict.tolist(), tues, iss):
        i, k = j % n, j // n
        if (i, k) in touches or _cols(p, f"vh_m{k}")[i] < 0: continue
        touches.add((i, k))
        _accident_menage(p, tr, w.menages[i], k, c_, t, gs)
    for j in pan.tolist():
        i, k = j % n, j // n
        if (i, k) in touches or _cols(p, f"vh_m{k}")[i] < 0: continue
        touches.add((i, k))
        mg = w.menages[i]
        o = individu(p, i, k)
        _panne(p, tr, o, tr.par_marche[mg.domicile.marche.id][2], DEVIS_PANNE)
        tr.stats["pannes"] += 1; p.compter("panne_vehicule")
        _noter_panne(tr, i, p.jour)
        _decider_reparation(p, tr, o)


def _rebut_slot(p, tr, i, k):
    """Un vehicule anonyme en fin de vie part a la casse : il sort de la cohorte de son lieu."""
    m = int(_cols(p, f"vh_m{k}")[i])
    lieu = tr.lieux[int(_cols(p, "vh_lieu")[i])]
    c = p.socle.parc.cohortes[(tr.mids[m], tr.flotte, lieu)]
    _vider_slot(p, tr, i, k)
    p.socle.parc.sortir_de_cohorte(c, 1, "rebut")
    tr.registre.sorties["rebut"][m] += 1
    tr.stats["rebuts"] += 1; p.compter("vehicule_rebut")


def _accident_menage(p, tr, mg, k, corporel, tues, iss):
    rng = p.hasard("transport_devis")
    m = int(_cols(p, f"vh_m{k}")[mg.id]); c = CARAC[m]
    lieu = mg.domicile.id
    o = individu(p, mg.id, k)
    _noter_panne(tr, mg.id, p.jour)
    garage = tr.par_marche[mg.domicile.marche.id][2]
    if corporel:
        tr.stats["accidents_corporels"] += 1
        n_t, n_b = _victimes(p, tr, mg, c.places, tues, iss, lieu, PERMIS_REQ[m])
        detruit = rng.random() < DETRUIT_C[CAT_IDX[m]]
        valeur = valeur_venale(c, (p.jour - int(_cols(p, f"vh_ne{k}")[mg.id])) / JOURS_AN, o.usure)
        s = _nouveau_sinistre(p, tr, "corporel", o, m, mg, lieu, valeur if detruit else 0.0, n_t + n_b, n_t)
        p.noter("accident_de_la_route", lieu=lieu, modele=c.nom, victimes=n_t + n_b, tues=n_t)
        if detruit:
            _vider_slot(p, tr, mg.id, k)
            _sortir(p, tr, o, "detruit")
            p.noter("vehicule_detruit", modele=c.nom, proprietaire=mg.id, cause="accident")
            return
        r = _panne(p, tr, o, garage, DEVIS_CORPOREL, s.id)
    else:
        tr.stats["accidents_materiels"] += 1; p.compter("sinistre_materiel")
        r = _panne(p, tr, o, garage, DEVIS_MATERIEL)
        s = _nouveau_sinistre(p, tr, "materiel", o, m, mg, lieu, 0.0, 0, 0)
        r.sinistre = s.id
    s.dommage = cout_devis(p, garage, r.pieces_kg, r.heures)
    _decider_reparation(p, tr, o)


def voler(p, mg, k):
    """Le vehicule de l emplacement k est vole : il passe au receleur ( cession « vol » ), l enquete dure ENQUETE_J jours."""
    tr = _tr(p); parc = p.socle.parc
    o = individu(p, mg.id, k)
    m = tr.idx_parc[o.modele]
    fiche = _vider_slot(p, tr, mg.id, k)
    valeur = valeur_venale(CARAC[m], (p.jour - fiche.ne) / JOURS_AN, o.usure)
    parc.ceder(o, tr.receleur, "vol")
    tr.fiches[o.id] = fiche
    v = Vol(len(tr.vols), p.jour, o.id, m, mg, mg.domicile.id, valeur)
    tr.vols.append(v)
    tr.sinistres.append(Sinistre(len(tr.sinistres), p.jour, "vol", o.id, m, mg, mg.domicile.id, False, valeur, 0, 0))
    p.poser(ENQUETE_J * C.PAS_PAR_JOUR, "transport_issue_vol", v.id)
    tr.stats["vols"] += 1
    p.noter("vol_de_vehicule", modele=CARAC[m].nom, proprietaire=mg.id, lieu=mg.domicile.id)
    return v


def _issue_vol(p, vid, donnees):
    tr = _tr(p); parc = p.socle.parc
    v = tr.vols[vid]
    if v.issue is not None: return
    o = parc.objets.get(v.objet)
    if o is None or o.proprietaire is not tr.receleur: v.issue = "hors_receleur"; return
    rng = p.hasard("transport_vols_issue")
    if rng.random() < RETROUVE: _restituer(p, tr, v, o)
    elif rng.random() < EXPORT_VOLE: v.issue = "exporte"; _sortir(p, tr, o, "exporte")
    else: v.issue = "depece"; _sortir(p, tr, o, "rebut")


def _restituer(p, tr, v, o):
    """Un vehicule vole retrouve revient a son proprietaire : un menage ( un emplacement libre, sinon il est vendu a la
    concession de son marche pour lui ), une entreprise ou l Etat ( sa flotte )."""
    v.issue = "retrouve"
    tr.stats["retrouves"] += 1
    p.noter("vehicule_retrouve", modele=CARAC[v.modele].nom, proprietaire=str(getattr(v.victime, "id", "etat")))
    if type(v.victime).__name__ == "Menage":
        rendre(p, o, v.victime, "restitution"); return
    parc = p.socle.parc
    parc.ceder(o, v.victime, "restitution"); tr.fiches.pop(o.id, None)
    if o.lieu != v.lieu: parc.deplacer(o, v.lieu)
    parc.fondre(o)


def rendre(p, o, mg, motif):
    """Rend un individu hors menage ( vole retrouve, requisition levee ) a un menage."""
    tr = _tr(p); parc = p.socle.parc
    dis = p.col("menage", "dissous")[mg.id] if "dissous" in p.colonnes["menage"] else 0
    if not dis and _slot_libre(p, mg.id) is not None and any(x.vivant for x in mg.membres):
        parc.ceder(o, mg, motif)
        _poser_dans_menage(p, tr, o, mg, tr.fiches[o.id])
        return True
    conc = tr.par_marche[mg.domicile.marche.id][0]
    m = tr.idx_parc[o.modele]
    val = _valeur_fiche(p, CARAC[m], tr.fiches[o.id]) * (1.0 - DECOTE_REPRISE)
    parc.ceder(o, conc, motif)
    if o.lieu != conc.marche: parc.deplacer(o, conc.marche)
    conc.occasions[o.id] = p.jour
    p.socle.livre.transferer(conc, mg if not dis else p.w.gouv, val, "reprise_vehicule")
    return False


# ================================================================== reparer ou remplacer
def _mensualites_auto(tr, mg_id):
    ps = tr.prets_auto.get(mg_id)
    if not ps: return 0.0
    vivants = [pr for pr in ps if pr.principal > 1e-6 and pr.defaut_j < 0]
    tr.prets_auto[mg_id] = vivants
    return math.fsum(pr.mensualite for pr in vivants)


def _utilisables(p, tr, mg_id, sauf=None):
    n = 0
    for k in K3:
        if _cols(p, f"vh_m{k}")[mg_id] < 0 or k == sauf: continue
        oid = tr.ind.get((mg_id, k))
        if oid is None or p.socle.parc.objets[oid].etat == O.SERVICE: n += 1
    return n


def _categories_voulues(p, mg, classe, bits):
    """Ce qui convient au menage : un pick-up s il a un paysan, sinon selon sa classe ; un deux-roues sans permis B."""
    if not bits & 1: return ("scooter", "moto") if bits & (2 | 4) else ()
    if any(h.vivant and h.role == "paysan" for h in mg.membres): return ("pick_up", "citadine", "berline")
    return (("citadine", "berline"), ("citadine", "berline", "suv"), ("berline", "suv", "citadine"))[int(classe)]


def _offres(p, tr, mg, classe, bits, reserve):
    """( occasion, neuf ) proposees au menage par SA concession : ( prix, numero ou modele, payable, mensualite tient )."""
    conc = tr.par_marche[mg.domicile.marche.id][0]
    cats = _categories_voulues(p, mg, classe, bits)
    if not cats: return conc, None, None
    occ = _occasions_de(p, tr, conc, cats)
    if occ:
        prix, oid, m = occ[0]
    else:                                   # rien en stock : une occasion de 10 ans, commandee pour lui
        m = IDX[cats[0]]; oid = None
        prix = prix_occasion(p, CARAC[m], Fiche(p.jour - int(AGE_COMMANDE * JOURS_AN), _km_commande(m), 0, 0))[0]
    o = (prix, oid, mg.caisse - prix >= reserve, m)
    rev = _revenu(p, mg.id)
    en_stock = [IDX[nom] for nom in cats if _stock_neuf(p, tr, conc, IDX[nom]) >= 1]
    m = en_stock[0] if en_stock else IDX[cats[0]]
    prix = prix_neuf(p, CARAC[m])[0]
    apport = max(APPORT_MIN * prix, 0.0)
    mens = BQ.mensualite(max(0.0, prix - max(0.0, mg.caisse - reserve)), BQ.taux_credit(p, "conso"), DUREE_CREDIT_NEUF)
    tient = mg.caisse - reserve >= apport and mens <= EFFORT_MAX_AUTO * 30.0 * rev
    neuf = (prix, m, mg.caisse >= prix + reserve, tient, bool(en_stock))
    return conc, o, neuf


def _km_commande(m): return CARAC[m].km_an * AGE_COMMANDE * float(facteur_age(AGE_COMMANDE / 2.0))


def _traits_menage(p, tr, mg):
    rev = _revenu(p, mg.id)
    n_veh = sum(1 for k in K3 if _cols(p, f"vh_m{k}")[mg.id] >= 0)
    vieux, usure = 0.0, 0.0
    for k in K3:
        m = int(_cols(p, f"vh_m{k}")[mg.id])
        if m < 0: continue
        a = (p.jour - int(_cols(p, f"vh_ne{k}")[mg.id])) / JOURS_AN
        if a >= vieux: vieux, usure = a, _usure_slot(_cols(p, f"vh_km{k}")[mg.id], m)
    return rev, n_veh, vieux, usure


def _reparation_contexte(p, tr, o, mg, classe, bits):
    r = tr.reparations[o.id]
    mg_id, k = tr.slot_de[o.id]
    m = tr.idx_parc[o.modele]; c = CARAC[m]
    devis = cout_devis(p, r.garage, r.pieces_kg, r.heures) * (1.0 + _tva(p))
    age = (p.jour - int(_cols(p, f"vh_ne{k}")[mg_id])) / JOURS_AN
    val = valeur_venale(c, age, o.usure)
    reserve = RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, mg)
    conc, occ, neuf = _offres(p, tr, mg, classe, bits, RESERVE_ACHAT_J * _cout_nourriture(p, mg))
    rev = _revenu(p, mg.id)
    x = (min(1.0, devis / max(1.0, val)), min(1.0, devis / max(1.0, mg.caisse - reserve)), min(1.0, age / 30.0),
         min(1.0, o.usure), min(1.0, rev / 300.0), min(2, _utilisables(p, tr, mg_id, sauf=k)) / 2.0,
         min(1.0, _besoin_km(p, tr, mg) / 60.0), min(1.0, _mensualites_auto(tr, mg_id) / max(1.0, 30.0 * rev)),
         min(3, len(tr.pannes_j.get(mg_id, ()))) / 3.0)
    return ContexteReparation(x, mg, o, devis, val, occ, neuf)


def _decider_reparation(p, tr, o):
    """Le menage decide du sort d un vehicule en panne ou accidente."""
    if o.id not in tr.slot_de or o.id not in tr.reparations: return
    mg_id, k = tr.slot_de[o.id]
    mg = p.w.menages[mg_id]
    classe, bits = _classe_bits(p, mg)
    ctx = _reparation_contexte(p, tr, o, mg, classe, bits)
    a = tr.dec_reparer.decider(mg_id, ctx)
    r = tr.reparations[o.id]
    if a == 0:
        if not reparer(p, o, mg):
            r.refus += 1
            if r.refus >= REFUS_MAX: _abandonner(p, tr, o, mg_id, k)
            else: p.poser(REDECIDER_J * C.PAS_PAR_JOUR, "transport_redecider", o.id)
    elif a in (1, 2):
        _abandonner(p, tr, o, mg_id, k)
        _acheter(p, tr, mg, a, classe, bits)
    else:
        _abandonner(p, tr, o, mg_id, k)


def _classe_bits(p, mg):
    cl = 0; bits = 0
    col = p.col("habitant", "vh_permis")
    for h in mg.membres:
        if not h.vivant: continue
        if h.role != "enfant": cl = max(cl, EC.CLASSES.get(h.classe, 0))
        if POP.age_de(p, h) >= POP.AGE_MAJEUR: bits |= int(col[h.id])
    return cl, bits


def _abandonner(p, tr, o, mg_id, k):
    """Le vehicule en panne part a la casse."""
    _vider_slot(p, tr, mg_id, k)
    _sortir(p, tr, o, "rebut")
    tr.stats["abandons"] += 1
    p.compter("vehicule_rebut")


def reparer(p, o, payeur):
    """Le garage repare : le payeur ( menage, entreprise ) paie pieces et heures TTC, moins ce que l assurance couvre ;
    les pieces sont consommees ( industrie d abord, puis pieces importees ; pneus a part ) ; le vehicule revient en
    service apres le travail. Rend vrai si la reparation est lancee."""
    tr = _tr(p); L = p.socle.livre
    r = tr.reparations.get(o.id)
    if r is None or r.en_cours: return False
    g = r.garage
    ht = cout_devis(p, g, r.pieces_kg, r.heures)
    ttc = ht * (1.0 + _tva(p))
    couvert = 0.0
    if tr.assureur is not None and r.sinistre is not None:
        couvert = max(0.0, min(ttc, float(tr.assureur(p, tr.sinistres[r.sinistre], ttc))))
        tr.sinistres[r.sinistre].couvert = couvert
    du = ttc - couvert
    reserve = RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, payeur) if type(payeur).__name__ == "Menage" else 0.0
    if payeur.caisse - reserve < du - 1e-9: return False
    if not _consommer_pieces(p, tr, g, r.pieces_kg, 0.0, "reparation_vehicule"):
        p.compter("penurie_pieces"); return False
    part = du / ttc if ttc > 0 else 0.0
    L.transferer(payeur, g, ht * part, "reparation_vehicule")
    if part > 0: ET.percevoir_tva(p, payeur, "pieces_auto", ht * part)
    g.marge_mois += (ht - r.pieces_kg * _prix_piece_kg(p) / MARKUP_PIECES) * part
    r.en_cours = True
    jours = max(1, math.ceil(r.heures / HEURES_JOUR_GARAGE))
    p.poser(jours * C.PAS_PAR_JOUR, "transport_fin_reparation", o.id)
    tr.stats["reparations"] += 1; p.compter("reparation_vehicule", du)
    return True


def _fin_reparation(p, oid, donnees):
    tr = _tr(p); parc = p.socle.parc
    o = parc.objets.get(oid)
    r = tr.reparations.pop(oid, None)
    if o is None or r is None: return
    parc.mettre_en_etat(o, O.SERVICE)
    if oid in tr.slot_de: anonymiser(p, o)
    elif oid in tr.fiches: pass
    else: _rentrer_flotte(p, tr, o)


def _redecider(p, oid, donnees):
    tr = _tr(p)
    o = p.socle.parc.objets.get(oid)
    if o is None or oid not in tr.reparations or tr.reparations[oid].en_cours: return
    _decider_reparation(p, tr, o)


def _consommer_pieces(p, tr, g, kg, pneus, motif):
    """Les pieces d un entretien ou d une reparation : d abord l acier usine de l industrie ( au plus
    PART_PIECES_INDUSTRIE ), puis les pieces importees ; et les pneus. Faux si le garage n a pas de quoi."""
    L = p.socle.livre
    ind = min(kg * PART_PIECES_INDUSTRIE, g.stock[tr.bid["pieces"]] * 1000.0)
    auto = kg - ind
    if g.stock[tr.bid["pieces_auto"]] < auto - 1e-9 or g.stock[tr.bid["pneus"]] < pneus - 1e-9: return False
    if ind > 0: L.consommer(g.stock, tr.bid["pieces"], ind / 1000.0, motif); g.conso_jour["pieces"] += ind / 1000.0
    if auto > 0: L.consommer(g.stock, tr.bid["pieces_auto"], auto, motif); g.conso_jour["pieces_auto"] += auto
    if pneus > 0: L.consommer(g.stock, tr.bid["pneus"], pneus, motif); g.conso_jour["pneus"] += pneus
    return True


def _entretiens(p, tr, n, mi, has):
    """Les vehicules dont l entretien est du ( intervalle en km, ou un an ) passent au garage de leur marche, si le menage
    peut payer en gardant sa semaine de nourriture ; sinon l entretien attend ( et les pannes doublent )."""
    S = _slots(p, n); w = p.w; L = p.socle.livre
    odo = np.stack([a[:n] for a in S["km"]]).astype(float)
    ks = np.stack([a[:n] for a in S["ks"]]).astype(float)
    js = np.stack([a[:n] for a in S["js"]]).astype(np.int64)
    du = has & (((odo - ks) >= INTERVALLE[mi]) | ((p.jour - js) >= JOURS_ENTRETIEN))
    for k, i in zip(*np.nonzero(du)):
        k, i = int(k), int(i)
        mg = w.menages[i]
        m = int(mi[k, i]); c = CARAC[m]
        g = tr.par_marche[mg.domicile.marche.id][2]
        pneus = c.pneus * max(0.0, float(odo[k, i] - ks[k, i])) / c.km_pneus
        ht = c.pieces_kg * _prix_piece_kg(p) + pneus * _prix_pneu(p) + c.heures * TAUX_HORAIRE_GARAGE
        ttc = ht * (1.0 + _tva(p))
        if mg.caisse - RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, mg) < ttc: continue
        if not _consommer_pieces(p, tr, g, c.pieces_kg, pneus, "entretien_vehicule"):
            p.compter("penurie_pieces"); continue
        L.transferer(mg, g, ht, "entretien_vehicule")
        ET.percevoir_tva(p, mg, "pieces_auto", ht)
        g.marge_mois += c.heures * TAUX_HORAIRE_GARAGE + (ht - c.heures * TAUX_HORAIRE_GARAGE) * (1.0 - 1.0 / MARKUP_PIECES)
        _depenser(tr, mg, ttc)
        S["ks"][k][i] = odo[k, i]; S["js"][k][i] = p.jour
        tr.stats["entretiens"] += 1; p.compter("entretien_vehicule", ttc)


def _prix_pneu(p):
    return p.socle.catalogue["pneus"].prix_monde * (1.0 + EXT.FRET["piece"]) * (1.0 + ET.DROITS_DOUANE["piece"]) * MARKUP_PIECES


# ================================================================== les flottes des entreprises et de l Etat
def _flottes(p, tr):
    """Les vehicules des entreprises et de l Etat : km moyens, carburant achete et brule a la station du marche,
    entretien au fil des jours, usure de la cohorte, pannes, accidents, vols, rebuts ( tires a la cohorte ). Camions et
    autocars usent les routes ( services publics : `passer` )."""
    parc = p.socle.parc; L = p.socle.livre; w = p.w
    rng = p.du_jour("transport_flottes")
    SP = importlib.import_module(".d12_services_publics", __package__) if p.a("services_publics") else None
    fj = FACTEUR_SEMAINE[p.socle.calendrier.jour_semaine(w.pas)]
    for f in list(tr.flottes):
        if not f.gere: continue
        c = CARAC[f.modele]
        coh = _cohorte(p, tr, f.modele, f.proprietaire, f.lieu)
        if coh is None or coh.nombre == 0: continue
        n = coh.nombre
        age = (p.jour - f.ne) / JOURS_AN
        km = n * c.km_an / JOURS_AN * float(facteur_age(age)) * fj
        lieu = w.carte.lieux[f.lieu]
        st = tr.par_marche[(lieu.marche or lieu).id][1]; g = tr.par_marche[(lieu.marche or lieu).id][2]
        voulu = km * c.l100 / 100.0 / LITRES_UNITE
        q = vendre_carburant(p, st, f.proprietaire, c.carburant, voulu, None) if voulu > 0 else 0.0
        km = km * (q / voulu if voulu > 0 else 0.0)
        tr.stats["km"] += km
        coh.usure = min(1.0, coh.usure + km / n / c.vie_km)
        if SP is not None and c.categorie in ("poids_lourd", "autocar") and km > 0 and lieu.marche is not None \
                and lieu.marche.id != lieu.id:
            try: SP.passer(p, lieu.id, lieu.marche.id, km / max(1.0, 2.0 * _km_route(p, tr, lieu, lieu.marche)))
            except KeyError: pass
        # l entretien, au fil des km
        pieces = c.pieces_kg * km / c.intervalle_km
        pneus = c.pneus * km / c.km_pneus
        ht = pieces * _prix_piece_kg(p) + pneus * _prix_pneu(p) + c.heures * km / c.intervalle_km * TAUX_HORAIRE_GARAGE
        if ht > 0 and f.proprietaire.caisse >= ht * (1.0 + _tva(p)) and _consommer_pieces(p, tr, g, pieces, pneus, "entretien_vehicule"):
            L.transferer(f.proprietaire, g, ht, "entretien_vehicule")
            ET.percevoir_tva(p, f.proprietaire, "pieces_auto", ht)
            g.marge_mois += ht * (1.0 - 1.0 / MARKUP_PIECES)
        # evenements a la cohorte
        u = coh.usure
        k_p = int(rng.poisson(n * c.pannes_an / JOURS_AN * (1.0 + USURE_PANNE * u * u) * tr.scenario["pannes"]))
        k_v = int(rng.poisson(n * VOL_AN[c.categorie] / JOURS_AN * tr.scenario["vols"]))
        k_r = int(rng.binomial(n, float(rebut_an(CAT_IDX[f.modele], age, u)) / JOURS_AN * min(1.0, tr.scenario["rebut"])))
        per_veh = np.full(n, km / n) * tr.scenario["accidents"]
        fr = tr.facteur_lieu[tr.k_lieu[f.lieu]] if tr.facteur_lieu is not None else 1.0
        idx, corp, vict, tues, iss = tirer_accidents(rng, per_veh, np.full(n, f.modele), np.full(n, fr * tr.scenario["corporels"]))
        if k_r:
            x = parc.sortir_de_cohorte(coh, min(k_r, coh.nombre), "rebut")
            tr.registre.sorties["rebut"][f.modele] += x; tr.stats["rebuts"] += x
        for _ in range(k_v):
            coh = _cohorte(p, tr, f.modele, f.proprietaire, f.lieu)
            if coh is None or coh.nombre == 0: break
            o = parc.materialiser(coh, p.pas)
            parc.ceder(o, tr.receleur, "vol")
            tr.fiches[o.id] = Fiche(int(f.ne), o.usure * c.vie_km, o.usure * c.vie_km, p.jour)
            v = Vol(len(tr.vols), p.jour, o.id, f.modele, f.proprietaire, f.lieu, valeur_venale(c, age, o.usure))
            tr.vols.append(v); tr.stats["vols"] += 1
            p.poser(ENQUETE_J * C.PAS_PAR_JOUR, "transport_issue_vol", v.id)
        for c_, t, gs in zip(corp.tolist(), tues, iss):
            coh = _cohorte(p, tr, f.modele, f.proprietaire, f.lieu)
            if coh is None or coh.nombre == 0: break
            o = parc.materialiser(coh, p.pas)
            if c_:
                tr.stats["accidents_corporels"] += 1
                gens = [h for h in w.au_travail_de(lieu, getattr(f.proprietaire, "role", "")) if h.vivant][:1]
                n_t, n_b = _frapper(p, tr, gens, t, gs, f.lieu, p.hasard("transport_victimes"))
                p.noter("accident_de_la_route", lieu=f.lieu, modele=c.nom, victimes=n_t + n_b, tues=n_t)
                if rng.random() < DETRUIT_C[CAT_IDX[f.modele]]:
                    _sortir(p, tr, o, "detruit"); continue
                loi = DEVIS_CORPOREL
            else:
                tr.stats["accidents_materiels"] += 1; loi = DEVIS_MATERIEL
            _panne(p, tr, o, g, loi)
            _reparer_flotte(p, tr, o, f.proprietaire)
        for _ in range(k_p):
            coh = _cohorte(p, tr, f.modele, f.proprietaire, f.lieu)
            if coh is None or coh.nombre == 0: break
            o = parc.materialiser(coh, p.pas)
            _panne(p, tr, o, g, DEVIS_PANNE)
            tr.stats["pannes"] += 1
            _reparer_flotte(p, tr, o, f.proprietaire)
    for oid, r in list(tr.reparations.items()):        # les vehicules de flotte qui attendaient des pieces
        if not r.en_cours and oid not in tr.slot_de and oid not in tr.fiches:
            o = parc.objets.get(oid)
            if o is not None: _reparer_flotte(p, tr, o, o.proprietaire)


def _reparer_flotte(p, tr, o, proprio):
    """Une entreprise fait toujours reparer ( son vehicule est un outil ) ; ce que sa caisse ne paie pas devient une
    creance du garage ( credit fournisseur ). Sans pieces, le vehicule attend au garage."""
    r = tr.reparations[o.id]
    g = r.garage; L = p.socle.livre
    if not _consommer_pieces(p, tr, g, r.pieces_kg, 0.0, "reparation_vehicule"):
        p.compter("penurie_pieces"); return False
    ht = cout_devis(p, g, r.pieces_kg, r.heures)
    L.payer_ou_devoir(proprio, g, ht, "reparation_vehicule", p.socle.creances, p.jour)
    x = L.transferer(proprio, p.w.gouv, ht * _tva(p), "tva"); p.w.tva_percue += x
    if ht * _tva(p) - x > 1e-6: tr.impayes.append(p.socle.creances.constater(p.w.gouv, proprio, ht * _tva(p) - x, "tva", p.jour))
    g.marge_mois += ht - r.pieces_kg * _prix_piece_kg(p) / MARKUP_PIECES
    r.en_cours = True
    p.poser(max(1, math.ceil(r.heures / HEURES_JOUR_GARAGE)) * C.PAS_PAR_JOUR, "transport_fin_reparation", o.id)
    tr.stats["reparations"] += 1; p.compter("reparation_vehicule", ht)
    return True


def _rentrer_flotte(p, tr, o):
    """Un vehicule de flotte repare rejoint sa cohorte."""
    p.socle.parc.fondre(o)


# ================================================================== les detenteurs au quotidien
def _matin(p):
    """6 h 20 : la medecine laisse la route a ce domaine ; les stations, garages et concessions se reapprovisionnent."""
    tr = _tr(p)
    if p.a("medecine"):
        med = p.domaine("medecine")
        if "route" not in med.reprises: importlib.import_module(".d16_medecine", __package__).reprendre_accidents(p, "route")
    for st in tr.stations: _approvisionner_station(p, tr, st)
    for g in tr.garages: _approvisionner_garage(p, tr, g)
    for conc in tr.concessions: _approvisionner_concession(p, tr, conc)


def _approvisionner_station(p, tr, st, final=False):
    """La station rachete a la raffinerie ( domaine 11 ) de quoi tenir STOCK_STATION_J jours de ventes, et paie
    l accise a l Etat ; si la raffinerie n en a pas assez et qu il reste moins d un jour, elle importe."""
    L = p.socle.livre
    for bien in FUELS:
        bid = tr.bid[bien]
        cible = STOCK_STATION_J * max(st.ventes_ema[bien], 1.0)
        manque = cible - st.stock[bid]
        if manque <= 0: continue
        acc = ACCISE_L[bien] * LITRES_UNITE
        q = ENE.vendre_produit(p, st, bien, min(manque, max(0.0, st.caisse) / (_prix_depart(p, bien) + acc)), st)
        if q > 0:
            L.transferer(st, p.w.gouv, q * acc, "accise_carburant")
            tr.stats["litres_achetes_d11"] += q * LITRES_UNITE
            st.achats_mois += q * (_prix_depart(p, bien) + acc)
        if st.stock[bid] < max(st.ventes_ema[bien], 1.0):
            besoin = max(st.ventes_ema[bien], 1.0) * 2.0 - st.stock[bid]
            x, paye = EXT.importer_au_port(p, st, st.stock, bien, min(besoin, max(0.0, st.caisse) / (EXT.prix_import(p, bien) + acc)), "import_biens")
            if x > 0:
                L.transferer(st, p.w.gouv, x * acc, "accise_carburant")
                tr.stats["litres_importes"] += x * LITRES_UNITE
                st.achats_mois += paye + x * acc


def _approvisionner_garage(p, tr, g):
    """Le garage commande l acier usine a l industrie ( `livrer` ) et importe pieces et pneus pour STOCK_GARAGE_J jours."""
    for bien in ("pieces", "pieces_auto", "pneus"):
        bid = tr.bid[bien]
        cible = STOCK_GARAGE_J * g.conso_ema[bien]
        manque = cible - g.stock[bid]
        if manque <= cible * 0.3: continue
        if bien == "pieces":
            prix = IND.BIENS["pieces"][2]
            q = min(manque, max(0.0, g.caisse) / prix, IND.stock_du_pays(p, "pieces"))
            if q > 1e-6: g.achats_mois += IND.livrer(p, "pieces", q, g.stock, g) * prix
        else:
            q = min(manque, max(0.0, g.caisse) / EXT.prix_import(p, bien) * 0.999)
            if q > 1e-6: g.achats_mois += EXT.importer_au_port(p, g, g.stock, bien, q, "import_biens")[1]


def _approvisionner_concession(p, tr, conc):
    """Le stock neuf remonte a sa cible ( import ) ; l occasion aussi ( import d Allemagne, 6 a 14 ans ) ; une occasion
    invendue depuis EXPORT_APRES_J jours part a l export."""
    rng = p.hasard("transport_concessions")
    for m in range(NM):
        if conc.cible_neuf[m] <= 0: continue
        manque = conc.cible_neuf[m] - _stock_neuf(p, tr, conc, m) - conc.commandes[m]
        if manque > 0: importer_vehicules(p, conc, m, manque, conc.marche)
    manque = conc.cible_occ - len(conc.occasions) - conc.occ_commandes
    for _ in range(max(0, manque)):
        m = IDX[("citadine", "berline", "suv")[int(rng.choice(3, p=np.array(PART_MODELES_CLASSE[1]) / sum(PART_MODELES_CLASSE[1])))]]
        age = float(rng.uniform(6.0, 14.0))
        km = CARAC[m].km_an * age * float(facteur_age(age / 2.0))
        if not importer_occasion(p, conc, m, age, km): break
    parc = p.socle.parc
    for oid, j in sorted(conc.occasions.items()):
        if p.jour - j < EXPORT_APRES_J: continue
        o = parc.objets.get(oid)
        if o is None: del conc.occasions[oid]; continue
        m = tr.idx_parc[o.modele]
        v = _valeur_fiche(p, CARAC[m], tr.fiches[oid]) * DECOTE_IMPORT_OCCASION
        del conc.occasions[oid]
        _sortir(p, tr, o, "exporte")
        p.socle.livre.recevoir_de_l_exterieur(conc, v, "export_vehicules")
        p.compter("export_occasion")


def _distribuer(p, tr):
    """Chaque mois ( jour 29 de chaque cycle de 30 ) : la moitie de la marge du mois va au proprietaire, sans descendre
    la caisse sous FDR_J jours d achats."""
    L = p.socle.livre
    for x in tr.concessions + tr.stations + tr.garages:
        fdr = FDR_J * x.achats_mois / 30.0
        a_verser = min(PART_DISTRIBUEE * max(0.0, x.marge_mois), max(0.0, x.caisse - fdr))
        if a_verser > 0.0 and x.proprietaire is not None:
            L.transferer(x, x.proprietaire, a_verser, "benefice_transport")
            p.compter("benefice_transport", a_verser)
        x.marge_mois = 0.0
        x.achats_mois = 0.0


def _administration(p):
    """10 h : la taxe de circulation des menages et des flottes dont c est le jour ; les examens du permis."""
    tr = _tr(p); w = p.w; L = p.socle.livre
    n = len(w.menages)
    jour = p.jour % 365
    ids = np.arange(n)
    S = _slots(p, n)
    M = np.stack([a[:n] for a in S["m"]])
    du = ((ids * 37) % 365 == jour) & (M >= 0).any(axis=0)
    for i in np.nonzero(du)[0].tolist():
        mg = w.menages[i]
        tot = 0.0
        for k in K3:
            m = int(M[k, i])
            if m >= 0: tot += taxe_circulation(CARAC[m], ANNEE_0 + int(S["ne"][k][i]) / JOURS_AN)
        _taxer(p, tr, mg, tot, "taxe_circulation")
    for f in tr.flottes:
        if f.jour_taxe != jour or not f.gere: continue
        coh = _cohorte(p, tr, f.modele, f.proprietaire, f.lieu)
        if coh is None: continue
        _taxer(p, tr, f.proprietaire, coh.nombre * taxe_circulation(CARAC[f.modele], ANNEE_0 + f.ne / JOURS_AN),
               "taxe_circulation_pro")
    _permis(p, tr)


def _taxer(p, tr, payeur, montant, motif):
    if montant <= 0: return
    x = p.socle.livre.transferer(payeur, p.w.gouv, montant, motif)
    tr.stats["taxe_circulation"] += x
    p.compter("taxe_circulation", x)
    if montant - x > 1e-6:
        tr.impayes.append(p.socle.creances.constater(p.w.gouv, payeur, montant - x, motif, p.jour))
        p.compter("taxe_circulation_impayee", montant - x)


def _permis(p, tr):
    """Des adultes sans permis B se presentent ( chance par age ) : lecons a l auto-ecole du garage, frais d examen a
    l Etat, reussite REUSSITE_EXAMEN."""
    w = p.w; H = w.habitants; L = p.socle.livre
    nj = p.col("habitant", "naissance_j")[:len(H)]
    pm = p.col("habitant", "vh_permis")
    age = (p.jour - nj) / JOURS_AN
    chance = np.zeros(len(H))
    for a, q in PASSAGE_PERMIS_AN:
        chance = np.where(age >= a, q, chance)
    viv = np.fromiter((h.vivant for h in H), bool, len(H))
    u = p.du_jour("transport_permis").random((len(H), 2))
    cand = np.nonzero(viv & ((pm[:len(H)] & 1) == 0) & (u[:, 0] < chance / JOURS_AN))[0]
    for i in cand.tolist():
        h = H[i]; mg = h.menage
        if mg is None: continue
        g = tr.par_marche[mg.domicile.marche.id][2]
        cout = LECONS_PERMIS + FRAIS_PERMIS
        if mg.caisse - RESERVE_ACHAT_J * _cout_nourriture(p, mg) < cout * (1.0 + _tva(p)): continue
        L.transferer(mg, g, LECONS_PERMIS, "lecons_conduite")
        ET.percevoir_tva(p, mg, "pieces_auto", LECONS_PERMIS)
        g.marge_mois += LECONS_PERMIS
        L.transferer(mg, w.gouv, FRAIS_PERMIS, "frais_permis")
        tr.stats["examens"] += 1
        if u[i, 1] < REUSSITE_EXAMEN:
            pm[i] |= 1; tr.stats["permis"] += 1; p.compter("permis_obtenu")
        else: p.compter("examen_echoue")


# ================================================================== la journee ( 20 h 30 )
def _journee(p):
    """La journee des vehicules : reconcilier les menages ( demenagement, extinction ), rouler, faire le plein, les
    evenements, les entretiens, les flottes, les notes, les decisions."""
    tr = _tr(p); w = p.w
    n = len(w.menages)
    _reconcilier(p, tr, n)
    v, bits, classe = _habitants(p, tr)
    km, mi, has = _rouler(p, tr, n, v, bits)
    _pleins(p, tr, n, mi, has)
    _entretiens(p, tr, n, mi, has)
    _noter(p, tr, n, v)                      # la note du jour, AVANT les decisions du jour ( jamais le soir meme )
    tr.depense_jour = {}                     # ce qui suit compte dans la note de demain
    _evenements(p, tr, n, km, mi, has)
    _flottes(p, tr)
    _decider_achats(p, tr, n, v, bits, classe)
    _lisser(tr)
    if (p.jour - tr.jour_install) % 30 == 29: _distribuer(p, tr)


def _lisser(tr):
    """Les ventes des stations et la consommation des garages, lissees sur ~ 5 jours ( la cible de leurs stocks )."""
    for st in tr.stations:
        for b in FUELS: st.ventes_ema[b] += 0.2 * (st.ventes_jour[b] - st.ventes_ema[b]); st.ventes_jour[b] = 0.0
    for g in tr.garages:
        for b in g.conso_jour: g.conso_ema[b] += 0.2 * (g.conso_jour[b] - g.conso_ema[b]); g.conso_jour[b] = 0.0


def _reconcilier(p, tr, n):
    """Un menage qui a demenage emmene ses vehicules ( cohorte et individus changent de lieu ) ; les vehicules d un
    menage eteint ( dissous, sans vivant ) sont rachetes par la concession de son marche, le produit a l Etat ( ou
    exportes si tout le menage a emigre )."""
    w = p.w; parc = p.socle.parc
    kl = p.col("menage", "vh_lieu")
    dis = p.col("menage", "dissous")[:n] if "dissous" in p.colonnes["menage"] else np.zeros(n, np.int8)
    S = _slots(p, n)
    M = np.stack([a[:n] for a in S["m"]])
    avec = (M >= 0).any(axis=0)
    for i in np.nonzero(avec)[0].tolist():
        mg = w.menages[i]
        vivant = any(x.vivant for x in mg.membres)
        if dis[i] or not vivant:
            _succession(p, tr, mg)
            continue
        k_now = tr.k_lieu[mg.domicile.id]
        if kl[i] != k_now:
            ancien = tr.lieux[int(kl[i])]
            nouveau = mg.domicile.id
            for k in K3:
                m = int(M[k, i])
                if m < 0: continue
                oid = tr.ind.get((i, k))
                if oid is not None: parc.deplacer(parc.objets[oid], nouveau)
                else: parc.deplacer_de_cohorte(parc.cohortes[(tr.mids[m], tr.flotte, ancien)], 1, nouveau)
            kl[i] = k_now


def _succession(p, tr, mg):
    conc = tr.par_marche[mg.domicile.marche.id][0]
    emigre = "ext_emigre_j" in p.colonnes["habitant"] and any(
        int(p.col("habitant", "ext_emigre_j")[h.id]) >= 0 for h in mg.membres)
    for k in K3:
        if _cols(p, f"vh_m{k}")[mg.id] < 0: continue
        o = individu(p, mg.id, k)
        m = tr.idx_parc[o.modele]
        fiche = _vider_slot(p, tr, mg.id, k)
        tr.reparations.pop(o.id, None)
        if emigre:
            p.socle.parc.ceder(o, conc, "emigration")
            tr.fiches[o.id] = fiche
            _sortir(p, tr, o, "exporte"); continue
        val = valeur_venale(CARAC[m], (p.jour - fiche.ne) / JOURS_AN, o.usure) * (1.0 - DECOTE_REPRISE)
        p.socle.parc.ceder(o, conc, "succession")
        if o.lieu != conc.marche: p.socle.parc.deplacer(o, conc.marche)
        tr.fiches[o.id] = fiche
        if o.etat != O.SERVICE:
            _sortir(p, tr, o, "rebut"); continue
        conc.occasions[o.id] = p.jour
        p.socle.livre.transferer(conc, p.w.gouv, val, "rachat_vehicule_succession")


# ------------------------------------------------------------------ les notes et les achats
def note_du_jour(p, tr, mg):
    """La consequence du jour pour CE menage : mobilite, a mange, exces d effort automobile, tampon entame."""
    w = p.w; i = mg.id
    voulu = max(KM_MOBILITE_MIN, _besoin_km(p, tr, mg))
    fait = float(tr.km_menage[i]) if i < len(tr.km_menage) else 0.0
    mob = min(1.0, fait / voulu)
    mange = 1.0 if w.nourri_menage.get(i, True) else 0.0
    rev = _revenu(p, i)
    effort = (_mensualites_auto(tr, i) / 30.0 + tr.depense_jour.get(i, 0.0)) / max(1.0, rev)
    tampon = 1.0 if mg.caisse < RESERVE_ALIMENTAIRE_J * _cout_nourriture(p, mg) else 0.0
    return 0.5 * mob + 0.5 * mange - min(1.0, max(0.0, effort - SEUIL_EFFORT)) - 0.5 * tampon


def _noter(p, tr, n, v):
    w = p.w
    for dec in (tr.dec_achat, tr.dec_reparer):
        cles = [k for k, a in dec.attentes.items() if a.choix]
        for cle in cles:
            mg = w.menages[cle]
            dec.noter(cle, note_du_jour(p, tr, mg), p.jour)
        for cle in [k for k, a in dec.attentes.items() if not a.choix]: del dec.attentes[cle]


def _decider_achats(p, tr, n, v, bits, classe):
    """Un menage qui a un permis decide chaque semaine ( son jour ) s il n a pas de vehicule utilisable, et tous les 14
    jours si son plus vieux vehicule a AGE_REMPLACER ans ou USURE_REMPLACER de sa vie ET qu il a eu une panne ou un
    accident dans les 90 jours ( on repense a une vieille voiture quand elle commence a lacher : a calibrer )."""
    w = p.w
    S = _slots(p, n)
    M = np.stack([a[:n] for a in S["m"]]).astype(np.int64)
    has = M >= 0; mi = np.where(has, M, 0)
    age = np.where(has, (p.jour - np.stack([a[:n] for a in S["ne"]]).astype(float)) / JOURS_AN, 0.0)
    usure = np.where(has, np.stack([a[:n] for a in S["km"]]).astype(float) / VIE_KM[mi], 0.0)
    vieux = ((age >= AGE_REMPLACER) | (usure >= USURE_REMPLACER)).any(axis=0)
    ennuis = np.zeros(n, bool)
    for i, l in tr.pannes_j.items():
        if i < n and l and p.jour - l[-1] <= 90: ennuis[i] = True
    vieux &= ennuis
    aucun = ~has.any(axis=0)
    dis = p.col("menage", "dissous")[:n] if "dissous" in p.colonnes["menage"] else np.zeros(n, np.int8)
    ids = np.arange(n)
    util = np.ones(n, bool)
    for (i, k), oid in tr.ind.items():          # un vehicule en panne ne compte pas comme utilisable
        if i < n and p.socle.parc.objets[oid].etat != O.SERVICE: util[i] = False
    sans = aucun | (~util & (has.sum(axis=0) <= 1))
    cand = np.nonzero((v > 0) & (dis == 0) & (bits > 0)
                      & ((sans & ((ids + p.jour) % JOURS_SANS == 0)) | (~sans & vieux & ((ids + p.jour) % JOURS_VIEUX == 0))))[0]
    for i in cand.tolist():
        if i in tr.commandes_clients: continue
        mg = w.menages[i]
        cl, b = int(classe[i]), int(bits[i])
        reserve = RESERVE_ACHAT_J * _cout_nourriture(p, mg)
        conc, occ, neuf = _offres(p, tr, mg, cl, b, reserve)
        rev, n_veh, vx, us = _traits_menage(p, tr, mg)
        util = _utilisables(p, tr, i)
        x = (min(1.0, rev / 300.0), min(1.0, mg.caisse / 20000.0), n_veh / 3.0, min(1.0, vx / 30.0), min(1.0, us),
             min(1.0, _besoin_km(p, tr, mg) / 60.0), min(6, int(v[i])) / 6.0,
             min(1.0, occ[0] / max(1.0, 365.0 * rev)) if occ else 1.0,
             min(1.0, neuf[0] / max(1.0, 730.0 * rev)) if neuf else 1.0,
             min(1.0, _mensualites_auto(tr, i) / max(1.0, 30.0 * rev)),
             min(3, len(tr.pannes_j.get(i, ()))) / 3.0, 1.0 if _categories_voulues(p, mg, cl, b) else 0.0,
             1.0 if util > 0 else 0.0)
        reprise = _slot_a_reprendre(p, tr, i) if not aucun[i] else None
        a = tr.dec_achat.decider(i, ContexteAchat(x, mg, occ, neuf))
        if a: _acheter(p, tr, mg, a, cl, b, reprise)


def _slot_a_reprendre(p, tr, i):
    """L emplacement que l achat remplace : le plus vieux vehicule a quatre roues ( ou le plus vieux )."""
    best, ba = None, -1.0
    for k in K3:
        m = int(_cols(p, f"vh_m{k}")[i])
        if m < 0: continue
        a = (p.jour - int(_cols(p, f"vh_ne{k}")[i])) / JOURS_AN
        if a > ba: best, ba = k, a
    return best


def _acheter(p, tr, mg, a, classe, bits, reprise=None):
    """Execute un achat decide : l occasion la moins chere qui lui va, ou le neuf, avec reprise de `reprise`."""
    reserve = RESERVE_ACHAT_J * _cout_nourriture(p, mg)
    conc, occ, neuf = _offres(p, tr, mg, classe, bits, reserve)
    if reprise is not None and tr.ind.get((mg.id, reprise)) is not None:
        o = p.socle.parc.objets[tr.ind[(mg.id, reprise)]]
        if o.etat != O.SERVICE: reprise = None
    if reprise is None and _slot_libre(p, mg.id) is None: reprise = _slot_a_reprendre(p, tr, mg.id)
    fait = 0.0
    if a == 1 and occ is not None:
        if occ[1] is not None: fait = vendre_occasion(p, conc, mg, occ[1], reprise)
        elif importer_occasion(p, conc, occ[3], AGE_COMMANDE, _km_commande(occ[3]), client=mg.id):   # paye ou finance a l arrivee
            tr.commandes_clients[mg.id] = p.jour; return -1.0
    elif a == 2 and neuf is not None:
        if neuf[4]: fait = vendre_neuf(p, conc, mg, neuf[1], reprise)
        elif importer_vehicules(p, conc, neuf[1], 1, conc.marche, client=mg.id):
            tr.commandes_clients[mg.id] = p.jour; return -1.0
    if fait <= 0.0: p.compter("achat_abandonne")
    return fait


# ================================================================== installation
def _declarer(p, tr):
    parc = p.socle.parc; cat = p.socle.catalogue
    for c in CARAC:
        m = parc.declarer_modele(c.nom, "vehicule", c.fob, c.masse_kg, c.vie_km / V_USAGE[c.categorie], arma=c.arma,
                                 arma_preuve=None,
                                 source=f"{c.categorie} ; prix catalogue {c.prix_ttc / DR:.0f} euros TTC ( ordre de grandeur "
                                        f"grec 2024-2025, a verifier ) ; FOB derive ( TVA, taxe d immatriculation, marge, "
                                        f"fret, droit retires ) ; {c.l100} l/100 km, {c.reservoir_l} l, autonomie "
                                        f"{c.autonomie_km():.0f} km ; pannes, vie, entretien a calibrer")
        tr.mids.append(m.id); tr.idx_parc[m.id] = c.idx
        c.modele = m
    for nom, famille, unite, prix_eur, masse, vol, src in (
            ("pieces_auto", "piece", "1 kg de pieces detachees automobiles ( filtres, freins, embrayage, courroies, "
             "carrosserie, fluides )", PRIX_PIECES_EUR_KG, 1.0, 0.8, "~ 12 euros le kg au port ( ordre de grandeur des "
             "importations de pieces de rechange, Eurostat Comext 8708, a calibrer )"),
            ("pneus", "piece", "un pneu de voiture 205/55 R16 ( un pneu de poids lourd en vaut 4 )", PRIX_PNEU_EUR, 8.5, 60.0,
             "~ 60 euros au port ( a calibrer )")):
        if nom not in cat.par_nom:
            cat.declarer(nom, famille, unite, prix_eur * DR, categorie_tva="normale", masse_kg=masse, volume_l=vol, source=src)
    for b in ("pieces_auto", "pneus", "pieces", "essence", "carburant"): tr.bid[b] = cat.id(b)


def _motifs(p):
    L = p.socle.livre
    for m in ("vente_vehicule", "reprise_vehicule", "carburant_station", "entretien_vehicule", "reparation_vehicule",
              "lecons_conduite", "export_vehicules", "rachat_vehicule_succession", "dotation_initiale_transport"):
        L.declarer_motif(m, "achat", "transport")
    for m in ("taxe_immatriculation", "accise_carburant", "taxe_circulation_pro"):
        L.declarer_motif(m, "impot_production", "transport")
    for m in ("taxe_circulation", "frais_permis"):              # SEC 2010 4.79 : impots courants des menages ( D.59 )
        L.declarer_motif(m, "impot_revenu", "transport")
    L.declarer_motif("benefice_transport", "revenu_propriete", "transport")


def _journal(p):
    J = p.socle.journal
    for t, champs in (("accident_de_la_route", ("lieu", "modele", "victimes", "tues")),
                      ("vol_de_vehicule", ("modele", "proprietaire", "lieu")),
                      ("vehicule_retrouve", ("modele", "proprietaire")),
                      ("vehicule_detruit", ("modele", "proprietaire", "cause"))):
        J.declarer(t, "transport", "individuel", champs)
    for t in ("vente_neuf", "vente_occasion", "reprise_vehicule", "import_neuf", "import_occasion", "export_occasion",
              "plein_carburant", "km_parcourus", "station_a_sec", "panne_vehicule", "entretien_vehicule",
              "reparation_vehicule", "sinistre_materiel", "blessure_route", "tue_route", "blessure_sans_medecine",
              "vehicule_rebut", "permis_obtenu", "examen_echoue", "taxe_circulation", "taxe_circulation_impayee",
              "credit_auto", "credit_auto_refuse", "achat_abandonne", "penurie_pieces", "benefice_transport"):
        J.declarer(t, "transport", "compte")


def _colonnes(p):
    cm, ch = p.colonnes["menage"], p.colonnes["habitant"]
    for k in K3:
        for nom, dt, d in (("m", np.int8, -1), ("ne", np.int32, 0), ("km", np.float32, 0.0), ("ks", np.float32, 0.0),
                           ("js", np.int32, 0), ("res", np.float32, 0.0)):
            cm.ajouter(f"vh_{nom}{k}", dt, d)
    cm.ajouter("vh_lieu", np.int16, -1)
    cm.ajouter("vh_ind", np.int8, 0)
    ch.ajouter("vh_permis", np.int8, 0)
    cm.assurer(len(p.w.menages)); ch.assurer(len(p.w.habitants))


def _proprietaire(p, marche, rng):
    """Le menage qui possede une affaire du marche : un menage aise du lieu, sinon n importe quel menage habite du lieu."""
    w = p.w
    aises = [m for m in w.menages if m.domicile.id == marche and any(x.vivant and x.classe == "aisee" for x in m.membres)]
    tous = aises or [m for m in w.menages if m.domicile.marche.id == marche and any(x.vivant for x in m.membres)]
    return tous[int(rng.integers(0, len(tous)))] if tous else None


def _detenteurs(p, tr, rng):
    w = p.w; L = p.socle.livre; B = BI
    bq = p.domaine("banques").banques
    pop = {k: w._pop_marche.get(k, 0) for k in w.marches}
    for j, mid in enumerate(sorted(w.marches)):
        conc = Concession(mid, _proprietaire(p, mid, rng))
        st = StationService(mid, _proprietaire(p, mid, rng), B.Stock())
        g = Garage(mid, _proprietaire(p, mid, rng), B.Stock())
        for k, x in enumerate((conc, st, g)): BQ.ouvrir_compte(p, x, bq[(3 * j + k) % len(bq)])
        tr.concessions.append(conc); tr.stations.append(st); tr.garages.append(g)
        tr.par_marche[mid] = (conc, st, g)
        h = max(1, pop[mid])
        for nom, mini in STOCK_MIN_NEUF.items():
            conc.cible_neuf[IDX[nom]] = max(mini, int(round(h * VENTES_NEUF_1000_AN / 1000.0 / JOURS_AN * STOCK_NEUF_J
                                                            * PARC_1000[nom] / sum(PARC_1000[x] for x in STOCK_MIN_NEUF))))
        conc.cible_occ = max(STOCK_MIN_OCC, int(round(h * VENTES_OCC_1000_AN / 1000.0 / JOURS_AN * STOCK_OCC_J)))
    reg = p.socle.registre
    reg.inscrire("concessions", "entreprises", _membres_concessions, "caisse", None, "Concession")
    for conc in tr.concessions:        # le capital d ouverture : la moitie du stock neuf vise, apportee de l etranger
        cap = 0.5 * sum(conc.cible_neuf[m] * CARAC[m].cout_rendu for m in range(NM))
        L.recevoir_de_l_exterieur(conc, cap, "investissement_direct")
    reg.inscrire("stations_service", "entreprises", _membres_stations, "caisse", "stock", "StationService")
    reg.inscrire("garages", "entreprises", _membres_garages, "caisse", "stock", "Garage")
    tr.reservoirs = Reservoirs(B.Stock())
    reg.inscrire("reservoirs_vehicules", "menages", _membres_reservoirs, None, "stock", None)


def _tirer_age(rng, cat, n=None):
    moy = AGE_MOYEN[cat]
    a = rng.gamma(4.0, moy / 4.0, n)
    return np.minimum(a, AGE_MAX)


def _recensement(p, tr, rng):
    """Le parc du jour de l installation : permis des habitants ; vehicules des menages selon leur revenu, pick-up des
    paysans, deux-roues des titulaires du permis A ; flottes des entreprises du moteur, autocars de l Etat ; stocks des
    concessions. Chaque vehicule entre au Parc par la source « initial » et au registre par « recensement »."""
    w = p.w; parc = p.socle.parc; H = w.habitants
    # --- permis
    pm = p.col("habitant", "vh_permis"); sexe = p.col("habitant", "sexe"); nj = p.col("habitant", "naissance_j")
    for h in H:
        if not h.vivant: continue
        a = (p.jour - int(nj[h.id])) / JOURS_AN
        if a < POP.AGE_MAJEUR: continue
        s = int(sexe[h.id]) if sexe[h.id] >= 0 else POP.HOMME
        qb = 0.0
        for seuil, q in PERMIS_B_AGE[s]:
            if a >= seuil: qb = q
        bits = 1 if rng.random() < qb else 0
        if rng.random() < PERMIS_A[s] * (0.4 if a >= 65 else 1.0): bits |= 2
        elif rng.random() < PERMIS_A1: bits |= 4
        if h.role == "convoyeur" or (s == POP.HOMME and a < 65 and rng.random() < PERMIS_C_HOMMES): bits |= 8 | 1
        if s == POP.HOMME and 25 <= a < 65 and rng.random() < PERMIS_D_HOMMES: bits |= 16 | 1
        pm[h.id] = bits
    # --- vehicules des menages
    n = len(w.menages)
    v, bits, classe = _habitants(p, tr)
    dis = p.col("menage", "dissous")[:n] if "dissous" in p.colonnes["menage"] else np.zeros(n, np.int8)
    ok = (v > 0) & (dis == 0)
    rev = np.array([_revenu(p, i) for i in range(n)])
    io = np.nonzero(ok)[0]
    q = np.zeros(n, np.int64)
    if len(io):
        rang = np.empty(len(io), np.int64); rang[np.argsort(rev[io], kind="stable")] = np.arange(len(io))
        q[io] = np.minimum(4, rang * 5 // len(io))
    paysan = np.zeros(n, bool)
    for h in H:
        if h.vivant and h.role == "paysan" and h.menage is not None: paysan[h.menage.id] = True
    pop = int(v[ok].sum())
    x_car = np.where(ok & ((bits & 1) != 0), np.array(VOITURES_PAR_QUINTILE)[q], 0.0)
    x_car *= VOITURES_1000 * pop / 1000.0 / max(1e-9, x_car.sum())
    x_2r = np.where(ok & ((bits & (2 | 4)) != 0), 1.0, 0.0)
    x_2r *= DEUX_ROUES_1000 * pop / 1000.0 / max(1e-9, x_2r.sum())
    u = rng.random((n, 4))
    kl = p.col("menage", "vh_lieu")
    compte = [0] * NM
    for i in io.tolist():
        liste = []
        if paysan[i] and bits[i] & 1 and u[i, 0] < PICKUP_PAYSAN: liste.append(IDX["pick_up"])
        nv = int(math.floor(x_car[i])) + (1 if u[i, 1] < x_car[i] - math.floor(x_car[i]) else 0)
        parts = np.array(PART_MODELES_CLASSE[int(classe[i])], float)
        for _ in range(nv):
            liste.append(IDX[VOITURES[int(rng.choice(3, p=parts / parts.sum()))]])
        n2 = int(math.floor(x_2r[i])) + (1 if u[i, 2] < x_2r[i] - math.floor(x_2r[i]) else 0)
        for _ in range(n2):
            liste.append(IDX["moto"] if (bits[i] & 2) and u[i, 3] < PART_MOTO else IDX["scooter"])
        liste = liste[:3]
        if not liste: continue
        mg = w.menages[i]
        kl[i] = tr.k_lieu[mg.domicile.id]
        for k, m in enumerate(liste):
            c = CARAC[m]
            age = float(_tirer_age(rng, c.categorie))
            km = c.km_an * age * float(facteur_age(age / 2.0)) * float(rng.uniform(0.8, 1.2))
            ks = max(0.0, km - float(rng.uniform(0.0, c.intervalle_km)))
            for nom, val in (("m", m), ("ne", p.jour - int(round(age * JOURS_AN))), ("km", km), ("ks", ks),
                             ("js", p.jour - int(rng.integers(0, 365))), ("res", float(rng.uniform(0.3, 1.0)) * c.reservoir_l)):
                _cols(p, f"vh_{nom}{k}")[i] = val
            parc.creer_cohorte(tr.mids[m], tr.flotte, mg.domicile.id, 1, "initial", min(1.0, km / c.vie_km))
            compte[m] += 1
    # le carburant deja dans les reservoirs ( dotation du jour du recensement )
    for f, nom in enumerate(FUELS):
        tot = 0.0
        for k in K3:
            m = _cols(p, f"vh_m{k}")[:n].astype(np.int64)
            sel = (m >= 0) & (FUEL_IDX[np.maximum(m, 0)] == f)
            tot += float(_cols(p, f"vh_res{k}")[:n][sel].astype(float).sum())
        if tot > 0: p.socle.livre.importer(tr.reservoirs.stock, tr.bid[nom], tot / LITRES_UNITE, "dotation_initiale_transport")
    # --- flottes
    for e in sorted(w.entreprises.values(), key=lambda e: e.id):
        travailleurs = len([h for h in w.au_travail_de(e.lieu, e.role) if h.vivant])
        for nom, par_trav in FLOTTE_TYPE.get(e.type, ()):
            k = max(1, int(round(travailleurs * par_trav)))
            _flotte_initiale(p, tr, rng, e, e.lieu.id, IDX[nom], k, compte)
    for mid in sorted(w.marches):
        k = max(1, int(round(w._pop_marche.get(mid, 0) / UTILITAIRES_MARCHE_HAB)))
        _flotte_initiale(p, tr, rng, w.marches[mid], mid, IDX["utilitaire"], k, compte)
    capitale = max(w.marches, key=lambda k: (w._pop_marche.get(k, 0), k))
    _flotte_initiale(p, tr, rng, w.gouv, capitale, IDX["bus"], max(1, int(round(pop * BUS_1000 / 1000.0))), compte)
    # --- stocks des concessions
    for conc in tr.concessions:
        for m in range(NM):
            if conc.cible_neuf[m] > 0:
                parc.creer_cohorte(tr.mids[m], conc, conc.marche, conc.cible_neuf[m], "initial"); compte[m] += conc.cible_neuf[m]
        for _ in range(conc.cible_occ):
            m = IDX[VOITURES[int(rng.choice(3, p=np.array(PART_MODELES_CLASSE[1]) / sum(PART_MODELES_CLASSE[1])))]]
            age = float(rng.uniform(6.0, 16.0)); km = CARAC[m].km_an * age * float(facteur_age(age / 2.0))
            o = parc.creer(tr.mids[m], conc, conc.marche, "initial", p.pas, min(1.0, km / VIE_KM[m]))
            tr.fiches[o.id] = Fiche(p.jour - int(round(age * JOURS_AN)), km, km, p.jour)
            conc.occasions[o.id] = p.jour
            compte[m] += 1
    for m in range(NM): tr.registre.entrees["recensement"][m] += compte[m]
    # --- le stock de depart des stations et des garages ( dotation )
    L = p.socle.livre
    for st in tr.stations:
        h = max(1, w._pop_marche.get(st.marche, 0))
        for bien in FUELS:
            q = STOCK_STATION_J * _conso_attendue(p, tr, st.marche, bien)
            st.ventes_ema[bien] = q / STOCK_STATION_J
            if q > 0: L.importer(st.stock, tr.bid[bien], q, "dotation_initiale_transport")
    for g in tr.garages:
        h = max(1, w._pop_marche.get(g.marche, 0))
        for bien, parhab in (("pieces_auto", PIECES_HAB_J), ("pneus", PNEUS_HAB_J)):
            q = STOCK_GARAGE_J * h * parhab
            g.conso_ema[bien] = h * parhab
            L.importer(g.stock, tr.bid[bien], q, "dotation_initiale_transport")
        g.conso_ema["pieces"] = h * PIECES_HAB_J * PART_PIECES_INDUSTRIE / 1000.0


def _conso_attendue(p, tr, marche, bien):
    """Unites par jour que les vehicules des menages du marche brulent en moyenne ( pour le stock de depart )."""
    w = p.w; n = len(w.menages); tot = 0.0
    for i in range(n):
        mg = w.menages[i]
        if mg.domicile.marche.id != marche: continue
        for k in K3:
            m = int(_cols(p, f"vh_m{k}")[i])
            if m < 0 or CARAC[m].carburant != bien: continue
            age = (p.jour - int(_cols(p, f"vh_ne{k}")[i])) / JOURS_AN
            tot += KM_AN[m] / JOURS_AN * float(facteur_age(age)) * L100[m] / 100.0 / LITRES_UNITE
    return tot


def _flotte_initiale(p, tr, rng, proprio, lieu, m, n, compte):
    c = CARAC[m]
    ages = _tirer_age(rng, c.categorie, n)
    u = float(np.mean([min(1.0, c.km_an * a * float(facteur_age(a / 2.0)) / c.vie_km) for a in ages]))
    p.socle.parc.creer_cohorte(tr.mids[m], proprio, lieu, int(n), "initial", u)
    f = Flotte(proprio, lieu, m, float(p.jour - np.mean(ages) * JOURS_AN), len(tr.flottes) * 37 % 365)
    tr.flottes.append(f)
    compte[m] += int(n)


def _avant_achats_d03(p):
    """18 h 50 : le gazole de marche ne sert plus la division transport des menages le temps de l achat de 19 h ( le
    menage fait le plein a la station pour ses km reels ). Une donnee du domaine 3, reposee a 19 h."""
    tr = _tr(p)
    tr.part_d03 = float(EC.PART_BIEN[EC.I_TRANSPORT])
    EC.PART_BIEN[EC.I_TRANSPORT] = 0.0


def _apres_achats_d03(p):
    tr = _tr(p)
    if tr.part_d03 is not None: EC.PART_BIEN[EC.I_TRANSPORT] = tr.part_d03
    tr.part_d03 = None


def installer(p):
    w = p.w
    tr = Transport()
    p.domaines["transport"] = tr
    tr.jour_install = p.jour
    tr.lieux = sorted(w.carte.lieux)
    tr.k_lieu = {lid: k for k, lid in enumerate(tr.lieux)}
    _declarer(p, tr); _motifs(p); _journal(p); _colonnes(p)
    rng = p.hasard("transport_recensement")
    _detenteurs(p, tr, rng)
    _recensement(p, tr, rng)
    tr.km_menage = np.zeros(len(w.menages))
    tr.dec_achat = p.decideur(POINT_ACHAT)
    tr.dec_reparer = p.decideur(POINT_REPARER)
    IND.commander(p, "pieces", len(w.habitants) * PIECES_HAB_J * PART_PIECES_INDUSTRIE / 1000.0)
    p.echeance("transport_arrivage", _arrivage)
    p.echeance("transport_fin_reparation", _fin_reparation)
    p.echeance("transport_issue_vol", _issue_vol)
    p.echeance("transport_redecider", _redecider)
    p.routine(6 + 20 / 60, 30, "transport", _matin)
    p.routine(10, 30, "transport", _administration)
    p.routine(18 + 50 / 60, 99, "transport", _avant_achats_d03)
    p.routine(19, 0, "transport", _apres_achats_d03)
    p.routine(20.5, 30, "transport", _journee)
    return tr


# ================================================================== controles ( portes )
def anomalies_parc(p):
    """Tout ce que le registre et les colonnes ne s expliquent pas : [ ( type, detail ) ].
      hors_registre      un modele du domaine dont le Parc compte plus ( ou moins ) que recensement + imports - sorties :
                         un vehicule apparu hors importation ou hors recensement ;
      hors_achat         un ( modele, lieu ) dont les emplacements des menages ne font pas la cohorte de la flotte plus
                         les individus : un vehicule pose dans un menage sans achat ( ou disparu sans sortie ) ;
      parc               Parc.verifier non nul ;
      individu           un individu de menage absent du Parc, ou dont le proprietaire n est pas le menage ;
      individu_orphelin  un individu d un modele du domaine qui n est ni dans un menage, ni en reparation, ni en stock
                         d occasion, ni vole, ni requisitionne : un individu oublie ( il devait rentrer dans sa cohorte ) ;
      reservoirs         les litres des colonnes ne font pas le Stock des reservoirs."""
    tr = _tr(p); parc = p.socle.parc; w = p.w
    out = []
    for m in range(NM):
        if parc.vivants[tr.mids[m]] != tr.registre.vivants(m):
            out.append(("hors_registre", CARAC[m].nom, parc.vivants[tr.mids[m]], tr.registre.vivants(m)))
    for nom, e in parc.verifier().items():
        if e: out.append(("parc", nom, e))
    n = len(w.menages)
    kl = p.col("menage", "vh_lieu")[:n].astype(np.int64)
    attendu = {}
    for k in K3:
        M = _cols(p, f"vh_m{k}")[:n].astype(np.int64)
        for i in np.nonzero(M >= 0)[0].tolist():
            if kl[i] < 0: out.append(("hors_achat", "sans_lieu", i)); continue
            cle = (int(M[i]), tr.lieux[int(kl[i])])
            attendu[cle] = attendu.get(cle, 0) + 1
    vu = {}
    for (pm, prop, lieu), c in parc.cohortes.items():
        if prop is tr.flotte and pm in tr.idx_parc:
            cle = (tr.idx_parc[pm], lieu); vu[cle] = vu.get(cle, 0) + c.nombre
    for (i, k), oid in tr.ind.items():
        o = parc.objets.get(oid)
        if o is None or o.proprietaire is not w.menages[i]: out.append(("individu", i, k, oid)); continue
        cle = (tr.idx_parc[o.modele], tr.lieux[int(kl[i])] if kl[i] >= 0 else None)
        vu[cle] = vu.get(cle, 0) + 1
    for cle in sorted(set(attendu) | set(vu), key=str):
        if attendu.get(cle, 0) != vu.get(cle, 0): out.append(("hors_achat", CARAC[cle[0]].nom, cle[1], attendu.get(cle, 0), vu.get(cle, 0)))
    concs = {id(c): c for c in tr.concessions}
    for o in parc.objets.values():
        if o.modele not in tr.idx_parc: continue
        if o.id in tr.slot_de or o.id in tr.reparations or o.id in tr.requisitions: continue
        if id(o.proprietaire) in concs and o.id in o.proprietaire.occasions: continue
        if o.proprietaire is tr.receleur and any(v.objet == o.id and v.issue is None for v in tr.vols): continue
        out.append(("individu_orphelin", CARAC[tr.idx_parc[o.modele]].nom, o.id))
    for f, nom in enumerate(FUELS):
        tot = 0.0
        for k in K3:
            M = _cols(p, f"vh_m{k}")[:n].astype(np.int64)
            sel = (M >= 0) & (FUEL_IDX[np.maximum(M, 0)] == f)
            tot += float(_cols(p, f"vh_res{k}")[:n][sel].astype(float).sum())
        st = tr.reservoirs.stock[tr.bid[nom]] * LITRES_UNITE
        if abs(tot - st) > 1e-3 * max(1.0, st) + 0.5: out.append(("reservoirs", nom, tot, st))
    return out


def recensement_du_parc(p):
    """Ce que le registre dit du parc : voitures pour 1 000 habitants, age moyen des voitures ( ans ), deux-roues pour
    1 000, part des adultes titulaires du permis B, vehicules par categorie."""
    tr = _tr(p); w = p.w; n = len(w.menages)
    viv = [h for h in w.habitants if h.vivant]
    pop = len(viv)
    ages, voit, deux = [], 0, 0
    for k in K3:
        M = _cols(p, f"vh_m{k}")[:n].astype(np.int64)
        ne = _cols(p, f"vh_ne{k}")[:n]
        sel = M >= 0
        v = sel & IS_VOITURE[np.maximum(M, 0)]
        voit += int(v.sum()); ages.extend(((p.jour - ne[v]) / JOURS_AN).tolist())
        deux += int((sel & (CAT_IDX[np.maximum(M, 0)] == CATEGORIES.index("deux_roues"))).sum())
    pm = p.col("habitant", "vh_permis")
    adultes = [h for h in viv if POP.age_de(p, h) >= POP.AGE_MAJEUR]
    par_cat = {}
    for m in range(NM):
        par_cat[CARAC[m].nom] = p.socle.parc.vivants[tr.mids[m]]
    return {"voitures_1000": 1000.0 * voit / max(1, pop), "age_voitures": float(np.mean(ages)) if ages else 0.0,
            "deux_roues_1000": 1000.0 * deux / max(1, pop),
            "permis_b": sum(1 for h in adultes if int(pm[h.id]) & 1) / max(1, len(adultes)), "par_modele": par_cat,
            "habitants": pop}


# ================================================================== API pour les autres domaines
def scenario(p, **facteurs):
    """Multiplie les taux de pannes, d accidents, de vols ou de rebut ( portes, scenarios ). Rend les facteurs."""
    tr = _tr(p)
    for k, v in facteurs.items():
        if k not in tr.scenario or not 0.0 <= v < 1e6: raise ValueError(f"facteur de scenario invalide {k}={v!r}")
        tr.scenario[k] = float(v)
    return dict(tr.scenario)


def caracteristiques(modele):
    """Domaines 15, 17, 18, 25 : les chiffres d un modele ( Caracteristiques ), par nom ou indice."""
    return CARAC[IDX[modele] if isinstance(modele, str) else modele]


def vehicules_de(p, detenteur):
    """Domaines 20, 21, 25 : [ ( modele, nombre, individu ou None ) ] des vehicules d un menage, d une entreprise, de l Etat."""
    tr = _tr(p); parc = p.socle.parc; out = []
    if type(detenteur).__name__ == "Menage":
        for k in K3:
            m = int(_cols(p, f"vh_m{k}")[detenteur.id])
            if m >= 0: out.append((CARAC[m].nom, 1, tr.ind.get((detenteur.id, k))))
        return out
    for (pm, prop, lieu), c in parc.cohortes.items():
        if prop is detenteur and pm in tr.idx_parc: out.append((CARAC[tr.idx_parc[pm]].nom, c.nombre, None))
    for o in parc.objets.values():
        if o.proprietaire is detenteur and o.modele in tr.idx_parc: out.append((CARAC[tr.idx_parc[o.modele]].nom, 1, o.id))
    return out


def acheter_flotte(p, acheteur, modele, n, lieu=None, gere=True):
    """Domaines 15, 17, 18 : une entreprise ou une administration achete `n` vehicules neufs d un modele : importes par la
    concession de son marche puis vendus ( prix TTC, TVA ) des qu ils sont en stock. `gere` : ce domaine fait vivre la
    flotte ( carburant, entretien, pannes ) ; sinon l acheteur la fait vivre lui-meme. Rend le nombre achete aujourd hui
    ( le reste est commande )."""
    tr = _tr(p); m = IDX[modele] if isinstance(modele, str) else modele
    lieu_obj = getattr(acheteur, "lieu", None)
    marche = (lieu_obj.marche or lieu_obj).id if lieu_obj is not None else sorted(tr.par_marche)[0]
    conc = tr.par_marche[marche][0]
    fait = 0
    for _ in range(int(n)):
        if _stock_neuf(p, tr, conc, m) < 1: break
        if vendre_neuf(p, conc, acheteur, m, credit=False) <= 0: break
        fait += 1
    if fait < n: importer_vehicules(p, conc, m, int(n) - fait - conc.commandes[m], conc.marche)
    for f in tr.flottes:
        if f.proprietaire is acheteur and f.modele == m: f.gere = gere
    return fait


def faire_le_plein(p, payeur, carburant, litres, marche):
    """Domaines 15, 17, 18, 25 : `litres` de gazole ( « carburant » ) ou d essence brules aussitot par un vehicule de
    l acheteur, achetes a la station du marche au prix de la pompe ( accise et TVA comprises ). Rend les litres servis."""
    st = _tr(p).par_marche[marche][1]
    return vendre_carburant(p, st, payeur, carburant, litres / LITRES_UNITE, None) * LITRES_UNITE


def entretenir(p, payeur, modele, km, marche):
    """Domaines 15, 17, 18 : l entretien de `km` parcourus par un vehicule d un modele, au garage du marche ( pieces,
    pneus, heures, TVA ). Rend les drachmes payees ( 0 si la caisse ou les pieces manquent )."""
    tr = _tr(p); c = caracteristiques(modele); g = tr.par_marche[marche][2]
    pieces = c.pieces_kg * km / c.intervalle_km; pneus = c.pneus * km / c.km_pneus
    ht = pieces * _prix_piece_kg(p) + pneus * _prix_pneu(p) + c.heures * km / c.intervalle_km * TAUX_HORAIRE_GARAGE
    if payeur.caisse < ht * (1.0 + _tva(p)) or not _consommer_pieces(p, tr, g, pieces, pneus, "entretien_vehicule"): return 0.0
    p.socle.livre.transferer(payeur, g, ht, "entretien_vehicule")
    return ht + ET.percevoir_tva(p, payeur, "pieces_auto", ht)


def accidents_du_jour(p):
    """Domaines 17 et 18 : les accidents corporels du jour ( lieu, modele, victimes, tues ), lus au journal."""
    return [e for e in p.socle.journal.derniers("accident_de_la_route", 10000) if e["jour"] == p.jour]


def sinistres(p, depuis=0, type_=None):
    """Domaine 20 : les sinistres ( accidents materiels et corporels, vols ) depuis le jour `depuis`."""
    return [s for s in _tr(p).sinistres if s.jour >= depuis and (type_ is None or s.type == type_)]


def brancher_assurance(p, couvrir):
    """Domaine 20 : `couvrir( p, sinistre, montant_ttc )` ( un objet picklable a __call__ ) rend ce que l assureur prend
    en charge d une reparation ; il le paie lui-meme au garage. Le menage paie le reste."""
    if not callable(couvrir) or getattr(couvrir, "__name__", "") == "<lambda>": raise ValueError("un objet appelable picklable")
    _tr(p).assureur = couvrir


def exposition(p):
    """Domaine 20 ( primes ) : par modele, vehicules vivants, et km parcourus depuis l installation ( tous vehicules )."""
    tr = _tr(p)
    return {"vehicules": {CARAC[m].nom: p.socle.parc.vivants[tr.mids[m]] for m in range(NM)}, "km": tr.stats["km"],
            "frequence_materielle_voiture_an": MATERIELS_VOITURE_AN}


def valeur_de(p, objet_id):
    """Domaines 20, 25 : la valeur venale d un individu ( hors taxes )."""
    tr = _tr(p); o = p.socle.parc.objets[objet_id]; m = tr.idx_parc[o.modele]
    if objet_id in tr.slot_de:
        i, k = tr.slot_de[objet_id]
        return valeur_venale(CARAC[m], (p.jour - int(_cols(p, f"vh_ne{k}")[i])) / JOURS_AN, o.usure)
    f = tr.fiches.get(objet_id)
    return valeur_venale(CARAC[m], (p.jour - f.ne) / JOURS_AN if f else 10.0, o.usure)


def vols(p, retrouves=None):
    """Domaine 21 : les vols ( la verite ; la police ne connait que les declarations, soit tous ici ) ."""
    return [v for v in _tr(p).vols if retrouves is None or (v.issue == "retrouve") == retrouves]


def retrouver(p, vol_id):
    """Domaine 21 : la police retrouve un vehicule vole avant la fin de l enquete : il revient a sa victime."""
    tr = _tr(p); v = tr.vols[vol_id]
    o = p.socle.parc.objets.get(v.objet)
    if v.issue is not None or o is None or o.proprietaire is not tr.receleur: return False
    _restituer(p, tr, v, o)
    return True


def impayes_circulation(p):
    """Domaine 21 : les creances de taxe de circulation encore actives ( recouvrement, saisie )."""
    K = p.socle.creances
    return [c for c in _tr(p).impayes if K.actives.get(c.id) is c]


def titulaires(p, categorie="B"):
    """Domaine 21 ( controles ), 25 ( conducteurs ) : les habitants vivants titulaires d un permis."""
    pm = p.col("habitant", "vh_permis"); b = PERMIS_BITS[categorie]
    return [h for h in p.w.habitants if h.vivant and int(pm[h.id]) & b]


def requisitionner(p, beneficiaire, n, categories=("voiture", "utilitaire_leger", "poids_lourd"), lieu=None):
    """Domaine 25 : requisition de `n` vehicules civils en etat de rouler ( des menages, de `lieu` s il est donne ) :
    ils sont cedes au beneficiaire ( motif requisition ). L indemnite est a la charge du domaine 25 ( `valeur` dans le
    rendu ). Rend [ ( numero, ancien proprietaire, valeur venale ) ]."""
    tr = _tr(p); w = p.w; parc = p.socle.parc; out = []
    n_m = len(w.menages)
    for i in range(n_m):
        if len(out) >= n: break
        mg = w.menages[i]
        if lieu is not None and mg.domicile.id != lieu: continue
        for k in K3:
            m = int(_cols(p, f"vh_m{k}")[i])
            if m < 0 or CARAC[m].categorie not in categories or (i, k) in tr.ind: continue
            o = individu(p, i, k)
            val = valeur_venale(CARAC[m], (p.jour - int(_cols(p, f"vh_ne{k}")[i])) / JOURS_AN, o.usure)
            fiche = _vider_slot(p, tr, i, k)
            parc.ceder(o, beneficiaire, "requisition")
            tr.fiches[o.id] = fiche
            tr.requisitions[o.id] = (mg, beneficiaire, p.jour, val)
            out.append((o.id, mg, val))
            if len(out) >= n: break
    return out


def restituer_requisition(p, objet_id):
    """Domaine 25 : la requisition est levee : le vehicule revient a son menage ( ou est vendu pour lui )."""
    tr = _tr(p)
    mg, _, _, _ = tr.requisitions.pop(objet_id)
    o = p.socle.parc.objets[objet_id]
    if o.etat != O.SERVICE: p.socle.parc.mettre_en_etat(o, O.SERVICE)
    return rendre(p, o, mg, "fin_de_requisition")
