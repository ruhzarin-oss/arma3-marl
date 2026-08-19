# RÉPARATION DU GEL — attente écrite AVANT le test

**20/08/2026.** Le sabotage `gel` ne rendait PLANTÉ que **1 fois sur 3** (mesure du 19/08,
22 h 26). Il en faut **3 sur 3** : c'est le contrôle positif du détecteur de figement.

## LA CAUSE, ÉTABLIE PAR LECTURE

Le verdict transite par la globale `HMT_PV`, et **l'étiquette du tirage est apposée à la
LECTURE** — elle n'identifie donc pas qui a écrit. Séquence mesurée :

1. tirage 1 gèle à T4 ; python rompt sur figement et passe au suivant ;
2. tirage 2 remet `HMT_PV` à nil et lance son prévol ;
3. le prévol **gelé du tirage 1** se réveille et écrit son `false` dans `HMT_PV` ;
4. tirage 2 lit ce verdict comme le sien — **27 s, écarts vides**. Tirage 3 : 5 s.

Le jeton de génération existait, mais il ne gardait que les **points de contrôle**, et un
prévol gelé n'en atteint aucun — c'est précisément ce que le gel lui fait. **La garde
manquait là où elle comptait : au moment de déposer le verdict.**

## LE CORRECTIF

Le spawn capture **sa** génération attendue et n'écrit `HMT_PV` que s'il est encore le
courant ; sinon il journalise `HMT|SOCLE|PREVOL|VERDICT_TU`.
⚠️ La capture est **dans le spawn**, pas dans une globale : une globale serait écrasée par
le lancement suivant et la garde laisserait tout passer.

## LES ATTENTES, ÉCRITES AVANT

| n° | attente |
|---|---|
| **G1** | `gel` rend **PLANTÉ 3 fois sur 3**, à l'étape **T4** |
| **G2** | au moins **un** `VERDICT_TU` journalisé — la garde doit se voir agir |
| **G3** | `jambes` reste **ROUGE 3/3 sur T5** — le correctif ne casse pas ce qui marchait |
| **G4** | le smoke sans sabotage reste **VERT** — la garde ne mange pas les verdicts valides |

## LE FALSIFICATEUR

> Si `gel` reste sous 3/3, la cause n'est pas (ou pas seulement) l'écriture concurrente du
> verdict, et le correctif est **retiré** plutôt que complété à l'aveugle.
