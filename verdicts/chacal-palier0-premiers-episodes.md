porte: CHACAL palier 0, premiers episodes : hors corpus, DEPART=3 trainait
date: 2026-09-07
graines: 3, 4
chiffre: g3 ECHEC EXFIL_MANQUEE (2333 s) ; g4 ABANDON ARTICULATION_ROMPUE (367 s, detachement detruit par la HMG en 86 s)
verdict: VIDE
depend_de: chacal-portes, lanceur-hmt-temoin
remplace_par: 
source: run 2026-09-07_1355_chacal

Les deux episodes portent la ligne AVERT|hors_corpus|depart|3 : CHACAL_DEPART = 3 trainait dans server.cfg depuis une session de mise au point, l'insertion et l'approche n'ont pas ete jouees.
Le « zero vivant » de g4 n'est pas un defaut de comptage : le detachement, pose a 460 m du site sans approche, a ete detruit par la mitrailleuse lourde en 86 s.
Ces deux episodes n'entrent pas dans le corpus. Remede applique : le lanceur ecrit DEPART, IMMORTEL et JOUR a chaque lancement, avec les valeurs du corpus par defaut.
Ce que ca n'etablit pas : rien sur le palier 0 joue en entier ; c'est l'objet du job suivant.
