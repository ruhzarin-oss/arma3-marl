# PRÉ-INSCRIPTION — ARGMAX CONTRE ÉCHANTILLONNAGE, écrite avant que l'artefact existe

**23/08/2026, 23 h 30.** Le rejeu de la graine 1 vient de partir (1 200 itérations,
~1 h 40). Son artefact **n'existe pas encore**. Ce document est écrit maintenant.

## Le fait à expliquer

La graine 1 rend **44,1 % en entraînement** (politique échantillonnée, graines
d'entraînement) et **3,3 % à la porte** (argmax, graines jamais vues). Deux différences
sont confondues dans cet écart : **la façon de décider** et **les graines**.

## La grille qui les sépare — 2 × 2, une seule mesure

| | graines d'ENTRAÎNEMENT | graines de TEST |
|---|---|---|
| **argmax** | A | **B** ← c'est le 3,3 % de la porte |
| **échantillonnage** | C ← c'est le 44,1 % de l'entraînement | D |

Aujourd'hui on ne connaît que **B** et **C**, qui diffèrent par **les deux** axes à la fois.
**A** et **D** tranchent.

## Les prédictions

| n° | prédiction | ce qu'elle signifie |
|---|---|---|
| **D1** | **D > 30 %** (échantillonner sur graines de test) | la politique est bonne, c'est **l'argmax qui dégénère** |
| **D2** | **A < 10 %** (argmax sur graines d'entraînement) | l'argmax échoue **même là où elle a appris** → ce n'est pas une affaire de graines |

**Si D1 et D2 passent : dégénérescence de l'argmax.** La politique a appris une stratégie
mixte ; la figer la détruit. Geste appelé : un terme d'entropie, ou une porte qui juge en
échantillonnant — mais **il faudra choisir, et le justifier**.

## Le falsificateur

> **Si D < 10 %** — échantillonner ne sauve rien — alors ce n'est **pas** l'argmax : c'est
> un **sur-apprentissage aux graines d'entraînement**, et l'entropie n'y ferait rien.
> Geste appelé : plus de graines d'entraînement, pas un terme de plus dans la perte.

> **Si D > 30 % ET A > 30 %** — l'argmax marche sur les graines vues et pas sur les autres —
> c'est encore du sur-apprentissage, sous un autre visage.

## Ce qui est interdit ici

- **Ajouter l'entropie avant de connaître la réponse.** Elle réparerait peut-être le
  symptôme, et on aurait un banc vert sans savoir lequel des deux défauts on a corrigé.
- **Changer la porte pour qu'elle échantillonne** avant de savoir. Ce serait déplacer le
  critère pour qu'il dise ce qui arrange — la faute exacte réparée ce matin sur le banc Arma.
- **Conclure sur cette seule graine.** Elle explique **un** échec. Si le mécanisme est réel,
  il devra se retrouver sur une autre graine perdante.
- **Choisir les seuils après.** 30 % et 10 % sont posés ici.
