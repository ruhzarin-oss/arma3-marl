# CRITERES — `degat_par_impact` RE-DERIVE, ET LES DEUX STRATIFICATIONS

Ecrits AVANT tout chiffre. Trois demandes de Fable du 04/09 tenues dans UN seul banc.

## POURQUOI C EST AVANT L ALLUMAGE, ET NON APRES
J avais ecrit « la courbe change la FORME du risque, pas son echelle ». **C est faux.** La
courbe a bouge partout (x1,27 a 100 m, x1,80 a 150 m) et surtout **d UNITE** : `0,233` vaut
`0,7 / 3,00 impacts`, et ces 3,00 impacts ont ete comptes avec le capteur qui rendait
**2 164 impacts pour 1 759 balles**. La probabilite de toucher est desormais **par
PROJECTILE** ; le degat, lui, est reste **par impact gonfle**. Les deux ne parlent plus la
meme langue. Allumer ÉQ. 1 la-dessus rendrait tout delta illisible.

## CE QUE LE BANC MESURE — TROIS CHOSES, UN SEUL TIR
1. **Impacts jusqu a la neutralisation**, cible VULNERABLE, capteur repare (un impact par
   PROJECTILE, source appariee). C est l ACTE DE MORT, pas un champ de `HandleDamage`.
2. **Stratification par MODE DE TIR** — `Fired` livre le mode. Elle transforme mon
   explication `CfgWeapons` (les deux non-monotonies tombent sur des transitions de mode) en
   MESURE. Aujourd hui c est une lecture de config, pas un fait mesure.
3. **Stratification par RANG DU COUP** dans l engagement. Une cible INVULNERABLE recoit des
   coups tardifs qu un vrai duel ne contient jamais. **Si `p_touche` depend du rang, la
   courbe est un melange qui ne se transporte pas** — et tout ce qui en depend est suspect.

## LES DEUX OBSERVABLES NE SONT PAS LA MEME — regle imposee par Fable
`degat_par_impact` s AJUSTE sur les impacts-jusqu a-mort. Il se VALIDE sur le 1,8 attaquant
par defenseur. **Jamais la meme observable pour les deux**, sinon l emergence est un
ajustement deguise.

## CE QUI FERAIT ECHOUER
- moins de **30 neutralisations** -> la mediane n est pas rendue ;
- `p_touche` qui varie avec le RANG au-dela de son IC -> **la courbe est declaree melange**,
  et l allumage d ÉQ. 1 est SUSPENDU, pas poursuivi ;
- un seul mode de tir observe -> la stratification par mode ne dit rien, on l inscrit comme
  non rendue au lieu de conclure.

## CONTROLE POSITIF
Cible vulnerable a 100 m, tireur en RED : elle doit TOMBER dans la duree du bloc. Si aucune
neutralisation n arrive, le banc mesure un stand de tir et rien n est lu.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la prise, rien sur ÉQ. 1. Ce banc rend une conversion et deux stratifications.
