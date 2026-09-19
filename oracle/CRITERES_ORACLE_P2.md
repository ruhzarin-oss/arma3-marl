# Critères pré-enregistrés — l'Oracle punit-il la mauvaise décision sans écraser la bonne ?

*19/09/2026 au soir, écrits avant le premier épisode. Contexte : le monde de CHACAL ne punit rien — `phase_discrete`
réussit dans 85 à 90 % des épisodes quel que soit le choix, les écarts entre options font 10 à 20 points, et le seul
effet « établi » ne s'est pas répliqué (fe897b7). Younes : « l'Oracle est là pour que l'Architecte ne réussisse pas
la mission ». L'Oracle commandant **v2.1** chasse : croyance de doctrine (la route est le passage obligé), doute qui revient
à cette doctrine, patrouille qui ratisse 300 m de route autour de la case où il nous croit et qui reçoit enfin son
point à suivre, budget de 6 déplacements, aucune lecture de nos positions.*

## Ce qu'on veut savoir

Un Oracle utile fait trois choses à la fois, et le test vérifie les trois :
1. il fait **baisser la réussite** hors du plafond — sinon il est un décor ;
2. il ne la fait **pas s'effondrer** — sinon il est un mur, et un mur n'apprend rien ;
3. il fait **payer un choix plus que l'autre** — c'est le seul point qui rend une décision apprenable.

## Le dispositif

Bras PATROUILLE seul (`menace_p2 = 4`) : c'est le seul moyen d'action de l'Oracle au niveau 1.
2 niveaux d'Oracle (0 témoin, 1 actif) × 2 options (1 tout de suite, 2 attendre) × 8 mondes × 4 graines de situation
= **128 épisodes**, 64 jobs mélangés sur 12 instances. Tout le reste comme `P2-PERCUE-19-09` : observation 260 m,
balayage réparé, portée du moteur 900 m, sonde active, de nuit. Oracle : budget 6, doute 15 %, erreur volontaire 15 %,
une décision par minute.

## Portes de qualité (lecture refusée si une seule échoue)

Q1 à Q7 comme `lire_p2_percue.py`, plus deux portes propres à l'Oracle :
- **QO1** : dans au moins 80 % des épisodes à Oracle 1, il a donné **au moins un ordre de patrouille** (`PATROUILLE_*`).
  Sinon il n'a pas joué, et on ne mesure pas l'Oracle.
- **QO2** : **aucune** ligne `CHACAL|O|` dans les épisodes témoins.

## Les trois lectures et leurs critères

Issue primaire `phase_discrete`, moyennes par case, écarts appariés par monde, IC 95 % par 10 000 rééchantillonnages
des mondes, graine 20260919.

1. **Pas un décor** : réussite moyenne à Oracle 1 **inférieure** à celle du témoin, IC de la différence excluant 0.
2. **Pas un mur** : à Oracle 1, la **meilleure** des deux options réussit dans **au moins 40 %** des épisodes.
3. **Il punit un choix plus que l'autre** — le cœur du test : l'interaction
   `I = [écart(attendre − tout de suite) | Oracle 1] − [le même écart | témoin]`.
   Prédiction écrite d'avance : **I < 0** — une patrouille qui ratisse la route rend l'attente près de la route plus
   coûteuse. Critère : IC 95 % de I excluant 0.

**ORACLE UTILE** si les trois tiennent. **DÉCOR** si (1) échoue. **MUR** si (2) échoue. **ADVERSAIRE SANS DÉCISION**
si (1) et (2) tiennent mais pas (3) : il fait perdre, mais autant quel que soit le choix.

## Puissance, écrite d'avance

32 épisodes par case (monde × situation), écart-type d'une interaction ≈ 0,14 : **une interaction de moins de ~30
points ne sera pas établie.** C'est volontairement exigeant : un Oracle qui ne crée pas un écart de cet ordre ne rendra
aucune décision apprenable à la taille de nos campagnes, et c'est précisément la leçon de P2.

## Falsificateur

« Si un adversaire qui chasse, avec un budget, ne crée pas un écart d'au moins 30 points entre les deux options, alors
la décision de traversée n'est pas la bonne décision à apprendre dans ce monde, et l'Oracle doit agir ailleurs
— sur une autre phase, ou avec d'autres moyens (fouille à pied, niveau 2). »

## Limites dites d'avance

- Un seul bras de menace (la patrouille) : ce test ne dit rien du poste.
- Le prior de doctrine (la route est le passage obligé) est **une hypothèse du commandant**, pas une donnée : un
  Oracle qui gagne grâce à elle gagne parce que la carte le lui permet, ce qui est réaliste mais doit être dit.
- Les contrôles de **non-triche** (téléporter le détachement) et de **positif** (traversée à découvert) du plan
  a139c63 ne sont pas joués ici ; ils restent dus avant toute campagne d'apprentissage.

## Contrôle en vol, à la place d'une fumée séparée

À la demande de Younes (« on va pas perdre 15 minutes »), la v2.1 part directement en campagne, sans fumée séparée.
Ses trois changements sont courts (le point de passage courant, le doute vers la doctrine, la vitesse au journal),
et la fumée v2 a déjà validé tout le reste : zéro erreur SQF sur six décisions, ordres donnés, budget dépensé.
En contrepartie, **les premiers épisodes à Oracle 1 sont surveillés en direct**, et la file est suspendue si :
- une seule erreur SQF apparaît ;
- ou la patrouille **ne se rapproche pas** de sa cible après un ordre (`patrouille_a` qui ne baisse pas, ou
  `vitesse_patrouille` nulle sur deux décisions de suite) — c'était exactement le défaut de la v2.
Les épisodes déjà joués avant une suspension ne sont pas lus avec la campagne.
