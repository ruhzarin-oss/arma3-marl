#!/bin/bash
# Reconstruit la mission multiple depuis le banc chacaloracle ( jamais modifie ) et les sources du multiple.
set -euo pipefail
B=/mnt/data/hmt/depot/bancs/chacalmulti
python3 $B/construire_mission.py /mnt/data/hmt/depot/bancs/chacaloracle/mission.Altis $B/mission.Altis 8
mkdir -p $B/mission.Altis/multi
cp $B/sources/commun.sqf $B/mission.Altis/multi/commun.sqf
cp $B/sources/initServer.sqf $B/mission.Altis/initServer.sqf
echo "sqf : $(find $B/mission.Altis -name '*.sqf' | wc -l)"
