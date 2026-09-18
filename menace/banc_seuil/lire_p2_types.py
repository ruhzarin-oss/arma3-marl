"""Lecture pre-enregistree de CHOIX-P2-TYPES-19-09 ( criteres : CRITERES_P2_TYPES_19-09.md ). Ecrite AVANT le lancement.
Meme logique que curriculum/CRITERES_CHOIX_17_09.md et C:\\hmt\\dbt\\outils\\lire_choix.py, mais lue directement dans les RPT ( la copie
chacalp2 n est pas branchee sur dbt ) : moyennes par case, ecarts apparies par monde, mondes a poids egaux, IC 95 % par 10 000
reechantillonnages des mondes.
  issue primaire : phase_discrete = fin de la phase 2 sans compromission, sans alarme, dix vivants ( definition de vignette_choix.sql ).
  bras           : le TYPE de menace ( niveau 4 = patrouille motorisee seule ; niveau 5 = poste de controle seul ), poses pres.
  modulation     = ecart( ATTENDRE - TOUT_DE_SUITE | PATROUILLE ) - ecart( ATTENDRE - TOUT_DE_SUITE | POSTE ).
Usage : python3 lire_p2_types.py [CAMPAGNE] [--sans-monde N]"""
import glob, json, os, random, re, sys
H = "/mnt/data/hmt"
CAMPAGNE = next((a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()), "CHOIX-P2-TYPES-19-09")
RETIRES = [int(sys.argv[i + 1]) for i, a in enumerate(sys.argv) if a == "--sans-monde"]
MONDES = [w for w in (4, 5, 6, 7, 8, 9, 11, 12) if w not in RETIRES]
BRAS = {4: "PATROUILLE", 5: "POSTE"}; OPTIONS = {1: "TOUT_DE_SUITE", 2: "ATTENDRE"}; B, GRAINE = 10000, 20260919
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), bras=BRAS.get(j.get("menace_p2")), option=j.get("traversee"), situation=j.get("situation"),
                 avant=j.get("avant"), balayage=j.get("balayage"), verdict=None, erreurs=0)
        try:
            e["verdict"] = json.load(open(d + "resultat.json")).get("verdict"); t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: E.append(e); continue
        e["erreurs"] = len(RX_ERR.findall(t))
        dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]; dec = [x for x in dec if x.get("point") == "TRAVERSEE"]
        cj = [champs(m) for m in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]; cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
        sit = [champs(m) for m in re.findall(r'"CHACAL\|E\|situation\|([^"]*)"', t)]; sit = [x for x in sit if x.get("phase") == "2"]
        fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[^|]*\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        reg = re.search(r'reglage_observation\|[^|]*\|phase\|2\|avant\|(\d+)\|balayage\|(\d+)\|distance_secteur\|(-?\d+)', t)
        e.update(n_decisions=len(dec), choix=int(float(dec[0]["choix"])) if dec else None, choix_joue=int(float(cj[0]["choix"])) if cj else None,
                 detail=cj[0].get("detail") if cj else None, attente=int(float(cj[0].get("attente", -1))) if cj else None,
                 percue=int(dec[0]["menace_percue"]) if dec and "menace_percue" in dec[0] else None, connues=int(dec[0].get("menaces_connues", 0)) if dec else None,
                 vehicule_vu=int(dec[0].get("vehicule_vu", 0)) if dec else None, types=sorted({x.get("type") for x in sit}),
                 fin=fin.group(1) if fin else None, discrete=int(fin is not None and fin.group(3) == "0" and fin.group(4) == "0" and fin.group(2) == "10"),
                 vivants=int(fin.group(2)) if fin else None, compromis=int(fin.group(3)) if fin else None, alarme=int(fin.group(4)) if fin else None,
                 avant_joue=int(reg.group(1)) if reg else None, balayage_joue=int(reg.group(2)) if reg else None)
        E.append(e)
