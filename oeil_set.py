#!/usr/bin/env python3
"""oeil_set — FABRIQUER LE JEU ETIQUETE DANS ARMA, sans annoter une seule image.

Arma connait la verite terrain. On lui demande de poser un soldat a une distance et un
camp CHOISIS, on photographie, et l'etiquette est connue PAR CONSTRUCTION. C'est ce qui
rend l'affaire economique : 153 episodes d'entrainement par heure, mais des milliers
d'images etiquetees.

TROIS PIEGES NOMMES AVANT DE COMMENCER, et ce qu'on fait contre :
 1. LA GEOGRAPHIE DES SPAWNS. Si le camp EST toujours pose au meme endroit, un detecteur
    apprend l'endroit, pas l'uniforme. -> le decalage lateral est TIRE AU HASARD, et le
    controle final permute les uniformes entre camps.
 2. LE CADRAGE. Une vue de joueur bouge. -> camera SCRIPTEE, cadrage identique a l'image
    pres, conditions de lumiere FIXES (11 h, ciel clair).
 3. LA CLASSE VIDE. Sans images SANS soldat, « detecter un soldat » n'a pas de negatif.
    -> un tiers des prises est « AUCUN », au meme endroit, meme cadrage.
"""
import os, sys, time, random, json, argparse, math
sys.path.insert(0, "/home/younes/arma3-marl")
from pont import Pont, PONT_DIR

PROFIL_CLIENT = "/mnt/c/Users/Younes/AppData/Local/Arma 3"
JEU = "/mnt/c/hmt_bridge/jeu"

# ⭐ LA GEOMETRIE DE LA PRISE DE VUE, ECRITE ET NON SUPPOSEE (reparation du 01/09).
# L'ecran fait 3440x1440 ; le daemon en decoupe 448x448 AU CENTRE, sans reduction.
# Une image n'est donc utilisable que si le soldat tombe dans CE carre-la, pas
# seulement « a l'ecran ». L'audit a montre que les deux tiers du jeu du 31/08
# n'avaient aucun soldat : le champ resserre a 28 deg mettait hors cadre tout
# decalage lateral de 8 m en deca de ~45 m.
ECRAN_W, ECRAN_H, CROP = 3440, 1440, 448
U0 = (ECRAN_W - CROP) / 2 / ECRAN_W ; U1 = (ECRAN_W + CROP) / 2 / ECRAN_W
V0 = (ECRAN_H - CROP) / 2 / ECRAN_H ; V1 = (ECRAN_H + CROP) / 2 / ECRAN_H
DEMI_CHAMP_DEG = 14.0        # camSetFov 0.25 -> 28 deg de champ vertical

