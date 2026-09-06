#!/usr/bin/env python3
"""porte_moyenne — LE MODELE RETROUVE-T-IL LES TARIFS SANS QU ON LES LUI MONTRE ?

⟨Fable⟩ « Un modele qui predit la transition mais ORDONNE MAL ces facteurs n a rien compris
d actionnable. » Portes scellees : DEPOT_BARREAU.md, 013b37748504b4f7.

LES TROIS CIBLES, mesurees independamment sur les MEMES blocs tenus a l ecart :
    supprime  x29,81   >>   knowsAbout>1  x2,77   >   vu  x2,45

⚠️ CORRECTION D INSTRUMENT (26/08, apres un premier passage FAUSSE). Le modele est entraine
avec un poids de classe de 3 143, donc ses probabilites sont poussees vers 1 : le « risque
AVEC » de la suppression valait 0,916. UN RAPPORT DE PROBABILITES SATURE NE PEUT PAS VALOIR
29 — je comparais une grandeur re-echelonnee a un rapport de taux brut. On compare desormais
des RAPPORTS DE COTES, qui sont invariants au re-echelonnage de la classe rare (propriete
standard de la regression logistique sous echantillonnage cas-temoin).

COMMENT ON MESURE CE QUE LE MODELE CROIT : par CONTREFACTUEL. Sur chaque fenetre ou le
facteur est ALLUME, on le met a zero sur toute la fenetre et on regarde de combien le risque
predit tombe. Le rapport risque-avec / risque-sans EST le tarif que le modele s est donne.
On ne lui a jamais dit lequel comptait : les dix traits entrent bruts.
"""
import numpy as np, torch, torch.nn as nn, json, hashlib, time
D = '/mnt/data/corpus_disque0/tenseurs'
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy'); T = X.shape[0]
ID, XX, YY, ZZ, VIV, CAMP, TIR, AZ, POST, SUPP, NEUF = range(11)
dev = 'cuda:0'; LEN = 12
# indices des traits DANS L ENTREE du modele (ordre de monde2.batir)
I_SUPP, I_VUE, I_KA = 7, 8, 9
CIBLES = {"supprime": 29.81, "knowsAbout": 2.77, "vu": 2.45}
H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_BARREAU.md', 'rb').read()).hexdigest()[:16]
R = json.load(open('/mnt/data/reparation.json'))
print("=" * 98); print(" PORTE MOYENNE — le modele retrouve-t-il les tarifs ? (portes %s)" % H); print("=" * 98, flush=True)

ok = AR[:, 5] > 0.5
cle = AR[ok, 0].astype(np.int64) * 100000 + AR[ok, 2].astype(np.int64)
ka_, vue_ = AR[ok, 3], AR[ok, 4]
o = np.argsort(cle, kind="stable"); cle, ka_, vue_ = cle[o], ka_[o], vue_[o]
bornes = np.linspace(0, T, 21).astype(int)

def batir(blocs, nb=3, pas_id=250):
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
            tr = np.stack([a[:, XX] / 5000, a[:, YY] / 5000, a[:, ZZ] / 500, a[:, CAMP],
                           a[:, TIR], a[:, AZ] / 360, a[:, POST] / 3, a[:, SUPP],
                           vv, kk / 4.0], 1).astype(np.float32)
            v = a[:, VIV]
            for k in range(LEN, len(a) - 1):
                if v[k] < 0.5: continue
                F.append(tr[k - LEN:k]); Y.append(1.0 if v[k + 1] < 0.5 else 0.0)
    return np.array(F, np.float32), np.array(Y, np.float32)

class Modele(nn.Module):
    def __init__(self, nf=10, nh=96):
        super().__init__(); self.g = nn.GRU(nf, nh, batch_first=True)
        self.t = nn.Sequential(nn.Linear(nh, nh), nn.ReLU(), nn.Linear(nh, 1))
    def forward(self, x):
        h, _ = self.g(x); return self.t(h[:, -1]).squeeze(-1)

t0 = time.time(); F, Y = batir(R["blocs_ecart"], nb=3)
print("  %d fenetres tenues a l ecart, %d positifs  (%.0f s)" % (len(Y), Y.sum(), time.time() - t0), flush=True)
m = Modele().to(dev); m.load_state_dict(torch.load('/mnt/data/monde2.pt', map_location=dev)); m.eval()
Xt = torch.tensor(F, device=dev)
def risque(t):
    with torch.no_grad():
        return torch.sigmoid(torch.cat([m(t[i:i + 8192]) for i in range(0, len(t), 8192)])).cpu().numpy()
p0 = risque(Xt)

print("\n─── LE TARIF QUE LE MODELE S EST DONNE (contrefactuel : on ETEINT le facteur) ───")
print("  %-14s %10s %12s %12s %12s" % ("facteur", "n allume", "COTE avec", "COTE sans", "RAPPORT"))
obt = {}
for nom, ci, seuil in (("supprime", I_SUPP, 1e-6), ("knowsAbout", I_KA, 1.0 / 4.0), ("vu", I_VUE, 0.5)):
    on = (F[:, -1, ci] > seuil)
    if on.sum() < 50: print("  %-14s trop peu de cas (%d)" % (nom, on.sum())); continue
    Z = Xt[torch.tensor(np.nonzero(on)[0], device=dev)].clone()
    pa = risque(Z); Z[:, :, ci] = 0.0; ps = risque(Z)
    cote = lambda q: float(np.mean(q / np.clip(1 - q, 1e-9, None)))
    avec, sans = cote(pa), cote(ps)
    r = avec / max(sans, 1e-12); obt[nom] = r
    print("  %-14s %10d %12.4f %12.4f %12.2f x   (proba %.3f -> %.3f)"
          % (nom, on.sum(), avec, sans, r, float(pa.mean()), float(ps.mean())))

print("\n─── LA PORTE : L ORDRE EST-IL RETROUVE ? ───")
print("  %-14s %14s %14s" % ("facteur", "VRAI (mesure)", "MODELE"))
for n in ("supprime", "knowsAbout", "vu"):
    print("  %-14s %13.2f x %13s" % (n, CIBLES[n], ("%.2f x" % obt[n]) if n in obt else "—"))
if len(obt) == 3:
    vrai = sorted(CIBLES, key=CIBLES.get, reverse=True)
    mod = sorted(obt, key=obt.get, reverse=True)
    print("\n  ordre VRAI   : %s" % "  >  ".join(vrai))
    print("  ordre MODELE : %s" % "  >  ".join(mod))
    domine = obt["supprime"] > 3 * max(obt["knowsAbout"], obt["vu"])
    signes = all(obt[n] > 1.0 for n in CIBLES)
    print("  tous les facteurs vont-ils dans le BON SENS (rapport > 1) ? %s"
          % ("oui" if signes else "NON — un facteur est INVERSE, le modele le croit protecteur"))
    print("\n  -> %s" % ("PASSE : l ordre est retrouve, tous les signes sont bons, et la suppression DOMINE."
                         if vrai == mod and domine and signes else
                         "ECHOUE : un facteur est INVERSE — le modele croit protecteur ce qui tue."
                         if not signes else
                         "ORDRE retrouve mais la suppression ne DOMINE pas — tarif appris trop plat."
                         if vrai == mod else
                         "ECHOUE : le modele ordonne MAL les facteurs. Il predit sans comprendre."))
json.dump({"hachage": H, "cibles": CIBLES, "obtenu": obt}, open('/mnt/data/porte_moyenne.json', 'w'), indent=1)
