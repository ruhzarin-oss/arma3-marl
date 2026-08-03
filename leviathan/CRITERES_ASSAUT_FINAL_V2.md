# CRITÈRES FIGÉS — ORDRE D'ASSAUT FINAL, V2 : LE DÉCLENCHEUR AU BON ENDROIT

Figés le 2026-07-28 après le run V1, AVANT toute nouvelle donnée.

## POURQUOI UNE V2
Le run V1 (`7c8d6c96a8cf6887`) a rendu **0 résolue sur 6**. Il ne réfute PAS l'ordre d'assaut
final : il ne l'a pas testé. Distances minimales atteintes : 34, 42, 55, 58, 67, 81 m pour un
déclencheur posé à **40 m**. Le mécanisme n'a pu s'armer que dans **1 opération sur 6**.

Deux fautes, consignées :
1. Le déclencheur a été placé là où le tir de démonstration s'était arrêté (26 m), pas là où
   le banc s'enlise réellement (55-81 m).
2. Le runner filtrait la sortie par `tail -1` et **jetait les lignes de tick** — donc toute
   preuve de déclenchement. Le fait a dû être reconstitué à partir des distances. Corrigé :
   le journal conserve désormais les lignes `FRANCHISSEMENT`.

## CE QUI CHANGE — UNE SEULE VARIABLE
`--assaut_final` passe de **40 m à 80 m**, borne haute de l'enlisement observé. Rien d'autre
ne bouge : A=12, D=12, 120 pas, 3 répétitions par mode, mêmes doctrines, même théâtre.

## SEUILS PRÉ-ENREGISTRÉS
1. **DÉCLENCHEMENT** : au moins **5 opérations sur 6** doivent afficher au moins une ligne
   `FRANCHISSEMENT`. En dessous, le mécanisme n'est toujours pas testé et rien d'autre ne se lit.
2. **RÉSOLUTION**, lue seulement si le déclenchement est atteint : **≥4 opérations sur 6
   RÉSOLUES** (FOB pris OU escouade anéantie).
   - ≥4/6 → l'ordre d'assaut final entre au protocole ; la certification du seuil de manœuvre
     redevient relançable.
   - <4/6 → l'ordre ne suffit pas à 12 contre 12. On cherche ailleurs, sans retoucher DIST une
     troisième fois : deux réglages successifs d'un même bouton, c'est du tuning, pas une mesure.

## CE QUI N'EST TOUJOURS PAS MESURÉ
La comparaison frontal / envelop. Trois répétitions par bras ne tranchent rien.

## INTERDICTIONS
Pas de troisième valeur de DIST dans ce chantier. Pas de retouche des seuils après un chiffre.
