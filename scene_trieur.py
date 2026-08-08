#!/usr/bin/env python3
"""scene_trieur.py — L ETIQUETTE DE SCENE, derivee de la carte, passee au trieur.

⟨Fable, 07/08⟩ « l etiquette de scene se derive sans y mettre la main : le corpus porte les
POSITIONS, la carte porte les BATIMENTS et les ROUTES. » Releve fait ce soir sur STRATIS —
le monde du corpus, verifie sur pieces (« Mission world: Stratis » dans le journal source ;
les cartes deja au dossier etaient toutes d Altis, d ou zero recouvrement).

LA DERIVATION EST MECANIQUE, aucun jugement :
    interieur  >= 3 batiments dans les 30 m
    rue        sur une route, ou 1-2 batiments proches
    lisiere    >= 5 arbres, pas de bati
    ouvert     ni bati, ni arbres, ni route

LA PORTE, deja deposee et non retouchee : un candidat n est MEILLEUR qu au-dela de +0,05
d AUC — l etalon du levier de la suppression, le plus gros gain qu un banc certifie ait
mesure sur ce corpus. Meme architecture, meme budget, memes blocs, 3 graines, reappris depuis
zero.

CE QUI FERAIT ECHOUER, ecrit avant : si l etiquette de scene n apporte pas un etalon
au-dessus des sept nombres, l idee du classificateur meurt ici — deux minutes, zero nuit.
"""
import sys, numpy as np, torch, torch.nn as nn

ETALON = 0.05
BLOC, MARGE, GRAINE = 500, 150, 11

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__sc__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y, TICK = g['SOI'], g['ENN'], g['MASQ'], g['Y'], g['TICK']

# --- la carte relevee ce soir
z = np.load('/home/younes/arma3-marl/leviathan/bati_stratis.npz')
MAI, ARB, ROU = z['MAISONS'], z['ARBRES'], z['ROUTE']
pas, taille = int(z['pas']), int(z['taille'])
n = MAI.shape[0]

# --- position de chaque instant : SOI porte x/1000, y/1000
px = SOI[:, 0] * 1000.0
py = SOI[:, 1] * 1000.0
dedans = (px >= 0) & (px < taille) & (py >= 0) & (py < taille)
ix = np.clip((px / pas).astype(int), 0, n - 1)
iy = np.clip((py / pas).astype(int), 0, n - 1)
mai, arb, rou = MAI[iy, ix], ARB[iy, ix], ROU[iy, ix]

interieur = (mai >= 3)
rue = ~interieur & ((rou > 0) | (mai >= 1))
lisiere = ~interieur & ~rue & (arb >= 5)
ouvert = ~interieur & ~rue & ~lisiere
SCENE = np.stack([interieur, rue, lisiere, ouvert], -1).astype(np.float32)

print(f"\n  {len(Y)} instants · dans les bornes de la carte : {dedans.mean():.1%}")
print("  " + "-" * 66)
for nom, m in (("interieur", interieur), ("rue", rue), ("lisiere", lisiere), ("ouvert", ouvert)):
    print(f"     {nom:10s} {m.mean():6.1%} des instants · mortalite {Y[m].mean() if m.any() else 0:.2%}")
print(f"     ⟨mortalite globale {Y.mean():.2%}⟩")

viv = MASQ > 0.5
d_min = np.where(viv, ENN[..., 3] * 400.0, 1e9).min(axis=1)
CONTINU = np.stack([
    np.clip(d_min, 0, 400) / 400.0,
    np.where(viv, ENN[..., 4] * 180.0, 180.0).min(axis=1) / 180.0,
    np.where(viv, ENN[..., 5] * 180.0, 180.0).min(axis=1) / 180.0,
    viv.sum(axis=1).astype(np.float32) / 12.0,
    SOI[:, 4],
], -1)
SUPPR = np.stack([SOI[:, 5], np.where(viv, ENN[..., 6], 0.0).max(axis=1)], -1)
SEPT = np.concatenate([CONTINU, SUPPR], -1)          # le cahier des charges

T = int(TICK.max()) + 1
nb = max(T // BLOC, 3)
bl = np.minimum(TICK // BLOC, nb - 1)
rg = np.random.default_rng(GRAINE)
ec = set(rg.permutation(nb)[:max(1, nb // 5)].tolist())
dans_ec = np.array([b in ec for b in bl])
coutu = (TICK % BLOC) >= BLOC - MARGE
te, tr = dans_ec & ~coutu, (~dans_ec) & ~coutu
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
i_tr = torch.tensor(np.where(tr)[0], device=dev)
i_te = torch.tensor(np.where(te)[0], device=dev)
y_t = torch.tensor(Y, device=dev)


def auc(s_, y_):
    o = np.argsort(s_); r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1
    return (r[y_ > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def juger(F, graine):
    torch.manual_seed(graine)
    X = torch.tensor(F, device=dev)
    m = nn.Sequential(nn.Linear(F.shape[1], 24), nn.ReLU(), nn.Linear(24, 1)).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=3e-3)
    for _ in range(400):
        i = i_tr[torch.randint(0, len(i_tr), (8192,), device=dev)]
        p = m(X[i]).squeeze(-1)
        l = nn.functional.binary_cross_entropy_with_logits(p, y_t[i])
        opt.zero_grad(); l.backward(); opt.step()
    with torch.no_grad():
        return auc(m(X[i_te]).squeeze(-1).cpu().numpy(), Y[te])


print("\n" + "=" * 76)
print(f"  LE TRIEUR — porte a l etalon {ETALON:+.2f} (le levier de la suppression)")
print("  " + "-" * 74)
res = []
for nom, F in (("SEPT NOMBRES (le defaut)", SEPT),
               ("SEPT + SCENE", np.concatenate([SEPT, SCENE], -1)),
               ("SCENE SEULE", SCENE)):
    a = [juger(F, s) for s in (0, 1, 2)]
    m, sd = float(np.mean(a)), float(np.std(a))
    res.append((nom, F.shape[1], m, sd))
    print(f"     {nom:26s} {F.shape[1]:>3} entrees · AUC {m:.4f} ±{sd:.4f}")
base = res[0][2]
gain = res[1][2] - base
print("  " + "-" * 74)
print(f"     apport de la scene : {gain:+.4f}   (exige >= {ETALON:+.2f})")

print("\n" + "=" * 76)
if gain >= ETALON:
    print("  LA SCENE INFORME. Connaitre le type d environnement ordonne le danger mieux que")
    print("  les sept nombres seuls, d au moins un etalon.")
    print("  -> on achete le classificateur entraine sur photos reelles.")
else:
    print("  LA SCENE N INFORME PAS au-dela de la porte. Les sept nombres portaient deja ce")
    print("  qu elle apporte — la distance au plus proche et le nombre d ennemis disent deja")
    print("  beaucoup du lieu. L idee meurt ici : deux minutes, zero nuit.")
print("  ⟨ce banc dit ce qu une observation CONTIENT, jamais ce qu une politique EN FAIT⟩")
print("  " + "=" * 74)
