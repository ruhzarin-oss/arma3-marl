"""PORTES DE LA GUERRE DES ILES, v0 ( ecrites avant la mesure, 26/09 ). Sans Arma : le cote Arma est un jouet.

G1 ZONES : la mission officielle de Malden rend 21 zones dont 2 bases, 405 points par minute sur ses 19 secteurs ;
   la capitale La Trinite est dans un secteur de valeur 30 ; la centrale est rattachee a une zone ( rayon
   d influence ). Controle positif : sans rayon d influence, la centrale est hors de toute zone.
G2 BOURSE : l exemple chiffre ( 10 000 unites de recettes, defense 40 %, 1,15 euro l unite, 50 militaires -> 46
   points ; 1 000 militaires -> 4,6 ) ; une recette negative ne verse rien ; une part de defense hors [0 ; 1] est
   refusee.
G3 RELEVE : la premiere releve rend 0 ; deux jours plus tard, les recettes = la somme de tresor.serie de ces deux jours
   ( au milliardieme ) et jours_clos = 2. Controle : une releve aussitot apres rend 0 et 0 jour.
G4 OCCUPATION ( AMENDEE le 26/09 APRES un echec : la v0 occupait par la quarantaine et mesurait la presence sur le
   lieu ; elle a ECHOUE - presence 1,0 sous occupation - parce qu un paysan qui vit sur sa ferme n a pas a sortir
   pour y travailler. Mecanisme et mesure changes ensemble, voir guerre/moteur.py. Puis fenetre portee a TROIS jours :
   le premier essai du sequestre tombait sur un dimanche et le lundi de Pentecote orthodoxe ( 18/06/2035 ), ou le
   temoin non plus ne livre rien ; on compare donc les fermes LES JOURS OU LE TEMOIN LIVRE ) : sur trois jours
   d occupation, la ferme occupee ne livre AUCUNE ration ( Exploitation.livre_j ), la ferme temoin en livre ; la ferme
   occupee en livrait avant ( controle positif ) et en relivre apres la liberation ( sept jours ) ; l occupation la
   compte parmi ses fermes sous sequestre. La conservation de Malden tient.
G5 HORLOGE ( jouet cote Arma, horloge simulee ) : la zone de Houdan passe a l envahisseur au tour 2 et revient au
   tour 4 -> le moteur la voit occupee apres le tour 2, liberee apres le tour 4 ; les points verses = la formule
   recalculee sur les releves ; une zone ennemie sans lieu n occupe rien.
G6 PONT : lire_tour rend zones et camps d un tour bien forme ; une zone manquante ou inconnue leve Incomplet, jamais
   « a personne » ; un versement negatif ou non fini est refuse avant d etre ecrit.
G7 MISSION : parentheses, crochets, accolades equilibres dans le SQF ; GUERRE_VERSION = arma.VERSION_MISSION ;
   GUERRE_PLAFOND = bourse.PLAFOND_ARMA ; 8 hommes par escouade dans chaque camp.
G8 PASSAGE D ANNEE ( ajoutee le 26/09 avec la correction de d06_etat._cloture ) : une ile seule passe le 1er janvier
   2036 ( jour 200 ) sans planter, et son exercice 2036 s ouvre a la cloture du 31 decembre, pas avant. Elle a su
   echouer : sans la correction, l ile mourait le 31 decembre a 18 h ( ValueError « jour 0 hors de l exercice » ).
G9 SOLDATS SUIVIS ( option 1 de Younes, ecrite avant la mesure ) : apres deux tours ( jouet cote Arma ), chaque ile a
   mobilise 32 soldats, tous vus au front, tous ABSENTS ( poste voyage, dans w.absents ) ; trois soldats de Malden tues
   dans Arma meurent dans le moteur, cause « combat », ne sont plus absents, et Malden compte trois militaires de
   moins ; les 29 autres restent vivants et absents ( controle : les trois etaient vivants juste avant ) ; un releve
   deplace leurs positions ; la conservation de Malden tient le lendemain. Le pont lit U et MORT, refuse un numero
   de front hors [1 ; 999 999].
G10 LA GUERRE COUTE AU TRESOR ( ecrite avant la mesure ) : la premiere releve fixe la base et ne paie rien ; 1 150
   points de plus depenses dans Arma = 115 000 euros d armement importe ( FOB ) plus le fret : la caisse de l Etat
   baisse exactement de ce qui est paye ; le soir, la ligne defense ( achats ) du budget monte d au moins le FOB ; la
   meme depense rendue deux fois ne paie qu une fois ( controle ) ; la conservation de Malden tient.
G11 LE GOUVERNEMENT VOIT LA GUERRE ( ecrite avant la mesure ) : Malden gouvernee par un code sonde, Stratis par les
   regles, deux jours : le code de Malden a recu chaque matin un bulletin avec la section guerre ( soldats au front,
   morts au combat, cout ) et c est lui qui a decide ( evenement decision_gouvernement : cerveau code:... ) ; Stratis
   a decide par les regles, sans une seule bascule « cerveau indisponible ».
G12 LE CONSEIL DE GUERRE ( sans Qwen ; ecrite avant la mesure ) : le scenario lu dans le journal de l essai 9 a des taux
   positifs ; un petit Malden en guerre ( 3 jours ) gouverne par le code de Qwen voit des soldats au front, paie des
   armes, a sa ferme occupee sous sequestre, tient sa conservation et rend une note ; dans un archipel, la releve d un
   gouvernement par le conseil change qui decide des le lendemain ; un code interdit ( import ) est refuse.
G13 VILLES OCCUPEES ( 27/09, ecrite avant la mesure ) : la zone de La Trinite ( capitale et siege du gouvernement )
   occupee trois jours dans un petit Malden : les presents au travail a La Trinite, rapportes a ceux d un lieu temoin
   ( la ferme de Dourdan ; AMENDE apres le premier essai : la ville de Larche, prise d abord, n a aucun emploi dans le
   moteur, 0 present, rapport impossible - La Trinite y tombait de 45 492 a 11 574 ), tombent sous 0,4 fois leur rapport d avant ; ils remontent au-dessus de 0,8 fois apres la liberation ;
   une quarantaine posee par le gouvernement lui-meme ( ailleurs ) reste ; le bulletin dit ville occupee et siege
   occupe ; la conservation tient.
   AMENDEE le 28/09 ( chef de projet ; ecrite avant la mesure ) : la porte echouait a 0,785 pour 0,8 depuis 2a06924
   ( bisection : 0,845 a 7bc0a5d, 0,785 a 2a06924 et a tous les commits d apres, identique au bit ). Le TEMOIN des memes
   jours, sans aucune occupation, donnait 0,781 : les fenetres « avant » ( jours 0 a 2 : samedi, dimanche, lundi de
   Pentecote orthodoxe ) et « liberee » ( jours 6 a 9 ) ne pesent pas les memes jours du calendrier de l agenda, entre
   dans les iles avec 2a06924 ( feries, dimanches, fin de l annee scolaire ) - un artefact de mesure, ni d17 ni d19.
   Nouvelle reference : le temoin apparie ( meme graine, memes jours, sans occupation ) ; occupee sous 0,4 fois le
   rapport du temoin sur les jours d occupation ( controle positif ), liberee au-dessus de 0,8 fois celui du temoin sur
   les jours d apres ; seuils inchanges ; jugee sur la graine neuve 2.
G14 USINES OCCUPEES ( 27/09, AMENDEE avant tout verdict : la premiere version mesurait la fonderie de Larche, mais
   les fonderies de Malden ne produisent RIEN, en paix comme a 10 000 habitants - le controle positif a echoue, rien a
   prouver ; la centrale, elle, produit ) : la zone de la centrale ( centrale01 ) occupee trois jours : ses ouvriers
   presents, rapportes a une ferme temoin hors zone ( Dourdan ), tombent sous 0,4 fois leur rapport d avant ; sa
   production tombe sous 0,5 fois ; tout remonte au-dessus de 0,8 fois apres la liberation. ( Deuxieme essai : ouvriers
   0,75 -> 0,19, mais production 1 216 -> 1 169 par jour, -4 % : le domaine 11 fait produire une centrale selon la demande
   du reseau. L occupation met desormais ses groupes EN PANNE, cause occupation - l etat des pannes du domaine 11.
   Troisieme essai : production 1 216 -> 0 -> 1 184, mais ouvriers 0,56 apres contre 0,75 avant : la fenetre d apres
   ( 4 jours ) contenait un dimanche, pas celle d avant. Fenetres portees a SEPT jours chacune : la meme semaine.
   Quatrieme essai : production 1 184 -> 0 -> 1 171, ouvriers 0,76 -> 0,19 -> 0,19. Sonde : la quarantaine est bien
   levee, mais l agenda ( domaine 5 ) planifie la semaine - les ouvriers reviennent 6 sur 21 le mercredi, les 21 le
   mardi suivant. La reprise se juge donc sur la DEUXIEME semaine apres la liberation. )
G15 LES LEVIERS SUIVENT LA TAILLE DU PAYS ( 27/09, ecrite avant la mesure ) : dans un pays de 2 000 habitants
   ( k = 4 ), le gouvernement peut acheter 8 000 unites de nourriture et pas 8 001 ; il peut relever les credits de
   subventions ( la ligne porte sur ses transferts ) puis verser une subvention qu il n aurait pas pu verser avant.
   ( Sur la vraie Stratis du jour 301, « acheter 100 000 » etait refuse a 2 000 et « fixer_budget subventions » borne
   a 3 000. Les regles plafonnent elles-memes a 2 000 : la porte d identite des domaines dit qu elles ne changent pas.
   AMENDEE apres le premier essai : 8 001 y etait refuse faute de CREDITS de la ligne interieur, pas par la borne - le
   test ne prouvait rien ; les credits sont maintenant larges, et le refus doit etre « achat invalide ». )
G16 L AIDE ALIMENTAIRE ( 27/09, ecrite avant la mesure ) : la vraie Stratis de l essai 15 ( jour 349, 98 % de menages
   sans nourriture, marches vides, reserve vide ) en trois copies ; dans chacune le gouvernement porte ses credits
   interieur ( achats ) a trois fois le vote ; puis il importe 200 000 unites de nourriture destination « reserve »
   dans la premiere, « population » dans la deuxieme, rien dans la troisieme ( le temoin ). Deux jours. Controle
   positif : le temoin a faim ( au moins 50 % chaque jour ). La reserve ne nourrit personne : a 2 points du temoin
   chaque jour. La population, si : au moins 30 points sous le temoin chaque jour. Les deux imports sont acceptes,
   l unite arrive dans le stock vise ; la conservation tient dans la copie aidee. Une autre destination, ou « population »
   pour un autre bien que la nourriture, est refusee.
   ( AMENDEE apres le premier essai : les deux imports etaient « acceptes » et RIEN n arrivait - les reserves de change
   de Stratis sont a -55 millions d euros, le controle des changes ne laisse rien passer, et le moteur ne le disait pas.
   Le refus est maintenant rendu. La porte teste donc le canal avec des devises - les reserves des trois copies sont
   PORTEES a 50 millions d euros, comme un pret d urgence ( le deuxieme essai les AUGMENTAIT de 50 millions : -5,5
   millions, toujours rien ) - et, AVANT, dans la copie aidee, l etat reel : l import est refuse, avec sa raison, et
   rien n entre. AMENDEE apres le troisieme essai : les DEVISES SEULES nourrissent Stratis - le temoin, avec ses 50
   millions et sans aide, passe de 98 % a 46 % puis 0,8 % de faim, parce que les negociants reimportent aussitot ; le
   controle « le temoin a faim chaque jour » ne pouvait plus tenir. Le temoin doit avoir faim AU DEPART, et l aide se
   juge le PREMIER jour : la population au moins 30 points sous le temoin ( 1,6 % contre 46 % ), la reserve a 2 points
   du temoin chaque jour. La famine de Stratis est une crise de devises. )
   REBASEE le 27/09 au soir ( chef de projet ; ecrite avant la mesure ) : la Stratis de l essai 15 portait la dette de
   faim de l ancien modele, et le modele du tronc la solde a la premiere aube ( 48 880 morts de faim sur 100 312, voir
   G20 ) : le temoin du premier jour mesurait un artefact. Le monde est desormais LA famine produite par le code
   d aujourd hui ( voir G20 : les fermes occupees, la banque centrale sans un euro ), copiee en memoire pour chaque bras.
   Les trois copies recoivent le pret d urgence de 50 millions d euros ; l occupation des fermes reste. L aide :
   deux jours de rations pour chaque vivant. Criteres : le temoin a faim au depart ( au moins 30 % ) ; sans devises
   ( l etat produit ), l import est refuse et rien n entre ; avec, les deux imports arrivent dans le stock vise ; la
   reserve ne nourrit personne ( a 2 points du temoin chaque jour ) ; la population, si : le premier jour, au plus la
   moitie de la faim du temoin et au moins 15 points sous lui ; autre destination refusee ; conservation.
G17 UN FOURNISSEUR IMPAYE NE LIVRE PLUS ( 27/09, ecrite avant la mesure ) : un petit archipel, Arma en jouet ; Malden
   ( WEST ) achete pour 1 150 points, et paie ; puis sa banque centrale n a plus de devises et Malden achete 1 150 points
   de plus : le paiement echoue ( 1 150 points impayes ) ; au tour suivant Malden ne recoit AUCUN point, Stratis en
   recoit ( controle ) ; les devises reviennent : l arriere est paye, et au tour d apres Malden recoit de nouveau des
   points. La conservation de Malden tient.
G18 LES CONVOIS A L ECHELLE DE L ILE ( 27/09, ecrite avant la mesure ) : la vraie Stratis de l essai 15 ( 98 % de
   menages sans nourriture, 368 000 rations faites qui attendent un camion dans ses fermes ) en deux copies : le temoin
   garde les convois du moteur ( 60 unites, un par ferme et par heure ) et reste au-dessus de 90 % de faim ; la copie aux
   convois a l echelle de l ile ( 200 ) tombe sous 5 % le premier jour - le stock bloque part ; sa conservation tient ;
   une ile reprise d un instantane d avant le 27/09 recoit l echelle de l archipel.
   ( AMENDEE apres le premier essai : il demandait aussi 5 % le DEUXIEME jour - 11,4 % mesure, puis 100 % au cinquieme :
   les fermes de cette Stratis ne produisent plus, leurs paysans ont une dette de faim de 52 rations, au-dela du seuil
   ou l on ne va plus travailler ( config.ABSENCE_FAIM 1,5 ) et qui ne baisse que d une ration par jour nourri - un autre
   piege, du moteur, rapporte a Younes. Le convoi se juge donc aussi sur une ile NEUVE : une petite Stratis ( echelle
   20, besoin de 10 000 rations par jour, convois du moteur plafonnes a 5 fermes x 24 x 60 = 7 200 ), 30 jours : aux
   convois a l echelle, les rations en attente dans les fermes au jour 30 sont au moins 10 fois moindres que chez le
   temoin, les reserves de change plus hautes, la faim moyenne des jours 21 a 30 pas plus haute d un point.
   AMENDEE apres le deuxieme essai : attente 1 359 contre 21 493, faim 0,99 % contre 1,12 %, mais reserves 32,20 contre
   32,39 millions d euros. La prediction etait fausse, pour une raison reelle, mesuree motif par motif : les fermes du
   temoin, qui ne peuvent pas envoyer leurs rations, vendent plus de grain et d huile a l etranger ( vente_negoce
   +127 000 ), et l ile mieux nourrie importe plus ( import_biens +149 000 ). Les reserves ne mesuraient pas le convoi ;
   le critere est retire. )
   ILE NEUVE RETIREE le 27/09 au soir ( chef de projet ) : depuis 2a06924 ( la fusion du tronc ca0765b : les 27 domaines
   dans les iles ), la recolte appartient au domaine 9 et son fret au domaine 15 ; monde.expedier ne lance plus un seul
   convoi de ferme et le plafond CAPACITE_CAMION x echelle_convois ne sert qu aux mondes sans eux - les deux bras etaient
   identiques au bit ( 12 613 et 12 613 ), l attente ne mesurait plus rien. Le fret des recoltes se juge en G24.
   REBASEE le 27/09 au soir ( chef de projet ) : la partie « vraie Stratis » est RETIREE - son temoin se jugeait apres la
   premiere aube, qui solde la dette de faim de l ancien modele ( 48 880 morts, voir G20 ) ; le goulot des convois est
   prouve sur l ile neuve. Reste de la vraie Stratis : une ile reprise d un instantane d avant le 27/09 recoit l echelle
   de l archipel ( chargee, sans jouer un jour ).
G20 LA VRAIE STRATIS AFFAMEE REPART ( 27/09, ecrite avant la mesure ; sur la faim du TRONC depuis la fusion de ca0765b :
   adaptation du corps de 40 %, travail jusqu a 12 rations de deficit, un jour nourri en repare 1, mort de faim au
   domaine 1 par SEUILS_FAIM - la loi et ses controles sont les portes du domaine 1 ) : la Stratis de l essai 15, reprise
   avec l echelle des convois, voit ses fermes relivrer dans les 8 jours et moins de 10 % de faim le huitieme ; la
   conservation tient. ( Historique : le premier essai a ECHOUE, ses paysans ne mangeaient pas le grain de leur ferme -
   l autoconsommation est ajoutee au domaine 9 ; le deuxieme lisait livre_j apres sa remise a zero de 6 h 40, un bogue
   du test. Avec la faim de la branche, avant la fusion : fermes au jour 7, faim 1,6 % au jour 8, 13 012 morts de faim. )
   AMENDEE le 27/09 au soir APRES mesure ( chef de projet ; plus severe, pas plus facile ) : sur le tronc, la Stratis de
   l essai 15 perd 48 880 habitants de faim sur 100 312 a la premiere aube - ses 98 % de menages au-dela du seuil de mort
   viennent de l ancien modele ( famine sans morts, fuite de devises ) et le modele du tronc les solde d un coup : un
   artefact de transition, et la faim tombait sous 10 % parce que les affames etaient morts. Nouveau critere, ecrit avant
   la prochaine mesure : les fermes relivrent en 8 jours, la faim passe sous 10 % le huitieme jour, ET les morts de faim
   de ces 8 jours restent sous 1 % des vivants du depart ( premiere borne, a calibrer : l IPC classe une zone en famine
   au-dela de 2 deces pour 10 000 par jour, soit 0,16 % en 8 jours - IPC, Guidance Note on Famine ). Nouveau monde : plus
   l instantane de l essai 15, mais une famine produite par le code d aujourd hui ( apres HMT-131 a et b ) : une Stratis
   stressee ( reserves a zero, importations coupees ) jusqu a la famine, puis relachee, et la reprise mesuree - les morts
   viennent au fil des jours. Hors de la porte ( --sans G20 ) tant que d01._placer n est pas corrige ( HMT-130 ).
   PRECISEE apres l essai du blocus seul ( 27/09, 23 h 40 ) : 60 jours sans un euro de devises n affament pas une Stratis
   neuve ( faim au plus 3,9 % au jour 31, aucun mort ) - l ile se nourrit de ses fermes. La famine vient donc de la
   cause de la guerre : les fermes OCCUPEES ( guerre/moteur.occuper, toutes les fermes de l ile ) ET la banque centrale
   sans un euro ; la relache leve les deux ; le controle positif garde les deux.
   LIMITE ( chef de projet ) : cette famine est COURTE ( 30 % de faim en 6 jours, aucun mort ) : le critere « morts de faim
   sous 1 % » y est tenu d office. La reprise apres une famine LONGUE, des habitants pres du seuil de mort, n est pas
   testee ici : une porte a part, a venir.
G21 LE REVENU MINIMUM GARANTI ( KEA, 27/09, ecrite avant la mesure ) : dans une petite Stratis, un versement du jour
   donne a chaque menage eligible exactement le seuil du jour ( 216 euros par mois a l echelle 1 + 0,5 par adulte de plus
   + 0,25 par enfant ) moins son revenu lisse hors KEA ; rien a un menage au-dessus du seuil ni a un menage aux avoirs
   au-dessus de la limite ; la caisse de l Etat baisse de la somme versee ; rien sans revenu_minimum. Sur 60 jours ( une
   petite Stratis a l echelle 20 ), la faim moyenne des jours 51 a 60 baisse d au moins un quart avec le
   KEA. ( Depuis la fusion ( chef de projet, 27/09 ) : le KEA n est branche dans aucun monde ; la porte le branche dans
   son petit monde pour juger le versement ; l effet sur 200 jours - 18,1 % de faim contre 8,4 % sans, le prix a 9,4 -
   est RETIRE en attendant la correction des prix du domaine 3 dans le tronc, et sera remesure alors. AMENDEE apres le
   premier essai : aucun menage n etait eligible - le plancher du KEA, 216 euros par mois, 6,3
   drachmes par jour, est sous les salaires, les pensions ( 20 par jour ) et les indemnites du moteur, et le revenu lisse
   sur 60 jours ne tombe sous lui que des mois apres la perte d un revenu. Le versement se juge sur soixante menages
   rendus eligibles a la main ; l effet sur la faim sur 200 jours, les 20 derniers, au meme seuil. )
   AMENDEE le 27/09 APRES avoir vu la mesure ( chef de projet ) : le critere etait ecrit sur un seul monde ; sur le
   tronc 12d226b, les graines 1 a 4 ( exploration, au rapport ) donnaient -20, -25, -36 et -48 % ( 8,8 % contre 13,4 % en
   moyenne ). Nouveau critere, juge sur 4 graines NEUVES ( 5 a 8 ) : petite Stratis a l echelle 20, 200 jours, la faim
   moyenne des jours 181 a 200 avec le KEA, appariee graine par graine a celle sans, baisse en moyenne d au moins 25 % ET
   baisse sur chaque graine ; montant inchange. Reserve : l effet grandit avec la derive de la faim de base ( -20 % a une
   base de 10 %, -48 % a 17 % ) ; a remesurer apres le correctif du moteur ( HMT-124 ).
G24 LE FRET DES RECOLTES ( 27/09 au soir, ecrite avant la mesure ; remplace l ile neuve de G18 ) : une Stratis neuve
   ( graine 1, echelle 20 ), 30 jours, releve chaque jour a midi : la couverture du marche de la capitale ( jours de
   demande lissee, d15.couverture ) et les vivres aux fermes ( rations pretes dans les fermes du moteur, en jours de la
   meme demande ). Un jour « bloque » : le marche tient moins d un jour ET les fermes plus de dix. Des jours 5 a 30 ( le
   demarrage exclu ) : aucune suite de plus de 2 jours bloques - la nourriture arrive au marche en 2 jours quand il en
   manque et que les fermes en ont. Controle positif : le fret du domaine 15 coupe ( sa routine _expedier ne lance plus
   rien ; les lots en route arrivent ) : la porte echoue. Une vraie suite de jours bloques est un goulot, pour la session
   du moteur ( d09 et d15 ).
   AMENDEE le 28/09 ( chef de projet ; ecrite avant la mesure ) : sur la graine 1, le bras libre passait ( 0 jour bloque )
   mais le controle positif ne savait pas echouer - fret coupe 30 jours, les rations pretes aux fermes ne montaient qu a
   3,7 jours, jamais au-dela de 10, et le marche restait nourri ( negoce, autoconsommation ). Les « greniers pleins »
   ( 2,4 millions de kg par ferme ) sont la recolte BRUTE du domaine 9, pas des rations bloquees. Nouveau critere : les
   rations pretes aux fermes ne depassent pas 2 jours de demande, chaque jour des jours 5 a 30 ( libre : 1,1 au plus sur
   la graine 1 ; coupe : 3,7 ). Jugee sur la graine neuve 2 ; la porte n est valide que si le bras libre PASSE et le bras
   au fret coupe ECHOUE.
G23 LES REFUS D HIER ( 27/09, ecrite avant la mesure ) : une decision du gouvernement de Malden avec une action refusee
   ( et sa raison ) ; le lendemain matin, le code qui gouverne recoit dans son bulletin la section refus_hier avec cette
   action et cette raison ; sans refus la veille, la liste est vide ( controle ).
G19 L AVIS AUX VOYAGEURS ( 27/09, ecrite avant la mesure ) : a l ouverture de la guerre ( jouet cote Arma ), le
   tourisme de Malden ( champ de bataille ) passe au risque 0,15 et celui de Stratis ( belligerante ) a 0,5 ; deux jours
   plus tard, les recettes touristiques de Malden sont sous 20 % de celles d un Malden en paix ( meme graine ).

   python -m guerre.porte_guerre"""
