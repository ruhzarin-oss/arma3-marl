import glob, json, os, re, sys
H = "/mnt/data/hmt"; camp = sys.argv[1] if len(sys.argv) > 1 else "FUMEE-BANC-JOURNAL-18-09"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1[89]_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != camp: continue
    d = os.path.dirname(jf)
    for g in sorted(x for x in os.listdir(d) if re.fullmatch(r"g\d+", x)):
        rpt = f"{d}/{g}/serveur.rpt"; etat = "fini"
        if not os.path.exists(rpt):
            v = sorted(glob.glob(f"/mnt/c/Users/Younes/hmtech{j['instance']}/*.rpt"), key=os.path.getmtime)
            if not v: print(j["version"], g, "pas de RPT"); continue
            rpt, etat = v[-1], "en vol"
        t = open(rpt, encoding="utf-8", errors="ignore").read()
        err = re.findall(r"(?i)error in expression[^\n]*\n[^\n]*\n[^\n]*", t)
        L = [dict(zip(x.split("|")[1::2], x.split("|")[2::2])) for x in re.findall(r'"CHACAL\|E\|sonde_perception\|([^"]*)"', t)]
        b = re.search(r'banc_perception\|([^"]*)', t); c = {}
        if b: f = b.group(1).split("|"); c = dict(zip(f[1::2], f[2::2]))
        fin = re.search(r'CHACAL\|FINI\|([A-Z_]*)\|([A-Z_0-9]*)', t); obs = re.search(r'observation\|[^|]*\|phase\|\d\|fin\|duree\|(\d+)', t)
        t0 = re.search(r'banc_perception\|([0-9.]+)', t); tf = re.search(r'CHACAL\|FINI\|[^"]*', t)
        n120 = sum(1 for l in L if int(l["depuis"]) <= 120)
        vm = [float(l["vis_moy"]) for l in L if "vis_moy" in l]; vx = [float(l["vis_max"]) for l in L if "vis_max" in l]
        con = next((int(l["depuis"]) for l in L if int(l["menaces_connues"]) > 0), None)
        print(f"{j['version']} {g} {etat} | erreurs {len(err)} | ligne_de_vue {c.get('ligne_de_vue')} hommes {c.get('hommes_avec_vue')} | sondes {len(L)} dont {n120} dans les 120 s"
              f" | vis_moy {min(vm) if vm else '-'}..{max(vm) if vm else '-'} vis_max {min(vx) if vx else '-'}..{max(vx) if vx else '-'}"
              f" | distance vraie {L[0]['verite_distance_menace'] if L else '-'} | connue a {con} s | fenetre {obs.group(1) if obs else '-'} s | {(fin.group(1) + '/' + fin.group(2)) if fin else 'pas de FINI'}")
        for e in err[:2]: print("   !!", e.replace("\n", " / ")[:300])
