porte: CHACAL palier 0, premiers episodes acceptes par les 15 portes
date: 2026-09-07
graines: 3, 4
chiffre: g3 ECHEC EXFIL_MANQUEE (2333 s, 6 vivants, 3 charges sur 3) ; g4 ABANDON ARTICULATION_ROMPUE (367 s, 0 vivant)
verdict: OUVERT
depend_de: chacal-portes, lanceur-hmt-temoin
remplace_par: 
source: run 2026-09-07_1355_chacal

Les deux premiers episodes du palier 0 (aucun defenseur) sont ACCEPTES par le lecteur : LAMBS actif, canaris vus, aucune ligne tronquee.
Les issues sont des issues de mission, pas des refus d'instrument : une exfiltration manquee apres les charges posees, et une articulation rompue a 6 minutes avec zero vivant a un palier sans ennemi.
Ce zero vivant au palier 0 doit etre decompose avant d'etre cru (regle 16). Premiere lecture de g4/serveur.rpt : la ligne PH|6|EXFILTRATION|fin|362.68|DETRUIT|vivants|0 tombe alors que les lignes d'etat S| du meme instant montrent encore les hommes 1,3,4,5,6 avec leur drapeau vivant, et pertes_est vaut 1.
Hypothese a tester : ARTICULATION_ROMPUE declenche une fin de mission qui compte les vivants sur un groupe vide, pas sur les hommes. C'est un defaut de 70_verdict.sqf ou 60_phases.sqf, pas une hecatombe. A verifier sur le RPT avant tout autre run.
