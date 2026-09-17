# Critères pré-enregistrés — banc des Oracles (BoTorch, QDax), sans Arma

*17/09/2026, vers 15 h 30. Demandé par Younes : « test les deux maintenant en profondeur ». Suite de
`plans/plan-architecte-oracle.md` (§ 4 et 4 bis). Écrit et commité avant les répétitions 0 à 19. Une seule lecture,
quand tout est calculé : `oracle/lire_banc_oracle.py`.*

## La question

Avec un budget de 1920 épisodes bruités, quel Oracle trouve le plus de **failles vraies** d'une règle fixe, sans en
inventer ? Et lequel trouve des failles **différentes** ?

## Le banc (`oracle/mondes.py`)

**Les situations.** θ = (distance, moment, leurre) dans [0, 1]³. Le leurre n'agit jamais.

**Le regret signé.** r(θ) = P(réussite | autre option) − P(réussite | règle) : c'est le regret de la règle. La règle
réussit 35 % du temps. Une **faille vraie** est une situation où r > 0,10.

**Un épisode.** L'option est tirée à pile ou face, puis :

```
z = 2·Y·(1{autre option} − 1{règle})        E[z | θ] = r(θ)
```

**Les mondes cachés**

| monde | failles | aire des failles |
|---|---|---|
| W0 nul | aucune (r = −0,25 partout) | 0 |
| W1 aiguille | une bosse étroite, pic +0,55 | 1,9 % |
| W2 quatre | quatre bosses séparées, pics +0,55, +0,50, +0,45 et +0,40 | 11,7 % |
| W3 large faible | une bosse large, pic +0,25 | 17,5 % |

**Budget.** 20 tours de 96 épisodes, soit 1920. Chaque oracle choisit où les jouer.

**Confirmation commune.** Chaque oracle propose au plus 8 candidats, séparés de plus de 0,15 en (distance, moment).
Chaque candidat reçoit 150 épisodes neufs, avec la même graine pour tous les oracles au même rang. Il est déclaré
faille si z̄ − 2,326·se > 0.
- **Régions trouvées** : les bosses dont la faille contient au moins un candidat déclaré.
- **Fausse faille** : un candidat déclaré avec r vrai ≤ 0.

## Les oracles, réglages fixés

| oracle | réglages |
|---|---|
| `uniforme` | 480 situations tirées au hasard × 4 épisodes ; candidats = meilleurs z̄ (borne basse) |
| `cases_plan` | l'Oracle du plan : 50 cases (5 × 5 × 2), U = z̄ + se, poids exponentiels ν = 3, part uniforme η = 0,2 ; candidats = situations explorées au meilleur z̄ |
| `parfait` | connaît les bosses et candidate leurs centres (borne haute de la confirmation) |
| `botorch_ts` | GP `SingleTaskGP`, bruit fixe 0,5, réglages par défaut de BoTorch 0.18.1 ; lot de 24 situations par échantillonnage de Thompson (`MaxPosteriorSampling`, 4000 situations tirées) ; candidats = maxima de la moyenne a posteriori sur 20 000 situations |
| `botorch_ts_court` | le même, avec des longueurs de corrélation bornées à [0,02 ; 0,30] (noyau RBF avec échelle) |
| `qdax_me4` | QDax 0.5.0, MAP-Elites en ask / tell sur les mêmes épisodes simulés ; grille 10 × 10 en (distance, moment) ; variation isoline (0,05 ; 0,10) ; 24 situations × 4 épisodes par tour ; candidats = élites au meilleur fitness |
| `qdax_me8` | le même, 12 situations × 8 épisodes par tour (fitness moins bruitée, même budget) |

## Calibrage et fumées faits avant (graines ≥ 1000, disjointes du banc)

**Oracle parfait** (puissance de la confirmation, 200 répétitions) :
- W1 : 0,98 région trouvée ;
- W2 : 3,73 sur 4 ;
- W3 : 0,45, car l'effet est faible et la confirmation a peu de puissance ;
- W0 : 0 fausse faille.

**Repères (40 répétitions)**

| oracle | W1 | W2 | fausses failles |
|---|---|---|---|
| uniforme | 0,55 | 1,73 | 0 |
| cases_plan (candidats = situations explorées) | 0,70 | 2,12 | — |

Une première version de `cases_plan` candidatait les centres de cases. Ils tombent hors des failles étroites : 0,10
région en W2. Elle a été corrigée avant le banc.

**Fumées de BoTorch**
- En qUCB (β = 4, optimisation séquentielle) : 322 s par répétition, et seulement 3,75 % du budget dans les failles de
  W2. **Abandonné.**
- En Thompson par défaut : 7 s par répétition, mais une longueur de corrélation de 1,44 sur la distance. Les failles
  étroites sont lissées, 24 % des situations sont jouées en bord d'espace, et 0 région est trouvée en W2 comme en W1
  (une répétition chacun). D'où la variante `court`, qui apprend des longueurs de 0,105 et 0,112 et place ses
  candidats près des bosses.

**Fumée de QDax** : 1,3 à 7,7 s par répétition, 0 à 2 régions en W2, 0 ou 1 en W1 (2 répétitions par variante).

## Critères (20 répétitions par oracle et par monde)

- **Contrôle nul** : dans W0, au plus 1 répétition sur 20 avec au moins une faille déclarée.
- **UTILE** : le contrôle nul tient, **et** l'une des deux conditions suivantes :
  - l'aiguille (W1) est trouvée dans au moins 5 répétitions de plus que l'uniforme ;
  - la moyenne de régions trouvées en W2 dépasse celle de l'uniforme d'au moins 1.
- **Comparaison au plan** : écart de régions trouvées avec `cases_plan`, en W1, W2 et W3, avec un IC 95 % par
  rééchantillonnage des répétitions. Descriptif, sans décision.

**Attendu écrit avant**
- BoTorch court est le meilleur sur l'aiguille et la faille large, car il exploite.
- QDax est le meilleur en diversité, sur les quatre failles de W2.
- BoTorch par défaut est pauvre, car il lisse trop.
