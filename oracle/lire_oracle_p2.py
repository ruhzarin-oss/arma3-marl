"""Lecture UNIQUE de ORACLE-P2-19-09 ( criteres : oracle/CRITERES_ORACLE_P2.md, ecrits avant ).
  python3 lire_oracle_p2.py [--sans-monde N ...]
Portes Q1-Q7 et QO1-QO2, puis trois lectures : pas un decor, pas un mur, il punit un choix plus que l autre."""
import glob, json, os, random, re, sys
H = "/mnt/data/hmt"; CAMPAGNE = os.environ.get("CAMPAGNE_LUE", "ORACLE-P2-19-09")
RETIRES = [int(sys.argv[i + 1]) for i, a in enumerate(sys.argv) if a == "--sans-monde"]
MONDES = [w for w in (4, 5, 6, 7, 8, 9, 11, 12) if w not in RETIRES]
OPTIONS = {1: "TOUT_DE_SUITE", 2: "ATTENDRE"}; NIVEAUX = {0: "TEMOIN", 1: "ORACLE"}
B, GRAINE = 10000, 20260919
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")


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
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), option=j.get("traversee"), niveau=j.get("oracle_cmd"),
                 avant=j.get("avant"), balayage=j.get("balayage"), verdict=None, erreurs=0)
        try:
            e["verdict"] = json.load(open(d + "resultat.json")).get("verdict"); t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: E.append(e); continue
        e["erreurs"] = len(RX_ERR.findall(t))
        dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]; dec = [x for x in dec if x.get("point") == "TRAVERSEE"]
        cj = [champs(m) for m in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]; cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
        sit = [champs(m) for m in re.findall(r'"CHACAL\|E\|situation\|([^"]*)"', t)]; sit = [x for x in sit if x.get("phase") == "2"]
        orc = re.findall(r'"CHACAL\|O\|decision\|[^"]*\|action\|([A-Z_]+)\|[^"]*\|budget\|(\d+)', t)
        fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        reg = re.search(r'reglage_observation\|[^|]*\|phase\|2\|avant\|(\d+)\|balayage\|(\d+)', t)
        x = dec[0] if dec else {}
        e.update(n_decisions=len(dec), choix=entier(x.get("choix")), choix_joue=entier(cj[0]["choix"]) if cj else None,
                 types=sorted({s.get("type") for s in sit}), fenetre=entier(x.get("moteur_depuis_fenetre")),
                 n_orc=len(orc), ordres=sum(1 for a, _ in orc if a.startswith("PATROUILLE")),
                 budget_fin=(entier(orc[-1][1]) if orc else None),
                 discrete=int(fin is not None and fin.group(4) == "0" and fin.group(5) == "0" and fin.group(3) == "10"),
                 compromis=int(fin.group(4)) if fin else None,
                 avant_joue=entier(reg.group(1)) if reg else None, balayage_joue=entier(reg.group(2)) if reg else None)
        e["situation"] = j.get("situation"); e["quand"] = os.path.basename(os.path.dirname(jf))
        E.append(e)
# ! LE REJEU DE LA NUIT. La station est tombee le 20/09 vers 00 h 35 ; six jobs interrompus ont ete REMIS EN FILE et
# rejoues EN ENTIER, donc certains episodes existent deux fois. La scene etant deterministe, un doublon est une copie
# exacte : le garder surpondererait sa case. On ne lit que le PREMIER episode de chaque
# ( monde, niveau, option, situation ). Regle ecrite avant toute lecture d effet.
vus = set(); D = []
for e in sorted(E, key=lambda x: x.get("quand") or ""):
    cle = (e["monde"], e["niveau"], e["option"], e.get("situation"))
    if cle in vus: continue
    vus.add(cle); D.append(e)
