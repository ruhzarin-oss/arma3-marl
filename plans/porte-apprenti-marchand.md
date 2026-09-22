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
