#!/bin/bash
# LES DEUX VOCABULAIRES, DOS A DOS — 10 actions puis 13, meme protocole, meme jour.
# Pre-inscription PREINSCRIPTION_POSTURES.md (b3626e1).
#
# ⚠️ ON APPELLE LE FICHIER, PAS LA FONCTION. `entrainer()` n est que la boucle : LA PORTE
# (G1/G2/G3 sur graines jamais vues) et le `torch.save` vivent sous `__main__`. Un appel
# par `python -c` entraine, n evalue rien, ne garde rien — et rend un « aucun fichier »
# qu on lit comme un refus de la porte. Faute commise et corrigee le 23/08 a 18 h.
# ⚠️ L UN APRES L AUTRE : ils se partageraient le GPU et se ralentiraient l un l autre.
cd /home/younes/arma3-marl || exit 1
for NA in 10 13; do
  L=/mnt/data/vocab${NA}.log
  : > "$L"
  export HMT_NA=$NA
  export HMT_PT=/home/younes/arma3-marl/boucle_pol_${NA}actions_2026-08-23.pt
  {
  echo "═══ ${NA} ACTIONS — debut $(date +%H:%M:%S) ═══"
  ./.venv/bin/python -u boucle.py 140
  echo "═══ fin $(date +%H:%M:%S) ═══"
  } >> "$L" 2>&1
  echo "$NA actions fini $(date +%H:%M)" >> /mnt/data/vocab_journal.txt
done
echo TERMINE >> /mnt/data/vocab_journal.txt
