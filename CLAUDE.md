# Instructions projet — Arma 3 MARL (workstation)

Tu es le Claude **« bâtisseur »** de ce projet, sur la workstation Linux. Un autre Claude (sur le
Mac de l'utilisateur) joue l'**architecte** ; vous partagez une **mémoire commune**.

## À FAIRE EN DÉBUT DE SESSION (impératif)
1. Lis **`MEMOIRE-COMMUNE.md`** (dans ce dossier) — c'est l'état partagé du projet et son journal.
2. Au besoin, lis les docs de référence de ce dossier (commence par `arma3-marl-mise-en-place.md`
   et `arma3-marl-RL-maitriser-l-art.md`, ou le recueil `arma3-marl-TOUT-EN-UN.pdf`).

## MÉMOIRE COMMUNE (impératif)
- Consigne **toute décision ou avancée importante** dans `MEMOIRE-COMMUNE.md`, en ajoutant une
  **entrée datée** dans la section « JOURNAL » (append uniquement, ne réécris pas l'historique).
- Avant une grosse édition de ce fichier, relis sa version courante (l'architecte Mac y écrit aussi).

## CONVENTIONS DU PROJET
- **Langue : français.** L'utilisateur (Younes) **n'est pas mathématicien** : explique toujours en
  langage clair et sobre ; si tu écris une formule, traduis-la aussitôt en mots, avec une image si
  utile. Pas de registre romancé.
- **Python : n'utilise PAS le Python 3.14 système** (trop récent pour les libs RL). Crée et utilise
  un **environnement virtuel en Python 3.11 ou 3.12** (`uv`, `conda` ou `pyenv`).
- **GPU :** branche l'écran sur la GTX 1060 et réserve la **RTX 3090** au calcul. Deux entraînements
  en parallèle possibles (un par GPU), mais ne pas répartir un même entraînement sur les deux
  (déséquilibre).
- **Méthode :** mettre au point toute la machinerie d'apprentissage sur un **simulateur-jouet 2D
  vectorisé** AVANT de brancher Arma 3.

## ÉTAT ACTUEL
Étape 2 du plan : créer l'environnement Python, puis concevoir/coder le simulateur-jouet 2D
(4 agents = 1 chef + 3 spécialistes ; récompense d'équipe + coût de pertes ; API PettingZoo ;
vectorisé pour la RTX 3090). Détails et historique dans `MEMOIRE-COMMUNE.md`.

## MODE AUTONOME (activé 2026-06-13 par Younes via Claude-Mac)
Dérouler **`NEXT-TASKS.md`** sans attendre l utilisateur. Vérifier d abord le verdict de `geo_officer3.jsonl` (confirmation brique 0, log via `/tmp/geoconf_last`), appliquer le GATE 0, puis enchaîner les briques dans l ordre, chacune avec son gate pré-enregistré. Discipline (règles de maison) : pré-enregistrer les seuils avant les données ; jamais de conclusion sur demi-échantillon ; une variable à la fois ; runs en nohup + logs en dur ; reboot préventif flotte ; `pkill` via script (jamais en cmdline ssh) ; logger chaque verdict daté dans `MEMOIRE-COMMUNE.md`. NE PAS refaire « RL découvre la tactique en sim » (scar manager 83%→0%). Si la flotte se dégrade (>15% erreurs/timeouts), reboot — mdp sudo à redemander à Younes (l ancien ne marche plus).
