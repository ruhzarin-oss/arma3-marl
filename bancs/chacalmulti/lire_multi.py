#!/usr/bin/env python3
"""lire_multi - lit un episode multiple, le DEMULTIPLEXE, et rend a chaque cellule le journal d'un episode seul.

Chaque cellule est ensuite lue par le lecteur du banc seul ( bancs/chacal/lire.py ), avec ses portes : canari, pas
continus, rien apres FINI, LAMBS actif. Une cellule que ce lecteur refuse est refusee, exactement comme un episode seul.

Ce qui s'ajoute ici, et qui n'existe pas dans un episode seul :
  - la CHARGE : images par seconde du serveur ( compteur non ordonnance ), avec le nombre de cellules actives ;
  - la PERCEPTION sous charge : la sonde de connaissance ( debout, 150 m, nuit, regard pose ), hors cellules ;
  - la CADENCE du journal de chaque cellule ( lignes VC, 2 s nominales ) ;
  - l'INDEPENDANCE : la connaissance croisee entre cellules, et le controle positif de ce journal ( la sonde ) ;
  - l'IDENTITE de chaque cellule ( la graine jouee est la graine demandee ) et la CONFORMITE de son monde a la table ;
  - les ERREURS SQF, attribuees a leur cellule par le chemin du fichier ;
  - la CENSURE : une cellule non finie a T_max n'a pas d'issue.

Usage : lire_multi.py <serveur.rpt> <dossier de l'episode> <job.json> <episode>   ( rend le JSON sur la sortie )
"""
import contextlib, io, json, math, os, re, statistics as st, sys

H = "/mnt/data/hmt"
sys.path.insert(0, f"{H}/depot/bancs/chacal")
import lire  # le lecteur du banc seul, inchange

rpt, out, jobf, ep = sys.argv[1:5]
job = json.load(open(jobf))
cellules = job["episodes"][str(ep)]
K = len(cellules)
RX_M = re.compile(r'"M\|(\d+)\|')
RX_FICHIER = re.compile(r"File .*?\\(c\d+|multi|initServer)[\\.]", re.I)

# ---------------- 1. demultiplexer ----------------
flux = {k: [] for k in range(0, K + 1)}
erreurs = {}          # cellule -> nombre
derniere_erreur = False
lignes_err = []
with open(rpt, "r", errors="ignore") as f:
    for l in f:
        m = RX_M.search(l)
        if m:
            k = int(m.group(1))
            flux.setdefault(k, []).append(l[:m.start()] + '"' + l[m.end():])
            continue
        if "Error in expression" in l or re.search(r"\bError\b.*(Undefined|Type|Missing|Generic|Zero divisor|Invalid)", l):
            derniere_erreur = True; lignes_err.append(l.strip()[:300])
        mf = RX_FICHIER.search(l)
        if mf and derniere_erreur:
            qui = mf.group(1).lower()
            cle = int(qui[1:]) if qui.startswith("c") else 0
            erreurs[cle] = erreurs.get(cle, 0) + 1
            derniere_erreur = False
if derniere_erreur: erreurs[-1] = erreurs.get(-1, 0) + 1

