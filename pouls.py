#!/usr/bin/env python3
"""pouls.py — LA SANDBOX TUE-T-ELLE AU BON TARIF ?

Tolerance deposee AVANT ce calcul : CRITERES_POULS.md.
  comparable    >= 2 000 observations Arma ET >= 2 000 pas de sandbox
  meme pouls    rapport entre 0,5 et 2,0 sur chaque tranche comparable
  la loi passe  >= 2/3 des tranches comparables dans la tolerance, aucune hors facteur 4

Grandeur comparee, cote Arma : « ce soldat meurt-il dans les 30 s ? », par tranche de
distance au plus proche ennemi. Cote sandbox : « l agent atteint-il le seuil de mort dans les
9 pas ? » — 30 s / 3,28 s par pas, la conversion mesuree.

LIMITE ECRITE D AVANCE, non corrigee : le corpus Arma mele attaquants et defenseurs, en
garnison comme en mouvement ; la sandbox n a qu un attaquant qui progresse a decouvert.
"""
import sys, math, numpy as np, torch

TRANCHES = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 250), (250, 400)]
HOR_PAS = 9          # 30 s / 3,28 s par pas
N_MIN = 2000

# ---------------------------------------------------------------- cote ARMA
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__pouls__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
ENN, MASQ, Y = g['ENN'], g['MASQ'], g['Y']
# ENN[..., 3] = min(d,400)/400  -> distance au plus proche ennemi VIVANT du releve
d_enn = np.where(MASQ > 0.5, ENN[..., 3] * 400.0, 1e9)
d_min_arma = d_enn.min(axis=1)
print(f"\n  ARMA   {len(Y)} observations · mortalite globale {Y.mean():.2%}")

# ---------------------------------------------------------------- cote SANDBOX
src2 = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__pouls2__'}
sys.argv = [sys.argv[0]]
exec(compile(src2[:src2.index("if '--smoke' in sys.argv:")], 'agent_complet.py', 'exec'), h)
t = h['torch']; dev = h['dev']
POS, AZI, MSK, NC = h['POS'], h['AZI'], h['MSK'], h['NC']
degats_du_pas, SEUIL_MORT = h['degats_du_pas'], h['SEUIL_MORT']
ALLURES, POSTURES_V = h['ALLURES'], h['POSTURES_V']

t.manual_seed(0)
B, NPAS = 4096, 80
idx = t.randint(0, NC, (B,), device=dev)
ang = t.rand(B, device=dev) * 2 * math.pi
p = t.stack([t.sin(ang), t.cos(ang)], -1) * 250.0
wp = t.zeros(B, 3, device=dev); wp[:, 0] = 1.0        # debout : la posture dominante mesuree
deg = t.zeros(B, device=dev); vivant = t.ones(B, device=dev)

d_hist, deg_hist, viv_hist = [], [], []
for _ in range(NPAS):
    v = p.unsqueeze(1) - POS[idx]
    d = t.where(MSK[idx] > 0.5, v.norm(dim=-1), t.full_like(v[..., 0], 1e9)).min(dim=1).values
    d_hist.append(d.clone()); deg_hist.append(deg.clone()); viv_hist.append(vivant.clone())
    deg = deg + degats_du_pas(p, wp, idx) * vivant
    vivant = vivant * (deg < SEUIL_MORT).float()
    # marche droit vers l objectif, course debout : le comportement de reference
    dr = -p / p.norm(dim=-1, keepdim=True).clamp(min=1e-6)
    p = p + dr * ALLURES[2] * POSTURES_V[0] * vivant.unsqueeze(-1)

D = t.stack(d_hist).cpu().numpy()          # (NPAS,B)
G = t.stack(deg_hist).cpu().numpy()
V = t.stack(viv_hist).cpu().numpy()
# « meurt-il dans les 9 pas ? » : le seuil est franchi avant NPAS et dans l horizon
mort_dans = np.zeros_like(G)
for k in range(len(G)):
    fin = min(k + HOR_PAS, len(G) - 1)
    mort_dans[k] = (G[fin] >= SEUIL_MORT) & (G[k] < SEUIL_MORT)
ok = (V > 0.5) & (D < 400)                  # vivant, et au moins un defenseur dans l enveloppe
d_sb, y_sb = D[ok], mort_dans[ok]
print(f"  SANDBOX {len(y_sb)} pas · mortalite globale {y_sb.mean():.2%}")

print("\n" + "=" * 76)
print(f"  {'tranche':>12} {'ARMA n':>9} {'ARMA':>8} {'SANDBOX n':>10} {'SANDBOX':>9} {'rapport':>9}")
print("  " + "-" * 74)
rapports, hors, comparables = [], 0, 0
for a, b in TRANCHES:
    ma = (d_min_arma >= a) & (d_min_arma < b)
    ms = (d_sb >= a) & (d_sb < b)
    na, ns = int(ma.sum()), int(ms.sum())
    ya = Y[ma].mean() if na else float('nan')
    ys = y_sb[ms].mean() if ns else float('nan')
    if na >= N_MIN and ns >= N_MIN and ya > 0:
        comparables += 1
        r = ys / ya
        rapports.append(r)
        etat = 'OK' if 0.5 <= r <= 2.0 else ('HORS x4' if (r > 4 or r < 0.25) else 'hors')
        if not (0.5 <= r <= 2.0):
            hors += 1
        print(f"  {a:5d}-{b:<6d} {na:>9d} {ya:>7.2%} {ns:>10d} {ys:>8.2%} {r:>8.2f}  {etat}")
    else:
        print(f"  {a:5d}-{b:<6d} {na:>9d} {ya:>7.2%} {ns:>10d} {ys:>8.2%} {'.':>8}  non comparable")
print("  " + "-" * 74)

print("\n" + "=" * 76)
if comparables == 0:
    print("  AUCUNE TRANCHE COMPARABLE. Le pouls ne se prend pas — on l ecrit tel quel.")
else:
    dans = comparables - hors
    pire = max(max(rapports), 1 / min(rapports))
    med = sorted(rapports)[len(rapports) // 2]
    print(f"  {dans}/{comparables} tranches dans la tolerance (exige >= 2/3)"
          f" · pire ecart x{pire:.2f} (exige < 4) · rapport median {med:.2f}")
    if dans / comparables >= 2 / 3 and pire < 4:
        print("\n  LE POULS EST BON. La sandbox tue au meme ordre de grandeur qu Arma, par")
        print("  tranche de distance. La loi est FIDELE, pas seulement fidelement construite.")
    else:
        print(f"\n  HORS TOLERANCE. Facteur de correction DERIVE (rapport median) : "
              f"{1/med:.3f} sur le degat par impact.")
        print("  Aucun autre bouton ne bouge, et l etage 1 se rejoue apres.")
        ecart = max(rapports) / min(rapports)
        if ecart > 2.5:
            print(f"  ⚠ mais l ecart VARIE d un facteur {ecart:.1f} selon la distance : ce n est")
            print("    pas la chaine qui est mal calibree, c est la FORME de la courbe.")
print("  " + "=" * 74)
