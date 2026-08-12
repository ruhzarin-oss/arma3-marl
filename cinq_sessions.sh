#!/bin/bash
# CINQ SESSIONS, deux mesures chacune. Chaque session est un serveur NEUF : c est la seule
# facon de mesurer la variance ENTRE sessions.
cd /mnt/data/harmattan-sandbox/arma3server
for s in 1 2 3 4 5; do
  P=$(pgrep -f "port=6022" | head -1); [ -n "$P" ] && kill $P; sleep 4
  nohup setsid ./arma3server_x64 -config=/mnt/data/harmattan-sandbox/staging/serverGC.cfg \
    -profiles=/mnt/data/harmattan-sandbox/profilesGC -port=6022 -world=Stratis -autoInit \
    "-mod=@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment" \
    -serverMod=@LAMBS_Danger > /mnt/data/harmattan-sandbox/logs/bruit_s$s.out 2>&1 < /dev/null &
  echo "session $s lancee"
  for i in $(seq 1 60); do
    grep -q "HMT|BR|TERMINE" /mnt/data/harmattan-sandbox/logs/bruit_s$s.out 2>/dev/null && break
    sleep 10
  done
  echo "session $s finie"
done
P=$(pgrep -f "port=6022" | head -1); [ -n "$P" ] && kill $P
echo "CINQ SESSIONS TERMINEES"
