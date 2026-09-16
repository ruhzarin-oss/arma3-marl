# Critères pré-enregistrés — gymnase de décisions CHACAL, v0

*16/09/2026. Écrit et commité AVANT le premier calcul de prédiction. Aucune prédiction du gymnase n'a été lue.*

## Ce qu'est le gymnase v0

Le gymnase ne simule pas de combat. Il **rejoue ce qu'Arma a produit** : pour une situation et un choix, il tire
l'issue parmi les épisodes Arma joués dans cette situation avec ce choix. Il enchaîne deux phases :

- **phase 5 (assaut)** : pour un monde, une porte et un délai de porteur, il tire un épisode Arma réel et en lit
  l'état à la fin de l'assaut : charges posées (0 à 3), hommes vivants.
- **phase 6 (exfiltration)** : pour cet état, il tire le succès de la mission avec la probabilité mesurée dans Arma.

Le choix qui n'a jamais été joué dans Arma est **interdit** dans le gymnase ; il n'est jamais extrapolé.

## Ce qui a été vu avant d'écrire ces critères

L'inventaire des données (couverture par monde, levier et phase) et une table de succès en phase 6 par hommes
vivants. Elle montre déjà une limite : à 7 vivants, 0 succès sur 9 à `depart=3` contre 15 sur 16 à `depart=5`.
« Vivants » ne suffit donc pas comme état d'un départ à l'autre, et le v0 est **restreint à `depart=5`**.

## Données

**Base** : verdict ACCEPTE, 0 erreur SQF, palier 4, socle 1, effectif 10, sans oracle, ablation, banc d'appui,
placeur, immortel ni jour ; tactique, appui_feu, feu_avant, mg_assaut, appui_fixe à 0 ; sans partage, réserve,
situation ni accélération ; `depart=5` ; mondes 7, 8, 11, 12.

**Construction de la phase 5** : REFERENCE-PROPRE-13-09, REFERENCE-JAMBES-13-09 (porte du script, 45 s),
DELAI-PORTEUR-14-09 (180 s), PORTE-A-CONTRE-PORTE-B-14-09, PORTE-B-CONTROLE-14-09, PORTE-HUIT-MONDES-15-09.
Porte : B si la version du job contient `-B-`, A sinon. La porte du script est la porte A : le verdict
`le-script-ne-choisit-pas-son-ouverture` la trouve gelée à la première porte dans 145 épisodes sur 145.

**Construction de la phase 6** : REFERENCE-PROPRE-13-09 et REFERENCE-JAMBES-13-09 (`arret=6`).

**Test, jamais lu par la construction** : CONFIRMATION-MISSION-15-09 — 96 épisodes, mondes 7, 8, 11, 12,
12 épisodes par monde et par bras, bras 45 s et 180 s, porte A, `arret=6`.

## Modèles

- **Phase 5** : distribution empirique de (charges, vivants) en fin d'assaut par (monde, porte, délai).
- **Phase 6** : si charges < 3, échec. Sinon P(succès | monde, classe de vivants ≤ 6 / 7-8 / 9-10), rétrécie vers
  le taux de la classe tous mondes confondus avec un poids de 4 épisodes fictifs. Contrôle bloquant : aucun succès
  à moins de 3 charges dans les données de construction, sinon le calcul s'arrête.
- **Prédiction d'un bras** : moyenne des 4 mondes à poids égaux (le test a 12 épisodes par monde et par bras).
- **Incertitude du gymnase** : 2 000 rééchantillonnages des épisodes Arma, dans chaque cellule.

## Portes

| porte | question | critère | nature |
|---|---|---|---|
| G1 | bras 45 s | prédiction du gymnase dans l'IC de Wilson 95 % du bras 45 s d'Arma | transfert, bloquante |
| G2 | bras 180 s | prédiction du gymnase dans l'IC de Wilson 95 % du bras 180 s d'Arma | transfert, bloquante |
| G3 | enchaînement | parmi les épisodes test entrés en phase 6 avec 3 charges : écart des succès observés aux succès attendus, \|z\| ≤ 2 | markov, bloquante |
| G4 | phase 5 seule | taux de 3 charges prédit dans l'IC de Wilson 95 % d'Arma, par bras | diagnostic : localise une erreur |
| G5 | effet du délai | signe de l'écart 180 − 45 du gymnase = signe de l'écart Arma | informative : l'écart Arma n'est pas établi (+10,4, IC [−8,3 ; +29,2]) |
| G6 | porte témoin | IC 95 % de l'écart B − A du gymnase (mission, 45 s) contient 0 | cohérence : mêmes données que le verdict de la porte, ce n'est pas un transfert |
| N | naïf | erreur absolue du gymnase contre celle du taux de référence constant (52,8 %) sur les deux bras | informative |

**Le v0 est validé si G1, G2 et G3 passent.** Sinon il ne sert pas à entraîner, et on écrit pourquoi.

## Apprentissage (seulement si le v0 est validé)

- Environnement : monde tiré au hasard parmi les 4 ; l'agent ne voit pas le monde ; choix parmi les options
  mesurées (45 s porte A, 45 s porte B, 180 s porte A ; 180 s porte B est interdit : jamais joué).
- Apprenant : Q tabulaire, moyenne d'échantillons, ε-glouton ε = 0,1, **1 000 000 épisodes par graine, 5 graines**.
- L1 : les 5 graines finissent sur le même choix, celui du calcul exact, et \|Q − valeur exacte\| < 0,01 partout.
  C'est un contrôle positif de la recette (la recette précédente était une loterie : 49,6 % ou 3,3 % selon la graine).
- L2 : la meilleure option ne compte comme une découverte que si l'IC 95 % de son avance sur la deuxième exclut 0.
- L3 : aucune préférence établie entre les portes A et B.

## Limites écrites d'avance

- Mondes connus : le test tient des épisodes à l'écart, pas des mondes. Ce n'est pas un examen sur mondes jamais vus.
- Une seule décision réellement mesurée (le délai du porteur), plus une décision témoin (la porte).
- La campagne test tourne sur une autre charge machine que la référence (43,8 % contre 52,8 % sur les mêmes mondes,
  verdict `un-taux-porte-sa-charge-machine`) : une partie de l'erreur possible vient d'Arma lui-même.
