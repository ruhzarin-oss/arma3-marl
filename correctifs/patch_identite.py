#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-IDENTITE-LEVIERS
# Le 13/09 la campagne EXFIL a tourne six jobs qui jouaient tous la reference : la classe
# CHACAL_EXFIL avait ete posee A L INTERIEUR du bloc CHACAL_SOCLE dans description.ext, donc
# BIS_fnc_getParamValue rendait le defaut. Le server.cfg portait bien EXFIL = 1, et la ligne FINI
# rendait exfil|0. Personne ne les a compares.
# Le controle d identite existait pourtant, mais il ne regardait que six champs : graine, palier,
# bras, depart, tenir, arret, oracle. On le rend GENERIQUE : tout levier que le job declare et que
# la ligne FINI porte doit concorder. Un levier ajoute demain sera controle sans qu on y pense.
import re, sys
p = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "LEVIERS_CONTROLES" in s:
    print("  deja present"); sys.exit(0)

ancien_debut = s.index('python3 - "$OUT/resultat.json" "$G" "$PAL" "$BRAS_NOM" "$DEPART" "$TENIR" "$ARRET" "$ORACLE" <<\'PY\'')
ancien_fin = s.index("PY\n", s.index('print("  identite conforme au job'))+3
ancien = s[ancien_debut:ancien_fin]

nouveau = '''python3 - "$OUT/resultat.json" "$JOB" "$G" "$PAL" "$BRAS_NOM" "$TENIR" "$ARRET" <<'PY'
import json,sys
p,job,g,pal,bras,tenir,arret = sys.argv[1:8]
def egal(a,b):
    # SQF rend les entiers sans decimale, mais on compare en nombre quand les
    # deux cotes sont numeriques : un "6" face a "6.0" n est pas un ecart de
    # mission, et un faux REFUS coute un episode de trois heures.
    try: return float(a)==float(b)
    except (TypeError,ValueError): return str(a)==str(b)
d=json.load(open(p)); e=d.get("entete",{})
j=json.load(open(job))
ecarts=[]
# 1. l identite de base, celle qui manquait le 08/09 : le corpus avait ete lu comme « le plan
#    echoue » alors que le bras temoin tournait.
for cle,attendu in (("graine",g),("palier",pal),("bras",bras),("tenir",tenir),("arret",arret)):
    obtenu=str(e.get(cle,"?"))
    if not egal(obtenu,attendu): ecarts.append(f"{cle} demande {attendu}, joue {obtenu}")
# 2. LEVIERS_CONTROLES : tout levier que le job declare ET que la ligne FINI porte doit concorder.
#    Ajout du 13/09 : la campagne EXFIL a tourne six jobs qui jouaient tous la reference, parce que
#    la classe du parametre etait mal imbriquee dans description.ext. Le server.cfg disait 1, la
#    ligne FINI disait 0, et personne ne les comparait. Un levier ecrit n est pas un levier LU.
LEVIERS_CONTROLES = ("depart","effectif","appui_feu","accessible","feu_avant","mg_assaut",
                     "delai_porteur","appui_fixe","oracle","socle","tactique","ablation",
                     "banc_appui","placeur","exfil")
controles=[]
for cle in LEVIERS_CONTROLES:
    if cle not in j or cle not in e: continue   # levier absent du job, ou episode anterieur au champ
    if not egal(str(e[cle]),str(j[cle])): ecarts.append(f"{cle} demande {j[cle]}, joue {e[cle]}")
    else: controles.append(cle)
if ecarts:
    d["verdict"]="REFUSE"; d["cause_refus"]="EPISODE_NON_CONFORME_AU_JOB: "+" ; ".join(ecarts)
    json.dump(d,open(p,"w"),indent=1,ensure_ascii=False)
    print("  !! EPISODE REFUSE :", "; ".join(ecarts)); sys.exit(1)
print("  identite conforme au job : graine",g,"palier",pal,"bras",bras,"tenir",tenir,"arret",arret)
print("  leviers relus dans la ligne FINI :", ", ".join(f"{c}={j[c]}" for c in controles) if controles else "aucun")
PY
'''
s2 = s.replace(ancien, nouveau, 1)
if s2 == s:
    print("  !! substitution ratee"); sys.exit(1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : lancer.sh : le controle d identite relit TOUS les leviers dans la ligne FINI")
