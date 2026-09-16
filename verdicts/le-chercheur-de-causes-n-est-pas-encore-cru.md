# Le chercheur de causes n'est pas encore cru

*16/09/2026 — statut REFUTE (l'hypothèse « le chercheur est digne de confiance » est refusée par ses propres contrôles)
— domaine : instrument*
*Critères : `chercheur_causes/CRITERES_CHERCHEUR_CAUSES_V0.md` (6bedbad), amendés par `CRITERES_CHERCHEUR_CAUSES_V1.md`
(00d8623), tous deux écrits avant la recherche qu'ils jugent.*

## Énoncé

Un chercheur automatique de causes, qui fabrique seul ses 618 variables à partir des journaux du banc et compare les
épisodes qui ne diffèrent que par un levier forcé, **retrouve les causes fortes** (le socle, la tactique, l'arrêt de
l'épisode, l'absence d'ennemi) et **ne voit plus rien sur ses placebos** une fois sa statistique corrigée. Mais il
**rate un mécanisme établi** : 180 s de délai font moins manquer les porteurs (0,32 → 0,18 charge manquée par épisode,
p = 0,004), et la correction pour tests multiples le laisse à q = 0,0502, juste au-dessus du seuil de 0,05. Selon la règle écrite
d'avance, ses trouvailles ne sont pas publiées comme résultats.

## Ce que fait le chercheur

1. **Variables** (`extraire_variables.py`) : chaque ligne écrite par le banc devient des variables par une règle
   générique — comptes par clé et par phase, valeurs catégorielles, maxima numériques, géométrie du monde, états de
   phase, ligne FINI. 1 973 épisodes, 823 variables, dont 618 assez présentes.
2. **Causes** : pour chaque levier forcé par un job, comparaison des épisodes du même monde avec les mêmes autres
   leviers, permutations du levier à l'intérieur de ces strates, BH à 5 %. Lecture entrelacée (même campagne) et non
   entrelacée (campagnes différentes, exposée à la dérive). 1 556 épisodes, 25 leviers, 64 comparaisons.
3. **Raisons** : les variables intermédiaires que le levier bouge et qui, à levier égal, portent l'effet (régression
   intra-strate), séparées de la **décomposition** (l'effet redit autrement). Puis le pourquoi du pourquoi.
4. **Pistes** : les corrélations au succès qu'aucun levier ne contrôle, marquées « levier à construire ».

## v0 — non cru

| contrôle | résultat |
|---|---|
| C+1 socle → charges | passe |
| C+2 tactique → charges | passe (tactique 5) |
| C+3 arrêt → succès | non testable : l'arrêt varie toujours avec le départ dans une même campagne |
| C+4 délai du porteur → charges | échoue |
| C−1 porte | passe |
| **C−2 placebos** | **échoue : les 5 faux leviers « découvrent » 19 à 32 variables intermédiaires chacun** |

**Faute n°1 (calcul).** Les découvertes des placebos étaient des variables **constantes dans chaque strate**
(géométrie du monde, événements présents dans toute une strate). Le levier ne peut pas les bouger ; la statistique
permutée est constante, son écart-type vaut le bruit d'arrondi, et le z (jusqu'à 19) sortait de ce bruit :
p normal = 0, p mesuré par 20 000 permutations = 1,0. **Seul le placebo l'a attrapée.**

**Faute n°2 (pré-enregistrement).** C+4 portait sur l'effet du délai sur les charges, alors que ce verdict est
AMENDE : effet non démontré (p = 0,219). Seul le mécanisme est établi (porteurs arrivés 90,1 % contre 95,0 %).

## v1 — pas cru non plus

Garde de variance intra-strate, p empirique à 20 000 permutations, raisons séparées de la décomposition, C+4 remplacé
par son mécanisme. Rien d'autre ne change.

| contrôle | résultat |
|---|---|
| C+1 socle 0 → 1 | **passe** : charges 1,50 → 2,67, q = 0,020 |
| C+2 tactique 0 → 5 | **passe** : charges 2,67 → 1,30, q = 0,020 |
| C+3 | non testable |
| **C+4′ délai 45 → 180, charges manquées faute de porteur** | **échoue** : 0,32 → 0,18, z = −2,84, p = 0,0043, **q = 0,0502** (105 variables testées) |
| C−1 porte | **passe** : aucune fausse découverte, dans les deux lectures |
| C−2 placebos | **passe** : 0 placebo sur 5 avec une découverte (contre 5 sur 5 en v0) |

## Ce qu'il a trouvé (non publié comme résultat, noté pour mémoire)

- `arret` 5 → 6 : succès 0 → 0,48, parce que la phase 6 est jouée (`ph|6|issue=ATTEINT`, part 1,00). Juste, et évident.
- `socle` 0 → 1 : charges +1,2, en partie par davantage de porteurs envoyés (`n|e|porteur`, part 0,35).
- `tactique` 5 : charges −1,4, entièrement par moins de porteurs envoyés (part 1,01, IC [0,74 ; 1,41]).
- `palier` 9 (pas d'ennemi) : 0 ennemi tué (il n'y en a pas), 10 vivants, 3 charges.
- Les raisons restent **peu profondes** : souvent une réécriture proche de l'effet (`n|e|ordre` pour l'arrêt).

## Ce que cela apprend

1. **Sans placebo passé dans la même machine, le v0 aurait publié 20 à 30 fausses raisons par levier.**
2. **Le goulot est la puissance, pas la méthode** : le mécanisme du porteur a le bon signe, p = 0,004, et il est dilué
   par la correction sur 105 variables, dont des doublons exacts (`n|e|porteur` et `n|e|porteur|p5` portent la même valeur).
3. **Les données forcées sont minces** : la plupart des leviers ne varient que dans 2 strates de 10 à 34 épisodes.
   Le chercheur deviendra utile quand Arma fera varier des leviers entrelacés sur beaucoup de mondes, ce que la couche
   de situation (menaces des six phases) commence à faire.

## Pour un v2 (pas le même jour, critères à écrire d'abord)

- Fusionner les variables identiques avant de compter les tests.
- Ordonner les raisons dans le temps : une raison doit précéder l'effet.
- Y verser les campagnes entrelacées à venir (menaces, partage).
- Faire écrire au chercheur, pour chaque piste « levier à construire », un projet de job — **jamais mis dans la file
  sans accord**.

## Falsificateur pré-enregistré

« Si un contrôle testable échoue, les trouvailles ne sont pas publiées comme résultats. » — **franchi, deux fois.**