import math, os, re, sys, time
from . import bourse as B, zones as Z, arma as A, moteur as GM
from .horloge import HorlogeDeGuerre

MISSION = os.path.join(Z.ICI, "mission", "GuerreIles.Malden")
OCCUPEE, TEMOIN = "Malden_V_Houdan", "Malden_V_Dourdan"


def livraisons(arc, ile, lieux, jours):
    """Jour par jour du moteur : pour chaque ferme, le plus grand livre_j du jour ( rations livrees ce jour-la )."""
    from monde.pays import d09_agriculture as AG
    p = arc.iles[ile].w.pays
    out = []
    for _ in range(jours):
        best = {l: 0.0 for l in lieux}
        for _ in range(144):
            arc.un_pas()
            for l in lieux: best[l] = max(best[l], AG.exploitation_de(p, l).livre_j)
        out.append(best)
    return out


def couverture(w, zones):
    """Pour chaque zone : ses fermes ( sequestre ), ses sites du moteur ( choc ), ses sites non couverts."""
    p = w.pays; out = {"fermes": 0, "moteur": 0, "non_couverts": []}
    for z in zones:
        for l in z["lieux"]:
            e = w.entreprises.get(l)
            if e is None: continue
            dom = p.repris.get(e.id)
            if dom == "agriculture": out["fermes"] += 1
            elif dom is None: out["moteur"] += 1
            else: out["non_couverts"].append(f"{l}:{dom}")
    return out


