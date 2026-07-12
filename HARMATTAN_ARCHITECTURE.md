# HARMATTAN — l'armée qui se commande seule (architecture finie)

Une faction militaire Arma 3 qui s'organise seule : une **chaîne de commandement complète**, du soldat
au général, où chaque étage fait le geste juste sur le vrai serveur. Tout est validé LIVE sur `server_fob` (:3902).

## La chaîne de commandement (le cœur)

```
GÉNÉRAL (Qwen 2.5:14b)   stratégie de théâtre : quel FOB, RENFORCER/MASSER/QRF
   │
   ├─ COLONEL / CAPITAINE / LIEUTENANT   (récursif : découpe l'objectif en éventail pour ses subordonnés)
   │
   └─ SERGENT (commander.pt)   place ses 2 éléments (8 soldats) vers son objectif ; LAMBS exécute
         │
         └─ SOLDAT (agent)   corps appris + ORCHESTRATION (tactique) + EXÉCUTEURS (tir/grenade/flanc/fumi/suppr)
```

**Un seul patron récursif** : « je reçois un objectif, je le découpe pour mes N subordonnés ». Empilé, il donne
tous les grades. `army.py --branch` règle l'échelon : `3`=Lieutenant(24), `3,3`=Capitaine(72), `3,3,3`=Colonel(216).

## Les 3 étages de décision (validés live)
1. **Général** — `officer_live.py` : lit le SITREP réel → RENFORCE le bon FOB (discrimination totale, MAIN+OUTPOST).
2. **Commandement** — `army.py` / `commander.pt` : coordonne l'avance (loi prouvée : plus de force = plus profond ;
   8→72 m, 24→71 m, 72→42 m contre le vrai FOB fortifié).
3. **Tactique** — `orchestration_arma_voyant.pt` (10 features Arma → 5 tactiques) + `tactics_exec.sqf` (exécuteurs) :
   chaque soldat choisit ET fait sa tactique, en **composition** avec son réflexe.

## Le système intégré
`command_stack.py` — TOUT en une boucle : Général → hiérarchie récursive → sergents → soldats+orchestration.
Un lancement → l'assaut complet, tous les étages.

## Les scripts (chacun validé)
| Fichier | Rôle |
|---|---|
| `officer_live.py` | l'officier général Qwen (SITREP → ordres) |
| `officer_sit.sqf` | le SITREP en fonction (pont natif fiable) |
| `orch_features.sqf` | les 10 features Arma de l'orchestration (parité prouvée) |
| `orchestration_arma_voyant.pt` | la tête de sélection de tactique (+91) |
| `tactics_exec.sqf` | les 5 exécuteurs (composition avec le réflexe) |
| `commander.pt` | le sergent (commande 8) |
| `army.py` | la chaîne récursive (tous les grades par `--branch`) |
| `command_stack.py` | **le système intégré (assemblage final)** |
| `clash_live.py` | 2 camps équipés qui se battent (co-évolution pas 0) |
| `battle_eval.py` | le reward LIVE (pénétration + survie + attrition) |
| `coevo3.py` | la league (F.1, robustesse pire-cas +90) |

## Les grands findings
- **« Gagner » se décide au COMMANDEMENT, pas à la tactique.** L'orchestration seule stalle ; avec le commandant, ça avance.
- **Le proxy tactique ≠ la victoire.** S'entraîner à « choisir la bonne tactique » ne fait pas gagner l'assaut (F.2).
  Le vrai reward = l'issue live (`battle_eval`).
- **Plus de force = plus profond** (la récursion des grades scale) ; une position fortifiée se prend par la masse + le tempo.
- **Composition** : les tactiques s'AJOUTENT au réflexe (fumi/grenade/suppr), elles ne l'écrasent pas.
- **Pont NATIF** (TCP 5816) = le canal fiable ; toute réponse passe par `HMT_EMIT`, jamais `diag_log` seul.

## Ce qui reste (une seule brique, ouverte)
**Co-évolution réelle** : rendre le DÉFENSEUR adaptatif (son propre commandement qui apprend à contrer) + league
anti-oubli des deux côtés → les deux camps montent en niveau sans fin. On en a vu l'embryon (le FOB qui se renforce
et repousse l'assaut). C'est le front de RECHERCHE (GPU, multi-session), pas de l'ingénierie.

## Lancer
```bash
# prérequis : server_fob (:3902) up + qwen2.5:14b sur Ollama :11434
cd ~/arma3-marl
.venv/bin/python leviathan/command_stack.py --fob M1 --branch 3,3   # système intégré, compagnie de 72
.venv/bin/python leviathan/army.py --fob M1 --branch 3,3,3          # colonel (216)
.venv/bin/python leviathan/officer_live.py --cycles 6 --fob M1      # l'officier général seul
```
