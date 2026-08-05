#!/usr/bin/env python3
"""fixation_horizons.py — LA FIXATION DURE-T-ELLE QUATRE SECONDES ?

L'HYPOTHESE, ET D'OU ELLE VIENT
  La fixation a ete refutee a l'horizon de 30 s : les ennemis qui tirent ailleurs ne
  protegent pas (+0,96 %, 1 strate favorable sur 10), avec un controle positif fort
  (+17,07 % pour un soldat reellement vise).
  Mais un fait certifie du projet dit que l'arc de tir donne un SURSIS DE 4 SECONDES.
  Si la fixation dure quatre secondes, la chercher sur trente la noie.

⟨cette hypothese NAIT D'UN NEGATIF. C'est le schema que Fable traque depuis trois jours.
 Elle n'est recevable que parce qu'elle etait deja ecrite AVANT comme fait certifie — le
 sursis de 4 s n'est pas invente ce matin — et parce que le critere H4 ci-dessous peut
 l'enterrer.⟩

ON NE TESTE PAS UN HORIZON, ON TESTE UNE TENDANCE
  Un seul point a 5 s ne prouverait rien. On mesure 3, 5, 10, 20 et 30 secondes : si la
  fixation est un phenomene de quelques secondes, l'effet doit DECROITRE avec l'horizon.

CRITERES, ecrits avant de regarder :
  H0 VALIDITE   a chaque horizon, la mortalite doit rester >= 0,5 %, sinon trop rare.
  H1 CONTROLE POSITIF  un soldat REELLEMENT VISE doit mourir plus, a TOUS les horizons.
                Si la cible ne predit plus la mort a 5 s, la mesure ne vaut rien.
  H2 FIXATION   a 5 s, ecart <= -2 points sur >= 7 strates sur 10.
  H3 NUL        cibles brassees : rien, a tous les horizons.
  H4 TENDANCE — LE CRITERE QUI PEUT ENTERRER L'HYPOTHESE
                l'effet de fixation doit etre MONOTONE en l'horizon : plus fort a 3 s qu'a
                30 s. S'il est PLAT, l'explication « noyee dans trente secondes » est
                fausse, et la fixation est refutee pour de bon — quel que soit H2.
"""
import sys, math, re
from collections import defaultdict
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
te = est_test
FEN = 1.5
HORIZONS = [3.0, 5.0, 10.0, 20.0, 30.0]

print("\n  lecture des tirs…", flush=True)
tirs = []
for l in open('/mnt/data/corpus/nuit_20260803.log', errors='ignore'):
    m = re.search(r'HMT\|AR\|tir\|([\d.]+)\|(\d+)\|(-?\d+)', l)
    if m: tirs.append((float(m.group(1)), int(m.group(2)), int(m.group(3))))
tirs.sort()
T_tir = np.array([t for t, _, _ in tirs])

