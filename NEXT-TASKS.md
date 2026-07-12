# NEXT-TASKS — Plan autonome HARMATTAN (relais Claude workstation)

> Écrit par le Claude-Mac (architecte) le 2026-06-13 ~12h, en passation au Claude-workstation (bâtisseur).
> **Mode autonome activé** : dérouler ce plan sans attendre l'utilisateur, en respectant les GATES pré-enregistrés.
> Toujours : pré-enregistrer les seuils AVANT les données · jamais de conclusion sur demi-échantillon · une variable à la fois · horloges en temps de jeu · runs en nohup + logs en dur dans `logs_train/` · reboot préventif flotte entre grandes tables · `pkill` JAMAIS dans la cmdline ssh (script via stdin) · logger chaque verdict dans `MEMOIRE-COMMUNE.md`.

## Où on en est (état à la passation)

- **Reconnaissance comportementale = MORTE** (sonde froide 26%, combat 32%, officier live −12 vs M3). Les postures se ressemblent sous le feu.
- **PIVOT GÉOMÉTRIE = gagnant.** Brique 0 :
  - le **vainqueur tourne** avec la forme de défense (matrice `mxg_*`, n=12) : standard→M8(83%), concentre→M5(58%), disperse→M2(33%), faible_ouest/est→M1. **Valeur de sélection +13** (adaptatif 52% vs meilleure fixe M2 38%).
  - la **géométrie est lisible à 100%** (classifieur spatial sur features de spawn, `geo_recon.jsonl`, LOO diagonal parfait).
- **Boucle adaptative câblée** (`officer_geo.py` : lit géométrie → champion → exécute ; `measure_geo_officer.py`). Smoke flotte-fraîche = 5/5 reco, 0 erreur.
- **Run de confirmation EN COURS** (`geoconf.sh` → `geo_officer3.jsonl`, ~70 min) : officier adaptatif vs M2 fixe, 8 reps × 5 géo × 2, sur flotte fraîche post-reboot OS.

## ÉTAPE 0 (immédiate) — fermer la brique 0

1. Attendre `GEOCONF FINIE` (`/tmp/geoconf_last` → le log) ; verdict aussi appendé dans `MEMOIRE-COMMUNE.md`.
2. **GATE 0** : si `adaptatif − fixe ≥ +8 pts` ET reco-en-boucle ≥ 90% → **BRIQUE 0 CLOSE** (le renversement du −12 est prouvé end-to-end).
   - Si +0 à +8 → marginal : escalader reps (n=16/géo) avant de graver.
   - Si erreurs > 15% → flotte encore malade : `pkill` (script) + reboot OS (demander le mdp sudo à l'utilisateur, l'ancien `R8IdSAsRHAmI` ne marche plus) + re-smoke avant de relancer.
3. Mettre à jour la thèse `~/Documents/HARMATTAN-these.md` §4.7 avec le chiffre (TÂCHE CÔTÉ MAC : le PDF se reconstruit avec `python3 ~/Documents/build_these.py` sur le Mac — la workstation logge juste le verdict).

## CAP — ordre pré-enregistré (chaque brique = une question, un gate, calibrée Arma anti-fiction)

### Brique 0-bis — DURCIR LA RECO SOUS BROUILLARD (rapide, à faire en premier)
- **Question** : la géométrie reste-t-elle lisible quand l'éclaireur ne voit QU'UNE PARTIE de l'ennemi (LOS) ? Le 100% était en lecture omnisciente (pont voit tout).
- **Build** : variante de `collect_geo_recon.py` où les features ne comptent que les ennemis « vus » (dans un cône/rayon LOS depuis une escouade de reconnaissance), pas tout `HMT_EN`. Réutiliser `_nearest_enemy_dist`/sight d'op_arma.
- **GATE** : reco ≥ 70% sous LOS → la boucle tient en réaliste. Sinon, noter quelles géométries deviennent ambiguës.

