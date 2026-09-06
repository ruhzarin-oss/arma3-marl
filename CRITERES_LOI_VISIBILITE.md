# CRITERES — LA LOI VISIBILITE -> TOUCHER, MESUREE SUR ARMA 3

Ecrits AVANT tout chiffre.

## LA QUESTION
`visible ** 2` vient de RV1 (`Target.cpp:1611`). **Ce n est qu une hypothese.** Sa porte
voisine (`MinVisibleFire`) vient d etre falsifiee sur Arma 3 le 03/09 : rien ne dit que
l exposant tienne. On MESURE donc P(toucher | fraction de corps visible) chez le
certificateur, au lieu de continuer a l importer.

## LE DISPOSITIF — UN DUEL, PAS UNE MELEE
Le falsificateur a livre des impacts SANS leurs coups tires : on ne peut pas en tirer une
probabilite. Il faut le DENOMINATEUR. En melee 8 contre 8 on ne sait pas a qui un coup
etait destine ; on revient donc au duel, comme la courbe du 26/07 :
un tireur, une cible, **tous deux invulnerables** (une cible qui tombe rend son bras muet ;
un tireur qui meurt supprime la condition — les deux pieges sont deja payes le 28/07).
Sessions COURTES et repetees : l IA cesse d engager apres ~60 s une cible qui ne tombe pas.
Plusieurs duels SIMULTANES et eloignes pour le debit.

La fraction de corps visible est relevee **AU DEPART DU COUP**, sur cinq points pied->oeil —
la meme sonde que le falsificateur, et la grandeur qu emploie le moteur.

## CE QUI FERAIT ECHOUER LA MESURE
- **Denominateur nul ou minuscule** : moins de 200 coups tires -> on ne conclut pas.
- **Pas d etalement** : si toutes les visibilites tombent dans une seule case, il n y a pas
  de courbe a mesurer. Il faut au moins **trois cases peuplees** (>= 30 coups chacune).
- **Controle positif** : dans la case pleinement visible (frac = 1) a 100 m, le taux de
  toucher doit retomber dans la bande de la courbe certifiee du 26/07 — **30 % debout a
  100 m**. Accepte entre **0,15 et 0,50**. Hors de cette bande, le banc mesure autre chose
  que le toucher et **rien n est lu**.

## CE QUI SE DEPOSERA
L exposant `a` de P = P0 * frac^a, ajuste sur les cases peuplees, avec son intervalle.
- `a` proche de 2 -> RV1 tenait, on garde `visible ** 2` et on le dit MESURE.
- `a` franchement different -> on remplace par la valeur mesuree.
- pas de decroissance lisible -> on RETIRE le terme, comme la porte.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la prise, rien sur le transfert, rien sur le canal de designation.
