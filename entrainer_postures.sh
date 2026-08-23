#!/bin/bash
# ENTRAINEMENT AVEC POSTURES — pre-inscription PREINSCRIPTION_POSTURES.md (b3626e1).
# Geste unique : NA = 13 au lieu de 10. Protocole identique, rien d autre ne change.
#
# ⚠️ ON APPELLE LE FICHIER, PAS LA FONCTION. `boucle.entrainer()` n est que la boucle
# d apprentissage : LA PORTE (G1/G2/G3, graines jamais vues) et le `torch.save` vivent sous
# `if __name__ == "__main__"`. Un appel par `python -c` entraine, n evalue rien, ne garde
# rien — et rend un « aucun fichier » qu on lirait comme un refus de la porte. C est ce que
# ma premiere version faisait, et je l ai lu comme un verdict pendant dix minutes.
# ⚠️ Une tache planifiee n a pas de terminal : sans redirection, sa sortie est perdue.
cd /home/younes/arma3-marl || exit 1
L=/mnt/data/postures.log
: > "$L"
export HMT_NA=13
export HMT_PT=/home/younes/arma3-marl/boucle_pol_13actions_2026-08-23.pt
{
echo "═══ debut $(date +%H:%M:%S) — NA=$HMT_NA — sortie $HMT_PT ═══"
./.venv/bin/python -u boucle.py 140
echo "═══ fin $(date +%H:%M:%S) ═══"
} >> "$L" 2>&1
