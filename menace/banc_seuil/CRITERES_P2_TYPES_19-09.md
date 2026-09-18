# Criteres pre-enregistres - CHOIX-P2-TYPES-19-09 : traverser ou attendre, selon le TYPE de menace, menace visible au moment du choix

*Nuit du 18 au 19/09/2026. Ecrit AVANT le lancement, pendant la grille de variance. Autorisation de Younes ( 18/09, ~22 h 55 ) : « tu peux lancer
P2, assure-toi de faire du vrai bon travail ». Suite de `plans/plan-choix-par-vignette.md`, de `curriculum/CRITERES_CHOIX_17_09.md` ( dont ce fichier
reprend le dispositif et le classement ) et de `plans/plan-menace-visible.md`. Banc : `bancs/chacalp2` ( copie de `bancs/chacal`, deux leviers
d observation ). **Cette campagne ne part que si la regle de `CRITERES_VARIANCE_OBSERVATION_19-09.md` a designe un reglage admissible** ; le
reglage retenu est inscrit en bas de ce fichier avant la pose des jobs.*

## La question
Le 17/09, CHOIX-P2 ( menace de niveau 3 contre temoin ) a classe le choix INDIFFERENT, et la ligne de decision ne percevait presque rien.
L hypothese du plan etait ailleurs : **patrouille qui roule : attendre ; poste fixe : attendre ne sert a rien**. Ici les deux bras sont les deux
TYPES de menace, poses seuls et pres ( niveaux 4 et 5 de 16e4b32 ), et le detachement observe 90 s avant de choisir.
Le type de menace change-t-il la meilleure option ? Et ce que le detachement PERCOIT au moment du choix le dit-il ?

## Dispositif
- 2 options ( traversee = 1 tout de suite, 2 attendre ) x 2 bras ( menace_p2 = 4 PATROUILLE motorisee seule, 5 POSTE de controle seul )
  x 8 mondes ( 4, 5, 6, 7, 8, 9, 11, 12 ) x **4 graines de situation ( 1, 2, 3, 4 ), une repetition chacune** = 128 episodes.
  Ecart assume au dispositif du 17/09 ( situation 1, 4 repetitions ) : mesure du 18/09, deux repetitions d un meme ( monde, situation ) sont
  identiques ( scene deterministe ). Quatre placements par monde apprennent plus que quatre copies, et c est le placement qui fait varier la
  perception a l interieur d un monde ( la porte de `lire_variance.py` ).
- Un job = une paire de mondes ( 4-5, 6-7, 8-9, 11-12 ), une option, un bras, une graine de situation : 64 jobs, melanges ( graine 1929 ) sur
  12 instances, reequilibres vers les instances libres. Fenetre de 90 s ( fixee par Younes ), palier 4, socle 1, vignette `d2a2`, de nuit.
- Fumee FUMEE-P2-TYPES-19-09 avant la campagne : 2 jobs ( PATROUILLE / attendre et POSTE / tout de suite ), mondes 4 et 5. Attentes : 0 erreur SQF,
  ACCEPTE, une decision TRAVERSEE conforme au job, `choix_joue` du meme choix, le type pose est celui du bras et lui seul, reglage joue = reglage
  du job, fin de phase 2 ecrite. Un seul echec : rien ne part.

## Portes de qualite, avant toute lecture d effet ( sinon : lecture refusee ) - `lire_p2_types.py`, ecrit avant
Q1 au moins 90 % des 128 episodes ACCEPTE ; Q2 zero erreur SQF ; Q3 une decision TRAVERSEE par episode, choix conforme au job, choix joue
conforme ; Q4 chaque case ( monde, bras, option ) a au moins 3 episodes ; Q5 le type pose est celui du bras, et lui seul ; Q6 le reglage
d observation joue est celui du job. Amendements 2 et 3 du 17/09 repris tels quels ( remplacement des episodes refuses par l enregistreur ;
retrait d un monde dont une case reste sous le seuil, lecture sur 6 mondes au moins, `--sans-monde N` ).

## Issue primaire, criteres et classement ( identiques au 17/09 )
`phase_discrete` : fin de la phase 2 sans compromission, sans alarme, dix vivants. Moyennes par case ; ecarts ( ATTENDRE - TOUT_DE_SUITE )
apparies par monde ; mondes a poids egaux ; IC 95 % par 10 000 reechantillonnages des mondes ( graine 20260919 ).
- **Modulation** = ecart PATROUILLE - ecart POSTE.
- **DEPENDANT du type de menace** : IC de la modulation excluant 0. **DOMINE** : sinon, et l IC de l ecart moyen des deux types exclut 0.
  **INDIFFERENT** : ni l un ni l autre, a la precision du dispositif.
- Hypothese ecrite avant : PATROUILLE, attendre vaut mieux ( ecart positif ) ; POSTE, attendre ne sert a rien ( ecart nul ou negatif : on reste
  plus longtemps a portee d un poste qui regarde la route ) -> modulation POSITIVE. Sens et inversion : rapportes, pas exiges.

## La perception au moment du choix ( descriptif, sans decision - c est la matiere de l Architecte )
Par bras : part des episodes ou `menace_percue > 0`, ou la menace est connue ( niveau 2 ), ou `vehicule_vu = 1`. Puis `phase_discrete` par option
selon que la menace etait percue ou non, et la liste des mondes ou la perception varie d un episode a l autre. Aucune regle n est ajustee ici.

## Puissance, ecrite d avance
Issue binaire, 4 episodes par case, 8 mondes : l ecart-type de la modulation moyenne vaut environ 0,18. **Une modulation de moins de ~35 points ne
sera pas etablie.** Un « indifferent » dira seulement que l effet est plus petit que ca. Si l issue est presque toujours 1 ( temoin du 17/09 : 1,000 ;
menace de niveau 3 : 0,77 ), la precision est meilleure mais l information plus pauvre : c est rapporte.

## Falsificateur
« Si la modulation n est pas etablie, le type de menace ne change pas la meilleure option a la precision de ce dispositif, et le choix de la phase 2
ne sert pas encore a apprendre a decider selon la situation - meme avec une menace visible. »

## Limites dites d avance
La mission jouee est une COPIE ( `chacalp2` ) dont le point d observation et le balayage peuvent differer de `bancs/chacal` : le resultat vaut pour
le reglage inscrit ci-dessous, et il est a rejouer sur `bancs/chacal` si Younes adopte ce reglage. La copie n est pas branchee sur dbt : les tests
`tag:decision` sont remplaces par les portes Q3, Q5 et Q6 du lecteur. Machine partagee avec le banc de perception ( charge archivee par run ).

## Reglage retenu par la regle de variance ( inscrit avant la pose des jobs )
A REMPLIR : avant = ... m, balayage = ... ; parts percue / connue de la grille ; ou « AUCUN REGLAGE ADMISSIBLE : la campagne ne part pas ».
