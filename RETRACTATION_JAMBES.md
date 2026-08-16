# RÉTRACTATION — `VERDICT_JAMBES.md` EST RETIRÉ

16/08/2026, ~20 h 30. Banc des jambes v3, commit `11fa45c`, 51 essais, 8 bras alternés.

## Ce que j'avais écrit il y a deux heures

> « `setVelocity` à Z = 0 ne déplace pas un fantassin **posé**. Les 25 mètres ne sont pas
> une marche, c'est un vol. »

**C'est faux, et le banc le dit sans ambiguïté.**

| bras | n | mètres | au sol | dispersion |
|---|---|---|---|---|
| **0 · CONTRÔLE** natif + `doMove`, 15 s | 7 | **46,5 m** | 100 % | 32,5 – 56,6 |
| **1 · `setVelocity` à plat — LE BRAS EN SERVICE** | 7 | **12,2 m** | **100 %** | **11,6 – 12,5** |
| 2 · `setVelocity` avec Z | 7 | 15,8 m | **58 %** | 11,8 – 19,9 |
| 3 · pilote + `doMove` | 6 | 11,3 m | 100 % | 10,3 – 14,6 |
| 4 · natif + `doMove` | 6 | 10,0 m | 100 % | 8,6 – 11,5 |
| 5 · sans engagement + `doMove` | 6 | 9,6 m | 100 % | 9,0 – 12,6 |
| 6 · sans engagement + `doMove` + `forceSpeed` | 6 | **13,3 m** | 100 % | 8,7 – 13,6 |
| 7 · **reproduction de T5** | 4 | 14,5 m | 100 % | **0,6 – 14,9** |

La primitive en service déplace l'homme de **12,2 m par ordre, au sol 100 % du temps, sept
essais sur sept, entre 11,6 et 12,5 m.** Il n'y a pas de panne du corps.

## La faute, et elle est de méthode

J'ai généralisé **quatre tirages d'un instrument** en propriété du moteur. La séparation
sur `isTouchingGround` était réelle dans ces quatre tirages ; elle ne décrivait pas
`setVelocity`, elle décrivait l'état particulier de l'homme que T5 emploie.

C'est exactement la règle 16 retournée contre moi : j'ai lu un instrument sans l'avoir
posé sur un cas où le phénomène est connu. Le banc des jambes EST ce cas, et il fallait le
construire **avant** d'écrire le verdict, pas après.

## Ce qui SURVIT du verdict retiré

**T5 est instable, et c'est mesuré** : le bras 7 le reproduit à l'identique et donne
`0,6 – 14,9 m` sur quatre essais — **un essai sur quatre tombe à 0,6 m.** Le phénomène
existe, il est intermittent, et il n'appartient qu'à T5.

Différence entre le bras 1 (jamais en panne) et le bras 7 (en panne 1 fois sur 4) :
le mode **témoin**, qui garde `AUTOCOMBAT`, et **le tir qui précède**. Supprimer le
mannequin ne suffit pas — l'IA garde la menace en mémoire quelques secondes et reprend
la main sur le déplacement.

## Ce qui est LEVÉ

Le sursis posé sur les 20,22 m, sur le facteur ×7,8 et sur le **44,8 % de prise** est
**levé**. Ils ne reposaient pas sur un corps en panne. `VERDICT_LIMITEUR.md`,
`VERDICT_CORPS.md` et le 44,8 % reprennent leur statut d'avant ce soir — ni plus, ni moins.

## Ce qui est ACQUIS, et c'est le vrai gain de la soirée

**Le corps rend 12,2 m sur les 19,7 m que le gymnase suppose** (6 m/s × 3,28 s), soit
**62 %**. Ce n'est pas une panne, c'est un écart d'étalonnage, mesuré pour la première fois.

Et **aucun candidat ne fait nettement mieux au sol** : le meilleur, `sans engagement +
doMove + forceSpeed`, rend 13,3 m — 9 % de plus que ce qui tourne déjà. Le bras qui monte
à 15,8 m est **écarté par le critère des 90 % au sol** : à 58 %, c'est du vol.

**Conclusion : on ne change pas la primitive.** Elle n'est pas le verrou.

## Réserves, écrites ici et pas ailleurs

- `n` vaut 6 ou 7 par bras, et **4 pour le bras 7** — le lanceur a coupé à 51 essais sur 64.
  La rétractation tient parce que le critère (> 8 m) est franchi largement, mais l'écart
  entre les bras 1, 3, 4, 5 et 6 **n'est pas départageable à ce `n`** et n'est pas revendiqué.
- Banc de LABORATOIRE : un homme seul, hors du feu. Il ne dit rien du déplacement sous le feu.
