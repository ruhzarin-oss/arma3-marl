"""Lecture UNIQUE de CONTROLES-ORACLE-20-09 ( criteres : oracle/CRITERES_CONTROLES_ORACLE.md, ecrits avant ).
Portes C1-C5, puis deux lectures : CP ( l adversaire peut punir ) et CN ( l Oracle ne lit pas nos positions )."""
import ast, glob, json, os, re
H = "/mnt/data/hmt"; CAMPAGNE = os.environ.get("CAMPAGNE_LUE", "CONTROLES-ORACLE-20-09")
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
FENETRE, MARGE, TOLERE = 5, 10, 2


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def entier(x, d=None):
    try: return int(float(x))
    except Exception: return d


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-2*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), ctrl=j.get("oracle_ctrl"), situation=j.get("situation"),
                 verdict=None, erreurs=0, quand=os.path.basename(os.path.dirname(jf)))
        try:
            e["verdict"] = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: E.append(e); continue
        e["erreurs"] = len(RX_ERR.findall(t))
        fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        e["compromis"] = entier(fin.group(4)) if fin else None
        pos = re.search(r'"CHACAL\|O\|ctrl\|positif\|([^"]*)"', t)
        e["pos"] = champs(pos.group(1)) if pos else None
        av = re.search(r'"CHACAL\|O\|ctrl\|teleport_avant\|([^"]*)"', t)
        ap = re.search(r'"CHACAL\|O\|ctrl\|teleport_apres\|([^"]*)"', t)
        e["tp_avant"] = champs(av.group(1)) if av else None
        e["tp_apres"] = champs(ap.group(1)) if ap else None
        e["t_tp"] = float(av.group(1).split("|")[0]) if av else None
        dec = []
        for m in re.findall(r'"CHACAL\|O\|decision\|([^"]*)"', t):
            c = champs(m); c["t"] = float(m.split("|")[0])
            try: c["b"] = ast.literal_eval(c.get("croyance", "[]"))
            except Exception: c["b"] = []
            dec.append(c)
        e["dec"] = dec
        E.append(e)

A = [e for e in E if e["verdict"] == "ACCEPTE"]
P = [e for e in A if e["ctrl"] == 1]; N = [e for e in A if e["ctrl"] == 3]
PREVUS = 32
print(f"== CONTROLES DE L ORACLE : {len(E)} episodes, {len(A)} acceptes ( positif {len(P)}, non-triche {len(N)} )")
portes = [
    ("C1 zero erreur SQF", sum(e["erreurs"] for e in A) == 0, f"{sum(e['erreurs'] for e in A)} erreur(s)"),
    ("C2 acceptes >= 90 % des prevus", len(A) >= 0.9 * PREVUS, f"{len(A)} / {PREVUS}"),
    ("C3 chaque bras a au moins 12 episodes", len(P) >= 12 and len(N) >= 12, f"positif {len(P)}, non-triche {len(N)}"),
    ("C4 bras positif : patrouille posee a moins de 400 m",
     bool(P) and all(e["pos"] and entier(e["pos"].get("patrouille_a"), 9999) <= 400 for e in P),
     f"{sum(1 for e in P if not (e['pos'] and entier(e['pos'].get('patrouille_a'), 9999) <= 400))} ecart(s)"),
    ("C5 bras non-triche : les deux lignes de teleport, saut >= 1000 m",
     bool(N) and all(e["tp_avant"] and e["tp_apres"] and entier(e["tp_avant"].get("saut"), 0) >= 1000 for e in N),
     f"{sum(1 for e in N if not (e['tp_avant'] and e['tp_apres'] and entier(e['tp_avant'].get('saut'), 0) >= 1000))} ecart(s)"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
if not all(ok for _, ok, _ in portes):
    print("\n   LECTURE REFUSEE : une porte de qualite a echoue. Aucun controle n est conclu."); raise SystemExit

pris = sum(1 for e in P if e["compromis"] == 1); tx = pris / len(P)
print(f"\n== CP  l adversaire peut-il punir ?  interception {pris} / {len(P)} = {tx:.3f}")
print(f"   {'PASSE : le canal de punition est ouvert.' if tx >= 0.90 else 'ECHOUE : le canal de punition est BOUCHE. Aucun nul de campagne Oracle ne sera lisible comme une absence d effet.'}")

viol = []
for e in N:
    a = e["tp_avant"]; i = entier(a.get("i_arr")); p0 = entier(a.get("p_arr"), 0); nom = a.get("vers")
    suite = [d for d in e["dec"] if d["t"] > e["t_tp"]][:FENETRE]
    fenetre = []
    for d in suite:
        fenetre.append(d)
        if d.get("vu", "RIEN") != "RIEN": break   # detection legitime : la fenetre s arrete ICI, cette ligne comprise
    fenetre = [d for d in fenetre if d.get("vu", "RIEN") == "RIEN"]
    cause = None
    for d in fenetre:
        if i is not None and i < len(d["b"]) and d["b"][i] > p0 + MARGE: cause = f"croyance {d['b'][i]} > {p0}+{MARGE}"; break
        if d.get("cible_patrouille") == nom: cause = "patrouille envoyee sur la case d arrivee"; break
    if cause: viol.append((e["monde"], e["situation"], nom, cause))
print(f"\n== CN  l Oracle suit-il le corps ?  {len(viol)} violation(s) sur {len(N)} episodes ( tolere {TOLERE} )")
for v in viol: print("   ", v)
print(f"   {'PASSE : la croyance ne suit pas la teleportation. L Oracle ne lit pas nos positions.' if len(viol) <= TOLERE else 'ECHOUE : l Oracle LIT NOS POSITIONS. Toute campagne Oracle est sans valeur tant que la ligne fautive n est pas trouvee.'}")
