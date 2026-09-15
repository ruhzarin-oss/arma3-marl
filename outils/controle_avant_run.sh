#!/bin/bash
# Refuse de partir si un piege connu est present. Usage : controle_avant_run.sh <job.json>
#
# ! LES RESIDUS SONT PAR BANC, PAS ABSOLUS (08/09/2026).
# Le projet Drone tourne en parallele du projet Arma : son editeur Unreal est un OUTIL DE TRAVAIL,
# pas un residu. Un controle qui refuse tout job des qu'Unreal tourne bloquerait toutes les nuits
# Arma. Le job declare donc ce qu'il TOLERE ; ce qui n'est pas tolere reste un refus.
#   "tolere": ["UnrealEditor", "vmware-vmx"]
# Ce qui n'est jamais tolerable garde son refus : un client arma3_x64 vole le pont de l'instance.
set -u
H=/mnt/data/hmt; JOB=${1:-}; ERR=0
TL=/mnt/c/Windows/System32/tasklist.exe
[ -f $H/.temoin ] || { echo "REFUS: temoin absent, /mnt/data n'est pas le bon disque"; ERR=1; }
[ -n "$JOB" ] && [ -f "$JOB" ] || { echo "REFUS: job introuvable '$JOB'"; exit 1; }
python3 - "$JOB" <<'EOF' || ERR=1
import json,sys
j=json.load(open(sys.argv[1]))
for k in ("banc","graines","instance","plafond_s"):
    if k not in j: print("REFUS: champ manquant :",k); sys.exit(1)
# ! LA REGLE DE NON-SINGULARITE A DEUX FORMES, PAS UNE.
# Deux graines distinctes protegent d un monde particulier. Mais une VIGNETTE
# veut l inverse : le MEME monde rejoue, parce que l alea du moteur n est pas
# seme et qu un episode n est pas reproductible. Rejouer 20 fois la graine 7
# mesure l etendue des issues A MONDE FIXE - et sans ce chiffre, aucune
# comparaison a un episode unique n est attribuable.
# Ce qui reste interdit dans les deux cas : UN seul episode.
g=len(set(j["graines"])); r=int(j.get("repetitions",1))
if r<1: print("REFUS: repetitions vaut",r,", minimum 1"); sys.exit(1)
if g<2 and r<5:
    print("REFUS: episode singulier -", g, "graine(s) distincte(s) et", r, "repetition(s).")
    print("       il faut AU MOINS DEUX GRAINES DISTINCTES (il en manque", 2-g, ")")
    print("       OU repetitions >= 5 (il en manque", 5-r, ")")
    sys.exit(1)
EOF
B=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['banc'])" "$JOB")
[ -x "$H/depot/bancs/$B/lancer.sh" ] || { echo "REFUS: banc $B sans lancer.sh executable dans le depot"; ERR=1; }
[ -z "$(git -C $H/depot status --short bancs/$B outils)" ] || { echo "REFUS: bancs/$B ou outils/ non commites"; ERR=1; }

# --- residus : ce que le job ne tolere pas
TOL=$(python3 -c "import json,sys;print(' '.join(json.load(open(sys.argv[1])).get('tolere',[])))" "$JOB")
# --- le LABO (instance 9) : un serveur de plus change la charge du run. Refus, sauf "labo" tolere.
PL=$H/etat/labo_arma.pid
INSTJ=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('instance'))" "$JOB")
if [ -s "$PL" ] && [ "$INSTJ" != "9" ]; then
  PLABO=$(tr -dc 0-9 < "$PL")
  if "$TL" /FI "PID eq $PLABO" 2>/dev/null | grep -qi arma3server; then
    echo " $TOL " | grep -qi " labo " || { echo "REFUS: le serveur du labo tourne (PID $PLABO) et le job ne tolere pas \"labo\""; ERR=1; }
  fi
