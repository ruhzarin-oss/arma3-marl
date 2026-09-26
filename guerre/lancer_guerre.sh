#!/bin/bash
# lancer_guerre.sh — demarre le serveur Arma de la guerre des iles (instance 10, GuerreIles.Malden).
# Copie de labo/lancer_labo.sh : memes refus (deja lance, jobs en cours qui ne le tolerent pas), meme deploiement
# PROUVE (la mission jouee = le depot), meme table rase du pont, meme attente du battement.
# ⚠️ Arret : bash guerre/arreter_guerre.sh (a la main de Younes).
set -uo pipefail
H=/mnt/data/hmt; D=$(cd "$(dirname "$0")" && pwd); DEPOT=$(dirname "$D"); I=10
PY=${PY:-/mnt/data/hmt/evogp/env/bin/python}
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
PROFIL=/mnt/c/Users/Younes/hmtech$I; PONT=/mnt/c/hmt_bridge/i$I; PIDF=$H/etat/guerre_arma.pid
MPM="/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/MPMissions/GuerreIles.Malden"
[ -f $H/.temoin ] || { echo "REFUS: temoin absent, /mnt/data n est pas le bon disque"; exit 2; }

vivant() { "$PWSH" -NoProfile -Command "if (Get-Process -Id $1 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"; }

# 1. Deja lance ?
if [ -f "$PIDF" ]; then
  P=$(tr -dc 0-9 < "$PIDF")
  if [ -n "$P" ] && vivant "$P"; then echo "REFUS: la guerre tourne deja (PID $P). Arret : bash guerre/arreter_guerre.sh"; exit 2; fi
fi

# 2. Des jobs en cours qui ne tolerent pas un serveur de plus ?
python3 - "$H/queue/en_cours" <<'PYEOF' || exit 2
import glob, json, sys
refus = []
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    try: j = json.load(open(f))
    except Exception: refus.append(f.split("/")[-1] + " (illisible)"); continue
    if "guerre" not in j.get("tolere", []): refus.append(f.split("/")[-1])
if refus:
    print("REFUS: jobs en cours qui ne tolerent pas la guerre :", " ".join(refus)); sys.exit(1)
PYEOF

# 3. La configuration de la guerre dans le profil hmtech10 ( server_guerre.cfg : le server.cfg du profil est celui de
#    l inventaire de Malden, on n y touche pas ), posee depuis le modele du depot a chaque lancement.
mkdir -p "$PROFIL" && cp "$D/server.cfg.modele" "$PROFIL/server_guerre.cfg"
grep -q 'template = "GuerreIles.Malden"' "$PROFIL/server_guerre.cfg" || { echo "REFUS: $PROFIL/server_guerre.cfg ne joue pas GuerreIles.Malden"; exit 2; }

# 4. La mission : le mission.sqm de Bohemia relu dans le jeu, puis deploiement PROUVE.
cd "$DEPOT" && "$PY" -m guerre.fabriquer_mission || { echo "ECHEC: mission.sqm illisible dans le jeu"; exit 1; }
DEP=$D/mission/GuerreIles.Malden
if ! diff -rq "$DEP" "$MPM" >/dev/null 2>&1; then
  rm -rf "$MPM.neuf"; cp -r "$DEP" "$MPM.neuf"; find "$MPM.neuf" -name '._*' -delete
  rm -rf "$MPM.vieux"; [ -d "$MPM" ] && mv "$MPM" "$MPM.vieux"
  mv "$MPM.neuf" "$MPM"; rm -rf "$MPM.vieux"
fi
diff -rq "$DEP" "$MPM" >/dev/null 2>&1 || { echo "REFUS: DEPLOIEMENT NON PROUVE, la mission jouee differerait du depot"; exit 2; }
echo "mission GuerreIles.Malden = depot (empreinte $(cd "$DEP" && find . -type f | sort | xargs cat | md5sum | cut -c1-12))"

# 5. Table rase du pont ; les anciens journaux du profil ( ceux de l inventaire du 24/09 ) sont ranges, pas effaces.
mkdir -p "$PONT"; rm -f "$PONT"/cmd_*.sqf "$PONT"/.tmp_*
mkdir -p "$PROFIL/rpt_anciens"; mv "$PROFIL"/*.rpt "$PROFIL/rpt_anciens/" 2>/dev/null || true

# 6. Lancement par WMI.
mkdir -p /mnt/c/hmt/guerre; cp "$D/lancer_guerre.ps1" /mnt/c/hmt/guerre/lancer_guerre.ps1
R=$("$PWSH" -NoProfile -ExecutionPolicy Bypass -File 'C:\hmt\guerre\lancer_guerre.ps1' -Instance $I -Monde Malden | tr -d '\r')
P=$(echo "$R" | sed -n 's/^PID \([0-9]*\)$/\1/p')
[ -n "$P" ] || { echo "ECHEC: lancement rate : $R"; exit 1; }
echo "$P" > "$PIDF"
echo "serveur de la guerre PID $P, port $((2402 + 10*I)), pont C:\\hmt_bridge\\i$I"

# 7. Pret = le battement ET Warlords pret (« guerre prete »). Charger Malden et Warlords prend une a trois minutes.
for s in $(seq 1 72); do
  sleep 5
  F=$(ls -t "$PROFIL"/*.rpt 2>/dev/null | head -n 1)
  if [ -n "$F" ] && grep -aq "\[LABO\] guerre prete" "$F"; then
    grep -a "\[LABO\] fonctions version\|\[LABO\] guerre prete" "$F" | tail -n 2
    echo "GUERRE PRETE en $((s*5)) s"; exit 0
  fi
  vivant "$P" || { echo "ECHEC: le serveur est mort au chargement (voir le RPT dans $PROFIL)"; exit 1; }
done
echo "ECHEC: Warlords pas pret en 360 s (voir le RPT dans $PROFIL)"; exit 1
