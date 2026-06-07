# FICHE DE ROUTE — HARMATTAN
### Escouade autonome, PROFONDE et COMPLEXE, en environnement ULTRA-CONTESTÉ
Règle d'or à chaque étape : **faire marcher → corriger → entraîner → critère « ça marche »** avant de passer à la suite.

---

## 🎯 MISSION CIBLE — « SAISIE ET TENUE D'UN POINT CLÉ CONTESTÉ »
- **Escouade** : 4 agents à rôles — **chef** (coordonne), **assaut** (prend), **appui** (suppresse), **sécurité** (couvre/tient).
- **Objectif** : **localiser → prendre → TENIR** un point défendu, sur une zone avec couvert et plusieurs approches.
- **Réussite** : objectif **tenu ≥ T pas** avec **≥ 3 survivants**, contre un ennemi qui **se bat pour de vrai**.

La difficulté monte sur **DEUX AXES en parallèle** : le **cerveau** des agents (axe A) et **contre qui** ils combattent (axe B).

---

## 🧠 AXE A — LE CERVEAU (capacités, dans l'ordre)

### A0 — Socle coopératif  [✅ FAIT]
PPO → MAPPO (CTDE) + shaping + curriculum + env vectorisé + multi-serveurs. Prend un objectif statique défendu (98 %).

### A1 — 🧭 ORIENTATION  (perception + mémoire)
- [ ] **Observation partielle (LOS)** : chaque agent ne voit que ce qui est à portée/en ligne de vue.
- [ ] **Mémoire (RNN/GRU)** : se souvenir de ce qu'on a vu (objectif aperçu, dernière position ennemie).
- **Critère** : localise + atteint l'objectif en vue partielle, **là où le sans-mémoire échoue**.

### A2 — 📡 COMMUNICATION  (partage d'info)
- [ ] **Canal de messages appris** entre agents (type TarMAC/IC3Net).
- [ ] **Chef léger** : agrège l'info et **assigne des sous-objectifs**.
- **Critère** : réussit une tâche à **info distribuée** qu'elle **rate sans comms**.

### A3 — ⚔️ TACTIQUE  (manœuvre coordonnée)
- [ ] **Macro-actions** (bondir / prendre couvert / suppresser / sécuriser) — résout le mur « téléport vs tir » (V3).
- [ ] **Rôles tactiques dans Arma** : appui suppresse / assaut contourne / sécurité tient.
- **Critère** : **prend ET tient** l'objectif, pertes minimes.

---

## 🎖️ AXE B — L'ADVERSAIRE (contre qui ils se battent, dans l'ordre)

### B0 — OPFOR statique simple  [✅ FAIT]
Gardiens immobiles. Tremplin pour apprendre les bases.

### B1 — 🪖 VRAIE IA DE COMBAT ARMA  [PROCHAIN PALIER]
- [ ] Activer la **vraie IA militaire d'Arma** comme ennemi : elle **manœuvre, prend couvert, flanque, suppresse, réagit** (on retire les `disableAI`, on lui donne patrouilles/comportement COMBAT, skill réaliste).
- [ ] Adversaire **varié** (effectifs, postures, positions) → les agents affrontent un vrai comportement militaire, pas une cible figée.
- **Critère** : la squad **gagne contre l'IA Arma** (prend+tient), sans l'exploiter bêtement.

### B2 — 🤺 OPFOR APPRIS  (self-play — ENDGAME)
- [ ] **Politique OPFOR** (mêmes briques, camp adverse — pont déjà symétrique HMT_AG/HMT_OP).
- [ ] **Boucle de self-play** (fictitious self-play / league à la AlphaStar).
- **Critère** : BLUFOR tient sa réussite **face à un ennemi qui s'améliore** (course à l'armement).

---

## 🌊 PROFONDEUR & COMPLEXITÉ (intégrés, PAS optionnels — c'est ce qui rend les agents profonds)

- [ ] **CMDP / curseur λ dans Arma** → **profondeur comportementale** : les agents **modulent leur risque** (prudent ↔ agressif) au lieu d'un seul style figé.
- [ ] **Domain randomization** → **robustesse** : positions/effectifs/objectif **aléatoires** chaque épisode → ils **généralisent** au lieu de mémoriser une carte.
- [ ] **Transfert toy→Arma** → **profondeur d'entraînement** : pré-entraîner vite sur le jouet (millions de pas) puis **affiner** dans Arma → atteint des comportements plus riches.
- [ ] **Capacité réseau qui grandit** → le réseau **grossit avec la difficulté** (mémoire, comms, plus de neurones) : petit aujourd'hui, profond quand la mission l'exige.

---

## 🗺️ SÉQUENCE D'EXÉCUTION
**Cerveau** : A0 ✅ → A1 mémoire → A2 comms → A3 tactique (macro-actions).
**Adversaire** : B0 ✅ → **B1 vraie IA Arma** → B2 OPFOR appris (self-play).
**Profondeur** : λ + randomization + transfert + capacité **tissés tout du long**.

