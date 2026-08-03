#!/usr/bin/env bash
# Ferme le CLIENT Arma (jeu + lanceur, sous Proton) et laisse le serveur dedie tranquille.
#
# Passer par ce script et JAMAIS par une commande ssh directe : un `pkill -f <motif>`
# dont le motif figure dans sa propre ligne de commande se tue lui-meme. Arrive trois
# fois le 26/07.
echo "=== avant ==="
ps -eo pid,pcpu,rss,comm --sort=-pcpu | grep -iE 'arma|wine|proton' | head -8 \
  | awk '{printf "  %6s  %5s%%  %6.0f Mo  %s\n", $1, $2, $3/1024, $4}'

pkill -f 'arma3launcher.exe'  2>/dev/null
pkill -f 'Arma3_x64.exe'      2>/dev/null
pkill -f 'arma3.exe'          2>/dev/null
sleep 4
pkill -9 -f 'Arma3_x64.exe'   2>/dev/null
pkill -9 -f 'arma3launcher'   2>/dev/null
sleep 2

echo "=== apres ==="
if ps -eo comm | grep -qiE 'Arma3_x64.exe|arma3launcher'; then
  echo "  !! le client tourne encore"
else
  echo "  client ferme"
fi
echo "=== le serveur dedie doit rester debout ==="
pgrep -f 'arma3server_x64' >/dev/null && echo "  serveur dedie UP" || echo "  serveur dedie ABSENT"
echo "=== charge machine ==="
uptime | sed 's/^/  /'
