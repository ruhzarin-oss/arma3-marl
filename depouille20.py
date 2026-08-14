import sys, re, glob, pathlib, math, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
NOMS = ["apx/S","apy/S","dgx","dgy","alive","slope","dcover","los","nd","p_deb","p_acc","p_cou"]
L = "/mnt/data/harmattan-sandbox/logs/live20"

E = []
for i in range(1, 21):
    f, tx = f"{L}/ep_{i}.npz", pathlib.Path(f"{L}/ep_{i}.txt")
    if not pathlib.Path(f).exists(): continue
    Z = np.load(f, allow_pickle=True)
    T = tx.read_text(errors="ignore")
    sc = re.search(r'HARMATTAN_SCENE def=(\d+) att=(\d+)', T)
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(\d+)', T)
    A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
    act = np.asarray(Z["actions"]).reshape(-1)
    p0 = pas == pas.min()
    E.append(dict(i=i, scene=(sc.group(1), sc.group(2)) if sc else None,
                  npas=len(np.unique(pas)),
                  viv=int(fin.group(2)) if fin else 4,
                  dmin=int(fin.group(3)) if fin else None,
                  az=math.degrees(math.atan2(A[p0,0].mean(), A[p0,1].mean())) % 360,
                  nact=len(np.unique(act)), acts=np.unique(act).tolist(), A=A, act=act))

print(f"  {len(E)} episodes lus sur 20\n")
print("─── CONTROLE POSITIF 1 : la scene confirmee par LE JEU ───")
ok = sum(1 for e in E if e["scene"] == ("4","4"))
print(f"  def=4 att=4 : {ok}/{len(E)}   " + ("✓ PASSE" if ok == len(E) else "⛔ des episodes non conformes"))

print("\n─── CONTROLE POSITIF 2 : les azimuts de naissance DIFFERENT-ils ? ───")
az = np.array([e["az"] for e in E])
print(f"  azimuts : {', '.join(f'{a:.0f}' for a in az)}")
print(f"  distincts a 5 deg pres : {len(np.unique(np.round(az/5)))}/{len(E)}   ecart-type {az.std():.1f} deg")
print("  " + ("✓ PASSE — 20 episodes, pas 20 copies" if len(np.unique(np.round(az/5))) >= len(E)-2 else "⛔ TOMBE — azimuts repetes"))

print("\n─── LA PORTE : les 12 colonnes restent-elles dans la plage ? ───")
G, pol = [], charger(B.DEV)
def rec(o,t):
    G.append(o.reshape(-1,o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l,v = pol(o); return l.argmax(-1),None,None
stg,*_ = B.jouer(B.monde(64,101), rec)
G = np.concatenate(G).astype(np.float64)
AA = np.concatenate([e["A"] for e in E])
gl,gh = np.percentile(G,1,axis=0), np.percentile(G,99,axis=0)
hors = [NOMS[k] for k in range(12) if not (gl[k] <= np.percentile(AA[:,k],50) <= gh[k])]
print(f"  colonnes hors plage : {len(hors)}/12" + ("" if not hors else "  → " + ", ".join(hors)))
print("  " + ("✓ PASSE" if not hors else "⛔ TOMBE — le monde a bouge sous la mesure"))

print("\n─── LA PRISE — critere DEJA CODE (dmin < 25), et vivants > 0 ───")
print("  ⚠️ `dmin` vaut 1 quand TOUS sont morts : c est degenere, pas une prise.")
print(f"  {'ep':>3}{'pas':>5}{'viv':>5}{'dmin':>6}{'act':>5}  issue")
npr = 0
for e in E:
    pr = (e["viv"] > 0) and (e["dmin"] is not None) and (e["dmin"] < 25)
    npr += pr
    iss = "PRISE" if pr else ("tous morts" if e["viv"] == 0 else "60 pas, pas pris")
    print(f"  {e['i']:>3}{e['npas']:>5}{e['viv']:>5}{str(e['dmin']):>6}{e['nact']:>5}  {iss}")
p = npr/len(E); ic = 1.96*math.sqrt(p*(1-p)/len(E))
print(f"\n  PRISE ARMA : {npr}/{len(E)} = {100*p:.1f} %   IC95 [{100*max(0,p-ic):.1f} ; {100*min(1,p+ic):.1f}]")
print(f"  reference gymnase (graine 101) : {stg['prise']:.1f} %")

print("\n─── LE GEL — regle deposee ───")
fig = sum(1 for e in E if e["nact"] == 1)
print(f"  episodes figes (une seule action de bout en bout) : {fig}/{len(E)}")
print(f"  actions distinctes par episode : mediane {np.median([e['nact'] for e in E]):.0f}  (gymnase 5)")
if fig >= 18:   v = "LE GEL EST REEL — le taux du gymnase (3,1 %) est rejete."
elif fig <= 3:  v = "IL N Y A JAMAIS EU DE GEL — Arma est compatible avec le gymnase."
else:           v = f"INDECIS ({fig}/20 est dans la bande 4-17). On ne conclut pas, on ne rejoue pas."
print(f"\n  ⇒ {v}")
