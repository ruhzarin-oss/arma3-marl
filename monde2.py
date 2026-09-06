#!/usr/bin/env python3
"""monde2 — LE MODELE DU MONDE, sur un banc REPARE et sous portes DEPOSEES.

Portes : DEPOT_BARREAU.md (013b37748504b4f7), scellees AVANT ce fichier.
  BASSE   : battre AUC 0,7379 sur la TRANSITION, blocs tenus a l ecart, avec son n.
  MOYENNE : retrouver l ordre des tarifs SANS qu on le lui montre —
            supprime x29,81  >>  knowsAbout x2,77  >  vu x2,45.

CE QUI CHANGE PAR RAPPORT A `monde.py`, ET POURQUOI :
 1. INDEXE PAR IDENTIFIANT. L ancien suivait des PLACES ; 93,5 % des entites changent de place
    au cours de leur vie, donc ZERO transition vivant->mort etait visible et sa tete de mort
    n avait aucune cible.
 2. COLONNES ALIGNEES sur meta.json. L ancien prenait X[...,:8] en oubliant `id` : tout etait
    decale d un cran, et sa « tete de mort » etait entrainee sur l ALTITUDE (AUC 0,9996 =
    persistance de z ; un temoin sans parametre y faisait 0,9825).
 3. CIBLE = LA TRANSITION, jamais l etat. « Est mort en k+1 » est trivial : 99,98 % l etaient
    deja en k, et le temoin « etait mort » y fait AUC 0,9998 sans un parametre.
 4. `posture` et `suppression` RECUPEREES — le [:8] les jetait.

L ENTREE NE CONTIENT PAS LES TARIFS. On donne les traits bruts par entite ; l ordre
suppression/knowsAbout/vu doit EMERGER, sinon la porte moyenne ne mesure rien.
"""
import numpy as np, torch, torch.nn as nn, json, time, hashlib, sys
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy')
T = X.shape[0]
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
dev = 'cuda:0'
H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_BARREAU.md', 'rb').read()).hexdigest()[:16]
R = json.load(open('/mnt/data/reparation.json'))
BARREAU = 0.7379
print("=" * 96); print(" MODELE DU MONDE — banc repare, portes scellees (%s)" % H); print("=" * 96, flush=True)

ok = AR[:, 5] > 0.5
cle = AR[ok, 0].astype(np.int64) * 100000 + AR[ok, 2].astype(np.int64)
ka_, vue_ = AR[ok, 3], AR[ok, 4]
o = np.argsort(cle, kind="stable"); cle, ka_, vue_ = cle[o], ka_[o], vue_[o]
bornes = np.linspace(0, T, 21).astype(int)
LEN = 12          # longueur de la fenetre par entite

def batir(blocs, nb=4, pas_id=250):
    """Fenetres de LEN pas, UNE ENTITE suivie par son IDENTIFIANT a travers les places."""
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
            for n in range(len(cl)):
                if j[n] > i[n]: kk[n] = ka_[i[n]:j[n]].max(); vv[n] = vue_[i[n]:j[n]].max()
            # traits BRUTS par pas : x, y, z, camp, tir, azimut, posture, suppression, vu, knowsAbout
            tr = np.stack([a[:, XX] / 5000, a[:, YY] / 5000, a[:, ZZ] / 500, a[:, CAMP],
                           a[:, TIR], a[:, AZ] / 360, a[:, POST] / 3, a[:, SUPP],
                           vv, kk / 4.0], 1).astype(np.float32)
            v = a[:, VIV]
            for k in range(LEN, len(a) - 1):
                if v[k] < 0.5: continue                      # on ne predit que pour un VIVANT
                F.append(tr[k - LEN:k]); Y.append(1.0 if v[k + 1] < 0.5 else 0.0)
    return np.array(F, np.float32), np.array(Y, np.float32)

t0 = time.time()
Fa, Ya = batir(R["blocs_etude"], nb=5)
Fe, Ye = batir(R["blocs_ecart"], nb=3)
print("  ETUDE  %d fenetres, %d positifs (%.4f %%)" % (len(Ya), Ya.sum(), 100 * Ya.mean()))
print("  ECART  %d fenetres, %d positifs (%.4f %%)   (%.0f s)" % (len(Ye), Ye.sum(), 100 * Ye.mean(), time.time() - t0), flush=True)
if Ya.sum() < 30 or Ye.sum() < 30:
    print("  ⛔ trop peu de positifs — on n entraine pas. Elargir les blocs."); sys.exit(0)

class Modele(nn.Module):
    def __init__(self, nf=10, nh=96):
        super().__init__()
        self.g = nn.GRU(nf, nh, batch_first=True)
        self.t = nn.Sequential(nn.Linear(nh, nh), nn.ReLU(), nn.Linear(nh, 1))
    def forward(self, x):
        h, _ = self.g(x); return self.t(h[:, -1]).squeeze(-1)

def auc(p, y):
    o = np.argsort(p, kind="stable"); z = y[o]
    pos = z.sum(); neg = len(z) - pos
    if pos == 0 or neg == 0: return float("nan")
    return float((np.arange(1, len(z) + 1)[z == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

torch.manual_seed(7)
m = Modele().to(dev); opt = torch.optim.Adam(m.parameters(), lr=1e-3)
Xa = torch.tensor(Fa, device=dev); Ta = torch.tensor(Ya, device=dev)
Xe = torch.tensor(Fe, device=dev)
w = float((1 - Ya.mean()) / max(Ya.mean(), 1e-9))
print("  poids de la classe rare : %.0f   (elle vaut %.4f %%)" % (w, 100 * Ya.mean()), flush=True)
lossf = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(w, device=dev))
B = 4096
print("\n─── ENTRAINEMENT (jamais sur les blocs tenus a l ecart) ───", flush=True)
for ep in range(14):
    m.train(); per = torch.randperm(len(Xa), device=dev); tot = 0.0
    for i in range(0, len(Xa), B):
        idx = per[i:i + B]
        l = lossf(m(Xa[idx]), Ta[idx])
        opt.zero_grad(); l.backward(); opt.step(); tot += float(l) * len(idx)
    if ep % 3 == 0 or ep == 13:
        m.eval()
        with torch.no_grad():
            pe = torch.cat([m(Xe[i:i + 8192]) for i in range(0, len(Xe), 8192)]).cpu().numpy()
        print("  epoque %2d  perte %.4f   AUC ECART %.4f   (barreau %.4f)"
              % (ep, tot / len(Xa), auc(pe, Ye), BARREAU), flush=True)
m.eval()
with torch.no_grad():
    pe = torch.cat([m(Xe[i:i + 8192]) for i in range(0, len(Xe), 8192)]).cpu().numpy()
a = auc(pe, Ye)
print("\n─── PORTE BASSE ───")
print("  MODELE  AUC %.4f  sur n = %d positifs" % (a, int(Ye.sum())))
print("  BARREAU AUC %.4f  (suppression subie, zero parametre)" % BARREAU)
print("  -> %s" % ("PASSE : le modele apporte quelque chose que le meilleur trait seul n a pas"
                   if a > BARREAU + 0.02 else
                   "ECHOUE : il ne bat pas le meilleur trait SEUL — un GRU pour rien"))
torch.save(m.state_dict(), '/mnt/data/monde2.pt')
json.dump({"hachage_portes": H, "auc": a, "barreau": BARREAU, "n_positifs": int(Ye.sum()),
           "n_fenetres_ecart": int(len(Ye))}, open('/mnt/data/monde2.json', 'w'), indent=1)
print("\n  (la PORTE MOYENNE se joue ensuite, sur ce meme modele sauve)")
