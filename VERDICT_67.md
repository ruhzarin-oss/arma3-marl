> ⛔ **ANNULÉ le 16/08/2026** — mesure faite avec les attaquants en `combatMode "BLUE"`,
> qui signifie « ne jamais tirer ». Les hommes n'ont pas combattu. Voir `REGISTRE_BLUE.md`
> et `VERDICT_ARME.md` (30/67 = 44,8 % une fois armés).

# Les 67 épisodes — l'écart de transfert est SERRÉ, le gel est RÉEL, B reste illisible

Mesuré le 15/08/2026, 15h53. Critères déposés le matin (`15b1a7d`), avenant (`b820d0c`),
clarification de B écrite **avant lecture** (`83adbd6`). 67 épisodes sur 67, aucun écarté.

## Les deux contrôles positifs passent

- scène confirmée par **le jeu** : `def=4 att=4` sur **67/67** ;
- azimuts de naissance, écart-type **94,4°** (porte corrigée : > 60°).

## 1. LA PRISE — l'écart de transfert tient, et cette fois serré

```
ARMA      8 / 67 = 11,9 %      IC95 [4,2 ; 19,7]
GYMNASE                59,4 %
```

**59,4 % est hors de l'intervalle.** À ±8 points au lieu de ±22, le verdict de
`VERDICT_TRANSFERT.md` n'est plus une indication : il est **serré**.

Rappel de la trajectoire : 0/20 (corps bridé) → 3/20 = 15 % → **8/67 = 11,9 %**. Le corps
réparé a sorti la prise de zéro et l'a stabilisée autour de 12 %. **Elle ne monte pas
au-delà.**

## 2. LE GEL — établi, après avoir été masqué trois fois par ma faute

```
ARMA     17 / 67 = 25,4 %      IC95 [15,0 ; 35,8]
gymnase de référence     3,1 %
```

**3,1 % est exclu de l'intervalle. Le gel est RÉEL.**

Ma bande « 4 à 17 sur 20 = indécis » l'avait déclaré non tranché **trois séries de suite**,
alors qu'il était établi dès la première. Le test binomial exact, déposé ce matin en
remplacement, le rend en une ligne.

Fable : *« un épisode figé, c'est ta politique dégénérée qui se remontre. Le gel n'est pas
un bruit à corriger, c'est un symptôme à expliquer. »*

## 3. B — NON LISIBLE, et on prolonge

```
GYMNASE   exposé SUR pente :  305 pas ·  30 morts · P=0,0984
          exposé hors      : 1019 pas · 124 morts · P=0,1217     PROTECTION = 1,24
ARMA      exposé SUR pente :  310 pas ·  17 morts · P=0,0548
          exposé hors      : 2070 pas · 166 morts · P=0,0802     PROTECTION = 1,46
```

- **contrôle 1 PASSE** : la protection dépasse 1 des deux côtés ;
- **contrôle 2 TOMBE** : 17 morts dans le groupe critique d'Arma au lieu des 30 exigés.

**Aucune lecture n'est admissible.** La clause 1 de l'avenant, déposée avant le run, dit :
*« si une case rend moins de 30 morts, on prolonge au MÊME protocole. On n'élargit pas la
bande, on ne baisse pas le seuil, on ne lit quand même pas. »*

**Je ne lis donc pas le rapport 1,24 / 1,46.** Mon extrapolation était optimiste — 9 morts
sur 20 épisodes prédisaient 30 sur 67, il en est venu 17. **Il faudrait ~118 épisodes au
total, soit ~51 de plus (≈ 2 h).**

⚠️ Et rappel de la clarification écrite avant lecture : **B mesure si la définition du
gymnase (cellule pentue) transfère, pas si le couvert protège sur Arma.**

## Ce que ces 67 épisodes établissent, en une ligne

**Le transfert échoue de façon stable et serrée (11,9 % contre 59,4 %), et la politique est
dégénérée sur Arma un épisode sur quatre.** La cause mécanique n'est pas dans ce run — elle
est dans le code du gymnase, déjà lue.
