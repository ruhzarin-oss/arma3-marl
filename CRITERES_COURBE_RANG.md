# CRITERES — LA COURBE A RANG BORNE (les coups 1-10)

Ecrits AVANT tout chiffre.

## POURQUOI
Mesure du 04/09, cible invulnerable, 14 692 balles, 124 duels longs :
`p_touche` = **0,354** [0,328 ; 0,381] aux coups 1-10 contre **0,407** [0,394 ; 0,419] aux
coups 31-80, **IC disjoints, et la hausse persiste DANS les memes duels**. Le tireur
s ameliore au fil de l engagement.

La courbe en service a ete mesuree sur **6 135 coups tardifs contre 1 250 precoces** : elle
decrit un engagement INSTALLE. **Un assaut est fait de PREMIERS coups.** Elle surestime donc
le toucher des premieres rafales — la phase exacte qui decide d un bond.

## CE QU ON MESURE
Les 18 conditions (6 distances x 3 postures), **coups de rang 1 a 10 SEULEMENT**, cible
invulnerable, capteur repare (un impact par PROJECTILE, source appariee).
Blocs COURTS (20 s) : chaque duel ne fournit alors presque que des coups precoces. Ce n est
pas une astuce de rendement, c est le REGIME qu on veut mesurer.

## CE QUI FERAIT ECHOUER
- moins de **300 balles de rang 1-10** dans une condition -> condition NON RENDUE ;
- taux global a 100 m debout hors de **[0,30 ; 0,41]** -> l instrument a bouge, rien n est lu.
  (la borne haute est le 0,407 tardif, la borne basse tient compte du 0,354 precoce mesure) ;
- si la courbe a rang borne ne differe de celle en service dans AUCUNE condition au-dela des
  IC, alors le rang ne portait rien a l echelle des 18 conditions : on garde celle en service
  et on inscrit que le mélange etait sans effet pratique.

## CE QUI SERA POSE
`courbe_toucher_rang1_10.json` + `degat_par_impact = 0,175` (mediane 4,0 impacts jusqu a la
mort, n=83, capteur repare) — les deux ENSEMBLE, parce que les deux ont change d unite en
meme temps. Regle de lissage inchangee : PAVA en posture UNIQUEMENT la ou les IC se
recouvrent.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur ÉQ. 1, rien sur la prise. On rend une courbe et une conversion.
