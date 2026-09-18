"""Lecteur unique du banc de perception ( 18/09 ) : toutes les campagnes du banc, un episode par ligne, puis le tableau des
points VALIDES. Un episode est valide si ligne_de_vue = 1, si le canal geometrique a VU la cible au moins une fois, sans banc_refuse ni erreur SQF.
La distance lue est la distance VRAIE ( verite_distance_menace de la premiere sonde ), pas la consigne.
Usage : python3 lire_banc_seuil.py [--md]"""
import glob, json, os, re, sys
H = "/mnt/data/hmt"
CAMPAGNES = ("BANC-PERCEPTION-18-09", "BANC-TROU-18-09", "FUMEE-BANC-VUE-FINE-18-09", "BANC-SEUIL-18-09")
md = "--md" in sys.argv
E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-18_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") not in CAMPAGNES: continue
    d = os.path.dirname(jf)
    for g in sorted(x for x in os.listdir(d) if re.fullmatch(r"g\d+", x)):
        rpt = f"{d}/{g}/serveur.rpt"; etat = "fini"
        if not os.path.exists(rpt):
            v = sorted(glob.glob(f"/mnt/c/Users/Younes/hmtech{j['instance']}/*.rpt"), key=os.path.getmtime)
            if not v: continue
            rpt, etat = v[-1], "en vol"
        t = open(rpt, encoding="utf-8", errors="ignore").read()
        e = dict(campagne=j["campagne"], banc=j["banc"], run=os.path.basename(d), monde=g, etat=etat, jour=int(j.get("jour", 0)),
                 consigne=j.get("controle_dist"), erreurs=len(re.findall(r"(?i)error in expression", t)), refuse="banc_refuse" in t)
        b = re.search(r'banc_perception\|([^"]*)', t)
        if b:
            f = b.group(1).split("|"); c = dict(zip(f[1::2], f[2::2]))
            e.update(ligne_de_vue=int(c.get("ligne_de_vue", -1)), hommes_avec_vue=c.get("hommes_avec_vue", "-"), vue_reelle=c.get("vue_reelle", "-"))
        L = [dict(zip(x.split("|")[1::2], x.split("|")[2::2])) for x in re.findall(r'"CHACAL\|E\|sonde_perception\|([^"]*)"', t)]
        if L:
            e.update(sondes=len(L), distance_vraie=int(float(L[0]["verite_distance_menace"])),
                     vue=next((int(l["depuis"]) for l in L if int(l["menaces_vues"]) > 0), None),
                     connue=next((int(l["depuis"]) for l in L if int(l["menaces_connues"]) > 0), None), duree=int(L[-1]["depuis"]))
            # ! L ANGLE DU REGARD ( ajout du 18/09, 16 h 40 ) : « regardee » doit se PROUVER. angle_min = plus petit ecart regard-cible
            # parmi les hommes. On garde l angle au debut, le plus petit de la fenetre, et l angle au moment ou la cible devient connue.
            def ang(l):   # le banc du matin ecrit « any » ( BIS_fnc_lowest inexistant ) : angle illisible, pas nul
                try: v = float(l.get("angle_min", "")); return int(v) if v >= 0 else None
                except ValueError: return None
            A = [ang(l) for l in L if ang(l) is not None]
            e.update(angle_debut=A[0] if A else None, angle_mini=min(A) if A else None,
                     angle_connue=next((ang(l) for l in L if int(l["menaces_connues"]) > 0), None),
                     tirs=len(re.findall(r"CHACAL\|E\|tir\|", t)))
        # ! Le banc du matin ( BANC-PERCEPTION ) porte ~57 erreurs par episode : BIS_fnc_lowest, inexistant, dans le seul champ
        # angle_min de la sonde ( corrige par b862eca ). Elles ne touchent pas la connaissance : on les compte sans exclure.
        erreurs_ok = e["erreurs"] == 0 or e["campagne"] == "BANC-PERCEPTION-18-09"
        # ! VUE = le canal geometrique de la mission a vu la cible au moins une fois : second temoin de la ligne de vue.
        # ( matin, 100 m monde 4 : ligne_de_vue = 1 depuis le chef, mais jamais vue ni connue - l ancien drapeau ne suffisait pas. )
        e["valide"] = (not e["refuse"]) and e.get("ligne_de_vue") == 1 and erreurs_ok and e.get("sondes", 0) > 0 and e.get("vue") is not None \
            and (e.get("connue") is not None or e.get("duree", 0) >= 290)   # un « jamais » ne compte qu une fois la fenetre finie
        E.append(e)
print(f"{len(E)} episodes lus, {sum(e['valide'] for e in E)} valides, {sum(e['refuse'] for e in E)} refuses par le banc, "
      f"{sum(1 for e in E if e.get('ligne_de_vue') == 0)} sans ligne de vue ( ancien banc ), {sum(e['erreurs'] for e in E)} erreur(s) SQF\n")
sep = " | " if md else "  "
if md: print("| campagne | monde | jour | consigne | distance vraie | ligne de vue | hommes avec vue | vue reelle | vue a | connue a | etat |\n|---|---|---|---|---|---|---|---|---|---|---|")
for e in E:
    c = [e["campagne"].replace("-18-09", ""), e["monde"], "jour" if e["jour"] else "nuit", e["consigne"], e.get("distance_vraie", "-"),
         "REFUS" if e["refuse"] else e.get("ligne_de_vue", "-"), e.get("hommes_avec_vue", "-"), e.get("vue_reelle", "-"),
         "-" if e.get("vue") is None else f"{e['vue']} s", ("jamais" if e.get("sondes") else "-") if e.get("connue") is None else f"{e['connue']} s",
         e["etat"] + ("" if e["valide"] else " ( exclu )")]
    print(("| " + " | ".join(str(x) for x in c) + " |") if md else sep.join(str(x).ljust(w) for x, w in zip(c, (22, 3, 4, 6, 5, 5, 3, 3, 5, 7, 16))))
for jour in (0, 1):
    V = sorted((e for e in E if e["valide"] and e["jour"] == jour), key=lambda e: e["distance_vraie"])
    if not V: continue
    print(f"\n== POINTS VALIDES, {'JOUR' if jour else 'NUIT'} ( distance vraie : connue a / jamais, monde )")
    print("   " + " ; ".join(f"{e['distance_vraie']} m {'jamais' if e['connue'] is None else str(e['connue']) + ' s'} ({e['monde']})" for e in V))
    print("   angle du regard ( debut / mini / a la connaissance ) : " + " ; ".join(
        f"{e['distance_vraie']} m {e.get('angle_debut')}/{e.get('angle_mini')}/{'-' if e.get('angle_connue') is None else e['angle_connue']}" for e in V if e['distance_vraie'] >= 140))
    co = [e["distance_vraie"] for e in V if e["connue"] is not None]; ja = [e["distance_vraie"] for e in V if e["connue"] is None]
    if co and ja:
        print(f"   plus loin CONNUE : {max(co)} m ; plus pres JAMAIS : {min(ja)} m ; delais connus : {sorted(set(e['connue'] for e in V if e['connue'] is not None))} s"
              + ( "" if max(co) < min(ja) else "  !! INVERSION : un point connu plus loin qu un point jamais connu" ))
