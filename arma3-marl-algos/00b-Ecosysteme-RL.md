# Écosystème du RL
### « D'où vient tout ça, et comment le domaine s'organise »

## Le problème qu'il résout (de quoi parle-t-on ?)

Avant de plonger dans les algorithmes, il faut une **carte**. Sans elle, ils semblent un fatras de
sigles. En réalité, ils descendent tous d'une même souche et répondent tous à une seule question :
*comment un agent apprend-il un bon comportement à partir d'une simple récompense ?*

## L'idée centrale : trois familles d'apprentissage

L'apprentissage automatique se divise en trois grandes familles. Comprendre où se situe le RL, c'est
comprendre sa nature profonde.

| Famille | Ce qu'on lui donne | Ce qu'elle apprend |
|---|---|---|
| **Supervisé** | des exemples *étiquetés* (« ceci est un char ») | à imiter les bonnes réponses |
| **Non supervisé** | des données *sans* étiquettes | à y trouver des structures cachées |
| **Renforcement (RL)** | *aucune* bonne réponse — seulement une **récompense** différée | à **agir** pour maximiser cette récompense |

> *Pour un littéraire :* le supervisé est un élève à qui l'on dicte les corrigés ; le RL est un
> enfant lâché dans le monde, qui n'apprend que des conséquences de ses actes. C'est plus lent, plus
> capricieux — mais c'est la seule façon d'apprendre à *agir* quand personne ne connaît d'avance la
> bonne conduite.

## Le mécanisme, pas à pas : la boucle fondamentale

Tout le RL tient dans une boucle, répétée des millions de fois :

<div class="formule">l'AGENT observe → choisit une ACTION → l'ENVIRONNEMENT change et renvoie une RÉCOMPENSE → l'agent ajuste sa politique → on recommence</div>

1. L'agent perçoit l'état (ou une fraction de l'état).
2. Sa **politique** (sa façon de décider) choisit une action.
3. L'environnement répond : nouvel état + récompense.
4. L'agent met à jour sa politique pour que les actions « payantes » deviennent plus probables.

Tout le reste — PPO, QMIX, COMA… — n'est qu'une **manière différente de faire l'étape 4** (ajuster
la politique) ou d'**organiser la boucle** (contre qui, sur quoi).

## La généalogie : d'où viennent *tes* algorithmes

Le RL a deux âges. **L'âge théorique** (années 1950-1990) : Bellman et les *processus de décision
markoviens* (la formalisation « état → action → récompense »), la programmation dynamique, le
**Q-learning** (Watkins, 1989), et la « bible » du domaine, le livre de **Sutton & Barto**. Puis
**l'âge profond** (depuis 2013) : la rencontre du RL avec les **réseaux de neurones**, qui a tout
fait exploser, portée par une culture singulière — *les jeux comme bancs d'essai*.

| Algorithme / idée | Né chez | Vers |
|---|---|---|
| DQN (le déclic « deep RL », Atari) | DeepMind | 2013-15 |
| PPO, MADDPG | OpenAI (+ Berkeley) | 2017 |
| VDN, PSRO, PBT, AlphaStar/ligue | **DeepMind** | 2017-19 |
| QMIX, COMA, banc d'essai SMAC | **Oxford** (labo WhiRL) | 2018 |
| MAPPO | Tsinghua / Berkeley | 2021 |
| HAPPO | UCL / Oxford | 2022 |
| PLR / curriculum automatique | UCL / Meta AI | 2020-21 |
| CMDP (contraintes) | théorie du contrôle (1999) → RL (Berkeley, 2017) | — |

> *À retenir :* une poignée de laboratoires (**DeepMind, OpenAI, Oxford**) a produit l'essentiel, en
> ~10 ans, autour des jeux (Atari → go → StarCraft → Dota). Ton projet n'est donc pas un bricolage :
> il s'inscrit dans une lignée **récente, concentrée et cohérente**.

## La carte du domaine (pour t'y retrouver)

- **Mono-agent vs multi-agents (MARL)** : un seul cerveau, ou plusieurs qui interagissent. Ton
  projet est multi-agents — la branche la plus difficile (les autres bougent aussi).
- **Sur-politique vs hors-politique** : apprendre des données qu'on vient de produire (PPO) ou
  ressasser de vieilles données stockées (Q-learning, QMIX). Le second est plus économe en données.
- **Par valeur vs par politique** : noter les situations (« valeur ») pour en déduire l'action, ou
  ajuster directement la façon de décider. La plupart des méthodes modernes mêlent les deux
  (*acteur-critique*).
- **Coopératif / compétitif / mixte** : ton cas est **mixte** — coopératif dans l'équipe, compétitif
  contre l'ennemi.

## Pourquoi cette carte t'est utile

Elle explique aussi tes **outils logiciels** : EPyMARL, RLlib, OmniSafe, PettingZoo sont nés de
cette même communauté pour implémenter exactement ces algorithmes. Théorie, code et bancs d'essai
viennent du même monde — ce qui veut dire que tout ce que tu apprends ici se branche directement sur
des bibliothèques existantes.

<div class="philo">En dernier regard. Le RL est, de toutes les approches de l'intelligence artificielle, la plus proche de la condition vivante. Le supervisé apprend dans une bibliothèque, entouré de corrigés ; le RL apprend dans l'arène, où nul ne lui dit la vérité, où seule compte la conséquence. C'est l'empirisme poussé à sa limite — l'idée, déjà chère à Hume puis aux pragmatistes, que nous ne connaissons le monde qu'en agissant sur lui et en éprouvant le retour de nos actes. Qu'une discipline d'ingénieurs ait redécouvert, en voulant faire jouer des machines, la vieille question de savoir comment l'expérience devient sagesse, n'est pas le moindre de ses charmes.</div>
