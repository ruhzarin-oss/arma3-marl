# VERDICT — LE PRÉVOL A ATTRAPÉ UNE PANNE DU CORPS

16/08/2026, ~19 h. Socle `1.8.0`, sonde du geste sur le commit `8f10a98`.

## Ce qui a été mesuré

Quatre tirages du prévol, chacun journalisant la vitesse relue, l'animation, la posture
et `isTouchingGround` pendant les 4 s de `setVelocity [0, 6, 0]` réémis à 10 Hz.

| déplacement | vitesse relue | `isTouchingGround` | animation | posture |
|---|---|---|---|---|
| **25 m** | 6 / 6 / 6 | **false** | `afal…` (il TOMBE) | STAND |
| **0 m** | 6 / 6 / 6 | true | debout immobile | STAND |
| **1 m** | 6 / 6 / 6 | true | debout immobile | STAND |
| **25 m** | 6 / 6 / 6 | **false** | `afal…` (il TOMBE) | STAND |

**Séparation parfaite sur `isTouchingGround`, 4 tirages sur 4.**

## Trois causes sur quatre réfutées, dans la même passe

Écrites avant la mesure, avec une signature attendue chacune ⟨règle de Fable : le deuxième
pari s'achète avec une sonde⟩.

- **FIGÉ** — réfutée : la vitesse relue vaut 6 dès la première relecture, l'impulsion est appliquée.
- **IA qui ré-engage** — réfutée : elle ne retombe jamais, ni au milieu ni à la fin.
- **POSTURE couchée** — réfutée : `STAND` aux quatre tirages, jamais `Ppne` ni `Pknl`.
- **Le sol** — RETENUE, et elle sépare sans recouvrement.

L'eau est également écartée : le journal des positions, exigé par Fable **dans le même
commit que le correctif**, donne `eau=false` aux deux premiers tirages. Il a servi le jour même.

## Le verdict

**Les 25 mètres ne sont pas une marche, c'est un vol.** Quand l'homme décolle il parcourt
sa distance sans friction ; quand il touche le sol le moteur écrase l'impulsion et il fait
un mètre. `setVelocity` à Z = 0 ne déplace pas un fantassin **posé**.

## Portée — ce n'est pas le prévol qui est en cause

`arma_couture.py:185` déplace l'agent par `_u setVelocity [_vx,_vy,0]` réémis toutes les
0,1 s. **C'est la même primitive, à la composante près : aucune.**

Donc **T5 n'est pas un instrument défaillant : c'est un instrument qui fonctionne et qui
vient d'attraper une panne réelle du corps de l'agent.** C'est son premier attrapage, et
il a bloqué le banc de lui-même (« PREVOL NON VERT — aucun épisode ne sera joué »).

## Ce qui devient sursitaire

Les **20,22 m** déposés le 15/08 (`VERDICT_LIMITEUR.md`, `VERDICT_CORPS.md`) sont
« exactement les 6 m/s × 3,28 s attendus ». Cette mesure n'a pas relevé `isTouchingGround`.
Si elle a été prise sur des hommes qui décollaient, **le facteur ×7,8 mesure une portance,
pas des jambes**. Non réfuté — **sursitaire**, au sens du registre.

Par conséquent le **44,8 % de prise** du 15/08 hérite du sursis : il est mesuré avec un
corps dont la primitive de déplacement n'est pas caractérisée.

## Ce que ça n'établit PAS

- Pas que l'agent ne bouge jamais : le banc a joué des épisodes complets et pris l'objectif.
- Pas la proportion de temps où un agent décolle en épisode : la mesure a été tentée et
  **le prévol l'a interdite**, ce qui est le comportement voulu.
- Pas quelle primitive il faut employer à la place. C'est la mesure suivante.

## Le pas suivant, et il est net

Un banc à quatre bras sur la même scène, grandeur = mètres parcourus en 3,28 s **et** part
de temps au sol :

1. `setVelocity` Z = 0 — le bras en service, plancher attendu ~1 m
2. `setVelocity` avec une composante Z faible
3. `doMove` vers un point à 60 m dans la direction voulue
4. `doMove` + `forceSpeed`

**Contrôle positif obligatoire ⟨règle 16⟩** : le bras 3 doit dépasser 15 m, sans quoi c'est
le banc qui est muet et non les primitives — 48 m ont déjà été mesurés jambes actives.
