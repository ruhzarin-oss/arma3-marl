# Pont CMO — voie 2 (fichiers + événement Lua)

Le moteur parle à **Command: Modern Operations 1.10** (build 1900.20, Steam, branche `public_beta_multiplayer`),
installé sous Windows dans `E:\SteamLibrary\steamapps\common\Command - Modern Operations`.
Pas de socket : le socket TCP n'existe que dans Command PE Standard. Pas d'automatisation de l'interface, pas de
pause : le jeu tourne en temps réel.

## La chaîne

| Sens | Chemin | Qui écrit |
|---|---|---|
| Aller | `Lua/hmt_pont/cmd_<n>.lua` | `cmo_labo.py` (un seul écrivain) |
| Retour | `ImportExport/hmt_r_<n>.inst` (JSON, texte dans `Comments`) | `ScenEdit_ExportInst`, depuis l'événement |
| Battement | `ImportExport/hmt_sync.inst`, à chaque seconde de jeu | idem |

L'événement `HMT_PONT` (déclencheur RegularTime, 1 s) lit la commande suivante et l'exécute sous `pcall`.
Le reçu porte le code : 0 exécutée, 1 erreur Lua, 2 ne compile pas, 3 refus.
Aucune ligne de console n'est utilisée en service : le limiteur de la 1.10 (3 envois, puis un toutes les 30 s)
vise la console.

## Poser le pont (une fois par scénario)

1. `python3 cmo/deployer.py` : copie `lua/hmt_pont.lua` et `lua/installer.lua` dans `Lua/hmt_pont/`, et écrit
   `hmt_config.lua`.
2. Dans CMO, ouvrir le scénario, puis taper une ligne dans la console Lua :
   `ScenEdit_RunScript('hmt_pont/installer.lua')`
3. Sauvegarder (Ctrl+S) et laisser le temps s'écouler (x1).

## Prouver

- `.venv/bin/python cmo/porte_cmo.py --controles` : le vrai Lua face à `faux_cmo.lua`, dans Lua 5.4 (lupa).
  19 tests, un par garde, et 3 mutants qui doivent être tués. Hors du jeu, en quelques secondes.
- `.venv/bin/python cmo/banc_pont.py` : dans le vrai CMO, avec des critères écrits d'avance (100 canaris, deux
  F-15C posés, déplacés puis retirés, une erreur volontaire, un reçu de 3000 lignes, 10 min d'endurance).
  S'il passe, il **certifie le build** ; `cmo_labo` refuse ensuite tout autre build (`strict=True`) tant que le
  banc n'a pas été relancé.

## Ce que seul CMO peut prouver (le banc le dira)

- `ScenEdit_ExportInst` depuis une action d'événement, et la taille maximale de `Comments`.
- `loadfile` dans le bac à sable de la 1.10 (sinon, relais par `ScenEdit_RunScript` ; la sonde de l'installateur
  le dit : `SONDE io dofile loadfile load os lecteur`).
- Le limiteur de la 1.10 ne touche pas les événements.
- `ScenEdit_AddUnit` avec `type='Air'` sur la base DB3000 v517, et la latence réelle.

## Le pont de juin (`cmo_bridge.py`, `cmo_bridge.lua`, `cmo_ping.lua`, `test_bridge.py`) est remplacé

Ces fichiers sont gardés pour l'historique. Il ne faut plus s'en servir, et voici pourquoi :
- ils écrivent par `io.open`, que la version Steam retire (sans réglage pour la rétablir) : ils étaient morts par
  construction ;
- `pcall(load(code))` avale l'erreur, puis marque la commande « exécutée » ;
- `send()` rend `False` aussi bien pour une panne que pour un refus ou une lenteur ;
- la numérotation vient du disque, pas de l'actuateur : après un rechargement du scénario, plus rien ne passe ;
- `test_bridge.py` ne faisait jamais tourner le Lua. Il reconnaissait un commentaire, et passait donc sur un ordre
  invalide (`{name=Hornet 1, ...}`).

## Limites

- Un seul CMO, avec l'écran allumé. Jeu en pause = plus de battement = `PontMort`, et c'est voulu.
- La branche bêta de Steam se met à jour toute seule : c'est pour ça que le build est certifié.
- La licence Steam (§3.1, §7.3) interdit l'usage commercial, académique, de recherche ou militaire sans accord
  écrit de l'éditeur.
