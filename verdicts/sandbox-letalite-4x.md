porte: Letalite de la sandbox, cible unique par defenseur
date: 2026-07-28
graines: n/a
chiffre: frontal 22,2 % -> 80,8 % avec selection de cible ; avantage du flanc x1,82 -> x0,82
verdict: ECHEC
depend_de: 
remplace_par: 
source: sandbox-letalite-4x-cible-unique

La sandbox etait environ quatre fois trop letale : la mesure Arma de balles par pas et par defenseur etait appliquee a CHAQUE attaquant separement.
Corrige, chaque defenseur n'engage que l'attaquant vivant le plus proche qu'il peut toucher, et le frontal passe de 22 % a 81 %.
L'avantage du flanc DISPARAIT : dans un monde correctement letal, foncer marche deja, donc manoeuvrer ne paie plus.
Trois hypotheses ont ete refutees avant la bonne ; la quatrieme montre que le flanqueur ne meurt pas d'etre expose plus longtemps mais d'un pas qui coute beaucoup plus cher.
Ce que ca n'etablit pas : le bon modele. Combien de balles les defenseurs mettent reellement sur combien d'hommes differents doit se mesurer sur Arma, rien d'interne ne peut arbitrer.
La source CWR a depuis montre que cible unique est faux aussi comme modele : le nombre d'attaquants engages par defenseur est le RESULTAT d'une boucle d'allocation, pas une constante.
