# Critères pré-enregistrés — chercheur de causes CHACAL, v0

*16/09/2026. Écrit et commité AVANT la première recherche. Aucune sortie du chercheur n'a été lue.*

## Ce que fait le chercheur

Il répond seul, sans qu'on lui dise où regarder, à trois questions sur les épisodes Arma déjà joués :

1. **Qu'est-ce qui cause quoi ?** Pour chaque levier forcé par un job, il compare les épisodes qui ne diffèrent
   **que** par ce levier : même monde, mêmes autres leviers. Seul un levier forcé peut établir une cause.
2. **Pourquoi ?** Pour chaque cause trouvée, il cherche par quoi elle passe : les variables que le levier fait bouger
   et qui, à levier égal, expliquent l'issue. Puis il recommence sur la variable trouvée, ce qui donne le pourquoi du
   pourquoi.
3. **Où chercher ensuite ?** Les variables liées au succès qu'aucun levier ne contrôle encore. Ce sont des
   **corrélations, pas des causes** : chacune devient une campagne Arma à proposer, jamais lancée sans accord.

## Données

- `extraire_variables.py` : chaque ligne écrite par le banc devient des variables selon une règle générique, sans
  liste à la main. 1 973 épisodes, 823 variables, 42 champs de job.
- **Exclus** : verdict non ACCEPTE, erreur SQF, épisodes sans campagne (ère d'avant les campagnes), et
  **SITUATION-PAR-PHASE-16-09 et FUMEE-SITUATION-16-09** : la campagne des menaces tourne encore et a ses propres
  critères ; le chercheur ne doit pas la lire avant.
- Porte : levier dérivé `porte_B` = 1 si la campagne commence par `PORTE-` et que la version contient `-B-`, 0 sinon.
  Il remplace `azimut_val`, propre à chaque monde.

## Méthode

- **Strate** : (campagne, site, valeur de tous les autres leviers). C'est la lecture **entrelacée**.
  Une seconde lecture retire la campagne de la strate : elle est dite **non entrelacée**, exposée à la dérive
  entre campagnes, et ne peut qu'étayer.
- **Statistique** : écart moyen entre les deux valeurs du levier, pondéré par strate (na·nb/(na+nb)).
  Au moins 5 épisodes par valeur.
- **p** : 1 000 permutations du levier **à l'intérieur des strates**, et z tiré de la distribution permutée.
- **Familles et contrôle du taux de fausses découvertes (BH, q = 5 %)** :
  - **Effets** (famille E, tous leviers ensemble) : `fini|charges`, `fini|detruits_scriptes`, `fini|exfiltres`,
    `fini|vivants`, `fini|pertes_est`, `fini_issue=SUCCES`, `fini|duree`.
  - **Variables intermédiaires** (famille M, par comparaison) : toutes les autres variables sans valeur manquante
    dans la comparaison.
- **Pourquoi** : pour chaque découverte de la famille E, chaque intermédiaire découvert en famille M est testé par
  régression intra-strate : proportion de l'effet qui passe par lui = 1 − β(levier | intermédiaire) / β(levier).
  IC par 300 rééchantillonnages dans les strates. Une variable corrélée à plus de 0,95 avec l'effet est une
  **tautologie** (la même mesure sous un autre nom) et ne compte pas comme raison.
- **Placebos** : 5 faux leviers (parité d'un hachage de l'identifiant d'épisode), passés dans la même machine, à part.

## Contrôles : le chercheur n'est cru que s'il les réussit

| contrôle | ce qu'il doit trouver seul | connu par |
|---|---|---|
| **C+1** | `socle` 0 → 1 augmente `fini|charges` | `socle-execution-10-sur-10` : 1/10 contre 10/10 |
| **C+2** | au moins une `tactique` ≠ 0 contre 0 diminue `fini|charges` | même verdict : infiltration 2/10 contre socle seul 10/10 |
| **C+3** | `arret` 5 → 6 augmente `fini_issue=SUCCES`, et une variable de phase 6 (`ph|6|…`) figure parmi les 5 premières raisons | `victoire-bout-en-bout-47-pourcent` : à `arret=5` le succès est impossible |
| **C+4** | lecture non entrelacée : `delai_porteur` 45 → 180 augmente `fini|charges`, et une variable du porteur (nom contenant `porteur` ou `PORTEUR`) figure parmi les 3 premières raisons | `delai-porteur-le-mecanisme-tient-pas-le-resultat` : porteurs à bout de délai 34 % contre 9 % |
| **C−1** | `porte_B` : aucune découverte sur `fini|charges`, `fini|detruits_scriptes`, `fini_issue=SUCCES` | `la-porte-nest-pas-une-decision` |
| **C−2** | au plus 1 placebo sur 5 avec au moins une découverte, dans l'une ou l'autre famille | le hasard |

Un contrôle dont la comparaison n'existe pas dans les données (moins de 5 épisodes par valeur dans les strates
communes) est déclaré **non testable**, pas réussi.

**Le chercheur est cru si tous les contrôles testables passent, avec au moins 3 contrôles positifs testables.**
Sinon ses trouvailles ne sont pas publiées comme résultats, et on écrit pourquoi.

## Limites écrites d'avance

- Il ne voit que ce que le banc écrit : une cause qui ne laisse pas de ligne dans les journaux lui est invisible.
- Les variables avec des valeurs manquantes (temps d'un événement qui n'a pas eu lieu) sont écartées dans les
  comparaisons où elles manquent.
- La « raison » est une variable intermédiaire mesurée, pas un mécanisme prouvé. La prouver demande de forcer
  cette variable dans Arma.
- Les trouvailles de la question 3 sont des corrélations : elles ne deviennent des causes qu'après une campagne Arma.
