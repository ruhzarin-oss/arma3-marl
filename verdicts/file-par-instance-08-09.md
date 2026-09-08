# La file était sérialisée par un RÉGLAGE, pas par la machine
**8 septembre 2026.** Commits `ca827b4` (outils) et `d722180` (gymnase).
Critères écrits avant la mesure : `CRITERES_PARALLELE_08_09.md`.

## Le fait
Le gymnase attendait HARMATTAN des heures. La cause n'était pas la file : c'était la tâche
planifiée `HMT_RUN`, réglée en **`MultipleInstances = IgnoreNew`**. Tant qu'un job tournait,
tout déclenchement suivant était **ignoré** — le lanceur n'était même jamais appelé. La
sélection par instance ajoutée le matin même était donc du **code mort**, et elle aurait pu le
rester longtemps : rien ne l'aurait signalé, puisque l'attente ressemblait exactement à ce
qu'elle est censée produire.

> ⭐ **Deux jobs n'avaient jamais eu besoin de la même machine.** Profils distincts (`hmtech0`,
> `hmtech3`), ports distincts (2402, 2432), missions distinctes. Ce qui les sérialisait était
> un **choix du lanceur**, pas une contrainte physique.

## Ce qui a été mesuré
| critère | attendu | mesuré | |
|---|---|---|---|
| **C1** deux jobs en vol | 2 instances, 2 serveurs Arma | chacal i3 (PID 13296) + porte0 i0 (PID 15932) | ✅ |
| **C2** le pont refuse encore | rien déposé, instance nommée | « GYM-13..16 attendent : l'instance 0 est occupée » | ✅ |
| **C3** la course ne passe pas | 1 job pris sur 2 appels simultanés | 1 pris, 1 « verrou i7 tenu par un autre appel » | ✅ |
| **C4** la chaîne `porte0` existe | FIN.json COMPLET, 2/2 graines | COMPLET, 339 s, 2/2 | ✅ |
| **C5** chacal non dérangé | même PID serveur | 13296 avant et après | ✅ |

## Ce qu'il a fallu ajouter, et pourquoi
- **Verrou atomique par `mkdir`.** `Parallel` rend possible que deux appels choisissent le même
  job, ou deux jobs de la même instance. Le verrou par `en_cours` se lit *après* coup : il ne
  protège d'aucune course. C3 le montre en bac à sable — jamais sur la file de production, *un
  contrôle ne doit pas pouvoir abîmer ce qu'il contrôle*.
- **Plafond `MAX=2`.** La parallélisation Arma a été **mesurée** à ×1,86 pour deux instances, et
  rien au-dessus de 13 % ensuite. On ne dépasse pas ce qui a été mesuré : au-delà, on ajouterait
  de la charge concurrente dans des mesures censées être comparables.
- **Le pont balaie deux projets.** Le gymnase est devenu le projet `GYM` ; sans cela ses tâches
  n'auraient **jamais** été déposées — et, là encore, rien ne l'aurait dit.

## ⛔ LE TROU QUI RENDAIT LE PONT MENTEUR
Un job **refusé** par le contrôle d'avant-run ne crée aucun run, donc aucun `FIN.json`, donc le
pont ne rendait rien : la tâche restait **« En cours » dans Plane indéfiniment**.
> **L'absence de nouvelle passait pour du travail en cours.** Un canal qui ne sait pas dire
> « refusé » ne dit pas non plus « en cours » — il ne dit rien, et on lit ce qu'on espère.

Les refus sont désormais rendus avec leur raison, et la tâche repart en « A faire ».
Deux tâches en souffrance ont été retrouvées à l'allumage : **GYM-13** (refusée à 17:30 pour
`outils/` non commités) et **HMT-25** (refusée à 12:46 pour `UnrealEditor` en charge).

## Ce que la sonde a appris en plus
`porte0` n'avait **jamais tourné** ; quatre cases réelles coûtent 5 h. Sonde à 60 s : la chaîne
monte, l'épisode se termine, les répétitions se lisent, la manipulation prend
(**2/2 se sont rapprochés sous 220 m** — l'intention est bien appliquée), et la porte
**REFUSE** la case parce que l'engagement tombe à 0,5 et 0,0.
> ⭐ La porte a refusé de rendre un chiffre là où la mesure n'avait pas eu lieu.
> *Une mesure doit savoir échouer* — celle-ci sait.

Une première sonde à `reps=1` avait été refusée par le banc lui-même (« il en faut au moins 2
par case ») : le banc porte ses propres gardes et elles tiennent.

## En service depuis 17:40
GYM-13 (ASSAILLIR 3:1, 2 graines × 4 répétitions × 600 s) tourne sur l'instance 0 pendant que
chacal poursuit sur la 3. Les trois cases suivantes s'enchaîneront seules, une par instance
libre. La porte zéro n'est pas jugée ici : son critère reste l'**inversion** du classement
ASSAILLIR/ROMPRE entre 3:1 et 1:3, à intervalles disjoints.
