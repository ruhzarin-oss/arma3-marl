#!/bin/bash
# ═══ LA SONDE D'UNITÉ ═══════════════════════════════════════════════════════════════
# ⟨prescrite par Fable, 17/08⟩ « Mesurer l unité statistique d un phénomène n est pas parier
# sur une cause. C est de la métrologie — le calibre sans lequel aucune sonde causale n a de
# puissance. » Elle ne parie sur RIEN : elle rend trois nombres — l unité, le taux de base,
# la stationnarité.
#
# SOCLE GELÉ : 1.13.0, commit db446bf. Aucune version ne bouge pendant cette sonde.
# RÉGIME : celui de la nuit — serveur NEUF par session, réveil natif, 6 prévols enchaînés.
# TAILLE : 12 sessions × 6 tirages = 72 tirages.
#
# STATISTIQUE ET SEUIL, ÉCRITS ICI AVANT DE TOURNER
#   p̂ = rouges totaux / 72.  Sous l hypothèse « unité = TIRAGE », les 12 proportions de
#   session varient d une binomiale : X² = Σ k(p_i − p̂)² / (p̂(1−p̂)) suit un χ² à 11 ddl.
#     · X² > 19,68  (p < 0,05) → L UNITÉ EST LA SESSION
#     · X² ≤ 19,68            → pas de surdispersion décelable → on traite comme TIRAGE
#   Les deux bandes PARTITIONNENT le domaine ⟨règle 18⟩.
#
# PUISSANCE, DÉCLARÉE AVANT ⟨cliquet neuf : une sonde sans puissance ne s exécute pas⟩
#   Effet fort (sessions quasi tout-vert ou tout-rouge, p̂≈0,3) → X² attendu ≫ 40 : détecté
#   quasi certainement. Effet faible (proportions de session à ±0,15 autour de p̂) → X²≈15 :
#   NON détecté. Cette sonde tranche un effet FORT ; un effet faible sortira « TIRAGE » à
#   tort, et c est écrit ici pour que personne ne lise le contraire plus tard.
#
# TÉLÉMÉTRIE ⟨règle de l empreinte du monde⟩ : la machine est PARTAGÉE. Un serveur
# `arma3server_dr64` (port 6082, autre session de travail) tourne. On le RELÈVE, on n y
# TOUCHE PAS. Une empreinte de monde qui ne liste pas ses co-locataires est incomplète.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/unite; mkdir -p $D
echo "socle : $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)  commit $(git rev-parse --short HEAD)" > $D/EMPREINTE.txt
for s in $(seq 1 12); do
  # ⚠️ ON NE TUE QUE CE QU ON A LANCE. Cliquet du 17/08 : sur machine partagée, le harnais
  # tue par PID enregistré, jamais par motif — le jour où l autre session renomme son
  # binaire, un `pkill` par motif tue sa nuit, ou la nôtre.
  if [ -f $D/mes_pids ]; then while read pid; do kill $pid 2>/dev/null; done < $D/mes_pids; fi
  : > $D/mes_pids
  sleep 3
  CO=$(pgrep -fa arma3server 2>/dev/null | grep -v x64 | wc -l)
  LOAD=$(cut -d' ' -f1 /proc/loadavg)
  echo "session $s  $(date +%H:%M:%S)  colocataires=$CO  load=$LOAD" | tee -a $D/JOURNAL.txt
  timeout 400 ./.venv/bin/python -u prevol.py 6 natif 45 > $D/s${s}.txt 2>&1
  pgrep -f arma3server_x64 > $D/mes_pids 2>/dev/null
  V=$(grep -c "vert=" $D/s${s}.txt); R=$(grep -ac "T5 IMMOBILE" $D/s${s}.txt)
  echo "  → session $s : $R rouges T5 sur 6" | tee -a $D/JOURNAL.txt
done
if [ -f $D/mes_pids ]; then while read pid; do kill $pid 2>/dev/null; done < $D/mes_pids; fi
echo "═══ SONDE D UNITE TERMINEE — $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
