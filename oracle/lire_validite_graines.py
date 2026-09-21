"""Test de validite des graines neuves ( regle : oracle/CRITERES_CALIBRATION_V2.md ). Ne lit AUCUNE issue.
Valide = accepte par le banc, non VOID, fin de phase 2 atteinte, ligne de carte presente."""
import glob, json, os, re
H = "/mnt/data/hmt"
res = {}
for jf in sorted(glob.glob(f"{H}/runs/2026-09-2*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "VALIDITE-GRAINES-21-09": continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        w = int(re.search(r"/g(\d+)", d).group(1))
        r = dict(accepte=False, void=False, fin_p2=False, carte=None, cause="")
        try: r["accepte"] = json.load(open(d + "resultat.json")).get("verdict") == "ACCEPTE"
        except Exception: r["cause"] = "pas de resultat"
        try:
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
            r["void"] = "CHACAL|FINI|VOID" in t
            if r["void"]:
                m = re.search(r"CHACAL\|FINI\|VOID\|([A-Z_]+)", t); r["cause"] = m.group(1) if m else "VOID"
            r["fin_p2"] = bool(re.search(r"CHACAL\|PH\|2\|APPROCHE\|fin\|", t))
            c = re.search(r"CHACAL\|O\|carte\|[^\"]*\|cases_routieres\|(\d+)\|", t)
            r["carte"] = int(c.group(1)) if c else None
        except Exception: pass
        res[w] = r
ok = [w for w in sorted(res) if res[w]["accepte"] and not res[w]["void"] and res[w]["fin_p2"] and res[w]["carte"] is not None]
print(f"{'graine':>6} {'accepte':>8} {'VOID':>5} {'fin_p2':>7} {'cases_rte':>10}  cause")
for w in sorted(res):
    r = res[w]
    print(f"{w:>6} {str(r['accepte']):>8} {str(r['void']):>5} {str(r['fin_p2']):>7} {str(r['carte']):>10}  {r['cause']}")
retenues = ok[:8]
print(f"\nvalides, dans l ordre : {ok}")
print(f"RETENUES ( 8 premieres ) : {retenues}" if len(retenues) == 8 else f"SEULEMENT {len(retenues)} VALIDES : il faut tester 25 a 31")
