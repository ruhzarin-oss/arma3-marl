# PHASE 1 — FONDATION (figée le 2026-06-02)

## Ce qui est construit et VALIDÉ
- Pipeline MARL vectorisé complet : environnements NumPy (des milliers de mondes en parallèle) +
  entraînement MAPPO/PPO à politique partagée (PyTorch) sur la RTX 3090.
- Historique par run : `~/Bureau/Harmattan-entrainements/run_*/` (config.json, history.csv,
  courbes.png, GIF avant/après, model.pt) + `index.csv`.
- Visualisation : GIF animés (carte, agents, danger, objectif).
- Accès distant opérationnel (Mac <-> workstation via SSH/Tailscale) + mémoire commune.

## SOCLE DE RÉFÉRENCE : v1 (squad coopérative à rôles)
- Fichiers : `toy2d_v1.py` (env) + `train_harmattan_v1.py` (MAPPO conditionné par rôle).
- Résultat : **réussite 100 %, 0 perte** ; rôles (mitrailleur = suppression, médecin = réanimation)
  appris et UTILES.
- Preuve de l'apport des rôles : avec rôles 100 %/0 mort **vs** sans rôles 73 %/~1 mort (même carte).
=> C'EST LA BASE SUR LAQUELLE ON CONSTRUIT.

## Inventaire (~/arma3-marl/)
- `toy2d.py` / `train_harmattan.py` — v0 (squad plate, 1 objectif). MAPPO + ActorCritic réutilisables.
- `toy2d_v1.py` / `train_harmattan_v1.py` — **v1 RÔLES (référence)**.
- `toy2d_v3.py` / `train_harmattan_v3.py` — essais hiérarchie/chef (archivés).
- `toy2d_v4.py` / `train_harmattan_v4.py` — essai doctrine cohésion (archivé).
- `render_toy2d.py`, `MEMOIRE-COMMUNE.md`, `CLAUDE.md`, docs de référence.

## LEÇONS APPRISES (capital)
1. Le MARL coopératif PLAT (MAPPO partagé) marche bien et vite.
2. Les rôles ont de la valeur QUAND la tâche force la coordination (sinon inutiles).
3. Exploration : long PLATEAU puis PERCÉE soudaine (tâches coopératives à récompense rare).
4. Le CURRICULUM (facile -> dur) débloque les tâches dures.
5. **La HIÉRARCHIE (chef décideur) est DURE à l'échelle squad** : des soldats compétents
   contournent systématiquement le chef (v2 n'apprend pas ; v3 chef redondant ; v4 cohésion =
   amas inutile). Un « vrai chef » suppose des agents plus capables.
6. La cohésion FORCÉE agglutine les agents et leur fait oublier la mission.

## STATUT : PHASE 1 FIGÉE.
## REPRISE = trajectoire initiale (plan mise-en-place) -> **ÉTAPE 3 : CMDP / curseur λ**
(la vraie contrainte de survie, en remplacement de la pénalité de pertes codée en dur `cas_pen=0.5`).
Jalon ultérieur « AGENTIC » : mémoire (RNN) + communication apprise -> alors seulement, un vrai chef.
