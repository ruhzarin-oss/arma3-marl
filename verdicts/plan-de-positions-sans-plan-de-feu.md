porte: Un plan de positions sans plan de feu : UN defenseur tue cinq assaillants, le detachement tire UNE balle
date: 2026-09-09
graines: 8, palier 4
chiffre: l'unite adverse 3 tire 36 coups entre 4959 et 4997 s et signe LES CINQ morts (CHEF, ADJOINT, DEMO_1, DEMO_2, MEDECIN) ; le detachement de dix hommes tire UN seul coup sur tout l'episode, a 4996,57 s, une demi-seconde avant la mort de son tireur ; l'element d'appui, deux hommes en position, tire ZERO
verdict: PASSE
depend_de: chacal-portes, etre-vu-tue-2x, angle-mort
remplace_par: 
source: run 2026-09-09_1115_chacal, graine 8

Au palier le plus leger jamais joue — quatre defenseurs, aucune arme lourde, aucune reserve, aucune patrouille — le dispositif se forme correctement et l'assaut est aneanti en trente-huit secondes. L'attribution des morts, faite sur le journal, ferme le diagnostic : ce n'est pas quatre defenseurs qui tuent cinq hommes, c'est UN SEUL.
Le detachement ne riposte pas. Un coup tire en un episode entier, par le MEDECIN, une demi-seconde avant de mourir. L'element d'appui, en place et vivant, n'a pas tire une balle.
La cause est de conception, et elle tient en une ligne du script : `CHACAL_POS_APPUI = CHACAL_OP`. **La position d'appui EST la position d'observation.** L'observatoire est choisi en phase 3 pour ce qu'il VOIT, un gain d'altitude de 183 m a 773 m du site. A cette distance, de nuit, couche, avec le regard fixe sur le centre du site, l'appui n'a aucune cible qu'il puisse engager — alors meme que son mode de tir est bien passe a RED au debut de l'assaut.
Le plan articule donc trois elements dans l'espace et n'ordonne jamais un appui par le feu. L'assaut franchit les derniers metres sans que personne ne cloue le defenseur qui l'attend.
Ce que ca explique en arriere : les cinq memes hommes qui meurent dix fois sur dix dans la vignette, l'assaut detruit en 224 s au palier 0, et le fait que retirer la mitrailleuse ou tripler le plafond ne change rien. Ces leviers agissaient sur le decor d'un probleme de feu.
Ce que ca N'ETABLIT PAS : qu'une position d'appui bien choisie suffise a gagner. C'est la mesure suivante, et elle demande une position choisie pour ses vues de TIR sur l'ouverture, a portee utile, distincte de l'observatoire.
Ce que ca condamne : doubler l'effectif. Vingt hommes dans la meme geometrie gagneraient par attrition, et le corpus retiendrait « charger avec plus de monde » comme geste gagnant. Le run a vingt reste utile comme CONTROLE — si vingt echouent aussi, le nombre n'etait pas la variable.
