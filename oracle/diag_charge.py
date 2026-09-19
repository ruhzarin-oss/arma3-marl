"""Charge de la machine au lancement de chaque job ( nombre de serveurs Arma deja en vol ), par campagne."""
import glob, json, os, re, statistics as st
H = "/mnt/data/hmt"
for camp in ("CHOIX-P2-TYPES-19-09", "P2-PERCUE-19-09"):
    C = []
    for jf in glob.glob(f"{H}/runs/2026-09-19_*/job.json"):
        if json.load(open(jf)).get("campagne") != camp: continue
        try:
            m = re.search(r"(\d+)\s+arma3server", open(os.path.dirname(jf) + "/charge_au_lancement.txt").read())
            C.append(int(m.group(1)) if m else 0)
        except Exception: pass
    print(f"{camp:22s} : serveurs deja en vol au lancement - mediane {st.median(C):.0f}, moyenne {st.mean(C):.1f}, "
          f"de {min(C)} a {max(C)} ( {len(C)} jobs )")