def sqf_equilibre(texte):
    """Parentheses, crochets et accolades equilibres, chaines et commentaires // retires."""
    s = re.sub(r'"(?:[^"]|"")*"', '""', texte)
    s = re.sub(r"//[^\n]*", "", s)
    pile, paires = [], {")": "(", "]": "[", "}": "{"}
    for c in s:
        if c in "([{": pile.append(c)
        elif c in ")]}":
            if not pile or pile.pop() != paires[c]: return False
    return not pile


class Scenario(A.FauxGuerre):
    """Le jouet, avec des changements de proprietaire au debut de certains tours."""
    def __init__(self, zones, script):
        super().__init__(zones); self.script = script

    def tour(self, points, reserves=None):
        for n, camp in self.script.get(self.tours + 1, {}).items(): self.proprio[n] = camp
        return super().tour(points, reserves)


INSTANTANE_AIDE = "/mnt/data/hmt/guerre/essai15/instantane"


def _aide(dest):
    """G16 : une copie de la famine produite ( les fermes restent occupees ), le pret d urgence, l import d aide ( ou rien ),
    deux jours. L aide : deux jours de rations pour chaque vivant."""
    import pickle
    from monde.archipel import Ile
    from monde import tests as T
    from monde.pays import d06_etat as ET, d07_exterieur as X
    w = pickle.loads(famine_produite()[0]); p = w.pays; ile = Ile("Stratis", w)
    q = 2.0 * int(w.table.vivant[:w.table.n].sum()) * __import__("monde.config", fromlist=["x"]).NOURRITURE_PAR_JOUR
    bu = ET._etat(p).budget
    r = {"credits": ET.appliquer(p, {"type": "fixer_budget", "ligne": "interieur", "montant": 3.0 * bu.votes[("interieur", "achats")]}),
         "faim0": round(GM.faim(w), 4), "q": q}
    if dest == "population":
        s0 = w.publics["population"]["nourriture"]
        r["sans_devises"] = ET.appliquer(p, {"type": "importer", "bien": "nourriture", "quantite": q, "destination": dest})
        r["sans_devises_arrive"] = round(w.publics["population"]["nourriture"] - s0)
    X.reserves_de_change(p); X._ext(p).reserves_euros = 5e7
    if dest is not None:
        s0 = (w.publics["reserve"]["nourriture"], w.publics["population"]["nourriture"])
        r["import"] = ET.appliquer(p, {"type": "importer", "bien": "nourriture", "quantite": q, "destination": dest})
        r["arrive"] = (round(w.publics["reserve"]["nourriture"] - s0[0]), round(w.publics["population"]["nourriture"] - s0[1]))
    if dest == "population":
        r["refus"] = [ET.appliquer(p, {"type": "importer", "bien": "nourriture", "quantite": 10, "destination": "armee"}),
                      ET.appliquer(p, {"type": "importer", "bien": "remedes", "quantite": 10, "destination": "population"})]
    r["faim"] = []
    for _ in range(2):
        T.jours(w, 1); r["faim"].append(round(ile.commande("etat")["faim"], 4))
    r["conservation"] = bool(p.socle.conservation.tenue()[0])
    return r


