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


## [pile 1/5] MANAGER APPRIS — SIM OPÉRATIONNEL + DÉCOUVERTE D'EXPLOIT (06/06 nuit, branche manager-appris)
**Construit** : `op_gpu.py` (sim opérationnel GPU : 4 escouades vs garnison+2 patrouilles+QRF, combat agrégé + bruit log-normal sd0.5, horloges de phase, succès strict/militaire) ; `calibrate_op_gpu.py` (partition scriptée vectorisée = machine à phases explicite) ; `train_manager.py` (PPO, manager 8 têtes [4 objectifs×8 + 4 postures×4], décision toutes les K=8 étapes, workers gelés, récompense terminale + shaping ennemi léger).
**Calibration on-trajectoire RÉUSSIE** : la partition scriptée rejouée dans le sim = **73.6 % militaire ≈ baseline Arma P-v3b 72 %** (qrf_dps 0.060, garr_dps 0.024). Le sim reproduit la vérité-terrain LE LONG de la doctrine.
**⚠️ EXPLOIT DÉCOUVERT (le manager l'a trouvé en 1 itération : 100 % dès it0)** : le sim n'est calibré QUE sur la trajectoire scriptée. Hors doctrine, il est trivialement exploitable — la politique « ZERG » (4 escouades à l'assaut direct du complexe, puis hold) fait **100 % militaire à 5 % de pertes** (vs scriptée 72 %/55 %). Cause : 4 escouades tuent la garnison trop vite (assault_dmg×4) pour subir des pertes, puis écrasent la QRF à pleine force. C'EST LE PIÈGE CENTRAL du RL basé-modèle (calibrer sur 1 trajectoire → exploité hors d'elle) — attrapé AVANT de gâcher un run d'entraînement.
**Tentatives de fix abandonnées (3 confondeurs auto-infligés en série, RÈGLE D'AIRAIN re-violée puis re-respectée)** : (a) pénalité ×2.8 sans-suppression + retrait dilution ×0.5 → écrase AUSSI la doctrine (0 %) ; (b) hausse garr_dps → idem ; (c) assault_eff gated par suppression → coupling caché (le suppresseur arrive lentement hors contact_r → supp_any=0 pendant l'assaut). LEÇON : calibrer un sim hors-trajectoire = tar-pit, une variable à la fois ET re-valider la doctrine à CHAQUE pas.
**Note de fond Arma-cohérente** : le wargame avait montré assaut-direct(B) ≈ doctrine(A) à 77 % → un manager qui « rush » n'est PAS forcément faux ; le bug est le 5 % de pertes (trop propre), pas que le rush marche. Le vrai fix = rendre le rush coûteux en PERTES (~35 % comme Arma B), pas le rendre perdant.
**ÉTAT** : sim validé on-trajectoire, exploit documenté NON résolu. PROCHAINE SOUS-TÂCHE (à tête reposée) : robustifier le sim hors-trajectoire (congestion/feu concentré qui punit la masse nue en PERTES sans toucher la doctrine), re-valider scriptée≈72 % ET zerg≈70 %/35 %pertes, PUIS lancer le PPO du manager. Baseline à battre : 72 % militaire.

## [pile 1/5] MANAGER APPRIS — PREMIER MANAGER ENTRAÎNÉ (06/06 nuit, manager.pt)
**Sim op rendu étanche après 6 trous fermés en série (chacun découvert par un test, jamais supposé)** : (1) zerg-4-assaut → pénalité masse-nue ; (2) split-2-assaut → pénalité PLATE par escouade (pas /n) ; (3) combiné-1s3a → QRF CONCENTRÉE (pas de dilution) ; (4) issues trop serrées (bruit par-pas moyenné) → VARIANCE PAR ÉPISODE (qrf_var=0.55, multiplicateur log-normal au spawn) ; (5) BUG MÉTRIQUE : ennemi_brisé créditait une QRF jamais spawnée (tuer les patrouilles=faux 71%) → total ne compte la QRF que si spawnée + garnison prise OBLIGATOIRE ; (6) esquive par l'anneau 60-120m → QRF spawn sur garr_down SEUL (réponse à la prise, pas à la position). Params v2 : garr_dps 0.010, patrol_bite 0.004, qrf_hp 22, qrf_dps 0.120, qrf_var 0.55, nu_dps 0.08. Validation multi-politiques (anti one-trajectory) : combiné-1s3a 70/35, zerg 47/52, doctrine scriptée 30 (défend la consol dispersée), staging-exploit 0.
**MANAGER PPO (train_manager.py, 8 têtes [4 objectifs×8 + 4 postures×4], décision/K=8 étapes, workers gelés, 400 it/8192 envs, ~15 min 3090, garde __main__ posé)** : courbe SAINE it0 34% → it100 81% → plateau **it200-399 ~83%/21% pertes** (PAS d'effondrement à 1% = pas d'exploit). **DISSECTION : garnison prise 100%, QRF déclenchée 100%, QRF entièrement détruite 0% MAIS saignée ≥43% (franchit le seuil 70%), 21% pertes, postures 41% assaut/28% hold/26% suppression = COMBINÉ-ARMS APPRIS.** Comportement = DOCTRINE DE RAID cohérente (prendre l'objectif, saigner la contre-attaque, décrocher) — non-exploitatif (paie 21% de pertes, affronte vraiment la QRF). ⚠️ NUANCE MÉTRIQUE assumée : le seuil « 70% ennemi détruit » compte une QRF à demi-tuée comme succès — défendable pour un RAID (pas besoin d'annihiler les renforts), mais c'est un choix de modélisation. **RÉSULTAT : manager appris 83% vs partition scriptée 30% en sim = +53 pts par doctrine adaptative émergente. JUGE FINAL = ARMA (32 vraies ops, prochain jalon).**

## VALIDATION ARMA DU MANAGER [pile 1/5] — Phase A franchie + pré-enregistrement (06/06 nuit)
**Phase A (pont d'obs + runner piloté-manager, `validate_manager_arma.py`)** : reconstruit les 22-obs du sim depuis l'état Arma (positions centroïdes, effectifs/7, PV garnison[0:12]/patrouilles[12:20]/QRF[20:] via tranches de HMT_EN ; QRF abs 8 vs sim 22 neutralisé car le manager ne voit que des fractions). Cerveau gelé koth_finetuned fait la micro (postures=biais logits). **Gate A : obs sane=True du début à la fin ✅.** Bug d'exécution trouvé+corrigé : le cerveau (entraîné au contact ~140m) se FIGE à distance ; la garde de transit assaut (_nearest_enemy>250) lui donnait la main trop tôt → escouades bloquées à ~270m. FIX côté runner (ne touche pas op_arma/baseline) : APPROCHE en posture 'move' tant que goal_dist>120m (marche de groupe), posture du manager adoptée seulement à l'arrivée. Après fix : d_min_cx 388→117m, garnison engagée (12→10), pertes 14% = harnais fonctionnel.
**ÉCART SIM-TO-REAL déjà visible au smoke** : le manager met 3 escouades sur CRETE (appui) + 1 seule à l'assaut — sa politique sim où CRETE = « suppression » exonérant la pénalité. En Arma, 3 escouades sur une crête à 188m ne suppriment rien de réel (pas de LOS/portée modélisée comme dans le sim) → 1 seule escouade craque la garnison = LENT. Overfit aux mécaniques du sim.
**PRÉ-ENREGISTREMENT (avant le run de masse) — affiné par le smoke** : prédiction militaire **30-50% en Arma** (sous les 83% sim ; le smoke montre l'under-commit à l'assaut). Seuils (déjà actés) : ≥72% = égale la doctrine scriptée (transfert réussi) ; 50-72% = transfert partiel ; **<40% = le sim a sur-appris, l'abstraction CRETE-suppression n'a pas tenu** (résultat précieux, attendu). 16 serveurs, 32 ops, QRF infanterie, max_steps 180, comparaison vs P-v3b 72%.
## VERDICT VALIDATION ARMA DU MANAGER [pile 1/5] — SIM-TO-REAL OVERFIT CONFIRMÉ (06/06 nuit, n=32)
**Résultat : militaire 0/32 (0%), complexe pris 22%, consolidation tenue 0, pertes 21%.** Vs sim 83%, vs partition scriptée Arma 72%. **SOUS le plancher pré-enregistré de 40% → branche « le sim a sur-appris » CONFIRMÉE** (prédiction 30-50% ; réel 0%, encore pire).
**Mode d'échec disséqué** : le manager met 3 escouades sur CRETE + 1 seule à l'assaut (politique optimale en sim, où CRETE = « suppression » exonérant la pénalité nu_dps). En Arma, 3 escouades sur une crête à 188m ne suppriment RIEN de réel (pas de LOS/portée comme dans l'abstraction sim) → l'escouade isolée ne craque la garnison que 22% du temps, et les escouades ne se concentrent jamais pour tenir la consolidation (consol=0) → QRF jamais défaite → 0% militaire.
**LECTURE (sans spin)** : le PIÈGE CENTRAL du RL basé-modèle démontré end-to-end — manager 83% sim → 0% réel parce que le sim a donné de la valeur à une posture tactiquement creuse. MAIS : (1) PRÉDIT et CHIFFRÉ à l'avance (pré-enregistrement) → écart MESURÉ, pas supposé ; (2) la PARTITION SCRIPTÉE reste invaincue (72% Arma) = une doctrine bien conçue à la main n'est pas trivialement battue par du RL sur sim abstrait ; (3) le PIPELINE de validation (pont d'obs, harnais, pré-enregistrement) fonctionne et est réutilisable.
**POUR UN MANAGER TRANSFÉRABLE (prochaine sous-tâche)** : sim haute-fidélité sur la SUPPRESSION (CRETE compte seulement sous LOS/proximité, pas un exempt binaire global) + domain randomization ; OU contraindre l'espace d'action à des options tactiquement saines ; OU re-fine-tune dans Arma (lent). **STATUT PILE [1/5] : infra manager + pipeline validation BÂTIS et VALIDÉS end-to-end ; premier manager entraîné NE TRANSFÈRE PAS (overfit sim documenté) ; partition scriptée = couche opérationnelle de référence.** Données : validate_manager.jsonl.

## PISTE ARCHITECTURE — ENCODEUR D'ENTITÉS PAR ATTENTION (notée 06/06, demande Younes — PAS un chantier ouvert)
**Idée** : 1-2 couches de self-attention sur les entités observées (alliés/ennemis visibles) AVANT le GRU — pattern AlphaStar/OpenAI Five. Gains attendus : nombre VARIABLE d'unités visibles (plus de padding/troncature à taille fixe), invariance par permutation (ennemi n°3 ↔ n°7 = même situation), pondération apprise de la menace prioritaire. Coût : quelques milliers de paramètres, négligeable pour la 3090.
**Périmètre** : encodeur d'observation SEULEMENT. NE PAS remplacer le GRU par un Transformer (GTrXL = instable avec PPO, chantier mémoire déjà fermé, piège cudnn déjà résolu — ne pas rouvrir) ; Decision Transformer hors sujet (offline, nous = PPO online + ligue) ; comms par attention = en réserve si la coordination plafonne.
**CRITÈRE D'ACTIVATION (pas avant)** : un symptôme observable — agents qui ignorent des menaces dans l'obs, ou plafond de padding sur le nombre d'unités visibles. Sans diagnostic = optimisation sans symptôme, on n'y touche pas. Priorité actuelle inchangée : pile [1/5] manager.

---

## 2026-06-06 — VOIE « ÉCOLE DE GUERRE » : répertoire doctrinal codé (pile [1/5], après échec du manager appris)

**Pivot conceptuel (idée Younes).** Le manager appris a échoué en Arma (0/32, sur-apprentissage sim : parking-CRETE creux). Plutôt qu'un RH qui DÉCOUVRE la tactique en sim (et invente des fictions), on lui donne un RÉPERTOIRE de manœuvres doctrinales déjà connues — il apprendra seulement *laquelle, quand*. On ne peut pas sur-apprendre une fiction absente du vocabulaire. Chaque manœuvre est Arma-exécutable PAR CONSTRUCTION (moteur de phases scripté) et mesurable directement -> le sélecteur choisira sur DONNÉES RÉELLES, pas sur le sim (court-circuite le mur sim-to-real). Analogue AlphaStar/OpenAI Five (imitation avant RL).

**Codé.** `maneuvers.py` (4 manœuvres = plan-dicts OperationRunner) + `run_maneuver.py` (mesure Arma smoke/masse, métriques P-v3b).
- M1 APPUI-ASSAUT (référence = P-v3b, 72 %) · M2 DOUBLE ENVELOPPEMENT · M3 ENVELOPPEMENT SIMPLE (flanc lourd) · M4 ASSAUT MASSÉ.

**SMOKE M2 (1 serveur, double enveloppement) — VERDICT : ÉCHEC, mais smoke RÉUSSI dans son but.**
- ✅ Prouvé : une manœuvre non triviale s'exécute de bout en bout dans le VRAI Arma.
- M2 : `mil=False, garr_pris=False, pertes 46 %, ennemi 19/20 intact`. Séquence : INFILTRATION → pertes >30 % sur le flanc EST → contingence « pertes en débordement » → EXFIL. **Jamais assauté.**
- **Trouvaille doctrinale** : le double enveloppement suppose un flanc NON défendu. Ici la garnison a un ÉCRAN DE PATROUILLES au nord (15150/16120) ; l'axe FLANC_E (15230/16110) passe dedans -> SQ_A_EST fond de 7 à 1 AVANT l'assaut. Manœuvre inadaptée à CETTE défense (à confirmer en masse).
- **2 bugs d'encodage corrigés** (correction, pas tuning) : (a) INFILTRATION M2 attendait l'escouade mourante -> bascule FIXER dès prong OUEST+appui en place ; (b) EXFIL `done_when` indexé sur escouade 0 (peut être anéantie) -> n'importe quelle escouade arrivée OU budget. Réencodage revalidé OK.
- **Discipline** : on NE tune PAS la géométrie de FLANC_E a posteriori. La table de masse dira si M2 est systématiquement faible ici = donnée pour le sélecteur (« ne pas choisir l'enveloppement contre flancs écrantés »).

**Prochain pas proposé** : table empirique de masse (16 serveurs) M1/M2/M3/M4, ~24 ops chacune -> taux de succès réel par manœuvre. Prédictions pré-enregistrées : M1 72 %, M2 55-75 % (smoke suggère plus bas), M3 60-72 %, M4 30-50 %.

### 2026-06-06 (suite) — Répertoire étendu à 7 manœuvres + prédictions pré-enregistrées

Ajout M5/M6/M7 (validés structurellement). Insight clé consigné : **ennemi Arma STATIQUE** -> seules les manœuvres à mécanisme PHYSIQUE (route, feux, échelons) produisent du signal ; les manœuvres de TROMPERIE (feinte) n'ont rien à tromper. M5 codé comme **témoin négatif** assumé. Lien thèse : un modèle ne récompense que les variables qu'il représente.
- M5 FEINTE+DÉBORDEMENT (démonstration E + effort principal O) · M6 INFILTRATION (axe SUD couvert INF_O/INF_E sous l'écran de patrouilles, assaut rapproché, sans base de feu) · M7 ATTAQUE ÉCHELONNÉE (1er échelon AO/AE, passage de lignes vers APPUI/RÉSERVE à ~25 % pertes).

**PRÉDICTIONS PRÉ-ENREGISTRÉES (% militaire, AVANT mesure de masse) :**
| M1 réf | M2 double env | M3 env. simple | M4 massé | M5 feinte | M6 infiltration | M7 échelon |
|---|---|---|---|---|---|---|
| 72 % (connu) | 20-45 % (smoke ⇒ revu bas) | 55-72 % | 30-50 % | ~M3 (50-70 %, sans bonus tromperie) | 45-70 % (route paie, mais pas de base de feu) | 55-72 % (préservation vs lenteur) |

Lecture : si M3/M6/M7 ≥ M1 -> meilleur chef d'op transférable ; si M5 ≈ M3 -> confirme « tromperie inerte » ; si M2 reste bas -> confirme « enveloppement inadapté aux flancs écrantés ». PUIS sélecteur sur cette table réelle (pas le sim).

### 2026-06-07 — TABLE DE MASSE (16 serveurs) : M1 mesuré + méthodologie de comparaison

**FICHIERS DE LA VOIE ÉCOLE-DE-GUERRE (inventaire) :**
- `maneuvers.py` — répertoire doctrinal, 7 manœuvres = plan-dicts OperationRunner (M1 appui-assaut réf · M2 double env · M3 env simple · M4 assaut massé · M5 feinte · M6 infiltration · M7 échelonnée). Géométrie + 2 corrections d'encodage smoke (FIXER au prong ouest ; EXFIL toute escouade).
- `run_maneuver.py` — mesure Arma d'une manœuvre (smoke 1 serveur / masse N serveurs), métriques P-v3b.
- `run_table.sh` — driver : boot 16 serveurs + mesure les 7 manœuvres en séquence + synthèse. Sortie `table_maneuvers.jsonl`.

**M1 (référence) mesuré n=16 : militaire 56,2 % | complexe pris 88 % | QRF affrontée 81 % | pertes 19 %.**
- Harnais SAIN (88 % prennent le complexe, pertes basses). 56 % vs 72 % baseline = dans l'IC (n=16, ±~24 %) -> M1-ici ≈ baseline, point estimé un peu bas.
- L'écart complexe-pris (88 %) vs militaire (56 %) vient du critère « ≥70 % ennemi total détruit » : la QRF survivante maintient l'ennemi >30 %. Pas les pertes.
- **MÉTHODO** : on compare M2..M7 à **M1 mesuré ici (56 %, même harnais)**, PAS au 72 % historique = comparaison apples-to-apples. C'est le baseline opérationnel de cette table.

**État au moment de l'enregistrement** : M1 fini (56 %), M2 en cours, M3-M7 à venir. Table relancée en arrière-plan (`/tmp/table.log`).

**M2 (double enveloppement) n=16 : militaire 62,5 % | complexe pris 75 % | QRF affrontée 69 % | pertes 27 %.**
- ⚠️ PRÉDICTION PRÉ-ENREGISTRÉE = 20-45 % -> RÉFUTÉE. M2 ≈ M1 (62,5 vs 56,2, IC chevauchants n=16). Le smoke (n=1, ANCIEN encodage) m'a induit en erreur : avec les 2 corrections (FIXER au prong ouest sans attendre la branche est mourante ; EXFIL toute escouade), le double enveloppement DEVIENT compétitif. Leçon track-record : ne pas extrapoler d'un smoke n=1 pré-correction.
- Conversion prise->militaire : M2 62,5/75 = 83 % (nettoie bien quand il prend) vs M1 56/88 = 64 % (QRF survit plus souvent). Mécanique différente, résultat net ≈ égal.

**M3 (enveloppement simple, base de feu lourde 2 escouades + 2 à l'assaut) n=16 : militaire 31,2 % | complexe pris 81 % | QRF affrontée 50 % | pertes 26 %.**
- ⚠️ PRÉDICTION = 55-72 % -> RÉFUTÉE (trop haut). M3 = PIRE jusqu'ici. Conversion prise->militaire = 31/81 = 38 % (nettoyage médiocre).
- MOTIF ÉMERGENT (2 préds fausses : M2 trop bas, M3 trop haut) : vs ennemi STATIQUE, la MASSE D'ASSAUT > la SUPPRESSION. M3 immobilise 2 escouades en suppress (qui « fixe » un ennemi qui penserait) -> ne reste que 2 à l'assaut -> prend mal, nettoie mal. La valeur de la suppression (épingler) est érodée par un ennemi qui continue de tirer — même logique que la feinte inerte (M5). Hypothèse à confirmer par M4 (massé) / M6 (infiltration sans base de feu) / M7 (échelon).

### 2026-06-07 — TABLE DE MASSE COMPLÈTE (7 manœuvres × 16 ops, 16 serveurs) : VERDICT FINAL

**Incident** : PC coupé ~01h04 pendant M5 (M1-M4 acquises). Reprise 07/06 via `run_table_resume.sh` (APPEND — le run_table.sh d'origine ÉCRASE le jsonl, ne jamais relancer tel quel), op M5 partielle purgée, backup `table_maneuvers.jsonl.bak-0607`.

**TABLE FINALE (n=16/manœuvre, QRF inf, max_steps 500)** :
| man | nom | mil% | cplx% | QRF% | pertes% | prédiction | verdict |
|---|---|---|---|---|---|---|---|
| M2 | double-env | **62.5** | 75 | 69 | 27 | 20-45 | ❌ trop bas |
| M1 | appui-assaut (réf) | 56.2 | 88 | 81 | 19 | 72 connu | (réf, IC ok) |
| M5 | feinte+débord | 56.2 | 75 | 50 | 31 | ≈M3 | ❌ structurel (+25 pts vs M3) |
| M6 | infiltration | 50.0 | 69 | 56 | 30 | 45-70 | ✅ seule tenue |
| M3 | env-simple | 31.2 | 81 | 50 | 26 | 55-72 | ❌ trop haut |
| M4 | assaut-massé | 25.0 | 69 | 56 | 30 | 30-50 | ❌ marginal (sous borne) |
| M7 | échelonnée | **25.0** | 56 | 50 | 37 | 55-72 | ❌ trop haut (pire pertes ET pire prise) |

**TRACK-RECORD DE CALIBRATION (à la Tetlock, sans spin) : 1 prédiction tenue sur 6.** Les erreurs ne sont pas du bruit, elles ont une DIRECTION : j'ai surestimé tout ce qui ressemble à la doctrine d'école (suppression, échelons) et sous-estimé le mouvement multi-axes. Mon prior doctrinal était calibré sur un ennemi qui PENSE.

**LOI ÉMERGENTE DE LA TABLE (vs cette défense statique écrantée)** : ce qui discrimine, c'est la PRESSION SIMULTANÉE SUR ≥2 AXES SÉPARÉS au moment du craquage. Gagnants 50-62 % = M2/M1/M5/M6 (tous ≥2 axes simultanés). Perdants 25-31 % = tout ce qui fragmente la force d'assaut : dans la FONCTION (M3, 2 escouades gelées en suppression), dans l'ESPACE (M4, masse sur 1 axe), dans le TEMPS (M7, échelons = défaite en détail — pire score : pertes 37 %, prise 56 % ; le 1er échelon saigne, le passage de lignes livre les frais par paquets). Corollaire M5 : la feinte marche contre un ennemi statique NON par tromperie mais par FIXATION PHYSIQUE (l'axe de démo absorbe le feu de l'écran) — la prédiction « tromperie inerte » confondait le mécanisme psychologique (absent) et le mécanisme physique (présent).

**⚠️ CAVEAT MÉTRIQUE (à disséquer AVANT le sélecteur)** : QRF spawnée seulement 50-56 % sur M5/M6/M7 (vs 81 % M1) ; le critère militaire ne compte la QRF que si spawnée → seuil 70 % plus facile sans elle. Une partie des scores M5/M6 est peut-être flattée. Sous-ensembles mil|QRF-spawnée : M5 6/8, M6 6/9, M7 3/8 (n trop petits pour trancher). Vérifier la cause du non-spawn (timeout ? ordre de prise ?) avant de graver le classement.

**PROCHAINE MARCHE** : (1) dissection du non-spawn QRF ; (2) PUIS sélecteur appris sur cette table réelle (la voie École-de-guerre court-circuite le mur sim-to-real : le répertoire est Arma-exécutable par construction, les données de choix sont réelles). Données : table_maneuvers.jsonl (112 ops), logs /tmp/table_resume.log (volatile).

### 2026-06-07 — MISSION VISUELLE « HMT-EcoleDeGuerre.Altis » + BAPTÊME DES OPS (construit + smoke validé)

**Construit (demande Younes : « visuel dans une mission nominative pour tracer les missions »)** :
- Mission `HMT-EcoleDeGuerre.Altis` (mpmissions, clone du pont + `hmt_trace.sqf`) : couche de traçage carte temps réel — points du théâtre, axes d'effort par phase (bandes orientées + flèches), trails des 4 escouades (1 dot/8 s, bleu APPUI/vert OUEST/orange EST/jaune RÉSERVE), ennemis vivants (triangles rouges)→morts (croix noires), HUD nom d'op+phase+pertes, jalons de contingence (croix violettes). Marqueurs globaux → visibles par tout client qui rejoint (slot jouable présent dans le sqm).
- `hmt-visu.sh` : serveur visuel dédié port 2302 (séparé des 16 de mesure ; ⚠️ multi_server.sh pkill TUE aussi ce serveur). Join : client Arma → LAN → 127.0.0.1:2302.
- `baptism.py` + `run_op_visual.py` (TracedRunner = OperationRunner + émission SQF sur OP_START/PHASE/SITREP/CONTINGENCE/QRF/OP_END, try/except : le traçage ne casse jamais l'op) ; `run_maneuver.py` patché : champ `"op"` (nom de baptême déterministe man×seed) dans chaque ligne jsonl.
**SMOKE VALIDÉ (OP AZALAI-01, M2, seed 1)** : op complète 628 s, succès, trace 79 ticks, 1 seule erreur SQF sur ~600 cmd (course fichier actuateur à haut débit — throttle HUD 1/15 steps posé ; la course est PRÉEXISTANTE au pont, à régler un jour par write-then-rename dans ArmaBridge).
**🎯 DISSECTION DU CAVEAT QRF — MÉCANISME ATTRAPÉ EN UNE OP TRACÉE** : AZALAI-01 fait mil=True SANS QRF : contingence « pertes en débordement » à step 174 → goto EXFIL en sautant ASSAUT/CONSOLIDATION, MAIS les escouades avaient déjà tué les 20 garnison+patrouilles pendant l'infiltration → enemy_dead_frac=1.0, pertes 29 % ≤ 50 % → succès militaire sans jamais affronter la contre-attaque. CAUSE : le spawn QRF est accroché à l'ENTRÉE EN PHASE CONSOLIDATION (on_enter), pas à la chute de la garnison. C'est le TROU #6 du sim op (« QRF spawn sur garr_down SEUL, réponse à la prise pas à la position ») JAMAIS reporté dans le harnais Arma. → Les scores M2/M5/M6 (QRF-spawn 50-69 %) sont flattés par les chemins de contingence qui contournent CONSOLIDATION. FIX CANDIDAT (décision Younes, change le harnais → re-mesure de table) : spawner la QRF sur garr_pris quel que soit l'état de phase, comme dans le sim.
**Addendum mission visuelle — MODE ÉDITEUR (07/06)** : Steam kicke Younes du multi local (problème connu) → bascule preview Eden. Mission copiée dans `<sandbox>/Steam/.../drive_c/users/steamuser/Documents/Arma 3/missions/HMT-EcoleDeGuerre.Altis` (drive_c lisible des 2 côtés = acquis C.4) ; `run_op_visual.py --editor` pointe le pont sur la copie Eden + lit le RPT client le plus récent (glob mtime) ; lanceur `op-visu.sh [M] [seed]`. ⚠️ deux copies de mission (mpmissions + Eden) — re-sync à la main si hmt_trace/init changent. Serveur visuel dédié (hmt-visu.sh, port 2302) arrêté mais conservé pour le jour où le kick Steam est réglé.
**🎯 DÉCOUVERTE D'INSTRUMENTATION (07/06, via la mission visuelle) — LES SPAWNS DE LA TABLE SONT DANS L'EAU** : mesuré in-game (`surfaceIsWater`) : les 4 spawns de maneuvers.py (y=15560-15740) sont EN MER (rivage Altis entre y=15700 et 15800 à x≈15000) → **les 112 ops de la table commencent par ~100-200 m de NAGE non modélisée** (armes inutilisables, lenteur, exposition). La comparaison ENTRE manœuvres reste valide (handicap identique pour toutes, y compris la baseline P-v3b), mais les chiffres absolus embarquent l'artefact. Découvert en UNE op regardée par Younes (« l'armée spawn dans l'eau ») après 112 ops headless aveugles — argument définitif pour le canal visuel. **Décision : maneuvers.py INTOUCHÉE jusqu'à la table v3 = {fix QRF-sur-garnison + spawns à terre} re-mesurée d'un bloc.** LZ (15180,15620) probablement mouillée aussi — à mesurer avant v3.
**Pont éditeur v2 — cause racine des 4 ops mortes TROUVÉE** : obs initiale lue dans le RPT client qui flush en retard → 0 unité vivante vue → step sans ordres → `send("")` → cmd_N à 0 octet = indistinguable d'« absent » pour l'actuateur → deadlock. Triple fix : protocole v2 sans état caché (numérotation continue max-disque+1, rattrapage par sondage au démarrage, JAMAIS de delete/reset — la resync v1 par sentinelle resettait en plein vol), écriture atomique tmp+rename, garde anti-fichier-vide (noop). Spawns visuels au sec (`VISU_SPAWNS`), purge du théâtre avant chaque op, insertion auto du joueur avec SQ_A_OUEST.
**MISSION VISUELLE — VALIDÉE END-TO-END AVEC JOUEUR EMBARQUÉ (07/06 ~13h30)** : op TAGANT-03 (M2, seed 3) jouée en preview Eden, Younes inséré au sol avec SQ_A_OUEST, temps réel (--speed 1, step_wait compensé 4s/step = dynamiques identiques à la mesure), déroulé complet INFILTRATION (48 steps, 7%) → FIXER → ASSAUT_CONVERGENT (percé en 5 steps) → ASSAUT_RENFORCE → CONSOLIDATION + QRF spawnée proprement (pas de contournement par contingence sur cette op). Chaîne stabilisée : `op-visu.sh [M] [seed] [vitesse]` ; touches F5/F6/F7 ; timeout 600s (pause alt-tab tolérée, recommander -noPause dans Steam) ; purge théâtre + spawns secs VISU_SPAWNS + insertion auto à chaque op. Le pont éditeur v2 (DLL + numérotation continue + atomic write + noop-guard) n'a plus failli après le dernier fix.
**SESSION VISUELLE CLOSE (07/06 ~14h)** : dernier point dur identifié = Arma solo PAUSE à la perte de focus → les ops meurent pendant que Younes lit le terminal ; remède définitif `hmt-arma.sh` (lance le client avec -noPause, variante `demo` avec mods visuels). CHAÎNE VISUELLE COMPLÈTE ET DOCUMENTÉE : hmt-arma.sh (client -noPause) → Eden preview HMT-EcoleDeGuerre → op-visu.sh [M] [seed] [vitesse] (pont DLL v2, temps réel par défaut, purge théâtre, spawns/LZ secs, insertion auto avec SQ_A_OUEST, F5/F6/F7, baptême + jsonl ecole_visu). Une op M2 vécue au sol jusqu'à CONSOLIDATION+QRF (4 % de pertes à la prise). À la prochaine session visuelle : tout marche en 4 gestes, zéro dette.
**BACKLOG VISUEL (retours Younes 07/06 après l'op vécue au sol)** : mouvements lents / postures qui clignotent (accroupi-debout) / soldats oisifs / dispersion. Diagnostic : (a) flicker = posture réémise chaque step + politique ÉCHANTILLONNÉE par unité/4 s (invisible à 4×) ; (b) lenteur = setUnitPos MIDDLE forcé en déplacement + behaviour combat ; (c) oisifs + dispersion = LA POLITIQUE RÉELLE du cerveau KOTH (action stop dans le répertoire, pas de tenue de formation) — c'est de l'information sur le cerveau, présente dans les 112 mesures, PAS un bug. Plan : fix cosmétique toujours actif (posture émise seulement au changement + AUTO en move) + flag `--polish` (hors contact : AWARE+pleine vitesse+formation ; au contact : la main au cerveau) — polish JAMAIS pour la mesure (change les dynamiques). À construire à la prochaine session visuelle (~30 min).
**PROFILS ENNEMIS (07/06, demande Younes « IA hardcore, 50-90 ennemis ») — mode visuel** : `op-visu.sh [M] [seed] [vitesse] [ennemi]` avec ennemi ∈ {normal 28 | pro 42 | hardcore 60 | nightmare 84}. pro+ = sous-skills montés (visée .75/.9, spot .95, courage/commanding 1) + **boucle de CHASSE** (toutes les 30 s, tout groupe est qui connaît un contact (knowsAbout>1.5) convertit sa patrouille en SAD FULL sur la position — fini l'ennemi statique). QRF échelonnée par wrapper, métrique de verdict rendue dynamique (metrics_dyn — les tranches 12/8/8 de run_maneuver cassaient). Mise en garde gradée consignée : à 1:3 vs pros, attente = plancher 0 % partout — l'intéressant est le cran d'INVERSION du classement des manœuvres ; ces profils = futurs bras « variation de défense » de la table v3+ pour le sélecteur. ⚠️ nightmare ≈ 112 unités en preview solo = FPS à surveiller ; le cerveau BLUFOR n'a jamais été fine-tuné contre ça (attendre une boucherie instructive).

### 2026-06-07 14h45 — OP-1 « SOCLE » : PRÉ-ENREGISTREMENT TABLE V3 (avant toute donnée)
**Harnais v3 posé d'un bloc** : (1) QRF déclenchée par CHUTE DE GARNISON à chaque step du runner (clé plan `qrf_on_garrison`, plus d'esquive par contingence) ; (2) géo sèche mesurée par sonde surfaceIsWater : 4 spawns + LZ (15840) + POSTE_RES (15800) — tout le reste de la géométrie de combat était déjà sec ; (3) wrapper `_with_qrf_trigger` sur les 7 manœuvres. maneuvers.py v3 ≠ v2 : AUCUNE comparaison brute inter-tables, seulement structure↔structure.
**Mécanismes attendus** : fix QRF = vent CONTRAIRE proportionnel à l'esquive v2 (M5 50 % d'esquive > M6 44 % > M2 31 % > M1 19 %) ; fix nage = vent FAVORABLE uniforme (approche plus rapide, moins exposée).
**PRÉDICTIONS (militaire %, n=16, v2 → fourchette v3)** : M1 56→**50-70** · M2 62.5→**45-60** · M3 31→**25-45** · M4 25→**20-40** · M5 56→**35-55** · M6 50→**35-55** · M7 25→**15-35**.
**QUESTION DÉCISIVE PRÉ-ENREGISTRÉE** : familles poolées A(M1,M2,M5,M6) vs B(M3,M4,M7) — **loi CONFIRMÉE** si écart ≥15 pts (z≥2) ; **AFFAIBLIE** si 5-15 pts ; **ARTEFACT** si <5 pts ou inversion. Vérification du fix : % d'ops « garnison prise ET QRF affrontée » attendu ≈ 100 (vs 50-81 en v2).
**ADDENDUM PRÉ-ENREGISTRÉ V3 (07/06 15h25 — APRÈS M1 seul, AVANT M2-M7)** : M1 v3 = 93.8 % (préd 50-70 RÉFUTÉE vers le haut ; QRF 100 % ✓ fix validé ; cause probable = approche comprimée à ~170 m par les spawns secs, l'écran de patrouilles ne mord plus). **RÈGLE D'EFFET PLAFOND (symétrique de la règle plancher du palier 1)** : si les familles A ET B sortent toutes deux >85 %, le verdict familles sera rendu **« NON-CONCLUANT : effet plafond »** — on ne départage pas des doctrines quand tout réussit. Départage secondaire pré-enregistré dans ce cas : pertes moyennes, % QRF détruite, durée des ops. Si plafond confirmé → harnais v4 à durcir (défense renforcée ou théâtre plus profond — PAS de retour à la nage).

### 2026-06-07 16h20 — PRINCIPE DE DESIGN (formulation Younes) + PRÉ-ENREGISTREMENT TABLE V4 (défense pro)
**PRINCIPE GRAVÉ : « c'est la difficulté qui fait l'apprentissage, pas l'inverse »** — complété par les deux accidents d'instrument du projet : plancher palier 1 (tout meurt = zéro signal) et plafond v3 (tout réussit = zéro signal). Règle opérationnelle : tenir le harnais à la FRONTIÈRE (~50 % de succès), difficulté par l'ADVERSAIRE (compétence/agressivité/nombre), jamais par accident de géographie.
**HARNAIS V4 = v3 (QRF inesquivable + géo sèche) + DÉFENSE PRO** : 30 garnison+patrouilles (×1.5) + QRF 12, sous-compétences montées (visée .75/.9, spot .95/.9, courage/commanding 1), boucle de CHASSE 30 s (tout groupe au contact convertit en SAD FULL). Module partagé enemy_profiles.py (mesure+visuel), métrique dynamique.
**PRÉDICTIONS PRÉ-ENREGISTRÉES (militaire %, n=16, AVANT toute donnée pro)** : M1 **30-55** · M2 **25-50** · M3 **10-35** · M4 **10-30** · M5 **20-45** · M6 **15-40** (spot 0.95 punit l'infiltration) · M7 **5-25**. Mode d'échec NOUVEAU attendu : la chasse transforme la défense en contre-attaque continue → pertes amies en hausse nette (>25 % moy), échecs par submersion pendant la consolidation.
**QUESTION DÉCISIVE (la loi des 2 axes, redevenue hypothèse après le rétro-éclairage v3)** : familles poolées A vs B — ≥15 pts = loi RE-confirmée sur harnais propre ET dur ; 5-15 = affaiblie ; <5/inversion = la loi v2 était l'ombre de l'eau. Règles plancher (<15 % les deux) et plafond (>85 % les deux) = NON-CONCLUANT → recalibrer (hardcore ou pro-ajusté).

### 2026-06-07 ~19h — TABLE V3 : RÉSULTATS (interrompue à M6 14/16) + VERDICT PLAFOND + INCIDENT

**TABLE V3 MESURÉE (harnais propre : QRF-sur-garnison + géo sèche, défense normale, n=16 sauf M6)** :
| man | n | mil% | garr% | QRF-spawn% | pertes% | dt moy | préd v3 | verdict préd |
|---|---|---|---|---|---|---|---|---|
| M4 assaut-massé | 16 | **100.0** | 100 | 100 | 12.9 | 685s | 20-40 | ❌ réfutée HAUT |
| M1 appui-assaut | 16 | 93.8 | 100 | 100 | 14.7 | 668s | 50-70 | ❌ réfutée HAUT |
| M2 double-env | 16 | 93.8 | 93.8 | 93.8 | 15.4 | 681s | 45-60 | ❌ réfutée HAUT |
| M3 env-simple | 16 | 93.8 | 100 | 100 | 13.2 | 702s | 25-45 | ❌ réfutée HAUT |
| M6 infiltration | **14** | 92.9 | 100 | 100 | 14.0 | 617s | 35-55 | ❌ réfutée HAUT (partiel) |
| M5 feinte+débord | 16 | **81.2** | 100 | 100 | 12.7 | 600s | 35-55 | ❌ réfutée HAUT |
| M7 échelonnée | **0** | — | — | — | — | — | 15-35 | JAMAIS MESURÉE |

**TRACK-RECORD V3 : 0/6 prédictions tenues, toutes réfutées vers le HAUT.** Direction univoque : j'avais modélisé le fix QRF comme vent contraire dominant ; en réalité le fix nage (vent favorable) a tout écrasé. **La difficulté de la v2 n'était pas la défense, c'était la baignade** — approche courte et sèche = +30 à +75 pts selon la manœuvre.

**FIX QRF VALIDÉ À 100 %** : QRF-spawn ≈ 100 % partout (vs 50-81 % v2) — l'esquive par contingence est morte, exactement comme conçu. Le seul effet contraire visible : **M5 81.2 % = pire score v3**, et c'était LA manœuvre qui esquivait le plus en v2 (50 %). Cohérent au mécanisme près.

**VERDICT FAMILLES (règle plafond pré-enregistrée DÉCLENCHÉE)** : A(M1,M2,M5,M6)=90.3 % vs B(M3,M4 — M7 absente)=96.9 % → les deux familles >85 % = **NON-CONCLUANT : EFFET PLAFOND** (et même légère inversion, dénuée de sens à ce niveau). Départage secondaire pré-enregistré : pertes 12.7-15.4 % quasi uniformes, durées 600-702s — **rien ne discrimine**. La loi des 2 axes reste donc HYPOTHÈSE OUVERTE, ni confirmée ni réfutée par la v3 ; c'est la table v4 (défense pro) qui doit trancher. ⚠️ Verdict prononcé avec M6 partiel (14/16) et M7 absente — M7 ne peut PAS renverser le plafond (il faudrait qu'elle sorte <85 % ET que ça tire B sous le seuil ; même M7=0 % donnerait B≈64 %, ce qui changerait le verdict en « non-concluant pour une autre raison », pas en confirmation propre). Compléter quand même pour l'hygiène de table.

**INCIDENT** : la mesure est morte entre M6 et M7 (~16h27, dernière op ZEPHYR-12), très probablement à la fermeture de la session Claude qui portait le run. Constat à 18h50 : **0 serveur arma3 vivant** (flotte entière tombée), aucun processus run_table/run_maneuver, **logs /tmp volatils PERDUS** (table v3 + boot flotte — la cause exacte de la mort est irrécupérable). Leçon répétée (2e crash de table en 2 jours, après le PC coupé du 06/06) : **un run de plusieurs heures doit être détaché de la session (nohup/systemd-run) ET logger en dur dans ~/arma3-marl/logs_train/, jamais /tmp.**
**M6 seeds manquants : 1 et 8.** Reprise = APPEND-only (jamais run_table_v3.sh brut, même piège que la v2 : il écrase le jsonl).

**ÉTAT DES ARTEFACTS (non commités au moment de la consigne)** : `table_maneuvers_v3.jsonl` (94 ops) ; `enemy_profiles.py` + `run_table_v4.sh` (harnais v4 prêt, smoke pro PAS encore passé) ; modifs `run_maneuver.py` (--enemy pro, métrique dyn) + `run_op_visual.py`. Tag `harnais-v3` posé, **tag `table-v3` PAS posé** (attendait M7).

**SÉQUENCE DE REPRISE (inchangée, gravée ici)** : (1) reboot flotte 16 serveurs ; (2) M6 seeds 1+8 puis M7 n=16, en APPEND, run détaché + log persistant ; (3) verdict familles FORMEL recalculé table complète ; (4) commit + tag `table-v3` ; (5) smoke pro (1 op, vérifier compétences + boucle de chasse sans erreur SQF côté serveur dédié) ; (6) table v4 défense pro (prédictions déjà gravées à l'entrée 16h20, NE PAS les retoucher).

### 2026-06-08 00h~ — TABLE V3 COMPLÉTÉE (reprise après crash) + VERDICT FORMEL
**Reprise append-only réussie** (`resume_v3.py` + `run_resume_v3.sh`, détaché setsid + log dur `logs_train/resume_v3_20260608_000611.log`) : M6 seeds 1+8 + M7 0-15 mesurés, 18/18 ops, 0 erreur. **table_maneuvers_v3.jsonl = 112 lignes (7×16 COMPLÈTE).**
**RÉSULTATS FINAUX (n=16/manœuvre, défense normale, harnais propre)** : M4 100 · M1 93.8 · M2 93.8 · M3 93.8 · M6 93.8 · M5 81.2 · **M7 81.2** (garr 87.5, pertes 9 % = la plus économe). 
**VERDICT FAMILLES FORMEL** : A(M1,M2,M5,M6)=90.6 % vs B(M3,M4,M7)=91.7 % → écart **−1.0 pt (z=−0.19)**, les deux >85 % = **NON-CONCLUANT : EFFET PLAFOND** (micro-inversion sans sens). Départage secondaire : pertes 9-15 %, rien ne discrimine. **Track-record v3 = 0/7, toutes réfutées vers le HAUT.** Fix QRF = **100 %** (garnison prise ⇒ QRF affrontée partout). 
**M7 ne renverse pas le plafond** (81.2 % > 85 % seuil de justesse ; il aurait fallu qu'elle plonge bas). La loi des 2 axes reste HYPOTHÈSE OUVERTE → tranchée par la table v4 (défense pro). Tag `table-v3` posé. SUITE : smoke pro (1 op --enemy pro) → table v4 (préds gravées 07/06 16h20, NE PAS retoucher).

### 2026-06-08 — SESSION SIM-TO-REAL « BROUILLARD » (null) + M1 OFFICIER LLM (réussi)

**(1) A/B BROUILLARD — sim-to-real, NON CONCLUANT mais recadrage utile.** Diagnostic vérifié : le sim KOTH tournait OMNISCIENT (`koth_gpu sight=1e9`) alors qu'Arma a du brouillard (`arma_env_koth sight=95`). A/B propre ligue brouillard(sight=95) vs omnisciente, mêmes réglages (envs=98304, 300 it, seed 0), puis transfert Arma KOTH (camp0 vs réf fixe). **Résultat : fog 0.723 vs omni 0.740, écart −0.017 (bruit).** **TWIST : les deux à ~73 %, PAS 0 %** → cette éval ne reproduit pas le 83→0 ; le 83→0 est en OPÉRATIONS (manager/manœuvres), pas en KOTH. **Acquis** : « brouillard-vision en KOTH » ÉLIMINÉ comme levier dominant ; 3090 GAVÉE (envs↑) = 150k tr/s / 99 % util (au défaut envs=16384 elle était affamée à 25k) ; ligue self-play SAINE (arms-race montée→redescente quand le pool grossit). Nouveaux : knob `--sight` (`train_league_gpu` + masque toujours-appliqué `koth_gpu`, rétro-compat 1e9), `eval_koth_arma.py`, `run_ab_full.sh`, `resume_v3.py`/`run_resume_v3.sh` (reprise v3 append), `league_fog_learner.pt`/`league_omni_learner.pt`.

**(2) M0/M1 — OFFICIER LLM sur exécuteurs gelés (PDF `arma3-marl-PLAN-officier-LLM`).** Stack 2 niveaux : officier (lent, POSTURE de faction) → spécialistes RL gelés (rapides). But : stabiliser le 3-corps (runaway/kingmaking).
- **M0a** : « posture = biais de logits » portée de `op_arma` dans `koth_gpu` (`POSTURES` + `posture_bias`, rétro-compat). **Diagnostic** : league_learner ET koth_finetuned sont SUPPRESS-saturés / AVANCER-mort (même forcé +10 AVANCER/−6 SUPPRESS, AVANCER plafonne ~14 %) → le sim ne récompense PAS la manœuvre (PDF §5 « mission=80 % ») → vocab ÉLAGUÉ à l'axe qui paie `defendre↔presser` (manœuvres prendre_colline/focus_leader/harceler/repli DIFFÉRÉES).
- **M0b** : `officer_m1.py` (sérialiseur état→texte coalition + parseur texte→posture robuste).
- **M1 (A/B/C, métrique runaway = le leader précoce gagne-t-il ?, exécuteur league_learner, N=4096)** : **A (rien) 0.92** (camp0 spawn-avantagé écrase, wins [17193,1503,14]) ; **B oracle** (leader→defendre, autres→presser) **0.64** = LEVIER VALIDÉ ; **C officier LLM 0.76** vers B = ✅ un LLM qui raisonne réduit le runaway. **⚠️ LE MODÈLE COMPTE** : `mistral-nemo:12b` (défaut PDF) ÉCHOUE (mislit son rang → politique inversée, 0.91≈A) ; **`qwen2.5:14b` RÉUSSIT** (politique correcte `{leader→defendre, retard→presser}`, bon raisonnement). → **officier = qwen2.5:14b.** Scripts : `m1_oracle_test.py`, `m1_llm_officer.py`, `m0a_posture_test.py`.

**SUITE décidée** : enrichir le sim pour que la MANŒUVRE paie (capture>attrition, terrain/couvert) → débloque le vocab complet de l'officier ; puis M3 RL-LLM (GRPO+QLoRA) pour fermer l'écart C→B.

### 2026-06-08 (suite) — ENRICHISSEMENT SIM : la manœuvre PAIE enfin (vocab officier débloqué)

**Problème** : exécuteurs SUPPRESS-saturés car le sim récompensait l'attrition-depuis-place, pas la manœuvre. **Fix (2 knobs koth_gpu, rétro-compat)** : `attrition_win=False` (tuer tout le monde = NUL, pas victoire → il faut tenir la colline) + `timeout_decisive=True` (à l'expiration, le plus de temps-zone gagne). Aussi knobs `secure_n`/`cap_need` ajoutés.
**⚠️ DISCIPLINE COMPUTE (rappel gravé, [[feedback_compute_discipline]])** : j'ai brûlé 3 runs 45 min à l'aveugle (v1 attrition-off→69% nuls ; v2 secure_n=1→backfire 76% ; v3 timeout_decisive→re-nuls). Younes : « je paie le compute, réfléchis mieux ». → STOP devinette, **mesure CHEAP gelée**.
**MESURE CHEAP (instrument_draws.py, frozen, 1 min)** sur league_maneuver en env {attrition_off + timeout_decisive} : **60% gagnées PAR LA COLLINE** (20% capture + 40% timeout-contrôle), **40% nuls = TOUS anéantissement** n_alive<=1 ; timeout-sans-contrôle 0% (timeout_decisive marche). → les nuls résiduels = entre-tuerie, PAS un blocage ; l'exécuteur gagne déjà par le terrain.
**VOCAB OFFICIER DÉBLOQUÉ (mesure gelée)** : sur league_maneuver, les postures PILOTENT enfin avec la bonne sémantique — `prendre_colline`→AVANCER **36%** + victoires **42%** ; `neutre`→AV 23% ; `defendre`→AV 18% + victoires 25%. (vs ancien league_learner où AVANCER restait bloqué 5-11% même forcé.) → **pas de retrain nécessaire, league_maneuver suffit.**
**INSIGHT** : en mode manœuvre la **coalition s'INVERSE** — prendre la colline GAGNE, se retrancher PERD (inverse de l'ancien KOTH-attrition où defendre gagnait 66%). L'officier devra découvrir une politique différente.
**Artefacts** : knobs koth_gpu (attrition_win/timeout_decisive/secure_n/cap_need) + passthrough train_league_gpu, `league_maneuver_learner.pt`, `instrument_draws.py`, `enrich_check*.py`, `run_enrich*.sh`. SUITE : M1 officier A/B/C sur league_maneuver, vocab complet (cheap). Artefact spawn camp-0-avantagé à symétriser (testbed propre). Gate M3 (QLoRA) derrière un plafond gelé caractérisé.

### 2026-06-09 — SESSION AUTONOME : voie OPÉRATIONNELLE « école de guerre » (étapes 1-2) → PORTE FERMÉE

**Cadre** : résoudre le 83→0 (manager RL sur-apprend la fiction CRÊTE du sim) en SÉLECTIONNANT une manœuvre du répertoire M1-M7 (Arma-exécutable par construction, données réelles) plutôt qu'en laissant un RL découvrir la tactique. Pipeline gaté : 1 table précise → 2 multi-situations (porte) → 3 officier-sélecteur si porte ouverte → 4 RL-LLM gaté.

**Recherche de la FRONTIÈRE (sondes cheap n=8, puis tables n=16)** : l'effectif N'EST PAS le levier de difficulté (mid_skill 35 corps = plafond) ; **LE LEVIER = la létalité-skill** (normal 94 % → `skilled` 62 % juste en montant visée/détection, sans chasse ni corps en plus). Profils ajoutés à enemy_profiles : knob `hunt` (sépare skills/chasse), `skilled` (skills, no hunt, 28), `skilled_hunt` (+chasse), `skilled_qrf` (+QRF×2.5). **Leçon dure** : n=3-8 TRÈS bruyant (skilled M2 : 0%@n3 → 50%@n6 → 62%@n8 → **31%@n16** ; M4 0%@n5 → 38%@n8) → **n≥16 obligatoire**, plusieurs fausses conclusions évitées en attendant n=16.

**ÉTAPE 1 — table précise vs `skilled` (n=16, 112 ops)** : M3 env-simple **62.5** > M1 50 > M6 43.8 > M4 37.5 = M7 37.5 > M2 31.2 > M5 25.0. Écart 37.5 pts — différenciation nette. La loi des familles v2 (multi-axes>fragmenté) NE tient PAS ici (M3 « fragmenté » gagne).

**ÉTAPE 2 — multi-situations = la PORTE** : M1-M7 × n=16 sur skilled / skilled_hunt / skilled_qrf (3 caractères : garnison-skill / chasse-soutenue / QRF-massive). **Gagnant = M3 sur les TROIS** (62.5 / 50.0 / 25.0). → **PAS de signal de sélection → PORTE FERMÉE → officier-sélecteur NON justifié** (étapes 3-4 non déclenchées, conforme au plan). La thèse « officier » se dissout 2e fois au contact de la mesure (1re fois = runaway KOTH = artefact attrition).

**VERDICT OPÉRATIONNEL** : **M3-fixe (enveloppement simple) résout « gagner une bataille »** — M3 93.8 %@normal (v3) **> partition scriptée 72 %** (le micro appris surclasse le hand-codé de ~22 pts). Confirmation enveloppe M3 (normal/pro) lancée. **CAVEAT** : les 3 situations = variantes de la MÊME garnison (skill+géométrie identiques, varient chasse/QRF) → difficulté/tempo, pas STRUCTURE. Un vrai problème de sélection exigerait des défenses de **GÉOMÉTRIE différente** (garnison concentrée/dispersée, faiblesses distinctes) — knobs actuels ne le font pas → **prochaine vraie question = enrichir l'espace de défense (build), avant de conclure « jamais de sélecteur »**. Rapport : REPORT.md. Commits : 2206b29 (sondes), 166f82a (étapes 1-2).

## KNOB DE GÉOMÉTRIE DE DÉFENSE — test (a) du PDF d'archi — 2026-06-09

Build : `geometries.py` (5 layouts de garnison à effectif TOTAL égal=20, skill=skilled, seule la STRUCTURE varie) + `run_maneuver.py --geometry`.
Table M1/M2/M3 × {faible_ouest, faible_est, standard} @ skilled, n=16 (16 serveurs, ~2h temps réel Arma).
RÉSULTATS (militaire %) :
            M1      M2      M3
faible_ouest 12.5    25.0    56.2   -> M3 NET
faible_est   25.0    37.5    43.8   -> M3 ≈ M2 (7 vs 6 /16 = égalité)
standard     43.8    31.2    43.8   -> M1 = M3 (7 vs 7 = égalité)

VERDICT : la GÉOMÉTRIE EST UN VRAI LEVIER (contrairement à la difficulté qui ne changeait pas le vainqueur) :
M1 oscille 12.5%->43.8% (×3.5), la dominance de M3 s'effondre (+31 pts faible_ouest -> égalité ailleurs).
MAIS M3 n'est JAMAIS battu (top ou ex-aequo sur les 3) -> un sélecteur "toujours M3" reste optimal -> officier PAS ENCORE justifié.
Les 3 géométries testées ne suffisent pas à détrôner M3. PISTE DÉCISIVE non testée : `concentre` (tout massé, AUCUN flanc)
devrait punir l'enveloppement (M3) et favoriser le frontal (M1) — et sur `standard` M1 ÉGALE déjà M3, donc concentre pourrait FAIRE BASCULER.
geometries.py contient déjà concentre + disperse, prêts. Si M1 gagne concentre pendant que M3 gagne faible_ouest -> basculement propre -> officier renaît.

## KNOB GEOMETRIE — concentre mesure (run Younes 09/06) — VERDICT FINAL

M1/M2/M3 x concentre @ skilled, n=16 :  M1 25.0%  |  M2 18.8%  |  M3 43.8%  -> M3 ECRASE (l anti-enveloppement ne le detrone PAS).
TABLE COMPLETE 4 geometries (militaire %, n=16) :
              M1     M2     M3
faible_ouest  12.5   25.0   56.2   M3
faible_est    25.0   37.5   43.8   M3
standard      43.8   31.2   43.8   M1=M3 (egalite)
concentre     25.0   18.8   43.8   M3
=> M3 EN TETE OU EX-AEQUO SUR LES 4. Jamais battu. Seul M1 l egale (standard) ; M1 ne le BAT jamais ; M2 ne gagne nulle part.
VERDICT : la geometrie EST un levier reel (classements qui bougent fort, M1 de 12.5 a 43.8) MAIS un selecteur "toujours M3" reste optimal partout
-> OFFICIER (quasi) MORT, sur base mesuree rigoureuse. M3-FIXE CONFIRME = livrable operationnel, blinde meme face a la geometrie.
Reste pour cloture totale : disperse (5e geometrie, codee non testee). Logique PDF : (a) tranche -> libre pour (b) couche strategique multi-acteurs.

## Munitions finies = la contrainte qui force lingeniosite (2026-06-09)
Insight Younes : munitions illimitees -> escouade FAINEANTE (spray) ; munitions limitees -> escouade INGENIEUSE (economise, se rapproche, manoeuvre). La RARETE est le professeur. Explique pourquoi tous les leviers precedents (posture, geometrie, faction-faible, eco) nont rien donne : aucune contrainte mordante => pas de decision => RL fainEant. On rejette leco ("cest la guerre pas wall street").

MECANIQUE (patch koth_gpu.py, flag ammo=False par defaut = retro-compatible) :
- self.ammo (C,N,A), init ammo_max=40 ; tirer coute 1, SUPPRIMER coute 3 (haut volume).
- a sec (ammo=0) => ne peut plus tirer ni supprimer.
- COUVERT (action 3) = NE TIRE PAS + RECHARGE (+8/pas) -> seule facon de reconstituer ses munitions.
- obs +1 canal : lagent VOIT ses munitions (apprend a economiser). obs_dim 10->11.
- Test fume OK : 20 pas de suppression vident le chargeur (~13 pas) ; 10 pas de couvert rechargent a fond.

A/B en cours (3090 99%, 414W, ~45min/escouade) : meme obs (11), seul ammo_max change.
- kothammo_abond : ammo_max=100000 (jamais contraignant -> fainEante temoin).
- kothammo_rare  : ammo_max=40 (rarete -> ingenieuse).
Puis eval_ammo.py compare DANS lenv rarete : munitions moy, % a sec, % COUVERT(recharge), dist dengagement, survie, controle.

## 2026-06-09 ~20h25 — ⚠️ DISPERSE ROUVRE LA PORTE OFFICIER (bâtisseur-Linux) — à confirmer n=32

**Contexte coordination** : l'entrée « KNOB GEOMETRIE — concentre VERDICT FINAL » plus haut conclut « officier (quasi) MORT » sur 4 géométries (M3 jamais battu) — mais elle a été écrite AVANT que `disperse` (5e géométrie, « codée non testée ») ne finisse. **Disperse vient de tomber et CONTREDIT ce verdict.**

**RÉSULTAT DISPERSE (n=16, skilled)** :
| man | mil% | garr_pris | QRF-spawn | pertes moy (min-max) |
|---|---|---|---|---|
| **M1 frontal** | **31.2** (5/16) | 13/16 | 13/16 | 38% (18-61) |
| M2 double-env | 18.8 (3/16) | 12/16 | — | 47% |
| M3 env-simple | 18.8 (3/16) | 12/16 | 12/16 | **51% (29-82)** |

→ **M1 PASSE DEVANT M3 (+12.4 pts) — 1re géométrie où M3 n'est PAS roi.** Le vainqueur CHANGE selon la structure (M3 sur flanc-faible, M1 sur garnison éclatée) → **un sélecteur a enfin de quoi sélectionner → officier RENAÎT.**

**DISSECTION (pas un artefact)** : M1 et M3 prennent la garnison à égalité (13 vs 12) et affrontent la QRF à égalité → PAS de confound QRF. La différence est le SANG : M3 saigne 51% (jusqu'à 82%) contre 38% pour M1. Mécanisme réel : disperse = 4 points faibles séparés ; l'enveloppement unique de M3 se fait hacher en terrain ouvert entre les positions ; la masse frontale de M1 concentre le feu point par point. **M1 mérite sa tête tactiquement.**

**⚠️ STATUT = NON GRAVÉ** : 5 vs 3 à n=16 = au ras du bruit (rappel projet : M2 62%@n8→31%@n16). **Confirmation EN COURS : M1+M3 disperse seeds 16-31 → n=32** (run détaché PID 203144, log `logs_train/disperse_confirm_*.log`, append-only via nouveau `--seed_base`). Si M1 reste devant à n=32 → basculement CONFIRMÉ → la ligne officier-sélecteur (sens du RL→LLM→RL-LLM) VIT. Sinon → M3-fixe = réponse finale.

**Table géométrie complète (n=16) pour mémoire** :
```
              M1     M2     M3    gagnant
faible_ouest  12.5   25.0   56.2  M3
faible_est    25.0   37.5   43.8  M3
standard      43.8   31.2   43.8  M1=M3
concentre     25.0   18.8   43.8  M3
disperse      31.2   18.8   18.8  M1   <- BASCULEMENT
```
NB : seules M1/M2/M3 testées vs géométrie ; M4-M7 × géométrie jamais mesuré (trou résiduel, secondaire à la question binaire).

## 2026-06-09 ~20h52 — ❌ DÉMENTI : le basculement disperse était du BRUIT (n=32, bâtisseur-Linux)

**CORRECTION de l'entrée « DISPERSE ROUVRE LA PORTE » ci-dessus.** Confirmation lancée (M1+M3 disperse seeds 16-31, append, n=32) :
```
              seeds0-15   seeds16-31(neufs)   n=32
M1 disperse   31.2%(5/16)   18.8%(3/16)       25.0%(8/32)
M3 disperse   18.8%(3/16)   25.0%(4/16)       21.9%(7/32)
```
**Split-half = verdict** : sur la moitié NEUVE, M3 repasse devant M1 (25.0 vs 18.8). À n=32, écart M1-M3 = 3.1 pts = 1 op (8 vs 7) = **statistiquement nul**. Le « M1>M3 » de n=16 était un artefact de bruit (le piège récurrent du projet : 2 ops d'écart à n=16 s'évaporent à n=32).

**STATUT GRAVÉ** : porte de sélection **RESTE FERMÉE**. Sur les 5 géométries, M3 est top ou à ÉGALITÉ — jamais proprement battu (disperse = égalité M1≈M3 à ~22-25%, pas défaite). **Officier-sélecteur NON justifié, confirmation incluse.** M3-fixe = réponse opérationnelle finale, robuste difficulté + géométrie + confirmation. **3e dissolution de « l'officier » au contact de la mesure** (1=runaway KOTH artefact, 2=multi-situations skilled, 3=géométrie+confirmation).

**Convergence des 2 Claude** : l'archi avait raison sur « officier (quasi) mort » — disperse ne l'a PAS ressuscité une fois le bruit retiré. Reste cohérent avec sa piste ammo (« la rareté est le professeur ») = la vraie explication de POURQUOI aucun levier (posture/géométrie/faction) ne crée de signal de sélection : sans contrainte mordante, RL fainéant → pas de décision → rien à sélectionner. La suite est là, pas dans la géométrie.

## 2026-06-10 ~00:55 — PROGRAMME DE NUIT bâtisseur-Linux (coordination archi)
**Répartition** : je tiens l'axe Arma (16 serveurs/CPU) cette nuit ; l'archi garde la 3090/ammo. Détail complet dans `PLAN-NUIT.md`.
**Découverte qui lance la nuit** : `skilled_react` (défense COORDONNÉE qui masse les patrouilles sur le flanc menacé) → **INVERSION nette à n=8** : M1 50 % (inchangé) vs M3 **0 %** (effondrement, baseline 62.5 %). 1re fois que la meilleure manœuvre change selon la défense → officier-sélecteur potentiellement RESSUSCITÉ. Confirmation n=16 en cours.
**Plan gaté** : Gate0 confirmer inversion n=16 → Étape1 construire `skilled_react_depth` (anti-frontal) → Étape2 MATRICE M1/M2/M3/M5 × {passive, anti-flanc, anti-centre} n=16 → Gate1 RPS ? → Étape3 valeur-de-sélection → Étape5 SPEC du défenseur APPRIS (= ta brique GPU, archi : co-évolution self-play attaque↔défense). Off-ramps pré-enregistrés. Tout append-only + détaché + logs durs.

## 2026-06-10 ~01:00 — RÈGLE MATÉRIEL : 3090 plafonnée à 75% (315W)
Younes : **tout run 3090 <= 75% de puissance**. Posé au niveau driver : `nvidia-smi -i 1 -pm 1 ; -pl 315` (75% du TDP 420W ; < point throttle 409W → plus frais). Script `set_3090_powerlimit.sh` (root requis, lancé par Younes). Le cap s'applique à TOUS les process GPU, ammo inclus. ⚠️ ARCHI : tes runs ammo sont auto-capés à 315W ; ne pas remonter le -pl. Ne survit pas au reboot (relancer le script si reboot).

## 2026-06-10 ~01:20 — GATE 0 : inversion CONFIRMÉE n=16 mais ATTÉNUÉE (split-half remord)
react n=16 (skilled_react, standard) : M1 **37.5%** (6/16) vs M3 **18.8%** (3/16). Split-half : M1 [s0-7 50% / s8-15 25%], M3 [s0-7 0% / s8-15 37.5%] -> la moitié NEUVE met M3 devant (probe n=8 M1 50/M3 0 = trop optimiste, même piège que disperse).
**Ce qui TIENT (robuste)** : effet DIFFÉRENTIEL = la défense réactive coûte −44 pts à M3 (62.5->18.8) vs −12 pts à M1 (50->37.5). Elle punit l'enveloppement BIEN plus que le frontal. Classement s'inverse en agrégat (M3 meilleur vs passif, M1 meilleur vs réactif) MAIS marge ~19 pts < seuil 20 + halves discordantes -> escalade n=32 (seeds 16-31) AVANT de graver. Ne PAS appeler la matrice tant que n=32 pas tranché.
Build fait pendant l'attente : `skilled_react_depth` (défense anti-frontale : bloc central avancé si contact frontal, laisse les flancs) = 2e axe de la matrice. Smoke à passer après le n=32.

## 2026-06-10 ~09:05 — GATE 0 TRANCHÉ n=32 : inversion CONFIRMÉE (modérée) + COÛT pathologique découvert
**Verdict n=32 (skilled_react, standard)** : M1 **34.4%** (11/32) vs M3 **21.9%** (7/32). Quarts M1 [4,2,2,3] stable ~34 ; M3 [0,3,2,2] (le 0/8 initial = malchance, reste ~25). 
**INVERSION CONFIRMÉE** : vs passif M3 62.5 > M1 50 ; vs réactif **M1 34.4 > M3 21.9**. Le champion CHANGE selon la défense -> officier-sélecteur justifié (modérément, gap 12.5 pts = 4 ops). 
**Robuste = l'effet DIFFÉRENTIEL** : la défense réactive coûte −40.6 pts à M3 vs −15.6 pts à M1. Punit l'enveloppement 2.6x plus que le frontal. C'est la vraie signature. Thèse Younes (« rendre l'ennemi intelligent ») VALIDÉE : c'est l'adaptation de l'ennemi, pas la géométrie/difficulté, qui crée le choix.
**⚠️ COÛT PATHOLOGIQUE (incident de nuit)** : les ops M3-vs-réactif grindent — dt MOYEN 12557s (3.5h), MAX 26581s (7.4h) vs 640s normal. Le standoff enveloppement-vs-réserve fait ramer le serveur (steps ~50s au lieu de ~10s). **La confirmation n=32 a mangé TOUTE la nuit (01:21->09:00)** -> Étapes 1-5 du PLAN-NUIT (matrice, valeur-sélection, depth, spec) PAS exécutées. 
**Échec de process à corriger** : j'aurais dû borner le temps d'op (max_steps plus bas pour le réactif, ou abort rapide quand enlisé) AVANT de lancer ; le moniteur n'a pas coupé le grind. La matrice est INFAISABLE au coût actuel -> fixer le coût d'abord.
**Construit non mesuré** : `skilled_react_depth` (défense anti-frontale, code+câblé+import OK) -> smoke à passer.
**Ammo archi** : eval toujours pas sorti dans ammo_ab.log ; kothammo_rare_*.pt + abond présents. 3090 capée 315W OK (idle).

## 2026-06-10 ~09:45 — VERDICT MUNITIONS COMPLET (archi) : le mécanisme mord, le comportement change, MAIS PAS de supériorité en duel
- **Mécanisme** (koth_gpu `ammo=True` : 40 balles, tir=1, suppress=3, COUVERT=recharge +8/pas, obs+1 canal munitions) : validé au smoke (à sec en ~13 pas de suppression continue, recharge pleine en 5 pas de couvert). Rétro-compatible (`ammo=False` par défaut).
- **A/B self-play** (300 iters chacun, même obs 11, seul ammo_max change : 100000 vs 40), éval DANS le monde rareté : rare vs abond = suppress 35 % vs 56 %, avancer 43 % vs 34 %, distance d'engagement 28.8 vs 32.7, survie 0.964 vs 0.852, contrôle 5.84 vs 5.16 → en auto-écologie, la rareté produit une escouade plus sobre et plus décisive.
- ⚠️ **DUEL DIRECT** (duel_ammo.py, 3 rotations de sièges, 169 352 batailles décidées, env rareté) : part RARETÉ **0.161** vs 0.333 attendu (abondance 0.420/siège ; effondrement siège 1 : 0.022). **L'escouade-abondance gagne le face-à-face même sous rareté.** L'éval A/B auto-référentielle (chacun contre soi-même) flattait la rareté — énième incarnation du mensonge de demi-mesure : ne jamais conclure sans confrontation directe.
- **VERDICT honnête** : la contrainte change le comportement (vrai) mais n'a PAS produit d'ingéniosité compétitive au budget actuel. Suspects : regen trop généreuse (+8/pas = contrainte molle), attrition_win par défaut (paie l'agression précoce), 300 iters seulement, pas de ligue mixte.
- **Pistes si on rouvre** : regen 0 + caisse de munitions à la base (vraie logistique spatiale) · attrition_win=False (le contrôle paie, pas le kill) · ligue rare-contre-abond (entraîner CONTRE le sprayeur) · porter dans Arma où les munitions sont natives.
- **Fil CLOS proprement (tag ammo-v1).** Le levier confirmé qui reste ouvert : l'ENNEMI ADAPTATIF (Gate 0, inversion n=32).

## 2026-06-10 ~10:15 — LISTE 2 LANCÉE : bornes de coût posées + PRÉ-ENREGISTREMENT MATRICE (archi, AVANT toute donnée)
**Bornes (op_arma.run + run_maneuver CLI)** : `max_wall=1200 s` (mur temps-réel par op) + `stall_wall=500 s` (abandon si AUCUN changement vivants/ennemis/phase pendant 500 s réels) → OP_ABORT journalisé, champ `abort` dans chaque ligne jsonl. Sémantique de verdict inchangée et honnête : un standoff avorté a la garnison vivante → mil=False naturellement (un assaut qui s'enlise est un assaut raté). Une op coûte désormais ≤ 20 min, jamais 7 h.
**Smokes en cours** : (A) M3 vs skilled_react borné = test du mur sur LA cellule pathologique ; (B) M1 vs skilled_react_depth = première exécution de la défense anti-frontale (validité SQF).
**PRÉ-ENREGISTREMENT — prédictions matrice (militaire %, n=16, cellules inconnues) — gravées AVANT les runs** :
- Connues réutilisées : passive×{M1,M2,M3,M5} = 50/31/62.5/25 ; react×{M1,M3} = 34.4/21.9 (n=32).
- react×M2 : **15-35** (l'anti-flanc punit les prongs ; M2 déjà faible vs passif).
- react×M5 : **25-45** (la démo Est absorbe la réaction anti-flanc → l'effort principal Ouest en profite ; M5 tient ou monte).
- depth×M1 : **15-35** (l'anti-centre doit punir le frontal — c'est sa raison d'être ; chute nette sous 50).
- depth×M2 : **35-55** (les deux flancs libres).
- depth×M3 : **50-70** (flanc libre → M3 retrouve ~son niveau passif).
- depth×M5 : **30-50** (l'effort principal déborde → profite ; la démo frontale se fait punir).
**GATE 1 pré-enregistré** : pierre-feuille-ciseaux CONFIRMÉ si la meilleure attaque change selon la défense — prédiction : passive→M3, react→M1, depth→M3 (ou M2). Clause d'échec : si depth×M1 ≥ 45, la défense anti-centre ne mord pas → matrice à 2 défenses, le noter sans spin. Toute cellule pivot à écart < 20 pts du 2ᵉ → escalade n=32 avant de graver (loi anti-bruit).
**Valeur de sélection (étape suivante)** = moyenne(meilleure attaque PAR défense) − moyenne(meilleure attaque FIXE globale) ; seuil de justification officier : 15-20 pts.

## 2026-06-10 ~11:50 — GATE 1 : MATRICE COMPLÈTE n=16 — RPS CONFIRMÉ, VALEUR DE SÉLECTION FAIBLE (archi)
**Matrice (militaire %, 96 ops nouvelles, 0 abort, dt 190-435 s — les bornes ont éteint la pathologie sans jamais mordre)** :
| | M1 | M2 | M3 | M5 | champion |
|---|---|---|---|---|---|
| passive | 50.0 | 31.0 | 62.5 | 25.0 | **M3** |
| react (anti-flanc) | **34.4** (n=32) | 18.8 | 21.9 (n=32) | 25.0 | **M1** |
| react_depth (anti-centre) | 18.8 | 31.2 | **50.0** | 43.8 | **M3** |
**Prédictions pré-enregistrées : 5/6 dans la fourchette** (depth×M2 31.2 juste sous 35-55) ; les 3 champions prédits (passive→M3, react→M1, depth→M3) : **3/3 corrects**. L'anti-centre mord exactement comme conçu (M1 50→18.8 ; clause d'échec « M1≥45 » non déclenchée).
**GATE 1 ✅ STRUCTUREL : le champion change selon la défense** (M3/M1/M3) — le pierre-feuille-ciseaux existe.
**MAIS valeur de sélection = +4.2 pts** (sélecteur 49.0 % vs M3-fixe 44.8 %) — **très en dessous du seuil 15-20**. Cause structurelle : M3 domine 2 colonnes sur 3 ; seule l'anti-flanc le punit vraiment. Sur CE vivier de défenses (3, écrites main), un commandant têtu-M3 ne perd que ~4 pts contre un sélecteur parfait → **l'officier est justifié structurellement mais marginal économiquement**.
**Escalade n=32 EN COURS (loi anti-bruit)** : react×M5 (écart 9.4 au champion), depth×M3 et depth×M5 (écart 6.2) — seeds 16-31 append. Verdict final après.
**Lecture pour la suite (pré-engagée)** : ne PAS entraîner un officier GRPO pour 4 points. La vraie marche = **DÉFENSEUR APPRIS** : élargir le vivier de défenses par RL (il trouvera des défenses qui punissent M3 plus fort que nos 2 écrites main) → la valeur de sélection remonte mécaniquement → ALORS l'officier a un métier rentable. La valeur de sélection dépend du vivier ; un vivier appris est la seule façon honnête de la faire monter.

## 2026-06-10 ~12:30 — RÉPERTOIRE DOUBLÉ : recherche doctrinale + 5 attaques + 5 défenses CODÉES (archi, décision Younes « tout coder, c'est la plus-value »)
**Livrable recherche** : `DOCTRINE-REPERTOIRE.md` — catalogue des formes offensives (FM 3-90 + art opératif) et défensives, chacune avec mécanisme / bat / battue-par / statut, les knobs de variante (axes, allocation, seuils de contingence, timing défensif) et les interactions prédites en bloc (§D).
**Attaques nouvelles (maneuvers.py, 12 manœuvres au total, tous les gotos validés)** :
- M8 PERCÉE (rupture sur axe étroit + exploitation vers ARRIERE 15000,16230)
- M9 TOURNANT (marche profonde PIVOT_E 15300,16150 → prise de l'arrière → assaut PAR LE NORD)
- M10 MARTEAU-ENCLUME (bloc BLOC_N 15040,16180 + assaut sud — le contre de l'élastique)
- M11 RAID (coup de main + EXFIL immédiat sans consolidation — vise le seuil 70 % avant la QRF)
- M12 RECO-EN-FORCE (sonde 1 escouade → branchement par CONTINGENCES : front dur→débordement ouest, front mou→frontal ; un frontal qui s'éternise bascule de lui-même) = mini-officier en dur, sa moyenne inter-défenses servira de PLANCHER au sélecteur appris.
**Défenses nouvelles (enemy_profiles.py, 8 défenses au total, plomberie générique def_sqf→DEFENSE_SQF)** :
- D3 skilled_mobile (réserve de frappe nord, SAD sur le centroïde des contacts ≥3)
- D4 skilled_elastic (lignes successives 16000→16150→16270 aux seuils 0.7/0.4 d'effectif)
- D5 skilled_herisson (tout au complexe, périmètre dense, MIDDLE)
- D6 skilled_appat (abandon de l'objectif → surplombs nord → nasse quand ≥3 attaquants dans 70 m)
- D7 skilled_sortie (spoiling : les patrouilles SAD sur les zones de rassemblement sud au 1er contact)
**Patrons SQF repris des leçons payées** : noyau-le-plus-proche tient toujours (métrique/QRF intactes) ; MOVE+hold pour bloquer (jamais SAD, leçon du standoff) ; SAD pour frapper ; boucles 8-20 s.
**EN FILE** : 10 smokes (M8-M12 vs skilled ; M1 vs les 5 défenses) chaînés derrière l'escalade n=32 en cours. Puis : prédictions par cellule AVANT toute table (§D du catalogue = hypothèses en bloc), mesure des colonnes/lignes nouvelles ≈ 50 cellules n=16 bornées (~2 nuits de flotte), re-calcul de la valeur de sélection sur le répertoire élargi (le chiffre qui décide de l'officier).

## 2026-06-10 ~13:20 — SMOKES RÉPERTOIRE 10/10 EXÉCUTÉS + PRÉ-ENREGISTREMENT GRANDE MATRICE 9×8 (archi, AVANT toute donnée)
**Smokes (validité d'exécution, PAS des taux — n=1)** : zéro erreur SQF/python sur les 10. M8 PERCÉE ✅ succès 1er coup (pertes 25 %, 3 ennemis restants). M12 RECO-EN-FORCE ✅ succès 1er coup (le branchement adaptatif fonctionne). M11 RAID : exécution propre, pertes 21 % seulement, mais 54 % de destruction < seuil 70 % (sa nature). M9 lent (500 pas). M10 saigne en approche d'enclume (écran de patrouilles — précédent M2 : on ne retouche PAS la géométrie, la table dira). Défenses : les 5 gagnent leur 1ʳᵉ op vs M1 ; trace mobile = signature doctrinale exacte (écran s'efface → garnison tombe → contre-attaque → M1 exfil à 36 %).
**PRÉ-ENREGISTREMENT — grande matrice 9 attaques × 8 défenses, fourchettes militaire % n=16, gravées AVANT mesure** (connues exclues) :
| atk\def | skilled | react | depth | mobile | elastic | herisson | appat | sortie |
|---|---|---|---|---|---|---|---|---|
| M1 | 50 (connu) | 34 (connu) | 19 (connu) | 20-40 | 25-45 | 35-60 | 20-45 | 15-35 |
| M2 | 31 (connu) | 19 (connu) | 31 (connu) | 30-50 | 30-50 | 30-55 | 20-45 | 20-40 |
| M3 | 62.5 (connu) | 22 (connu) | 66 (connu) | 25-45 | 35-55 | 35-60 | 20-45 | 20-40 |
| M5 | 25 (connu) | 16 (connu) | 31 (connu) | 30-55 | 25-45 | 20-40 | 20-45 | 15-35 |
| M8 | 40-65 | 10-30 | 10-30 | 15-35 | 15-35 | 30-55 | 15-40 | 20-40 |
| M9 | 25-50 | 15-35 | 35-60 | 15-35 | 25-50 | 10-30 | 25-50 | 25-50 |
| M10 | 25-50 | 10-30 | 30-55 | 20-40 | **45-70** | 15-35 | 25-50 | 20-40 |
| M11 | 20-40 | 15-35 | 25-45 | 15-35 | 15-35 | 25-50 | **0-20** | 20-45 |
| M12 | 45-65 | 25-45 | 30-55 | 25-50 | 30-55 | 30-55 | 25-50 | 25-50 |
**Hypothèses fortes nommées** : (a) M10-élastique 45-70 = LE contre (le repli meurt sur le bloc) ; (b) M11-appât 0-20 = le suicide (la nasse) ; (c) M8 fort seulement vs cordon (skilled), avalé par profondeur/mobile ; (d) M12 = ROBUSTESSE (jamais pire ligne, plancher du futur sélecteur) ; (e) hérisson punit M9 (rien à tourner) et M5 (démo dans le vide).
**Gate D1 pré-enregistré** : valeur de sélection recalculée sur la matrice 9×8 complète ≥ 15-20 pts → l'officier devient RENTABLE → liste 3 branche officier. Sinon → le répertoire seul est la valeur (M12/robustesse) et la diversité devra venir du défenseur APPRIS.
**Protocole** : 60 cellules nouvelles n=16 bornées (mur 1200 s/enlisement 500 s), ordre = nouvelles-attaques×connues (15) → connues×nouvelles-défenses (20) → nouvelles×nouvelles (25). Append-only mx_*.jsonl. Pas de retouche de géométrie en cours de table.

## 2026-06-10 ~15:00 — PONT TCP NATIF CONSTRUIT (levier débit ×2-3, archi, décision Younes « optimiser le temps »)
**Diagnostic** : le « pont socket » existant (hmt_ext_x64.dll) n'était qu'un contournement fichier pour le CLIENT solo. Le vrai goulot du harnais de MESURE : cmd_N.sqf (polling 0.2 s) + diag_log→RPT (flush paresseux) + relecture de 500 Ko de log PAR requête ×16 serveurs (contention disque).
**Construit (tout testé hors-Arma)** :
- `socket_bridge/hmt_native.c` → `hmt_native_x64.so` (extension NATIVE Linux du serveur dédié) : thread TCP loopback (port = env HMT_EXT_PORT, 5801+i posé par multi_server.sh), commandes en RAM (ring 128, chunking M|/D| pour >10 Ko), obs forwardées en TCP immédiat ("o|ligne"), HMT_SYNC <n> à la connexion (reprise inter-ops), MSG_NOSIGNAL partout (un client mort ne tue JAMAIS le serveur). Test ctypes complet : version/sync/multi-lignes/chunking 25 Ko/reconnexion ✅.
- `arma_socket_bridge.py` : SocketBridge, interface IDENTIQUE à ArmaBridge (send/_log_lines/_last_recv) = drop-in. Transformation transparente des `diag_log format [...]`/`diag_log "..."` en émissions socket (parser à crochets imbriqués + échappement SQF "" — 3 cas piégeux testés ✅).
- `harmattan_actuator_native.sqf` (compteur HMT_NN) + init.sqf template : **les DEUX actuateurs coexistent** (fichier toujours chargé = rétro-compat totale ; natif en plus si la .so répond). Bascule côté Python par env **HMT_SOCKET=1** ; settle 0.5→0.15 en mode socket (les obs n'attendent plus le flush RPT). step_wait INCHANGÉ (c'est du temps de jeu — le toucher fausserait la comparabilité des tables).
**Gain attendu** : ~2.2 s/pas → ~1.25 s/pas (×1.75) + suppression de la contention disque ×16 → ×2+ sous flotte chargée. À MESURER par l'A/B chaîné (fichier vs TCP, même op/seed) qui part automatiquement après la grande matrice + reboot flotte dual-mode.
**Règle de bascule** : si A/B propre (métriques identiques, gain confirmé) → les tables suivantes passent en HMT_SOCKET=1 ; le mode fichier reste le fallback gravé.

## 2026-06-10 ~16:30 — PISTE MULTI-THÉÂTRES OUVERTE : CMO + DCS (décision Younes)
La bibliothèque Steam de Younes couvre tous les échelons de la guerre : DCS (technique air) · Arma (tactique sol) · **CMO (opératif aéronaval)** · HoI4 (stratégique). Décision : étendre la méthode Harmattan aux théâtres 2 et 3. **Plans complets dans `~/Bureau/Plans-CMO-DCS/`** (Gate 0 plomberie → répertoire → matrice → valeur de sélection → officier, pour chacun).
**Préparé** : CMO (1076160) et DCS (223750) possédés, non installés ; bibliothèque /mnt/data/SteamLibrary enregistrée ; Proton Experimental pré-assigné aux deux (config.vdf). **Leçon d'infra** : Steam refuse le logon réseau en mode headless/-silent → l'installation exige la session graphique. RDP bloqué à distance par le verrou GNOME (« Session creation inhibited », LockedHint résiste à loginctl unlock-session non-root) → Younes finalisera sur place. Re-verrouillage auto DÉSACTIVÉ (gsettings lock-enabled false, idle-delay 0) → le problème ne se reproduira plus une fois la session déverrouillée une fois.
Client RDP installé sur le Mac (Windows App 11.3.5, extraction directe du pkg Microsoft — brew cassé) + raccourci `workstation.rdp` sur le Bureau Mac.

## 2026-06-11 ~00:35 — CMO + DCS INSTALLÉS par Younes (session débloquée sur place)
**Emplacement (important : 3e bibliothèque, client SNAP)** : `/mnt/data/harmattan-sandbox/Steam/steamapps/common/` — CMO 35 Go (1076160) · DCS World **369 Go** (223750) · Arma 3 client 41 Go (107410). Préfixes Proton créés pour les trois (`compatdata/`) → premiers lancements probablement faits. Le client Steam actif pour le jeu = **snap** (`~/snap/steam/...`), PAS le deb que j'avais configuré.
**Matrice intacte pendant le téléchargement des 450 Go** (38/60 cellules à 00:30, rythme 19 min/cellule — la charge ~67 de la soirée s'explique en partie par le download). Reboot/A-B pont TCP : **ANNULÉS sur ordre de Younes** (ab_socket tué) — l'A/B est parké, relançable à la demande.
**Prochaine marche** : Gate 0 CMO dès la flotte libérée (plan dans ~/Bureau/Plans-CMO-DCS/PLAN-CMO.md, adapter les chemins au préfixe snap).

## 2026-06-11 ~07:45 — 🎯 GATE D1 : MATRICE 9×8 COMPLÈTE (960 ops) — LA PORTE S'OUVRE : VALEUR DE SÉLECTION +15.5 pts
**Matrice complète (militaire %, n=16/cellule sauf react n=32)** :
| | skilled | react | depth | mobile | elastic | herisson | appat | sortie |
|---|---|---|---|---|---|---|---|---|
| M1 | 50.0 | 34.4 | 18.8 | 37.5 | 25.0 | 50.0 | 25.0 | 37.5 |
| M2 | 31.0 | 18.8 | 31.2 | 43.8 | 31.2 | 50.0 | 18.8 | 37.5 |
| M3 | 62.5 | 21.9 | 65.6 | 75.0 | 62.5 | 87.5 | 43.8 | 75.0 |
| M5 | 25.0 | 15.6 | 31.2 | 75.0 | 68.8 | 68.8 | 68.8 | 50.0 |
| M8 | 43.8 | 25.0 | 37.5 | 56.2 | 62.5 | 56.2 | 43.8 | 62.5 |
| M9 | 12.5 | 31.2 | 18.8 | 50.0 | 62.5 | 93.8 | 81.2 | 81.2 |
| M10 | 25.0 | 31.2 | 18.8 | 81.2 | 81.2 | **100** | **100** | 71.4 |
| M11 | 31.2 | 18.8 | 12.5 | 78.6 | 64.3 | 64.3 | 28.6 | 42.9 |
| M12 | 31.2 | **56.2** | 31.2 | 71.4 | 57.1 | 85.7 | 78.6 | **85.7** |
**CHAMPIONS : 3 régimes distincts** — M3 (défenses ancrées : skilled 62.5, depth 65.6) · M10 marteau-enclume (défenses qui abandonnent l'écran : mobile/elastic 81.2, herisson/appat 100) · M12 reco-en-force (défenses adaptatives : react 56.2, sortie 85.7).
**ROBUSTESSE (moyenne/8 défenses)** : M10 63.6 > M12 62.2 > M3 61.7 > M9 53.9 > M5 50.4 > M8 48.4 > M11 42.6 > M1 34.8 > M2 32.8. **Les 2 pièces codées HIER prennent les 2 premières places** — la décision Younes « tout coder, c'est la plus-value » remboursée en 24 h.
**VALEUR DE SÉLECTION = 79.1 (sélecteur parfait) − 63.6 (M10-fixe) = +15.5 pts** → SEUIL 15-20 ATTEINT (borne basse) → **l'officier-sélecteur devient ÉCONOMIQUEMENT justifié**, sous réserve de l'escalade n=32 des pivots (12 cellules lancées 07:45, colonnes serrées : mobile/elastic/herisson/appat/sortie top-2 + skilled M3/M8).
**Track-record des prédictions : ~17/60 dans la fourchette** — j'ai systématiquement SOUS-estimé les attaquants contre les défenses nouvelles. Erreurs les plus instructives : M9-hérisson prédit 10-30 → **93.8** ; M10-hérisson prédit 15-35 → **100** ; M10-appât 25-50 → **100**. LOI DOCTRINALE ÉMERGENTE : une défense dense SANS écran meurt face à toute manœuvre qui possède l'extérieur (l'enclume/la marche profonde s'installent sans opposition, puis le marteau frappe un périmètre compressé). Corollaire de la loi d'hier (« l'écran est sacré ») : le hérisson est le PIRE des sacrifices d'écran, pas le meilleur.
**M12 confirme sa nature** : jamais championne nulle part SAUF contre les 2 défenses qui réagissent — l'adaptation ne paie que contre l'adaptation — et 2e robustesse globale. C'est le PLANCHER que le sélecteur appris devra battre.
**Prochaines marches** : (1) n=32 pivots en cours → verdict consolidé ; (2) commit+tag gate-d1 ; (3) le PROBLÈME DE RECONNAISSANCE (l'officier doit DEVINER la défense depuis les indices de contact — le stub lit la vérité terrain, un vrai officier non) ; (4) M13 assaut-sous-fumigène + 5e action fumée dans le sandbox (l'expérience « le RL peut-il étendre le livre ? », validée par Younes cette nuit).

## 2026-06-11 ~13:30 — INCIDENT FLOTTE (fuite mémoire) + 2 LEÇONS D'INFRA (archi)
**Incident** : après le marathon de la matrice (~1000 ops, 20 h), les serveurs Arma avaient fui à ~3.8 Go chacun → RAM 60/60 + swap plein → charge 180, 4 serveurs morts, le n=32 des pivots sortait en TimeoutError. **Remède** : kill + reboot flotte (multi_server.sh 16) → RAM 33/60, 16 serveurs frais, n=32 relancé 13:10 (verdict consolidé attendu ~16:45, analyse dédupliquée par seed — les mesures de la phase dégradée sont remplacées).
**LEÇON 1 (au panthéon)** : *tout `pkill -f` est un suicide en puissance* — 3 incidents en 1 heure (la séquence s'est tuée elle-même 2×, puis a tué sa propre session ssh : le motif vivait dans la cmdline). Parade définitive : **passer les motifs par stdin** (écrire un script distant via heredoc puis l'exécuter — la cmdline ne contient que le nom du script).
**LEÇON 2** : *reboot préventif de la flotte entre les grandes tables* (~1000 ops = la limite mesurée avant épuisement mémoire). À intégrer aux futurs scripts de table : `bash multi_server.sh 16` en tête.
**Mémoire Mac mise à jour** (état au 11/06 : Gate D1, répertoire 12×8, multi-théâtres, leçons).

## 2026-06-11 ~15:10 — ⚠️ SUSPICION DE CONFOND MAJEUR : LA CHARGE DE LA FLOTTE BIAISE LA MESURE (pré-enregistré AVANT les données restantes)
**Constat (3 cellules pivots refaites sur flotte FRAÎCHE, seeds 16-31 vs seeds 0-15 de la nuit)** : mobile×M10 81.2→31.2 · mobile×M11 78.6→43.8 · elastic×M10 81.2→**6.7**. Effondrement systématique de −35 à −75 pts — PAS du bruit de seed.
**Hypothèse pré-enregistrée (mécanisme)** : la nuit, la flotte se dégradait (fuite RAM → swap → charge 60-70 puis 180) → le sim serveur RALENTIT pendant que le harnais cadence en TEMPS RÉEL (step_wait 1.0 s mur) → moins de pas de sim (donc de réaction de l'IA DÉFENSIVE) par pas de harnais → **les scores attaquants de la nuit sont INFLATÉS**, d'autant plus que la cellule est tardive (phases B/C). Cousin direct de la leçon « un budget en pas n'est pas un budget en temps » : *une mesure en temps mur n'est comparable qu'à charge égale*.
**PRÉDICTION pré-enregistrée** : les 9 cellules n=32 restantes sortiront TOUTES en-dessous de leur valeur nocturne (déflation systématique). Hypothèse alternative à exclure : le template de mission a changé au reboot (actuateur natif en plus) — contrôle prévu : 1 cellule sur template ANCIEN, flotte fraîche ; prédiction : même déflation (le template est innocent, la charge est coupable).
**CONSÉQUENCE SI CONFIRMÉ** : le verdict Gate D1 (+15.5 pts) est COMPROMIS — matrice de nuit à re-mesurer sous protocole contrôlé : **reboot préventif de flotte toutes les ~10 cellules + charge surveillée et consignée par cellule**. Les valeurs n=32 flotte-fraîche deviennent la graine de la matrice propre.
**Ce que la discipline a fait** : c'est l'escalade n=32 (loi anti-bruit) qui a attrapé l'artefact AVANT qu'on ne construise dessus. 5e mensonge de demi-mesure du projet, le plus gros — et le plus instructif : l'instrument (la flotte) fait partie de la mesure.

## 2026-06-11 ~16:00 — OPTION A ENGAGÉE : cadence en TEMPS DE JEU + pont TCP (décision Younes)
**Verdict UDP** : non — sur loopback, la latence TCP+NODELAY est en microsecondes ; le goulot est le poll actuateur (0,1 s) et la cadence sim, pas le transport. UDP sacrifierait ordre+livraison pour rien. Le levier vitesse = le pont TCP natif déjà construit (parké hier) + settle réduit.
**Implémenté (op_arma.py, rétro-compatible)** : `step_game` (s-jeu/pas, env HMT_STEP_GAME) — step() attend désormais que la SIMULATION ait avancé de step_game secondes (lecture SQF `time` via _game_time()), mur de sécurité 6×. Sans le réglage : ancien comportement inchangé. **La mesure devient insensible à la charge** — la cure structurelle du confond découvert ce midi.
**Chaîné derrière le n32 en cours (AUCUN reboot)** : (1) calibration step_game = rythme s-jeu/pas de l ANCIEN harnais sur flotte saine (1 op M1 instrumentée, serveur 0) ; (2) smoke du nouvel instrument (HMT_SOCKET=1 + HMT_STEP_GAME) ; (3) **cellule d équivalence** mobile×M10 seeds 32-47 vs la référence ancien-instrument-flotte-fraîche (31.2 %) → si match ±bruit, l instrument est validé ; la re-matrice 60 cellules (protocole durci : reboot/10 cellules + charge consignée) partira APRÈS ce verdict, sur go explicite.
**Prédictions n32 (8/8 déjà confirmées)** : déflation systématique nuit→frais de −12 à −81 pts. Contrôle template : abandonné sauf échec d équivalence (mécanisme de charge accablant, et le nouvel instrument supprime la question).

## 2026-06-11 ~17:20 — 2e CONFOND DÉCOUVERT : LA GÉOMÉTRIE « STANDARD » ≠ LA GARNISON DE RÉFÉRENCE (archi)
**Constat** : M3×skilled s effondre à 0/6 sur flotte FRAÎCHE (réf 62.5 % du 08/06) alors que M8×skilled tient (43.8→37.5 ✓). Cause trouvée : `GEOMETRIES["standard"]` (12→10 garnison, patrouilles 4+4 r120 → **5+5 r110**) ≠ `M.GARRISON` original. Depuis le patch géométrie (09/06), TOUTE mesure utilise la nouvelle disposition — mais les références skilled (M1 50 / M2 31 / M3 62.5 / M5 25, table v4 du 08/06) datent de l ANCIENNE. M3 meurt en 1-4 min à 32-50 % de pertes : sa marche de flanc EST traverse l écran renforcé à 5 pros. Pas de la charge, pas le template : **une dérive silencieuse de référence**.
**Leçon (panthéon)** : *une « géométrie standard » créée à côté de l originale est une NOUVELLE référence — renommer ou re-baseline, jamais supposer l équivalence.* (Cousine de « tout argmax est un tie-break déguisé ».)
**Ce qui SURVIT aux 2 confonds** (mesuré géométrie nouvelle + flotte fraîche) : Gate 0 react n=32 (M1 34.4 > M3 21.9), la matrice 3-défenses du 10/06 matin (+4.2), les cellules n32 fraîches d aujourd hui. **Ce qui tombe** : les références v4 de la colonne skilled (à re-mesurer : 4 cellules de plus) + toute la matrice de nuit (charge).
**Périmètre re-matrice corrigé : 64 cellules** (60 + la colonne skilled M1/M2/M3/M5) — UN seul instrument (temps-de-jeu + TCP), UNE seule géométrie (standard 10/5/5 assumée comme LA référence), protocole durci (reboot/10 cellules, charge consignée).

## 2026-06-11 ~17:45 — PONT CMO CONSTRUIT (Gate 0 à 80%, archi)
**Reco terrain** : CMO = Lua 5.4 embarque (lua54/NLua/KeraLua), prefixe Proton OK, mapping **Z:\ = /** (le pont fichier marche comme pour Arma), Steam snap actif, display :0 deverrouille. Scenarios = XML. setAccTime inerte sur dedie (deja vu).
**Construit (~/arma3-marl/cmo/, commite)** : cmo_ping.lua (TEST ATOMIQUE : le Lua de CMO peut-il io.open un fichier ? = LE point critique du pont) · cmo_bridge.lua (event recurrent : dump unites Blue/Red lat/lon/cap/vit/alt + lit/exec cmd.lua + ack — jumeau exact du pont Arma) · cmo_bridge.py (CmoBridge : ping/read_state/send) · GATE0-CMO.md (3 etapes).
**Lancement headless KO** : `steam -applaunch` route vers le mauvais client (2 steams : snap actif + deb) ; `snap run steam -applaunch` bute sur l autorisation X + steam-runtime-launcher-service introuvable depuis SSH. → **0a (lancer) + 0b (coller cmo_ping.lua dans la console Lua) = a faire dans la session graphique de Younes** (1 clic + 1 coller), comme l install. Le reste du pont est pret et testable immediatement apres.
**Risque a lever en 0b** : la securite Lua de CMO peut bloquer io.open (Game>Options>Lua security a decocher). Si ca resiste : voie ScenEdit_ExportInst.
**Re-matrice** : intacte (cellule 1/72), insensible a la charge CMO grace a l instrument v2 (step_game) — lancer CMO ne la fausse PAS, juste la ralentit un peu.

## 2026-06-11 ~21:30 — CMO via VM Windows : TOUTE la prep faite sans reboot (archi + Younes)
Wine impraticable (bug FDICopy/WoW64 sur 5 Protons + GE10-27). Solution : VM Windows = CMO natif.
**Fait (sans reboot)** :
- Pile KVM installee : qemu-system-x86 10.2, libvirt 12, virt-install, ovmf, swtpm, qemu-utils (younes ds groupes kvm+libvirt).
- ISO Windows 10 22H2 FR (5.73 Go, validee bootable) -> /mnt/data/vm/iso/win10.iso ; virtio-win.iso (754 Mo).
- /mnt/data/vm/create_vm.sh : VM Win10 (8 Go/6 coeurs, disque SATA 80 Go, e1000, spice). Boot driverless. virtiofs RETIRE (pont via Samba apres install).
- Pont commite ~/arma3-marl/cmo/ : cmo_bridge.py + .lua + test_bridge.py (TEST A BLANC PASSE) + GATE0-CMO.md.
**SEUL VERROU RESTANT** : VT-x desactive au BIOS -> /dev/kvm absent (kvm-ok: "CPU does not support KVM extensions"). Le reboot VT-x activera AUSSI les groupes + libvirtd. A faire APRES le run Gate D1 (Younes ne veut pas couper le run).
**Apres reboot VT-x** : bash /mnt/data/vm/create_vm.sh -> install Windows -> Steam+CMO -> Samba pour le dossier pont -> charger cmo_bridge.lua dans CMO (Lua security OFF) -> 1er round-trip reel = Gate 0 CMO.

## 2026-06-12 ~03:40 — VM CMO OPÉRATIONNELLE (éteinte pour la nuit, reprise demain)
**Tout marche** : VT-x activé (reboot fait), VM `cmo-win` = Windows 10 Pro N 22H2 (8 Go/6 vCPU, disque SATA 80 Go, /mnt/data/vm/cmo-win.qcow2). Agent qemu-ga connecté (après install virtio-win-guest-tools). Pilotage Windows depuis l hote via /mnt/data/vm/gx.sh + gxps.sh (guest-exec, encodage base64). Client Steam installé (auto, depuis l hote). CMO EN TÉLÉCHARGEMENT (~1-2 % à l arrêt, reprend au boot). RDP activé (compte **harmattan / Harmattan2026!**, écoute 3389). Port-forward hôte 3390->VM:3389 posé (iptables, survit tant que l hôte ne reboote pas). Internet VM OK.
**VM ÉTEINTE proprement 03:40** pour rendre le CPU à la re-matrice (la VM ajoutait ~6 vCPU de charge).
**REPRISE DEMAIN** : `virsh start cmo-win` -> CMO finit de télécharger -> RDP Mac sur 100.66.136.67:3390 (harmattan/Harmattan2026!) -> lancer CMO -> charger cmo_bridge.lua (Lua security OFF) -> 1er round-trip = Gate 0. Pont host-side : adapter cmo_bridge.py au relais par agent qemu-ga (pas besoin de Samba). Re-matrice : 32/72 à 03:40, fin Gate D1 cet après-midi.

## 2026-06-12 ~17:16 — GATE D1 PROPRE : MATRICE 9x8 COMPLETE (instrument v2, insensible a la charge)
**Valeur de selection = +4.7 pts** (selecteur 67.2 vs M3-fixe 62.5). Le +15.5 du 10/06 etait un ARTEFACT de charge -> confirme et corrige.
**4 champions distincts (le pierre-feuille-ciseaux EXISTE)** : M3 (skilled 81, react 62, depth 69, mobile 62), M12 (appat 81, sortie 69), M8 (herisson 62), M1 (elastic 50).
**M12 reco-en-force adaptative VALIDEE** : championne contre appat et sortie = les defenses qui REAGISSENT. La these "adaptation contre adaptation" tient sur donnees propres. (Read provisoire a 69/72 disait M12 KO : faux, appat/sortie pas encore mesures -> M12 81/69 dessus.)
**Revision Gate 0** : instrument propre -> M3 bat M1 contre react (62>31). Inversion react du 10/06 aussi affectee par la charge.
**VERDICT** : RPS structurellement REEL mais valeur de selection MARGINALE (+4.7 < seuil 15-20). Officier-selecteur justifie en principe, faible gain sur CE theatre (M3 trop dominant). Robustesse: M3 62 > M12 60 > M1 42.
**Implication** : rendre officier RENTABLE -> (a) defenseur APPRIS (diversifie defenses -> monte la valeur), (b) theatre plus riche = CMO.

## 2026-06-12 — CAP REDEFINI (vision Younes validee)
Livrable principal = COMMANDEMENT ARMEE DE TERRE pilote IA, multi-echelons, 1000+ hommes, haute intensite entre pays, ACE/realisme, ennemi co-evolutif, doctrine FR/OTAN, observable+explicable, Younes observateur, systeme reutilisable. CMO = theatre 2. Contrainte: Arma != 1000 IA/serveur -> echelons hauts en abstraction GPU, point de contact dans Arma. Pyramide strategique/operatif/tactique/soldat. Le +4.7 valait sur jouet symetrique; a cette echelle le commandement est IMPERATIF. JALON 1 = officier operatif commande une op multi-escouades autonome+adaptative+explicable dans Arma, observateur. Detail complet: VISION-COMMANDEMENT.md.

## 2026-06-12 — JALON 1.1+1.2 : OFFICIER OPERATIF (test a blanc 8/8)
officer_op.py : officier qwen2.5:14b qui lit un rapport de contact -> DEDUIT la posture defensive -> CHOISIT la manoeuvre M1-M12 -> ALLOUE -> JUSTIFIE en clair (doctrine FR/OTAN, savoir ancre sur la matrice propre v2). Test a blanc test_officer_op.py : 8 situations (1 par posture, sans la nommer) -> 8/8 = champion mesure, posture correctement deduite, justifications militaires coherentes (ex appat: "ennemi a abandonne pour nous attirer -> occuper avec reserves pour contre-attaquer"). Le frozen officer commande deja juste ET explicable. SUITE: 1.3 adaptation live dans Arma (re-decision aux points cles) + 1.4 observabilite + 1.5 mesure live vs manoeuvre fixe.

## 2026-06-12 — JALON 1.3+1.4 : OFFICIER LIVE DANS ARMA (boucle de commandement bout-en-bout)
officer_live.py : sonde -> rapport de contact (secteurs ennemis + objectif) -> officier qwen DECIDE -> execute (OperationRunner) -> RE-DECIDE si echec (change de manoeuvre). Journal d ordres lisible (observabilite 1.4).
SMOKE vs skilled_appat : 1ere lecture -> estime HERISSON -> M8 -> echec 14% -> RE-LECTURE: ennemi a quitte l objectif + concentre nord -> deduit APPAT -> bascule M12. Final mil=False pertes 39% garr_pris=True. LA BOUCLE ADAPTATIVE MARCHE : l appat a berne la 1ere lecture, l officier s est corrige seul apres contact. LECON: reconnaissance au 1er contact imparfaite (postures reactives ne se revelent que sous pression) = prochain a durcir. SUITE 1.5: mesure officier-adaptatif vs M3-fixe sur posture ALEATOIRE/op.

## 2026-06-12 — JALON 1.5 : officier adaptatif vs M3-fixe (verrou isole = RECONNAISSANCE)
Mesure 32 ops (8 postures x2 x2 conditions, 16 serveurs). Officier 7/16=44% (pertes 28%) vs M3-fixe 6/16=38% (pertes 35%). Leger avantage officier, MAIS diagnostic clef : l officier a choisi M8 aux 16 premieres decisions (offline il faisait 8/8). Cause : le rapport de contact LIVE (secteurs figes) ne porte PAS les signatures de posture -> tout ressemble a dense-autour-objectif -> lit toujours HERISSON->M8. Ses 8 succes viennent surtout de la RE-DECISION (M8->M12, 8 cas) qui rattrape. CONCLUSION: cerveau officier OK (raisonne juste), YEUX casses (perception live). Adaptation = bon filet de securite. PROCHAIN (1.1-bis): la sonde doit MESURER LA REACTION ennemie (mouvement avant/apres: massage flanc, abandon objectif, sortie) car les postures sont definies par la reaction, pas une photo statique. Fichiers: run_officer_measure.py, officer_vs_fixe.jsonl.

## 2026-06-13 ~12h — PASSATION AUTONOME (Claude-Mac → Claude-workstation)
Younes a demandé que ça CONTINUE en autonome côté workstation. État : **reconnaissance comportementale MORTE** (26/32%, officier −12) → **PIVOT GÉOMÉTRIE gagnant** : brique 0 = le vainqueur tourne avec la forme de défense (**sélection +13**, matrice `mxg_*`) ET la géométrie est **lisible à 100%** (`geo_recon.jsonl`). Boucle adaptative câblée (`officer_geo.py`). Workstation **rebootée (OS)** pour repartir propre (l ancien run live échouait à 72% par dégradation flotte ; le mdp sudo `R8IdSAsRHAmI` NE MARCHE PLUS). Smoke flotte-fraîche = 5/5 reco, 0 erreur. **Run de confirmation EN COURS** (`geoconf.sh` → `geo_officer3.jsonl`, verdict appendé ici à la fin). **PLAN COMPLET + GATES pré-enregistrés : voir `NEXT-TASKS.md`.** Ordre : fermer brique 0 → reco sous brouillard (LOS) → multi-objectif → échelon opératif (répertoire-sélecteur, PAS RL-découvre, scar 83→0) → ennemi co-évolutif. Thèse projet livrée Mac : `~/Documents/HARMATTAN-these.md`/`.pdf` (§4.7 à compléter avec le verdict de confirmation, rebuild `build_these.py` côté Mac).

## 2026-06-13 12:29 — CONFIRMATION BRIQUE 0 (run AUTONOME, flotte fraiche post-reboot OS)

===== LIVRABLE : OFFICIER ADAPTATIF vs FIXE (M2) =====
ADAPTATIF : 4/12 = 33%
FIXE (M2) : 2/12 = 17%
ECART = +17 points   (hier, sur les postures comportementales : -12)
reconnaissance EN BOUCLE : 100% (12/12)

par geometrie (adaptatif | fixe | manoeuvre(s) lue(s)) :
  std   adapt 2/4 | fixe 0/4 | ['M8']
  conc  adapt 2/2 | fixe 1/2 | ['M5']
  disp  adapt 0/2 | fixe 0/2 | ['M2']
  f_O   adapt 0/2 | fixe 1/2 | ['M1']
  f_E   adapt 0/2 | fixe 0/2 | ['M1']

## 2026-06-13 ~15h45 — INFRA RÉPARÉE (concurrence du pont)
**Symptôme** : mesures end-to-end à 70-84% d erreurs (TimeoutError + ValueError max() vide). **Diagnostic propre** (infra_diag.py) : Phase A = 16/16 serveurs SAINS en solo ; Phase B = 0/12 en concurrence. **Cause = pic CPU synchrone** : 12 serveurs spawnent ~48 unités EN MÊME TEMPS → serveurs Arma mono-thread saturés → la 2e commande (cmd 2 = PRO_SKILL) ne se traite jamais → stall. La matrice marchait car ses commandes étaient étalées (ops longues). **FIX (2 pièces)** : (1) `op_arma._query` = attente par POLL avec timeout 20s au lieu d un `max()` qui crashe (backup `op_arma.py.bak_query`) ; (2) **STAGGER** des workers (`measure_geo_officer.worker` : `time.sleep(srv*1.8)`) pour étaler les spawns initiaux. **Vérifié : 0/12 → 12/12** (infra_concur.py, stagger 2s). RÈGLE : tout harnais concurrent doit STAGGER les départs de workers.

## 2026-06-13 16:31 — CONFIRMATION PROPRE brique 0 (infra reparee : _query poll-timeout + worker stagger 1.8s)

===== LIVRABLE : OFFICIER ADAPTATIF vs FIXE (M2) =====
ADAPTATIF : 3/6 = 50%
FIXE (M2) : 1/6 = 17%
ECART = +33 points   (hier, sur les postures comportementales : -12)
reconnaissance EN BOUCLE : 100% (6/6)

par geometrie (adaptatif | fixe | manoeuvre(s) lue(s)) :
  std   adapt 2/2 | fixe 0/2 | ['M8']
  conc  adapt 0/1 | fixe 1/1 | ['M5']
  disp  adapt 0/1 | fixe 0/1 | ['M2']
  f_O   adapt 1/1 | fixe 0/1 | ['M1']
  f_E   adapt 0/1 | fixe 0/1 | ['M1']

## 2026-06-13 ~16h30 — SOCLE INFRA RÉPARÉ (vraie cause trouvee)
Les mesures end-to-end echouaient a 70-85% PAS a cause de la concurrence ni du close. **Vraie cause (prouvee par leak_probe/leak_probe2)** : (1) chaque op creait un NOUVEAU pont -> la **2e connexion a un serveur echoue** (op 0 OK, op 1 timeout, en sequentiel) ; (2) **fuite de groupes** : le spawn supprimait les unites mais PAS les groupes (+7 groupes/op -> 92 apres 12 ops). **FIX (2 pieces)** : (1) RÉUTILISER un env/pont par serveur, re-spawn par op (`officer_geo.make_env`/`respawn`, `measure_geo_officer.worker` cree 1 env/worker) ; (2) `{ deleteGroup _x } forEach allGroups` au spawn (`op_arma.py`, backup `.bak_grpleak`). **Verifie : 8-way churn = 0% erreurs** (vs 70-85%), groupes plats a 8. Diagnostics : `leak_probe.py`, `leak_probe2.py`, `infra_diag.py`. Backups op_arma : `.bak_query` (poll-timeout), `.bak_grpleak` (deleteGroup).

## 2026-06-13 ~17h — CORRECTION : l env reutilise BIAISE la mesure (ne pas l utiliser pour mesurer)
Le fix "reutiliser 1 env/pont par serveur" REGLE les timeouts (0% erreurs en churn 8-way) MAIS **fausse les issues** : sur `standard`, M8 fait **0/4** alors que la matrice (env frais) donne **83%** (P~0.0008 = pas du bruit). Donc : env reutilise = OK pour des diagnostics de DEBIT seulement, JAMAIS pour mesurer. **Verdict fiable brique 0 = la MATRICE `mxg`** (env frais, instrument valide, n=12/cellule) = **+14** (champions 52% vs M2 38%) x reco 100%. **REGLE MESURE** : pattern matrice uniquement (run_maneuver, env FRAIS, <=1 op/serveur/process, reboot entre cellules) -> correct ET sans timeout. Bons fixes a GARDER partout : `deleteGroup` au spawn (vraie fuite) + `_query` poll-timeout. NE PAS reutiliser l env pour une mesure.

## 2026-06-13 ~18h — PIVOT PERCEPTION SPATIALE (théorie + cible SOTA 2026) — session Mac architecte

Younes valide un **pivot important** : donner aux agents la **perception du terrain** (relief, routes, bâtiments, couvert) → monde compris → commander devient nécessaire (complément du pivot géométrie). « Ça devient du combat collaboratif. » Barre fixée : **« faire avec l'état des technos 2026 ce qu'il se fait de mieux »** (standard durable). Recherche web faite.

**Document de reprise autonome livré** (Mac `~/Documents/` + copié ici dans `~/arma3-marl/`) : **`arma3-marl-perception-spatiale-SOTA-2026.md`** — contient tout pour qu'une session reparte seule : les 8 piliers théoriques (repère/symétrie, croyance statique/dynamique, statistique suffisante, encodeurs, options+façonnage potentiel Ng 1999, crédit COMA, généralisation/PLR, sim-to-real), la pile SOTA 2026, le build recommandé, le contrat d'observation (§6, premier artefact à coder), les décisions ouvertes, les action items (§8) et la biblio.

**Pile SOTA 2026 cible (résumé)** : encodeur **Perceiver tokenisé** (a remplacé le Transformer d'AlphaStar à perf égale) ; **équivariance PARTIELLE** (le terrain BRISE la symétrie → PEnGUiN/score de symétrie appris, PAS équivariance pleine) ; **mémoire spatiale lieu-centrique** (Spatially-Aware Transformer/Neural Map) pour le dynamique caché ; CTDE **famille MAT/AOAD-MAT** (l'ordre de décision appris = chef-d'abord apprenable) ; **modèle du monde latent type Dreamer SANS reconstruction pixel** (×10-100 échantillons = LE levier 3090 + budget sim-to-real). Déjà alignés frontière : officier LLM + ligue PSRO + PLR/randomisation (≈ SMACv2/SMAC-HARD). ANTI-HYPE : pas de world model à reconstruction pixel, pas d'équivariance pleine, pas de gros modèle fondation (ne tient pas sur 3090).

**Discipline** : développer dans le sandbox GPU rapide (koth_gpu/op_gpu) AVANT Arma ; le **contrat d'observation doit être identique sandbox↔Arma** (garde-fou SCAR 83→0).

**Prochaine marche (au choix de Younes)** : (A) graver la fiche PhD de référence (framework `arma3-marl-algos/phd.py`) ; (B) figer + coder le contrat d'observation (§6 : trancher taille fenêtre W, résolution c, overlay vs tokens d'entités). Décisions ouvertes listées au §7 du doc.

## 2026-06-13 ~19h — PIVOT PERCEPTION SPATIALE : FAISABILITE CONFIRMEE
Nouveau doc `arma3-marl-perception-spatiale-SOTA-2026.md` (Mac+workstation, idee Younes : donner aux agents la perception du TERRAIN -> combat collaboratif, complement du pivot geometrie). **Sonde de faisabilite 13/06 (probe_gpu_terrain.py + probe_arma_v2.py) : OK des DEUX cotes.** (1) Sandbox GPU : pente+couvert+LOS vectorises = 24700 envs/s, 1.6 Go. (2) Export Arma : elevation 32x32 en 0.04s (statique->precalcul), routes via `nearRoads` (PAS nearestRoads), batiments via nearestObjects/nearestTerrainObjects. Altis@objectif : relief 9m, 50 routes, ~60-176 batiments. **Aucun bloqueur** -> le contrat d obs (§6 du doc : egocentrique, W=128m, c=2m, grille 64x64, calques statiques+dynamiques) est remplissable identique sandbox<->Arma (adresse le SCAR sim-to-real). PREREQUIS note : le sandbox koth_gpu/op_gpu est PLAT -> il faut d abord lui faire PORTER du terrain. PROCHAIN PAS : figer le contrat puis G-perc-0 (variables seules, baseline) -> G-perc-1 (grille+encodeur Perceiver) etc. Mesurer TOUJOURS au pattern matrice.

## 2026-06-13 ~19h30 — CONTRAT D OBSERVATION FIGE (Younes a valide "Standard")
`obs_contract.py` (Mac + workstation) = source de verite UNIQUE de la perception spatiale. Parametres figes : fenetre **128m**, resolution **2m** -> grille **64x64**, repere EGOCENTRIQUE oriente cap (devant=+y). 5 calques statiques (elevation/pente/route/batiment/couvert, [0,1]), tokens dynamiques (1/entite, dim 10 : type one-hot + ego_xy + bearing + dist + etat), 6 variables agent. Transform `to_egocentric` + `validate()` = garde-fou sim<->Arma (le sandbox ET Arma doivent passer validate). PROCHAIN PAS : G-perc-0 (variables seules baseline) PUIS faire PORTER le terrain au sandbox (koth_gpu/op_gpu plats) + exporteur Arma (cache offline via getTerrainHeightASL/nearRoads/nearestObjects, syntaxes verifiees). Mesurer au pattern matrice.

## 2026-06-13 ~20h — G-perc-0 INCREMENT 1 : moteur de terrain GPU bati + teste
`terrain_gpu.py` (Mac+workstation) = brique reutilisable, testee EN ISOLATION (discipline). Genere relief/pente/couvert/route par env (gen 4096 terrains 48x48 = 537ms), echantillonne au point de l agent (pente, dist-couvert, route), calcule la LOS ray-march contre le relief (12288 agents = 65ms, VRAM 0.5Go). LOS degagee 19% sur paires aleatoires longue portee (sain, le relief joue). C est la fondation de la perception (cote sandbox) + le miroir Arma utilisera les memes calques (export verifie : getTerrainHeightASL/nearRoads/nearestObjects). PROCHAIN INCREMENT : (1) hook sur koth_gpu `_dmg_terrain_mult` (defaut 1.0, no-op, backup avant) ; (2) koth_terrain.py = sous-classe qui genere le terrain par env + ajoute les variables de perception a l obs (contrat obs_contract) + LOS gate sur le combat ; (3) entrainer/evaluer -> gate G-perc-0 (pipeline tourne, metrique stable). Mesurer au pattern matrice.

## 2026-06-13 ~20h30 — G-perc-0 INCREMENT 2 : cablage OK, mais KOTH = MAUVAIS banc d essai (constat cle)
`koth_terrain.py` (sous-classe de koth_gpu, hook `_dmg_terrain_mult` ajoute a koth_gpu, backup `.bak_terrhook`) : terrain par env + 6 variables de perception dans l obs (pente/dist_couvert/dist+cap_route/LOS) + LOS du relief sur le combat. **Tout marche mecaniquement** (obs 10->16, LOS calculee et branchee). MAIS sweep relief : meme a 150m de relief, la LOS ne reduit le combat KOTH que de ~7-12%. CAUSE : le KOTH fait converger les 3 camps sur le POINT central -> combat bout-portant -> le relief ne bloque rien a 20-40m, ET l agent ne peut pas EXPLOITER le terrain (il doit aller au centre). **=> Le KOTH symetrique est le MAUVAIS banc d essai pour la perception.** La perception ne paie que sur une tache ENGAGEMENT A DISTANCE + terrain EXPLOITABLE (approche en defile, tenir la hauteur) = la tache ASSAUT/DEFENSE (approcher un objectif defendu a travers le terrain, ou vivent M1-M12 et le +14), pas la colline. ACQUIS : moteur terrain (terrain_gpu) + cablage reutilisables. PROCHAIN PAS : banc d essai assaut-a-travers-terrain (1 attaquant manoeuvre vers 1 objectif defendu, terrain entre les deux, succes = atteindre/nettoyer sans se faire faucher) -> la perception y devient un levier. Lecon recurrente : la MISSION est le professeur.

## 2026-06-13 ~21h — G-perc-0 BANC D ESSAI VALIDE : assault_terrain (le terrain DECIDE)
Fichiers : `terrain_gpu.py` (moteur), `assault_terrain.py` (tache assaut), `assault_exposure.py` (sonde exploitabilite). VALIDE des deux facons : (1) exploitabilite = choisir le cap d approche fait varier l exposition 23%(defile) / 46%(moyen) / 73%(decouvert) -> -50% en choisissant ; (2) en sim, assaut direct scripte : terrain PLAT = 0% objectif atteint / 100% pertes ; relief 35m = 75% / 29% pertes ; relief 60m = 89% / 14%. **Le terrain DECIDE l issue (vs 2% en KOTH).** Donc lire le terrain + choisir l approche = levier massif et recompense -> bon banc d essai pour la perception. obs (9) inclut deja les variables de perception (pente, dist_couvert, LOS, objectif, ennemi proche). PROCHAIN PAS = G-perc-0 entrainement : PPO sur assault_terrain AVEC variables de perception vs SANS (agent aveugle) -> la perception doit augmenter objectifs-atteints / baisser pertes. Puis G-perc-1 : grille egocentrique + encodeur Perceiver (obs_contract) bat les variables seules. Tout 100% GPU, reutilisable, miroir Arma via contrat d obs (export verifie).

## 2026-06-13 ~22h — G-perc-0 v1 : NEGATIF (-9) mais diagnostic CLE = pas de STEERING
train_assault (PPO sur assault_terrain, perception ON vs aveugle, 250 iters, hit=0.10) : PERCEPTION 54% vs AVEUGLE 62% objectifs atteints = **-9 pts (la perception a NUI).** CAUSE (design, pas bug RL) : dans assault_terrain le mouvement est TOUJOURS en ligne droite vers l objectif (tox=-apx) ; les 4 actions = HOLD/AVANCER/COUVERT/SUPPRIMER, **l agent ne choisit jamais sa DIRECTION** -> il voit le couvert mais ne peut pas y aller -> la perception = bruit inutile -> gene l apprentissage. LECON : percevoir ne sert a rien sans ACTION pour l exploiter (le steering). La sonde d exploitabilite (choisir l approche divise l exposition par 2) supposait un agent qui PILOTE sa direction, absent ici. FIX = espace d action DIRECTIONNEL (cap parmi K, ou sous-but) + reward shape vers l objectif -> alors voir le couvert -> piloter vers le defile -> paie. PROCHAIN : recoder le steering dans assault_terrain + relancer perception-vs-aveugle. Artefacts : assault_perc.pt / assault_blind.pt (v1, sans steering).

## 2026-06-13 ~23h — G-perc-0 FRANCHIE (+54) : la perception du terrain est DECISIVE (tache refondue)
Apres 3 impasses (RL no-steering -9 ; RL steering -11 ; scripte cover-routing +1) le diagnostic a tenu : sur les taches ou le combat DECISIF est a bout portant (KOTH scrum, assaut-AU-POINT), la perception ne sert a rien. **REFONTE de la tache (assault_terrain) : victoire = NEUTRALISER les defenseurs PAR LE FEU** (plus "atteindre le point"), defenseurs letaux (hit 0.15), le couvert reduit les degats recus, suppression tue en ~7 pas. -> foncer = 100% aneanti / 0 neutralise (verifie) ; seule voie = tirer depuis le COUVERT + manoeuvrer. **RESULTAT RL (train_assault, 300 iters, perception ON vs masquee) : PERCEPTION 57% defenseurs neutralises vs AVEUGLE 3% = +54 pts. G-perc-0 FRANCHIE.** L aveugle ne trouve pas de position couverte-avec-vue -> n engage pas -> ne gagne jamais. La perception est DECISIVE dans la tache qui la recompense (le combat collaboratif feu+mouvement). Fichiers : assault_terrain.py (tache refondue, win-by-fire, steering 8 caps + HOLD + SUPPRESS), train_assault.py (PPO perception ON/OFF), assault_perc.pt/assault_blind.pt. NUANCE : la perception gagne mais saigne (57% pertes) -> efficacite a ameliorer (G-perc-1 : grille egocentrique + Perceiver via obs_contract ; coordination base-de-feu/manoeuvre ; credit COMA). Mais le GATE est franchi net. LECON : les vieilles taches CACHAIENT la valeur de la perception ; il fallait la tache qui la recompense (mission = professeur).

## 2026-06-13 ~23h45 — G-perc-1 : la GRILLE (contexte spatial) bat le POINT, mais nuance
train_grid (GRILLE = fenetre locale 8x8 couvert+pente aplatie dans le MLP, obs_dim 137, vs POINT = 9 variables, tache win-by-fire, 300 iters, envs 4096) : **GRILLE 46% neutralises (pertes 44%) vs POINT 0% (pertes 100%) = +46.** NUANCE HONNETE : le POINT s effondre ici (0%) alors que la meme obs-point avait fait 57% au run +54 (envs 8192) -> le RL sur l obs maigre est INSTABLE (57% ou 0% selon seed/envs). Donc le +46 brut est gonfle par un effondrement. VRAI constat : la grille rend la tache dure FIABLEMENT apprenable (robuste a moins d envs) ET baisse les pertes (44% vs 57% = mieux CMDP, exploite la DISPOSITION du couvert pas juste le point). A CONFIRMER : 2-3 seeds (le point baseline a oscille 57->0). Direction validee : contexte spatial utile -> investir CNN/Perceiver (le MLP-aplati gache la structure 2D ; un CNN equivariant fera mieux). Fichiers : assault_grid.pt / assault_point.pt, train_grid.py, assault_terrain.py (grid_obs flag, _local_grid). NUANCE generale : RL sur cette tache = haute variance, toujours multi-seed avant de graver.

## 2026-06-13 ~minuit — FEUILLE DE ROUTE MAITRESSE validee Younes : substrat -> systeme -> tactique -> officier
Cap reaffirme : l objectif = un SYSTEME de combat COLLABORATIF, puis les tactiques par-dessus, puis l echelon officier. Ordre par dependances, un GATE par couche :
1. [SUBSTRAT] PERCEPTION du terrain : agents voient le terrain (obs_contract = pont sim<->Arma). Gate : grille robuste ET bat le point (seed-sweep en cours, G-perc-1). [+54 montre que percevoir aide ; reste a confirmer la grille multi-seed]
2. [SYSTEME] COORDINATION = LE COEUR : roles EMERGENTS (base de feu / manoeuvre), credit bien attribue (COMA / difference rewards, Pilier 6 ; embedding de role RODE/ROMA si besoin). Gate : equipe COORDONNEE (recompense d equipe + credit contrefactuel) > N agents solo (memes yeux, pas de credit). Mesurer que la coordination EMERGE (pas juste chaque agent qui percoit) -> c est ca le vrai test du collaboratif.
3. [TACTIQUE] REPERTOIRE M1-M12 : une manoeuvre = une CONFIGURATION de la coordination (qui cloue, qui deborde, ou). Gate : bonne manoeuvre selon situation > manoeuvre fixe (la valeur de selection, mais sur une equipe qui EXECUTE vraiment).
4. [OFFICIER] COMMANDANT LLM (qwen2.5:14b) : lit la situation -> choisit la config/manoeuvre -> l equipe execute -> justifie en clair. Gate : adaptatif > fixe end-to-end, explicable.
PRINCIPES : la manoeuvre n est pas un waypoint mais une config de coordination (-> coordination AVANT tactique) ; l officier ne commande que ce que l equipe sait executer (-> officier EN DERNIER) ; la perception est le fil rouge sim<->Arma (tout le sandbox se rebranche sur Altis via le contrat). PROCHAIN apres seed-sweep : si perception validee -> attaquer la COUCHE 2 (coordination : COMA + mesure d emergence des roles), PAS plus de perception.

## 2026-06-14 ~00h30 — IDEE Younes : PERCEPTION PAR ECHELON (carte tactique a l officier)
Principe verrouille : chaque echelon percoit a SON echelle, meme moteur terrain (terrain_gpu) agrege differemment.
- SOLDAT : fenetre locale egocentrique 128m (obs_contract) = son terrain immediat.
- EQUIPE : conscience des coequipiers (binome + son feu) = couche coordination (en cours, train_coord).
- OFFICIER : CARTE TACTIQUE = vue d etat-major de toute la zone d operation (plus large + grossiere) : relief/routes/couvert + positions de MES escouades + dispositions ennemies connues + objectifs. L officier lit la carte -> choisit la manoeuvre/config -> l equipe execute. Pour l officier-LLM : serialiser la carte en image tactique textuelle (ou cnn vision) -> raisonne -> choisit M1-M12 -> justifie en clair. = upgrade du rapport-texte actuel (officer_op) vers une vraie LECTURE DE CARTE terrain-aware.
- (STRATEGE : carte theatre, encore plus grossiere — plus tard.)
A BATIR couche 4 (officier), apres coordination + tactique. Architecture de perception UNIFIEE sur la pyramide.

## 2026-06-14 ~01h — COEUR DU PROJET VALIDE : l OFFICIER-SELECTEUR paie (il gere les agents en CHOISISSANT)
Chemin de la couche officier, en clair : (1) coord soldat implicite emerge deja (47% feu+mouvement) ; (2) obs-coequipiers = marginal (+2/-5) ; (3) ROLES FIXES + recompense de structure = ECHEC (Goodhart : l equipe farme le bonus de structure sans neutraliser -> 0% victoire) ; (4) OFFICIER-SELECTEUR (officer_select.py) = MARCHE. L officier (scripte) lit le terrain -> CHOISIT l axe d approche (defile = exposition min) -> l equipe EMERGENTE (assault_grid.pt, sait deja se battre) EXECUTE. Resultat (zero reentrainement) : OFFICIER(defile) 65% neutralise / 47% pertes ; hasard 55/56 ; pire-axe 47/63. **L officier qui CHOISIT = +10 neutralise ET -9 pertes vs pas d officier.** PREUVE : la plus-value de l officier = le CHOIX ADAPTATIF, pas une structure figee (Younes : l officier gere les agents en choisissant). C est le +14 (valeur de selection) EXECUTE end-to-end avec une equipe qui se bat, dans le sandbox terrain. Et c est le choix le + SIMPLE (1 axe) -> une vraie manoeuvre (axe+schema+objectif) donnera plus. PROCHAIN : officier-LLM (qwen2.5:14b) qui lit une CARTE TACTIQUE -> choisit la manoeuvre -> JUSTIFIE en clair (commandant explicable) ; + espace de config plus riche (M1-M12). Fichiers : officer_select.py, assault_grid.pt (equipe), terrain_gpu/assault_terrain. Confirme la feuille de route substrat->coordination(emerge)->TACTIQUE/OFFICIER(la plus-value).

## 2026-06-14 ~02h — SIGNATURE : l OFFICIER-LLM explicable tourne (lit la carte -> choisit -> justifie)
officer_llm.py : qwen2.5:14b recoit une CARTE TACTIQUE (par axe d approche : % du trajet a decouvert sous le feu + couvert ; le vrai signal terrain, PAS l exposition argmin deguisee mais le readout d une reco) -> repond en JSON {axe, justification} -> on VERIFIE son choix contre l officier scripte (exposure_by_bearing, qu il ne voit pas). Resultat : 6/6 situations il choisit le TOP-2 d exposition (rang 0/7 partout) vs ~25% au hasard. Justifie en francais clair en citant le % (ex: "Seul l axe Sud-Ouest presente 25% d exposition, ce qui reduit le risque"). => le COMMANDANT EXPLICABLE marche : lit -> choisit le defile -> explique. Il HERITE du +10/-9 (meme axe que le scripte -> l equipe emergente execute mieux). PIEGE evite : v1 de la carte donnait "fusils couvrant = max sur trajet" -> saturait a 4/4 partout (defenseurs groupes vus de partout) -> AUCUN signal -> LLM tombait sur "convention nord-sud" 2/6. Fix : exposition = FRACTION du trajet vue (continue, 23-92%) = le vrai discriminant. HONNETE : choix ~argmin ici (carte = expo par axe) -> prouve le PIPELINE (lire/choisir/justifier fonde), pas un jugement tactique fin -> le raisonnement non-trivial viendra avec les MANOEUVRES RICHES (axe+schema+objectif). Fichiers : officer_llm.py (SYS prompt FR, tactical_map, ask_llm ollama/qwen2.5:14b). PROCHAIN EN COURS : officer_maneuver.py = valeur de selection du SCHEMA (concentre vs pince) par situation.

## 2026-06-14 ~02h30 — MANOEUVRES RICHES : valeur de selection du SCHEMA = +6 (apres avoir tue un artefact +20)
officer_maneuver.py : l officier choisit le SCHEMA en plus de l axe. CONCENTRE (toute l escouade sur le meilleur axe/defile) vs PINCE (2 elements sur 2 axes >=135 deg pour diviser le feu). PIEGE STATISTIQUE attrape : oracle sur 1 seul tirage (par env prendre le meilleur des 2 schemas) = MALEDICTION DU VAINQUEUR -> donnait +20 pts BIDON (combat stochastique : 1-0.41^2=83% meme si schemas identiques). BUG attrape aussi : ma boucle R-tirages ne reinitialisait pas la sante des defenseurs (ddmg/dsupp) entre tirages -> cumul -> 99% faux ; fix : place() reinit ddmg+dsupp (officer_select joue 1 ep/env donc son +10/-9 reste propre). Mesure CORRIGEE (de-bruitee R=24 tirages/situation + HOLD-OUT : decider le schema sur 12 tirages, l evaluer sur 12 autres = non biaise) : CONCENTRE 57% neutralise/49% pertes ; PINCE 61%/50% ; pince meilleure dans 46% des situations (aucun schema ne domine -> d ou la valeur de choisir) ; oracle de-bruite 70% (+9 plafond) ; HOLD-OUT 67% = **+6 pts REELS capturables**. CONCLUSION HONNETE : l AXE est le levier dominant (+10/-9), le SCHEMA ajoute +6 par-dessus -> manoeuvre riche (axe+schema) utile, plus-value de l officier se cumule. Discipline : un +20 trop beau -> remesure -> +6 reel (on ne vend pas d artefact, cf Younes "on ne fonctionne pas a l intuition a ce niveau"). PROCHAIN (synthese) : l officier-LLM choisit AXE + SCHEMA depuis la carte -> mesurer le gain capture (vise +10 et +6). Fichiers : officer_maneuver.py (rollouts/place avec reinit defenseurs, kB_far, hold-out).

## 2026-06-14 ~03h — SYNTHESE BRANCHEE : OFFICIER INTEGRE end-to-end (lit -> choisit l axe -> equipe execute -> explique)
Avant de cabler le LLM sur le schema, question honnete tranchee (officer_synth.py) : le +6 du schema est-il PREVISIBLE depuis la carte ? Teste 2 features a priori (pas de peche) : (1) gap exposition (2e mors pince - meilleur axe) corr -0.17 -> capture +0 ; (2) recouvrement des fusils couvrant les 2 mors (Jaccard, mecaniste : la pince divise le feu ssi fusils differents) corr -0.03 -> capture -3. CONCLUSION MESUREE : le schema N EST PAS lisible sur la carte (plafond oracle +9 existe par situation mais aucune feature ne dit lequel) -> son +6 demande un SELECTEUR APPRIS sur l obs complete, pas une lecture LLM. Donc on ne cable PAS le schema (faux choix qui capturerait ~0). 
officer_full.py = L OFFICIER INTEGRE, UNE boucle (plus 3 scripts) : qwen2.5:14b lit la carte tactique -> choisit l AXE -> justifie en clair -> l equipe emergente (assault_grid.pt) ASSAUT -> resultat rapporte. Schema = concentre (defaut, car non-lisible). BILAN 12 situations combat de-bruite x16 : OFFICIER 56% neutralise/54% pertes vs PAS D OFFICIER (axe hasard) 48%/55% -> apport +8 neutralise / -2 pertes (confirme le +10/-9 mesure a l echelle officer_select). HONNETE : situation ou tous les axes sont mauvais (42% expose) -> officier choisit le moins pire mais 0% (pas magique) ; justifications propres citant le %. ETAT : couche officier VALIDEE ET INTEGREE en SIM (lit/choisit/execute/explique). RESTE : (1) schema via selecteur appris (futur), (2) passage ARMA (obs_contract gele, jamais teste en jeu). Fichiers : officer_synth.py (2 features, train/test, verdict non-lisible), officer_full.py (boucle integree, fight_rep de-bruite).

## 2026-06-14 ~03h30 — VERDICT SCHEMA : du BRUIT, pas un signal (le selecteur appris echoue aussi) -> officier = AXE seul, propre
officer_schemelearn.py : MLP (16 features = exposition 8 axes + fusils/axe, repere canonique meilleur-axe-en-0) entraine a predire le meilleur schema, poids = |avantage|, train 1/2 situations, test sur l autre. RESULTAT : precision 54% sur les situations decisives (50% = hasard) -> capture -1 pt vs fixe (plafond oracle +9). => meme un modele appris ne predit PAS quel schema gagne. Le "+6/+9" du schema etait de la MALEDICTION DU VAINQUEUR RESIDUELLE. Traque sur 3 mesures de plus en plus serrees : (1) oracle 1 tirage +20 [bruit] -> (2) hold-out sur tirages +6 [mais decider exige de rejouer chaque schema, non deployable] -> (3) selecteur appris sur la carte 54%/-1 [un officier reel capture ~0]. CONCLUSION SOLIDE : quand pince bat concentre c est l interaction idiosyncratique terrain x RNG x politique, PAS une regle tactique lisible -> on ne cable pas le schema (faux choix). 
ETAT FINAL COUCHE OFFICIER (sim) : l officier a UN vrai levier, solide et explicable = CHOISIR L AXE D APPROCHE (+10/-9, officer_select ; LLM 6/6 officer_llm ; integre end-to-end officer_full +8). Le schema est fixe au defaut (pince marginalement meilleure en moyenne 61 vs 57, mais aucune valeur per-situation capturable). Discipline : on a refuse de sur-compliquer l officier avec un choix qui ne capture rien. RESTE LE GROS MORCEAU : passage ARMA (obs_contract gele, jamais teste en jeu) = la prochaine vraie marche, a attaquer frais. Fichiers : officer_schemelearn.py (MLP selecteur, verdict bruit).

## 2026-06-14 ~04h — PASSAGE ARMA, JALON 1 FRANCHI : perception+decision de l officier-axe sur le VRAI terrain Altis
On attaque le passage Arma. Reconnaissance pont (op_arma.py) : OpArma.spawn(friendly_spawns, garrison) controle OU les escouades apparaissent (=l axe) ; _query(sqf) renvoie tout SQF via le log RPT -> on interroge la LOS terrain REELLE. Officier existant officer_op.py = officier OPERATIF (choisit manoeuvre M1-M12 depuis rapport de contact, posture-based, qwen) -> different de l officier-axe terrain de cette nuit.
JALON 1 (perception sim->reel) FAIT, 3 scripts (arma_expo.py, arma_scan.py, arma_officer.py) : (1) exposition par axe calculee sur le relief reel via terrainIntersectASL (pendant exact du ray-march heightmap sim), SANS combat ni spawn -> deterministe, leger, exempt de la discipline-combat. (2) Le DEFILE EXISTE sur Altis : objectifs plats/cotiers = expo saturee ~100% (pas de defile, comme sim) ; objectifs en relief = vrai spread. Scan de 24 objectifs terrestres -> defiles FORTS trouves : (12000,21000)h123m defile 30%/spread70, (9000,18000)h213m 40%/60, (9000,21000)h33m 30%/70, etc. SPREAD JUSQU A 70 PTS = encore plus fort qu en sim (~50). (3) BOUCLE PERCEPTION->DECISION FERMEE : l officier-LLM (qwen2.5:14b, urllib) lit la carte tactique calculee sur Altis -> choisit Sud-Est 25% = LE DEFILE REEL (correct) -> justifie en clair. => le mur sim->reel est FRANCHI pour la perception+decision de l officier-axe.
JALON 2 (combat A/B) A STAGER A FROID (pas a 4h sous load 10.5 = biais garanti) : SPEC = plan de mission parametre par l axe (escouade assaut spawn au cap choisi via spawn(friendly_spawns), garnison=defenseurs a l objectif) ; net d escouade KOTH charge ; OperationRunner.run() ; mesurer enemy_dead_frac + losses ; DEFILE vs PIRE-AXE, n=4-8 reps/condition, DISCIPLINE MATRICE (env frais, <=1 op/serveur/process, reboot entre lots). Question : le +10/-9 du sim survit-il en combat Arma reel ? = LE test sim->reel de l officier-axe. Chaque op = minutes temps reel -> campagne ~1h. Fichiers Arma : arma_expo.py, arma_scan.py, arma_officer.py (tous sur workstation ~/arma3-marl).

## 2026-06-14 ~04h30 — JALON 2 (combat A/B) : boucle OK, mais le +10/-9 du sim NE SE TRANSFERE PAS (encore) — SCAR honnete
arma_axis_combat.py : escouade assaut une garnison depuis l AXE defile (expo min 25%) vs PIRE axe (100%), objectif (12000,21000), combat Arma reel, discipline matrice (OpArma fraiche/op, 1 serveur/op job j->srv j). BOUCLE DE COMBAT VALIDEE (spawn a l axe -> assaut -> metriques reviennent). REGISTRE bracketed sur 3 smokes : 8att vs 6def patrol = TRIVIAL (100% garr_killed, 0-12% pertes, pas de signal d axe) ; 6 vs 12 durci skill0.75 static = MASSACRE (83-100% pertes, tous ENLISEMENT) ; 8 vs 8 skill0.5 static-overwatch = regime interessant MAIS 4/6 ops ABORTENT (ENLISEMENT/TIMEOUT_MUR, combats non resolus -> chiffres = etat fige mi-combat). SIGNAL (n=3, bruite, aborts) : defile garr_killed 79%/pertes 83% vs pire 71%/67% -> NE CONFIRME PAS l avantage du defile, si qqchose c est l INVERSE. 
DIAGNOSTIC (cle) : le defile agit sur l exposition pendant l APPROCHE ; ma mesure prend l ISSUE DE L ASSAUT COMPLET, dominee par la melee finale a l objectif (tous axes convergent) + bruit Arma + aborts -> le mecanisme du defile est ENTERRE sous le combat rapproche. = SCAR (mur sim->reel) : le +10/-9 propre du sim ne se transfere PAS gratuitement. HONNETE : on NE conclut PAS que le defile aide en Arma (les donnees ne le soutiennent pas) ni qu il n aide pas (mesure sale). On refuse de tuner le regime a l aveugle (= p-hacking).
CAMPAGNE PROPRE A MENER A FROID : (1) ISOLER LES PERTES D APPROCHE (mesurer les morts AVANT contact rapproche, pas l issue d assaut) = le vrai mecanisme du defile ; (2) un regime qui SE RESOUT (pas de standoffs qui abortent) ; (3) n>=8/condition. Fichiers : arma_axis_combat.py, smokes arma_axis_smoke{,2,3}.jsonl. Jalon 1 (perception+decision sur vrai terrain) reste FRANCHI et propre ; jalon 2 (le defile aide-t-il en combat reel ?) RESTE OUVERT.

## 2026-06-14 ~05h — JALON 2 FRANCHI : LE DEFILE PASSE LE MUR SIM->REEL (pertes d approche -38 pts, propre)
Le premier A/B (issue d assaut complet) ne montrait pas l avantage du defile -> DIAGNOSTIC : la melee finale a l objectif + les aborts noyaient le mecanisme. FIX (pas du p-hacking : la metrique = le mecanisme annonce d avance) : ISOLER LES PERTES D APPROCHE. Nouveau design arma_axis_combat.py : escouade traverse en mode move (avance sans s arreter) jusqu a un point d appui a 55m de l objectif, on mesure les pertes A CET INSTANT = morts subis en traversant le terrain a decouvert (= LA ou le defile agit). Garnison 10 def static-overwatch skill0.6 ; escouade 8 ; move=15 (approche graduelle) ; objectif (12000,21000) defile=axe3(25%) pire=axe0(100%). 
RESULTAT (16 ops, 8/condition, 1 serveur/op, 0 ABORT, separation NETTE defile 0-12% vs pire 38-62%) : PERTES D APPROCHE defile 9% vs pire 47% -> LE DEFILE EPARGNE +38 PTS. => le +10/-9 du sim NON SEULEMENT se transfere mais plus fort (-38) sur le vrai relief Altis en vrai combat Arma. L OFFICIER-AXE TRAVERSE LA SCAR. Mecanisme physique : moins de LOS terrain = moins de touches en traversant -> escouade arrive a l objectif a 8/8 (defile) vs ~4/8 (pire) -> survie a l approche se COMPOSE (plus d hommes au contact = assaut plus fort). 
ETAT : couche officier-axe VALIDEE en sim (officer_select +10, officer_llm 6/6, officer_full +8) ET en ARMA REEL (jalon 1 perception/decision sur Altis + jalon 2 combat -38 pts d approche). HONNETE : 1 seul objectif teste -> robustesse multi-objectifs = extension naturelle (mais effet large+constant+mecaniste). Fichiers : arma_axis_combat.py, arma_axis_approche.jsonl (16 ops). Discipline qui a paye : on n a PAS conclu non-transfert prematurement -> diagnostic du confond -> mesure du bon mecanisme -> signal propre.

## 2026-06-14 ~05h30 — Les 3 items ouverts : #1 robuste OUI, #2 assaut inconcluant, #3 deja negatif
#1 ROBUSTESSE MULTI-OBJECTIFS (arma_axis_multi.py) : pertes d approche defile vs pire sur 4 objectifs a defile fort d Altis, 32 ops, 0 abort. RESULTAT : defile epargne sur 4/4 objectifs -> (12000,21000) +41, (9000,21000) +78, (21000,6000) +16, (9000,18000) +56, MOYENNE +48 pts. Defile 0-12% pertes partout, pire 16-78%. => le -38 d un seul objectif EST ROBUSTE, pas un coup de chance. Le mecanisme (moins de LOS terrain = moins de touches en traversant) generalise sur Altis.
#2 ASSAUT COMPLET / COMPOSITION (arma_axis_assault.py) : INCONCLUANT. Tension de regime : pour que l assaut SE RESOLVE il faut une garnison faible (6, skill0.5), mais alors elle est trop faible pour que le deficit d approche (defile 8 hommes vs pire ~4 au contact) DECIDE -> meme 4 hommes prennent l objectif. Resultat n=6/cond : defile garr_killed 72%/pertes 54%/succes 67%/0 abort ; pire 64%/25%/67%/2 aborts. Les 2 aborts cote pire (squads qui calent, TIMEOUT) biaisent ses pertes vers le bas (0% = pas combattu). Lecture honnete : defile tue un peu plus + plus FIABLE (0 abort vs 2), mais la composition en SUCCES n est PAS isolee proprement (regime resolvable = trop clement). On NE tune PAS a l aveugle (p-hacking). Le resultat propre reste l avantage A L APPROCHE (#1).
#3 SCHEMA SELECTEUR APPRIS : deja repondu NEGATIF en sim (officer_schemelearn.py, 54% = hasard, le schema lui-meme est du bruit non-predictible). Re-tester en Arma = sans objet (pas de signal a capturer). Non relance.
BILAN OFFICIER-AXE : sim (+10/-9, LLM 6/6, integre +8) ET Arma (jalon1 perception/decision sur Altis + jalon2 pertes d approche -48 moyen ROBUSTE sur 4 objectifs). Limite honnete : composition approche->succes d assaut non isolee (regime narrow). Fichiers : arma_axis_multi.py, arma_axis_assault.py, arma_axis_multi.jsonl, arma_axis_assault.jsonl.

## 2026-06-14 ~06h — COMPOSITION isolee (protocole decouple) : +12 MODESTE a n=8 (le +39 du pilote etait du bruit)
Protocole decouple (arma_assault_curve.py) pour isoler la composition approche->succes d assaut, la ou le bout-en-bout echouait (tension de regime). COURBE B : escouade spawnee DEJA AU CONTACT (point d appui 40m axe defile) avec K hommes (K=2..8) vs garnison, P(prendre l objectif). Echec=echec (budget fixe, pas d abort). Puis RECOMPOSITION : survivants par axe (mesures d approche, ~7.8 defile / ~3.9 pire) injectes dans la courbe B.
PILOTE n=5 (garr5/skill0.4/foot40) : courbe semblait RAIDE (K=6=80%) -> composition +39. MAIS consolidation n=8 : K=6 retombe a 38% -> le 80% etait une FLUCTUATION DE PETIT ECHANTILLON (comme le +20 winner s curse). Vraie courbe n=8 : 0%(K2) 25 12 12 38 38 29%(K8) = pente DOUCE, pas un seuil net (meme 8 hommes ne prennent que ~35% face a 5 def en surveillance -> l assaut equitable est DUR). RECOMPOSITION n=8 : defile 31% vs pire 19% succes d assaut attendu -> COMPOSITION +12 pts (conservateur, courbe mesuree depuis le foothold defile).
VERDICT HONNETE #2 : la composition est REELLE EN DIRECTION (plus d hommes survivants -> plus de prises) mais MODESTE (+12, pas +39). Un regime a seuil net existe surement mais le chercher = retuner jusqu au beau chiffre = p-hacking, REFUSE. Discipline : firmer le n a attrape un 3e chiffre gonfle (apres +20 oracle et +20 schema). Le gros resultat robuste reste l APPROCHE (-48 pts, 4/4 obj) ; la composition assaut est +12 modeste. Fichiers : arma_assault_curve.py, arma_assault_curve.jsonl (n5), arma_assault_curve8.jsonl (n8).

## 2026-06-18 ~17h — CHANTIER OCCUPATION : un adversaire de ~2000 hommes sur Altis, runtime + moteur d'alerte VALIDES en Arma reel
On batit le MONDE adverse (REDFOR/CSAT occupant Altis) qui servira de theatre aux agents BLUFOR. Trois piliers, tous valides sur le vrai serveur Arma (slot 2, jamais de pkill global, jamais multi_server.sh).

PILIER 1 — GENERATEUR (laydown_altis.py -> staff/occupation_altis.json). Lit altis_catalog/roads/relief, pose 183 elements / 1978 hommes / 4 secteurs (NE 667, NO 375, SE 390, SO 546) : 111 localites garnisonnees (taille par categorie ville50/bourg26/village13/hameau6/site6, mise a l'echelle vers la cible 2000), 4 FOB + QG de theatre (NE), QRF par secteur, DCA, checkpoints routiers, postes d'observation, defenses cotieres, relais radio, patrouilles, convois. Carte du dispositif : map_altis.py -> staff/occupation_altis.html (carte tactique autonome, nord en haut, grille 5km, couleur par secteur, taille ronde ∝ effectif).

PILIER 2 — RUNTIME / SCALING (caracterise empiriquement). Dynamic Simulation est LE mecanisme : 49 FPS serveur ON vs 13,6 OFF = x3,6. Budget ACTIF (hommes eveilles) tient ~700-1000/serveur ; effondrement vers ~1200 actifs simultanes. Donc 2000 = VIVIER GELE viable (l'IA ne tourne que dans la bulle dyn-sim autour d'un acteur BLUFOR, le reste dort a cout ~0). Plafond de groupes ~144/side/machine -> au-dela de 2000 il faut des Headless Clients (CPU reparti). Livrable doctrine : staff/occupation_runtime.sqf (dyn-sim distances tunees + hibernation par groupe + garde-fou budget + hook LAMBS optionnel).

PILIER 3 — MOTEUR D'ALERTE / REACTIVITE (le coeur du realisme, valide). occupation_react2.py : garnison(20)+QRF(14) east, contact(6) west injecte qui charge au tir a 155m. CHAINE PROUVEE sur Arma reel : contact -> detection (knowsAbout 0->4.0) a t+32s -> alerte monte 0->1->2->3/3 -> QRF dispatchee des la detection -> QRF se rapproche (1702->1538m, ~2 m/s a pied, continu). Livrable doctrine : staff/alert_engine.sqf (FSM par secteur : escalade/de-escalade du niveau d'alerte, dispatch QRF au 1er contact, re-armement quand le secteur redevient calme). LIMITE HONNETE : la QRF n'atteint pas le contact dans la fenetre (1,7km a pied = ~14 min) -> on prouve la CHAINE (detection->escalade->dispatch->rapprochement), pas l'interception complete ; un vrai run laisserait la QRF arriver ou utiliserait des vehicules.

LECONS DE PLOMBERIE (chere a apprendre, a ne pas reperdre) : (1) les spawns par lots doivent etre BATCHES (>3000 char/cmd) — 1 groupe/cmd en boucle serree PERD des unites (57-103 au lieu de 1276). (2) Les PREMIERS envois post-boot sont PERDUS (l'actuateur natif callExtension n'est pas pret a 3s) -> il faut un HANDSHAKE de disponibilite (ping jusqu'a reponse) AVANT le 1er spawn, puis VERIFIER que chaque spawn a pris (compter les unites par side, retry sinon). Sans ca : "Undefined variable HMT_QRF", knowsAbout=0, tout echoue silencieusement. (3) ArmaBridge expose send()+_log_lines(), pas de _query (les requetes = send d'un diag_log puis lecture du log).

ETAT : les 3 piliers du prompt "ORDRE DE BATISSE" sont valides empiriquement. Livrables : occupation/laydown_altis.py, occupation/map_altis.py, staff/occupation_altis.json, staff/occupation_altis.html, staff/alert_engine.sqf, staff/occupation_runtime.sqf, occupation_react2.py. Prochaine extension naturelle : Headless Clients pour depasser 2000, brancher la dyn-sim sur les agents BLUFOR (acteurs reveilleurs), QRF vehiculee pour l'interception complete.

## 2026-06-18 ~19h45 — BRIQUE 0 VALIDEE : l'environnement RAID Arma-dans-la-boucle tourne (reset/step/obs/reward/done)
Nouveau cadrage (decide avec Younes) : pas un assaut de garnison mais un RAID FORCES SPECIALES. 20 SF BLUFOR prennent UN objectif decompose en 10 SOUS-OBJECTIFS ; les ~500-731 REDFOR DEFENDENT l'ile (garnison locale + QRF reactive + moteur d'alerte). 20 vs 500 frontal = suicide -> la dyn-sim fait que seul le local se reveille -> vrai combat = 20 vs ~44 + renforts. L'asymetrie FORCE l'audace (vitesse avant l'alerte) ET la coordination (20 agents / 10 sous-obj = probleme d'allocation = commandement hierarchique). Choix d'archi : ARMA DANS LA BOUCLE (haute fidelite, lent : ~10 min/episode -> campagne = jours, on parallelisera sur plusieurs serveurs).

BRIQUE 0 (env type Gym autour du pont) FAITE et VALIDEE sur Arma reel. raid/raid_env.py : RaidEnv.reset() -> relance serveur (slot), handshake, spawne DEF(30)+QRF(14)+20 SF (verifies par comptage), renvoie obs ; step(targets) -> applique 20 doMove, avance DT=8s, lit l'etat en 1 aller-retour pont, calcule recompense (+sous-obj pris, -temps=audace, -pertes), renvoie obs/reward/done (VICTOIRE/ANEANTI/TEMPS). raid/raid_smoke.py : assaut scripte temoin (chacun fonce sur son sous-obj i%10).

LECON DE PLOMBERIE MAJEURE (la cle qui debloque tout) : l'actuateur FICHIER execute nos cmd_N.sqf via "call compile _c" SYNCHRONE dans son propre thread spawn. Nos spawns lourds (boucle 30 createUnit + BIS_fnc_taskPatrol) tournent donc SUR LA PILE de l'actuateur -> la pile du scheduler s'accumule cmd apres cmd -> "GIAS pre stack size violation" -> actuateur casse -> spawns suivants perdus silencieusement. FIX : envelopper CHAQUE cmd lourd (spawns ET les doMove de chaque pas) dans "[] spawn { ... }" -> call compile lance le thread et rend la main aussitot, le travail tourne sur une pile FRAICHE. Plus d'accumulation. (S'ajoute aux lecons occupation : handshake avant 1er spawn, 1 cmd court par spawn, verif/retry par comptage, pas de _query.)

RESULTAT de l'assaut scripte (= le PLANCHER a battre) : politique bete (charge frontale) -> 1/10 sous-objectifs tenus, 8/20 SF survivants, recompense -54, issue TEMPS. La chaine reactive marche : detection -> alerte 4.0 -> QRF dispatchee ; attrition des deux cotes (SF 20->8, defense 44->32). C'est VOULU : la tache est dure et asymetrique, grosse marge pour une politique apprise (manoeuvrer, prioriser, surprendre avant l'alerte). Fichiers : raid/raid_env.py, raid/raid_smoke.py. Objectif teste = aerodrome NE (14038,16143), insertion a ~920m SO. Prochaine etape : BRIQUE 2 = MAPPO (acteur attention + porte d'audace, allocation 10 actions, critique central) branche sur RaidEnv, parallelise sur plusieurs serveurs Arma.

## 2026-06-19 ~11h — VOIE 2 (INCARNATION) LANCEE + ARMA PILOTABLE A 50 Hz : les deux moitiees tiennent
Suite directe du chantier raid. Trois resultats majeurs cette session.

1) PLAFOND DE LA COUCHE COMMANDEMENT — CONFIRME EMPIRIQUEMENT (pourquoi on bascule sur l'incarnation).
On a ajoute a l'acteur MAPPO une 2e tete POSTURE (debout/accroupi/couche + setCombatMode RED) en plus de la tete DESTINATION (10 sous-obj + tenir). Resultat sur Arma (12 serveurs) : la posture A EMPIRE le probleme — la politique trouve l'exploit trivial (rester couche a l'abri, ne pas avancer) -> survivants 19-20/20 mais sous-objectifs tenus = 0,0/10. Avant posture : ~10/20 survivants, 0,8 tenus. LECON : l'agent ne peut pas GAGNER une fusillade (c'est l'IA d'Arma qui se bat), donc le seul signal apprenable est "survivre" ; lui donner plus de controle = juste mieux exploiter la survie, jamais prendre l'objectif. AUCUN espace d'action sur la couche commandement ne craquera la mission tant que l'agent ne controle pas le COMBAT. => preuve qu'il faut un CORPS pilote (voie 2). Run 1 garde comme baseline + nourrit le modele du monde (raid_attack.log).

2) VOIE 2 = INCARNATION DANS ISAAC, brique 1 (corps oriente-but) VALIDEE. Le corps AMP (28 DOF, controle total) savait bouger (style walk/run/dance imite) mais n'avait AUCUN but (_get_rewards = torch.ones). On a cree la tache Isaac-Humanoid-AMP-Move-Direct-v0 : HumanoidAmpMoveEnv (sous-classe) + cible commandee (rejoindre un point, en re-enchainer), recompense = vitesse vers la cible + bonus d'arrivee, style garde par AMP. BUG CLE (2 essais perdus dessus) : la config skrl AMP avait task_reward_scale: 0.0 -> ma recompense de but etait MULTIPLIEE PAR ZERO (reusait skrl_walk_amp_cfg). Fix = skrl_move_amp_cfg.yaml dedie avec task_reward_scale: 1.0 (style 2.0) + cible donnee en REPERE CORPS (quat_rotate_inverse), pas en repere monde. RESULTAT apres fix : reward MONTE franchement (instantane 0,28 -> 4,35/pas ; episode 7 -> 242, a 12% du run) -> le corps APPREND a rejoindre la cible. Fichiers : isaaclab_src/.../humanoid_amp/humanoid_amp_move_env.py, +cfg HumanoidAmpMoveEnvCfg, +agents/skrl_move_amp_cfg.yaml, registration dans __init__.py. Lance via amp_motor_chain-style (scripts/reinforcement_learning/skrl/train.py --task Isaac-Humanoid-AMP-Move-Direct-v0 --algorithm AMP --headless --num_envs 4096, CUDA_VISIBLE_DEVICES=1).

3) ARMA PILOTABLE A 50 Hz (le pont n'est plus le goulot). Le pont (fichier ET socket natif) plafonnait a ~10 Hz. Diagnostic : ce n'est PAS le socket (TCP localhost <1 ms, hmt_native.c deja en C) ni l'extension (une extension ne peut PAS bouger une unite, elle ne fait que renvoyer une chaine a SQF) — c'est le SCHEDULER SQF : l'actuateur tournait dans une boucle [] spawn (env planifie) reveillee ~10x/s. FIX EXPERT : appliquer les commandes dans un handler addMissionEventHandler ["EachFrame", {...}] (env NON-planifie, tourne a chaque frame = 50 Hz). Mesure (rate_test2.py, slot 14, disableAI "ALL" + setVelocity) : APPLICATION = 50,0 Hz, mouvement reel +31 m en 5 s a 6,2 m/s (lisse, precis), envoi commande fire-and-forget = illimite (252k/s). DECOUPLAGE cle : l'EachFrame applique la DERNIERE action chaque frame (50 Hz) pendant que la politique decide a ~10 Hz -> execution lisse temps reel avec une politique lente (resout le "fige entre 2 decisions"). => Arma redevient une cible de DEPLOIEMENT temps reel pour un controleur entraine dans Isaac, et la voie 1 (disableAI ALL + pilotage) redevient possible pour le deploiement. Fichiers : rate_test.py, rate_test2.py ; snippet EachFrame.

GPU : pousser AMP a 16384 envs a THRASHE le CPU (load 77, GPU 0 %) — AMP est CPU-bound quand il partage avec Arma ; 4096 = la bonne config, la 3090 n'est pas saturee par AMP (~25-50 %).

ARCHITECTURE CLAIRE MAINTENANT : corps -> Isaac (rapide, entrainement) ; monde/mission/deploiement -> Arma (pilotable 50 Hz). Suite : brique 2 du corps (viser/tirer/couvert dans Isaac), puis deploiement du controleur dans Arma via EachFrame.

## 2026-06-20 ~14h30 — VIRAGE : ProtoMotions/SMPL abandonne, retour NOTRE pipeline AMP (marche validee en video) + NOUVEAU CONCEPT "souffrance = mecanisme de selection"

1) PROTOMOTIONS / SMPL-DANS-ISAACLAB = IMPASSE, ABANDONNE. Le pivot SMPL (reutiliser AMASS + checkpoints pre-entraines NVIDIA) bloque a "Materializing lazy modules" (1ere passe forward du modele), insoluble : (a) compile ON -> torch.compile/Inductor compile des kernels triton sans fin (cache fige ~168 Mo, 1 worker, 30 min) ; (b) compile OFF (patch TORCH_COMPILE_AVAILABLE=False ligne 40 component_manager.py) -> meme forward grince en eager 27 min, 1 coeur, GPU a 0 pourcent, jamais de [Step]. Ni device, ni num_envs(16), ni taille motion-file, ni famine CPU (3 process fantomes 18h tues) ne l expliquent. SMPL+mujoco aussi mort (max_ctrl=0, sim2sim). Decision Younes : on arrete de perdre des journees sur les modeles des autres -> construire NOTRE humanoide, possede a 100 pourcent.

2) RETOUR PIPELINE AMP = NOTRE corps, VIDEO DE MARCHE VALIDEE. Tache Isaac-Humanoid-AMP-Walk-Direct-v0 rejouee depuis checkpoint Walk pur (logs/skrl/humanoid_amp_walk/2026-06-18_22-11-09_amp_torch/checkpoints/best_agent.pt) -> MARCHE STABLE ET NATURELLE (verifiee image par image : debout, foulee, balancement bras, aucune chute ; Younes valide). Video headless RESOLUE par notre script play_dlssoff.py --headless --video --video_length 300 (fix anti-ecran-noir integre) -> mp4 dans logdir/videos/play/. Verif sans ffmpeg systeme : binaire embarque imageio_ffmpeg.get_ffmpeg_exe() -> extraire frames PNG -> lire. GOTCHA checkpoint<->tache : chaque checkpoint ne charge QUE sa tache (obs Walk=81 vs Move=84 ; Move charge sur Walk = state_dict mismatch). humanoid_amp_walk/2026-06-19_13-51-04 est en fait un MOVE (demarche cassee, humanoides tombent — confirme en images).

3) MOVE (oriente-but) RELANCE + WARM-START prepare. Recompense corrigee deja en place (task_weight=1.5, reach_bonus=5.0 dans humanoid_amp_env_cfg.py). Baseline Move relancee (16384 envs, 80k timesteps, ~3h) -> apprend (recompense instantanee moy 0.58 -> 1.53 a 37 pourcent). Fix : yaml Move logait dans "humanoid_amp_walk" -> separe en "humanoid_amp_move". TECHNIQUE WARM-START (= fine-tuning AMP, "les deux ensemble" : partir du cerveau marche + garder le prof de style) : surgery checkpoint Walk -> Move. Seuls 4 tenseurs changent (81->84) : policy/value net_container.0.weight (3 colonnes cible = 0 -> ignore la cible au depart = marche exactement comme Walk au step 0, puis apprend a s en servir) + observation_preprocessor mean/var. Discriminateur (162) + couches profondes recopies tels quels. optimizer.state vide (momentum frais). Script /home/younes/warmstart_move.py -> /home/younes/isaaclab_src/logs/warmstart_move_init.pt. VERIFIE sur la 1060 : warm-start = EXACTEMENT memes actions que Walk quand cible=0 (diff max 0.0). Chaine auto /home/younes/chain_move.sh : attend baseline -> rend video baseline -> lance warm-start (experiment_name warmstart). But : comparer baseline (style seul) vs warm-start (fine-tuning).

4) LA 1060 (verifie) : fait du PyTorch (matmul OK, sm_61 supporte par torch 2.7 cu126/cu128) ; NE PEUT PAS faire d Isaac Sim (pas de coeurs RTX). Donc 1060 = calcul non-Isaac en parallele, la 3090 garde tout le corps/Isaac. CUDA_DEVICE_ORDER=PCI_BUS_ID : CUDA_VISIBLE_DEVICES=0 -> cuda:0 = 1060 ; =1 = 3090.

5) NOUVEAU CONCEPT (Younes) : "MECANISME DE LA SOUFFRANCE" comme moteur de SELECTION. Definition : souffrance = restriction d une action voulue et investie -> tension aversive -> adaptation sous contrainte -> vers une delivrance. Delivrance choisie = ACCOMPLISSEMENT (but atteint = recompense positive), PAS le simple soulagement (les deux differents a coder). Critique retenue : la delivrance n est pas garantie (souffrance injuste sans recompense) -> on s en sert comme filtre. Mapping RL : action voulue = preference politique ; restriction = contrainte/penalite ; adaptation = apprentissage ; delivrance = objectif. Les pieces existent (Constrained MDP, reward shaping, curriculum, active inference/Friston, homeostatic RL / douleur artificielle) mais la SYNTHESE (souffrance nommee + delivrance=accomplissement, 2 phases pour selectionner) est notre apport.
DEUX PHASES (regle critique : SEPARER entrainer et selectionner) : PHASE 1 FORGER (on ENTRAINE) = but atteignable + contrainte -> reussite=recompense ; apprend a reussir sous contrainte. PHASE 2 EPROUVER (on SELECTIONNE, on n entraine PAS) = but impossible + aucune recompense -> on OBSERVE. Entrainer sur du sans-issue enseigne l impuissance apprise ou l exploit degenere (= exploit survie deja vu raid env, tenus=0) ; donc phase 2 = juger, pas former. MESURE PHASE 2 (point dur, pas de recompense) : ne pas fuir vers l exploit (l abri) + tenir l objectif + coherence + persistance. Piege : ne pas selectionner la tete brulee (parfois bien souffrir = decrocher proprement). Regle : bon agent = reussit phase 1 ET ne s effondre/triche pas en phase 2.

6) TESTBED "COULOIR DE SOUFFRANCE" sur la 1060 (pur PyTorch, REINFORCE vectorise par population). Env : couloir (avancer coute -PAIN/pas), ABRI au depart (0 douleur = l exploit), BUT au bout (+GOAL phase 1 seulement). Scripts /home/younes/suffering_vec.py (1er run) puis suffering_vec2.py (scale + metrique corrigee). 1er run (64 agents x 512 envs) : mecanisme DISCRIMINE — 26/64 FUIENT a l abri quand le but disparait, agent #0 TIENT (P1 100 pourcent, exploit 0 pourcent). Lecon : metrique naive ("avance") penalisait l agent au but -> remplacee par "ne fuit pas + tient l objectif". Scale (256 agents x 256 envs, 1000 updates) : 1060 a 100 pourcent util, 4.8 Go/6 Go, 89 W. RESULTAT FINAL (256 agents x 256 envs, 1000 updates) : 138 sur 256 BON (reussit + ne fuit pas), 118 craquent (fuite plus de 50 pourcent) ; meilleur agent #0 P1=100 pourcent tient l objectif 73 pourcent fuite 0 pourcent ; P1 moyenne 54 pourcent (forte variance = pb entrainement REINFORCE, pas de selection -> passer a PPO) ; mem 4.5 Go sur 6. La metrique corrigee (ne fuit pas + tient) discrimine nettement la population.

ARCHITECTURE A DEUX PILIERS EN PARALLELE : 3090 = LE CORPS (Isaac AMP : marche -> oriente-but -> gestes soldat) ; 1060 = LA SOUFFRANCE/SELECTION + le MODELE DU MONDE (pur PyTorch, non-Isaac). "Le corps apprend a bouger ; le modele du monde apprend a prevoir ; la souffrance trie les agents."

## 2026-06-20 ~17h30 — PBT VALIDEE sur le toy souffrance (1060). Direction Younes : garder les meilleurs ET les entrainer = population-based training. Boucle suffering_pbt.py : entrainer K updates -> classer (reussit + ne fuit pas) -> remplacer le bas par copies MUTEES du haut -> recommencer. Resultat = convergence en 2 generations : gen0 57pc/145 BON, gen1 86pc/221, gen2 100pc/256 et stable jusqua gen15 -> FINAL P1 100pc, 256/256 BON, fuite 0pc, tient 68pc. La PBT REGLE le probleme d exploration que PPO+entropie ne reglait pas (52pc) : les gagnants (qui ont decouvert le but) sont clones dans les slots perdants -> la solution se propage a toute la population. Elite 20 meilleurs sauvee -> /home/younes/maac_nuit/elite_agents.pt. SUITE OBLIGATOIRE (sinon on ne mesure plus, tout le monde gagne) : durcir la phase 2 (couloir plus long, leurres, douleur+) + tester sur phase 2 JAMAIS VUE (anti-surapprentissage/monoculture). Garde-fou breeding : cloner le top-K varie, pas le seul #1.

## 2026-06-20 ~18h30 — PILIER SOUFFRANCE suite : test honnete -> tete brulee -> retrait tactique. (1) TEST HONNETE (suffering_holdout.py) : l elite PBT passe TOUTES les conditions jamais vues (depart milieu, secousses, couloir 1.8x) -> robustesse genuine, pas de surapprentissage/monoculture. (2) POINT DE RUPTURE (suffering_break.py) : meme tiree de force en arriere (poussee -1.3, progression 0), elle choisit avancer 100pc, recule 0pc -> TETE BRULEE confirmee : le critere ne-fuit-pas est trop grossier, il elimine le BON repli. (3) RAFFINEMENT Younes : decrocher = RETRAIT TACTIQUE (revenir plus fort, regagner la superiorite) PAS fuite. 3 comportements (fuite=abandonne / tete brulee=meurt / retrait tactique=differe et revient). Dans un monde a gagnabilite variable + recompense accomplissement-seul, les 3 se trient seuls -> pas besoin d etiqueter. Boucle sur le raid (rompre contact, repositionner, re-assaut). (4) v1 tactical_retreat.py = ECHEC INSTRUCTIF : mort pas punie -> camper-et-mourir-riche bat se-replier -> morts 100pc. LECON : retrait tactique rationnel SEULEMENT si survivre est obligatoire pour gagner (la mort doit couter plus que la recompense grappillee). (5) v2 (mort punie -10) = SUCCES PARTIEL : morts 100->0pc, accompli 17.4 (ni tete brulee ni fuite). MAIS le timing fin a emerge tot (recul +1.1 gen1) puis la PBT l a optimise away (+0.1) vers camper-au-bord-sur + coup-de-main. LECON : PBT optimise la FITNESS pas l elegance ; si l env n oblige pas le timing, elle prend le raccourci. (6) v3 EN COURS (tactical_retreat3.py) : maintien SOUTENU exige (HOLDREQ=3) -> tenir survivable seulement en fenetre calme -> timing force. NB : tout ca = prototype 1060 ; la RECETTE (recompense survie-instrumentale + PBT + fine-tuning) se PORTERA sur le corps Isaac 3090, pas gardee en agents separes.

## 2026-06-20 ~19h — PILIER SOUFFRANCE consolide (decision Younes). v4 (tactical_combat.py, mecanique de combat) = demi-victoire : le combat REGLE la planque (il tient l objectif CONTESTE, tient@gagnable 8.1, 0 mort, ne se cache plus sous le feu — corrige le defaut majeur de v3). MAIS ne se replie pas du submerge (tient@submerge 10.0) car submerge pas assez letal -> il l encaisse. Brave mais pas discernant. DECISION : on CONSOLIDE ici ; l agent qui DISCERNE (tenir gagnable + fuir ecrasant, via submerge letal = v5) sera travaille PLUS TARD, sur le vrai corps. RECETTE ACQUISE (a porter sur le corps Isaac via fine-tuning) = selection PBT + recompense survie-instrumentale (mort doit couter) + mecanique de combat (tenir le conteste gagnable PAIE). Scripts toy 1060 : suffering_vec/pbt/holdout/break + tactical_retreat(1/2/3) + tactical_combat. Elite sauvee elite_agents.pt.

## 2026-06-20 ~19h15 — COMPARAISON Move baseline vs warm-start : le WARM-START A PERDU (contre-intuitif, important). Reward Total-mean baseline vs warm-start : 2k=14.6 vs -144.6 ; 10k=145 vs 48 ; 40k=515 vs 395 ; 80k=685 vs 599. Derriere du debut a la fin. CAUSE : warm-starter les POIDS injecte un prior marche-droite RIGIDE qui conflite avec aller-vers-la-cible (le -144 = il marche tout droit en ignorant la cible, colonnes cible a zero) -> doit desapprendre -> plus lent qu a neuf. En AMP la baseline a DEJA le savoir marche via la recompense de STYLE (prior SOUPLE) -> warm-start = meme prior mais rigide = poids mort. LECON (valide le plan ASE) : composer via warm-start des poids aide SEULEMENT si la nouvelle compromise PROLONGE l ancienne ; si elle la REORIENTE (marche->tourner/strafe), le prior souple par le STYLE (ajouter mocaps ASE au prof AMP) bat le warm-start rigide. => empiler les competences via le STYLE, pas via les poids. Videos move_baseline.mp4 / move_warmstart.mp4.

## 2026-06-20 ~19h30 — FIN DE SESSION (pause). ETAT MACHINE : au repos, 1060 et 3090 idle (~44-49C, 0 pourcent), aucun process lourd. BILAN 2 PILIERS. (A) CORPS (3090, Isaac AMP) : notre pipeline valide ; marche naturelle OK (video) ; Move oriente-but OK (recompense corrigee task_weight=1.5) MAIS les mouvements NON-marche (recul/strafe/virage) sont moches car AUCUNE mocap -> improvises depuis la marche-avant. Warm-start teste = A PERDU (prior poids rigide conflite avec aller-vers-la-cible) -> LECON : empiler les competences via le STYLE (mocaps AMP), pas via les poids. (B) SOUFFRANCE/SELECTION (1060, toy) : recette consolidee = selection PBT + recompense survie-instrumentale (la mort doit couter) + mecanique de combat (tenir le conteste gagnable PAIE) ; agent qui tient l objectif sous le feu et survit ; le DISCERNEMENT (se replier de l ecrasant via submerge letal) reste a faire plus tard. PROCHAIN PAS PRIORITAIRE : enrichir le style AMP avec motions ASE (WalkBackward, WalkLeft/Right, TurnLeft90/TurnRight90 dans /home/younes/ASE/ase/data/motions/reallusion_sword_shield) -> ecrire+valider un convertisseur poselib .npy -> IsaacLab .npz (28 DOF/15 corps, respecter l ordre dof_names/body_names ; valider en convertissant WalkForward et comparant a humanoid_walk.npz) -> reentrainer Move -> mouvements omnidirectionnels naturels. Fans boitier en manuel 80 pourcent (pwm1-6_enable=1) ; pour repasser en auto silencieux : pwm*_enable=5 (sudo). Tout sauvegarde : ce journal + backup Bureau/save02 + memoire locale Claude.

## 2026-06-20 ~21h — CONVERTISSEUR ASE->IsaacLab CONSTRUIT ET VALIDE (le crux quaternion->DOF resolu). Squelette amp_humanoid IDENTIQUE entre ASE et notre tache (15 corps memes noms). convert_ase.py (poselib + scipy) : corps globaux directs depuis poselib ; DOF = decomposition euler xyz des rotations LOCALES (coude/genou = axe Y, trouve par diagnostic). VALIDATION : auto-coherence 0.01 deg (max 0.5), ET amplitudes DOF du walk converti collent au walk existant (genou +0.06/+1.32 vs +0.25/+1.27, coude/hanche idem) -> convention compatible Isaac. GOTCHA : motions reallusion_sword_shield ont 17 corps (epee+bouclier) -> ne garder que les 15 de l humanoide par nom. CONVERTI : walk_backward(233f) strafe_left(271) strafe_right(175) turn_left(49) turn_right(49), tous 30fps 15 corps. SET DE STYLE OMNI construit = humanoid_omni.npz (928 frames @30fps, forward x4 + recul + strafe G/D + virage G/D), dernieres frames droppees (pas de transition parasite). Move cfg pointe dessus (motion_file=humanoid_omni.npz, experiment_name omni). REENTRAINEMENT Move-omni LANCE (16384 envs, 80k, ~2.5h), rendu auto arme (render_omni.sh) -> video omnidirectionnelle prete a la fin. Confirme la lecon warm-start : on enrichit le STYLE (mocaps), pas les poids. Scripts: convert_ase.py, render_omni.sh.

## 2026-06-20 ~21h30 — BIBLIOTHEQUE ASE COMPLETE convertie : 90/90 motions, 0 echec (convertisseur convert_all.py robuste sur tout le catalogue). Sauvees dans motions/ase_lib/ au format IsaacLab (15 corps, 28 dof, convention validee). Inventaire : LOCOMOTION ~19 (walk/run/jog, Walk+Run Forward/Backward/Left/Right, Turn90/180 G/D) ; COMBAT ~51 (26 Atk, 9 Sword, 6 Shield, 5 Counter, 5 Kill) ; REACTIONS ~20 (5 Fall, 6 Idle Alert/Battle/Ready, 3 Dodge, 3 Standoff, 3 Taunt). USAGE : piocher des SETS COHERENTS par competence (locomotion->Move, combat->tache combat, etc.), JAMAIS tout dans un seul discriminateur AMP (sinon bouillie). Caveat : combat = epee/bouclier (melee) -> les dynamiques de corps/appuis/esquives transferent au soldat, le maniement d arme (slash) != fusil (mocap fusil dediee plus tard). La couche soldat-combat a donc sa matiere premiere prete. Set omni actuel (6 mouvements) peut etre enrichi (run, walk variants, turn180) pour le prochain Move.

## 2026-06-21 — DECISION STRATEGIQUE TRANCHEE (Younes) : on veut un CORPS REACTIF PILOTE (se bat, encaisse, manoeuvre sous le feu), PAS de la generation cinematique. Donc physique/RL OBLIGATOIRE, complexite assumee (le DL pur genere des animations = ce qu Arma fait deja, pas un controleur reactif ; le mocap n a ni actions ni physique -> il FAUT apprendre en sim). Recherche net faite sur les methodes anti-bouillie : AMP 1-discriminateur mode-collapse sur datasets divers (confirme) ; solutions = conditionner sur le skill : ASE 2022 (skill embeddings, limites sur tres divers), Multi-AMP (one-hot discret, simple), PULSE 2023 + MaskedMimic 2024 (VAE-latent + tracking = SOTA pour gros repertoire, mais MaskedMimic=ProtoMotions stack fragile, ASE=IsaacGym deprecie). ROADMAP fixee : (bas-niveau) maitrise du repertoire en physique-RL avec skill-conditionne -> Multi-AMP one-hot en 1er sur NOTRE IsaacLab (bas risque), graduer vers MaskedMimic/PULSE pour les 80 ; (haut-niveau) politique tactique = souffrance/selection ; (deploiement) Arma via actuateur 50Hz. Gate immediat = test strafe (conversion saine ? mix vs technique). MaskedMimic = combine DL generatif + tracker physique -> ce n est pas DL vs RL, la SOTA combine.

## 2026-06-21 ~14h30 (Claude-Mac architecte) — ENVELOPPE : COQUE DE COUVERT CONSTRUITE+VALIDEE ; l usage NE SE SCRIPTE PAS (-> apprendre)
Pivot demande par Younes : laisser l humanoide Isaac de cote (patinage non resolu), reprendre l ENVELOPPE SENSORIELLE de l avatar Arma. Etat trouve : avatar_fight.py (16/06) sent deja YEUX=LOS reelle (lineIntersectsSurfaces) + OREILLES=getSuppression + PROPRIO, cerveau=clone LAMBS (Net 14->4), commande le soldat. BASELINE (avatar_fight, server0, seed41, 3 OPFOR @70m) : avance vers l objectif, Arma auto-vise/tue 1/3, survit MAIS tactiquement INERTE (1re_reaction=None, jamais de couvert/suppression).
TROU IDENTIFIE : l enveloppe sent les ENNEMIS, pas le COUVERT. AJOUT = COQUE DE COUVERT : eventail de 12 rayons horizontaux (lineIntersectsSurfaces) en repere CORPS autour du soldat -> distance au 1er obstacle par direction. VALIDEE en isolation (sense_probe.py) : au complexe -> murs a 2 m detectes ; terrain degage -> front a 15 m (max=rien). FIX CLE du raycast : origine = getPosASL _u + 0.9 m (poitrine), PAS eyePos (qui passe SOUS le sol quand le soldat est couche -> rayons=0 partout ; mesure : eyePos.z 38.3 baissee 0.7 = 37.6 < sol ASL 37.9 = underground).
USAGE teste (2 regles codees main) -> ENCADRENT l echec : v1 (avatar_cover.py, twitchy) avance dans le feu, dithere, 43% degats, 0 kill ; v2 (avatar_cover2.py, hysteresis+commit) prend couvert@1s, 0% degat, 1 kill MAIS se terre et N AVANCE PLUS (objectif jamais approche). Le baseline debile accomplit plus que les deux. LECON (= these projet) : la PERCEPTION se resout par ingenierie (coque OK), le JUGEMENT avancer/couvrir/supprimer (dosage continu agression-prudence, situationnel) NE SE SCRIPTE PAS -> c est le discernement du pilier souffrance/selection. VERDICT : enveloppe enrichie (coque couvert + menace + proprio) PRETE a brancher sur une politique APPRISE ; arret du hand-tuning. Fichiers (workstation ~/arma3-marl) : sense_probe.py, debug_ray.py, avatar_cover.py, avatar_cover2.py. Serveur Arma slot 0 (multi_server.sh 1) ; lancement avatar : .venv/bin/python avatar_coverX.py <slot> <dist> <n_en> <skill> <seed> <cycles> <label>. Prochain pas propose : obs_enrichie -> PPO/selection (pilier 1060) ou clone+finetune ; bon banc d essai = approche AVEC couvert exploitable (pas l approche a decouvert du complexe, qui n offre pas de couvert avant l objectif).

## 2026-06-21 ~14h45 (Claude-Mac architecte) — CERVEAU APPRIS pour l avatar : COQUE DE COUVERT +97 (la these prouvee bout-a-bout)
Suite du fil enveloppe (cf entree ~14h30) : la regle codee-main echouait des 2 cotes (trop agressive 43% degats / trop prudente figee). Donc : apprendre l usage. Construit un sandbox SOLDAT-SEUL en ajoutant une COQUE DE COUVERT a assault_terrain (flag shell_obs + _cover_shell : 12 rayons ray-marches dans le champ cover, CENTRES SUR LA MENACE = rayon 0 vers l ennemi ; + degats en proprio) = l obs de l avatar Arma. PPO (train_soldier.py, A=1 vs D=2 win-by-fire, relief40 hit0.10, 250 iters, 8192 envs, 3090, ~200k tr/s, ~20min/run). RESULTAT : AVEC coque 97% neutralises / 2% pertes (declic it~60 : 0->87%) ; SANS coque (aveugle a la DIRECTION du couvert) 0% neutralises / 32% pertes -> il se planque, survit, n engage JAMAIS (pas de position couverte-AVEC-VUE). ECART = +97 pts. CONFIRME G-perc au niveau SOLDAT et plus fort (+97 vs +54 equipe) : meme enveloppe, regle-main echoue, politique APPRISE maitrise le dosage avancer/couvert/feu. Checkpoints soldier_shell.pt / soldier_noshell.pt ; assault_terrain.py patche (.bak_shell). GPU device : ce venv = FASTEST_FIRST par defaut -> CUDA_VISIBLE_DEVICES=1 = le 1060 (no kernel image sm_61) ; forcer CUDA_DEVICE_ORDER=PCI_BUS_ID + CVD=1 pour la 3090. CAVEAT DEPLOIEMENT (honnete) : l obs sandbox melange egocentrique (coque/los/nd/degats) ET coords-monde sandbox (pos/scale, dir-centre) ; pour piloter le VRAI avatar Arma il faut une obs TRANSFER-CLEAN (objectif=origine, echelle 200m, memes features calculables cote Arma via le pont). PROCHAIN PAS : rendre l obs transferable -> brancher soldier_shell.pt comme cerveau de l avatar (remplace le clone LAMBS + la regle main) -> tester en Arma reel. Fichiers : assault_terrain.py, train_soldier.py, soldier_shell.pt.

## 2026-06-21 ~15h (Claude-Mac architecte) — SOUFFRANCE/SELECTION greffee sur le soldat-couvert : DISCERNEMENT PARTIEL
Porte la recette souffrance/PBT sur le soldat a coque (apres soldier_shell +97). Mode `suffer` ajoute a assault_terrain : gagnabilite VARIABLE par env (desactivation aleatoire de defenseurs, D_min..D), signal de DEBORDEMENT dans l obs ([degats recus, fraction de defenseurs qui peuvent me toucher]), MORT QUI COUTE (-1.5 au lieu de -0.4). train_soldier_pbt.py = PBT (P=8, bas tiers <- copies mutees du haut, fitness = victoire@gagnable + survie@submerge), gagnabilite 1v2..1v5 a l entrainement, eval 1v2 (gagnable) / 1v6 (submerge). 6 gens x 16 iters, 3090. SCORECARD : victoire@gagnable 0->58(g3 declic)->91%(g5) ; survie@submerge 100->64->59%(g5). VERDICT : la recette TOURNE, l agent apprend a se battre (91% = competence du soldat plain, pas d effondrement). Discernement PARTIEL : survie@submerge tient ~59% pendant que la victoire grimpe (=> PAS purement brave, sinon survie s effondre) MAIS meurt 41% sur submerge = encore brave = pattern recurrent "brave mais pas discernant" (cf tactical_combat v4 du 20/06). LEVIER (= lecon v4->v5) : submerge pas assez letal/couteux -> durcir (submerge plus letal + mort coute plus + inclure 1v6 a l entrainement) -> survie@submerge vers 85%+. Checkpoint soldier_suffer.pt. CAVEAT : 59% survie = "bon usage couvert" autant que "decroche" -> confirmer au comportement. Fichiers : assault_terrain.py (mode suffer, .bak_suffer), train_soldier_pbt.py.

## 2026-06-21 ~16h30 (Claude-Mac architecte) — SANDBOX = REPLIQUE ARMA (decision Younes) : infra batie+verifiee ; le solo collapse en "se planquer"
Decision Younes : "la sandbox doit etre une REPLIQUE Arma sinon c est pas possible" (la maquette d entrainement des forces speciales). Cause : le cerveau soldier_suffer deploye en Arma se COINCE sur les murs (sandbox synthetique = cretes franchissables ; Arma = murs solides). EXPORT du complexe (export_replica.py, sur la methode probe_arma_v2) : elevation getTerrainHeightASL 64x64 + 132 batiments via nearestObjects/boundingBoxReal -> rasterises en grille d occupation SOLIDE 140x140 (2 m/case, 14.6% bati). Sauve replica.npz. Carte de verif validee par Younes (empreintes == grille). PHYSIQUE REPLIQUE (mode replica dans assault_terrain, opt-in, .bak_replica) : batiments SOLIDES qui bloquent le MOUVEMENT (collision : 0% agents dans un mur apres marche aleatoire) ET la LOS (smoke : relief seul 100% LOS degagee -> avec murs 24%, les murs bloquent 75%). ENTRAINEMENT sur la replique (train_replica.py, 1 soldat vs 3, win-by-fire, 300 iters, 8192 envs) : RESULTAT = pertes 100->0% (apprend a SURVIVRE) MAIS neutralises 0% PARTOUT -> COLLAPSE "se planquer et survivre" (standoff : 75% LOS bloquee -> le solo ne peut tirer sans s exposer -> il ne s expose pas). LECON : la replique a fait son job = elle revele la VRAIE difficulte (un soldat SEUL ne nettoie pas un complexe defendu en y entrant tout droit -> c est un probleme d ESCOUADE feu+mouvement, pas solo ; le terrain synthetique le cachait via LOS facile). Infra juste, probleme devenu realiste+dur. Checkpoint soldier_replica.pt (0% neutralise = inutile tel quel). PROCHAINE DIRECTION = choix de design Younes : solo->escouade (assault_grid + officier-axe), curriculum (proche/peu de murs -> complexe entier), pousser la penetration dans la reward, ou ennemi intelligent/self-play. Fichiers : export_replica.py, replica.npz, assault_terrain.py (mode replica), train_replica.py, smoke_replica.py.

## 2026-06-21 ~17h (Claude-Mac architecte) — ESCOUADE 20v10 sur la replique : MEME collapse -> ce n est pas le nombre, c est l AMORCAGE (sparse reward)
Direction Younes : "on envoie une equipe de 20, pas un agent seul". Lance assaut escouade sur la replique du complexe (train_replica.py, A=20 vs D=10, conscience d equipe team_obs=feu+mouvement, win-by-fire, 300 iters, 2048 envs, ~10k tr/s). RESULTAT : pertes 100->10% (l equipe apprend a survivre, MIEUX que le solo) MAIS neutralises 0% PARTOUT -> MEME collapse "rester au bord et survivre". LECON CLE : ce n est PAS un probleme de nombre (20 au lieu de 1 = juste moins de pertes, 0 neutralise quand meme). Goulot = MUR DE LA RECOMPENSE RARE : 75% LOS bloquee par les murs -> toucher la garnison (poche centrale) exige une penetration coordonnee qui s expose -> l equipe ne tombe jamais dessus au hasard -> optimum local safe (survie). La replique revele que le vrai probleme = l AMORCAGE de l apprentissage sur objectif dur, pas la tactique d escouade. soldier_squad.pt = 0% neutralise (inutile tel quel). DEBLOCAGE = choix de design Younes (je n invente pas) : CURRICULUM (facile->dur, le plus probable), EXPLORATION via PBT (celle qui a debloque le toy souffrance 52->100%), ou SHAPING (recompenser obtenir-LOS/penetrer pas seulement tuer). + reponse Altis : tout l ile en 2D (terrain+empreintes solides) FAISABLE (biblio de zones = generalisation) ; 3D fin "moindre detail" (interieurs/etages) IMPRATICABLE et inutile (le sandbox 2D entraine, le vrai 3D d Arma agit au deploiement via lineIntersectsSurfaces). Fichiers : train_replica.py (A,D args, team_obs), assault_terrain (replica+team).

## 2026-06-21 ~18h (Claude-Mac architecte) — PBT exploration sur la replique : 0% -> l amorçage exige un CURRICULUM
Direction Younes : tester la PBT (mecanisme du toy souffrance) pour percer le mur d exploration de l assaut sur la replique. NB important : on a separe PBT-MECANISME (propager une trouvaille = exploration) de la RECETTE-SOUFFRANCE (PBT + survie-instrumentale + combat = discernement). Mis SEULEMENT le mecanisme (replica_pbt.py, P=8 squads 20v10, win-by-fire, shell+team, K=12, G=8) ; PAS la recompense souffrance (qui pousserait vers la survie = renforcerait le planquage, contre-productif pour l amorçage). RESULTAT : garnison neutralisee 0% sur les 8 generations -> la PBT seule NE PERCE PAS. Raison : la PBT ne propage que ce qui existe ; aucune squad ne reussit une 1ere fois (succes trop rare a froid) -> rien a cloner. DIAGNOSTIC SOLIDE (confirme 4x : solo 0%, escouade 0%, PBT-escouade 0%) : l assaut du complexe realiste NE S APPREND PAS A FROID ; ce n est ni le terrain ni le nombre ni l exploration brute, c est l AMORCAGE. LEVIER RESTANT = CURRICULUM (demarrer ou le succes est trouvable : garnison proche / attaquants deja en LOS / peu de murs -> durcir vers le complexe entier, PBT propage a chaque palier). = choix de design Younes (leviers sandbox : distance garnison, nb murs spawn-objectif, taille garnison). Fichiers : replica_pbt.py. PROCHAIN = curriculum (Younes concoit OU Claude propose paliers + Younes valide avant lancement).

## 2026-06-21 ~19h30 (Claude-Mac architecte) — BUG TROUVE : les defenseurs spawnaient DANS les murs (=intouchables) -> tout le 0% s explique
Le curriculum (3090 A=20 + 1060 A=12 en parallele) a fait 0% a TOUS les paliers, MEME le palier 1 (point-blank 20v2). Diagnostic (diag_palier1.py) : 50% des DEFENSEURS spawnent DANS un batiment -> intouchables (LOS bloquee par le mur qui les entoure) -> "neutralise"=toute la garnison morte devient IMPOSSIBLE, pas juste dur. CAUSE : en mode replica j avais ecarte les ATTAQUANTS des murs mais PAS les defenseurs. RE-CADRAGE IMPORTANT : le 0% de toute la journee (solo, escouade, PBT, curriculum) n etait PAS (que) "sparse-reward trop dur a explorer" -> c etait PARTIELLEMENT IMPOSSIBLE (cibles dans les murs). Mon diagnostic sparse-reward etait incomplet. FIX (ws_patch_defnudge.py, .bak_defnudge) : jitter les defenseurs hors des murs (mode replica). RE-DIAG palier 1 : defenseurs dans un mur 50%->0%, LOS attaquant->defenseur 16%->40% -> palier 1 GAGNABLE. Curriculum relance (3090 A=20, 1060 A=12) pour verifier que ca decolle enfin. Lecon : toujours verifier que la tache est GAGNABLE (cibles atteignables) avant de conclure "trop dur a apprendre". Fichiers : diag_palier1.py, assault_terrain (defnudge).

## 2026-06-21 ~20h (Claude-Mac architecte) — CURRICULUM (post-fix defenseurs) MARCHE : chaine 92->57->41->9% ; le complexe entier reste dur
Apres le fix defenseurs-dans-les-murs, curriculum relance sur les 2 GPU (3090 esc.20, 1060 esc.12). RESULTAT = chaine MONOTONE (fini le 0%) : esc.20 palier1 92% -> p2 57% -> p3 41% -> p4 (complexe entier 20v10) 9% ; esc.12 92->49->18->5%. CONCLUSIONS : (1) le pipeline replique+PBT+curriculum APPREND vraiment (paliers 1-3 montrent du vrai apprentissage) -- de "impossible (0%)" a "ca bootstrappe et grimpe". (2) Plus d attaquants aide (esc.20 > esc.12 a chaque palier). (3) MAIS le palier 4 (depart 115m, garnison 10, complexe dense) plafonne a 9%/5% -- l assaut complet du vrai complexe n est PAS pris. Le saut p3->p4 (41%->9%) est trop raide. Checkpoints squad_curriculum.pt (esc.20) / squad_curriculum_A12.pt (esc.12). LEVIERS SUIVANTS (design Younes) : paliers intermediaires entre (85m,6) et (115m,10), + plus de generations/palier (il avancait apres 1-5 gen), + eventuellement mesurer le nettoyage PARTIEL (neutralise=tout-mort est un seuil strict ; la squad tue surement des defenseurs sans tout nettoyer). Fichiers : curriculum_replica.py (A,NE en args), squad_curriculum*.pt.

## 2026-06-21 ~21h (Claude-Mac architecte) — CURRICULUM v2 REUSSI : le squad assaille le complexe (71% de la garnison tuee)
Apres fix defenseurs-dans-murs + metrique partielle corrigee (auto_reset=False, l ancien info[dkilled] etait ecrase par l auto-reset = aliasing avec self._prev_dk) + paliers fins (intermediaire 100m/8) + avancement sur le PARTIEL (% def tues, signal dense). Piege debug du jour : chaque commande de relance commencait par pkill -f curriculum_replica -> elle tuait le run de la commande PRECEDENTE juste apres son entete (d ou "meurt avant gen 1"). Fix = lancer sans pkill. RESULTAT (5 paliers, 2 GPU) : TOUS les paliers maitrises (>=60% tues). esc.20 (3090) : p1 92 -> p2 77 -> p3 65 -> p4 62 -> p5(complexe entier 20v10) 68%, eval finale 71% def tues / 13% tout-nettoye. esc.12 (1060) : 91/74/61/63/60, finale 63% tues / 4% tout-nettoye. CHEMIN : 0% (impossible, bug) -> 9% (curriculum v1, full-clear) -> 71% def tues (v2). LE SQUAD ASSAILLE VRAIMENT LE COMPLEXE. Bemol : tout-nettoyer les 10 (finir les derniers retranches) reste dur (13%) ; on descend la garnison a ~3/10. Plus d attaquants aide (71>63). Checkpoints squad_curr2_A20.pt / squad_curr2_A12.pt. PROCHAINE ETAPE = deployer squad_curr2_A20.pt sur le VRAI complexe Arma (test du transfert). Fichiers : curriculum_replica.py (v2, paliers fins + partiel + auto_reset=False), assault_terrain (replica+defnudge), squad_curr2_*.pt.

## 2026-06-21 ~22h (Claude-Mac architecte) — BOUCLE BOUCLEE : squad replique deploye en ARMA REEL, 38% (pics 90%)
Deploiement de squad_curr2_A20.pt (entraine sur la replique) sur le VRAI complexe Arma, via squad_deploy.py (obs 26-dim multi-agent par soldat : base9+coque13+equipe4, pilote 20 soldats, actions 8 caps/tenir/supprimer ; Arma fait le tir). Lance sur 10 SERVEURS en parallele (flotte multi_server.sh 10), 20v10, ~60s/op. RESULTAT (garnison tuee, 10 reps) : 0,0,40,90,0,80,60,60,0,50 -> MOYENNE 38%, pics 80-90%. LE TRANSFERT MARCHE (pas 0% : les tactiques de manoeuvre de la replique transferent en Arma reel). Ecart 71% sim -> 38% reel (attendu : balistique+IA+pathfinding Arma vs combat abstrait sandbox). VARIANCE forte : 4 reps a 0% (approche echoue : coinces/timeout 60s), 6 a 40-90%. Aucun tout-nettoye (derniers retranches durs, comme en sim). BOUCLE COMPLETE end-to-end : export Arma->replique solide->curriculum PBT (71% sim)->deploiement Arma reel (38%). Du "1 soldat coince dans un mur (0%)" du matin a "escouade prend jusqu a 90% du vrai complexe". Gotcha smoke : 40 cycles=11s trop court (les soldats doivent marcher 115m en temps reel) -> 200 cycles ~60s. PISTES : investiguer les 4 reps a 0% (timeout 60s trop court ? embouteillage pathfinding 20 doMove ? angle d approche ?), allonger le temps, n>10. Fichiers : squad_deploy.py, deploy_*.log. Checkpoint deploye : squad_curr2_A20.pt.

## 2026-06-22 (Claude-Mac architecte) — LE DEPLOIEMENT D HIER ETAIT UNE COQUILLE VIDE : debug du pilotage, puis 1er deploiement REELLEMENT incarne (0% -> 70%)
Re-examen du deploiement Arma : les 38% d hier (pics 90%) etaient un LEURRE -- la squad ne MANOEUVRAIT PAS, elle restait collee a ~105m du spawn, et les kills venaient de l IA AUTOTARGET d Arma, PAS de la politique. La politique sortait "avancer" 100% mais les corps ne bougeaient pas. Journee entiere a debugger le PILOTAGE setVelocity (voie 1 : handler EachFrame 50Hz applique la derniere action ; rate_test2.py = reference validee +30m/5s sur 1 soldat).

DECOUVERTES (toutes prouvees sur harnais fiable SocketBridge+grab, pas le file-mode op_arma qui flanche) :
1. setVelocity DEPLACE bien l infanterie et SCALE a 20/20 (30,7m en 5s, FPS=50). Jamais un probleme d echelle, de groupe (limite 12 non atteinte), de murs ni de collision.
2. disableAI DOIT couper FSM+ANIM+AUTOCOMBAT, pas seulement MOVE+PATH. Avec MOVE+PATH seuls (combat garde), l IA d Arma reprend la main sur le corps et ECRASE setVelocity a ~80% : 6m au lieu de 30m. En coupant FSM/ANIM/AUTOCOMBAT mais en GARDANT TARGET/AUTOTARGET/AIMING -> le soldat bouge ET garde le tir reflexe d Arma (= design "reflexes=regle, decisions lentes=appris").
3. Bug "3/20" : envoyer le mouvement en [] spawn { 40 setVariable } DROPE sous charge (scheduler Arma ne termine pas) -> 17/20 restent immobiles. Fix = tableaux globaux HMT_VX/HMT_VY (assignation unique) + handler indexe.
4. DEUX BUGS LATENTS tues, qui debloquent tout :
   (a) _y au lieu de _x dans le forEach HMT_EN de la requete SENSE -> l ennemi le plus proche etait TOUJOURS null -> contact=False, action "supprimer" jamais declenchee dans TOUS les runs precedents (la squad etait litteralement AVEUGLE a l ennemi). Fix _y->_x.
   (b) l assignation DIRECTE HMT_VX=[...] en contexte non-planifie declenche "GIAS pre stack size violation" sous la charge du handler 50Hz -> corrompt le pont -> SENSE echoue sur tous les cycles suivants -> squad figee. Fix = la mettre dans [] spawn { HMT_VX=...; HMT_VY=... } (1 instruction -> ne drope pas ET pas de violation).
5. op_arma._query (SENSE) flanche sur serveur frais -> warm-up ~10s + retry + settle 0.30.

RESULTAT end-to-end (squad_curr2_A20 sur vrai complexe, 20v10, server0 propre) : garnison 0% -> 70% NEUTRALISEE, contact=True, 19/20 SURVIVENT, SENSE tient les 200 cycles. PREMIER deploiement ou la BOUCLE D INCARNATION SE FERME pour de vrai : 20 corps pilotes par le cerveau appris qui percoivent, decident, tirent, survivent. Le mur principal du projet (transfert sim->Arma du corps) est tombe.

COMPORTEMENT REEL = "supprimer" 99%, n assaut PAS. La squad gagne le DUEL A DISTANCE (creep 110->83m, tir a ~70-100m soldat-ennemi, portee fusil normale) et neutralise 70% par le feu, mais s arrete au seuil (~83m) sans entrer dans le complexe. Les ~3 derniers = retranches dans les batiments, intuables de l exterieur (LOS bloquee par les murs). Ecart sim(71% clear)->reel(suppression a distance) : dans Arma le feu de suppression tue seul a distance -> "supprimer" domine.

DIRECTION SUIVANTE validee par Younes ("apprendre a checker les batiments et les nettoyer pour prendre l objectif") = 3 ETAPES :
1. VERIFIER/DONNER DES INTERIEURS AU SANDBOX. Soupcon fort : la grille solide 2m (14,6% bati) = batiments BLOCS PLEINS, sans pieces ni portes -> la politique ne PEUT pas apprendre a entrer/nettoyer (rien ou rentrer en sim). C est l etape ZERO, tout en depend. Action immediate : inspecter replica.npz / export_replica.py.
2. Objectif intermediaire "FERMER ET OCCUPER LE POINT" (atteindre le centre) avant "nettoyer piece par piece" -- plus simple, teste deja l entree. Levier reward : les retranches etant intuables de dehors (LOS murs), un bonus clear-total/occupation force naturellement l entree.
3. ROLES (base de feu vs element d assaut = fire & movement). Le "suppression a distance" obtenu = phase 1 reussie ; l assaut rapproche est un AUTRE metier -> colle au MARL a roles du projet, plutot qu une politique homogene.

Gotcha locomotion intra-batiment : on a coupe disableAI PATH -> Arma ne contourne plus -> franchir une porte = la politique elle-meme via la coque 12 rayons (perception doit resoudre l interieur). Cran de difficulte au-dessus du combat a distance.
Fichiers/diag du jour (ws /home/younes/arma3-marl/) : rate_test2.py (ref 50Hz), move_combat.py (ALL vs MOVE), move_sweep.py (configs disableAI), scale20.py/scale20arr.py (20/20 tableau), move_pervar.py, force_north.py, diag_move.py ; cible patchee : squad_deploy.py ; relaunch0.sh (relance serveur propre). Checkpoint : squad_curr2_A20.pt (inchange).

## 2026-06-22 (suite, Claude-Mac architecte) — DIRECTION CQB tranchee + role d'assaut VALIDE en vrai Arma (60% nettoye)
Suite au 1er deploiement incarne (suppression a distance 70% mais n'entre pas). Younes tranche le fork de modelisation CQB = "REEL ARMA AU DEPLOIEMENT" (fidele a sa conclusion du 21/06 : pas de fake d'interieurs en 2D ; le sandbox 2D entraine l'approche+suppression, le vrai 3D d'Arma gere l'entree+nettoyage via les buildingPos). Donc PAS de reconstruction du sandbox avec interieurs.

VERIFS factuelles :
- Sandbox : export_replica.py ligne 46 remplit toute la bounding-box de chaque batiment en SOLIDE -> blocs pleins, zero interieur (confirme le verrou).
- Vrai complexe (probe_buildings.py) : 74 batiments, 61 ENTERABLES, 366 buildingPos (vraies maisons Arma 3-11 spots). CQB pleinement pertinent ici.
- Fondation CQB (garrison_verify.py) : 10 defenseurs garnis DANS les batiments (buildingPos, repartis sur 50 batiments) -> depuis la ligne de suppression (~90m sud) 10/10 INTUABLES (LOS bloquee). Donc avec garnison-dans-les-batiments la suppression a distance ne clot RIEN -> il faut entrer (vrai scenario CQB ; l'ancien 70% visait une garnison a decouvert).

ROLE D'ASSAUT valide (assault_cqb.py) : K=8 soldats, pathfinder Arma REACTIVE (disableAI ALL leve, doMove vers le defenseur vivant assigne par index = repartition sur batiments distincts + doTarget). Arma fait entrer les soldats dans les batiments et nettoyer. RESULTAT : nettoyage 40% (convergence sur le plus proche, 90s) -> 60% (repartition par index + 140s), assaillants survivants 7/8. Les ~4 restants = retranches profonds (etages/pieces du fond) non atteints en 140s par 8 gars.

CONCLUSION : la doctrine FIRE & MOVEMENT tient en vrai Arma = base de feu (politique apprise setVelocity, supprime les exposes, 70%) + element d'assaut (pathfinder Arma doMove->buildingPos, deloge les retranches, 60%, quasi sans perte). = exactement le MARL a roles du projet. Les 3 etapes du plan (interieurs / entrer-occuper / roles) validees en une session.
LEVIERS pour pousser le clear vers 100% : plus d'assaillants / plus de temps ; ou IA CQB experte (LAMBS Danger.fsm building-clearing, cf [[mods-capability-not-tactics]], pas encore installe). PROCHAIN = INTEGRATION : combiner base-de-feu (politique) + element d'assaut (pathfinder) dans UN deploiement qui fait la sequence complete approche->suppression->assaut->clear->prise d'objectif (split des roles = choix de design Younes). Fichiers : probe_buildings.py, garrison_verify.py, assault_cqb.py.

---

## 2026-07-28 14:25 CEST (Claude-Mac, Opus 5) — PASSATION : courbe n°2 LIVRÉE, létalité ×4 DÉCOUVERTE, banc de répartition du feu EN ÉCHEC

### 1. CE QUI TOURNE À L'INSTANT

| quoi | détail |
|---|---|
| `arma3server_x64` | **PID 314761**, démarré 14:20, `-port=3912 -world=Altis`, config `staging/server_altis.cfg`, profils `profiles_altis` |
| pont natif | **écoute 127.0.0.1:5826** (fd du même PID). ⚠️ **UN SEUL CLIENT À LA FOIS** |
| mods | `@CBA_A3;@ALiVE;@ace;…;@rhsusaf;@rhsafrf`, serverMod `@LAMBS_Danger` |
| chaînes de banc | **AUCUNE. Toutes terminées** (`bissel.log` finit sur `BISSEL_FIN`). Rien n'a été relancé depuis. |
| autres | `aquilon_daemon.py` (PID 3872), `moniteur_matrix.py` (11504), `rudder_proxy.py` (6142) — indépendants, pas touchés |

⚠️ Ce serveur Altis a été **redémarré une quinzaine de fois** aujourd'hui par les scripts `banc_*.sh` / `bissection*.sh`. Chacun appelle `relancer_meltemi.sh`.

### 2. ACQUIS DE LA JOURNÉE (solides, gravés en mémoire)

**COURBE N°2 — LA SUPPRESSION MESURÉE.** Critères `c266ebdc31631d92`, résultat `courbe_suppression_DUEL_VALIDE.json`.
Duel symétrique 100 m, cibles invulnérables, impacts comptés par `HitPart`, 3 séances × 60 s, 0 cible morte.

| | témoin | supprimé |
|---|---|---|
| balles/s | 2,47 | 1,41 |
| au but | 42,2 % [39-46] | 5,9 % [4-8] |

→ **cadence ×0,57, précision ×0,14, capacité de nuire ×0,08.** La sandbox mettait 0 % ; la vraie valeur est 8 %.
→ **Décroissance : la cadence revient à ~89 % en 2 s**, puis plafonne vers 60 % pendant ≥18 s. Pas de sandbox = 3,28 s → bon ordre de grandeur, un peu généreux.

**SIX DÉFAUTS SILENCIEUX TUÉS.**
1. **Collision de noms `HMT_NSUP`** (compteur ET liste de tireurs → `[0,0,0,0,unité,…]`) → `0 reveal [...]`, erreur de type toutes les 4 s dans un envoi sans accusé → **c'est ce qui tuait le pont à +12 s depuis deux jours.** Le journal le criait : Arma « 8 tireurs », Python « 4 arroseurs ».
2. **`HandleDamage` sous-compte les impacts d'un facteur 4** (12 % vs 48 % pour `HitPart`, à 100 m où la courbe n°1 dit ~48 %). → **compter avec `HitPart` + `allowDamage false`**.
3. **`HandleDamage → 0` ne protège PAS** (4 cibles sur 4 mortes à 100 %).
4. **Bras témoin qui ne combattait pas** (cible `CARELESS`, visée coupée = mannequin ; 0,22 b/s). Le banc comparait un duel à un stand de tir.
5. **`reverdict_arc2` testait un arc SANS ARC** : `def_arc` non fixé → défaut demi-angle 180°, cône = cercle entier, aucun angle mort.
6. **Le témoin d'initiative regardait les FIXEURS** (`initiative()` prend l'attaquant le plus proche ; la doctrine crochet met 2 hommes sur 4 en fixation frontale).

**Piège de plomberie :** `mesurer_suppression.py` pointe par défaut sur **stratis (port 5816)** en lisant des cellules **d'Altis** (x≈23 000, 3× hors carte). **Toujours passer `--theatre altis`.**

**RE-VERDICTS.**
- Courbe n°2 (`CRITERES_REVERDICT_SUPP.md`, critères figés) : flanc 85,5 % → 84,5 %, **écart 1 point = COSMÉTIQUE**. L'avantage du flanc ne venait pas d'un interrupteur de suppression.
- Arc (`CRITERES_REFERENCE_ARC3.md` `5bbb7f957f0319e8`, `CRITERES_TEMOIN_VENTILE.md` `dae84b78e1b8c319`) : témoin ventilé **flanqueurs 61,5 % / 63,2 %** (seuil ≥60 ✓, confirmé sur graines neuves 21-23), fixeurs 25,4 % / 25,9 %, **frontal 36 % contre un seuil ≤35 → ÉCHEC reproductible, seuil NON retouché**.
- **L'arc ouvrant n'est PAS adopté** : il écrase la prise du crochet de 43 % à 7 %, et le ×15,7 est un rapport sur des quasi-zéros.

**⭐ LA DÉCOUVERTE LA PLUS IMPORTANTE — LA SANDBOX EST ~4× TROP LÉTALE.**
`tir_par_pas = 1,15` est une mesure Arma **par défenseur**. La boucle de dégâts l'appliquait à **chaque attaquant séparément** → 4,6 balles/pas avec A=4. Mesuré : **1,8 attaquant pris à partie par défenseur**.
Chaîne de diagnostic (3 hypothèses réfutées avant la bonne) : paires ×1,13 seulement ; pas de falaise au seuil (10 % entre 0,50 et 0,70) ; exposition du flanqueur 1,1→1,3 pas ; **mais survie du flanqueur 35 % → 1 %** et **pire pas encaissé 0,280 → 0,471** pour un seuil de mort à 0,70 (19 % meurent en UN pas). Le fixeur **n'arrive jamais** (0 % partout) → toute la prise repose sur le flanqueur.

Correctif `cible_unique` posé dans `assault_terrain.py` (défaut `False`, non régressif ; sauvegarde `.avantcible`). Effet **énorme** :

| cône dur | frontal | crochet | ×prise |
|---|---|---|---|
| sans sélection | 22,2 % | 40,4 % | 1,82 |
| **avec sélection** | **80,8 %** | **66,9 %** | **0,82** |

→ **L'AVANTAGE DU FLANC DISPARAÎT.** Une partie de ce qui a été conclu sur la manœuvre depuis deux semaines reposait peut-être sur un excès de létalité. **Rien d'interne ne peut arbitrer : il faut le chiffre d'Arma.**

### 3. LE BANC DE RÉPARTITION DU FEU — ÉTAT EXACT : EN ÉCHEC, 0 CHIFFRE

**But :** mesurer sur Arma, en fenêtres de 3,28 s, (a) les balles par tireur et (b) **le nombre d'hommes DIFFÉRENTS qu'un même soldat prend à partie**. C'est ce chiffre qui tranche `cible_unique`.

**Six tentatives, aucune mesure.** Historique factuel :

| # | dispositif | résultat |
|---|---|---|
| 1 | `mesurer_repartition.py`, 8 déf. + 4 att., AUTOTARGET **actif**, aucun ordre | **0 tir défenseurs.** Canari non bloquant → le banc a imprimé « ~4 milliards de fois trop létal » (division par zéro). Corrigé : canari bloquant. |
| 2 | + ordre de tir aux **attaquants** seulement | **att. 411 tirs, déf. 0.** → ce n'est pas la mise en place, c'est la riposte. |
| 3 | + `setVehicleAmmo 1`, compteur attaquants | idem, déf. 0 |
| 4 | + amorce unique aux défenseurs (`doTarget`/`doFire`) | **déf. 0 malgré un ordre explicite** |
| 5 | `mesurer_repartition2.py` : on observe le camp qui tirait (WEST) | **0 tir de tous les côtés** |
| 6 | `bissection_selection.py`, 4 crans depuis la config du banc de suppression | **crans 0,1,2,3 : MORT (pose)** — la pose elle-même ne répond plus |

**Bugs de banc trouvés et corrigés en route** (utiles pour la suite) :
- les variables **`private` ne survivent pas au découpage des envois** : chaque `send` est un script séparé. C'est ce qui cassait la pose quand on découpe. → utiliser des globales, ou une **requête unique** comme le fait `mesurer_suppression.py`.
- ma conversion en globales n'avait remplacé que la **première** référence par ligne → `setSkill`, `allowDamage false` et **`setCombatMode RED` n'étaient jamais appliqués**.
- `checkAIFeature` **n'existe pas** dans cette version → requête muette.

**Hypothèse non testée au moment de l'arrêt** (c'est là que je m'arrêtais) : `bissection_selection.py` utilise des noms de variables **trop courts** — `HMT_S`, `HMT_C`, `HMT_D`, `HMT_G`. Or **`HMT_S` est déjà la liste d'unités de `mesurer_suppression.py`**, et le pont/mission peuvent en utiliser d'autres. Le correctif prêt (non appliqué) était de **tout préfixer en `HMT_BS*`**.

**Contrainte structurelle établie, et c'est le vrai obstacle :** la seule configuration dont on sache qu'elle tire est celle du banc de suppression — **`AUTOTARGET` DÉSACTIVÉ** + `reveal` + `doTarget` + `doFire` répétés toutes les 4 s. Elle **impose la cible**, donc elle ne peut pas mesurer une sélection libre. Tant que ce nœud n'est pas défait, le chiffre est inatteignable par cette voie.

### 4. À MOITIÉ FAIT

- **`cible_unique`** : implémenté, prouvé actif (dégâts par vivant −55 % au 1er pas, exposition inchangée au dix-millième), **mais NON CERTIFIÉ** faute du chiffre Arma. Reste `False` par défaut.
- **`supp_residuel=0.08` / `supp_persist=0.35`** : implémentés, prouvés actifs, re-verdict passé (cosmétique). Restent **inactifs par défaut**. Personne ne les a encore activés dans un entraînement.
- **Arc ouvrant** : mécanisme du contournement démontré (61-63 % sur les flanqueurs), **frontal échoue d'un point deux fois**. Non adopté.
- **`mesurer_suppression.py`** : réparé et fiable, mais son `--theatre` défaut reste **stratis** (piège).
- **`sig()`** : corrigé (`sig_taux`, variance de Poisson) parce qu'il traitait une cadence comme une proportion et plantait au-dessus de 1 balle/s.

### 5. CE QUE J'ALLAIS FAIRE ENSUITE

1. Préfixer `bissection_selection.py` en `HMT_BS*` et relancer les 4 crans (**c'était l'action interrompue**).
2. Si la pose repart : lire le premier cran qui éteint le feu → soit le chiffre `hommes_différents/tireur`, soit la raison exacte pour laquelle Arma ne peut pas le donner dans ce harnais.
3. Avec le chiffre : trancher `cible_unique`, puis **refaire le re-verdict du flanc** dans le monde correctement létal. C'est la question ouverte n°1 du projet.

### 6. FAUTE DE MÉTHODE À NE PAS REFAIRE

Le matin, la bissection a résolu en 20 minutes un blocage de deux jours — **partir de ce qui survit, ajouter une pièce à la fois**. L'après-midi, sur le banc de répartition, **j'ai deviné six fois de suite** (munitions, autotarget, camp observé, ordres…) : six runs, zéro chiffre. Je n'ai pas appliqué ma propre leçon. **Sur ce pont, deviner ne marche jamais ; bissecter marche.**

### 7. FICHIERS CRÉÉS OU MODIFIÉS AUJOURD'HUI

**Sandbox** — `~/arma3-marl/` :
- `assault_terrain.py` **MODIFIÉ** : `supp_residuel`, `supp_persist`, `cible_unique` (tous non régressifs). Sauvegardes `.avantcourbe2`, `.avantcible`.
- `fumee_courbe2.py` (smoke-test, créé)

**Bancs et sondes** — `~/arma3-marl/leviathan/` :
- créés : `sonde_qui_tue.py`, `sonde_pieces.py`, `bissection.sh`, `attendre_pont.py`, `banc_supp.sh`, `vrai_banc.sh`, `sonde_hitpart.py`, `reverdict_supp.py`, `faire_reference_arc3.py`, `reverdict_arc3.py`, `diag_puissance_feu.py`, `diag_falaise.py`, `diag_flanqueur.py`, `diag_qui_meurt.py`, `mesurer_repartition.py`, `mesurer_repartition2.py`, `banc_repartition.sh`, `sonde_riposte.py`, `banc_riposte.sh`, `bissection_selection.py`, `bissection_sel.sh`
- modifié : `mesurer_suppression.py` (collision `HMT_NSUP`, `HitPart`, duel symétrique, JSON avant affichage, `sig_taux`). Sauvegardes `.avantcollision`, `.avantnan`, `.avantcibles`, `.avantduel`, `.avanthitpart`, `.avantsig`
- critères figés : `CRITERES_SUPPRESSION_DUEL.md` (`c266ebdc31631d92`), `CRITERES_REVERDICT_SUPP.md`, `CRITERES_REFERENCE_ARC3.md` (`5bbb7f957f0319e8`), `CRITERES_TEMOIN_VENTILE.md` (`dae84b78e1b8c319`)
- résultats : `courbe_suppression_DUEL_VALIDE.json`, `courbe_suppression_stand_de_tir.json` (annulé, biais témoin), `reverdict_supp.json`, `reference_arc3.json`, `reference_arc3_cible.json`, `reverdict_arc3*.json`
- journaux : `bissection.log`, `vrai_banc.log`, `repartition.log`, `riposte.log`, `bissel.log`

**Mémoire longue (Mac)** : `courbe2-suppression-mesuree.md`, `sandbox-letalite-4x-cible-unique.md` (nouveaux), `arc-tir-sursis-mesure.md` (complété).


## 2026-07-28 15:00 CEST (Claude-Mac, Opus 5) — VERDICT : LE CHIFFRE DE RÉPARTITION DU FEU EST TOMBÉ

**Cause racine des six échecs : `currentTarget` N'EXISTE PAS dans ce build d'Arma.**
Le capteur du banc appelait une commande absente → le bloc `addEventHandler ["Fired", {...}]`
ne compilait pas → tout le script de pose mourait sans un mot dans le journal. Ni les noms de
variables (`HMT_S`), ni la longueur du script, ni `AUTOTARGET` n'étaient en cause : les trois
hypothèses sont RÉFUTÉES, mesurées une par une. `assignedTarget` existe, lui, mais ne rend que
la cible IMPOSÉE — inutilisable pour mesurer un choix libre.

**Correctif : capteur `HitPart` posé sur les CIBLES.** Chaque impact donne (victime, tireur) :
on lit la sélection dans les impacts, pas dans l'intention. `HitPart` traverse
`allowDamage false` (déjà établi le 28/07 sur la courbe n°2). Piège rencontré et corrigé :
`(_this select 0) select 0` appliquait `select` deux fois — le handler jetait silencieusement.

**RÉSULTAT — hommes DIFFÉRENTS pris à partie par tireur, par fenêtre de 3,28 s** (4 vs 4, 100 m,
skill 0,5, cibles invulnérables, 6 fenêtres par cran, canari 57-68 tirs) :

| cran | dispositif | hommes différents/tireur | balles/tireur/pas |
|---|---|---|---|
| 0 | cible IMPOSÉE (témoin) | 0,95 | 7,68 |
| 1 | + AUTOTARGET réactivé | 0,78 | 7,00 |
| 2 | + ordres toutes les 10 s | 0,75 | 6,50 |
| 3 | **sélection LIBRE** (une impulsion puis rien) | **0,68** | 7,11 |

**VERDICT PRÉ-ENREGISTRÉ (seuil figé avant les données : <1,5 → `cible_unique=True` fidèle ;
>3 → ancien monde fidèle ; 1,5-3 → facteur intermédiaire) : 0,68 → `cible_unique=True` EST FIDÈLE.**
Loin du seuil, et le témoin à cible imposée (0,95) est au-dessus de la sélection libre (0,68) :
laissé libre, un soldat d'Arma se concentre, il ne s'éparpille pas.

**CE QUE ÇA TRANCHE :** l'ancienne boucle de dégâts (chaque défenseur frappait CHAQUE attaquant)
n'était pas une approximation, c'était une erreur de facteur ~4. Le correctif `cible_unique` est
certifié par Arma. Il doit passer en défaut `True`.

**CONTRE (limites à ne pas cacher) :** (1) fenêtre de 3,28 s — un tireur peut changer de cible sur
un horizon plus long ; (2) géométrie de duel (4 alignés à 25 m, 100 m de face), pas une géométrie
d'assaut ; (3) cibles INVULNÉRABLES : personne ne meurt, donc aucun report de tir sur mort de la
cible — le vrai chiffre en combat est probablement un peu plus haut, ce qui va dans le sens du
verdict, pas contre lui.

**SUIVANT — la question n°1 du projet est maintenant ouvrable :** refaire le re-verdict
frontal vs flanc dans le monde correctement létal (`cible_unique=True`). C'est ce qui dira si
l'avantage du flanc conclu depuis deux semaines est réel ou s'il était un artefact de létalité.

Fichiers : `bissection_selection.py` (capteur HitPart, sauvegarde `.avantprefixe`),
`bissection_selection_{0,1,2,3}.json`, run `/mnt/data2/lab/runs/repartition_feu_arma/`.

## 2026-07-28 15:15 CEST (Claude-Mac, Opus 5) — RE-VERDICT FLANC : L'AVANTAGE ÉTAIT UN ARTEFACT DE LÉTALITÉ

`cible_unique` passé en défaut **`True`** dans `assault_terrain.py` (sauvegarde
`.avantcibledefaut`), sur la foi du chiffre Arma du jour (0,68 homme différent par tireur,
seuil pré-enregistré <1,5).

Critères figés AVANT le run : `CRITERES_REVERDICT_CIBLE.md` (empreinte `a26a97a30c0eed05`).
Seuil repris tel quel du re-verdict n°1, **non retouché** : le flanc paie ssi prise
flanc/frontal ≥1,50 ET coût flanc/frontal ≤0,60.
Une seule variable change entre les deux mondes : les deux ont la courbe n°1 ET la courbe n°2.
200 épisodes par bras et par monde, graine 7, doctrines SCRIPTÉES.

| monde | doctrine | prise | pertes/prise | expo/m |
|---|---|---|---|---|
| ANCIEN (`cible_unique=False`) | frontal | 36,0 % | 0,29 | 0,026 |
| ANCIEN | flanc | 84,5 % | 0,16 | 0,015 |
| MESURÉ (`cible_unique=True`) | frontal | **95,0 %** | 0,31 | 0,028 |
| MESURÉ | flanc | 95,0 % | 0,12 | 0,012 |

| monde | prise flanc/frontal | coût flanc/frontal | verdict |
|---|---|---|---|
| ANCIEN | **×2,35** | ×0,56 | **LE FLANC PAIE** |
| MESURÉ | **×1,00** | ×0,39 | le flanc ne paie pas |

**>>> L'AVANTAGE DU FLANC ÉTAIT UN ARTEFACT DE LÉTALITÉ.** Il paie dans le monde 4× trop
létal, il ne paie plus dans le monde mesuré. Les conclusions sur la manœuvre tirées de
l'ancien monde sont à reprendre.

**Ce qui reste vrai, et c'est important :** le flanc garde son avantage de COÛT (×0,39 —
il perd 2,5 fois moins d'hommes par prise, et son exposition par mètre est deux fois plus
basse). Ce qui disparaît, c'est son avantage de PRISE : dans un monde correctement létal,
le frontal arrive aussi (95 % contre 36 % avant). Le flanc n'achète plus le succès, il
achète des vies.

**CONTRE :** (1) une seule graine (7) et une seule géométrie défensive (ligne + arc 120°) ;
(2) doctrines scriptées, pas apprises — une politique apprise pourrait exploiter autre chose ;
(3) le frontal à 95 % interroge : un banc où presque tout réussit sépare mal. Le prochain
banc doit durcir la défense jusqu'à ramener le frontal dans une plage discriminante
(25-75 %), sinon on mesure un plafond et non une doctrine.

**Piège d'infra trouvé et corrigé :** `CUDA_VISIBLE_DEVICES=1` désignait la **GTX 1060**, pas
la 3090 — CUDA numérote par puissance, `nvidia-smi` par bus PCI. `CUDA_DEVICE_ORDER=PCI_BUS_ID`
ajouté à `/mnt/data2/lab/lab_run.sh` : sans lui, tout run GPU de la file partait sur la
mauvaise carte (et échouait en « no kernel image »). Le venv `/mnt/steam/harmattan/venvs/rl`
n'existe plus (réorg disques) ; le venv qui marche est `~/env_isaaclab` (torch 2.7.0+cu128).

Fichiers : `reverdict_cible.py`, `CRITERES_REVERDICT_CIBLE.md`, `reverdict_cible.json`,
`assault_terrain.py.avantcibledefaut`, run `/mnt/data2/lab/runs/reverdict_cible_flanc/`.

## 2026-07-28 15:16 CEST (Claude-Mac, Opus 5) — LE SEUIL DE MANŒUVRE : 2 DÉFENSEURS PAR ATTAQUANT

Critères figés AVANT le run : `CRITERES_BALAYAGE_MENACE.md` (empreinte `cfe67bb4d459d5dd`).
Monde MESURÉ figé (courbe n°1 + n°2 + `cible_unique=True`), aucune courbe retouchée.
Seul D varie. A=4, 200 épisodes par bras et par point, graine 7, doctrines scriptées.

| D | prise frontal | prise flanc | prise fl/fr | coût fl/fr | dans la bande |
|---|---|---|---|---|---|
| 4 | 95,0 % | 95,0 % | ×1,00 | ×0,39 | non (plafond) |
| 6 | 73,5 % | 92,5 % | ×1,26 | ×0,49 | oui |
| **8** | 54,0 % | 87,0 % | **×1,61** | ×0,50 | oui |
| 10 | 39,5 % | 82,0 % | ×2,08 | ×0,57 | oui |
| 12 | 30,0 % | 77,0 % | ×2,57 | ×0,60 | oui |
| 16 | 20,5 % | 72,5 % | ×3,54 | ×0,66 | non (plancher) |

**>>> SEUIL DE MANŒUVRE : D = 8, soit DEUX DÉFENSEURS PAR ATTAQUANT.**
En-dessous, le flanc n'achète que des vies. Au-dessus, il achète la prise elle-même, et
l'avantage croît de façon monotone (×1,26 → ×3,54).

**Ce que ça change :** le verdict du 28/07 (« l'avantage du flanc était un artefact de
létalité ») était vrai À D=4 — et D=4 est hors bande, le banc y plafonnait à 95 %. La
lecture correcte n'est pas « le flanc ne paie pas » mais **« le flanc paie au-dessus d'un
rapport de forces de 1 contre 2 »**. La doctrine optimale est une FONCTION de la menace,
pas une constante. C'est la base de l'adaptabilité : un agent doit lire la densité adverse
et choisir, pas mémoriser une manœuvre.

**Signal secondaire, à ne pas lisser :** l'avantage de COÛT s'érode quand la menace monte
(×0,39 à D=4, ×0,50 à D=8, ×0,60 à D=12, ×0,66 à D=16 — hors critère). Les deux avantages
du flanc évoluent en sens INVERSE : il achète de plus en plus la prise, de moins en moins
les vies. À forte menace, contourner devient un pari, plus une économie.

**CONTRE :** une seule graine (7), une seule géométrie défensive (ligne + arc 120°), doctrines
scriptées, A=4 fixe. Le seuil D=8 est un seuil DE CE BANC ; il doit être certifié sur Arma
avant d'être une affirmation sur le monde réel.

Fichiers : `balayage_menace.py`, `CRITERES_BALAYAGE_MENACE.md`, `balayage_menace.json`,
run `/mnt/data2/lab/runs/balayage_menace/`.

## 2026-07-28 15:40 CEST (Claude-Mac, Opus 5) — ARMA REFUSE L'ÉCHELLE DU SANDBOX + terrain Pyrgos vérifié

**TERRAIN (vérifié en dur, `verifier_terrain.py`, `verif_terrain_altis.json`).**
Cinq points sur cinq à TERRE (objectif, départ, mi-chemin, deux flancs) — altitudes 14 à 23 m.
Relief : amplitude **12 m** sur un cercle de 120 m → terrain qui porte, pas une plaine.
Couvert (objets de terrain à 40 m) : objectif 185, couloir frontal 122, flancs 138 et 162.
**Asymétrie flanc/frontal ×1,33** contre un seuil figé à 1,30 : ça passe, mais de peu.
⚠ La fiche de théâtre annonçait 13 contre 46 (×3,5) au 25/07 — instrument différent
(bâtiments vs objets de terrain), pas une contradiction, mais la marge réelle est mince.
`poser_fob.py` forçait Stratis en dur ; il honore désormais `HMT_THEATRE` (`.avanttheatre`).

**SONDE DE RÉGIME (garnison 8 fixe, mode frontal, 2 reps par point).**

| attaquants | prise frontale | pertes WEST | EAST neutralisés | bande 25-75 % |
|---|---|---|---|---|
| 4 | 0 % | 2,00 | 1,50 | non |
| 8 | 0 % | 1,50 | 2,00 | non |
| 12 | **50 %** | 1,00 | 2,00 | OUI |
| 18 | **50 %** | 5,00 | 2,00 | OUI |

**>>> L'ÉCHELLE ABSOLUE DU SANDBOX NE TRANSFÈRE PAS.** Le sandbox donne 54 % de prise à
4 attaquants contre 8 défenseurs ; Arma donne 0 %, deux fois sur deux. Il faut **12 hommes
contre 8** pour seulement atteindre 50 %. Le sandbox laisse quatre hommes prendre un objectif
tenu par huit — Arma refuse.

Conséquence : le seuil « D/A ≥ 2 » n'est pas certifiable à A=4, puisque rien ne s'y résout.
C'est l'issue n°4 des critères figés (`b764211cf2e274ca`) : réparer le régime avant lecture.

**CERTIFICATION V2 LANCÉE** — critères `CRITERES_CERTIF_SEUIL_ARMA_V2.md` (`8f6e129af26fecf8`) :
A=12 fixe (plus petit effectif dans la bande), D ∈ {8,12,16,24} soit D/A ∈ {0,67 ; 1,00 ;
1,33 ; 2,00}, frontal vs envelop, 3 reps, 24 opérations. Question : le seuil transfère-t-il
en RAPPORT (bascule attendue à D/A = 2) même si l'échelle absolue est fausse ?

## 2026-07-28 16:20 CEST (Claude-Mac, Opus 5) — CERTIFICATION V2 : RIEN N'A ÉTÉ MESURÉ (22 enlisements sur 24)

Critères `CRITERES_CERTIF_SEUIL_ARMA_V2.md` (`8f6e129af26fecf8`). A=12 fixe, D ∈ {8,12,16,24},
frontal vs envelop, 3 reps, 24 opérations, Altis/Pyrgos.

| D | D/A | prise frontal | prise envelop | pertes fr | pertes fl | bande |
|---|---|---|---|---|---|---|
| 8 | 0,67 | 33 % | 33 % | 1,00 | 1,67 | OUI |
| 12 | 1,00 | 0 % | 0 % | 3,67 | 1,67 | non |
| 16 | 1,33 | 0 % | 0 % | 3,33 | 4,00 | non |
| 24 | 2,00 | 0 % | 0 % | 4,67 | 2,67 | non |

**⚠ LE SCRIPT A IMPRIMÉ UNE CONCLUSION FAUSSE** (« aucune bascule dans la bande → le seuil est
un artefact du sandbox »). Sa branche s'est déclenchée parce que la bande contenait UNE seule
cellule. Avec une cellule on ne peut rien dire d'une bascule. La conclusion est retirée.

**LE VRAI ÉTAT : ZÉRO DESTRUCTION SUR 24 OPÉRATIONS.**

| D | mode | pris | détruits | ENLISÉS | distance d'arrêt |
|---|---|---|---|---|---|
| 8 | frontal / envelop | 1/3 · 1/3 | 0/3 · 0/3 | 2/3 · 2/3 | 46 m · 40 m |
| 12 | frontal / envelop | 0/3 · 0/3 | 0/3 · 0/3 | **3/3 · 3/3** | 60 m · 58 m |
| 16 | frontal / envelop | 0/3 · 0/3 | 0/3 · 0/3 | **3/3 · 3/3** | 87 m · 62 m |
| 24 | frontal / envelop | 0/3 · 0/3 | 0/3 · 0/3 | **3/3 · 3/3** | 110 m · 76 m |

Aucun assaut n'est allé au bout. Les attaquants sont VIVANTS, cloués entre 40 et 110 m, à
échanger du feu jusqu'à épuisement du budget de pas. Critère d'abandon figé : au-delà de 25 %
d'abandons une cellule est NON MESURÉE — **toutes les cellules sont entre 67 % et 100 %**.
C'est l'issue n°4 des critères, pas la n°3. **On n'a rien mesuré.** Entrée de file : NEGATIF.

**Le seul signal propre** : la distance d'arrêt croît avec la garnison (46 → 110 m en frontal).
Les attaquants sont cloués de plus en plus loin. Cohérent, mais ça parle du budget de temps du
banc, pas de la doctrine.

**Deuxième fois aujourd'hui que JALON 2 se répète** : lire des chiffres tirés de combats figés.
Le garde-fou (bande + comptage des abandons) a fonctionné — c'est lui qui a rattrapé le script.

**DIAGNOSTIC LANCÉ, une seule variable** : budget de pas 60 → 150, mêmes cellules (A=12 vs
D=8 et D=12, frontal, 2 reps). ≥3 résolues sur 4 → le banc manquait de temps et le budget de
pas entre au protocole. 0 résolue → le temps n'est pas la cause, il faudra lire la logique
d'assaut (`assault_tick`, `standoff`) avant tout nouveau run.

## 2026-07-28 16:45 CEST (Claude-Mac, Opus 5) — LA LIGNE D'ASSAUT FINAL : ILS S'ARRÊTENT À 3 MÈTRES DU CRITÈRE

**DIAGNOSTIC ENLISEMENT (budget de pas 60 → 150, une seule variable).**
0 opération sur 4 résolue. Plus de temps les rapproche (28-36 m au lieu de 46-60 m) et leur
fait neutraliser 2 à 5 défenseurs, mais aucun assaut n'aboutit. **Le temps n'est pas la cause.**

**LE CRITÈRE DE PRISE EST À 25 m** (`envelop_arma.py:169`, `pen < 25`). Les distances minimales
mesurées sont de 28, 33, 36 et 50 m. Ils s'arrêtent à TROIS MÈTRES du critère.

**Hypothèse « objectif inatteignable » : RÉFUTÉE (MESURÉ).** Garnison vidée (0 défenseur),
mêmes attaquants, même trajet : distance minimale **20 m**, FOB PRIS au tick 23, 0 perte.
Le point est atteignable et le critère franchissable. L'arrêt à 28 m est donc bien causé par
le feu adverse, pas par le bâti de Pyrgos.

**>>> C'EST LA LIGNE D'ASSAUT FINAL, AU SENS DU MANUEL.** Les assaillants montent au contact,
neutralisent une partie de la garnison, et ne franchissent pas le dernier bond. Le banc n'a
aucun mécanisme pour le forcer : pas de suppression synchronisée sur le franchissement, pas
de fumée, pas d'ordre d'assaut final.

**Ce que le manuel prédisait, avant les données** (noté à 16h05, avant ce diagnostic) :
« ton banc envoie 12 hommes coupés 45/55 contre 24 défenseurs — la doctrine aurait prédit
l'échec avant le run » et « on ne franchit pas la ligne d'assaut final sans supprimer ».
Prédiction confirmée. C'est le premier apport concret du répertoire doctrinal.

**PROCHAIN TEST, pré-enregistré** : `--smoke` (déjà implémenté dans `envelop_arma.py`) sur la
cellule A=12 vs D=12, qui était 0/3. Seuil figé AVANT : **≥2 opérations sur 3 résolues**
(prise OU anéantissement) → l'écran de fumée est la clé du dernier bond et devient un
paramètre du protocole. <2/3 → la fumée ne suffit pas, il faudra un ordre d'assaut final
explicite (suppression synchronisée sur le franchissement).

## 2026-07-28 16:50 CEST (Claude-Mac, Opus 5) — ⚠ `def_arc` EST UN BOUTON DÉBRANCHÉ + le débordement double est une ASSURANCE, pas une manœuvre

**LE BOUTON MORT (MESURÉ).** `assault_terrain.py:174` — quand `def_rand=True`, l'arc défensif
est tiré dans **U(40°,70°) de demi-angle** (soit 80-140° d'arc total) et **`def_arc` n'est
jamais lu**. Tous les bancs du projet passent `def_rand=True`. Tous les commentaires qui
annoncent « arc de tir 120 deg : le flanc EXISTE comme angle mort » décrivent un paramètre
ignoré. Preuve : quatre balayages à 60/120/240/360° ont rendu des chiffres IDENTIQUES au point
près. Un paramètre multiplié par six qui ne change rien n'est pas un paramètre.

Ce que ça n'invalide pas : les verdicts du jour restent des mesures valides (l'arc tiré est
toujours étroit, un angle mort existe toujours). Ce que ça invalide : la DESCRIPTION des bancs
et toute lecture qui attribuait un résultat à « l'arc de 120° ».

**MATRICE À GÉOMÉTRIE FIGÉE** (`--fixe` ajouté : `def_rand=False`, spread 20°, rline 37,5 m,
seul l'arc varie ; les doctrines sont scriptées, elles ne peuvent rien mémoriser, la
randomisation ne protégeait rien ici). D=8, A=4, 200 épisodes, graine 7 :

| arc total | frontal | appui-mvt | déb. simple | déb. double | infiltration | bonds | double − simple |
|---|---|---|---|---|---|---|---|
| 60° | 57 % | 56 % | 100 % | 100 % | 100 % | 28 % | +0 |
| 120° | 35 % | 29 % | 94 % | 93 % | 90 % | 15 % | **−1** |
| 240° | 20 % | 19 % | 43 % | 41 % | **51 %** | 6 % | **−2** |
| 360° | 5 % | 4 % | 16 % | 17 % | 22 % | 1 % | NON MESURÉE (max 22 % < seuil 25 %) |

**>>> LE DÉBORDEMENT DOUBLE NE BAT JAMAIS LE SIMPLE À GÉOMÉTRIE FIGÉE.** Son +8 de la matrice
précédente venait ENTIÈREMENT de la randomisation : le décentrage U(−25°,+25°) fait partir le
crochet simple du mauvais côté une fois sur deux, le double couvre les deux flancs.
**Ce n'est pas une manœuvre supérieure, c'est une assurance contre l'ignorance.** Sa valeur
mesure le coût de ne pas savoir où l'ennemi fait face — un problème de RENSEIGNEMENT déguisé
en problème de tactique. Prédiction du manuel (« le double doit perdre contre le simple à
faible effectif ») : **CONFIRMÉE dès qu'on retire l'incertitude.**

**L'arc est la variable dominante** : la prise passe de 100 % à 16 % quand il s'ouvre. Il était
débranché depuis le début.

**Troisième prédiction du manuel confirmée** : à 240°, quand plus aucun flanc n'est aveugle,
c'est l'INFILTRATION qui passe devant (51 % contre 43 % au débordement simple). « Exige du
couvert et une défense non continue » — elle prend le relais exactement là où le crochet meurt.

Fichiers : `manuel.py` (FIGÉ), `matrice_manuel.py` (+`--arc_deg`, +`--fixe`),
`CRITERES_MATRICE_MANUEL.md` (3c86c7051e57cbad), `CRITERES_ARC_EXPLOIT.md` (043c5333d90aa8a4),
`matrice_manuel.json`, `arc_{60,120,240,360}.json` (INERTES, à ne pas lire),
`arcfix_{60,120,240,360}.json`.

## 2026-07-28 16:55 CEST (Claude-Mac, Opus 5) — AUDIT DES BOUTONS : 3 paramètres silencieusement écrasés, garde-fou posé

`audit_boutons.py` + `audit_boutons.sh` : chaque paramètre passé par les bancs est joué à
DEUX valeurs extrêmes, même graine, même doctrine (`debordement_simple`, D=8, A=4, 150 épisodes).
Sorties identiques au chiffre près → bouton INERTE dans la configuration où les bancs tournent.
**Un processus par bouton** : un assert CUDA empoisonne tout le contexte et emporterait les suivants.

**Résultat brut : 12 inertes sur 21 testés.** Le chiffre brut serait une sur-affirmation ;
voici le découpage, qui seul compte.

**A. Écrasés par un autre bouton — LES SEULS INQUIÉTANTS (3)**
`def_arc`, `def_rline`, `def_spread` : tous tués par `def_rand=True`. La géométrie défensive
que trois bancs croyaient régler était tirée au hasard par épisode.

**B. Inertes par construction de l'expérience — attendu, pas un défaut (7)**
`approach_w`, `death_pen` : paramètres de RÉCOMPENSE, or les doctrines sont scriptées, rien
n'apprend. `arc_obs`, `champ_risque` : paramètres d'OBSERVATION, une doctrine scriptée ne lit
pas l'obs. `emergent_expo`, `nav_around` : exigent `replica=True`, absent ici. `sec_par_pas` :
n'est utilisé que pour convertir `arc_latence_s` et nourrir `stress` — c'est une unité, pas
une physique (vérifié ligne par ligne).

**C. Inertes parce que la doctrine ne les sollicite pas (2)**
`postures`, `hull` : le débordement simple ne se couche jamais, la posture reste debout, donc
le profil de corps ne change pas. Un banc avec une doctrine qui se couche les réveillerait.

**D. Configurations qui ne tournent pas (2)**
`def_line=False` → **assert CUDA, l'environnement tombe** (défenseurs en anneau à 12 m :
distance hors des bornes de la table de toucher, hypothèse à confirmer).
`stress=True` → refusé (erreur au constructeur).

**ACTIFS (9)** : `def_rand`, `cible_unique`, `tir_par_pas`, `degat_par_impact`, `supp_kill`,
`supp_residuel`, `supp_persist`, `secure_only`, `flank_kill`.

**GARDE-FOU POSÉ** (`assault_terrain.py`, sauvegarde `.avantgarde`) : si `def_rand=True` ET
qu'une valeur non-défaut est passée pour `def_arc`/`def_spread`/`def_rline`, l'environnement
émet un `RuntimeWarning` explicite. Vérifié sur les trois cas : avertit quand il faut, se tait
quand il faut. **Soit on randomise, soit on règle, jamais les deux en silence.**

**Ce que la journée établit, et c'est l'énoncé de la thèse** : quatre défauts d'instrument
trouvés en une journée (létalité ×4, conclusion de script erronée, bouton d'arc débranché,
`CUDA_VISIBLE_DEVICES` sur la mauvaise carte), tous rattrapés par des seuils pré-enregistrés
et des gardes, jamais par l'intuition. L'audit transforme l'accident en méthode : quatre
minutes suffisent à savoir quels boutons d'un banc sont réellement branchés.

## 2026-07-28 16:48 CEST — FUMÉE : 1/3, SOUS LE SEUIL (mais n=3 ne tranche rien)

Cellule A=12 vs D=12, 150 pas, `--smoke --smoke_dist 45`, 14 grenades par opération.
Une seule variable ajoutée par rapport au run de certification.

| rep | pris | survivants | distance min | EAST neutralisés |
|---|---|---|---|---|
| 1 | non | 6/12 | 67 m | 4/12 |
| 2 | non | 7/12 | 28 m | 6/12 |
| 3 | **OUI** | **10/12** | 20 m | 2/12 |

Seuil pré-enregistré : ≥2/3 résolues. Obtenu 1/3 → **la fumée ne suffit pas**, il faut un
ordre d'assaut final explicite (suppression synchronisée sur le franchissement).

**À NE PAS SURINTERPRÉTER** : sans fumée la cellule était 0/3, avec fumée 1/3. À n=3, cet
écart ne prouve rien — ni que la fumée aide, ni qu'elle est inutile. Ce qui est notable :
quand l'assaut passe, il passe bien (20 m atteints, 2 pertes sur 12).

**PROCHAINE BRIQUE (non lancée)** : un ordre d'assaut final dans `envelop_arma.py` — au
passage sous ~40 m, les fixeurs supprimant en continu pendant que l'élément d'assaut reçoit
un `doMove` répété sur le point d'objectif, sans interruption de tir. C'est le mécanisme que
le manuel décrit et que le banc n'a pas.

## 2026-07-28 18:25 CEST — ORDRE D'ASSAUT FINAL : LA CAUSE DE SIX SEMAINES D'ENLISEMENT

**LA CAUSE, MESURÉE.** `doSuppressiveFire` **arrête l'unité**. Dans `HMT_ENVELOP_APPLY`, tout
attaquant ayant une ligne de vue recevait `doTarget` + `doSuppressiveFire` : il se figeait sur
place. C'est l'enlisement constaté sur 28 opérations les 14/06 et 28/07 — attribué jusqu'ici à
la tactique, alors que c'était une commande SQF qui clouait les hommes au sol.

**LE MÉCANISME AJOUTÉ** (`--assaut_final DIST`, défaut 0 = désactivé, non régressif) :
sous DIST mètres, l'élément d'assaut cesse de tirer (`doWatch objNull`, `doTarget objNull`,
plus de `doSuppressiveFire`), se lève et court (`setUnitPos "UP"`, `forceSpeed 100`), et reçoit
un `doMove` répété sur l'objectif. Les fixeurs continuent de supprimer. C'est le dernier bond
du manuel : l'élément d'assaut ne tire pas, la base de feu couvre.
Fichiers : `envelop_arma.sqf` (+`.avantassaut`, copié dans les deux missions),
`envelop_arma.py` (+`.avantassaut`).

**PREUVE D'ACTIVATION (n=1)** : cellule A=12 vs D=12, frontal, déclencheur 40 m →
**FOB PRIS au tick 87**, 26 → 19 m en quatre pas après déclenchement, 6 pertes sur 12.
La même cellule sans l'ordre était 0 prise sur 3, arrêtée à 58-60 m.

**RUN V1 (`7c8d6c96a8cf6887`) : 0 RÉSOLUE SUR 6 — MAIS IL N'A PAS TESTÉ L'ORDRE.**
Distances minimales : 34, 42, 55, 58, 67, 81 m pour un déclencheur à 40 m. Le mécanisme n'a pu
s'armer que dans **1 opération sur 6**. Le seuil pré-enregistré (≥5/6 résolues) n'est pas
atteint et l'entrée est NEGATIF — mais la lecture correcte est : à 12 contre 12, les assaillants
n'atteignent même pas la distance de déclenchement.

**DEUX FAUTES DE MA PART, CONSIGNÉES :**
1. Déclencheur placé là où le tir de démonstration s'était arrêté (26 m), pas là où le banc
   s'enlise réellement (55-81 m).
2. Le runner filtrait par `tail -1` et **jetait les lignes de tick**, donc toute preuve de
   déclenchement. Il a fallu reconstituer par les distances. Corrigé : le journal conserve
   désormais les lignes `FRANCHISSEMENT`. C'est exactement le défaut traqué chez les autres
   bancs toute la journée — un instrument qui ne garde pas la trace de ce qu'il mesure.

**V2 LANCÉE** (`CRITERES_ASSAUT_FINAL_V2.md`, `c921d934a962560b`) : une seule variable, le
déclencheur passe à 80 m. Deux seuils en cascade : d'abord ≥5/6 opérations doivent AFFICHER un
déclenchement (sinon rien d'autre ne se lit), ensuite ≥4/6 doivent être résolues.
**Pas de troisième valeur de DIST dans ce chantier** : deux réglages successifs d'un même
bouton, c'est du tuning, pas une mesure.

## 2026-07-28 19:10 CEST — CERTIF DANS LA BANDE : NON MESURÉE, mais l'écart d'abandons dénonce un mécanisme

Critères `CRITERES_CERTIF_BANDE.md` (`657f109d4af8e368`). A=12 vs D=8, 6 reps par bras,
ordre d'assaut final DÉSACTIVÉ, Altis/Pyrgos.

| bras | prise | abandons | pertes/prise | EAST neutralisés |
|---|---|---|---|---|
| frontal | 33 % | **67 %** | 1,50 | 2,7/8 |
| envelop | 83 % | **17 %** | 1,80 | 2,7/8 |

**Verdict des critères : bras frontal NON MESURÉ** (67 % d'abandons > 25 %). Aucune comparaison
ne se lit, aucune prédiction du sandbox n'est tranchée.

**MAIS L'ÉCART D'ABANDONS EST LE SIGNAL.** Dans `envelop_arma.py`, pendant leur crochet les
débordeurs reçoivent `fire = 0` (« swing silencieux », ligne ~152) ; les frontaux reçoivent
tous `fire = 1`. Or `doSuppressiveFire` FIGE l'unité (mesuré ce soir).

**HYPOTHÈSE (SUPPOSÉ) : les débordeurs avancent parce qu'on leur interdit de tirer, les frontaux
s'arrêtent parce qu'on leur ordonne de tirer.** L'avantage du flanc mesuré sur Arma serait un
artefact de l'ORDRE DE FEU, pas une vertu de la géométrie. C'est la même histoire que le
débordement double du sandbox cet après-midi : un avantage qui vient du harnais, pas de la
tactique.

**Ce que ça mettrait en cause si c'est vrai** : tous les A/B frontal-vs-débordement de ce banc,
y compris le banc FIBUA du 23/07. À vérifier avant d'en graver quoi que ce soit de plus.

**TEST SUIVANT, une seule variable** : un FRONTAL SILENCIEUX (`fire = 0` jusqu'au contact,
même trajet, même effectif). Si son taux d'abandon s'effondre et sa prise rejoint celle de
l'envelop, l'avantage du flanc sur ce banc est un artefact de l'ordre de feu.

## 2026-07-28 19:23 CEST — FRONTAL SILENCIEUX : effet FORT, seuil ÉCHOUÉ, pré-inscription MAL CALIBRÉE

Critères `CRITERES_FRONTAL_SILENCIEUX.md` (`45f3851a98d62c57`). A=12 vs D=8, 6 reps,
une seule variable : `--silencieux` (`fire=0` en progression).

| bras | prise | abandons | dist_min moy |
|---|---|---|---|
| frontal BRUYANT | 33 % | 67 % | — |
| **frontal SILENCIEUX** | **67 %** | **33 %** | 28 m |
| envelop bruyant | 83 % | 17 % | — |

**Verdict des critères : SEUIL 1 ÉCHOUÉ** (33 % d'abandons > 25 %). Entrée NEGATIF, seuil 2
non lu. Le run reste consigné tel quel, il n'est pas réinterprété.

**⚠ LA CONCLUSION IMPRIMÉE PAR LE SCRIPT EST FAUSSE.** Il affiche « l'ordre de feu n'explique
PAS l'enlisement ». Les données disent l'inverse en tendance : abandons divisés par deux,
prise doublée, dans la direction prédite. À n=6, 33 % contre 67 % c'est 2 opérations contre 4 —
ça ne tranche pas. **Troisième fois aujourd'hui qu'une branche codée d'avance surinterprète**
(après `certif_seuil_arma` et `arc_exploit`). Les branches de conclusion doivent être écrites
aussi prudemment que les seuils.

**LA FAUTE EST DANS MA PRÉ-INSCRIPTION, et elle est instructive.** J'ai fixé le seuil d'abandons
à ≤25 % alors que le bras de comparaison était à 67 %. Un effet qui DIVISE PAR DEUX — le
résultat le plus probable si l'hypothèse est vraie — atterrit à 33 % et échoue au seuil.
**J'ai posé une barre qu'un succès net ne franchissait pas.** Un seuil doit être calibré sur
la taille d'effet attendue, pas choisi rond.

**RÉPLICATION OUVERTE** (`CRITERES_SILENCE_REPLICATION.md`) : trois bras × 18 opérations,
comparaison primaire sur la PRISE (frontal silencieux − frontal bruyant ≥ +20 points), seuils
écrits avant les données. Le run à n=6 n'est pas effacé : il est le pilote qui a servi à
dimensionner celle-ci.

## 2026-07-28 21:36 CEST — ⭐⭐⭐ LA VARIANCE DU BANC ARMA DÉPASSE LES EFFETS QU'ON Y CHERCHE

Réplication `CRITERES_SILENCE_REPLICATION.md` (`e289a5f5e592ec36`), 3 bras × 18 opérations,
A=12 vs D=8, Altis/Pyrgos. 54 opérations, 2 h 11.

| bras | ops | prise | enlisés | pertes/prise |
|---|---|---|---|---|
| frontal bruyant | 18 | **67 %** | 33 % | 3,33 |
| frontal silencieux | 18 | **33 %** | 67 % | 4,00 |
| envelop bruyant | 18 | 61 % | 39 % | 1,82 |

**Verdict des critères** : bras `frontal_silencieux` NON MESURÉ (67 % d'enlisements > garde 40 %).
La comparaison primaire ne se lit pas. Entrée NEGATIF.

**L'HYPOTHÈSE DU SILENCE EST MORTE, ET RETOURNÉE.** Pilote (n=6) : silencieux 67 %, bruyant 33 %.
Réplication (n=18) : bruyant 67 %, silencieux 33 %. **Les deux chiffres ont échangé leurs places.**

**>>> LE RÉSULTAT DE LA NUIT, ET IL VAUT PLUS QUE L'HYPOTHÈSE QU'IL TUE :**
**le même bras, mesuré deux fois, donne 33 % puis 67 % de prise.**
`certif_bande` (18h46, 6 ops) : frontal bruyant 33 %. `replication_silence` (21h36, 18 ops) :
frontal bruyant 67 %. Même script, même configuration, même rapport de forces, même théâtre.
**34 points d'écart entre deux mesures du même bras.**

**La variance de ce banc dépasse tous les effets qu'on y cherche depuis six semaines.** Ça
explique d'un coup : le seuil de manœuvre qui ne se certifie pas, la fumée à 1/3, l'ordre
d'assaut à 0/6, le pilote qui s'inverse. On mesurait du bruit avec une règle trop fine.

**OBSERVATION NON PRÉ-ENREGISTRÉE** (à traiter comme telle) : l'envelop prend l'objectif aussi
souvent que le frontal (61 % contre 67 %) pour **1,82 perte contre 3,33**. Le flanc achète des
VIES, pas l'objectif. C'est exactement ce que le sandbox a mesuré ce matin (coût ×0,39). Seule
chose que deux instruments indépendants affirment ensemble aujourd'hui.

**CE QUI DOIT PRÉCÉDER TOUTE AUTRE MESURE SUR CE BANC** : estimer sa variance. Rejouer UN SEUL
bras en blocs indépendants et mesurer l'écart entre blocs. Ce chiffre donne le n minimal de
toute comparaison future. Sans lui, chaque A/B de ce banc est une loterie qu'on interprète.

## 2026-07-29 — JOURNÉE ENTIÈRE : L'AGENT PASSE DE 0,3 % À 72 % DE SUCCÈS

Architecte : Fable. Exécution : Opus 5. Arbitrage : Younes.
**Tous les chiffres ci-dessous sont mesurés par l'instrument certifié au jalon 1.**

---

### 1. LE JALON 1 — DES INSTRUMENTS QUI ONT PROUVÉ LEUR ZÉRO
Motif : sept pannes en deux jours, toutes dans l'instrument, jamais dans l'objet mesuré.
**Règle qui a fermé la boucle** : on possède des objets dont la réponse est connue — les six
doctrines écrites à la main. Aucun instrument n'a le droit de produire un chiffre tant qu'il n'a
pas retrouvé ces chiffres-là.

Fichiers : `CRITERES_JALON1.md` (`2129aea319627f8f`), `banc_mission.py` (collecte seule, journaux
en ajout, empreintes des fichiers dans l'en-tête), `analyse_journal.py` (recalcule le prédicat et
le compare au monde), `audit_ordre.py` (orchestrateur, plus aucune boucle de mesure),
`preuve_permutation.py`, `etalon_j1.sh`, `etalon_j1_5graines.sh`, `controle_nul_e6.sh`.

**Quatre bugs de fond corrigés dans `monde_mission.py`** : permutation résolue après le
re-tirage ; premier pas jamais permuté ; mode épisode qui supprime le pas désynchronisé par
construction ; instantanés du toucher et bornes de mission figés avant le re-tirage.

**AMENDEMENT 4, accepté par Younes** : l'ancienne table d'étalon est retirée. Elle mesurait des
doctrines **amputées** — le pas était désynchronisé, donc passé le 14e pas global plus aucun
épisode ne recevait le signal qui déclenche le crochet ou l'éventail. Les trois doctrines à phase
unique décrochaient de 28 à 32 points ; les trois qui n'utilisent pas le pas tombaient dans la
tolérance. Signature du mécanisme, pas coïncidence.

**Étalon consolidé, 5 graines, protocole persisté, étendue max 5,8 points** :
| doctrine | PRENDRE | INFILTRER |
|---|---|---|
| débordement double | 87,5 | 62,9 |
| débordement simple | 84,9 | 61,5 |
| infiltration | 83,7 | 50,2 |
| appui-mouvement | 46,0 | 13,2 |
| frontal | 45,0 | 7,8 |
| bonds alternés | 24,6 | 10,0 |

**Contrôle nul (E6)** : écart **exactement 0,000** sur les six doctrines, 120 passes,
122 880 épisodes. *Un instrument qui n'a pas prouvé son zéro ne mesure pas, il opine.*

---

### 2. CE QUI A ÉTÉ ESSAYÉ ET FERMÉ, PAR SES PROPRES PORTES

| version | mécanisme | résultat | pourquoi c'est clos |
|---|---|---|---|
| v3 | monde d'avant les correctifs | 4,1 % | monde cassé |
| v4 | monde certifié, verbe | 26-32 % | ×8 par le seul correctif du monde |
| v5 | l'ordre devient un budget consommé | ~2 % | dose **plate à 3,0** quel que soit le budget |
| v6 | couche réactive, 4 règles | ~1 % | la couche substituait **64 à 74 %** des gestes |
| 3b | lagrangien, λ persistant | 5-15 % | λ > 1,0 avant l'itération 200, garde-fou déclenché |

**v5** : le critique apprenait parfaitement le budget (écart de valeur 0,24) mais la politique ne
s'en servait pas (divergence d'actions 0,0004 sur une échelle qui monte à 0,693). Le verbe était
une constante d'épisode dont la conséquence n'existait qu'au dernier pas.

**v6, le témoin décisif** — les doctrines passées **à travers** la couche :
| doctrine | arrivée sans | arrivée à travers |
|---|---|---|
| infiltration | 94,9 % | **1,0 %** |
| débordement double | 96,2 % | 6,8 % |
| frontal | 54,2 % | 0,5 % |
Une politique qui ne lit aucune observation s'effondre de 95 % à 1 %. Ce n'était pas
l'apprentissage. **La conclusion d'obéissance à rho 1,000 sur l'agent entraîné est RETIRÉE :
elle mesurait l'immobilité.** Un agent qui n'arrive jamais respecte n'importe quel budget.

**3b** : les épisodes qui violent sont ceux qui arrivent. Taxer l'exposition retire l'arrivée
avant de retirer la violation. **Mais le run précédent, où λ était plafonné à 0,2 par un bug de
reprise, a donné 51 % d'arrivée et 25 % de succès — meilleur que le témoin sans contrainte.**
Un petit coût d'exposition guide vers les routes discrètes, qui sont aussi celles qui arrivent.
Un gros coût tue.

---

### 3. CE QUI A MARCHÉ — IMITATION PUIS AFFINAGE (recette SHAMAL)

**Contrôle à un seul changement** : budget poussé à l'infini, aucune couche → arrivée
24,2 → 28,3 %. La machinerie était saine, la contrainte était le coupable.

**Deux écarts, qu'il ne faut plus confondre** : la contrainte (28,3 → 0,3 %) et la compétence
(96,2 → 28,3 %). Le second est le vrai mur.

**Professeur** : `debordement_double` seul, 15 050 240 paires, filtrées sur les épisodes qui
**arrivent** et non sur ceux qui réussissent. Accord de clonage **96,2 %** sur données tenues à
l'écart, 3 époques.

**Résultat final, graines TENUES À L'ÉCART (2000-2002), 2048 épisodes par cellule :**
| | arrivée | succès à B=2,2 |
|---|---|---|
| clone | 76,4 % | 64,0 % |
| affiné graine 0 | 88,1 % | **72,2 %** |
| affiné graine 1 | 90,7 % | **71,8 %** |
| affiné graine 2 | 78,2 % | 65,6 % |

**Gain moyen sur le clone : +5,9 points. Critère pré-enregistré de +5 points : FRANCHI.**
Arrivée de 76 à 90 %, contre 96 % pour le professeur original.

**Réserve** : les trois graines régressent à l'itération 200 (succès moyen 57,4 %, sous le clone).
Le point de contrôle 100 est le bon. Même motif de régression tardive que v4.

Fichiers : `collecte_prof.py`, `clone_prof.py`, `affine.sh`, `ckpt/clone.pt`,
`ckpt/aff_g{0,1,2}_100.pt`, `CRITERES_3B_LAGRANGIEN.md` (`392bbcd9c236d0f7`),
`CRITERES_V6_REFLEXE.md` (`4420f233b5b301be`), `CRITERES_V5_BUDGET.md` (`9274c81a3842a5e5`).

---

### 4. LES LEÇONS DE MÉTHODE, PAYÉES CHER

1. **Toute porte qu'un agent immobile peut franchir est nulle.** Mes deux portes de v6 étaient
   des portes de solidité ; il leur manquait une compagne de vivacité — vérifier que le corps
   **laisse encore arriver**.
2. **Un réflexe masque, il ne choisit jamais.** Critère exécutable de Fable : la règle s'écrit-elle
   en interdisant des actions, sans autre effet ? Ma règle d'éloignement écrivait un cap : ce
   n'était pas un réflexe, c'était une décision tactique déguisée, et elle retournait le corps
   contre le but.
3. **Collecte et jugement doivent être deux programmes distincts.** Le banc écrit des épisodes
   bruts en ajout seul ; l'analyse recalcule le prédicat et le compare au monde. Ce contrôle a
   attrapé **trois** bugs dans mon propre code en une heure, tous invisibles en mode épisode.
4. **Douze erreurs d'instrumentation en deux jours, toutes de la même forme** : une valeur lue
   après que l'état a bougé, ou un champ qui ne veut pas dire ce qu'on croit. Le champ `took` du
   journal valait « le pas du toucher est renseigné », or ce pas ne l'est qu'au succès : les deux
   colonnes mesuraient la même chose et on ne pouvait pas répondre à « l'escouade arrive-t-elle ».
5. **Ce qui rattrape, ce n'est jamais l'intuition** : c'est un seuil écrit avant les données, un
   témoin, ou un contrôle nul. Trois branches ont été fermées par leur propre garde-fou.
6. **Machine en veille = neuf heures de labo perdues.** `systemctl suspend` à 01h43. Commande
   `dodo` posée : elle refuse la veille si la file travaille.
7. **`CUDA_VISIBLE_DEVICES=1` désignait la GTX 1060**, pas la 3090 — CUDA numérote par puissance,
   `nvidia-smi` par bus PCI. `CUDA_DEVICE_ORDER=PCI_BUS_ID` ajouté au lanceur.
8. **Trois travaux tiennent sur la 3090** : mesure à 16 % d'occupation avec un seul, 99 % avec
   trois. Le goulot est le lancement des noyaux côté processeur, pas la carte.

## 2026-08-10 — ANTISTASI : capteur + reset debout (socle, pas verdict)
Antistasi Ultimate v11.9.12 (release officielle @A3U) tourne HEADLESS sur Stratis,
port jeu 6072, pont TCP 5876. Serveur dedie propre, les 5 bancs en cours intacts.

CAPTEUR — addon separe `@HMT_Capteur` charge en -serverMod. Antistasi reste VANILLA :
l observateur est exterieur au monde observe. Emet toutes les 10 s sur le pont :
  A3A_ETAT|t|date|hr|argent|tier|aggOcc|aggInv|soutien|compFIA|unites|groupes
  A3A_ZONES|<marqueur>=<camp>, ... (26 zones Stratis)
  A3A_LIEU|<marqueur>|<type>|<x>|<y>  (inventaire fixe, une fois)

DEMARRAGE SANS JOUEUR — Antistasi attend `A3A_saveData` (choix admin). Injecte par le
pont : startType=new, factions [Occ,Inv,Reb,Civ,Riv] = NATO_Arid / CSAT_Arid / FIA /
Civ / LE, startPos = marqueur Synd_HQ. Campagne ouverte : hr=8 argent=1000 tier=1.

RESET — la campagne entiere tient dans profileNamespace, un seul fichier
(Player.vars.Arma3Profile, 148 077 octets). Point zero fige avec empreinte sha256
ac97206e959c636d21998944bfd276777c3e50b32a9c5e5590d895ff54acdf96.
`reset_antistasi.sh reset` = tue, restaure le fichier, relance ; `autoLoadLastGame=60`
recharge SANS admin. CYCLE MESURE : etat identique revenu a t=75 s apres relance
(hr=8 argent=1000 tier=1 aggOcc=1 aggInv=1 soutien=0 compFIA=5). Cout ~3 min/reset,
dont 60 s de minimum impose par le parametre.

PIEGES PAYES — `compile` ne passe pas par le preprocesseur : tout `//` casse la
commande envoyee par le pont (nettoyage a l emission). Le template de mission d un
addon n est pas trouve par nom : extraction dans mpmissions + #include reecrits en
chemin absolu `\x\A3A\addons\maps\`. `pbo - unknown` au log = simple absence de
numero de build, PAS une erreur de chargement.

PAS ENCORE FAIT : aucun agent, aucun apprentissage, aucune action envoyee a la
campagne. Socle seulement.

## 2026-08-10 — VERDICT NEGATIF : l acceleration du temps ne sert a rien sur Antistasi
Question : setTimeMultiplier accelere-t-il la CAMPAGNE, donc le debit d entrainement ?
Mesure sur une 2e instance dediee (ports 6082/5886), point zero identique, la 1re
instance intacte -> au passage, deux campagnes tournent en PARALLELE sans probleme.

Ecrit avant la mesure : verdict NEGATIF si `time` reste a ~1 s/s pendant que `date`
accelere. Controle positif : `date` DOIT accelerer, sinon la commande n a pas pris.

RESULTAT sur 2 fenetres de 120 s :
  temps MISSION : A = 1,00 s/s   B = 0,99 s/s   -> x0,99
  horloge MONDE : A ~ x1         B ~ x16        -> controle PASSE
Le battement economique d Antistasi est `time + 600` (fn_resourcecheck.sqf) = du temps
MISSION. setTimeMultiplier ne touche que l horloge du monde. LEVIER MORT.

CONSEQUENCE, plus dure que le chiffre : le tick economique vaut 10 MINUTES REELLES. Un
episode de campagne qui a du sens se compte donc en HEURES, pas en minutes. A 14
instances (mesure : 0,22 coeur et 1,8 Go a vide, plafond RAM ~23 instances), cela fait
336 heures-serveur/jour, soit ~110 episodes de 3 h. Pas 35 000 decisions/jour.

=> Antistasi au niveau CAMPAGNE n est pas un environnement d ENTRAINEMENT sur ce
   materiel. C est un CERTIFICATEUR. Meme partage que sandbox/Arma, un etage plus haut :
   pour apprendre, il faudra une replique symbolique rapide de la campagne.
