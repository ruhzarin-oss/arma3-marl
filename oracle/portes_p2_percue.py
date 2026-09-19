"""Lecture UNIQUE de P2-PERCUE-19-09 ( criteres : oracle/CRITERES_P2_PERCUE.md et son amendement 1, ecrits avant ).
  python3 lire_p2_percue.py [--sans-monde N ...]
Portes Q1-Q8, puis le RAPPEL par le type ( doit contenir -0,369 ), puis la lecture PRINCIPALE par la perception
moteur_depuis_fenetre, puis les controles de sensibilite et l issue secondaire ( duree de la phase 2 )."""
import glob, json, os, random, re, sys
H = "/mnt/data/hmt"; CAMPAGNE = "P2-PERCUE-19-09"
RETIRES = [int(sys.argv[i + 1]) for i, a in enumerate(sys.argv) if a == "--sans-monde"]
MONDES_TOUS = [4, 5, 6, 7, 8, 9, 11, 12]
MONDES = [w for w in MONDES_TOUS if w not in RETIRES]
BRAS = {4: "PATROUILLE", 5: "POSTE"}; OPTIONS = {1: "TOUT_DE_SUITE", 2: "ATTENDRE"}
B, GRAINE, VERDICT = 10000, 20260919, -0.369
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
ATTENDUS = {"PATROUILLE": ["PATROUILLE_ROUTE"], "POSTE": ["POSTE_DE_CONTROLE"]}


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def entier(x, d=None):
    try: return int(float(x))
    except Exception: return d


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json") + glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), bras=BRAS.get(j.get("menace_p2")), option=j.get("traversee"),
                 avant=j.get("avant"), balayage=j.get("balayage"), verdict=None, erreurs=0)
        try:
            e["verdict"] = json.load(open(d + "resultat.json")).get("verdict"); t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: E.append(e); continue
        e["erreurs"] = len(RX_ERR.findall(t))
        dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]; dec = [x for x in dec if x.get("point") == "TRAVERSEE"]
        cj = [champs(m) for m in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]; cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
        sit = [champs(m) for m in re.findall(r'"CHACAL\|E\|situation\|([^"]*)"', t)]; sit = [x for x in sit if x.get("phase") == "2"]
        deb = re.search(r'CHACAL\|PH\|2\|APPROCHE\|debut\|([0-9.]+)', t)
        fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        reg = re.search(r'reglage_observation\|[^|]*\|phase\|2\|avant\|(\d+)\|balayage\|(\d+)', t)
        x = dec[0] if dec else {}
        e.update(n_decisions=len(dec), choix=entier(x.get("choix")), choix_joue=entier(cj[0]["choix"]) if cj else None,
                 detail=cj[0].get("detail") if cj else None, types=sorted({s.get("type") for s in sit}),
                 fenetre=entier(x.get("moteur_depuis_fenetre")), instant=entier(x.get("moteur_entendu")),
                 d_moteur=entier(x.get("distance_moteur"), -1),
                 discrete=int(fin is not None and fin.group(4) == "0" and fin.group(5) == "0" and fin.group(3) == "10"),
                 duree=(float(fin.group(1)) - float(deb.group(1))) if (fin and deb) else None,
                 avant_joue=entier(reg.group(1)) if reg else None, balayage_joue=entier(reg.group(2)) if reg else None)
        E.append(e)
prevus = 2 * 2 * 8 * 4
A = [e for e in E if e["verdict"] == "ACCEPTE" and e["monde"] in MONDES]
print(f"== LECTURE {CAMPAGNE} : {len(E)} episodes trouves, {len(A)} acceptes ( mondes lus : {MONDES} )")
cases = {(w, b, o): [e for e in A if e["monde"] == w and e["bras"] == b and e["option"] == o] for w in MONDES for b in BRAS.values() for o in OPTIONS}
P = [e for e in A if e["bras"] == "PATROUILLE"]; Q = [e for e in A if e["bras"] == "POSTE"]
sens = (sum(1 for e in P if e["fenetre"] == 1) / len(P)) if P else 0; faux = sum(1 for e in Q if e["fenetre"] == 1)
portes = [
    ("Q1 episodes acceptes >= 90 % des prevus", len([e for e in E if e["verdict"] == "ACCEPTE"]) >= 0.9 * prevus, f"{len([e for e in E if e['verdict'] == 'ACCEPTE'])} acceptes ( prevus {prevus} )"),
    ("Q2 zero erreur SQF", sum(e["erreurs"] for e in A) == 0, f"{sum(e['erreurs'] for e in A)} erreurs"),
    ("Q3 une decision TRAVERSEE par episode, choix et choix joue conformes au job",
     all(e.get("n_decisions") == 1 and e.get("choix") == e["option"] and e.get("choix_joue") == e["option"] for e in A),
     f"{sum(1 for e in A if not (e.get('n_decisions') == 1 and e.get('choix') == e['option'] and e.get('choix_joue') == e['option']))} non conforme(s)"),
    ("Q4 chaque case ( monde, bras, option ) a au moins 3 episodes", all(len(v) >= 3 for v in cases.values()), f"{sum(1 for v in cases.values() if len(v) >= 3)} / {len(cases)}"),
    ("Q5 le type pose est celui du bras, et lui seul", all(e.get("types") == ATTENDUS[e["bras"]] for e in A), f"{sum(1 for e in A if e.get('types') != ATTENDUS[e['bras']])} au mauvais type"),
    ("Q6 le reglage joue est celui du job", all(e.get("avant_joue") == e["avant"] and e.get("balayage_joue") == e["balayage"] for e in A), f"{sum(1 for e in A if not (e.get('avant_joue') == e['avant'] and e.get('balayage_joue') == e['balayage']))} ecart(s)"),
    ("Q7 moteur_depuis_fenetre present dans chaque decision", all(e.get("fenetre") in (0, 1) for e in A), f"{sum(1 for e in A if e.get('fenetre') not in (0, 1))} absent(s)"),
    ("Q8 la perception reproduit sa confirmation ( >= 65 % en patrouille, 0 faux positif en poste )", sens >= 0.65 and faux == 0, f"sensibilite {sens:.0%}, faux positifs {faux}"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
if not all(ok for _, ok, _ in portes): print("\n   LECTURE REFUSEE : une porte de qualite a echoue. Aucun effet n est lu."); raise SystemExit
print('\n   PORTES SEULEMENT : aucun effet calcule ici.')
