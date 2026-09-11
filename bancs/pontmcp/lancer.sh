#!/bin/bash
# BANC PONTMCP — le premier banc du LABO (Fable, 11/09/2026). Instance 9, mission Labo.Altis.
# Un passage = lancer le labo, jouer labo/banc_pontmcp.py, arrêter le labo.
# Écrit <run>/<S>/resultat.json. Contrat de run.sh : lancer.sh <run> <graine> <job.json> <sous-dossier>
#
# La « graine » ne change pas le monde : deux graines = deux fois le même contrôle, sur deux
# démarrages de serveur. C'est la forme que la règle de non-singularité prend ici.
# ⚠️ lancer_labo.sh REFUSE tant qu'un autre job en cours ne tolère pas "labo" : ce banc se joue
# file vide, ou avec des jobs qui l'acceptent.
set -uo pipefail
R=$1; G=$2; JOB=$3; SOUS=${4:-g$G}; OUT=$R/$SOUS
D=/mnt/data/hmt/depot/labo
mkdir -p "$OUT"
if ! bash $D/lancer_labo.sh > "$OUT/lancer.log" 2>&1; then
  echo "labo non lancé : $(tail -n 1 "$OUT/lancer.log")"
  echo '{"verdict":"REFUSE","cause":"LABO_NON_LANCE"}' > "$OUT/resultat.json"; exit 1
fi
python3 $D/banc_pontmcp.py > "$OUT/resultat.json" 2> "$OUT/banc.err"; RC=$?
bash $D/arreter_labo.sh >> "$OUT/lancer.log" 2>&1        # E5 l'a déjà tué ; ceci range le PID
F=$(ls -t /mnt/c/Users/Younes/hmtech9/*.rpt 2>/dev/null | head -n 1)
[ -n "$F" ] && cp "$F" "$OUT/serveur.rpt"
grep -q '"verdict"' "$OUT/resultat.json" || { echo "banc sans verdict, voir banc.err"; exit 1; }
echo "passage $G : $(grep -o '"verdict": "[A-Z]*"' "$OUT/resultat.json" | head -n 1)"
exit $RC
