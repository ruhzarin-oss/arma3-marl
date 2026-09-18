# Criteres pre-enregistres - la variance de perception selon le point d observation et le balayage ( ecrit AVANT tout episode )

*Nuit du 18 au 19/09/2026, travail autonome autorise par Younes ( points 1 a 4 du plan + P2 ; bancs/chacal intouchable ).
Banc `bancs/chacalp2` = copie de `bancs/chacal` ( niveaux 4 et 5 ) + `patch_mission_observation.py` ( leviers CHACAL_AVANT, CHACAL_BALAYAGE ).*

## Pourquoi
La porte de variance ( `menace/lire_variance.py` ) reste fermee : VARIANCE-SITUATION-18-09 donne 25 % de menaces percues, 0 % de connues.
Deux causes mesurees le 18/09 : ( 1 ) le detachement observe la route depuis 260 m en retrait, les postes sont a 320-713 m, et de nuit la
connaissance d une cible debout et regardee s arrete entre 215 et 300 m ; ( 2 ) le balayage de la fenetre pivote sous doWatch seul, trop
lentement pour tenir dix secondes par azimut.

## Etape 1 - FUMEE-OBSERVATION-19-09 ( 2 jobs, mondes 4 et 5, P2 niveau 5, situation 1, traverser tout de suite, fenetre 90 s )
| job | reglage | attendu |
|---|---|---|
| ORIGINE | avant = 260, balayage = 0 | 0 erreur SQF, ACCEPTE, ligne `reglage_observation` ( 260, 0 ) ; **meme perception au choix que VS-P2_TYPE2_s1 sur bancs/chacal** ( monde 4 : percue 0 ; monde 5 : percue 1 ) et meme distance de pose ( 207 et 269 m ) : les leviers a leur defaut ne changent rien |
| REGLE | avant = 120, balayage = 1 | 0 erreur SQF, ACCEPTE, ligne `reglage_observation` ( 120, 1 ), `distance_secteur` entre 60 et 190 m, decision et `choix_joue` presents, phase 2 terminee sans plafond |
Un seul echec : on corrige et on rejoue la fumee. Rien d autre ne part.

## Etape 2 - VARIANCE-OBSERVATION-19-09 : la grille
avant dans { 260, 180, 120 } x balayage dans { 0, 1 } = 6 reglages ; chacun joue P2 niveau 5 ( poste de controle seul, pose pres ) sur
4 paires de mondes ( 4-5, 6-7, 8-9, 11-12 ) x 2 graines de situation ( 1, 2 ) = 16 episodes par reglage, 96 en tout, traverser tout de suite,
fenetre de 90 s ( fixee par Younes ). 48 jobs melanges sur 12 instances. Lecture : `menace/lire_variance.py`, inchange, par reglage.

## Regle de choix du reglage, ecrite d avance
1. Un reglage est ADMISSIBLE s il passe les deux portes de `lire_variance.py` : part globale de `menace_percue > 0` au choix dans
   [ 30 % ; 70 % ], ET au moins un monde qui melange les deux issues.
2. Parmi les admissibles, on retient celui dont la part de menaces CONNUES ( niveau 2 ) est la plus proche de 50 % ; a egalite, le plus
   proche de l origine ( avant le plus grand, puis balayage 0 ) : on change la mission le moins possible.
3. Garde-fou de mission : un reglage ou plus de 25 % des episodes finissent la phase 2 compromis ou avec des pertes est ECARTE ( observer
   de plus pres ne doit pas couter la vignette ) ; l origine sert de reference.
4. Si AUCUN reglage n est admissible : la campagne P2 ne part pas. Je rapporte la grille telle quelle, et la decision revient a Younes.

## Predictions ecrites avant
- a. A l origine ( 260, 0 ) : percue ~25 %, connue 0 % ( reproduit VARIANCE-SITUATION ).
- b. Le balayage repare seul ( 260, 1 ) ne suffit pas : les postes restent hors de portee ; connue < 15 %.
- c. Observer de plus pres ( 120 ) fait monter la part connue ; avec le balayage repare elle depasse 30 %.
- d. Risque : a 120 m la part d episodes compromis en phase 2 monte ( le poste a des jumelles de nuit et regarde la route ).
Toute prediction fausse est rapportee telle quelle.

## Additif du 19/09, 0 h 00 - la fumee a echoue sur UN point, correction et fumee v2 ( ecrit AVANT la fumee v2 )
Fumee v1 : ORIGINE conforme dans les deux mondes ( monde 4 percue 0 a 207 m, monde 5 percue 1 a 269 m : identique a VS-P2_TYPE2_s1 sur
bancs/chacal ), 0 erreur SQF, lignes presentes. REGLE ( 120, 1 ) : monde 4 observe depuis 121 m, conforme ; **monde 5 observe depuis 208 m, hors
de la bande 60-190 m ecrite**. Cause lue dans le RPT : au depart direct le detachement est pose a 330 m de la route quel que soit le levier, il
devait marcher 210 m au lieu de 70, et il s est enlise ( reflexe de gel, 324 s ). Correction : `patch_mission_observation_v2.py` pose le
detachement a CHACAL_AVANT + 70 m ( l origine reste 330 m ). Fumee v2 : memes deux jobs, memes attentes, plus : l etape APPROCHE_ROUTE annonce
une distance de 40 a 110 m dans les deux reglages, et la fenetre s ouvre avant 150 s de mission.
