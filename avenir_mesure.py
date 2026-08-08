#!/usr/bin/env python3
"""avenir_mesure.py — LE TEST D AVENIR, refait sur les SEULES paires mesurees des deux cotes.

CE QUI A TUE LA PREMIERE VERSION : `HMT_VMAX` borne le nombre de calculs de ligne de vue par
soldat et par tick ; le reste sort a -1, « NON MESURE, a ne pas lire comme pas de vue ». La
couverture est de 61,5 % en mediane et varie de 17 a 100 %. A 10 s d ecart, seuls 4,4 % des
hommes etaient mesures AUX DEUX instants : je comparais deux echantillons, pas deux etats.

⟨j avais lu ce commentaire dans l emetteur et je l ai quand meme enfreint : traiter l absence
 de mesure comme une absence de vue. La regle 6 amendee visait exactement ca.⟩

CE QU ON FAIT : on balaie plusieurs horizons, et pour chacun on ne garde que les hommes
MESURES A t ET A t+DELTA. On rapporte la couverture avant le resultat — si elle est trop
maigre, on le dit et on ne lit pas.

CRITERES, inchanges :
  A  contre la PERSISTANCE (recopier le present) : ecart d AUC lisible au-dela de 0,010
  B  la DIRECTION : exactitude lisible au-dela de 3 points sur le prior
  effectif minimal pour lire : 2 000 couples, dont >= 200 transitions
"""
import math, sys, numpy as np, torch, torch.nn as nn
from collections import defaultdict

DEMI_CONE = 35.0
HORIZONS = [2.0, 5.0, 10.0]
N_MIN, TRANS_MIN, ECART_AUC, ECART_DIR = 2000, 200, 0.010, 0.03
D = '/mnt/data/corpus/tenseurs'

X = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy')
TPS = np.load(f'{D}/temps.npy')
T, N, _ = X.shape
par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    par_tick[int(t)].append((int(a), int(b), k, v, mes))
ticks = np.array(sorted(par_tick.keys()))
dt = float(np.median(np.diff(TPS[ticks])))
print(f"\n  {len(ticks)} ticks · pas median {dt:.2f} s")

_cache = {}


def table(ti):
    if ti in _cache:
        return _cache[ti]
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    d = {int(xt[j, 0]): (xt[j, 1], xt[j, 2], xt[j, 7], xt[j, 8], xt[j, 9])
         for j in range(N) if pt[j] and xt[j, 0] > 0 and xt[j, 4] > 0.5}
    if len(_cache) > 4000:
        _cache.clear()
    _cache[ti] = d
    return d


