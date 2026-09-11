#!/bin/bash
# arreter_labo.sh — arrête le serveur du labo par son PID, APRÈS avoir vérifié que ce PID est bien
# le serveur hmtech9 : Windows recycle les PID, celui du fichier peut désigner n'importe quoi.
# ⚠️ Le classifieur de Claude refuse les arrêts de processus : c'est à Younes de lancer ce script
# (ou au banc pontmcp, qui arrête le serveur qu'il a lui-même lancé).
set -uo pipefail
H=/mnt/data/hmt; PIDF=$H/etat/labo_arma.pid
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
[ -f "$PIDF" ] || { echo "aucun labo enregistré ($PIDF absent)"; exit 0; }
P=$(tr -dc 0-9 < "$PIDF")
[ -n "$P" ] || { echo "fichier de PID vide : retiré"; rm -f "$PIDF"; exit 0; }
L=$("$PWSH" -NoProfile -Command "(Get-CimInstance Win32_Process -Filter 'ProcessId=$P').CommandLine" | tr -d '\r')
if [ -z "$L" ]; then echo "le PID $P ne tourne plus : fichier retiré"; rm -f "$PIDF"; exit 0; fi
case "$L" in
  *arma3server_x64.exe*-name=hmtech9*) ;;
  *) echo "REFUS: le PID $P n'est pas le serveur du labo : $L"; exit 2 ;;
esac
"$PWSH" -NoProfile -Command "Stop-Process -Id $P -Force"
sleep 3
rm -f "$PIDF"; echo "serveur du labo (PID $P) arrêté"
