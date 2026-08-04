#!/usr/bin/env python3
"""expo_fidele.py — LA FONCTION DE COUT DE LA SANDBOX EST-ELLE FIDELE AU CORPUS ?

Criteres deposes dans CRITERES_ETAPE5.md AVANT ce run.

L'agent apprend sur `expo`, une fonction ANALYTIQUE batie a partir de mesures ponctuelles :
demi-cone 35°, plateau puis chute, base 0,45 decroissante, marche de posture a 120 m.
Le corpus contient la mortalite REELLEMENT observee sur 563 000 observations.

  si expo est FIDELE  -> l'etape 5 ne passe pas par la fonction de cout, et remplacer
                         celle-ci serait un remede sans mal ⟨la faute de cette nuit⟩
  si expo est INFIDELE -> l'etape 5 a son objet : apprendre le risque sur le corpus

E0 VALIDITE   le predicteur appris doit battre le plancher de >= 0,05 d'AUC
E1 LE DEFAUT  ecart < 0,03 d'AUC -> expo est fidele · > 0,03 -> le defaut est etabli
E2 SENS       expo doit etre POSITIVEMENT correlee a la mortalite
E3 NUL        sur etiquettes brassees, tout doit retomber a 0,5
"""
import sys, math, time
sys.argv = [sys.argv[0]]

# on reutilise EXACTEMENT la construction d'exemples de la sonde 1 — meme corpus, memes
# ennemis retenus, meme cible (mort a 30 s), meme partage apprentissage/ecart
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn

print(f"\n  {len(SOI)} observations · mortalite {Y.mean():.2%} · "
      f"tenu a l'ecart {est_test.sum()}", flush=True)

# ---------------------------------------------------------------- expo, telle qu'elle est
# ENN[:,:,3] = distance/400 · ENN[:,:,4] = a_lui/180 (l'angle sous lequel JE suis dans SON
# champ) — c'est exactement ce dont expo a besoin. Aucune reconstruction, aucune supposition.
CHAMP_, SEUIL_, PENTE_ = 35.0, 120.0, 12.0
def expo_analytique(ENN, MASQ):
    d  = np.clip(ENN[:, :, 3] * 400.0, 1.0, None)
    ec = ENN[:, :, 4] * 180.0
    dans = 1.0 / (1.0 + np.exp(-(CHAMP_ - ec) * 1.2))
    base = 0.45 * (1.0 - np.clip(d/400, 0, 1))
    e = (base + (1.0-base) * dans) * (1.0 - np.clip(d/450, 0, 1))
    e = np.where(MASQ > 0.5, e, 0.0)
    return e.max(axis=1)

E = expo_analytique(ENN, MASQ)

def auc(score, y):
    """aire sous la courbe ROC, par les rangs. 0,5 = hasard."""
    score = np.asarray(score, float); y = np.asarray(y, float)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return float('nan')
    r = np.empty(len(score)); r[np.argsort(score)] = np.arange(len(score))
    return float((r[y > 0.5].sum() - n1*(n1-1)/2) / (n1*n0))

te = est_test
a_expo = auc(E[te], Y[te])

# ---------------------------------------------------------------- le predicteur appris
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
class Lecteur(nn.Module):
    """meme forme que la sonde 1 : chaque ennemi encode, puis PONDERE par attention."""
    def __init__(s, ce, cs, h=96):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(ce, h), nn.ReLU(), nn.Linear(h, h))
        s.q = nn.Linear(cs, h)
        s.out = nn.Sequential(nn.Linear(cs+h, h), nn.ReLU(), nn.Linear(h, 1))
    def forward(s, soi, enn, msk):
        z = s.enc(enn)
        a = (z * s.q(soi).unsqueeze(1)).sum(-1) / math.sqrt(z.shape[-1])
        a = torch.softmax(a.masked_fill(msk < 0.5, -1e9), -1).unsqueeze(-1)
        return s.out(torch.cat([soi, (z*a).sum(1)], -1)).squeeze(-1)

def entraine(Yc, graine=0, iters=600):
    torch.manual_seed(graine)
    m = Lecteur(ENN.shape[-1], SOI.shape[-1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), 2e-3)
    tr = np.where(~te)[0]
    S = torch.tensor(SOI, device=dev); N_ = torch.tensor(ENN, device=dev)
    M = torch.tensor(MASQ, device=dev); Yt = torch.tensor(Yc, device=dev)
    pos = float(Yc[tr].mean())
    w = torch.tensor((1-pos)/max(pos, 1e-6), device=dev)
    for it in range(iters):
        b = torch.tensor(np.random.choice(tr, 4096), device=dev)
        p = m(S[b], N_[b], M[b])
        perte = nn.functional.binary_cross_entropy_with_logits(p, Yt[b], pos_weight=w)
        opt.zero_grad(); perte.backward(); opt.step()
    with torch.no_grad():
        idx_te = np.where(te)[0]
        out = []
        for i in range(0, len(idx_te), 65536):
            b = torch.tensor(idx_te[i:i+65536], device=dev)
            out.append(m(S[b], N_[b], M[b]).cpu().numpy())
    return np.concatenate(out)

