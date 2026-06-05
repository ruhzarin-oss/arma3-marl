# PPO / MAPPO
### « Progresser à petits pas garantis »

## Le problème qu'il résout

Pour améliorer une politique, l'idée naturelle est : « pousse un peu plus fort vers les gestes qui
ont rapporté ». C'est le *gradient de politique*. Mais brut, il a deux défauts mortels. D'abord, il
est **très bruité** : on estime « ce qui rapporte » à partir de quelques parties au hasard, donc
l'estimation tremble. Ensuite, et surtout, **un seul pas trop grand détruit tout** : la politique
bascule dans une région catastrophique, n'y récolte plus que de mauvaises données, et ne s'en
relève jamais. En RL, on ne peut pas « annuler » un mauvais pas — les données suivantes sont déjà
produites par la politique abîmée.

## L'idée centrale

**Améliorer la politique, mais en s'interdisant de trop s'éloigner de la précédente à chaque pas.**
C'est l'idée de *région de confiance* : on ne fait confiance à notre estimation que dans un petit
voisinage. PPO impose cette retenue d'une manière simple et robuste — en *coupant* la récompense
dès qu'on change trop.

## Le mécanisme, pas à pas

1. On joue un paquet de parties avec la politique **actuelle** (on récolte états, actions,
   récompenses).
2. On estime, pour chaque geste, son **avantage** : a-t-il fait mieux ou moins bien que prévu ?
3. On fait plusieurs petites passes d'ajustement qui augmentent la probabilité des gestes à bon
   avantage — **mais bridées** par le mécanisme de coupure.
4. En parallèle, on entraîne un « critique » (la fonction *valeur*) qui apprend à pronostiquer, pour
   réduire le bruit des estimations.
5. On jette ces données (elles ne valent que pour l'ancienne politique) et on recommence.

## Les formules, traduites

**① La surprise, brique de base.**

<div class="formule">δ = (récompense reçue) + γ · V(situation suivante) − V(situation actuelle)</div>

*V* est le **pronostic** d'une situation ; *δ* est l'**écart** entre ce qui arrive et ce qu'on
attendait. *γ* (entre 0 et 1) dit qu'un bien lointain compte un peu moins qu'un bien immédiat.

> *Pour un littéraire :* le commentateur qui révise son jugement sur un coup une fois la suite connue.

**② L'avantage** — somme des surprises (technique nommée *GAE*) :

<div class="formule">avantage = δ maintenant + (un peu moins) δ ensuite + (encore moins) δ après…</div>

> *En clair :* le bilan, bon ou mauvais, qu'un geste a réellement déclenché dans la durée.

**③ Le ratio de changement.**

<div class="formule">ratio = (envie de la NOUVELLE politique pour ce geste) ÷ (envie de l'ANCIENNE)</div>

> *Pourquoi ce terme ?* Il mesure *de combien* on s'écarte de la politique qui a produit les
> données. C'est lui qu'on va brider.

**④ Le cœur de PPO — l'objectif coupé.**

<div class="formule">on récompense : ratio × avantage … MAIS si le ratio sort de [1−ε, 1+ε], on le COUPE (plus de récompense au-delà)</div>

Si l'avantage est positif, on veut monter le ratio — mais au-delà de *1+ε* (ex. +20 %), la coupure
annule le gain : inutile d'aller plus loin. Symétriquement pour un avantage négatif.

> *Pour un littéraire :* un **limiteur de vitesse sur l'enthousiasme**. *ε* est la longueur de la
> laisse. Foncer sur une impression fragile, c'est se planter ; PPO l'interdit par construction.

**⑤ Le sucre en plus.** On ajoute souvent un petit **bonus d'entropie** : une prime à rester un peu
imprévisible, pour ne pas se figer trop tôt sur une seule tactique (encourager l'exploration).

## Un exemple concret

Ton groupe tente un **débordement par la droite**. Sur dix répétitions, il réussit deux fois mieux
que la moyenne : avantage positif. PPO augmente la propension à déborder — mais d'un cran seulement.
Pourquoi pas à fond ? Parce que ces dix parties sont peu nombreuses : peut-être un coup de chance.
La laisse *ε* empêche l'équipe de devenir obsédée par le débordement sur une preuve trop maigre.

## Variantes & pièges

- **TRPO** : l'ancêtre, qui impose la même retenue par une contrainte mathématique dure (puissant
  mais lourd). PPO l'approxime par la coupure — plus simple, presque aussi bon.
- **IPPO** : chaque agent fait son PPO dans son coin (étonnamment solide en pratique).
- **MAPPO / HAPPO** : les versions équipe (ci-dessous).
- *Pièges :* mal régler *ε* (trop grand = instable, trop petit = apprentissage lent) ; oublier de
  normaliser les récompenses ; mal concevoir ce que voit le critique central.

## Ce que MAPPO ajoute (la version équipe)

- **Un critique qui voit tout** pendant l'entraînement (l'état global du champ de bataille), alors
  que chaque soldat **agit avec ses seuls yeux**. C'est le principe CTDE : apprendre avec une vue
  d'ensemble, exécuter en aveugle partiel.
- **Un cerveau partagé, décliné par rôle** : les agents mutualisent leur expérience.

## Pourquoi on l'utilise ici

La prudence intégrée (la laisse *ε*) **dompte l'instabilité du multi-agents** : quand les
coéquipiers changent sans cesse, les petits pas bornés évitent l'effondrement. C'est, en pratique,
la base la plus robuste et la plus simple à faire tenir debout — le bon point de départ.

<div class="philo">En dernier regard. PPO est une philosophie de la mesure faite algorithme. Il refuse les deux tentations symétriques de l'esprit : l'immobilisme qui n'apprend de rien, et l'enthousiasme qui réforme tout sur une intuition fragile. Aristote nommait vertu ce juste milieu, et prudence (phronèsis) l'art d'avancer sans se renier. PPO formalise une sagesse très ancienne : on ne progresse pas en se reniant à chaque épreuve, mais en corrigeant le cap d'un degré à la fois — assez pour avancer, assez peu pour rester soi-même et pouvoir se corriger encore demain.</div>
