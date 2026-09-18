"""Lecteur general du banc de perception ( nuit du 18 au 19/09 ) : PORTEE, ACCROUPI, BALAYAGE. Un episode par ligne ( --detail ), puis
les parts connues par case. Validite ecrite dans les criteres de chaque campagne :
  ligne de vue = 1, pas de refus, 0 erreur SQF, vis_moy > 0,01 ( cible reelle non masquee ), un « jamais » seulement si la fenetre est
  allee au bout ; en regard centre ( mode 5 ) l angle de la premiere sonde doit etre <= 5 deg.
Usage : python3 lire_banc_v3.py CAMPAGNE [CAMPAGNE ...] [--detail] [--md] [--fenetre 90]"""
import glob, json, os, re, statistics, sys
H = "/mnt/data/hmt"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
detail, md = "--detail" in sys.argv, "--md" in sys.argv
FEN = int(sys.argv[sys.argv.index("--fenetre") + 1]) if "--fenetre" in sys.argv else 90
if "--fenetre" in sys.argv: args.remove(str(FEN))
TR = [(0, 125), (125, 175), (175, 225), (225, 275), (275, 350), (350, 450), (450, 550), (550, 700)]


def tranche(d): return next((f"{a}-{b}" for a, b in TR if a <= d < b), "700+")


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1[89]_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") not in args: continue
    d = os.path.dirname(jf)
    for g in sorted(x for x in os.listdir(d) if re.fullmatch(r"g\d+(_r\d+)?", x)):
        rpt = f"{d}/{g}/serveur.rpt"; etat = "fini"
        if not os.path.exists(rpt):
            v = sorted(glob.glob(f"/mnt/c/Users/Younes/hmtech{j['instance']}/*.rpt"), key=os.path.getmtime)
            if not v: continue
            rpt, etat = v[-1], "en vol"
        t = open(rpt, encoding="utf-8", errors="ignore").read()
        e = dict(campagne=j["campagne"], version=j["version"], inst=j["instance"], monde=int(re.match(r"g(\d+)", g).group(1)), etat=etat,
                 jour=int(j.get("jour", 0)), consigne=j.get("controle_dist"), mode=int(j.get("controle_perception", 0)), posture=int(j.get("controle_posture", 0)),
                 az=int(j.get("controle_az", 0)), obs=int(j.get("observation", 300)), erreurs=len(re.findall(r"(?i)error in expression", t)), refuse="banc_refuse" in t)
        b = re.search(r'banc_perception\|([^"]*)', t)
        if b:
            f = b.group(1).split("|"); c = dict(zip(f[1::2], f[2::2]))
            e.update(ligne_de_vue=int(c.get("ligne_de_vue", -1)), hommes=c.get("hommes_avec_vue", "-"), essais=c.get("essais", "-"), vis_pose=c.get("vis_pose", "-"))
        L = [dict(zip(x.split("|")[1::2], x.split("|")[2::2])) for x in re.findall(r'"CHACAL\|E\|sonde_perception\|([^"]*)"', t)]
        if L:
            vm = [float(l["vis_moy"]) for l in L if float(l.get("vis_moy", -1)) >= 0]; A = [float(l["angle_min"]) for l in L if float(l["angle_min"]) >= 0]
            e.update(sondes=len(L), distance=int(float(L[0]["verite_distance_menace"])), duree=int(L[-1]["depuis"]),
                     vue=next((int(l["depuis"]) for l in L if int(l["menaces_vues"]) > 0), None),
                     connue=next((int(l["depuis"]) for l in L if int(l["menaces_connues"]) > 0), None),
                     vis_moy=round(sum(vm) / len(vm), 2) if vm else None, angle1=int(A[0]) if A else None, angle_min=int(min(A)) if A else None,
                     tirs=len(re.findall(r"CHACAL\|E\|tir\|", t)))
        pourquoi = []
        if e["refuse"]: pourquoi.append("refus")
        if e.get("ligne_de_vue") != 1 and not e["refuse"]: pourquoi.append("pas de ligne banc")
        if e["erreurs"]: pourquoi.append("erreur SQF")
        if not e.get("sondes"): pourquoi.append("pas de sonde")
        elif (e.get("vis_moy") or 0) <= 0.01: pourquoi.append("cible masquee")
        if e.get("sondes") and e["mode"] == 5 and (e.get("angle1") is None or e["angle1"] > 5): pourquoi.append("regard non centre")
        if e.get("sondes") and e.get("connue") is None and e.get("duree", 0) < e["obs"] - 10: pourquoi.append("fenetre inachevee")
        e["valide"] = not pourquoi; e["pourquoi"] = ", ".join(pourquoi)
        E.append(e)
V = [e for e in E if e["valide"]]
print(f"{', '.join(args)} : {len(E)} episodes lus, {len(V)} valides, {sum(e['refuse'] for e in E)} refus ( aucune ligne de vue ), "
      f"{sum(1 for e in E if 'cible masquee' in e['pourquoi'])} cibles masquees, {sum(1 for e in E if e['etat'] == 'en vol')} en vol, {sum(e['erreurs'] for e in E)} erreur(s) SQF")
if detail:
    print("\nmonde ecl. mode post az   consigne vraie  hommes essais vis_pose vis_moy angle1  vue   connue   etat")
    for e in sorted(E, key=lambda e: (e["jour"], e["mode"], e["posture"], e["az"], e.get("distance", 0), e["monde"])):
        print(f"{e['monde']:4d}  {'jour' if e['jour'] else 'nuit'} {e['mode']:3d} {e['posture']:4d} {e['az']:4d} {str(e['consigne']):>7s} {str(e.get('distance', '-')):>6s} {str(e.get('hommes', '-')):>6s} {str(e.get('essais', '-')):>5s} "
              f"{str(e.get('vis_pose', '-')):>8s} {str(e.get('vis_moy', '-')):>7s} {str(e.get('angle1', '-')):>6s} {('-' if e.get('vue') is None else str(e['vue']) + ' s'):>5s} "
              f"{(('jamais' if e.get('sondes') else '-') if e.get('connue') is None else str(e['connue']) + ' s'):>8s}   {e['etat']}{'' if e['valide'] else ' ( exclu : ' + e['pourquoi'] + ' )'}")
print(f"\n== PARTS CONNUES PAR CASE ( episodes valides ; « en {FEN} s » = la fenetre de la mission )")
cases = {}
for e in V: cases.setdefault((e["jour"], e["mode"], e["posture"], e["az"], tranche(e["distance"])), []).append(e)
if md: print(f"| eclairage | mode | posture | ecart d azimut | distance vraie | n | connue ( fenetre entiere ) | connue en {FEN} s | delai median des connus | mondes |\n|---|---|---|---|---|---|---|---|---|---|")
for k in sorted(cases, key=lambda k: (k[0], k[1], k[2], k[3], int(k[4].split("-")[0].replace("+", "")))):
    L = cases[k]; K = [e for e in L if e["connue"] is not None]; K90 = [e for e in K if e["connue"] <= FEN]
    med = f"{statistics.median(e['connue'] for e in K):.0f} s" if K else "-"
    c = ["jour" if k[0] else "nuit", k[1], "accroupie" if k[2] else "debout", f"{k[3]} deg", k[4] + " m", len(L), f"{len(K)}/{len(L)}", f"{len(K90)}/{len(L)} = {len(K90) / len(L):.0%}", med, sorted({e["monde"] for e in L})]
    print(("| " + " | ".join(str(x) for x in c) + " |") if md else "   " + "  ".join(str(x).ljust(w) for x, w in zip(c, (5, 3, 10, 8, 10, 3, 7, 14, 6, 30))))
