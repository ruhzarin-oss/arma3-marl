# CRITÈRES FIGÉS — MATRICE DU MANUEL (avant les données)

Figés le 2026-07-28, AVANT tout run. Non négociables après coup.

## QUESTION
Le banc n'avait que deux coups : frontal et débordement, avec des paramètres posés à la
main. Six manœuvres tirées du manuel (`manuel.py`) croisées avec six niveaux de menace.
Deux questions, dans cet ordre :
1. Une manœuvre différente gagne-t-elle selon la menace ?
2. Si oui, combien vaut le fait de CHOISIR — comparé au meilleur choix fixe ?

## DISPOSITIF
Monde MESURÉ figé (courbe n°1, courbe n°2, `cible_unique=True`), aucune courbe retouchée.
A=4 attaquants, D ∈ {4,6,8,10,12,16}, 200 épisodes par cellule, graine 7, 36 cellules.
Manœuvres SCRIPTÉES : le choix n'est pas appris ici. C'est justement ce que la matrice
doit rendre possible ensuite.

## COLONNE EXPLOITABLE
Une colonne D n'est lue que si l'écart de prise entre la meilleure et la pire manœuvre y
atteint **10 points**. En dessous, le répertoire ne sépare rien à ce niveau de menace et
la colonne ne désigne aucun vainqueur.

## VALEUR DE SÉLECTION — le chiffre qui décide de la suite
Chef adaptatif (meilleure manœuvre à chaque menace) moins meilleur choix FIXE, en points
de prise, moyenné sur les colonnes exploitables.
- **≥ +8 points** → l'adaptabilité paie : le répertoire justifie un sélecteur appris.
  (référence : la brique 0 avait mesuré +13 sur l'axe géométrie.)
- **0 à +8** → marginal : une seule manœuvre suffit presque partout.
- **≤ 0** → le répertoire ne sert à rien sur cet axe. Résultat, pas échec.

## LES CONDITIONS DU MANUEL, ÉCRITES COMME PRÉDICTIONS
Chacune est confrontée à la matrice. Le manuel n'a pas mesuré Arma : il est ici source
d'hypothèses, jamais de justification.

| manœuvre | ce que le manuel prédit |
|---|---|
| frontal délibéré | ne paie que contre une défense faible ; doit être battu dès que la menace monte |
| appui-mouvement | doit dominer le frontal partout où la base de feu est à portée |
| débordement simple | doit payer quand la défense a un arc étroit et qu'une fixation crédible existe |
| débordement double | doit PERDRE contre le débordement simple à faible effectif (force divisée en trois) |
| infiltration | doit payer en EXPOSITION, pas en vitesse ni en prise |
| bonds alternés | doit payer là où le frontal s'enlise |

Une prédiction démentie est un résultat qui se consigne, pas une manœuvre à retoucher.

## INTERDICTIONS
Aucune retouche des manœuvres, de leurs paramètres, de la plage de D, du nombre
d'épisodes ou des seuils après avoir vu un chiffre. `manuel.py` est FIGÉ à partir de
maintenant : toute variante future est une manœuvre NOUVELLE, ajoutée, jamais une
correction de l'existante.
