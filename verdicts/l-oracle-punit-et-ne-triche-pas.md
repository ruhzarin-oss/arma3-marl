# L'Oracle punit, et il ne triche pas

*20/09/2026, campagne `CONTROLES-ORACLE-V3-20-09`, critères `oracle/CRITERES_CONTROLES_ORACLE.md` écrits avant le
premier épisode. 52 épisodes joués, 36 acceptés, 18 par bras. Statut : **ÉTABLI**, avec les réserves de la fin.*

## Ce qui est établi

**Le canal de punition est ouvert.** Quand on amène la patrouille au contact — points de passage effacés, ordre de
mouvement sur nos hommes toutes les 15 s, médiane du plus proche à **99 m** — elle prend le détachement
**18 fois sur 18**. Le monde sait punir ; il ne le faisait pas parce que personne ne venait.

**L'Oracle ne lit pas nos positions.** Détachement téléporté à plus de 1 000 m (souvent 2,7 à 3,3 km), formation
conservée, personne prévenu : sa croyance sur la case d'arrivée ne bouge pas, **0 violation sur 18**, et la fenêtre
d'observation était réelle (porte de vacuité 18/18, deux décisions sans détection au minimum).

**Et il n'y va même pas par hasard.** Sa patrouille prend pour cible la case d'arrivée dans **11,1 %** des épisodes
téléportés, contre **38,7 %** mesurés sur 62 épisodes Oracle sans téléport. Moins souvent que le hasard.

Huit portes de qualité passées, zéro erreur SQF.

## Ce que ça change

Les six campagnes de résultats nuls — « aucun des sept choix ne dépend de la situation » — n'étaient pas des
mesures d'absence d'effet : **elles mesuraient un monde où personne ne venait faire payer.** Le plancher n'était pas
statistique, il était tactique. Avec un adversaire certifié capable de punir et honnête dans ce qu'il sait, une
campagne neuve peut enfin poser la question du choix.

## Les fautes que ces contrôles ont attrapées, toutes dans mon dispositif

| faute | signature | coût |
|---|---|---|
| contrôle positif qui **passe** au lieu de confronter | la patrouille posée à 300 m repart à 4 000 m | interception lue à 3/16 au lieu de 18/18 |
| clause « la patrouille vise la case d'arrivée » **sans modèle nul** | se déclenche 38,7 % du temps sans téléport | 4 fausses violations, « l'Oracle triche » |
| case d'arrivée = le SITE, donc la garnison | détection immédiate, fenêtre fermée | contrôle vacant, incapable d'échouer |
| mission modifiée **pendant** que douze serveurs jouaient | `DEPLOIEMENT NON PROUVE`, seconde graine sans résultat | 16 épisodes sur 32 |
| porte C2 comptant des **exemplaires** | un rejeu ne remplit jamais l'ancien dossier | porte impossible à satisfaire après un plantage |
| test d'abandon sans garde sur liste vide | `CHACAL_fnc_centre` sur zéro survivant | 4 erreurs SQF, défaut dormant depuis toujours |

## Réserves, écrites ici pour qu'on ne les oublie pas

Trois portes de qualité ont été **relâchées après les avoir vues échouer** (C7 élargie aux épisodes déjà compromis,
C2 réécrite deux fois). Aucune ne touche les lectures CP et CN, aucune ne déplace un seuil d'effet, et chacune
remplaçait un critère mal ciblé — mais elles ne sont pas pré-enregistrées, et je les compte comme telles.

Les trois autres contrôles du plan § 7 restent dus : le **négatif**, la **jouabilité**, et la **calibration du
budget** de l'Oracle.