print("  comptage tireur -> cible, et mortalite a cinq horizons…", flush=True)
VISE, AILL = [], []
YH = {h: [] for h in HORIZONS}
for ti in ticks_ar[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    pos, viv = {}, {}
    for j in range(N):
        if pt[j] and xt[j,0] > 0:
            u = int(xt[j,0]); pos[u] = 1; viv[u] = xt[j,4] > 0.5
    liens = defaultdict(list)
    for a, b, k, v, mes in ar_par_tick[int(ti)]:
        if a in pos and b in pos: liens[a].append(b); liens[b].append(a)
    tnow = TPS[ti]
    i0 = np.searchsorted(T_tir, tnow - FEN); i1 = np.searchsorted(T_tir, tnow + FEN)
    tir_de = defaultdict(list)
    for _, s, c in tirs[i0:i1]: tir_de[s].append(c)
    for u, es in liens.items():
        if not viv.get(u, False) or not es: continue
        ens = es[:K]
        nv = na = 0
        for e in set(ens):
            cb = tir_de.get(e, [])
            if not cb: continue
            if u in cb: nv += 1
            elif any(c >= 0 for c in cb): na += 1
        VISE.append(float(nv)); AILL.append(float(na))
        tm = mort_de.get(u)
        for h in HORIZONS:
            YH[h].append(1.0 if (tm is not None and tnow < tm <= tnow + h) else 0.0)
VISE = np.array(VISE, np.float32); AILL = np.array(AILL, np.float32)
YH = {h: np.array(v, np.float32) for h, v in YH.items()}
assert len(VISE) == len(Y), f"desalignement {len(VISE)} / {len(Y)}"
assert np.allclose(YH[30.0], Y), "l horizon 30 s doit reproduire Y de la sonde 1"
print(f"  {len(VISE)} observations · controle d alignement et de reproduction : OK", flush=True)
print("  mortalite par horizon : " + " · ".join(f"{h:.0f}s {YH[h].mean():.2%}" for h in HORIZONS))

# ---------------------------------------------------------------- risque, par horizon
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
S = torch.tensor(SOI,device=dev); E = torch.tensor(E_geo,device=dev); M = torch.tensor(MASQ,device=dev)
tr = np.where(~te)[0]
def risque_pour(Yc, graine=0):
    torch.manual_seed(graine); np.random.seed(graine)
    m = R(ENN.shape[-1], SOI.shape[-1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), 2e-3)
    Yt = torch.tensor(Yc, device=dev)
    p_ = max(float(Yc[tr].mean()), 1e-5); w = torch.tensor((1-p_)/p_, device=dev)
    for _ in range(800):
        b = torch.tensor(np.random.choice(tr,4096), device=dev)
        l = nn.functional.binary_cross_entropy_with_logits(m(S[b],E[b],M[b]), Yt[b], pos_weight=w)
        opt.zero_grad(); l.backward(); opt.step()
    with torch.no_grad():
        o = []
        for i in range(0, len(Yc), 65536):
            b = torch.arange(i, min(i+65536,len(Yc)), device=dev)
            o.append(m(S[b],E[b],M[b]).cpu().numpy())
    return np.concatenate(o)

def strat(v, Yc, RISK, seuil=0.5):
    q = np.quantile(RISK, np.linspace(0,1,11))
    L, ok = [], 0
    for i in range(10):
        s = (RISK >= q[i]) & (RISK <= q[i+1])
        a = s & (v > seuil); b = s & (v <= seuil)
        if a.sum() < 50 or b.sum() < 50: continue
        L.append((a.sum(), b.sum(), Yc[a].mean()-Yc[b].mean()))
        if Yc[a].mean() < Yc[b].mean(): ok += 1
    g = float(np.average([d for *_,d in L], weights=[a+b for a,b,_ in L])) if L else 0.0
    return g, ok, len(L)

print("\n" + "="*80)
print("  L'EFFET DEPEND-IL DE L'HORIZON ?   (a risque geometrique egal, recalcule par horizon)")
print("  " + "-"*78)
print(f"  {'horizon':>8s} {'mortalite':>10s} {'VISE':>18s} {'tire AILLEURS':>22s}")
res = {}
for h in HORIZONS:
    Yc = YH[h]
    if Yc.mean() < 0.005:
        print(f"  {h:7.0f}s {Yc.mean():9.2%}   trop rare — ecarte"); continue
    RISK = risque_pour(Yc, graine=int(h))
    gv, okv, nv = strat(VISE, Yc, RISK)
    ga, oka, na = strat(AILL, Yc, RISK)
    res[h] = (gv, ga, oka, na)
    print(f"  {h:7.0f}s {Yc.mean():9.2%}   {gv:+7.2%} ({okv}/{nv})   {ga:+11.2%} ({oka}/{na})",
          flush=True)
print("="*80)

hs = sorted(res)
h0 = all(YH[h].mean() >= 0.005 for h in hs)
h1 = all(res[h][0] > 0.02 for h in hs)
print(f"\n  H0 VALIDITE  mortalite >= 0,5 % a tous les horizons retenus -> {'OK' if h0 else 'ECHEC'}")
print(f"  H1 CONTROLE POSITIF  le vise meurt plus a TOUS les horizons -> {'OK' if h1 else 'ECHEC'}")
if 5.0 in res:
    g5, ok5, n5 = res[5.0][1], res[5.0][2], res[5.0][3]
    h2 = ok5 >= 7 and g5 < -0.02
    print(f"  H2 FIXATION a 5 s  ecart {g5:+.2%} · favorables {ok5}/{n5} -> {'OK' if h2 else 'ECHEC'}")
ecarts = [res[h][1] for h in hs]
h4 = ecarts[0] < ecarts[-1] - 0.01
print(f"  H4 TENDANCE  effet a {hs[0]:.0f}s = {ecarts[0]:+.2%} · a {hs[-1]:.0f}s = {ecarts[-1]:+.2%}"
      f"  -> {'l effet DECROIT avec l horizon' if h4 else 'PLAT : l explication par l horizon est FAUSSE'}")

rng = np.random.default_rng(11)
RISK5 = risque_pour(YH[5.0] if 5.0 in res else YH[hs[0]], graine=99)
gn, _, _ = strat(rng.permutation(AILL), YH[5.0] if 5.0 in res else YH[hs[0]], RISK5)
h3 = abs(gn) < 0.01
print(f"  H3 NUL       cibles brassees a 5 s : {gn:+.2%} -> {'OK' if h3 else 'ECHEC'}")

print("\n" + "="*80)
if h4 and (5.0 in res and res[5.0][1] < -0.02):
    print("  LA FIXATION EXISTE, MAIS ELLE EST BREVE. Elle se voit a quelques secondes et")
    print("  s efface a trente : c est un SURSIS, pas une protection durable.")
elif not h4:
    print("  L HYPOTHESE DE L HORIZON EST FAUSSE. L effet ne decroit pas quand on raccourcit")
    print("  la fenetre : la fixation n etait pas « noyee dans trente secondes », elle")
    print("  N EXISTE PAS. Le quatrieme canal est clos definitivement.")
else:
    print("  PAS D EFFET NET a 5 s non plus. Voir les controles ligne par ligne.")
print("="*80)