fi
SNAP=$("$TL" 2>/dev/null | grep -Eio 'UnrealEditor[A-Za-z-]*|vmware-vmx|arma3_x64\.exe' | sort | uniq -c | tr '\n' ' ')
for p in UnrealEditor vmware-vmx 'arma3_x64\.exe'; do
  nom=$(echo "$p" | sed 's/\\\.exe//')
  echo " $TOL " | grep -qi " $nom " && continue
  "$TL" 2>/dev/null | grep -Eqi "$p" && { echo "REFUS: $nom tourne et n'est pas dans \"tolere\" du job (voir C:\\hmt\\stop)"; ERR=1; }
done
[ -n "$SNAP" ] && echo "  charge concurrente au lancement : $SNAP"

# --- ATTEIGNABILITE : l issue visee est-elle seulement possible avec ces leviers ?
# ! LE DEFAUT LE PLUS COUTEUX DU PROJET (10 au 12/09/2026).
# 245 episodes ont tourne en arret=5. La phase 6 n etait jamais jouee, CHACAL_EXFILTRES restait a
# zero, et le critere de SUCCES exige six exfiltres sur dix. Le succes etait donc STRUCTUREMENT
# impossible : les 245 episodes sont sortis en ECHEC par construction, et 204 d entre eux etaient
# en realite des assauts reussis. Trois jours de travail ont porte sur l assaut en croyant porter
# sur la victoire.
# Une vignette reste un instrument legitime. Mais elle doit DIRE SON NOM : le job declare
# "vignette": 1 et assume que son issue ne sera jamais SUCCES. Sans cette declaration, refus.
python3 - "$JOB" <<'PY' || ERR=1
import json,sys
j=json.load(open(sys.argv[1]))
if j.get("banc") != "chacal": sys.exit(0)
arret = j.get("arret", 6); depart = j.get("depart", 1); vignette = j.get("vignette", 0)
manque = []
if arret < 6: manque.append(f"arret={arret} : la phase 6 EXFILTRATION n est pas jouee, donc exfiltres reste a 0")
eff = j.get("effectif", 10)
if arret >= 6 and eff < 1: manque.append(f"effectif={eff}")
if manque and not vignette:
    print("REFUS: ATTEIGNABILITE - l issue SUCCES est impossible avec ces leviers :")
    for m in manque: print("        .", m)
    print('        Si c est voulu, declare "vignette": 1 dans le job et assume que l issue ne sera jamais SUCCES.')
    sys.exit(1)
if manque and vignette:
    print("  vignette declaree : issue SUCCES hors d atteinte, c est assume (" + " ; ".join(manque) + ")")
if depart >= 3 and not vignette:
    print(f"  note : depart={depart}, les phases anterieures ne sont pas jouees (hors corpus, ecrit dans le journal)")
PY

LIBRE=$(df --output=avail -BG /mnt/data | tail -n 1 | tr -dc 0-9)
[ "${LIBRE:-0}" -gt 50 ] || { echo "REFUS: ${LIBRE:-?} Go libres, minimum 50"; ERR=1; }
# ⚠️ 15/09 : values[] N EST PAS UNE GARDE, c est MESURE. Un job demandant delai_porteur=150,
# absent de values[] = {45,60,90,120,180} dont le defaut est 45, a joue 150 : la ligne FINI porte
# |delai_porteur|150 et le lecteur a ACCEPTE. Rien dans la chaine n arrete une faute de frappe -
# ni le moteur, qui rend server.cfg verbatim, ni ce script, qui ne lisait jamais description.ext,
# ni lancer.sh. On AVERTIT donc, et on ne REFUSE PAS : refuser changerait le comportement du banc,
# et une valeur hors liste est parfois voulue. Le script sort toujours en 0, le `|| true` est une
# ceinture de plus - il ne doit JAMAIS empecher un job de partir.
python3 /mnt/data/hmt/depot/outils/verifier_valeurs.py "$JOB" 2>/dev/null || true
[ $ERR = 0 ] && echo "CONTROLE OK"
exit $ERR
