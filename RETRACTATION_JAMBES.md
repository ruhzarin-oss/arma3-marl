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

## CE QUI TUE LE VERDICT — et ce n'est pas le bras 7

⟨correction portée après l'audit de Fable, 16/08 22 h⟩ Ma première rédaction s'appuyait sur
le bras 7. **C'est la mauvaise preuve.**

Le verdict disait « **ne déplace pas** un fantassin posé » — une affirmation déterministe.
Elle est falsifiée net par le **bras 1** : sept hommes posés, sept déplacements, 12,2 m,
dispersion 11,6–12,5. Un seul contre-exemple suffisait ; il y en a sept.

Le bras 7, lui, est **ambigu** — n = 4, bimodal, et sa colonne « mètres » est une **médiane
que je n'avais pas déclarée**. Un critère posé sur le **minimum** aurait rendu le verdict
inverse. Le statistique fait partie du critère : cliquet déposé en `AMENDEMENT_NATIF.md` § D.

## LES DEUX PHRASES, et il en faut deux

1. **Le mécanisme tombe.** `setVelocity` déplace un fantassin posé. Le vol n'explique rien.
2. **Le phénomène survit et change de cause.** L'immobilité intermittente existe toujours —
   elle vit dans le 0,6 m du bras 7 et dans les rouges de T5. Je n'ai pas retiré le
   phénomène, je l'ai **réattribué** : ce n'est pas la primitive, c'est l'IA qui reprend
   la main. Un verdict qui aurait dit « parfois l'IA reprend la main et l'homme ne bouge
   pas » aurait survécu. Celui que j'ai écrit disait autre chose, et il est mort.

## La faute d'origine, que je n'avais pas nommée

**Ce verdict n'a jamais été acheté.** Ma sonde jugeait quatre causes pré-écrites ; la
séparation sur `isTouchingGround` est une **cinquième signature, trouvée dans les
données**. Et la cause pré-écrite qui survivait était (c) — « vitesse 6, déplacement
nul » —, la signature de l'**obstacle**, jamais traitée.

Le vol était mon **deuxième pari**, et il est entré au registre **avant** son banc.
Cliquet en `CLIQUETS_16-08.md` § 1.

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

## LE 62 % NE RESTE PAS ICI — c'est une charge de fidélité NEUVE

⟨audit Fable⟩ « *Un document de rétractation rétracte. Les verdicts neufs prennent leur
propre banc.* » Le 12,2 m contre 19,7 m est déplacé en `CHARGE_FIDELITE_JAMBES.md` et il y
porte un **sursis NEUF sur le transfert gymnase → live** — même famille que le couvert ×11
et la létalité ×4.

Il interroge directement le prédicat NATIF : parmi les douze colonnes tenues « dans la
plage du gymnase », **lesquelles encodent le déplacement** ? Si le gymnase suppose des
jambes 60 % plus rapides que le monde n'en donne, cette plage est peut-être inatteignable,
ou atteinte à la marge. Non mesuré, non tranché, **ouvert**.

## Ce qui est mesuré, et reste ici

**Le corps rend 12,2 m sur les 19,7 m que le gymnase suppose** (6 m/s × 3,28 s), soit
**62 %**. Ce n'est pas une panne, c'est un écart d'étalonnage, mesuré pour la première fois.

Et **aucun candidat ne fait nettement mieux au sol** : le meilleur, `sans engagement +
doMove + forceSpeed`, rend 13,3 m — 9 % de plus que ce qui tourne déjà. Le bras qui monte
à 15,8 m est **écarté par le critère des 90 % au sol** : à 58 %, c'est du vol.

**CHOIX — pas verdict.** On ne change pas la primitive. ⟨étiquetage imposé par l'audit⟩
Le critère RETENU (≥ 8 m ET ≥ 90 % au sol) était pré-écrit, mais il admet **le bras 1 ET le
bras 6**, et le mot « nettement » n'avait **aucune marge déposée**. Départager 12,2 de 13,3
à n = 6 ou 7 n'est pas possible. C'est donc un choix par défaut — garder ce qui tourne —
défendable, et qui ne se cite pas comme une mesure.

## Réserves, écrites ici et pas ailleurs

- `n` vaut 6 ou 7 par bras, et **4 pour le bras 7** — le lanceur a coupé à 51 essais sur 64.
  La rétractation tient parce que le critère (> 8 m) est franchi largement, mais l'écart
  entre les bras 1, 3, 4, 5 et 6 **n'est pas départageable à ce `n`** et n'est pas revendiqué.
- Banc de LABORATOIRE : un homme seul, hors du feu. Il ne dit rien du déplacement sous le feu.
