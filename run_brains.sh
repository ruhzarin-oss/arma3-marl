#!/bin/bash
cd /home/younes/arma3-marl
pkill -9 -f ow_train_brain
sleep 2
rm -f brains.log
echo "===== CERVEAU A : knob =====" >> brains.log
.venv/bin/python ow_train_brain.py --arm knob >> brains.log 2>&1
echo "===== CERVEAU B : emergent =====" >> brains.log
.venv/bin/python ow_train_brain.py --arm emergent >> brains.log 2>&1
echo "===== FINI =====" >> brains.log
