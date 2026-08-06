# Le POULS — la sandbox tue-t-elle au bon tarif ?

*6 août 2026, 16h30. Tolérance déposée AVANT tout calcul. Aucune mortalité de sandbox n'a été
mesurée.*

## Pourquoi

> ⟨Fable, 06/08⟩ **« Tu as vérifié les organes, pas le pouls. »**

Chaque constante de la loi de mort est mesurée — la courbe de toucher, les balles par pas, le
dégât par impact, le seuil. **Leur produit ne l'est pas.** Quatre constantes justes peuvent
composer une mortalité d'ensemble fausse : les erreurs se multiplient.

La PORTE 0 prouve que le monde **discrimine**. Elle ne prouve pas qu'il discrimine **au bon
tarif**. Tant que ce fichier n'est pas rempli, la loi est *fidèlement construite*, pas *fidèle*.

## La grandeur comparée, et ses deux nécessaires précautions

**Côté Arma** — corpus de 563 383 observations, mortalité **10,00 %**. L'étiquette est
précise : *un soldat meurt-il dans les **30 secondes** qui suivent ?* Une observation = un
soldat, à un instant, ayant au moins un ennemi dans son enveloppe.

**Côté sandbox** — un pas vaut **3,28 s** (conversion mesurée). Trente secondes valent donc
**9,1 pas**. On mesure : *l'agent accumule-t-il le seuil de mort (0,70) dans les 9 pas qui
suivent ?* Même restriction : au moins un défenseur vivant à moins de 400 m.

**Précaution 1 — la comparaison se fait PAR TRANCHE DE DISTANCE**, au défenseur le plus
proche. Un agrégat global mélangerait des situations que les deux mondes ne peuplent pas de la
même façon.

**Précaution 2, écrite comme limite et non comme excuse** : le corpus Arma mêle **attaquants
et défenseurs**, en garnison comme en mouvement. La sandbox n'a qu'un **attaquant qui
progresse à découvert**. Les deux populations ne sont pas les mêmes, et cet écart-là ne sera
pas corrigé — il sera **rapporté**.

## La tolérance, déposée

Une tranche est **comparable** si elle porte au moins **2 000 observations Arma** et
**2 000 pas de sandbox**.

> **Même pouls : le rapport des mortalités reste entre 0,5 et 2,0** sur chaque tranche
> comparable — un facteur 2 dans un sens ou dans l'autre.
>
> **Verdict global : la loi passe si au moins les deux tiers des tranches comparables sont
> dans la tolérance**, et si aucune tranche n'est hors d'un facteur **4**.

⟨un facteur 2 par tranche est large, et c'est délibéré : on cherche une erreur de chaîne — un
facteur 3, 5 ou 10 — pas un désaccord de troisième décimale entre deux mondes qu'on sait
différents.⟩

## Ce qui se passe si ça sort hors tolérance

**Aucun bricolage.** La chaîne reçoit un **facteur de correction dérivé de l'écart mesuré** —
le rapport médian des tranches comparables, appliqué au dégât par impact — et **l'étage 1 se
rejoue après**. On ne règle rien à la main, et on ne touche à aucun autre bouton.

Si l'écart n'est **pas** un facteur constant mais dépend de la distance, alors ce n'est pas la
chaîne qui est mal calibrée, c'est la **forme** de la courbe : on l'écrit tel quel, et la
bande 200-250 m — la seule extrapolée, et celle où commence chaque épisode — devient le
premier suspect.

## Ce que ce test ne peut pas dire

Il compare des **taux**, pas des **causes**. Deux mondes peuvent tuer au même rythme pour des
raisons différentes. C'est un contrôle de vraisemblance d'ensemble — le pouls, exactement — et
il ne remplace ni la PORTE 0 ni la certification sur Arma.
