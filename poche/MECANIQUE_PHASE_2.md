# La mécanique de la phase 2 — étape 0 du monde de poche (22/09/2026)

*Lue dans le code de la mission (`bancs/chacaloracle/mission.Altis/chacal/`) et dans les journaux de 1 678 épisodes de
phase 2 acceptés, zéro épisode joué. Demandée par Fable (`AVIS_FABLE_22_09.md`, étape 0) : chaque mécanisme étiqueté
**mesuré / mesurable / inconnu**, et la règle d'arrêt appliquée avant d'écrire une ligne de la poche.*

## Ce que « compromis » veut dire — le piège n° 1 de Fable, confirmé

`CHACAL_fnc_compromettre` (60_phases.sqf, l. 712) : la compromission n'est **pas** « l'ennemi nous a repérés ». C'est ce
que **le détachement constate**, par trois déclencheurs :

| déclencheur | règle dans le code | part des épisodes de phase 2 |
|---|---|---|
| `COUP_RECU` | un de nos hommes touché par un tir non ouest (`Hit`) | ~10 % |
| `ENNEMI_VU_EN_COMBAT` | nous **voyons** (≤ 700 m, `CHACAL_fnc_voit`, toutes les 2 s) un membre de `CHACAL_EST_SITE` en comportement **COMBAT** | ~10 % |
| `FEU_PROCHE` | un tir non ouest à moins de 45 m d'un de nos hommes (`FiredNear`) | ~3 % |
| aucun | | 74-77 % |

La compromission est donc un événement de **feu** ou de **notre** perception — jamais directement de la leur. L'alarme
(`knowsAbout` du camp est) est une chose séparée.

## Deux découvertes qui changent le périmètre de la poche

**1. « Vu en combat » arrive sans alarme 132 fois sur 180 (73 %).** L'ennemi ne sait pas que nous sommes là, mais nous
voyons un de ses hommes en mode combat, et le détachement se déclare compromis. C'est **notre** perception, pas la
leur.

**2. La patrouille routière fait partie de la « garnison ».** `CHACAL_EST_SITE` est figée à la fin de 30_opfor.sqf
(l. 234 : tous les hommes de l'est hors réserve) — **après** la création de la patrouille de route (`CHACAL_gRoute`,
l. 195) et **avant** celle des menaces de la route (35_menaces.sqf). La patrouille que pilote l'Oracle compte donc pour
« vu en combat » ; le poste de contrôle de `menace_p2`, non.

Mesuré sur les journaux, part des épisodes compromis par chaque cause :

| menace | Oracle | vu en combat | touché | feu proche |
|---|---|---|---|---|
| patrouille | 1 | **44,4 %** | 5,6 % | 0,0 % |
| patrouille proche | 0 | 7,9 % | 6,1 % | 1,8 % |
| patrouille proche | 1 | 12,3 % | 7,7 % | 4,0 % |
| poste proche | 0 | 5,3 % | 9,0 % | 3,2 % |
| poste proche | 1 | 12,9 % | **25,1 %** | 4,4 % |
| les deux proches | 0 / 1 | 9,5 / 11,1 % | 7,4 / 15,6 % | 3,2 / 2,2 % |

L'Oracle ne donne à sa patrouille que des points de passage (`MOVE`, vitesses NORMAL/LIMITED, 45_oracle.sqf l. 172) —
pas de mode combat. **Pourquoi son équipage est en COMBAT quand nous le voyons n'est écrit nulle part** : réaction
propre de l'IA, LAMBS, ou connaissance individuelle sans alarme de camp. Conséquence pour le duel : **une partie de la
« punition » de l'Oracle passe par le fait d'être aperçu**, pas par une détection de sa part.

## Les mécanismes, étiquetés

| # | mécanisme | ce qu'on sait | étiquette |
|---|---|---|---|
| M1 | définition de la compromission (3 déclencheurs) | code lu | **mesuré** |
| M2 | structure de la phase : approche (~11 min dans l'exemple), fenêtre d'observation, décision, attente, traversée, fin | code lu ; durées journalisées | **mesuré** |
| M3 | règle d'attente (option 2) : traverser 45 s après la dernière vue du véhicule, ou 240 s sans l'avoir vu, plafond 420 s ; détachement en `doStop` | code lu (60_phases l. 1074-1088) ; attente médiane **244 s** | **mesuré** ; dérive pendant l'attente **mesurable** (seul `doStop`, pas `disableAI PATH`) |
| M4 | durée de la phase : **467 s** en traversant, **694 s** en attendant (+227 s d'exposition) | journaux | **mesuré** — c'est le piège n° 2 de Fable, réel |
| M5 | réflexe de rupture après compromission (fuite à 400 m, fin de phase) | code lu | **mesuré** |
| M6 | notre perception d'eux (moteur à 900 m, vue 250-450 m de nuit) | bancs du 18-19/09 | **mesuré** |
| M7 | **leur** perception de nous (noyau miroir) | jamais mesuré | **inconnu → mesurable** (étape 2) |
| M8 | **pourquoi l'équipage passe en COMBAT** sans alarme | rien dans le code | **inconnu → mesurable** : journaliser le comportement de la patrouille |
| M9 | qui tire le premier | le journal des tirs est coupé après la mise en place (`removeAllEventHandlers "Fired"`, 50_capture l. 255) | **inconnu → mesurable** : garder le journal des tirs dans le banc miroir |

## La règle d'arrêt de Fable, appliquée

*« Si un mécanisme inconnu domine, le périmètre change avant qu'une ligne soit écrite. »*

« Vu en combat » pèse **~40 % des compromissions** de phase 2, et son moteur (M8) est inconnu. Il domine au sens de la
règle. **Le périmètre change :** la poche ne peut pas être une seule course « leur acquisition contre notre traversée ».
Il lui faut **deux courses** :

1. **Ils nous acquièrent et nous tirent dessus** (touché, feu proche) — noyau miroir M7, tir M9 ;
2. **Nous les voyons en mode combat** — notre perception M6, **mesurée**, fois la probabilité qu'ils soient en COMBAT
   au moment où nous les voyons (M8, **à mesurer**).

La seconde course est, paradoxalement, la plus facile à rendre vraie : sa moitié perception est déjà mesurée. Le banc
miroir de l'étape 2 doit donc aussi **journaliser toutes les 2 s le comportement de chaque membre de la patrouille et du
poste**, et garder le journal des tirs.

Qui tire le premier (M9) reste inconnu : le critère « notre propre feu > 30 % » ne peut pas être évalué sur les journaux
existants ; il le sera par le banc miroir, avant la construction de la poche.
