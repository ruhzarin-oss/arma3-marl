# LEVIATHAN — une faction militaire qui s'organise seule

**Lancé le 26/06/2026.** Codename : le *Léviathan* de Hobbes = la société organisée vue comme **un seul corps**.

## Vision (A)
Une faction qui tient un territoire et **s'organise toute seule** : répartition des rôles, hiérarchie, réaction coordonnée aux menaces — sans script figé. « Société organisée » en habit militaire, sur Arma (le bon terrain : pas besoin d'économie/loi à greffer).

## Serveur dédié
- **server0** / SLOT 0 / port 2402 / Altis — hostname renommé **LEVIATHAN**
  (`/mnt/data/harmattan-sandbox/staging/server0.cfg`, sauvegarde `.bak.preleviathan`).

## Ce qu'on RÉUTILISE (on ne réinvente rien — leçon du 26/06)
- `occupation/laydown_altis.py` + `staff/occupation_*.json` — le territoire + la garnison (la faction qui vit).
- `staff/alert_engine.sqf` / `occupation_react2.py` — les sens (détection) + la QRF.
- `commander_env.py` / `train_commander.py` — le commandement **appris** niveau escouade (base de feu + manœuvre).
- `b1_commander.py` (seam) — exécution par LAMBS.
- `arma_bridge.py` — le pont.

## Ce qui est NOUVEAU (le seul ajout)
Un **allocateur de faction** au-dessus de l'escouade : il attribue les rôles
(garnison / patrouille / QRF / réserve) à travers les secteurs et **réalloue sous pression**
quand une menace apparaît. C'est la couche « organisation » qui manque — le reste existe déjà.

## Premier incrément (PROPOSÉ — à valider avec Younes avant de coder)
La faction tient 2-3 secteurs. Une menace surgit sur l'un.
La faction **réalloue une réserve** via une décision **apprise** au niveau faction,
comparée au baseline **alerte→QRF scripté**. Mesure : taux de tenue vs baseline.
Sandbox d'abord (motif `CommanderEnv`/`AssaultTerrain`), vrai Arma ensuite (server LEVIATHAN).
**NE PAS** reconstruire le commandant d'escouade ni l'occupation — seulement la couche au-dessus.

## Principe de marche
Converger : des incréments **finis** qui s'empilent. Valider sur le vrai Arma. Pas d'océan ouvert.
Quand on tourne en rond ou qu'on duplique l'existant → on stoppe et on recadre.
