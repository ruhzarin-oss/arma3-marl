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

L'événement `HMT_PONT` (déclencheur RegularTime, 1 s) lit la commande suivante et l'exécute sous `pcall`,
**une seule par passage** : CMO applique certains effets entre deux passages (une suppression, par exemple), et
chaque commande doit voir le monde laissé par la précédente.
Le reçu porte le code : 0 exécutée, 1 erreur Lua, 2 ne compile pas, 3 refus.
Aucune ligne de console n'est utilisée en service : le limiteur de la 1.10 (3 envois, puis un toutes les 30 s)
vise la console.

## Poser le pont (une fois par scénario)

1. `python3 cmo/deployer.py` : copie `lua/hmt_pont.lua` et `lua/installer.lua` dans `Lua/hmt_pont/`, et écrit
   `hmt_config.lua`.
2. Dans CMO, ouvrir le scénario, puis taper une ligne dans la console Lua :
   `ScenEdit_RunScript('hmt_pont/installer.lua')`
3. Sauvegarder (Ctrl+S) et laisser le temps s'écouler (x1). Un scénario neuf démarre en pause : sans horloge,
   l'événement ne passe pas, et le pont ne bat pas.

Après un changement du Lua, pas besoin de console : `.venv/bin/python cmo/deployer.py --recharger` copie le Lua
et le fait relire à CMO par le pont lui-même (CMO relit bien le fichier, il ne garde pas l'ancien compilé).

## Prouver

- `.venv/bin/python cmo/porte_cmo.py --controles` : le vrai Lua face à `faux_cmo.lua`, dans Lua 5.4 (lupa).
  22 tests, un par garde, et 3 mutants qui doivent être tués. Hors du jeu, en quelques secondes.
- `.venv/bin/python cmo/banc_pont.py` : dans le vrai CMO, avec des critères écrits d'avance (100 canaris, deux
  F-15C posés, déplacés puis retirés, une erreur volontaire, un reçu de 3000 lignes, 10 min d'endurance).
  S'il passe, il **certifie le build** ; `cmo_labo` refuse ensuite tout autre build (`strict=True`) tant que le
  banc n'a pas été relancé.

## Ce que le vrai CMO a montré (build 1900.20, 28 et 29/09)

- **Le bac à sable de la 1.10 est plus fermé que celui de la 1.09.** La sonde de l'installateur rend
  `SONDE 0 0 0 0 1 2` : ni `io`, ni `dofile`, ni `loadfile`, ni `load` (seul `os` reste). En juillet, `dofile`
  marchait encore. Le pont lit donc ses commandes par `ScenEdit_RunScript`, qui relit bien le fichier à chaque fois.
- **`ScenEdit_ExportInst` écrit depuis une action d'événement,** et un reçu de 3000 lignes arrive entier.
- **Latence :** 0,96 s de médiane et 1,36 s au pire sur 100 allers-retours ; c'est un passage de l'événement.
- **Le limiteur de la 1.10 ne touche pas les événements :** 10 minutes à un canari toutes les 5 s, 0 perte.
- **La suppression d'une unité est différée au passage suivant :** `ScenEdit_DeleteUnit` rend vrai, mais
  `ScenEdit_GetUnit` et la liste du camp montrent l'unité jusqu'au passage d'après. La table rase se prouve donc par
  `HMT_recompter`, une autre commande, et le reçu doit venir d'un passage ultérieur.
- **`GetBuildNumber()`** rend `v1.10 - Build 1900.20` ; le pont en garde les nombres : `1.10.1900.20`.
- **`ScenEdit_AddUnit`** accepte `type='Air'`, avec le F-15C (dbid 3500, loadout 16934) de la base DB3000.
- **Coût :** quand aucune commande n'attend, CMO note chaque seconde une erreur « fichier absent » dans
  `Logs/LuaHistory_<date>.txt` (`RunScript` n'a pas de mode silencieux). Mesuré le 29/09 : 95 octets par seconde,
  soit environ 8 Mo par jour.
- **Banc réel passé le 29/09 (5 critères sur 5)** : le build 1.10.1900.20 est certifié
  (`/mnt/data/hmt/etat/cmo_banc/20260929_003400.json`).

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
