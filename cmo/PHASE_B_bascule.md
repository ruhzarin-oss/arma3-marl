# Phase B — bascule vers le round-trip CMO réel

## Fait (côté Linux, prouvé)
- Protocole d'ancrage **batch** reconstruit : `cmo_anchor.py` (hôte) + `cmo_anchor.lua` (CMO).
- 3 leçons Arma intégrées : **compteur monotone** (zéro run perdu/rejoué, reprise auto),
  **watchdog anti-gel** (détecte le figement du battement `hb.json`, requeue), **lock anti-zombie**.
- Test à blanc `test_anchor.py` : gel injecté au 4e run → **10/10 aboutis, 0 perdu**. Critère Phase B tenu *à blanc*.
- Dossier-pont créé dans le partage existant : hôte `/mnt/data/MONDE/assets/fab_inbox/cmo_bridge`
  → **pas de reconfig .vmx** (sous-dossier du partage `fab_inbox` déjà monté).
- VM CMO **allumée**, VMware Tools répond. Verrou VT-x/VM levé.
- DOE Phase C pré-chargé dans `DOE_PHASE_C` : 8+AWACS vs {8,6,4,2} + témoin 2v2, N=10 (les 3 cellules de l'audit).

## À faire par Younes dans la VM (GUI, une seule fois)
1. Dans Windows, repérer la lettre de lecteur du dossier partagé `fab_inbox` (souvent `Z:` via
   `\\vmware-host\Shared Folders\fab_inbox`). Le sous-dossier `cmo_bridge` doit y apparaître.
2. Dans **cmo_anchor.lua**, caler `ANCHOR_DIR` sur `...\fab_inbox\cmo_bridge\` (drive letter réel),
   et `BLUE_CLASS`/`RED_CLASS`/AWACS sur les vraies classes DB du scénario.
3. CMO → **Game → Options → Lua security = OFF** (sinon `io.open` bloqué).
4. Ouvrir le **scénario d'ancrage** (une boîte vide, 1 zone de combat) et attacher `cmo_anchor.lua`
   comme action d'un **événement récurrent (~1/s sim)**. Lancer la sim (compression temps élevée).

## Puis (moi, sans intervention)
```
ssh younes@workstation 'cd ~/compose-embodiment/cmo && python3 cmo_anchor.py'
```
→ l'orchestrateur émet les 50 jobs, surveille, requeue au besoin, écrit `anchor_results.json`.
Critère Phase B **réel** : 10× de suite sans intervention, zéro run perdu.

## Note honnêteté
La *mécanique* du pont est prouvée (à blanc). La *construction d'unités* Lua (`ScenEdit_AddUnit`,
comptage survivants) reste à valider au 1er round-trip contre la DB CMO réelle — c'est la seule inconnue.
