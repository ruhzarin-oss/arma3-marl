import sys, re, glob, math, pathlib, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B, terrain_gpu as TG
DC, ALIVE, LOS = 6, 4, 7
L = "/mnt/data/harmattan-sandbox/logs/live67"

E = []
for i in range(1, 68):
    f, tx = f"{L}/ep_{i}.npz", pathlib.Path(f"{L}/ep_{i}.txt")
    if not pathlib.Path(f).exists(): continue
    Z = np.load(f, allow_pickle=True); T = tx.read_text(errors="ignore")
    sc  = re.search(r'HARMATTAN_SCENE def=(\d+) att=(\d+)', T)
    fin = re.search(r'fin au pas (\d+) : vivants=(\d+) dmin=(\d+)', T)
    A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
    act = np.asarray(Z["actions"]).reshape(-1); p0 = pas == pas.min()
    E.append(dict(i=i, sc=(sc.group(1),sc.group(2)) if sc else None,
                  viv=int(fin.group(2)) if fin else 4, dmin=int(fin.group(3)) if fin else None,
                  az=math.degrees(math.atan2(A[p0,0].mean(), A[p0,1].mean()))%360,
                  nact=len(np.unique(act)), A=A, pas=pas))
print(f"  {len(E)} episodes lus\n")

print("─── CONTROLES POSITIFS ───")
n4 = sum(1 for e in E if e["sc"] == ("4","4"))
print(f"  1. scene def=4 att=4 confirmee par LE JEU : {n4}/{len(E)} → " + ("✓ PASSE" if n4==len(E) else "⛔"))
az = np.array([e["az"] for e in E])
print(f"  2. azimuts, ecart-type {az.std():.1f} deg (porte corrigee : > 60) → " + ("✓ PASSE" if az.std()>60 else "⛔"))

# ─── B : protection chez les exposes, definition = CELLULE PENTUE (voir CLARIF_B.md)
pol = charger(B.DEV); e = B.monde(64, 101); e.reset()
Cg, Mg, Eg = [], [], []
for t in range(60):
    inc = TG.sample(e.cover, e.apx, e.apy, e.scale).clamp(max=1.0).reshape(-1).cpu().numpy()
    o = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    with torch.no_grad(): l, v = pol(e._obs())
    e.step(l.argmax(-1), auto_reset=False)
    o2 = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    viv = o[:, ALIVE] > 0.5
    Cg.append((inc>0.5)[viv]); Eg.append((o[:,LOS]>0.5)[viv])
    Mg.append(((o[:,ALIVE]>0.5)&(o2[:,ALIVE]<=0.5))[viv])
Cg, Mg, Eg = np.concatenate(Cg), np.concatenate(Mg), np.concatenate(Eg)

Ca, Ma, Ea, Na = [], [], [], []
for ep in E:
    A, pas = ep["A"], ep["pas"]; u = np.unique(pas); P = [A[pas==p] for p in u]
    for a, b in zip(P[:-1], P[1:]):
        n = min(len(a), len(b))
        if n == 0: continue
        viv = a[:n, ALIVE] > 0.5
        Ca.append((a[:n,DC]<1e-6)[viv]); Ea.append((a[:n,LOS]>0.5)[viv]); Na.append(a[:n,8][viv])
        Ma.append(((a[:n,ALIVE]>0.5)&(b[:n,ALIVE]<=0.5))[viv])
Ca, Ma, Ea, Na = map(np.concatenate, (Ca, Ma, Ea, Na))

print("\n─── B : « la definition du gymnase (CELLULE PENTUE) transfere-t-elle ? » ───")
print("     ⚠️ ce n est PAS « le couvert protege-t-il sur Arma » — voir CLARIF_B.md\n")
R = {}
for nom, C, M, X in [("GYMNASE", Cg, Mg, Eg), ("ARMA", Ca, Ma, Ea)]:
    C, M = C[X], M[X]
    nc, nl = int(C.sum()), int((~C).sum()); mc, ml = int(M[C].sum()), int(M[~C].sum())
    pc, pl = mc/max(nc,1), ml/max(nl,1)
    R[nom] = dict(prot=(pl/pc if pc>0 else float("inf")), mc=mc, ml=ml)
    print(f"  {nom}\n    expose SUR pente : {nc:5d} pas · {mc:3d} morts · P={pc:.4f}")
    print(f"    expose hors      : {nl:5d} pas · {ml:3d} morts · P={pl:.4f}    PROTECTION = {R[nom]['prot']:.2f}\n")
ok1 = all(R[k]["prot"] > 1 for k in R); ok2 = all(R[k]["mc"]>=30 and R[k]["ml"]>=30 for k in R)
print(f"  controle 1 (protection>1) : " + " · ".join(f"{k} {R[k]['prot']:.2f}" for k in R) + " → " + ("✓" if ok1 else "⛔ capteur muet"))
print(f"  controle 2 (>=30 morts)   : " + " · ".join(f"{k} {R[k]['mc']}/{R[k]['ml']}" for k in R) + " → " + ("✓" if ok2 else "⛔"))
if ok1 and ok2:
    r = R["GYMNASE"]["prot"]/R["ARMA"]["prot"]
    print(f"\n  rapport = {r:.2f}  ⇒ " + ("le GYMNASE SUR-PROTEGE, B RETENUE" if r>2 else "refutee dans l autre sens" if r<0.5 else "les deux protegent PAREIL, B REFUTEE"))
else:
    print("\n  ⇒ B NON LISIBLE. Clause 1 de l avenant : on PROLONGE au meme protocole.")

print("\n─── LA PRISE ───")
npr = sum(1 for e in E if e["viv"]>0 and e["dmin"] is not None and e["dmin"]<25)
p = npr/len(E); s = 1.96*math.sqrt(p*(1-p)/len(E))
print(f"  {npr}/{len(E)} = {100*p:.1f} %   IC95 [{100*max(0,p-s):.1f} ; {100*min(1,p+s):.1f}]   gymnase 59,4 %")
print(f"  59,4 % dans l intervalle ? " + ("OUI" if p-s <= 0.594 <= p+s else "NON — l ecart de transfert TIENT"))

print("\n─── LE GEL (test binomial exact contre 3,1 %, bande absurde retiree) ───")
fig = sum(1 for e in E if e["nact"]==1); pf = fig/len(E); sf = 1.96*math.sqrt(pf*(1-pf)/len(E))
print(f"  {fig}/{len(E)} = {100*pf:.1f} %   IC95 [{100*max(0,pf-sf):.1f} ; {100*min(1,pf+sf):.1f}]   reference gymnase 3,1 %")
print(f"  ⇒ " + ("3,1 % EXCLU — le gel est REEL" if not (pf-sf <= 0.031 <= pf+sf) else "compatible avec le gymnase"))
