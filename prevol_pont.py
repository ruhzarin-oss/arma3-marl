#!/usr/bin/env python3
"""prevol_pont — CONTROLE N.0 DU HARNAIS : la latence aller-retour.

Fable : « la voie se choisit sur ce nombre, pas sur un avis ».
Critere PRE-INSCRIT, ecrit avant la mesure : mediane < 1,0 s et p99 < 3,0 s sur
100 allers-retours. Sous ce seuil un cycle de decision de 4 s tient largement.
Au-dessus, le harnais est a repenser AVANT d'ecrire la moindre ligne de plus.

ALLER  : on ecrit C:\\hmt_bridge\\cmd_<N>.sqf ; la DLL hmt_ext_x64 le lit au niveau OS
         (fopen), ce qui contourne le gel d'index d'Arma. Pas de -filePatching.
RETOUR : diag_log -> RPT, suivi depuis WSL par /mnt/c/...

Ce script ne suppose rien : si l'aller ne passe pas, il le DIT au lieu d'attendre.
"""
import os, time, glob, statistics, sys

PONT = "/mnt/c/hmt_bridge"
PROF = "/mnt/c/Users/Younes/hmtech0"
N    = 100
PAS  = 0.05

def dernier_rpt():
    fs = sorted(glob.glob(os.path.join(PROF, "*.rpt")), key=os.path.getmtime)
    return fs[-1] if fs else None

rpt = dernier_rpt()
if rpt is None:
    print("PAS DE RPT — le serveur ne tourne pas"); sys.exit(2)
print(f"rpt   : {os.path.basename(rpt)}")
print(f"pont  : {PONT}")

# ⚠️ ON SE CALE SUR LE COMPTEUR DE LA MISSION, pas sur les fichiers presents.
# L'actuateur attend cmd_(n+1) et RIEN D'AUTRE. Partir d'un autre numero fait attendre
# les deux cotes indefiniment, et cette attente ressemble exactement a une panne de pont.
# La mission publie HMT_SYNC dans son battement de coeur : on le lit.
def lire_sync(chemin, patience=12.0):
    t0 = time.time()
    while time.time() - t0 < patience:
        with open(chemin, "r", errors="ignore") as g:
            vus = [l for l in g if "HMT_SYNC" in l]
        if vus:
            return int(vus[-1].split("HMT_SYNC")[1].split()[0])
        time.sleep(0.5)
    return None

n_mission = lire_sync(rpt)
if n_mission is None:
    print("PAS DE HMT_SYNC — la mission ne publie pas son compteur"); sys.exit(2)
for vieux in glob.glob(f"{PONT}/cmd_*.sqf"):
    os.remove(vieux)
n0 = n_mission + 1
print(f"sync  : mission a n={n_mission}, on part de cmd_{n0}\n")

f = open(rpt, "r", errors="ignore")
f.seek(0, os.SEEK_END)

lat, perdus = [], 0
for i in range(N):
    n = n0 + i
    jeton = f"PONG-{n}"
    t0 = time.time()
    tmp = f"{PONT}/.tmp_{n}"
    with open(tmp, "w") as g:
        g.write(f'diag_log "[PONT] {jeton}";\n')
    os.replace(tmp, f"{PONT}/cmd_{n}.sqf")     # ecriture ATOMIQUE : jamais de fichier a moitie ecrit
    vu = False
    while time.time() - t0 < 4.0:
        ligne = f.readline()
        if not ligne:
            time.sleep(PAS); continue
        if jeton in ligne:
            lat.append(time.time() - t0); vu = True; break
    if not vu:
        perdus += 1
        if perdus == 1:
            print(f"!! cmd_{n} JAMAIS revenue apres 8 s — l'aller ne passe pas")
    if (i + 1) % 25 == 0:
        m = statistics.median(lat) if lat else float('nan')
        print(f"  {i+1:3d}/{N}  recus={len(lat)}  perdus={perdus}  mediane={m:.3f} s")

print()
if not lat:
    print("VERDICT : AUCUN aller-retour. La voie DLL ne passe pas.")
    print("          -> soit l'extension n'est pas chargee, soit le chemin du pont differe.")
    sys.exit(1)

lat.sort()
med = statistics.median(lat)
p99 = lat[min(len(lat) - 1, int(0.99 * len(lat)))]
print(f"n={len(lat)}  perdus={perdus}")
print(f"mediane = {med:.3f} s   (seuil pre-inscrit < 1,000)")
print(f"p99     = {p99:.3f} s   (seuil pre-inscrit < 3,000)")
print(f"min={lat[0]:.3f}  max={lat[-1]:.3f}")
ok = (med < 1.0) and (p99 < 3.0) and (perdus == 0)
print()
print("VERDICT CONTROLE 0 :", "PASSE — la voie DLL tient un cycle de 4 s" if ok else "ECHOUE")
sys.exit(0 if ok else 1)
