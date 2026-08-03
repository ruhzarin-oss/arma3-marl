#!/usr/bin/env bash
# juge_prof.sh — ETAPE (B) DE L ARCHITECTE : LE PROFESSEUR CHEZ LE JUGE EXTERNE.
# Aucune couture d observation : le debordement tourne nativement dans Arma via envelop_arma.
# Effectifs IDENTIQUES au gymnase : 4 attaquants contre 8 defenseurs.
# n=40, en 5 blocs de 8, pour verifier que l etendue inter-blocs reste binomiale.
# Le gymnase annonce 96,2 % d arrivee. Regle tripartite, intervalle de Wilson a 95 % :
#   borne basse >= 86 %  -> GYMNASE CREDIBLE
#   borne haute <  86 %  -> GYMNASE CONDAMNE
#   entre les deux       -> doubler a n=80
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
rm -f "$LEV"/juge_*.json
for bloc in 1 2 3 4 5; do
  for rep in 1 2 3 4 5 6 7 8; do
    n=$(( (bloc-1)*8 + rep ))
    echo "--- operation $n / 40 (bloc $bloc)"
    timeout 180 python3 poser_fob.py 8 2>&1 | tail -1
    timeout 180 python3 envelop_arma.py setup --theatre altis --nag 4 >/dev/null 2>&1
    timeout 600 python3 envelop_arma.py run --theatre altis --mode envelop --nag 4 \
        --steps 120 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out "juge_b${bloc}_r${rep}.json" 2>&1 | grep -E "FOB PRIS|ANÉANTIE|ÉCHEC" | tail -1
    timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done
echo ""
python3 juge_bilan.py
echo "JUGE_PROF_DONE"
