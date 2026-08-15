# Dépôt — 67 épisodes, critères écrits AVANT lancement

Déposé le 15/08/2026. Taille fixée par le calcul du dépouillement précédent : Arma rend
**9 morts exposés-sur-couvert en 20 épisodes**, il en faut **30** par groupe, donc
**67 épisodes** — environ dix heures de banc. La taille n'est pas choisie, elle est dérivée.

## Question PRINCIPALE — B, la valeur du couvert

Reprise **à l'identique** de `DEPOT_COUVERT.md` et de son `AMENDEMENT_COUVERT.md` :
protection = P(mort | exposé, hors couvert) ÷ P(mort | exposé, sur couvert), `incover`
côté gymnase, `dcover == 0` côté Arma, chez **les exposés seulement**.

Contrôles inchangés : protection > 1 dans chaque monde, ≥ 30 morts par groupe.
Bandes inchangées : **> 2** le gymnase sur-protège (B retenue) · **0,5 à 2** B réfutée ·
**< 0,5** réfutée dans l'autre sens.

## Question SECONDAIRE, déposée maintenant et non après — la prise

67 épisodes ramènent l'intervalle sur une proportion de ±22 à **±12 points**. La prise se
lira contre les **59,4 %** du gymnase, par le critère déjà codé (`dmin < 25` **et**
`vivants > 0`). Aucune bande nouvelle : l'écart est établi si l'IC95 d'Arma exclut 59,4 %.

## Question TROISIÈME — le gel, et l'aveu qui va avec

**Ma bande « 4 à 17 sur 20 = indécis » était fausse par construction.** Le gymnase fige un
épisode sur 32 (3,1 %). Sous ce taux, observer **4 figés sur 20** a déjà une probabilité de
2 % ; en déclarer 17 « indécis » n'avait aucun sens. **8/20 contre 3,1 % donne p < 10⁻⁶.**

C'est une faute d'arithmétique, démontrable **sans regarder une seule donnée** — même
famille que mon arrondi du choix de site, mon critère `dcover` insatisfiable et ma porte
d'azimut trop stricte. Quatrième du jour.

**Le test qui remplace, déposé ici** : test binomial exact du taux observé contre 3,1 %.
- IC95 du taux d'Arma **exclut 3,1 %** → **le gel est RÉEL** ;
- IC95 **contient 3,1 %** → Arma est compatible avec le gymnase.

Pas de bande arbitraire : un intervalle et une référence.

⚠️ Ce remplacement est énoncé **sans référence au résultat des trois séries** ⟨règle 13⟩ :
il ne s'appuie que sur l'arithmétique du taux de référence, et il **resserre** — il
remplace une bande floue par un test.

## CONTRÔLES POSITIFS, repris

1. scène confirmée par le JEU : `def=4 att=4` ;
2. azimuts de naissance distincts — porte corrigée : **écart-type > 60°**, au lieu de mon
   comptage de casiers à 5° qui échouait sur la majorité des séries valides ;
3. les 12 colonnes dans la plage du gymnase.

## Ce qui ferait échouer

- moins de 50 épisodes valides sur 67 ;
- une colonne hors plage ;
- moins de 30 morts par groupe **malgré** les 67 épisodes → la question B se ferme
  définitivement pour cette voie, et il faudra un banc conçu pour elle.

## Ce qui n'est PAS promis

Ni que B soit tranchée, ni que la prise monte. Dix heures de banc peuvent rendre trois
réponses négatives, et ce serait un résultat.
