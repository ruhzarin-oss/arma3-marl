# CRITÈRES FIGÉS — RE-VERDICT « CIBLE UNIQUE » (avant les données)

Figés le 2026-07-28, AVANT tout run. Non négociables après coup.

## QUESTION
L'avantage du flanc, conclu depuis deux semaines, survit-il quand on corrige la
létalité ? La sandbox faisait frapper CHAQUE attaquant par CHAQUE défenseur.
Arma dit : **0,68 homme différent par tireur et par fenêtre de 3,28 s**
(sélection libre, banc de bissection du 2026-07-28, seuil pré-enregistré <1,5).

## VARIABLE ISOLÉE — UNE SEULE
Les deux mondes ont la courbe n°1 (toucher) ET la courbe n°2 (suppression :
`supp_residuel=0.08`, `supp_persist=0.35`). Seul diffère :

- ANCIEN  : `cible_unique=False` — chaque défenseur frappe tous les attaquants.
- MESURÉ  : `cible_unique=True`  — chaque défenseur frappe un attaquant par pas.

Mêmes graines, même géométrie défensive, mêmes doctrines SCRIPTÉES (une politique
apprise dans l'ancien monde mesurerait son inadaptation, pas la fidélité du monde).

## SEUIL DE « LE FLANC PAIE » — repris tel quel du re-verdict n°1, non retouché
Le flanc paie si et seulement si :
- rapport de prise flanc/frontal **≥ 1,50**, ET
- rapport de coût (pertes par prise) flanc/frontal **≤ 0,60**.

## LECTURE DES ISSUES, décidée d'avance
- Paie dans l'ANCIEN, ne paie plus dans le MESURÉ →
  **l'avantage du flanc était un artefact de létalité.** Deux semaines de
  conclusions sur la manœuvre sont à reprendre. C'est le résultat le plus probable
  au vu du correctif (frontal 22 %→81 % en pré-test).
- Paie dans les DEUX → l'avantage tient à la géométrie, la létalité ne le portait pas.
  Les conclusions antérieures tiennent.
- Ne paie dans AUCUN → le banc ne sépare plus rien : c'est le banc qu'il faut revoir,
  pas la doctrine.
- Paie dans le MESURÉ seulement → résultat inattendu, à ne pas expliquer après coup :
  on le consigne tel quel et on cherche pourquoi.

## INTERDICTIONS
Aucune retouche des courbes, des seuils ou du nombre d'épisodes après avoir vu un
chiffre. 200 épisodes par bras et par monde, graine 7. Si le run casse, on répare
le harnais et on relance à l'identique.
