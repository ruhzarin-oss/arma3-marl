# Mise en place technique — entraîner les agents de combat Arma 3

Ce document liste, en clair, ce dont le projet a besoin pour s'entraîner : code, bibliothèques,
matériel, et l'ordre dans lequel construire. Il accompagne le corpus théorique
([arma3-marl-theorie-complete.md](arma3-marl-theorie-complete.md)) et sa traduction
([arma3-marl-en-clair.md](arma3-marl-en-clair.md)).

---

## L'idée directrice

Le projet est **deux chantiers très différents collés ensemble** :

1. **Le pont vers Arma 3** — faire dialoguer le jeu et le code Python. Partie difficile,
   sur-mesure, qu'aucune bibliothèque ne livre clé en main.
2. **Le moteur d'apprentissage** — les algorithmes (MAPPO, QMIX, lagrangien…). Ici, des
   bibliothèques mûres font l'essentiel du travail.

**Recommandation stratégique majeure** (découle du Module 7 : la lenteur d'Arma est le goulot) :
ne pas développer les algorithmes directement sur Arma. Construire d'abord un **simulateur-jouet
rapide**, y mettre au point toute la machinerie, et **ne brancher Arma qu'à la fin** pour valider
et affiner. Voir la dernière section.

---

## Couche 1 — Le côté simulateur (Arma 3) — *sur-mesure*

- **Serveur dédié Arma 3 (binaire Linux natif)**, lancé **sans affichage** (*headless*) : juste le
  moteur de simulation, pas le jeu avec sa fenêtre.
- **Mission d'entraînement en SQF** (langage de script d'Arma) : apparition des soldats, ennemi,
  objectif, et surtout **remise à zéro très rapide** entre épisodes (replacer les unités sans
  redémarrer le serveur). Le *reset* rapide est vital (dizaines de milliers d'épisodes).
- **Le pont (morceau délicat).** Arma appelle une bibliothèque externe en plein jeu via la
  commande SQF `callExtension`. On écrit une petite **extension native** (`.so` sous Linux) qui
  fait le passe-plat SQF ↔ Python. Briques réelles :
  - **`arma-rs`** (Rust) — la voie recommandée pour écrire l'extension proprement ;
  - ou **Intercept** (C++) — équivalent.
  - Dialogue extension ↔ Python : **ZeroMQ** ou sockets TCP simples.
- **Extraction de l'observation, en SQF** : à chaque pas, interroger le jeu (positions, ennemis
  repérés via `knowsAbout` / `nearTargets`, santé, munitions) et l'envoyer à Python.
- **Application des actions, en SQF** : traduire la décision de Python en ordres (`doMove`,
  `doTarget`, `commandFire`…). **Désactiver l'IA native** (`disableAI`) sur les unités pilotées
  par la politique, pour qu'elles n'aient qu'un seul cerveau.
- **Accélération du temps** (`setAccTime`) et **plusieurs serveurs en parallèle** pour multiplier
  le débit. Attention : chaque instance Arma est lourde (CPU/RAM) → une poignée, pas des centaines.

> C'est la couche que tu construis toi-même : gros de l'effort d'ingénierie et principale
> difficulté.

## Couche 2 — Le contrat d'interface (branchement standard)

Habiller Arma selon une norme reconnue :
- **PettingZoo** — norme d'interface pour environnements **multi-agents** (équivalent multi-joueurs
  de Gym/Gymnasium). On enveloppe le pont Arma dans une classe PettingZoo (`reset()`, `step()`) →
  compatible avec quantité d'outils.
- **Gymnasium** — équivalent **mono-agent** ; utile pour les premiers tests.

Couche fine mais stratégique : la prise standard sur laquelle se branchent tous les moteurs.

## Couche 3 — Le moteur d'apprentissage (bibliothèques mûres)

| Bibliothèque | À quoi elle sert | Pour le projet |
|---|---|---|
| **EPyMARL** | Implémente exactement nos algos : QMIX, VDN, MAPPO, COMA, MADDPG… | La meilleure pour coller à la théorie et prototyper. |
| **Ray RLlib** | Moteur RL industriel, multi-agents, **distribué** (parallélisme multi-cœurs/machines). | Pour passer à l'échelle, orchestrer les instances Arma. |
| **MARLlib** | Surcouche unifiée sur RLlib, nombreux algos + compatible PettingZoo. | Bon compromis richesse/robustesse. |
| **CleanRL** | Implémentations en un seul fichier, lisibles (dont MAPPO). | Pour **comprendre** le code, pas pour la production. |
| **Stable-Baselines3** | Algos mono-agent fiables (PPO…). | Pour valider le premier prototype à un agent. |

