"""Lecteur de SEUIL-PAR-MONDE-18-09 ( criteres : CRITERES_SEUIL_PAR_MONDE_18-09.md ). Un episode par ligne, puis la table
monde -> d*, puis les quatre predictions ecrites avant. La fumee FUMEE-BANC-JOURNAL-18-09 est lue avec ( meme instrument ).
Usage : python3 lire_seuil_par_monde.py [--md]"""
import glob, json, os, re, sys
H = "/mnt/data/hmt"; CAMPAGNES = ("FUMEE-BANC-JOURNAL-18-09", "SEUIL-PAR-MONDE-18-09"); md = "--md" in sys.argv
E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1[89]_*/job.json")):
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
        e = dict(version=j["version"], rejeu="REJEU" in j["version"], inst=j["instance"], monde=int(g[1:]), etat=etat, consigne=j["controle_dist"],
                 obs=int(j.get("observation", 300)), erreurs=len(re.findall(r"(?i)error in expression", t)), refuse="banc_refuse" in t)
        b = re.search(r'banc_perception\|([^"]*)', t)
        if b:
            f = b.group(1).split("|"); c = dict(zip(f[1::2], f[2::2]))
            e.update(ligne_de_vue=int(c.get("ligne_de_vue", -1)), hommes=c.get("hommes_avec_vue", "-"), azimut=c.get("azimut", "-"))
        L = [dict(zip(x.split("|")[1::2], x.split("|")[2::2])) for x in re.findall(r'"CHACAL\|E\|sonde_perception\|([^"]*)"', t)]
        if L:
            vm = [float(l["vis_moy"]) for l in L if float(l.get("vis_moy", -1)) >= 0]; vx = [float(l["vis_max"]) for l in L if float(l.get("vis_max", -1)) >= 0]
            e.update(sondes=len(L), distance=int(float(L[0]["verite_distance_menace"])), duree=int(L[-1]["depuis"]),
                     vue=next((int(l["depuis"]) for l in L if int(l["menaces_vues"]) > 0), None),
                     connue=next((int(l["depuis"]) for l in L if int(l["menaces_connues"]) > 0), None),
                     vis_moy=round(sum(vm) / len(vm), 2) if vm else None, vis_max=round(sum(vx) / len(vx), 2) if vx else None,
                     vis_debut=vm[0] if vm else None, angle=min((int(float(l["angle_min"])) for l in L if float(l["angle_min"]) >= 0), default=None))
        # valide : ligne de vue, pas de refus, 0 erreur, et un « jamais » seulement si la fenetre est allee au bout
        e["valide"] = (not e["refuse"]) and e.get("ligne_de_vue") == 1 and e["erreurs"] == 0 and e.get("sondes", 0) > 0 \
            and (e.get("connue") is not None or e.get("duree", 0) >= e["obs"] - 10)
        E.append(e)
print(f"{len(E)} episodes lus, {sum(e['valide'] for e in E)} valides, {sum(e['refuse'] for e in E)} refuses ( aucune ligne de vue ), "
      f"{sum(1 for e in E if e['etat'] == 'en vol')} en vol, {sum(e['erreurs'] for e in E)} erreur(s) SQF\n")
