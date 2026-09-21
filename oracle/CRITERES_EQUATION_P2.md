# L'équation de l'Architecte en phase 2 — critères écrits avant tout ajustement

*21/09/2026. Point 1 du plan du duel Architecte / Oracle : écrire la règle de l'Architecte comme une **équation**
lisible, pour que l'Oracle puisse ensuite la lire et viser ses failles. Demandé par Younes : pousser EvoGP **à fond**
et brancher un **réseau de neurones** dessus.*

## La question

**Avec seulement ce que l'Architecte perçoit au moment de choisir, et l'option qu'il prend, peut-on prédire s'il
sera compromis en phase 2 — sur des mondes qu'on n'a jamais vus ?**

## Les données — fixées avant d'ajuster

Table `equation/p2/table_p2.csv`, construite par `oracle/table_equation_p2.py` : **1 003 épisodes de phase 2
acceptés**, 18 campagnes, 16 mondes. Sont exclues les campagnes de **contrôle** (téléport, patrouille forcée) et les
**fumées**. Pas de déduplication : le moteur est stochastique (un rejeu de la même graine change d'issue), chaque
épisode est un tirage.

**Population de l'équation :** les épisodes qui **atteignent la décision** et ne sont **pas déjà compromis à ce
moment-là** — ceux où le choix peut encore compter. Les autres sont comptés et rapportés à part.

**Issue :** compromission à la fin de la phase 2.

**Variables permises — ce que l'Architecte sait, lu sur sa ligne de décision (jeu A) :**
l'option ; alarme et temps depuis l'alarme ; hommes vivants ; défenseurs connus ; véhicule vu, véhicule connu ;
menace perçue, menaces vues, menaces connues (par le camp, par l'homme) ; distance perçue de la menace ; menace
mobile ; depuis quand elle est vue ; et, quand ils existent (campagnes du 19/09 et après), moteur entendu, distance
du moteur, véhicule vu dans la fenêtre, nombre de vues de la menace, menace mobile vue, moteur depuis la fenêtre.
Leur absence dans les campagnes anciennes est codée par une indicatrice, pas imputée en silence.

**Variables interdites à l'Architecte — elles décrivent le monde, pas sa perception :** tous les champs `verite_*`,
`moteur_allume` (l'état réel du moteur), `erreur_position` (calculée avec la vraie position). Elles ne peuvent entrer
que dans le **modèle du monde** (jeu B, ci-dessous), jamais dans la règle.

**Jeu B, le modèle du monde — lecture secondaire :** jeu A plus le contexte : Oracle monté ou non, période
rapide, jour ou nuit, types de menace, portée du son, réglages d'observation.

## Les quatre modèles

1. **Constante** — le taux de compromission du pli d'entraînement. C'est la barre à battre.
2. **Régression logistique** (L2, pénalité choisie par validation interne), variables du jeu A **et leurs
   interactions avec l'option** — c'est la forme simple écrite à la main.
3. **Réseau de neurones** — perceptron à deux couches cachées (64, 32), dropout, décroissance des poids, arrêt
   précoce sur une validation interne, **ensemble de 10 réseaux**. Il n'impose aucune forme : il donne **le
   plafond** de ce qui est prévisible dans ces variables.
4. **EvoGP à fond** — sur la 3090. Population **300 000**, **300 générations** dans la validation croisée,
   **5 graines** par pli ; arbres jusqu'à 64 nœuds ; fonctions `+ − × ÷ min max neg > < tanh exp log abs`.
   Trois niveaux de parcimonie (0, 10⁻⁴, 10⁻³ par nœud) pour tracer le front précision / simplicité. Pour
   comparaison : la dernière fois, 5 000 × 50 — soit **360 fois moins** de programmes évalués par graine.

## La validation — sur des mondes jamais vus

**Validation croisée en laissant un monde de côté** : 16 plis, chaque monde testé une fois par un modèle qui ne l'a
jamais vu. Métrique : **score de Brier** (erreur quadratique d'une probabilité), log-perte en second.
IC 95 % de l'écart à la constante par **10 000 rééchantillonnages des mondes**, graine 20260921.

## Les règles de décision, écrites d'avance

- **Une équation est retenue** si son Brier sur mondes neufs est **inférieur à celui de la constante, IC de
  l'écart hors de zéro**.
- **Part du plafond captée** = (Brier constante − Brier équation) / (Brier constante − Brier réseau), rapportée pour
  la logistique et pour EvoGP, si le réseau bat la constante.
- **Formule finale d'EvoGP :** le niveau de parcimonie est choisi **par la validation croisée** (celui qui donne le
  meilleur Brier sur mondes neufs) ; la formule est ensuite réajustée sur toutes les données, population
  **1 000 000**, **600 générations**, **10 graines**, et on garde la meilleure. C'est elle qui sera donnée à lire à
  l'Oracle.
- **Ce que l'équation dit du choix :** probabilité prédite de compromission sous *traverser* et sous *attendre*,
  pour chaque épisode, et la règle qui en découle.

## Falsificateurs

- **Si ni la logistique ni EvoGP ne battent la constante sur mondes neufs** avec le jeu A, l'Architecte n'a **aucune
  règle apprenable** à partir de ce qu'il perçoit, dans le monde tel qu'il a été joué. Ce n'est pas un échec du
  duel : c'est la preuve qu'il faut que l'Oracle **crée** la structure que l'équation apprendra.
- **Si même le réseau ne bat pas la constante**, il n'y a rien de prévisible dans ces variables, quelle que soit la
  forme — et c'est la perception de l'Architecte qu'il faudra enrichir.

## Ce que je sais d'avance et dois dire

Les épisodes viennent surtout d'un monde qui punissait peu (16 % de compromission) ; l'effet de l'option a été
mesuré nul ou non répliqué plusieurs fois. **La réponse la plus probable est une équation plate.** Elle est écrite
pour pouvoir le dire proprement.
