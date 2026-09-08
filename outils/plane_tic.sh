#!/bin/bash
# Un battement du pont Plane <-> file. Lance par la tache planifiee HMT_PLANE, toutes les 10 min.
# Ordre voulu : on REND d abord (liberer les taches finies), on POUSSE ensuite (la file est vide).
H=/mnt/data/hmt
exec >> $H/etat/plane.log 2>&1
echo "--- $(date -Is)"
python3 $H/depot/outils/plane_rend.py
python3 $H/depot/outils/plane_pousse.py
