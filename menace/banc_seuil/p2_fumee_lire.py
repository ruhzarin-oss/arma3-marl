"""Fumee de P2 : les attentes ecrites dans CRITERES_P2_TYPES_19-09.md, episode par episode."""
import glob, json, os, re, sys
H = "/mnt/data/hmt"; CAMP = sys.argv[1] if len(sys.argv) > 1 else "FUMEE-P2-TYPES-19-09"; ATT = {4: ["PATROUILLE_ROUTE"], 5: ["POSTE_DE_CONTROLE"]}; tout = True; n = 0; vol = False
def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMP: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        if not os.path.exists(d + "resultat.json"): print(j["version"], os.path.basename(d.rstrip("/")), ": en vol"); vol = True; continue
        n += 1; v = json.load(open(d + "resultat.json")).get("verdict"); t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]; dec = [x for x in dec if x.get("point") == "TRAVERSEE"]
        cj = [champs(m) for m in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]; cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
        types = sorted({champs(m).get("type") for m in re.findall(r'"CHACAL\|E\|situation\|([^"]*)"', t) if champs(m).get("phase") == "2"})
        reg = re.search(r'reglage_observation\|[^|]*\|phase\|2\|avant\|(\d+)\|balayage\|(\d+)', t); fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[^|]*\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        err = len(re.findall(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type", t))
        ok = dict(erreurs=err == 0, accepte=v == "ACCEPTE", decision=len(dec) == 1 and int(float(dec[0]["choix"])) == j["traversee"], choix_joue=len(cj) == 1 and int(float(cj[0]["choix"])) == j["traversee"],
                  type=types == ATT[j["menace_p2"]], reglage=bool(reg) and (int(reg.group(1)), int(reg.group(2))) == (j["avant"], j["balayage"]), fin_de_phase=fin is not None)
        tout &= all(ok.values())
        print(j["version"], os.path.basename(d.rstrip("/")), "|", " ".join(f"{k}:{'OK' if x else 'ECHEC'}" for k, x in ok.items()), "|", "types", types, "| detail", cj[0].get("detail") if cj else None, "attente", cj[0].get("attente") if cj else None,
              "| percue", dec[0].get("menace_percue") if dec else None, "vehicule_vu", dec[0].get("vehicule_vu") if dec else None, "| fin", fin.group(0)[10:] if fin else None, "| verdict", v, "| erreurs", err)
print("FUMEE", "ECHOUEE" if not tout else ("PASSEE" if n == 4 and not vol else "INCOMPLETE"), f"( {n} episodes lus sur 4 )")
