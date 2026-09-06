#!/bin/bash
# On refait les points du barreau du site degele, effaces par une tache ONCE partie seule.
# ⚠️ PLUS DE `rm -rf` EN TETE DE SCRIPT : si ce lanceur repart par accident, il ne doit
# pas pouvoir detruire ce qu'il a produit. On refuse de demarrer si les points existent.
cd /home/younes/arma3-marl
exec > refaire_site.log 2>&1
echo "debut $(date +%H:%M:%S)"
for d in ckpt_site_g0 ckpt_site_g1; do
  if [ -n "$(ls $d/*.pt 2>/dev/null)" ]; then
    echo "REFUS : $d contient deja des points. Rien ne sera efface."; exit 1
  fi
  mkdir -p $d
done
./.venv/bin/python -u harnais.py --instance 1 --barreau B0 --D 30 --sites apprentissage \
  --episodes 2904 --maj 24 --lr 3e-4 --beta 0.01 --graine 0 \
  --reprise ckpt_b0/pt_001992.pt --resemer --transfert --ckpt ckpt_site_g0 \
  > site_g0.log 2>&1 < /dev/null &
A=$!; echo "  graine 0 -> instance 1, pid=$A"
sleep 5
./.venv/bin/python -u harnais.py --instance 2 --barreau B0 --D 30 --sites apprentissage \
  --episodes 2904 --maj 24 --lr 3e-4 --beta 0.01 --graine 1 \
  --reprise ckpt_b0_g1/pt_001992.pt --resemer --transfert --ckpt ckpt_site_g1 \
  > site_g1.log 2>&1 < /dev/null &
B=$!; echo "  graine 1 -> instance 2, pid=$B"
wait $A; wait $B
echo ""; grep -E "ARRET A ISSUE|^FIN :" site_g0.log site_g1.log
echo "fini $(date +%H:%M:%S)"
