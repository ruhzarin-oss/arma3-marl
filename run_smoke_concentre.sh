#!/bin/bash
cd /home/younes/arma3-marl
echo "=== SMOKE concentre : M3 x concentre @ skilled, 1 op ==="
date
.venv/bin/python -u run_maneuver.py --maneuver M3 --geometry concentre --enemy skilled --smoke 2>&1
echo "=== SMOKE FINI ==="
date
