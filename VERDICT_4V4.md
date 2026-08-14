# Le banc live à 4 contre 4 — deux fautes de monde réparées, une anomalie qui reste

Mesuré le 14/08/2026. Critères déposés avant dans `DEPOT_4V4.md`. **Un seul épisode :
aucun verdict de concordance.**

## Ce qui a changé, et c'est massif

| | site plat, 8 contre 13 | site apparié, 4 contre 4 |
|---|---|---|
| colonnes hors plage | 5 / 12 | **0 / 12** |
| survie | tous morts au pas 14-17 | **4 / 4 vivants aux 60 pas** |
| progression | 26 m puis mort sur place | **de 143 m à 103 m** |
| actions distinctes | 1 | 1 |

**La porte PASSE** : les 12 colonnes tiennent (22,1 % des décisions ont une colonne hors
plage, aucune médiane ne sort).

Deux fautes de monde, deux réparations, et l'effet ne se discute pas : on est passé
d'hommes qui meurent sans avancer à des hommes qui survivent et gagnent quarante mètres.

## L'anomalie qui reste — énoncée correctement cette fois

L'agrégat du gymnase (8 actions sur 10 240 décisions) mélangeait 64 environnements et
40 pas. Comparé à ce qui est comparable — **un** environnement, sur la durée :

```
GYMNASE, par episode : mediane 5 actions distinctes  ·  une seule action dans 3,1 % des cas
GYMNASE, au meme pas : mediane 1 action (les 4 hommes agissent ENSEMBLE)
ARMA                 : 1 action sur 60 pas, et elle ne change JAMAIS
```

**Deux corrections à ce que j'ai raconté toute la journée.**

1. Que les quatre hommes émettent la même action au même pas n'a **rien d'anormal** :
   le gymnase fait pareil, médiane 1. Mon « gel » n'était pas là.
2. Ce qui est réellement anormal, c'est que **l'action ne change pas dans le temps**.
   Le gymnase en change cinq fois par épisode ; un seul épisode sur trente-deux reste sur
   une action de bout en bout. Arma est dans cette queue — **rare, pas impossible**.

Et l'observation, elle, bouge : `dmin` passe de 143 à 103. **L'entrée change, la sortie
non — aucun seuil de décision n'est franchi.**

## Ce que ça ne dit pas

Un épisode. 240 décisions. Une graine. Un événement à 3,1 % observé une fois n'est pas
une anomalie établie — c'est ce qu'on attend d'arriver une fois sur trente-deux.

## La suite

Le monde du banc correspond enfin à celui de l'entraînement. **Des répétitions sont
maintenant lisibles pour la première fois** — c'est exactement le « banc live rejoué avec
le contrat réparé » demandé, et c'est le préalable à toute citation du gymnase comme
transféré.

Si l'anomalie tient sur N épisodes, alors l'écart n'est plus ni dans l'observation ni dans
la scène, et il faudra regarder le **corps** : dix actions qui ne mordent pas sur Arma
comme elles mordent au gymnase.