prevus = 8 * 2 * 2 * 4
A = [e for e in E if e["verdict"] == "ACCEPTE" and e["monde"] in MONDES]
print(f"== LECTURE {CAMPAGNE} : point TRAVERSEE, options TOUT_DE_SUITE ( 1 ) / ATTENDRE ( 2 ), bras PATROUILLE ( niveau 4 ) / POSTE ( niveau 5 ), issue primaire phase_discrete")
if RETIRES: print(f"   monde(s) retire(s) de la lecture : {RETIRES}")
attendus = {"PATROUILLE": ["PATROUILLE_ROUTE"], "POSTE": ["POSTE_DE_CONTROLE"]}
cases = {(w, b, o): [e for e in A if e["monde"] == w and e["bras"] == b and e["option"] == o] for w in MONDES for b in BRAS.values() for o in OPTIONS}
portes = [
    ("Q1 episodes acceptes >= 90 % des prevus", len([e for e in E if e["verdict"] == "ACCEPTE"]) >= 0.9 * prevus, f"{len([e for e in E if e['verdict'] == 'ACCEPTE'])} acceptes sur {len(E)} ( prevus {prevus} )"),
    ("Q2 zero erreur SQF", sum(e["erreurs"] for e in A) == 0, f"{sum(e['erreurs'] for e in A)} erreurs"),
    ("Q3 une decision TRAVERSEE par episode, choix conforme au job, choix joue conforme", all(e.get("n_decisions") == 1 and e.get("choix") == e["option"] and e.get("choix_joue") == e["option"] for e in A),
     f"{sum(1 for e in A if not (e.get('n_decisions') == 1 and e.get('choix') == e['option'] and e.get('choix_joue') == e['option']))} episode(s) non conforme(s)"),
    ("Q4 chaque case ( monde, bras, option ) a au moins 3 episodes", all(len(v) >= 3 for v in cases.values()), f"{sum(1 for v in cases.values() if len(v) >= 3)} cases pleines sur {len(cases)}"),
    ("Q5 le type de menace pose est celui du bras, et lui seul", all(e.get("types") == attendus[e["bras"]] for e in A), f"{sum(1 for e in A if e.get('types') != attendus[e['bras']])} episode(s) au mauvais type"),
    ("Q6 le reglage joue est celui du job", all(e.get("avant_joue") == e["avant"] and e.get("balayage_joue") == e["balayage"] for e in A), f"{sum(1 for e in A if not (e.get('avant_joue') == e['avant'] and e.get('balayage_joue') == e['balayage']))} ecart(s)"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
if not all(ok for _, ok, _ in portes): print("\n   LECTURE REFUSEE : une porte de qualite a echoue. Aucun effet n est lu."); raise SystemExit


def moy(L, k): return sum(e[k] for e in L) / len(L)


def lire(issue):
    m = {c: moy(v, issue) for c, v in cases.items()}
    ec = {b: {w: m[(w, b, 2)] - m[(w, b, 1)] for w in MONDES} for b in BRAS.values()}
    mod = {w: ec["PATROUILLE"][w] - ec["POSTE"][w] for w in MONDES}; moyen = {w: (ec["PATROUILLE"][w] + ec["POSTE"][w]) / 2 for w in MONDES}
    rng = random.Random(GRAINE); tir = [[rng.choice(MONDES) for _ in MONDES] for _ in range(B)]
    def ic(v):
        s = sorted(sum(v[w] for w in t) / len(t) for t in tir); return s[int(0.025 * B)], s[int(0.975 * B) - 1]
    return m, ec, mod, moyen, ic


m, ec, mod, moyen, ic = lire("discrete")
print("\n== ISSUE PRIMAIRE ( ecrite avant ) : phase_discrete")
for b in BRAS.values():
    print(f"      {b:11s} TOUT_DE_SUITE {sum(m[(w, b, 1)] for w in MONDES) / len(MONDES):.3f}   ATTENDRE {sum(m[(w, b, 2)] for w in MONDES) / len(MONDES):.3f}"
          f"   ecart {sum(ec[b].values()) / len(MONDES):+.3f}  IC [{ic(ec[b])[0]:+.3f} ; {ic(ec[b])[1]:+.3f}]")
M, IM = sum(mod.values()) / len(MONDES), ic(mod); Y, IY = sum(moyen.values()) / len(MONDES), ic(moyen)
print(f"      MODULATION ( patrouille - poste ) : {M:+.3f}  IC [{IM[0]:+.3f} ; {IM[1]:+.3f}]")
print(f"      ecart moyen des deux types : {Y:+.3f}  IC [{IY[0]:+.3f} ; {IY[1]:+.3f}]")
print("      modulation par monde : " + "  ".join(f"{w}:{mod[w]:+.2f}" for w in MONDES))
c2 = IM[0] > 0 or IM[1] < 0; c3 = c2 and (sum(ec["PATROUILLE"].values()) * sum(ec["POSTE"].values()) < 0); dom = (not c2) and (IY[0] > 0 or IY[1] < 0)
print(f"\n== CRITERES\n   C2 MODULATION ETABLIE : {'OUI' if c2 else 'NON'}\n   C3 INVERSION ( C2 et signes opposes ) : {'OUI' if c3 else 'NON'}")
print(f"\n   CLASSEMENT : {'DEPENDANT du type de menace' if c2 else ('DOMINE' if dom else 'INDIFFERENT')}")
print("\n== LA PERCEPTION AU MOMENT DU CHOIX ( descriptif, sans decision )")
for b in BRAS.values():
    L = [e for e in A if e["bras"] == b]
    print(f"   {b:11s} : percue > 0 dans {sum(e['percue'] > 0 for e in L)}/{len(L)} ; connue ( niveau 2 ) dans {sum(e['percue'] == 2 for e in L)}/{len(L)} ; vehicule_vu dans {sum(e['vehicule_vu'] for e in L)}/{len(L)}")
for nom, f in (("percue = 0", lambda e: e["percue"] == 0), ("percue > 0", lambda e: e["percue"] > 0)):
    for o in OPTIONS:
        L = [e for e in A if f(e) and e["option"] == o]
        if L: print(f"   {nom} , {OPTIONS[o]:13s} : phase_discrete {moy(L, 'discrete'):.3f} ( n = {len(L)} ) ; compromis {moy(L, 'compromis'):.3f} ; alarme {moy(L, 'alarme'):.3f} ; vivants {moy(L, 'vivants'):.2f}")
intra = [w for w in MONDES if 0 < sum(e["percue"] > 0 for e in A if e["monde"] == w) < len([e for e in A if e["monde"] == w])]
print(f"   mondes ou la perception varie d un episode a l autre : {intra}")
print("\n== ISSUES SECONDAIRES ( descriptives ) : fin de phase, attente jouee")
for b in BRAS.values():
    for o in OPTIONS:
        L = [e for e in A if e["bras"] == b and e["option"] == o]
        if L: print(f"   {b:11s} {OPTIONS[o]:13s} n = {len(L):3d} ; compromis {moy(L, 'compromis'):.3f} ; alarme {moy(L, 'alarme'):.3f} ; vivants {moy(L, 'vivants'):.2f} ; attente moyenne {moy(L, 'attente'):.0f} s ; details {sorted({e['detail'] for e in L})}")
