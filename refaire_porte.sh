#!/bin/bash
# ═══ REJOUER LA PORTE SUR UN SOCLE SAIN ⟨21/08⟩ ══════════════════════════════════════════
# La porte du 20/08 tournait avec `_m` orpheline : le placeur plantait sur sa ligne de
# retour, 102 erreurs sur cinq lots. Son verdict ne tient pas.
# ⚠️ LES TAMPONS D ABORD : ils sont sur le socle 5.4.0, la porte tournera sur 5.5.0 —
# la ligne 4 exige la MEME version des deux cotes. Cinq sabotages, puis la porte.
cd /home/younes/arma3-marl || exit 1
J=/mnt/data/refaire_porte.txt; : > $J
dire() { echo "$(date +%H:%M) $*" | tee -a $J; }
dire "socle $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)  commit $(git rev-parse --short HEAD)"
# ── archiver l ancienne porte avant que les noms ne soient reutilises
mkdir -p /mnt/data/preuves/2026-08-20_porte_invalidee
cp -p /mnt/data/porte/* /mnt/data/preuves/2026-08-20_porte_invalidee/ 2>/dev/null
dire "ancienne porte archivee"
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
dire "═══ LES CINQ SABOTAGES sur le hash neuf ═══"
bash six_sabotages.sh >> $J 2>&1
dire "tampons ecrits :"
cat /mnt/data/sabotages6/TAMPONS.txt | tee -a $J
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
dire "═══ LA PORTE, cinq lots de douze ═══"
bash porte_lots.sh >> $J 2>&1
dire "═══ TERMINE ═══"
