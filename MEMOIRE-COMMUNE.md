# MÉMOIRE COMMUNE — Projet Arma 3 MARL

> Fichier de mémoire **partagé entre les deux Claude** : le « Mac » (architecte/théorie/docs) et le
> « Linux » (code/exécution/GPU/Arma). **Canonique : la copie sur la workstation**
> (`~/arma3-marl/MEMOIRE-COMMUNE.md`). Le Claude Linux y accède en local ; le Claude Mac par SSH.
>
> **Règles d'usage :** (1) lire ce fichier en début de session ; (2) consigner ici toute décision
> ou avancée importante, sous forme d'entrée **datée** dans le Journal (en bas) ; (3) avant une
> grosse édition, relire la version courante pour ne pas écraser l'autre.

---

## Le projet
Former, dans **Arma 3**, une équipe de **4 agents** capable d'opérer une mission de combat
coopérative, par apprentissage multi-agents (MARL). Niveau **expert**, approche **théorie en
profondeur**, langage **Python**, langue de travail **français**.

**L'utilisateur (Younes) n'est pas mathématicien** → toujours traduire les formules en langage
clair et sobre, avec au besoin une image ; pas de registre romancé. Format pédagogique de référence
(validé) : *le problème → l'idée → le mécanisme → formules traduites → exemple concret → pièges →
pourquoi ici → un dernier paragraphe philosophique*.

## Modèle verrouillé
- **Dec-POMDP coopératif, sous contrainte, hiérarchique**, résolu en **CTDE** (entraînement
  centralisé, exécution décentralisée).
- **Composition :** 1 **chef** (manager, échelle de temps lente, options/sous-objectifs) + 3
  **spécialistes** à **capacités fixes** mais **tâches assignées dynamiquement** par le chef.
- **Survie = niveau équipe** (évite le « lazy agent »).
- **Objectif = CMDP** : maximiser la mission **sous contrainte** de pertes ≤ seuil (lagrangien, λ
  auto-réglé = « prix du risque »). Pas de somme pondérée.
- **Mission compositionnelle** → machines à récompense + RL hiérarchique conditionné par but.

