# ✅ LE CRITÈRE EST VALIDÉ SUR TIRAGE FRAIS

**20/08/2026, 00 h 50.** Pré-inscription `ce5e3a0`, écrite et committée **avant** la mesure.
Le plancher de **15,2 m** est entré comme **constante** — aucune re-dérivation.
Tirage **graine 23** (la dérivation utilisait 19), ±250 m autour de 4644/5652, **aucun filtre**.

## LE RÉSULTAT

| | n | min | médiane | max |
|---|---|---|---|---|
| **canal sain** | 60 | **17,4 m** | 22,4 | 35,0 |
| **jambes coupées** (`vy = 0`) | 60 | 0,0 | 4,6 | **8,7 m** |
| canal sain, **second passage** | 60 | 17,8 | 22,3 | 37,8 |

| n° | prédiction | obtenu | |
|---|---|---|---|
| P1 | zéro faux-rouge | **0/60** | PASSE |
| P2 | zéro faux-vert | **0/60** | PASSE |
| P3 | max(sabotés) < min(sains) | **8,7 < 17,4** | PASSE |
| P4 | verdict stable entre deux passages | **0/60** | PASSE |

**Marges :** le saboté le plus haut est à **−6,5 m** du plancher ; le sain le plus bas à
**+2,2 m**. Le creux est **plus large** qu'à la dérivation (8,7–17,4 contre 11,8–18,7).

**Règle de trois** : 0 erreur sur 60 par bras borne chaque taux à **≤ 5 %** en confiance 95 %.

## LE CRITÈRE ADOPTÉ

| | |
|---|---|
| **question** | le canal de locomotion est-il vivant dans cette session ? |
| **grandeur** | distance parcourue en 4 s, canal `sv_vz_preserve_10hz`, socle 4.0.0 |
| **échantillon** | les 8 azimuts de la couture (`_a*45`), tous les hommes en parallèle |
| **statistique** | le **MAXIMUM** sur les 8 |
| **seuil** | **15,2 m** |
| **passages** | **1** — verdict stable à 0/60 sur deux dérivations indépendantes |
| **coût** | 8 fenêtres de 5,5 s, ~50 s, quel que soit le nombre de lieux |

## LES RÉSERVES, MAINTENUES ET ÉCRITES

⚠️ **« max ≥ plancher » prouve que les impulsions ARRIVENT, pas que l'homme marche au sol.**
Un azimut parcouru en vol compte comme preuve de vie du canal — c'est correct pour cette
question, et il ne faut pas le lire autrement.

⚠️ **Ce critère ne certifie PAS un lieu.** La grandeur « ce lieu est praticable » n'existe
pas de façon stable (r = 0,771, plafond r² ≈ 0,59) : cinq tentatives l'ont mesuré. Le
critère certifie **une session**, pas un terrain.

⚠️ **Angles morts** ⟨règle 20⟩ : même carte, même région ; serveur au repos (cadence
d'impulsions identique au monde éveillé, nt 39-40 des deux côtés, mais rien n'est dit d'une
charge plus lourde) ; testé contre **un seul** mode de panne — les jambes.

## POURQUOI IL A FALLU CINQ ARRÊTS POUR L'ÉCRIRE

Je cherchais un critère pour **la mauvaise question**. Je voulais certifier un **lieu** —
d'où le **minimum** sur les azimuts, qui hérite du scintillement (un blocage sur trois
change d'avis entre deux passages). Le prévol demandait **une session**, dont la signature
de panne est **globale** — d'où le **maximum**, qui absorbe ce scintillement.

> **La statistique se dérive de la question. Une question mal posée ne se répare pas par
> un meilleur estimateur.**

## CE QUI SUIT, ET CE QUI ATTEND UN AVAL

**Peut se faire** : fusionner placeur et T5 dans le socle autour de ce critère, réécrire
`quatre.py` sans le concept de « faux-reçu » (il meurt avec le sélecteur), retamponner les
six sabotages, rallumer une porte.
**Attend Younes** : l'arbitrage du tempo du gymnase (6 m/s enseignés contre 3,75 rendus en
montée — l'écart persiste après le passage au canal avec gravité), et l'aval sur la fusion,
qui est un changement d'architecture du prévol.
