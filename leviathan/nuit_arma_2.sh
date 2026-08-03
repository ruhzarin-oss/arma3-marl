#!/usr/bin/env bash
# nuit_arma_2.sh — A3 (sursis sous volume) puis A4 (eclaireur FIBUA, sur Stratis).
# Serveur neuf avant chaque etape ; chien de garde ; resultats en continu.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
J=/tmp/nuit_journal.txt

echo "" | tee -a "$J"
echo "##### A3 — SURSIS SOUS VOLUME DE FEU (Altis) #####" | tee -a "$J"
bash etape_arma.sh 2400 sonde_tau_volume.py --reps 6 --duree 60 --out tau_volume.json 2>&1 | tee -a "$J"
echo "A3 : code ${PIPESTATUS[0]}" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### A4 — ECLAIREUR FIBUA (Stratis) — REPERE, NE CERTIFIE PAS #####" | tee -a "$J"
# bascule de theatre : un seul serveur a la fois. Les pkill sont dans ce fichier sur
# disque : lances depuis une commande ssh, le motif se tuerait lui-meme.
pkill -f 'server_altis.cfg' 2>/dev/null
sleep 8
bash /mnt/data/harmattan-sandbox/launch_fob.sh >/dev/null 2>&1
for i in $(seq 1 40); do
  ss -tlnp 2>/dev/null | grep -q 5816 && break
  sleep 5
done
sleep 25
if timeout 90 python3 etat_stratis.py 2>&1 | tee -a "$J" | grep -q 'monde=Stratis'; then
  timeout -k 30 9000 bash eclaireur_fibua.sh 2>&1 | tee -a "$J"
  echo "A4 : code ${PIPESTATUS[0]}" | tee -a "$J"
  python3 agg_eclaireur.py 2>&1 | tee -a "$J"
else
  echo "!! pont Stratis muet — A4 non engage" | tee -a "$J"
fi

echo "" | tee -a "$J"
echo "===== NUIT ARMA 2 terminee $(date '+%H:%M') =====" | tee -a "$J"
echo "NUIT_ARMA_2_DONE" | tee -a "$J"
