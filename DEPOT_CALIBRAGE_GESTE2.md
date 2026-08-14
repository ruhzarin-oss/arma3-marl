# Dépôt — règle d'arrêt et lecture du calibrage du geste n°2

Déposé le 14/08/2026 **avant relance**, sur décision de Fable. Les calibrages tournaient
depuis 5 h **sans aucune règle d'arrêt** — ils accumulaient jusqu'à ce que quelqu'un les lise.

## Ce que le calibrage fait

L'aiguille était au butoir : **84,4 % de prise au témoin**, hors de la bande 20-80 % ⟨règle 2⟩.
Un banc où l'on gagne 5 fois sur 6 ne peut rien séparer. On balaie l'effectif défenseur de
**4 à 14** pour trouver le réglage qui ramène le taux dans la bande. **Un seul bras, aucune
comparaison, aucun verdict ne sort de ce run** — c'est du réglage de monde.

## La règle d'arrêt — un n PAR RÉGLAGE, pas une durée

**50 accrochages clos par effectif.** À n = 50, l'intervalle binomial vaut ±11 points vers
80 % — largement assez pour une bande large de 60 points.

11 réglages × 50 = **550 accrochages**. Les serveurs en ont produit **779** au total :
la règle était probablement déjà atteinte, et le scandale est que **personne ne pouvait le
lire** faute d'étiquette de réglage sur les lignes.

## La lecture — unique, déposée avant

**Verdict = le plus petit effectif dont le taux de prise retombe sous 80 %.** Une seule
lecture, pas de relecture, pas d'ajustement après coup.

## L'étiquette obligatoire ⟨règle 17⟩

**La relance n'a lieu qu'après estampillage du réglage sur chaque ligne émise.** Le champ
qui suit `fin` est un identifiant d'accrochage qui **repart à 1 à chaque redémarrage** —
le piège du segmenteur, qui a mordu trois fois. Sans étiquette, la campagne ne part pas.

## Deux serveurs sur le même calibrage — doublon ou réplicat

Critère de Fable, en une phrase : si le tarif calibré est une propriété **du monde**, partagée
par les deux bancs → **doublon**, un serveur suffit ou la grille se partage (A2 prend 4-9,
CT prend 10-14, temps divisé par deux). Si chaque banc reçoit **son** tarif → deux travaux
légitimes, mais **chaque verdict ne se lit que sur son banc**.

*Un calibrage n'a pas besoin de réplicat : une porte se dimensionne, c'est la certification
qui porte les contrôles.*

## Récupération des 779 déjà acquis

Deux clés **indépendantes**, dont l'accord est exigé :
1. les remises à 1 du compteur segmentent le journal ; la séquence des segments se mappe sur
   le calendrier du script de balayage, horodatages à l'appui ;
2. une signature interne par accrochage — identifiants distincts de défenseurs apparus, ou
   lignes de spawn dans le RPT — qui **est** l'effectif.

**Les segments où les deux clés ne s'accordent pas sont jetés.** Un calibrage n'a pas besoin
de tous ses points.
