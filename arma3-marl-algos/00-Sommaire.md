# Comprendre les algorithmes du RL multi-agents
### Cours en clair — du débutant à la maîtrise, sans être mathématicien

Ce recueil est conçu comme un **cours**. Chaque fiche suit la même progression pédagogique :

1. **Le problème** — la difficulté précise que l'algorithme attaque, et pourquoi les approches
   naïves échouent.
2. **L'idée centrale** — l'intuition qui débloque tout, en une phrase.
3. **Le mécanisme, pas à pas** — comment ça marche réellement, étape par étape.
4. **Les formules, traduites** — chaque formule est donnée, dite en mots, puis illustrée par une
   image *« pour un littéraire »*. On explique aussi *pourquoi* chaque terme est là.
5. **Un exemple concret** — l'algorithme à l'œuvre dans une scène de combat.
6. **Variantes & pièges** — les cousins de l'algorithme, et ses modes d'échec connus.
7. **Pourquoi on l'utilise ici** — son rôle dans ton projet Arma 3.
8. **En dernier regard** — une lecture *philosophique*.

> Aucune formule n'est laissée nue : elle est toujours traduite. Tu peux tout comprendre sans
> mathématiques — mais le contenu, lui, est de niveau expert.

## Ordre de lecture

| # | Fiche | La question qu'elle résout |
|---|---|---|
| 00b | **Écosystème du RL** | D'où vient tout ça, et comment le domaine s'organise-t-il ? |
| 01 | **PPO / MAPPO** | Comment progresser sans que l'apprentissage explose ? |
| 02 | **HAPPO** | Comment des agents *différents* s'améliorent-ils ensemble, à coup sûr ? |
| 03 | **QMIX & décomposition de valeur** | Comment des décisions locales servent-elles le bien de l'équipe ? |
| 04 | **COMA** | Qui, dans l'équipe, a *vraiment* mérité le succès ? |
| 05 | **CMDP / Lagrangien** | Comment réussir la mission *sans* dépasser un seuil de pertes ? |
| 06 | **Auto-jeu & PSRO / ligue** | Comment forger des agents robustes face à un adversaire intelligent ? |
| 07 | **PBT** | Comment régler et diversifier les entraînements tout seuls ? |
| 08 | **PLR (curriculum)** | Comment apprendre à généraliser plutôt qu'à mémoriser ? |

**Deux familles.** Les fiches **00b → 05** décrivent *comment une équipe apprend* (la « boucle
interne »). Les fiches **06 → 08** décrivent *comment on organise les entraînements entre eux* (la
« boucle externe »). À lire en complément : le dossier **« Le RL — maîtriser l'art »** (forces,
échecs, remèdes).
