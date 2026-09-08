porte: CHACAL palier 0, BRAS TEMOIN : marcher droit sur l'objectif ne le prend pas
date: 2026-09-08
graines: 5, 6
chiffre: 2 episodes ACCEPTES, 15 portes vertes sur 15 ; g5 ABANDON ARTICULATION_ROMPUE (103 min, 10 vivants, 0 charge) ; g6 ABANDON COMPROMIS_LOIN (52 min, 6 morts en 15 s par un MRAP a mitrailleuse lourde) ; 0 charge posee sur 3 dans les deux cas
verdict: PASSE
depend_de: chacal-portes, lanceur-hmt-temoin
remplace_par: 
source: run 2026-09-08_0956_chacal

CE N'EST PAS LE PLAN QUI A ETE JOUE. `CHACAL_BRAS = 1` trainait dans server.cfg : les deux episodes sont du BRAS TEMOIN, celui qui saute l'observation et l'articulation et marche droit sur l'objectif.
Le temoin echoue deux fois sur deux, et c'est exactement ce qu'un temoin doit faire s'il vaut la peine d'exister : g5 arrive a 515 m sans dispositif, la rearticulation est refusee, renoncement avec dix hommes intacts ; g6 se fait prendre par le vehicule de route a mitrailleuse lourde du palier 0 et perd six hommes en quinze secondes pendant l'approche.
Ce que ca etablit : le bras temoin ne prend pas l'objectif au palier le plus faible. Le corpus a donc une base de comparaison, ce qui rend le plan mesurable.
Ce que ca N'ETABLIT PAS, et c'est l'erreur que j'ai d'abord commise : rien sur le plan en six phases, qui n'a jamais tourne. Toute lecture « le plan echoue » a partir de ce run est fausse.
Remede applique : le lanceur ecrit TOUS les parametres de mission a chaque lancement, et un controle d'identite refuse l'episode si graine, palier ou bras joues different de ceux du job.
