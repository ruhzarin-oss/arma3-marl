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
rng = random.Random(GRAINE)
TIR = {}


def ic(v):
    ws = sorted(v); cle = tuple(ws)
    if cle not in TIR: r = random.Random(GRAINE); TIR[cle] = [[r.choice(ws) for _ in ws] for _ in range(B)]
    s = sorted(sum(v[w] for w in t) / len(t) for t in TIR[cle]); return s[int(0.025 * B)], s[int(0.975 * B) - 1]


def moy(L, k="discrete"): return sum(e[k] for e in L) / len(L)


print("\n== 1. RAPPEL PAR LE TYPE ( controle : le monde a-t-il change ? )")
m = {c: moy(v) for c, v in cases.items()}
ec = {b: {w: m[(w, b, 2)] - m[(w, b, 1)] for w in MONDES} for b in BRAS.values()}
modT = {w: ec["PATROUILLE"][w] - ec["POSTE"][w] for w in MONDES}
MT, IT = sum(modT.values()) / len(modT), ic(modT)
for b in BRAS.values():
    print(f"      {b:11s} TOUT_DE_SUITE {sum(m[(w, b, 1)] for w in MONDES) / len(MONDES):.3f}   ATTENDRE {sum(m[(w, b, 2)] for w in MONDES) / len(MONDES):.3f}"
          f"   ecart {sum(ec[b].values()) / len(MONDES):+.3f}  IC [{ic(ec[b])[0]:+.3f} ; {ic(ec[b])[1]:+.3f}]")
rappel = MT < 0 and IT[0] <= VERDICT <= IT[1]
print(f"      modulation par le type : {MT:+.3f}  IC [{IT[0]:+.3f} ; {IT[1]:+.3f}]   ( verdict 843118c : {VERDICT:+.3f} )")
print(f"      RAPPEL : {'REUSSI' if rappel else 'ECHOUE - le monde a change, la lecture principale est NULLE'}")


def par_perception(cle, nom):
    cel = {(w, g, o): [e for e in A if e["monde"] == w and e[cle] == g and e["option"] == o] for w in MONDES for g in (0, 1) for o in OPTIONS}
    retenus = [w for w in MONDES if all(len(cel[(w, g, o)]) > 0 for g in (0, 1) for o in OPTIONS)]
    print(f"      mondes couverts ( quatre cases pleines ) : {retenus}")
    if len(retenus) < 6: print(f"      COUVERTURE INSUFFISANTE ( {len(retenus)} mondes < 6 )"); return None
    mm = {c: moy(v) for c, v in cel.items() if v}
    e1 = {w: mm[(w, 1, 2)] - mm[(w, 1, 1)] for w in retenus}; e0 = {w: mm[(w, 0, 2)] - mm[(w, 0, 1)] for w in retenus}
    mod = {w: e1[w] - e0[w] for w in retenus}
    M, I = sum(mod.values()) / len(mod), ic(mod)
    print(f"      entendu     : ecart ( attendre - tout de suite ) {sum(e1.values()) / len(e1):+.3f}  IC [{ic(e1)[0]:+.3f} ; {ic(e1)[1]:+.3f}]")
    print(f"      non entendu : ecart ( attendre - tout de suite ) {sum(e0.values()) / len(e0):+.3f}  IC [{ic(e0)[0]:+.3f} ; {ic(e0)[1]:+.3f}]")
    print(f"      MODULATION par {nom} : {M:+.3f}  IC [{I[0]:+.3f} ; {I[1]:+.3f}]")
    print("      par monde : " + "  ".join(f"{w}:{mod[w]:+.2f}" for w in retenus))
    return M, I


print("\n== 2. LECTURE PRINCIPALE : par la perception moteur_depuis_fenetre")
r = par_perception("fenetre", "moteur_depuis_fenetre")
print("\n== CRITERE ECRIT D AVANCE")
if not rappel: print("   LECTURE NULLE : le rappel par le type a echoue")
elif r is None: print("   LECTURE NULLE : couverture insuffisante")
else:
    M, I = r; etabli = I[0] > 0 or I[1] < 0
    if etabli and M * MT > 0: print("   APPRENABLE : la modulation par la perception est etablie, et de meme signe que celle par le type")
    elif etabli: print("   ETABLIE MAIS DE SIGNE OPPOSE au type : a examiner, aucune regle n en est tiree")
    else: print("   NON APPRENABLE a la precision du dispositif : la dependance existe, la perception ne la porte pas assez")
print("\n== 3. CONTROLE DE SENSIBILITE : par moteur_entendu ( drapeau instantane )")
par_perception("instant", "moteur_entendu")
print("\n== 4. DESCRIPTIF : phase_discrete et duree de la phase 2")
for g in (1, 0):
    for o in OPTIONS:
        L = [e for e in A if e["fenetre"] == g and e["option"] == o]
        D = [e["duree"] for e in L if e["duree"] is not None]
        if L: print(f"   {'entendu    ' if g else 'non entendu'} {OPTIONS[o]:13s} n = {len(L):3d} : phase_discrete {moy(L):.3f} ; duree mediane {sorted(D)[len(D)//2]:.0f} s")
for b in BRAS.values():
    for o in OPTIONS:
        L = [e for e in A if e["bras"] == b and e["option"] == o]; D = [e["duree"] for e in L if e["duree"] is not None]
        if L: print(f"   {b:11s} {OPTIONS[o]:13s} n = {len(L):3d} : duree mediane de la phase 2 {sorted(D)[len(D)//2]:.0f} s")
