"""Lecture des controles « menace visible » ( plan v2 : perception conjuguee menace_percue ), une fois tous les jobs finis.
  python lire_controles.py [ prefixe de date des runs, defaut 2026-09-18 ]"""
import glob, json, os, re, sys
H = "/mnt/data/hmt"; CAMPAGNE = "CONTROLE-MENACE-VISIBLE-17-09"
PREFIXE = sys.argv[1] if len(sys.argv) > 1 else "2026-09-18"
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
POINTS = {"TRAVERSEE", "INSERTION_ATTENTE", "ITINERAIRE"}

def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}

def episodes(campagne, filtre=None):
    out = []
    for jf in glob.glob(f"{H}/runs/{PREFIXE}*/job.json"):
        j = json.load(open(jf))
        if j.get("campagne") != campagne or (filtre and not filtre(j)): continue
        for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
            try:
                v = json.load(open(d + "resultat.json")).get("verdict"); rpt = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
            except Exception: continue
            dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', rpt)]
            dec = [x for x in dec if x.get("point") in POINTS]
            obs = [champs(m) for m in re.findall(r'"CHACAL\|E\|observation\|([^"]*\|fin\|[^"]*)"', rpt)]
            out.append(dict(nom=j["version"].split("-g")[0], monde=os.path.basename(d.rstrip("/")), verdict=v, erreurs=len(RX_ERR.findall(rpt)),
                            version3="CHACAL|OK|decision|version|3" in rpt, dec=dec[0] if dec else None, obs=obs[0] if obs else None,
                            n_obs=len(obs), ctl="controle_perception" in rpt))
    return out

E = episodes(CAMPAGNE)
if not E: raise SystemExit("aucun episode")
par = {}
for e in E: par.setdefault(e["nom"], []).append(e)
f = lambda x, k: int(float(x[k])) if x and k in x else None
print(f"== {len(E)} episodes ; erreurs SQF totales {sum(e['erreurs'] for e in E)} ; refuses {sum(e['verdict'] != 'ACCEPTE' for e in E)} ; version 3 partout : {all(e['version3'] for e in E)}")
for nom in sorted(par):
    L = par[nom]
    print(f"\n-- {nom} : {len(L)} episodes, acceptes {sum(e['verdict'] == 'ACCEPTE' for e in L)}, erreurs {sum(e['erreurs'] for e in L)}, fenetres {sum(e['n_obs'] for e in L)}")
    for e in L:
        o, d = e["obs"], e["dec"]
        print(f"   {e['monde']:7s} fin fenetre : vues {f(o,'menaces_vues')} connues {f(o,'menaces_connues')} dist {f(o,'distance_menace')} err {o.get('erreur_position') if o else None} "
              f"mobile {f(o,'menace_mobile')} vue_depuis {f(o,'vue_depuis')} | percue {f(o,'menace_percue')} camp {f(o,'menaces_camp')} homme {f(o,'menaces_homme')} "
              f"| verite {f(o,'verite_menaces')} dist_vraie {f(o,'verite_distance_menace')} | {d.get('point') if d else None} choix {d.get('choix') if d else None} percue_au_choix {f(d,'menace_percue')}")
print("\n== CRITERES ECRITS AVANT")
def part(nom, test):
    L = [e for e in par.get(nom, []) if e["verdict"] == "ACCEPTE" and e["obs"]]
    return sum(test(e) for e in L), len(L)
k, n = part("MV-POSITIF", lambda e: f(e["obs"], "menace_percue") > 0); print(f"   POSITIF  menace_percue > 0 en fin de fenetre : {k}/{n}  ( attendu >= 80 % ) -> {'OUI' if n and k >= 0.8 * n else 'NON'}")
k, n = part("MV-POSITIF", lambda e: f(e["obs"], "menaces_connues") > 0); print(f"            dont connue du groupe : {k}/{n}  ( descriptif )")
k, n = part("MV-NEGATIF", lambda e: f(e["obs"], "menace_percue") == 0); print(f"   NEGATIF  menace_percue = 0 en fin de fenetre : {k}/{n}  ( attendu >= 95 % ) -> {'OUI' if n and k >= 0.95 * n else 'NON'}")
k, n = part("MV-NUL", lambda e: f(e["obs"], "menace_percue") == 0 and f(e["obs"], "verite_menaces") == 0 and f(e["dec"], "menace_percue") == 0)
print(f"   NUL      aucune perception ni verite de menace : {k}/{n}  ( attendu 100 % ) -> {'OUI' if n and k == n else 'NON'}")
o = par.get("MV-ORIGINE", [])
ref = episodes("CHOIX-P2-17-09", lambda j: j.get("traversee") == 1 and j.get("menace_p2") == 3 and set(j.get("graines", [])) & {4, 5})
cles = ("phase", "point", "options", "choix", "decideur")
ok_or = bool(o) and all(e["n_obs"] == 0 and e["dec"] and e["erreurs"] == 0 for e in o) and all(
    any(r["dec"] and all(r["dec"].get(c) == e["dec"].get(c) for c in cles) for r in ref) for e in o)
print(f"   ORIGINE  pas de fenetre, 0 erreur, decision identique a CHOIX-P2 ( {', '.join(cles)} ) : {'OUI' if ok_or else 'NON'} ( {len(o)} episodes, {len(ref)} de reference )")
print(f"   GLOBAL   0 erreur SQF : {'OUI' if sum(e['erreurs'] for e in E) == 0 else 'NON'}")
print("\n== VARIANCE DE LA PERCEPTION A 90 S ( part des episodes ou menace_percue > 0 au moment du choix ; attendu 30 a 70 % )")
for nom in ("MV-P2_TYPE1", "MV-P2_TYPE2", "MV-P1_TYPE1", "MV-P1_TYPE2", "MV-P4_TYPE1", "MV-P4_TYPE2"):
    L = [e for e in par.get(nom, []) if e["verdict"] == "ACCEPTE" and e["dec"]]
    k = sum((f(e["dec"], "menace_percue") or 0) > 0 for e in L)
    print(f"   {nom:13s} {k}/{len(L)}  {'dans la plage' if L and 0.3 <= k / len(L) <= 0.7 else 'HORS PLAGE : a rapporter a Younes'}")
