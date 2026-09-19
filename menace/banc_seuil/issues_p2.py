"""Candidats d issue pour la phase 2, sur les 120 episodes joues. TOUS BRAS CONFONDUS : on juge la capacite de
l issue a discriminer, jamais l effet d une option ou d un type.
! CORRECTION : la liste est_sur_ouest contient parfois une entite qui n est PAS du detachement ( identifiant
apparu en cours d episode ). On ne garde que les identifiants presents au PREMIER echantillon de la phase 2."""
import glob, json, os, re, statistics as st
H = "/mnt/data/hmt"
L = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "CHOIX-P2-TYPES-19-09": continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        deb = re.search(r'"CHACAL\|PH\|2\|APPROCHE\|debut\|([0-9.]+)', t)
        fin = re.search(r'"CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        if not (deb and fin): continue
        t0, t1 = float(deb.group(1)), float(fin.group(1))
        ech = []
        for m in re.finditer(r'"CHACAL\|VC\|([0-9.]+)\|\d\|est_sur_ouest\|(\[\[.*?\]\])"', t):
            ts = float(m.group(1))
            if t0 <= ts <= t1:
                try: ech.append((ts, json.loads(m.group(2))))
                except Exception: pass
        if not ech: continue
        nos = {a[0] for a in ech[0][1]}                       # le detachement, tel qu il est au debut de la phase
        vus, pic = 0, 0.0
        for ts, v in ech:
            mx = max((float(a[1]) for a in v if a[0] in nos), default=0.0)
            pic = max(pic, mx)
            if mx > 0.05: vus += 1
        L.append(dict(duree=t1 - t0, issue=fin.group(2), vivants=int(fin.group(3)), compromis=int(fin.group(4)),
                      alarme=int(fin.group(5)), n_hommes=len(nos),
                      discrete=int(fin.group(4) == "0" and fin.group(5) == "0" and fin.group(3) == "10"),
                      part_vu=vus / len(ech), pic=pic))

def bina(nom, xs):
    p = sum(xs) / len(xs)
    print(f"   {nom:38s} : {p:5.0%}   ( {'PLAFOND' if p > 0.8 else 'PLANCHER' if p < 0.2 else 'EXPLOITABLE'} )")

def cont(nom, xs):
    q = st.quantiles(xs, n=4)
    z = sum(1 for x in xs if x <= 1e-9) / len(xs)
    print(f"   {nom:38s} : mediane {st.median(xs):8.2f}  quartiles {q[0]:8.2f} / {q[2]:8.2f}  max {max(xs):8.2f}  "
          f"ecart-type {st.pstdev(xs):7.2f}  a zero {z:4.0%}")

print(f"== {len(L)} episodes ; detachement de {st.mode([e['n_hommes'] for e in L])} hommes suivis\n")
print("A. ISSUE ACTUELLE"); bina("phase_discrete", [e["discrete"] for e in L])
print("\nB. BINAIRES PLUS EXIGEANTES")
bina("discrete ET jamais vue ( pic <= 0,05 )", [int(e["discrete"] and e["pic"] <= 0.05) for e in L])
bina("discrete ET moins de 400 s", [int(e["discrete"] and e["duree"] < 400) for e in L])
bina("jamais vue, quoi qu il arrive", [int(e["pic"] <= 0.05) for e in L])
bina("aucune compromission", [int(e["compromis"] == 0) for e in L])
print("\nC. CONTINUES")
cont("part du temps ou l ennemi nous connait", [e["part_vu"] for e in L])
cont("pic de connaissance ennemie ( 0 a 4 )", [e["pic"] for e in L])
cont("duree de la phase 2 ( s )", [e["duree"] for e in L])
print("\nD. REPERES")
print(f"   fins : {dict((k, sum(1 for e in L if e['issue'] == k)) for k in sorted({e['issue'] for e in L}))}")
print(f"   episodes ou l ennemi nous connait au moins une fois : {sum(1 for e in L if e['pic'] > 0.05) / len(L):.0%}")
