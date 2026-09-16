#!/bin/bash
# Lecture de FUMEE-DECISION-P5-16-09 contre les attentes ecrites dans ses jobs.
R=/mnt/data/hmt/runs
for r in $(grep -l '"campagne": *"FUMEE-DECISION-P5-16-09"' $R/*/job.json | xargs -n1 dirname | sort); do
  for g in $(ls -d $r/g*/ | xargs -n1 basename); do
    python3 - "$r" "$g" <<'PY'
import sys, re, json
r, g = sys.argv[1], sys.argv[2]
job = json.load(open(f"{r}/job.json")); res = json.load(open(f"{r}/{g}/resultat.json"))
t = open(f"{r}/{g}/serveur.rpt", "rb").read().decode("latin-1", "ignore")
err = len(re.findall(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type", t))
marq = "CHACAL|OK|decision|version|1" in t
dec = re.findall(r'CHACAL\|E\|decision\|([\d.]+)\|phase\|5\|point\|DELAI_PORTEUR\|options\|\[45,180\]\|choix\|(\d+)\|decideur\|(\w+)\|alarme\|(\d)\|depuis_alarme\|(-?\d+)\|compromis\|(\d)\|vivants\|(\d+)\|defenseurs_connus\|(\d+)\|verite_defenseurs\|(\d+)\|situation\|(\d+)', t)
pas = re.findall(r'CHACAL\|E\|premier_pas_assaut\|([\d.]+)', t)
porteurs = re.findall(r'CHACAL\|E\|porteur\|[^"]*\|delai\|(\d+)', t)
fin5 = re.search(r'CHACAL\|PH\|5\|ASSAUT\|fin\|([\d.]+)\|([A-Z_]+)', t)
site = re.search(r'CHACAL\|OK\|monde\|.*?\|site\|(\[[^\]]*\])', t)
duree = re.search(r'CHACAL\|FINI\|.*?\|duree\|(\d+)', t)
fini = re.search(r'CHACAL\|FINI\|([A-Z]+)\|([A-Z_]+).*?\|charges\|(\d)\|.*?\|vivants\|(\d+)', t)
ch = int(job["delai_porteur"])
ok = dict(sqf=err == 0, accepte=res["verdict"] == "ACCEPTE", marqueur=marq, une_decision=(len(dec) == 1) == bool(pas),
          avant_premier_pas=bool(dec and pas and float(dec[0][0]) <= float(pas[0])), choix=bool(dec) and int(dec[0][1]) == ch,
          porteurs=all(int(p) == ch for p in porteurs) and len(porteurs) > 0,
          alarme_menace=(job["menace_p5"] == 0) or (bool(dec) and dec[0][3] == "1"), fin_p5=bool(fin5))
print(f"{job['version']:26s} {g}  {'TOUT BON' if all(ok.values()) else 'ECHEC ' + str([k for k, v in ok.items() if not v])}")
print(f"      decision {dec[0] if dec else None}  premier_pas {pas[:1]}  porteurs {porteurs}  fin5 {fin5.groups() if fin5 else None}")
print(f"      site {site.group(1) if site else None}  duree {duree.group(1) if duree else None}  fini {fini.groups() if fini else None}")
PY
  done
done
echo "== sites de reference SITUATION-PAR-PHASE-16-09 ( P5 )"
for r in $(grep -l '"version": *"P5_ASSAUT_' $R/*/job.json | xargs -n1 dirname | sort); do for g in g5 g6; do echo "   $g $(grep -a -o 'CHACAL|OK|monde|.*|site|\[[^]]*\]' $r/$g/serveur.rpt | grep -o 'site|\[[^]]*\]' | head -1)"; done; done | sort -u
