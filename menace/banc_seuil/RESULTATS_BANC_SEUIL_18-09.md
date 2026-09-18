# Banc de perception - le seuil de connaissance, nuit et jour ( 18/09/2026 )

**Statut : DESCRIPTIF, pas un verdict.** 1 a 2 mondes par point, 4 mondes, une posture ( debout ), une heure de nuit ( 1 h 30,
lune 0,79, jumelles de vision nocturne ), une heure de jour ( 12 h 30 ). Ecrit par la session du balayage, a la demande de
Younes ( « lance la mesure de detection visuelle », puis « go » pour la fumee et pour la campagne du seuil ).

## Ce qui a ete joue
| campagne | banc | episodes | remarque |
|---|---|---|---|
| BANC-PERCEPTION-18-09 ( matin, autre session ) | chacal | 10 | verdict d666662 ; ~57 erreurs SQF par episode ( BIS_fnc_lowest, champ angle seul ) |
| BANC-TROU-18-09 | chacal | 6 joues sur 20 prevus | **4 episodes sur 6 sans ligne de vue** ; 7 jobs suspendus puis abandonnes ( `queue/suspendus/` ) |
| FUMEE-BANC-VUE-FINE-18-09 | chacalvue | 6 | test d acceptation du patch : PASSE ( `ACCEPTATION_BANC_VUE_FINE.md` ) |
| BANC-SEUIL-18-09 | chacalvue | 18 | 0 refus, 0 erreur SQF ; criteres `CRITERES_BANC_SEUIL_18-09.md` deposes a 15 h 51, avant les jobs |

Lecture unique : `lire_banc_seuil.py` ( 40 episodes lus, 28 valides ). Un episode est valide si `ligne_de_vue = 1`, si le canal
geometrique de la mission a VU la cible au moins une fois, sans `banc_refuse`, sans erreur SQF ( sauf l erreur connue du matin ),
et un « jamais » ne compte qu une fois la fenetre de 300 s finie. La distance est la distance VRAIE ( `verite_distance_menace` ).

## L outil : `patch_banc_vue_fine.py`
L ancien banc cherchait la ligne de vue sur 18 azimuts, a une distance exacte, depuis le seul chef, et posait la cible meme sans
ligne de vue. Le patch teste 360 candidats ( 72 azimuts x 5 distances a +-6 % ), compte les HOMMES qui voient, exige la moitie,
refuse sinon ( VOID immediat en mode banc : 4 s au lieu de 13 min ), et verifie la cible reelle par `checkVisibility`.
Fumee : positif 100 m connu a 6 s ( 2/2 ) ; 225 m monde 4, 0 ligne de vue avant, 9 hommes sur 10 apres ; monde 5 refuse
proprement ; negatif VOID ( 2/2 ). **Il n est PAS encore applique a `bancs/chacal`** : il tourne sur la copie `bancs/chacalvue`
( commit 0ccc10f ; mission `CHACALVUE.Altis`, config `server_vue.cfg`, le `server.cfg` partage n est jamais ecrit ).

## Les points valides, par monde ( distance vraie -> delai avant connaissance du groupe )
**NUIT**
| monde | points |
|---|---|
| 4 | 51 m 6 s ; 99 m 6 s ; 150 m 6 s ; **156 m jamais** ; **158 m 7 s** ; 161 m jamais ; 173 m jamais ; 198 m jamais ; 298 m jamais |
| 5 | 46 m 6 s ; 99 m 6 s ( x2 ) ; 155 m 6 s ; 156 m 6 s ; 164 m jamais ; 300 m jamais ; 598 m jamais |
| 6 | 143 m 6 s ; 172 m **12 s** ; 200 m **65 s** |
| 7 | 148 m 8 s ; ( 173 m connue a 7 s et 198 m jamais : EXCLUS, le canal geometrique n a jamais vu la cible ) |

**JOUR**
| monde | points |
|---|---|
| 4 | 144 m 7 s ; 190 m 8 s ; 280 m **70 s** |
| 5 | 147 m 6 s ; 198 m **112 s** ; 301 m **259 s** ; ( 300 m jamais, ancien banc ) |

## Ce que ca etablit, et ce que ca n etablit pas
1. **Sous 150 m, de nuit comme de jour, une cible debout regardee est connue en 6 a 8 s** : 14 points sur 14, 4 mondes.
2. **De nuit, au-dela de 200 m, jamais connue en 300 s** dans les mondes 4 et 5 ( 5 points ). Le monde 6 connait encore a 200 m ( 65 s ).
3. **Le seuil depend du LIEU, pas seulement de la distance.** De nuit : monde 4 ~158 m, monde 5 entre 156 et 164 m, monde 6 au-dela
   de 200 m. De jour a ~195 m : 8 s dans le monde 4, 112 s dans le monde 5. Dans le monde 4 il y a meme une inversion a 2 m pres
   ( 156 jamais, 158 connue ) : autour du seuil, l azimut ou le fond decident.
4. **Le delai s allonge pres du seuil** ( monde 6 nuit : 6, 12, 65 s ; monde 5 jour : 6, 112, 259 s ; monde 4 jour : 7, 8, 70 s ).
   Un « jamais en 300 s » pres du seuil peut donc n etre qu un delai plus long que la fenetre.
5. **Le jour porte plus loin que la nuit** : connue a 280-301 m de jour, contre 158-200 m de nuit selon le lieu.

