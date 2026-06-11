# GATE 0 — CMO : valider le pont Python <-> CMO (3 étapes)

**Pré-requis** : CMO installé (✅ /mnt/data/.../Command - Modern Operations), Proton (✅), mapping Z:\ = / (✅).
Le pont = jumeau du pont Arma : le Lua de CMO lit/écrit des fichiers dans `/tmp/cmo_bridge/` (vu `Z:\tmp\cmo_bridge\` côté jeu).

## Étape 0a — lancer CMO (TA session graphique, 1 clic)
Le lancement headless via SSH bute sur le confinement snap + l'autorisation X → à faire dans ta session :
Steam → **Command Modern Operations → Jouer**. (Proton est déjà assigné.) Si un Launcher s'affiche, "Play".

## Étape 0b — le TEST ATOMIQUE : le Lua de CMO écrit-il un fichier ? (LE point critique)
1. Dans CMO : charge **n'importe quel scénario** (le plus court : QuickBattle, ou un scénario "Down Bird" / "Fail Safe"). Mets-le en pause.
2. Ouvre la **console Lua** : menu **Editor → Lua Script Console** (ou "Special Actions").
3. Côté workstation (terminal/SSH), lance l'attente :
   `cd ~/arma3-marl/cmo && python3 cmo_bridge.py ping`
4. Dans la console Lua de CMO, **colle le contenu de `cmo_ping.lua`** et exécute.
5. Résultat attendu côté Python : `HMT_CMO_PING ok time=...`
   - ✅ → **le pont fichier marche** : io.open est autorisé, tout le reste suit. GATE 0 quasi acquis.
   - ❌ "AUCUN ping reçu" → io.open bloqué par la sécurité Lua : Game → Options → décocher "Lua security", réessayer. Si ça résiste : voie alternative (ScenEdit_ExportInst) à étudier.

## Étape 0c — le pont VIVANT (event récurrent)
Une fois 0b ✅ :
1. Dans l'éditeur de scénario : **Event → New** ; Trigger = **Regular Time** (intervalle 1 s) ; Action = **Lua Script**, colle `cmo_bridge.lua`.
2. Lance le scénario (non-pause).
3. Côté Python : `python3 cmo_bridge.py` (lecture d'état) → doit lister les unités Blue/Red avec lat/lon qui évoluent.
4. Test d'injection : `python3 -c "from cmo_bridge import CmoBridge; CmoBridge().send('ScenEdit_SpecialMessage(\"Blue\",\"pont OK\")')"` → le message s'affiche dans CMO.
   - ✅ les 3 (état lu + commande exécutée + unités qui bougent) → **GATE 0 CMO FRANCHI**.

## Ensuite (plan PLAN-CMO.md) : répertoire de 5-6 doctrines de frappe × 5 défenses → matrice → valeur de sélection → officier.
