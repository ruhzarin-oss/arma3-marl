#!/bin/bash
cd /home/younes/arma3-marl
.venv/bin/python -u run_maneuver.py --maneuver M3 --geometry standard --enemy skilled_react --smoke 2>&1
echo "=== SMOKE_REACT_FINI ==="
