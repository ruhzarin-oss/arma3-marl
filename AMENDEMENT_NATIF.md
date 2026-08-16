# AMENDEMENT AU PRÉDICAT NATIF — écrit AVANT toute lecture

16/08/2026, ~22 h. Aucun `.npz` de la nuit n'a été ouvert. Les épisodes tournent.

Trois trous relevés par l'audit de Fable. Chacun serait sinon **comblé après lecture, donc
par le résultat**. Aucun ne référence un chiffre de cette nuit : ils sont identifiés **par
conception**, ce qui les rend licites au titre de la règle 13, et chacun **resserre**.

## A · RÈGLE DE COMPLÉMENT — atteindre réellement 67

La porte donne ~4 % de prévols rouges (2 sur 50), de **cause assignable** : le placeur ne
trouve pas de ligne de vue pour le mannequin. Sur 134 lancements, cela fait environ
**5 épisodes jetés**. Le harnais lance exactement 67 fois par passe : une passe rendra donc
64 ou 65 épisodes, pas 67.

**Vérifié ce soir** : `banc_live.py:236` sort en `sys.exit(2)` sur prévol rouge, et le
relevé n'est écrit qu'en ligne 318. Un prévol rouge ne produit **aucun** `.npz`. La nuit
n'est pas contaminée ; elle est seulement **incomplète**.

> **RÈGLE** — les épisodes manquants sont **rejoués au matin, avant l'ouverture du moindre
> `.npz`**. Une passe qui n'atteint pas 67 épisodes valides n'est **pas citable**.

## B · APPARIEMENT — même prévol des deux côtés

Le 44,8 % du 15/08 a été joué **sans le prévol de ce soir** : ni le correctif T5, ni la
porte, ni le sabotage n'existaient, et T5 rougissait un tirage sur deux.

Une certification plus stricte **jette davantage de mondes défectueux**. L'échantillon
NATIF de cette nuit sera donc tiré d'une distribution **plus propre** que celle où le
44,8 % a été mesuré. Le biais pousse **dans le sens du retrait de l'acquis** — le pire des
sens, parce qu'il est celui qu'on croit prudent.

> **RÈGLE** — la clause « NATIF ≥ politique retire le 44,8 % des acquis » est **suspendue**.
> Elle ne redeviendra applicable que contre une politique **rejouée sous le prévol
> `1.10.0`**. Cette nuit mesure **la baseline natif sous l'instrument neuf**, et rien d'autre.

## C · AGRÉGATION — le chiffre cité, et le sort de la bande

Deux trous laissés ouverts dans `DEPOT_NATIF.md` seraient tranchés après lecture.

> **RÈGLE C1** — si les deux passes concordent (< 10 points), le chiffre cité est le
> **groupement des deux passes**, pas la meilleure ni la pire. Les deux taux individuels
> sont publiés à côté.
>
> **RÈGLE C2** — un écart inférieur à 12 points entre NATIF et la politique laisse le
> 44,8 % **exactement où il est** : ni confirmé, ni retiré, ni promu. La bande n'est pas un
> résultat faible, c'est **une absence de résultat**, et elle ne déplace rien au registre.

## D · Le statistique fait partie du critère

Faute constatée ce soir : mes critères disaient « < 3 m / > 8 m » sans dire **de quelle
statistique**. Les tableaux affichaient une **médiane non déclarée** — et sur le bras 7,
un critère « n'importe quel essai < 3 m » aurait rendu le verdict **inverse**.

> **RÈGLE** — tout seuil déposé nomme sa statistique (médiane, moyenne, minimum, quantile)
> **dans la phrase qui le pose**. Un seuil sans statistique n'est pas un critère.

Appliqué rétroactivement au prédicat NATIF : **taux de prise = proportion d'épisodes pris
sur épisodes valides ; concordance et écart lus sur cette proportion.**
