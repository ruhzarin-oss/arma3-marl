# CRITÈRES v6 — L'ORDRE EST CÂBLÉ DANS LE CORPS (figés avant la première ligne)

Écrits le 2026-07-29 par Opus 5, en appliquant la méthode de Fable — deux demandes à
l'architecte ont été bloquées par un filtre, la provenance est donc différente des jalons
précédents et doit être connue. Arbitrage : Younes.

## POURQUOI v6 — LE DÉCLENCHEUR PRÉ-ENREGISTRÉ S'EST ARMÉ
Deux formes de récompense essayées, deux échecs mesurés :
- amendement 3 : pénalité d'exposition par pas → enseignait l'immobilité ;
- v5 : budget consommé, dépassement télescopique → **dose plate à 3,0 quel que soit le budget
  accordé** (2,97 / 3,06 / 3,08 / 3,03 pour B = 0,9 / 1,6 / 2,2 / 3,5), divergence des actions
  plate à 0,0004 sur une échelle qui monte à 0,693.

Le critique apprend parfaitement le budget (écart de valeur 0,24). La politique ne s'en sert
pas. **La récompense n'est pas le levier.**

## LE PRINCIPE
Un réflexe n'est pas une décision rapide, c'est une décision **qu'on ne prend pas**. La couche
s'applique **après** la politique et peut passer outre. On n'apprend plus à ne pas s'exposer :
on ne le peut plus.

Le budget agit **mécaniquement** sur les seuils de déclenchement. L'obéissance cesse d'être
quelque chose à apprendre.

## LE CATALOGUE — quatre règles, toutes tirées des politiques de référence
| règle | surveille | impose | tirée de |
|---|---|---|---|
| **R1 couvert** | exposition instantanée > seuil₁ | posture basse ce pas-ci | les postures des doctrines |
| **R2 décrochage** | dose consommée > seuil₂·B | le cap qui réduit le plus l'exposition | le crochet large |
| **R3 appui** | l'agent est à l'arrêt ET à portée | APPUI plutôt que l'inaction | l'élément de fixation |
| **R4 franchissement** | distance à l'objectif < seuil₄ | déplacement vers l'objectif, APPUI **interdit** | l'assaut final mesuré sur Arma |

R4 est la version mécanique de ce qu'on a mesuré sur le vrai Arma : `doSuppressiveFire`
**arrête** l'unité, et six semaines d'enlisement venaient de là. On l'interdit au contact.

## L'ARTICULATION — le réseau émet les SEUILS, pas les gestes
Tête d'actions inchangée. **Tête supplémentaire de 4 scalaires**, les seuils, produits à chaque
pas. Seuil effectif :
```
seuil_i = sigmoïde(sortie_réseau_i) · g_i(B)
```
`g_i` monotone en B. **Même avec des seuils aléatoires, un petit budget déclenche R1 et R2 plus
tôt.** C'est là que l'ordre est câblé dans le corps.

## GARANTIE ANTI-IMMOBILITÉ — à asserter dans le code, pas à espérer
1. **R2 et R4 imposent un DÉPLACEMENT**, jamais un arrêt. Seules R1 (posture) et R3 (appui)
   sont stationnaires.
2. **Compteur par agent** : au-delà de **K = 3 pas** consécutifs d'action stationnaire imposée,
   toutes les substitutions sont désactivées pour un pas et l'action de la politique passe.
3. **Inégalité à asserter** : sur toute fenêtre de K+1 pas, au moins un pas est choisi par la
   politique. Donc la fraction de pas stationnaires imposés est **bornée par K/(K+1) = 0,75**,
   et le déplacement moyen à l'initialisation est strictement positif.

## LES DEUX PORTES — et la seconde est l'idée neuve
**Porte 1 — CONTRÔLE NUL, l'équivalent de E6.** Couche active mais tous les seuils poussés à
l'infini : elle ne se déclenche jamais. Elle doit reproduire la politique sous-jacente
**exactement**. Écart **0,000** sur les six politiques de référence et sur un réseau entraîné.
Une couche qui ne prouve pas son inertie ne peut pas prouver son effet.

**Porte 2 — L'OBÉISSANCE AVANT TOUT ENTRAÎNEMENT.** Couche active, seuils **aléatoires**,
politique **non entraînée**. La dose consommée doit déjà croître avec le budget :
**ρ de Spearman ≥ 0,80 sur 8 niveaux de B.**

C'est le cœur de v6. Si le corps ne produit pas l'obéissance **sans aucun apprentissage**, le
dispositif a échoué avant d'avoir commencé, et on ne lance pas un entraînement. On a passé deux
versions à espérer qu'un agent apprenne à obéir ; cette fois l'obéissance se vérifie sur pièce
avant le premier pas de gradient.

## LE NOUVEAU TÉMOIN
v4 et v5 ne sont plus des références : le pipeline d'action a changé. Deux témoins neufs, tous
deux mesurés par l'instrument certifié, dans le monde à budget :
1. **Les six politiques de référence passées À TRAVERS la couche**, seuils par défaut → le
   nouvel étalon.
2. **Une politique aléatoire à travers la couche** → le plancher.
Tout chiffre de v6 se lit entre ces deux bornes, jamais contre v4.

## CE QU'ON GARDE DE v5, ET CE QU'ON JETTE
- **Gardé** : le monde à budget, l'observation, le prédicat de succès, la plage [0,6 – 4,2]
  fixée par la mesure de frontière. Cette partie est mesurée et saine.
- **Jeté** : les poids de v5, critique compris. L'observation est la même mais la distribution
  d'actions change entièrement ; un critique entraîné sur un comportement qui n'obéissait pas
  est un mauvais a priori. Archivé comme pièce.
- **En question, à trancher par Younes** : le terme de dépassement de la récompense devient
  largement redondant puisque la couche fait respecter le budget mécaniquement. Le garder ne
  nuit pas — il est borné — mais ce n'est plus lui qui travaille.

## INTERDITS
Ceux des jalons précédents restent. En plus :
- **Aucun entraînement tant que la porte 2 n'est pas franchie.**
- **Aucune cinquième règle** avant que les quatre aient passé le contrôle nul.
- Les seuils sont émis par le réseau ; **aucune règle ne dicte un geste écrit en dur qui ne
  soit pas dans le catalogue ci-dessus.**
