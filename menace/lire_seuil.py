"""Banc de seuil : a quelle distance la menace devient-elle connue, et en combien de temps ( jour / nuit ).
Sortie : par condition, la part d episodes ou menace_percue atteint 2 ( connue du groupe ) avant 90 s, la fenetre du plan."""
import glob, json, os, re
H = "/mnt/data/hmt"; FENETRE = 90
L = []
for jf in glob.glob(f"{H}/runs/2026-09-*/job.json"):
    j = json.load(open(jf))
    if j.get("campagne") != "BANC-SEUIL-18-09": continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try: t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        b = re.search(r'"CHACAL\|E\|banc_perception\|[^"]*\|ligne_de_vue\|([01])[^"]*\|distance_posee\|(\d+)', t)
        if not b: continue
        if "CHACAL|E|banc_refuse|" in t or b.group(1) == "0":
            L.append(dict(jour=j.get("jour", 0), dist=j.get("controle_dist", -1), monde=os.path.basename(d.rstrip("/")),
                          exclu=True)); continue
        S = []
        for m in re.finditer(r'"CHACAL\|E\|sonde_perception\|([0-9.]+)\|[^"]*\|depuis\|(\d+)\|[^"]*\|menace_percue\|(\d)\|menaces_vues\|(\d+)\|menaces_connues\|(\d+)', t):
            S.append((int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))))
        if not S: continue
        vue = next((s[0] for s in S if s[2] > 0), None)
        connue = next((s[0] for s in S if s[3] > 0), None)
        L.append(dict(jour=j.get("jour", 0), dist=j.get("controle_dist", -1), monde=os.path.basename(d.rstrip("/")),
                      exclu=False, vue=vue, connue=connue,
                      connue_dans_fenetre=int(connue is not None and connue <= FENETRE),
                      vue_dans_fenetre=int(vue is not None and vue <= FENETRE)))
print(f"== BANC DE SEUIL : {len(L)} episodes ( {sum(1 for e in L if e['exclu'])} exclus, sans ligne de vue )")
print("\n moment   distance   episodes   vue <= 90 s   connue <= 90 s   1er vu (s)   1er connu (s)")
for jour in (0, 1):
    for dist in sorted({e["dist"] for e in L if e["jour"] == jour}):
        G = [e for e in L if e["jour"] == jour and e["dist"] == dist and not e["exclu"]]
        if not G: continue
        v = sum(e["vue_dans_fenetre"] for e in G) / len(G); c = sum(e["connue_dans_fenetre"] for e in G) / len(G)
        pv = [e["vue"] for e in G if e["vue"] is not None]; pc = [e["connue"] for e in G if e["connue"] is not None]
        print(f" {'jour' if jour else 'nuit':5s}    {dist:5d} m    {len(G):5d}       {v:5.0%}         {c:5.0%}        "
              f"{(sum(pv)/len(pv) if pv else float('nan')):7.1f}      {(sum(pc)/len(pc) if pc else float('nan')):7.1f}")
print("\nCible du plan : une bande ou la menace est connue dans 30 a 70 % des episodes au moment du choix.")
