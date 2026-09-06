#!/usr/bin/env python3
"""monde3 — LA REPARATION EST DANS LE LECTEUR, PAS DANS LE MODELE.

DIAGNOSTIC DU 26/08 : `vu` etait appris a 49 % de son tarif (x1,19 pour x2,45).
 · redondance avec knowsAbout : REFUTEE (correlation 0,082 ; ka vaut 3,93 vu et 3,79 non-vu) ;
 · rarete : n explique pas (knowsAbout est le PLUS frequent et n est appris qu a 72 %) ;
 · ⭐ DILUTION A LA LECTURE : seules 55 291 paires (source,cible) figurent dans la table.
   Mon extracteur mettait `vu`=0 pour TOUTE paire absente — donc « JAMAIS OBSERVE » devenait
   « PAS VU ». Le meta prevenait : « 0 => vue NON OBSERVEE, ne pas lire comme absence de vue ».

LA CORRECTION : TROIS ETATS AU LIEU DE DEUX. On ajoute un onzieme trait `observe` (une arete
MESUREE existe-t-elle pour cet homme a ce tick ?). Le modele peut alors distinguer
« su non-vu » de « inconnu », ce qu il ne pouvait pas faire.

⚠️ Et une decouverte annexe : knowsAbout vaut 3,9 sur 4 en moyenne, VU OU PAS. Il est
QUASI SATURE — donc le test « knowsAbout > 1 » ne mesurait pas un degre de connaissance mais
L EXISTENCE D UNE ARETE. Le tarif x2,77 qu on lui attribuait est en fait celui de
l OBSERVABILITE. On garde les deux traits separes pour que le banc puisse le dire.
"""
import numpy as np, torch, torch.nn as nn, json, time, hashlib
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy'); T = X.shape[0]
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
dev = 'cuda:0'; LEN = 12; BARREAU = 0.7379
H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_BARREAU.md', 'rb').read()).hexdigest()[:16]
R = json.load(open('/mnt/data/reparation.json'))
print("=" * 96); print(" MONDE 3 — encodage a TROIS ETATS (portes %s)" % H); print("=" * 96, flush=True)

ok = AR[:, 5] > 0.5
cle = AR[ok, 0].astype(np.int64) * 100000 + AR[ok, 2].astype(np.int64)
ka_, vue_ = AR[ok, 3], AR[ok, 4]
o = np.argsort(cle, kind="stable"); cle, ka_, vue_ = cle[o], ka_[o], vue_[o]
bornes = np.linspace(0, T, 21).astype(int)

