porte: En vignette d'assaut, le feu de l'appui avant le premier pas fait passer l'assaut de 2 a 5 reussites sur 10 — tendance, pas encore etablie
date: 2026-09-10
graines: 7, 8, cinq repetitions chacune, deux bras apparies (seul CHACAL_FEU_AVANT change)
chiffre: 3 charges sur 3 : feu_avant 0 = 2/10 (graine 7 : 0/5, graine 8 : 2/5) ; feu_avant 1 = 5/10 (graine 7 : 2/5, graine 8 : 3/5) ; Fisher unilateral p = 0,17 ; l'appui tire avant le premier pas de l'assaut dans 7 episodes sur 10 avec, 0 sur 10 sans
verdict: OUVERT
depend_de: plan-de-positions-sans-plan-de-feu, palier4-gagne-une-fois-sur-deux
remplace_par: 
source: runs 2026-09-10_1505_chacal (VA0) et suivant (VA1), vignette depart 5 arret 5, palier 4, appui_feu 1 ; vignette de controle 2026-09-10_1445_chacal

Le plan de Fable du 10/09 : reveler les defenseurs a l'appui, cible designee, feu libre ; l'assaut attend le premier coup ; l'assaut marche en AWARE, ordre relance toutes les 10 s.
A 7 episodes par bras, egalite 2/7 contre 2/7, et Fable avait retire sa phrase « la mission gagne le jour ou l'appui tire avant l'assaut ». Les trois derniers episodes du bras 1 ont tous pose 3 sur 3 : 5/10 contre 2/10. Ecart dans le sens attendu, mais p = 0,17 : il peut venir du hasard.
Deux mesures sures dans ce run :
1. Sans designation, l'appui ne connait aucune cible — la restitution de l'observation donne 0 defenseur dans tous les episodes — et il ne tire pas avant l'assaut.
2. Avec designation en mode RED, dans les episodes ou il ne tire pas, les deux tireurs QUITTENT leur position : 11 a 18 km/h pendant l'attente, l'un finit a 72 m des defenseurs, un autre a 400 m. RED = « engage a volonte » : l'appui part au contact au lieu de tirer.
Ce que ca N'ETABLIT PAS : quelle piece du plan agit. Trois mecanismes changent ensemble (designation, attente, relance de l'ordre). La relance est soupconnee de casser la marche du porteur vers la tour — non verifie.
Suite decidee avec Fable : ne plus empiler. Brique 1 = controle positif de l'appui seul (YELLOW, fixe sur place, LAMBS coupe sur les deux tireurs ; 4 defenseurs reveles ; tous tues en 60 s dans 8 essais sur 10).
