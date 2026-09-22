# Porte de l'apprenti marchand — écrite le 22/09/2026 à 21 h, AVANT toute mesure

## Ce qu'on apprend

Le commerce entre marchés : quel bien part de quel marché, vers lequel, en quelle quantité. Aujourd'hui c'est une
règle (`Monde.commerce_regle`) : elle expédie vers le marché où l'écart de prix couvre le transport et la marge.
L'apprenti est un perceptron à une couche cachée (10 entrées, 10 neurones, 2 sorties : envie d'expédier, part du
camion), soit 132 poids. Il ne voit que des prix, une route, un stock et l'heure — **jamais l'avenir, jamais la
vérité du monde**, comme l'Architecte.

## L'épreuve

Un monde complet de 20 jours avec une **sécheresse** tirée de sa graine : les villages d'une région perdent 55 à 80 %
de leur récolte pendant 7 jours, à partir d'un jour tiré entre 3 et 8. Mondes d'école : graines 1 à 8. Mondes
d'examen : graines 101 à 110, **jamais vus pendant l'apprentissage**.

## La note, écrite d'avance

`note = −100 × (part moyenne de ménages sans nourriture) + (argent gagné par le pays) / 1000`

Les ménages nourris d'abord, l'argent ensuite. Un monde dont la conservation dérive de plus de 1e−6 est invalide.

## La porte

L'apprenti est retenu s'il bat la règle **à la fois** :
- sur la note médiane des 10 mondes d'examen, et
- dans au moins **7 mondes sur 10**.

## Le falsificateur

- Si les trois témoins (règle, aucun commerce, commerce aveugle) rendent la même note à moins de 5 points près,
  **l'épreuve ne mesure rien** : l'apprentissage est annulé, pas l'instrument corrigé après coup.
- Si l'apprenti gagne à l'école mais pas à l'examen, il a **appris ses mondes**, pas son métier : refusé.
- Si la faim est nulle partout chez tous les témoins, la note est au plancher : refusée comme mesure.


---

# Version 2 — 22 h 05, après l'annulation de la version 1 par son propre falsificateur

**La version 1 est annulée.** Ses trois témoins, mesurés avant tout apprentissage sur les 10 mondes d'examen :
règle 50,22 — aucun commerce 49,73 — commerce aveugle 50,39. Moins d'un point d'écart, quand la porte en exigeait
cinq ; la faim était au plancher (0,3 %) et la note était portée par l'argent, qui vient des exportations au port et
ne dépend presque pas du marchand. Une épreuve qui ne sépare pas ses témoins ne mesure pas l'élève.

**Ce qui change.**
- L'épreuve : **deux capitales sur trois** perdent 88 à 98 % de leur récolte pendant **douze jours**, à partir d'un
  jour tiré entre 2 et 4. La nourriture existe encore dans le pays ; il faut l'amener.
- La note : **les habitants seuls**. `note = −100 × (part moyenne de ménages sans nourriture) − 5 × morts`.
  L'argent est retiré de la note (il est toujours mesuré et journalisé, mais il ne juge plus).

**Les témoins de la version 2, mesurés avant tout apprentissage** (10 mondes d'examen, 20 jours) :

| témoin | note médiane | ménages sans nourriture | morts |
|---|---|---|---|
| aucun commerce | −32,97 | 29,2 % | 0,5 |
| règle d'origine | −23,84 | 19,2 % | 0,2 |
| commerce aveugle | −22,64 | 16,8 % | 0,2 |

Dix points séparent le meilleur du pire témoin : l'épreuve mesure. **Et elle apprend déjà quelque chose** : la règle
de rentabilité, qui retient un bien tant que l'écart de prix ne couvre pas la route, **affame la région frappée** —
expédier sans condition fait mieux qu'elle.

## La porte, version 2 (inchangée sur le fond, une exigence ajoutée)

L'apprenti est retenu s'il bat **à la fois** :
- la règle d'origine sur la note médiane des 10 mondes d'examen, **et** dans au moins 7 mondes sur 10 ;
- **le commerce aveugle** sur la note médiane — sinon il n'aura fait que réinventer « expédier toujours ».

## Le falsificateur, version 2

- S'il gagne à l'école (graines 1 à 8) mais pas à l'examen (graines 101 à 110) : il a appris ses mondes, refusé.
- Si sa note d'examen ne dépasse pas celle du commerce aveugle : refusé, quelle que soit sa marge sur la règle.
- Si la conservation dérive de plus de 1e−6 dans un monde : ce monde est invalide, la mesure est refaite.
