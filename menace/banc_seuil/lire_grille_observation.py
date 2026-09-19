"""Lecture de la grille VARIANCE-OBS-a<avant>-b<balayage>-19-09 ( criteres : CRITERES_VARIANCE_OBSERVATION_19-09.md ).
Pour chaque reglage : les deux portes de menace/lire_variance.py ( INCHANGE, appele tel quel ), la part connue ( niveau 2 ), et le garde-fou de
mission ( part des episodes ou la phase 2 finit compromise ou avec des pertes ). Puis la regle de choix ecrite d avance."""
import glob, json, os, re, subprocess
H = "/mnt/data/hmt"; R = []
for a in (260, 180, 120):
    for b in (0, 1):
        camp = f"VARIANCE-OBS-a{a}-b{b}-19-09"
        out = subprocess.run(["python3", f"{H}/depot/menace/lire_variance.py", camp], capture_output=True, text=True).stdout
        p1 = "PORTE, part globale 30-70 % : OK" in out; p2 = "PORTE, variance A L INTERIEUR d un monde : OK" in out
        E = []
        for jf in glob.glob(f"{H}/runs/2026-09-19_*/job.json"):
            j = json.load(open(jf))
            if j.get("campagne") != camp: continue
            for d in glob.glob(os.path.dirname(jf) + "/g*/"):
                try: v = json.load(open(d + "resultat.json")).get("verdict"); t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
                except Exception: continue
                dec = re.search(r'"CHACAL\|E\|decision\|[^"]*point\|TRAVERSEE[^"]*menace_percue\|(\d)\|menaces_vues\|(\d+)\|menaces_connues\|(\d+)', t)
                fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[^|]*\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
                reg = re.search(r'reglage_observation\|[^|]*\|phase\|2\|avant\|(\d+)\|balayage\|(\d+)\|distance_secteur\|(-?\d+)', t)
                E.append(dict(v=v, err=len(re.findall(r"(?i)error in expression", t)), percue=int(dec.group(1)) if dec else None,
                              abime=int(fin is None or fin.group(3) != "0" or fin.group(2) != "10"), dsect=int(reg.group(3)) if reg else None,
                              regle=(int(reg.group(1)), int(reg.group(2))) if reg else None))
        A = [e for e in E if e["v"] == "ACCEPTE" and e["err"] == 0 and e["percue"] is not None]
        n = len(A)
        R.append(dict(a=a, b=b, n=n, lus=len(E), p1=p1, p2=p2, percue=sum(e["percue"] > 0 for e in A) / n if n else None, connue=sum(e["percue"] == 2 for e in A) / n if n else None,
                      abime=sum(e["abime"] for e in A) / n if n else None, dsect=sorted(e["dsect"] for e in A if e["dsect"] is not None), conforme=all(e["regle"] == (a, b) for e in A)))
print(" avant balayage   n ( lus )   percue > 0   connue ( niv. 2 )   phase 2 abimee   observe depuis ( m )   reglage joue   porte globale   porte intra-monde")
for r in R:
    if not r["n"]: print(f" {r['a']:5d} {r['b']:8d}   0 ( {r['lus']} )"); continue
    print(f" {r['a']:5d} {r['b']:8d} {r['n']:4d} ( {r['lus']:2d} )   {r['percue']:9.0%}   {r['connue']:15.0%}   {r['abime']:13.0%}   {r['dsect'][0]:4d} - {r['dsect'][-1]:4d}            {'conforme' if r['conforme'] else 'ECART'}     {'OK' if r['p1'] else 'ECHEC':6s}          {'OK' if r['p2'] else 'ECHEC'}")
adm = [r for r in R if r["n"] and r["p1"] and r["p2"] and r["abime"] <= 0.25 and r["conforme"]]
print("\n REGLE ECRITE D AVANCE : admissible = deux portes OK et phase 2 abimee <= 25 % ; on retient la part CONNUE la plus proche de 50 %, a egalite le plus proche de l origine")
if not adm: print(" -> AUCUN REGLAGE ADMISSIBLE : la campagne P2 ne part pas.")
else:
    c = sorted(adm, key=lambda r: (abs(r["connue"] - 0.5), -r["a"], r["b"]))[0]
    print(f" -> admissibles : {[(r['a'], r['b']) for r in adm]} ; RETENU : avant = {c['a']} m, balayage = {c['b']} ( percue {c['percue']:.0%}, connue {c['connue']:.0%}, phase 2 abimee {c['abime']:.0%} )")
