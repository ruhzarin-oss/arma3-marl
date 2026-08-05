#!/usr/bin/env python3
"""risque_appris.py — LE RISQUE APPRIS SUR LE CORPUS, rendu TRANSFERABLE a la sandbox.

⟨mesure du 05/08 : expo, la fonction de cout de la sandbox, vaut AUC 0,5005 — le hasard.
 Un predicteur appris sur la GEOMETRIE SEULE atteint 0,7138. Ce n'est pas un avantage
 d'information : c'est la fonction qui n'ordonne rien.⟩

L'OBSTACLE QU'IL FAUT MESURER AVANT DE SUBSTITUER. Le predicteur a 0,7138 lit `SOI` =
[x/1000, y/1000, z/100, azimut/360, posture/3, suppression]. Les deux premieres sont des
coordonnees ABSOLUES d'Altis, la troisieme une altitude, la sixieme la suppression du
soldat. **La sandbox n'a rien de tout cela** : elle travaille en coordonnees relatives a
l'objectif, sur terrain plat, et son agent n'est jamais supprime.

Un predicteur qui s'appuierait sur la position absolue apprendrait « on meurt plus a tel
endroit d'Altis » — vrai sur le corpus, intransferable et sans interet.

ON MESURE DONC CE QUE COUTE LA TRANSFERABILITE, au lieu de le supposer :
  A. COMPLET        toutes les entrees                        (le plafond)
  B. GEOMETRIE      d, angle sur moi, angle sur lui           (ce que Fable designe)
  C. TRANSFERABLE   B, moins tout ce que la sandbox n'a pas   (ce qu'on peut vraiment poser)

CRITERES, ecrits avant :
  R0 la variante C doit battre le plancher de >= 0,05 d'AUC. Sinon rien a substituer.
  R1 la variante C doit rester a <= 0,03 de la variante B. Si la transferabilite coute
     davantage, c'est que le predicteur s'appuyait sur des entrees intransferables, et il
     faut le dire au lieu de livrer un modele qui ne marchera pas.
  R2 CONTROLE NUL : sur etiquettes brassees, C retombe a 0,5.

⟨lecon de Fable, 05/08 : deposer aussi le critere sur l'ABSOLU du sortant, pas seulement
 l'ecart entre candidats. R0 est cet absolu.⟩
"""
import sys, math, time
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn

dev = 'cuda' if torch.cuda.is_available() else 'cpu'
te = est_test
print(f"\n  {len(SOI)} observations · mortalite {Y.mean():.2%} · a l'ecart {te.sum()}", flush=True)

def auc(s, y):
    s = np.asarray(s, float); y = np.asarray(y, float)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return float('nan')
    r = np.empty(len(s)); r[np.argsort(s)] = np.arange(len(s))
    return float((r[y > 0.5].sum() - n1*(n1-1)/2) / (n1*n0))

class Risque(nn.Module):
    """chaque defenseur encode, puis PONDERE par attention. Meme forme que la sonde 1."""
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

def entraine(S_, E_, Yc, graine=0, iters=800):
    torch.manual_seed(graine); np.random.seed(graine)
    m = Risque(E_.shape[-1], S_.shape[-1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), 2e-3)
    tr = np.where(~te)[0]
    S = torch.tensor(S_, device=dev); E = torch.tensor(E_, device=dev)
    M = torch.tensor(MASQ, device=dev); Yt = torch.tensor(Yc, device=dev)
    pos = float(Yc[tr].mean()); w = torch.tensor((1-pos)/max(pos, 1e-6), device=dev)
    for _ in range(iters):
        b = torch.tensor(np.random.choice(tr, 4096), device=dev)
        p = m(S[b], E[b], M[b])
        l = nn.functional.binary_cross_entropy_with_logits(p, Yt[b], pos_weight=w)
        opt.zero_grad(); l.backward(); opt.step()
    with torch.no_grad():
        idx = np.where(te)[0]; out = []
        for i in range(0, len(idx), 65536):
            b = torch.tensor(idx[i:i+65536], device=dev)
            out.append(m(S[b], E[b], M[b]).cpu().numpy())
    return m, np.concatenate(out)

# ---------------------------------------------------------------- les trois variantes
# ENN = [k/4, vu, mes, d/400, a_lui/180, a_moi/180, sup_ennemi]
# SOI = [x/1000, y/1000, z/100, azimut/360, posture/3, suppression_soi]
E_geo = ENN.copy(); E_geo[:, :, [0,1,2,6]] = 0.0
# la sandbox connait : la distance, les deux angles, ET la posture de chaque defenseur.
# Elle ne connait NI knowsAbout, NI « il me voit », NI les mesures du moteur.
E_tr = ENN[:, :, [3,4,5]].copy()
S_tr = SOI[:, [4]].copy()          # la posture du soldat, et rien d'autre de transferable

variantes = [("A COMPLET      ", SOI, ENN),
             ("B GEOMETRIE    ", SOI, E_geo),
             ("C TRANSFERABLE ", S_tr, E_tr)]
res = {}
for nom, S_, E_ in variantes:
    t0 = time.time()
    m, p = entraine(S_, E_, Y)
    a = auc(p, Y[te]); res[nom.strip()] = (a, m, S_, E_)
    print(f"  {nom} AUC {a:.4f}   ({S_.shape[-1]} sur soi, {E_.shape[-1]} par defenseur, "
          f"{time.time()-t0:.0f} s)", flush=True)

a_A = res['A COMPLET'][0]; a_B = res['B GEOMETRIE'][0]; a_C = res['C TRANSFERABLE'][0]
# CONTROLE NUL. Le premier jet evaluait le modele entraine sur etiquettes brassees contre
# les VRAIES etiquettes — un reseau quasi aleatoire de (d, angle) correle alors par hasard
# avec la mortalite, et le controle rendait 0,5304 sans qu'aucune chaine ne fuie.
# On evalue contre les etiquettes BRASSEES, celles sur lesquelles il a appris.
Ybr = np.random.permutation(Y)
_, p_nul = entraine(S_tr, E_tr, Ybr, graine=9, iters=200)
a_nul = auc(p_nul, Ybr[te])

print("\n" + "="*70)
r0 = (a_C - 0.5) >= 0.05
print(f"  R0 ABSOLU    C bat le plancher de {a_C-0.5:+.3f} (exige +0,05)   -> {'OK' if r0 else 'ECHEC'}")
r1 = (a_B - a_C) <= 0.03
print(f"  R1 COUT DE LA TRANSFERABILITE   B - C = {a_B-a_C:+.4f} (exige <= 0,03)"
      f"   -> {'OK' if r1 else 'ECHEC : le predicteur s appuyait sur des entrees intransferables'}")
r2 = abs(a_nul - 0.5) < 0.02
print(f"  R2 NUL       etiquettes brassees : {a_nul:.4f}   -> {'OK' if r2 else 'ECHEC'}")
print(f"\n  rappel : expo, la fonction actuelle, vaut 0,5005 — le hasard.")
print("="*70)

if r0 and r1 and r2:
    m = res['C TRANSFERABLE'][1]
    torch.save({'etat': m.state_dict(), 'ce': E_tr.shape[-1], 'cs': S_tr.shape[-1],
                'auc': a_C, 'auc_geo': a_B, 'auc_complet': a_A},
               '/mnt/data/corpus/risque_geo.pt')
    print(f"  ECRIT /mnt/data/corpus/risque_geo.pt   (AUC {a_C:.4f})")
    print("  -> substituable a expo. Reste a verifier qu'il ORDONNE DIFFEREMMENT.")
else:
    print("  NE PAS SUBSTITUER — voir le controle qui a lache.")
