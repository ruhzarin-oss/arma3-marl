# QMIX & décomposition de valeur
### « Que l'intérêt de chacun serve le bien de tous »

## Le problème qu'il résout

À l'exécution, chaque soldat décide **seul**, avec ses seuls yeux (pas de vue d'ensemble, pas de
temps pour délibérer). Mais la récompense est **collective**. Comment garantir que « chacun fait au
mieux pour soi, localement » revienne à « l'équipe fait au mieux, globalement » ? Si l'on apprend
une note d'équipe géante (dépendant des actions de tous), elle est impossible à utiliser sur le
terrain (chacun devrait connaître les actions des autres). Si chacun apprend dans son coin
(*Independent Q-Learning*), la coordination s'effondre. Il faut un pont entre les deux.

## L'idée centrale

**Construire la note d'équipe à partir des notes individuelles, selon une règle qui force la
coïncidence des optima.** Chaque agent a sa propre note ; une « note d'équipe » les combine ; et la
combinaison est choisie de telle sorte que maximiser sa note individuelle revienne toujours à
servir la note d'équipe. On apprend ensemble (avec la note d'équipe), on exécute séparément (chacun
sa note).

## Le mécanisme, pas à pas

1. Chaque agent a un réseau qui lui donne une **note** (valeur) pour chacune de ses actions
   possibles, à partir de sa seule observation.
2. Un **réseau mélangeur** combine ces notes individuelles en une **note d'équipe**, en s'aidant de
   l'état global (disponible à l'entraînement).
3. On entraîne le tout pour que la note d'équipe prédise bien la récompense future réelle
   (apprentissage par valeur, type Q-learning, avec mémoire de rejeu).
4. **Contrainte clé** : le mélangeur est forcé d'être *monotone* (voir ④) — c'est ce qui garantit la
   coïncidence des optima.
5. À l'exécution, on jette le mélangeur : chaque agent choisit l'action de **sa** meilleure note.

## Les formules, traduites

**① La règle de coïncidence (principe IGM).**

<div class="formule">meilleur choix de l'ÉQUIPE = (meilleur choix du soldat 1, …, meilleur choix du soldat n)</div>

> *Pour un littéraire :* on veut que la somme des décisions « les meilleures pour soi » forme
> *exactement* la meilleure décision collective. Que l'égoïsme local et le bien commun pointent dans
> la même direction. Sans cette propriété, la décentralisation trahit l'équipe.

**② La fabrication de la note d'équipe.**

<div class="formule">note d'équipe = mélange( note du soldat 1, …, note du soldat n ; état global )</div>

**③ La règle de montée (monotonie).**

<div class="formule">si la note d'UN SEUL membre monte, la note d'équipe ne peut que monter ou rester égale</div>

> *Pourquoi cette règle garantit le ①* : si améliorer un membre ne peut **jamais** nuire à l'équipe,
> alors chacun peut chercher son propre maximum sans risque pour le collectif. La monotonie *est* le
> pont entre l'individuel et le commun.

**④ La hiérarchie d'expressivité.** VDN additionne simplement les notes (rudimentaire). QMIX les
mélange de façon monotone mais **non linéaire**, en tenant compte de l'état (bien plus riche). QPLEX
va plus loin encore (voir le piège).

## Un exemple concret

Le mitrailleur « note » très haut l'action *suppression* quand l'ennemi est groupé ; le voltigeur
note haut *avancer* quand il est couvert. Le mélangeur apprend que, **ensemble**, ces deux notes
hautes valent une excellente note d'équipe (suppression + progression = manœuvre réussie). Chacun,
en suivant sa propre note, déclenche la bonne combinaison — sans s'être concerté.

## Variantes & pièges

- **La limite à connaître (capital).** Certaines manœuvres sont en **tout-ou-rien** : déborder à
  deux est excellent ; *un seul* qui s'élance sans couverture est *pire que rien*. Là, améliorer un
  seul membre **dégrade** l'ensemble — ce que la règle de montée **interdit de représenter**. QMIX
  est alors aveugle à ces tactiques.
- **VDN** (somme), **QTRAN** et **QPLEX** (qui lèvent la limite de monotonie, au prix d'un
  entraînement plus délicat), **Weighted QMIX** (corrige un biais).
- *Piège :* croire que QMIX peut tout représenter. Pour de la coordination « tout-ou-rien », il faut
  monter en gamme (QPLEX) ou passer à l'acteur-critique (MAPPO/HAPPO).

## Pourquoi on l'utilise ici

C'est la base de l'apprentissage **par valeur** en équipe : très économe en données (il ressasse
une mémoire de rejeu). On le garde en réserve pour des actions discrètes, en sachant sa limite — et
on lui préfère HAPPO quand la coordination devient « tout-ou-rien ».

<div class="philo">En dernier regard. QMIX pose, sans le dire, la plus vieille question de la métaphysique : le tout est-il la somme de ses parties ? Sa règle de montée est un pari d'harmonie — l'idée, déjà chère à Leibniz, que le bien de chacun puisse composer le bien de tous. Et sa limite est tout aussi profonde : il existe des touts qui sont *plus* que la somme — la manœuvre coordonnée, l'accord choral, l'élan collectif — où le sens naît de la relation, non de l'addition. L'algorithme trace ainsi, à sa manière, la frontière exacte entre ce que le réductionnisme sait reconstruire et ce qui lui demeure, irréductiblement, étranger.</div>
