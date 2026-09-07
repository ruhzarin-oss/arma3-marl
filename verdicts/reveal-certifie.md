porte: Controle positif de la liaison drone par reveal
date: 2026-08-16
graines: 1
chiffre: bras B 20/20 ont tire, mediane 3,2 s ; bras A0 sans reveal 2/20, mediane 17,8 s
verdict: PASSE
depend_de: drone-arma-rien
remplace_par: 
source: controle-positif-reveal-certifie

Sur 20 repetitions valides, la commande reveal fait tirer en trois secondes une escouade qui sans elle ne tire pas.
Les deux portes deposees avant la mesure passent, la seconde au ras du seuil. L'escouade est en mode natif, aucun tir force : l'IA decide seule.
La premiere tentative avait echoue et elle le reste ; la cause a ete trouvee par un temoin d'ouverture journalise d'avance, pas par une relecture.
Ce que ca requalifie : le moteur n'ayant aucun canal drone vers l'IA, reveal ne sonde pas un mecanisme du monde, il EST la liaison drone ecrite a la main.
Niveau, cadence et latence deviennent donc des parametres de modele a calibrer, pas des faits du jeu.
Ce que ca n'etablit pas : le rendement d'une information injectee. La porte oracle, sur un banc contenant une decision consommatrice d'information, n'a jamais ete jouee.
