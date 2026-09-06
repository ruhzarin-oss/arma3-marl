#!/bin/bash
# B0@60 — voir PRE_B0_60.md, ecrite AVANT ce script.
# Deux graines, UNE PAR INSTANCE, en parallele. L'instance 0 est laissee au client Arma
# (elle partage son dossier de pont avec lui ; les melanger serait la collision R2-bis).
cd /home/younes/arma3-marl
exec > nuit60.log 2>&1
echo "debut $(date +%H:%M:%S)"
DEPART=ckpt_b0/pt_001992.pt
echo "reprise depuis $DEPART (point certifie B0@30, graine 0)"
for i in 1 2; do
  R=$(ls -t /mnt/c/Users/Younes/hmtech$i/*.rpt | head -1)
  echo "instance $i : $(grep -c 'ETAT PRET' "$R") lignes PRET, sync=$(grep -o 'HMT_SYNC [0-9]*' "$R" | tail -1)"
done
rm -rf ckpt_b60_g0 ckpt_b60_g1

# graine 0 sur l'instance 1, graine 1 sur l'instance 2
nohup ./.venv/bin/python -u harnais.py --instance 1 --barreau B0 --D 60 \
  --episodes 3992 --maj 24 --lr 3e-4 --beta 0.01 --graine 0 \
  --reprise $DEPART --resemer --ckpt ckpt_b60_g0 > b60_g0.log 2>&1 < /dev/null &
echo "  graine 0 -> instance 1, pid=$!"
sleep 5
nohup ./.venv/bin/python -u harnais.py --instance 2 --barreau B0 --D 60 \
  --episodes 3992 --maj 24 --lr 3e-4 --beta 0.01 --graine 1 \
  --reprise $DEPART --resemer --ckpt ckpt_b60_g1 > b60_g1.log 2>&1 < /dev/null &
echo "  graine 1 -> instance 2, pid=$!"
sleep 120
echo ""; echo "--- apres 2 minutes ---"
echo "### graine 0 ###"; tail -5 b60_g0.log
echo "### graine 1 ###"; tail -5 b60_g1.log
