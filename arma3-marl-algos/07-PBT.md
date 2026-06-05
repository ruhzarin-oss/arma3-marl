# PBT — Entraînement par population
### « Une évolution darwinienne des entraînements »

## Le problème qu'il résout

Tout entraînement RL dépend d'une foule de **réglages** (vitesse d'apprentissage, dose
d'exploration, poids divers…) dont on ne connaît pas d'avance les bonnes valeurs. La méthode
habituelle — essayer une combinaison, attendre des heures, recommencer — est lente et coûteuse. Pire :
les bons réglages **changent au cours** de l'entraînement (au début il faut explorer, plus tard il
faut affiner). Un réglage fixe est donc forcément sous-optimal à un moment ou un autre.

## L'idée centrale

**Entraîner toute une population en parallèle, et laisser les bonnes recettes se répandre et muter,
en continu.** Plutôt que de chercher *les* bons réglages d'avance, on les fait **évoluer** pendant
l'entraînement : sélection des meilleurs, copie, petites mutations. La nature trouve à notre place.

## Le mécanisme, pas à pas

1. On lance **N entraînements en parallèle**, chacun avec des réglages un peu différents.
2. À intervalles réguliers, on **évalue** chaque membre (sa performance du moment).
3. **Exploiter** : un membre nettement moins bon **abandonne** son état et **copie** celui d'un
   membre nettement meilleur (poids du réseau *et* réglages).
4. **Explorer** : juste après avoir copié, il **perturbe** légèrement les réglages (au hasard, un
   peu) — autant de tentatives d'aller plus loin que le « parent ».
5. On laisse tourner. La qualité moyenne monte, et les réglages **s'adaptent dans le temps** sans
   qu'on touche à rien.

## Les formules, traduites

**① Exploiter (sélection).**

<div class="formule">si un membre est nettement moins bon → il adopte l'état et les réglages du meilleur</div>

> *Pour un littéraire :* les recettes perdantes sont abandonnées ; les gagnantes se reproduisent.

**② Explorer (mutation).**

<div class="formule">après avoir copié → on perturbe un peu les réglages (légèrement, au hasard)</div>

> *Pourquoi les deux ensemble :* copier seul fige la population sur un unique gagnant (on s'appauvrit) ;
> muter seul disperse sans capitaliser. **Sélection + variation** : c'est la formule même de
> l'évolution. La diversité de la population est une assurance contre l'impasse.

## Un exemple concret

Cinq entraînements de ton équipe tournent de front. Au bout d'une heure, trois stagnent, deux
progressent vite (ils avaient, par chance, une meilleure dose d'exploration). Les trois retardataires
**copient** l'un des deux bons, puis **perturbent** légèrement leurs réglages — l'un essaie un peu
plus d'exploration, l'autre un peu moins. Une heure plus tard, c'est l'une de ces *mutations* qui
mène, et les autres la copient à leur tour. Sans intervention, la population a trouvé un réglage que
tu n'aurais pas deviné — et qui, en plus, **a changé** au bon moment.

## Variantes & pièges

- Se combine avec presque tout : PBT **par-dessus** MAPPO, ou **par-dessus** l'auto-jeu (c'est
  exactement ce que faisait AlphaStar : PBT + ligue).
- *Pièges :* il faut **plusieurs entraînements de front** (gourmand — mais ta machine s'y prête) ;
  une mauvaise mesure de « qui est le meilleur » fausse toute la sélection ; et la population peut
  **converger trop vite** vers un seul type si l'on n'entretient pas assez de diversité.

## Pourquoi on l'utilise ici

PBT **règle les réglages tout seul** (gros gain de temps et de performance) et **diversifie les
stratégies** (assurance contre l'impasse). Il exploite à merveille ta workstation, capable de faire
tourner plusieurs entraînements simultanés. On l'ajoute *en dernier*, comme enveloppe, une fois la
base solide.

<div class="philo">En dernier regard. PBT incarne une épistémologie sans architecte : le progrès n'y vient pas d'un plan génial, mais de la variation aveugle suivie d'une sélection impitoyable. C'est l'idée de Darwin, que Popper transposa à la connaissance — nos théories, disait-il, « meurent à notre place » : on les laisse échouer pour ne pas échouer soi-même. Leçon d'humilité : on n'a pas besoin de savoir d'avance ce qui est juste, pourvu qu'on entretienne assez de diversité et qu'on accepte d'éliminer ce qui échoue. La sagesse n'est pas toujours dans le concepteur ; parfois, elle est répartie dans la population — et dans le temps qu'on lui laisse.</div>
