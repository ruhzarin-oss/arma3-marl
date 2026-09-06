#!/usr/bin/env python3
"""plancher_bruit — LE SEUIL SE DEDUIT DU BRUIT, IL NE SE CHOISIT PAS.

⚠️ LA FAUTE QUE CE FICHIER REPARE. J ai depose un seuil de succes a « +1,0 survivant » AU
JUGEMENT, sans avoir mesure la dispersion du banc. Or le bras `greffe` du dernier run n a
donne AUCUN veto (0 sur 174 decisions) : il etait donc COMPORTEMENTALEMENT IDENTIQUE au bras
`nu`. Et il a rendu 2,50 contre 6,00. **Trois bras au meme comportement, 3,5 survivants
d ecart.** Mon seuil etait trois fois SOUS le bruit, et mes deux verdicts precedents ne
voulaient rien dire.

Partout ailleurs dans ce dossier j ai DIMENSIONNE l instrument — la fenetre du raster, la
scene, le budget. Le seuil, non. C est le meme geste, et il manquait.

ON MESURE : la MEME configuration, la MEME doctrine (le natif nu), N fois. Tout ce qui
apparait est du bruit — il n y a rien d autre a voir.
"""
import sys, time, json, math
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from greffe_arma import scene, E

N = 12
print("=" * 90); print(" PLANCHER DE BRUIT — %d repetitions du MEME bras, dans la MEME scene" % N)
print("=" * 90, flush=True)
b = None; bl, ro = [], []
try:
    b = NativeBridge(port=5801, timeout=40)
    for k in range(N):
        scene(b, k)
        time.sleep(150)
        r = b.query(E("HMTN b=%1 o=%2", "{alive _x} count units HMT_GB", "{alive _x} count units HMT_GO"),
                    r"HMTN b=(\d+) o=(\d+)", want=1, timeout=30)
        if not r: print("  %2d : pas de reponse" % k, flush=True); continue
        x, y = int(r[0].group(1)), int(r[0].group(2))
        bl.append(x); ro.append(y)
        print("  repetition %2d : bleus %d/8   rouges %d/20" % (k, x, y), flush=True)
finally:
    if b:
        try: b.close()
        except Exception: pass

if len(bl) >= 4:
    a = np.array(bl, float)
    m, s = a.mean(), a.std(ddof=1)
    print("\n─── LE BRUIT ───")
    print("  survivants amis : moyenne %.2f   ecart-type %.2f   etendue [%d ; %d]" % (m, s, a.min(), a.max()))
    print("  erreur-type sur une moyenne de 2 graines  : %.2f" % (s / math.sqrt(2)))
    print("  erreur-type sur une moyenne de %d graines  : %.2f" % (len(a), s / math.sqrt(len(a))))
    print("\n─── LE SEUIL QUI EN DECOULE ───")
    print("  Pour detecter un effet a 95 %% avec deux moyennes de n graines, il faut")
    print("  un ecart d au moins ~2,8 x ecart-type / racine(n) :")
    for n in (2, 4, 8, 16, 32):
        print("     n = %-3d graines par bras  ->  detectable a partir de %+.2f survivant" % (n, 2.8 * s / math.sqrt(n)))
    print("\n  ⛔ MON SEUIL DEPOSE ETAIT +1,0 AVEC 2 GRAINES.")
    print("     Il aurait fallu n = %d graines par bras pour qu il soit atteignable."
          % max(2, int(math.ceil((2.8 * s / 1.0) ** 2))))
    json.dump({"n": len(bl), "bleus": bl, "rouges": ro, "moyenne": m, "ecart_type": s},
              open('/mnt/data/plancher_bruit.json', 'w'), indent=1)
else:
    print("\n  trop peu de repetitions valides pour conclure")
