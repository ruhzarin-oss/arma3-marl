#!/usr/bin/env python3
"""sonde2.py — LE BROUILLAGE DES ARÊTES.

La question : les liens qu'on a capturés portent-ils de l'information, ou le modèle
prédirait-il aussi bien sans eux ? ⟨sonde réclamée par Fable, la moins chère des trois,
et celle qui conditionne les deux autres⟩

DEUX TÂCHES, choisies parce qu'elles sont tactiques et vérifiables :
  A · cet homme va-t-il TIRER dans les 2 secondes ?
  B · cet homme va-t-il MOURIR dans les 10 secondes ?

TROIS CONDITIONS, pas deux. Sans plancher, un écart ne s'interprète pas.
  1. SANS arêtes ......... l'homme seul : position, regard, posture, suppression
  2. AVEC arêtes vraies .. + ce qu'il sait des ennemis, + qui le connaît
  3. AVEC arêtes BROUILLÉES  les mêmes valeurs, rattachées à d'autres hommes

CRITÈRES ÉCRITS AVANT DE REGARDER ⟨règle payée quatre fois le 31/07⟩

  · Si (2) ne bat pas (1) d'au moins 3 % relatif : les arêtes n'apportent rien dès le départ.
    Inutile d'aller plus loin, le brouillage ne dira rien.
  · Si (3) reste à moins de 10 % de (2) : ÉCHEC de la sonde. Le modèle n'utilisait pas les
    liens — il a appris le décor, et un encodeur à attention ne servira à rien.
  · Si (3) retombe vers (1) : SUCCÈS. Les liens portent l'information, et la casser la retire.
  · Le brouillage doit conserver la DISTRIBUTION des valeurs (mêmes nombres, autres
    destinataires). Sinon on mesure un changement de statistique, pas une perte de structure.

Mesure : aire sous la courbe ROC. Elle vaut 0,5 pour un modèle qui devine au hasard, ce qui
donne un repère absolu en plus des comparaisons.
"""
import numpy as np, json, sys, time
import torch, torch.nn as nn
from collections import defaultdict

D = '/mnt/data/corpus/tenseurs'
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
torch.manual_seed(7); np.random.seed(7)
print(f"appareil : {dev}", flush=True)
if dev == 'cuda': print(f"  {torch.cuda.get_device_name(0)}", flush=True)

meta = json.load(open(f'{D}/meta.json'))
X    = np.load(f'{D}/noeuds.npy', mmap_mode='r')     # (T, N, 11)
P    = np.load(f'{D}/presence.npy', mmap_mode='r')   # (T, N)
AR   = np.load(f'{D}/aretes.npy')                    # (tick, de, vers, k, vue, mesuree)
MORTS= np.load(f'{D}/morts.npy')                     # (temps, victime, tueur, source)
TPS  = np.load(f'{D}/temps.npy')
SPL  = np.load(f'{D}/split.npy')
T, N, _ = X.shape
print(f"corpus : {T} ticks, {N} places, {len(AR)} arêtes", flush=True)

# --- index des arêtes par tick, pour ne pas rebalayer 1,5 million de lignes à chaque fois
ar_par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    ar_par_tick[int(t)].append((int(a), int(b), k, v, mes))
ticks_avec_aretes = np.array(sorted(ar_par_tick.keys()))
print(f"ticks porteurs d'arêtes : {len(ticks_avec_aretes)}", flush=True)

# --- morts par identifiant, pour la cible B
mort_de = {}
for tm, vic, tue, src in MORTS:
    v = int(vic)
    if v not in mort_de: mort_de[v] = tm

