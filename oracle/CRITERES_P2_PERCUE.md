# Critères pré-enregistrés — P2 avec la menace PERÇUE : la règle est-elle apprenable ?

*19/09/2026, écrits avant le premier épisode. Le verdict 843118c établit que la meilleure option dépend du **type**
de menace. Mais le type n'est pas visible par le détachement : la règle est vraie et injouable. La perception
`moteur_entendu` est désormais confirmée à 900 m (sensibilité 82 %, spécificité 100 %, sur graines neuves).*

## La question

**La modulation tient-elle quand on conditionne sur ce que le détachement PERÇOIT, et non plus sur la vérité ?**

C'est la différence entre une loi de la nature et une règle qu'un agent peut suivre. Une règle qui dépend d'une
chose invisible ne s'apprend pas.

## Le dispositif

Identique au 19/09 (`CHOIX-P2-TYPES-19-09`) à deux choses près : `portee_son = 900`, et la sonde de décision active.
2 options × 2 bras (patrouille 4 / poste 5) × 8 mondes × 4 graines de situation = **128 épisodes**. Option tirée à
pile ou face, écrite dans le job. Observation 260 m, balayage réparé, de nuit, Oracle commandant à 0.

## Les deux lectures, écrites d'avance

1. **Rappel (contrôle)** : modulation par le **type** vrai. Elle doit retrouver le verdict 843118c
   (−0,369 IC [−0,640 ; −0,126]). Si elle ne le retrouve pas, quelque chose a changé dans la mission et la lecture
   principale ne vaut pas.
2. **Principale** : modulation par la **perception** `moteur_entendu` au moment du choix — écart (attendre − tout de
   suite) quand un moteur est entendu, moins le même écart quand il ne l'est pas.

## Les critères

- **APPRENABLE** : l'IC 95 % de la modulation par la perception exclut zéro, et son signe est celui de la modulation
  par le type. La règle « si j'entends un moteur, je traverse ; sinon j'attends » est alors fondée sur ce que
  l'agent voit.
- **NON APPRENABLE** : l'IC contient zéro alors que le rappel (1) retrouve bien la modulation par le type. La
  dépendance existe mais la perception ne la porte pas : il faudra un autre canal.
- **LECTURE NULLE** : si le rappel ne retrouve pas le verdict.

Mêmes portes de qualité Q1 à Q6 que `lire_p2_types.py`, mêmes amendements (remplacement des refusés, retrait d'un
monde, six mondes au minimum). Mêmes IC : bootstrap sur les mondes, graine 20260919.

## Puissance, écrite d'avance

La perception coupe l'échantillon en deux groupes inégaux : environ 20 % des épisodes entendent un moteur (82 % des
patrouilles, soit un quart du total). Le groupe « entendu » comptera ~30 épisodes. **Une modulation de moins de
~45 points ne sera pas établie** — c'est plus exigeant que les 35 points du verdict par type, et c'est le prix à
payer pour conditionner sur une perception imparfaite. Un « non établi » devra se lire comme « trop petit pour ce
dispositif », pas comme « inexistant ».

## Falsificateur

« Si la modulation par la perception n'est pas établie alors que celle par le type l'est, la règle mesurée le 19/09
n'est pas apprenable par l'agent avec cette perception, et il faut un canal qui sépare mieux que 82 / 100. »
