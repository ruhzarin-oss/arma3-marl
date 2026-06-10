#!/bin/bash
# Plafonne la RTX 3090 (GPU index 1) à 75% du TDP (420W) = 315W.
# Règle Younes 10/06 : tout run 3090 <= 75% de puissance.
set -e
echo "=== AVANT ==="
nvidia-smi -i 1 --query-gpu=name,power.limit,power.draw --format=csv,noheader
nvidia-smi -i 1 -pm 1            # persistence mode (le limit tient tant que le driver est chargé)
nvidia-smi -i 1 -pl 315          # 75% de 420W
echo "=== APRES ==="
nvidia-smi -i 1 --query-gpu=name,power.limit,power.draw --format=csv,noheader
echo "OK : 3090 plafonnee a 315W (75%)."
