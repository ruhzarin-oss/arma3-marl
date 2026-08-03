# CRITÈRES — COURBE DE CALIBRATION SUR L'ISSUE (figés avant les données)

Écrits le 2026-07-30. Arbitrage : Younes.

## LE CONSTAT QUI L'IMPOSE
Le professeur (débordement) chez le juge externe, 4 attaquants contre 8 défenseurs, n=38 :
**0 prise. Intervalle de Wilson [0,0 % ; 9,2 %]. Étendue inter-blocs 0 point sur 5 blocs.**
Le bac à sable annonce **96,2 %**. Verdict pré-enregistré appliqué : **gymnase condamné pour
cette configuration**, toute revendication qui en découle est gelée — y compris les 72 % de
l'agent affiné.

## LA CAUSE, NOMMÉE
On a calibré les **pièces**, jamais l'**issue**. La courbe de toucher, la courbe de suppression
et la répartition du feu ont été mesurées sur Arma en juillet, chacune juste et reproductible.
Mais l'assemblage n'a jamais été confronté. Les petits biais — couvert un peu généreux, vitesse
un peu haute, détection un peu lente — sont chacun dans la tolérance et vont tous dans le même
sens. Leur produit donne 96 contre 0.

## CE QU'ON MESURE
La même chose dans les deux mondes, à effectifs défenseurs constants (D=8), en faisant varier
les attaquants : **A ∈ {4, 8, 12, 18, 24}**.
Manœuvre : le débordement, dans les deux mondes. Métrique unique : **le taux de prise**.

- Côté juge : `envelop_arma.py --mode envelop`, **n=40 par point**, en blocs de 8, ~1 h par point.
- Côté gymnase : `manuel.py` débordement double, 1024 épisodes par point, instrument certifié.

## CE QU'ON EN TIRE, décidé d'avance
1. **Le point d'accord** : le plus petit A où les deux mondes sont à moins de **10 points** l'un
   de l'autre, bornes de Wilson à 95 % comprises. En dessous de ce A, le bac à sable est
   déclaré non représentatif et aucune revendication n'en sort.
2. **La forme de l'écart** : si l'écart décroît régulièrement avec A, c'est un biais de calibration
   qu'on peut corriger. S'il reste constant ou change de signe, c'est une erreur de structure et
   il faudra chercher ce que le bac à sable ne modélise pas du tout.
3. **Si aucun A ne s'accorde** : le bac à sable ne représente Arma à aucun rapport de forces sur
   cette plage. C'est un résultat, et il condamne bien plus que cet agent.

## INTERDITS
- Ne pas retoucher le bac à sable pendant cette mesure. On mesure l'écart, on ne le répare pas.
- Ne pas changer la manœuvre, les effectifs défenseurs, ni le théâtre entre les points.
- Ne pas lire un point à moins de 32 opérations côté juge.
- Aucune revendication tirée du bac à sable ne reprend vie avant qu'un point d'accord existe.
