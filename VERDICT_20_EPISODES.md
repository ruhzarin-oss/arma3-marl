# Les 20 épisodes du banc live — LA PORTE TOMBE, la lecture n'est pas citable

Mesuré le 14/08/2026. Critères déposés avant dans `DEPOT_20_EPISODES.md` (commit `53bcc51`).
20 épisodes indépendants, 4 contre 4, site apparié.

## Les deux contrôles positifs PASSENT

- **La scène confirmée par le JEU** : `def=4 att=4` sur 20 épisodes sur 20.
- **Les azimuts de naissance DIFFÈRENT** : 20 valeurs distinctes à 5° près, écart-type
  101,5°. Ce sont bien vingt épisodes, pas vingt copies. *C'est le contrôle qui manquait
  quand j'ai comparé deux mondes en croyant comparer des camarades.*

## LA PORTE TOMBE — `dcover`, pour la quatrième fois

```
                     1%      50%      99%
GYMNASE            0.000    0.035    0.131
ARMA (20 ep.)      0.000    0.133    0.533
```

**60,1 % des décisions d'Arma sont au-dessus du 99ᵉ centile du gymnase.** 12 épisodes sur
20 ont leur médiane hors plage, et deux lisent **0,53** — le garde-fou `16/30`, c'est-à-dire
*aucun couvert trouvé*.

Mon dépôt posait ça comme condition d'échec : *« une colonne qui ressort de sa plage → le
monde a bougé sous la mesure »*. **Elle est ressortie. La lecture n'est donc pas citable.**

L'épisode unique de tout à l'heure lisait `dcover` à 0,033, pile sur le gymnase. C'était un
tirage chanceux, et j'en avais tiré que la colonne était réparée. **Vingt épisodes disent
le contraire.**

## Ce que la mesure donne malgré tout — SOUS RÉSERVE, non citable

| | Arma | gymnase |
|---|---|---|
| **prise** | **0 / 20 = 0,0 %** | 59,4 % |
| tous morts | 16 / 20 | — |
| 60 pas sans prendre | 4 / 20 | — |
| actions distinctes / épisode | médiane **2** | 5 |

⚠️ `dmin` vaut 1 quand **tous** sont morts : c'est dégénéré, pas une prise. Sans ce garde,
seize épisodes auraient été comptés comme des prises. Le critère employé est
`dmin < 25 ET vivants > 0`.

## Le gel — INDÉCIS, et on ne rejoue pas

**10 épisodes figés sur 20.** La règle déposée disait : ≥ 18 → le gel est réel ; ≤ 3 → il
n'a jamais existé ; **4 à 17 → indécis, on ne conclut pas et on ne rejoue pas en espérant
mieux.** 10 tombe au milieu de la bande. **Aucune conclusion sur le gel.**

## Ce qu'il faut retenir

Le 0/20 contre 59,4 % est brutal, mais **je ne le cite pas comme « la politique ne
transfère pas »** : la porte est tombée, et la colonne qui l'a fait tomber est exactement
celle qui a déjà été fausse trois fois. Une entrée systématiquement quatre fois trop grande
est un candidat suffisant pour expliquer l'échec — le mesurer proprement demande de
réparer `dcover` d'abord.

**Ce qui est acquis, en revanche** : le banc produit enfin vingt épisodes valides,
différents, dans le monde de l'entraînement, avec ses deux contrôles positifs qui passent.
C'est le premier instrument de cette journée dont on sait qu'il tourne droit.

## La suite

`dcover` se calibre. La sonde de terrain a montré que le seuil en service (3,241) est
5× trop haut et que le seuil corrigé (0,648) dépasse dans l'autre sens — médiane 0,000
sur Stratis au hasard contre 0,035 au gymnase. **Ce n'est pas un correctif d'une ligne,
c'est un étalonnage**, et il se dépose avant d'être mesuré.