Bon enchaînement concret :
1. **B1 (vraie IA Arma)** + **domain randomization** → durcir l'adversaire et généraliser sur le socle actuel.
2. **A1 (mémoire)** + obs partielle → début phase agentique.
3. **A2 (comms)** → coordination apprise.
4. **A3 (macro-actions)** → vraie tactique de combat.
5. **λ-Arma** → moduler le risque ; **transfert** → accélérer.
6. **B2 (self-play)** → l'endgame agent-vs-agent.

> Prérequis dur : **la mémoire (A1)** conditionne A2, A3 et B2. Sans elle, pas de combat dynamique ni de self-play.

---

## 📅 PLANNING OPÉRATIONNEL — séquence gravée le 2026-06-07 (post-table École-de-guerre)
Règle inchangée : chaque OP a un critère d'entrée, un livrable, un critère de sortie. On ne saute pas, on ne parallélise que la piste annexe.

### OP-1 « SOCLE » — Table v3 (harnais purgé)  [~1 soirée, 2-3 h serveurs]
- Fix harnais D'UN BLOC dans maneuvers.py/op_arma : QRF spawn sur CHUTE DE GARNISON (plus d'esquive par contingence) + spawns/LZ à terre (plus de nage).
- Pré-enregistrement : « la loi ≥2-axes survit-elle au harnais propre ? » + fourchettes par manœuvre.
- Re-mesure 7 manœuvres × 16 ops → verdict, synthèse journal. **Sortie : baseline propre.**

### OP-2 « AUTOPSIE » — dissection v3 vs v2  [~1 h]
- Podium par familles, IC, track-record des prédictions mis à jour. Note de recherche courte (PDF eisvogel).

### OP-3 « MIROIR » — variation de défense en mesure  [~1 soirée]
- Porter les profils ennemis (pro/hardcore : skill+CHASSE+nombre) dans le harnais headless.
- Mesurer famille A (M1/M2/M5/M6) + M3 témoin vs pro ET hardcore (n=16).
- **Question décisive : le classement des manœuvres S'INVERSE-T-IL quelque part ?**
- GATE : inversion → OP-4. Pas d'inversion nulle part → le sélecteur est une constante, SAUTER OP-4 (résultat en soi).

### OP-4 « ARBITRE » — le sélecteur appris  [si gate OP-3 ouverte ; ~1-2 soirées]
- Apprendre contexte→manœuvre sur DONNÉES RÉELLES (v3 + variantes défense). Validation hold-out + pré-enregistrement.

### OP-5 « DJEBEL » — doctrine asymétrique codée  [~1-2 soirées]
- Redéfinir le succès à 1:N (objectif de raid + ratio d'attrition + survie force) — sans ça, aucun gradient.
- Coder 3 manœuvres asymétriques : EMBUSCADE/APPÂTAGE (exploiter la chasse), RAID ÉCLAIR, HARCÈLEMENT-DÉCROCHAGE.
- Les mesurer scriptées vs hardcore : si même scripté rien ne marche, le problème est mal posé (re-cadrer avant d'entraîner).

### OP-6 « FORGE » — le chasseur dans le sim GPU  [~2-3 soirées]
- Porter hunt+skill+nombre dans op_gpu. Calibration on-trajectoire PUIS validation multi-politiques anti-exploit (protocole ZERG).

### OP-7 « CREUSET » — curriculum d'apprentissage  [~1 semaine 3090]
- PPO avec curriculum pro→hardcore→nightmare, récompense asymétrique d'OP-5.
- HYPOTHÈSE PRÉ-ENREGISTRÉE (07/06) : le cerveau découvrira une forme d'APPÂTAGE (attirer la poursuite, détruire en détail) sans qu'on la code. Émergence = démonstration phare.
- **[directive Younes 07/06 — remplace le backlog « polish visuel », annulé]** Le cerveau doit COMPRENDRE ses actions, pas être maquillé :
  - **Engagement** : coût de changement d'action injustifié (anti-flicker appris) + actions à durée (semi-MDP : « bondir jusqu'au muret » = 1 décision qui court jusqu'à complétion/interruption justifiée).
  - **Gestion de l'effort** (économie des forces) : récompense à la force restante AU MOMENT du craquage + malus au sur-engagement sans nécessité ; ajout d'OBS d'effort (qui tire, depuis quand, état des escouades sœurs) — on ne peut doser que ce qu'on voit.
  - Garde-fou : nouveau cerveau = nouvelle validation pré-enregistrée vs baseline v3 ; koth_finetuned et la mesure restent intouchés.

### OP-8 « RETOUR AU RÉEL » — fine-tune + validation Arma  [~1-2 semaines, le vrai mur]
- Fine-tune sur rollouts Arma (16 serveurs, acc 4) vs pro ; validation pré-enregistrée n=32 vs hardcore.
- Leçon-manager appliquée : prédictions chiffrées AVANT, seuil d'échec accepté d'avance.

### Piste annexe (n'importe quand, ne bloque rien)
- Sessions visuelles Younes en pro/hardcore = données qualitatives (où ça meurt) pour OP-5/OP-7.
