import sys, re, glob, math, pathlib, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import COLS
L = "/mnt/data/harmattan-sandbox/logs/live67"

E, casses = [], 0
for f in sorted(glob.glob(f"{L}/ep_*.npz")):
    tx = pathlib.Path(f.replace(".npz", ".txt"))
    if not tx.exists(): continue
    try:
        Z = np.load(f, allow_pickle=True)
        A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
        act = np.asarray(Z["actions"]).reshape(-1)
    except Exception:
        casses += 1; continue          # episode coupe en cours d ecriture
    T = tx.read_text(errors="ignore")
    sc  = re.search(r'HARMATTAN_SCENE def=(\d+) att=(\d+)(?: enmain=(\d+))?', T)
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(\d+)', T)
    if len(pas) == 0: casses += 1; continue
    p0 = pas == pas.min()
    E.append(dict(sc=(sc.group(1), sc.group(2)) if sc else None,
                  enmain=(int(sc.group(3)) if (sc and sc.group(3)) else None),
                  viv=(int(fin.group(2)) if fin else 4),
                  dmin=(int(fin.group(3)) if fin else None),
                  npas=len(np.unique(pas)), nact=len(np.unique(act[act >= 0])),
                  az=math.degrees(math.atan2(A[p0,0].mean(), A[p0,1].mean())) % 360))

n = len(E)
print(f"  {n} episodes ARMES lus   ({casses} ecarte(s), tronque(s) par l arret)\n")
n4 = sum(1 for e in E if e["sc"] == ("4","4"))
az = np.array([e["az"] for e in E])
em = sorted({e["enmain"] for e in E if e["enmain"] is not None})
print("─── CONTROLES POSITIFS ───")
print(f"  1. scene def=4 att=4 par LE JEU : {n4}/{n}  " + ("✓" if n4 == n else "⛔"))
print(f"  2. azimuts, ecart-type {az.std():.1f} deg (porte > 60)  " + ("✓" if az.std() > 60 else "⛔"))
print(f"  3. arme en main : {em if em else 'champ absent'}")

pris = lambda e: e["viv"] > 0 and e["dmin"] is not None and e["dmin"] < 25
k = sum(1 for e in E if pris(e)); p = k/n; s = 1.96*math.sqrt(p*(1-p)/n)
mort = sum(1 for e in E if e["viv"] == 0)
plein = sum(1 for e in E if e["npas"] >= 59)
dm = np.median([e["npas"] for e in E]); am = np.median([e["nact"] for e in E])
fig = sum(1 for e in E if e["nact"] == 1); pf = fig/n; sf = 1.96*math.sqrt(pf*(1-pf)/n)

print("\n─── LE RESULTAT ───")
print(f"  {'':<26}{'ARMES':>16}{'DESARMES (67)':>16}")
print(f"  {'PRISE':<26}{str(k)+'/'+str(n)+' = '+f'{100*p:.1f} %':>16}{'8/67 = 11,9 %':>16}")
print(f"  {'IC95':<26}{f'[{100*max(0,p-s):.1f} ; {100*min(1,p+s):.1f}]':>16}{'[4,2 ; 19,7]':>16}")
print(f"  {'tous morts':<26}{f'{mort}/{n} = {100*mort/n:.0f} %':>16}{'~85 %':>16}")
print(f"  {'60 pas complets':<26}{f'{plein}/{n} = {100*plein/n:.0f} %':>16}{'—':>16}")
print(f"  {'duree mediane':<26}{f'{dm:.0f} pas':>16}{'~17 pas':>16}")
print(f"  {'actions distinctes (med)':<26}{f'{am:.0f}':>16}{'2':>16}")
print(f"\n─── LE GEL (binomial contre les 3,1 % du gymnase) ───")
print(f"  {fig}/{n} = {100*pf:.1f} %   IC95 [{100*max(0,pf-sf):.1f} ; {100*min(1,pf+sf):.1f}]")
print("  ⇒ " + ("3,1 % EXCLU — le gel persiste" if not (pf-sf <= 0.031 <= pf+sf) else "compatible — LE GEL A DISPARU"))
print(f"\n─── CONTRE LE GYMNASE (59,4 %) ───")
print("  ⇒ " + ("59,4 % est DANS l intervalle — l ecart de transfert NE TIENT PLUS" if p-s <= 0.594 <= p+s
                else "59,4 % reste HORS de l intervalle — l ecart TIENT"))
