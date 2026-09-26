#!/bin/bash
# arreter_guerre.sh — arrete le serveur de la guerre par son PID, APRES avoir verifie que ce PID est bien hmtech10.
# ⚠️ A la main de Younes (le classifieur refuse a Claude les arrets de processus).
set -uo pipefail
H=/mnt/data/hmt; PIDF=$H/etat/guerre_arma.pid
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
[ -f "$PIDF" ] || { echo "aucune guerre enregistree ($PIDF absent)"; exit 0; }
P=$(tr -dc 0-9 < "$PIDF")
[ -n "$P" ] || { echo "fichier de PID vide : retire"; rm -f "$PIDF"; exit 0; }
L=$("$PWSH" -NoProfile -Command "(Get-CimInstance Win32_Process -Filter 'ProcessId=$P').CommandLine" | tr -d '\r')
if [ -z "$L" ]; then echo "le PID $P ne tourne plus : fichier retire"; rm -f "$PIDF"; exit 0; fi
case "$L" in
  *arma3server_x64.exe*-name=hmtech10*) ;;
  *) echo "REFUS: le PID $P n est pas le serveur de la guerre : $L"; exit 2 ;;
esac
"$PWSH" -NoProfile -Command "Stop-Process -Id $P -Force"
sleep 3
rm -f "$PIDF"; echo "serveur de la guerre (PID $P) arrete"
