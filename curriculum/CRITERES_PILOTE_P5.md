# Critères pré-enregistrés — pilote de la phase 5 : le délai du porteur selon la situation

*16/09/2026. Écrit et commité AVANT le lancement. Plan : `plans/plan-choix-par-vignette.md` (d148974).
Mission : ligne de décision, commit 8c9ae95. dbt : `pilote_p5`, tests `tag:decision`, lecture
`C:\hmt\dbt\outils\lire_pilote_p5.py` (dbt fb69b5a). La fumée FUMEE-DECISION-P5-16-09 doit être passée avant.*

## La question

La situation de phase 5 (menace de niveau 3 : alarme donnée avant l'assaut et deux défenseurs de plus) change-t-elle
la meilleure valeur du choix **DELAI_PORTEUR** (45 s ou 180 s) ?

## Ce qu'on sait déjà

- Sans menace, 180 s fait arriver plus de porteurs (90,1 % contre 95,0 %, 838 porteurs) et pose plus de charges en
  vignette (+11,1 points, IC [+0,7 ; +21,6]) ; l'effet sur la mission n'est pas démontré (verdict AMENDE).
- La menace de phase 5 pèse : alarme à 80 et 39 s contre 212 et 178 s, 2 tués contre 0 et 1 (2 épisodes par bras).

## Hypothèse écrite avant

Sans menace, 180 s aide ; avec l'alarme déjà donnée et deux défenseurs de plus, rester 3 minutes sur l'objectif
coûte des hommes, et l'avantage de 180 s diminue ou s'inverse.

## Dispositif

- Vignette `depart=4 arret=5 obs=0`, palier 4, socle 1, sans réserve, graine de situation 1.
- **2 choix** (delai_porteur 45 / 180) × **2 bras** (TÉMOIN menace_p5=0 / MENACE menace_p5=3) × **8 mondes**
  (graines 4, 5, 6, 7, 8, 9, 11, 12 : 8 sites distincts vérifiés) × **6 répétitions** = **192 épisodes**.
- Un job par (bras, choix, monde) : 32 jobs. Ordre de lancement par monde, les 4 cases d'un même monde côte à côte :
  les bras tournent en même temps sur la même charge machine (règle « apparier ET entrelacer »).
- Instances 1-8 et 10-13, attribuées en rotation ; nourrice à 12 serveurs au plus.

## Issues

- **Primaire** : `assaut_utile` = 3 charges posées **et** au moins 6 hommes vivants en fin d'assaut. Le succès de la
  mission exige 3 charges et 6 exfiltrés sur 10 : c'est ce que l'assaut doit laisser à l'exfiltration.
- **Secondaires, descriptives, sans décision** : `trois_charges`, `charges`, `tues_p5`, `vivants`.

## Portes de qualité, avant toute lecture d'effet (sinon : lecture refusée)

| porte | critère |
|---|---|
| Q1 | au moins 90 % des 192 épisodes ACCEPTE |
| Q2 | zéro erreur SQF |
| Q3 | tests dbt bloquants à zéro sur la campagne : décision présente et unique, choix conforme au job, choix exécuté, alarme lue après la pose, conséquence avant l'arrêt, zéro erreur SQF |
| Q4 | chaque case (monde, bras, choix) a au moins 4 épisodes acceptés |
| Q5 | observable vivant : alarme = 1 au moment du choix dans tous les épisodes MENACE |

## Critères

Moyennes par case, écarts appariés par monde, moyenne des 8 mondes à poids égaux, IC 95 % par 10 000
rééchantillonnages des mondes (graine 20260916).

| critère | définition | rôle |
|---|---|---|
| C1 | écart 180 − 45 dans le témoin | informatif |
| **C2** | **modulation** = écart MENACE − écart TÉMOIN ; établie si son IC exclut 0 | **décide** |
| C3 | inversion = C2 établie et écarts témoin et menace de signes opposés | qualifie |

- **C2 établie** : le choix DELAI_PORTEUR entre au curriculum et au gymnase v1.
- **C2 non établie** : le choix reste **choix témoin**, comme la porte.
- Le sens conforme à l'hypothèse (écart témoin > 0, modulation < 0) est rapporté, pas exigé.

## Puissance, écrite d'avance

Pour une issue binaire autour de 50 %, 6 épisodes par case donnent un écart-type d'environ 0,20 par case, 0,41 pour
la modulation d'un monde, environ 0,14 pour la moyenne des 8 : **une modulation de moins de ~30 points ne sera
pas établie**. Un résultat nul ne prouvera donc pas l'absence de modulation ; il dira qu'elle est plus petite que ça.

## Falsificateur

« Si C2 n'est pas établie, la menace de phase 5 n'a pas changé le meilleur délai du porteur à la précision de ce
dispositif, et le choix ne sert pas encore à apprendre à décider selon la situation. »

## Fumée préalable (FUMEE-DECISION-P5-16-09, 4 épisodes)

Attentes écrites dans ses jobs : zéro erreur, 4 ACCEPTE, marqueur présent, une décision par épisode juste avant le
premier pas de l'assaut, choix égal au job, porteurs au délai décidé, alarme = 1 au choix côté menace, fin de phase 5
écrite, même site que SITUATION-PAR-PHASE-16-09. **Si une attente échoue, le pilote ne part pas.**
