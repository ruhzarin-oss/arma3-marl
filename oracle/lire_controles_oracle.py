"""Lecture UNIQUE de CONTROLES-ORACLE-20-09 ( criteres : oracle/CRITERES_CONTROLES_ORACLE.md, ecrits avant ).
Portes C1-C5, puis deux lectures : CP ( l adversaire peut punir ) et CN ( l Oracle ne lit pas nos positions )."""
import ast, glob, json, os, re
H = "/mnt/data/hmt"; CAMPAGNE = os.environ.get("CAMPAGNE_LUE", "CONTROLES-ORACLE-20-09")
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
FENETRE, MARGE, TOLERE = 5, 10, 2
SANS_TELEPORT = 0.387   # mesure sur 62 episodes Oracle sans teleport, oracle/contre_epreuve_cible_patrouille.py


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
        suivi = [entier(champs(m).get("patrouille_a")) for m in re.findall(r'"CHACAL\|O\|ctrl\|positif_suivi\|([^"]*)"', t)]
        e["suivi"] = [x for x in suivi if x is not None]
        e["au_contact"] = min(e["suivi"]) if e["suivi"] else None
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

A0 = [e for e in E if e["verdict"] == "ACCEPTE"]
# ! AMENDEMENT 1 : la version defectueuse du controle envoyait TOUJOURS sur le SITE, ou nos hommes etaient vus
# aussitot ; la fenetre se fermait et le controle ne pouvait plus echouer. Ces episodes ne sont pas lus.
Av = [e for e in A0 if e["ctrl"] != 3 or (e["tp_avant"] and e["tp_avant"].get("vers") not in ("SITE", "ABORDS"))]
ecartes = len(A0) - len(Av)
# ! AMENDEMENT 2 : on lit le PREMIER episode ACCEPTE de chaque ( bras, monde, situation ). « Accepte », et non
# « premier tout court » : c est l erreur qui a rendu le remplacement d ORACLE-P2-19-09 sans effet, un exemplaire
# refuse bloquant le rejeu valide de la meme case.
vus = set(); A = []
for e in sorted(Av, key=lambda x: x.get("quand") or ""):
    cle = (e["ctrl"], e["monde"], e["situation"])
    if cle in vus: continue
    vus.add(cle); A.append(e)
doublons = len(Av) - len(A)
P = [e for e in A if e["ctrl"] == 1]
N = [e for e in A if e["ctrl"] == 3]
PREVUS = 32
print(f"== CONTROLES DE L ORACLE : {len(E)} episodes, {len(A)} acceptes ( positif {len(P)}, non-triche {len(N)} )")
print(f"   {ecartes} episode(s) ecarte(s) : case d arrivee SITE ou ABORDS ( version defectueuse du controle ) ; {doublons} doublon(s) de rejeu")


def fenetre_de(e):
    """les decisions qui suivent le saut, coupees a la premiere detection legitime ( celle-ci exclue )"""
    f = []
    for d in [x for x in e["dec"] if x["t"] > e["t_tp"]][:FENETRE]:
        if d.get("vu", "RIEN") != "RIEN": break
        f.append(d)
    return f

assez = [e for e in N if len(fenetre_de(e)) >= 2]
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
    ("C6 [ VACUITE ] au moins 12 episodes offrent 2 decisions sans detection apres le saut",
     len(assez) >= 12, f"{len(assez)} / {len(N)} ; s il en manque, on ne lui a pas laisse l occasion de tricher"),
    # ! V2 : en v1 la patrouille etait posee a 300 m et repartait aussitot. Un controle positif qui ne met
    # personne en face ne prouve rien : on exige desormais qu elle soit VENUE AU CONTACT.
    ("C7 [ CONFRONTATION ] bras positif : la patrouille est venue a moins de 150 m",
     bool(P) and sum(1 for e in P if (e.get("au_contact") or 9999) <= 150) >= 0.8 * len(P),
     f"{sum(1 for e in P if (e.get('au_contact') or 9999) <= 150)} / {len(P)} ; mediane du plus proche "
     f"{sorted((e.get('au_contact') or 9999) for e in P)[len(P) // 2] if P else '-'} m"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
if not all(ok for _, ok, _ in portes):
    print("\n   LECTURE REFUSEE : une porte de qualite a echoue. Aucun controle n est conclu."); raise SystemExit

pris = sum(1 for e in P if e["compromis"] == 1); tx = pris / len(P)
print(f"\n== CP  l adversaire peut-il punir ?  interception {pris} / {len(P)} = {tx:.3f}")
print(f"   {'PASSE : le canal de punition est ouvert.' if tx >= 0.90 else 'ECHOUE : le canal de punition est BOUCHE. Aucun nul de campagne Oracle ne sera lisible comme une absence d effet.'}")

viol = []; vise = []
for e in N:
    a = e["tp_avant"]; i = entier(a.get("i_arr")); p0 = entier(a.get("p_arr"), 0); nom = a.get("vers")
    fenetre = fenetre_de(e)
    cause = None
    for d in fenetre:
        if i is not None and i < len(d["b"]) and d["b"][i] > p0 + MARGE: cause = f"croyance {d['b'][i]} > {p0}+{MARGE}"; break
    if cause: viol.append((e["monde"], e["situation"], nom, cause))
    if any(d.get("cible_patrouille") == nom for d in fenetre): vise.append(e)
print(f"\n== CN  l Oracle suit-il le corps ?  {len(viol)} violation(s) sur {len(N)} episodes ( tolere {TOLERE} )")
for v in viol: print("   ", v)
print(f"   {'PASSE : la croyance ne suit pas la teleportation. L Oracle ne lit pas nos positions.' if len(viol) <= TOLERE else 'ECHOUE : l Oracle LIT NOS POSITIONS. Toute campagne Oracle est sans valeur tant que la ligne fautive n est pas trouvee.'}")
# ! V2 : la clause « la patrouille vise la case d arrivee » n est plus un seuil mais une COMPARAISON. Mesure sur
# 62 episodes Oracle SANS teleport ( oracle/contre_epreuve_cible_patrouille.py ) : 38,7 %. Un seuil nu se
# declenchait quatre fois sur dix sur rien.
tx_vise = len(vise) / len(N) if N else 0
print(f"\n== CN-bis  la patrouille va-t-elle vers la case d arrivee plus souvent qu au hasard ?")
print(f"   avec teleport {len(vise)} / {len(N)} = {tx_vise:.3f}   contre {SANS_TELEPORT:.3f} sans teleport")
print(f"   {'PASSE : pas plus souvent qu au hasard.' if tx_vise <= SANS_TELEPORT + 0.15 else 'ECHOUE : la patrouille est attiree par la case ou nous sommes reellement.'}")
