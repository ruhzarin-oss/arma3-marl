# SIROCCO V2 — pousser le modèle jusqu'où il tient, et savoir où il casse

> 27/07/2026. Suite de `SIROCCO.md`. Dix mécanismes que la v1 laisse de côté, classés par
> impact. Et d'abord le problème que la v1 esquive.

---

## 0. D'abord : où la métaphore devient dangereuse

**Le système immunitaire n'a aucun objectif à prendre.**

Sa fonction est la survie de l'hôte. Point. Il n'avance pas, il ne saisit rien, il n'a pas de
terrain à tenir. Poussé jusqu'au bout, un système immunitaire tactique produit un agent qui
survit magnifiquement et ne prend rien.

C'est exactement ce que ton banc FIBUA t'a déjà appris à refuser : **certifier sur
prise-à-pertes, pas sur la survie**. Et c'est le piège que la métaphore tend naturellement,
parce qu'elle est bâtie pour ça.

Donc chaque mécanisme ajouté doit passer une question, et une seule :

> **En quoi ça aide à PRENDRE ?**
> Si la réponse est « ça aide à durer », c'est un piège. On le laisse.

Bonne nouvelle : trois mécanismes du corps sont franchement **offensifs**, et ce sont les plus
intéressants pour toi — la fièvre (§1.7), le sacrifice cellulaire (§1.9), l'inflammation dirigée
(qui concentre au lieu de fuir). Ce sont ceux qu'il faut pousser en priorité, pas les défensifs.
La v1 n'en contient aucun.

---

## 1. Les dix mécanismes manquants, par impact

### 1.1 L'axe du stress — un scalaire qui déplace TOUS les seuils

Le corps a un modulateur global : adrénaline, cortisol. Un seul signal qui décale d'un coup la
réactivité de tout le système. Sous adrénaline, les seuils tombent : on réagit vite, mal, à tout.
Sous cortisol prolongé, l'immunité se déprime — on économise.

**Tactique.** Munitions restantes, pertes subies, temps restant, distance à l'objectif → **un seul
nombre**, l'urgence. Il module tous les seuils de la cascade en même temps.

Ce que ça change : aujourd'hui tes seuils sont fixes. Le même agent joue la même partition à la
minute 1 et à la minute 20, avec 300 cartouches ou 30. Avec l'axe du stress, il devient prudent
quand il a le temps et téméraire quand il ne l'a plus — **sans qu'on ait rien appris de neuf**.

**Aide à prendre ?** Oui, directement : quand le temps manque, l'agent accepte une exposition
qu'il refusait. C'est ce qui fait entrer.

**Coût : très faible.** Meilleur rapport de toute la liste.

---

### 1.2 La sélection négative — le thymus, et c'est un mécanisme d'ENTRAÎNEMENT

Le fait le plus contre-intuitif de l'immunologie : **environ 95 % des lymphocytes T fabriqués
sont détruits avant de servir**. Pas parce qu'ils sont mauvais contre l'ennemi — parce qu'ils
réagissent au **soi**.

L'immunité ne consacre pas l'essentiel de son effort à reconnaître l'ennemi. Elle le consacre à
**ne pas réagir à ce qui n'est pas une menace**.

**Tactique.** Un banc de sélection négative : on génère des variantes de politique, on les passe
sur des situations *sans menace réelle* (des amis qui bougent, des tirs amis, du bruit lointain,
un civil), et on **élimine** celles qui réagissent. Pas de pénalité, pas de shaping : un filtre
binaire, avant l'entraînement principal.

Pourquoi ça compte pour toi : l'auto-immunité (le fratricide) est un compteur qu'on ne peut pas
seulement pénaliser dans une récompense. Une politique qui tire parfois sur un ami reste une
politique qui tire sur un ami. Le thymus l'élimine **par construction**.

**Aide à prendre ?** Indirectement mais fortement : une escouade qui ne se tire pas dessus et ne
se plaque pas sur du bruit avance beaucoup plus vite.

**Coût : moyen.** C'est le seul vrai mécanisme d'entraînement nouveau de cette liste.

---

### 1.3 La sélection clonale — le mécanisme adaptatif réel

On dit « l'immunité adaptative apprend ». C'est faux, et la nuance est utile. Elle ne descend
aucun gradient. Elle fait ceci :

