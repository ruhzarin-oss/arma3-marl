"""
Chercheur de causes CHACAL - etape 1 : fabriquer les variables SANS les choisir.

Chaque ligne que le banc ecrit devient des variables, par une regle generique, sans liste a la main :
  n|cle            nombre de lignes E|cle ( et AVERT|cle ) dans l episode
  n|cle|pK         meme compte, dans la phase K ( phase courante lue sur les lignes PH )
  n|cle|NOM=VALEUR compte des lignes ou un champ nomme porte une valeur categorielle ( MAJUSCULES )
  n|cle|JETON      compte des jetons categoriels positionnels ( ex : le role dans E|mort )
  max|cle|nom      maximum d un champ numerique nomme
  ok|cle|nom       valeur numerique des lignes OK ( geometrie du monde : avant tout traitement )
  ph|K|debut|nom   etat au debut et a la fin de chaque phase, duree, issue=...
  fini|nom         la ligne FINI ; fini_issue=..., fini_cause=...
Les leviers sont lus a part, depuis job.json ( ce qui a ete force ).

Sorties : /mnt/data/hmt/chercheur_causes/donnees/{variables,episodes}.parquet
"""
import glob, json, os, re, collections
import pyarrow as pa, pyarrow.parquet as pq

RUNS = "/mnt/data/hmt/runs"
SORTIE = "/mnt/data/hmt/chercheur_causes/donnees"
RX = re.compile(r'^\s*\d+:\d\d:\d\d "CHACAL\|([A-Z]+)\|(.*)"\s*$')
RX_ERREUR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
RX_CAT = re.compile(r"^[A-Z][A-Z0-9_]{1,30}$")
RX_NOM = re.compile(r"^[a-z][a-z0-9_]{0,30}$")
IGNORE = {"S", "VC", "VG", "VH", "GEO", "C", "CANARI", "EMPREINTE"}
JOB_NON_LEVIERS = {"instance", "repetitions", "graines", "version", "note", "campagne", "tolere", "banc"}

def nombre(x):
    try:
        v = float(x)
        return v if v == v and abs(v) < 1e12 else None
    except (TypeError, ValueError): return None

lignes_var, lignes_ep = [], []
for run in sorted(glob.glob(f"{RUNS}/*/")):
    try: job = json.load(open(run + "job.json"))
    except Exception: continue
    if job.get("banc") != "chacal": continue
    for dossier in sorted(glob.glob(run + "g*/")):
        rpt = dossier + "serveur.rpt"
        if not os.path.exists(rpt): continue
        eid = f"{os.path.basename(run.rstrip('/'))}/{os.path.basename(dossier.rstrip('/'))}"
        try: res = json.load(open(dossier + "resultat.json"))
        except Exception: res = {}
        texte = open(rpt, "rb").read().decode("latin-1", "ignore")
        v = collections.defaultdict(float); maxi = {}
        phase, site = 0, None
        for brute in texte.splitlines():
            m = RX.match(brute)
            if not m: continue
            famille, ch = m.group(1), m.group(2).split("|")
            if famille in IGNORE: continue
            cle = ch[0]
            if famille == "PH" and len(ch) >= 4:
                k, moment = ch[0], ch[2]
                if moment == "debut":
                    phase = int(k); v[f"ph|{k}|joue"] = 1; v[f"ph|{k}|debut_t"] = nombre(ch[3]) or 0
                    for i in range(4, len(ch) - 1, 2):
                        if nombre(ch[i + 1]) is not None: v[f"ph|{k}|debut|{ch[i]}"] = nombre(ch[i + 1])
                elif moment == "fin" and len(ch) >= 5:
                    v[f"ph|{k}|duree"] = (nombre(ch[3]) or 0) - v.get(f"ph|{k}|debut_t", 0)
                    v[f"ph|{k}|issue={ch[4]}"] = 1
                    for i in range(5, len(ch) - 1, 2):
                        if nombre(ch[i + 1]) is not None: v[f"ph|{k}|fin|{ch[i]}"] = nombre(ch[i + 1])
                continue
            if famille == "FINI":
                v[f"fini_issue={ch[0]}"] = 1; v[f"fini_cause={ch[1]}"] = 1
                for i in range(2, len(ch) - 1, 2):
                    if nombre(ch[i + 1]) is not None: v[f"fini|{ch[i]}"] = nombre(ch[i + 1])
                continue
            if famille == "OK":
                if cle == "monde" and "site" in ch: site = ch[ch.index("site") + 1]
                for i in range(1, len(ch) - 1):
                    if RX_NOM.match(ch[i]) and nombre(ch[i + 1]) is not None and f"ok|{cle}|{ch[i]}" not in v:
                        v[f"ok|{cle}|{ch[i]}"] = nombre(ch[i + 1])
                continue
            if famille not in ("E", "AVERT"): continue
            base = f"{famille.lower()}|{cle}"
            v[f"n|{base}"] += 1; v[f"n|{base}|p{phase}"] += 1
            debut = 2 if famille == "E" else 1
            i = debut
            while i < len(ch):
                tok = ch[i]
                if RX_NOM.match(tok) and i + 1 < len(ch):
                    val = ch[i + 1]
                    if RX_CAT.match(val): v[f"n|{base}|{tok}={val}"] += 1; i += 2; continue
                    x = nombre(val)
                    if x is not None:
                        kk = f"max|{base}|{tok}"; maxi[kk] = x if kk not in maxi else max(maxi[kk], x); i += 2; continue
                elif RX_CAT.match(tok):
                    v[f"n|{base}|{tok}"] += 1
                i += 1
        v.update(maxi)
        lignes_var.extend(dict(episode_id=eid, variable=k, valeur=float(x)) for k, x in v.items() if x is not None)
        ep = dict(episode_id=eid, run=os.path.basename(run.rstrip('/')), campagne=job.get("campagne") or "SANS_CAMPAGNE",
                  version=job.get("version") or "", graine=nombre(re.sub(r"\D.*", "", os.path.basename(dossier.rstrip('/'))[1:])),
                  site=site, verdict=res.get("verdict"), erreurs_sqf=len(RX_ERREUR.findall(texte)))
        for k, x in job.items():
            if k in JOB_NON_LEVIERS: continue
            if isinstance(x, bool): x = int(x)
            if isinstance(x, (int, float)): ep[f"job|{k}"] = float(x)
        lignes_ep.append(ep)

os.makedirs(SORTIE, exist_ok=True)
pq.write_table(pa.Table.from_pylist(lignes_var), f"{SORTIE}/variables.parquet")
cles = sorted({k for e in lignes_ep for k in e})
pq.write_table(pa.Table.from_pylist([{k: e.get(k) for k in cles} for e in lignes_ep]), f"{SORTIE}/episodes.parquet")
print(f"episodes {len(lignes_ep)}  valeurs {len(lignes_var)}  variables distinctes {len({l['variable'] for l in lignes_var})}  leviers de job {len([c for c in cles if c.startswith('job|')])}")
