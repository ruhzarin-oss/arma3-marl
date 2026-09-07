porte: CHACAL palier 0, premiers episodes acceptes par les 15 portes
date: 2026-09-07
graines: 3, 4
chiffre: g3 ECHEC EXFIL_MANQUEE (2333 s, 6 vivants) ; g4 ABANDON ARTICULATION_ROMPUE (367 s, 0 vivant, 8 morts sur 10 par la HMG en 86 s)
verdict: OUVERT
depend_de: chacal-portes, lanceur-hmt-temoin
remplace_par: 
source: run 2026-09-07_1355_chacal

Les deux episodes sont ACCEPTES par le lecteur (LAMBS actif, canaris vus, aucune ligne tronquee), mais ils sont HORS CORPUS : server.cfg portait CHACAL_DEPART = 3, reste d'une session de mise au point du 07/09 a 01:15, et la mission l'a dit (AVERT hors_corpus, approche_non_jouee). L'approche, l'observation et l'articulation n'ont pas ete jouees.
Le zero vivant de la graine 4 est VRAI. Lecture des evenements E|mort : les dix hommes meurent entre 272 s et 358 s, huit par la mitrailleuse O_HMG_01_high_F (id 13, 189 coups), deux par le tireur 5. Le detachement a ete pose en vue d'une garnison de 16 avec une HMG servie, sans approche : c'est une execution, pas une tactique.
L'etiquette ARTICULATION_ROMPUE est fausse : dans 70_verdict.sqf, la branche ABANDON (CHACAL_ABANDON et zero charge) passe AVANT le test « zero vivant », donc un detachement detruit est enregistre comme un abandon. Et 60_phases.sqf ligne 982 declare l'abandon alors que plus personne n'est en vie pour renoncer. Correction proposee, non appliquee : tester _vivants == 0 en premier (ECHEC, DETACHEMENT_DETRUIT), et ne poser CHACAL_ABANDON que s'il reste un homme.
Ce que ca n'etablit pas : rien sur le palier 0 joue en entier. Le lanceur ecrit desormais DEPART, IMMORTEL et JOUR a chaque lancement ; le prochain job doit etre depart 1, et ces deux episodes ne doivent pas entrer dans le corpus.
