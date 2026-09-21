"""EXPLORATOIRE, non pre-enregistre. Hier j ai annonce « la route predit la prise » sur la COMPROMISSION BRUTE
de R+F par classe de monde ( 0,42 contre 0,15, mondes connus ). Aujourd hui la lecture L3 utilise l APPORT
( R+F moins T ). Pour savoir si j ai quelque chose a retirer, on recalcule la meme mesure qu hier, sur les
donnees d aujourd hui."""
import glob, json, os, re
H = "/mnt/data/hmt"
RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[0-9.]+\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')
def lire(camp):
    vus, out = set(), []
    for jf in sorted(glob.glob(f"{H}/runs/2026-09-2*/job.json")):
        j = json.load(open(jf))
        if j.get("campagne") != camp: continue
        b = "T" if j.get("oracle_cmd") == 0 else ("N" if j.get("oracle_b") == 0 else ("F" if j.get("oracle_delta") == 30 else "R"))
        for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
            w = int(re.search(r"/g(\d+)", d).group(1)); cle = (b, w, j["situation"])
            if cle in vus: continue
            try:
                if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
                t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
            except Exception: continue
            m = RX_FIN.search(t)
            if not m: continue
            vus.add(cle); out.append((b, w, int(m.group(3))))
    return out
HAUTE, BASSE = (7, 8, 9, 11), (4, 5, 6, 12)
for camp in ("CALIBRATION-ADVERSAIRE-20-09", "CALIBRATION-P2-V2-21-09"):
    L = lire(camp)
    for nom, ws in (("haute prise ( 7 cases )", HAUTE), ("basse prise ( 4-5 cases )", BASSE)):
        rf = [c for b, w, c in L if b in ("R", "F") and w in ws]; t = [c for b, w, c in L if b == "T" and w in ws]
        print(f"{camp:<30} {nom:<26} compromission R+F {sum(rf) / len(rf):.3f} ( n {len(rf)} )   T {sum(t) / len(t):.3f} ( n {len(t)} )")
