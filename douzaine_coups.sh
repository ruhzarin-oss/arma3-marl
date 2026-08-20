#!/bin/bash
# ═══ LA DOUZAINE DE VERIFICATION ⟨Fable, 20/08⟩ ════════════════════════════════════════
# La condition 3 du predicat NATIF — « le natif TIRE, >= 1 coup par episode en mediane » —
# n a pas pu etre levee sur les 107 episodes de la nuit : `banc_live.py` n enregistrait
# AUCUN coup. Le compteur est pose depuis (commit b492549).
# ⚠️ ON NE REJOUE PAS LES 107. Douze episodes suffisent a dire si les combats sont reels :
#   · si la mediane des coups attaquants est >= 1, la reserve s eteint VERS L AVANT et les
#     107 gardent leur asterisque — ils ne sont pas re-valides, ils sont ENCADRES ;
#   · si la douzaine CONTREDIT, alors le rejeu complet devient du.
# ⚠️ ATTENTE ECRITE AVANT : mediane des coups attaquants >= 1, et le canal declare doit
# valoir `sv_vz_preserve_10hz` dans les douze.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/douzaine; mkdir -p $D; : > $D/JOURNAL.txt
echo "socle $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)  commit $(git rev-parse --short HEAD)" | tee -a $D/JOURNAL.txt
for i in $(seq 1 12); do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
  sleep 3
  rm -f /tmp/releve_live.npz
  timeout 640 ./.venv/bin/python banc_live.py natif > $D/e$i.txt 2>&1
  rc=$?; [ "$rc" = "124" ] && echo "  ⛔ MINUTEUR MORDU e$i" | tee -a $D/JOURNAL.txt
  V=$(grep -ac "prevol VERT" $D/e$i.txt)
  C=$(grep -ao "COUPS  : .*" $D/e$i.txt | head -1)
  K=$(grep -ao "CANAL  : .*" $D/e$i.txt | head -1)
  echo "  e$i/12  $(date +%H:%M)  vert=$V  $C  $K" | tee -a $D/JOURNAL.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ DOUZAINE TERMINEE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
