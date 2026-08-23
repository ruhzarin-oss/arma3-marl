#!/bin/bash
# POURQUOI LA PORTE NE PASSE PLUS — deux causes candidates, testees dos a dos.
#
# FAIT : l artefact du 13/08 rend 50,7 % avec le code d AUJOURD HUI — une bonne politique
# EXISTE dans ce monde. Ce n est donc pas le monde : c est l entrainement qui ne la trouve
# plus. Meme protocole, 140 iterations, 10 actions : 5,7 %, BATTU par la frontale (-7,1) et
# par le flanc (-28,6). La porte refuse, et elle a raison de refuser.
#
# Deux changements sont passes APRES l artefact :
#   16/08 b3a11cb  chirurgie du couvert (le monde)
#   17/08 e856a86  la recompense : `dprec - d` devient `dprec - 0,99 * d`
#
# ⚠️ PREDICTIONS ECRITES AVANT DE LANCER :
#   B1  a 420 iterations, recompense INCHANGEE, la porte passe (G1 positif contre les deux)
#   R1  a 140 iterations, γ = 1,0 (la recompense d avant le 17/08), la porte passe
#
#   B1 seul  -> l entrainement etait coupe trop tot, la recompense est saine
#   R1 seul  -> la correction du 17/08 a casse l apprentissage
#   les deux -> il faudra choisir sur autre chose que ce banc
#   aucun    -> ce n est ni le budget ni la recompense, et je ne saurai pas encore
#
# Raison de croire a B1 : la courbe MONTAIT ENCORE a l iteration 139 (15 -> 68 m). Ca
# ressemble a un entrainement coupe, pas a une recompense cassee.
cd /home/younes/arma3-marl || exit 1
export HMT_NA=10

L=/mnt/data/cause_budget.log; : > "$L"
export HMT_PT=/home/younes/arma3-marl/pol_budget420.pt
{ echo "═══ ARM B — 420 iterations, recompense INCHANGEE (γ=0,99) — $(date +%H:%M:%S) ═══"
  ./.venv/bin/python -u boucle.py 420
  echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
echo "B fini $(date +%H:%M)" >> /mnt/data/cause_journal.txt

L=/mnt/data/cause_recompense.log; : > "$L"
export HMT_GAMMA_PHI=1.0
export HMT_PT=/home/younes/arma3-marl/pol_recompense_ancienne.pt
{ echo "═══ ARM R — 140 iterations, γ=1,0 : la recompense d AVANT le 17/08 — $(date +%H:%M:%S) ═══"
  ./.venv/bin/python -u -c "import sys;sys.path.insert(0,'.');import boucle;print('  GAMMA_PHI effectif :', boucle.GAMMA_PHI)"
  ./.venv/bin/python -u boucle.py 140
  echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
echo "R fini $(date +%H:%M)" >> /mnt/data/cause_journal.txt
echo TERMINE >> /mnt/data/cause_journal.txt
