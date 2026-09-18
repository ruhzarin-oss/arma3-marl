# Banc de perception, regard centre : il n y a PAS de seuil de distance entre 128 et 215 m de nuit ( 18/09/2026, 22 h 45 )

**Statut : DESCRIPTIF ( un episode par monde et par distance ), mais il CORRIGE le compte rendu de l apres-midi ( 3c0204f ).**
Ordre de Younes : attaquer le plan 33e1c3a en parallele, sur la copie `bancs/chacalvue`, 12 serveurs. `bancs/chacal` n a pas ete touche.

## Ce qui a ete joue
| campagne | episodes | instrument |
|---|---|---|
| FUMEE-BANC-JOURNAL-18-09 | 4 | + `patch_banc_journal.py` ( f26d2d9 ) : sonde a 1 s, checkVisibility continu, fenetre 600 s fermee 30 s apres la connaissance, episode rendu apres la fenetre. Regard NON centre. |
| FUMEE-BANC-REGARD-18-09 | 2 | + `patch_banc_regard.py` ( 2786e65 ) : chaque homme est TOURNE vers la cible avant le doWatch. |
| SEUIL-PAR-MONDE-18-09 | 34 | meme instrument ; 8 mondes ( 4, 5, 6, 7, 8, 9, 11, 12 ) x 4 distances + un rejeu ; bras entrelaces sur 12 instances. |
40 episodes, 0 erreur SQF, 3 refus propres ( aucune ligne de vue, rendus en quelques secondes ), 37 valides dont 33 a regard centre.
Criteres ecrits avant : `CRITERES_SEUIL_PAR_MONDE_18-09.md` ( et son additif de 22 h 05 avant la fumee v2 ). Lecteur : `lire_seuil_par_monde.py`.

## Le resultat ( 33 episodes valides a regard centre, nuit 1 h 30, lune 0,79, jumelles de vision nocturne, cible debout )
- **29 connues sur 33, en 3 a 11 s ( mediane 5 s ; 28 sur 29 en 8 s ou moins ), de 128 m a 215 m, dans les 8 mondes.**
- **Le delai ne depend pas de la distance** : 5,8 s en moyenne sous 170 m ( n = 15 ), 5,1 s a 170 m et plus ( n = 14 ).
- **Les 4 « jamais en 600 s » ont tous une visibilite continue quasi nulle** ( `vis_moy` 0,00 ; 0,00 ; 0,00 ; 0,01 ) : monde 5 a 148 et
  156 m, monde 8 a 168 m, monde 12 a 193 m. La cible REELLE est masquee : les rayons testent un point, `createUnit` pose l ennemi a 3 m
  pres, et il peut tomber derriere un buisson. Ce sont des defauts du banc, pas des echecs de perception.
- La regle ne va que dans un sens : deux cibles sont CONNUES malgre `vis_moy` <= 0,01 ( monde 6 a 166 m en 11 s, monde 5 a 156 m en 3 s ).
- **Deterministe** : monde 4 a 157 m, original 6 s, rejeu 7 s, meme azimut ( 80 ). Rejouer un ( monde, distance ) n ajoute presque rien.
- Precision du « 6 s » de la journee : a la sonde de 1 s, la connaissance tombe souvent a 3 s. Le 6 s etait la grille de 5 s.

## Les predictions ecrites avant, et leur sort
| prediction | sort |
|---|---|
| 1. LIEU : les d* des mondes s etalent sur plus de 30 m | **SANS OBJET** : il n y a pas de d* dans la bande jouee ( tout est connu, sauf les cibles masquees ). Les « d* » que le lecteur imprime pour les mondes 8 et 12 ne sont que la position d une cible masquee. |
| 2. DELAI : le delai s allonge pres du seuil | **REFUTEE** : 4 mondes sur 7 ne s allongent pas, et les moyennes sont egales ( 5,8 s / 5,1 s ). |
| 3. DEUXIEME VARIABLE : vis_moy separe connus et jamais pres du seuil ( aire >= 0,75 ) | **MAL POSEE, a moitie tenue** : sur tous les episodes centres l aire vaut 0,97, mais `checkVisibility` ne fait que detecter une cible MASQUEE ( <= 0,01 ) ; entre 0,02 et 0,84 elle ne change ni l issue ni le delai. Ce n est pas la « deuxieme variable d une equation », c est un controle de validite du banc. |
| 4. DETERMINISME : le rejeu donne la meme issue, delai a 2 s pres | **TENUE** ( 6 s / 7 s ). |

