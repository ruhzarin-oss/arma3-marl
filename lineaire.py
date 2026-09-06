#!/usr/bin/env python3
"""lineaire — LE PRIX EST-IL VRAIMENT UN GRADIENT ? On le prouve avant de rebatir quoi que ce soit.

Signature trouvee : le choix reel est rang 3 sur 5 dans 100,0 % des cas, avec des candidats
symetriques (0, ±30, ±60). Lecture : le prix varie MONOTONEMENT avec l angle, donc c est un
GRADIENT lisse, pas une carte de zones. Mais « rang 3 toujours » a une autre explication
possible que je dois ecarter : que le modele ignore purement la POSITION et ne lise que
l historique — auquel cas les cinq candidats auraient des prix quasi IDENTIQUES, et le rang
serait un artefact d ordre de tri.

TROIS EPREUVES, sur les journaux :
  E1. Le prix est-il monotone en angle ? (correlation prix contre angle, par decision)
  E2. Les cinq prix sont-ils distincts, ou l ecart est-il du bruit numerique ?
  E3. ⭐ LE CONTROLE POSITIF DU CHAMP DE PRIX ⟨regle 16⟩ : le modele separe-t-il deux
      positions dont on SAIT qu elles different — l une PRES d un ennemi vu, l autre LOIN ?
      S il ne separe pas des positions connues differentes, il n a pas de champ spatial.
"""
import sys, math, json
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
D = '/mnt/data/corpus_disque0/tenseurs'; dev = 'cuda:0'; LEN = 12
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
tr = lambda x, y, z, c, t_, az, po, su, vu, ka: [x/5000, y/5000, z/500, c, t_, az/360, po/3, su, vu, ka/4.0]
def prix(B):
    with torch.no_grad():
        return torch.sigmoid(M(torch.tensor(np.array(B, np.float32), device=dev))).cpu().numpy()

print("=" * 94); print(" LE PRIX EST-IL UN GRADIENT ? trois epreuves"); print("=" * 94, flush=True)
COR, ETEN, SEP = [], [], []
ANG = list(range(0, 360, 30))
for b in R["blocs_ecart"][:2]:
    ta, tb = bornes[b], min(bornes[b] + 3000, bornes[b + 1])
    A = np.asarray(X[ta:tb]); pr = np.asarray(P[ta:tb]) > 0.5
    idb = A[..., ID]; ids = np.unique(idb[pr])
    px, py, cp = A[..., XX], A[..., YY], A[..., CAMP]
    for u in ids[:: max(1, len(ids) // 90)]:
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
        for k in range(LEN, len(a) - 2, 11):
            if a[k, VIV] < 0.5: continue
            h = np.array([tr(a[q, XX], a[q, YY], a[q, ZZ], a[q, CAMP], a[q, TIR], a[q, AZ],
                             a[q, POST], a[q, SUPP], vv[q], kk[q]) for q in range(k - 11, k)])
            # E1/E2 : douze directions autour du cercle, 20 m
            B = []
            for d in ANG:
                r_ = math.radians(d)
                B.append(np.vstack([h, tr(a[k, XX] + 20*math.sin(r_), a[k, YY] + 20*math.cos(r_),
                                          a[k, ZZ], a[k, CAMP], a[k, TIR], d, a[k, POST], a[k, SUPP], vv[k], kk[k])]))
            p = prix(B)
            ETEN.append(float((p.max() - p.min()) / max(p.mean(), 1e-12)))
            # un gradient pur donne un COSINUS parfait en fonction de l angle
            c = np.cos(np.radians(ANG)); s2 = np.sin(np.radians(ANG))
            best = max(abs(np.corrcoef(p, c)[0, 1]), abs(np.corrcoef(p, s2)[0, 1]))
            COR.append(float(best))
            # E3 : CONTROLE POSITIF — 20 m VERS l ennemi le plus proche contre 20 m a l OPPOSE
            t_ = tt[k]
            adv = pr[t_] & (cp[t_] != a[k, CAMP])
            ia = np.nonzero(adv)[0]
            if len(ia) == 0: continue
            dd = (px[t_, ia] - a[k, XX])**2 + (py[t_, ia] - a[k, YY])**2
            jm = ia[int(np.argmin(dd))]
            vx, vy = px[t_, jm] - a[k, XX], py[t_, jm] - a[k, YY]
            nn_ = math.hypot(vx, vy)
            if nn_ < 30: continue
            vx, vy = vx / nn_, vy / nn_
            B2 = []
            for sgn in (+1, -1):
                B2.append(np.vstack([h, tr(a[k, XX] + 20*sgn*vx, a[k, YY] + 20*sgn*vy, a[k, ZZ],
                                           a[k, CAMP], a[k, TIR], a[k, AZ], a[k, POST], a[k, SUPP], vv[k], kk[k])]))
            q = prix(B2)
            SEP.append(float(q[0] - q[1]))          # vers l ennemi MOINS loin de l ennemi
co = np.array(COR); et = np.array(ETEN); se = np.array(SEP)
print("  decisions rejouees : %d   (controle positif sur %d)\n" % (len(co), len(se)))
print("─── E1 · LE PRIX EST-IL UN COSINUS DE L ANGLE ? (signature d un gradient pur) ───")
print("  correlation |prix, cos(angle)| : mediane %.3f   p10 %.3f   part > 0,95 : %.1f %%"
      % (np.median(co), np.percentile(co, 10), 100 * (co > 0.95).mean()))
print("  -> %s" % ("GRADIENT PUR : le prix est une fonction lineaire de la position"
                   if np.median(co) > 0.95 else "pas un simple gradient"))
print("\n─── E2 · L ECART ENTRE CANDIDATS EST-IL REEL ? ───")
print("  etendue relative sur 12 directions : mediane %.4f   p10 %.4f" % (np.median(et), np.percentile(et, 10)))
print("\n─── E3 · CONTROLE POSITIF : vers l ennemi CONTRE a l oppose ───")
if len(se):
    print("  prix(vers) - prix(oppose) : mediane %+.5f   part POSITIVE %.1f %%" % (np.median(se), 100 * (se > 0).mean()))
    print("  -> %s" % ("✅ IL SEPARE, et dans le BON SENS : s approcher coute plus cher"
                       if np.median(se) > 0 and (se > 0).mean() > 0.65 else
                       "⛔ IL NE SEPARE PAS deux positions connues differentes — pas de champ spatial utilisable"
                       if abs(np.median(se)) < 1e-4 else
                       "⚠️ il separe mais A L ENVERS : s approcher lui parait moins dangereux"))
json.dump({"cor_med": float(np.median(co)), "eten_med": float(np.median(et)),
           "sep_med": float(np.median(se)) if len(se) else None,
           "sep_pos": float((se > 0).mean()) if len(se) else None}, open('/mnt/data/lineaire.json', 'w'), indent=1)
