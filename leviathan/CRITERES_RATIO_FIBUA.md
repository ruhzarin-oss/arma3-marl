# CRITÈRES — RÉ-ANCRAGE DU BANC ARMA SUR LA CONFIGURATION FIBUA CERTIFIÉE

Figés le 27/07/2026, **avant** le premier relevé du balayage.

## Le point zéro n'est pas inventé, il est repris

Le banc Arma qui vient de rendre **0 % pour les deux doctrines** (`banc_arma.py`) était une
géométrie neuve : 4 attaquants, 8 défenseurs, **aucun élément d'appui**, cellules posées à
(23000, 17400) — dont **deux sur quatre EN MER** (altitudes −87 et −131 m, mesuré par
`sonde_terrain.py`). Il est écarté.

Le point zéro repris est celui de l'**A/B Arma à 3 bras** du 23/07 : `envelop_arma.py`,
théâtre **Stratis / FOB Maxwell (3253, 2984)**, garnison EAST tenue, **12 attaquants**,
**élément d'appui présent** (les fixeurs), trois bras à effectif total égal :

| bras | doctrine | ce qu'il isole |
|---|---|---|
| **A** `frontal` | tout le monde assaute de face | le témoin |
| **B** `supfront` | fixeurs + assaut **frontal** | la suppression **sans** l'angle |
| **C** `envelop` | fixeurs + débordement de **flanc** | la suppression **avec** l'angle |

Repères mesurés le 23/07 (n = 1 par bras, défense 8) :

| bras | pertes WEST | EAST neutralisés | pénétration mini |
|---|---|---|---|
| A frontal | **4** / 12 | 3 | 30 m |
| B fix+front | 0 / 12 | 1 | 78 m |
| C fix+FLANC | 0 / 12 | **3** | 34 m |

Aucun bras n'a pris le FOB. Mais **C domine B** : mêmes pertes (0), **trois fois** les
neutralisations, et il entre à 34 m au lieu de 78 m. Et **C domine A** : mêmes
neutralisations, **quatre pertes de moins**. C'est ce classement qu'on doit retrouver,
puis faire **basculer en prise** en balayant le rapport de forces.

## Le balayage

Une seule variable : le **nombre d'attaquants**, la garnison restant celle du FOB.
`--nag ∈ {8, 12, 18}`, soit des rapports d'environ 1:1, 1,5:1 et 2,25:1.
3 bras × 3 rapports × 2 répétitions = **18 épisodes**. Tout le reste est celui du 23/07
(`--offset 45 --standoff 70 --flank 0.45 --assault_tick 24 --steps 60`, pas de fumée).

## Le juge, écrit avant

**Critère principal — PRISE-À-PERTES.** `prise` = fraction d'épisodes où un attaquant entre
à moins de 25 m du FOB. `pertes par prise` = pertes WEST cumulées ÷ nombre de prises.

**LE POINT DE CERTIFICATION** est le plus petit `nag` qui satisfait les **trois** conditions :
1. `prise(C) − prise(A) ≥ 25 points`
2. `prise(A) ≤ 50 %`  — le frontal doit pouvoir échouer
3. `prise(C) ≥ 40 %`  — le crochet doit pouvoir réussir

C'est **ce point** que le sandbox devra reproduire. Jamais l'inverse.

**Critère de repli, déclaré d'avance** (car la prise peut rester nulle partout) :
- **pénétration** : médiane de `min_fob_dist`, plus petite = mieux ;
- **taux d'échange** : `EAST neutralisés ÷ pertes WEST` (pertes = 0 → on rapporte les
  neutralisations brutes, pas un rapport infini).
Séparation de repli : `pénétration(C) ≤ pénétration(A) − 25 m` **et** `pertes(C) < pertes(A)`.

**CONTRE-ÉPREUVE, obligatoire.** À `nag = 12`, le classement du 23/07 doit se reproduire :
- `pertes(A) > pertes(B)` **et** `pertes(A) > pertes(C)`
- `neutralisés(C) ≥ 2 × neutralisés(B)`
- `pénétration(C) < pénétration(B)`
**Si la contre-épreuve échoue, on ne conclut RIEN du balayage.** Le bras témoin ne
reproduit pas sa référence : la mesure est jetée, pas expliquée.

## Interdits
1. Toucher `offset`, `standoff`, `flank` ou `assault_tick` après avoir vu les chiffres.
2. Déclarer un point de certification qui ne remplit pas les trois conditions.
3. Aligner le banc Arma sur le sandbox. C'est le sandbox qui s'aligne.