### Brique 1 — MULTI-OBJECTIF (front + profondeur)
- **Question** : avec PLUSIEURS objectifs (2-3 villages/points), la décision opérative (axe principal, séquencement, allocation) paie-t-elle vs un plan fixe ?
- **Build** : étendre la géométrie à plusieurs objectifs adressables (op_arma : plusieurs garnisons spatiales). Mesurer valeur de sélection au niveau OPÉRATIF (quel objectif d'abord / comment répartir les 4 escouades).
- **GATE** : sélection opérative ≥ +10 → l'échelon opératif a un sens.

### Brique 2 — MONTER L'ÉCHELON OPÉRATIF (répertoire-sélecteur, PAS RL-découvre)
- **Rappel scar** : le manager RL `train_manager` a fait 83% sim → **0% Arma** (sur-apprend la fiction CRÊTE). NE PAS refaire « RL découvre la tactique en sim ».
- **Build** : un sélecteur (LLM officier qwen2.5:14b ou petit classifieur) qui, sur le monde multi-objectif, choisit un PLAN opératif dans un répertoire Arma-exécutable, sur features réelles. Réutiliser `op_gpu.py` SEULEMENT comme accélérateur calibré, jamais comme source de vérité.
- **GATE** : bat la meilleure partition fixe en Arma réel (n≥16).

### Brique 3 — ENNEMI CO-ÉVOLUTIF
- **Question** : un DÉFENSEUR appris (ligue `train_league_gpu`) génère-t-il la diversité structurelle tout seul et force-t-il l'adaptation (punit un M3/M8 répété) ?
- **Risque** : sim-to-real (le défenseur appris en sim doit se transposer en géométries Arma-exécutables). Garder le défenseur dans l'espace des géométries/postures Arma-exécutables.

## Outils clés (rappel)
`officer_geo.py` (boucle), `measure_geo_officer.py` (--reps --seed0 --append --servers), `collect_geo_recon.py` (reco), `geometries.py` (5 formes), `analyze_geo.py` (matrice+sélection), `run_maneuver.py --geometry`, pont natif `hmt_native_x64.so` (HMT_SOCKET=1), `multi_server.sh 16` (flotte). Cerveau soldat = `koth_finetuned.pt`.

## INFRA (réparée 13/06) — à respecter pour tout run concurrent
- Cause des 70% d erreurs = pic CPU synchrone (spawns simultanés sur serveurs mono-thread). 
- Fix en place : `op_arma._query` poll-timeout + `measure_geo_officer.worker` stagger `srv*1.8`. Vérifié 0/12→12/12.
- **RÈGLE** : tout nouveau harnais concurrent DOIT staggerer les départs de workers (sleep srv*~1.8s) ; sinon timeouts. Diagnostic réutilisable : `infra_diag.py` (Phase A solo / Phase B concurrence), `infra_concur.py <stagger> <N>`.
- Confirmation propre brique 0 EN COURS : `geo_officer_clean.jsonl` (verdict appendé dans MEMOIRE-COMMUNE).

## SOCLE RÉPARÉ (13/06 ~16h30) — REMPLACE la note infra precedente
Vraie cause des 70% derreurs = (1) reconnexion par op (2e connexion/serveur echoue) + (2) fuite de groupes. FIX en place et VERIFIE (0% err 8-way churn) : `officer_geo` reutilise 1 env/pont par worker (make_env/respawn) ; `op_arma` spawn fait `deleteGroup`. **Le churn long est maintenant PROPRE** -> plus besoin de reboot par batch pour la mesure (garder un reboot occasionnel pour la RAM sur runs tres longs). Tout harnais doit : 1 env reutilise par serveur (jamais reconnecter par op).

## CORRECTION SOCLE (13/06 ~17h) — prioritaire sur les notes infra precedentes
L env REUTILISE biaise la mesure (std M8 0/4 vs matrice 83%) -> NE PAS l utiliser pour mesurer. **Toute mesure = pattern matrice** (run_maneuver, env FRAIS, <=1 op/serveur/process, reboot entre cellules) : correct ET pas de timeout (1 connexion/serveur/process). Garder `deleteGroup` + `_query` poll-timeout (vrais fixes). Brique 0 CLOSE = +14 (matrice). Suite : reco sous brouillard -> multi-objectif -> echelon operatif -> co-evolution (cf. plus haut), en mesurant TOUJOURS avec le pattern matrice.