t0 = time.time()
pred = entraine(Y)
a_appris = auc(pred, Y[te])

# ---------------------------------------------------------------- LA COMPARAISON EQUITABLE
# Le predicteur ci-dessus voit knowsAbout, « il me voit », les mesures du moteur et la
# suppression. expo ne voit QUE la geometrie. Le comparer tel quel serait injuste et
# conclurait trop fort. On refait donc l'apprentissage sur la GEOMETRIE SEULE :
#   ENN[:,:,3] = distance   ENN[:,:,4] = l'angle sous lequel je suis dans son champ
#   ENN[:,:,5] = l'angle sous lequel il est dans le mien
# C'est exactement l'information dont dispose expo, plus l'angle reciproque.
GEO = ENN.copy()
GEO[:, :, 0] = 0.0   # knowsAbout
GEO[:, :, 1] = 0.0   # il me voit
GEO[:, :, 2] = 0.0   # mesure du moteur
GEO[:, :, 6] = 0.0   # suppression
_ENN_PLEIN = ENN
ENN = GEO
pred_geo = entraine(Y, graine=2)
a_geo = auc(pred_geo, Y[te])
ENN = _ENN_PLEIN
print(f"  predicteur GEOMETRIE SEULE : AUC {a_geo:.4f}", flush=True)
print(f"  predicteur appris entraine en {time.time()-t0:.0f} s", flush=True)

# ---------------------------------------------------------------- E3 controle nul
Ybr = np.random.permutation(Y)
a_nul_expo = auc(E[te], Ybr[te])
pred_nul = entraine(Ybr, graine=1, iters=200)
a_nul_appris = auc(pred_nul, Ybr[te])

# ---------------------------------------------------------------- verdict
print("\n" + "="*72)
print(f"  AUC sur les donnees tenues a l'ecart   (plancher = 0,500)")
print(f"    expo, la fonction de la sandbox ....... {a_expo:.4f}")
print(f"    predicteur appris sur le corpus ....... {a_appris:.4f}")
print(f"    ecart .................................. {a_appris-a_expo:+.4f}")
print("="*72)

e0 = (a_appris - 0.5) >= 0.05
print(f"\n  E0 VALIDITE  le predicteur bat le plancher de {a_appris-0.5:+.3f} (exige +0,05)"
      f"   -> {'OK' if e0 else 'ECHEC : la geometrie ne predit rien, le test est sans objet'}")

e2 = a_expo > 0.5
print(f"  E2 SENS      expo est {'POSITIVEMENT' if e2 else 'NEGATIVEMENT'} correlee "
      f"(AUC {a_expo:.4f})   -> {'OK' if e2 else 'ECHEC : erreur de signe ou de domaine'}")

e3 = abs(a_nul_expo-0.5) < 0.02 and abs(a_nul_appris-0.5) < 0.02
print(f"  E3 NUL       etiquettes brassees : expo {a_nul_expo:.4f} · appris {a_nul_appris:.4f}"
      f"   -> {'OK' if e3 else 'ECHEC : la chaine fuit'}")

ecart = a_appris - a_expo
print(f"\n  E1 LE DEFAUT EXISTE-T-IL ?")
print(f"     contre le predicteur COMPLET   : ecart {ecart:+.4f}")
print(f"     contre la GEOMETRIE SEULE      : ecart {a_geo-a_expo:+.4f}   <- LA COMPARAISON EQUITABLE")
print(f"     (seuil 0,03)")
ecart = a_geo - a_expo
print("\n" + "="*72)
if not (e0 and e2 and e3):
    print("  UN CONTROLE A CEDE — on ne conclut pas.")
elif ecart > 0.03:
    print("  EXPO EST INFIDELE. A INFORMATION EGALE — la geometrie seule — un predicteur")
    print("  appris sur le corpus ordonne le danger nettement mieux que la fonction")
    print("  analytique de la sandbox. Ce n'est donc pas un avantage d'information.")
    print("  -> L'ETAPE 5 A SON OBJET : apprendre le risque sur le corpus et le substituer")
    print("     a expo comme fonction de cout de l'entrainement.")
else:
    print("  EXPO EST FIDELE. La fonction analytique ordonne le danger aussi bien qu'un")
    print("  predicteur appris sur 563 000 observations reelles.")
    print("  -> L'ETAPE 5 NE PASSE PAS PAR LA FONCTION DE COUT. Remplacer expo serait")
    print("     un remede sans mal — exactement la faute commise cette nuit avec le champ.")
    print("     Elle doit porter sur le REJEU des trajectoires, et ce sera un autre test.")
print("="*72)