def batir(blocs, nb=5, pas_id=250):
    F, Y = [], []
    for b in blocs[:nb]:
        ta, tb = bornes[b], min(bornes[b] + 6000, bornes[b + 1])
        A = np.asarray(X[ta:tb]); pr = np.asarray(P[ta:tb]) > 0.5
        idb = A[..., ID]; ids = np.unique(idb[pr])
        for u in ids[:: max(1, len(ids) // pas_id)]:
            m = pr & (idb == u)
            if m.sum() < LEN + 2: continue
            tt, pl = np.nonzero(m); s = np.argsort(tt); tt, pl = tt[s], pl[s]
            gu, gi = np.unique(tt, return_index=True); tt, pl = tt[gi], pl[gi]
            a = A[tt, pl, :]
            cl = np.sort((tt + ta) * 100000 + int(u))
            i = np.searchsorted(cle, cl, "left"); j = np.searchsorted(cle, cl, "right")
            kk = np.zeros(len(cl), np.float32); vv = np.zeros(len(cl), np.float32)
            obs = (j > i).astype(np.float32)          # ⭐ LE TROISIEME ETAT
            for n in range(len(cl)):
                if j[n] > i[n]: kk[n] = ka_[i[n]:j[n]].max(); vv[n] = vue_[i[n]:j[n]].max()
            tr = np.stack([a[:, XX] / 5000, a[:, YY] / 5000, a[:, ZZ] / 500, a[:, CAMP],
                           a[:, TIR], a[:, AZ] / 360, a[:, POST] / 3, a[:, SUPP],
                           vv, kk / 4.0, obs], 1).astype(np.float32)
            v = a[:, VIV]
            for k in range(LEN, len(a) - 1):
                if v[k] < 0.5: continue
                F.append(tr[k - LEN:k]); Y.append(1.0 if v[k + 1] < 0.5 else 0.0)
    return np.array(F, np.float32), np.array(Y, np.float32)

t0 = time.time()
Fa, Ya = batir(R["blocs_etude"], nb=5); Fe, Ye = batir(R["blocs_ecart"], nb=3)
print("  ETUDE %d fenetres / %d positifs   ECART %d / %d   (%.0f s)"
      % (len(Ya), Ya.sum(), len(Ye), Ye.sum(), time.time() - t0), flush=True)
print("  part des pas OBSERVES (arete mesuree existante) : %.1f %%" % (100 * Fa[:, -1, 10].mean()), flush=True)

class Modele(nn.Module):
    def __init__(self, nf=11, nh=96):
        super().__init__(); self.g = nn.GRU(nf, nh, batch_first=True)
        self.t = nn.Sequential(nn.Linear(nh, nh), nn.ReLU(), nn.Linear(nh, 1))
    def forward(self, x):
        h, _ = self.g(x); return self.t(h[:, -1]).squeeze(-1)

def auc(p, y):
    o = np.argsort(p, kind="stable"); z = y[o]
    pos = z.sum(); neg = len(z) - pos
    return float((np.arange(1, len(z) + 1)[z == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

torch.manual_seed(7)
m = Modele().to(dev); opt = torch.optim.Adam(m.parameters(), lr=1e-3)
Xa = torch.tensor(Fa, device=dev); Ta = torch.tensor(Ya, device=dev); Xe = torch.tensor(Fe, device=dev)
w = float((1 - Ya.mean()) / max(Ya.mean(), 1e-9))
lossf = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(w, device=dev))
print("\n─── ENTRAINEMENT ───", flush=True)
for ep in range(14):
    per = torch.randperm(len(Xa), device=dev); tot = 0.0
    for i in range(0, len(Xa), 4096):
        idx = per[i:i + 4096]; l = lossf(m(Xa[idx]), Ta[idx])
        opt.zero_grad(); l.backward(); opt.step(); tot += float(l.detach()) * len(idx)
    if ep % 4 == 0 or ep == 13:
        with torch.no_grad():
            pe = torch.cat([m(Xe[i:i + 8192]) for i in range(0, len(Xe), 8192)]).cpu().numpy()
        print("  epoque %2d  perte %.4f  AUC ECART %.4f" % (ep, tot / len(Xa), auc(pe, Ye)), flush=True)
with torch.no_grad():
    pe = torch.cat([m(Xe[i:i + 8192]) for i in range(0, len(Xe), 8192)]).cpu().numpy()
a = auc(pe, Ye)
print("\n─── PORTE BASSE ───")
print("  MODELE 3  AUC %.4f   (modele 2 : 0.9285 | barreau %.4f)  n = %d positifs" % (a, BARREAU, int(Ye.sum())))

print("\n─── PORTE MOYENNE (rapports de COTES) ───")
def risque(t):
    with torch.no_grad():
        return torch.sigmoid(torch.cat([m(t[i:i + 8192]) for i in range(0, len(t), 8192)])).cpu().numpy()
CIB = {"supprime": 29.81, "knowsAbout": 2.77, "vu": 2.45}
obt = {}
print("  %-14s %10s %12s %12s" % ("facteur", "n allume", "vrai", "MODELE 3"))
for nom, ci, seuil in (("supprime", 7, 1e-6), ("knowsAbout", 9, 0.25), ("vu", 8, 0.5)):
    on = Fe[:, -1, ci] > seuil
    if on.sum() < 50: continue
    Z = torch.tensor(Fe[on], device=dev)
    pa = risque(Z); Z[:, :, ci] = 0.0; ps = risque(Z)
    cote = lambda q: float(np.mean(q / np.clip(1 - q, 1e-9, None)))
    r = cote(pa) / max(cote(ps), 1e-12); obt[nom] = r
    print("  %-14s %10d %11.2f x %11.2f x   (%.0f %% du tarif)" % (nom, on.sum(), CIB[nom], r, 100 * r / CIB[nom]))
print("\n  AVANT (modele 2) : supprime 27,91 | knowsAbout 2,00 | vu 1,19  (94 %, 72 %, 49 %)")
if "vu" in obt:
    print("  -> `vu` passe de 49 %% a %.0f %% de son tarif   %s"
          % (100 * obt["vu"] / CIB["vu"],
             "REPARE" if obt["vu"] > 1.8 else "toujours sous-appris"))
torch.save(m.state_dict(), '/mnt/data/monde3.pt')
json.dump({"auc": a, "barreau": BARREAU, "tarifs": obt, "n_positifs": int(Ye.sum())},
          open('/mnt/data/monde3.json', 'w'), indent=1)
