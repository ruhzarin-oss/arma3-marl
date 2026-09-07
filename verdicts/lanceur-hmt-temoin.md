porte: Lanceur HMT : un job dans queue/ produit un FIN.json sans session ssh
date: 2026-09-07
graines: 3, 4
chiffre: 2 runs COMPLET (4733 s puis 2793 s), 4 episodes CHACAL, 4 serveurs lances et arretes par PID, 0 session ssh ouverte
verdict: PASSE
depend_de: chacal-portes
remplace_par: 
source: runs 2026-09-07_1125_chacal et 2026-09-07_1355_chacal

Le tuyau planificateur Windows (HMT_RUN) -> file.sh -> controle_avant_run -> run.sh -> bancs/chacal/lancer.sh -> lire.py -> FIN.json -> etat.py tient de bout en bout.
Il a survecu a un vrai redemarrage de la machine (HMT_BOOT, 11:19) et a repris sa cadence seul.
Le premier run a ete REFUSE par la porte lambs_actif : le lanceur demarrait le serveur sans CBA ni LAMBS. C'est l'instrument qui l'a vu, pas la relecture. Corrige (commit 23c2a99), le second run passe les 15 portes sur les deux graines.
Ce que ca n'etablit pas : rien sur le contenu tactique des episodes ; seulement que la chaine mesure et sait refuser.
