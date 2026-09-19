"""Pourquoi la modulation par le type passe-t-elle de -0,369 a -0,062 ? Deux causes a separer, sur les episodes
deja joues : la CHARGE de la machine, et le comportement de la case qui a bouge ( patrouille / attendre )."""
import glob, json, os, re, statistics as st
H = "/mnt/data/hmt"


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


for camp in ("CHOIX-P2-TYPES-19-09", "P2-PERCUE-19-09"):
    charges, L = [], []
    for jf in glob.glob(f"{H}/runs/2026-09-19_*/job.json"):
        j = json.load(open(jf))
        if j.get("campagne") != camp: continue
        d0 = os.path.dirname(jf)
        try:
            c = open(d0 + "/charge_au_lancement.txt").read()
            charges.append(len(re.findall(r"arma3server", c)) or int((re.findall(r"(\d+)\s+arma3server", c) or [0])[0]))
        except Exception: pass
        if j.get("menace_p2") != 4 or j.get("traversee") != 2: continue
        for d in glob.glob(d0 + "/g*/"):
            try:
                if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
                t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
            except Exception: continue
            cj = [champs(m) for m in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]
            cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
            fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[^|]*\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
            L.append(dict(detail=cj[0].get("detail") if cj else None, compromis=int(fin.group(3)) if fin else None,
                          alarme=int(fin.group(4)) if fin else None, monde=int(re.search(r"/g(\d+)", d).group(1))))
    print(f"== {camp}")
    if charges: print(f"   serveurs deja en vol au lancement : mediane {st.median(charges)}, de {min(charges)} a {max(charges)} ( {len(charges)} jobs )")
    if L:
        from collections import Counter
        print(f"   PATROUILLE / ATTENDRE, {len(L)} episodes : compromis {sum(e['compromis'] or 0 for e in L)/len(L):.2f} ; "
              f"alarme {sum(e['alarme'] or 0 for e in L)/len(L):.2f}")
        print(f"      ce que devient l attente : {dict(Counter(e['detail'] for e in L))}")
