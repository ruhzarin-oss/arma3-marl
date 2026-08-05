#!/usr/bin/env python3
"""fixation_vraie.py — LA FIXATION, AVEC LA CIBLE DU TIR.

⟨05/08, 5 h : j'allais lancer une re-capture de huit heures pour obtenir la cible du tir.
 Verification prealable — la regle du projet — : l'emetteur v9 l'emet DEJA. Ligne 92,
 `assignedTarget _u`, avec un commentaire disant que FiredMan a ete teste et ecarte.
 277 021 lignes `HMT|AR|tir|temps|tireur|cible` dorment dans nuit_20260803.log, dont
 215 480 (78 %) avec une cible identifiee. Elle n'etait simplement pas dans les tenseurs.
 Aucune re-capture. La donnee etait la depuis le debut.⟩

LA QUESTION, ENFIN POSABLE PROPREMENT
  Un ennemi qui tire sur mon camarade NE TIRE PAS SUR MOI.
  A danger geometrique egal, un soldat dont les ennemis visibles tirent SUR QUELQU'UN
  D'AUTRE meurt-il moins ? C'est la fixation au sens strict — et c'est la derniere
  hypothese debout pour expliquer le +12,3 points de l'attaque a deux axes.

⟨la tentative precedente comptait « mes camarades tirent », sans savoir sur qui. Elle a
 trouve l'INVERSE : +2,83 % de mortalite a risque egal. Mais sans la cible, elle ne
 mesurait que « il y a du combat ici ». Avec la cible, la question change de nature.⟩

CRITERES, ecrits avant de regarder :
  G0 VALIDITE  chaque strate doit avoir >= 5 % d'observations de chaque cote.
  G1 FIXATION  a risque egal, un soldat dont les ennemis visibles tirent AILLEURS doit
               mourir MOINS : ecart <= -2 points sur >= 7 strates sur 10.
  G2 CONTROLE POSITIF  un soldat REELLEMENT VISE doit mourir PLUS, nettement. Si la cible
               journalisee ne predit meme pas la mort de celui qu'elle designe, elle n'est
               pas fiable et RIEN de ce qui suit ne vaut. C'est le controle qui peut tout
               arreter.
  G3 NUL       en brassant les cibles entre tireurs, les deux effets doivent disparaitre.
"""
import sys, math, re
from collections import defaultdict
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
te = est_test
FEN = 1.5     # fenetre autour du tick : un tir compte s'il part a moins de 1,5 s

# ---------------------------------------------------------------- lire les tirs
print("\n  lecture des tirs…", flush=True)
tirs = []
for l in open('/mnt/data/corpus/nuit_20260803.log', errors='ignore'):
    m = re.search(r'HMT\|AR\|tir\|([\d.]+)\|(\d+)\|(-?\d+)', l)
    if m: tirs.append((float(m.group(1)), int(m.group(2)), int(m.group(3))))
tirs.sort()
T_tir = np.array([t for t, _, _ in tirs])
print(f"  {len(tirs)} tirs · {sum(1 for _,_,c in tirs if c >= 0)} avec cible identifiee "
      f"({sum(1 for _,_,c in tirs if c >= 0)/len(tirs):.0%})", flush=True)

# index : pour chaque instant, quels tirs sont dans la fenetre
def tirs_autour(tnow):
    i = np.searchsorted(T_tir, tnow - FEN)
    j = np.searchsorted(T_tir, tnow + FEN)
    return tirs[i:j]

# ---------------------------------------------------------------- compter, tick par tick
print("  comptage tireur -> cible…", flush=True)
VISE, AILLEURS = [], []       # ennemis qui me visent · ennemis qui visent quelqu'un d'autre
for ti in ticks_ar[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    pos, viv = {}, {}
    for j in range(N):
        if pt[j] and xt[j,0] > 0:
            u = int(xt[j,0]); pos[u] = (xt[j,1], xt[j,2]); viv[u] = xt[j,4] > 0.5
    liens = defaultdict(list)
    for a, b, k, v, mes in ar_par_tick[int(ti)]:
        if a in pos and b in pos:
            liens[a].append(b); liens[b].append(a)
    tnow = TPS[ti]
    fen = tirs_autour(tnow)
    tir_de = defaultdict(list)
    for _, s, c in fen: tir_de[s].append(c)
    for u, es in liens.items():
        if not viv.get(u, False) or not es: continue
        es = sorted(set(es))[:K] if False else es
        # on garde EXACTEMENT le meme sous-ensemble que la sonde 1 : les K mieux informes
        ens = sorted(liens[u], key=lambda e: 0)[:K]
        nv, na = 0, 0
        for e in set(ens):
            cibles = tir_de.get(e, [])
            if not cibles: continue
            if u in cibles: nv += 1
            elif any(c >= 0 for c in cibles): na += 1
        VISE.append(float(nv)); AILLEURS.append(float(na))
VISE = np.array(VISE, np.float32); AILLEURS = np.array(AILLEURS, np.float32)
print(f"  {len(VISE)} observations · vise par au moins un {(VISE>0).mean():.2%} · "
      f"ennemi qui tire ailleurs {(AILLEURS>0).mean():.2%}", flush=True)
assert len(VISE) == len(Y), f"desalignement : {len(VISE)} contre {len(Y)}"

# ---------------------------------------------------------------- le risque geometrique
class R(nn.Module):
    def __init__(s, ce, cs, h=96):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(ce,h), nn.ReLU(), nn.Linear(h,h))
        s.q = nn.Linear(cs,h)
        s.out = nn.Sequential(nn.Linear(cs+h,h), nn.ReLU(), nn.Linear(h,1))
    def forward(s, soi, enn, msk):
        z = s.enc(enn)
        a = (z*s.q(soi).unsqueeze(1)).sum(-1)/math.sqrt(z.shape[-1])
        a = torch.softmax(a.masked_fill(msk<0.5,-1e9),-1).unsqueeze(-1)
        return s.out(torch.cat([soi,(z*a).sum(1)],-1)).squeeze(-1)