1. générer de la **diversité au hasard** (recombinaison des gènes d'anticorps)
2. tester contre l'antigène
3. **amplifier** ce qui se lie le mieux
4. **muter** les gagnants et recommencer (maturation d'affinité)

C'est de l'évolution, en quelques jours, dans un ganglion.

**Tactique.** Tu as déjà la co-évolution en ligue, entre les runs. Ce qui manque, c'est le même
mécanisme **appliqué au répertoire de réponses, pendant la mission** : contre *ce* défenseur, dans
*cette* rue, quelle variante de réponse s'affine ? Ton officier LLM qui choisit dans un menu
pré-calculé est déjà l'étage 1 de ça. Il manque les étages 3 et 4 — amplifier et muter le gagnant.

**Aide à prendre ?** Oui, c'est le mécanisme même de l'adaptation à un adversaire particulier.

**Coût : élevé.** C'est une grosse brique, à faire en dernier.

---

### 1.4 La présentation d'antigène — le protocole de communication qu'on n'a pas à découvrir

Une cellule infectée ne raconte pas ce qui lui arrive. Elle **affiche un fragment** de ce qu'elle
a rencontré, sur une molécule standard (le CMH). Le lymphocyte qui passe lit le fragment. Format
fixe, contenu variable.

**Tactique.** Les agents ne s'échangent ni leur état ni leurs observations. Chacun **affiche une
signature courte de ce qui le menace** : direction, portée estimée, cadence, encaissé. Le voisin
qui lit cette signature peut agir sans avoir rien vu lui-même.

L'intérêt est méthodologique : la communication apprise entre agents échoue souvent, parce que le
vocabulaire doit être découvert en même temps que la tâche. Ici **le vocabulaire est fixé par la
biologie** — c'est un format, pas un langage. On n'apprend que quoi en faire.

**Aide à prendre ?** Oui : c'est ce qui permet à l'appui de partir sans avoir vu la cible.

**Coût : faible à moyen.**

---

### 1.5 Le drainage est directionnel — un signal qui traverse les murs ment

La lymphe ne diffuse pas dans toutes les directions. Elle est **collectée par des vaisseaux** et
convoyée vers des ganglions précis. La topologie du réseau fait partie du mécanisme.

**Tactique.** Ma v1 diffuse le champ en rond, isotrope. C'est faux, et de façon coûteuse : dans une
ville, ça fait remonter une alarme **à travers un mur**. L'agent de l'autre côté du mur s'alarme
d'un danger qui ne peut pas l'atteindre.

Correction : diffusion **anisotrope**, masquée par la carte de solidité. Le signal remonte la rue,
contourne le bâtiment, ne le traverse pas. Tu as déjà tout ce qu'il faut (`replica.npz`,
`_sample_solid`).

**Aide à prendre ?** Oui : moins de fausses alarmes = moins de temps plaqué = plus d'avance. Et en
FIBUA c'est décisif, puisque tout y est cloisonné.

**Coût : très faible.** À faire tout de suite après l'axe du stress.

---

### 1.6 Le « missing self » — remplir l'étage 0, qui est vide

Entre l'inné (secondes) et l'adaptatif (jours), il y a un trou de plusieurs jours où l'organisme
perd du terrain. La nature l'a comblé avec les **cellules NK**, et leur règle de déclenchement est
remarquable : elles ne tuent pas ce qu'elles **reconnaissent**, elles tuent ce qui **manque du
marqueur du soi**. Elles réagissent à une *absence*.

**Tactique.** Dans ma v1, l'étage 0 (VEILLE) ne fait rien du tout — il attend. Or la règle NK le
remplit exactement : un agent en veille s'oriente vers **la direction où aucun ami ne couvre**.
Le canal SOI existe déjà ; il servait d'IFF et d'anti-blob. Il devient un **déclencheur** : le trou
dans la couverture attire l'attention.

**Aide à prendre ?** Oui : c'est ce qui fait qu'une escouade couvre son secteur en avançant, au
lieu de regarder toute dans la même direction.

**Coût : très faible.** Quelques lignes dans la cascade.

---

### 1.7 La fièvre — dégrader le monde pour tout le monde

Premier mécanisme franchement offensif. Le corps monte en température : **ses propres enzymes
fonctionnent moins bien**, mais celles du pathogène encore moins. On accepte de se dégrader parce
qu'on dégrade l'autre davantage.

**Tactique.** Fumée, suppression généralisée, combat de nuit, brouillage. Toutes ces actions
réduisent la performance des **deux** camps. Un agent qui ne les considère jamais choisit de jouer
à armes égales alors qu'il pourrait jouer à armes inégales.

Le critère de décision est mesurable et non trichable : **engager la fièvre quand mon désavantage
relatif diminue**. Contre un défenseur retranché qui voit loin, la fumée coûte peu à l'assaillant
et beaucoup au défenseur. Contre un adversaire mobile, l'inverse.

**Aide à prendre ?** C'est peut-être le mécanisme qui y aide le plus de toute la liste — et il est
totalement absent de la v1.

**Coût : faible côté décision, dépend de ce qu'Arma expose côté exécution.**

---

### 1.8 L'immunité entraînée — ta question de doctorat, déguisée

Découverte récente et solide : l'immunité **innée** a aussi une mémoire, épigénétique. Le vaccin
BCG protège partiellement contre des infections qui n'ont rien à voir avec la tuberculose.
S'entraîner contre une menace améliore la réponse à des menaces **différentes**.

**Tactique.** C'est exactement ton sujet — le transfert inter-incarnation. La question devient
mesurable : *entraîner sur un type d'engagement améliore-t-il un type non vu ?*

**Aide à prendre ?** Pas directement. Mais c'est la question qui vaut une thèse.

**Coût : c'est de la mesure, pas du code.** Un protocole, un jeu tenu à l'écart.

---

### 1.9 Le sacrifice — payer de sa personne pour informer

Une cellule infectée peut se détruire elle-même en libérant des signaux d'alarme (pyroptose).
Elle paie de sa vie pour que le reste sache.

**Tactique.** Tu as déjà la moitié de l'idée, et c'est ta meilleure trouvaille : le coût n'est pas
« ne pas être vu », c'est **être vu utilement**. La pyroptose en est la version extrême :
**s'exposer exprès pour révéler** la position du tireur.

C'est rationnel dès que l'information vaut plus que l'agent. Sur une escouade de 8 contre un
défenseur invisible, elle vaut souvent plus.

**Attention** : chez toi ce doit être une **décision**, jamais un réflexe. Un réflexe de sacrifice
est une machine à perdre des hommes.

**Coût : faible en mécanisme, délicat en récompense.**

---

### 1.10 Les deux erreurs — le seuil n'est pas un hyperparamètre, c'est la décision

L'immunité arbitre en permanence entre deux fautes : **rater un pathogène** et **attaquer le soi**.
Tout le système est ce compromis. Et l'évolution ne le règle pas une fois pour toutes : elle le
règle **par tissu**. L'œil et le cerveau sont des sites *immuno-privilégiés* — on y préfère laisser
passer une infection plutôt que détruire le tissu par l'inflammation.

**Tactique.** Le seuil doit dépendre de la **mission** et du **lieu**.

- reconnaissance → seuils **hauts** : ne pas réagir, rester invisible, encaisser du risque
- assaut → seuils **bas** : réagir tôt, quitte à sur-réagir
- zones immuno-privilégiées → **on ne réagit pas** : civils, secteur ami, ROE

Ce n'est pas un réglage, c'est une entrée de la mission. Dans la v1, `s1` est une constante — c'est
la principale naïveté qui reste.

**Coût : faible.** Mais il faut décider qui fournit le réglage (l'officier, probablement).

---

## 2. Ce que ça donne, empilé

```
   MISSION ──────────────► seuils de base (recon haut / assaut bas)   §1.10
      │
   AXE DU STRESS ────────► module TOUS les seuils, en continu         §1.1
      │
   ┌──┴─────────────────────────────────────────────────────────┐
   │  0 VEILLE      couvre le TROU de couverture (missing self)  │ §1.6
   │  1 REFLEXE     inchangé                                     │
   │  2 LOCAL       déclenché aussi par la SIGNATURE d'un voisin │ §1.4
   │  3 RECRUTEMENT gradient anisotrope : contourne les murs     │ §1.5
   │  4 ADAPTATIF   + décision de FIÈVRE et de SACRIFICE         │ §1.7 §1.9
   │  5 RESOLUTION  inchangé                                     │
   └────────────────────────────────────────────────────────────┘
      │
   THYMUS ──────────────► élimine les politiques auto-immunes    §1.2
      │                    (avant l'entraînement, filtre binaire)
   SELECTION CLONALE ───► affine le répertoire contre CE défenseur §1.3
```

---

## 3. L'ordre — et pourquoi

**B0 — la sonde `FiredNear`, avant tout.** Rien de cette liste ne change ce fait : le canal
FRÔLEMENT est le seul pari du système. Tant qu'il n'est pas mesuré, tout le reste est bâti sur du
sable.

Ensuite, par rapport impact/coût :

| # | Mécanisme | Coût | Aide à prendre |
|---|---|---|---|
| 1 | Axe du stress §1.1 | très faible | **oui, direct** |
| 2 | Drainage anisotrope §1.5 | très faible | oui (FIBUA) |
| 3 | Missing self §1.6 | très faible | oui |
| 4 | Seuils par mission §1.10 | faible | oui |
| 5 | Thymus §1.2 | moyen | oui, indirect |
| 6 | Fièvre §1.7 | faible + Arma | **oui, le plus** |
| 7 | Présentation d'antigène §1.4 | moyen | oui |
| 8 | Sacrifice §1.9 | faible + récompense | oui |
| 9 | Sélection clonale §1.3 | élevé | oui |
| 10 | Immunité entraînée §1.8 | mesure | non (mais = la thèse) |

---

## 4. Ce qui est déjà codé de cette V2

Les quatre mécanismes à coût faible sont écrits et testés en isolation. **Rien n'est branché.**

| Mécanisme | Où | État |
|---|---|---|
| Axe du stress + seuils par mission §1.1 §1.10 | `sirocco_etat.py` | testé |
| Drainage anisotrope §1.5 | `sirocco.py` → `set_solide()` | testé |
| Missing self §1.6 | `sirocco_cascade.py` → `grad_soi=` | testé |
| Double sélection thymique §1.2 | `sirocco_thymus.py` | testé |

**Le drainage.** Une cloison pleine bloque complètement le signal ; une porte le laisse passer
atténué (0.0008 contre 0.0012 à l'air libre). Le signal remonte la rue au lieu de traverser le mur.

**L'axe du stress**, mesuré sur le banc : sous le feu, le seuil passe de 0.175 à 0.134 et l'audace
monte à ×1.36. Quand le temps manque sans que le danger change, l'audace monte seule de ×1.00 à
×1.35 — c'est ce qui fait entrer. Après quatre minutes d'attrition (50 % de pertes, 15 % de
munitions), le cortisol atteint 0.51 et l'audace **retombe à ×0.82** : l'escouade épuisée cesse
d'attaquer. C'est un comportement, pas un bug.

**Le thymus.** Quatre candidats, deux épreuves :

| candidat | positive | négative | pire faute | verdict |
|---|---|---|---|---|
| aucun filtre IFF | OK | AUTO-IMM | ami tire près **100 %** | DÉTRUIT |
| atténuation 50 % | OK | AUTO-IMM | ami tire près **95 %** | DÉTRUIT |
| filtre IFF franc | OK | OK | — | **SURVIT** |
| sourd (seuil 0.95) | **SOURD** | OK | — | DÉTRUIT |

Trois choses à lire dans ce tableau.

Une politique sans filtre IFF **se plaque 100 % du temps** dès que son binôme ouvre le feu. Ce
n'est pas un cas tordu : c'est ce que produit `FiredNear` tel quel. Sans thymus, SIROCCO couche
l'escouade au premier coup de feu ami.

La **demi-mesure ne marche pas** : atténuer le signal ami de moitié laisse 95 % de fautes. Le
filtre doit être franc.

Et le **sourd passe la sélection négative** haut la main. C'est le piège : ne garder que
l'épreuve du soi sélectionne des agents qui ne réagissent à rien. Il faut les deux épreuves.

---

## 5. Le contre-poids, à relire avant chaque brique

Une seule métrique décide : **prise-à-pertes**. Pas la survie, pas l'exposition, pas le nombre de
réactions correctes.

Un système immunitaire tactique bien réglé qui ne prend pas l'objectif est un système raté. La
médecine connaît ce patient : il ne meurt pas de l'infection, il meurt de sa propre réponse.
