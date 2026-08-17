#!/bin/bash
# ═══ LES TROIS CORRECTIFS, ENCHAÎNÉS ═══════════════════════════════════════════════════
# 1 · seuil 23 m (justifié par principe : un placeur n'est jamais plus indulgent que le
#     test qu'il prépare — T5 attend 24 m) ······················· POSÉ, socle 2.1.0
# 2 · acte de tir sur un homme dans le mode SERVI ··············· POSÉ, socle 2.1.0
# 3 · porte rejouée, mêmes critères : 50 réceptions, ZÉRO faux-reçu
#
# Le smoke passe d'abord — trois leviers à vérifier (traverse, tir, et les cinq lieux) —
# et la porte ne se lance QUE s'il passe.
cd /home/younes/arma3-marl || exit 1
echo "═══ SMOKE $(date +%H:%M) ═══"
if ! ./.venv/bin/python -u smoke_placeur.py; then
  echo "⛔ SMOKE ÉCHOUÉ — la porte ne sera PAS lancée."; exit 2
fi
echo ""
echo "═══ PORTE $(date +%H:%M) — 50 réceptions, zéro faux-reçu exigé ═══"
HMT_SESSION="_PORTE2" ./.venv/bin/python -u prevol.py 50 natif 45
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ TERMINÉ $(date +%H:%M) ═══"
