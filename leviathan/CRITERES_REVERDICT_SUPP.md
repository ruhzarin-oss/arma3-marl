# CRITÈRES FIGÉS — RE-VERDICT DE LA COURBE N°2

Figés **avant** le run. Toute lecture postérieure se juge là-dessus.

## La question

La suppression mesurée sur Arma change-t-elle les verdicts du monde, ou est-ce un
raffinement cosmétique ?

## Le protocole

Même politique **scriptée**, deux mondes, mêmes graines, même géométrie défensive.
**Les deux mondes portent la courbe n°1.** Seule la suppression diffère.

- ANCIEN : tout ou rien (le défenseur supprimé s'éteint, effacé au pas suivant)
- MESURÉ : `supp_residuel=0.08`, `supp_persist=0.35`

Deux doctrines : FRONTAL (droit dessus) et FLANC (fixer + crocheter hors de l'arc).

## Ce qu'on attend, écrit avant de regarder

Le feu de couverture était **gratuitement protecteur** : arroser éteignait l'adversaire.
Il devient **coûteux et partiel**. Donc :

1. La doctrine FLANC, qui utilise SUPPRESS pour fixer, doit **perdre** du terrain — son
   élément de fixation n'éteint plus l'adversaire.
2. Si le flanc **garde** son avantage malgré ça, l'avantage tient à la **géométrie**, pas à
   un bug de suppression. C'est le résultat le plus solide possible.
3. Si le flanc **s'effondre**, alors tout l'avantage mesuré jusqu'ici reposait sur un
   défenseur qu'on éteignait d'un interrupteur — et il faut le redire publiquement.

## Ce qui invalide le run

- Un écart de prise **inférieur à 3 points** entre les deux mondes → changement
  cosmétique, on le dit.
- Politique **apprise** au lieu de scriptée → on mesure son inadaptation, pas le monde.
- Les deux mondes n'ont pas la **même** courbe n°1 → on mélange deux corrections.

## Le verrou

Un paramètre mesuré ne se retouche que par une **meilleure mesure**. Si le résultat déplaît,
il reste. `supp_residuel=0.08` a des intervalles à 95 % disjoints ; `supp_persist=0.35` est
le maillon faible (la décroissance n'a suivi que la cadence, pas la précision).
