#!/bin/bash
# Arrêt propre de la nuit CMO : TERM au processus PYTHON ( pas au shell de tmux ), attente de la ligne « fin ».
P=$(pgrep -f "^.venv/bin/python cmo/endurance.py|/\.venv/bin/python cmo/endurance.py" | head -1)
[ -z "$P" ] && P=$(pgrep -f "python cmo/endurance.py" | while read p; do [ "$(cat /proc/$p/comm)" != "sh" ] && echo $p; done | head -1)
echo "python pid=$P ($(cat /proc/$P/comm 2>/dev/null))"; kill -TERM $P
for i in $(seq 1 40); do kill -0 $P 2>/dev/null || break; sleep 1; done
tail -n 1 $(ls -t /mnt/data/hmt/etat/cmo_nuit/*.jsonl | head -1) | cut -c1-160
tmux kill-session -t cmo_nuit 2>/dev/null; true
