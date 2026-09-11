porte: L oracle a l assaut ne fait pas gagner : savoir ou sont les defenseurs pendant l assaut pose les 3 charges 8 fois sur 18, contre 4 sur 12 sans
date: 2026-09-11
graines: 7, 8, trois repetitions chacune par job ; 3 jobs oracle (instances 1, 3, 5), 2 jobs reference (2, 4), joues en meme temps
chiffre: oracle 8/18 (44 %) contre reference 4/12 (33 %), memes graines, meme charge, meme heure ; critere ecrit avant : reussite >= 15/18, echec <= 9/18 -> ECHEC ; ecart non significatif (Fisher unilateral ~0,4)
verdict: ECHEC
depend_de: controle-positif-reveal-certifie, feu-avant-vignette, alize-reflexe-trop-tard
remplace_par: 
source: runs 2026-09-11_164849_chacal_i1, _164949_i2, _165019_i3, _165049_i4, _165119_i5 ; commit c93fc26

Question posee par Fable apres HMT-39 : quand on sait ou sont les defenseurs, gagne-t-on ? Les defenseurs sont reveles (reveal 4, certifie 20/20) a tous nos hommes et inscrits comme vus, rafraichis au debut de l assaut.
Reponse, pour CET oracle : non. 8 sur 18 contre 4 sur 12, dans le bruit. L information seule, donnee aux hommes, ne change pas l issue de l assaut.
RESERVE MAJEURE (revue de Fable, 11/09) : l oracle est pose APRES le choix de l ouverture (60_phases.sqf, choix l.884-898, oracle l.947). La porte d entree est donc choisie A L AVEUGLE meme avec l oracle (journal : gardes|[0,0]|renseignement|0 au choix). Ce verdict mesure « connaitre les defenseurs pendant l assaut, et donner une cible a l appui », PAS « choisir sa porte en connaissant les defenseurs ». L oracle complet reste a mesurer.
Ce que ca etablit : donner la connaissance aux executants (IA d Arma) ne suffit pas ; l appui qui recoit des cibles en RED part au contact (mesure du 10/09), il ne fixe pas.
Suite possible (Fable, experience 2') : oracle AVANT le choix de la porte, puis oracle + feu d appui dirige depuis une position tenue.