def _echelle_a_la_reprise():
    """G18 : une ile reprise d un instantane d avant le 27/09 recoit l echelle de l archipel - chargee, sans jouer un jour."""
    from monde.archipel import _convois as poser, charger
    w = charger(os.path.join(INSTANTANE_AIDE, "Stratis.pkl"))
    avant = "echelle_convois" in vars(w)
    poser(w, 200.0)
    return {"deja": avant, "echelle": w.echelle_convois}


def _g13(occuper, graine):
    """G13 : un petit Malden ( graine donnee ), La Trinite occupee du jour 3 au jour 6 ( ou non : le temoin apparie ) ;
    les presents au travail a La Trinite et a Dourdan, avant ( jours 0 a 2 ), pendant ( 3 a 5 ), apres ( 6 a 9 )."""
    from monde import population as PO13
    from monde.archipel import Archipel
    carte = Z.carte_de_guerre(open(os.path.join(MISSION, "mission.sqm"), encoding="latin-1").read(), "Malden")
    zs = carte["zones"]
    arc13 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False, graine=graine)
    w13 = arc13.iles["Malden"].w; t13 = w13.table
    zt = next(z["n"] for z in zs if "Malden_C_LaTrinite" in z["lieux"]); lt = next(z["lieux"] for z in zs if z["n"] == zt)
    kt, kl = w13.carte.lieux["Malden_C_LaTrinite"].n, w13.carte.lieux["Malden_V_Dourdan"].n
    w13.gouv.lois.setdefault("quarantaine", []).append("Malden_V_Goisse")       # la quarantaine du gouvernement, ailleurs
    def au_travail(jours):
        tot = [0, 0]
        for _ in range(jours * 144):
            arc13.un_pas(); n13 = t13.n
            at = (t13.vivant[:n13] == 1) & (t13.poste[:n13] == PO13.CODE_POSTE["travail"])
            tot[0] += int((at & (t13.lieu[:n13] == kt)).sum()); tot[1] += int((at & (t13.lieu[:n13] == kl)).sum())
        return tot
    av = au_travail(3)
    if occuper: arc13.commande("Malden", "occuper", zt, lt, True)
    b13 = GM.bulletin_guerre(w13)
    pe = au_travail(3)
    if occuper: arc13.commande("Malden", "occuper", zt, lt, False)
    ap = au_travail(4)
    gv = "Malden_V_Goisse" in w13.gouv.lois["quarantaine"] and "Malden_C_LaTrinite" not in w13.gouv.lois["quarantaine"]
    tenue = bool(arc13.commande("Malden", "tenue")[0])
    arc13.fermer()
    return {"av": av, "pe": pe, "ap": ap, "gv": gv, "tenue": tenue, "villes": b13["villes_occupees"], "siege": b13["siege_du_gouvernement_occupe"]}


def _monde_de_g14():
    """G14 joue dans le monde ou jouait G13 avant son amendement du 28/09 : un petit Malden ( graine du moteur ), la
    quarantaine du gouvernement a Goisse, La Trinite occupee du jour 3 au jour 6 puis liberee, 10 jours ; rejoue a
    l identique pour que G14 ne change pas."""
    from monde.archipel import Archipel
    carte = Z.carte_de_guerre(open(os.path.join(MISSION, "mission.sqm"), encoding="latin-1").read(), "Malden")
    zs = carte["zones"]
    arc = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    w = arc.iles["Malden"].w
    zt = next(z["n"] for z in zs if "Malden_C_LaTrinite" in z["lieux"]); lt = next(z["lieux"] for z in zs if z["n"] == zt)
    w.gouv.lois.setdefault("quarantaine", []).append("Malden_V_Goisse")
    for _ in range(3 * 144): arc.un_pas()
    arc.commande("Malden", "occuper", zt, lt, True); GM.bulletin_guerre(w)
    for _ in range(3 * 144): arc.un_pas()
    arc.commande("Malden", "occuper", zt, lt, False)
    for _ in range(4 * 144): arc.un_pas()
    return arc, w, w.table


def _fret_recoltes(couper=False, jours=30, graine=2):
    """G24 : une Stratis neuve, 30 jours ; chaque midi, la couverture du marche de la capitale et les vivres prets aux
    fermes, en jours de sa demande lissee. `couper` : la routine de fret du domaine 15 ne lance plus rien."""
    from monde.archipel import creer_ile
    from monde.pays import d15_logistique as LG
    ancien = LG._expedier
    if couper: LG._expedier = lambda p, h: LG._avancer_lots(p, LG._lg(p))
    try:
        w = creer_ile("Stratis", graine, 20.0); p = w.pays
        mid = w.carte.gouvernement.marche.id if getattr(w.carte.gouvernement, "marche", None) is not None else next(iter(w.marches))
        fermes = [e for e in w.entreprises.values() if e.type == "ferme"]
        cov, stock_fermes, bloque = [], [], []
        for j in range(jours):
            for k in range(144):
                w.pas_suivant()
                if k == 6 * 6 - 1:                                    # midi ( le jour commence a 6 h )
                    dem = LG._demande(p, mid, "nourriture")
                    c = LG.couverture(p, mid, "nourriture"); sf = sum(e.stocks.get("nourriture", 0.0) for e in fermes) / dem
                    cov.append(round(c, 2)); stock_fermes.append(round(sf, 1)); bloque.append(j >= 4 and c < 1.0 and sf > 10.0)
        suite = plus = 0
        for x in bloque:
            suite = suite + 1 if x else 0; plus = max(plus, suite)
        return {"plus_longue_suite_bloquee": plus, "jours_bloques": sum(bloque), "fermes_max_j5_30": max(stock_fermes[4:]),
                "couverture": cov[::3], "fermes_en_jours": stock_fermes[::3],
                "conservation": bool(p.socle.conservation.tenue()[0])}
    finally:
        LG._expedier = ancien


def _neuve(echelle_convois):
    """G18 : une petite Stratis neuve ( echelle 20 ), 30 jours, a l echelle de convois donnee."""
    from monde.archipel import creer_ile, Ile
    from monde import tests as T
    from monde.pays import d07_exterieur as X
    w = creer_ile("Stratis", 1, 20.0); w.echelle_convois = float(echelle_convois); ile = Ile("Stratis", w); f = []
    for _ in range(30):
        T.jours(w, 1); f.append(ile.commande("etat")["faim"])
    attente = sum(e.stocks.get("nourriture", 0.0) for e in w.entreprises.values() if e.type == "ferme")
    return {"attente": round(attente), "reserves": round(X.reserves_de_change(w.pays)[0]), "faim_21_30": round(sum(f[20:]) / 10, 4),
            "conservation": bool(w.pays.socle.conservation.tenue()[0])}


ZONE_FAMINE = 99                                   # la zone fictive qui occupe toutes les fermes de l ile
_FAMINE = {}


def famine_produite(graine=1, echelle=20.0, faim_visee=0.30, blocus_max_j=60):
    """LA famine des portes G16 et G20 ( 27/09 ), produite par le code d aujourd hui : une Stratis neuve joue 10 jours ;
    puis toutes ses fermes sont occupees et, chaque matin, la banque centrale n a plus un euro ( reserves au plancher ),
    jusqu a ce que la faim atteigne `faim_visee` ( au plus `blocus_max_j` jours ). Rend ( l ile en octets, le suivi ) :
    chaque bras la recopie en memoire. Produite une fois par processus."""
    cle = (graine, echelle, faim_visee, blocus_max_j)
    if cle in _FAMINE: return _FAMINE[cle]
    import pickle
    from monde.archipel import creer_ile, Ile
    w = creer_ile("Stratis", graine, echelle); ile = Ile("Stratis", w)
    for _ in range(10): _jour_de_famine(w, ile, False)
    fermes = sorted(l for l, x in w.entreprises.items() if x.type == "ferme")
    GM.occuper(w, ZONE_FAMINE, fermes, True)
    blocus = []
    while len(blocus) < blocus_max_j and (not blocus or blocus[-1] < faim_visee): blocus.append(_jour_de_famine(w, ile, True))
    _FAMINE[cle] = (pickle.dumps(w, protocol=pickle.HIGHEST_PROTOCOL), {"blocus_jours": len(blocus), "faim_blocus": blocus, "fermes": fermes})
    return _FAMINE[cle]


def _jour_de_famine(w, ile, blocus):
    from monde.pays import d07_exterieur as X
    p = w.pays; e = X._ext(p)
    for k in range(144):
        if blocus and k == 0: X.reserves_de_change(p); e.reserves_euros = X.PLANCHER_RESERVES
        w.pas_suivant()
    return round(ile.commande("etat")["faim"], 4)


