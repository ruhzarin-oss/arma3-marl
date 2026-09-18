# Criteres pre-enregistres - BANC-SEUIL-18-09 ( ecrit AVANT de poser, 18/09/2026 ~15 h 55, accord de Younes : « go » )

Banc `chacalvue` ( commit 0ccc10f, mission patchee par patch_banc_vue_fine, fumee passee : 6 episodes, 0 erreur SQF ).
Remplace les 7 jobs suspendus de BANC-TROU-18-09 ( ancien banc : 4 episodes sur 6 perdus faute de ligne de vue ).

## Acquis avant cette campagne ( nuit, cible debout regardee, ligne de vue libre, 1 a 2 episodes par point )
connue a 6 s : 50, 100, 150 m ; jamais en 300 s : 173, 198, 300, 600 m. Jour : 300 m jamais ( n = 1 ).
! Tous les points valides entre 150 et 200 m viennent du MONDE 4.

## Jobs - 9 jobs x 2 mondes = 18 episodes, 3 instances
- instance 2, NUIT, mondes 4 et 5 : 160, 155, 165 m ( resserrer le seuil la ou il a ete vu )
- instance 3, NUIT, mondes 6 et 7 : 150, 175, 200 m ( le seuil est-il le meme AILLEURS ? )
- instance 4, JOUR, mondes 4 et 5 : 150, 300, 200 m ( positif de jour, confirmation du 300, puis le milieu )

## Lecture
Par episode VALIDE ( ligne_de_vue = 1, pas de banc_refuse, 0 erreur SQF ) : distance VRAIE = `verite_distance_menace` de
la premiere sonde ( pas la consigne ), `connue` = menaces_connues > 0 avant 300 s, `delai` = premiere sonde connue.
Les episodes refuses ( VOID BANC_SANS_LIGNE_DE_VUE ) sont comptes et exclus.

## Predictions ecrites avant
- MARCHE : tout delai connu <= 10 s ; dans un meme monde, aucun point connu plus loin qu un point inconnu.
- FALSIFICATEURS de la marche : un delai connu >= 30 s ( accumulation a la CWR ), ou une inversion dans un meme monde.
- CONSTANTE : le seuil des mondes 6-7 tombe dans [150 ; 200] comme celui du monde 4. S il en sort ( 150 m inconnue, ou
  200 m connue ), le seuil DEPEND DU LIEU et une equation en distance seule est insuffisante - il faudra une 2e variable.
- JOUR : 150 m connue ( sinon le bras JOUR est muet, rien ne se lit ). Si 300 m est de nouveau inconnue, le seuil de jour
  est dans ]150 ; 300[ et le point 200 m le coupe en deux.

## Limites dites d avance
1 a 2 mondes par point : DESCRIPTIF. Lance pendant PRIX DU TEMPS ( charge archivee par run ). Une seule posture ( debout ),
une seule heure de nuit ( 1 h 30, lune 0,79 ), jumelles de vision nocturne portees : le seuil vaut pour CES conditions.
