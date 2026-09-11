#!/bin/bash
# lancer_labo.sh — démarre le serveur Arma du LABO (instance 9, mission Labo.Altis). Il ne mesure rien.
# Usage : bash /mnt/data/hmt/depot/labo/lancer_labo.sh
#
# ⚠️ LE LABO NE DOIT PAS CONTAMINER UNE MESURE. Un serveur de plus pendant un job change la charge
# du run sans le faire échouer : charge_au_lancement l'archive, il ne l'interdit pas. On refuse donc
# de démarrer tant qu'un job en cours ne déclare pas "labo" dans son champ "tolere".
# ⚠️ Arrêt : bash labo/arreter_labo.sh (à la main de Younes : le classifieur refuse à Claude les
# arrêts de processus).
set -uo pipefail
H=/mnt/data/hmt; D=$H/depot/labo; I=9
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
PROFIL=/mnt/c/Users/Younes/hmtech$I; PONT=/mnt/c/hmt_bridge/i$I; PIDF=$H/etat/labo_arma.pid
MPM="/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/MPMissions/Labo.Altis"
[ -f $H/.temoin ] || { echo "REFUS: témoin absent, /mnt/data n'est pas le bon disque"; exit 2; }

vivant() { "$PWSH" -NoProfile -Command "if (Get-Process -Id $1 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"; }

# 1. Déjà lancé ?
if [ -f "$PIDF" ]; then
  P=$(tr -dc 0-9 < "$PIDF")
  if [ -n "$P" ] && vivant "$P"; then
    echo "REFUS: le labo tourne déjà (PID $P). Arrêt : bash labo/arreter_labo.sh"; exit 2
  fi
fi

# 2. Des jobs en cours qui ne tolèrent pas le labo ?
python3 - "$H/queue/en_cours" "$I" <<'EOF' || exit 2
import glob, json, sys
d, inst = sys.argv[1], sys.argv[2]
refus = []
for f in sorted(glob.glob(d + "/*.json")):
    try:
        j = json.load(open(f))
    except Exception:
        refus.append(f.split("/")[-1] + " (illisible)")
        continue
    if str(j.get("instance")) == inst:
        continue                      # le banc pontmcp lui-même : c'est lui qui lance le labo
    if "labo" not in j.get("tolere", []):
        refus.append(f.split("/")[-1])
if refus:
    print("REFUS: jobs en cours qui ne tolèrent pas le labo :", " ".join(refus))
    print('       attendre la fin de la file, ou ajouter "labo" à leur champ "tolere"')
    sys.exit(1)
EOF

# 3. Le profil hmtech9, créé depuis le modèle s'il manque.
if [ ! -f "$PROFIL/server.cfg" ]; then
  mkdir -p "$PROFIL" && cp "$D/server.cfg.modele" "$PROFIL/server.cfg" && echo "profil hmtech$I créé"
fi
grep -q 'template = "Labo.Altis"' "$PROFIL/server.cfg" || { echo "REFUS: $PROFIL/server.cfg ne joue pas Labo.Altis"; exit 2; }

# 4. Déploiement PROUVÉ : la règle des bancs (le dépôt doit être ce qui tourne). Un `mv` échoue
# quand un serveur tient la mission ouverte ; on compare après coup, on n'annonce pas.
DEP=$D/mission.Altis
if ! diff -rq "$DEP" "$MPM" >/dev/null 2>&1; then
  rm -rf "$MPM.neuf"; cp -r "$DEP" "$MPM.neuf"; find "$MPM.neuf" -name '._*' -delete
  rm -rf "$MPM.vieux"; [ -d "$MPM" ] && mv "$MPM" "$MPM.vieux"
  mv "$MPM.neuf" "$MPM"; rm -rf "$MPM.vieux"
fi
diff -rq "$DEP" "$MPM" >/dev/null 2>&1 || { echo "REFUS: DÉPLOIEMENT NON PROUVÉ, la mission jouée différerait du dépôt"; exit 2; }
echo "mission Labo.Altis = dépôt (empreinte $(cd "$DEP" && find . -type f | sort | xargs cat | md5sum | cut -c1-12))"

# 5. Table rase du pont et du journal : une commande qui traîne serait rejouée dès cmd_1.
mkdir -p "$PONT"; rm -f "$PONT"/cmd_*.sqf "$PONT"/.tmp_*; rm -f "$PROFIL"/*.rpt

# 6. Lancement par WMI : le serveur survit à la fin de la session ssh.
mkdir -p /mnt/c/hmt/labo; cp "$D/lancer_labo.ps1" /mnt/c/hmt/labo/lancer_labo.ps1
R=$("$PWSH" -NoProfile -ExecutionPolicy Bypass -File 'C:\hmt\labo\lancer_labo.ps1' -Instance $I | tr -d '\r')
P=$(echo "$R" | sed -n 's/^PID \([0-9]*\)$/\1/p')
[ -n "$P" ] || { echo "ÉCHEC: lancement raté : $R"; exit 1; }
echo "$P" > "$PIDF"
echo "serveur du labo PID $P, port $((2402 + 10*I)), pont C:\\hmt_bridge\\i$I"

# 7. Prêt = un battement dans le RPT. Charger Altis prend une à deux minutes.
for s in $(seq 1 60); do
  sleep 5
  F=$(ls -t "$PROFIL"/*.rpt 2>/dev/null | head -n 1)
  if [ -n "$F" ] && grep -aq "\[LABO\] HMT_SYNC" "$F"; then
    grep -a "\[LABO\] fonctions version" "$F" | tail -n 1
    echo "LABO PRÊT en $((s*5)) s"; exit 0
  fi
  vivant "$P" || { echo "ÉCHEC: le serveur est mort au chargement (voir le RPT dans $PROFIL)"; exit 1; }
done
echo "ÉCHEC: pas de battement en 300 s (voir le RPT dans $PROFIL)"; exit 1
