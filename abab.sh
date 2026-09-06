#!/bin/bash
# ABAB — voir PRE_PARALLELISATION.md, ecrit AVANT ce script.
cd /home/younes/arma3-marl
exec > abab.log 2>&1
echo "orchestrateur demarre a $(date +%H:%M:%S)"

DEPART=$(ls -t ckpt_b0_g1/*.pt | head -1)
cp -f "$DEPART" /tmp/depart_para.pt
echo "point de depart de l instance 1 : $DEPART"
rm -rf ckpt_para_jetable && mkdir -p ckpt_para_jetable
rm -f /mnt/c/hmt_bridge/i1/cmd_*.sqf

bloc () {   # $1 = nom, $2 = duree s, $3 = charge (oui/non)
  echo "=== $1  $(date +%H:%M:%S)  charge=$3 ==="
  if [ "$3" = "oui" ]; then
    nohup ./.venv/bin/python -u harnais.py --instance 1 --barreau B0 --D 30 \
      --episodes 4000 --maj 24 --lr 3e-4 --beta 0.01 --graine 1 \
      --reprise /tmp/depart_para.pt --ckpt ckpt_para_jetable \
      > i1_$1.log 2>&1 < /dev/null &
    PID=$!
    echo "  harnais i1 lance, pid=$PID"
    sleep "$2"
    # ⚠️ ON TUE PAR PID. Un `pkill harnais` emporterait la graine 1 avec lui.
    kill "$PID" 2>/dev/null && echo "  harnais i1 arrete (pid $PID)"
    sleep 5
  else
    sleep "$2"
  fi
  echo "=== $1 fini $(date +%H:%M:%S) ==="
}

bloc A1 1200 non
bloc B1 1200 oui
bloc A2 1200 non
bloc B2 1200 oui
echo "orchestrateur fini a $(date +%H:%M:%S)"