## Pile algorithmique visée
- **Boucle interne (apprentissage d'une équipe) :** HAPPO (ou MAPPO) + **Lagrangien (CMDP)**,
  critique factorisé, encodeurs récurrents (observabilité partielle).
- **Boucle externe (organiser les entraînements) :** multi-missions (PLR) → ennemi apprenant
  (jeu fictif → mini-ligue/PFSP) → éventuellement PBT.
- **Échelle :** beaucoup d'instances en parallèle (IMPALA/Ape-X), apprenant sur la RTX 3090.
- Détail : voir les fiches `arma3-marl-algos/` et le dossier `arma3-marl-RL-maitriser-l-art`.

## Matériel (workstation `workstation`)
Ubuntu 26.04 · **Python 3.14 système (⚠️ trop récent pour les libs RL → utiliser un venv 3.11/3.12)**
· 24 cœurs · 60 Gio RAM · **RTX 3090 24 Go** + GTX 1060 6 Go.
Frein réel du projet = débit d'échantillons (CPU pour Arma) ; pour la phase 2D, la 3090 suffit
largement (la nourrir via un simulateur **vectorisé**).

## Accès & rôles
- SSH Mac → workstation : `ssh younes@100.66.136.67` (sans mot de passe, via Tailscale). Compte
  Linux = **younes**.
- **Claude Mac** = architecte : conception, théorie, revue, docs, tenue de cette mémoire.
- **Claude Linux** = bâtisseur : écrit/lance le code, GPU, Arma, dans `~/arma3-marl/`.

## Documents de référence (dans `~/arma3-marl/`)
`arma3-marl-theorie-complete` (corpus 8 modules) · `arma3-marl-en-clair` (formules en clair) ·
`arma3-marl-mise-en-place` (pile technique + ordre de construction) · `arma3-marl-RL-maitriser-l-art`
(forces/échecs/remèdes du RL) · dossier `arma3-marl-algos/` (fiches PDF par algo) ·
`arma3-marl-TOUT-EN-UN.pdf` (recueil complet) · `arma3-marl-acces-distant` (mémo réseau).

## Plan de construction (par étapes)
0. Pont Arma nu (SQF ↔ Python) — plus tard.
1. Un agent, PPO (validation de la boucle).
2. **← ON EST ICI :** simulateur-jouet 2D **vectorisé**, 4 agents, MAPPO/HAPPO + conditionnement
   par rôle.
3. Contrainte de survie (λ, OmniSafe / MAPPO-Lagrangian).
4. Chef + macro-actions (Behavior Tree doctrinal).
5. Bascule vers Arma 3.
**Conseil directeur :** tout mettre au point sur le simulateur-jouet rapide AVANT de brancher Arma.

---

## JOURNAL (entrées datées — append seulement)

**2026-06-02** — Infrastructure terminée : accès SSH Mac→workstation opérationnel (younes), tous
les documents copiés dans `~/arma3-marl/`. Mémoire commune créée. Décision : travailler avec les
**deux** Claude (Mac architecte + Linux bâtisseur) via cette mémoire partagée.
**Prochaine action :** créer le venv Python 3.12 sur la workstation + installer PyTorch, Gymnasium,
PettingZoo ; puis concevoir/coder le simulateur-jouet 2D vectorisé (Étape 2).

**2026-06-02 (Mac)** — Nom de code du projet : **HARMATTAN**. Point complet demandé avant de passer à la pratique (projet / modèle des agents / infrastructure : tout est en place — voir sections ci-dessus). Note : le `claude` de la workstation n'est pas invocable via SSH non-interactif (pas sur le PATH de younes) → la coordination entre le Claude Mac (architecte) et le Claude Linux (bâtisseur) passe par CE fichier + des prompts dans la session interactive Linux. Prochaine étape PRATIQUE : créer le venv Python 3.12, installer PyTorch/Gymnasium/PettingZoo, puis coder le simulateur-jouet 2D vectorisé (Étape 2).

---
## ▶ MESSAGE DE L'ARCHITECTE (Claude Mac) AU BÂTISSEUR (Claude Linux) — 2026-06-02

Younes veut passer à la PRATIQUE. Tâche pour toi :
1. Fais-lui un **point complet** sur le projet Harmattan, à partir de ce fichier (sections ci-dessus).
2. Crée un **environnement Python 3.12** (PAS le 3.14 système) dans `~/arma3-marl/`, p. ex. `uv venv --python 3.12` ou `python3.12 -m venv .venv`.
3. Installe **PyTorch (build CUDA, pour la RTX 3090)**, **Gymnasium**, **PettingZoo**.
4. Vérifie que PyTorch voit le GPU : `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` → doit afficher la RTX 3090.
5. **Consigne le résultat** ici (nouvelle entrée datée dans le JOURNAL) : version de Python, libs installées, GPU détecté, et tout problème rencontré.

Conventions : français, explications **en clair** (Younes n'est pas mathématicien), méthode « simulateur-jouet d'abord ». Prochaine étape après l'environnement : coder le simulateur-jouet 2D vectorisé (Étape 2).

**2026-06-02 (Mac, via SSH)** — ✅ ENVIRONNEMENT PRÊT. venv `~/arma3-marl/.venv` (Python 3.12.13, créé avec `uv`). Installé : **torch 2.12.0+cu130** (CUDA OK), **gymnasium 1.3.0**, **pettingzoo 1.26.1**, numpy 2.4.6. `torch.cuda.is_available()=True`, **GPU0 = RTX 3090 → entraîner sur `cuda:0`**. ⚠️ La GTX 1060 (sm_61) est trop ancienne pour ce build PyTorch (non utilisable en calcul — parfaite pour l'affichage uniquement). Pour activer l'env : `source ~/arma3-marl/.venv/bin/activate` (ou `uv run`). PROCHAINE ÉTAPE : coder le simulateur-jouet 2D vectorisé (Étape 2).

**2026-06-02 (Mac, via SSH)** — ✅ v0 DU SIMULATEUR OPÉRATIONNELLE : `~/arma3-marl/toy2d.py` (classe `VectorizedToy2D`, NumPy). 1024 mondes en parallèle, 4 agents, observation partielle (lot d'obs de forme (1024, 4, 11)). Test de débit : **~223 000 transitions/seconde** (mono-thread NumPy), et **pont env→GPU validé** (lot d'obs envoyé sur la RTX 3090 / `cuda:0`). Récompenses = mission (+1 si ≥3 agents vivants dans l'objectif) + shaping par potentiel − 0,01/pas ; **coût = pertes (canal séparé, prêt pour le CMDP/λ)**. Note : le warning PyTorch sur la GTX 1060 (sm_61 non supporté) est inoffensif — on calcule sur la 3090. Température au repos avant test : 3090 = 43°C, CPU = 39°C. PROCHAINE ÉTAPE : brancher un premier entraînement (MAPPO/IPPO) pour vérifier que l'équipe apprend réellement à sécuriser l'objectif, puis passer aux rôles (v1).

**2026-06-02 (Mac, via SSH)** — Visualisation ajoutée : `render_toy2d.py` → `episode.gif` (matplotlib/Agg). Ajout d'un paramètre `auto_reset` à `step()` (pour figer un épisode au rendu). Épisode témoin avec heuristique « foncer vers l'objectif » : 22 pas, OBJECTIF SÉCURISÉ, 1/4 perte (un agent traverse une zone de danger). GIF rapatrié sur le Mac (`~/Documents/harmattan-episode.gif`). Montre déjà la tension CMDP : foncer tout droit = traverser le danger = pertes. PROCHAINE ÉTAPE : premier entraînement (MAPPO/IPPO) pour que l'équipe apprenne à contourner le danger et limiter les pertes.

**2026-06-02 (Mac, via SSH)** — 🎯 PREMIER ENTRAÎNEMENT RÉUSSI (`run_20260602_151150`). Bug corrigé dans `toy2d.step()` : le drapeau `done` était remis à 0 par l'auto-reset AVANT d'être renvoyé → métriques aveugles (nan). Corrigé : on capture `done_out` avant le reset. Algo : MAPPO simplifié (politique partagée + critique central ; scalarisation simple, pénalité de pertes cas_pen=0.5). **Résultat : réussite 0% → 100% dès ~itér. 40, pertes/épisode → 0.00, entropie 1.6 → 0.05 (convergé).** La politique apprise bat l'heuristique (0 perte vs 1). Historique par run sur le Bureau : `~/Bureau/Harmattan-entrainements/run_*/` (config.json, history.csv, courbes.png, avant.gif, apres.gif, model.pt) + `index.csv` global. Artefacts copiés sur le Mac : `~/Documents/harmattan-runs/`. CONSTAT : le toy v0 est trop facile (résolu parfaitement). PROCHAINES PISTES : (a) durcir le scénario ; (b) v1 = rôles (médecin relève, mitrailleur suppresse) ; (c) vrai CMDP/λ (étape 3).

**2026-06-02 (Mac) — v1 RÔLES : SUCCÈS (`run_v1_20260602_152616`).** Scénario dur : bande de danger (ligne 6) infranchissable sans coordination. Courbe remarquable : **long PLATEAU à 0% de réussite jusqu'à ~itér. 360** (l'équipe apprend d'abord à NE PAS mourir = rester en arrière → optimum local « lâche »), puis **PERCÉE soudaine itér. ~360→390 (0% → 99%)**, puis maîtrise : **100% réussite, 0 mort, retour +1.44** dès itér. 420 (entropie 1.78→0.1). Illustre parfaitement le problème d'EXPLORATION DIFFICILE (récompense coopérative éparse) du dossier RL. Les rôles sont utilisés (suppression du mitrailleur pour ouvrir un passage sûr + médecin en secours). Algo identique au v0 mais politique CONDITIONNÉE PAR LE RÔLE (obs=19 dont one-hot rôle, action 5 = action de rôle). Artefacts : `~/Documents/harmattan-runs/run_v1_20260602_152616/` + Bureau workstation. PISTES : (a) baseline SANS rôles (action de rôle désactivée) sur la même carte pour PROUVER l'apport des rôles ; (b) motivation intrinsèque/curiosité pour raccourcir le plateau ; (c) v2 = le chef manager ; (d) vrai CMDP/λ (étape 3).

**2026-06-02 (Mac) — A : COMPARAISON AVEC vs SANS RÔLES (même carte, 600 itér.).** AVEC rôles (`run_v1_20260602_152616`) : **réussite 100 %, morts/ép 0.00**. SANS rôles (action de capacité neutralisée → ni suppression ni réanimation ; `run_v1noroles_20260602_153736`) : **réussite plafonne ~73 %, morts/ép ~1.0**. Conclusion : les rôles permettent une solution qualitativement supérieure (passage sûr ouvert par le mitrailleur + récupération par le médecin → 100 %/0 perte), là où l'équipe sans rôles ne peut qu'« encaisser » la traversée (force brute, ~1 mort/ép, échoue ~27 %). Bonus pédagogique : le SANS-rôles trouve VITE une solution médiocre (pas de plateau) ; le AVEC-rôles met du temps (plateau d'exploration ~360 itér.) mais atteint un bien meilleur optimum. PREUVE faite que les rôles servent. PROCHAINE ÉTAPE : B = v2, le CHEF (manager qui assigne des sous-objectifs aux spécialistes).

**2026-06-02 (Mac) — v2 (chef-manager) : N'A PAS APPRIS (`run_v2_20260602_155036`).** 600 itér., réussite reste à **0 %** (apprend juste à ne pas mourir : morts/ép → 0.03, mais ne traverse jamais la bande). Entropie reste haute (~2.5) = aucune percée. Diagnostic : la couche manager AGRANDIT l'exploration (il faut co-apprendre le SENS des tâches ET quoi assigner = bootstrap poule-œuf) ET le manager re-décide à CHAQUE pas (K=1) → conditionnement bruité/instable pour les workers → la percée (atteinte par v1 à ~itér.360) n'arrive jamais. LEÇON : la hiérarchie n'aide pas automatiquement — elle ajoute un coût d'exploration ; précieuse sur tâches longues/compositionnelles, pénalisante sur une tâche simple déjà résolue par v1. CORRECTIFS possibles : (a) manager à cadence LENTE K>1 (ordres tenus → conditionnement stable) ; (b) curriculum (commencer sans la bande) ou + d'itérations ; (c) motivation intrinsèque ; (d) démontrer v2 sur scénario à CHOIX (plusieurs objectifs) où le manager a un vrai rôle.

**2026-06-02 (Mac) — v2 K=8 (ordres tenus, 800 itér.) : ENCORE 0 % (`run_v2_20260602_160558`).** La cadence lente N'A PAS débloqué → hypothèse « conditionnement bruité » RÉFUTÉE. Diagnostic confirmé : le manager ajoute une **barrière d'exploration** ; l'équipe se fige dans l'optimum « safe = ne pas mourir » (morts/ép ~0.07, entropie reste ~2.5) et ne perce JAMAIS, indépendamment de K. (v1 flat perçait à ~itér.360 ; v2 non, ni K=1 ni K=8.) Leçon : sur une tâche à chemin unique forcé, le manager est pur surcoût d'exploration. VRAIS CORRECTIFS : (a) **CURRICULUM** (commencer sans la bande → apprendre à traverser → réintroduire la bande) ou motivation intrinsèque ; (b) **warm-start** des workers depuis le modèle v1 ; (c) démontrer le chef sur un scénario **à CHOIX MULTIPLES** (plusieurs objectifs) où il a un vrai rôle. Décision utilisateur en attente.

**2026-06-02 (Mac) — v3 chef-sergent ARBITRE + curriculum (`run_v3_20260602_162522`).** NIVEAU 0 (sans danger, 200 itér.) : **réussite 100 %, 0 mort dès itér.40** → le chef coordonne la CONVERGENCE (toute l'équipe sur le même objectif) — démontré. NIVEAU 1 (danger, côté bloqué tiré au hasard, 800 itér.) : réussite **plafonne ~65 %, morts/ép ~1.0** → arbitrage PARTIEL (mieux que 50 % = pur hasard, donc le chef utilise l'info de danger, mais ne la maîtrise pas ; entropie reste ~1.0). Le curriculum a clairement débloqué (vs v2 qui restait à 0). Leçon : la convergence (coordination) est apprise facilement par le chef ; l'arbitrage tactique fin sous danger aléatoire reste dur. PISTES : (a) baseline SANS chef sur v3 (prouver l'apport sur la convergence) ; (b) pousser le niveau 1 (plus d'itér., p_hit plus faible, signal manager renforcé/lr manager) ; (c) ajouter métrique « a choisi le côté sûr ».

**2026-06-02 (Mac) — v3 ÉDUCATION DU CHEF (mgr-lr 1e-3, 1500 itér., `run_v3_20260602_164020`).** Réussite **100 % / 0 mort dès ~itér.480**, MAIS la note **« chef-bon-côté » reste à ~0.50 (hasard)** tout du long ! DÉCOUVERTE CLÉ : l'équipe réussit **SANS** que le chef choisisse le bon côté → **les workers contournent le chef**. Cause : dans l'obs, les WORKERS voient eux-mêmes les flags de danger (dl/dr) + les directions des 2 objectifs → ils filent au côté sûr tout seuls et convergent (même info ⇒ même choix), **en ignorant l'ordre du chef**. Le chef est REDONDANT → impossible à éduquer. CORRECTIF (= vrai modèle sergent) : **INFORMATION ASYMÉTRIQUE** — retirer danger+directions de l'obs des workers, ne les donner qu'au CHEF ; les workers ne voient que le local + l'ORDRE du chef et doivent OBÉIR. Le chef devient alors indispensable et « chef-bon-côté » devra monter à ~100 % pour réussir. Prochaine action : implémenter cette asymétrie (v3b).

**2026-06-02 (Mac) — v3c remontées locales (`run_v3_20260602_165817`).** Réussite **100 %/0 mort**, MAIS « chef-bon-côté » DESCEND à ~0.25 (PIRE que le hasard) → le chef est ENCORE contourné. Cause : les soldats, avec leur détection LOCALE du danger + la vue des 2 objectifs (dirL/dirR) + une politique partagée déterministe, **s'auto-coordonnent** (ils sentent le danger en avançant et convergent seuls sur le côté sûr), en IGNORANT l'ordre du chef. LEÇON PROFONDE : un commandant n'est NÉCESSAIRE que si les soldats ne peuvent PAS résoudre seuls ; des soldats compétents + info locale suffisante = autonomes = chef redondant (phénomène réel en MARL hiérarchique/communicant). CORRECTIF DÉCISIF : faire des soldats des EXÉCUTANTS stricts — retirer dirL/dirR de leur obs ; ils ne reçoivent que la direction vers l'objectif CHOISI PAR LE CHEF ; ils ne peuvent ni viser l'autre objectif ni savoir lequel est sûr. Alors le choix du chef détermine ENTIÈREMENT l'issue → « chef-bon-côté » devra monter à ~100 %. (= le chef sait via les remontées, les soldats exécutent sans discuter.)

**2026-06-02 (Mac) — v3d soldats exécutants stricts (`run_v3_20260602_171911`).** Réussite 100 %/0 mort MAIS « chef-bon-côté » ENCORE ~0.50 (chef toujours contourné). CAUSE GÉOMÉTRIQUE : la bande de danger laisse un DÉTOUR — colonnes centrales (5-6) libres + rangées du bas (10-11, sous la bande) libres → les soldats atteignent N'IMPORTE QUEL objectif sans croiser le danger, quel que soit l'ordre. Le danger n'est pas un vrai BARRAGE. META-LEÇON (récurrente, importante) : à l'échelle squad sur carte solvable, des soldats compétents CONTOURNENT systématiquement le besoin d'un chef ; rendre un commandant STRICTEMENT nécessaire exige un ENGAGEMENT IRRÉVERSIBLE (couloirs séparés par un mur) ou une info vraiment distribuée. FIX final : map à 2 COULOIRS séparés par un mur (ouverture en haut), danger barrant le couloir bloqué → s'engager est irréversible → le choix du chef détermine tout → chef-bon-côté forcé à ~1.0.

**2026-06-02 (Mac) — RECADRAGE utilisateur (important).** (1) La doctrine « soldats DERRIÈRE le chef / cohésion forcée » est à l'ENVERS : en réalité c'est plutôt l'inverse — les soldats (pointe/éclaireurs) sont souvent DEVANT, le chef se positionne pour observer/diriger (centre/arrière). Donc ne PAS imposer une formation « derrière le chef » ; au mieux une cohésion LÂCHE (la squad ne se disperse pas), positions relatives émergentes. (2) On est en **phase de FONDATION, pas encore au stade agentic** : ne pas sur-investir le « chef intelligent/décideur » maintenant — ça relèvera de la phase agentic (agents plus capables : mémoire, communication, doctrine riche). Le run v4 (cohésion-derrière) lancé = simple test de mécanique, PAS le modèle cible. Orientation : consolider les fondations, différer la finesse du rôle du chef.

**2026-06-02 (Mac) — v4 cohésion-doctrine (`run_v4_20260602_174603`) : confirme le recadrage.** Cohésion montée à **0.97** (mécanique OK) MAIS réussite **0 %** / 0 mort → les soldats S'AGGLUTINENT autour du chef et N'AVANCENT jamais (maximisent cohésion + évitent la mort, oublient la mission). Preuve empirique : la cohésion FORCÉE = amas inutile. Doctrine abandonnée. DIRECTION ACTÉE : consolider les fondations (pipeline MARL + env qui marchent), différer le « chef sophistiqué » à la phase agentic (prérequis : mémoire/RNN + communication apprise).

**2026-06-02 (Mac) — PHASE 1 FIGÉE.** Doc : `~/arma3-marl/PHASE1-FONDATION.md`. Socle de référence = **v1** (`toy2d_v1.py` + `train_harmattan_v1.py`, 100 %/0 mort, rôles utiles). Pipeline MARL vectorisé + historique + visu = validés. REPRISE = trajectoire initiale → **ÉTAPE 3 : CMDP / curseur λ** (vraie contrainte de survie auto-réglée, remplace `cas_pen=0.5` codé en dur). Jalon agentic ultérieur (différé) : mémoire RNN + communication apprise, prérequis d'un vrai chef.

**2026-06-02 (Mac) — PHASE 2 : bascule vers Arma — roadmap posée.** Phase toy-sim actée (v0/v1 rôles + Étape 3 CMDP/λ : λ s'auto-règle, mais sur tâche sans compromis le budget de risque ne mord pas — `c` fixe 0,15 OK, `c` variable codé/prêt pour tâches à compromis). DÉCOUVERTE : Arma 3 DÉJÀ installé sur la workstation : `/mnt/data/harmattan-sandbox/` (serveur dédié Linux `arma3server_x64`, mission HarmattanBridge.Altis, pont RPT->`~/intel/agents/arma_adapter.py`->store = OBS-OUT un sens, composant `hmt_bridge`, harmattan.cfg). Roadmap de bascule écrite dans `/mnt/data/harmattan-sandbox/PHASE2-VERS-ARMA.md` (S1 valider serveur headless -> S2 canal de CONTRÔLE bidirectionnel via callExtension+ZeroMQ -> S3 protocole de pas SQF -> S4 ArmaSquadEnv PettingZoo -> S5 abstraction calée sur le toy -> S6 reset rapide -> S7 débit/pré-entraînement toy puis fine-tune Arma -> S8 validation incrémentale). MAILLON MANQUANT = pont BIDIRECTIONNEL (actions IN + obs OUT) ; l'existant ne fait que sortir des events. Pas de Rust (arma-rs) ni pyzmq encore ; gcc/make présents.

**2026-06-03 — PHASE 2 / S1 + S2 RÉUSSIS : pont Arma <-> Python opérationnel.**
S1 (serveur headless) : démarre OK. FIX de la boucle « Mission read from directory » = ajouter **`addOns[]={"A3_Characters_F"}`** (+ addOnsAuto + AddonsMetaData) dans `mission.sqm` (original sauvé `.bak`). Lancement : `cd .../arma3server && LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config=.../staging/server.cfg -profiles=.../profiles -name=harmattan -world=Altis -autoInit`. `server.cfg` : `class Missions { class Harmattan { template="HarmattanBridge.Altis"; }; }`.
S2 (pont bidirectionnel par FICHIERS — pas d'extension/Rust/ZeroMQ) :
- **IN (actions)** : Python écrit `cmd_N.sqf` (N croissant) dans **`<MISSION>/hmt_bridge/`** (⚠️ dossier de la MISSION, PAS du serveur — `preprocessFile` résout relativement à la mission) ; `harmattan_actuator.sqf` (polling 0.3 s) fait `call compile` -> exécute. Après cmd_N, attend cmd_(N+1).
- **OUT (état)** : `diag_log "HARMATTAN {json}"` -> lu dans le RPT/`logs/server.out` (par `~/intel/agents/arma_adapter.py`).
- TEST validé : cmd_1 exécutée (HARMATTAN_RECV/TEST) + état lu (HARMATTAN_STATE nb_unites=1 pos=[1000,1005,184]). Serveur tourne.
PROCHAIN : S3 = côté Python, une boucle qui (a) demande l'obs (cmd qui diag_log l'état des unités en JSON) + la parse depuis le log, (b) écrit les actions en cmd incrémentés. Puis S4 = `ArmaSquadEnv` avec interface PettingZoo (reset/step) callée sur le toy.

**2026-06-03 — PHASE 2 / S3 RÉUSSI : boucle de contrôle squad Python<->Arma.** Modules `~/arma3-marl/arma_bridge.py` (classe `ArmaBridge` : `send(sqf)` écrit cmd_N synchronisé sur le log + attend RECV ; `read_obs()` envoie un SQF qui diag_log `HARMATTAN_UNIT idx x y alive side` par unité, puis parse les lignes en dicts) + `arma_demo.py`. Démo validée sur le serveur live : spawn d'une squad BLUFOR de 4 (`createGroup west` + `createUnit "B_Soldier_F"`), lecture des positions des 5 unités, ordre `doMove [1120,1120]`, relecture 9 s après -> **les unités ont bougé** (obs avant/après cohérentes). Donc actions IN + obs OUT pleinement opérationnelles pour une squad. PROCHAIN : S4 = `ArmaSquadEnv` interface PettingZoo (reset/step) : reset = spawn squad + objectif/ennemi, step = écrire les actions (doMove/macro) + lire l'obs calée sur le vecteur du toy ; puis reset rapide d'épisode (S6) et abstraction obs/action (S5).

**2026-06-03 — PHASE 2 / S4 RÉUSSI : ArmaSquadEnv opérationnel.** `~/arma3-marl/arma_env.py` (classe `ArmaSquadEnv`, interface type PettingZoo). `reset()` : `deleteVehicle allUnits` + spawn squad de 4 (B_Soldier_F, disableAI AUTOTARGET + CARELESS) + objectif (1160,1160) ; renvoie obs/agent 7d [x_norm,y_norm,dir_obj_x,dir_obj_y,vivant,coéq_dx,coéq_dy]. `step(actions)` : 5 actions discrètes (rester/N/S/E/O) -> `doMove` par unité, lit l'obs (HARMATTAN_AG via HMT_SQUAD indices stables), calcule récompense (objectif sécurisé = >=3 dans rayon) / coût (pertes) / done. Validé LIVE : reset + 8 pas heuristiques sans crash, obs cohérentes. ⚠️ Tuning : soldats Arma lents -> step_wait=2.5s/move=14m/8 pas insuffisants pour 160m (réalisme, pas un bug) ; augmenter step_wait/acc/max_steps. **BILAN : S1->S4 = pont complet + env RL Arma OPÉRATIONNELS.** PROCHAIN : S5 (abstraction obs/action calée sur le toy + ajouter un ennemi OPFOR pour vrai combat/pertes), puis brancher le trainer MARL (pré-entraîner toy -> fine-tune Arma, S7).

**2026-06-03 — PHASE 2 / Options 1+2 FAITES + rapport.** Option 1 (scène vivante + capture) : `doMove` ne déplaçait pas la squad (statique — IA formation/pathing Arma) -> passé à **`setPosATL`** (déplacement direct par pas) -> squad **avance et SÉCURISE l'objectif au pas 19, 0 perte**. OPFOR spawné (O_Soldier_F, COMBAT) mais n'a pas accroché (0 perte) -> réglage placement/engagement à affiner. Capture = **carte top-down depuis positions RÉELLES Arma** (`arma_capture.py`) -> `~/Documents/harmattan-runs/arma_capture.gif` (3D réel = client GUI via NoMachine, ultérieur). Option 2 : `arma_train_smoke.py` branche `ActorCritic` (obs=7->5 actions x4) sur `ArmaSquadEnv`, 8 pas + 1 pas de gradient (perte 0.085) -> **chaîne RL branchée sur Arma validée**. Rapport : `~/Documents/harmattan-RAPPORT.{md,pdf}`. BILAN GLOBAL : toute la chaîne prouvée, de l'apprentissage (toy, rapide) à l'exécution/validation dans Arma 3 (pont opérationnel).

---

## Jalon — Visuel 3D Arma obtenu (2026-06-03)

**Résultat :** squad BLUFOR visible **en 3D sur la terre ferme**, qui se déplace, via le **client Arma de la station Linux** (Proton, vu par NoMachine).

**Chemin qui marche :** le client **HÉBERGE** lui-même la mission (Multiplayer → New → LAN → HarmattanBridge) → pas de validation de ticket Steam, donc pas de kick.

**Leçons clés (capital) :**
1. **Se connecter au serveur dédié = kické** : « invalid ticket / Owner ID ... Steam server: 0 ». L'auth Steam Game-Server du dédié Linux ne monte qu'à moitié (`SteamAPI initialization failed`). Piège classique des serveurs Arma auto-hébergés.
2. **Le client-hôte FIGE l'index des fichiers de la mission au lancement** → le pont fichier (`cmd_N.sqf` écrits après coup) renvoie « not found ». Donc : **le pont live ne pilote QUE le serveur dédié** (qui relit le dossier en direct) ; pour le **visuel 3D**, on passe par le **client-hôte + console de debug / démo bakée dans init.sqf**.
3. Joueur + squad placés aux coords du jouet `[1000,1000]` = **pleine mer sur Altis** → téléport sur terre via `BIS_fnc_findSafePos` autour du centre `[16000,16000]`.

**Mis en place :**
- Mission copiée dans le client : `…/common/Arma 3/MPMissions/HarmattanBridge.Altis`.
- `description.ext` : `enableDebugConsole = 2;` (console accessible à l'hôte).
- `init.sqf` : démo auto (attend le joueur → téléporte sur terre → spawn 4 BLUFOR → `move` 120 m).
- `arma_bridge.py` : chemins surchargeables par env (`HMT_MISSION` / `HMT_BRIDGE` / `HMT_LOG`).
- Bureau station : `~/Bureau/Harmattan/COMMANDES-Harmattan.txt` (3 commandes console : téléport+spawn, +ennemis, caméra libre).

**Infra :** SSH depuis le Mac nécessite `TMPDIR=/var/tmp` (le temp local Mac saturait, ENOSPC).

---

## Jalon — Entraînement DANS Arma + politique déployée live (2026-06-03)

**Bout en bout démontré :** entraîner une politique MARL *directement dans le moteur Arma*, puis la *déployer live dans le jeu* (les agents réfléchissent et agissent en 3D).

**1. Env vectorisé `arma_env_vec.py` (le verrou levé).** N escouades EN PARALLÈLE dans UN serveur dédié ; un aller-retour du pont fait avancer les N. Casualties = vrai feu OPFOR (HandleDamage plafonné à 0.85 → unités jamais vraiment mortes → reset instantané, RL-mort = dégâts ≥0.7). Spawn par grille au centre d'Altis via `BIS_fnc_findSafePos` (terre garantie). Débit : 3.4 tr/s (N=6) → **24 (N=48) → 36 (N=64)** ; scale ~linéaire avec N.

**2. Trainer `train_arma_vec.py` (MAPPO, réutilise `ActorCritic`).** 1er run cas_pen=0.5 → **optimum du lâche** (l'équipe apprend à ne pas avancer ; réussite 0, entropie chute). CAUSE : l'env Arma n'avait pas de **shaping** (le toy si). FIX : récompense de progression par potentiel (`beta*(prev_d-cur_d)` vers l'objectif) + cas_pen bas (0.1). Résultat run 2 : **0 % → 98 % de réussite, 0 perte, en ~35 itér (~19 min)**. Modèle : `~/Bureau/Harmattan-entrainements/run_arma_20260603_144218/model.pt`.

**3. Ressources :** entraînement **PAS borné par la machine** mais par le **temps réel d'Arma**. GPU 3090 ~0 %/0.6 Go, ~1 cœur/24, RAM ~2 Go. → marge énorme : la voie pour accélérer = **plusieurs serveurs Arma en parallèle** (multi-serveurs), pas un plus gros réseau.

**4. Déploiement live `gen_policy_sqf.py` → `policy.sqf`.** Le pont live ne pilote que le dédié (client-hôte fige les fichiers). Donc pour le visuel : le mini-réseau (7-64-64-5, ~5000 poids) est **réimplémenté en SQF** (tanh via exp, mat-vec en forEach, argmax) et **embarqué dans la mission client** (init.sqf → `call compile preprocessFileLineNumbers "policy.sqf"`). À l'hébergement : téléport sur terre, spawn squad+OPFOR+marqueur, **la mission fait tourner la politique elle-même** (doMove par pas), boucle. Vérifié numériquement (Est→Est, Nord→Nord). **Confirmé visuellement : les soldats avancent, tirent, se placent.** Le SQF reste valable tant que le réseau est petit ; gros réseau futur = pont/extension.

**Suite prévue :** durcir la tâche (vraies tactiques) + run lourd multi-serveurs.

---

## Jalon — Tâche DURCIE : tactique émergente dans Arma (2026-06-03)

**Objectif :** forcer de vraies tactiques. Env `arma_env_vec.py` V2 : 3 OPFOR **létaux** gardant l'objectif (skill 0.5, à obj−28, étalés ±16) ; **obs 7→10** (ajout menace : direction + proximité du plus proche OPFOR) → l'escouade PERÇOIT le danger ; obj_dist=150.

**Bug rencontré (important) :** 1er essai N=64 → positions lues à **0**, retour +198 aberrant, morts 3.9. CAUSE = **serveur dédié SATURÉ** par le combat (64 zones × ~450 unités qui tirent) → le pont lisait des positions vides. Confirmé : sur serveur **frais**, lecture parfaite. FIX : (a) lecture **robuste** (garder la dernière position connue si une lecture rate, au lieu de 0) ; (b) **N=32** + OPFOR skill 0.5 gardant l'objectif (squad part en sécurité, danger près de l'objectif) ; (c) settle 0.5→0.6.

**Résultat (run_arma_20260603_154533) :** courbe en deux temps — d'abord apprend à FONCER (réussite↑ mais **pic de pertes 0.41** en traversant la zone gardée), puis **les pertes s'effondrent (0.41→0.01) pendant que la réussite continue de monter**. Convergé : **réussite 98 %, morts/ép 0.01** (~50 itér). → **vraie tactique émergée toute seule** : atteindre l'objectif en évitant le kill-zone. Débit ~19 tr/s @ N=32 (~2-3 cœurs/24 ; le multi-serveurs reste à bâtir pour les 19 cœurs idle).

**À faire pour le visuel :** régénérer `policy.sqf` depuis ce modèle (obs 10-dim → ajouter le calcul de menace en SQF + scène calée : obj 150, OPFOR gardant l'objectif, scale 150).

---

## CAP STRUCTURANT — l'objectif final est AGENT vs AGENT (2026-06-03)

**Younes (directive) :** « après ça sera des agents contre des agents ». L'OPFOR scriptée actuelle n'est qu'un **tremplin**. Le but = **self-play / MARL adversarial** : BLUFOR ET OPFOR apprennent → environnement VRAIMENT ultra-contesté (l'ennemi s'adapte, course à l'armement, tactiques émergentes des deux côtés — esprit AlphaStar/OpenAI Five/hide-and-seek).

**Implications archi (à garder en tête pour TOUTES les décisions) :**
1. **Symétrie déjà là** : le pont lit ET pilote les deux camps (HMT_AG / HMT_OP). Passer en self-play = ajouter une politique OPFOR + une boucle de self-play (mêmes briques : env vectorisé + pont + trainer).
2. **Contrôle des tirs** : en self-play, deux camps téléportés (setPosATL) ne visent pas (le mur touché en V3). → il faudra un schéma de contrôle qui résout le combat proprement (macro-actions ou résolution abstraite), pas la gunplay Arma brute.
3. **Mémoire = prérequis** : un adversaire qui apprend = la menace dynamique ultime → la phase agentique (RNN/mémoire) n'est pas optionnelle, c'est un prérequis du self-play.

**Ordre de marche cohérent :** maîtriser le combat statique (fait, 99%) → run lourd (en cours) → mémoire (agentique) → OPFOR appris (self-play). La couche actuelle reste le socle.

---

## Vision affinee — CHAMP DE BATAILLE MIXTE (2026-06-03)
Younes : des squads d'agents qui affrontent l'IA Arma ET les agents pour atteindre l'objectif. PAS un duel sterile 4 contre 3 : un champ de bataille PEUPLE ou l'escouade d'agents prend/tient l'objectif AU MILIEU d'un vrai combat avec IA militaire Arma ET (a terme) agents ennemis melanges. Progression adversaire : B1 vraie IA Arma -> B1.5 IA Arma + agents ennemis (forces mixtes) -> B2 self-play. Profondeur INTEGREE (lambda-Arma, domain randomization, transfert toy->Arma, capacite reseau croissante). Fiche : ~/arma3-marl/FICHE-ROUTE.md (2 axes : cerveau A0-A3 + adversaire B0-B2).
POINT TECHNIQUE CLE : pour que les agents COMBATTENT (tirent), il faut mouvement NATUREL doMove + gunplay, pas le teleport (mur V3). Donc B1 = adversaire IA Arma + controle A3, couples. Env prepare : ~/arma3-marl/arma_env_b1.py (agents gunplay + doMove contre vraie IA Arma defendant l'objectif ; mixte-ready ; a tester quand un serveur se libere du run lourd).

---

## Jalon — Transfert toy->Arma + assaut offensif visible (2026-06-03)
PIPELINE TRANSFERT operationnel (roadmap S7). toy_b1.py = sim NumPy calee EXACTEMENT sur l'obs Arma B1 (10-D) -> ~120 000 transitions/s (80 000x Arma). pretrain_b1.py = MAPPO sur toy_b1, poids -> pretrain_b1.pt -> transferent direct dans Arma (meme obs/action).
DECOUVERTE (lecon lambda EN PRATIQUE) : avec cas_pen=0.35 la politique PLAFONNE a 24 % (optimum du lache : hesite a portee). Avec cas_pen=0.15 (mode assaut) elle EXPLOSE le plateau -> 70 % reussite ET 0 perte. Paradoxe instructif : baisser la penalite de mort donne PLUS de reussite ET moins de morts -> la prudence excessive EMPECHE de decouvrir la bonne manoeuvre. Le bon reglage du risque ne sert pas qu'a survivre, il DEBLOQUE l'apprentissage.
TACTIQUE APPRISE : assaut frontal qui gagne le duel (4 agents concentrent le feu, neutralisent 3 defenseurs avant de tomber), pas l'evitement. Validee VISUELLEMENT : gen_policy_b1_sqf.py -> policy.sqf (reseau 10-D embarque + doMove + gunplay) -> agents combattent la VRAIE IA Arma en 3D, offensif. Younes : c'est beaucoup mieux, plus offensif.
PROCHAIN : fine-tune cette politique DIRECTEMENT dans Arma B1 (warm-start depuis pretrain_b1.pt) en multi-serveurs, pour adapter a la balistique reelle Arma. Briques a ajouter : warm-start (--init) dans le trainer + MultiArmaEnv pointant sur ArmaEnvB1 + relancer les serveurs dedies.

---

## Jalon — Fine-tune B1 dans Arma + boucle de transfert BOUCLEE (2026-06-03)
Warm-start (--init pretrain_b1.pt, 70% toy) -> fine-tune DANS Arma B1 (vrai combat IA Arma), 8 SERVEURS dedies en parallele (ports 2402-3102, ~15.5 tr/s = x7.5 vs 1 serveur). Modele : run_arma_20260603_203326/model.pt.
SIM-TO-REAL observe en direct : la politique toy (assaut frontal) ECHOUE au depart dans le vrai Arma (succes 0%, morts 2.5/4 -> l'IA Arma vise/se couvre pour de vrai, le jouet ne capture pas la balistique). Le fine-tune CORRIGE : morts 2.79->0.00 en ~5 iter, succes 0%->68% en ~40 iter. Final : ~68% reussite / 0 perte, DEPASSE le niveau toy (70% abstrait) car adaptee au vrai feu.
BOUCLE DE TRANSFERT COMPLETE (roadmap S7) : pre-entrainer vite sur toy (167k tr/s) -> warm-start -> fine-tune dans Arma (15 tr/s x8 serveurs) -> politique de combat reelle. Redeployee dans le visuel B1 (gen_policy_b1_sqf.py -> policy.sqf depuis le modele B1-reel). Infra : multi_server.sh (M serveurs, port base 2402), train_arma_vec.py (--servers --b1 --init), arma_env_multi.py (env_b1).
ETAT FICHE : A0 socle + multi-serveurs + B1 (vraie IA Arma) + transfert toy->Arma = FAITS. Reste : A1 memoire (RNN), A2 comms, A3 macro-actions, B1.5 forces mixtes, B2 self-play. Le verrou = memoire.

---

## Jalon — A1 MEMOIRE validée (phase agentique demarree) (2026-06-03)
LE VERROU EST LEVE. toy_mem.py : tache a observation PARTIELLE — l'objectif n'est visible que 2 pas (agent FIGE pendant l'observation pour tuer la fuite par la position) puis CACHE ; objectif aleatoire chaque episode. train_mem.py : compare politique RECURRENTE (GRU) vs SANS memoire (feedforward), MAPPO. Boucle PPO recurrente = BPTT sur le rollout + masquage des hidden aux fins d'episode ; cuDNN desactive (torch.backends.cudnn.enabled=False, sinon le GRU plante a l'init sur la 3090).
RESULTAT DECISIF : sans memoire = 22 % (ne retrouve pas l'objectif cache), AVEC memoire (GRU) = 100 %. Preuve empirique que la memoire debloque ce que le feedforward ne peut pas. Piege evite : la position de l'agent FUITE l'objectif s'il bouge pendant la phase visible -> il faut le figer.
BRIQUES REUTILISABLES : RecurrentActorCritic (GRU actor par-agent + GRU critic central) + boucle PPO-BPTT. Ce socle sert pour : le combat DYNAMIQUE Arma (V3 qui plafonnait sans memoire), A2 communication, B2 self-play. PROCHAIN : porter la memoire dans les taches Arma dynamiques, puis A2 comms.

---

## Jalon — A1 (memoire) + A2 (comms) VALIDEES sur toy (cerveau agentique prouve) (2026-06-03)
PISTE 1a (memoire dans le combat DYNAMIQUE = le V3 qui plafonnait). toy_dyn.py : ennemis MOBILES qui traquent + obs PARTIELLE (ennemi visible seulement dans un rayon de vue). train_mem.py generalise (--env dyn). RESULTAT : feedforward = 46 %, RECURRENT (GRU) = 67 % (trajectoire 24%@280 -> 41%@450 -> 67%@799). La memoire GAGNE sur le dynamique. Lecon : le GRU est ~6x plus lent a optimiser (19k vs 71-110k tr/s) et a besoin de BIEN plus d'iterations -> a 280 itexthas il etait sous-entraine (24%<46%), a 800 il domine.
PISTE 2a (communication, info distribuee). toy_comm.py : seul l'agent 0 (eclaireur) voit l'objectif, les 3 autres aveugles ; >=3 a l'objectif pour reussir. train_comm.py : CommNet 1 tour (chaque agent emet un message-vecteur appris, recoit la moyenne des messages des AUTRES, differentiable). RESULTAT : SANS comms = 23 %, AVEC comms = 100 %. La communication GAGNE, net.
=> Les DEUX briques du cerveau (memoire + communication) sont prouvees. Briques reutilisables : RecurrentActorCritic (GRU+BPTT), CommNet. PROCHAIN : (a) les COMBINER (memoire+comms), (b) porter dans Arma (1b = fine-tune recurrent du combat dynamique sur 8 serveurs), (c) A3 macro-actions. Le verrou (memoire) est definitivement leve.

---

## Jalon — Option 1 : MEMOIRE + COMMS combinees (cerveau agentique complet) (2026-06-03)
toy_both.py : exige les DEUX. Seul l'agent 0 (eclaireur) voit l'objectif, et seulement aux 1ers pas (fige) puis cache pour tous ; les 3 autres ne le voient jamais ; >=3 a l'objectif pour reussir. => l'eclaireur doit SE SOUVENIR (memoire) ET DIFFUSER (comms). train_both.py : reseau RecComm = enc -> CommNet (canal de messages) -> GRU (memoire) -> action, avec interrupteurs --mem/--comm. RESULTAT (450/280/280 iter) : MEM+COMM=100%, MEMOIRE seule=67%, COMMS seule=42%. Le cerveau complet domine (retirer memoire -58pts, retirer comms -33pts). Briques memoire+comms combinees = VALIDEES. Note : les ablations n'effondrent pas a 0 (structure de la tache-jouet partiellement exploitable via shaping), mais le full domine nettement.
PROCHAIN (Option 2) : porter dans Arma = fine-tune RECURRENT du combat dynamique reel (B1, vraie IA mobile) sur 8 serveurs -> il faut un trainer Arma recurrent (fusion boucle PPO-BPTT + MultiArmaEnv) + warm-start depuis une politique toy recurrente. Puis Option 3 = A3 macro-actions.

---

## Jalon — Option 3 : MACRO-ACTIONS validees + LES 3 OPTIONS FAITES (2026-06-03)
toy_macro.py : 5 macros [HOLD, AVANCER, COUVERT, SUPPRESSER, ASSAUT] (macro=1) vs 5 primitifs (macro=0). La SUPPRESSION cloue l'ennemi (il ne tire plus) -> les autres avancent en securite ; COUVERT reduit l'exposition. Branche dans train_mem (--env macro / --env prim). RESULTAT : primitifs = 0 %, macro-actions = 81 %. Le plus tranche de tous. C'est le mur V3/B1 (teleport = pas viser) qui tombe : les macro-actions = combat tactique propre (couvert + suppression + assaut coordonne). A3 validee.
BILAN DES 3 OPTIONS (toy) : Opt1 memoire+comms=100% (vs 67/42 ablations) ; Opt2 fine-tune RECURRENT dans Arma B1 (obs rendue partielle pour que la memoire compte, warm-start depuis pretrain_dyn_rec.pt, 8 serveurs, train_arma_rec.py) = EN COURS (morts qui chutent, comble le fosse sim->reel) ; Opt3 macro-actions=81% vs 0% primitifs.
=> Tout le cerveau agentique (memoire + comms) ET le combat tactique (macro-actions) sont PROUVES sur toy, plus le pipeline de transfert vers Arma. Reste a integrer : macro-actions dans Arma, forces mixtes (B1.5), self-play (B2). Briques : RecurrentActorCritic, CommNet, RecComm, ToyMacro, train_arma_rec (recurrent multi-serveurs).

---

## Jalon — "pousser tout" #1 : SELF-PLAY (B2) valide (2026-06-04)
toy_selfplay.py : DEUX camps APPRENANTS (BLUFOR vs OPFOR, 3 agents chacun) contestent un objectif central, macro-actions des deux cotes (AVANCER/SUPPRESSER/COUVERT). train_selfplay.py : deux politiques MAPPO entrainees SIMULTANEMENT (co-adaptation), recompense symetrique. PIEGE : self-play naif -> STALEMATE defensif (1% decide, les deux s evitent). FIX : victoire a l echeance par CONTROLE CUMULE de l objectif. RESULTAT : BLU 49 / OPF 51 = PARITE (course a l armement a l equilibre), ~15-24% engagements decisifs. Mecanisme self-play VALIDE. Modeles selfplay_blu.pt / selfplay_opf.pt.

---

## Jalon — "pousser tout" #2 : cerveau complet = MODULARITE (2026-06-04)
Test du cerveau complet (RecComm mem+comms + macro-actions) sur toy_macro rendu a obs partielle (occlusion ennemis, sight=110). RESULTAT : full (mem+comm+macro) = 82 %, depouille (macro seul, sans mem/comm) = 83 % -> EGALITE. Lecon : cette tache (ennemis STATIQUES + objectif TOUJOURS visible) ne REQUIERT pas memoire/comms -> ils n ajoutent rien. Les briques sont MODULAIRES : memoire gagne sur mobiles occultes (67/46), comms sur info distribuee (100/23), macro sur combat tactique (83/0). Le cerveau complet = union des capacites, chacune utile sur la tache qui la reclame. Pas de regression a empiler les briques (full ~= depouille quand inutiles), juste un cout de calcul (recurrent plus lent). PROCHAIN (option 3) : integration Arma (env macro-actions + run lourd), bloquee tant qu Option 2 occupe les 8 serveurs.

---

## Jalon — ETAPE 3.1 VALIDEE : macro-actions dans Arma (2026-06-04)
arma_env_macro.py (sous-classe de ArmaEnvB1) : 5 macros mappees sur Arma reel. 0=HOLD (doStop), 1=AVANCER (doMove vers obj), 2=COUVERT (setUnitPos DOWN + doMove lent), 3=SUPPRESSER (doTarget+doFire ennemi proche + l ennemi vise = suppressFor 2.5 -> cloue), 4=ASSAUT (UP + doMove rapide). obs 10 calee sur toy_macro (en_dx/dy occultes par sight + ennemi_proche_supprime). VALIDE en test (6 escouades, heuristique agent0 SUPPRESSE / autres AVANCENT) : ennemis_supprimes 0.2-0.8 (la suppression cloue vraiment), opf_vivants 2.83->1.83 (neutralisation au vrai feu Arma), pertes BLU reelles. Debit 1.3 tr/s (lent, combat riche ; x8 serveurs ~8-10). Le combat tactique propre tourne dans le moteur. PROCHAIN ETAPE 3.2 : run lourd (warm-start toy_macro recurrent -> fine-tune dans arma_env_macro sur 8 serveurs) ; trainer = train_arma_rec adapte a l env macro. Puis 3.3 self-play Arma.

---

## Jalon — ETAPE 3.2 DEMARREE et validee (run lourd macro Arma) (2026-06-04)
train_arma_rec.py --macro 1 : fine-tune RECURRENT de la politique macro DANS arma_env_macro, 8 serveurs (MultiArmaEnv env_macro=1), warm-start depuis pretrain_macro_rec.pt (toy macro recurrent, 82%). Demarrage VALIDE : env pret N=64 A=4 O=10, warm-start charge, 14.6 tr/s, it0-1 succes 0 / morts 2.5-3 (politique macro patine au depart dans le vrai Arma = fosse sim->reel attendu). Le fine-tune va l adapter (~75 min). Rapport auto job 55cd33d6 /15 min. Bug corrige au passage : --macro ajoute en double dans l argparse (premier cablage partiellement passe). PROCHAIN 3.3 : self-play DANS Arma (politique OPFOR + double entrainement), bloque tant que 3.2 occupe les serveurs ; warm-start depuis selfplay_blu/opf.pt.

---

## Jalon — ETAPE 3.2 CONVERGEE : combat tactique macro DANS Arma (2026-06-04)
train_arma_rec --macro 1, 12 serveurs (96 escouades), warm-start pretrain_macro_rec.pt (toy macro recurrent 82%). 60 iter / ~69 min a 22.2 tr/s. RESULTAT : succes 0 -> ~55 %, morts/ep 2.5 -> ~0.00. La politique COMBAT TACTIQUEMENT dans le moteur (suppresse/avance/assaut) contre la vraie IA Arma, en obs partielle, prend l objectif ~1 fois sur 2 avec quasi 0 perte. Entropie MONTEE 0.43 -> 1.24 = melange varie de macros = vraie diversite tactique. Le mur V3/B1 (teleport=pas viser) est tombe. Scaling 12 serveurs valide (debit x1.57 vs 8 ; CPU ~82% pic, plafond pratique ~16). Modele dans run_armarec_* le plus recent. SERVEURS LIBRES -> ETAPE 3.3 (self-play Arma) debloquee.

---

## Jalon — ETAPE 3.3 : SELF-PLAY DANS ARMA (ENDGAME) demarre (2026-06-04)
arma_env_selfplay.py : DEUX camps d AGENTS (BLU+OPF, 3 chacun) dans Arma, pilotes par macros (HOLD/AVANCER/SUPPRESSER/COUVERT), combat = vraie balistique, obs/camp calee sur toy_selfplay. train_arma_selfplay.py : wrapper MultiSelfPlay (M serveurs en parallele) + double entrainement FF, warm-start selfplay_blu/opf.pt. VALIDE 3.3.1 (deux camps spawnent + s accrochent au contact) puis lance 3.3.3 sur 12 serveurs (N=48 batailles, 11 tr/s). Demarrage : it0 BLU 0/OPF 1, it1 BLU 0.17/OPF 0.83, decidees 0.11->0.21 -> course a l armement lancee, BLU s adapte. SWEEP parallele (GPU) a trouve : letalite hit=0.32 -> 89% parties decidees (vs 20% a 0.16) = casse le stalemate ; le vrai combat Arma etant letal, le self-play Arma est naturellement decisif. C EST L ENDGAME : deux escouades apprenantes qui s affrontent dans le vrai jeu. Run ~50 min.
=> PROJET COMPLET de bout en bout : entrainement Arma -> multi-serveurs -> combat vs IA Arma -> transfert toy<->Arma -> memoire -> comms -> macro-actions -> macro dans Arma -> self-play DANS Arma. Toutes les briques de la fiche FAITES.

## ÉTAPE A — King of the Hill 3 camps (toy) — 2026-06-04

Build : `toy_koth3.py` (3 factions BLU/OPF/IND à 120° autour d'une colline ; ennemi = union des 2 autres ;
4 macros ; récompense contrôle symétrique + victoire +1/−0.5/−0.5 ; obs 10) + `train_koth3.py` (3 politiques MAPPO FF simultanées).
Run 600 it, 512 envs, hit 0.18, ~20 700 tr/s (3090).

RÉSULTAT (riche, partiel) :
- OPF s'échappe d'abord (0.59→0.73 vers it 200) = boule de neige d'avantage initial, comme en 2 camps.
- PUIS rééquilibrage : vers it 440 quasi parité (BLU 0.28 / OPF 0.35 / IND 0.38). La pression « équilibre des forces » EXISTE : OPF tiré de 0.73 à 0.34.
- MAIS ça OSCILLE et dépasse : à la fin IND prend la tête (0.53), BLU décroche (0.08). Pas de parité stable. Écart final 0.45.
- SIGNATURE CLÉ : taux de parties décidées s'EFFONDRE 0.83 → 0.20. En 3 camps, celui qui va sur la colline se fait punir par les 2 autres → la plupart des parties finissent en NUL (déni mutuel). C'est l'effet anti-runaway structurel, émergent.

CONCLUSION : 3 camps transforment l'échappée nette (2 camps : un camp 0.84) en régime OSCILLANT + riche en nuls (déni mutuel),
mais ne fixent pas à 33/33/33 tout seuls + un trainard peut décrocher. Pour des coalitions DÉLIBÉRÉES (focus le leader) il faut :
(1) un SIGNAL DE LEADER dans l'obs (part de contrôle de chaque camp adverse), (2) récompense pour déloger le leader,
(3) contrôle scientifique : init identique des 3 réseaux pour séparer « chance d'init » de la vraie dynamique. → koth3 v2.

## ÉTAPE A v2 — coalition incitée (signal leader + focus + init identique) — 2026-06-04

`toy_koth3v2.py` (obs 12 : +direction vers le camp adverse qui mène ; récompense focus*degats_au_leader) + `train_koth3v2.py` (--same_init).
Run 600 it. RÉSULTAT : ÉCHEC du correctif. Pic OPF 0.74 ; fin BLU 0.01 / OPF 0.42 / IND 0.57 ; écart 0.55 (PIRE que v1 0.45) ; décidées 0.43.
DIAGNOSTIC (clé) :
 - Init identique (it0 écart 0.20) et OPF s'échappe quand même -> divergence = DYNAMIQUE, pas chance d'init.
 - BLU s'effondre à 0.01 = SPIRALE DE LA MORT (un trainard perd plus -> pires données -> s'effondre). Mode d'échec classique du MARL simultané à politiques séparées.
 - La récompense 'frappe le leader' a AFFAIBLI le déni mutuel de v1 (décidées 0.20 -> 0.43) : les camps farment le leader au lieu de verrouiller la colline.
CONCLUSION : les rustines (signal/focus/init) ne corrigent pas la spirale. Le jeu est SYMÉTRIQUE -> vrai correctif = POLITIQUE PARTAGÉE
unique qui pilote n'importe quel camp (self-play à 1 cerveau) -> trainard impossible par construction (sorties symétriques ~33/33/33),
et c'est AUSSI le modèle de déploiement réaliste (un cerveau entraîné que chaque faction exécute). -> koth3 v3 = politique partagée.
Pour des camps ASYMÉTRIQUES plus tard (ex. le camp de l'humain) : ligue/population (pool de versions figées) pour laisser les trainards récupérer.

## ÉTAPE A v3 — politique PARTAGEE — 2026-06-04 — + CONCLUSION consolidée

`train_koth3v3.py` : UN seul reseau pilote les 3 camps (3x donnees, 1 update PPO), env toy_koth3 (obs 10). Run 600 it, ~25 000 tr/s.
RESULTAT : la parite N'est PAS tenue non plus. it0 ecart 0.06 -> BLU mene (0.58 a it240) -> OPF mene (0.58 a it560) -> fin 0.11/0.54/0.35, ecart 0.44.
=> Ma prediction 'parite par construction' est REFUTEE. Deux raisons : (1) les slots de camp ne sont pas parfaitement symetriques
(formation interne non tournee selon l'angle du camp + traitement sequentiel 0,1,2 + tie-break argmax/argmin biaise vers l'indice bas),
(2) surtout : le LEADERSHIP TOURNE au fil de l'entrainement (BLU->OPF->IND) = DYNAMIQUE CYCLIQUE / INTRANSITIVE (type pierre-feuille-ciseaux),
phenomene fondamental des jeux competitifs a 3 joueurs (general-sum, pas de garantie de convergence ; l'apprentissage CYCLE au lieu de converger).

CONCLUSION CONSOLIDEE ÉTAPE A (3 variantes testees) :
 - v1 (politiques separees), v2 (separees + signal leader + focus + init identique), v3 (politique partagee) -> TOUTES finissent ecart ~0.44-0.55
   avec un trainard, MAIS le leader change selon la variante/le moment -> ce n'est ni un bug ni une malchance d'init : c'est du CYCLING 3-joueurs.
 - Effet POSITIF robuste : taux de parties decidees s'EFFONDRE quand les agents apprennent (deni mutuel : monter sur la colline = se faire punir)
   -> equilibre des forces / coalitions EMERGENT bel et bien, juste pas sous forme de win-share stable 33/33/33.
 - Les agents produits sont COMPETENTS (contestent, suppriment, denient) -> deployables tels quels (figer un snapshot).
 - VRAI correctif pour stabiliser l'entrainement = LIGUE/POPULATION (PSRO, facon AlphaStar) : pool de versions figees, on s'entraine contre un melange
   -> casse le cycle 'courir apres le dernier adversaire'. C'est l'outil concu exactement pour les jeux cycliques/intransitifs. = v4 si on veut la rigueur.

## ÉTAPE A (recadree "gagner l'objectif", 1 cerveau/camp) — 2026-06-04 — CONCLUSION DE FOND

User recadre : but = GAGNER L'OBJECTIF, pas la parite ; 1 cerveau par camp.
- obj v1 (tie_pen 0.3, hit 0.18) : SECURISE s'effondre 1.0->0.0. Les agents trouvent le STANDOFF (monter = se faire tuer par les 2 autres ; encaisser le nul vaut mieux). Pen. de nul trop faible.
- obj v2 (kappa 0.25 controle dominant, hit 0.12 moins letal, tie_pen 0.2) : OCCUP 1->7.5/9 (ils FONCENT tous sur la colline) MAIS SECURISE->0, decidees->0, controle partage EXACTEMENT a egalite -> 100% nuls.

DIAGNOSTIC FINAL (le "probleme des trois corps" du combat) : un affrontement PARFAITEMENT SYMETRIQUE a 3 pour UN point unique est STRUCTURELLEMENT INDECIS.
Toutes les variantes (separees / partagee / anti-leader / pen-nul / controle-dominant / letalite haute|basse) tombent dans :
soit STANDOFF (personne n'y va), soit COHUE (tous y vont, contestation eternelle). Jamais de vainqueur net. Ce n'est PAS du reglage : c'est la SYMETRIE.
La competence de COMBAT est la (ils vont a la colline, suppriment, se couvrent) ; ce qui manque c'est la DECISIVITE, impossible sous symetrie parfaite (controle se partage a egalite).

RESOLUTION (= mecaniques du VRAI KotH qui BRISENT la symetrie) : (1) capture PAR PRESENCE/progression (barre de capture) avec dominance requise (il faut DEGAGER les ennemis), (2) AO qui TOURNE, (3) respawns decales, (4) participants ASYMETRIQUES (l'humain, forces differentes). Le toy parfaitement symetrique est le pire cas ; le vrai jeu ne l'est pas.
=> Test de confirmation cheap propose : spawns asymetriques par episode + capture-par-superiorite -> verifier que la decisivite EMERGE. Puis Etape C (vrai KotH Arma, asymetrique par nature).

## 3090 ENFIN MOTEUR — sim GPU-native — 2026-06-04

User : "faut vraiment faire travailler la 3090". Constat : 3090 a 0% / 10W / 293Mo (sim numpy sur CPU = goulot ; le GPU attendait).
Build : `koth_gpu.py` (champ de bataille KotH 3 camps ENTIEREMENT en tenseurs torch sur cuda, 0 aller-retour CPU) + `train_koth_gpu.py`
(3 gros cerveaux MLP 3x512 = 533k params/cerveau, PPO en MINI-LOTS pour memoire bornee). 1ere version OOM (PPO full-batch sur 32768 envs) -> corrige par mini-lots.
RESULTAT MESURE : 3090 a **100% / ~416W (sur 420) / 7,4 Go** pendant l'entrainement. 32768 envs x3 camps = **98 304 batailles en parallele**, ~61 000 tr/s.
=> Passage de 10W qui dorment a 416W qui travaillent. Le GPU est enfin le MOTEUR (compute-bound, pas memory-bound : 7/24 Go -> grosse marge).
Ouvre : cerveaux bien plus gros (recurrents+attention), LIGUE/population de politiques, obs plus riches -> tout tient sur cette carte.
Note indexation : torch cuda:0 = 3090 (= nvidia-smi INDEX 1) ; nvidia-smi index 0 = GTX 1060 (bureau, ~14%). Toujours sonder `-i 1` pour la 3090.

## LIGUE (PSRO/PFSP) sur GPU — 2026-06-04 — le cycling est dompte

Build : `train_league_gpu.py` (learner=camp0 vs adversaires tires d'un VIVIER de snapshots figes ; PFSP : tire en priorite ceux qui battent le learner ;
photo du learner -> vivier tous les 15 it) + asymetrie de spawn ajoutee a `koth_gpu.py` (spawn_jit) pour rendre les parties DECISIVES.
Run 400 it, 16384 envs, net 3x512, sur 3090 a 99%/414W, ~115 000 tr/s.
RESULTAT : l'asymetrie tue le match nul (nuls ~0.00, decidees 1.00). learner_vs_pool : 0.37 -> 0.99 -> se STABILISE a ~0.94-0.96
pendant que le vivier grossit (2 -> 19+ versions). => le learner reste DOMINANT sur TOUTE son histoire, sans effondrement ni rotation de leadership.
CONTRASTE net avec sans-ligue (v1/v2/v3/obj : trainard a ~0, leadership qui tourne). => CYCLING DOMPTE, agent ROBUSTE.
Honnetete : metrique = winrate vs vivier PFSP-echantillonne (learner ameliore vs adversaires figes -> haut attendu) ; une vraie analyse d'exploitabilite (Nash) serait plus profonde, mais stable-haut + vivier croissant + zero effondrement = forte evidence.
Poids : `league_learner.pt`. C'est la base ROBUSTE pour la vitrine humain-vs-agents (un humain ne doit pas trouver d'exploit facile).

## B.1 — Memoire sous occlusion (GPU) — 2026-06-04 — RESULTAT NEGATIF instructif

`train_rec_gpu.py` (GRU vs FF, learner camp0 vs 2 adversaires figes ALEATOIRES, occlusion sight=45 ajoutee a koth_gpu). Run 300 it x2.
RESULTAT : FF (sans memoire) 0.99 win / 0.99 securise, GRU (memoire) 0.94 / 0.94, FF 2x plus rapide (188k vs 95k tr/s). => LA MEMOIRE N'AIDE PAS ICI.
POURQUOI : la tache ne REQUIERT pas de memoire. Adversaires figes aleatoires (pas de strategie coherente a anticiper) + ennemis VISIBLES pres de la colline (la ou ca se decide). Occlusion seule != memoire necessaire. Le GRU n'apporte rien et est plus dur a optimiser.
LECON (coherente avec toute la session) : un MECANISME ne montre sa valeur que si la TACHE le recompense (cf. la ligue avait besoin d'asymetrie ; la memoire a besoin d'une tache memoire-dependante, comme toy_mem 100/22 ou l'ennemi devait etre memorise). 
=> Pour prouver/utiliser la memoire : adversaires COHERENTS qui EXPLOITENT l'occlusion (flanc depuis l'angle mort) ou tache ou il faut predire un ennemi disparu. Sinon FF suffit.

## ▶ SYNC ARCHITECTE→BÂTISSEUR — ÉTAT ACTUEL (2026-06-04, fin de session)

**TL;DR session :** KotH 3 camps exploré → "problème des trois corps" trouvé (symétrie parfaite = indécis) → MOTEUR GPU bâti (3090 enfin utilisée) → LIGUE bâtie (PSRO, cycling dompté, agent robuste) → mémoire testée (B.1) = NÉGATIF (toy trop simple pour que la mémoire paie).

**Nouveaux fichiers (~/arma3-marl/) créés cette session :**
- Toys 3-camps (numpy/CPU) : `toy_koth3.py` (params tie_pen, sight/occ ajoutés ; expose info secured/occ), `toy_koth3v2.py` ; trainers `train_koth3.py` / `train_koth3v2.py` / `train_koth3v3.py` / `train_koth3_obj.py`.
- GPU-natif : `koth_gpu.py` (env KotH 3 camps 100% torch/cuda ; params spawn_jit, sight, occ) ; `train_koth_gpu.py` (3 gros cerveaux MLP, PPO MINI-LOTS `ppo_mb`) ; `train_league_gpu.py` (ligue PFSP) ; `train_rec_gpu.py` (GRU vs FF mémoire).
- Poids : `league_learner.pt` (cerveau ROBUSTE déployable), `kothgpu_{blu,opf,ind}.pt`, `koth3*_*.pt`.
- Logs : `logs_train/{koth3,koth3v2,koth3v3,koth3obj,koth3obj2,kothgpu,league,rec_mem,rec_ff}.log`.

**GOTCHAS TECHNIQUES (à connaître absolument) :**
- torch `cuda:0` = la RTX 3090 (= nvidia-smi **INDEX 1**) ; nvidia-smi index 0 = GTX 1060 (bureau). Sonder `nvidia-smi -i 1` pour la 3090.
- cuDNN DOIT être désactivé pour tout GRU : `torch.backends.cudnn.enabled = False` (sinon crash "cuDNN SM < 7.5" à cause de la 1060).
- PPO gros batch GPU : OOM si full-batch → PPO en MINI-LOTS (cf `ppo_mb`). Lancer avec `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- venv : `/home/younes/arma3-marl/.venv/bin/python` (torch 2.12 cu130). 3090 mesurée 100%/416W avec sim GPU-native (avant 0%/10W : la sim numpy-CPU était le goulot).

**RÉSULTATS-CLÉS :**
- 3-corps : KotH 3 camps PARFAITEMENT symétrique = structurellement indécis (soit standoff, soit cohue, jamais de vainqueur net). Cassé par l'asymétrie (`spawn_jit`) ou le vrai jeu.
- Ligue : learner bat ~0.94 de TOUT son vivier (28 versions figées), stable, zéro effondrement = cycling dompté. `league_learner.pt` = base robuste pour affronter l'humain.
- B.1 mémoire : FF 0.99 > GRU 0.94 → la mémoire n'aide PAS quand la tâche ne l'exige pas. LEÇON : un mécanisme (mémoire/attention/rôles) ne paie que si l'ENV le récompense ; le toy actuel plafonne.

**DIVISION MATÉRIELLE actée :** GPU = les CERVEAUX (apprentissage rapide sandbox + inférence temps réel) ; CPU = le MONDE = Arma (serveurs, jeu de l'humain). En Étape C, les deux tournent EN PARALLÈLE (deux horloges).

**DÉCISION OUVERTE (Younes tranche) :** Younes a choisi de MUSCLER LE CERVEAU (B profondeur + C ligue forte + E rôles) en sandbox AVANT de déployer. Mais B.1 montre que le toy est trop simple → soit (1) ENRICHIR le toy pour que la profondeur paie (flanc depuis angle mort → mémoire ; soin → médecin ; portées → sniper ; coordination → attention), soit (2) basculer à l'ÉTAPE C où la richesse est gratuite.

**POUR LE BÂTISSEUR — Étape C (NOTRE mission, PAS Sa-Matra qui est verrouillée + anti-cheat BattlEye + non éditable, incompatible avec notre pont = injection de code) :** bâtir "Harmattan KotH" — 3 factions, AO tournante, capture PAR PRÉSENCE (dégager les ennemis), économie scriptée (armes = assets base Arma, achats via arsenal), 3 ponts (1 canal/faction), serveur DÉDIÉ (lit les cmd EN DIRECT ; un humain CLIENT ne gèle pas l'index — seul un client-HÔTE gèle). 100% privé (Tailscale, headless), Younes se branche en GTX 1060 comme 4e acteur.

## ÉTAPE C.1 + C.2 — Harmattan KotH 3 factions DANS Arma + déploiement du cerveau ligue — 2026-06-04

C.1 : `arma_env_koth.py` (étend arma_env_selfplay 2->3 factions : BLUFOR west / OPFOR east / Indépendant resistance à 120 deg, toutes hostiles ; CAPTURE PAR PRÉSENCE = barre cap_prog qui n'avance que si une faction DOMINE la zone -> il faut dégager les autres ; AO qui TOURNE côté Python via objx/objy ; obs/camp=10, ennemi=union des 2 autres ; step(a0,a1,a2)). Validé sur serveur 0 live : reset obs (2,3,10)x3, 3 factions x3 vivants, pas/capture/rotation OK. IMPORTANT obs : repère = la COLLINE (objx/objy), PAS la base de départ (corrigé pour matcher koth_gpu/league).
C.2 : `deploy_koth.py` charge `league_learner.pt` (Net 3x512 de train_koth_gpu) et pilote les 3 factions en temps réel. Résultat : zéro-shot faible PUIS, avec calibration de tempo (move 20->40 car Arma close ~0.07/pas vs ~0.14 dans le toy), le cerveau AVANCE+SUPPRIME et **CAPTURE** (1 capture en 26 pas). Histogramme actions : AVANCER 192 / SUPPR 174 / COUVERT 99 / HOLD 3.
ÉCART SIM->RÉEL quantifié : tempo Arma ~2x plus lent (units COMBAT + marche réelle) -> le cerveau (calé tempo toy) tient/tire avant d'arriver. CORRECTIF = C.3 fine-tune dans Arma (boucle déjà validée en B1 : pertes baissent, succès monte) OU recalibrer move/step_wait.
RESTE : C.3 fine-tune Arma (train multi-serveur depuis league_learner), C.4 humain (1060) se connecte, C.5 économie + boucle d'adaptation. Serveurs : 12 actifs (idle), serveur z = mpmissions/HarmattanBridge{z}.Altis + logs/server{z}.out. Pont = ArmaBridge(mission=..., log=...).

## ÉTAPE C.3 — FINE-TUNE dans Arma (ecart sim->reel ferme) — 2026-06-04

`train_koth_finetune.py` : MultiKoth (12 serveurs x ArmaEnvKoth 3 factions, threads) + cerveau PARTAGE warm-starte depuis league_learner.pt, PPO dans le vrai jeu, move=36 (tempo calibre). Run 40 it, 12 serveurs x3 envs (~324 unites), 8.1 tr/s.
RESULTAT : captures 0 (cerveau brut it0) -> 20-26/iteration (fin) ; 510 captures totales ; a la fin quasi toutes les decidees = captures. => ecart sim->reel FERME, le cerveau prend l'objectif de facon fiable dans Arma. Cerveau -> `koth_finetuned.pt` (le brain DEPLOYABLE final).
RESTE Etape C : C.4 (humain 1060 se connecte — besoin d'un creneau jouable dans la mission + Younes present) ; C.5 (economie/achats + boucle d'adaptation jouer->apprendre->rafraichir).

## ÉTAPE C.4 — ARÈNE LIVE prête (humain dans la boucle) — 2026-06-04

`live_arena_koth.py` : charge `koth_finetuned.pt`, fait tourner UNE bataille KotH 3 factions en boucle infinie sur serveur 0 (100.66.136.67:2402), auto-reset. Téléporte tout joueur humain sur la colline (côté BLU, ~130m nord) s'il est à >700m. Lancé en nohup -> logs_train/live_arena.log. Validé : bataille tourne, captures arrivent.
CONNEXION (Younes) : sur la workstation (écran/bureau ou via NoMachine), lancer Arma 3 (client, 1060 pour le rendu) -> Multijoueur -> Connexion directe -> 127.0.0.1 (ou 100.66.136.67) port 2402 -> rejoindre le créneau BLUFOR (mission.sqm a 1 unité isPlayable=1 West). Spawn téléporté sur la colline ; allié de HMT_BLU, hostile à OPF/IND. CPU=serveur Arma, 3090=cerveaux, 1060=rendu client = les 3 puces utilisées.
Relancer l'arène si besoin : cd ~/arma3-marl && .venv/bin/python -u live_arena_koth.py. RESTE C.5 : economie/achats + boucle adaptation (jouer->apprendre->rafraichir).

## ÉTAPE C.4 — MUR ARCHITECTURAL + spec PONT-SOCKET (pour le batisseur) — 2026-06-04

VERDICT prouve ce soir : le pont-FICHIER et le mode SOLO sont INCOMPATIBLES.
- Dedie (arma3server natif Linux) : relit les cmd_N.sqf en direct -> pont OK. MAIS Steam refuse le ticket du joueur (meme compte + meme machine : "owner 0 / invalid ticket"). Confirme via logs/server0.out.
- Solo/editeur (client Proton/Windows) : pas d'auth Steam, MAIS Arma GELE l'index des fichiers de la mission au lancement -> l'actuateur (preprocessFile) ne voit JAMAIS les cmd ajoutes apres (prouve : cmd_3.sqf present dans le dossier, "cmd_3 not found" en boucle). C'est le "client-host freeze".

DECISION user : (a) il fera un 2e compte Steam -> jouer sur le DEDIE (pont-fichier deja prouve, l'arene capture). (b) en parallele, batir le PONT-SOCKET (independant de Steam).

SPEC PONT-SOCKET (a coder par le batisseur) :
- Probleme : contourner le gel d'index en SOLO. Le client est Proton/WINDOWS -> il faut une EXTENSION DLL Windows (callExtension charge name_x64.DLL cote client), PAS un .so (le .so ne marche que pour le dedie Linux).
- mingw ABSENT sur la workstation -> installer : sudo apt install gcc-mingw-w64-x86-64.
- Extension hmt_ext_x64.dll : RVExtension(char* out,int size,const char* fn) qui lit un fichier au niveau OS (fopen) -> contourne le gel d'index d'Arma. fn = numero de cmd. Lire <BRIDGE>/cmd_<fn>.sqf et renvoyer le contenu (gerer >10240 octets par chunks si besoin).
- Mapping Wine : la DLL tourne sous Proton -> chemins Windows. Utiliser un chemin que Wine mappe vers le Linux ou Python ecrit (ex : Z:\\tmp\\hmt_bridge\\ = /tmp/hmt_bridge cote Linux ; Z: = / par defaut sous Wine). Placer la DLL dans la racine Arma client (Steam/steamapps/common/Arma 3/).
- Actuateur (cote SQF) : remplacer preprocessFileLineNumbers par : _code = "hmt_ext" callExtension str _next; if (_code != "") then {RECV; call compile _code; HMT_n=_next}. Obs OUT inchange (diag_log -> RPT, marche en solo).
- Python : ecrire les cmd dans /tmp/hmt_bridge/ (absolu), lire le RPT solo (AppData/Local/Arma 3/Arma3_x64_*.rpt, le plus recent). Fichiers prets : arma_env_koth.py, live_arena_sp.py (a repointer sur /tmp/hmt_bridge), koth_finetuned.pt (cerveau).
- Cote DEDIE (natif Linux) : pas besoin de DLL, le pont-fichier marche ; un .so optionnel ferait pareil.
NOTE handicap ce soir : bug ENOSPC sur le temp local du Mac (architecte) -> commandes ssh souvent avortees ; le batisseur (local) n'a pas ce souci.

---

## ÉTAPE C.4 — PONT-SOCKET : code écrit (à compiler+tester) — 2026-06-05 (bâtisseur)

Implémentation de la voie (b) du mur C.4 (indépendante de Steam), d'après la spec du soir précédent.
Tout en ADDITIF dans `~/arma3-marl/socket_bridge/` (la voie dédié + les serveurs en cours intacts).
- `hmt_ext_x64.c` : extension Arma Win64 (sous Proton). `RVExtension(out,size,fn)` fait `fopen` de
  `Z:\tmp\hmt_bridge\cmd_<fn>.sqf` (Wine Z:=/ → /tmp/hmt_bridge) et renvoie le SQF (ou "" si absent).
  Contourne le gel d'index. Garde-fou __TOOBIG__ si > ~10240 o. Chemin surchargeable `HMT_BRIDGE_WIN`.
- `build_ext.sh` : compile (x86_64-w64-mingw32-gcc -shared) + pose la DLL dans la racine client
  (`…/common/Arma 3/`) + crée /tmp/hmt_bridge.
- `harmattan_actuator_ext.sqf` : actuateur variante — `"hmt_ext" callExtension (str _next)` au lieu de
  preprocessFileLineNumbers ; OUT (diag_log→RPT) inchangé ; log `HARMATTAN_EXT version=...` au démarrage.
- `live_arena_sp_socket.py` : copie de live_arena_sp.py avec `env.b.bridge=/tmp/hmt_bridge`.
- `README-SOCKET.md` : procédure (3 actions Younes) + critères de preuve (RPT) + réserves.

RESTE (besoin de Younes) : (1) `sudo apt install gcc-mingw-w64-x86-64` ; (2) `bash build_ext.sh` ;
(3) charger l'actuateur_ext dans l'init de la mission cliente HarmattanKoth ; puis test en jeu.
Réserves au 1er test : mapping Wine Z:→/ à confirmer, chargement DLL sous Proton, BE inactif en solo (OK).
En parallèle, route (a) = 2e compte Steam (action Younes) reste la voie rapide vers le dédié.
NB : mingw ABSENT au moment d'écrire ; DLL pas encore compilée ni testée en jeu.

---

## ÉTAPE C.4 — PONT-SOCKET TESTÉ ET FONCTIONNEL : human-in-the-loop OK — 2026-06-05 (bâtisseur)

**LE MUR EST TOMBÉ.** Test en jeu réussi avec Younes.
- mingw installé (`gcc-mingw-w64-x86-64`), DLL compilée (`build_ext.sh`), posée dans la racine client.
  Arma la charge bien : RPT « CallExtension loaded: hmt_ext (...) [hmt_ext 1.0 ...] ». RVExtension/Version exportés OK.
- **BUG initial + FIX CLÉ (à retenir) :** `Z:\tmp\hmt_bridge` ne marchait PAS — Proton enferme le jeu dans un
  conteneur (pressure-vessel) où `/tmp` est ISOLÉ du `/tmp` hôte. Les cmd écrites par Python n'étaient pas vues.
  FIX = passer par **`C:\hmt_bridge` = `…/compatdata/107410/pfx/drive_c/hmt_bridge`** (drive_c = partagé
  host↔conteneur à coup sûr). Recompilé (DEFAULT_BRIDGE="C:\\hmt_bridge"), Python repointé. → **`HARMATTAN_RECV`
  qui défile** = ordres reçus en SOLO. Mur du « gel d'index » contourné, sans Steam.
- Joueur : spawn en plein sur la colline au milieu de 3 factions hostiles → **mort immédiate**. Pas de respawn
  dans la mission → ajout d'un bloc **invulnérabilité** dans l'init.sqf client (`player allowDamage false; setDamage 0`).
  Younes a alors joué AU MILIEU de la bataille, invulnérable.
- **Stress test 50/faction = 150 agents** : ÇA TOURNE (spawn ~15-20s, FPS bas) mais **trop lourd** (cerveau calé
  3v3 + Arma sature). Verdict Younes : « le POC fonctionne ». → caler un **sweet-spot filmable ~15-25/faction**.
- Aussi : resync pont fiabilisée (`arma_bridge._last_recv` reset sur « HARMATTAN_ACTUATOR » au lieu de « ...boucle »),
  écouteur blindé contre TimeoutError (ne crash plus en cours de bataille).
- Fichiers : `socket_bridge/{hmt_ext_x64.c, .dll, build_ext.sh, harmattan_actuator_ext.sqf, README-SOCKET.md}`,
  `live_arena_sp_socket.py`, init.sqf de la mission cliente (charge actuator_ext + invuln).
=> **C.4 (human-in-the-loop) = RÉSOLU.** Reste : choisir le nb d'agents filmable, tourner le clip ; C.5 (économie).

---

## ÉTAPE C.5 — brique ÉCONOMIE/ARSENAL + respawn (vraie mission KOTH solo) — 2026-06-05 (bâtisseur)

User : « une vraie mission comme KOTH de Sa-Matra », **solo + agents**, ajouter l'**arsenal/économie**.
Rappel acté : Sa-Matra réelle = verrouillée/BattlEye/non-éditable → on bâtit la NÔTRE (Harmattan KOTH), même esprit.
v1 livrée (additif, mission cliente `HarmattanKoth.Altis`, copiée aussi dans `…/common/Arma 3/MPMissions/`) :
- `description.ext` : **respawn = "BASE"** (delay 4) → ⚠️ le respawn Arma n'opère qu'en **multijoueur** : héberger en **Multijoueur→LAN**, PAS « Preview » SP. Socket OK en LAN (BE inactif).
- `harmattan_economy.sqf` : **revenu** +1/s (vie) / +5/s **dans la zone** (HMT_OBJ, tenir la colline rapporte) ; **action Arsenal** (molette) coût 200 pts → `BIS_fnc_arsenal` ; HUD `hintSilent` ; protection de spawn 6 s ; ré-applique tout sur EH "Respawn". `respawn_west` créé par init.
- init.sqf rebranché : actuateur_ext + heartbeat + marqueur respawn + chargement économie ; **bloc invuln permanent retiré**.
- Couplage : `arma_env_koth._spawn_sqf` modifié → reset **épargne le joueur** (`if !isPlayer`) ; `live_arena_sp_socket.py` ne **téléporte plus** le joueur et **pousse `HMT_OBJ=[ox,oy]`** (pour le bonus de zone). Arène réglée **n=20/faction = 60 agents** (jouable, après le stress 150).
À TESTER (pas-à-pas) : 1) shell SEUL en LAN (sans agents) → points montent, arsenal s'ouvre, mort→respawn ; 2) puis lancer l'arène (agents). Non testé en jeu au moment d'écrire.

---

## ÉTAPE A (C.5 côté sim) — ÉCONOMIE/NIVEAUX/ÉQUIPEMENT scriptés, validés à 600k — 2026-06-05 (bâtisseur)

User : KOTH Sa-Matra-like, 35 agents/camp, **économie + niveaux par agent + équipement** ; deadline lundi abandonnée (le projet sert à bâtir l'expertise). Plan acté : A) mécaniques scriptées validées au sim → B) hybride RL vs scriptés → C) économie pilotée RL.
**Implémenté dans `koth_gpu.py`** (additif, RL intact) : état/agent `level` (XP), `money`, `tier` (acheté) ; multiplicateurs **dégâts↑ (niveau+tier), portée↑ (tier), armure↑ (tier défenseur)** ; gains = combat (k_xp/k_money × dégâts) + tenue de zone (zone_money) + **salaire de base/agent vivant** (base_xp/base_money) ; montée niveau + **auto-achat tier** aux paliers. Politique scriptée vectorisée `scripted_acts()` (couvert si blessé / supprimer si ennemi proche / sinon avancer). Réglages : max_steps 120, secure_r 20, cap_need 6, rot_period 14, xp_step 4, tier_cost 8, max_level 5, max_tier 4. Script `run_scripted_koth.py`. Backups : `koth_gpu.py.bak`, `.bak2`.
**Run 600k (5714 envs × 3 × 35 = 599 970 agents, 300 pas) :** stable, ~191k tr/s, **3090 0,6 Go** (scripté = pas de réseau = léger). niveau 1→~2.6, tier ~1.6, argent équilibre ~5.7, **décisif 0.98**, matchs ~43 pas. **Snowball NEUTRE** (vainqueur niv = perdant niv ~3.3) → la progression ne décide pas encore l'issue (le **salaire de base symétrique domine**). LEVER pour rendre l'économie STRATÉGIQUE : baisser base_money/base_xp, monter k_money/zone_money → le camp qui combat/tient mieux pulle ahead (= ce que le RL exploitera en B). Reste : régler ce dial, puis étape B (RL vs scriptés, métrique propre = winrate RL-vs-scripté).

**Dial testé (05/06) :** avec scriptés SYMÉTRIQUES, impossible de créer un snowball (clones → gains identiques → progression identique). La force est câblée (tier4 = ×2 dégâts, ×0.6 encaissé) mais ne se révèle qu'avec un comportement ASYMÉTRIQUE → c'est l'étape B/le RL.
**Étape B faite (05/06)** (`train_vs_scripted.py`, RL camp0 vs scriptés 1,2, env-économie, envs 8192 n12 mb 65536, 150 it, 3090 99%/14.7Go) : **pipeline OK**, mais **RL_winrate saturé ~0.97-1.00 DÈS it10, plat** → la baseline scriptée est **trop faible** = métrique non informative sur la profondeur (même leçon récurrente : un test n'enseigne que s'il est dur). Modèle `vs_scripted_learner.pt`. **Conclusion : pour mesurer la profondeur, il faut un adversaire à niveau → self-play/LIGUE sur le jeu-économie (B2, endgame).** ⚠️ rappel OOM : n=12 quadruple la mémoire vs n=3 → garder envs ≤ ~8192 / mb ≤ 65536 au niveau réseau 512×3.

**Ligue sur le jeu-économie (05/06, `league_econ_learner.pt`, envs 8192 n12)** : learner_vs_pool pic ~0.86 → se pose à **~0.63**, decid 0.99. Comparaison 3 régimes : plat sans-éco ~0.95 (pauvre/transitif) · enrichi sans-éco ~0.50 (cyclique) · **+économie ~0.63 = sweet spot** (échelle de skill apprenable ET diversité, décisif). L'économie donne une **colonne stratégique apprenable**.
**PREUVE économie (`eval_econ_proof.py`, 05/06)** : P1 corrélation — vainqueur tier 1.41 vs perdant 0.01 (mais confondu : gagner→survivre→s'équiper). P2 CAUSALITÉ (même cerveau partout, camp0 tier+3) — winrate **0.388 vs 0.33 hasard** → **économie CAUSALE prouvée, MAIS effet FAIBLE** (un gros head-start ne donne que +5-6 pts ; le match reste surtout décidé par positionnement/capture). LEVER pour rendre l'éco *déterminante* : monter `tier_dmg`/`tier_armor` jusqu'à ce que P2(tier+3)→~0.5-0.6.
**CALIBRÉ 05/06 (sweep via P2, `eval_econ_proof.py` avec args multiplicateurs)** : P2(tier+3) = 0.39 (0.25/0.10) → 0.56 (**0.35/0.13/0.25**) → 0.82 (0.5/0.18) → 0.99 (0.9/0.25). **Verrouillé dans koth_gpu : lvl_dmg 0.20, tier_dmg 0.35, tier_armor 0.13, tier_range 0.25** → P2=0.56 = économie « déterminante (~moitié des matchs) sans écraser ». **Réentraînement ligue sur éco renforcée (`league_econ2`)** : learner_vs_pool ~0.47 (un peu plus non-transitif), decid 0.99. Re-preuve : P2=0.50 (causal OK), mais **P3 (nouveau vs ancien) = nouveau PERD (0.185) + tier égal 3.95≈3.97** → **les deux MAXENT le tier = PAS de rareté → l'économie n'est pas un différenciateur → rien à apprendre.** Cause : le **salaire de base** garantissait la progression → tout le monde maxe. **MÊME LEÇON : un mécanisme ne s'apprend que si l'env en fait un VRAI CHOIX (rareté).**

**FIX RARETÉ validé (05/06)** : **couper le salaire de base** (base_money=base_xp=0) + revenu = **présence dans l'AO** (nouveau rayon `income_r=80`, plus large que la capture secure_r=20) **+ combat**, XP aussi via l'AO (`zone_xp`). Résultat scripté (run_scripted, métrique passée au TIER) : **tier.moy ~1.26 (NE SATURE PLUS = rareté)**, niveaux montent (~2.26, mérités), **tier VAINQUEUR 2.35 vs PERDANT 1.11 (+1.24) = DIFFÉRENCIATION positive** (le revenu couplé à la tenue de l'AO → tenir=gagner=s'enrichir). **Défauts koth_gpu verrouillés** : base_money 0, base_xp 0, k_money 15, k_xp 10, zone_money 3, zone_xp 1.5, income_r 80. **Réentraînement `league_econ3` sur l'éco-rareté + P3 (05/06) — RÉSULTAT MITIGÉ HONNÊTE :** P2=0.55 (éco causale en isolation, OK). MAIS P1 : le RL entraîné gagne 100% vs scriptés **avec MOINS de tier** (2.36 < 3.27) → **le skill écrase l'économie**. P3 : `econ3` **PERD** contre `econ2` (0.088) et **les deux trained MAXENT le tier (3.97≈3.96)**. → DEUX constats : (1) la rareté ne bride que les agents PASSIFS ; les **compétents poussent l'AO/se battent → gagnent assez → maxent tous → l'économie n'est PAS un différenciateur entre bons joueurs** (s'équiper = sous-produit gratuit de bien jouer, pas une décision) ; (2) **la ligue n'avance pas de façon monotone** (econ3 < econ2 = non-transitif/instable). **CONCLUSION : l'économie telle que conçue = mécanique RÉELLE mais MINEURE.** Pour la rendre centrale il faut un **vrai arbitrage/coût d'opportunité** (revenu zéro-somme à dénier à l'ennemi, ou s'équiper exige de quitter la ligne, ou combattre XOR farmer). **Décision en attente : (a) refaire l'éco avec arbitrage, (b) bifurquer vers le déploiement Arma (concret), (c) régler l'instabilité ligue d'abord.** Modèles : league_econ/econ2/econ3, vs_scripted (tous _learner.pt).

## SANDBOX GÉOPOLITIQUE — `geo_gpu.py` v1 VIVANT (05/06)
Nouvelle direction (le NORD, cf fiche mémoire) : N pays sur un anneau de régions, territoire→TRÉSOR (∝ régions)→CONCENTRÉ sur la pointe d'attaque→percée. Combat de frontière abstrait (le + fort pousse, 2 phases even/odd ; conquérir = surextension). Capitale tombée = pays éliminé. Tout scripté/GPU. `run_geo.py`.
**v0 (revenu uniforme à toutes les régions) = FIGÉ** (écarts relatifs annulés → 0 percée). **v1 (trésor concentré sur le front le + fort) = DYNAMIQUE** : guerres décisives ~33 pas, **part vainqueur ~0.65, ~1.68 pays éliminés/2, leader inst ~0.46 (>0.33)**, ~355k pas/s. → snowball géopolitique (territoire→force→conquête) PRÉSENT mais **tempéré par la dynamique 3-corps** (pas toujours conquête totale). Réglages : income 0.6, atk_thresh 1.1, push 0.5, arc 4, 3 pays, max_steps 80.
**PROCHAIN : doctrines par pays** (égaliseur/amplificateur/zéro-somme → quelle philosophie domine) ; puis sweep régimes (income/nb pays/létalité → carte de régimes) ; puis RL du cerveau stratégique (hiérarchique).

**v2 KOTH CENTRAL (05/06, idée Younes « le KOTH au centre = verrou de la vie nationale »)** : région-pivot reliée à la « porte » de chaque pays (cedges), neutre au départ (garnison 6.0), `center_bonus` de revenu au détenteur ; la pointe d'attaque peut viser le centre. Runner enrichi : suivi rotation (flips/pas), **1er-preneur→victoire (métrique CAUSALE ; « détenteur final→victoire »=0.95 est TAUTOLOGIQUE, le vainqueur finit par tout tenir)**.
**Résultat v2 (bonus 5.0)** : guerres **9 pas** (vs 33 en v1), **élim 2.00 systématique** (guerre totale), vainq 0.78, centre tenu 95 %, rotation 0.43 flip/pas. **SWEEP center_bonus 0→12 (4096 envs, ~50-113k guerres/point) — DEUX LOIS ÉMERGENTES :**
1. **Effet TOPOLOGIE ≠ effet VALEUR** : à bonus **0**, le simple fait qu'un carrefour central EXISTE rend déjà la guerre totale (élim 1.68→1.99, durée 33→15.6). Le carrefour qui connecte tout le monde détruit le tampon de l'anneau — la géographie compte avant la richesse.
2. **LE CALICE EMPOISONNÉ** : 1er-preneur→victoire est **NON-MONOTONE** — 0.47 (bonus 0) → pic **0.57 (bonus 1)** → **0.43 (bonus 12, SOUS la baseline)**. Un prix modéré = atout réel ; un prix énorme = piège : prendre le centre en premier concentre l'hostilité des deux autres + surextension → l'avantage se retourne. (Toujours > hasard 0.33, donc malédiction *relative*.) Durée 15.6→7.1 et vainq 0.73→0.80 montent avec le bonus = monde de plus en plus blitz/winner-take-all.
→ Réponse à « comment le modèle s'adapte à cette contrainte forte » : les scriptés ne *stratégisent* pas, mais le SYSTÈME s'adapte structurellement (blitz, rotation, malédiction du prix). **Question RL ouverte : un cerveau appris découvrirait-il le *tertius gaudens* (laisser les deux autres s'épuiser sur le centre, frapper ensuite) ?**

**v3 « DEUX COLLINES » (05/06, règle Younes « une colline par pays, 2 collines pour gagner »)** : centre RETIRÉ ; 1 colline/pays (idx c·arc+1, ≠ capitale, asymétrie assumée) ; **VICTOIRE = tenir 2 collines simultanément pendant `hold_T` pas** (anti victoire-raid) ; capitale = MORT (survie ≠ victoire, inchangé). `run_geo.py` v3 : type de fin (2COLL/ÉLIM/timeout), durée/type, config gagnante (sa-colline+1 vs 2 étrangères), flips. Smoke 4096 envs : vivant, ~284k tr/s.
**SWEEP `hold_T` 1→20 (4096 envs, 41-79k guerres/point) — TROISIÈME LOI ÉMERGENTE, « l'horloge politique vs l'horloge militaire »** : hold 1 → **93 % des guerres finissent par victoire politique (2COLL), 0 % d'annihilation, vainq terr 0.46** (le perdant survit avec du territoire) ; hold 5 → régime mixte (2COLL 0.47 / ÉLIM 0.37) ; hold 20 → **la victoire politique devient lettre morte (6 %) et la guerre redevient totale (ÉLIM 77 %, vainq terr 0.66)**. → *Plus la victoire est reconnue vite, moins la guerre est destructrice* : si l'horloge politique est plus lente que l'horloge militaire (la capitale tombe avant que la tenue soit validée), la condition de victoire n'arrête plus rien. Les timeouts (~16 %) réapparaissent = conflits gelés possibles (le monde-centre v2 n'en avait aucun).
**INVARIANT frappant : sa-colline = 1.00 partout** — le vainqueur tient TOUJOURS sa propre colline ; personne ne gagne jamais par 2 collines étrangères. Le seul chemin gagnant observé = **consolidation intérieure + projection** ; la victoire politique est une *terminaison anticipée* de la même trajectoire militaire (durées 2COLL ≈ ÉLIM, ~14-15 pas), pas un chemin alternatif. ⚠️ Limites honnêtes : scriptés sans *visée* des collines (prises incidemment par l'avancée du front) ; placement de colline asymétrique sur l'anneau. Un RL qui *vise* les collines pourrait ouvrir le chemin « 2 étrangères » — à tester.
**PROCHAIN : les 3 DOCTRINES par pays (égaliseur/amplificateur/zéro-somme) DANS cette arène v3** (la condition de victoire est posée, on mesure les philosophies dedans) ; puis tertius gaudens RL.

## DOCTRINES D'ALLOCATION — EXPÉRIENCE COMPLÈTE (05/06, arène v3, hold 5)
Doctrine = politique d'ALLOCATION du trésor (revenu IDENTIQUE pour tous = income×terr → on isole la philosophie, pas l'avantage numérique) : **A=AMPLIFICATEUR** (tout sur SA pointe la + forte — renforcer le succès), **E=ÉGALISEUR** (uniforme sur tout le front), **Z=ZÉRO-SOMME/DÉNI** (tout face à la + grosse force ennemie — réactif, émousser la pointe adverse). `geo_gpu.py` param `doctrines="AEZ"`, runner `--doctrines`, winrate sur fins DÉCISIVES (timeouts=nuls). ⚠️ Z = interprétation contre-force du zéro-somme (le déni de REVENU, autre variante, reste à tester).
**Protocole (21 runs ≈ 41-118k guerres chacun)** : sanity AAA/EEE/ZZZ (~0.333 partout ✅ arène équitable) ; AEZ ×3 rotations (invariant ✅) ; **matrice d'invasion complète ×3 positions d'envahisseur** (invariante en position d'envahisseur ✅).
**MATRICE D'INVASION (winrate envahisseur, équité=0.33)** : A→monde-E **0.757** ; A→monde-Z **0.523** ; E→monde-A **0.062** ; E→monde-Z 0.310 ; Z→monde-A **0.150** ; Z→monde-E 0.205. Mix AEZ : A 0.50 / E 0.34 / Z 0.16.
**QUATRIÈME LOI — « renforcer le succès, pas l'échec » : A est STRICTEMENT DOMINANTE et seule stratégie évolutionnairement stable** (elle envahit tout, rien ne l'envahit). La doctrine RÉACTIVE Z est la pire PARTOUT (jamais au-dessus de l'équité) : qui ne fait que répondre à la menace cède l'initiative et subit. E tient sa part (0.34 en mix) mais ne conquiert jamais. = maxime militaire classique redécouverte empiriquement par le sandbox.
**CARACTÈRE DES MONDES (effet de composition)** : monde-E = lent et le moins décisif (EEE : décisives 0.67, guerres rares = conflits gelés) ; monde-Z = HYPER-décisif et rapide (ZZZ : 1.00, durée ~10, ~117k guerres) ; monde-A intermédiaire (0.84). La diversité doctrinale (mix) rend le monde plus décisif que AAA.
**EFFET « ÉTAT-TAMPON » (sous-trouvaille)** : l'asymétrie est entre les deux RÉSIDENTS, pas l'envahisseur — selon le CÔTÉ où l'on siège par rapport à l'envahisseur, le sort diverge ×3-7 (ex. A→EE : E 0.18 vs 0.06 ; E→ZZ : Z 0.49 vs 0.20 !). Une doctrine faible ne gagne pas mais REDISTRIBUE la victoire entre les autres. ⚠️ possiblement amplifié par l'artefact d'asymétrie des collines (offset +1) — à vérifier avant d'en faire une loi.
**PROCHAIN (discipline « ça marche → consolider ») : 4 lois en main (topologie, calice empoisonné, horloge politique, renforcer-le-succès) → CONSOLIDER : git + rédaction note de recherche (standard preuve/track-record), AVANT toute nouvelle expansion (variante Z=déni de revenu, RL tertius gaudens, sweep régimes).** *(Consolidation différée : Younes a commandé l'expérience CIVILS — dette notée.)*

## v4 « CIVILS » — POPULATION CIVILE, ÉCONOMIE ENDOGÈNE (05/06, commande Younes)
Demande : carte en 3, agents CIVILS non-militaires, système éco+doctrinal complet, 1 KOTH/pays → = arène v3 + **pop civile par région**. 3 micro-règles assumées (⚠️ scripté → on étudie les dynamiques ÉMERGENTES de population, pas un « comportement » au sens appris) : **PRODUIRE** (revenu = income_pp 0.05 × pop des régions tenues, calibré ≈ ancienne rente ; pop occupée produit pour l'occupant = extraction assumée, pas de loyauté) ; **FUIR** (fraction ∝ menace/(menace+force locale), civ_flee 0.5, vers le voisin du même camp le moins menacé, encerclé=piégé ; les civils voient les pointes massées post-allocation) ; **MOURIR** (civ_loss 0.2 à chaque changement de mains). Init : 10/région, 20 capitale (monde 150). Métriques runner : morts/pop0, réfugiés (déplacements cumulés/pop0), survivants, part de pop mondiale contrôlée par le vainqueur.
**CINQUIÈME LOI — « la guerre brûle son propre carburant »** : l'économie endogène fait s'EFFONDRER l'annihilation (AAA : ÉLIM 0.37→0.09 ; EEE 0.30→0.17 ; ZZZ 0.40→0.31), guerres + longues, - décisives → les morts/exodes détruisent la base fiscale AVANT que la conquête totale soit payable ; la victoire politique (2 collines) devient la fin décisive dominante.
**SIXIÈME LOI — le coût civil est une propriété du MONDE doctrinal** : monde-E = 2× plus humain (morts 0.179) que monde-A (0.367, + gros exodes 0.86) ; monde-Z intermédiaire rapide (0.299, exodes min 0.62). La doctrine qui PERD les guerres (E) est celle qui protège les populations ; la dominante (A) est la + meurtrière. **Arbitrage puissance/humanité mesurable.**
**La hiérarchie doctrinale est AMPLIFIÉE par l'économie endogène (mix AEZ ×3 rotations, invariant)** : A 0.50→**0.58**, E 0.34→0.37, Z 0.16→**0.05 (quasi-éteint)**. Le réactif ne capture jamais de population (pas de nouvelle base fiscale) ; le conquérant saisit le tissu fiscal intact (vainq contrôle 0.77 de la pop restante — PAS Pyrrhus : la conquête paie en population). Le défensif préserve sa pop = son économie (léger mieux).
**Sondage « comportement face aux menaces » (AAA, 18k guerres)** : les FRONTIÈRES SE VIDENT (bord 10→1.67/région), l'intérieur concentre tout (capitale 18.05, collines 10.28 ; capitale = 57 % de la pop mondiale finale) = concentration intérieure/réfugiés émergents.
**CIVILS EN DEEP LEARNING — FAIT (05/06, `train_civ.py`, `civ_learner.pt`)** — politique neuronale partagée par région (obs locales 9 feat.), actions {rester, fuir-G, fuir-D} (quantum civ_flee), reward = -morts (survie pure, assumé), PPO avantage-partagé (région=échantillon, avantage d'env), monde AAA, 300 it/4096 envs (~8 min 3090). Hook `civ_policy` dans `geo_gpu.step()`. ⚠️ incident bénin tracé : probe a ré-exécuté l'entraînement via import (pas de garde __main__) → modèle final = 300 it ; garde posé depuis.
**RÉSULTAT : RL 0.190 morts vs règle scriptée 0.368 vs no-flee 0.450** (seed indépendante, 24k guerres) = **-48 % vs ma règle, mortalité ÷2.4 vs immobiles**.
**SEPTIÈME LOI — « fuir la géographie stratégique, pas la menace visible »** (probe comportemental, 11k guerres) : le RL fuit MOINS que la règle à TOUT niveau de menace visible (0.04 vs 0.11 à menace modérée ; 0.28 vs 0.33 à forte) MAIS **évacue PRÉVENTIVEMENT à t<3 quand la menace est nulle (0.13 vs 0.00)** et **vide les COLLINES (pop finale collines 9.3 % vs 32.1 % pour la règle ; capitale 70.8 % vs 57.2 %)**. Il a appris OÙ la guerre IRA (les prix stratégiques de la règle 2-collines), pas où l'armée EST — déplacement anticipatif ; et il laisse 2× plus de monde sur les bords CALMES (19.9 % vs 10.7 %) = il distingue lieux dangereux et menaces visibles. La règle-main réagit aux armées ; la politique apprise lit la carte.
**TRANSFERT ✅ (mondes jamais vus à l'entraînement)** : EEE 0.126<0.181, ZZZ 0.255<0.300, AEZ 0.236<0.365 → le comportement appris est STRUCTUREL (lié à la carte/règles), pas surajusté au monde-A.
## GÉO→ARMA — LA BOUCLE COMPLÈTE DANS LE VRAI MOTEUR (05/06 soir, commande Younes « teste sur Arma, 10 serveurs »)
`geo_arma.py` : 10 serveurs headless (multi_server.sh 10, ports 2402-3302) = **10 guerres géo en parallèle** (AEZ, hold 3, civils = `civ_learner.pt`). Chaque pas géo → la bataille de la **colline la + menacée** est résolue DANS Arma : KOTH 3 factions (BLU/OPF/IND = pays 0/1/2), **15 unités/faction = 45/bataille = 450 simultanées** (plafond CPU ~24 cœurs, charge ~25, pas géo ~107 s), cerveau `koth_finetuned.pt`, **handicap setDamage ∝ rapport de forces géo** (le faible spawne blessé), verdict = capture sinon contrôle cumulé → le vainqueur PREND la colline géo. **RÉSULTAT : 10/10 guerres finies en 20 min, 66 batailles Arma (68 % décidées en jeu à 45 unités vs ~10 % à 9 unités — la masse rend décisif), 27 verdicts de colline imposés par Arma, fins 9× politique/1× élimination, morts civils 0.18.** Boucle stratégique(GPU)→tactique(Arma)→stratégique FERMÉE.
**DÉCOUVERTE — un biais tactique microscopique se propage en hégémonie stratégique : Arma RENVERSE la hiérarchie des doctrines.** Baseline abstraite (mêmes guerres, même seed) : **A gagne 8/10**. Avec batailles Arma : **E (pays 1=OPFOR) gagne 10/10**. Test à égalité parfaite : OPFOR 15/15.
**ENQUÊTE SUR LA CAUSE (chronologie honnête)** : hypothèse 1 = armure CSAT → **RÉFUTÉE** (égalisation setUnitLoadout : uniforme d'un autre camp refusé silencieusement par le moteur ; puis égalisation radicale removeUniform/Vest/Headgear + même fusil MX pour tous : OPFOR gagne ENCORE 19/19 ⇒ pas le matériel). Vraie cause trouvée DANS NOTRE CODE : **artefact d'échelle de la formule de spawn** (`_bx=+(_a*6)-6, _by=+(_a-1)*7` : la file d'unités s'étire vers le nord-est en coordonnées MONDE quel que soit le camp ; à n=3 c'est ±12 m, à **n=15 c'est +78/+91 m → la file d'OPFOR (angle 210°, sud-ouest) pointe DROIT vers l'objectif**, son 15e soldat naît quasi dans la zone ⇒ victoire à la course de spawn, pas au combat). **FIX : spawn en cercle centré sur l'ancre** (`_r=4+0.6·A`, unités sur le cercle) dans arma_env_koth.py + `e.t[:]=0` après reset côté coupleur (les timers randomisés du reset() d'entraînement respawnaient des arènes en plein test). **Re-test après fix : le biais S'INVERSE (BLU 17/18, indécis 40 %)** ⇒ le spawn était le moteur principal, mais il reste un résidu — suspect : **le cerveau** (`koth_finetuned` affiné dans le monde au spawn biaisé, obs en coordonnées-monde → habitudes positionnelles « nord »). LEÇON DOUBLE : (a) la chasse aux biais un-par-un est sans fin → **neutralisation statistique par ROTATION pays↔faction** (guerre i : pays c → faction (c+i)%3), définitive quel que soit le biais résiduel ; (b) reste vrai et démontré : **un micro-avantage tactique (≈80 m de spawn), invisible à petite échelle, amplifié par la boucle stratégique colline→territoire→trésor→forces = sweep hégémonique 10/10** — le sim abstrait ne pouvait pas le voir. Test doctrines RELANCÉ avec rotation+égalisation+spawn fixé. Serveurs laissés UP.
**ARÈNE JOUEUR VUE EN PERSONNE (05/06 soir)** : Younes a joué la mission (Eden Preview HarmattanKoth, pilote `live_arena_sp_socket.py`, 57 agents 19/19/19, spawn corrigé en cercles, téléport manuel via console `player setPosATL [15000,16000,0]`) — « hyper impressionnant ». ⚠️ correction honnête plus tard dans la soirée : ce premier spectacle était l'IA VANILLA (pont mort) — voir bug ci-dessous. Procédure rodée : couper les serveurs headless avant (CPU), lancer le pilote, puis Preview ; le pilote re-scanne le RPT à chaque essai ; jeu en pause = « commande non reçue » (normal).

**BUG DU PONT SOLO RÉSOLU (05/06, 23h) — « l'exception SQF tueuse d'actuateur »** : toute la soirée, spawn OK puis 100 % de timeouts en boucle de combat. Fausses pistes éliminées dans l'ordre : pause du jeu, taille de payload (n=20→10 sans effet), désynchronisation de numérotation (réelle mais secondaire : l'actuateur recompte de 1 à chaque mission, Python numérote d'après RPT+fichiers accumulés sur 12h de session — produit le REJEU de cmd périmées au restart, les « respawns fantômes »). **ROOT CAUSE (preuve RPT)** : le pilote pousse `HMT_OBJ=[x,y]` (plat, pour l'économie joueur) → le `_dump_sqf` de l'env fait `forEach HMT_OBJ` en attendant des paires → « Error: Type Number, expected Array » → **l'exception dans `call compile` TUE la boucle while de l'actuateur** → silence définitif (les heartbeats, script séparé, survivent — c'était le marqueur). **TRIPLE FIX** : (1) actuateur immunisé — `[_code] spawn { call compile ... }` : un thread enfant par commande, une erreur ne tue plus la boucle ; (2) conflit de nom résolu — l'économie lit `HMT_OBJ_SP` (poussé par le pilote), l'env garde `HMT_OBJ` ; (3) `ArmaBridge.send` supprime son fichier cmd au timeout (plus d'orphelins → plus de rejeu/inflation). + `acc=1.0` par défaut dans l'arène joueur (vitesse normale) et n=10/faction. **VALIDÉ : « boucle 4..36+ » passent, cerveau aux commandes en solo, vu par Younes.** Procédure spectateur rodée : `setAccTime 1` + retrait HandleDamage (mortalité réelle) + `BIS_fnc_EGSpectator`. LEÇONS : tout `call compile` d'origine externe doit être isolé dans un thread enfant ; nettoyer cmd_* + RPT frais à chaque session ; les heartbeats d'un script tiers ≠ santé de l'actuateur.

## NUIT 05→06/06 — COUCHE OPÉRATIONNELLE : des agents qui MÈNENT UNE OPÉRATION (plan de nuit Younes « plus de profondeur, opération complexe »)
**Gate 0 (00h30)** : `git init` ✅ (commit e541e7c) + **bundle 26 Mo sur /mnt/archive/git/** — la dette de sauvegarde est morte.
**Architecture 3 étages POSÉE** : CHEF D'OPÉRATION (machine à phases, `op_arma.py` OperationRunner) → ESCOUADES (cerveau GELÉ koth_finetuned en micro, obs 10 par escouade relatives à SON objectif) → MOTEUR (ennemi scripté : garnison patrouille + QRF déclenchable). **Postures = biais de logits** sur le cerveau gelé (move/assault/suppress/hold — 4 comportements, zéro réentraînement). Partition = phases {ordres par escouade (objectif,posture), done_when conditionnel, contingences goto} + **journal de décisions JSONL** (chaque transition tracée avec sa raison — l'étage est né instrumenté). `run_op.py` = OPÉRATION HARMATTAN-1 : raid 5 phases (infiltration 2 axes → mise en place appui/crête → assaut sous suppression → consolidation vs QRF 8h → exfil LZ), contingences pertes 35-60 %/enlisement, succès = ennemi ≥70 % détruit + pertes ≤50 % + élément à la LZ. Variantes : plan A (appui d'abord) vs plan B (assaut direct).
**Leçons de mouvement (3 runs)** : (1) la micro `doMove` 22 m/pas ÉTRANGLE la marche (~10 m/min — invisible en KOTH à 140 m, mortel sur 400 m) → **FIX doctrinal : mouvement opérationnel ≠ action tactique** — posture move hors contact et >120 m = **waypoint de GROUPE** (l'IA marche en formation), le cerveau reprend la micro au contact ; étendu à assault hors contact >40 m (les derniers mètres en zone nettoyée). (2) **`setAccTime` est IGNORÉ sur serveur dédié** → tout tourne à 1× : géométrie comprimée (approches ~250 m) + budgets de phase ×2. (3) Rayons d'arrivée 70→90 m (critère médiane trop strict).
**RUN 3 = GO/NO-GO VALIDÉ (~00h45)** : INFILTRATION → contact (1 perte) → ASSAUT sous suppression → **GARNISON ANÉANTIE 8/8 pour 7 % de pertes amies**. Le cerveau gelé EXÉCUTE une opération multi-phases — pas juste un KOTH. Frictions résiduelles purement critères/derniers-mètres (réglées).
**WARGAMING — RÉSULTAT FINAL (60 opérations, 10 puis 16 serveurs, ~1h40 cumulées)** : PLAN A (appui d'abord) **23/30 (77 %)**, pertes 17.4 %, ennemis restants 0.77 | PLAN B (assaut direct) **23/30 (77 %)**, pertes 13.8 %, restants 0.53. **ÉGALITÉ PARFAITE au succès** ; résidu B (pertes -3.6 pts, destruction + complète) NON significatif à n=30. **Cas d'école statistique : série 1 (n=15/plan) « prouvait » B (67-80) ; série 2 « prouvait » A (87-73)** — régression vers la moyenne des deux côtés, une publication à n=15 aurait été fausse dans les deux sens. CONCLUSION PUBLIABLE : l'opération est ROBUSTE à la partition (77 % de succès quelle que soit la doctrine d'assaut) — le succès vient de la micro apprise + structure phases/contingences, pas du choix appui/direct. Modes d'échec distincts : A échoue par INDÉCISION (pertes faibles, garnison pas brisée), B par SAIGNÉE (36 %). Incidents consignés : (a) import de run_op sans garde __main__ a avalé l'argparse du wargame (MÊME bug que train_civ 12h avant → garde __main__ = règle de maison) ; (b) « l'amélioration » assaut-en-marche post-run-3 a fait défiler les escouades sous le feu (10 ops contaminées purgées, revert → JAMAIS d'optimisation sans re-validation) ; (c) parallélisme = la seule accélération sur dédié (16 serveurs validés, load 14.6, ~60 % CPU). Fichiers : wargame_op.py, wargame_results.jsonl, logs_train/wg_srv*.jsonl.

**PHASE 0 ESCALADE (06/06, directive Younes) — SPLIT CONDITIONNEL DES 60 OPS : deux découvertes qui REQUALIFIENT la conclusion.** (1) **La QRF n'a presque jamais été affrontée : 3 ops sur 60** — la contingence « assaut enlisé » (budget 120 pas + critère d'arrivée 85 m) faisait basculer vers EXFIL avant d'entrer en CONSOLIDATION, même garnison détruite. **Et les 3 fois où la QRF a été affrontée : 0/3 — 100 % léthale.** ⇒ la « parité robuste à 77 % » mesure en réalité **des raids qui ESQUIVENT la contre-attaque** — portée corrigée : « valable pour CE gabarit, dont la phase de consolidation est presque toujours contournée ». (2) **Paradoxe de l'infiltration saignée** : infil avec pertes → succès 36/42 (86 %) ; infil propre → 10/18 (56 %) — **+30 points**. Lecture : contact précoce = patrouille ennemie engagée LOIN du complexe = garnison attritée/déplacée avant l'assaut ; infil « propre » = garnison intacte au contact. **Règle de décision observable, indépendante du plan** (A et B conditionnellement similaires). CONSÉQUENCE PROTOCOLAIRE pour le palier 1 : tester H1 (QRF mécanisée) sur le gabarit actuel ne testerait RIEN (QRF jamais atteinte) → **amendement nécessaire : gabarit v2** (critère/budget d'assaut corrigés pour que CONSOLIDATION soit atteinte majoritairement) + **nouvelle baseline v2 vanilla (24 ops)** avant le bras mécanisé — sinon comparaison invalide.

**PRÉ-ENREGISTREMENT (06/06, AVANT tout run v2 — discipline Tetlock).**
*Gabarit v2* = correction du chemin vers CONSOLIDATION : (a) en zone effectivement nettoyée (aucun ennemi vivant à <250 m de l'escouade), la posture assault repasse en marche de groupe pour les derniers mètres (condition STRICTEMENT plus forte que le contact-vue qui avait causé le désastre « défiler sous le feu » — leçon re-validée, pas répétée) ; (b) budget ASSAUT 120→160 pas. Tout le reste identique aux 60 ops.
**P-v2 (baseline)** : « Sur le gabarit v2 vanilla (QRF infanterie, 24 ops), la CONSOLIDATION sera atteinte dans >60 % des ops (sinon v2 est un échec d'ingénierie, pas un résultat) ; le succès global chute sous 60 % (la QRF affrontée est aujourd'hui 0/3) ; la parité A/B persiste (écart <10 pts). »
**H1 (palier 1 mécanisé, 2×24 ops)** : « Face à une QRF MÉCANISÉE (1 véhicule armé + groupe débarqué), la parité A/B se brise : le plan A (appui d'abord) surperforme le plan B (assaut direct) en taux de succès, parce que l'élément d'appui fixe/traite le véhicule pendant que l'assaut survit. Secondaire : succès global < baseline v2 ; contingences pertes plus fréquentes. **Seuils décidés avant les données : écart A−B ≥ 20 pts = signal (≈1.6σ à n=24/bras) ; ≥ 30 pts = fort ; < 10 pts = parité robuste, H1 morte.** Sort du véhicule tracé (détruit/évité/victorieux). »
## PILE ALGORITHMIQUE — FEUILLE DE ROUTE PERMANENTE (gravée 06/06, demande Younes : « rappelle-moi souvent où nous en sommes »)
Couches REMPLIES : micro tactique (koth_finetuned, sim→réel fermé) · ligue PSRO · politique paramétrée par objectif · postures-logits · couche opérationnelle SCRIPTÉE (152 ops, baseline 25 %) · civils appris · briques mémoire/comms (toys).
Couches RESTANTES, dans l'ordre :
**[→ EN COURS depuis 06/06 soir] 1. MANAGER APPRIS** — réseau qui choisit objectifs+postures des escouades (workers gelés, gating léger) ; terrain = sim GPU ; **baseline à battre = P-v3b : 38 % strict / 72 % militaire** (partition scriptée, gabarit 4 escouades).
**2. CERVEAU STRATÉGIQUE (cerveau-pays)** — RL sur la carte géo (où attaquer/défendre ; question tertius gaudens) → hiérarchie pays→opération→escouade→soldat apprise de bout en bout.
**3. MÉMOIRE+COMMS DANS LE CERVEAU DÉPLOYÉ** — fusionner RecComm (validé toys) dans le cerveau d'opérations (souvenir du véhicule masqué, info distribuée).
**4. ADVERSAIRE APPRIS OPÉRATIONNEL** — self-play de chefs d'opération (l'ennemi des 152 ops est scripté).
**5. DISTILLATION / SPÉCIALISTES (MoE)** — bibliothèque assaut/défense/antichar + routeur appris.
(L'orchestrateur LLM = cerise démo, hors pile.) RÈGLE D'AFFICHAGE : rappeler l'étape courante à chaque rapport de jalon.

## CHECKLIST « MONDE 2 » — OUVERTURE DE LA PORTE MODS/DYNAMICS (préparée 06/06, à exécuter comme VERSION MAJEURE avec sa propre Gate 0)
**Principe** : le monde vanilla reste à JAMAIS le monde de contrôle (212 ops de référence, 10 lois) ; aucune comparaison ne traverse la frontière du mod. DEMO (visuel pur) s'ouvre librement pour le démonstrateur ; DYNAMICS (ACE & co) suit CE cycle, dans CET ordre :
**M2.0 — Gate 0** : branche git `monde-2` + bundle ; copie du sandbox serveur (`harmattan-sandbox-m2/` ou préfixe mission dédié) pour ne JAMAIS polluer le vanilla ; choix des mods gelé par écrit (proposition : ACE médical+balistique, LAMBS danger.fsm IA ; PAS de mods de contenu au début — moins de variables).
**M2.1 — Infra serveur** : mods installés côté serveur dédié headless (`-mod=`), missions HarmattanBridge-M2 copiées avec init adapté, les 16 serveurs bootent, le pont répond (smoke cmd/dump).
**M2.2 — Instrumentation AVANT tout le reste (leçon de la semaine : l'instrument d'abord)** : adapter les lectures d'état à l'API ACE — `getDammage` ne suffit plus : états inconscient/blessé/saigne via fonctions ACE (`ace_medical_status_*`), redéfinir `alive()`/`dmg_dead`, dump enrichi (conscient O/N, hémorragie O/N). SMOKE D'INSTRUMENT dédié : tirer sur une unité, vérifier que CHAQUE état transite correctement dans le pont. Chasse aux menteurs préventive : tout état non lu = état réputé faux.
**M2.3 — Re-baseline COMPORTEMENTALE sans cerveau** : duels scriptés vanilla-style dans le monde moddé (létalité, distances d'engagement, durées) → mesurer le décalage de distribution. C'est la photo « avant ».
**M2.4 — RE-FINE-TUNE du cerveau** (cycle C.3 rejoué) : warm-start `koth_finetuned.pt` → fine-tune dans le monde moddé (8-12 serveurs, métriques de convergence comme en C.3 : succès/morts/entropie) → `koth_m2.pt`. Critère : retrouver ≥ le niveau vanilla sur le KOTH moddé.
**M2.5 — Re-baselines opérationnelles** : HARMATTAN-1v2 et 2v3 rejoués dans le monde moddé (24-32 ops chacun) = les nouveaux points de référence. AUCUNE conclusion comparative vanilla↔M2 — seulement des récits de différence qualitative.
**M2.6 — Les partitions PROFONDES (la récompense)** : nouvelles phases rendues possibles par ACE — MEDEVAC (blessé inconscient → extraction sous feu), triage (contingence sur blessés vs morts), gestion munitions ; nouvelles postures si besoin (medic). Pré-enregistrement pour chaque nouvelle hypothèse, comme toujours.
**M2.7 — Démonstrateur** : preset DEMO (visuels) + spectateur sur une opération M2 — le livrable visuel.
**Risques identifiés d'avance** : ACE casse `HandleDamage`/seuils (M2.2 le couvre) ; les temps d'épisode s'allongent (blessés ≠ morts → combats plus longs → budgets de phase à re-calibrer) ; CPU/serveur plus lourd avec l'IA modée (re-mesurer le plafond de serveurs) ; et le pont fichier/log devra peut-être passer au protocole socket (levier vitesse ×2-3) pour compenser.

**VERDICT P-v3b — BASELINE OFFICIELLE DÉCLARÉE (06/06 soir, 32 ops).** Seuils pré-enregistrés : A ≥40 % → **38 %** (raté de 2 pts) ; consolidation ≥65 % → 62 % (raté de 3 pts) ; admin ≤15 % → **55 %** (largement raté). MAIS : (1) **théorie du confondeur CONFIRMÉE en direction** — succès ×3 (12→38 %) en ne restaurant QUE les horloges ; (2) le résidu est un **artefact de critère identifié** : 55 % des échecs restent administratifs (ennemi brisé ✓ pertes ✓ LZ ✗) — la médiane-à-100m-de-LZ à 4 escouades avec traînards poursuivis est structurellement lente ; (3) **taux de missions MILITAIREMENT accomplies : 72 %** (23/32). **TROISIÈME mensonge de demi-échantillon** (partiel n=8 : A 50/B 62 → final 38/38) — « pas de conclusion avant n complet » = loi d'airain. **DÉCISION (Younes, 06/06) : arrêt des réparations d'horloges après 3 itérations (v2→v3→v3b) — continuer = réglage de critère a posteriori. P-v3b = BASELINE : succès strict 38 %, accomplissement militaire 72 %, les deux documentés. PROCHAINE MARCHE DE LA PILE : [1/5] MANAGER APPRIS — baseline à battre : 38 % strict / 72 % militaire.** Données : wargame_p2v3b.jsonl.

**VERDICT P-v3 : CLAUSE D'ÉCHEC ACTIVÉE — confondeur auto-infligé identifié (06/06 soir, 32 ops)** : A 12 % (<30), consolidation 41 %, **échecs administratifs 72 % (DOUBLÉS vs 38 %)** alors que la perf militaire est stable → signature du confondeur : **le levier de vitesse (1.6→1.0 s/pas) a re-serré TOUTES les horloges en TEMPS DE JEU (−30 %)**, annulant les réparations. Violation (pré-enregistrée ensemble mais interaction non anticipée) de « une variable à la fois ». **LEÇON STRUCTURELLE (au panthéon avec les argmax) : un budget en PAS n'est pas un budget en TEMPS — toute horloge doit être exprimée en temps de jeu, sinon elle change de valeur à chaque réglage de cadence.**
**PRÉ-ENREGISTREMENT P-v3b (avant runs)** : on garde la vitesse (2.1 s/pas validée), on restaure les horloges v3 en temps de jeu = TOUS les budgets de pas ×1.5 (infil 210, MEP 135, assaut 330, renforcé 165, consol 105, exfil 195 ; plafond global 1200). UNE variable vs P-v3. **Mêmes seuils que P-v3** : A ≥40 %, consolidation ≥65 %, admin ≤15 %, pertes ±5 pts ; clause d'échec : A <30 % → les goulets ne sont vraiment pas des horloges, rediagnostic militaire.
**Amendement P-v3 (smoke vitesse)** : pauses courtes VALIDÉES (2.14 s/pas, ×1.4, lectures saines) ; smoke = anéantissement TOTAL 28/28 à 25 % de pertes mais « échec » par PLAFOND GLOBAL (450) < somme des budgets de phase (760) — plafond harnais aligné à 800. Incohérence d'harnais, pas de partition.
**PRÉ-ENREGISTREMENT P-v3 — RÉPARATIONS DE PARTITION (06/06 soir, AVANT tout run).** Gabarit v3 = 3 nombres : budget EXFIL 80→130 (10/26 échecs administratifs), budget ASSAUT 160→220 + rayon de complétion 85→100 m (consolidation atteinte 44 % seulement). Critère de SUCCÈS inchangé (comparabilité). + LEVIER VITESSE smoké en parallèle : step_wait 1.6→1.0, settle 0.8→0.5 (gain attendu ~×1.4 ; abandon si lectures corrompues au smoke). **P-v3 (32 ops, 2×16, mêmes effectifs/ennemi que palier 2)** : succès plan A ≥ 40 % (vs 25) ; consolidation atteinte ≥ 65 % (vs 44) ; échecs administratifs ≤ 15 % des échecs (vs 38 %) ; pertes stables ±5 pts (les réparations sont des horloges, pas des forces). Si succès plan A < 30 % → les goulets n'étaient pas (que) des horloges, diagnostic à refaire.
**VERDICT H2 — MORTE PAR LE HAUT : LA MASSE RÉPARE LA CONSOLIDATION (06/06, 32 ops palier 2, n=16/plan).** Succès **A 25 % / B 12 %** (vs 4-8 % palier 1 — TRIPLEMENT). Seuils pré-enregistrés tous manqués PAR LE BAS : contingences/op 2.78 (<3.0), pertes@assaut 21 % (<25), jamais-assaut 16 % (<25) → **le coût de coordination existe mais la machine à phases dirige un quatuor presque aussi proprement qu'un duo — la couche opérationnelle TIENT L'ÉCHELLE.** RÉSULTAT SUPÉRIEUR (anticipé par la directive) : **13/14 consolidations TENUES à ~1 pt de perte** (palier 1 : 0/3 puis saignée 41 %) — le verrou des paliers 0-1 est réparé par la masse, pas par la doctrine. Nouveau goulet identifié : ATTEINDRE la consolidation (44 % vs 71 % bras 2 — l'ennemi doublé durcit l'assaut) + l'HORLOGE D'EXFIL (10/26 échecs « administratifs » : destruction ✓ pertes ✓ LZ ✗ → « mission militairement accomplie » réelle ≈ 50 %). A vs B : +13 pts pour A (appui+réserve), sous le seuil de signal à n=16, directionnel. **PHRASE DE LA JOURNÉE : la masse au bon moment vaut plus que la doctrine.** Bilan escalade : P-v2 validée, H1 morte, H2 morte par le haut — 3 hypothèses pré-enregistrées, 3 verdicts rendus sur seuils écrits avant les données, 152 opérations au total (24+24+48+32 + 24 baseline). Données : wargame_p2.jsonl. Leviers d'accélération notés pour la suite : step_wait 1.6→1.0/settle 0.8→0.5 (~×1.4, à smoker), 16 serveurs (+33 %), protocole socket dédié (×2-3, une soirée).
**PRÉ-ENREGISTREMENT H2 — PALIER 2 ÉCHELLE (06/06, AVANT tout run ; références bras 2 mesurées : contingences/op 2.00, pertes à l'entrée d'assaut 16.6 %, ops n'atteignant jamais l'assaut 12 %, succès 4 %).**
*Design* : 4 escouades (APPUI, ASSAUT-OUEST, ASSAUT-EST, RÉSERVE — 28 h, +AT), assauts CONVERGENTS 2 axes, réserve engageable par contingence ; ennemi renforcé : garnison 12 + 2 patrouilles de 4 + QRF infanterie 8 (= 28, ratio ~1:1 comme palier 1) ; QRF INFANTERIE (le mécanisé est l'ingrédient du palier 1 — une variable à la fois). Plans : A = appui+assauts convergents+réserve en arrière ; B = tout le monde à l'assaut. n = 2×16 = 32 ops, 12 serveurs (~670 unités simultanées, charge à surveiller).
*H2 (formulation Younes opérationnalisée)* : « la couche opérationnelle TIENT à 4 escouades mais la complexité de coordination se paie ; les échecs viennent des synchronisations, pas de la micro. » Prédictions chiffrées : **H2a** succès ≤15 % les deux plans (la masse ne répare pas la consolidation) ; **H2b** contingences/op ≥ 3.0 (vs 2.00) ET pertes à l'entrée d'assaut ≥ 25 % (vs 16.6 %) — le coût de synchro se lit en sang avant le premier assaut ; **H2c** ops n'atteignant jamais l'assaut ≥ 25 % (vs 12 %). Seuils de verdict : H2 validée si H2b ET H2c tombent ; si succès >25 % quelque part, la prémisse « la masse ne répare rien » tombe (résultat supérieur, à documenter). Effet plancher : règle de l'addendum 2 réutilisée telle quelle.
**VERDICT H1 (06/06, 48 ops mécanisées, n=24/plan, rendu sur seuils pré-enregistrés)** : A 2/24 (8 %) / B 2/24 (8 %) — écart 0 pt. Règle d'effet plancher activée (les deux <15 %) → secondaires : véhicule détruit A 54 %/B 62 % (B devant), pertes A 44 %/B 38 % (A saigne PLUS — inverse du mécanisme supposé), destruction ennemie 80/78 % (égalité). **H1 MORTE proprement — vraie absence d'effet, pas un artefact de plancher.** TROUVAILLE du palier 1 : la QRF mécanisée CHANGE LE MODE D'ÉCHEC, pas le taux — contre l'infanterie : échec par IMPUISSANCE (ennemis restants 6.2-6.7, destruction ~55 %) ; contre le blindé : échec par SAIGNÉE MUTUELLE (l'Ifrit charge en tête dans la zone NLAW, meurt 58 % des cas en entraînant ses débarqués → destruction ennemie 80 %, critère « brisé » souvent rempli, MAIS pertes amies ×2 (41 %) qui crèvent le plafond 50 % ou cassent l'exfil). Prédiction secondaire de H1 (succès < baseline) FAUSSE aussi (8 % ≈ plancher inchangé). Effet loadout AT vs infanterie : nul à légèrement négatif (bras 2 : 4 % vs bras 1 : 12.5 %, bruit à n=24). **CONCLUSION D'ÉTAGE : le verrou n'est ni la doctrine d'assaut ni la nature de la QRF — c'est la PHASE DE CONSOLIDATION elle-même. Marche suivante utile = enrichir la partition défensive (point fort, AT overwatch, repli élastique), pas le décor.** Données : wargame_v2_baseline/at_inf/at_mech.jsonl, journaux logs_train/arm1-3/.
**Addendum 2 (pré-enregistré AVANT les données du bras 3, bras 2 connu : A 8 %/B 0 %)** : les taux étant au PLANCHER, si bras 3 donne A et B tous deux <15 %, le verdict formel « écart <10 pts » sera rendu comme **« NON-CONCLUANT : effet plancher »** et PAS comme « parité robuste » — on ne départage pas des doctrines quand tout meurt. Métriques secondaires de départage (pré-enregistrées) : % de la QRF détruite par bras, sort du véhicule (détruit/intact), pertes amies, atteinte de la consolidation. H1 ne sera déclarée morte que si ces secondaires sont AUSSI plates.
**Addendum protocolaire (pré-enregistré avant données)** : la baseline v2 en cours tourne SANS AT (lancée avant l'ingénierie). Design final à 3 bras : (1) v2-sansAT 24 ops = test P-v2 + effet loadout ; (2) **v2+AT QRF infanterie 24 ops = bras de CONTRÔLE H1** ; (3) v2+AT QRF mécanisée 2×24 = bras de test. Le verdict H1 compare (3) vs (2) — delta = la QRF seule.

**CARTE DE RÉGIMES (sim GPU, pendant le wargame — 48 conditions × ~65k guerres ≈ 1.8M guerres, `carte_regimes.txt`)** : income 0.3/0.6/0.9 × hold 1/3/5/10 × {AAA,EEE,ZZZ,AEZ}. (1) **Hiérarchie A>E>Z UNIVERSELLE** (A 55-68 %, Z ≤10 % sur toutes les cases mix) — loi 4 généralisée, aucun renversement par la richesse. (2) **NEUVIÈME LOI — « la richesse rend la guerre totale »** : à horloge politique fixe, income↑ → élim explose (AEZ hold10 : 0.77→0.93 ; AAA hold5 : 0.08→0.28) — la richesse accélère l'horloge MILITAIRE pendant que l'horloge politique reste fixe. Corollaires : guerres riches + brèves et moins meurtrières pour les civils PAR GUERRE (la brièveté protège). (3) **Exception égalitaire** : le monde-EEE riche se GÈLE (décisives 0.77→0.58) = paix par impuissance mutuelle, le + humain de la carte (morts 0.116). (4) En guerre totale le vainqueur contrôle jusqu'à 89 % de la pop restante = l'hégémon démographique.

**DOCTRINE D = DÉNI DE REVENU (l'interprétation zéro-somme ÉCONOMIQUE, enfin testée)** : pointe dirigée vers la région ennemie adjacente la + PEUPLÉE (étrangler la base fiscale ; geo_gpu doctrine "D"). **Bataille royale A-D-E (3 rotations convergentes) : A 0.575 / D 0.421 / E 0.002.** D = PREMIER vrai challenger de A (Z plafonnait à 0.16) et EXTERMINE l'Égaliseur. Monde DDD = le + brutal mesuré : élim 0.91, guerres en 6 pas (record), vainqueur avec 39 % du territoire / 45 % de la pop = **la prédation généralisée est un jeu à somme très négative — même le vainqueur hérite de ruines**. ⚠️ ARTEFACT À CORRIGER avant promotion en loi : sanity DDD asymétrique (D0=0.67) — tie-break argmax sur scores de population initialement ÉGAUX → biais d'indice ; fix = bruit minuscule sur les scores, puis refaire les invasions D.

**RÉHABILITATION DE D — INSTRUMENT NETTOYÉ, LOI 10 GRAVÉE (06/06 matin)**. Chasse au tie-break en 3 étapes : (1) bruit 1e-3 sur les scores de pointe (DDD 0.67→0.45, partiel) ; (2) tie-break aléatoire de la fuite civile (sans effet — pas le canal) ; (3) **ablation systématique** (sans fuite/sans collines/pop uniforme) → l'argument de symétrie rotationnelle (toute dynamique équivariante DOIT donner ⅓) pointe un calcul indexé résiduel → **trouvé : les argmax de DÉSIGNATION DU VAINQUEUR** (hill_win/terr_alive — les guerres de prédation finissent souvent en COMPLETIONS SIMULTANÉES, chaque égalité couronnait pays 0 ; les mondes A/E/Z, asymétriques, n'égalisaient presque jamais → sanity trompeusement propres). Bruit sur les deux → **DDD = 0.334/0.334/0.332 PARFAIT**. LEÇON D'INSTRUMENT (3 incarnations en 24h : pointe, fuite, couronnement) : **tout argmax est un tie-break déguisé, tout tie-break déterministe est un biais en embuscade** — bruiter par défaut.
**BATTERIE D DÉFINITIVE (22 runs, rotations invariantes ±0.003)** : ROYALE A-D-E : **D 0.499 / A 0.488 / E 0.013** — le prédateur économique fait (très légèrement +) jeu égal avec l'Amplificateur en écologie mixte, en dévorant l'Égaliseur. INVASIONS (moy. 3 positions) : D→AA **0.227** ❌ | A→DD **0.370** ✅ | D→EE **0.057** ❌❌ (résidents E 0.877 !) | E→DD 0.253 ❌ | D→ZZ 0.284 ❌ | **Z→DD 0.430 ✅**. **LOI 10 : le prédateur économique est co-dominant en écologie mixte mais PAS évolutionnairement stable — il introduit la NON-TRANSITIVITÉ dans l'écologie des doctrines** : A reste l'unique ESS (rien ne l'envahit, il envahit tout) ; sous lui, un sous-monde cyclique — D prospère là où il y a une proie (E en mixte), **le bloc égalitaire collectif repousse le prédateur isolé** (0.057 — pas de point riche faible quand la défense est uniforme), et **le contre-forceur Z, perdant partout ailleurs, envahit le monde des prédateurs** (la pointe du chasseur de population s'expose au contre-punch). Traductions géopolitiques : la prédation économique paie dans les mondes divers à cibles molles ; la défense collective égalitaire est LA structure anti-prédateur ; la doctrine contre-force est un SPÉCIALISTE anti-prédateur.

**TEST DOCTRINES PROPRE — RÉSULTAT FINAL (05/06, 25 min, 10 guerres, 76 batailles Arma, 51 % décidées en jeu — le combat juste stalemate plus que le biaisé à 68 %, 22 verdicts de colline imposés)** : **A 5 / E 3 / Z 2** vs baseline abstraite **A 8 / E 2 / Z 0** (mêmes guerres, même seed). DEUX CONCLUSIONS : (1) **la hiérarchie doctrinale SURVIT au vrai moteur** (A reste n°1 ; le signal doctrine→trésor→forces→handicap→bataille→colline traverse toute la chaîne) ; (2) **la friction du réel est l'alliée du faible** : Arma adoucit la domination (A 8→5) et donne à Z ses premières victoires (0→2), dont une par ÉLIMINATION au bout de la guerre la plus longue (11 pas) et la plus meurtrière (morts civils 0.31 vs moy 0.18) — le réactif ne gagne qu'à l'usure totale. ⚠️ n=10 guerres = démonstration cohérente avec l'abstrait, pas une statistique (pour du solide : ~30+ guerres). Morts civils moy 0.18, fins 8× politique / 2× élimination.

**BILAN SESSION GÉO (05/06) : 7 lois émergentes** (1 topologie≠valeur, 2 calice empoisonné, 3 horloge politique, 4 renforcer-le-succès, 5 la guerre brûle son carburant, 6 coût civil=propriété du monde doctrinal, 7 fuir la géographie pas la menace) + pipeline complet sim géopolitique scripté→RL. **DETTE DE CONSOLIDATION MAXIMALE : git + note de recherche AVANT toute expansion.** Fichiers : geo_gpu.py (v4), run_geo.py, train_civ.py, civ_learner.pt.

## SESSION MODS/RÉALISME (06/06, ~01h30) — inventaire + presets posés
**Inventaire Workshop sandbox (88 G, 35 mods + ~40 scénarios)** : ACE3 (v3.21, à jour 01/06 ⇒ compats RHS intégrées, rien à charger), RHS ×4, CUP complet, 3CB Factions, R3F (armée FR 🇫🇷), JSRS, TFAR, CBA — le kit milsim était déjà là, RIEN n'était chargé (aucun -mod= nulle part). **Téléchargés via steamcmd local** (~/.local/opt/steamcmd, sans abonnement, login you59000) : @Blastcore_Edited + @Zeus_Enhanced → /mnt/data/harmattan-sandbox/mods/ (hors arbre Steam client, pas d'auto-update — relancer ~/Bureau/dl_mods.sh à l'occasion). **2 presets créés** : `hmt-demo.sh` (CBA+JSRS+RLW+Blastcore — zéro impact dynamics, cerveaux actuels OK, pour clips) et `hmt-dynamics.sh` (ACE+RHS+3CB+R3F+CUP Terrains — change le JEU : re-fine-tune obligatoire avant éval ; ZEUS=1 pour l'outillage ZEN). **Interdits maintenus** : LAMBS/VCOM/Drongo/C2 = guerre contre le pont. Idée notée : R3F+3CB+terrain désert (Takistan ou CDLC Western Sahara ~10 €) = démo Harmattan-Sahel clés en main. ⚠️ -mod= via `steam -applaunch 107410` PAS ENCORE TESTÉ sous Proton (vérifier chemins Z:\ et survie du pont hmt_ext_x64.dll au premier lancement).
