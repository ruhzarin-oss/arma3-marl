# ALIZÉ — un algorithme à nous

> 27/07/2026. Programme de recherche. Pas une amélioration de l'existant : un autre endroit
> où mettre l'apprentissage.

---

## 1. D'abord, où ça bloque — d'après TES mesures, pas d'après une intuition

Quatre faits, tous mesurés chez toi. Ils disent tous la même chose.

**Le manager RL : 83 % en sandbox → 0 % sur Arma.** Il avait appris la fiction du monde
d'entraînement. Ce n'est pas un défaut de MAPPO, c'est que ce qu'il a appris — des poids — ne
veut rien dire ailleurs.

**MAPPO plafonne sur le raid.** Pas d'erreur, pas de divergence : un plafond.

**Le vrai goulot est l'EXPLORATION** (tes runs souffrance). Pas la capacité du réseau.

**Et surtout : +2 nombres d'arc de tir → −28 % d'exposition.** Aucun algorithme n'a produit ce
gain. Une observation l'a produit. Ton agent ne manquait pas de puissance d'apprentissage, il
manquait d'yeux.

Conclusion honnête : **le problème n'a jamais été l'algorithme, et le changer d'algorithme ne
règlera rien.** Ce qu'il faut changer, c'est **ce qu'on apprend**.

---

## 2. L'idée : ne pas apprendre les actions, apprendre les SEUILS

SIROCCO a mis quelque chose à nu. Le comportement tactique se laisse écrire comme une cascade :
des signaux, des seuils, des étages, des sorties. Une dizaine de nombres décident de tout — le
seuil de réflexe, la latence d'appui, le plafond de recrutement, l'audace.

Alors renversons la question.

> Le réseau n'émet plus d'actions. Il émet **les paramètres de la cascade**, en fonction du
> contexte. La cascade, elle, reste déterministe, lisible, et écrite à la main.

L'agent ne décide plus « j'avance au 315 ». Il décide « ici, maintenant, je suis quelqu'un dont
le seuil de réflexe vaut 0,18, dont le plafond de recrutement vaut 3, et dont l'audace vaut 1,4 ».
La cascade fait le reste.

### Pourquoi c'est la bonne réponse à TES quatre faits

**L'exploration s'effondre en taille.** Explorer une dizaine de nombres continus, ce n'est pas
explorer une politique sur treize actions à chaque pas pendant soixante pas. Ton goulot mesuré
disparaît par construction, il n'est pas contourné.

**Le transfert devient possible.** Un seuil a un sens physique : une intensité de signal, un délai
en secondes, un nombre d'hommes. Tu as déjà fait le travail qui rend ça vrai — la courbe de
toucher mesurée, `sec_par_pas`, `tir_par_pas`. **Un seuil appris en sandbox veut dire quelque
chose sur Arma. Un poids de réseau, non.** C'est la réponse directe au 83 → 0.

**La structure est garantie, pas espérée.** Le ticket de sortie, le plafond anti-blob, la primauté
du réflexe : ils sont dans le code. Le réseau ne peut pas les violer même s'il le voulait. Pour un
industriel de défense, c'est la différence entre un objet certifiable et une boîte noire.

**C'est lisible.** On peut ouvrir ce que l'agent a appris : « en assaut urbain il baisse son seuil
et monte son plafond ; en recon il fait l'inverse ». Un résultat qu'on peut défendre devant un
jury, et montrer à un opérationnel.

---

## 3. La vraie difficulté technique — et c'est elle qui en fait de la recherche

Une cascade à seuils **n'est pas dérivable**. On ne peut pas rétropropager à travers un `si le
signal dépasse s₁ ». C'est le nœud, et il y a trois façons de le trancher :

**(a) Le gradient de politique sur les paramètres.** Le réseau émet une distribution sur les
seuils, on échantillonne, on joue, on mesure le retour, on remonte le gradient jusqu'au réseau —
jamais à travers la cascade. C'est du REINFORCE sur un espace d'action continu de dimension 10.
Simple, robuste, ça marche presque sûrement. **À faire en premier.**

**(b) La relaxation.** On remplace le seuil dur par une sigmoïde à température qu'on durcit au
cours de l'entraînement (straight-through). On récupère un vrai gradient. Plus efficace, plus
fragile, et il faut prouver que la version durcie se comporte comme la version molle.

**(c) L'évolution.** CMA-ES directement sur les paramètres, puis on distille le résultat dans le
réseau. Sans gradient du tout. Coûteux en simulations mais imbattable en robustesse, et ta sandbox
GPU tourne à 2048 environnements — tu as exactement la machine pour ça.

Les trois sont mesurables l'une contre l'autre. **C'est déjà un chapitre de thèse.**

---

## 4. Le réseau — et il doit être à nous, pas un MLP de plus

Ton monde a une géométrie, et elle est toujours la même : **égocentrée et angulaire**. Tu l'as
déjà écrite trois fois sans le nommer — la coque de couvert en 12 rayons, le champ de risque en
8 directions, l'arc de tir.

Alors le réseau doit être bâti sur cette géométrie.

