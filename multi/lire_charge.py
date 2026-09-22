"""Lecture UNIQUE du balayage de charge C3 ( multi/CRITERES_MULTI.md, amendement 1 ). Usage : lire_charge.py <dossier du run>

Par K : FPS ( images mesurees pendant que les K cellules sont toutes actives ), delai de la sonde, cadence du journal
des cellules, erreurs SQF, connaissance ennemie croisee. K* = le plus grand K qui passe toutes les portes.
Le taux de compromission par K est RAPPORTE, jamais garde."""
import glob, json, re, statistics as st, sys
from collections import defaultdict

R = sys.argv[1]
job = json.load(open(f"{R}/job.json"))
parK = defaultdict(lambda: {"fps": [], "sonde": [], "sonde_cycles": 0, "iv": [], "sqf": 0, "croise": 0, "controle": 0,
                            "episodes": 0, "cellules": 0, "acceptees": 0, "compromis": [], "censurees": 0, "duree": []})
for g in sorted(glob.glob(f"{R}/g*/resultat.json"), key=lambda p: int(re.search(r"/g(\d+)/", p).group(1))):
    e = re.search(r"/g(\d+)/", g).group(1)
    d = json.load(open(g))
    cel = job["episodes"][e]; K = len(cel)
    P = parK[K]; P["episodes"] += 1
    m = d.get("multi", {})
    rpt = open(g.replace("resultat.json", "serveur.rpt"), errors="ignore").read()
    for mm in re.finditer(r"MULTI\|C\|fps\|[0-9.]+\|images\|(\d+)\|reel_s\|([0-9.]+)\|.*?\|cellules_actives\|(\d+)", rpt):
        if int(mm.group(3)) == K and float(mm.group(2)) > 0: P["fps"].append(int(mm.group(1)) / float(mm.group(2)))
    P["sonde"] += m.get("sonde", {}).get("delais", []); P["sonde_cycles"] += m.get("sonde", {}).get("cycles", 0)
    P["sqf"] += sum(int(v) for v in (m.get("erreurs_sqf") or {}).values())
    P["croise"] += m.get("croise", {}).get("ennemis", 0); P["controle"] += m.get("croise", {}).get("controle_sonde_vu", 0)
    P["censurees"] += len(m.get("censurees", []))
    for k, c in d.get("cellules", {}).items():
        P["cellules"] += 1; P["acceptees"] += c.get("verdict") == "ACCEPTE"
        if c.get("verdict") == "ACCEPTE" and c.get("compromis") is not None: P["compromis"].append(int(c["compromis"]))
        if c.get("duree_phase2") is not None: P["duree"].append(c["duree_phase2"])
        # porte de cadence ( amendement 3 ) : le POULS de la cellule, boucle ordonnancee de 2 s qui ne fait rien d'autre
        tv = [float(x) for x in re.findall(r'CHACAL\|C\|pouls\|([0-9.]+)', open(f"{R}/g{e}/c{k}/serveur.rpt", errors="ignore").read())]
        P["iv"] += [b - a for a, b in zip(tv, tv[1:])]

def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))] if v else None
ref = parK.get(1)
ref_fps = st.median(ref["fps"]) if ref and ref["fps"] else None
ref_sonde = st.median(ref["sonde"]) if ref and ref["sonde"] else None
ref_cad = (sum(1.8 <= x <= 2.5 for x in ref["iv"]) / len(ref["iv"])) if ref and ref["iv"] else None
porte_cad = 0.95 if (ref_cad is None or ref_cad >= 0.95) else ref_cad - 0.02
print(f"reference K=1 : fps mediane {ref_fps and round(ref_fps, 1)}, sonde mediane {ref_sonde}, cadence {ref_cad and round(ref_cad, 3)} -> porte de cadence {round(porte_cad, 3)}")
passe = {}
for K in sorted(parK):
    P = parK[K]
    fm = st.median(P["fps"]) if P["fps"] else None; f5 = q(P["fps"], 0.05)
    sm = st.median(P["sonde"]) if P["sonde"] else None
    cad = (sum(1.8 <= x <= 2.5 for x in P["iv"]) / len(P["iv"])) if P["iv"] else None
    portes = {
        "fps_mediane": fm is not None and ref_fps is not None and fm >= ref_fps - 3,
        "fps_p5": f5 is not None and f5 >= 20,
        "sonde_bande": sm is not None and 3 <= sm <= 11,
        "sonde_ref": sm is not None and ref_sonde is not None and sm <= ref_sonde + 3,
        "cadence": cad is not None and cad >= porte_cad,
        "sqf": P["sqf"] == 0, "croise": P["croise"] == 0,
    }
    passe[K] = all(portes.values())
    comp = (sum(P["compromis"]) / len(P["compromis"])) if P["compromis"] else None
    print(f"\nK={K} : {P['episodes']} episodes, {P['cellules']} cellules, {P['acceptees']} acceptees, {P['censurees']} censurees")
    print(f"   fps mediane {fm and round(fm, 1)}  p5 {f5 and round(f5, 1)}  ( {len(P['fps'])} mesures de 2 s, toutes cellules actives )")
    print(f"   sonde : mediane {sm}  ( {len(P['sonde'])} connues sur {P['sonde_cycles']} cycles ) ; pouls dans [1,8 ; 2,5] : {cad and round(cad, 3)}")
    print(f"   erreurs SQF {P['sqf']} ; connaissance ennemie croisee {P['croise']} ; controle du journal croise vu {P['controle']} fois")
    print(f"   RAPPORTE : compromission {comp and round(comp, 3)} ( n = {len(P['compromis'])} ) ; duree de phase 2 mediane {st.median(P['duree']) if P['duree'] else None} s")
    print("   portes : " + " ".join(f"{k}={'OK' if v else 'NON'}" for k, v in portes.items()) + f"  ->  {'PASSE' if passe[K] else 'ECHOUE'}")
ks = [K for K in sorted(passe) if passe[K]]
kstar = max(ks) if ks else None
print(f"\nK* = {kstar}" + ("" if kstar is None else f"  ( plafond geographique a 3 km : 5 )"))
