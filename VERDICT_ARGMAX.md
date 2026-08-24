# LA LOTERIE, EXPLIQUÉE — toutes apprennent, deux sur trois seulement se **condensent**

**24/08/2026, 10 h.** Pré-inscription `PREINSCRIPTION_ARGMAX.md` (`ca2f7e7`), écrite
**avant que l'artefact existe**. Mesures faites sur l'artefact conservé grâce à la
réparation de la sauvegarde (`aa48ed0`) — sans elle, ce dossier était impossible.

## La grille 2 × 2 : les deux prédictions passent

| graine 1 | graines d'ENTRAÎNEMENT | graines de TEST |
|---|---|---|
| **argmax** | **4,0 %** | **3,3 %** |
| **échantillonnage** | **42,2 %** | **39,0 %** |

- **D1 passe** (39,0 > 30) · **D2 passe** (4,0 < 10).
- **Ce n'est pas du sur-apprentissage** : en échantillonnant elle rend **39 %** sur des
  graines jamais vues. Elle généralise très bien.
- **C'est l'argmax, et rien d'autre.**

## Mais l'argmax n'est PAS mauvais partout — la porte lit juste

| artefact | argmax | échantillonnage | écart |
|---|---|---|---|
| graine 1 (TOMBE) | 3,3 % | **42,3 %** | **+39,0** |
| graine 0 (PASSE) | **49,6 %** | 37,9 % | −11,7 |
| artefact du 13/08 | **51,1 %** | 31,5 % | −19,6 |

**Pour les deux politiques qui réussissent, l'argmax est MEILLEUR** — comme il doit l'être.
**La porte n'est donc pas en cause**, et l'hypothèse « le banc lisait mal depuis le début »
tombe.

## ⭐⭐⭐ Ce que la mesure dit vraiment

> **En échantillonnant, les trois sont dans la même bande : 42,3 · 37,9 · 31,5 %.**
> **La graine « perdante » est la MEILLEURE des trois.**
>
> **Les trois entraînements ont également réussi. Ce qui est aléatoire, ce n'est pas
> l'apprentissage — c'est la CONDENSATION en une politique déterministe utilisable.**

L'algorithme optimise le rendement d'une politique **stochastique**. Rien, dans l'objectif,
ne demande que son **argmax** soit bon. Deux fois sur trois il l'est ; une fois sur trois la
politique reste un **mélange** dont le mode est mauvais. **Aucun terme de la perte ne
contrôle cette propriété** — et c'est cohérent avec les deux défauts déjà déposés
(`97b996e`) : **aucune entropie**, et **l'avantage normalisé pas par pas**.

⭐ **Cliquet : optimiser une politique stochastique et la déployer figée sont deux choses,
et rien ne garantit la seconde.** On l'a payé une fois par tirage sur trois.

## Ce que ça change pour Arma

`banc_live.py:341` déploie **en argmax**. L'artefact du 13/08 y rend **51,1 %** en argmax
contre 31,5 % en échantillonnant : **pour cet artefact-là, l'argmax était la bonne lecture**,
et les mesures d'Arma ne sont pas touchées. **Mais c'est un coup de chance de tirage**, pas
une propriété de la recette.

## L'arbitrage, qui n'est pas le mien

La pré-inscription disait : *« il faudra choisir, et le justifier »*. Trois voies, et je
donne mon avis sans trancher :

1. **Juger et déployer en échantillonnant.** C'est la lecture qui correspond à ce que
   l'algorithme optimise, et elle rend la recette **reproductible** (31-42 % sur trois
   tirages au lieu de 3-51). ⚠️ Elle **baisse** les chiffres des gagnants (49,6 → 37,9) :
   ce n'est pas un geste qui arrange, c'est un geste qui resserre.
2. **Garder l'argmax et faire de la condensation un objectif** — entropie annelée, ou une
   pénalité sur l'écart entre le rendement échantillonné et le rendement figé. Plus coûteux,
   plus juste : on obtient ce qu'on demande au lieu de l'espérer.
3. **Garder l'argmax et tirer plusieurs graines**, en gardant celle qui condense. Honnête si
   c'est **écrit** : c'est acheter un tirage, pas améliorer une recette.

⚠️ **Ce qu'il ne faut pas faire** : changer la porte pour l'échantillonnage **et** annoncer
les 42,3 % de la graine 1 comme un progrès. Ce serait déplacer le critère pour qu'il dise
ce qui arrange — la faute réparée sur le banc Arma hier matin.
