# AMENDEMENT 1 À LA PRÉ-INSCRIPTION RASTER — LE BUDGET ÉTAIT FAUX

**Déposé le 25/08/2026.** Amende `PREINSCRIPTION_RASTER.md`, hachage `06c6d263e68a4172`,
qui reste valide sur tout le reste (les quatre bras, les cinq portes, le brouilleur, la
fenêtre, les canaux).

## LA FAUTE

J'ai pris `iters=140` parce que c'est le **défaut de `boucle.py`**, sans vérifier avec quel
budget les artefacts de référence du dépôt avaient été appris. Ils l'ont été à **1200** —
leurs noms le disent : `pol_1200_g0.pt`, `pol_1200_g1_rejeu_TOMBE.pt`. Le seul artefact
appris à 140 s'appelle `pol_140_reference_TOMBE.pt`.

**C'est le paramètre hérité d'un instrument mort, encore une fois.** Même classe de faute que
le « 6 m/s » du 20/08 : un chiffre cité sans avoir été lu là où il est effectif.

## COMMENT ELLE A ÉTÉ PRISE

**Par le bras A, qui est le contrôle positif du banc.** Mesuré, à 140 itérations :

| unité | prise | mètres tenus |
|---|---|---|
| A graine 0 | **0,7 %** | 70,1 m |
| A graine 1 | **0,3 %** | 70,3 m |
| doctrine `frontal` (scriptée) | 12,8 % | 112,4 m |
| doctrine `flanc` (scriptée) | 34,3 % | 98,5 m |

La référence ne bat pas le hasard, ni aucune doctrine. **Un banc dont la référence n'apprend
pas ne peut rien détecter** : les quatre bras auraient rendu zéro, et l'égalité aurait été
lue comme « le raster n'apporte rien ». C'était un NON-RÉSULTAT déguisé en verdict.

## CE QUI EST CHANGÉ, ET RIEN D'AUTRE

`iters` passe de **140 à 1200**. Les quatre bras, les cinq portes, les trois jeux de graines,
le décodeur et le monde sont **inchangés**.

## POURQUOI CE N'EST PAS UN CRITÈRE DÉPLACÉ

**Aucun chiffre des bras B, C ou D n'existait au moment de cet amendement.** Le run coupé est
archivé sous `raster_banc_140_MALDIMENSIONNE.log` : on peut y vérifier que seules deux unités
ont été jugées, `A:0` et `A:1`. Je n'ai pas vu la revendication avant de changer le budget —
j'ai vu la RÉFÉRENCE échouer, et c'est la seule chose qu'un contrôle positif sert à montrer.

## AJOUT — LE FILM, PAS LA DERNIÈRE IMAGE

À 1200 itérations, un point final unique ne dit pas si une graine a été bonne PUIS s'est
défaite. On évalue donc tous les 200 pas sur **`GRAINES_SELECT`** (201-206) — ni apprises,
ni jugées. **`GRAINES_TEST` n'est lu qu'une fois, à la fin.** La courbe est publiée avec le
verdict ; elle ne sert à sélectionner aucun point de sauvegarde.

## NOTE D'EXÉCUTION

Quatre bras tournent **en parallèle** : mesuré, quatre processus ensemble prennent moins de
temps mural qu'un seul (330 s contre 435 s), GPU à 90 %, 14,5 Gio sur 24. Le parallélisme ne
change aucun résultat — chaque processus a sa graine torch et son monde.
