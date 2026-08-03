# CRITÈRES ÉTAPE 3b — LE LAGRANGIEN (figés avant la première ligne)

Écrits le 2026-07-29. Plan de Fable, porte rebasée par Opus 5 sur une mesure qu'il n'avait pas.
Arbitrage : Younes.

## CE QUI EST ÉTABLI, MESURÉ
**Contrôle à un seul changement** (étape 2, budget poussé à l'infini, aucune couche réactive,
4 points de contrôle, 2048 épisodes chacun) :
arrivée **24,2 → 22,4 → 24,3 → 28,3 %**, succès 19,5 % à 400 itérations.
→ **La machinerie est saine. Le coupable de l'effondrement est la contrainte de budget.**

**Le piège de terminaison soupçonné est absent** : vérifié en lecture, le dépassement de budget
ne termine aucun épisode depuis la refonte du matin.

**La couche réactive est désarmée** : elle substituait 64 à 74 % des gestes, et une doctrine qui
arrive 94,9 % sans elle n'arrive plus qu'à 1,0 % en la traversant.

## LES DEUX ÉCARTS, qu'il ne faut plus confondre
| écart | de | à | levier |
|---|---|---|---|
| la contrainte | 28,3 % | 0,3 % | ce jalon |
| la compétence | 96,2 % | 28,3 % | l'imitation, étape 4 |

## LA PORTE, REBASÉE — et pourquoi
Fable demandait « arrivée ≥ 60 % de l'arrivée doctrinale », soit 58 %. **Inatteignable par
construction** : l'agent sans aucune contrainte plafonne à 28,3 %, le lagrangien ne peut au
mieux que restaurer ce niveau. La porte mesurait la compétence en croyant mesurer la contrainte.

**Porte rebasée sur le témoin mesuré :**
1. **arrivée ≥ 25,3 %** — à moins de 3 points des 28,3 % du témoin sans contrainte ;
2. **taux de violation ≤ 15 %** — fraction d'épisodes arrivés en dépassant leur budget ;
3. **Spearman(dose, budget) ≥ 0,90** — la dose doit suivre l'ordre. Cette porte redevient une
   mesure et non une illusion, maintenant que l'arrivée n'est plus nulle : un agent immobile ne
   peut plus la franchir.

**Toute porte qu'un agent immobile peut franchir est nulle.** Leçon de v6, inscrite ici.

## LE MÉCANISME — un seul changement par rapport au témoin
La contrainte cesse d'être une pénalité fixe payée dès le premier pas. Elle devient un
multiplicateur qui **part de zéro** et se resserre seulement quand l'agent viole trop souvent :
```
récompense = progrès + succès_à_l_ARRIVEE − λ · exposition_du_pas
λ ← max(0, λ + η · (violation_mesurée − cible))     cible = 0,10, λ init = 0, η = 0,01
```
D'abord apprendre la route, économiser ensuite. Le curriculum est produit par le multiplicateur,
il n'est pas écrit à la main.

**La récompense de succès porte sur l'ARRIVÉE, pas sur le succès contraint.** La contrainte est
désormais le travail de λ, pas celui du prédicat. L'évaluation, elle, continue de mesurer le
succès contraint — c'est la vraie métrique.

## PIÈGE CONNU, à ne pas cacher
Un lagrangien ne garantit la contrainte **qu'à convergence**. Un λ qui monte trop vite reproduit
la pénalité fixe et donc l'immobilité ; trop lentement, la contrainte n'est jamais respectée.
On journalise λ à chaque itération. **Si λ dépasse 1,0 avant l'itération 200, on arrête** : c'est
la signature du retour au piège.

## INTERDITS
- Aucun autre changement dans ce jalon : pas de couche, pas d'imitation, pas de retouche du monde.
- Ne pas ajuster la cible de violation après avoir vu un chiffre.
- Trois graines avant toute affirmation.
