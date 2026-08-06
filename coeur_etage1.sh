#!/usr/bin/env bash
# BATTEMENT DE COEUR. Une panne silencieuse doit devenir bruyante — regle du 06/08.
while pgrep -f "agent_complet.py --champ" >/dev/null; do
  G=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null | tail -1)
  L=$(grep -c "palier" /home/younes/arma3-marl/RESULTAT_ETAGE1_CHAMP.log 2>/dev/null)
  echo "$(date +%H:%M) gpu[$G] paliers=$L charge=$(cut -d\  -f1 /proc/loadavg)" >> /tmp/etage1_coeur.log
  sleep 300
done
echo "$(date -Is) plus aucun run — coeur arrete" >> /tmp/etage1_coeur.log
