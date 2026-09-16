"""
Gymnase de decisions CHACAL - etape 1 : extraire les transitions de phase jouees dans Arma.

Une ligne par episode Arma. Pour chaque phase jouee : l etat au debut, l etat a la fin, l issue
de la phase, et les leviers effectivement joues. Le gymnase ne connait QUE ces transitions : il
ne simule rien, il reechantillonne ce qu Arma a produit.

Source de verite des leviers : la ligne FINI ( ce que le moteur a lu ), pas le job ( ce qui a ete
ecrit ). Lecon du 13/09 « un levier ecrit n est pas un levier lu » : les deux sont gardes et
comparés, un ecart est compte.

Sortie : /mnt/data/hmt/gymnase_decisions/donnees/phases.parquet ( + copie pour dbt ).
"""
import glob, json, os, re, shutil, collections
import pyarrow as pa, pyarrow.parquet as pq

RUNS = "/mnt/data/hmt/runs"
SORTIE = "/mnt/data/hmt/gymnase_decisions/donnees"
COPIE_DBT = "/mnt/c/hmt/dbt/donnees"
RX = re.compile(r'^\s*\d+:\d\d:\d\d "CHACAL\|([A-Z]+)\|(.*)"\s*$')
RX_ERREUR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
LEVIERS = ["depart", "arret", "palier", "socle", "tenir", "effectif", "accessible", "appui_feu", "feu_avant",
           "mg_assaut", "delai_porteur", "appui_fixe", "oracle", "tactique", "ablation", "banc_appui", "placeur",
           "exfil", "azimut", "obs", "lambs", "echelle"]
JOB_SEUL = ["partage", "qrf_n", "qrf_delai", "qrf_dist", "acc", "situation", "menace_p1", "menace_p2",
            "menace_p3", "menace_p4", "menace_p5", "menace_p6", "immortel", "jour", "azimut_val", "instance"]

def nombre(x):
    try: return float(x)
    except (TypeError, ValueError): return None

rangs, ecarts = [], collections.Counter()
for run in sorted(glob.glob(f"{RUNS}/*/")):
    try: job = json.load(open(run + "job.json"))
    except Exception: continue
    if job.get("banc") != "chacal": continue
    for dossier in sorted(glob.glob(run + "g*/")):
        rpt = dossier + "serveur.rpt"
        if not os.path.exists(rpt): continue
        try: res = json.load(open(dossier + "resultat.json"))
        except Exception: res = {}
        texte = open(rpt, "rb").read().decode("latin-1", "ignore")
        r = dict(episode_id=f"{os.path.basename(run.rstrip('/'))}/{os.path.basename(dossier.rstrip('/'))}",
                 campagne=job.get("campagne"), graine=nombre(re.sub(r"\D.*", "", os.path.basename(dossier.rstrip('/'))[1:])),
                 verdict=res.get("verdict"), erreurs_sqf=len(RX_ERREUR.findall(texte)))
        charges_t, morts_bleus = [], []
        fini = {}
        for brute in texte.splitlines():
            m = RX.match(brute)
            if not m: continue
            famille, ch = m.group(1), m.group(2).split("|")
            if famille == "OK" and ch[0] == "monde":
                i = ch.index("site"); r["site"] = ch[i + 1]
            elif famille == "PH" and len(ch) >= 10:
                k, moment = ch[0], ch[2]
                if moment == "debut":
                    r[f"p{k}_debut_t"] = nombre(ch[3]); r[f"p{k}_debut_vivants"] = nombre(ch[5])
                    r[f"p{k}_debut_compromis"] = nombre(ch[7]); r[f"p{k}_debut_alarme"] = nombre(ch[9])
                elif moment == "fin" and len(ch) >= 11:
                    r[f"p{k}_fin_t"] = nombre(ch[3]); r[f"p{k}_fin_issue"] = ch[4]; r[f"p{k}_fin_vivants"] = nombre(ch[6])
                    r[f"p{k}_fin_compromis"] = nombre(ch[8]); r[f"p{k}_fin_alarme"] = nombre(ch[10])
            elif famille == "E" and ch[0] == "charge_posee":
                charges_t.append(nombre(ch[1]))
            elif famille == "E" and ch[0] == "mort" and len(ch) > 5 and ch[5]:
                morts_bleus.append((nombre(ch[1]), ch[5]))
            elif famille == "E" and ch[0] == "choix_ouverture":
                r["porte_indice"] = nombre(ch[3])
            elif famille == "E" and ch[0] == "partage":
                r["partage_regle"] = ch[3]; r["partage_bouchon"] = nombre(ch[7])
            elif famille == "E" and ch[0] == "qrf_partie":
                r["qrf_partie_t"] = nombre(ch[1])
            elif famille == "E" and ch[0] == "compromis" and "compromis_t" not in r:
                r["compromis_t"] = nombre(ch[1])
            elif famille == "E" and ch[0] == "oracle_alarme" and "alarme_t" not in r:
                r["alarme_t"] = nombre(ch[1])
            elif famille == "FINI":
                fini = dict(zip(ch[2::2], ch[3::2])); r["fini_issue"] = ch[0]; r["fini_cause"] = ch[1]
        for k in ("charges", "sur", "exfiltres", "vivants", "phase_max", "duree", "pertes_est", "renseignement", "azimut_joue"):
            r[f"fini_{k}"] = nombre(fini.get(k))
        for k in LEVIERS:
            lu, ecrit = nombre(fini.get(k)), nombre(job.get(k))
            r[f"lev_{k}"] = lu if lu is not None else ecrit
            if lu is not None and ecrit is not None and lu != ecrit and k not in ("echelle",): ecarts[k] += 1
        for k in JOB_SEUL:
            r[f"lev_{k}"] = nombre(job.get(k))
        # charges posees AVANT la fin de l assaut : l etat qui entre en phase 6
        if r.get("p5_fin_t") is not None:
            r["p5_fin_charges"] = float(sum(1 for t in charges_t if t is not None and t <= r["p5_fin_t"] + 0.01))
        # pertes bleues par phase, par role - pour savoir plus tard si « vivants » suffit comme etat
        for k in range(1, 7):
            d, f = r.get(f"p{k}_debut_t"), r.get(f"p{k}_fin_t")
            if d is not None and f is not None:
                roles = [ro for t, ro in morts_bleus if t is not None and d <= t <= f]
                r[f"p{k}_morts_roles"] = ",".join(roles)
        rangs.append(r)

cles = sorted({k for r in rangs for k in r})
table = pa.Table.from_pylist([{k: r.get(k) for k in cles} for r in rangs])
os.makedirs(SORTIE, exist_ok=True)
pq.write_table(table, f"{SORTIE}/phases.parquet")
shutil.copy(f"{SORTIE}/phases.parquet", f"{COPIE_DBT}/phases.parquet")
print(f"episodes {len(rangs)}  colonnes {len(cles)}")
print("ecarts job/FINI par levier (levier ecrit mais pas lu) :", dict(ecarts))