## CORRECTION du compte rendu de l apres-midi ( `RESULTATS_BANC_SEUIL_18-09.md`, 3c0204f )
Trois de ses conclusions venaient du BANC, pas du monde :
1. « le seuil de nuit est vers 158 m ( monde 4 ), entre 156 et 164 m ( monde 5 ) » - FAUX : regard centre, le monde 4 connait a 160 et
   170 m en 3-4 s, le monde 5 a 160 et 171 m en 3-5 s. Cause : `doWatch` seul. `angle_min` ( le MEILLEUR des dix hommes ) tombait a 0 deg
   alors que les autres regardaient ailleurs ; et le pivot prenait jusqu a 90 s.
2. « le seuil depend du lieu » - NON ETABLI : ce qui variait d un lieu a l autre etait l angle de depart et le masquage de la cible.
3. « le delai s allonge pres du seuil ( 65, 70, 112, 259 s ) » - ARTEFACT du pivot : ces episodes partaient a 22-30 deg de la cible, et la
   sonde a 1 s montre la connaissance tomber a la seconde ou le regard arrive dessus ( fumee v1, monde 5 : 24 deg -> 3 deg en 90 s ).
Ce qui TIENT de l apres-midi : connue en quelques secondes sous 150 m ; `patch_banc_vue_fine.py` ( recherche fine, refus VOID ) ; la
refutation de la marche et de l accumulateur reste vraie en tant que refutation, mais pour une mauvaise raison - aucune des deux formes
n a de sens si le delai mesure etait celui du pivot. La note pour e33942b ( « bande par monde » ) est RETIREE.

## Ce que ca change pour le plan 33e1c3a
- Point 3 ( table monde -> d* ) : FAIT, et la reponse est « pas de d* sous 215 m ». Point 5 ( poser les menaces a d* x [ 0,8 ; 1,2 ] ) : **TOMBE**.
- La variance de perception au moment du choix ne viendra pas de la distance dans la bande 130-215 m. Elle vient de **OU LES HOMMES
  REGARDENT** et de **combien de temps ils balaient** : dans la mission, la fenetre balaie trois azimuts ( -45, 0, +45 ) 10 s chacun, et un
  pivot de 24 deg peut prendre 90 s. Les menaces des campagnes VP_* etaient a 320-713 m : il reste a borner la portee REGARD CENTRE au-dela
  de 215 m ( un seul point non centre : 263 m connue en 3 s ; 240 m jamais ).
- Prochaines mesures utiles, dans l ordre : ( a ) portee regard centre a 250, 300, 400, 500, 600 m, nuit et jour ; ( b ) le balayage reel de
  la mission : part des menaces connues selon l ecart d azimut entre la menace et l axe de la phase ( 0, 30, 60, 90, 135, 180 deg ) et la
  duree de la fenetre ; ( c ) corriger le banc : apres la pose, si `vis_moy` de la cible reelle <= 0,01, essayer le candidat suivant.
- Pour l agent : le levier n est pas « se rapprocher » mais « regarder dans la bonne direction assez longtemps ». C est une decision
  ( ou observer, combien de temps ) qui peut dependre de la situation - donc un bon candidat pour la ligne de decision.

## Limites
Un episode par ( monde, distance ) ; une heure de nuit, une posture, vision nocturne portee ; bande 128-215 m seulement ; la distance
vraie ( au plus proche homme ) s ecarte de la consigne jusqu a 60 m dans les mondes 8, 9, 11 ( colonne etiree ) ; dans les mondes 8 et 9,
5 a 7 hommes sur 10 seulement ont la ligne de vue ; machine partagee ( charge archivee par run ).