def lire(ti):
    """par soldat MESURE : (vu, direction du plus proche qui me voit, voisins)."""
    T_ = table(ti)
    mes, vu, dirn, vois = set(), set(), {}, defaultdict(list)
    for a, b, k, v, m in par_tick[ti]:
        if a not in T_ or b not in T_:
            continue
        vois[a].append(b)
        if m < 0.5:
            continue
        mes.add(a)
        if v > 0.5:
            xa, ya, aa, _, _ = T_[a]
            xb, yb, ab, _, _ = T_[b]
            gis = math.degrees(math.atan2(xa - xb, ya - yb)) % 360
            if abs(((gis - ab + 180) % 360) - 180) < DEMI_CONE:
                vu.add(a)
                rel = ((gis + 180) % 360 - aa + 180) % 360 - 180
                dirn[a] = int(((rel + 45) % 360) // 90)
    return T_, mes, vu, dirn, vois


def auc(s_, y_):
    o = np.argsort(s_); r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1
    return float('nan') if n1 == 0 or n0 == 0 else \
        (r[y_ > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def entraine(F, y, tr, te, sortie=1):
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    torch.manual_seed(0)
    Xt = torch.tensor(F, device=dev); yt = torch.tensor(y, device=dev)
    m = nn.Sequential(nn.Linear(F.shape[1], 24), nn.ReLU(), nn.Linear(24, sortie)).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=3e-3)
    itr = torch.tensor(np.where(tr)[0], device=dev)
    nb = min(2048, len(itr))
    for _ in range(400):
        i = itr[torch.randint(0, len(itr), (nb,), device=dev)]
        p = m(Xt[i])
        l = (nn.functional.binary_cross_entropy_with_logits(p.squeeze(-1), yt[i])
             if sortie == 1 else nn.functional.cross_entropy(p, yt[i]))
        opt.zero_grad(); l.backward(); opt.step()
    with torch.no_grad():
        return m(Xt[torch.tensor(np.where(te)[0], device=dev)]).cpu().numpy()


for H in HORIZONS:
    saut = max(1, int(round(H / dt)))
    F, yn, yd, pe, gr = [], [], [], [], []
    vus_t = tot_t = 0
    for i in range(0, len(ticks) - saut, 5):
        ti, tf = int(ticks[i]), int(ticks[i + saut])
        Tp, mp, vp, dp, vois = lire(ti)
        Tf, mf, vf, df, _ = lire(tf)
        tot_t += len(mp)
        communs = mp & mf
        vus_t += len(communs)
        for u in communs:
            es = vois.get(u, [])
            if not es:
                continue
            xu, yu, au, pu, su = Tp[u]
            d = [math.hypot(xu - Tp[e][0], yu - Tp[e][1]) for e in es]
            j = int(np.argmin(d)); e = es[j]
            xe, ye, ae, _, _ = Tp[e]
            gis = math.degrees(math.atan2(xu - xe, yu - ye)) % 360
            F.append([min(d[j], 400) / 400,
                      abs(((gis - ae + 180) % 360) - 180) / 180,
                      abs((((gis + 180) % 360) - au + 180) % 360 - 180) / 180,
                      len(es) / 12.0, pu / 3.0, su])
            yn.append(1.0 if u in vf else 0.0)
            yd.append(df.get(u, -1))
            pe.append(1.0 if u in vp else 0.0)
            gr.append(i // 400)
    F = np.array(F, np.float32); yn = np.array(yn, np.float32)
    yd = np.array(yd, np.int64); pe = np.array(pe, np.float32); gr = np.array(gr)
    couv = vus_t / max(tot_t, 1)
    trans = pe < 0.5
    print("\n" + "=" * 76)
    print(f"  HORIZON {H:.0f} s  ({saut} releves)")
    print("  " + "-" * 74)
    print(f"     couverture (mesures aux DEUX instants) : {couv:.1%}"
          f" · {len(F)} couples · {int(trans.sum())} surs")
    if len(F) < N_MIN or trans.sum() < TRANS_MIN:
        print("     EFFECTIF INSUFFISANT — on ne lit pas.")
        continue
    rg = np.random.default_rng(11)
    ec = set(rg.permutation(gr.max() + 1)[:max(1, (gr.max() + 1) // 5)].tolist())
    te = np.isin(gr, list(ec)); tr = ~te
    mtr, mte = tr & trans, te & trans
    if mte.sum() < 100 or yn[mte].sum() < 10:
        print(f"     trop peu de transitions tenues a l ecart ({int(mte.sum())},"
              f" {int(yn[mte].sum())} positives) — on ne lit pas.")
        continue
    a_p = auc(pe[mte], yn[mte])
    a_m = auc(entraine(F, yn, mtr, mte).squeeze(-1), yn[mte])
    print(f"     transitions jugees {int(mte.sum())} · dont vues ensuite {int(yn[mte].sum())}")
    print(f"     PERSISTANCE  AUC {a_p:.4f}   <- controle negatif")
    print(f"     modele       AUC {a_m:.4f}   ecart {a_m - a_p:+.4f}"
          f"   {'LISIBLE' if a_m - a_p >= ECART_AUC else 'sous la porte'}")
    m2 = trans & (yd >= 0)
    m2te, m2tr = te & m2, tr & m2
    if m2te.sum() >= 200:
        pr = np.bincount(yd[m2tr], minlength=4).argmax()
        e_pr = (yd[m2te] == pr).mean()
        e_mo = (entraine(F, yd, m2tr, m2te, 4).argmax(1) == yd[m2te]).mean()
        print(f"     DIRECTION  prior {e_pr:.1%} · modele {e_mo:.1%} · ecart {e_mo-e_pr:+.1%}"
              f"   {'LISIBLE' if e_mo - e_pr >= ECART_DIR else 'sous la porte'}")
    else:
        print(f"     DIRECTION  {int(m2te.sum())} cas tenus a l ecart — illisible")
print("\n" + "=" * 76)
print("  ⟨la couverture est rapportee AVANT chaque resultat : a 4,4 % on ne lisait pas deux")
print("   etats du meme monde, on lisait deux echantillons differents.⟩")
print("  " + "=" * 74)
