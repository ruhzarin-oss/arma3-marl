#!/usr/bin/env python3
"""trieur.py — LE BANC-MATRICE DEVIENT LE TRIEUR D OBSERVATIONS.

⟨Fable, 07/08 : « toute observation candidate de l etage 1 passe par lui AVANT de couter une
 nuit de GPU. Deux minutes par candidat. »⟩

Le banc a son certificat (commit 685e3a9) : deux paires d ordre connu separees (+3,68 et
+3,91), `expo` y echoue, controle nul a -0,01 %, six strates utilisables. Il a donc le droit
de juger ce qu une observation CONTIENT.

CE QU IL NE DIT PAS, et qui est ecrit : ce qu une POLITIQUE en fait. Le levier certifie de
Younes — deux nombres, -28 % d exposition — a ete mesure sur un agent qui AGIT. Ici on classe.

LES CANDIDATS, dans l ordre de Fable :
  1. CONTINU        distance, angles, nombre d ennemis, posture      (le defaut actuel)
  2. DISCRET        les huit faits d etat                            (l idee de Younes)
  3. MIXTE          continu + discret                                (les faits ajoutent-ils ?)
  4. + SUPPRESSION  continu + la suppression SUBIE                   (la question la plus
                    rentable : l ablation du 05/08 dit que 92 % de l ecart venait de la)
  5. + VUE          continu + vu directionnel + combien me voient
  6. TOUT           tout ce qui precede

REGLE DU BANC, non negociable : meme architecture, meme budget, meme moitie d apprentissage,
tous REAPPRIS DEPUIS ZERO. Sinon on mesure qui a le plus revise, pas qui voit le mieux.

TAILLE DE LA PORTE, declaree avant : sur 99 000 instants tenus a l ecart, ce banc distingue
un ecart d AUC d environ 0,005. Un candidat n est declare MEILLEUR qu au-dela de 0,01.
"""
import sys, numpy as np, torch, torch.nn as nn

DEMI_CONE = 35.0
BLOC, MARGE, GRAINE = 500, 150, 11
ECART_LISIBLE = 0.01

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__tri__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y, TICK = g['SOI'], g['ENN'], g['MASQ'], g['Y'], g['TICK']

viv = MASQ > 0.5
d_e = ENN[..., 3] * 400.0
a_lui = ENN[..., 4] * 180.0
a_moi = ENN[..., 5] * 180.0
vu_dir_e = viv & (ENN[..., 2] > 0.5) & (ENN[..., 1] > 0.5) & (a_lui < DEMI_CONE)
cone_e = viv & (a_lui < DEMI_CONE)
d_min = np.where(viv, d_e, 1e9).min(axis=1)
n_vu = vu_dir_e.sum(axis=1)
n_cone = cone_e.sum(axis=1)
supp_moi = SOI[:, 5]
supp_enn = np.where(viv, ENN[..., 6], 0.0).max(axis=1)

CONTINU = np.stack([
    np.clip(d_min, 0, 400) / 400.0,
    np.where(viv, a_lui, 180.0).min(axis=1) / 180.0,
    np.where(viv, a_moi, 180.0).min(axis=1) / 180.0,
    viv.sum(axis=1).astype(np.float32) / 12.0,
    SOI[:, 4],
], -1)
DISCRET = np.stack([
    (n_vu >= 1).astype(np.float32), (n_vu >= 2).astype(np.float32),
    (n_cone >= 1).astype(np.float32), (n_cone >= 2).astype(np.float32),
    (d_min < 50).astype(np.float32),
    ((d_min >= 50) & (d_min < 150)).astype(np.float32),
    (d_min >= 150).astype(np.float32), SOI[:, 4],
], -1)
SUPPR = np.stack([supp_moi, supp_enn], -1)
VUE = np.stack([(n_vu >= 1).astype(np.float32), n_vu.astype(np.float32) / 12.0], -1)

CANDIDATS = [
    ("1 CONTINU (le defaut)", CONTINU),
    ("2 DISCRET (les etats)", DISCRET),
    ("3 MIXTE continu+etats", np.concatenate([CONTINU, DISCRET], -1)),
    ("4 CONTINU + SUPPRESSION", np.concatenate([CONTINU, SUPPR], -1)),
    ("5 CONTINU + VUE dirig.", np.concatenate([CONTINU, VUE], -1)),
    ("6 TOUT", np.concatenate([CONTINU, DISCRET, SUPPR, VUE], -1)),
]

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
        s = m(X[i_te]).squeeze(-1).cpu().numpy()
    return auc(s, Y[te])


print(f"\n  {len(Y)} instants · mortalite {Y.mean():.2%}"
      f" · apprentissage {tr.sum()} · ecart {te.sum()}")
print(f"  taille de la porte declaree : un ecart d AUC est LISIBLE au-dela de {ECART_LISIBLE:.3f}")
print("\n" + "=" * 78)
print(f"  {'CANDIDAT':<26} {'entrees':>8} {'AUC (3 graines)':>18} {'contre le defaut':>18}")
print("  " + "-" * 76)
base = None
res = []
for nom, F in CANDIDATS:
    a = [juger(F, s) for s in (0, 1, 2)]
    m, sd = float(np.mean(a)), float(np.std(a))
    if base is None:
        base = m
    d = m - base
    res.append((nom, F.shape[1], m, sd, d))
    marque = '' if abs(d) < ECART_LISIBLE else ('  MIEUX' if d > 0 else '  MOINS BIEN')
    print(f"  {nom:<26} {F.shape[1]:>8} {m:>12.4f} ±{sd:.4f} {d:>+13.4f}{marque}")
print("  " + "-" * 76)

print("\n" + "=" * 78)
best = max(res, key=lambda r: r[2])
print(f"  MEILLEUR CANDIDAT : {best[0].strip()}   AUC {best[2]:.4f}")
gains = [(n, d) for n, _, _, _, d in res[1:] if d >= ECART_LISIBLE]
if gains:
    print("  Ce qui apporte quelque chose au-dela du defaut continu :")
    for n, d in gains:
        print(f"     {n.strip():<26} {d:+.4f}")
else:
    print("  RIEN n apporte au-dela du continu : aucun candidat ne depasse la taille de porte.")
print("\n  ⟨ce banc dit ce qu une observation CONTIENT. Jamais ce qu une politique EN FAIT —")
print("   le levier certifie de Younes, -28 % d exposition, a ete mesure sur un agent qui")
print("   AGIT. Les etats devront gagner leur place sur le banc A2, chez Arma.⟩")
print("  " + "=" * 76)
