#!/bin/bash
H=/mnt/data/hmt; date +%H:%M
for c in PORTEE FO VO BANC3 P2N; do n=$(ls $H/queue/faits 2>/dev/null | grep -c "_${c}_"); e=$(ls $H/queue/en_cours | grep -c "_${c}_"); f=$(ls $H/queue/*.json 2>/dev/null | grep -c "_${c}_"); r=$(ls $H/queue/refuses | grep -c "_${c}_.*json$"); [ $((n+e+f+r)) -gt 0 ] && echo "$c : faits $n ; en cours $e ; en file $f ; refuses $r"; done
echo "depot : $(git -C $H/depot log -1 --format='%h %ad' --date=format:'%H:%M') ; sale bancs/outils : $(git -C $H/depot status --short bancs/ outils/ | wc -l) ; disque libre : $(df -h /mnt/data | tail -n 1 | awk '{print $4}')"
