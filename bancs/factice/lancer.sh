#!/bin/bash
# BANC FACTICE — il ne mesure RIEN. Il existe pour prouver la CHAINE d'orchestration
# (Prefect -> run.sh -> lancer.sh -> resultat.json -> FIN.json) sans allumer un serveur Arma.
# Aucun episode joue ici n'est une donnee : le verdict est ecrit en dur.
# Usage identique aux vrais bancs : lancer.sh <dossier_run> <graine> <job.json> <sous_dossier>
set -u
R=$1; G=$2; JOB=${3:-}; S=${4:-g$G}
mkdir -p "$R/$S"
sleep 20
cat > "$R/$S/resultat.json" <<JSON
{"verdict":"ACCEPTE","entete":{"issue":"SUCCES","graine":"$G","palier":"0","bras":"PLAN"}}
JSON
echo "factice : graine $G ecrite dans $R/$S/resultat.json"
