#!/usr/bin/env python3
"""sonde2b.py — LE BROUILLAGE, REFAIT.

Le premier jet ne testait pas ce qu'il prétendait tester. Deux défauts :
  · le drapeau « il tire en ce moment » était dans les entrées, donc prédire le tir à
    2 secondes se réduisait à lire la persistance (AUC 0,89 sans la moindre arête).
  · les liens étaient résumés en SIX nombres — c'est-à-dire exactement l'agrégation par
    somme qu'on cherche à mettre en défaut. La sonde mesurait la pauvreté du résumé, pas
    la richesse des liens.

Ici les liens sont donnés UN PAR UN, avec ce qui les caractérise vraiment :
ce que je sais de lui, si je le vois, à quelle distance, ET SOUS QUEL ANGLE PAR RAPPORT À
MON REGARD. ⟨mesuré au contrôle positif : un observateur seul ne voit pas un ennemi à 50 m
sur son flanc et voit celui à 300 m droit devant — l'angle décide, pas la distance⟩
Distance et angle ne sont pas capturés : ils se recalculent ici, hors ligne, gratuitement.

QUATRE CONDITIONS. Chacune répond à une question différente.
  1. SANS liens ................ le plancher
  2. liens RÉSUMÉS (6 nombres) . ce que fait une agrégation par somme
  3. liens UN PAR UN ........... ce que pourrait lire une attention
  4. liens un par un BROUILLÉS . les mêmes valeurs, rattachées à d'autres hommes

CRITÈRES ÉCRITS AVANT DE REGARDER
  · (3) doit battre (1) d'au moins 3 % de pouvoir prédictif, sinon les liens ne portent rien
    et la sonde 1 est sans objet.
  · (4) doit retomber d'au moins 10 % sous (3), sinon le modèle n'utilisait pas la structure
    des liens mais leur seule statistique — le décor.
  · (3) contre (2) est un avant-goût de la sonde 1 : si lire un par un ne bat pas le résumé,
    l'attention n'a pas de raison d'être.
  · Le brouillage conserve la distribution : mêmes valeurs, autres destinataires.

Mesure : aire sous la courbe ROC. 0,5 = hasard.
"""
import numpy as np, json, time
import torch, torch.nn as nn
from collections import defaultdict

D = '/mnt/data/corpus/tenseurs'
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
torch.manual_seed(7); np.random.seed(7)
torch.cuda.set_device(0)

X   = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P   = np.load(f'{D}/presence.npy', mmap_mode='r')
AR  = np.load(f'{D}/aretes.npy')
MORTS = np.load(f'{D}/morts.npy')
TPS = np.load(f'{D}/temps.npy')
SPL = np.load(f'{D}/split.npy')
T, N, _ = X.shape
print(f"corpus : {T} ticks, {N} places, {len(AR)} arêtes", flush=True)

ar_par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    ar_par_tick[int(t)].append((int(a), int(b), k, v, mes))
ticks_ar = np.array(sorted(ar_par_tick.keys()))

mort_de = {}
for tm, vic, tue, src in MORTS:
    v = int(vic)
    if v not in mort_de: mort_de[v] = tm

K = 8                      # liens retenus par homme, les mieux connus d'abord
CL = 6                     # nombres par lien
PAS = 4

