# Les douze manques du monde — programme décidé par Younes le 22/09/2026 à 23 h

« Mets en place immédiatement les 12 points ; tu peux couper les autres serveurs, on part sur celui-ci. »
La ferme CHACAL est arrêtée (tâches `HMT_ORACLE` et `HMT_RUN` désactivées, `STOP` posé, exécuteurs tués,
un seul serveur Arma vivant : celui du monde). Ce fichier est le programme, et chaque point porte sa porte.

## Vague 1 — ce qui commande tout : des agents qui décident et qui paient

| # | manque | ce qu'on fait | porte | falsificateur |
|---|---|---|---|---|
| 1 | personne ne décide | les ménages choisissent **combien de nourriture stocker** ; les habitants choisissent **de changer de métier** | l'agent qui apprend fait moins de jours de faim que la règle sur 10 mondes jamais vus, dans ≥ 7 | si la règle est déjà au plancher de faim, l'épreuve est nulle |
| 2 | la conséquence ne revient pas | chaque ménage reçoit sa propre récompense le lendemain (faim, dépense) | la récompense moyenne monte pendant la formation | une récompense qui monte sans que la faim baisse = mesure fausse |
| 3 | rien ne dure | **doctrine commune** (poids partagés) + **mémoire personnelle** par ménage, écrites sur disque, rechargées au départ | un monde relancé repart avec la doctrine apprise et fait mieux qu'un monde neuf | si le fichier ne change rien, la mémoire est décorative |
| 4 | la qualification est complaisante | l'agent **agit** sur des mondes jamais vus (sécheresse tirée), pas de questions écrites par moi | écart formé / non formé mesuré sur mondes inédits | gagner à l'école et perdre à l'examen = mémorisation |

## Vague 2 — le monde lui-même

| # | manque | ce qu'on fait | porte |
|---|---|---|---|
| 5 | personne ne naît ni ne vieillit | naissances, vieillissement, retraite, mort naturelle | la population tient 90 jours sans s'effondrer ni exploser |
| 6 | l'armée n'est qu'un dépôt | unités réelles, ravitaillement, garnisons incarnées | un convoi coupé vide la garnison dans le délai calculé |
| 7 | les convois sont des nombres | camions incarnés dans Arma, **réseau routier d'Arma** au lieu du vol d'oiseau ×1,3 | l'écart entre distance calculée et trajet réel < 15 % |
| 8 | les lois sont toujours obéies | fraude, marché noir, refus de travailler | une taxe trop lourde produit de la fraude mesurable |
| 9 | les maladies sont invisibles | malades conduits à l'hôpital dans Arma, soignants incarnés | un malade grave se retrouve à l'hôpital dans le jeu |

## Vague 3 — la machine

| # | manque | ce qu'on fait | porte |
|---|---|---|---|
| 10 | le monde ne dure pas | reprise d'un instantané **dans Arma**, cycles enchaînés | un pays qui vit 7 jours d'affilée, arrêts compris |
| 11 | une seule bulle | bulles multiples, montée en charge jusqu'au plafond | 300 corps tenus, pouls et images/s mesurés |
| 12 | Claude n'est pas branché | MCP sur le serveur du monde | observer et interroger sans jamais toucher une mesure en cours |

## Ordre d'exécution

1 → 2 → 3 → 4 d'abord, parce qu'ils transforment 13 500 décisions de règle en 13 500 décisions d'agents.
Puis 10 (le monde doit durer pour qu'on apprenne au-delà d'un jour), puis 5, 7, 8, 9, 6, puis 11 et 12.

## Amendement du 22/09, 23 h 45 — la porte du point 1 se durcit d'un témoin

**Premier essai, refusé.** Ménages formés : 17,33 % de jours de faim, 9 mondes sur 10 meilleurs que la règle
(19,16 %) — la porte écrite était donc franchie. Mais le témoin **choix au hasard** fait 13,08 % de faim et
0,1 mort contre 0,7. Un élève battu par le hasard n'a rien appris d'utile : **refusé**.

**Cause trouvée.** La note se lisait le soir même : stocker coûtait de l'argent tout de suite et ne rapportait
rien avant le lendemain. L'élève a donc appris à ne rien stocker. La conséquence remonte désormais sur **trois
jours** (`HORIZON = 3` dans `monde/agents.py`).

**La porte, désormais** : un agent formé doit battre **la règle** (médiane et ≥ 7 mondes sur 10) **et le témoin au
hasard** sur la faim médiane. Cette exigence vaut pour les douze points, pas seulement pour le premier — c'est la
deuxième fois de la soirée qu'un témoin bête bat un élève (voir l'apprenti marchand).