if md: print("| monde | consigne | distance vraie | instance | hommes avec vue | vue a | connue a | connue en 90 s | vis_moy | vis_max | angle mini | etat |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
for e in sorted(E, key=lambda e: (e["monde"], e.get("distance", 0))):
    c = [e["monde"], e["consigne"], e.get("distance", "-"), e["inst"], "REFUS" if e["refuse"] else e.get("hommes", "-"),
         "-" if e.get("vue") is None else f"{e['vue']} s", ("jamais" if e.get("sondes") else "-") if e.get("connue") is None else f"{e['connue']} s",
         "-" if not e.get("sondes") else ("oui" if (e.get("connue") is not None and e["connue"] <= 90) else "non"), e.get("vis_moy", "-"), e.get("vis_max", "-"), e.get("angle", "-"),
         e["etat"] + (" REJEU" if e["rejeu"] else "") + ("" if e["valide"] else " ( exclu )")]
    print(("| " + " | ".join(str(x) for x in c) + " |") if md else "  ".join(str(x).ljust(w) for x, w in zip(c, (3, 5, 5, 3, 5, 5, 7, 4, 5, 5, 4, 20))))
V = [e for e in E if e["valide"] and not e["rejeu"]]
print("\n== TABLE monde -> d* ( milieu entre le plus loin CONNU et le plus pres JAMAIS ; en 600 s, puis en 90 s )")
seuils = {}
for m in sorted(set(e["monde"] for e in V)):
    P = sorted((e for e in V if e["monde"] == m), key=lambda e: e["distance"]); ligne = []
    for nom, borne in (("600 s", 10 ** 9), ("90 s", 90)):
        co = [e["distance"] for e in P if e["connue"] is not None and e["connue"] <= borne]; ja = [e["distance"] for e in P if e["connue"] is None or e["connue"] > borne]
        if co and ja and max(co) < min(ja): ds = (max(co) + min(ja)) / 2; txt = f"d* = {ds:.0f} m [ {max(co)} ; {min(ja)} ]"
        elif co and ja: ds = None; txt = f"INVERSION ( connu jusqu a {max(co)} m, jamais des {min(ja)} m )"
        elif co: ds = None; txt = f"> {max(co)} m ( tout connu )"
        else: ds = None; txt = f"< {min(ja)} m ( rien de connu )"
        if nom == "600 s": seuils[m] = ds if ds else (max(co) if co and not ja else (min(ja) if ja and not co else (max(co) + min(ja)) / 2))
        ligne.append(f"{nom} : {txt}")
    print(f"   monde {m:2d} : " + " | ".join(ligne) + "   points : " + " ; ".join(f"{e['distance']} m {'jamais' if e['connue'] is None else str(e['connue']) + ' s'} v={e['vis_moy']}" for e in P))
if seuils:
    print("\n== PREDICTION 1 ( LIEU ) : etalement des d* = " + f"{max(seuils.values()) - min(seuils.values()):.0f} m sur {len(seuils)} mondes ( > 30 m attendu )")
print("== PREDICTION 2 ( DELAI ) : par monde, delai du connu le plus lointain contre le plus proche")
for m in sorted(set(e["monde"] for e in V)):
    K = sorted((e for e in V if e["monde"] == m and e["connue"] is not None), key=lambda e: e["distance"])
    if len(K) >= 2: print(f"   monde {m:2d} : {K[0]['distance']} m {K[0]['connue']} s -> {K[-1]['distance']} m {K[-1]['connue']} s : {'s allonge' if K[-1]['connue'] > K[0]['connue'] else 'ne s allonge pas'}")
pres = [e for e in V if e["monde"] in seuils and e.get("vis_moy") is not None and abs(e["distance"] - seuils[e["monde"]]) <= 0.2 * seuils[e["monde"]]]
co = [e["vis_moy"] for e in pres if e["connue"] is not None]; ja = [e["vis_moy"] for e in pres if e["connue"] is None]
if co and ja:
    auc = sum((1 if a > b else 0.5 if a == b else 0) for a in co for b in ja) / (len(co) * len(ja))
    print(f"== PREDICTION 3 ( DEUXIEME VARIABLE ) : vis_moy des connus {sorted(co)} contre jamais {sorted(ja)} ; aire sous la courbe = {auc:.2f} ( >= 0,75 retenue, <= 0,60 rejetee )")
else: print("== PREDICTION 3 : pas encore de connus ET de jamais pres des seuils")
R = [e for e in E if e["rejeu"] and e["valide"]]
for r in R:
    o = [e for e in V if e["monde"] == r["monde"] and e["consigne"] == r["consigne"]]
    if o: print(f"== PREDICTION 4 ( DETERMINISME ) monde {r['monde']} a {r['consigne']} m : original {o[0]['distance']} m {'jamais' if o[0]['connue'] is None else str(o[0]['connue']) + ' s'} ( azimut {o[0].get('azimut')} ) ; rejeu {r['distance']} m {'jamais' if r['connue'] is None else str(r['connue']) + ' s'} ( azimut {r.get('azimut')} )")