def _morts_de_faim(w):
    from monde.pays import d01_population as D1
    col = w.pays.colonnes["habitant"]; n = w.table.n
    return int(((col["cause_deces"][:n] == D1.CAUSES.index("faim")) & (col["deces_j"][:n] >= 0)).sum())


def _faim_produite(relacher=True, reprise_j=8):
    """G20 : la famine produite, relachee ( occupation levee, devises revenues ) ou non ( le controle positif ), et la
    reprise mesuree `reprise_j` jours : la faim, les livraisons des fermes, les morts de faim, la conservation."""
    import pickle
    from monde.archipel import Ile
    octets, suivi = famine_produite()
    w = pickle.loads(octets); p = w.pays; A = p.domaine("agriculture"); ile = Ile("Stratis", w); tb = w.table
    if relacher: GM.occuper(w, ZONE_FAMINE, suivi["fermes"], False)
    v0, m0 = int(tb.vivant[:tb.n].sum()), _morts_de_faim(w)
    f, livre = [], []
    for _ in range(reprise_j):
        f.append(_jour_de_famine(w, ile, not relacher)); livre.append(round(A.serie[-1][1]) if A.serie else 0)
    return {"blocus_jours": suivi["blocus_jours"], "faim_blocus": suivi["faim_blocus"][-1], "faim": f, "livre": livre,
            "vivants0": v0, "morts_de_faim_reprise": _morts_de_faim(w) - m0, "conservation": bool(p.socle.conservation.tenue()[0])}


def g20_passe(r):
    return (max(r["livre"]) > 0 and r["faim"][-1] <= 0.10 and r["morts_de_faim_reprise"] < 0.01 * r["vivants0"]
            and r["conservation"])


SANS = ()                                          # les portes sautees : python -m guerre.porte_guerre --sans G20