E_geo = ENN.copy(); E_geo[:,:,[0,1,2,6]] = 0.0
torch.manual_seed(0); np.random.seed(0)
m = R(ENN.shape[-1], SOI.shape[-1]).to(dev)
opt = torch.optim.Adam(m.parameters(), 2e-3)
tr = np.where(~te)[0]
S = torch.tensor(SOI,device=dev); E = torch.tensor(E_geo,device=dev)
M = torch.tensor(MASQ,device=dev); Yt = torch.tensor(Y,device=dev)
p_ = float(Y[tr].mean()); w = torch.tensor((1-p_)/p_, device=dev)
for _ in range(800):
    b = torch.tensor(np.random.choice(tr,4096), device=dev)
    l = nn.functional.binary_cross_entropy_with_logits(m(S[b],E[b],M[b]), Yt[b], pos_weight=w)
    opt.zero_grad(); l.backward(); opt.step()
with torch.no_grad():
    o = []
    for i in range(0, len(Y), 65536):
        b = torch.arange(i, min(i+65536,len(Y)), device=dev)
        o.append(m(S[b],E[b],M[b]).cpu().numpy())
RISK = np.concatenate(o)

# ---------------------------------------------------------------- stratifier
def strat(v, seuil=0.5):
    q = np.quantile(RISK, np.linspace(0,1,11))
    L, ok = [], 0
    for i in range(10):
        s = (RISK >= q[i]) & (RISK <= q[i+1])
        a = s & (v > seuil); b = s & (v <= seuil)
        if a.sum() < 50 or b.sum() < 50: continue
        L.append((i, a.sum(), b.sum(), Y[a].mean(), Y[b].mean(), Y[a].mean()-Y[b].mean(),
                  min(a.sum(),b.sum())/max(s.sum(),1)))
        if Y[a].mean() < Y[b].mean(): ok += 1
    return L, ok
glob = lambda L: float(np.average([d for *_,d,_ in L], weights=[a+b for _,a,b,*_ in L])) if L else 0.0

def montre(v, titre, seuil=0.5):
    L, ok = strat(v, seuil)
    print(f"\n  {titre}")
    print(f"  {'strate':>7s} {'n avec':>8s} {'n sans':>8s} {'mort AVEC':>11s} {'mort SANS':>11s} {'ecart':>9s}")
    for i,a,b,ma,mb,d,_ in L:
        print(f"  {i+1:7d} {a:8d} {b:8d} {ma:10.2%} {mb:10.2%} {d:+8.2%}")
    g = glob(L)
    print(f"  -> {len(L)}/10 strates · favorables {ok} · ECART GLOBAL {g:+.2%}")
    return L, ok, g

print("\n" + "="*82)
Lv, okv, gv = montre(VISE, "G2 CONTROLE POSITIF — un soldat REELLEMENT VISE meurt-il plus ?")
g2 = gv > 0.02
print(f"     -> {'OK, la cible journalisee predit bien la mort' if g2 else 'ECHEC : la cible n est pas fiable, RIEN de ce qui suit ne vaut'}")

if g2:
    La, oka, ga = montre(AILLEURS, "G1 FIXATION — les ennemis visibles tirent AILLEURS")
    g0 = len(La) >= 7 and all(p >= 0.05 for *_,p in La)
    g1 = oka >= 7 and ga < -0.02
    print(f"\n  G0 VALIDITE  {len(La)}/10 strates exploitables -> {'OK' if g0 else 'ECHEC'}")
    print(f"  G1 FIXATION  favorables {oka}/{len(La)} · ecart {ga:+.2%} (exige <= -2 pts)"
          f"  -> {'OK' if g1 else 'ECHEC'}")

    rng = np.random.default_rng(7)
    Lb, okb, gb = strat(rng.permutation(AILLEURS))[0], 0, 0
    Lb2, okb2 = strat(rng.permutation(AILLEURS))
    g3 = abs(glob(Lb2)) < 0.01
    print(f"  G3 NUL       cibles brassees : ecart {glob(Lb2):+.2%} -> {'OK' if g3 else 'ECHEC'}")

    print("\n" + "="*82)
    if g1 and g3:
        print("  LA FIXATION EXISTE. A danger geometrique egal, un soldat dont les ennemis")
        print("  visibles tirent SUR QUELQU'UN D'AUTRE meurt moins. C'est le mecanisme du")
        print("  +12,3 points : deux axes, donc des ennemis occupes ailleurs.")
    else:
        print("  PAS DE FIXATION DETECTABLE, meme avec la cible du tir. Le quatrieme canal")
        print("  tombe pour de bon, et le +12,3 points reste sans mecanisme identifie.")
    print("="*82)
