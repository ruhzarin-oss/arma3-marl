#!/bin/bash
# LA NUIT DE L HESITATION — deux decodeurs, meme artefact, meme nuit, ENTRELACES.
# Predicat : PREDICAT_NUIT_HESITATION.md, ecrit avant le premier episode.
# ⚠️ ENTRELACES episode par episode, et MEME GRAINE D ACTION au meme rang : l appariement
# ecrase la variance, et aucune derive de la machine ne peut se confondre avec le decodeur.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/hesitation; mkdir -p "$D"
for i in $(seq 1 67); do
  for DEC in echantillon argmax; do
    F=$D/${DEC}_e${i}.txt
    if [ -f "$F" ] && grep -aq "BANC DE MONTAGE TERMINE" "$F"; then continue; fi
    for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
    sleep 3; rm -f /tmp/releve_live.npz
    HMT_SESSION="_h${DEC}e${i}" HMT_DECODEUR=$DEC HMT_GRAINE_ACT=$i HMT_TAU=1.0 \
      timeout 640 ./.venv/bin/python banc_live.py politique > "$F" 2>&1
    rc=$?
    [ "$rc" = "124" ] && echo "  ⛔ MINUTEUR MORDU — $DEC e$i" | tee -a "$D/journal.txt"
    [ -f /tmp/releve_live.npz ] && cp /tmp/releve_live.npz "$D/${DEC}_e${i}.npz"
    V=$(grep -ac "prevol VERT" "$F" 2>/dev/null)
    A=$(grep -a "APRES PREVOL" "$F" 2>/dev/null | tail -1 | cut -c1-45)
    echo "  $DEC e${i}/67  $(date +%H:%M)  vert=$V  $A" | tee -a "$D/journal.txt"
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ NUIT DE L HESITATION TERMINEE — $(date +%H:%M) ═══" | tee -a "$D/journal.txt"
