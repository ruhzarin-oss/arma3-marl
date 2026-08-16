# VERDICT — LA PORTE DU PRÉVOL TIENT

16/08/2026, ~21 h 30. Socle `1.10.0`, commit `5741a81`. `prevol.py 50 normal`.

## Le contrôle positif, D'ABORD

Phrase écrite avant : *« retirer les munitions du témoin doit faire rougir T4 »*.

| | tirages | rouges | dont sur T4 |
|---|---|---|---|
| **sabotage** — munitions retirées | 3 | **3** | **3** |

Diagnostic rendu par le prévol : `arme:oui autoc:true fsm:false path:true mode:RED
dist:14 vue:1 mun:0`. Il ne dit pas seulement non — il **désigne la panne fabriquée**,
et aucune autre.

## La porte

| | tirages | verts | échecs | seuil |
|---|---|---|---|---|
| **normal** | 50 | **48** | **2** | 2 |

**TENUE — mais PILE AU SEUIL**, et ça se dit. Un troisième échec coupait la nuit.

## Les deux échecs, et ils ont la même cause

- tirage 27 — `T4 PLACE SANS VUE : 12 essais, meilleure vue 0.03`
- tirage 28 — `T4 AUCUNE BALLE REELLE — ... dist:40 vue:0 mun:26`

Le placeur cherche douze positions pour le mannequin et n'en trouve parfois aucune avec
ligne de vue. `mun:26` : l'homme est armé et approvisionné. **C'est du relief, pas une
panne d'arme.** Ni la primitive, ni le pilotage, ni le socle ne sont en cause.

## T5 : ZÉRO ROUGE SUR CINQUANTE

C'est le résultat de la soirée. T5 rougissait une fois sur deux à 18 h.

Le correctif — retirer `AUTOCOMBAT` **entre** T4 et T5 — a été posé sur une cause
**mesurée dans le banc des jambes**, pas devinée : bras 1 (`AUTOCOMBAT` coupé) 12,2 m sept
fois sur sept ; bras 7 (`AUTOCOMBAT` gardé après un tir) un essai sur quatre à 0,6 m.

Rappel du coût : entre les deux, **quatre diagnostics faux** — le mannequin vivant, l'eau,
la posture, et enfin `setVelocity` lui-même, ce dernier promu en verdict puis retiré
(`RETRACTATION_JAMBES.md`). Ce qui a tranché n'est aucun raisonnement : c'est un banc qui
met les deux états dans la **même passe**.

## Ce que la porte autorise, et rien de plus

Le prévol est un instrument **jugé** : il sait rougir sur commande, il tient 48 fois sur 50,
et il nomme sa panne. Les épisodes peuvent être joués.

Elle n'autorise pas à citer un chiffre d'épisode : c'est `DEPOT_NATIF.md` qui le gouverne.
