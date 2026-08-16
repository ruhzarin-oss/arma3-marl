#!/bin/bash
# ═══ LE COMPLEMENT — atteindre 67 EPISODES VALIDES par passe ══════════════════════════
# ⟨AMENDEMENT_NATIF.md § A⟩ La porte donne ~4 % de prevols rouges de cause assignable. Le
# harnais lance 67 fois, il ne rend donc pas 67 episodes. Les manquants se rejouent ICI,
# AVANT l ouverture du moindre npz. Une passe sous 67 valides n est PAS citable.
#   usage : complement.sh <bras>       (natif | politique)
BRAS=${1:-natif}
D=/mnt/data/$BRAS
cd /home/younes/arma3-marl || exit 1
mkdir -p "$D"
for PASSE in 1 2; do
  N=$(ls "$D"/p${PASSE}_e*.npz 2>/dev/null | wc -l)
  echo "═══ passe $PASSE : $N valides, il en manque $((67 - N)) ═══"
  K=1000
  while [ "$N" -lt 67 ]; do
    for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
    sleep 3
    rm -f /tmp/releve_live.npz
    timeout 330 ./.venv/bin/python banc_live.py "$BRAS" > "$D/p${PASSE}_e${K}.txt" 2>&1
    if [ -f /tmp/releve_live.npz ]; then cp /tmp/releve_live.npz "$D/p${PASSE}_e${K}.npz"; fi
    N=$(ls "$D"/p${PASSE}_e*.npz 2>/dev/null | wc -l)
    echo "  complement $K → $N/67  $(date +%H:%M)"
    K=$((K + 1))
    # garde-fou : si 30 tentatives ne comblent pas, c est le PREVOL qui a change de regime,
    # pas la malchance. On s arrete et on le dit.
    if [ "$K" -gt 1030 ]; then echo "  ⛔ 30 tentatives sans combler — le prevol a change de regime. ARRET."; exit 2; fi
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ COMPLEMENT TERMINE — 67 valides par passe ═══"
