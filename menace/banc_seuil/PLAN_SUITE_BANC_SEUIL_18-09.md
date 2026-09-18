# Plan pour la session qui tient la file - suite du banc de seuil ( ecrit le 18/09/2026 au soir, a la demande de Younes )

Source : commit 3c0204f, `menace/banc_seuil/RESULTATS_BANC_SEUIL_18-09.md` ( 40 episodes, 28 valides ). A lire avant tout.

## 0. Un seul ecrivain
Trois sessions ont ecrit sur la WS aujourd hui. Younes designe celle qui tient la file et le depot ; les autres preparent
HORS depot ( `/mnt/data/hmt/en-attente/` ) et lui passent la main. Avant tout job : `git log -3` et `ls queue/en_cours`.

## 1. Laisser finir les 5 jobs VP_* et lire la variance ( rien a poser avant )
Si la part « menace connue au choix » entre dans 30-70 % avec les niveaux 4 et 5 : aller directement au point 5.
Sinon : points 2 a 4.

## 2. Donner la recherche fine a `bancs/chacal` ( file VIDE, 1 minute + 35 minutes de fumee )
`bancs/chacal` a le refus simple ( 16e4b32 ) mais cherche encore sur 18 azimuts depuis le seul chef, et un refus dure 300 s.
A 150-300 m : ~2 episodes sur 3 refuses, 13 min chacun.
- `python3 menace/banc_seuil/patch_banc_vue_fine.py` ( prevu pour passer APRES le refus simple : il le retire et pose le sien ;
  rejoue deux fois, il refuse bruyamment ).
- Controle : dans `60_phases.sqf`, `RECHERCHE FINE` = 1, `BANC_SANS_LIGNE_DE_VUE` = 1, un seul bloc `banc_refuse` ; commit.
- Fumee : `menace/banc_seuil/jobs_vue.py` avec `banc="chacal"` ; criteres deja ecrits dans `ACCEPTATION_BANC_VUE_FINE.md`
  ( positif 100 m connu en <= 10 s ; 225 m : ligne de vue dans >= 1 monde sur 2 ; negatif : VOID en < 3 min, 0 erreur SQF ).
- Fumee passee : retirer `bancs/chacalvue` et `MPMissions/CHACALVUE.Altis`, archiver les 7 jobs TROU de `queue/suspendus/`.

## 3. Le complement du banc de seuil : PAR MONDE, pas une distance unique
Ce que les 28 points disent : sous 150 m, connue en 6-8 s partout ; le seuil de nuit est ~158 m dans le monde 4, entre 156 et
164 m dans le monde 5, AU-DELA de 200 m dans le monde 6 ; pres du seuil le delai s allonge ( 12, 65, 112, 259 s ).
Consequences pour la regle e33942b ( « la distance dont la part connue en 90 s est la plus proche de 50 % » ) :
- une distance unique ne donnera pas 30-70 % dans tous les mondes : ecrire la regle PAR MONDE, ou en distance relative au
  seuil du lieu ( a ecrire AVANT de lire, comme e33942b ) ;
- avant de jouer 6 repetitions d un meme ( monde, distance ) : rejouer UNE fois le point monde 4 / 156 m. Si le resultat est
  identique, la scene est deterministe et repeter n ajoute pas de n ; mettre alors l effort sur PLUS DE MONDES
  ( 4, 5, 6, 7, 8, 9, 11, 12 ) x 4 distances plutot que sur 6 repetitions ;
- distances proposees : mondes 4 et 5 : 150, 157, 164, 171 m ; mondes 6 et 7 : 170, 185, 200, 215 m ; autres mondes :
  150, 170, 190, 210 m puis resserrer ;
- bras ENTRELACES entre instances ( chaque instance joue des distances et des mondes meles, pas un bras par instance ).

## 4. Petit patch de journalisation, a faire avec le point 3 ( c est la deuxieme variable de l equation )
- ecrire la valeur CONTINUE de `checkVisibility` ( moyenne et max sur les hommes ), pas seulement le compte > 0,5 ;
- sonde a 1 s pendant les 120 premieres secondes ; fenetre portee a 600 s pour les distances proches du seuil
  ( sinon « jamais » et « plus de 300 s » sont confondus ) ;
- trancher la regle « le canal geometrique doit avoir VU » : elle a exclu un episode du monde 7 ou la cible etait CONNUE a 7 s.

## 5. Porte de decision, ecrite d avance
- une bande ( par monde ) donne 30-70 % : ecrire les criteres de la campagne P2 a types separes, puis la lancer ;
- aucune bande n y arrive : la perception est un interrupteur A L ECHELLE DE L EPISODE. La variance doit alors venir du
  PLACEMENT : poser la menace a d* x [ 0,8 ; 1,2 ], d* = seuil du monde lu au point 3. La campagne P2 part avec ce placement.

## 6. Range pour l instant ( rien a lancer )
- la boucle EvoGP sur 12 serveurs et les parametres Architecte / Oracle : sur des perceptions constantes ils apprennent du vide ;
- le prix du temps : indecis, 750 episodes pour trancher, hors chemin critique. Si Younes rouvre l axe, l horloge existe deja
  dans les jobs ( `qrf_delai`, `qrf_n` : un renfort a N minutes ) ; rien a construire.
