#!/bin/bash
# LA DETTE DE 13 MINUTES — le chiffre FONDATEUR du dossier (5,7 % a 140 iterations) n a
# jamais eu de lecture echantillonnee : a l epoque le torch.save vivait dans le if de la
# porte, et l artefact a ete jete. Sans cette piece, le registre garde une enigme resolue
# dont la preuve manque. P3 est deposee (8b687a7) : sa lecture echantillonnee sort AU-DESSUS
# DE 20 %, et le premier dossier se re-etiquette "artefact de budget + artefact de lecture".
cd /home/younes/arma3-marl || exit 1
export HMT_NA=10 HMT_SEED=0
export HMT_PT=/home/younes/arma3-marl/pol_140_reference.pt
L=/mnt/data/rejeu140.log; : > "$L"
{ echo "═══ REJEU 140 ITERATIONS — debut $(date +%H:%M:%S) ═══"
  ./.venv/bin/python -u boucle.py 140
  echo "═══ fin $(date +%H:%M:%S) ═══"; } >> "$L" 2>&1
echo TERMINE >> /mnt/data/rejeu140_journal.txt