# ===================== CONSTRUCTION DES EXEMPLES =====================
# Un exemple = un homme vivant à un tick porteur d'arêtes.
#   entrée « soi »   : 8 nombres tirés de sa ligne de nœud
#   entrée « liens » : 6 nombres résumant ce qu'il sait et ce qu'on sait de lui
#   cibles           : a-t-il tiré dans les 2 s ? est-il mort dans les 10 s ?
print("\nconstruction des exemples", flush=True)
t0 = time.time()
SOI, LIENS, YA, YB, GRP, TICK = [], [], [], [], [], []
PAS = 2                                   # 1 tick sur 2 parmi ceux qui portent des arêtes
for ti in ticks_avec_aretes[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    idm = {int(xt[j,0]): j for j in range(N) if pt[j] and xt[j,0] > 0}
    if not idm: continue
    # les liens de ce tick, agrégés par observateur ET par cible
    sait  = defaultdict(list)             # ce que MOI je sais
    connu = defaultdict(list)             # ce que les AUTRES savent de moi
    for a, b, k, v, mes in ar_par_tick[int(ti)]:
        sait[a].append((k, v, mes)); connu[b].append((k, v, mes))
    tnow = TPS[ti]
    # fenêtre future pour la cible A : le drapeau « a tiré » sur les 10 ticks suivants (~2 s)
    fin = min(ti + 10, T)
    fut = np.asarray(X[ti+1:fin, :, 6]) if fin > ti+1 else None
    futid = np.asarray(X[ti+1:fin, :, 0]) if fin > ti+1 else None
    a_tire = set()
    if fut is not None:
        w = np.argwhere(fut > 0.5)
        for r, c in w: a_tire.add(int(futid[r, c]))
    for uid, j in idm.items():
        if xt[j,4] < 0.5: continue        # on ne prédit rien pour un cadavre
        SOI.append([xt[j,1]/1000, xt[j,2]/1000, xt[j,3]/100,
                    xt[j,5], xt[j,7]/360, xt[j,8]/3, xt[j,9], xt[j,6]])
        s = sait.get(uid, []); c = connu.get(uid, [])
        LIENS.append([
            len(s)/10,                                        # combien d'ennemis je connais
            max((k for k,_,_ in s), default=0)/4,              # le mieux connu
            sum(k for k,_,_ in s)/40,                          # ma connaissance totale
            len(c)/10,                                         # combien me connaissent
            max((k for k,_,_ in c), default=0)/4,              # le mieux informé sur moi
            sum(v for _,v,mes in c if mes)/max(sum(1 for _,_,mes in c if mes),1),  # part qui me VOIT
        ])
        YA.append(1.0 if uid in a_tire else 0.0)
        tm = mort_de.get(uid)
        YB.append(1.0 if (tm is not None and tnow < tm <= tnow + 10) else 0.0)
        GRP.append(uid); TICK.append(ti)

SOI = np.array(SOI, np.float32); LIENS = np.array(LIENS, np.float32)
YA = np.array(YA, np.float32); YB = np.array(YB, np.float32)
TICK = np.array(TICK); GRP = np.array(GRP)
print(f"  {len(SOI)} exemples en {time.time()-t0:.0f} s")
print(f"  va tirer  : {YA.mean():.1%}    va mourir : {YB.mean():.1%}", flush=True)

# --- découpe par BLOC, telle qu'elle a été figée à la conversion (jamais par tick au hasard)
est_test = SPL[TICK] == 1
print(f"  apprentissage {(~est_test).sum()}   tenu à l'écart {est_test.sum()} ({est_test.mean():.0%})", flush=True)

def auc(y, p):
    o = np.argsort(p); y = y[o]
    pos = y.sum(); neg = len(y) - pos
    if pos == 0 or neg == 0: return float('nan')
    rangs = np.arange(1, len(y)+1)
    return (rangs[y == 1].sum() - pos*(pos+1)/2) / (pos*neg)

class Petit(nn.Module):
    def __init__(s, d):
        super().__init__()
        s.f = nn.Sequential(nn.Linear(d,64), nn.ReLU(), nn.Linear(64,64), nn.ReLU(), nn.Linear(64,1))
    def forward(s, x): return s.f(x).squeeze(-1)

def entrainer(Xtr, ytr, Xte, yte, nom, epoques=30):
    m = Petit(Xtr.shape[1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    pos = max(ytr.sum(), 1); poids = torch.tensor((len(ytr)-pos)/pos, device=dev)
    lf = nn.BCEWithLogitsLoss(pos_weight=poids)
    xt = torch.tensor(Xtr, device=dev); yt = torch.tensor(ytr, device=dev)
    xe = torch.tensor(Xte, device=dev)
    B = 8192
    for ep in range(epoques):
        perm = torch.randperm(len(xt), device=dev)
        for i in range(0, len(xt), B):
            k = perm[i:i+B]
            opt.zero_grad(); l = lf(m(xt[k]), yt[k]); l.backward(); opt.step()
    m.eval()
    with torch.no_grad():
        p = m(xe).cpu().numpy()
    return m, auc(yte, p)

def brouiller(L, ticks, graine=13):
    """Mélange les lignes de liens ENTRE hommes, à l'intérieur d'un même tick.
    La distribution des valeurs est intacte ; seule l'association homme<->liens est cassée."""
    rng = np.random.default_rng(graine)
    L2 = L.copy()
    ordre = np.argsort(ticks, kind='stable')
    deb = 0
    ts = ticks[ordre]
    for i in range(1, len(ts)+1):
        if i == len(ts) or ts[i] != ts[deb]:
            bloc = ordre[deb:i]
            if len(bloc) > 1: L2[bloc] = L[bloc[rng.permutation(len(bloc))]]
            deb = i
    return L2

print("\n" + "="*72)
resultats = {}
for nom_cible, Y in [('va TIRER dans 2 s', YA), ('va MOURIR dans 10 s', YB)]:
    print(f"\n### {nom_cible}   (taux de base {Y.mean():.2%})")
    ytr, yte = Y[~est_test], Y[est_test]
    if yte.sum() < 20:
        print("  pas assez de cas positifs tenus à l'écart — ON NE CONCLUT PAS"); continue

    # 1. SANS arêtes
    _, a1 = entrainer(SOI[~est_test], ytr, SOI[est_test], yte, 'sans')
    # 2. AVEC arêtes vraies
    F = np.hstack([SOI, LIENS])
    _, a2 = entrainer(F[~est_test], ytr, F[est_test], yte, 'avec')
    # 3. AVEC arêtes brouillées — on brouille SEULEMENT le test, le modèle est le même
    Lb = brouiller(LIENS, TICK)
    Fb = np.hstack([SOI, Lb])
    m2 = Petit(F.shape[1]).to(dev)
    m2, _ = entrainer(F[~est_test], ytr, F[est_test], yte, 'avec2')
    with torch.no_grad():
        a3 = auc(yte, m2(torch.tensor(Fb[est_test], device=dev)).cpu().numpy())

    g21 = (a2-0.5)/(a1-0.5) - 1 if a1 > 0.5 else float('nan')
    g23 = (a2-a3)/(a2-0.5) if a2 > 0.5 else float('nan')
    print(f"  1. sans arêtes ......... AUC {a1:.4f}")
    print(f"  2. avec arêtes vraies .. AUC {a2:.4f}   (+{g21:.1%} de pouvoir sur (1))")
    print(f"  3. arêtes BROUILLÉES ... AUC {a3:.4f}   (perte {g23:.1%} du pouvoir de (2))")
    resultats[nom_cible] = (a1, a2, a3, g21, g23)

print("\n" + "="*72)
print("VERDICT — contre les critères écrits avant\n")
for nom, (a1,a2,a3,g21,g23) in resultats.items():
    print(f"  {nom}")
    if not (a2 > a1 and g21 > 0.03):
        print(f"    -> les arêtes n'apportent rien dès le départ (+{g21:.1%} < 3 %).")
        print(f"       Le brouillage ne peut rien dire. À creuser AVANT la sonde 1.")
    elif g23 < 0.10:
        print(f"    -> ÉCHEC : casser les liens ne coûte que {g23:.1%} (< 10 %).")
        print(f"       Le modèle avait appris le décor. Une attention ne servirait à rien.")
    else:
        print(f"    -> SUCCÈS : casser les liens coûte {g23:.1%} du pouvoir prédictif.")
        print(f"       Les arêtes portent bien l'information. La sonde 1 a un sens.")
    print()