# ---------------- 2. chaque cellule, par le lecteur du banc seul ----------------
ref = {}
try: ref = json.load(open(f"{H}/depot/multi/emprises.json")).get("mondes", {})
except Exception: pass
res_cellules = {}
for k in range(1, K + 1):
    spec = cellules[k - 1]
    d = os.path.join(out, f"c{k}"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "serveur.rpt"), "w").writelines(flux.get(k, []))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: lire.main(os.path.join(d, "serveur.rpt"), os.path.join(d, "extrait"), spec["graine"])
        except Exception as e: print(json.dumps({"verdict": "REFUSE", "cause": f"LECTEUR_EN_ECHEC: {e}"}))
    try: r = json.loads(buf.getvalue())
    except Exception: r = {"verdict": "REFUSE", "cause": "LECTURE_ILLISIBLE"}
    e = r.get("entete", {})
    # identite : ce que la cellule a JOUE contre ce que le job a DEMANDE
    ecarts = []
    for cle in ("graine", "palier", "arret", "depart", "effectif"):
        attendu = spec.get(cle, job.get(cle))
        if attendu is None or cle not in e: continue
        try: ok = float(e[cle]) == float(attendu)
        except (TypeError, ValueError): ok = str(e[cle]) == str(attendu)
        if not ok: ecarts.append(f"{cle} demande {attendu}, joue {e[cle]}")
    if ecarts and r.get("verdict") == "ACCEPTE":
        r["verdict"] = "REFUSE"; r["cause_refus"] = "CELLULE_NON_CONFORME: " + " ; ".join(ecarts)
    # conformite du monde a la table ( le meme monde que dans le banc seul ? )
    conf = None
    o = r.get("opord") or e.get("opord") or []
    site = None
    for i in range(len(o) - 1):
        if o[i] == "site":
            try: site = [float(x) for x in str(o[i + 1]).strip("[]").split(",")[:2]]
            except Exception: pass
    rw = ref.get(str(spec["graine"]))
    if site and rw: conf = round(math.dist(site, rw["site"]), 1)
    # cadence du journal de la cellule : intervalles entre lignes VC est_sur_ouest
    tv = [float(x) for x in re.findall(r'CHACAL\|VC\|([0-9.]+)\|\d+\|est_sur_ouest', "".join(flux.get(k, [])))]
    iv = [b - a for a, b in zip(tv, tv[1:])]
    txt = "".join(flux.get(k, []))
    # le POULS : une boucle ordonnancee de 2 s qui ne fait rien ; son retard est celui de la logique de mission
    tp = [float(x) for x in re.findall(r'CHACAL\|C\|pouls\|([0-9.]+)', txt)]
    ip = [b - a for a, b in zip(tp, tp[1:])]
    p2d = re.search(r"CHACAL\|PH\|2\|APPROCHE\|debut\|([0-9.]+)", txt)
    p2f = re.search(r"CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)", txt)
    dec = re.search(r"CHACAL\|E\|choix_joue\|([0-9.]+)\|point\|TRAVERSEE\|choix\|(\d)\|detail\|([A-Z_]+)", txt)
    comp = re.search(r"CHACAL\|E\|compromis\|([0-9.]+)\|cause\|([A-Z_]+)\|phase\|(\d)", txt)
    res_cellules[str(k)] = {
        "graine": spec["graine"], "role": spec.get("role", ""), "verdict": r.get("verdict"),
        "cause_refus": r.get("cause_refus") or r.get("cause"),
        "portes_en_echec": [p for p, v in (r.get("portes") or {}).items() if not v],
        "issue": e.get("issue"), "compromis": e.get("compromis"), "alarme": e.get("alarme"), "vivants": e.get("vivants"),
        "compromis_cause": comp.group(2) if comp else None,
        "choix": int(dec.group(2)) if dec else None, "choix_detail": dec.group(3) if dec else None,
        "duree_phase2": round(float(p2f.group(1)) - float(p2d.group(1))) if (p2d and p2f) else None,
        "monde_ecart_m": conf, "erreurs_sqf": erreurs.get(k, 0),
        "cadence_mediane": round(st.median(iv), 2) if iv else None,
        "cadence_dans_bande": round(sum(1.8 <= x <= 2.5 for x in iv) / len(iv), 3) if iv else None,
        "pouls_mediane": round(st.median(ip), 2) if ip else None,
        "pouls_dans_bande": round(sum(1.8 <= x <= 2.5 for x in ip) / len(ip), 3) if ip else None, "pouls_n": len(ip),
        "lignes": len(flux.get(k, [])),
    }
    json.dump(r, open(os.path.join(d, "resultat.json"), "w"), indent=1, ensure_ascii=False)

# ---------------- 3. l'episode : charge, sonde, croisements, censure ----------------
m0 = "".join(flux.get(0, []))
fps = []
for mm in re.finditer(r"MULTI\|C\|fps\|([0-9.]+)\|images\|(\d+)\|reel_s\|([0-9.]+)\|fps_moteur\|([0-9.]+)\|fps_min\|([0-9.]+)\|unites\|(\d+)\|groupes\|(\d+)\|scripts\|(\[[^\]]*\])\|cellules_actives\|(\d+)", m0):
    t, im, rs = float(mm.group(1)), int(mm.group(2)), float(mm.group(3))
    fps.append({"t": t, "fps": im / rs if rs > 0 else 0, "unites": int(mm.group(6)), "actives": int(mm.group(9))})
