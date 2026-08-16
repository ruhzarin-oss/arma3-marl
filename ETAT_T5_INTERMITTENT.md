# ÉTAT AU 17/08 ~01 h 30 — T5 EST INTERMITTENT, CAUSE INCONNUE, J'ARRÊTE

## Le tableau complet, toutes sessions de la journée

| session | socle | contexte | T5 rouge |
|---|---|---|---|
| porte, 21 h | 1.10.0 | 50 prévols, un serveur | **0 / 50** |
| nuit NATIF | 1.10.0 | serveur neuf par épisode, réveil natif | **24 / 34** |
| compare | 1.12.0 | réveils alternés | **17 / 20** |
| normal | 1.12.0 | sans réveil | **2 / 12** |
| compare | 1.13.0 | réveils alternés | **2 / 16** |
| échauffement 45 s | 1.13.0 | le délai de la nuit | **0 / 4** |
| échauffement 150 s | 1.13.0 | délai triplé | **3 / 3** |

## SIX hypothèses réfutées, chacune par la mesure et non par le raisonnement

1. **Le mannequin vivant pendant T5** — corrigé, T5 rougissait encore.
2. **L'eau** — `eau=false`, journal exigé dans le même commit.
3. **La posture couchée** — `STAND` aux quatre tirages.
4. **`setVelocity` ne déplace pas un homme posé** — promu en VERDICT puis **retiré** :
   le banc des jambes rend 12,2 m, sept fois sur sept, 100 % au sol.
5. **Le réveil de l'IA** — T5 passe dans les deux réveils sur le socle 1.13.0.
6. **La cadence d'impulsions** — `nt` = 39-40 et `fps` = 48-49 sur seize tirages, sans écart.
7. **L'échauffement du serveur** — réfuté **à l'envers** : 45 s donne 3 verts sur 4,
   150 s en donne 0 sur 3.

## Ce qui reste vrai, et c'est peu

- `connu:0` — le témoin n'est jamais vu des ennemis.
- `autocombat_reel:false`, `fsm:false`, `path:true` — l'état déclaré est l'état réel.
- `degats:0` — il n'est jamais touché.
- `nt` ≈ 40, `fps` ≈ 48 — la boucle tourne à plein régime.

**Un homme intact, avec ses jambes, que personne ne voit, sous une boucle à plein régime,
fait un mètre en quatre secondes — de façon intermittente et sans variable connue qui suive.**

## Ce que je constate sans l'expliquer

Le phénomène semble se jouer **par session** plutôt que par tirage : des sessions entières
sont bonnes, d'autres entières sont mauvaises. Sur 1.13.0, deux sessions consécutives et
identiques au code près ont donné 3/4 verts et 0/3 verts. **Ce n'est pas affirmé** — c'est
la seule régularité apparente, et elle n'a pas été mise à l'épreuve.

## LA QUESTION DE CONCEPTION, à trancher à froid

**Faut-il T5 ?** Le banc des jambes certifie déjà la primitive de déplacement — 12,2 m par
ordre, sept essais sur sept, dispersion 11,6-12,5, avec son contrôle positif à 46,5 m.
T5 teste, dans un instrument qui bloque tout, ce qu'un banc dédié établit mieux.

Trois issues possibles, aucune choisie ce soir :
- **retirer T5** et s'appuyer sur le banc des jambes, rejoué périodiquement ;
- **desserrer T5** en le portant sur plusieurs essais avec un critère de majorité ;
- **garder T5 tel quel** et payer le diagnostic jusqu'au bout.

Le choix engage tous les épisodes à venir. Il se prend avec Younes et Fable, **pas seul
à une heure et demie du matin après six hypothèses fausses**.

## Ce que je ne fais pas

Ni septième pari, ni nuit relancée, ni npz ouvert. Dix relevés valides dorment dans
`/mnt/data/natif`, ils ne sont pas lisibles à 10 sur 67 et ne le seront pas.
