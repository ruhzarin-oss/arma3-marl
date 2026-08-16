# La chirurgie du couvert — le monde est meilleur, l'apprentissage n'y prend pas

Mesuré le 16/08/2026. Critères déposés avant dans `DEPOT_CHIRURGIE_COUVERT.md`.
**Un seul changement** : le multiplicateur scalaire `1 − 0,7·incover` est retiré ; la
protection ne vient plus que de la rupture de vue, directionnelle par construction.

## L'opération passe son examen

| | référence | **opéré** | porte |
|---|---|---|---|
| protection par la rupture de vue | ×7,48 | **×6,72** | > 2 ✓ |
| létalité par homme-pas | 0,0402 | **0,0433** | 0,01-0,30 ✓ |
| les 8 caps déplacent | 8/8 | **8/8** | 8/8 ✓ |
| prise de l'**ancienne** politique | 51,1 % | **42,6 %** | 20-80 ✓ |

**Le contrôle positif déposé est franchi** : après avoir retiré la seule protection scalaire,
être derrière un masque protège encore ×6,72. Le monde opéré **a des abris, et ils sont
directionnels**.

## Le fait qui éclaire tout

**La rupture de vue protégeait déjà ×7,48 dans le monde d'origine.** Le multiplicateur
scalaire n'ajoutait qu'un ×1,2 par-dessus.

**Et pourtant l'ancienne politique perd 8,5 points quand on le retire** — 51,1 → 42,6.
Elle s'appuyait donc sur un abri qui pèse un cinquième chez elle et **rien du tout sur
Arma**. C'est exactement le défaut de type que Fable avait nommé sans le mesurer.

## LE RÉENTRAÎNEMENT ÉCHOUE

140 itérations dans le monde opéré, graines **held-out** :

| bras | monde opéré | (monde de référence) |
|---|---|---|
| **appris** | **4,3 %** | 51,1 % |
| frontal | 4,4 % | 12,8 % |
| **flanc** | **25,0 %** | 34,3 % |

**La politique réentraînée fait le score de l'assaut frontal bête, et le flanc écrit à la
main la bat six fois.** L'ordre est **inversé** par rapport au monde de référence.

## Ce que ce n'est PAS

**Ce n'est pas un monde injouable** : l'ancienne politique y fait **42,6 %**, le flanc 25 %.
La prise est atteignable.

**C'est l'apprentissage qui n'y prend pas.** La courbe le dit : mètres parcourus de 18 à 80,
prise bloquée à **0,8 %** au 139ᵉ pas. **Elle apprend à avancer, pas à arriver.**

## Trois lectures possibles, aucune tranchée

1. **budget trop court** — 140 itérations suffisaient dans un monde où l'abri scalaire
   donnait un signal facile ; sans lui l'exploration est plus dure ;
2. **façonnage inadapté** — le guide à 0,001 par mètre gagné suffisait à amorcer là-bas ;
   ici il pousse à marcher sans apprendre à survivre ;
3. **le monde est plus juste ET plus dur**, et 140 itérations ne sont plus le bon prix.

Ces trois-là **se départagent par une seule mesure** : rejouer l'entraînement à budget
multiplié. Je ne la lance pas sans l'avoir déposée.

## Ce que ça coûte au dossier

**Le monde de référence reste le seul où l'on sache entraîner.** Donc le 59,4 % qui sert
d'étalon garde son statut — mais on sait désormais qu'il est obtenu dans un monde dont le
couvert est **mal typé**, et qu'une politique qui y apprend perd 8,5 points dès qu'on retire
la béquille.

**L'ordre inversé est le vrai signal** : dans un monde au couvert directionnel, **la
doctrine écrite à la main bat l'apprentissage**. C'est cohérent avec ce que le gymnase
disait déjà — le feu-et-mouvement scripté y faisait 46,1 % contre 51,1 % à la politique,
soit neuf dixièmes de la valeur sans le moindre apprentissage.