def resume_fps(v):
    if not v: return None
    x = sorted(f["fps"] for f in v)
    return {"n": len(x), "mediane": round(st.median(x), 1), "p5": round(x[max(0, int(0.05 * len(x)) - 0)], 1) if len(x) > 1 else round(x[0], 1),
            "min": round(x[0], 1), "unites_max": max(f["unites"] for f in v)}
fps_tous = resume_fps([f for f in fps if f["actives"] == K])
fps_total = resume_fps(fps)
sonde = [(int(a), float(b)) for a, b in re.findall(r"MULTI\|E\|sonde\|[0-9.]+\|cycle\|\d+\|connue\|(-?\d)\|delai\|(-?[0-9.]+)", m0)]
masquees = sum(1 for c, d in sonde if c < 0)
sonde = [(c, d) for c, d in sonde if c >= 0]
delais = [d for c, d in sonde if c == 1]
cro = [(int(a), int(b), int(c), int(d)) for a, b, c, d in re.findall(r"MULTI\|E\|croise\|[0-9.]+\|chefs\|(\d+)\|ennemis\|(\d+)\|amis\|(\d+)\|controle_sonde\|(\d+)", m0)]
sonde_croisee = sum(int(x) for x in re.findall(r"MULTI\|E\|croise\|[^\"]*\|sonde_croisee\|(\d+)", m0))
det_enn = re.findall(r"MULTI\|E\|croise\|([0-9.]+)\|chefs\|\d+\|ennemis\|[1-9]\d*\|amis\|\d+\|controle_sonde\|\d+\|detail_ennemis\|(\[[^|]*\])", m0)
esp = [(int(a), int(b), int(c)) for a, b, c in re.findall(r"MULTI\|E\|espacement\|(\d+)\|(\d+)\|metres\|(\d+)", m0)]
cens = [int(x) for x in re.findall(r"MULTI\|E\|censure\|[0-9.]+\|cellule\|(\d+)", m0)]
fini = re.search(r"MULTI\|FINI\|([0-9.]+)\|cellules\|(\d+)\|finies\|(\d+)", m0)
montees = re.findall(r"MULTI\|OK\|cellule\|(\d+)\|montee\|(\d)\|duree_reelle\|([0-9.]+)", m0)
multi = {
    "fini": bool(fini), "k": K, "censurees": cens,
    "fps_toutes_actives": fps_tous, "fps_sur_l_episode": fps_total,
    "sonde": {"cycles": len(sonde), "masquees": masquees, "connues": len(delais), "delai_median": round(st.median(delais), 2) if delais else None,
              "delais": sorted(round(d, 1) for d in delais)},
    "croise": {"echantillons": len(cro), "ennemis": sum(c[1] for c in cro), "amis": sum(c[2] for c in cro),
               "controle_sonde_vu": sum(1 for c in cro if c[3] > 0), "sonde_croisee": sonde_croisee, "detail_ennemis": det_enn[:5]},
    "espacement_min": min((e[2] for e in esp), default=None), "espacements": esp,
    "montee": [(int(a), int(b), float(c)) for a, b, c in montees],
    "erreurs_sqf": erreurs, "exemples_erreurs": lignes_err[:4],
}
acceptees = [k for k, c in res_cellules.items() if c["verdict"] == "ACCEPTE"]
verdict = "ACCEPTE" if (fini and sum(erreurs.values()) == 0) else "REFUSE"
resume = (f"K={K} finies={fini.group(3) if fini else '?'} acceptees={len(acceptees)} censurees={len(cens)} "
          f"fps med={fps_tous['mediane'] if fps_tous else '?'} p5={fps_tous['p5'] if fps_tous else '?'} "
          f"sonde med={multi['sonde']['delai_median']} ({len(delais)}/{len(sonde)}) croise_ennemis={multi['croise']['ennemis']} "
          f"erreurs_sqf={sum(erreurs.values())}")
print(json.dumps({"verdict": verdict, "episode": ep, "resume": resume, "multi": multi, "cellules": res_cellules},
                 indent=1, ensure_ascii=False))
