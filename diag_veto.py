#!/usr/bin/env python3
"""diag_veto — POURQUOI LE COPILOTE NE PARLE JAMAIS. Trois hypotheses, trois signatures,
ZERO run sur Arma. ⟨prescription de Fable, 27/08⟩

Le veto n a mordu 0 fois sur 174 decisions. Avant de refaire seize graines — ce qui
mesurerait seize fois l identite — on tranche hors ligne :

  H1. LA MARGE EST TROP SEVERE. Signature : la masse des rapports prix_natif/prix_meilleur
      se tient entre 1,00 et 1,25. Remede : la marge se DIMENSIONNE depuis l histogramme
      (l ecart discriminant median), deposee avant relance, JAMAIS reglee sur le score.
  H2. LE MODELE EST PLAT a cette echelle. Signature : tous les rapports ~1,00. Alors ce n est
      pas la marge qu on regle, c est L INSTRUMENT qu on interroge — controle positif du
      champ de prix : separe-t-il des positions CONNUES DIFFERENTES ?
  H3. ⭐ LE NATIF EST DEJA A L ARGMIN. Signature : le rang du choix natif est 1 sur 5.
      Ce serait un RESULTAT : l IA d Arma price deja ce que le modele price.

On rejoue les etats sur les JOURNAUX, pas sur le serveur.
"""
import sys, math, json
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
D = '/mnt/data/corpus_disque0/tenseurs'
dev = 'cuda:0'; LEN = 12; PAS_M = 20.0

class Modele(nn.Module):
    def __init__(self, nf=10, nh=96):
        super().__init__(); self.g = nn.GRU(nf, nh, batch_first=True)
        self.t = nn.Sequential(nn.Linear(nh, nh), nn.ReLU(), nn.Linear(nh, 1))
    def forward(self, x):
        h, _ = self.g(x); return self.t(h[:, -1]).squeeze(-1)
M = Modele().to(dev); M.load_state_dict(torch.load('/mnt/data/monde2.pt', map_location=dev)); M.eval()

X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy'); T = X.shape[0]
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
ok = AR[:, 5] > 0.5
cle = AR[ok, 0].astype(np.int64) * 100000 + AR[ok, 2].astype(np.int64)
ka_, vue_ = AR[ok, 3], AR[ok, 4]
o = np.argsort(cle, kind="stable"); cle, ka_, vue_ = cle[o], ka_[o], vue_[o]
R = json.load(open('/mnt/data/reparation.json')); bornes = np.linspace(0, T, 21).astype(int)
tr = lambda x, y, z, camp, tir, az, post, supp, vu, ka: [x/5000, y/5000, z/500, camp, tir, az/360, post/3, supp, vu, ka/4.0]

print("=" * 94); print(" POURQUOI LE VETO NE MORD JAMAIS — trois signatures, zero run"); print("=" * 94, flush=True)
HIST, RANGS, ECARTS = [], [], []
for b in R["blocs_ecart"][:2]:
    ta, tb = bornes[b], min(bornes[b] + 4000, bornes[b + 1])
    A = np.asarray(X[ta:tb]); pr = np.asarray(P[ta:tb]) > 0.5
    idb = A[..., ID]; ids = np.unique(idb[pr])
    for u in ids[:: max(1, len(ids) // 120)]:
        m = pr & (idb == u)
        if m.sum() < LEN + 3: continue
        tt, pl = np.nonzero(m); s = np.argsort(tt); tt, pl = tt[s], pl[s]
        gu, gi = np.unique(tt, return_index=True); tt, pl = tt[gi], pl[gi]
        a = A[tt, pl, :]
        cl = np.sort((tt + ta) * 100000 + int(u))
        i2 = np.searchsorted(cle, cl, "left"); j2 = np.searchsorted(cle, cl, "right")
        kk = np.zeros(len(cl), np.float32); vv = np.zeros(len(cl), np.float32)
        for n in range(len(cl)):
            if j2[n] > i2[n]: kk[n] = ka_[i2[n]:j2[n]].max(); vv[n] = vue_[i2[n]:j2[n]].max()
        for k in range(LEN, len(a) - 2, 7):
            if a[k, VIV] < 0.5: continue
            hist = np.array([tr(a[q, XX], a[q, YY], a[q, ZZ], a[q, CAMP], a[q, TIR], a[q, AZ],
                                a[q, POST], a[q, SUPP], vv[q], kk[q]) for q in range(k - 11, k)])
            # LE CHOIX REEL de l entite : son deplacement observe au pas suivant
            vx, vy = a[k + 1, XX] - a[k, XX], a[k + 1, YY] - a[k, YY]
            n0 = math.hypot(vx, vy)
            if n0 < 1.0: continue
            az0 = math.degrees(math.atan2(vx, vy)) % 360
            cands = []
            for d in (0, -60, -30, 30, 60):
                ang = math.radians(az0 + d)
                nx, ny = a[k, XX] + PAS_M * math.sin(ang), a[k, YY] + PAS_M * math.cos(ang)
                cands.append(tr(nx, ny, a[k, ZZ], a[k, CAMP], a[k, TIR], az0 + d, a[k, POST], a[k, SUPP], vv[k], kk[k]))
            B = np.stack([np.vstack([hist, c]) for c in cands]).astype(np.float32)
            with torch.no_grad():
                p = torch.sigmoid(M(torch.tensor(B, device=dev))).cpu().numpy()
            HIST.append(float(p[0] / max(p.min(), 1e-12)))
            RANGS.append(int((p < p[0]).sum()) + 1)
            ECARTS.append(float((p.max() - p.min()) / max(p.mean(), 1e-12)))
h = np.array(HIST); rg = np.array(RANGS); ec = np.array(ECARTS)
print("  decisions rejouees : %d\n" % len(h), flush=True)

print("─── H1 · LA MARGE EST-ELLE TROP SEVERE ? ───")
print("  rapport prix_choisi / prix_meilleur :")
for q in (50, 75, 90, 95, 99):
    print("     p%-3d = %.3f" % (q, np.percentile(h, q)))
for seuil in (1.05, 1.10, 1.25, 1.50, 2.0):
    print("     part au-dessus de %.2f : %5.1f %%" % (seuil, 100 * (h > seuil).mean()))

print("\n─── H2 · LE MODELE EST-IL PLAT A CETTE ECHELLE ? ───")
print("  etendue relative des 5 candidats (max-min)/moyenne : mediane %.4f  p90 %.4f"
      % (np.median(ec), np.percentile(ec, 90)))
print("  -> %s" % ("PLAT : a 20 m pres, tout se ressemble pour lui" if np.median(ec) < 0.05
                   else "il DISCRIMINE entre les candidats"))

print("\n─── H3 · LE CHOIX REEL EST-IL DEJA LE MOINS CHER ? ───")
for r in (1, 2, 3, 4, 5):
    print("     rang %d : %5.1f %%" % (r, 100 * (rg == r).mean()))
print("  rang moyen du choix reel : %.2f  (hasard = 3,00)" % rg.mean())
print("  -> %s" % ("⭐ LE NATIF EST DEJA A L ARGMIN — l IA d Arma price ce que le modele price."
                   if rg.mean() < 2.4 else
                   "le choix reel n est PAS le moins cher : il y avait de la place pour un veto"
                   if rg.mean() > 3.4 else "le choix reel est indifferent au prix du modele"))
json.dump({"n": len(h), "rapport_p50": float(np.median(h)), "rapport_p90": float(np.percentile(h, 90)),
           "etendue_mediane": float(np.median(ec)), "rang_moyen": float(rg.mean())},
          open('/mnt/data/diag_veto.json', 'w'), indent=1)
