# Pont-socket C.4 — faire jouer un humain en SOLO (contourne le gel d'index)

**Problème résolu :** en solo/host, Arma gèle l'index des fichiers → l'actuateur `preprocessFile`
ne voit jamais les `cmd_N.sqf` ajoutés après le lancement. La DLL `hmt_ext_x64` lit le fichier au
**niveau OS** (`fopen`) via `callExtension` → l'actuateur reçoit quand même les commandes.

**Inchangé :** l'OUT (obs) sort toujours par `diag_log` → RPT (fonctionne en solo).

## Pièces
- `hmt_ext_x64.c` — la DLL (lit `Z:\tmp\hmt_bridge\cmd_<N>.sqf`, renvoie le SQF).
- `build_ext.sh` — compile + pose la DLL dans la racine client + crée `/tmp/hmt_bridge`.
- `harmattan_actuator_ext.sqf` — actuateur variante socket (callExtension au lieu de preprocessFile).
- `../live_arena_sp_socket.py` — l'arène, mais le pont écrit dans `/tmp/hmt_bridge`.

## Procédure (3 actions de ta part)

**1) Installer le compilateur (une fois) :**
```
sudo apt install -y gcc-mingw-w64-x86-64
```

**2) Compiler + déployer la DLL :**
```
bash ~/arma3-marl/socket_bridge/build_ext.sh
```
→ vérifie qu'il liste les exports `RVExtension` / `RVExtensionVersion`.

**3) Charger l'actuateur socket dans la mission cliente** (`…/Documents/Arma 3/missions/HarmattanKoth.Altis/init.sqf`) :
- copier `harmattan_actuator_ext.sqf` dans le dossier de la mission ;
- dans `init.sqf`, remplacer la ligne qui charge l'ancien actuateur par :
  ```
  call compile preprocessFileLineNumbers "harmattan_actuator_ext.sqf";
  ```
  (je peux faire ce câblage pour toi si tu veux.)

## Test
```
cd ~/arma3-marl && .venv/bin/python -u live_arena_sp_socket.py
```
…puis lance Arma (client, rendu 1060) → la mission HarmattanKoth en **Preview/host**.

**Ce qui prouve que ça marche (dans le RPT solo) :**
- `HARMATTAN_EXT version=hmt_ext 1.0 ...`  ← la DLL répond (extension chargée)
- `HARMATTAN_RECV cmd 1`, `2`, …          ← les commandes passent par la DLL
- côté Python : « PONT OK ! vivants … » puis les boucles de capture.

## Réserves d'ingénieur (à vérifier au 1er test, peuvent demander 1 itération)
- **Mapping `Z:`** : sous Proton, `Z:` = `/` par défaut → `Z:\tmp\hmt_bridge` = `/tmp/hmt_bridge`.
  Si la DLL ne lit rien, vérifier ce mapping (sinon poser `HMT_BRIDGE_WIN` dans l'env du jeu).
- **BattlEye** : en solo/éditeur il est inactif → les extensions custom chargent. (En MP officiel, non.)
- **Taille des cmd** : `callExtension` plafonne à ~10240 octets ; nos cmd sont petites. Si un jour
  une cmd dépasse, la DLL renvoie `__TOOBIG__` (à découper en chunks — non implémenté, non requis ici).
- **Voie dédié intacte** : rien ici ne touche la voie serveur-dédié (qui marche) ni les serveurs en cours.
