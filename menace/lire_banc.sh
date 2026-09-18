#!/bin/bash
echo "jobs banc finis : $(grep -c 'FINI 2026-09-18_BANC_' /mnt/data/hmt/etat/file.log) / 5 ; en vol $(ls /mnt/data/hmt/queue/en_cours/ | wc -l)"
for d in /mnt/data/hmt/runs/2026-09-18_*; do
  [ -f $d/job.json ] && grep -q BANC-PERCEPTION $d/job.json || continue
  v=$(python3 -c "import json;print(json.load(open('$d/job.json'))['version'])")
  for g in $d/g*/; do
    [ -f $g/serveur.rpt ] || continue
    python3 - "$v" "$(basename $g)" "$g/serveur.rpt" <<'PY'
import re, sys
v, monde, f = sys.argv[1:4]
t = open(f, encoding="utf-8", errors="ignore").read()
vue = re.search(r'"CHACAL\|E\|banc_perception\|[^"]*\|ligne_de_vue\|([01])', t)
if ("CHACAL|E|banc_refuse|" in t) or (vue and vue.group(1) == "0"):
    print(f"{v:10s} {monde:4s} EXCLU : aucune ligne de vue vers la cible ( le banc mesurerait le relief )"); raise SystemExit
L = re.findall(r'"CHACAL\|E\|sonde_perception\|([^"]*)"', t)
def ch(s):
    p = s.split("|"); return {p[i]: p[i+1] for i in range(len(p)-1)}
if not L: print(v, monde, ": aucune ligne"); raise SystemExit
d = [ch(x) for x in L]
vus = [int(x["menaces_vues"]) for x in d]; con = [int(x["menaces_connues"]) for x in d]
camp = [int(x["menaces_camp"]) for x in d]; hom = [int(x["menaces_homme"]) for x in d]
prem = next((int(x["depuis"]) for x in d if int(x["menaces_connues"]) > 0), -1)
print(f"{v:10s} {monde:4s} {len(d):3d} mesures sur {d[-1]['depuis']:>3s} s : vues max {max(vus)} ( {sum(1 for x in vus if x>0)*100//len(vus)} % du temps ), "
      f"connues max {max(con)}, camp max {max(camp)}, homme max {max(hom)} ; premiere connaissance a {prem} s")
PY
  done
done
