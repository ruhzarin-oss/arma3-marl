# Aucun algorithme d'équation n'est retenu à 500 épisodes ; EvoGP est le seul à trouver les trois formes, à 1000

*17/09/2026 — statut ETABLI — domaine : méthode (banc d'équation, sans Oracle)*
*Critères pré-enregistrés : `equation/CRITERES_BANC_EQUATION.md` (41f2ae6, correctif d'export 2d0f6ac, amendement 1
EvoGP 4c40b54, correctif de contiguïté c38077a ; tous avant les calculs concernés). Sorties :
`equation/resultats/lecture_synthetique.txt`, `lecture_arma.txt`, `lecture_arma_evogp.txt`. Plan :
`plans/plan-architecte-oracle.md`.*

## Énoncé

**Test A (synthétique, vérité connue).** Aucun des 5 algorithmes ne retrouve les trois formules cachées au moins
18 fois sur 20 à n = 500 : aucun n'est **RETENU**. Aucun n'invente de formule quand il n'y en a pas (au plus 1 fausse
sur 20, à tout n). La logistique L1 est la meilleure sur les formes linéaire et seuil (19/20 et 19/20), mais **ne peut
pas** représenter la croix (0/20), comme écrit d'avance. **EvoGP (GPU) est le seul à retrouver la croix** ; à n = 1000,
il retrouve les trois formes (19, 19 et 20 sur 20), sans aucune fausse formule.

**Test B (vrais épisodes Arma : P1, P2, P4, pilote P5).** Aucun algorithme ne déclare de gain sur la meilleure option
fixe, comme attendu : au moment du choix, les perceptions sont presque constantes.

## Test A : formules retrouvées sur 20 (déclarée à 1 % et accord ≥ 0,80)

| algo | F1 linéaire n=500 | F2 croix n=500 | F3 seuil n=500 | F1 / F2 / F3 à n=1000 | fausses sous F0 (200/500/1000) | durée d'un essai |
|---|---|---|---|---|---|---|
| l1 | **19** | 0 | **19** | 20 / 0 / 20 | 1 / 0 / 0 | 1 s |
| arbre | 12 | 0 | **18** | 18 / 1 / 20 | 0 / 0 / 0 | 0,3 s |
| gplearn | 2 | 0 | **18** | 7 / 0 / 20 | 0 / 0 / 0 | 43 s |
| evogp | 14 | 7 | 15 | **19 / 19 / 20** | 0 / 0 / 0 | 2 s |
| evogp_p01 | 14 | 3 | 14 | 18 / 1 / 20 | 0 / 0 / 0 | 1,7 s |

Exemples de formules apprises (n = 1000, première répétition) :
- evogp_p01 sur F1 : `0,50 − distance` ; sur F3 : `max((alarme − distance) − 0,25 ; −0,50)`. Lisibles et justes, mais
  il manque `vehicule_vu` en F1.
- evogp sur F2 : `(0,50 + min(0 ; −((0,50 × (moment > 0,50)) > 0,25))) × −(distance > 0,50)`. Juste, peu lisible.
- gplearn : formules chargées de leurres (en moyenne 0,3 à 2 leurres par formule).

## Ce que cela apprend

1. **Aucun algorithme ne gagne partout.** Le linéaire est imbattable quand la forme est linéaire ou presque, et aveugle
   à la croix. La programmation génétique sur GPU est la seule à voir la croix, mais elle demande deux fois plus
   d'épisodes et produit des formules chargées si la parcimonie est faible.
2. **La parcimonie est le vrai réglage.** À 0,001 par nœud, EvoGP trouve la croix mais prend des leurres (1,2 à 2,3 par
   formule). À 0,01, il ne prend presque plus de leurres, mais il manque la croix. Il faudra la choisir par validation
   croisée, pas à la main.
3. **La vitesse change ce qui est possible.** EvoGP explore environ 30 fois plus de formules que gplearn, en 20 fois
   moins de temps. Pour l'Architecte du plan, c'est le candidat du niveau 2 (nouvelle forme).
4. **Sur Arma, aucune équation ne peut encore rien apprendre** : la ligne de décision ne perçoit pas la menace au
   moment du choix. Le niveau 3 du plan (nouvelle perception) passe avant tout algorithme.

## Fautes et pièges évités

- **Banc indétectable par construction** (corrigé avant le calcul, 41f2ae6) : avec les premiers effets (±1 à ±2 logits),
  même la bonne règle n'était déclarée que 9 % (croix) à 80 % (seuil) du temps à n = 500. Vu par la fumée à graines
  disjointes, recalibré sur le générateur seul.
- **Export du test B** (2d0f6ac) : la table `pilote_p5` contenait aussi les épisodes CHOIX-P6 et la fumée ; filtrés
  avant tout calcul.
- **EvoGP sur données pandas** (c38077a) : les noyaux CUDA exigent un tableau contigu ; le test B plantait, le test A
  n'est pas touché.
- **Lecture d'EvoGP avant la fin de gplearn**, à la demande de Younes : aucun réglage ne pouvait plus changer, les
  critères étaient commités.

## Falsificateur pré-enregistré

« Un algorithme n'est retenu que s'il retrouve F1, F2 et F3 au moins 18 fois sur 20 à n = 500 et ne déclare F0 qu'au
plus 1 fois sur 20. » — **aucun retenu.**