doublons = len(E) - len(D); E = D
prevus = 2 * 2 * 8 * 4
A = [e for e in E if e["verdict"] == "ACCEPTE" and e["monde"] in MONDES]
print(f"== LECTURE {CAMPAGNE} : {len(E)} episodes apres retrait de {doublons} doublon(s) de rejeu, {len(A)} acceptes ( mondes {MONDES} )")
cases = {(w, n, o): [e for e in A if e["monde"] == w and e["niveau"] == n and e["option"] == o] for w in MONDES for n in NIVEAUX for o in OPTIONS}
O1 = [e for e in A if e["niveau"] == 1]; O0 = [e for e in A if e["niveau"] == 0]
portes = [
    ("Q1 acceptes >= 90 % des prevus", len([e for e in E if e["verdict"] == "ACCEPTE"]) >= 0.9 * prevus, f"{len([e for e in E if e['verdict'] == 'ACCEPTE'])} ( prevus {prevus} )"),
    ("Q2 zero erreur SQF", sum(e["erreurs"] for e in A) == 0, f"{sum(e['erreurs'] for e in A)} erreurs"),
    ("Q3 une decision TRAVERSEE, choix et choix joue conformes", all(e.get("n_decisions") == 1 and e.get("choix") == e["option"] and e.get("choix_joue") == e["option"] for e in A),
     f"{sum(1 for e in A if not (e.get('n_decisions') == 1 and e.get('choix') == e['option'] and e.get('choix_joue') == e['option']))} non conforme(s)"),
    ("Q4 chaque case ( monde, niveau, option ) a au moins 3 episodes", all(len(v) >= 3 for v in cases.values()), f"{sum(1 for v in cases.values() if len(v) >= 3)} / {len(cases)}"),
    ("Q5 la menace posee est la patrouille, et elle seule", all(e.get("types") == ["PATROUILLE_ROUTE"] for e in A), f"{sum(1 for e in A if e.get('types') != ['PATROUILLE_ROUTE'])} ecart(s)"),
    ("Q6 le reglage joue est celui du job", all(e.get("avant_joue") == e["avant"] and e.get("balayage_joue") == e["balayage"] for e in A), f"{sum(1 for e in A if not (e.get('avant_joue') == e['avant'] and e.get('balayage_joue') == e['balayage']))} ecart(s)"),
    ("Q7 moteur_depuis_fenetre present", all(e.get("fenetre") in (0, 1) for e in A), f"{sum(1 for e in A if e.get('fenetre') not in (0, 1))} absent(s)"),
    ("QO1 l Oracle a donne au moins un ordre de patrouille dans >= 80 % de ses episodes",
     bool(O1) and sum(1 for e in O1 if e["ordres"] > 0) >= 0.8 * len(O1), f"{sum(1 for e in O1 if e['ordres'] > 0)} / {len(O1)}"),
    ("QO2 aucune ligne de l Oracle chez le temoin", all(e["n_orc"] == 0 for e in O0), f"{sum(1 for e in O0 if e['n_orc'] > 0)} temoin(s) touche(s)"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
if not all(ok for _, ok, _ in portes): print("\n   LECTURE REFUSEE : une porte de qualite a echoue. Aucun effet n est lu."); raise SystemExit
TIR = {}


def ic(v):
    ws = sorted(v); cle = tuple(ws)
    if cle not in TIR: r = random.Random(GRAINE); TIR[cle] = [[r.choice(ws) for _ in ws] for _ in range(B)]
    s = sorted(sum(v[w] for w in t) / len(t) for t in TIR[cle]); return s[int(0.025 * B)], s[int(0.975 * B) - 1]


def moy(L, k="discrete"): return sum(e[k] for e in L) / len(L)


m = {c: moy(v) for c, v in cases.items()}
print("\n== REUSSITE ( phase_discrete ) par case")
for n in NIVEAUX:
    print(f"   {NIVEAUX[n]:7s} TOUT_DE_SUITE {sum(m[(w, n, 1)] for w in MONDES) / len(MONDES):.3f}   ATTENDRE {sum(m[(w, n, 2)] for w in MONDES) / len(MONDES):.3f}")
niv = {n: {w: (m[(w, n, 1)] + m[(w, n, 2)]) / 2 for w in MONDES} for n in NIVEAUX}
dN = {w: niv[1][w] - niv[0][w] for w in MONDES}; DN, IDN = sum(dN.values()) / len(dN), ic(dN)
ec = {n: {w: m[(w, n, 2)] - m[(w, n, 1)] for w in MONDES} for n in NIVEAUX}
I = {w: ec[1][w] - ec[0][w] for w in MONDES}; MI, II = sum(I.values()) / len(I), ic(I)
meilleure = max(sum(m[(w, 1, o)] for w in MONDES) / len(MONDES) for o in OPTIONS)
print("\n== 1. PAS UN DECOR : la reussite baisse-t-elle avec l Oracle ?")
print(f"   ecart de reussite Oracle - temoin : {DN:+.3f}  IC [{IDN[0]:+.3f} ; {IDN[1]:+.3f}]")
c1 = IDN[1] < 0
print(f"   -> {'TENU' if c1 else 'ECHOUE : l Oracle ne fait pas baisser la reussite ( decor )'}")
print("\n== 2. PAS UN MUR : la meilleure option reussit-elle encore ?")
c2 = meilleure >= 0.40
print(f"   meilleure option sous Oracle : {meilleure:.3f}  -> {'TENU' if c2 else 'ECHOUE : moins de 40 % ( mur )'}")
print("\n== 3. IL PUNIT UN CHOIX PLUS QUE L AUTRE ( interaction )")
for n in NIVEAUX:
    print(f"   {NIVEAUX[n]:7s} ecart ( attendre - tout de suite ) {sum(ec[n].values()) / len(MONDES):+.3f}  IC [{ic(ec[n])[0]:+.3f} ; {ic(ec[n])[1]:+.3f}]")
print(f"   INTERACTION I = {MI:+.3f}  IC [{II[0]:+.3f} ; {II[1]:+.3f}]   ( predite negative )")
print("   par monde : " + "  ".join(f"{w}:{I[w]:+.2f}" for w in MONDES))
c3 = II[0] > 0 or II[1] < 0
print("\n== CRITERE ECRIT D AVANCE")
if not c1: print("   DECOR")
elif not c2: print("   MUR")
elif not c3: print("   ADVERSAIRE SANS DECISION : il fait perdre, autant quel que soit le choix")
else: print(f"   ORACLE UTILE : il punit un choix plus que l autre ( interaction {'negative, comme predit' if MI < 0 else 'POSITIVE, contraire a la prediction'} )")
print("\n== DESCRIPTIF : ce que fait l Oracle")
print(f"   ordres de patrouille par episode : moyenne {sum(e['ordres'] for e in O1) / max(1, len(O1)):.1f} ; "
      f"budget restant en fin d episode : moyenne {sum((e['budget_fin'] or 0) for e in O1) / max(1, len(O1)):.1f}")
for n in NIVEAUX:
    L = [e for e in A if e["niveau"] == n]
    print(f"   {NIVEAUX[n]:7s} : compromis {moy(L, 'compromis'):.2f} ; moteur entendu au choix {sum(e['fenetre'] or 0 for e in L) / len(L):.0%}")
