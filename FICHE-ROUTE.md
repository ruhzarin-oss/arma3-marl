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
