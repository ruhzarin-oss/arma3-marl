# CRITÈRES FIGÉS — LA VARIANCE DU BANC (avant les données)

Figés le 2026-07-28, AVANT tout run.

## POURQUOI CE RUN PASSE AVANT TOUS LES AUTRES
Le même bras — frontal bruyant, A=12 vs D=8 — a rendu **33 %** de prise à 18h46 (6 ops) et
**67 %** à 21h36 (18 ops). Même script, même configuration. **34 points d'écart.**
Tant que la variance du banc n'est pas chiffrée, aucun A/B qu'on y fait ne veut dire quoi que
ce soit : on ne sait pas distinguer un effet d'un tirage.

## DISPOSITIF
UN SEUL bras, répété : frontal bruyant, A=12 vs D=8, 120 pas, Altis/Pyrgos, paramètres
identiques à `replication_silence`. **6 blocs indépendants de 9 opérations** = 54 opérations.
Rien ne varie entre les blocs. Toute différence observée est du bruit, par construction.

## CE QUI EST MESURÉ
1. La prise de chaque bloc.
2. **L'étendue** : prise du meilleur bloc moins prise du pire.
3. L'écart-type des six blocs.

## SEUILS PRÉ-ENREGISTRÉS
- **Étendue ≤ 20 points** → le banc est utilisable à n=9 par bras. Les A/B passés restent
  discutables mais pas condamnés.
- **Étendue 20-40 points** → il faut au moins **30 opérations par bras** pour lire un effet de
  20 points. Tout A/B du banc fait à moins de 30 ops par bras est déclaré non concluant,
  rétroactivement, y compris FIBUA du 23/07.
- **Étendue > 40 points** → le banc, dans cette configuration, ne peut pas trancher un A/B de
  doctrine. Il faut réduire la variance à la source (garnison figée, météo figée, spawn figé,
  monde ALiVE gelé) avant d'y remesurer quoi que ce soit.

## CE QUI N'EST PAS MESURÉ
Aucune doctrine, aucune comparaison. Ce run ne parle que de l'instrument.

## INTERDICTIONS
Pas de retouche des seuils ni du nombre de blocs après un chiffre. Aucun résultat de ce run ne
sert à réinterpréter un A/B passé : il sert à décider lesquels sont lisibles.