print("\nconstruction des exemples (distance et angle recalculés ici)", flush=True)
t0 = time.time()
SOI, RES, IND, YA, YB, TICK = [], [], [], [], [], []
for ti in ticks_ar[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    pos = {}; azi = {}
    for j in range(N):
        if pt[j] and xt[j,0] > 0:
            uid = int(xt[j,0]); pos[uid] = (xt[j,1], xt[j,2]); azi[uid] = xt[j,7]
    idm = {int(xt[j,0]): j for j in range(N) if pt[j] and xt[j,0] > 0}
    if not idm: continue

    sait = defaultdict(list); connu = defaultdict(list)
    for a, b, k, v, mes in ar_par_tick[int(ti)]:
        sait[a].append((k, v, mes, b)); connu[b].append((k, v, mes, a))

    tnow = TPS[ti]
    fin = min(ti + 10, T)
    a_tire = set()
    if fin > ti + 1:
        fut = np.asarray(X[ti+1:fin, :, 6]); fid = np.asarray(X[ti+1:fin, :, 0])
        for r, c in np.argwhere(fut > 0.5): a_tire.add(int(fid[r, c]))

    for uid, j in idm.items():
        if xt[j,4] < 0.5: continue
        # DÉFAUT CORRIGÉ : le drapeau de tir ne figure PLUS dans les entrées
        SOI.append([xt[j,1]/1000, xt[j,2]/1000, xt[j,3]/100,
                    xt[j,5], xt[j,7]/360, xt[j,8]/3, xt[j,9]])

        s = sait.get(uid, []); c = connu.get(uid, [])
        RES.append([len(s)/10, max((k for k,_,_,_ in s), default=0)/4, sum(k for k,_,_,_ in s)/40,
                    len(c)/10, max((k for k,_,_,_ in c), default=0)/4,
                    sum(v for _,v,m,_ in c if m)/max(sum(1 for _,_,m,_ in c if m),1)])

        # les liens un par un, les mieux connus d'abord
        v = np.zeros(K*CL, np.float32)
        mp = pos.get(uid); ma = azi.get(uid, 0.0)
        for n, (k, vu, mes, autre) in enumerate(sorted(s, key=lambda x:-x[0])[:K]):
            ap = pos.get(autre)
            if ap is None or mp is None:
                d = rel = 0.0
            else:
                dx, dy = ap[0]-mp[0], ap[1]-mp[1]
                d = (dx*dx+dy*dy)**0.5
                gis = np.degrees(np.arctan2(dx, dy)) % 360
                rel = abs(((gis - ma + 180) % 360) - 180)      # 0 = droit devant, 180 = dans le dos
                d = min(d, 400.0)
            v[n*CL:(n+1)*CL] = [k/4, vu, mes, d/400, rel/180, 1.0]
        IND.append(v)

        YA.append(1.0 if uid in a_tire else 0.0)
        tm = mort_de.get(uid)
        YB.append(1.0 if (tm is not None and tnow < tm <= tnow + 10) else 0.0)
        TICK.append(ti)

SOI = np.array(SOI, np.float32); RES = np.array(RES, np.float32); IND = np.array(IND, np.float32)
YA = np.array(YA, np.float32); YB = np.array(YB, np.float32); TICK = np.array(TICK)
print(f"  {len(SOI)} exemples en {time.time()-t0:.0f} s")
print(f"  va tirer {YA.mean():.1%}   va mourir {YB.mean():.1%}", flush=True)

est_test = SPL[TICK] == 1
print(f"  apprentissage {(~est_test).sum()}   tenu à l'écart {est_test.sum()} ({est_test.mean():.0%})", flush=True)

def auc(y, p):
    o = np.argsort(p); y = y[o]
    pos = y.sum(); neg = len(y)-pos
    if pos == 0 or neg == 0: return float('nan')
    r = np.arange(1, len(y)+1)
    return (r[y==1].sum() - pos*(pos+1)/2)/(pos*neg)

class Petit(nn.Module):
    def __init__(s, d):
        super().__init__()
        s.f = nn.Sequential(nn.Linear(d,128), nn.ReLU(), nn.Linear(128,64), nn.ReLU(), nn.Linear(64,1))
    def forward(s, x): return s.f(x).squeeze(-1)

def entrainer(Xtr, ytr, epoques=25):
    m = Petit(Xtr.shape[1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    pos = max(ytr.sum(),1)
    lf = nn.BCEWithLogitsLoss(pos_weight=torch.tensor((len(ytr)-pos)/pos, device=dev))
    xt = torch.tensor(Xtr, device=dev); yt = torch.tensor(ytr, device=dev)
    B = 16384
    for ep in range(epoques):
        perm = torch.randperm(len(xt), device=dev)
        for i in range(0, len(xt), B):
            k = perm[i:i+B]
            opt.zero_grad(); lf(m(xt[k]), yt[k]).backward(); opt.step()
    m.eval(); return m

def evaluer(m, Xte, yte):
    with torch.no_grad():
        return auc(yte, m(torch.tensor(Xte, device=dev)).cpu().numpy())

def brouiller(L, ticks, graine=13):
    rng = np.random.default_rng(graine); L2 = L.copy()
    o = np.argsort(ticks, kind='stable'); ts = ticks[o]; deb = 0
    for i in range(1, len(ts)+1):
        if i == len(ts) or ts[i] != ts[deb]:
            b = o[deb:i]
            if len(b) > 1: L2[b] = L[b[rng.permutation(len(b))]]
            deb = i
    return L2

INDb = brouiller(IND, TICK)
print("\n" + "="*74, flush=True)
for nom, Y in [('va MOURIR dans 10 s', YB), ('va TIRER dans 2 s', YA)]:
    print(f"\n### {nom}   (taux de base {Y.mean():.2%})", flush=True)
    ytr, yte = Y[~est_test], Y[est_test]
    if yte.sum() < 50:
        print("  trop peu de cas tenus à l'écart — ON NE CONCLUT PAS"); continue

    F1 = SOI
    F2 = np.hstack([SOI, RES])
    F3 = np.hstack([SOI, IND])
    F4 = np.hstack([SOI, INDb])

    a1 = evaluer(entrainer(F1[~est_test], ytr), F1[est_test], yte)
    a2 = evaluer(entrainer(F2[~est_test], ytr), F2[est_test], yte)
    m3 = entrainer(F3[~est_test], ytr)
    a3 = evaluer(m3, F3[est_test], yte)
    a4 = evaluer(m3, F4[est_test], yte)            # même modèle, liens brouillés

    g = lambda a, b: (a-0.5)/(b-0.5)-1 if b > 0.5 else float('nan')
    print(f"  1. sans liens ............ AUC {a1:.4f}")
    print(f"  2. liens RÉSUMÉS ......... AUC {a2:.4f}   ({g(a2,a1):+.1%} sur le plancher)")
    print(f"  3. liens UN PAR UN ....... AUC {a3:.4f}   ({g(a3,a1):+.1%} sur le plancher, {g(a3,a2):+.1%} sur le résumé)")
    print(f"  4. un par un BROUILLÉS ... AUC {a4:.4f}   (perte {(a3-a4)/max(a3-0.5,1e-9):.1%} du pouvoir de (3))")

    print("  VERDICT :")
    if g(a3, a1) < 0.03:
        print(f"    les liens n'apportent rien ({g(a3,a1):+.1%} < 3 %). La sonde 1 est sans objet.")
    elif (a3-a4)/max(a3-0.5,1e-9) < 0.10:
        print(f"    ÉCHEC — casser les liens ne coûte que {(a3-a4)/max(a3-0.5,1e-9):.1%}. Le modèle a appris le décor.")
    else:
        print(f"    SUCCÈS — les liens portent l'information et la casser la retire.")
        if g(a3, a2) > 0.03:
            print(f"    De plus, les lire UN PAR UN bat le résumé de {g(a3,a2):+.1%} : l'attention a un sens.")
        else:
            print(f"    Mais les lire un par un ne bat pas le résumé ({g(a3,a2):+.1%}) : l'attention n'apporterait rien ici.")
    print(flush=True)
