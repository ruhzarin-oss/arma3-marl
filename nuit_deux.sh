#!/bin/bash
# ═══ LES DEUX NUITS, SOUS PROTOCOLE APPARIE ══════════════════════════════════════
# Rejeu apres VERDICT_COMPARAISON_RETIREE.md (f0c389b) : le natif recevait son ordre
# d assaut AVANT le prevol et marchait 60 a 180 s. Repare en 84eacf6 — les deux bras sont
# inertes jusqu au pas 0 et recoivent leur premier ordre au meme instant.
#
# ⚠️ NOUVEAUX DOSSIERS. Les nuits retirees restent en place : ce sont les preuves du
# verdict retire, et on n efface pas ce qu on a retire — on le garde a cote du neuf.
# ⚠️ MEME PREDICAT, MEMES n. DEPOT_NATIF.md (16/08) : 2 passes x 67 episodes par bras.
# Rien d autre ne change. Un rejeu qui change deux choses ne prouve ni l une ni l autre.
cd /home/younes/arma3-marl || exit 1
for BRAS in natif politique; do
  D=/mnt/data/${BRAS}2; mkdir -p "$D"
  for PASSE in 1 2; do
    echo "═══ $BRAS PASSE $PASSE — $(date +%H:%M) ═══" | tee -a "$D/journal.txt"
    for i in $(seq 1 67); do
      F=$D/p${PASSE}_e${i}.txt
      # reprenable par la MARQUE DE FIN, jamais par l existence du fichier
      if [ -f "$F" ] && grep -aq "BANC DE MONTAGE TERMINE" "$F"; then continue; fi
      for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
      sleep 3
      rm -f /tmp/releve_live.npz
      HMT_SESSION="_${BRAS}2p${PASSE}e${i}" timeout 640 ./.venv/bin/python banc_live.py $BRAS > "$F" 2>&1
      rc=$?
      [ "$rc" = "124" ] && echo "  ⛔ MINUTEUR MORDU — $BRAS p${PASSE} e${i} tronque" | tee -a "$D/journal.txt"
      [ -f /tmp/releve_live.npz ] && cp /tmp/releve_live.npz "$D/p${PASSE}_e${i}.npz"
      V=$(grep -ac "prevol VERT" "$F" 2>/dev/null)
      M=$(grep -ac "ESCOUADE MORTE AVANT LE DEPART" "$F" 2>/dev/null)
      A=$(grep -a "APRES PREVOL" "$F" 2>/dev/null | tail -1 | cut -c1-60)
      echo "  $BRAS p${PASSE} e${i}/67  $(date +%H:%M)  vert=$V  sans_esc=$M  $A" | tee -a "$D/journal.txt"
    done
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ LES DEUX NUITS SONT TERMINEES — $(date +%H:%M) ═══" | tee -a /mnt/data/natif2/journal.txt