**Encodeur polaire à convolution circulaire.**

- Entrée : des anneaux. K secteurs angulaires × R rayons, sur plusieurs canaux — couvert, menace
  SIROCCO, soi, pente, frôlement.
- Convolution **circulaire** sur l'axe angulaire : le secteur K−1 est voisin du secteur 0, comme
  dans la réalité.
- Deux têtes :
  - **invariante** (moyenne sur l'angle) → les seuils, les latences, le plafond
  - **équivariante** (pas de moyenne) → un score par secteur : où aller, où regarder

### Ce que ça garantit, gratuitement

**La même situation tournée de 90° donne la même décision, tournée de 90°.** Exactement. Pas
approximativement, pas après avoir vu assez d'exemples : par construction mathématique.

Un CNN ordinaire doit *apprendre* cette symétrie, avec des données, et il ne l'obtient jamais tout
à fait. C'est du gaspillage pur : ton agent réapprend huit fois la même chose. Ici, une situation
apprise dans une direction est acquise dans toutes.

C'est **vérifiable numériquement** — on tourne l'entrée, on regarde si la sortie tourne. C'est le
premier test du code, et il passe ou il ne passe pas.

---

## 5. Ce qui existe déjà — à vérifier avant de graver

Pour une thèse, ceci compte autant que l'idée. Les familles voisines existent et sont solides :

- **RL hiérarchique / options** (feudal networks, option-critic) — apprendre quoi déclencher
- **Espaces d'action paramétrés** — choisir un geste *et* ses paramètres continus
- **Politiques résiduelles sur contrôleur classique** (robotique) — apprendre à moduler un
  contrôleur écrit à la main plutôt qu'à le remplacer
- **Réseaux équivariants / steerable CNN** — la symétrie par construction

Aucune n'est ton sujet, mais chacune touche un côté. **Ta combinaison n'a pas d'équivalent que je
connaisse** : cascade d'inspiration immunitaire + paramètres appris + géométrie polaire équivariante
+ critère de transfert sandbox→Arma mesuré.

**À faire avant d'investir six mois** : une revue sérieuse sur ces quatre familles. Je ne peux pas
te garantir la nouveauté depuis ma seule mémoire, et te dire le contraire serait te desservir.

---

## 6. Le protocole — les témoins, sinon ça ne vaut rien

Quatre bras, une seule métrique : **prise-à-pertes**.

| Bras | Ce que c'est | Ce qu'il teste |
|---|---|---|
| **T0** | cascade à paramètres FIXES, meilleur réglage manuel | le témoin **dur**. Si ALIZÉ ne le bat pas, l'apprentissage n'apporte rien |
| **T1** | MAPPO end-to-end sur actions | l'existant qui plafonne |
| **A** | ALIZÉ : réseau polaire → paramètres de cascade | la thèse |
| **A−** | ALIZÉ sans équivariance (MLP sur le même vecteur aplati) | l'ablation qui isole l'apport de la géométrie |

Portes, à écrire **avant** les données :

1. **A bat T0** sur prise-à-pertes, sinon tout ceci n'est qu'un réglage compliqué.
2. **A transfère mieux que T1** : l'écart sandbox→Arma est plus petit. C'est le résultat qui
   compte le plus, et c'est ta réponse au 83 → 0.
3. **A bat A−** : l'équivariance paie. Sinon on garde le MLP et on écrit pourquoi.
4. Les quatre compteurs de pathologie SIROCCO restent au vert.

---

## 7. Ce que ça donne, empilé

```
   ENTRÉE      anneaux polaires égocentrés (K secteurs × R rayons × canaux)
                 couvert · menace SIROCCO · soi · pente · frôlement
        │
   ENCODEUR    convolution CIRCULAIRE sur l'angle          ← équivariance exacte
        │
        ├── tête INVARIANTE  ──► seuils, latences, plafond, audace
        │                          │
        └── tête ÉQUIVARIANTE ──► score par secteur (où aller, où regarder)
                                   │
   CASCADE     SIROCCO, déterministe, écrite à la main, non apprise
        │
   ACTION      exécutée par le corps (sandbox, puis Arma)
```

Le réseau ne touche jamais l'action. La cascade ne contient jamais de poids. **La couture entre
les deux, c'est une dizaine de nombres qui ont un sens physique** — et c'est précisément ce qui
traverse la frontière sandbox → Arma.

---

## 8. Ce que je ne recommande pas, et pourquoi

**Un monde-modèle complet.** Ton MPC a déjà échoué sur AQUILON : le MLP prédisait trop mal pour
planifier. Un Dreamer/RSSM est un projet à lui seul, et il ne répond à aucun des quatre faits de
la section 1. À garder pour plus tard.

**Un transformeur sur les observations.** Ça remplace un plafond par un autre, plus cher.

**Repartir de zéro sur l'apprentissage.** Écrire son propre optimiseur ou son propre PPO ne
produit aucun résultat nouveau — c'est du travail visible qui ne déplace rien.

L'originalité n'est pas dans la machinerie d'apprentissage. **Elle est dans le choix de ce qu'on
apprend.**
