#!/bin/bash
# ENTRAINEMENT AVEC POSTURES — pre-inscription PREINSCRIPTION_POSTURES.md (b3626e1).
# Geste unique : NA = 13 au lieu de 10. Protocole identique, rien d autre ne change.
cd /home/younes/arma3-marl || exit 1
export HMT_NA=13
export HMT_PT=/home/younes/arma3-marl/boucle_pol_13actions_2026-08-23.pt
echo "═══ debut $(date +%H:%M:%S) — NA=$HMT_NA — sortie $HMT_PT ═══"
./.venv/bin/python -c "
import sys; sys.path.insert(0,'/home/younes/arma3-marl')
import boucle
print('  vocabulaire effectif :', boucle.NA, 'actions')
boucle.entrainer(iters=140, n=256, lr=3e-4)
"
echo "═══ fin $(date +%H:%M:%S) ═══"
