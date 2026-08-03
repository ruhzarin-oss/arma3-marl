#!/usr/bin/env python3
"""sonde1.py — LA SOMME CONTRE L'ATTENTION.

L'encodeur du modèle du monde agrège les entités par SOMME. C'est le verrou : après une
somme, « qui interagit avec qui » n'existe plus. La question est de savoir si ça coûte
quelque chose sur CE corpus.

L'HYPOTHÈSE, éclairée par la sonde 3 : l'ennemi qui compte compte PLUS que la moyenne des
ennemis. La somme traite tout le monde pareil ; l'attention peut se concentrer sur celui qui
me tient dans son champ à 200 m pendant que trois autres regardent ailleurs.

  · si un seul ennemi bien placé décide du sort, l'attention gagne
  · si c'est la moyenne qui décide, la somme suffit et le verrou n'en est pas un

CE QU'ON COMPARE — à budget de paramètres ÉGAL, mêmes graines, mêmes exemples :
  1. SANS ennemis ...... le plancher (le soldat seul)
  2. SOMME ............. chaque ennemi encodé, puis ADDITIONNÉS
  3. ATTENTION ......... chaque ennemi encodé, puis PONDÉRÉS selon leur pertinence

CRITÈRES ÉCRITS AVANT DE REGARDER
  1. (2) et (3) doivent tous deux battre (1). Sinon les ennemis n'apportent rien et la
     comparaison d'architectures n'a pas d'objet.
  2. (3) doit battre (2) d'au moins 5 % du pouvoir prédictif gagné sur le plancher.
     En dessous : le verrou de la somme n'en est pas un ICI, et on cherche ailleurs.
  3. LE CONTRÔLE QUI PEUT TOUT FAIRE ÉCHOUER — sur les soldats qui n'ont QU'UN SEUL ennemi,
     l'attention et la somme doivent être ÉQUIVALENTES. Avec un seul élément, pondérer ou
     additionner revient au même. Si l'attention gagne quand même, son avantage vient de son
     architecture (plus de couches, plus de souplesse) et non de sa lecture des liens :
     toute la sonde est alors invalide.

⟨leçon du 03/08 : la tâche doit être DE CAMP. « va tirer » et « va mourir » se lisaient dans
 l'état local. Ici la cible est la mort à 30 s, mais elle est prédite À PARTIR DE L'ENSEMBLE
 DES ENNEMIS et de leur géométrie — c'est bien une question relationnelle.⟩
"""
import numpy as np, time, math, json
import torch, torch.nn as nn
from collections import defaultdict

D = '/mnt/data/corpus/tenseurs'
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
torch.cuda.set_device(0)

X   = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P   = np.load(f'{D}/presence.npy', mmap_mode='r')
AR  = np.load(f'{D}/aretes.npy')
MORTS = np.load(f'{D}/morts.npy')
TPS = np.load(f'{D}/temps.npy')
SPL = np.load(f'{D}/split.npy')
T, N, _ = X.shape
print(f"corpus : {T} ticks, {len(AR)} arêtes", flush=True)

ar_par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    ar_par_tick[int(t)].append((int(a), int(b), k, v, mes))
ticks_ar = np.array(sorted(ar_par_tick.keys()))

mort_de = {}
for tm, vic, tue, src in MORTS:
    v = int(vic)
    if v not in mort_de: mort_de[v] = tm

K  = 12      # ennemis retenus par soldat
CE = 7       # nombres par ennemi
HOR = 30.0