def main():
    global SANS
    if "--sans" in sys.argv: SANS = tuple(sys.argv[sys.argv.index("--sans") + 1].split(","))
    ok = {}
    if not os.path.exists(os.path.join(MISSION, "mission.sqm")):
        from . import fabriquer_mission as FM
        print(f"   mission.sqm de Bohemia lu dans le jeu ( empreinte {FM.fabriquer()} )", flush=True)
    sqm = open(os.path.join(MISSION, "mission.sqm"), encoding="latin-1").read()
    carte = Z.carte_de_guerre(sqm, "Malden")
    zs = carte["zones"]
    sect = [z for z in zs if z["genre"] == "secteur"]
    zone_de = {l: z["n"] for z in zs for l in z["lieux"]}
    # G1
    lt = next(z for z in zs if "Malden_C_LaTrinite" in z["lieux"])
    lieux = __import__("json").load(open(os.path.join(Z.PAYS, "malden.json")))["lieux"]
    _, hors0 = Z.rattacher(zs, lieux, rayon=0.0)
    ok["G1 21 zones, 2 bases, 405 points par minute"] = (len(zs) == 21 and len(sect) == 19 and sum(z["valeur"] for z in sect) == 405)
    ok["G1 La Trinite dans un secteur de valeur 30"] = lt["genre"] == "secteur" and lt["valeur"] == 30
    ok["G1 la centrale rattachee ; controle : hors zone sans rayon"] = ("centrale01" in zone_de) and ("centrale01" in hors0)
    # G2
    p50, f50, _ = B.points_de_la_minute(10000, 0.4, 1.15, 50)
    p1000, f1000, _ = B.points_de_la_minute(10000, 0.4, 1.15, 1000)
    pneg, _, _ = B.points_de_la_minute(-5000, 0.4, 1.15, 50)
    try: B.points_de_la_minute(1, 1.5, 1.15, 1); refuse = False
    except ValueError: refuse = True
    ok["G2 bourse : 46 et 4,6 points, rien sur recette negative, part hors bornes refusee"] = (
        abs(p50 - 46.0) < 1e-9 and abs(p1000 - 4.6) < 1e-9 and f1000 == 0.1 and pneg == 0.0 and refuse)
    # G3, G4, G5 : un petit archipel Malden + Stratis, sequentiel ( on lit les iles de l interieur )
    from monde.archipel import Archipel
    t0 = time.time()
    arc = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    w = arc.iles["Malden"].w
    r0 = arc.commande("Malden", "guerre_releve")
    arc.jours(2)
    r2 = arc.commande("Malden", "guerre_releve")
    serie = [s for s in GM._etat(w).tresor.serie]
    attendu = math.fsum(s[1] for s in serie[-2:])
    r2b = arc.commande("Malden", "guerre_releve")
    ok["G3 releve : 0 au depart, puis la somme des deux jours ; controle aussitot apres = 0"] = (
        r0["recettes"] == 0 and r0["jours_clos"] == 0 and r2["jours_clos"] == 2 and abs(r2["recettes"] - attendu) <= 1e-9 * max(1, abs(attendu))
        and r2b["recettes"] == 0 and r2b["jours_clos"] == 0)
    print(f"   releve : {r2['recettes']:.0f} {r2['monnaie']} en 2 jours, defense {r2['part_defense']:.3f}, {r2['militaires']} militaires", flush=True)
    # G4
    print(f"   couverture des zones de Malden : {couverture(w, zs)}", flush=True)
    zo = zone_de[OCCUPEE]
    lz = next(z["lieux"] for z in zs if z["n"] == zo)
    avant = livraisons(arc, "Malden", (OCCUPEE, TEMOIN), 3)
    occ = arc.commande("Malden", "occuper", zo, lz, True)
    pendant = livraisons(arc, "Malden", (OCCUPEE, TEMOIN), 3)
    arc.commande("Malden", "occuper", zo, lz, False)
    apres = livraisons(arc, "Malden", (OCCUPEE, TEMOIN), 7)
    tenue = arc.commande("Malden", "tenue")
    r = lambda js: [(round(j[OCCUPEE]), round(j[TEMOIN])) for j in js]
    print(f"   rations livrees par jour ( occupee, temoin ) : avant {r(avant)}, occupee {r(pendant)}, liberee {r(apres)}", flush=True)
    jours_temoin = lambda js: [j for j in js if j[TEMOIN] > 0]
    ok["G4 controle positif : les jours ou le temoin livre, la ferme livrait avant l occupation"] = (
        bool(jours_temoin(avant)) and all(j[OCCUPEE] > 0 for j in jours_temoin(avant)))
    ok["G4 occupee : la ferme sous sequestre ne livre rien, le temoin livre"] = (
        all(j[OCCUPEE] == 0 for j in pendant) and bool(jours_temoin(pendant)) and occ["fermes"] == [OCCUPEE])
    ok["G4 liberee : les jours ou le temoin livre, la ferme relivre"] = (
        bool(jours_temoin(apres)) and all(j[OCCUPEE] > 0 for j in jours_temoin(apres)))
    ok["G4 conservation de Malden"] = bool(tenue[0])
    # G5
    vide = next(z["n"] for z in sect if not z["lieux"])
    horloge = iter(x / 432.0 for x in range(10 ** 8))          # 432 pas du moteur ( 3 jours ) par periode d une seconde simulee
    arma = Scenario(zs, {2: {zo: "EAST", vide: "EAST"}, 4: {zo: "WEST"}})
    h = HorlogeDeGuerre(arc, arma, carte, periode_s=1.0, horloge=lambda: next(horloge)).ouvrir()
    vus, tours = [], []
    for _ in range(4):
        h.boucle(tours=h.tours + 1)
        vus.append(sorted(getattr(arc.iles["Malden"].w, "occupations", {})))      # lu sans releve : une releve de plus volerait des recettes
        tours.append(h.derniere)
    ok["G5 occupee apres le tour 2, liberee apres le tour 4, zone vide jamais occupee"] = (
        vus[0] == [] and vus[1] == [zo] and vus[2] == [zo] and vus[3] == [])
    formule = all(abs(B.points_de_la_minute(r["recettes"], r["part_defense"], r["euros_par_unite"], r["militaires"])[0]
                      - l["points"][r["camp"]]) < 1e-9 for l in tours for r in l["iles"].values())
    somme = all(abs(arma.verse[c] - math.fsum(l["points"][c] for l in tours)) < 1e-6 for c in ("EAST", "WEST"))
    ok["G5 les points verses suivent la formule, et Arma a recu leur somme"] = formule and somme
    print(f"   horloge : {h.tours} tours ; points par tour {[{c: round(v, 1) for c, v in l['points'].items()} for l in tours]} ; "
          f"jours du moteur par tour {[l['iles']['Malden']['jours_clos'] for l in tours]}", flush=True)
    arc.fermer()
    # G6
    bonnes = [("VERSE", [0, 10.0, 10.0]), ("VERSE", [1, 20.0, 20.0])] + \
             [("ZONE", [round(z["x"]), round(z["y"]), 1 if z["n"] != zo else 0]) for z in zs] + \
             [("FORCES", [0, 8, 1, 0, 1150, 1]), ("FORCES", [1, 16, 2, 3, 2300, 2]), ("CIBLE", [0, 7102, 6096]),
              ("CIBLE", [1, -1, -1]), ("TEMPS", [120])]
    t = A.lire_tour(bonnes, zs)
    manque = [l for l in bonnes if not (l[0] == "ZONE" and l[1][0] == round(zs[3]["x"]))]
    inconnue = bonnes + [("ZONE", [100, 100, 0])]
    def leve(lignes):
        try: A.lire_tour(lignes, zs); return False
        except A.AL.Incomplet: return True
    def refuse_versement(p):
        try: A.corps_du_tour(p); return False
        except A.AL.Refus: return True
    ok["G6 tour bien forme lu ; zone manquante ou inconnue -> Incomplet ; versement invalide refuse"] = (
        t["zones"][zo] == "EAST" and t["camps"]["WEST"]["vivants"] == 16 and t["camps"]["WEST"]["cible"] is None
        and leve(manque) and leve(inconnue) and refuse_versement({"EAST": -1}) and refuse_versement({"WEST": float("nan")})
        and "//" not in A.corps_du_tour({"EAST": 1.5, "WEST": 2}))
    v, m = A.lire_positions([("U", [1, 7, 3000, 7000, 0.25]), ("U", [0, 9, 5000, 11000, 0.0]), ("MORT", [1, 4])])
    def refuse_numero(k):
        try: A.corps_du_tour({"EAST": 1}, {"EAST": [k]}); return False
        except A.AL.Refus: return True
    ok["G9 pont : U et MORT lus, numero de front hors bornes refuse"] = (
        v["WEST"] == [(7, 3000, 7000, 0.25)] and v["EAST"] == [(9, 5000, 11000, 0.0)] and m == {"EAST": [], "WEST": [4]}
        and refuse_numero(0) and refuse_numero(1_000_000)
        and A.corps_du_tour({"EAST": 1, "WEST": 2}, {"EAST": [1, 2], "WEST": []}) == "[1.000, 2.000, [1, 2], []] call GUERRE_fnc_tour2;")
    # G7
    fn = open(os.path.join(MISSION, "fonctions.sqf")).read()
    ini = open(os.path.join(MISSION, "initServer.sqf")).read()
    sv = open(os.path.join(MISSION, "suivi.sqf")).read()
    dc = open(os.path.join(MISSION, "doctrine.sqf")).read()
    version = int(re.search(r"GUERRE_VERSION = (\d+);", fn).group(1))
    plafond = int(re.search(r"GUERRE_PLAFOND = (\d+);", fn).group(1))
    escouades = re.search(r"GUERRE_ESCOUADE = \[(.*?)\];", fn, re.S).group(1)
    tailles = [len(re.findall(r'"[^"]+"', b)) for b in re.findall(r"\[([^\[\]]*)\]", escouades)]
    ok["G7 SQF equilibre, version, plafond, escouades de 8"] = (
        sqf_equilibre(fn) and sqf_equilibre(ini) and sqf_equilibre(sv) and "//" not in sv and sqf_equilibre(dc) and "//" not in dc and version == A.VERSION_MISSION and plafond == B.PLAFOND_ARMA
        and tailles == [8, 8])
    # G8
    from monde.archipel import creer_ile
    from monde import tests as T
    w8 = creer_ile("Malden", 1, 4.0); e8 = w8.pays.domaine("etat"); vus = []
    w8.pays.cloture("porte_guerre", lambda p, c: vus.append((p.jour, e8.fisc.debut)))
    try:
        T.jours(w8, 205); plante = None
    except Exception as ex: plante = f"{type(ex).__name__} au jour {w8.jour} : {ex}"
    ouvert = next((j for j, d in vus if d == 200), None)
    print(f"   passage d annee : {plante or 'aucun plantage jusqu au jour ' + str(w8.jour)} ; exercice 2036 ouvert a la cloture vue au jour {ouvert}", flush=True)
    ok["G8 le 1er janvier passe, l exercice s ouvre a la cloture du 31 decembre"] = plante is None and ouvert == 200
    # G9
    from monde.pays import d01_population as POP1
    from monde import population as PO
    arc9 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    faux = A.FauxGuerre(zs)
    h9_t = iter(x / 432.0 for x in range(10 ** 8))
    h9 = HorlogeDeGuerre(arc9, faux, carte, periode_s=1.0, periode_suivi_s=1 / 6.0, horloge=lambda: next(h9_t)).ouvrir()
    h9.boucle(tours=2); h9.suivre_soldats()
    w9 = arc9.iles["Malden"].w; t9 = w9.table
    f9 = w9.guerre_front
    b9 = {ile: arc9.commande(ile, "guerre_releve")["front"] for ile in ("Malden", "Stratis")}
    absents = all(t9.statut[s["i"]] == PO.ABSENT and t9.poste[s["i"]] == PO.CODE_POSTE["voyage"] and s["i"] in w9.absents for s in f9.values())
    mil0 = GM.militaires(w9)
    tues = sorted(faux.soldats["WEST"])[:3]
    vivants_avant = all(t9.vivant[f9[k]["i"]] == 1 for k in tues)
    pos_avant = {k: (f9[k]["x"], f9[k]["y"]) for k in f9}
    for k in tues: faux.tuer("WEST", k)
    for k in list(faux.soldats["WEST"])[:5]: faux.soldats["WEST"][k] = (1234.0, 4321.0)
    h9.suivre_soldats()
    cause = w9.pays.colonnes["habitant"]["cause_deces"]
    morts_ok = all(t9.vivant[f9[k]["i"]] == 0 and cause[f9[k]["i"]] == POP1.CAUSES.index("combat") and f9[k]["i"] not in w9.absents
                   and f9[k]["etat"] == "mort" for k in tues)
    restent = [s for k, s in f9.items() if k not in tues]
    restent_ok = len(restent) == 29 and all(t9.vivant[s["i"]] == 1 and t9.statut[s["i"]] == PO.ABSENT for s in restent)
    bouges = sum(1 for k, s in f9.items() if k not in tues and (s["x"], s["y"]) != pos_avant[k])
    mil1 = GM.militaires(w9)
    arc9.jours(1); tenue9 = arc9.commande("Malden", "tenue")
    print(f"   soldats suivis : front {b9} ; militaires de Malden {mil0} -> {mil1} ; {bouges} positions deplacees", flush=True)
    ok["G9 32 soldats par ile mobilises, vus au front, absents"] = (
        b9["Malden"] == {"reserve": 0, "front": 32, "mort": 0} and b9["Stratis"] == {"reserve": 0, "front": 32, "mort": 0} and absents)
    ok["G9 trois tues dans Arma meurent au combat dans le moteur ( controle : vivants juste avant )"] = (
        vivants_avant and morts_ok and mil1 == mil0 - 3)
    ok["G9 les 29 autres vivants et absents, positions suivies, conservation"] = restent_ok and bouges == 5 and bool(tenue9[0])
    # G10
    w10 = arc9.iles["Malden"].w
    e10 = GM._etat(w10)
    # une ile qui n a jamais paye ( l horloge de G9 a deja fixe la base de Malden a 0 point : premier essai de G10
    # ECHOUE pour cette raison, 466 266 francs payes pour une « base » de 5 000 points )
    for att in ("guerre_points_payes", "guerre_paye"): w10.__dict__.pop(att, None)
    base = arc9.commande("Malden", "guerre_payer", 5000.0, B.EUROS_PAR_POINT)
    c0 = w10.gouv.caisse; d0 = e10.budget.depenses.get(("defense", "achats"), 0.0)
    r10 = arc9.commande("Malden", "guerre_payer", 6150.0, B.EUROS_PAR_POINT)
    c1 = w10.gouv.caisse
    bis = arc9.commande("Malden", "guerre_payer", 6150.0, B.EUROS_PAR_POINT)
    fob = 1150 * B.EUROS_PAR_POINT / w10.etalon_or["dernier_taux"]
    arc9.jours(1)
    d1 = GM._etat(w10).budget.depenses.get(("defense", "achats"), 0.0)
    tenue10 = arc9.commande("Malden", "tenue")
    print(f"   la guerre paie : base {base} ; paye {r10['paye']:.2f} ( FOB {fob:.2f} ) ; caisse {c0:.2f} -> {c1:.2f} ; "
          f"defense achats {d0:.2f} -> {d1:.2f} ; deuxieme fois {bis['paye']}", flush=True)
    ok["G10 la base ne paie rien ; l achat sort de la caisse, FOB + fret ; une seule fois"] = (
        base["paye"] == 0.0 and r10["paye"] > fob and abs((c0 - c1) - r10["paye"]) <= 1e-6 * max(1.0, r10["paye"])
        and bis["paye"] == 0.0)
    ok["G10 le soir, la ligne defense monte d au moins le FOB ; conservation"] = (d1 - d0) >= fob * (1 - 1e-9) and bool(tenue10[0])
    arc9.fermer()
    # G11
    sonde = "def gouverner(b, memoire):\n    memoire['vus'] = memoire.get('vus', 0) + 1\n    memoire['guerre'] = b.get('guerre')\n    return [{'type': 'rien'}]\n"
    arc11 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False, gouvernement={"Malden": sonde})
    modeles = {ile: arc11.commande(ile, "guerre_voir") for ile in ("Malden", "Stratis")}
    arc11.commande("Malden", "guerre_mobiliser", 5)
    arc11.jours(2)
    wm, ws = arc11.iles["Malden"].w, arc11.iles["Stratis"].w
    mem = wm.cerveau.interieur.memoire
    dec = lambda w: [e for e in w.evenements if e.get("type") == "decision_gouvernement"]
    g11 = mem.get("guerre") or {}
    print(f"   gouvernements : {modeles} ; le code a vu {mem.get('vus')} bulletins, guerre = {g11}", flush=True)
    ok["G11 le code recoit la section guerre chaque matin et decide"] = (
        mem.get("vus", 0) >= 2 and g11.get("soldats_en_reserve") == 5 and "morts_au_combat" in g11 and "cout_guerre_total" in g11
        and all(str(e.get("cerveau", "")).startswith("code:") for e in dec(wm)) and len(dec(wm)) >= 2)
    # G12
    from . import conseil as CO
    sc_reel = CO.scenario("/mnt/data/hmt/guerre/essai9", "Malden")
    sc = dict(sc_reel, part_recettes_armes=max(0.05, sc_reel["part_recettes_armes"]), morts_par_militaire_jour=max(0.005, sc_reel["morts_par_militaire_jour"]),
              lieux_occupes=[OCCUPEE])
    m12 = CO.evaluer_en_guerre(open(os.path.join(CO.SIX_ILES, "Malden.py")).read(), "Malden", sc, echelle=4.0, jours=3, graine=2001)
    g12 = m12["guerre"]
    lu = {k: v for k, v in sc_reel.items() if k != "lieux_occupes"}
    print(f"   conseil : scenario reel {lu} ; petit Malden en guerre : score {m12['score']} guerre {g12}", flush=True)
    ok["G12 scenario lu ; un petit pays en guerre : front, morts, armes payees, ferme occupee, conservation"] = (
        sc_reel["part_au_front"] > 0 and g12["soldats_au_front"] > 0 and g12["morts_au_combat"] >= 1 and g12["cout_guerre_total"] > 0
        and g12["fermes_sous_sequestre"] == 1 and m12["conservation"] and isinstance(m12["score"], float))
    arc12 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    avant = arc12.commande("Malden", "guerre_voir")
    apres = arc12.commande("Malden", "guerre_gouverner", sonde, "conseil:Malden")
    arc12.jours(1)
    d12 = [e for e in arc12.iles["Malden"].w.evenements if e.get("type") == "decision_gouvernement"]
    try: arc12.commande("Malden", "guerre_gouverner", "import os\ndef gouverner(b, memoire):\n    return []\n"); refuse12 = False
    except Exception: refuse12 = True
    ok["G12 la releve change qui decide ; un code interdit est refuse"] = (
        avant == "regles" and apres.startswith("code:") and d12 and str(d12[-1].get("cerveau", "")).startswith("code:") and refuse12)
    arc12.fermer()
    # G13 ( amendee le 28/09 : contre le temoin apparie des memes jours, graine neuve 2 )
    oc13, te13 = _g13(True, 2), _g13(False, 2)
    rap = lambda x: x[0] / max(1, x[1])
    print(f"   villes occupees : La Trinite / Dourdan, occupee {oc13['av']} {oc13['pe']} {oc13['ap']} ; temoin {te13['av']} {te13['pe']} {te13['ap']} ; "
          f"occupee / temoin {rap(oc13['pe']) / max(1e-9, rap(te13['pe'])):.3f}, liberee / temoin {rap(oc13['ap']) / max(1e-9, rap(te13['ap'])):.3f} ; "
          f"bulletin {oc13['villes']} siege {oc13['siege']}", flush=True)
    ok["G13 controle positif : La Trinite travaillait avant ; occupee, sous 0,4 fois le rapport du temoin des memes jours"] = (
        oc13["av"][0] > 0 and oc13["av"][1] > 0 and oc13["pe"][1] > 0 and rap(oc13["pe"]) < 0.4 * rap(te13["pe"]))
    ok["G13 liberee, au-dessus de 0,8 fois le temoin ; la quarantaine du gouvernement reste ; bulletin ; conservation"] = (
        rap(oc13["ap"]) > 0.8 * rap(te13["ap"]) and oc13["gv"] and "Malden_C_LaTrinite" in oc13["villes"] and oc13["siege"]
        and oc13["tenue"])
    # G15
    from monde.pays import d06_etat as ET15
    arc15 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    w15 = arc15.iles["Malden"].w; p15 = w15.pays
    w15.gouv.caisse = max(w15.gouv.caisse, 1e8)
    b15 = ET15._etat(p15).budget
    b15.credits[("interieur", "achats")] = b15.credits.get(("interieur", "achats"), 0.0) + 1e7    # la borne seule doit lier
    a_ok = ET15.appliquer(p15, {"type": "acheter", "bien": "nourriture", "quantite": 8000, "destination": "population"})
    a_non = ET15.appliquer(p15, {"type": "acheter", "bien": "nourriture", "quantite": 8001, "destination": "population"})
    dispo0 = b15.credits.get(("subventions", "transferts"), 0.0) - b15.depenses.get(("subventions", "transferts"), 0.0)
    s_avant = ET15.appliquer(p15, {"type": "subvention", "cible": "menages_pauvres", "montant": round(dispo0 + 5000)})
    f15 = ET15.appliquer(p15, {"type": "fixer_budget", "ligne": "subventions", "montant": round(b15.depenses.get(("subventions", "transferts"), 0.0) + dispo0 + 10000)})
    s_apres = ET15.appliquer(p15, {"type": "subvention", "cible": "menages_pauvres", "montant": round(dispo0 + 5000)})
    print(f"   leviers : acheter 8 000 {a_ok} ; 8 001 {a_non} ; subvention avant {s_avant} ; fixer_budget {f15} ; subvention apres {s_apres}", flush=True)
    ok["G15 acheter jusqu a 2 000 x k, pas au-dela ; subventions relevees puis versees"] = (
        a_ok[0] and not a_non[0] and "achat invalide" in a_non[1] and not s_avant[0] and f15[0] and s_apres[0])
    arc15.fermer()
    # G14 ( dans le monde ou G13 jouait avant son amendement, rejoue a l identique )
    from monde import population as PO13
    arc13, w13, t13 = _monde_de_g14()
    z14 = zone_de["centrale01"]; l14 = next(z["lieux"] for z in zs if z["n"] == z14)
    kc, kw = w13.carte.lieux["centrale01"].n, w13.carte.lieux["Malden_V_Dourdan"].n
    def usine(jours):
        pres, prod = [0, 0], 0.0
        for _ in range(jours):
            a0 = sum(w13.entreprises["centrale01"].produit_du_jour.values())
            for _ in range(144):
                arc13.un_pas(); n14 = t13.n
                at = (t13.vivant[:n14] == 1) & (t13.poste[:n14] == PO13.CODE_POSTE["travail"])
                pres[0] += int((at & (t13.lieu[:n14] == kc)).sum()); pres[1] += int((at & (t13.lieu[:n14] == kw)).sum())
            a1 = sum(w13.entreprises["centrale01"].produit_du_jour.values())
            prod += (a1 - a0) if a1 >= a0 else a1
        return pres, prod / jours
    pa, qa = usine(7)
    arc13.commande("Malden", "occuper", z14, l14, True)
    pp, qp = usine(7)
    arc13.commande("Malden", "occuper", z14, l14, False)
    usine(7)                                        # la semaine du retour ( l agenda planifie la semaine )
    pl, ql = usine(7)
    rp = lambda x: x[0] / max(1, x[1])
    print(f"   usines occupees : ouvriers de la centrale / temoin avant {pa} ( {rp(pa):.2f} ), occupee {pp} ( {rp(pp):.2f} ), liberee {pl} "
          f"( {rp(pl):.2f} ) ; production par jour {qa:.0f} -> {qp:.0f} -> {ql:.0f}", flush=True)
    ok["G14 controle positif : la centrale travaillait ; occupee, ouvriers sous 0,4 fois, production sous 0,5 fois"] = (
        pa[0] > 0 and pa[1] > 0 and pp[1] > 0 and qa > 0 and rp(pp) < 0.4 * rp(pa) and qp < 0.5 * qa)
    ok["G14 liberee, au-dessus de 0,8 fois"] = rp(pl) > 0.8 * rp(pa) and ql > 0.8 * qa
    arc13.fermer()
    # G16
    from multiprocessing import get_context
    famine_produite()                            # une fois, avant les copies ( le fork les herite )
    with get_context("fork").Pool(3) as pool:
        re16, po16, te16 = pool.map(_aide, ["reserve", "population", None])
    Q16 = round(po16["q"])
    print(f"   aide alimentaire ( famine produite ) : temoin {te16} ; reserve {re16} ; population {po16}", flush=True)
    ok["G16 controle positif : le temoin a faim au depart ; les deux imports acceptes, arrives dans le stock vise"] = (
        te16["faim0"] >= 0.30 and te16["credits"][0] and re16["import"][0] and po16["import"][0]
        and re16["arrive"] == (Q16, 0) and po16["arrive"] == (0, Q16))
    ok["G16 sans devises ( l etat reel ) : l import est refuse, avec sa raison, et rien n entre"] = (
        not po16["sans_devises"][0] and "refuse" in po16["sans_devises"][1] and po16["sans_devises_arrive"] == 0)
    ok["G16 la reserve ne nourrit personne ; la population, si ; autre destination refusee ; conservation"] = (
        all(abs(a - b) <= 0.02 for a, b in zip(re16["faim"], te16["faim"]))
        and po16["faim"][0] <= 0.5 * te16["faim"][0] and po16["faim"][0] <= te16["faim"][0] - 0.15
        and not any(x[0] for x in po16["refus"]) and po16["conservation"])
    # G17
    from monde.pays import d07_exterieur as X17
    arc17 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    faux17 = A.FauxGuerre(zs)
    h17_t = iter(x / 432.0 for x in range(10 ** 8))
    h17 = HorlogeDeGuerre(arc17, faux17, carte, periode_s=1.0, suivre=False, horloge=lambda: next(h17_t)).ouvrir()
    p17 = arc17.iles["Malden"].w.pays
    def devises(v): X17.reserves_de_change(p17); X17._ext(p17).reserves_euros = v
    def un_tour(): h17.boucle(tours=h17.tours + 1); return h17.derniere
    t1 = un_tour()
    faux17.depense["WEST"] = 1150.0; t2 = un_tour()
    devises(-1e9); faux17.depense["WEST"] = 2300.0; t3 = un_tour()
    t4 = un_tour()
    devises(1e9); t5 = un_tour()
    t6 = un_tour()
    tenue17 = arc17.commande("Malden", "tenue")
    arc17.fermer()
    m17 = lambda t: (round(t["iles"]["Malden"]["points"], 1), round(t["iles"]["Malden"]["paiement"]["paye"]), t["iles"]["Malden"]["paiement"]["dette_points"],
                     round(t["iles"]["Stratis"]["points"], 1))
    print(f"   fournisseur impaye ( points Malden, paye, impayes, points Stratis ) : {[m17(t) for t in (t2, t3, t4, t5, t6)]}", flush=True)
    ok["G17 paye puis impaye : 1 150 points d arriere ; au tour suivant Malden ne recoit rien, Stratis si"] = (
        t2["iles"]["Malden"]["paiement"]["paye"] > 0 and t3["iles"]["Malden"]["points"] > 0 and t3["iles"]["Malden"]["paiement"]["paye"] == 0
        and t3["iles"]["Malden"]["paiement"]["dette_points"] == 1150.0 and t4["iles"]["Malden"]["points"] == 0.0
        and t4["iles"]["Stratis"]["points"] > 0)
    ok["G17 les devises reviennent : l arriere est paye, Malden recoit de nouveau ; conservation"] = (
        t5["iles"]["Malden"]["paiement"]["paye"] > 0 and t5["iles"]["Malden"]["paiement"]["dette_points"] == 0.0
        and t6["iles"]["Malden"]["points"] > 0 and bool(tenue17[0]))
    # G18
    ec18 = _echelle_a_la_reprise()
    print(f"   convois : echelle posee a la reprise {ec18}", flush=True)
    ok["G18 une ile d avant le 27/09 recoit l echelle de l archipel a la reprise"] = (not ec18["deja"] and ec18["echelle"] == 200.0)
    # G24
    with get_context("fork").Pool(2) as pool:
        fr24, cp24 = pool.map(_fret_recoltes, [False, True])
    print(f"   fret des recoltes : {fr24}", flush=True)
    print(f"   controle positif ( fret coupe ) : {cp24}", flush=True)
    ok["G24 le fret des recoltes : les rations pretes aux fermes sous 2 jours de demande, jours 5 a 30 ( graine 2 ) ; conservation"] = (
        fr24["fermes_max_j5_30"] <= 2.0 and fr24["conservation"])
    ok["G24 controle positif : fret du domaine 15 coupe, la porte echoue"] = cp24["fermes_max_j5_30"] > 2.0
    # G20
    import numpy as np
    from monde.archipel import creer_ile
    from monde import tests as T20
    if "G20" in SANS:                            # 27/09 : l aube du jour 350 dure ~70 min ( d01._placer, HMT-130 )
        print("   G20 sautee ( --sans G20 ) : la porte n est pas complete", flush=True)
    else:
        re20 = _faim_produite(); te20 = _faim_produite(relacher=False)
        print(f"   famine produite puis relachee : {re20}", flush=True)
        print(f"   controle positif ( le blocus continue ) : {te20}", flush=True)
        ok["G20 une famine du code d aujourd hui relachee : fermes en 8 jours, faim sous 10 % le huitieme, morts de faim sous 1 % ; conservation"] = (
            re20["faim_blocus"] >= 0.30 and g20_passe(re20))
        ok["G20 controle positif : sans relache, la meme porte echoue"] = not g20_passe(te20)
    # G21 : un versement du jour, verifie menage par menage
    from monde.pays import d06_etat as ET21
    w21 = creer_ile("Stratis", 1, 4.0); p21 = w21.pays; ET21.brancher_revenu_minimum(p21); T20.jours(w21, 3)
    tb21 = w21.table; n21 = tb21.n; M21 = len(w21.menages); cm = p21.colonnes["menage"]; ch21 = p21.colonnes["habitant"]
    viv = np.nonzero((tb21.vivant[:n21] == 1) & (tb21.menage[:n21] >= 0))[0]; mid = tb21.menage[viv].astype(np.int64)
    age = (p21.jour - ch21["naissance_j"][viv].astype(np.float64)) / 365.0
    ad = np.bincount(mid[age >= 18], minlength=M21)[:M21].astype(float); en = np.bincount(mid[age < 18], minlength=M21)[:M21].astype(float)
    ech = np.where(ad > 0, 1 + 0.5 * np.maximum(0, ad - 1) + 0.25 * en, 0.0)
    seuil = 216.0 * ech / 30.0 / 1.15; rev = np.maximum(0.0, cm["eco_revenu"][:M21] - cm["rmg_lisse"][:M21]); avoirs = 7200.0 * ech / 1.15
    cibles21 = np.nonzero((cm["dissous"][:M21] == 0) & (ad > 0))[0][:60]          # soixante menages sans revenu, presque sans avoirs
    cm["eco_revenu"][cibles21] = 0.0; cm["rmg_lisse"][cibles21] = 0.0; w21.table.menages.caisse[cibles21] = 10.0
    rev = np.maximum(0.0, cm["eco_revenu"][:M21] - cm["rmg_lisse"][:M21])
    caisse0 = w21.table.menages.caisse[:M21].copy(); g0 = w21.gouv.caisse
    attendu = np.where((cm["dissous"][:M21] == 0) & (ad > 0) & (caisse0 <= avoirs), np.maximum(0.0, seuil - rev), 0.0)
    attendu[attendu <= 0.01] = 0.0
    ET21._revenu_minimum(p21)
    recu = w21.table.menages.caisse[:M21] - caisse0
    kea_exact = bool(attendu.sum() > 0) and float(np.abs(recu - attendu).max()) < 1e-6
    riche = (rev >= seuil) & (ad > 0); aise = caisse0 > avoirs
    rien = float(np.abs(recu[riche | aise]).max(initial=0.0)) < 1e-9
    etat = abs((g0 - w21.gouv.caisse) - float(recu.sum())) < 1e-6
    w0_21 = creer_ile("Stratis", 1, 4.0); T20.jours(w0_21, 3)
    sans21 = not any(f is ET21._revenu_minimum for fs in w0_21.pays.routines.values() for _, _, f in fs)
    print(f"   revenu minimum : {int((attendu > 0).sum())} menages eligibles sur {M21}, {float(recu.sum()):.0f} verses ; exact {kea_exact}, "
          f"rien aux riches et aux aises {rien}, Etat {etat}, branche dans aucune ile {sans21}", flush=True)
    ok["G21 le versement exact ; rien aux riches ni aux aises ; l Etat paie ; branche dans aucune ile"] = kea_exact and rien and etat and sans21
    # G23
    arc23 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False); w23 = arc23.iles["Malden"].w
    vus23 = []
    class _Sonde23:
        modele = "sonde"
        def __call__(self, b, memoire=""): vus23.append(b.get("refus_hier")); return [], "sonde"
    c23 = GM.CerveauDeGuerre(_Sonde23(), w23)
    w23.noter("decision_gouvernement", motifs="", cerveau="sonde",
              actions=[{"action": {"type": "fixer_budget", "ligne": "defense", "montant": 1e12}, "acceptee": False, "raison": "credits 1e12 hors [0 ; 1]"},
                       {"action": {"type": "rien"}, "acceptee": True, "raison": ""}])
    c23({}, "")
    w23.noter("decision_gouvernement", motifs="", cerveau="sonde", actions=[{"action": {"type": "rien"}, "acceptee": True, "raison": ""}])
    c23({}, "")
    arc23.fermer()
    print(f"   refus d hier : apres un refus {vus23[0]} ; sans refus {vus23[1]}", flush=True)
    ok["G23 le code recoit les refus d hier avec leur raison ; liste vide sans refus"] = (
        len(vus23) == 2 and len(vus23[0]) == 1 and vus23[0][0]["action"]["type"] == "fixer_budget" and "hors" in vus23[0][0]["raison"]
        and vus23[1] == [])
    # G19
    arc19 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    h19_t = iter(x / 432.0 for x in range(10 ** 8))
    h19 = HorlogeDeGuerre(arc19, A.FauxGuerre(zs), carte, periode_s=1.0, suivre=False, horloge=lambda: next(h19_t)).ouvrir()
    paix19 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    h19.boucle(tours=1); paix19.jours(3)
    r19 = arc19.commande("Malden", "tourisme_etat"); s19 = arc19.commande("Stratis", "tourisme_etat"); p19 = paix19.commande("Malden", "tourisme_etat")
    print(f"   avis aux voyageurs : {h19.risques} ; recettes 7 jours Malden en guerre {r19['recettes_7j']}, en paix {p19['recettes_7j']}", flush=True)
    ok["G19 risques poses a l ouverture ; recettes de Malden en guerre sous 20 % de la paix"] = (
        r19["risque"] == 0.15 and s19["risque"] == 0.5 and p19["recettes_7j"] > 0 and r19["recettes_7j"] <= 0.2 * p19["recettes_7j"])
    arc19.fermer(); paix19.fermer()
    ok["G11 l ile sans code decide par les regles, sans bascule"] = (
        len(dec(ws)) >= 2 and all(e.get("cerveau") == "regles" and not str(e.get("motifs", "")).startswith("cerveau indisponible") for e in dec(ws)))
    arc11.fermer()
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    passe = all(ok.values())
    print(f"PORTES DE LA GUERRE : {'FRANCHIES' if passe else 'ECHOUEES'}{' ( SANS ' + ', '.join(SANS) + ' )' if SANS else ''} ( {time.time() - t0:.0f} s )")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
