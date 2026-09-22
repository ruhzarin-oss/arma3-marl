"""Lecture des episodes de phase 2 : les armes de l Oracle ( lues dans le job ), la perception de l Architecte a la
decision, l option jouee, et l issue. Utilise pour l historique ET pour les iterations de l Oracle."""
import glob, json, os, re
from . import config as C

RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[0-9.]+\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
PERCEPTION = ["alarme", "depuis_alarme", "vivants", "defenseurs_connus", "vehicule_vu", "vehicule_connu", "menace_percue",
              "menaces_vues", "menaces_connues", "menaces_camp", "menaces_homme", "distance_menace", "menace_mobile",
              "vue_depuis", "moteur_entendu", "distance_moteur", "vue_vehicule", "n_vues_menace", "menace_mobile_vue",
              "moteur_depuis_fenetre", "compromis"]


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def num(x, d=None):
    try: return float(x)
    except Exception: return d


def admissible(j):
    """Un episode de phase 2 comparable a ce que joue l Oracle."""
    if j.get("banc") == "chacalmulti": return False   # un job multiple n est pas un episode : ses cellules reviennent en runs virtuels
    return (bool(j.get("menace_p2")) and int(j.get("depart", 0)) == 2 and int(j.get("arret", 0)) == 2
            and int(j.get("oracle_ctrl") or 0) == 0 and int(j.get("echelle", 100)) == 100
            and str(j.get("banc", "")).startswith("chacal"))


def lire_episode(jf, d, j):
    e = dict(dossier=os.path.basename(os.path.dirname(jf)) + "/" + os.path.basename(os.path.dirname(d)),
             campagne=j.get("campagne"), version=j.get("version"), graine=int(re.search(r"/g(\d+)", d).group(1)),
             option_imposee=int(j.get("traversee") or 0), verdict=None, erreurs=0, fin=False)
    for k in C.ARMES: e[k] = j.get(k, C.DEFAUTS[k])
    try: e["verdict"] = json.load(open(d + "resultat.json")).get("verdict")
    except Exception: return e
    try: t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
    except Exception: return e
    e["erreurs"] = len(RX_ERR.findall(t))
    m = RX_FIN.search(t)
    if m: e.update(fin=True, compromis=int(m.group(3)), alarme_fin=int(m.group(4)), vivants_fin=int(m.group(2)))
    dec = [champs(x) for x in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]
    dec = [x for x in dec if x.get("point") == "TRAVERSEE"]
    cj = [champs(x) for x in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]
    cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
    e["atteint_decision"] = int(bool(dec))
    e["choix_joue"] = int(num(cj[0].get("choix"), 0)) if cj else None
    if dec:
        for k in PERCEPTION: e["p_" + k] = num(dec[0].get(k))
    e["option"] = e["choix_joue"] or e["option_imposee"]
    return e


def episodes(filtre_campagne=None, admissibles_seulement=True):
    out = []
    for jf in sorted(glob.glob(f"{C.RUNS}/2026-*/job.json")):
        try: j = json.load(open(jf))
        except Exception: continue
        if filtre_campagne and not filtre_campagne(j.get("campagne", "")): continue
        if admissibles_seulement and not admissible(j): continue
        for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
            # ! amendement 6 ( 22/09 ) : un episode coupe par un arret DECIDE ( ordre de Younes, trace dans le journal )
            # n est pas un episode ; il est marque ARRET_MANUEL et sa case est rejouee par la reparation
            if os.path.exists(d + "ARRET_MANUEL"): continue
            out.append(lire_episode(jf, d, j))
    return out


def utilisables(E):
    """Pour apprendre : acceptes, fin de phase 2 lue, zero erreur SQF, option connue."""
    return [e for e in E if e["verdict"] == "ACCEPTE" and e["fin"] and e["erreurs"] == 0 and e.get("option") in (1, 2)]
