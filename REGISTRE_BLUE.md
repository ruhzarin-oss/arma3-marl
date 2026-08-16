# Registre — tout verdict LIVE antérieur au `combatMode RED` est SURSITAIRE

Déposé le 16/08/2026, geste 3 du plan de Fable. **Balayage mécanique, pas au cas par cas.**

## La règle

**Tout verdict qui repose sur une mesure faite dans Arma avant le 16/08 est suspect**, parce
que les attaquants y portaient `combatMode "BLUE"` — « ne jamais tirer ». Ils n'ont pas
combattu ; ils ont marché sous le feu.

La règle est **mécanique** : la date et le mode décident, pas mon jugement sur chaque cas.

## ANNULÉS — le désarmement en est la cause directe

| verdict | ce qu'il affirmait | pourquoi il tombe |
|---|---|---|
| `VERDICT_TRANSFERT.md` | 0/20, « la politique ne transfère pas » | hommes désarmés |
| `VERDICT_67.md` | 11,9 % de prise ; **le gel est RÉEL** (p < 10⁻⁶) | le gel valait 7,5 % une fois armé — IC contenant les 3,1 % du gymnase |
| `VERDICT_SERIE3.md` | 3/20 = 15 %, « les premières prises » | désarmés |
| `VERDICT_DESARME.md` | attribuait la cause à `AUTOCOMBAT` | déjà corrigé par `CORRECTIF_DESARME.md` |
| baseline **FLANC 0/18** | la doctrine ne prend jamais | désarmée elle aussi |
| baseline **NATIF** | — | jamais lue : `FSM` recoupé, contrôle tombé |

## SURSITAIRES — mesurés en `BLUE`, mais leur grandeur n'en dépend PAS

Ils tiennent probablement ; ils ne sont **pas citables** tant qu'ils ne sont pas refaits
sous socle 1.2.0.

- `VERDICT_COLONNES_LIVE.md` — les 12 colonnes dans la plage du gymnase. Les colonnes sont
  des **observations**, pas des tirs : le désarmement ne les touche pas. Mais elles ont été
  relevées sur des hommes qui mouraient trop vite.
- `VERDICT_CORPS.md` — le rendement de pilotage (0,42 contre 0,46) et le ×2,8 de
  déplacement. Le déplacement ne dépend pas du tir, **mais la trajectoire d'un homme qui ne
  riposte pas n'est pas celle d'un homme qui combat**.
- `VERDICT_SUBIE.md` (exposition CHOISIE) et `VERDICT_TARIF.md` — mesurés sur des hommes
  désarmés, donc sur une exposition **subie par construction**. À refaire.
- `VERDICT_CACHER.md`, partie Arma — le masquage 1,37. Même réserve.

## DEBOUT — indépendants du live

- `VERDICT_A_GEOMETRIQUE.md` — le couvert 3× plus loin, mesuré **sur la carte seule** ;
- le couvert du gymnase protège **sans cacher** (masquage 1,08) — mesuré au gymnase ;
- `setVelocity` est une **impulsion** — sonde à 3 bras, contrôles positifs ;
- `GYMNASE_4BRAS.md` — le classement FRONTAL/FLANC/SCRIPT/POLITIQUE, pur gymnase ;
- `VERDICT_ESSAI_A.md` — l'étage 1, mesuré sur des **appuis** en `COMBAT`/`RED` ;
- toutes les lois certifiées sur Arma antérieures (toucher, angle mort, être-vu).

## Ce que ce registre coûte, et pourquoi il vaut son prix

**Quatre verdicts annulés, cinq en sursis.** Dont un que j'avais établi à p < 10⁻⁶ et
répété trois séries de suite.

⟨Fable⟩ *« Une p-value mesure parfaitement un monde faux. »*

C'est la raison d'être de ce registre : il ne juge pas la statistique, il juge **le monde
dans lequel elle a été prise**.