Conseil : **EPyMARL pour apprendre/prototyper**, **RLlib/MARLlib pour industrialiser** le
parallélisme Arma.

## Couche 4 — La sécurité / la contrainte (le CMDP)

Pour « maximiser la mission sous contrainte de pertes » :
- **OmniSafe** — bibliothèque de référence du RL « sûr » : méthodes lagrangiennes (le curseur λ
  qui s'auto-règle) et apparentées.
- **MAPPO-Lagrangian / MACPO** — versions **multi-agents sous contrainte** (codebases de Gu et
  al.). Implémentation directe du Module 1.

## Couche 5 — Le socle et l'outillage

- **PyTorch** — socle de calcul des réseaux ; base d'EPyMARL, RLlib, OmniSafe. *(JAX + JaxMARL est
  plus rapide, mais seulement pour des environnements écrits en JAX — pas un simulateur externe
  comme Arma. Donc PyTorch ici.)*
- **Hydra** — gestion des fichiers de configuration des expériences.
- **Weights & Biases** ou **TensorBoard** — courbes d'apprentissage, comparaison d'essais.
- **Docker** — figer l'environnement (serveur Arma + dépendances Python), reproductibilité.

## Le matériel

Contre-intuitif : **le frein n'est pas le GPU, c'est le CPU.** Les réseaux du MARL sont petits
(GPU milieu de gamme suffit). Faire tourner plusieurs instances Arma en parallèle est gourmand en
**cœurs CPU et RAM**. Donc : beaucoup de cœurs, RAM généreuse, GPU correct. Point à vérifier sur
la machine dédiée : **combien d'instances Arma elle fait tourner de front.**

---

## Le conseil décisif : un simulateur-jouet d'abord

Le MARL réclame des **millions** de pas ; Arma en produit lentement. Développer directement sur
Arma = chaque bug coûte des heures. Méthode qui marche :

1. **Écrire un simulateur grossier et ultra-rapide** : carte 2D, points, ennemis simplifiés, même
   structure (4 agents, 1 chef, objectif, pertes). En PettingZoo, des milliers de fois plus rapide
   qu'Arma.
2. **Mettre au point toute la machinerie dessus** : MAPPO, conditionnement par rôle, curseur λ,
   hiérarchie du chef. Débogage rapide et bon marché.
3. **Une fois la machinerie au point, brancher Arma** (couches 1-2) pour l'**ajustement final**.
   Arma = terrain de validation et de réalisme, pas de débogage.

---

## L'ordre de construction (par étapes)

- **Étape 0 — Le pont nu.** Un script SQF envoie « bonjour » à Python et reçoit une réponse. Valide
  la plomberie.
- **Étape 1 — Un seul agent.** Un soldat, objectif simple (« atteindre ce point »), entraîné avec
  PPO (Stable-Baselines3). Valide la boucle observation → décision → action → récompense.
- **Étape 2 — Simulateur-jouet multi-agents.** Les 4 agents en PettingZoo sur la carte 2D rapide.
  MAPPO + partage de paramètres conditionné par rôle (EPyMARL). La coordination apparaît ici.
- **Étape 3 — La contrainte de survie.** Ajouter le curseur λ (OmniSafe / MAPPO-Lagrangian).
- **Étape 4 — Le chef et les manœuvres.** Hiérarchie (chef qui assigne des sous-objectifs) +
  macro-actions implémentées en Behavior Tree doctrinal.
- **Étape 5 — Bascule vers Arma.** Brancher sur le vrai jeu et affiner.

---

## Récapitulatif des dépendances (pile recommandée)

- **Jeu** : serveur dédié Arma 3 (Linux, headless) + mission SQF + Eden Editor.
- **Pont** : `arma-rs` (Rust) ou Intercept (C++) + ZeroMQ.
- **Interface** : PettingZoo (multi-agents), Gymnasium (mono-agent).
- **Apprentissage** : EPyMARL (prototype) puis RLlib/MARLlib (échelle) ; CleanRL pour comprendre.
- **Contrainte** : OmniSafe, MAPPO-Lagrangian / MACPO.
- **Socle** : PyTorch.
- **Outillage** : Hydra, Weights & Biases / TensorBoard, Docker.
- **Matériel** : CPU multi-cœurs + RAM généreuse (frein réel) + GPU milieu de gamme.
