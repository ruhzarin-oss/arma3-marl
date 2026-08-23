# LES QUATRE VÉRIFICATIONS, ZÉRO RUN — deux défauts trouvés, et ils se composent

**23/08/2026, 19 h 15.** Les quatre questions posées par Fable, lues dans le code.
Aucun entraînement lancé pour ça.

## 1. `d` est moyenné sur TOUS les hommes, et les morts se figent

`boucle.py:114` — `d = sqrt(apx² + apy²).mean(1)` : moyenne sur les **quatre emplacements**.
`assault_terrain.py:618` — `moving = (acts < 8).float() * al` : **un mort ne bouge plus**,
sa position reste là où il est tombé.

> **Conséquence, arithmétique.** Avec 3 morts figés à 95 m et le survivant sur l'objectif,
> `d = (3×95 + 25)/4 = 77,5 m`. **Le survivant qui gagne un mètre ne déplace `d` que d'un
> quart de mètre.** Le guidage du dernier coureur — précisément l'homme qui fait la prise —
> **est divisé par le nombre de vivants.**

**Et ça compose avec la rente de γ** : la rente vaut `0,001 × 0,01 × d`, et les morts
**maintiennent `d` haut**. Donc à mesure que l'escouade perd des hommes :
**la rente de camping reste pleine, le gain d'avancer est divisé par quatre.**
Le rapport bascule exactement là où l'escouade commence à prendre des pertes — **au bord de
l'enveloppe de tir, à 95 m.** C'est le mur mesuré.

## 2. Une mort ne termine PAS l'épisode

`assault_terrain.py:818` — `done = win | wiped | timeout`. Seul l'**anéantissement** termine.
La pénalité implicite de mort est donc modérée, pas énorme. **Réponse nette, rien à corriger.**

## 3. La prise est payée UNE FOIS

`boucle.py:131` — `neuf = info["took"] & ~fini`, et `win` fait partie de `done`, donc `fini`
passe à vrai au même pas. **Une impulsion, pas une rente. Rien à corriger.**

## 4. ⛔ À la troncature, le critique ne bootstrappe PAS — et il n'y a AUCUNE entropie

`boucle.py:169` — `R = torch.zeros_like(rs[0])` puis `R = r + 0.99 * R` à rebours.
**R part de zéro.** Le pas 60 est donc traité comme un **état terminal de valeur nulle** :
un épisode qui survit jusqu'à la limite de temps voit son avenir estimé à **rien**.
C'est le défaut classique des limites de temps — et c'est aussi ce qui **casse la prémisse
du théorème de façonnage** (Φ(terminal) ≠ 0), que la correction du 17/08 invoquait.

`boucle.py:180` — `perte = pl + 0.5 * vl` : **aucun terme d'entropie.** Dans une tâche à
récompense rare, rien n'empêche la politique de se figer tôt sur le comportement sûr.

## 5. ⛔ TROUVÉ EN CHEMIN : l'avantage est normalisé PAS PAR PAS

`boucle.py:175-176`, **dans la boucle sur les pas** :
```python
adv = (ret_a - v).detach()
adv = (adv - adv.mean()) / (adv.std() + 1e-6)
```
La normalisation se fait **à l'intérieur d'un pas de temps**, entre environnements.

> **Le pas où la prise arrive voit son avantage énorme ramené à variance 1 — exactement
> comme un pas de pur bruit.** La normalisation par pas **détruit l'échelle relative entre
> les pas**, et c'est précisément l'information dont une tâche à récompense rare a besoin.
> Un pas où il ne se passe rien voit son bruit **gonflé** à variance 1.

## 6. Et une note : les pénalités du monde ne servent pas

`assault_terrain.py` expose `death_pen` et `suffer_pen`, mais `jouer` **ignore le `rew` du
monde** et fabrique le sien. Ces leviers n'agissent pas ici. À savoir avant d'y toucher.

## Ce que ça change

**Trois causes candidates au mur de 95 m**, et elles ne s'excluent pas :
la **rente de survie** (γ, 17/08), le **guidage divisé par les morts** (§1), et la
**normalisation par pas** qui aplatit le signal rare (§5).

⚠️ **Aucune n'est établie.** Ce sont des lectures de code, pas des mesures. Et le bras B
vient de montrer que **le mur finit par céder** vers l'itération 380 : ce n'est donc pas un
équilibre absorbant, c'est un **retard**. Ces trois défauts sont des candidats pour expliquer
ce retard — chacun se teste séparément, un bras à la fois, jamais deux.

⚠️ **Et rappel de Fable, qui vaut ici** : ne pas réparer les trois d'un coup. Ça marcherait
peut-être, et on ne saurait pas lequel.
