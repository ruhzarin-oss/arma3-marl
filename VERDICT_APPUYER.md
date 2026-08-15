# Le verbe APPUYER n'a PAS de primitive démontrée sur Arma

Trois balayages le 15/08/2026 au soir. **Aucun ne rend de verdict déposé** — ce sont des
sondes de diagnostic, pas des bancs. Elles se lisent ensemble.

## Ce que les trois montrent

**Balayage 1 — les ÉTATS** (5 configurations, cible = un muret) : **zéro coup partout.**
Arme en main, arme haute, COMBAT/RED, aucun `disableAI`, ennemi révélé — rien.

**Balayage 2 — les COMMANDES** (5 commandes, cible = un ennemi vivant à 60 m) : toutes
tirent. `forceWeaponFire` 4 · `fireAtTarget` 7 · `doFire` 3 · `fire` 19 · **et l'IA laissée
seule, sans aucune commande : 8.**

**Balayage 3 — l'ISOLATION** (4 conditions) : toutes tirent, **1 à 3 coups**, y compris en
visant une **position vide**. Mon hypothèse « l'IA ne tire qu'sur des ennemis connus » est
**réfutée**.

## La lecture, cohérente avec l'essai A du matin

Vingt commandes envoyées en 8 secondes produisent **1 à 3 coups**. Et **l'IA sans aucune
commande en produit 8.** Les commandes ne démontrent donc pas qu'elles **ajoutent** du feu :
le feu vient de l'engagement propre de l'IA quand elle a un ennemi acquérable.

C'est exactement ce que l'essai A a mesuré ce matin : **94 % du feu part sans ordre.**

Et le zéro du banc `feu_force` s'explique : sa cible était **derrière un muret**, donc jamais
acquise — pas de contact, pas de feu, et les commandes n'y changeaient rien.

**⇒ Il n'existe pas, à ce jour, de primitive démontrée pour faire tirer un homme d'Arma sur
commande.** Le verbe `APPUYER` du plan de Fable n'a pas d'exécuteur.

## Ce que je n'affirme pas

Les comptes sont **minuscules et bruités** — 1 à 19 coups, un essai par condition. Ces
sondes **ne prouvent pas** que les commandes sont inertes ; elles montrent qu'aucune ne se
distingue de l'IA seule à cette taille. **Un verdict demanderait le protocole de l'essai A**
— fenêtres alternées ordre/silence, répétitions — avec une cible **acquérable**, ce que le
banc `feu_force` n'avait pas.

## Aveu de conduite

**J'ai enchaîné trois balayages en tâtonnant**, chacun sur une hypothèse née de l'échec du
précédent. C'est le travers que Fable m'a nommé ce matin : réfuter une hypothèse au prix
d'une mesure. Le bon geste était **un seul banc déposé** avec cible acquérable et fenêtres
alternées.

## Ce que ça change au plan

Le plan de Fable repose sur quatre verbes fermés, dont `APPUYER(secteur)` — et il pariait
que *« le saut de 12 % à 50 % pourrait se cacher là »*. **Ce verbe est aujourd'hui sans
exécuteur.** Avant de bâtir l'étage soldat, il faut soit lui trouver une primitive, soit
retirer le verbe et le remplacer par ce qu'Arma sait faire : **placer un homme en contact
et le laisser engager.**
