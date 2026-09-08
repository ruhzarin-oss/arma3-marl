# Contrôle de la file par instance — critères écrits AVANT la mesure
**8 septembre 2026.** Le changement demandé : le gymnase ne doit plus attendre HARMATTAN sur une
file qui ne concerne pas les deux. Trois pièces ont bougé (`file2.sh`, `plane_pousse.py`, la
tâche `HMT_RUN`). Aucune n'est réputée marcher tant que ce contrôle n'est pas passé.

Contexte au moment du contrôle : **chacal tient l'instance 3** (run `2026-09-08_1415_chacal`).

## C1 — POSITIF : deux jobs en vol sur deux instances
Après dépôt d'une sonde `porte0` d'instance 0 et un déclenchement de `HMT_RUN` :
`queue/en_cours/` contient **deux** jobs, d'instances **3 et 0**, et Windows montre **deux**
`arma3server_x64.exe`.
⛔ **Échoue si** un seul job est en vol, ou si les deux portent la même instance.
*C'est le seul critère qui prouve le résultat demandé. Sans lui, tout le reste est décoratif.*

## C2 — FALSIFICATEUR du pont : le verrou par instance refuse encore
`plane_pousse.py` lancé pendant que la sonde occupe l'instance 0 **n'écrit rien** dans `queue/`
et annonce que l'instance 0 est occupée. Les quatre tâches PORTE ZERO restent « A faire ».
⛔ **Échoue s'il dépose quoi que ce soit** — le verrou n'aurait alors pas été déplacé, il aurait
été **supprimé**, et deux serveurs Arma se battraient pour le profil `hmtech0`.

## C3 — FALSIFICATEUR du verrou atomique : une course ne passe pas
Deux appels de `file2.sh` lancés **en même temps** avec deux jobs d'instance 0 en attente :
**un seul** est pris.
⛔ **Échoue si les deux partent** — c'est précisément ce que le passage en `Parallel` rend
possible et ce que `mkdir` doit interdire.

## C4 — La chaîne `porte0` existe vraiment
La sonde rend un `FIN.json` de verdict **COMPLET** avec **2 graines lues sur 2**, et chaque
`resultat.json` est lisible.
⛔ **Échoue si** FIN.json manque, si une graine ne rend rien, ou si `lire.py` sort en erreur.
*Raison d'être de la sonde : `porte0` n'a jamais tourné. Les quatre cases réelles coûtent 5 h ;
on ne les lance pas sur une chaîne non éprouvée.*

## C5 — CONTRÔLE NÉGATIF : chacal n'est pas dérangé
Le `run.log` de `2026-09-08_1415_chacal` progresse encore après la sonde, et son PID de serveur
est le même avant et après.
⛔ **Échoue si** chacal meurt, perd son serveur, ou cesse d'écrire.

## Ce que ce contrôle NE dit pas
Il ne dit rien de la **fidélité** des mesures jouées en parallèle. La parallélisation Arma a été
mesurée à ×1,86 pour deux instances ; le plafond `MAX=2` de `file2.sh` s'y tient. Au-delà, la
charge concurrente entrerait dans les mesures — `run.sh` l'archive, il ne la neutralise pas.
