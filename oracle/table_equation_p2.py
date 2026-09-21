"""Construit la table de l equation P2 : une ligne par episode de phase 2 accepte, toutes campagnes.
Deux familles de colonnes, qu on ne melange pas :
  - OBSERVABLES : ce que l Architecte sait au moment de choisir ( ligne de decision, champs perceptifs ) ;
  - MONDE : le contexte, connu de nous mais PAS de l Architecte ( verite, Oracle, type de menace, campagne ).
Les champs « verite_* » sont interdits dans l equation de l Architecte : ils decrivent le monde, pas sa perception.
Issue : compromission a la fin de la phase 2. Les episodes sans ligne de decision sont gardes et marques
( atteint_decision = 0 ) : l equation de decision ne les utilise pas, mais leur taux est rapporte."""
import csv, glob, json, os, re
H = "/mnt/data/hmt"
EXCLUES = re.compile(r"^(CONTROLES-ORACLE|FUMEE-|VALIDITE-GRAINES)")   # controles ( teleport, patrouille forcee ) et fumees
RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')
OBS = ["alarme", "depuis_alarme", "compromis_avant", "vivants_avant", "defenseurs_connus", "vehicule_vu", "menace_percue",
       "menaces_vues", "menaces_connues", "distance_menace", "erreur_position", "menace_mobile", "vue_depuis",
       "vehicule_connu", "menace_mobile_vue", "moteur_entendu", "distance_moteur", "moteur_allume", "vue_vehicule",
       "n_vues_menace", "moteur_depuis_fenetre", "menaces_camp", "menaces_homme"]


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def num(x):
    try: return float(x)
    except Exception: return None


rows, vus = [], set()
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    try: j = json.load(open(jf))
    except Exception: continue
    if not j.get("menace_p2") and j.get("vignette") != 2: continue
    c = j.get("campagne", "?")
    if EXCLUES.match(c): continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        w = int(re.search(r"/g(\d+)", d).group(1))
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        m = RX_FIN.search(t)
        if not m: continue
        cle = (c, w, j.get("situation"), j.get("traversee"), j.get("oracle_cmd"), j.get("oracle_b"), j.get("oracle_delta"),
               j.get("menace_p2"), j.get("avant"), j.get("balayage"), j.get("portee_son"))
        # ! Pas de deduplication ici : le moteur est STOCHASTIQUE ( un rejeu de la meme graine change d issue, et meme
        # de verdict - vu sur ORACLE-P2 le 20/09 ). Chaque episode accepte est un tirage independant ; l unite est le
        # dossier d episode. La regle « premier accepte » servait a ne pas surponderer une case dans une lecture
        # d effet equilibree ; ici on ajuste une fonction, et le decoupage par monde protege la validation.
        r_id = os.path.basename(os.path.dirname(jf)) + "/" + os.path.basename(os.path.dirname(d))
        if r_id in vus: continue
        vus.add(r_id)
        dec = [champs(x) for x in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]
        dec = [x for x in dec if x.get("point") == "TRAVERSEE"]
        sit = [champs(x) for x in re.findall(r'"CHACAL\|E\|situation\|([^"]*)"', t)]
        sit = [x for x in sit if x.get("phase") == "2"]
        carte = re.search(r'CHACAL\|O\|carte\|[^"]*\|cases_routieres\|(\d+)\|', t)
        r = dict(episode=r_id, campagne=c, monde=w, situation=j.get("situation"), option_job=j.get("traversee"),
                 oracle=int(j.get("oracle_cmd") or 0), oracle_b=j.get("oracle_b"), oracle_delta=j.get("oracle_delta"),
                 jour=j.get("jour"), menace_p2=j.get("menace_p2"), avant=j.get("avant"), balayage=j.get("balayage"),
                 portee_son=j.get("portee_son"), types="+".join(sorted({s.get("type", "") for s in sit})),
                 cases_routieres=int(carte.group(1)) if carte else None,
                 compromis=int(m.group(4)), alarme_fin=int(m.group(5)), vivants_fin=int(m.group(3)), issue=m.group(2),
                 atteint_decision=int(bool(dec)))
        if dec:
            x = dec[0]
            r["option"] = num(x.get("choix"))
            r["decideur"] = x.get("decideur")
            for k in OBS:
                src = {"compromis_avant": "compromis", "vivants_avant": "vivants"}.get(k, k)
                r[k] = num(x.get(src))
            r["verite_distance_menace"] = num(x.get("verite_distance_menace"))   # MONDE, interdit a l Architecte
            r["verite_menaces"] = num(x.get("verite_menaces"))
        else:
            r["option"] = j.get("traversee")
        rows.append(r)
cols = sorted({k for r in rows for k in r})
os.makedirs(f"{H}/equation/p2", exist_ok=True)
with open(f"{H}/equation/p2/table_p2.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
from collections import Counter
print(f"{len(rows)} episodes ; atteint la decision {sum(r['atteint_decision'] for r in rows)} ; compromis {sum(r['compromis'] for r in rows)}")
print("par campagne :", dict(Counter(r["campagne"] for r in rows)))
print("mondes :", sorted({r["monde"] for r in rows}))
print("options :", dict(Counter(r.get("option") for r in rows)))
print("champs perceptifs presents ( sur les episodes a decision ) :",
      {k: sum(1 for r in rows if r.get(k) is not None) for k in ("moteur_entendu", "menace_mobile_vue", "moteur_depuis_fenetre", "distance_moteur", "n_vues_menace", "menace_percue", "distance_menace")})