print(f"\nconstruction — jusqu'à {K} ennemis par soldat", flush=True)
t0 = time.time()
SOI, ENN, MASQ, Y, NENN, TICK = [], [], [], [], [], []
PAS = 3
for ti in ticks_ar[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    pos = {}; azi = {}; viv = {}; sup = {}; pst = {}
    for j in range(N):
        if pt[j] and xt[j,0] > 0:
            u = int(xt[j,0]); pos[u] = (xt[j,1], xt[j,2], xt[j,3]); azi[u] = xt[j,7]
            viv[u] = xt[j,4] > 0.5; sup[u] = xt[j,9]; pst[u] = xt[j,8]
    liens = defaultdict(list)
    for a, b, k, v, mes in ar_par_tick[int(ti)]:
        if a in pos and b in pos:
            liens[a].append((b, k, v, mes)); liens[b].append((a, k, v, mes))
    tnow = TPS[ti]
    for u, es in liens.items():
        if not viv.get(u, False) or not es: continue
        pu = pos[u]; au = azi[u]
        # on classe les ennemis par ce qu'ils savent de moi : le plus informé d'abord
        es = sorted(es, key=lambda x: -x[1])[:K]
        v = np.zeros((K, CE), np.float32); msk = np.zeros(K, np.float32)
        for n, (e, k, vu, mes) in enumerate(es):
            pe = pos.get(e)
            if pe is None: continue
            dx, dy = pu[0]-pe[0], pu[1]-pe[1]
            d = math.hypot(dx, dy)
            if d < 1: d = 1.0
            gis_e_u = math.degrees(math.atan2(dx, dy)) % 360
            # sous quel angle SUIS-JE dans SON champ  (c'est ça qui tue, mesuré +75 %)
            a_lui = abs(((gis_e_u - azi.get(e, 0.0) + 180) % 360) - 180)
            # et lui dans le mien
            a_moi = abs(((((gis_e_u+180) % 360) - au + 180) % 360) - 180)
            v[n] = [k/4, vu, mes, min(d,400)/400, a_lui/180, a_moi/180, sup.get(e,0.0)]
            msk[n] = 1.0
        SOI.append([pu[0]/1000, pu[1]/1000, pu[2]/100, au/360, pst.get(u,0)/3, sup.get(u,0.0)])
        ENN.append(v); MASQ.append(msk); NENN.append(int(msk.sum())); TICK.append(ti)
        tm = mort_de.get(u)
        Y.append(1.0 if (tm is not None and tnow < tm <= tnow + HOR) else 0.0)

SOI = np.array(SOI, np.float32); ENN = np.array(ENN, np.float32)
MASQ = np.array(MASQ, np.float32); Y = np.array(Y, np.float32)
NENN = np.array(NENN); TICK = np.array(TICK)
est_test = SPL[TICK] == 1
print(f"  {len(SOI)} observations en {time.time()-t0:.0f} s   mortalité {Y.mean():.2%}")
print(f"  ennemis par soldat : médiane {np.median(NENN):.0f}, moyenne {NENN.mean():.1f}, max {NENN.max()}")
print(f"  apprentissage {(~est_test).sum()}   tenu à l'écart {est_test.sum()}", flush=True)

def auc(y, p):
    o = np.argsort(p); y = y[o]
    pos = y.sum(); neg = len(y)-pos
    if pos == 0 or neg == 0: return float('nan')
    r = np.arange(1, len(y)+1)
    return (r[y==1].sum() - pos*(pos+1)/2)/(pos*neg)

H = 48
class Plancher(nn.Module):
    def __init__(s):
        super().__init__()
        s.f = nn.Sequential(nn.Linear(6,H), nn.ReLU(), nn.Linear(H,H), nn.ReLU(),
                            nn.Linear(H,H), nn.ReLU(), nn.Linear(H,1))
    def forward(s, soi, enn, msk): return s.f(soi).squeeze(-1)

class Somme(nn.Module):
    """chaque ennemi encodé séparément, puis ADDITIONNÉS — l'encodeur actuel du RSSM"""
    def __init__(s):
        super().__init__()
        s.e = nn.Sequential(nn.Linear(CE,H), nn.ReLU(), nn.Linear(H,H), nn.ReLU())
        s.f = nn.Sequential(nn.Linear(6+H,H), nn.ReLU(), nn.Linear(H,1))
    def forward(s, soi, enn, msk):
        h = s.e(enn) * msk.unsqueeze(-1)
        return s.f(torch.cat([soi, h.sum(1)], -1)).squeeze(-1)

class Attention(nn.Module):
    """mêmes encodages, mais PONDÉRÉS selon leur pertinence au lieu d'être additionnés"""
    def __init__(s):
        super().__init__()
        s.e = nn.Sequential(nn.Linear(CE,H), nn.ReLU(), nn.Linear(H,H), nn.ReLU())
        s.q = nn.Linear(6, H)
        s.f = nn.Sequential(nn.Linear(6+H,H), nn.ReLU(), nn.Linear(H,1))
    def forward(s, soi, enn, msk):
        h = s.e(enn)                                   # (B, K, H)
        q = s.q(soi).unsqueeze(1)                      # (B, 1, H)
        sc = (h*q).sum(-1) / math.sqrt(H)              # (B, K)
        sc = sc.masked_fill(msk < 0.5, -1e9)
        a = torch.softmax(sc, -1).unsqueeze(-1)
        ctx = (h*a).sum(1)
        return s.f(torch.cat([soi, ctx], -1)).squeeze(-1)

def entrainer(cls, idx_tr, idx_te, graine, epoques=20):
    torch.manual_seed(graine); np.random.seed(graine)
    m = cls().to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    ytr = Y[idx_tr]; pos = max(ytr.sum(),1)
    lf = nn.BCEWithLogitsLoss(pos_weight=torch.tensor((len(ytr)-pos)/pos, device=dev))
    s_tr = torch.tensor(SOI[idx_tr], device=dev); e_tr = torch.tensor(ENN[idx_tr], device=dev)
    m_tr = torch.tensor(MASQ[idx_tr], device=dev); y_tr = torch.tensor(ytr, device=dev)
    B = 8192
    for ep in range(epoques):
        perm = torch.randperm(len(s_tr), device=dev)
        for i in range(0, len(s_tr), B):
            k = perm[i:i+B]
            opt.zero_grad()
            lf(m(s_tr[k], e_tr[k], m_tr[k]), y_tr[k]).backward()
            opt.step()
    m.eval()
    with torch.no_grad():
        s_te = torch.tensor(SOI[idx_te], device=dev); e_te = torch.tensor(ENN[idx_te], device=dev)
        m_te = torch.tensor(MASQ[idx_te], device=dev)
        p = np.concatenate([m(s_te[i:i+65536], e_te[i:i+65536], m_te[i:i+65536]).cpu().numpy()
                            for i in range(0, len(s_te), 65536)])
    return auc(Y[idx_te], p), sum(x.numel() for x in m.parameters())

def campagne(nom, filtre):
    idx = np.where(filtre)[0]
    tr = idx[~est_test[idx]]; te = idx[est_test[idx]]
    print(f"\n### {nom}   apprentissage {len(tr)}  écart {len(te)}  mortalité {Y[te].mean():.2%}", flush=True)
    if len(te) < 5000 or Y[te].sum() < 100:
        print("   trop peu d'exemples — ON NE CONCLUT PAS"); return None
    out = {}
    for lib, cls in [('plancher', Plancher), ('somme', Somme), ('attention', Attention)]:
        aucs = []
        for g in (1, 2, 3):
            a, np_ = entrainer(cls, tr, te, g)
            aucs.append(a)
        out[lib] = (float(np.mean(aucs)), float(np.std(aucs)), np_)
        print(f"   {lib:10s} AUC {np.mean(aucs):.4f} ± {np.std(aucs):.4f}   ({np_} paramètres)", flush=True)
    return out

print("\n" + "="*74)
r_multi = campagne("SOLDATS AVEC AU MOINS 3 ENNEMIS  (l'attention a de quoi arbitrer)", NENN >= 3)
r_seul  = campagne("CONTRÔLE — SOLDATS AVEC UN SEUL ENNEMI  (rien à arbitrer)", NENN == 1)

print("\n" + "="*74)
print("VERDICT — contre les critères écrits avant\n")
if r_multi:
    pl, so, at = r_multi['plancher'][0], r_multi['somme'][0], r_multi['attention'][0]
    g_so = (so-pl)/max(pl-0.5,1e-9); g_at = (at-pl)/max(pl-0.5,1e-9)
    gain = (at-so)/max(so-pl,1e-9) if so > pl else float('nan')
    print(f"  1. les ennemis apportent : somme {g_so:+.1%}, attention {g_at:+.1%} sur le plancher")
    ok1 = so > pl and at > pl
    print(f"     -> {'PASSE' if ok1 else 'ÉCHOUE'}")
    print(f"  2. l'attention bat la somme de {gain:+.1%} du gain (seuil 5 %)")
    ok2 = gain >= 0.05
    print(f"     -> {'PASSE' if ok2 else 'ÉCHOUE'}")
    ok3 = True
    if r_seul:
        d = r_seul['attention'][0] - r_seul['somme'][0]
        ok3 = abs(d) < 0.005
        print(f"  3. sur un seul ennemi, écart attention-somme : {d:+.4f} (doit être ~0)")
        print(f"     -> {'PASSE' if ok3 else 'ÉCHOUE — avantage architectural, sonde invalide'}")
    print()
    if ok1 and ok2 and ok3:
        print("  L'ATTENTION LIT CE QUE LA SOMME DÉTRUIT.")
        print("  Le verrou est confirmé : l'encodeur du modèle du monde doit changer.")
    elif ok1 and not ok2 and ok3:
        print("  LA SOMME SUFFIT ICI. Le verrou n'en est pas un sur ce corpus :")
        print("  c'est la moyenne des ennemis qui décide, pas un ennemi en particulier.")
        print("  Ne pas complexifier l'encodeur — chercher ailleurs (horizon, entrées).")
    else:
        print("  RÉSULTAT NON CONCLUANT — voir quel contrôle a lâché.")
