#!/usr/bin/env bash
# calib_juge.sh — le cote JUGE de la courbe de calibration sur l issue.
# Meme manoeuvre, D=8 constant, on fait varier les attaquants. n=40 par point, blocs de 8.
# Criteres : CRITERES_CALIBRATION_ISSUE.md (162338a0f996a435). A=4 deja fait : 0 sur 38.
# INTERDIT : ne rien retoucher au bac a sable pendant cette mesure. On mesure l ecart.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
NAGS="${NAGS:-8 12 18 24}"
for A in $NAGS; do
  echo "########## A=$A contre D=8 ##########"
  rm -f "$LEV"/calib_A${A}_*.json
  for n in $(seq 1 40); do
    timeout 180 python3 poser_fob.py 8 >/dev/null 2>&1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag $A >/dev/null 2>&1
    timeout 600 python3 envelop_arma.py run --theatre altis --mode envelop --nag $A \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out "calib_A${A}_${n}.json" >/dev/null 2>&1
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
    if [ $((n % 8)) -eq 0 ]; then
      python3 calib_bilan.py "$A" partiel
    fi
  done
  python3 calib_bilan.py "$A"
done
echo ""
python3 calib_bilan.py TOUT
echo "CALIB_JUGE_DONE"
