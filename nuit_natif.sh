#!/bin/bash
# ═══ LA NUIT — NATIF x2, DOS A DOS ═══════════════════════════════════════════════════
# Predicat d acceptation : DEPOT_NATIF.md, ecrit AVANT le premier episode.
# Deux passes a l identique. Concordance exigee a moins de 10 points, sinon aucun des
# deux n est cite ⟨Fable : deux chiffres qui divergent sont un avertissement recu avant
# de batir dessus⟩.
cd /home/younes/arma3-marl || exit 1
mkdir -p /mnt/data/natif
for PASSE in 1 2; do
  echo "═══ PASSE $PASSE — $(date +%H:%M) ═══"
  for i in $(seq 1 67); do
    for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
    sleep 3
    rm -f /tmp/releve_live.npz
    timeout 330 ./.venv/bin/python banc_live.py natif > /mnt/data/natif/p${PASSE}_e${i}.txt 2>&1
    if [ -f /tmp/releve_live.npz ]; then cp /tmp/releve_live.npz /mnt/data/natif/p${PASSE}_e${i}.npz; fi
    V=$(grep -ac "prevol VERT" /mnt/data/natif/p${PASSE}_e${i}.txt 2>/dev/null)
    echo "  p${PASSE} e${i}/67  $(date +%H:%M)  prevol_vert=${V}  npz=$([ -f /mnt/data/natif/p${PASSE}_e${i}.npz ] && echo oui || echo NON)"
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ NUIT TERMINEE — $(date +%H:%M) ═══"
