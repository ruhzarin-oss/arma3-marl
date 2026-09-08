#!/bin/bash
# PONTPLANE — CONTROLE DE PLOMBERIE du pont Plane <-> file. Ne touche NI Arma NI le GPU.
# Il prouve une seule chose, de bout en bout : une tache Plane devient un job, le job devient
# un run, le run rend un FIN.json, et le verdict remonte a la tache. Quelques secondes.
#
# Pourquoi un banc pour ca : parce que le projet a paye cinq fois un compteur qui mentait sans
# erreur. Une plomberie non eprouvee est un instrument non eprouve.
set -uo pipefail
R=$1; G=$2; JOB=$3; OUT=$R/g$G
mkdir -p "$OUT"
python3 - "$OUT" "$G" "$JOB" <<'PY'
import json, sys, time, os
out, g, job = sys.argv[1], int(sys.argv[2]), sys.argv[3]
J = json.load(open(job))
res = {"verdict": "OK", "graine": g, "banc": J.get("banc"),
       "plane": J.get("plane"), "horodatage": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "controle": "la chaine Plane -> file -> run -> FIN -> Plane est complete"}
json.dump(res, open(os.path.join(out, "resultat.json"), "w"), indent=1, ensure_ascii=False)
print("graine %d : OK" % g)
PY
