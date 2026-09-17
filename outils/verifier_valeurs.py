# -*- coding: utf-8 -*-
"""AVERTIT quand un job demande une valeur absente de values[] dans description.ext.
N EMPECHE RIEN : mesure du 15/09, une valeur hors liste est JOUEE TELLE QUELLE, donc
refuser serait changer le comportement du banc. On se contente de le DIRE, fort.
Sort toujours en 0 : ce script ne doit jamais empecher un job de partir."""
import json, re, sys, os

CHAMPS = {
    "delai_porteur": "CHACAL_DELAI_PORTEUR", "effectif": "CHACAL_EFFECTIF",
    "assaut_x": "CHACAL_ASSAUT_X", "echelle": "CHACAL_ECHELLE",
    "palier": "CHACAL_PALIER", "depart": "CHACAL_DEPART", "arret": "CHACAL_ARRET",
    "tenir": "CHACAL_TENIR", "appui_feu": "CHACAL_APPUI_FEU", "oracle": "CHACAL_ORACLE",
    "tactique": "CHACAL_TACTIQUE", "ablation": "CHACAL_ABLATION", "placeur": "CHACAL_PLACEUR",
    "azimut": "CHACAL_AZIMUT", "obs": "CHACAL_OBS", "hmg": "CHACAL_HMG",
    "p1_attente": "CHACAL_P1_ATTENTE", "traversee": "CHACAL_TRAVERSEE", "obs_duree": "CHACAL_OBS_DUREE", "itineraire": "CHACAL_ITINERAIRE", "observation": "CHACAL_OBSERVATION", "controle_perception": "CHACAL_CONTROLE_PERCEPTION", "sonde": "CHACAL_SONDE", "exfil": "CHACAL_EXFIL", "delai_mode": "CHACAL_DELAI_MODE", "f_len": "CHACAL_F_LEN",
}

def declarees(ext):
    d = {}
    try: t = open(ext, encoding="utf-8", errors="ignore").read()
    except Exception: return d
    for m in re.finditer(r"class (CHACAL_\w+)\s*\{(.*?)\n\s*\};", t, re.S):
        v = re.search(r"values\[\]\s*=\s*\{([^}]*)\}", m.group(2))
        if v: d[m.group(1)] = [x.strip() for x in v.group(1).split(",") if x.strip()]
    return d

def main():
    if len(sys.argv) < 2: return 0
    job = sys.argv[1]
    banc = os.environ.get("CHACAL_BANC", "/mnt/data/hmt/depot/bancs/chacal")
    ext = os.path.join(banc, "mission.Altis", "description.ext")
    try: j = json.load(open(job, encoding="utf-8"))
    except Exception as e:
        print(f"  AVERT valeurs : job illisible ( {e} ) - controle non fait"); return 0
    d = declarees(ext)
    if not d:
        print(f"  AVERT valeurs : aucune liste values[] lue dans {ext} - controle non fait"); return 0
    n = 0
    for champ, cls in CHAMPS.items():
        if champ not in j or cls not in d: continue
        if str(j[champ]) not in d[cls]:
            n += 1
            print(f"  AVERT valeurs : {champ} = {j[champ]} est ABSENT de values[] de {cls} "
                  f"( declarees : {','.join(d[cls])} )")
    if n:
        print(f"  AVERT valeurs : {n} valeur(s) hors liste. MESURE DU 15/09 : une valeur hors liste")
        print(f"                  est JOUEE TELLE QUELLE, elle ne retombe PAS au defaut. Le job part.")
        print(f"                  Si c est voulu, tant mieux ; si c est une faute de frappe, rien")
        print(f"                  d autre dans la chaine ne l arretera.")
    return 0

sys.exit(main())
