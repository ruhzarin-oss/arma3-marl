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

## Résultat — 21/09 16 h 40 : **l'équation est plate, et même le réseau ne voit rien**

Lecture unique, jeu A, 962 épisodes, 16 mondes laissés de côté tour à tour. Brier sur mondes jamais vus :

| modèle | Brier | écart à la constante | IC 95 % par monde |
|---|---|---|---|
| **constante** | **0,1114** | — | — |
| logistique (avec interactions option × perception) | 0,1117 | +0,0003 | [+0,0000 ; +0,0007] |
| **réseau de neurones** (le plafond) | 0,1150 | **+0,0036** | [+0,0011 ; +0,0062] — **pire** |
| EvoGP, sans parcimonie | 0,1229 | +0,0116 | [+0,0039 ; +0,0197] — pire |
| EvoGP, parcimonie 10⁻⁴ | 0,1161 | +0,0048 | [+0,0015 ; +0,0076] — pire |
| EvoGP, parcimonie 10⁻³ | 0,1124 | +0,0010 | [−0,0000 ; +0,0021] |

**Verdict, selon la règle écrite d'avance : aucune équation ne bat la constante sur des mondes neufs — et le réseau
non plus.** Tout ce qui cherche une forme plus riche fait pire : il apprend le bruit de ses propres mondes.

**La formule finale** — parcimonie choisie par la validation croisée, puis 1 000 000 de programmes × 600
générations × 10 graines — est :

> **P(compromis) = 0,10**

Une constante. EvoGP poussé **360 fois** plus loin que la dernière fois, avec toutes les fonctions permises, converge
sur « rien ». Elle est indifférente entre traverser et attendre dans 100 % des épisodes.

### Ce que ça veut dire

- **Ce n'est pas un manque d'effort de l'algorithme** : à ce budget, et avec un réseau qui n'impose aucune forme,
  s'il y avait une structure dans ces variables on l'aurait vue. C'est le premier falsificateur écrit d'avance qui
  est franchi : **l'Architecte n'a aucune règle apprenable à partir de ce qu'il perçoit, dans le monde tel qu'il a
  été joué.**
- Un indice le disait dès la construction de la table : dans ces 962 épisodes, la **distance de la menace n'est
  jamais connue** au moment du choix — la variable est constante. L'Architecte décide aveugle.
- **Pour le duel :** c'est la confirmation que c'est à l'Oracle de **créer** la structure que l'équation apprendra.
  Le diable, qui explore en ce moment même, cherche précisément des situations où une option vaut mieux que
  l'autre ; tant qu'il n'en trouve pas, aucune règle n'a rien à apprendre.
- La règle que lit le diable reste « traverser » : une équation indifférente départage par défaut vers traverser,
  c'est exactement la même cible.

Le modèle du monde (jeu B, variables de contexte) est lu séparément quand son calcul finit.
