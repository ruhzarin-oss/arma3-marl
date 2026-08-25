# DÉCISION — **l'agent hésite**, au gymnase comme dans Arma

**24/08/2026, soir. Décision de Younes**, prise explicitement après mesure, et non héritée.

## Ce qui est décidé

> **Le décodeur devient l'ÉCHANTILLONNAGE, partout.** `boucle.py` (la porte) et
> `banc_live.py` (le déploiement dans Arma) tirent désormais l'action dans la distribution
> au lieu de prendre son maximum. Le décodeur est un **paramètre déclaré**
> (`HMT_DECODEUR`), pas un héritage.

## Le motif, mesuré

L'algorithme optimise le **rendement d'une politique stochastique**. La lire en argmax est
une **hypothèse supplémentaire**, que rien dans l'objectif ne garantit — et elle tombe une
fois sur deux :

| artefact | argmax | échantillonné |
|---|---|---|
| graine 0 | 49,6 % | **37,9 %** |
| graine 1 | **3,3 %** | **42,3 %** |
| artefact 13/08 | 51,1 % | 31,5 % |

**Figé : 3,3 à 51,1 %. En hésitant : 31,5 à 42,3 %.** Le décodeur d'hésitation **resserre**.

## ⚠️ Ce que cette décision COÛTE — et pourquoi ce n'est pas un critère déplacé

**Elle baisse les gagnants** : la graine 0 passe de 49,6 % à 37,9 %, l'artefact du 13/08 de
51,1 % à 31,5 %. Elle **resserre les bons et rattrape les mauvais**.

> Un critère qu'on déplacerait « pour qu'il dise ce qui arrange » **monterait** les chiffres.
> Celui-ci les **baisse**. C'est la marque qu'il suit un raisonnement et pas un résultat.

## ⚠️ Ce que cette décision N'INVALIDE PAS — et ce qu'elle change

**Le verdict Arma du 23/08 reste vrai** — natif 30,7 %, politique 33,6 %, écart −2,9 points,
IC contenant zéro. **Il décrit l'objet FIGÉ**, qui était bien ce qui était déployé alors.

**Mais toute mesure future sous ce décodeur porte sur un OBJET DIFFÉRENT**, et exige **sa
propre nuit**. On ne compare pas un chiffre d'hier à un chiffre de demain à travers un
changement de décodeur. ⚠️ **C'est écrit ici pour que personne ne le fasse par inadvertance,
moi le premier.**

## Ce que ça simplifie

**La loterie de condensation cesse d'être une porte pour la livraison.** Les trois artefacts
rendent 31,5 à 42,3 % en hésitant : il n'y a plus de graine « ratée ». Le **k = 4** de la
doctrine à trois canaux n'est donc plus nécessaire **pour livrer** — il reste utile **pour
la dispersion scientifique**, et le **canal de santé** (rendement de condensation) devient
une **curiosité** au lieu d'une contrainte.

⭐ **Cliquet : quand un objet est optimisé stochastique, le déployer figé est une hypothèse —
et une hypothèse se mesure avant d'être héritée.** Celle-là avait été héritée pendant des
mois, et elle décidait, à elle seule, si une nuit d'entraînement était un succès ou un échec.

## Ce qui reste à faire, et qui n'est pas fait

1. **Une nuit Arma sous le nouveau décodeur** pour savoir ce que vaut la politique quand on
   la laisse hésiter dans le vrai jeu. ⚠️ **Non lancée, non prédite** — elle appelle son
   prédicat écrit d'avance, comme les autres.
2. ⚠️ **Un risque non mesuré à déclarer** : dans Arma, hésiter à chaque pas produit une
   marche moins régulière que dans le gymnase, où le pas est un déplacement instantané. Le
   pont pilote par vitesse ; une action qui change tous les 3,28 s peut se comporter
   autrement qu'au gymnase. **Ça n'a jamais été mesuré, et ça peut mordre.**
