#!/bin/bash
# BARREAU DU SITE DEGELE — entrainement. Branche prevue par PRE_SITE_DEGELE.md :
# la sonde de vacance a ECHOUE (1/5 sur les deux graines), le barreau est vivant.
#
# ⚠️ DEUX FACONS DE PERDRE UNE NUIT, RENCONTREES TOUTES LES DEUX AUJOURD'HUI :
#  1. `nohup ... &` SANS `< /dev/null` : l'enfant garde l'entree standard de la session,
#     et la fin de la session WSL l'emporte. Constate a 14:50:54, a la seconde ou le
#     lanceur s'est termine. Les episodes etaient sains (15/15 et 10/10), juste tues.
#  2. Le lanceur qui rend la main : la tache planifiee se termine, l'arbre meurt.
#     On `wait` donc les deux enfants — tant que le lanceur attend, la tache vit.
cd /home/younes/arma3-marl
exec > nuit_site.log 2>&1
echo "debut $(date +%H:%M:%S)"
rm -rf ckpt_site_g0 ckpt_site_g1
./.venv/bin/python -u harnais.py --instance 1 --barreau B0 --D 30 --sites apprentissage \
  --episodes 5992 --maj 24 --lr 3e-4 --beta 0.01 --graine 0 \
  --reprise ckpt_b0/pt_001992.pt --resemer --transfert --ckpt ckpt_site_g0 \
  > site_g0.log 2>&1 < /dev/null &
A=$!; echo "  graine 0 -> instance 1, pid=$A"
sleep 5
./.venv/bin/python -u harnais.py --instance 2 --barreau B0 --D 30 --sites apprentissage \
  --episodes 5992 --maj 24 --lr 3e-4 --beta 0.01 --graine 1 \
  --reprise ckpt_b0_g1/pt_001992.pt --resemer --transfert --ckpt ckpt_site_g1 \
  > site_g1.log 2>&1 < /dev/null &
B=$!; echo "  graine 1 -> instance 2, pid=$B"
wait $A; echo "graine 0 finie $(date +%H:%M:%S)"
wait $B; echo "graine 1 finie $(date +%H:%M:%S)"
echo "fini $(date +%H:%M:%S)"
