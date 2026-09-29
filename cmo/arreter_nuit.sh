#!/bin/bash
# Arrêt propre de l'endurance CMO : TERM au processus PYTHON seulement ( ni au shell de tmux, ni au serveur tmux, dont
# la ligne de commande contient aussi « cmo/endurance.py » : 29/09, un TERM au serveur a fermé toutes les sessions ).
P=""
for p in $(pgrep -f "cmo/endurance.py"); do
    case "$(cat /proc/$p/comm 2>/dev/null)" in python*) P=$p; break;; esac
done
[ -z "$P" ] && { echo "aucune endurance en vol"; exit 0; }
echo "python pid=$P"; kill -TERM $P
for i in $(seq 1 40); do kill -0 $P 2>/dev/null || break; sleep 1; done
tail -n 1 $(ls -t /mnt/data/hmt/etat/cmo_nuit/*.jsonl | head -1) | cut -c1-160