def declencher(nom, patience=8.0):
    t = f"{PONT_DIR}/shoot.txt"
    tmp = f"{PONT_DIR}/.shoot_tmp"
    with open(tmp, "w") as g: g.write(nom)
    os.replace(tmp, t)
    t0 = time.time()
    while time.time() - t0 < patience:
        if not os.path.exists(t) and os.path.exists(f"{JEU}/{nom}.png"):
            return True
        time.sleep(0.05)
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--graine", type=int, default=7)
    ap.add_argument("--sortie", default="/home/younes/arma3-marl/oeil_jeu.jsonl")
    # ⭐ MODE CENTRE. On pose deux questions quand on cherche un soldat dans un paysage :
    # le RECONNAITRE, et le TROUVER. La seconde ecrase la premiere — un homme occupe un
    # millieme de la surface. En le posant sur l'axe (lat=0) on peut decouper le CENTRE
    # de l'image et poser la premiere question SEULE. C'est la reparation du 31/08.
    ap.add_argument("--centre", action="store_true")
    ap.add_argument("--dmin", type=int, default=0)
    ap.add_argument("--prefixe", default="i")
    a = ap.parse_args()

    rng = random.Random(a.graine)
    pont = Pont(PROFIL_CLIENT)
    print(f"pont client : {pont.rpt.split('/')[-1]}  n={pont.n}", flush=True)
    if pont.attendre("ETAT PRET", 90) is None:
        print("la camera n'est jamais posee"); return 2
    os.makedirs(JEU, exist_ok=True)

    # distances CHOISIES pour couvrir le regime qui compte : de la ou l'homme est gros
    # a la ou il fait cinq pixels. Le jeu doit contenir le difficile, sinon il ment.
    DIST = [25, 40, 60, 90, 130, 180, 250, 320, 400]
    CAMPS = ["EST", "OUEST", "AUCUN"]

    lignes, rates, rejets = [], 0, {}
    t0 = time.time()
    with open(a.sortie, "w") as f:
        for i in range(a.n):
            camp = CAMPS[i % 3]                       # equilibre exact des trois classes
            dispo = [x for x in DIST if x >= a.dmin]
            d    = rng.choice(dispo)
            # le decalage lateral se BORNE au champ : a 25 m, 8 m valent 17,7 deg et
            # sortent du cadre. On tire dans les 70 % du demi-champ, jamais au-dela.
            lat_max = min(8.0, 0.70 * d * math.tan(math.radians(DEMI_CHAMP_DEG)))
            lat  = 0.0 if a.centre else rng.uniform(-lat_max, lat_max)
            post = 0 if a.centre else rng.choice([0, 0, 0, 1, 2])
            nom  = f"{a.prefixe}{i:05d}"
            pont.envoyer(f'[{i}, "{camp}", {d}, {lat:.2f}, {post}] spawn HMT_fnc_poser;')
            ligne = pont.attendre(f"[OEIL] POSE {i} ", 12)
            if ligne is None:
                rates += 1; rejets["silence"] = rejets.get("silence", 0) + 1; continue

            # ⭐ ON LIT CE QUE LA MISSION REPOND, ON NE SUPPOSE PLUS RIEN
            ch = dict(kv.split("=", 1) for kv in ligne.replace('"', "").split()
                      if "=" in kv and kv.split("=", 1)[0] in ("u", "v", "vue"))
            u, v, vue = float(ch.get("u", -1)), float(ch.get("v", -1)), int(ch.get("vue", 0))
            if camp != "AUCUN":
                dans = (U0 <= u <= U1) and (V0 <= v <= V1)
                if not dans:
                    rates += 1; rejets["hors_cadre"] = rejets.get("hors_cadre", 0) + 1; continue
                if not vue:
                    rates += 1; rejets["masque"] = rejets.get("masque", 0) + 1; continue

            if not declencher(nom):
                rates += 1; rejets["capture"] = rejets.get("capture", 0) + 1; continue
            # position EN PIXELS dans la vignette : elle sert a la sonde par patch
            px = round(u * ECRAN_W - (ECRAN_W - CROP) / 2, 1) if camp != "AUCUN" else -1
            py = round(v * ECRAN_H - (ECRAN_H - CROP) / 2, 1) if camp != "AUCUN" else -1
            rec = dict(nom=nom, camp=camp, d=d, lat=round(lat, 2), posture=post,
                       present=int(camp != "AUCUN"), px=px, py=py, vue=vue)
            f.write(json.dumps(rec) + "\n"); f.flush()
            lignes.append(rec)
            if (i + 1) % 25 == 0:
                v = (time.time() - t0) / (i + 1)
                print(f"  {i+1}/{a.n}  gardees={len(lignes)} rejets={rejets}  "
                      f"{v:.2f} s/image  reste {(a.n-i-1)*v/60:.1f} min", flush=True)

    print(f"\n{len(lignes)} images GARDEES, {rates} rejetees {rejets}, {time.time()-t0:.0f} s")
    print("⭐ une image rejetee n'est PAS une image ratee : c'est une image dont on sait")
    print("   qu'elle mentirait. Le rejet est le controle, pas la panne.")
    print(f"jeu   : {JEU}")
    print(f"index : {a.sortie}")
    n_pres = sum(r["present"] for r in lignes)
    print(f"presents={n_pres}  absents={len(lignes)-n_pres}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
