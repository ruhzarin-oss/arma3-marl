# ✅ LE GEL EST RÉPARÉ — établi par un témoin, avec une réserve écrite

**20/08/2026.** Pré-inscription `b10da04`, attentes écrites **avant** le test.

## LA CAUSE

Le verdict transite par la globale `HMT_PV`, et **l'étiquette du tirage est apposée à la
LECTURE** — elle n'identifie donc pas qui a écrit. Un prévol gelé se réveille après le
`_fige_break` de python et dépose son verdict dans la case que le tirage suivant vient de
remettre à nil. Le jeton de génération existait, mais il ne gardait que les **points de
contrôle** — et un prévol gelé n'en atteint aucun, puisque c'est exactement ce que le gel
lui fait. **La garde manquait là où elle comptait : au moment de déposer le verdict.**

## LE CORRECTIF

Le spawn capture **sa** génération attendue — dans le spawn, jamais dans une globale, qui
serait écrasée par le lancement suivant — et n'écrit `HMT_PV` que s'il est encore le
courant. Sinon il journalise `HMT|SOCLE|PREVOL|VERDICT_TU`.

## LES ATTENTES, JUGÉES

| n° | attente | résultat | |
|---|---|---|---|
| G1 | `gel` → PLANTÉ 3/3 à l'étape T4 | **3/3 à T4** | **PASSE** |
| **G2** | **au moins un `VERDICT_TU` journalisé** | **0** | **ÉCHOUE** |
| G3 | `jambes` → ROUGE 3/3 sur T5 | **3/3 sur T5** | **PASSE** |
| G4 | smoke sans sabotage → VERT | **3/3, porte tenue** | **PASSE** |

## LE TÉMOIN — c'est lui qui établit la causalité

Même socle 5.4.0, même tout, **la garde en moins** (`prevol_sansgarde.py`) :

| | avec la garde | sans la garde |
|---|---|---|
| `gel` | **PLANTÉ 3/3** | **1/3** — et le tirage 2 rend **VERT en 4,9 s** |

Le défaut était donc **pire que diagnostiqué** : il ne produisait pas seulement des échecs
aux écarts vides, il produisait des **VERTS IMMÉRITÉS** — un tirage validé par le verdict
d'un prévol périmé, en cinq secondes.

## LA RÉSERVE, ÉCRITE ET NON MASQUÉE

**G2 a échoué : la garde n'a jamais journalisé son refus.** Le témoin prouve qu'elle est la
cause du changement — même socle, seule différence, résultat inversé — mais **le chemin
exact n'est pas observé**. Trois hypothèses non départagées : (a) le prévol périmé est tué
avec le serveur avant d'atteindre son écriture ; (b) la ligne de journal échoue
silencieusement ; (c) la garde agit par un effet de timing plutôt que par son test.

⚠️ **Une sonde dédiée est due**, et elle n'est pas écrite cette nuit : un mécanisme qui
n'a pas été vu agir reste une hypothèse, même quand son effet est mesuré. C'est le cliquet
de la soirée appliqué à moi-même — *un correctif qui n'a pas été vu agir n'est pas établi*.

Le correctif est **conservé** parce que le témoin établit son effet et que G3 et G4
montrent qu'il ne casse rien. Il sera **confirmé ou remplacé** quand la sonde aura parlé.
