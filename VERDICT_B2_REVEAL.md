# VERDICT B2 — LE `reveal` EST INUTILE. T7 CERTIFIE BIEN LE CANAL DE LA POLITIQUE.

17/08/2026. Socle `2.7.0`, plan 2×2 `reveal` × comportement, **sur lieux certifiés**,
8 essais par condition, critères écrits avant.

## Le résultat

| `reveal` | comportement | n | coups (médiane) | min–max | zéros |
|---|---|---|---|---|---|
| non | AWARE | 8 | 7 | 2–10 | **0/8** |
| non | COMBAT | 8 | 9 | 4–13 | **0/8** |
| oui | AWARE | 8 | 8 | 1–10 | **0/8** |
| oui | COMBAT | 8 | 11 | 5–15 | **0/8** |

**Aucun zéro dans aucune condition.** Le critère pré-écrit — « le `reveal` est nécessaire si
sans lui la médiane tombe à 0 dans les deux comportements » — n'est franchi nulle part.

> ## ➤ LE `reveal` EST INUTILE. La divergence certificateur/servi sur ce point est SANS CONSÉQUENCE.

T7 et l'acte 3 donnent la cible à leur tireur ; `arma_couture.py` ne le fait jamais. **Cette
différence n'empêche pas le feu de partir.** T7 vert garantit donc bien que le canal que la
politique emprunte fonctionne.

## Ce que ça CORRIGE de ma propre lecture

Quand le refactoring B1 a supprimé le `reveal`, le placeur s'est mis à rendre **0 coup**, et
j'ai écrit que « sans `reveal`, l'homme ne tire pas ». **C'était faux.** Le vrai coupable était
le `setCaptive true` que j'avais posé sur le mannequin au bloc A1 — un homme captif est neutre,
donc n'est plus une cible. Les deux fautes ont été corrigées coup sur coup, et j'ai attribué
la guérison à la mauvaise.

**Je ne l'avais pas déposé comme résultat**, précisément parce qu'un accident n'est pas une
mesure. Sans cette retenue, un faux serait entré au registre — et il aurait fait condamner un
test qui fonctionne.

## Le second facteur, mesuré au passage

`COMBAT` tire un peu plus qu'`AWARE` : **+2 coups** sans `reveal`, **+3** avec. Le `reveal`
lui-même ajoute **+1 à +2 coups**. Aucun de ces écarts ne franchit un seuil déposé, et aucun
ne change le verdict binaire : **dans les quatre conditions, le feu part**.

À noter tout de même : le certificateur (COMBAT + `reveal`, 11 coups) tire **1,6 fois plus**
que l'homme servi (AWARE sans `reveal`, 7 coups). Ce n'est pas une panne, mais c'est un écart
de cadence entre ce qu'on certifie et ce qui joue. Non revendiqué, non déposé comme charge :
`n = 8` et aucun seuil n'avait été écrit pour la cadence.

## Ce qui reste des trois divergences de Fable

| divergence | statut |
|---|---|
| (a) `reveal` présent chez le certificateur, absent chez le servi | **MESURÉE — sans conséquence** |
| (b) `doWatch` sur un OBJET (socle) contre une POSITION (couture) | **NON MESURÉE** |
| (c) `AWARE` (servi) contre `COMBAT` (bancs) | **MESURÉE — écart de cadence, pas de panne** |
