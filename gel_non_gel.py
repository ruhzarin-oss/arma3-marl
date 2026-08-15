"""11,9 contre 59,4 melange DEUX ecarts : celui du monde, et la degenerescence (gel 25,4 %).
⟨Fable⟩ « Que fait le sous-ensemble NON GELE sur Arma ? S il fait 15 %, le monde est le
coupable ; s il fait 35 %, tu accuses le gymnase d un crime commis par l optimisation. »
Aucune donnee nouvelle : les 67 episodes deja acquis."""
import sys, re, glob, math, pathlib, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import COLS
L = "/mnt/data/harmattan-sandbox/logs/live67"

def lire(rep):
    E = []
    for f in sorted(glob.glob(f"{rep}/ep_*.npz")):
        i = int(re.search(r'ep_(\d+)', f).group(1))
        tx = pathlib.Path(f.replace(".npz", ".txt"))
        if not tx.exists(): continue
        Z = np.load(f, allow_pickle=True); T = tx.read_text(errors="ignore")
        fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(\d+)', T)
        act = np.asarray(Z["actions"]).reshape(-1)
        E.append(dict(i=i, nact=len(np.unique(act)),
                      viv=int(fin.group(2)) if fin else 4,
                      dmin=int(fin.group(3)) if fin else None))
    return E
E = lire(L)
pris = lambda e: e["viv"] > 0 and e["dmin"] is not None and e["dmin"] < 25
def bloc(S, nom):
    if not S: print(f"  {nom:<24} vide"); return None
    k = sum(1 for e in S if pris(e)); n = len(S); p = k/n
    s = 1.96*math.sqrt(p*(1-p)/n) if n else 0
    print(f"  {nom:<24} {k:2d}/{n:2d} = {100*p:5.1f} %   IC95 [{100*max(0,p-s):5.1f} ; {100*min(1,p+s):5.1f}]")
    return p

print(f"  {len(E)} episodes (les 67 deja acquis, aucune donnee nouvelle)\n")
print("─── LA PRISE, SELON QUE L EPISODE EST GELE OU NON ───")
tout   = bloc(E, "TOUS")
nongel = bloc([e for e in E if e["nact"] > 1], "NON GELES")
gel    = bloc([e for e in E if e["nact"] == 1], "GELES")
print(f"\n  gymnase de reference : 59,4 %")

print("\n─── LA LECTURE DE FABLE ───")
if nongel is None: raise SystemExit
if nongel < 0.20:
    print(f"  {100*nongel:.1f} % — proche des {100*tout:.1f} % d ensemble.")
    print("  ⇒ LE MONDE EST BIEN LE COUPABLE. Retirer le gel ne rachete pas l ecart.")
elif nongel > 0.30:
    print(f"  {100*nongel:.1f} % — nettement au-dessus des {100*tout:.1f} % d ensemble.")
    print("  ⇒ J ACCUSAIS LE GYMNASE D UN CRIME COMMIS PAR L OPTIMISATION.")
    print("     Une bonne part de l ecart est de la DEGENERESCENCE, pas du monde.")
else:
    print(f"  {100*nongel:.1f} % — entre les deux. Les deux ecarts pesent, aucun ne domine.")
print(f"\n  part des episodes geles : {100*sum(1 for e in E if e['nact']==1)/len(E):.1f} %")
