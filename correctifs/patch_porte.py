#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-PORTE-ATTEIGNABILITE
# Le defaut le plus couteux du projet n est pas une erreur de code, c est une erreur de methode :
# on mesure avant d avoir verifie que l instrument peut repondre.
#   245 episodes du 10 au 12/09 tournaient en arret=5. La phase 6 n etait jamais jouee, le compteur
#   d exfiltres restait a zero, et le critere de succes en exige six. Le SUCCES etait STRUCTUREMENT
#   impossible, et les 245 episodes sont sortis en ECHEC par construction. 204 d entre eux etaient
#   en realite des assauts REUSSIS.
# Cette porte rend cette erreur impossible a refaire en silence. Un job qui ne peut pas atteindre
# l issue qu il pretend mesurer doit le DECLARER. Une vignette reste permise - c est un instrument
# legitime - mais elle doit dire son nom.
import re, sys
p = "/mnt/data/hmt/depot/outils/controle_avant_run.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "ATTEIGNABILITE" in s:
    print("  deja present"); sys.exit(0)

ancre = 'LIBRE=$(df --output=avail -BG /mnt/data | tail -n 1 | tr -dc 0-9)'
if ancre not in s:
    print("  !! ancre disque absente"); sys.exit(1)

bloc = '''# --- ATTEIGNABILITE : l issue visee est-elle seulement possible avec ces leviers ?
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

'''
s2 = s.replace(ancre, bloc + ancre, 1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : controle_avant_run.sh : porte d ATTEIGNABILITE")