## Les predictions ecrites avant, et leur sort
| prediction | sort |
|---|---|
| MARCHE : tout delai connu <= 10 s ( `CRITERES_BANC_TROU`, `CRITERES_BANC_SEUIL` ) | **REFUTEE** : 12, 65, 70, 112, 259 s |
| MARCHE : aucune inversion dans un meme monde | **REFUTEE** : monde 4 nuit, 156 jamais / 158 connue |
| CONSTANTE : le seuil des mondes 6-7 tombe dans [150 ; 200] m | **REFUTEE** : monde 6 connait a 200 m |
| JOUR : 150 m connue ( positif ) | tenue ( 2/2 ) |
| JOUR : le seuil de jour depasse celui de nuit | tenue |
| ACCUMULATEUR ajuste sur le jour : 11 a 14 s a 190 m ( `PREDICTION_JOUR_200m.md`, deposee 16 h 46 avant le job ) | **REFUTEE** : 8 s ( monde 4 ) et 112 s ( monde 5 ) - ni la marche ni l accumulateur |

**Mon erreur sur l accumulateur : une agregation.** Je l ai ajuste sur des points de jour venant de DEUX mondes ( 144-147 m, 280 m
monde 4, 301 m monde 5 ) comme s ils etaient sur une meme courbe. Monde par monde, la forme « delai court puis explosion pres d un
seuil propre au lieu » reste compatible avec les donnees ( 3 points par monde : aucun test possible ), mais UNE courbe commune est fausse.

## Forme candidate pour la suite ( HYPOTHESE, a tester sur des episodes jamais vus )
delai( d ) = t0 + S / ( a.L.v / d^2 - f ), jamais si a.L.v / d^2 <= f, seuil d* = racine( a.L.v / f ) ; L = lumiere, **v = visibilite du
lieu**. Ce qu il faut pour la tester : ( 1 ) journaliser la valeur CONTINUE de `checkVisibility` ( aujourd hui seul le compte d hommes
> 0,5 est ecrit ; il a deja montre des desaccords avec les rayons : 10 contre 0 a 156 m monde 5, et c est le monde « dur » de jour ) ;
( 2 ) sonde a 1 s pendant les deux premieres minutes ; ( 3 ) fenetre plus longue que 300 s pres du seuil ; ( 4 ) 4 a 5 distances PAR
monde ; ( 5 ) EvoGP sur les points, et la forme n entre que si elle bat la plus simple sur des episodes neufs.

## Limites
- Bras non entrelaces entre instances : nuit mondes 4-5 sur l instance 2, nuit mondes 6-7 sur la 3, jour sur la 4. La mesure est en
  secondes de jeu ( 6 s ou des dizaines de secondes ), peu sensible a la charge, mais ce n est pas verifie.
- Charge : BANC-TROU et la fumee ont tourne pendant PRIX DU TEMPS v1 ( 8 serveurs ) ; BANC-SEUIL sur machine presque vide de 16 h 40 a
  17 h 02, puis sous PRIX DU TEMPS v2 ( 12 serveurs de plus ) pour ses 8 derniers episodes. La charge est archivee dans chaque run.
- Angle du regard : plusieurs episodes partent a 22-30 deg de la cible ( le pivot prend du temps ). A 143-190 m cela n a pas empeche une
  connaissance en 6 a 8 s ; pres du seuil l effet n est pas separable de la distance avec ces donnees.
- La regle « la geometrie doit avoir VU » exclut deux episodes du monde 7, dont un ou la cible est pourtant CONNUE a 7 s : la regle est
  peut-etre trop severe, ou le canal geometrique ( cone de 70 deg ) a un angle mort. A trancher avant une campagne plus large.
- Apres connaissance, de jour, le detachement ENGAGE ( 118 tirs, 4 morts a 280 m ) : le banc mesure le delai de connaissance, pas la suite.

## Pour l autre session ( commit e33942b, « banc de seuil : la regle de choix de la bande de distance » )
Ces points repondent en partie a sa question. De nuit, la bande ou la connaissance bascule est **155-175 m dans les mondes 4 et 5**
( connue en 6-7 s a 155-158 m, jamais a 156-164 m : c est la que la part connue approche 50 % ), mais elle est **au-dela de 200 m dans le
monde 6**. Une distance unique ne donnera donc pas 30-70 % dans tous les mondes : la bande est a choisir PAR MONDE, ou a lire en distance
relative au seuil du lieu. Et `bancs/chacal` n a pas encore la recherche fine : sans elle, un banc a 150-300 m perd 2 episodes sur 3.

## Fichiers
`patch_banc_vue_fine.py`, `ACCEPTATION_BANC_VUE_FINE.md`, `CRITERES_BANC_TROU_18-09.md`, `CRITERES_BANC_SEUIL_18-09.md`,
`PREDICTION_JOUR_200m.md`, `jobs_trou.py`, `jobs_vue.py`, `jobs_seuil.py`, `lire_banc_seuil.py`, `TABLEAU_EPISODES.md` ( sortie du lecteur ).

## Heures de depot d origine des fichiers ecrits AVANT les mesures ( /mnt/data/hmt/en-attente/ )
- 18/09/2026 15:22:57 : ACCEPTATION_BANC_VUE_FINE.md
- 18/09/2026 15:51:38 : CRITERES_BANC_SEUIL_18-09.md
- 18/09/2026 14:47:04 : CRITERES_BANC_TROU_18-09.md
- 18/09/2026 16:46:21 : PREDICTION_JOUR_200m.md
