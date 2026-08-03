# CRITÈRES FIGÉS — BALAYAGE DE LA MENACE (avant les données)

Figés le 2026-07-28, AVANT tout run. Non négociables après coup.

## QUESTION
À partir de quelle densité de menace la manœuvre redevient-elle payante ?
Le re-verdict du 28/07 a montré qu'à 4 défenseurs dans le monde correctement létal,
le flanc n'achète plus la prise (×1,00) — seulement des vies (coût ×0,39).
Ce n'est pas « le flanc ne paie jamais » : c'est « le flanc ne paie pas À CE NIVEAU
DE MENACE ». On cherche le seuil.

## LE CADRAN — une seule variable balayée
Nombre de défenseurs D ∈ {4, 6, 8, 10, 12, 16}, attaquants A=4 fixe.
Monde figé au monde MESURÉ : courbe n°1, courbe n°2, `cible_unique=True`.
Aucune courbe n'est retouchée. Mêmes doctrines scriptées, graine 7,
200 épisodes par bras et par point.

## CE QU'ON LIT, décidé d'avance
1. **Bande discriminante** : les D où la prise frontale tombe entre 25 % et 75 %.
   Hors de cette bande, le banc ne sépare rien et ses ratios ne sont pas interprétés.
2. **Seuil de manœuvre** : le plus petit D, DANS la bande, où prise flanc/frontal ≥1,50.
   S'il n'existe pas sur la plage balayée, on l'écrit tel quel : « pas de seuil sous
   D=16 » — on n'étend pas la plage après coup pour en trouver un.
3. **Avantage de coût** : le rapport pertes/prise flanc/frontal est relevé à chaque D.
   On s'attend à ce qu'il reste ≤0,60 partout. S'il s'inverse quelque part, c'est le
   résultat le plus intéressant du run et il doit être signalé, pas lissé.

## INTERDICTIONS
Pas de retouche des courbes, des seuils, du nombre d'épisodes ou de la plage de D
après avoir vu un chiffre. Si le run casse, on répare le harnais et on relance à
l'identique.
