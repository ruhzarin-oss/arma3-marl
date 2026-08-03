#!/usr/bin/env bash
# controle_nul_e6.sh — PORTE E6 : LA PORTE QUI REND LE JALON 1 VERT.
# L audit d ordre passe sur les six doctrines scriptees. Une doctrine ne lit AUCUNE
# observation : ses actions sont identiques, les graines sont identiques, le predicat utilise
# le verbe VRAI inchange. L ecart attendu n est pas « petit », il est EXACTEMENT 0,000.
# Toute valeur non nulle prouve que le chemin de permutation contamine l etat du monde.
# Un instrument qui n a pas prouve son zero ne mesure pas, il opine.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
echec=0
for d in frontal_delibere appui_mouvement debordement_simple debordement_double infiltration bonds_alternes; do
  echo "--- $d"
  timeout 1200 $PY audit_ordre.py --pilote "doctrine:$d" --graines 5 --base 1000 \
      --episodes 1024 --D 8 --pas 80 2>&1 | grep -vE "Warning|warn" | grep -E "ecart|ZERO|CONTAMINATION|prendre|infiltrer"
  [ ${PIPESTATUS[0]} -ne 0 ] && echec=1
done
echo ""
echo "=== VERDICT E6 ==="
if [ $echec -eq 0 ]; then
  echo "  >>> ZERO EXACT SUR LES SIX DOCTRINES. Le jalon 1 est VERT."
  echo "      L instrument a prouve son zero : il mesure, il n opine plus."
else
  echo "  >>> AU MOINS UNE DOCTRINE A BOUGE. Le jalon 1 n est PAS vert."
  echo "      Aucun verdict sur mission_v3.pt. On repare le chemin de permutation."
fi
echo "CONTROLE_NUL_DONE"
